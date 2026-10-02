import json
import unittest
from pathlib import Path

from tools.v29_run_development_panel import SPEC_PATH, _validate_spec, run_panel
from two_player.v29_development import DATASET_ROOT, development_schedule


class V29DevelopmentPanelTests(unittest.TestCase):
    def test_frozen_development_panel_spec_is_exact_and_preoutcome(self):
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        _validate_spec(spec)
        self.assertEqual(spec["development_match_schedule"]["block_count"], 160)
        self.assertFalse(spec["dataset"]["locked_final_access"])
        self.assertEqual(spec["matched_run_config"]["epochs"], 3)
        seeds = {row["match_seed"] for row in development_schedule()}
        self.assertEqual(len(seeds), 40)
        self.assertTrue(min(seeds) >= 35_000_000)

    def test_panel_rejects_changed_epoch_or_objective_arm(self):
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        spec["matched_run_config"]["epochs"] = 2
        with self.assertRaisesRegex(ValueError, "differs from the frozen panel"):
            _validate_spec(spec)

    def test_output_cannot_overlap_audited_dataset(self):
        with self.assertRaisesRegex(ValueError, "disjoint from the audited dataset"):
            run_panel(DATASET_ROOT, Path("unused-approval.json"), DATASET_ROOT)
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        spec["variants"][0] = "other-objective"
        with self.assertRaisesRegex(ValueError, "differs from the frozen panel"):
            _validate_spec(spec)
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        spec["selection_rule"] = "post-hoc selection"
        with self.assertRaisesRegex(ValueError, "differs from the frozen panel"):
            _validate_spec(spec)


if __name__ == "__main__":
    unittest.main()
