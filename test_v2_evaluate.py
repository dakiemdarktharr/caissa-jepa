"""Evaluator correctness fixtures, never evidence of learned performance."""
import copy
from types import SimpleNamespace
import unittest

import numpy as np

from two_player.games import BoardGame, State, exact_value
from two_player_v2.evaluate import evaluate, plan_root, representation


TTT = BoardGame("fixture", 3, 3, 3)


def root_for(game, state):
    actions = game.legal_actions(state)
    cache = {}
    return {"game": game.name, "trajectory": "fixture-trajectory",
            "root_id": "fixture-root", "split": "development", "beyond_depth": True,
            "state": {"board": list(state.board), "player": state.player},
            "actions": list(actions),
            "oracle_values": [-exact_value(game, game.transition(state, a), cache) for a in actions]}


class OracleModel:
    """Feature-valued latent fixture with exact values and exact legal dynamics."""
    def __init__(self, game, variant="rjepa"):
        self.game = game
        self.config = SimpleNamespace(variant=variant)
        self.calls = 0
        self.cache = {}

    def encode(self, x):
        self.calls += 1
        return np.asarray(x).copy()

    def project(self, z):
        return np.asarray(z)[:, :16]

    def state(self, features):
        board = tuple(int(features[r*8+c]-features[64+r*8+c])
                      for r in range(self.game.rows) for c in range(self.game.cols))
        return State(board, 1)

    def value(self, z):
        self.calls += 1
        return np.asarray([[exact_value(self.game, self.state(row), self.cache)] for row in z], dtype=float)

    def policy_logits(self, z):
        return np.zeros((len(z), 65))

    def rollout(self, z, actions, horizon=2):
        self.calls += 1
        result = []
        for row, moves in zip(z, actions):
            state = self.state(row)
            for h in range(horizon):
                if moves[h].sum() != 1:
                    raise AssertionError("Invalid action supplied to model")
                state = self.game.transition(state, int(moves[h].argmax()))
            result.append(self.game.features(state))
        return np.asarray(result)


class V2EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.state = State((1, 1, 0, -1, -1, 0, 0, 0, 0), 1)
        self.root = root_for(TTT, self.state)
        self.options = {"games": {TTT.name: TTT}, "max_seconds": 30}

    def test_exact_and_hybrid_match_exact_oracle_for_both_players(self):
        states = (self.state, State(tuple(-x for x in self.state.board), -1),
                  State((1, 0, 0, 0, -1, 0, 0, 0, 1), -1))
        for state in states:
            root = root_for(TTT, state)
            for track in ("exact", "hybrid"):
                with self.subTest(state=state, track=track):
                    result = plan_root(root, OracleModel(TTT), track=track, **self.options)
                    self.assertEqual(result["status"], "complete", result)
                    self.assertEqual(result["regret"], 0)
                    self.assertEqual(result["action_estimates"], root["oracle_values"])
                    self.assertGreater(result["neural_leaves"], 0)
                    self.assertEqual(result["nodes"], result["transitions"])

    def test_terminal_override_and_forced_pass_perspectives(self):
        result = plan_root(self.root, None, **self.options)
        self.assertEqual(result["action"], 2)
        self.assertEqual(result["action_estimates"][0], 1)
        self.assertEqual(result["neuralcounts"]["value_calls"], 0)
        game = BoardGame("pass-fixture", 4, 4, 0, reversi=True)
        state = State((0, 1, -1, -1)+(-1,)*12, 1)
        root = root_for(game, state)
        self.assertEqual(root["actions"], [64])
        result = plan_root(root, OracleModel(game), games={game.name: game}, max_seconds=30)
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(result["action_estimates"], [-1.0])
        self.assertEqual(result["regret"], 0)
        self.assertEqual(result["nodes"], 2)
        self.assertEqual(result["neural_leaves"], 0)

    def test_node_boundary_is_inclusive_and_partial_trees_are_not_scored(self):
        full = plan_root(self.root, None, **self.options)
        exact = plan_root(self.root, OracleModel(TTT), max_nodes=full["nodes"], **self.options)
        self.assertEqual(exact["status"], "complete", exact)
        model = OracleModel(TTT)
        partial = plan_root(self.root, model, max_nodes=full["nodes"]-1, **self.options)
        self.assertEqual(partial["status"], "censored")
        self.assertEqual(partial["reason"], "node_budget")
        self.assertEqual(partial["nodes"], full["nodes"]-1)
        self.assertIsNone(partial["action"])
        self.assertIsNone(partial["regret"])
        self.assertEqual(model.calls, 0)

    def test_time_overrun_in_neural_call_is_censored(self):
        elapsed = [0.0]
        model = OracleModel(TTT)
        base_value = model.value

        def slow_value(z):
            answer = base_value(z)
            elapsed[0] = 2.0
            return answer

        model.value = slow_value
        result = plan_root(self.root, model, games={TTT.name: TTT}, max_seconds=1,
                           clock=lambda: elapsed[0])
        self.assertEqual(result["status"], "censored")
        self.assertEqual(result["reason"], "time_budget")
        self.assertIsNone(result["regret"])
        self.assertEqual(result["neuralcounts"]["value_calls"], 1)
        self.assertEqual(result["seconds"], 2)

    def test_direct_hybrid_reencodes_and_failed_rows_preserve_schedule(self):
        model = OracleModel(TTT, variant="direct")
        model.rollout = lambda *args, **kwargs: self.fail("Direct must re-encode")
        result = plan_root(self.root, model, track="hybrid", **self.options)
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(result["neuralcounts"]["rollout_calls"], 0)
        bad = copy.deepcopy(self.root)
        bad["root_id"] = "bad-root"
        bad["actions"].reverse()
        results = evaluate([self.root, bad, self.root], model, **self.options)
        self.assertEqual(len(results), 6)
        self.assertEqual([r["root_id"] for r in results], ["fixture-root"]*2+["bad-root"]*2+["fixture-root"]*2)
        self.assertEqual([r["status"] for r in results], ["complete"]*2+["error"]*2+["complete"]*2)
        self.assertTrue(all(results[i]["regret"] is None for i in (2, 3)))

    def test_selection_final_denied_before_any_predictions(self):
        for split in ("selection", "final", "test", "train"):
            model = OracleModel(TTT)
            forbidden = dict(self.root, split=split)
            with self.assertRaises(ValueError):
                evaluate([self.root, forbidden], model, **self.options)
            self.assertEqual(model.calls, 0)
        allowed = plan_root(dict(self.root, split="train"), None, allow_train=True, **self.options)
        self.assertEqual(allowed["status"], "complete")

    def test_nonfinite_values_fail_closed(self):
        model = OracleModel(TTT)
        model.value = lambda z: np.full((len(z), 1), np.nan)
        result = plan_root(self.root, model, **self.options)
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["regret"])

    def test_representation_soft_policy_terminal_masks_and_horizon_counts(self):
        child = TTT.transition(self.state, 2)
        batch = {"x": np.zeros((1, 3, 198)), "valid": np.array([[True, True, False]]),
                 "legal": np.zeros((1, 3, 65), bool), "policy": np.zeros((1, 3, 65)),
                 "value": np.array([[[1.0], [-1.0], [0.0]]]), "actions": np.zeros((1, 2, 65))}
        batch["x"][0, 0] = TTT.features(self.state)
        batch["x"][0, 1] = TTT.features(child)
        legal = TTT.legal_actions(self.state)
        batch["legal"][0, 0, list(legal)] = True
        batch["policy"][0, 0, 2] = 1
        batch["actions"][0, 0, 2] = 1
        metrics = representation(OracleModel(TTT), batch)
        self.assertEqual(metrics["samples"], 2)
        self.assertEqual(metrics["policy_samples"], 1)
        self.assertEqual(metrics["terminal_samples"], 1)
        self.assertEqual(metrics["missing_states"], 1)
        self.assertAlmostEqual(metrics["policy_nll"], np.log(len(legal)))
        self.assertEqual(metrics["policy_mrr"], 1)
        self.assertEqual(metrics["value_mse"], 0)
        self.assertEqual(metrics["horizons"]["1"]["online_latent_mse"], 0)
        self.assertEqual(metrics["horizons"]["2"]["samples"], 0)
        self.assertIsNone(metrics["horizons"]["2"]["online_latent_mse"])
        self.assertEqual(metrics["projected"]["samples"], 2)
        active_features = batch["x"][batch["valid"]]
        self.assertEqual(metrics["unprojected"]["median_std"], float(np.median(active_features.std(axis=0))))
        self.assertEqual(metrics["projected"]["median_std"], float(np.median(active_features[:, :16].std(axis=0))))
        bad = copy.deepcopy(batch)
        bad["policy"][0, 1, 0] = 1
        with self.assertRaises(ValueError):
            representation(OracleModel(TTT), bad)


if __name__ == "__main__":
    unittest.main()
