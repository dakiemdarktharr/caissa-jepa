from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.research_checkpoint import STATUS_START, STATUS_END, checkpoint, git


class ResearchCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.remote = Path(self.tmp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(self.remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "--initial-branch=main", str(self.root)], check=True, capture_output=True)
        git(self.root, "config", "user.email", "fixture@example.invalid")
        git(self.root, "config", "user.name", "Synthetic Fixture")
        git(self.root, "remote", "add", "origin", str(self.remote))
        (self.root / ".gitignore").write_text("chess_data/\n*.npz\n")
        (self.root / "note.md").write_text("initial\n")
        (self.root / "README.md").write_text(f"{STATUS_START}\nSynthetic checkpoint 0\n{STATUS_END}\n")
        self.revision = 0
        git(self.root, "add", ".gitignore", "note.md", "README.md")
        git(self.root, "commit", "-m", "fixture")

    def publish(self, paths=("note.md",), **kwargs):
        selected = list(paths)
        if git(self.root, "status", "--porcelain", "--untracked-files=all", "--", *selected, check=False).stdout:
            self.revision += 1
            (self.root / "README.md").write_text(f"{STATUS_START}\nSynthetic checkpoint {self.revision}\n{STATUS_END}\n")
            selected.append("README.md")
        return checkpoint(self.root, selected, "fixture checkpoint", push=True,
                          expected_remote=str(self.remote), **kwargs)

    def test_round_trip_clone_preserves_only_selected_files_and_can_retry_push(self):
        (self.root / "note.md").write_text("verified progress\n")
        (self.root / "unrelated.md").write_text("leave untouched\n")
        result = self.publish()
        self.assertTrue(result["remote_verified"])
        self.assertFalse(self.publish()["created_commit"])
        clone = self.root.parent / "restored"
        subprocess.run(["git", "clone", str(self.remote), str(clone)], check=True, capture_output=True)
        self.assertEqual((clone / "note.md").read_text(), "verified progress\n")
        self.assertIn("Synthetic checkpoint 1", (clone / "README.md").read_text())
        self.assertFalse((clone / "unrelated.md").exists())

    def test_rejects_excluded_artifacts_wrong_remote_and_staged_work(self):
        (self.root / "chess_data").mkdir()
        (self.root / "chess_data/result.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "excluded"):
            self.publish(["chess_data/result.json"])
        (self.root / "weights.npz").write_bytes(b"fixture")
        with self.assertRaises(ValueError):
            self.publish(["weights.npz"])
        with self.assertRaisesRegex(ValueError, "destination"):
            checkpoint(self.root, ["note.md"], "test", expected_remote="wrong")
        (self.root / "other.md").write_text("other\n")
        git(self.root, "add", "other.md")
        with self.assertRaisesRegex(ValueError, "staged"):
            self.publish()
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only").stdout.strip(), "other.md")

    def test_rejects_traversal_oversize_and_symlink(self):
        with self.assertRaises(ValueError):
            self.publish(["../outside.md"])
        (self.root / "large.json").write_bytes(b"x" * 2_000_001)
        with self.assertRaises(ValueError):
            self.publish(["large.json"])
        (self.root / "link.md").symlink_to(self.root / "note.md")
        with self.assertRaises(ValueError):
            self.publish(["link.md"])

    def test_diverged_remote_is_not_overwritten(self):
        self.publish()
        clone = self.root.parent / "second"
        subprocess.run(["git", "clone", str(self.remote), str(clone)], check=True, capture_output=True)
        git(clone, "config", "user.email", "fixture@example.invalid")
        git(clone, "config", "user.name", "Synthetic Fixture")
        (clone / "remote.md").write_text("remote progress\n")
        git(clone, "add", "remote.md"); git(clone, "commit", "-m", "remote change")
        git(clone, "push", "origin", "main")
        before = git(clone, "rev-parse", "HEAD").stdout.strip()
        (self.root / "note.md").write_text("local progress\n")
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish()
        self.assertIn(before, git(self.root, "ls-remote", str(self.remote), "refs/heads/main").stdout)

    def test_standard_csv_line_endings_preserved_but_trailing_spaces_rejected(self):
        csv_bytes = b"metric,value\r\nloss,1.0\r\n"
        (self.root / "metrics.csv").write_bytes(csv_bytes)
        self.assertTrue(self.publish(["metrics.csv"])["remote_verified"])
        restored = subprocess.check_output(["git", "--git-dir", str(self.remote), "show", "main:metrics.csv"])
        self.assertEqual(restored, csv_bytes)
        (self.root / "bad.py").write_bytes(b"value = 1 \r\n")
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish(["bad.py"])

    def test_changed_files_require_readme_status_refresh_before_staging(self):
        (self.root / "note.md").write_text("new source\n")
        with self.assertRaisesRegex(ValueError, "select README"):
            checkpoint(self.root, ["note.md"], "missing dashboard", expected_remote=str(self.remote))
        readme = self.root / "README.md"
        readme.write_text(readme.read_text() + "Unrelated prose edit\n")
        with self.assertRaisesRegex(ValueError, "unchanged"):
            checkpoint(self.root, ["note.md", "README.md"], "stale dashboard", expected_remote=str(self.remote))
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only").stdout, "")

    def test_small_reviewed_publication_artifacts_preserve_bytes_and_size_cap(self):
        # A PDF can lack NUL bytes in its initial sample while containing
        # non-UTF8 stream bytes and whitespace; attributes must keep it binary.
        artifacts = {"report.pdf": b"%PDF-1.4\n\x94synthetic-byte-fixture \n%%EOF\n",
                     "figure.png": b"\x89PNG\r\n\x1a\n\x00synthetic-byte-fixture",
                     "figure.svg": b'<svg xmlns="http://www.w3.org/2000/svg"/> \n',
                     ".gitattributes": b"*.pdf binary\n*.png binary\n*.svg -whitespace\n"}
        for name, data in artifacts.items():
            (self.root / name).write_bytes(data)
        self.assertTrue(self.publish(artifacts)["remote_verified"])
        for name, data in artifacts.items():
            restored = subprocess.check_output(["git", "--git-dir", str(self.remote), "show", "main:" + name])
            self.assertEqual(restored, data)
        (self.root / "oversize.pdf").write_bytes(b"x" * 2_000_001)
        with self.assertRaises(ValueError):
            self.publish(["oversize.pdf"])

    def test_missing_duplicate_or_reversed_status_markers_rejected(self):
        for content in ["No status section", f"{STATUS_START}\nx\n{STATUS_START}\n{STATUS_END}",
                        f"{STATUS_END}\nx\n{STATUS_START}", f"{STATUS_START}\n{STATUS_END}"]:
            with self.subTest(content=content):
                (self.root / "README.md").write_text(content)
                with self.assertRaises(ValueError):
                    checkpoint(self.root, ["README.md"], "invalid dashboard", expected_remote=str(self.remote))
                self.assertEqual(git(self.root, "diff", "--cached", "--name-only").stdout, "")


if __name__ == "__main__":
    unittest.main()
