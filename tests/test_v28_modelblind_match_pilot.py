import json
import tempfile
import unittest
from pathlib import Path

from tools.v28_modelblind_match_pilot import (
    PROTOCOL, V28_GAMES, make_schedule, play_paired_block, run_pilot,
    verify_block,
)


class ModelBlindMatchPilotTests(unittest.TestCase):
    def test_schedule_is_disjoint_from_locked_match_seed_range_and_balanced(self):
        rows = make_schedule(matches_per_checkpoint=2, checkpoint_seeds=(17, 29))
        self.assertEqual(len(rows), len(V28_GAMES) * 2 * 2 * 2)
        self.assertTrue(all(row["match_seed"] >= 33_000_000 for row in rows))
        self.assertEqual({row["game"] for row in rows}, set(V28_GAMES))
        self.assertEqual({row["comparison"] for row in rows},
                         {"independent-tape-self-play", "reversed-tape-self-play"})
        self.assertEqual(len({row["block_id"] for row in rows}), len(rows))

    def test_paired_proxy_games_replay_and_are_deterministic(self):
        row = make_schedule(matches_per_checkpoint=1, checkpoint_seeds=(17,))[0]
        first = play_paired_block(row)
        second = play_paired_block(row)
        def without_runtime(value):
            if isinstance(value, dict):
                return {key: without_runtime(item) for key, item in value.items()
                        if key not in {"elapsed_seconds", "runtime_seconds"}}
            if isinstance(value, list):
                return [without_runtime(item) for item in value]
            return value
        self.assertEqual(without_runtime(first), without_runtime(second))
        self.assertTrue(verify_block(row, first))
        self.assertIn(first["paired_score_d"], (-0.5, -0.25, 0.0, 0.25, 0.5))

    def test_small_pilot_saves_only_proxy_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.jsonl"
            result = run_pilot(path, blocks=4)
            self.assertEqual(result["schema"], PROTOCOL)
            self.assertEqual(result["block_count"], 4)
            loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(loaded[0]["record_type"], "manifest")
            self.assertIn("proxy", loaded[0]["status"])
            outcomes = loaded[1:]
            self.assertEqual(len(outcomes), 4)
            self.assertTrue(all(verify_block(row, outcome)
                                for row, outcome in zip(make_schedule(
                                    matches_per_checkpoint=1,
                                    checkpoint_seeds=(17,)), outcomes)))
            receipt = json.loads(Path(result["receipt_path"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["artifact"]["sha256"], result["artifact_sha256"])

    def test_pilot_rejects_unbalanced_sample_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "multiple"):
                run_pilot(Path(directory) / "pilot.json", blocks=5)


if __name__ == "__main__":
    unittest.main()
