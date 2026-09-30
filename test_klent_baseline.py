import unittest

import numpy as np

from two_player.klent_baseline import alternating_lambda_returns, regularized_policy_target


class RegularizedPolicyTargetTests(unittest.TestCase):
    def test_matches_direct_legal_action_formula(self):
        policy = np.array([0.2, 0.3, 0.0, 0.5])
        q_values = np.array([0.1, -0.2, 1000.0, 0.4])
        legal = np.array([True, True, False, True])
        alpha, beta = 0.03, 0.1
        actual = regularized_policy_target(policy, q_values, legal, alpha=alpha, beta=beta)
        logits = (q_values[legal] + beta * np.log(policy[legal])) / (alpha + beta)
        expected = np.exp(logits - logits.max())
        expected /= expected.sum()
        np.testing.assert_allclose(actual[legal], expected, rtol=1e-13, atol=1e-15)
        self.assertEqual(actual[2], 0.0)
        self.assertAlmostEqual(float(actual.sum()), 1.0)

    def test_batch_rows_and_constant_q_shift(self):
        policy = np.array([[0.25, 0.75, 0.0], [0.0, 0.4, 0.6]])
        q_values = np.array([[1e4, 9999.0, -1e4], [-1e4, -9999.0, -9998.0]])
        legal = np.array([[True, True, False], [False, True, True]])
        original = regularized_policy_target(policy, q_values, legal)
        shifted = regularized_policy_target(policy, q_values + np.array([[1e4], [-1e4]]), legal)
        np.testing.assert_allclose(original, shifted, rtol=3e-11, atol=2e-14)
        np.testing.assert_allclose(original.sum(axis=-1), 1.0)
        self.assertTrue(np.all(original[~legal] == 0.0))

    def test_single_legal_action_gets_probability_one(self):
        result = regularized_policy_target(
            np.array([0.0, 1.0, 0.0]), np.array([-1e6, 12.0, 1e6]), np.array([False, True, False])
        )
        np.testing.assert_array_equal(result, np.array([0.0, 1.0, 0.0]))

    def test_rejects_empty_mask_bad_policy_and_invalid_regularizers(self):
        with self.assertRaisesRegex(ValueError, "at least one legal"):
            regularized_policy_target([1.0, 0.0], [0.0, 0.0], [False, False])
        with self.assertRaisesRegex(ValueError, "positive probability"):
            regularized_policy_target([1.0, 0.0], [0.0, 0.0], [True, True])
        with self.assertRaisesRegex(ValueError, "zero probability"):
            regularized_policy_target([0.5, 0.5], [0.0, 0.0], [True, False])
        with self.assertRaisesRegex(ValueError, "alpha must be positive"):
            regularized_policy_target([1.0], [0.0], [True], alpha=0.0, beta=0.0)


class AlternatingLambdaReturnTests(unittest.TestCase):
    def setUp(self):
        # Three plies; the last actor wins. Values are from the next player-to-move.
        self.rewards = np.array([0.0, 0.0, 1.0])
        self.next_values = np.array([0.25, -0.5, 999.0])
        self.terminal = np.array([False, False, True])

    def test_lambda_zero_uses_one_step_bootstrap_and_terminal_reward(self):
        result = alternating_lambda_returns(
            self.rewards, self.next_values, self.terminal, lam=0.0, gamma=1.0
        )
        np.testing.assert_allclose(result, [-0.25, 0.5, 1.0])

    def test_lambda_one_is_sign_correct_terminal_monte_carlo(self):
        result = alternating_lambda_returns(
            self.rewards, self.next_values, self.terminal, lam=1.0, gamma=1.0
        )
        np.testing.assert_allclose(result, [1.0, -1.0, 1.0])

    def test_intermediate_lambda_matches_backward_definition(self):
        result = alternating_lambda_returns(
            self.rewards, self.next_values, self.terminal, lam=0.3, gamma=1.0
        )
        # G2=1; G1=-(.7*(-.5)+.3*G2)=.05; G0=-(.7*.25+.3*G1)=-.19.
        np.testing.assert_allclose(result, [-0.19, 0.05, 1.0])

    def test_role_swap_negates_every_return(self):
        original = alternating_lambda_returns(self.rewards, self.next_values, self.terminal, lam=0.4)
        swapped = alternating_lambda_returns(-self.rewards, -self.next_values, self.terminal, lam=0.4)
        np.testing.assert_allclose(swapped, -original)

    def test_terminal_bootstrap_is_ignored(self):
        a = alternating_lambda_returns(self.rewards, self.next_values, self.terminal, lam=0.7)
        changed = self.next_values.copy()
        changed[-1] = -1e200
        b = alternating_lambda_returns(self.rewards, changed, self.terminal, lam=0.7)
        np.testing.assert_array_equal(a, b)

    def test_rejects_truncation_shape_and_nonfinite_values(self):
        with self.assertRaisesRegex(ValueError, "end at a terminal"):
            alternating_lambda_returns([0.0], [0.0], [False])
        with self.assertRaisesRegex(ValueError, "matching vectors"):
            alternating_lambda_returns([0.0, 1.0], [0.0], [False, True])
        with self.assertRaisesRegex(ValueError, "must be finite"):
            alternating_lambda_returns([np.nan], [0.0], [True])


if __name__ == "__main__":
    unittest.main()
