from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.v28_modelblind_match_pilot import _canonical
from tools.v28_modelblind_pilot_supervisor import (
    _code_fingerprints, _derived_paths, _selected_schedule,
    _validate_completion)


class PilotSupervisorTests(unittest.TestCase):
    def test_selected_schedule_matches_runner_sizing_for_small_and_full_runs(self):
        small = _selected_schedule(8)
        self.assertEqual(len(small), 8)
        self.assertEqual(len(_selected_schedule(9600)), 9600)
        with self.assertRaises(ValueError):
            _selected_schedule(7)
        with self.assertRaises(ValueError):
            _selected_schedule(84)

    def test_preflight_covers_runner_and_supervisor_sidecars(self):
        output = Path("pilot.jsonl")
        paths = {path.name for path in _derived_paths(output)}
        self.assertIn("pilot.jsonl.receipt.json.tmp", paths)
        self.assertIn("pilot.jsonl.supervisor.json.terminal-fallback.json", paths)

    def test_behavior_source_fingerprints_change_when_dependency_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "rules.py"
            source.write_text("RULES = 1\n", encoding="utf-8")
            first = _code_fingerprints({"two_player/games.py": source})
            source.write_text("RULES = 2\n", encoding="utf-8")
            second = _code_fingerprints({"two_player/games.py": source})
        self.assertNotEqual(first, second)

    def test_supervisor_is_in_run_fingerprint_and_midrun_source_change_fails_closed(self):
        fingerprints = _code_fingerprints()
        self.assertIn("tools/v28_modelblind_pilot_supervisor.py", fingerprints)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "no_artifact.jsonl"
            changed = dict(fingerprints)
            changed["two_player/games.py"] = "0" * 64
            with mock.patch(
                    "tools.v28_modelblind_pilot_supervisor._code_fingerprints",
                    return_value=changed):
                with self.assertRaisesRegex(ValueError, "code inputs changed"):
                    _validate_completion(
                        output, blocks=8,
                        source_sha=fingerprints["tools/v28_modelblind_match_pilot.py"],
                        schedule_sha="f" * 64,
                        code_fingerprints=fingerprints)

    def test_completion_requires_matching_artifact_receipt_schedule_and_source(self):
        schedule = _selected_schedule(8)
        schedule_sha = hashlib.sha256(_canonical(schedule)).hexdigest()
        code_fingerprints = _code_fingerprints()
        source_sha = code_fingerprints["tools/v28_modelblind_match_pilot.py"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pilot.jsonl"
            manifest = {
                "schema": "v28-modelblind-match-pilot-v01",
                "record_type": "manifest",
                "block_count": len(schedule),
                "schedule_sha256": schedule_sha,
                "source_sha256": source_sha,
            }
            output.write_text(json.dumps(manifest) + "\n" +
                              "{}\n" * len(schedule), encoding="utf-8")
            artifact_sha = hashlib.sha256(output.read_bytes()).hexdigest()
            receipt = {
                "schema": "v28-modelblind-match-pilot-v01-receipt",
                "block_count": len(schedule),
                "source_sha256": source_sha,
                "schedule_sha256": schedule_sha,
                "artifact": {"path": str(output), "bytes": output.stat().st_size,
                             "sha256": artifact_sha},
            }
            output.with_suffix(output.suffix + ".receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8")
            validated = _validate_completion(output, blocks=8,
                                             source_sha=source_sha,
                                             schedule_sha=schedule_sha,
                                             code_fingerprints=code_fingerprints)
            self.assertEqual(validated["sha256"], artifact_sha)
            self.assertEqual(validated["block_count"], 8)
            receipt["schedule_sha256"] = "0" * 64
            output.with_suffix(output.suffix + ".receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schedule hash mismatch"):
                _validate_completion(output, blocks=8,
                                     source_sha=source_sha,
                                     schedule_sha=schedule_sha,
                                     code_fingerprints=code_fingerprints)


if __name__ == "__main__":
    unittest.main()
