import json
import unittest
from pathlib import Path

from tools.v28_run_development_panel import SPEC_PATH, _validate_spec


class V28DevelopmentPanelTests(unittest.TestCase):
    def test_frozen_development_panel_spec_is_exact_and_preoutcome(self):
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        _validate_spec(spec)
        self.assertEqual(spec["development_match_schedule"]["block_count"], 160)
        self.assertFalse(spec["dataset"]["locked_final_access"])

    def test_panel_rejects_changed_epoch_or_objective_arm(self):
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        spec["matched_run_config"]["epochs"] = 2
        with self.assertRaisesRegex(ValueError, "differs from the frozen panel"):
            _validate_spec(spec)
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        spec["variants"][0] = "other-objective"
        with self.assertRaisesRegex(ValueError, "differs from the frozen panel"):
            _validate_spec(spec)


if __name__ == "__main__":
    unittest.main()
