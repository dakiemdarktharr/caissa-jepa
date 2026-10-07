"""Pure structural validator for a prospective V2.12 training schedule.

This validates an in-memory manifest object only. It does not load data,
select windows, replay episodes, create schedules, or authorize a profile/fit.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any

from .v212_model import ARMS


SCHEDULE_SCHEMA = "caissa.v212.training-schedule.v02"
TRAIN_GAMES = ("connect4-gravity-6x7", "reversi6")
HORIZONS = (1, 2, 4)
MASK_FIELDS = (
    "valid_nonterminal",
    "terminal_masked",
    "missing_or_truncated",
    "invalid_transition",
)
SEED_COUNT = 20
UPDATES_PER_SEED = 87
EPOCHS = 3
BATCHES_PER_EPOCH = 29
BATCH_SIZE = 64
WINDOWS_PER_GAME_PER_BATCH = 32
WINDOWS_PER_GAME = 928
BATCH_PAYLOAD_SCHEMA = "caissa.v212.scheduled-batch-payload.v01"


@dataclass(frozen=True)
class ValidatedScheduleManifest:
    """Immutable schedule snapshot plus its one-time structural receipt."""

    schedule_sha256: str
    seeds: tuple[Mapping[str, Any], ...]


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json(item)
                                 for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _strict_int(value: object) -> bool:
    return type(value) is int


def scheduled_batch_payload_sha256(
    seed_ordinal: int,
    update_index: int,
    ordered_window_records: list[tuple[tuple[str, str, int], str]],
) -> str:
    """Digest one batch identity and ordered ID/payload-hash roster."""
    payload = {
        "schema": BATCH_PAYLOAD_SCHEMA,
        "seed_ordinal": seed_ordinal,
        "update_index": update_index,
        "windows": [
            {"id": list(identity), "payload_sha256": payload_sha256}
            for identity, payload_sha256 in ordered_window_records
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_window_record(value: object) -> tuple[tuple[str, str, int], str]:
    _require(isinstance(value, Mapping)
             and set(value) == {"id", "payload_sha256"},
             "window record needs exactly id and payload_sha256")
    identity_value = value["id"]
    _require(isinstance(identity_value, (list, tuple)) and len(identity_value) == 3,
             "window id must be [game, episode_id, start_ply]")
    game, episode_id, start_ply = identity_value
    _require(game in TRAIN_GAMES, "window id names a non-training game")
    _require(type(episode_id) is str and bool(episode_id),
             "window id needs a nonempty episode id")
    _require(_strict_int(start_ply) and start_ply >= 0,
             "window id needs a nonnegative integer start ply")
    payload_sha256 = value["payload_sha256"]
    _require(type(payload_sha256) is str and len(payload_sha256) == 64
             and all(char in "0123456789abcdef" for char in payload_sha256),
             "window payload digest must be a lowercase SHA-256 hex string")
    return (game, episode_id, start_ply), payload_sha256


def _validate_mask_counts(value: object, arm: str) -> dict[str, dict[str, int]]:
    _require(isinstance(value, Mapping) and set(value) == {"1", "2", "4"},
             "mask counts must contain exactly horizons 1, 2, and 4")
    result = {}
    for horizon_key, horizon in (("1", 1), ("2", 2), ("4", 4)):
        counts = value[horizon_key]
        _require(isinstance(counts, Mapping) and set(counts) == set(MASK_FIELDS),
                 "each horizon needs the four D03 mask-count fields")
        normalized = {}
        for field in MASK_FIELDS:
            count = counts[field]
            _require(_strict_int(count) and count >= 0,
                     "mask counts must be nonnegative integers")
            upper = BATCH_SIZE * horizon if field == "invalid_transition" else BATCH_SIZE
            _require(count <= upper, "mask count exceeds its horizon/batch bound")
            normalized[field] = count
        if arm == "direct-leaf-value" and horizon == 4:
            _require(normalized["valid_nonterminal"] >= 1,
                     "direct-leaf update has no valid nonterminal H4 leaf")
        result[horizon_key] = normalized
    return result


def validate_schedule_manifest(manifest: Mapping) -> dict[str, object]:
    """Validate the frozen 20×87 shared-window schedule shape and mask roster.

    The manifest schema stores one ordered 64-window ID/payload-digest list
    and mask counts by arm for each update. Each seed must use a stable bank of
    928 distinct windows per game in every epoch, with each bank member
    appearing exactly once per epoch. Batch order may differ between epochs.
    This checks structure and digest declarations only; it does not verify the
    payload bytes, source episodes, exact-rule replay, split provenance, or
    fingerprints.
    """
    _require(isinstance(manifest, Mapping), "schedule manifest must be a mapping")
    _require(set(manifest) == {"schema", "seeds"},
             "schedule manifest has unknown or missing top-level fields")
    _require(manifest["schema"] == SCHEDULE_SCHEMA,
             "unsupported schedule manifest schema")
    seeds = manifest["seeds"]
    _require(isinstance(seeds, list) and len(seeds) == SEED_COUNT,
             "schedule must contain exactly 20 paired seed records")

    ordinals = []
    model_seeds = []
    seed_banks: dict[int, dict[int, dict[str, dict[tuple[str, str, int], str]]]] = {}
    for seed_position, seed_record in enumerate(seeds):
        _require(isinstance(seed_record, Mapping)
                 and set(seed_record) == {"seed_ordinal", "model_seed", "updates"},
                 "seed record has unknown or missing fields")
        ordinal = seed_record["seed_ordinal"]
        model_seed = seed_record["model_seed"]
        _require(_strict_int(ordinal) and 0 <= ordinal < SEED_COUNT,
                 "seed ordinal must be in 0..19")
        _require(ordinal == seed_position,
                 "seed records must be in canonical ordinal order")
        _require(_strict_int(model_seed) and model_seed >= 0,
                 "model seed must be a nonnegative integer")
        ordinals.append(ordinal)
        model_seeds.append(model_seed)
        updates = seed_record["updates"]
        _require(isinstance(updates, list) and len(updates) == UPDATES_PER_SEED,
                 "each seed must contain exactly 87 updates")
        seed_banks[ordinal] = {epoch: {game: {} for game in TRAIN_GAMES}
                               for epoch in range(EPOCHS)}
        seen_update_indexes = set()

        for update_position, update in enumerate(updates, start=1):
            _require(isinstance(update, Mapping) and set(update) == {
                "update_index", "epoch_index", "batch_index", "window_ids",
                "batch_payload_sha256", "mask_counts_by_arm",
            }, "update record has unknown or missing fields")
            index = update["update_index"]
            epoch = update["epoch_index"]
            batch_index = update["batch_index"]
            _require(_strict_int(index) and 1 <= index <= UPDATES_PER_SEED,
                     "update index must be in 1..87")
            _require(index == update_position,
                     "updates must appear in chronological index order")
            _require(index not in seen_update_indexes,
                     "seed record contains a duplicate update index")
            seen_update_indexes.add(index)
            expected_epoch = (index - 1) // BATCHES_PER_EPOCH
            expected_batch = (index - 1) % BATCHES_PER_EPOCH
            _require(_strict_int(epoch) and epoch == expected_epoch
                     and _strict_int(batch_index) and batch_index == expected_batch,
                     "update index does not match its epoch/batch boundary")

            raw_ids = update["window_ids"]
            _require(isinstance(raw_ids, list) and len(raw_ids) == BATCH_SIZE,
                     "each scheduled update must contain exactly 64 ordered window ids")
            records = [_validate_window_record(value) for value in raw_ids]
            declared_batch_digest = update["batch_payload_sha256"]
            _require(type(declared_batch_digest) is str
                     and len(declared_batch_digest) == 64
                     and all(char in "0123456789abcdef"
                             for char in declared_batch_digest),
                     "batch payload digest must be a lowercase SHA-256 hex string")
            expected_batch_digest = scheduled_batch_payload_sha256(
                ordinal, index, records)
            _require(declared_batch_digest == expected_batch_digest,
                     "batch payload digest does not match its ordered records")
            ids = [identity for identity, _ in records]
            _require(len(set(ids)) == BATCH_SIZE,
                     "scheduled update contains duplicate window ids")
            game_counts = {game: 0 for game in TRAIN_GAMES}
            for identity, payload_sha256 in records:
                game_counts[identity[0]] += 1
                bank = seed_banks[ordinal][epoch][identity[0]]
                previous_hash = bank.setdefault(identity, payload_sha256)
                _require(previous_hash == payload_sha256,
                         "one window id has conflicting payload hashes")
            _require(all(game_counts[game] == WINDOWS_PER_GAME_PER_BATCH
                         for game in TRAIN_GAMES),
                     "each scheduled update must contain 32 windows per game")

            arm_counts = update["mask_counts_by_arm"]
            _require(isinstance(arm_counts, Mapping) and set(arm_counts) == set(ARMS),
                     "mask roster must contain exactly all six V2.12 arms")
            normalized_counts = {
                arm: _validate_mask_counts(arm_counts[arm], arm) for arm in ARMS
            }
            common = normalized_counts[ARMS[0]]
            _require(all(normalized_counts[arm] == common for arm in ARMS[1:]),
                     "all arms must share identical per-horizon mask counts")

        _require(seen_update_indexes == set(range(1, UPDATES_PER_SEED + 1)),
                 "seed record is missing one or more update indexes")

        epoch_banks = seed_banks[ordinal]
        for epoch in range(EPOCHS):
            for game in TRAIN_GAMES:
                _require(len(epoch_banks[epoch][game]) == WINDOWS_PER_GAME,
                         "each epoch must cover 928 distinct windows per game")
        for epoch in range(1, EPOCHS):
            for game in TRAIN_GAMES:
                _require(epoch_banks[epoch][game] == epoch_banks[0][game],
                         "the selected per-game window bank changed across epochs")

    _require(sorted(ordinals) == list(range(SEED_COUNT)),
             "seed ordinals must cover 0..19 exactly once")
    _require(len(set(model_seeds)) == SEED_COUNT,
             "paired initialization seeds must be distinct")

    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    return {
        "schema": SCHEDULE_SCHEMA,
        "seed_count": SEED_COUNT,
        "updates_per_seed": UPDATES_PER_SEED,
        "windows_per_game_per_epoch": WINDOWS_PER_GAME,
        "mask_rows": SEED_COUNT * UPDATES_PER_SEED * len(ARMS) * len(HORIZONS),
        "schedule_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def validate_and_freeze_schedule_manifest(
    manifest: Mapping,
) -> ValidatedScheduleManifest:
    """Validate one detached snapshot and freeze its rows for repeated lookup.

    The structural validator is intentionally a one-time panel preflight. A
    trainer should pass this immutable value to every scheduled update rather
    than revalidating the entire 20×87 declaration on each call.
    """
    snapshot = deepcopy(manifest)
    receipt = validate_schedule_manifest(snapshot)
    return ValidatedScheduleManifest(
        schedule_sha256=str(receipt["schedule_sha256"]),
        seeds=tuple(_freeze_json(seed) for seed in snapshot["seeds"]),
    )
