import sys
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import v29_model_match
from tools import v29_development_match_analysis as analysis


class V29DevelopmentMatcherTests(unittest.TestCase):
    def test_analyzer_pins_evaluator_and_rules_sources(self):
        root = Path(__file__).resolve().parents[1]
        matcher_hash = hashlib.sha256(
            (root / "tools" / "v29_model_match.py").read_bytes()).hexdigest()
        rules_hash = hashlib.sha256(
            (root / "two_player" / "games.py").read_bytes()).hexdigest()
        self.assertEqual(matcher_hash, analysis.MATCHER_SOURCE_SHA256)
        self.assertEqual(rules_hash, analysis.GAME_RULES_SOURCE_SHA256)

    def test_locked_schedule_access_is_blocked(self):
        with patch.object(sys, "argv", ["v29_model_match.py", "unused", "unused.jsonl"]):
            with self.assertRaises(SystemExit) as raised:
                v29_model_match.main()
        self.assertEqual(raised.exception.code, 2)

    def test_callable_confirmatory_api_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "blocks locked V08"):
            v29_model_match.run_schedule([], {}, "unused.jsonl", confirmatory=True)


if __name__ == "__main__":
    unittest.main()
