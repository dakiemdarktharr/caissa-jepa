import unittest
from types import SimpleNamespace

from two_player.games import BoardGame
from two_player.v212_model import ARMS
from two_player.v212_scheduled_batch import compute_scheduled_panel_batch
from two_player.v212_trajectory_audit import Window, window_payload_sha256


def _fixture_games():
    return {
        "connect4-gravity-6x7": BoardGame(
            "connect4-gravity-6x7", 6, 7, 4, gravity=True),
        "reversi6": BoardGame("reversi6", 6, 6, 0, reversi=True),
    }


def _window(game, episode_id, start_ply):
    state = game.initial()
    states = [state]
    actions = []
    for _ in range(4):
        action = game.legal_actions(state)[0]
        actions.append(action)
        state = game.transition(state, action)
        states.append(state)
    return Window(
        game=game.name,
        episode_id=episode_id,
        split="train",
        episode_outcome=0,
        start_ply=start_ply,
        states=tuple(states),
        actions=tuple(actions),
        valid_targets=(1, 2, 4),
        terminal_targets=(),
    )


class _SpyModel:
    def __init__(self, arm, seed, calls):
        self.config = SimpleNamespace(arm=arm, seed=seed)
        self.calls = calls

    def loss_grad(self, batch):
        self.calls.append((self.config.arm, batch))
        self.assert_read_only(batch)
        try:
            batch["forbidden"] = None
        except TypeError:
            pass
        else:
            raise AssertionError("scheduled batch mapping must be read-only")
        return {"arm": self.config.arm}, {"sentinel": 0}

    @staticmethod
    def assert_read_only(batch):
        if any(value.flags.writeable for value in batch.values()):
            raise AssertionError("scheduled batch arrays must be read-only")


class V212ScheduledBatchTests(unittest.TestCase):
    def setUp(self):
        self.games = _fixture_games()
        self.windows = tuple(
            [_window(self.games["connect4-gravity-6x7"], f"c4-{i}", i)
             for i in range(32)]
            + [_window(self.games["reversi6"], f"rv-{i}", i)
               for i in range(32)]
        )
        self.calls = []
        self.models = {
            arm: _SpyModel(arm, 2026, self.calls) for arm in ARMS
        }

    def test_one_materialized_batch_is_shared_read_only_by_all_six_arms(self):
        result = compute_scheduled_panel_batch(
            self.windows, self.games, self.models,
            seed_ordinal=0, update_index=1)
        self.assertEqual(tuple(result.by_arm), ARMS)
        self.assertEqual(len(self.calls), 6)
        self.assertEqual({id(batch) for _, batch in self.calls},
                         {id(self.calls[0][1])})
        self.assertEqual(result.seed_ordinal, 0)
        self.assertEqual(result.update_index, 1)
        self.assertEqual(len(result.ordered_window_ids), 64)
        self.assertEqual(len(result.ordered_window_payload_sha256), 64)
        self.assertEqual(len(result.window_order_sha256), 64)
        self.assertEqual(len(result.batch_payload_sha256), 64)
        self.assertEqual(
            result.ordered_window_payload_sha256[0],
            window_payload_sha256(self.windows[0], self.games[self.windows[0].game]))

    def test_window_payload_digest_changes_when_payload_changes(self):
        window = self.windows[0]
        changed = Window(
            game=window.game,
            episode_id=window.episode_id,
            split=window.split,
            episode_outcome=1,
            start_ply=window.start_ply,
            states=window.states,
            actions=window.actions,
            valid_targets=window.valid_targets,
            terminal_targets=window.terminal_targets,
        )
        game = self.games[window.game]
        self.assertNotEqual(window_payload_sha256(window, game),
                            window_payload_sha256(changed, game))

    def test_raw_batch_mapping_cannot_bypass_the_window_adapter(self):
        with self.assertRaisesRegex(ValueError, "64 audited windows"):
            compute_scheduled_panel_batch(
                {"x": "caller-built"}, self.games, self.models,
                seed_ordinal=0, update_index=1)
        self.assertEqual(self.calls, [])

    def test_unbalanced_or_duplicate_window_roster_fails_before_model_calls(self):
        unbalanced = self.windows[:32] + (self.windows[0],) + self.windows[33:]
        with self.assertRaisesRegex(ValueError, "32 windows per game"):
            compute_scheduled_panel_batch(
                unbalanced, self.games, self.models,
                seed_ordinal=0, update_index=1)
        duplicated = self.windows[:-1] + (self.windows[32],)
        with self.assertRaisesRegex(ValueError, "duplicate window identities"):
            compute_scheduled_panel_batch(
                duplicated, self.games, self.models,
                seed_ordinal=0, update_index=1)
        self.assertEqual(self.calls, [])

    def test_seed_update_arm_and_adapter_identity_are_checked(self):
        for kwargs, message in (
            ({"seed_ordinal": 20, "update_index": 1}, "seed ordinal"),
            ({"seed_ordinal": 0, "update_index": 88}, "update index"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                compute_scheduled_panel_batch(
                    self.windows, self.games, self.models, **kwargs)

        mixed_seed = dict(self.models)
        mixed_seed[ARMS[-1]] = _SpyModel(ARMS[-1], 2027, self.calls)
        with self.assertRaisesRegex(ValueError, "paired initialization seed"):
            compute_scheduled_panel_batch(
                self.windows, self.games, mixed_seed,
                seed_ordinal=0, update_index=1)

        wrong_game = dict(self.games)
        wrong_game["reversi6"] = BoardGame("other", 6, 6, 0, reversi=True)
        with self.assertRaisesRegex(ValueError, "adapter identity"):
            compute_scheduled_panel_batch(
                self.windows, wrong_game, self.models,
                seed_ordinal=0, update_index=1)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
