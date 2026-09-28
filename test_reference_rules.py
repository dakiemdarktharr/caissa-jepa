"""Bounded differential rules validation; no research dataset/model predictions.

The reference is a separately written same-project implementation, not an
external engine. This suite prints coverage counts for a reproducible receipt.
"""
import ast
import hashlib
import json
from pathlib import Path
import random
import time
import unittest

from benchmarks.reference_rules import (PASS, ReferenceGame, ReferenceState,
                                       ReferenceSolver, ReferenceBudgetExceeded)
from two_player.games import GAMES, BoardGame, State, exact_value


def reference_for(adapter):
    return ReferenceGame(adapter.rows, adapter.cols, adapter.k, adapter.gravity, adapter.reversi)


def adapter_action(game, cell):
    return 64 if cell == PASS else (cell // game.cols) * 8 + cell % game.cols


class ReferenceRulesTests(unittest.TestCase):
    def compare_state(self, adapter, reference, state, counters):
        other = reference.from_board(state.board, state.player)
        terminal = adapter.terminal(state)
        self.assertEqual(reference.terminal(other), terminal)
        actions = reference.legal_actions(other)
        self.assertEqual(tuple(sorted(adapter_action(adapter, a) for a in actions)),
                         tuple(sorted(adapter.legal_actions(state))))
        counters['state_visits'] += 1
        counters['terminal_visits'] += terminal is not None
        counters['forced_pass_visits'] += actions == (PASS,)
        for action in actions:
            expected = adapter.transition(state, adapter_action(adapter, action))
            actual = reference.transition(other, action)
            self.assertEqual(reference.board(actual), expected.board)
            self.assertEqual(actual.player, expected.player)
            counters['compared_transitions'] += 1
        return other

    def test_reversi6_generated_rules_forced_pass_and_endgame_values(self):
        started = time.perf_counter()
        adapter = BoardGame('reference-reversi6-fixture', 6, 6, 0, reversi=True)
        reference = reference_for(adapter)
        self.assertEqual(reference.board(reference.initial()), adapter.initial().board)
        counts = dict(state_visits=0, terminal_visits=0, forced_pass_visits=0,
                      compared_transitions=0, solver_positions=0, solver_nodes=0)
        rng = random.Random(9837306)
        unique = set(); endgames = {}
        for _ in range(120):
            state = adapter.initial()
            for _ply in range(2 * 36 + 3):
                other = self.compare_state(adapter, reference, state, counts)
                unique.add(state)
                legal = reference.legal_actions(other)
                if not legal:
                    break
                if state.board.count(0) <= 6:
                    endgames[state] = None
                child = reference.transition(other, rng.choice(legal))
                state = State(reference.board(child), child.player)
            else:
                self.fail('Reversi6 exceeded finite-length bound')
        solver = ReferenceSolver(reference, node_limit=100_000, time_limit=5.)
        adapter_cache = {}
        for state in list(endgames)[:32]:
            other = reference.from_board(state.board, state.player)
            expected = {a: -exact_value(adapter, adapter.transition(state, a), adapter_cache)
                        for a in adapter.legal_actions(state)}
            actual = {adapter_action(adapter, a): v for a, v in solver.action_values(other).items()}
            self.assertEqual(actual, expected)
            counts['solver_nodes'] += solver.last_stats['nodes']
            self.assertEqual(solver.value(other), max(expected.values()))
            counts['solver_positions'] += 1
        self.assertEqual(counts['solver_positions'], 32)
        self.assertEqual(counts['terminal_visits'], 120)
        self.assertGreater(counts['forced_pass_visits'], 0)
        # Explicit pass and terminal signs, independent of stochastic coverage.
        forced = reference.from_board((0, 1, -1, -1, -1, -1) + (-1,) * 30)
        self.assertEqual(reference.legal_actions(forced), (PASS,))
        self.assertEqual(solver.value(forced), -1)
        after_pass = reference.transition(forced, PASS)
        self.assertEqual(solver.value(after_pass), 1)
        end = reference.transition(after_pass, 0)
        self.assertEqual(reference.terminal(end), -1)
        self.assertEqual(solver.value(end), -1)
        self.assertEqual(reference.legal_actions(end), ())
        counts.update(unique_states=len(unique), seconds=time.perf_counter() - started)
        print('REFERENCE_REVERSI6_COVERAGE ' + json.dumps(counts, sort_keys=True))

    def test_generic_even_reversi_configuration(self):
        for size in (2, 4, 6, 8):
            game = ReferenceGame(size, size, 0, reversi=True)
            state = game.initial()
            self.assertEqual(state.plus.bit_count(), 2)
            self.assertEqual(state.minus.bit_count(), 2)
            self.assertEqual(len(game.board(state)), size * size)
            if size == 2:
                self.assertEqual(game.terminal(state), 0)
            else:
                self.assertEqual(len(game.legal_actions(state)), 4)
        for args in ((5, 5, 0), (4, 6, 0), (6, 6, 3)):
            with self.assertRaises(ValueError):
                ReferenceGame(*args, reversi=True)
        with self.assertRaises(ValueError):
            ReferenceGame(6, 6, 0, gravity=True, reversi=True)

    def test_reference_dependency_isolation_and_rectangular_rules(self):
        path = Path(__file__).parent / 'benchmarks' / 'reference_rules.py'
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or '')
        self.assertTrue(all(not name.startswith(('two_player', 'numpy')) for name in imported))
        rng = random.Random(3071)
        receipt = {}
        for adapter in (BoardGame('rect-placement3', 3, 4, 3),
                        BoardGame('rect-placement4', 3, 4, 4),
                        BoardGame('rect-gravity4', 4, 5, 4, gravity=True)):
            reference = reference_for(adapter)
            counts = dict(state_visits=0, terminal_visits=0, forced_pass_visits=0, compared_transitions=0)
            self.assertEqual(reference.identity()['source_sha256'],
                             hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest())
            for _ in range(80):
                state = adapter.initial()
                while True:
                    other = self.compare_state(adapter, reference, state, counts)
                    legal = reference.legal_actions(other)
                    if not legal:
                        break
                    child = reference.transition(other, rng.choice(legal))
                    state = State(reference.board(child), child.player)
            self.assertEqual(counts['terminal_visits'], 80)
            receipt[adapter.name] = counts
        print('REFERENCE_RECTANGULAR_COVERAGE ' + json.dumps(receipt, sort_keys=True))

    def test_exhaustive_tictactoe_rules_and_values(self):
        adapter = GAMES['tic-tac-toe']; reference = reference_for(adapter)
        pending = [adapter.initial()]; seen = set()
        counts = dict(state_visits=0, terminal_visits=0, forced_pass_visits=0, compared_transitions=0)
        solver = ReferenceSolver(reference); adapter_cache = {}
        while pending:
            state = pending.pop()
            if state in seen:
                continue
            seen.add(state)
            other = self.compare_state(adapter, reference, state, counts)
            self.assertEqual(solver.value(other), exact_value(adapter, state, adapter_cache))
            pending.extend(adapter.transition(state, a) for a in adapter.legal_actions(state))
        self.assertEqual(len(seen), 5478)
        self.assertEqual(counts['terminal_visits'], 958)
        self.assertEqual(solver.value(reference.initial()), 0)
        print('REFERENCE_TTT_COVERAGE ' + json.dumps(counts, sort_keys=True))

    def test_generated_all_games_and_bounded_endgame_solvers(self):
        rng = random.Random(29092026)
        receipt = {}
        for name, adapter in GAMES.items():
            reference = reference_for(adapter)
            self.assertEqual(reference.board(reference.initial()), adapter.initial().board)
            counts = dict(state_visits=0, terminal_visits=0, forced_pass_visits=0,
                          compared_transitions=0, solver_positions=0)
            unique = set(); endgames = {}
            for _ in range(160):
                state = adapter.initial()
                for ply in range(2 * adapter.rows * adapter.cols + 3):
                    self.compare_state(adapter, reference, state, counts)
                    unique.add(state)
                    if adapter.terminal(state) is not None:
                        break
                    if state.board.count(0) <= 5:
                        endgames[state] = None
                    # Generate moves from the reference, not the adapter under test.
                    other = reference.from_board(state.board, state.player)
                    action = rng.choice(reference.legal_actions(other))
                    child = reference.transition(other, action)
                    state = State(reference.board(child), child.player)
                else:
                    self.fail('Generated game exceeded finite-length bound')
            solver = ReferenceSolver(reference, node_limit=100_000, time_limit=5.)
            adapter_cache = {}
            for state in list(endgames)[:32]:
                other = reference.from_board(state.board, state.player)
                expected = {a: -exact_value(adapter, adapter.transition(state, a), adapter_cache)
                            for a in adapter.legal_actions(state)}
                actual = {adapter_action(adapter, a): v for a, v in solver.action_values(other).items()}
                self.assertEqual(actual, expected)
                self.assertEqual(solver.value(other), max(expected.values()))
                counts['solver_positions'] += 1
            counts['unique_states'] = len(unique)
            self.assertEqual(counts['terminal_visits'], 160)
            self.assertGreater(counts['solver_positions'], 0)
            if adapter.reversi:
                self.assertGreater(counts['forced_pass_visits'], 0)
            receipt[name] = counts
        print('REFERENCE_GENERATED_COVERAGE ' + json.dumps(receipt, sort_keys=True))

    def test_pass_terminal_perspective_invalid_states_and_budgets(self):
        game = ReferenceGame(4, 4, 0, reversi=True)
        state = game.from_board((0, 1, -1, -1) + (-1,) * 12)
        self.assertEqual(game.legal_actions(state), (PASS,))
        solver = ReferenceSolver(game)
        self.assertEqual(solver.value(state), -1)
        child = game.transition(state, PASS)
        self.assertEqual(solver.value(child), 1)
        end = game.transition(child, 0)
        self.assertEqual(game.terminal(end), -1)
        self.assertEqual(solver.value(end), -1)
        with self.assertRaises(ValueError):
            game.transition(end, PASS)
        with self.assertRaises(ValueError):
            game.validate(ReferenceState(1, 1))
        with self.assertRaises(ValueError):
            game.validate(ReferenceState(1 << 16, 0))
        with self.assertRaises(ValueError):
            game.transition(state, True)
        tiny = ReferenceGame(3, 3)
        budgeted = ReferenceSolver(tiny, node_limit=1)
        with self.assertRaises(ReferenceBudgetExceeded):
            budgeted.value(tiny.initial())
        self.assertNotIn(tiny.initial(), budgeted.cache)
        self.assertFalse(budgeted.last_stats['complete'])
        terminal = tiny.from_board((1, 1, 1, -1, -1, 0, 0, 0, 0), -1)
        self.assertEqual(ReferenceSolver(tiny, node_limit=1).value(terminal), -1)
        identity = game.identity()
        self.assertEqual(len(identity['source_sha256']), 64)
        self.assertNotEqual(identity['config_sha256'], tiny.identity()['config_sha256'])
        self.assertIn('not a third-party', identity['config']['independence'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
