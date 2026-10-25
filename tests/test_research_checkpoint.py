from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.research_checkpoint import checkpoint, git


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
        git(self.root, "add", ".gitignore", "note.md")
        git(self.root, "commit", "-m", "fixture")

    def publish(self, paths=("note.md",), **kwargs):
        return checkpoint(self.root, list(paths), "fixture checkpoint", push=True,
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


if __name__ == "__main__":
    unittest.main()
