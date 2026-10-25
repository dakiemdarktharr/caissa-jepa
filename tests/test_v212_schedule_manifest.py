import unittest
import hashlib
import json

from two_player.v212_model import ARMS
from two_player.v212_schedule_manifest import (
    SCHEDULE_SCHEMA,
    TRAIN_GAMES,
    ValidatedScheduleManifest,
    scheduled_batch_payload_sha256,
    validate_and_freeze_schedule_manifest,
    validate_schedule_manifest,
)


def _mask_counts():
    return {
        str(horizon): {
            "valid_nonterminal": 32,
            "terminal_masked": 0,
            "missing_or_truncated": 32,
            "invalid_transition": 0,
        }
        for horizon in (1, 2, 4)
    }


def _synthetic_manifest():
    seeds = []
    for seed_ordinal in range(20):
        banks = {
            game: [(game, f"{game}-episode-{index // 32}", index)
                   for index in range(928)]
            for game in TRAIN_GAMES
        }
        updates = []
        for epoch in range(3):
            rotation = (epoch * 128) % 928
            orders = {}
            for game in TRAIN_GAMES:
                bank = banks[game]
                orders[game] = bank[rotation:] + bank[:rotation]
            for batch_index in range(29):
                start = batch_index * 32
                window_ids = (
                    orders[TRAIN_GAMES[0]][start:start + 32]
                    + orders[TRAIN_GAMES[1]][start:start + 32]
                )
                window_records = [
                    (
                        identity,
                        hashlib.sha256(json.dumps(
                            identity, separators=(",", ":"),
                            ensure_ascii=False).encode("utf-8")).hexdigest(),
                    )
                    for identity in window_ids
                ]
                updates.append({
                    "update_index": epoch * 29 + batch_index + 1,
                    "epoch_index": epoch,
                    "batch_index": batch_index,
                    "window_ids": [
                        {
                            "id": list(identity),
                            "payload_sha256": payload_sha256,
                        }
                        for identity, payload_sha256 in window_records
                    ],
                    "batch_payload_sha256": scheduled_batch_payload_sha256(
                        seed_ordinal, epoch * 29 + batch_index + 1,
                        window_records),
                    "mask_counts_by_arm": {
                        arm: _mask_counts() for arm in ARMS
                    },
                })
        seeds.append({
            "seed_ordinal": seed_ordinal,
            "model_seed": 10_000 + seed_ordinal,
            "updates": updates,
        })
    return {"schema": SCHEDULE_SCHEMA, "seeds": seeds}


def _refresh_batch_digest(seed_record, update):
    records = [
        (tuple(record["id"]), record["payload_sha256"])
        for record in update["window_ids"]
    ]
    update["batch_payload_sha256"] = scheduled_batch_payload_sha256(
        seed_record["seed_ordinal"], update["update_index"], records)


class V212ScheduleManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _synthetic_manifest()

    def test_full_synthetic_schedule_has_expected_roster_and_digest(self):
        receipt = validate_schedule_manifest(self.manifest)
        self.assertEqual(receipt["seed_count"], 20)
        self.assertEqual(receipt["updates_per_seed"], 87)
        self.assertEqual(receipt["windows_per_game_per_epoch"], 928)
        self.assertEqual(receipt["mask_rows"], 20 * 87 * 6 * 3)
        self.assertEqual(len(receipt["schedule_sha256"]), 64)

    def test_previous_schema_version_is_rejected(self):
        manifest = dict(self.manifest, schema="caissa.v212.training-schedule.v02")
        with self.assertRaisesRegex(ValueError, "unsupported schedule manifest schema"):
            validate_schedule_manifest(manifest)

    def test_validated_schedule_snapshot_is_detached_and_immutable(self):
        frozen = validate_and_freeze_schedule_manifest(self.manifest)
        original_seed = self.manifest["seeds"][0]["model_seed"]
        self.manifest["seeds"][0]["model_seed"] += 99
        self.assertEqual(frozen.seeds[0]["model_seed"], original_seed)
        self.manifest["seeds"][0]["model_seed"] = original_seed
        with self.assertRaises(TypeError):
            frozen.seeds[0]["model_seed"] = 1
        with self.assertRaises(TypeError):
            frozen.seeds[0]["updates"][0]["update_index"] = 99
        self.assertEqual(len(frozen.schedule_sha256), 64)

    def test_validated_snapshot_cannot_be_forged_with_caller_rows_or_digest(self):
        with self.assertRaises(TypeError):
            ValidatedScheduleManifest("a" * 64, ())
        with self.assertRaisesRegex(ValueError, "exactly 20 paired seed records"):
            ValidatedScheduleManifest({"schema": SCHEDULE_SCHEMA, "seeds": []})

    def test_missing_update_and_misplaced_update_are_rejected(self):
        updates = self.manifest["seeds"][0]["updates"]
        first, second = updates[0], updates[1]
        updates[0], updates[1] = second, first
        try:
            with self.assertRaisesRegex(ValueError, "chronological index order"):
                validate_schedule_manifest(self.manifest)
        finally:
            updates[0], updates[1] = first, second

        removed = updates.pop()
        try:
            with self.assertRaisesRegex(ValueError, "exactly 87 updates"):
                validate_schedule_manifest(self.manifest)
        finally:
            updates.append(removed)

        update = updates[0]
        old_epoch = update["epoch_index"]
        update["epoch_index"] = 1
        try:
            with self.assertRaisesRegex(ValueError, "epoch/batch boundary"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["epoch_index"] = old_epoch

    def test_per_batch_composition_duplicates_and_direct_leaf_h4_fail(self):
        seed_record = self.manifest["seeds"][0]
        update = seed_record["updates"][0]
        original_ids = update["window_ids"]
        original_digest = update["batch_payload_sha256"]
        wrong_mix = [dict(row, id=row["id"][:]) for row in original_ids]
        wrong_mix[0]["id"][0] = TRAIN_GAMES[1]
        update["window_ids"] = wrong_mix
        _refresh_batch_digest(seed_record, update)
        try:
            with self.assertRaisesRegex(ValueError, "32 windows per game"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["window_ids"] = original_ids
            update["batch_payload_sha256"] = original_digest

        duplicate_ids = [dict(row, id=row["id"][:]) for row in original_ids]
        duplicate_ids[1] = dict(duplicate_ids[0], id=duplicate_ids[0]["id"][:])
        update["window_ids"] = duplicate_ids
        _refresh_batch_digest(seed_record, update)
        try:
            with self.assertRaisesRegex(ValueError, "duplicate window ids"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["window_ids"] = original_ids
            update["batch_payload_sha256"] = original_digest

        leaf_counts = update["mask_counts_by_arm"]["direct-leaf-value"]["4"]
        previous_valid = leaf_counts["valid_nonterminal"]
        previous_missing = leaf_counts["missing_or_truncated"]
        leaf_counts["valid_nonterminal"] = 0
        leaf_counts["missing_or_truncated"] = 64
        try:
            with self.assertRaisesRegex(ValueError, "no valid nonterminal H4"):
                validate_schedule_manifest(self.manifest)
        finally:
            leaf_counts["valid_nonterminal"] = previous_valid
            leaf_counts["missing_or_truncated"] = previous_missing

    def test_mask_rows_must_match_for_all_arms(self):
        update = self.manifest["seeds"][0]["updates"][0]
        counts = update["mask_counts_by_arm"]["single-pair-jepa"]["1"]
        previous = counts["valid_nonterminal"]
        previous_missing = counts["missing_or_truncated"]
        counts["valid_nonterminal"] = previous - 1
        counts["missing_or_truncated"] = previous_missing + 1
        try:
            with self.assertRaisesRegex(ValueError, "identical per-horizon mask"):
                validate_schedule_manifest(self.manifest)
        finally:
            counts["valid_nonterminal"] = previous
            counts["missing_or_truncated"] = previous_missing

    def test_mask_counts_reject_unclassified_rows_and_invalid_transitions(self):
        counts = self.manifest["seeds"][0]["updates"][0]["mask_counts_by_arm"]
        horizon = counts["multi-step-jepa"]["1"]
        original = dict(horizon)
        horizon["missing_or_truncated"] = 0
        try:
            with self.assertRaisesRegex(ValueError, "classify all 64"):
                validate_schedule_manifest(self.manifest)
        finally:
            horizon.update(original)

        horizon["invalid_transition"] = 1
        try:
            with self.assertRaisesRegex(ValueError, "invalid selected transitions"):
                validate_schedule_manifest(self.manifest)
        finally:
            horizon.update(original)

    def test_model_seed_roster_must_be_distinct_and_nonnegative(self):
        first, second = self.manifest["seeds"][0], self.manifest["seeds"][1]
        original = second["model_seed"]
        second["model_seed"] = first["model_seed"]
        try:
            with self.assertRaisesRegex(ValueError, "seeds must be distinct"):
                validate_schedule_manifest(self.manifest)
        finally:
            second["model_seed"] = original

        second["model_seed"] = -1
        try:
            with self.assertRaisesRegex(ValueError, "nonnegative integer"):
                validate_schedule_manifest(self.manifest)
        finally:
            second["model_seed"] = original

    def test_selected_window_bank_cannot_change_between_epochs(self):
        seed_record = self.manifest["seeds"][0]
        update = seed_record["updates"][29]
        original = update["window_ids"][0]
        original_digest = update["batch_payload_sha256"]
        update["window_ids"][0] = dict(original, payload_sha256="0" * 64)
        _refresh_batch_digest(seed_record, update)
        try:
            with self.assertRaisesRegex(ValueError, "bank changed across epochs"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["window_ids"][0] = original
            update["batch_payload_sha256"] = original_digest

    def test_payload_digest_must_be_sha256_and_stable_for_each_window_id(self):
        update = self.manifest["seeds"][0]["updates"][0]
        original = update["window_ids"][0]
        update["window_ids"][0] = dict(original, payload_sha256="bad")
        try:
            with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["window_ids"][0] = original

    def test_declared_batch_digest_must_bind_schedule_identity_and_payloads(self):
        update = self.manifest["seeds"][0]["updates"][0]
        original = update["batch_payload_sha256"]
        update["batch_payload_sha256"] = "0" * 64
        try:
            with self.assertRaisesRegex(ValueError, "does not match its ordered records"):
                validate_schedule_manifest(self.manifest)
        finally:
            update["batch_payload_sha256"] = original


if __name__ == "__main__":
    unittest.main()
