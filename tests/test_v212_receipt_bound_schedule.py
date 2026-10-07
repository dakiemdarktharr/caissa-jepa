import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_v212_schedule_manifest import _synthetic_manifest
from two_player.games import BoardGame
from two_player.v212_model import ARMS
from two_player.v212_schedule_manifest import validate_and_freeze_schedule_manifest
from two_player.v212_receipt_bound_schedule import (
    ReceiptBoundBatchResult,
    build_train_replay_receipt_index,
    compute_receipt_bound_panel_batch,
    validate_actual_mask_roster,
    validate_window_receipt_binding,
)
from two_player.v212_trajectory_audit import audit_trajectories


def _mask_counts(h4=32):
    return {
        str(horizon): {
            "valid_nonterminal": h4 if horizon == 4 else 32,
            "terminal_masked": 0,
            "missing_or_truncated": 0,
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

    def test_receipt_bound_call_checks_row_before_no_update_helper(self):
        games = {self.game.name: self.game}
        receipt_index = build_train_replay_receipt_index([self.episode], games)
        window = self.audit.windows[0]
        manifest = validate_and_freeze_schedule_manifest(_synthetic_manifest())
        update = manifest.seeds[0]["updates"][0]
        model_seed = manifest.seeds[0]["model_seed"]
        models = {
            arm: SimpleNamespace(config=SimpleNamespace(arm=arm, seed=model_seed))
            for arm in ARMS
        }
        scheduled = SimpleNamespace(
            batch_payload_sha256=update["batch_payload_sha256"]
        )

        def run_scheduled(*args, pre_model_call=None, **kwargs):
            self.assertTrue(callable(pre_model_call))
            pre_model_call({})
            return scheduled

        with (
            patch("two_player.v212_receipt_bound_schedule.validate_window_receipt_binding",
                  return_value=["b" * 64] * 64),
            patch("two_player.v212_receipt_bound_schedule._observed_mask_counts",
                  return_value=_mask_counts()),
            patch("two_player.v212_receipt_bound_schedule.compute_scheduled_panel_batch",
                  side_effect=run_scheduled),
        ):
            result = compute_receipt_bound_panel_batch(
                manifest, receipt_index, [window] * 64, games, models,
                seed_ordinal=0, update_index=1,
            )
        self.assertIsInstance(result, ReceiptBoundBatchResult)
        self.assertEqual(result.schedule_sha256, manifest.schedule_sha256)
        self.assertEqual(result.scheduled, scheduled)
        self.assertEqual(
            result.ordered_episode_receipt_sha256,
            ("b" * 64,),
        )


if __name__ == "__main__":
    unittest.main()
