import unittest

from tools.v28_reversi4_rules_gate import audit, reference_legal_actions, reference_transition
from two_player.games import BoardGame


class Reversi4RulesGateTests(unittest.TestCase):
    def test_independent_reference_finds_initial_moves_and_pass_behavior(self):
        game = BoardGame("test-reversi4", 4, 4, 0, reversi=True)
        initial = game.initial()
        self.assertEqual(reference_legal_actions(initial), game.legal_actions(initial))
        self.assertEqual(reference_legal_actions(initial), (1, 8, 19, 26))
        with self.assertRaisesRegex(ValueError, "illegal reference action"):
            reference_transition(initial, 64)

    def test_bounded_reachable_rules_and_two_ply_closure(self):
        receipt = audit(state_limit=1000)
        coverage = receipt["coverage"]
        self.assertGreater(coverage["reachable_states_including_terminal"], 1)
        self.assertGreater(coverage["transitions_differentially_checked"], 0)
        self.assertGreater(coverage["complete_two_ply_reply_pairs"], 0)
        self.assertEqual(receipt["checks"]["all_reachable_legal_transitions"], "pass")
        self.assertFalse(coverage["complete_enumeration"])
        self.assertFalse(receipt["training_started"])
        self.assertFalse(receipt["data_generated"])


if __name__ == "__main__":
    unittest.main()
