import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import v28_development_match_analysis as analysis
from tools.v28_model_match import _state_hash
from two_player.games import BoardGame


class DevelopmentPanelBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.seeds = (17, 29)
        self.arms = ("reply-jepa", "task-value-dynamics", "direct-leaf")
        self.ledger = {
            "approval_sha256": "a" * 64,
            "dataset_fingerprint": "b" * 64,
            "records_sha256": "c" * 64,
            "audit_sha256": "d" * 64,
        }
        self.match_receipt = {
            "panel_checkpoint_sha256": {},
            "panel_training_receipt_sha256": {},
            "panel_run_identity": {},
        }
        self.rows = []

        for seed in self.seeds:
            for arm in self.arms:
                folder = self.root / str(seed) / arm
                folder.mkdir(parents=True)
                checkpoint = folder / "checkpoint.npz"
                checkpoint.write_bytes(f"checkpoint-{seed}-{arm}".encode())
                checkpoint_sha = self.sha(checkpoint)
                receipt_path = Path(str(checkpoint) + ".receipt.json")
                training = {
                    "schema": "caissa-jepa-v28-train-receipt-v1",
                    "checkpoint_sha256": checkpoint_sha,
                    "variant": arm,
                    "fit_scope": "development-only",
                    "split": "train",
                    "development_approval_sha256": self.ledger["approval_sha256"],
                    "dataset_fingerprint": self.ledger["dataset_fingerprint"],
                    "dataset_sha256": self.ledger["records_sha256"],
                    "audit_sha256": self.ledger["audit_sha256"],
                    "run_config_sha256": "e" * 64,
                    "model_code_sha256": "f" * 64,
                    "trainer_code_sha256": "1" * 64,
                    "optimizer_step": 3,
                    "completed_epochs": 1,
                    "effective_run": {"fit_scope": "development-only"},
                }
                receipt_path.write_text(json.dumps(training), encoding="utf-8")
                receipt_sha = self.sha(receipt_path)
                row = {
                    "seed": seed,
                    "variant": arm,
                    "status": "completed",
                    "checkpoint": str(checkpoint),
                    "checkpoint_sha256": checkpoint_sha,
                    "receipt": str(receipt_path),
                    "receipt_sha256": receipt_sha,
                    "optimizer_step": 3,
                    "completed_epochs": 1,
                }
                self.rows.append(row)
                self.match_receipt["panel_checkpoint_sha256"].setdefault(
                    str(seed), {})[arm] = checkpoint_sha
                self.match_receipt["panel_training_receipt_sha256"].setdefault(
                    str(seed), {})[arm] = receipt_sha
                self.match_receipt["panel_run_identity"].setdefault(
                    str(seed), {})[arm] = {
                        field: training[field] for field in (
                            "dataset_fingerprint", "dataset_sha256", "audit_sha256",
                            "run_config_sha256", "model_code_sha256",
                            "trainer_code_sha256", "optimizer_step", "completed_epochs")
                    }

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def validate(self):
        with patch.object(analysis, "PANEL_SEEDS", self.seeds), patch.object(
                analysis, "ARMS", self.arms):
            analysis._validate_panel_bindings(self.root, {
                **self.ledger, "runs": self.rows,
            }, self.match_receipt)

    def test_exact_panel_paths_hashes_and_identities_pass(self):
        self.validate()

    def test_match_receipt_mismatch_fails_closed(self):
        self.match_receipt["panel_checkpoint_sha256"]["17"][
            "reply-jepa"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "does not bind"):
            self.validate()

    def test_missing_panel_arm_fails_closed(self):
        self.rows.pop()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.validate()


class DevelopmentGameReplayTests(unittest.TestCase):
    def setUp(self):
        self.game = BoardGame("tic-tac-toe", 3, 3)
        state = self.game.initial()
        transcript = []
        actions = (0, 8, 1, 9, 2)
        counts = {"plus": {"transitions": 0, "decision_calls": 0,
                           "wall_seconds": 0.0, "cpu_seconds": 0.0},
                  "minus": {"transitions": 0, "decision_calls": 0,
                            "wall_seconds": 0.0, "cpu_seconds": 0.0}}
        for ply, action in enumerate(actions):
            seat = "plus" if state.player == 1 else "minus"
            legal = list(self.game.legal_actions(state))
            before = state
            state = self.game.transition(state, action)
            transcript.append({
                "ply": ply, "player": before.player,
                "state_sha256": _state_hash(before), "legal_actions": legal,
                "action": action, "action_value": 0.0,
                "next_state_sha256": _state_hash(state),
                "planner_transitions": 0,
                "decision_wall_seconds": 0.0, "decision_cpu_seconds": 0.0,
            })
            counts[seat]["decision_calls"] += 1
        self.record = {
            "status": "complete", "score_plus": 1.0,
            "terminal_utility_plus": self.game.terminal(state),
            "terminal_state_sha256": _state_hash(state),
            "transcript": transcript,
            "compute": {
                "plus": {**counts["plus"], "branch_value_calls": 0,
                         "latent_evaluations": 0},
                "minus": {**counts["minus"], "branch_value_calls": 0,
                         "latent_evaluations": 0},
            },
        }

    def test_terminal_game_replays_and_returns_valid_score(self):
        self.assertEqual(analysis._validate_game_record(self.game, self.record), 1.0)

    def test_impossible_fractional_score_is_rejected(self):
        self.record["score_plus"] = 0.25
        with self.assertRaisesRegex(ValueError, "score domain"):
            analysis._validate_game_record(self.game, self.record)

    def test_terminal_utility_mismatch_is_rejected_by_replay(self):
        self.record["terminal_utility_plus"] = 0
        with self.assertRaisesRegex(ValueError, "fails replay"):
            analysis._validate_game_record(self.game, self.record)


if __name__ == "__main__":
    unittest.main()
