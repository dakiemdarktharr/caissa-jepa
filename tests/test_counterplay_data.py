"""Synthetic contract/reference checks; no accepted corpus or fitted model."""
import copy
import unittest

import numpy as np

from benchmarks.reference_rules import ReferenceBudgetExceeded
from counterplay.data import (GAMES, audit_state, build, candidate_root,
                             critical_pair, generate_episode, model_batch,
                             replay_episode, selected_windows, solved_fork,
                             state_from)
from two_player.games import BoardGame, exact_value


class CounterplayDataTests(unittest.TestCase):
    def test_seed_role_identity_replay_and_corruption(self):
        for game in GAMES.values():
            e = generate_episode(game, 191, "train", 0)
            self.assertEqual(e, generate_episode(game, 191, "train", 0))
            other = generate_episode(game, 191, "development", 0)
            self.assertNotEqual(e["seed"], other["seed"])
            states, compared = replay_episode(e)
            self.assertGreater(compared, 0)
            self.assertEqual(game.terminal(states[-1]), e["outcome"])
            broken = copy.deepcopy(e)
            broken["outcome"] = 1 if e["outcome"] != 1 else -1
            with self.assertRaisesRegex(ValueError, "outcome"):
                replay_episode(broken)
            broken = copy.deepcopy(e)
            broken["actions"][0] = -1
            with self.assertRaises(ValueError):
                replay_episode(broken)
        with self.assertRaisesRegex(ValueError, "locked"):
            generate_episode(GAMES["reversi6"], 191, "locked", 0)

    def test_full_fork_values_match_independent_traversal(self):
        game = BoardGame("fixture-ttt", 3, 3)
        state = game.initial()
        for a in (0, 8, 1):
            state = game.transition(state, a)
        result = solved_fork(game, state, seconds=5.0)
        self.assertEqual(result["reference_class"], "terminal-solved")
        seen = set()
        for row in result["rows"]:
            first = game.transition(state, row["a"])
            if row["b"] is None:
                value = state.player * game.terminal(first)
            else:
                child = game.transition(first, row["b"])
                value = exact_value(game, child)
                self.assertEqual(child.player, state.player)
            self.assertEqual(row["q"], value)
            seen.add((row["a"], row["b"]))
        expected = set()
        for a in game.legal_actions(state):
            child = game.transition(state, a)
            if game.terminal(child) is not None:
                expected.add((a, None))
            else:
                expected.update((a, b) for b in game.legal_actions(child))
        self.assertEqual(seen, expected)
        with self.assertRaises((TimeoutError, ReferenceBudgetExceeded)):
            solved_fork(game, game.initial(), node_cap=1, seconds=5.0)

    def test_critical_selection_requires_nonterminal_pair_and_is_reference_only(self):
        def r(a, b, q, terminal=False):
            return {"a": a, "b": b, "q": q, "terminal": terminal}
        rows = [r(0, 1, -1, True), r(0, 2, 1),
                r(1, 3, -1), r(1, 4, 1), r(1, 5, 1), r(2, None, 0, True)]
        self.assertEqual(critical_pair(rows), {"a": 1, "b": 3, "controls": [4, 5]})
        rows[3]["terminal"] = rows[4]["terminal"] = True
        self.assertIsNone(critical_pair(rows))
        # A tied worst reply cannot qualify as a unique critical reply.
        self.assertIsNone(critical_pair([r(0, 1, -1), r(0, 2, -1), r(1, None, 0)]))

    def test_window_deduplication_isolation_target_perspectives_and_masks(self):
        game = GAMES["reversi6"]
        e = generate_episode(game, 731, "train", 0)
        windows, counts = selected_windows([e, e], set(), 32, 731)
        self.assertGreater(len(windows), 0)
        self.assertGreater(counts["within_role_content_duplicate"], 0)
        self.assertEqual(len({w["content_id"] for w in windows}), len(windows))
        self.assertTrue(all(len(w["source_ids"]) == 2 for w in windows))
        forbidden = game.canonical_key(state_from(windows[0]["states"][2]))
        clean, counts = selected_windows([e], {forbidden}, 32, 731)
        self.assertGreater(counts["eval_root_collision"], 0)
        self.assertTrue(all(game.canonical_key(state_from(s)) != forbidden
                            for w in clean for s in w["states"]))
        seen = {w["content_id"] for w in windows}
        other, counts = selected_windows([e], set(), 32, 731, seen)
        self.assertEqual(other, [])
        self.assertGreater(counts["cross_role_content_collision"], 0)
        # Repeated rows here are a synthetic adapter fixture, never a schedule.
        batch = model_batch([windows[0]] * 64)
        self.assertTrue(batch["transition_valid"].all())
        self.assertFalse(batch["terminal"].any())
        w = windows[0]
        expected = np.array([s["player"] * w["outcome"] for s in w["states"][1:]])
        np.testing.assert_array_equal(batch["future_value"][0], expected)
        self.assertEqual(batch["value"][0], w["states"][0]["player"] * w["outcome"])
        broken = copy.deepcopy(w)
        broken["actions"][0] = -1
        with self.assertRaises(ValueError):
            model_batch([broken] * 64)

    def test_root_selection_and_tiny_build_are_deterministic_and_accounted(self):
        e = generate_episode(GAMES["reversi6"], 137, "development", 0)
        self.assertEqual(candidate_root(e, 137, 6), candidate_root(e, 137, 6))
        data = build(137, train_episodes=1, development_episodes=1,
                     train_cap=32, development_cap=32, cpu_seconds=30)
        self.assertFalse(data["reference_yield_gate"])
        self.assertEqual(sum(x["generated_episodes"] for x in data["audit"].values()), 4)
        for root in data["roots"]:
            self.assertIn(root["status"], ("complete", "failed"))
            self.assertTrue(all(GAMES[w["game"]].canonical_key(state_from(s)) != root["root_id"]
                                for bank in data["windows"].values() for w in bank for s in w["states"]))
        with self.assertRaises(TimeoutError):
            build(137, cpu_seconds=1e-12)

    def test_forced_pass_consumes_transition_and_terminal_has_no_legal_action(self):
        game = GAMES["reversi6"]
        from two_player.games import State
        state = State((0, 1, -1, -1, -1, -1) + (-1,) * 30)
        self.assertEqual(game.legal_actions(state), (64,))
        self.assertEqual(audit_state(game, state), 1)
        child = game.transition(state, 64)
        self.assertEqual(child.player, -state.player)
        terminal = game.transition(child, 0)
        self.assertEqual(game.legal_actions(terminal), ())
        self.assertEqual(game.terminal(terminal), -1)


if __name__ == "__main__":
    unittest.main()
