import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.v211_development_match_analysis import _mean_interval
from tools import v211_model_match
from tools.v211_model_match import _extract_effective_run, verify_baseline_runtime
from tools.v211_run_development_panel import _is_current_process_in_job, run_panel
from two_player.v211_development import (SCHEDULE_COMPARISONS, SEEDS,
                                         development_schedule, validate_spec)
from tools.v28_match_power import _canonical_hash


class V211ProtocolTests(unittest.TestCase):
    def test_frozen_spec_and_schedule_reproduce(self):
        spec = validate_spec()
        rows = development_schedule()
        self.assertEqual(len(rows), 240)
        self.assertEqual(_canonical_hash(rows), spec["schedule"]["schedule_sha256"])
        self.assertEqual(set(row["comparison"] for row in rows),
                         set(SCHEDULE_COMPARISONS))
        self.assertEqual(set(row["checkpoint_seed"] for row in rows), set(SEEDS))
        self.assertEqual({row["match_seed"] for row in rows},
                         set(range(35_010_000, 35_010_040)))
        self.assertTrue(all(row["color_assignments"] == [1, -1] for row in rows))

    def test_seed_cluster_interval_requires_all_20_seeds(self):
        summary = _mean_interval([0.1] * 20)
        self.assertAlmostEqual(summary["mean"], 0.1)
        self.assertEqual(summary["seed_clusters"], 20)
        self.assertEqual(summary["positive_seed_clusters"], 20)
        with self.assertRaises(ValueError):
            _mean_interval([0.1] * 19)

    def test_schedule_hash_is_sensitive_to_control_label(self):
        rows = development_schedule()
        rows[0]["comparison"] = "unfrozen-control"
        self.assertNotEqual(_canonical_hash(rows),
                            "c6574b28767dc29e80c3bfd2ad158c58528561a8dc2c5393c86d54534f33bc2e")

    def test_fit_runner_requires_supervisor_token_before_data_access(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(PermissionError):
                run_panel("unused", "unused", "unused",
                          supervision_token="0" * 64)

    def test_fit_runner_rejects_valid_token_without_job_object(self):
        token = "a" * 64
        with (mock.patch.dict("os.environ", {
                "CAISSA_V211_SUPERVISOR_TOKEN": token}, clear=True),
              mock.patch("tools.v211_run_development_panel._is_current_process_in_job",
                         return_value=False)):
            with self.assertRaisesRegex(PermissionError, "Windows Job Object"):
                run_panel("unused", "unused", "unused", supervision_token=token)

    def test_receipt_parser_decodes_effective_run_without_history(self):
        receipt = {
            "completed_epochs": 3,
            "effective_run": {"runtime": {"python": "3.x"}, "seed": 5},
            "history": [{"loss": 123.0, "epoch": 1}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            with mock.patch("tools.v211_model_match.json.loads",
                            wraps=json.loads) as loads:
                result = _extract_effective_run(path)
        self.assertEqual(result, receipt["effective_run"])
        self.assertEqual(loads.call_count, 1)
        self.assertNotIn('"history"', loads.call_args.args[0])

    def test_matcher_validates_supervisor_resource_attestation(self):
        with tempfile.TemporaryDirectory() as directory:
            panel_root = Path(directory) / "candidate"
            status_path = panel_root.with_suffix(".supervisor.json")
            supervisor_hash = v211_model_match._sha(
                v211_model_match.ROOT / "tools" / "v211_development_panel_supervisor.py")
            helper_hash = v211_model_match._sha(
                v211_model_match.ROOT / "tools" / "v29_development_panel_supervisor.py")
            runner_hash = v211_model_match._sha(
                v211_model_match.ROOT / "tools" / "v211_run_development_panel.py")
            samples = [{"available_physical_bytes": 2_500_000_000,
                        "memory_load_percent": 50,
                        "elapsed_seconds": index * 20.0} for index in range(4)]
            status = {
                "schema": "caissa-jepa-v211-panel-supervisor-v01",
                "status": "complete", "fit_started": True, "return_code": 0,
                "termination_reason": None, "output": str(panel_root.resolve()),
                "supervisor_sha256": supervisor_hash,
                "resource_helper_sha256": helper_hash,
                "runner_sha256": runner_hash,
                "memory_gate_bytes": 2_000_000_000,
                "available_memory_floor_bytes": 1_000_000_000,
                "process_commit_limit_bytes": 1_300_000_000,
                "process_cpu_limit_seconds": 4 * 60 * 60,
                "panel_wall_limit_seconds": 6 * 60 * 60,
                "preflight_samples": samples,
                # Working set is reported separately; the Job Object enforces commit.
                "peak_working_set_bytes": 1_500_000_000,
                "elapsed_seconds": 120.0,
            }
            status_path.write_text(json.dumps(status), encoding="utf-8")
            attestation = {
                "status_path": str(status_path.resolve()),
                "status_sha256": v211_model_match._sha(status_path),
                "supervisor_code_sha256": supervisor_hash,
                "resource_helper_sha256": helper_hash,
                "runner_code_sha256": runner_hash,
                "job_object_assigned": True,
                "process_commit_limit_bytes": 1_300_000_000,
                "process_cpu_limit_seconds": 4 * 60 * 60,
                "available_memory_floor_bytes": 1_000_000_000,
                "memory_gate_bytes": 2_000_000_000,
                "stable_preflight_samples": samples,
                "peak_working_set_bytes": 1_500_000_000,
                "elapsed_seconds": 120.0,
                "termination_reason": None,
            }
            v211_model_match._verify_supervisor_attestation(
                {"supervisor_attestation": attestation}, panel_root)

            status["resource_helper_sha256"] = "0" * 64
            status_path.write_text(json.dumps(status), encoding="utf-8")
            attestation["status_sha256"] = v211_model_match._sha(status_path)
            with self.assertRaisesRegex(ValueError, "resource gate"):
                v211_model_match._verify_supervisor_attestation(
                    {"supervisor_attestation": attestation}, panel_root)

    def test_pre_fit_runtime_gate_checks_all_60_controls(self):
        spec = {"dataset": {"expected_identity": {
            "dataset_fingerprint": "fingerprint", "records_sha256": "records",
            "audit_sha256": "audit"}}}
        rows = {}
        for seed in SEEDS:
            for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
                checkpoint_root = (v211_model_match.V29_LEDGER_PATH.parent /
                                   str(seed) / variant)
                rows[(seed, variant)] = {
                    "receipt": str(checkpoint_root / "checkpoint.npz.receipt.json"),
                    "receipt_sha256": "receipt-hash",
                    "checkpoint_sha256": "checkpoint-hash",
                }
        runtime = {"python": "test-runtime"}
        with (mock.patch("tools.v211_model_match.validate_spec", return_value=spec),
              mock.patch("tools.v211_model_match._baseline_panels",
                         return_value=(Path("ledger"), {}, rows)),
              mock.patch("tools.v211_model_match._sha", return_value="receipt-hash"),
              mock.patch("tools.v211_model_match._runtime_identity", return_value=runtime),
              mock.patch("tools.v211_model_match._receipt_identity",
                         return_value={"effective_run": {"runtime": runtime}}) as receipt):
            self.assertEqual(verify_baseline_runtime(), runtime)
        self.assertEqual(receipt.call_count, 60)

    def test_supervisor_cli_bootstraps_repo_import_path(self):
        command = [sys.executable,
                   str(v211_model_match.ROOT / "tools" /
                       "v211_development_panel_supervisor.py"),
                   "--help"]
        result = subprocess.run(command, cwd=v211_model_match.ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Bounded Windows supervisor", result.stdout)


if __name__ == "__main__":
    unittest.main()
