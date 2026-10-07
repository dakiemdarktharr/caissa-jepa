import random
import unittest
from types import SimpleNamespace

from tests.test_v212_schedule_manifest import (
    _refresh_batch_digest,
    _synthetic_manifest,
)
from two_player.games import BoardGame
from two_player.v212_model import ARMS, preflight_batch
from two_player.v212_schedule_manifest import validate_and_freeze_schedule_manifest
from two_player.v212_receipt_bound_schedule import (
    ReceiptBoundBatchResult,
    build_train_replay_receipt_index,
    compute_receipt_bound_panel_batch,
    validate_actual_mask_roster,
    validate_window_receipt_binding,
)
from two_player.v212_trajectory_audit import (
    Window,
    audit_trajectories,
    window_payload_sha256,
)
from two_player.v212_window_batch import windows_to_model_batch


def _terminal_train_episode(game, episode_id, seed, min_plies=32):
    """Create a seeded legal fixture episode long enough for 32 windows."""
    for offset in range(512):
        rng = random.Random(seed + offset)
        states = [game.initial()]
        actions = []
        while game.terminal(states[-1]) is None:
            legal = game.legal_actions(states[-1])
            if len(actions) < min_plies:
                safe = [action for action in legal
                        if game.terminal(game.transition(states[-1], action)) is None]
                if not safe:
                    break
                action = rng.choice(safe)
            else:
                action = rng.choice(legal)
            actions.append(action)
            states.append(game.transition(states[-1], action))
        outcome = game.terminal(states[-1])
        if len(actions) >= min_plies and outcome is not None:
            return {
                "game": game.name,
                "episode_id": episode_id,
                "split": "train",
                "states": tuple(states),
                "actions": tuple(actions),
                "outcome": outcome,
            }
    raise AssertionError(f"could not construct a {min_plies}-ply {game.name} fixture")


def _manifest_with_receipted_fixture_batch(games):
    episodes = [
        _terminal_train_episode(games["connect4-gravity-6x7"], "fixture-c4-long", 401),
        _terminal_train_episode(games["reversi6"], "fixture-reversi-long", 701),
    ]
    audited = audit_trajectories(episodes, games)
    selected = {
        game_name: [window for window in audited.windows if window.game == game_name][:32]
        for game_name in games
    }
    if any(len(rows) != 32 for rows in selected.values()):
        raise AssertionError("fixture episodes must yield 32 windows per game")
    windows = selected["connect4-gravity-6x7"] + selected["reversi6"]
    receipt_index = build_train_replay_receipt_index(episodes, games)
    replacement_records = {}
    for game_name, rows in selected.items():
        for window in rows:
            identity = (window.game, window.episode_id, window.start_ply)
            replacement_records[identity] = {
                "id": list(identity),
                "payload_sha256": window_payload_sha256(window, games[game_name]),
            }

    raw_manifest = _synthetic_manifest()
    seed = raw_manifest["seeds"][0]
    first_update = seed["updates"][0]
    old_records = first_update["window_ids"]
    replacement_by_old_id = {
        tuple(old["id"]): replacement_records[tuple(window_id)]
        for old, window_id in zip(
            old_records,
            [(window.game, window.episode_id, window.start_ply) for window in windows],
        )
    }

    # Replace the same 64 bank members in each epoch to preserve the frozen
    # per-game 928-window roster and cross-epoch identity constraints.
    for update in seed["updates"]:
        changed = False
        for index, record in enumerate(update["window_ids"]):
            replacement = replacement_by_old_id.get(tuple(record["id"]))
            if replacement is not None:
                update["window_ids"][index] = dict(replacement)
                changed = True
        if changed:
            _refresh_batch_digest(seed, update)

    first_update = seed["updates"][0]
    batch = windows_to_model_batch(windows, games)
    actual_masks = {
        str(horizon): {field: int(value) for field, value in batch_masks.items()}
        for horizon, batch_masks in preflight_batch(batch)["counts"].items()
    }
    first_update["mask_counts_by_arm"] = {
        arm: actual_masks for arm in ARMS
    }
    _refresh_batch_digest(seed, first_update)
    return raw_manifest, receipt_index, windows, games, actual_masks


def _mask_counts(h4=32):
    return {
        str(horizon): {
            "valid_nonterminal": h4 if horizon == 4 else 32,
            "terminal_masked": 0,
            "missing_or_truncated": 64 - (h4 if horizon == 4 else 32),
            "invalid_transition": 0,
        }
        for horizon in (1, 2, 4)
    }


class V212ReceiptBoundScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = BoardGame("fixture-c4", 4, 4, k=3, gravity=True)
        actions = (24, 25, 16, 17, 8)
        states = [cls.game.initial()]
        for action in actions:
            states.append(cls.game.transition(states[-1], action))
        cls.episode = {
            "game": cls.game.name,
            "episode_id": "bound-fixture",
            "split": "train",
            "states": tuple(states),
            "actions": actions,
            "outcome": 1,
        }
        cls.audit = audit_trajectories([cls.episode], {cls.game.name: cls.game})

    def test_train_receipt_index_binds_every_audited_window(self):
        index = build_train_replay_receipt_index(
            [self.episode], {self.game.name: self.game})
        self.assertEqual(set(index.episode_receipt_sha256),
                         {(self.game.name, "bound-fixture")})
        self.assertEqual(index.audited_window_count, len(self.audit.windows))
        self.assertEqual(len(index.window_records), len(self.audit.windows))
        receipt_sha256 = index.episode_receipt_sha256[(self.game.name, "bound-fixture")]
        for window in self.audit.windows:
            identity = (window.game, window.episode_id, window.start_ply)
            self.assertEqual(
                index.window_records[identity]["episode_receipt_sha256"], receipt_sha256,
            )

    def test_ordered_schedule_records_must_match_receipted_payloads(self):
        receipt_index = build_train_replay_receipt_index(
            [self.episode], {self.game.name: self.game})
        window = self.audit.windows[0]
        identity = (window.game, window.episode_id, window.start_ply)
        record = {
            "id": identity,
            "payload_sha256": receipt_index.window_records[identity]["payload_sha256"],
        }
        records = [record] * 64
        windows = [window] * 64
        hashes = validate_window_receipt_binding(
            records, windows, receipt_index.window_records,
            receipt_index.episode_receipt_sha256,
            {self.game.name: self.game})
        self.assertEqual(len(hashes), 64)
        self.assertEqual(
            hashes[0], receipt_index.episode_receipt_sha256[(self.game.name, "bound-fixture")],
        )

        wrong = dict(record, payload_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "payload differs"):
            validate_window_receipt_binding(
                [wrong] + records[1:], windows, receipt_index.window_records,
                receipt_index.episode_receipt_sha256,
                {self.game.name: self.game})

        misbound_index = {
            identity: {
                "payload_sha256": receipt_index.window_records[identity]["payload_sha256"],
                "episode_receipt_sha256": "f" * 64,
            }
        }
        with self.assertRaisesRegex(ValueError, "parent episode receipt"):
            validate_window_receipt_binding(
                records, windows, misbound_index,
                receipt_index.episode_receipt_sha256,
                {self.game.name: self.game})

    def test_actual_masks_must_match_all_arms_and_direct_leaf_h4(self):
        declared = {arm: _mask_counts() for arm in ARMS}
        validate_actual_mask_roster(declared, _mask_counts())

        altered = {arm: _mask_counts() for arm in ARMS}
        altered["recursive-raw-state"]["2"]["valid_nonterminal"] -= 1
        altered["recursive-raw-state"]["2"]["missing_or_truncated"] += 1
        with self.assertRaisesRegex(ValueError, "differ from replayed batch"):
            validate_actual_mask_roster(altered, _mask_counts())

        no_h4 = {arm: _mask_counts(h4=0) for arm in ARMS}
        with self.assertRaisesRegex(ValueError, "direct-leaf update"):
            validate_actual_mask_roster(no_h4, _mask_counts(h4=0))

    def test_nontrain_episode_collection_is_rejected(self):
        dev_episode = dict(self.episode, split="development")
        with self.assertRaisesRegex(ValueError, "train episodes only"):
            build_train_replay_receipt_index(
                [dev_episode], {self.game.name: self.game})

    def test_receipt_bound_call_routes_through_real_paired_call_boundary(self):
        games = {
            "connect4-gravity-6x7": BoardGame(
                "connect4-gravity-6x7", 6, 7, k=4, gravity=True),
            "reversi6": BoardGame(
                "reversi6", 6, 6, k=0, reversi=True),
        }
        raw_manifest, receipt_index, windows, games, actual_masks = (
            _manifest_with_receipted_fixture_batch(games)
        )
        manifest = validate_and_freeze_schedule_manifest(raw_manifest)
        update = manifest.seeds[0]["updates"][0]
        model_seed = manifest.seeds[0]["model_seed"]
        seen_batches = []

        def fake_loss_grad(arm):
            def run(model_batch):
                self.assertFalse(model_batch["x"].flags.writeable)
                seen_batches.append((arm, model_batch))
                return {"arm": arm}, {}
            return run

        models = {
            arm: SimpleNamespace(
                config=SimpleNamespace(arm=arm, seed=model_seed),
                loss_grad=fake_loss_grad(arm),
            )
            for arm in ARMS
        }

        result = compute_receipt_bound_panel_batch(
            manifest, receipt_index, windows, games, models,
            seed_ordinal=0, update_index=1,
        )
        self.assertIsInstance(result, ReceiptBoundBatchResult)
        self.assertEqual(result.schedule_sha256, manifest.schedule_sha256)
        self.assertEqual(result.scheduled.batch_payload_sha256,
                         update["batch_payload_sha256"])
        self.assertEqual(update["mask_counts_by_arm"][ARMS[0]], actual_masks)
        self.assertEqual(set(result.scheduled.by_arm), set(ARMS))
        self.assertEqual([arm for arm, _ in seen_batches], list(ARMS))
        self.assertTrue(all(model_batch is seen_batches[0][1]
                            for _, model_batch in seen_batches))
        self.assertEqual(
            result.ordered_episode_receipt_sha256,
            tuple(dict.fromkeys(
                receipt_index.window_records[(window.game, window.episode_id,
                                              window.start_ply)]
                ["episode_receipt_sha256"] for window in windows
            )),
        )


if __name__ == "__main__":
    unittest.main()
