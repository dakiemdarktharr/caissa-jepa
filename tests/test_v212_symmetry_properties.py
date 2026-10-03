"""Software-contract checks for the V2.12 in-scope spatial transforms.

These deterministic fixtures test adapter rules only. They do not generate or
save a development-root schedule, labels, match outcomes, or training data.
"""

import unittest

from two_player.games import State
from two_player.v212_pilot import VARIANTS


def _fixed_legal_path(game, choose_action):
    """Replay a deterministic legal path in memory, including its terminal state."""
    state = game.initial()
    states = [state]
    while game.terminal(state) is None:
        actions = game.legal_actions(state)
        action = choose_action(actions, len(states))
        state = game.transition(state, action)
        states.append(state)
    return states


def _pass_fixture(game):
    """A hand-built Reversi rules fixture where +1 must pass and -1 can move."""
    board = [1] * (game.rows * game.cols)
    board[0] = 0
    board[1] = 1
    board[2] = -1
    return State(tuple(board), player=1)


class V212SymmetryProperties(unittest.TestCase):
    def assert_transform_properties(self, game, states):
        identity = tuple(range(game.rows * game.cols))
        transforms = game.transforms()
        self.assertIn(identity, transforms, game.name)

        for map_index, mapping in enumerate(transforms):
            with self.subTest(game=game.name, mapping=map_index):
                self.assertEqual(len(mapping), game.rows * game.cols)
                self.assertEqual(set(mapping), set(range(game.rows * game.cols)))

                for state in states:
                    game.validate(state)
                    role_swapped = State(
                        tuple(-piece for piece in state.board), -state.player
                    )
                    self.assertEqual(
                        game.canonical_key(role_swapped),
                        game.canonical_key(state),
                    )
                    terminal = game.terminal(state)
                    probe_action = game.legal_actions(state)
                    probe_action = probe_action[0] if probe_action else 64
                    mapped_state, _ = game.transform(state, probe_action, mapping)
                    self.assertEqual(game.terminal(mapped_state), terminal)
                    self.assertEqual(
                        game.canonical_key(mapped_state), game.canonical_key(state)
                    )

                    actions = game.legal_actions(state)
                    mapped_actions = [
                        game.transform(state, action, mapping)[1]
                        for action in actions
                    ]
                    self.assertEqual(len(mapped_actions), len(set(mapped_actions)))
                    self.assertEqual(set(mapped_actions), set(game.legal_actions(mapped_state)))

                    for action, mapped_action in zip(actions, mapped_actions):
                        successor = game.transition(state, action)
                        transformed_successor, _ = game.transform(
                            successor, action, mapping
                        )
                        self.assertEqual(
                            game.transition(mapped_state, mapped_action),
                            transformed_successor,
                        )

    def test_declared_maps_preserve_rules_on_fixed_legal_paths(self):
        selectors = (
            lambda actions, _ply: min(actions),
            lambda actions, _ply: max(actions),
            lambda actions, ply: actions[(ply * 7) % len(actions)],
        )
        for game in VARIANTS:
            states = []
            for selector in selectors:
                states.extend(_fixed_legal_path(game, selector))
            with self.subTest(game=game.name):
                self.assert_transform_properties(game, states)

    def test_reversi_pass_is_fixed_and_transition_commutes(self):
        for game in VARIANTS:
            if not game.reversi:
                continue
            state = _pass_fixture(game)
            self.assertEqual(game.legal_actions(state), (64,))
            self.assertEqual(game.legal_actions(State(state.board, player=-1)), (0,))
            self.assert_transform_properties(game, [state])
            for mapping in game.transforms():
                mapped_state, mapped_pass = game.transform(state, 64, mapping)
                self.assertEqual(mapped_pass, 64)
                self.assertEqual(
                    game.transition(mapped_state, 64),
                    State(mapped_state.board, -1),
                )


if __name__ == "__main__":
    unittest.main()
