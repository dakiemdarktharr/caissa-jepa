import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from tools.v29_development_panel_supervisor import (
    AVAILABLE_MEMORY_FLOOR_BYTES, MEMORY_GATE_BYTES,
    PROCESS_COMMIT_LIMIT_BYTES, PROCESS_CPU_LIMIT_SECONDS, RUNNER_BOOTSTRAP,
    _MemoryCpuJob, run_panel_supervised)
from two_player.v29_development import DATASET_ROOT


class V29PanelSupervisorTests(unittest.TestCase):
    def test_resource_guards_leave_memory_for_the_desktop(self):
        self.assertGreater(MEMORY_GATE_BYTES, AVAILABLE_MEMORY_FLOOR_BYTES)
        self.assertEqual(PROCESS_COMMIT_LIMIT_BYTES, 1_300_000_000)
        self.assertGreater(PROCESS_CPU_LIMIT_SECONDS, 0)

    def test_runner_bootstrap_waits_for_parent_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = root / "runner.py"
            marker = root / "started.txt"
            runner.write_text(
                "from pathlib import Path; import sys; "
                "Path(sys.argv[1]).write_text('started')\n",
                encoding="utf-8")
            child = subprocess.Popen(
                [sys.executable, "-B", "-c", RUNNER_BOOTSTRAP,
                 str(runner), str(marker)], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(0.15)
                self.assertIsNone(child.poll())
                self.assertFalse(marker.exists())
                assert child.stdin is not None
                child.stdin.write(b"1")
                child.stdin.flush()
                child.stdin.close()
                self.assertEqual(child.wait(timeout=10), 0)
                self.assertEqual(marker.read_text(encoding="utf-8"), "started")
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=10)

    def test_dataset_must_be_exact_pinned_dev09(self):
        with self.assertRaisesRegex(ValueError, "exact audited DEV09"):
            run_panel_supervised(Path("other-data"), Path("grant.json"),
                                 Path("chess_data/v29_panel"))

    @unittest.skipUnless(os.name == "nt", "Windows supervisor path checks")
    def test_output_cannot_overlap_dev09_and_grant_path_is_pinned(self):
        from tools.v29_development_panel_supervisor import APPROVAL_PATH
        with self.assertRaisesRegex(ValueError, "exact local V2.9 development grant"):
            run_panel_supervised(DATASET_ROOT, Path("other-grant.json"),
                                 Path("chess_data/v29-panel-test"))
        with self.assertRaisesRegex(ValueError, "fresh child of ignored chess_data"):
            run_panel_supervised(DATASET_ROOT, APPROVAL_PATH,
                                 DATASET_ROOT / "v29-panel-test")

    @unittest.skipUnless(os.name == "nt", "Windows Job Objects are Windows-only")
    def test_job_object_applies_and_can_query_memory_for_child(self):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | \
                getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", "import time; time.sleep(5)"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=flags)
        try:
            with _MemoryCpuJob(child, memory_bytes=1_300_000_000,
                               cpu_seconds=20) as job:
                current, peak = job.working_set_bytes()
                self.assertGreater(current, 0)
                self.assertGreaterEqual(peak, current)
                job.terminate(0)
                child.wait(timeout=10)
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
