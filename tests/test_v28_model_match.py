import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from two_player.games import BoardGame
from two_player.v28_model import Config, METHOD_VERSION
from tools.v28_match_power import CHECKPOINT_SEEDS, make_schedule
from tools.v28_model_match import (_play_game, _verify_game, play_paired_block,
                                   _load_locked_schedule, _validate_schedule,
                                   run_schedule, PROTOCOL, LOCKED_BUDGET)


class FixedPolicy:
    def __init__(self, variant, *, illegal=False):
        self.config = Config(variant=variant, seed=17, latent=4)
        self.illegal = illegal

    def plan_action(self, game, state):
        legal = tuple(game.legal_actions(state))
        values = {action: 0.0 for action in legal}
        return ((65 if self.illegal else legal[0]), values)


class V28ModelMatchTests(unittest.TestCase):
    def test_primary_schedule_is_complete_and_hash_guarded(self):
        schedule = make_schedule(matches_per_checkpoint=1)
        self.assertEqual(len(schedule), 80)
        _validate_schedule(schedule)
        corrupted = copy.deepcopy(schedule)
        corrupted[0]["match_seed"] += 1
        with self.assertRaisesRegex(ValueError, "hash"):
            _validate_schedule(corrupted)

    def test_paired_color_scores_are_from_jepa_perspective_and_replay(self):
        schedule = make_schedule(matches_per_checkpoint=1)
        row = next(row for row in schedule
                   if row["game"] == "connect4-gravity-6x7"
                   and row["comparison"] == "task-value-dynamics")
        jepa = FixedPolicy("reply-jepa")
        control = FixedPolicy("task-value-dynamics")
        result = play_paired_block(row, jepa, control)
        self.assertEqual(result["score_plus"],
                         result["plus_assignment"]["jepa"]["score_plus"])
        self.assertEqual(result["score_minus"],
                         1 - result["minus_assignment"]["jepa"]["score_plus"])
        self.assertEqual(result["paired_score_d"],
                         (result["score_plus"] + result["score_minus"]) / 2 - 0.5)
        game = BoardGame("connect4-gravity-6x7", 6, 7, 4, True)
        corrupted = copy.deepcopy(result["plus_assignment"]["jepa"])
        corrupted["transcript"][0]["action"] = 63
        self.assertFalse(_verify_game(game, corrupted))
        corrupted = copy.deepcopy(result["plus_assignment"]["jepa"])
        corrupted["transcript"][0]["decision_wall_seconds"] = 2.1
        self.assertFalse(_verify_game(game, corrupted))

    def test_illegal_action_is_a_model_forfeit_and_role_score_is_checked(self):
        game = BoardGame("connect3-test", 3, 3, 3)
        record = _play_game(game, FixedPolicy("reply-jepa", illegal=True),
                            FixedPolicy("task-value-dynamics"),
                            checkpoint_seed=17, match_seed=34_000_000)
        self.assertEqual(record["status"], "model_forfeit")
        self.assertEqual(record["forfeit_role"], "plus")
        self.assertEqual(record["score_plus"], 0.0)
        self.assertTrue(_verify_game(game, record))

    def test_primary_checkpoint_seed_panel_is_fixed(self):
        self.assertEqual(len(CHECKPOINT_SEEDS), 20)
        self.assertEqual(len(set(CHECKPOINT_SEEDS)), 20)

    def test_locked_runner_rejects_uncommitted_inference_budget(self):
        with self.assertRaisesRegex(ValueError, "budget"):
            run_schedule(make_schedule(), {}, "unused.jsonl", confirmatory=True,
                         commitment_sha256="a" * 64,
                         max_move_seconds=LOCKED_BUDGET["max_move_seconds"] + 0.1)

    def test_commitment_wrapper_resolves_and_fingerprints_raw_schedule(self):
        rows = make_schedule()
        original_wrapper = json.loads(Path(
            "docs/validation/V28_MATCH_SCHEDULE_V08_COMMITMENT.json").read_text(
                encoding="utf-8"))
        manifest = original_wrapper["commitment"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools" / "v28_match_power.py").write_bytes(
                Path("tools/v28_match_power.py").read_bytes())
            (root / "tools" / "v28_match_analysis.py").write_bytes(
                Path("tools/v28_match_analysis.py").read_bytes())
            artifact_path = root / "chess_data" / "locked.json"
            artifact_path.parent.mkdir()
            raw = json.dumps({"manifest": manifest, "blocks": rows}, sort_keys=True,
                             indent=2, allow_nan=False).encode("utf-8") + b"\n"
            artifact_path.write_bytes(raw)
            wrapper = {"commitment": manifest,
                       "analysis_code_sha256": hashlib.sha256(
                           (root / "tools" / "v28_match_analysis.py").read_bytes()).hexdigest(),
                       "learned_match_protocol": {
                "protocol": PROTOCOL, "budget": LOCKED_BUDGET}, "artifact": {
                "path": "chess_data/locked.json", "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest()}}
            wrapper_path = root / "commitment.json"
            wrapper_path.write_text(json.dumps(wrapper), encoding="utf-8")
            with patch("tools.v28_model_match.ROOT", root):
                schedule_data, loaded, fingerprint = _load_locked_schedule(wrapper_path)
                self.assertEqual(loaded, rows)
                self.assertEqual(schedule_data["manifest"], manifest)
                self.assertEqual(fingerprint, hashlib.sha256(raw).hexdigest())
                wrapper["artifact"]["sha256"] = "0" * 64
                wrapper_path.write_text(json.dumps(wrapper), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "fingerprint"):
                    _load_locked_schedule(wrapper_path)

    def test_streamed_run_writes_atomic_receipt_for_complete_schedule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = root / "checkpoint.npz"
            checkpoint.write_bytes(b"test-only synthetic checkpoint")
            receipt_path = root / "training.receipt.json"
            receipt_path.write_text("{}", encoding="utf-8")
            panels = {}
            for seed in CHECKPOINT_SEEDS:
                panels[seed] = {}
                for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
                    policy = FixedPolicy(variant)
                    policy.config = Config(variant=variant, seed=seed, latent=4)
                    policy.step = 1
                    policy.training_state = {"completed_epochs": 1, "history": []}
                    policy._checkpoint_path = str(checkpoint)
                    policy._training_receipt_path = str(receipt_path)
                    policy._training_receipt = {
                        "dataset_fingerprint": "d" * 64,
                        "dataset_sha256": "a" * 64,
                        "audit_sha256": "b" * 64,
                        "run_config_sha256": "c" * 64,
                        "model_code_sha256": "e" * 64,
                        "trainer_code_sha256": "f" * 64,
                        "optimizer_step": 1,
                        "completed_epochs": 1,
                        "effective_run": {"method": METHOD_VERSION,
                                           "model": asdict(policy.config),
                                           "run": {"epochs": 1, "shuffle_seed": 1},
                                           "runtime": {"python_version": "test"},
                                           "dataset_fingerprint": "d" * 64}}
                    panels[seed][variant] = policy
            schedule = make_schedule(matches_per_checkpoint=1)
            output = root / "dev_matches.jsonl"
            receipt = run_schedule(schedule, panels, output)
            self.assertEqual(receipt["block_count"], len(schedule))
            self.assertFalse(receipt["confirmatory"])
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), len(schedule) + 1)
            self.assertEqual(rows[0]["record_type"], "manifest")
            self.assertFalse(rows[0]["outcomes_are_locked"])
            saved = json.loads(output.with_suffix(".jsonl.receipt.json")
                               .read_text(encoding="utf-8"))
            self.assertEqual(saved["artifact_sha256"], receipt["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
