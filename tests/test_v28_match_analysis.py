import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.v28_match_analysis import (_holm, analyze, validate_outcomes,
                                     load_locked_schedule)
from tools.v28_match_power import (
    CHECKPOINT_SEEDS, COMPARISONS, FIRST_MATCH_SEED, GAMES,
    MATCHES_PER_CHECKPOINT, make_schedule,
)


class MatchAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.schedule = make_schedule(
            checkpoint_seeds=(17,), matches_per_checkpoint=2)
        self.outcomes = [
            {"block_id": row["block_id"], "game": row["game"],
             "comparison": row["comparison"], "checkpoint_seed": row["checkpoint_seed"],
             "match_seed": row["match_seed"], "external_censored": False,
             "score_plus": 0.5, "score_minus": 0.5, "status": "complete"}
            for row in self.schedule
        ]

    def test_complete_schedule_is_accepted(self):
        actual = validate_outcomes(self.schedule, self.outcomes)
        self.assertEqual(len(actual), len(self.schedule))
        self.assertEqual(len(actual), len(GAMES) * len(COMPARISONS) * 2)

    def test_locked_loader_binds_analysis_code_and_schedule_artifact(self):
        root_source = Path(__file__).resolve().parents[1]
        wrapper = json.loads((root_source / "docs" / "validation" /
                              "V28_MATCH_SCHEDULE_V08_COMMITMENT.json").read_text(
                                  encoding="utf-8"))
        rows = make_schedule()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools_dir = root / "tools"
            tools_dir.mkdir()
            for name in ("v28_match_power.py", "v28_match_analysis.py"):
                (tools_dir / name).write_bytes((root_source / "tools" / name).read_bytes())
            schedule_path = root / wrapper["artifact"]["path"]
            schedule_path.parent.mkdir(parents=True)
            schedule_bytes = json.dumps(
                {"manifest": wrapper["commitment"], "blocks": rows},
                sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n"
            schedule_path.write_bytes(schedule_bytes)
            wrapper["artifact"].update(
                bytes=len(schedule_bytes),
                sha256=hashlib.sha256(schedule_bytes).hexdigest())
            wrapper_path = root / "commitment.json"
            wrapper_path.write_text(json.dumps(wrapper), encoding="utf-8")
            with patch("tools.v28_match_analysis.ROOT", root):
                loaded = load_locked_schedule(schedule_path, wrapper_path)
                self.assertEqual(loaded["blocks"], rows)
                analysis_path = tools_dir / "v28_match_analysis.py"
                analysis_path.write_text("# changed analysis\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "analysis source"):
                    load_locked_schedule(schedule_path, wrapper_path)

    def test_missing_or_duplicate_block_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_outcomes(self.schedule, self.outcomes[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_outcomes(self.schedule, self.outcomes + [self.outcomes[0]])

    def test_external_failure_must_censor_all_arms_and_games(self):
        group_seed = self.outcomes[0]["match_seed"]
        censored = []
        for row in self.outcomes:
            item = dict(row)
            if item["match_seed"] == group_seed:
                item = {key: value for key, value in item.items()
                        if key not in ("score_plus", "score_minus", "status")}
                item["external_censored"] = True
            censored.append(item)
        self.assertEqual(len(validate_outcomes(self.schedule, censored)), len(self.schedule))
        censored[0]["external_censored"] = False
        censored[0].update(score_plus=0.5, score_minus=0.5, status="complete")
        with self.assertRaisesRegex(ValueError, "all arms"):
            validate_outcomes(self.schedule, censored)

    def test_model_forfeit_is_retained_as_a_scored_outcome(self):
        row = dict(self.outcomes[0], status="model_forfeit", score_plus=0.0)
        rows = [row if item["block_id"] == row["block_id"] else item
                for item in self.outcomes]
        self.assertIn(row["block_id"], validate_outcomes(self.schedule, rows))

    def test_holm_stepdown_is_monotone_and_familywise_adjusted(self):
        adjusted = _holm({"a": 0.01, "b": 0.03})
        self.assertAlmostEqual(adjusted["a"], 0.02)
        self.assertAlmostEqual(adjusted["b"], 0.03)
        reversed_order = _holm({"a": 0.03, "b": 0.01})
        self.assertAlmostEqual(reversed_order["a"], 0.03)
        self.assertAlmostEqual(reversed_order["b"], 0.02)

    def test_locked_analysis_uses_paired_games_and_applies_holm(self):
        schedule = make_schedule()
        outcomes = []
        for row in schedule:
            checkpoint_index = CHECKPOINT_SEEDS.index(row["checkpoint_seed"])
            offset = row["match_seed"] - FIRST_MATCH_SEED - checkpoint_index * MATCHES_PER_CHECKPOINT
            if row["comparison"] == COMPARISONS[0]:
                score = 1.0 if offset % 2 == 0 else 0.5
            else:
                score = 1.0 if offset % 2 == 0 else 0.0
            outcomes.append({
                "block_id": row["block_id"], "game": row["game"],
                "comparison": row["comparison"],
                "checkpoint_seed": row["checkpoint_seed"],
                "match_seed": row["match_seed"], "external_censored": False,
                "score_plus": score, "score_minus": score, "status": "complete",
            })
        result = analyze(schedule, outcomes, bootstrap_replicates=1000)
        self.assertAlmostEqual(result["primary_effects"][COMPARISONS[0]]["mean_d"], 0.25)
        self.assertAlmostEqual(result["primary_effects"][COMPARISONS[1]]["mean_d"], 0.0)
        self.assertLess(result["primary_effects"][COMPARISONS[0]]["p_holm"], 0.05)
        self.assertGreater(result["primary_effects"][COMPARISONS[1]]["p_holm"], 0.05)
        self.assertFalse(result["superiority_pass"])


if __name__ == "__main__":
    unittest.main()
