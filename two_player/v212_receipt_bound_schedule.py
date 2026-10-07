"""No-update checks binding V2.12 schedule rows to replayed episode content.

This is a preflight seam, not a trainer. It consumes a previously constructed
in-memory exact-rule receipt index and one window batch, then checks a single
declared schedule row and actual adapter masks before delegating to the
existing six-arm no-update call helper. It performs no file I/O, selection,
optimizer update, checkpointing, or training.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .games import BoardGame
from .v212_episode_replay_receipt import _build_receipt_from_audited_windows
from .v212_model import ARMS, preflight_batch
from .v212_schedule_manifest import validate_schedule_manifest
from .v212_scheduled_batch import (
    ScheduledBatchResult,
    compute_scheduled_panel_batch,
)
from .v212_trajectory_audit import (
    Window,
    audit_trajectories,
    window_payload_sha256,
)
from .v212_window_batch import windows_to_model_batch


@dataclass(frozen=True)
class ReceiptBoundBatchResult:
    scheduled: ScheduledBatchResult
    schedule_sha256: str
    ordered_episode_receipt_sha256: tuple[str, ...]


@dataclass(frozen=True)
class TrainReplayReceiptIndex:
    episode_receipt_sha256: Mapping[tuple[str, str], str]
    window_records: Mapping[tuple[str, str, int], Mapping[str, str]]
    audited_episode_count: int
    audited_window_count: int


def build_train_replay_receipt_index(
    episodes: Sequence[Mapping[str, Any]],
    games: Mapping[str, BoardGame],
) -> TrainReplayReceiptIndex:
    """Audit the supplied train episodes and index receipts by episode/window.

    Passing the entire in-memory train episode collection through the existing
    auditor also exercises its duplicate-ID, canonical-window, and overlap
    checks. The returned index is scoped only to these supplied records; it is
    not a file/source provenance or complete train-split audit receipt.
    """
    if not isinstance(episodes, Sequence) or isinstance(episodes, (str, bytes)):
        raise ValueError("episodes must be an in-memory sequence")
    if not episodes:
        raise ValueError("at least one train episode is required")
    if any(not isinstance(episode, Mapping) or episode.get("split") != "train"
           for episode in episodes):
        raise ValueError("receipt index accepts train episodes only")

    audited = audit_trajectories([dict(episode) for episode in episodes], dict(games))
    windows_by_episode: dict[tuple[str, str], list[Window]] = {}
    for window in audited.windows:
        windows_by_episode.setdefault((window.game, window.episode_id), []).append(window)

    receipt_digests: dict[tuple[str, str], str] = {}
    windows: dict[tuple[str, str, int], dict[str, str]] = {}
    for episode in episodes:
        key = (episode["game"], episode["episode_id"])
        game = games.get(episode["game"])
        if game is None:
            raise ValueError("episode names a game without a supplied rules adapter")
        receipt = _build_receipt_from_audited_windows(
            episode, game, tuple(windows_by_episode.get(key, ())))
        receipt_digests[key] = receipt["receipt_sha256"]
        receipt_sha256 = receipt["receipt_sha256"]
        for record in receipt["window_records"]:
            identity = tuple(record["id"])
            windows[identity] = {
                "payload_sha256": record["payload_sha256"],
                "episode_receipt_sha256": receipt_sha256,
            }

    if len(audited.windows) != len(windows):
        raise ValueError("episode receipt index does not cover audited windows")
    frozen_windows = MappingProxyType({
        identity: MappingProxyType(record) for identity, record in windows.items()
    })
    return TrainReplayReceiptIndex(
        episode_receipt_sha256=MappingProxyType(receipt_digests),
        window_records=frozen_windows,
        audited_episode_count=len(episodes),
        audited_window_count=len(audited.windows),
    )


def validate_window_receipt_binding(
    declared_records: Sequence[Mapping[str, Any]],
    windows: Sequence[Window],
    receipt_window_index: Mapping[tuple[str, str, int], Mapping[str, str]],
    episode_receipt_index: Mapping[tuple[str, str], str],
    games: Mapping[str, BoardGame],
) -> tuple[str, ...]:
    """Require ordered schedule rows to match replayed windows and receipts."""
    if len(declared_records) != 64 or len(windows) != 64:
        raise ValueError("schedule row and replay batch must each contain 64 windows")
    receipt_hashes = []
    for record, window in zip(declared_records, windows):
        if not isinstance(window, Window):
            raise ValueError("scheduled input must contain Window records")
        identity = (window.game, window.episode_id, window.start_ply)
        if record.get("id") != list(identity):
            raise ValueError("schedule window order/identity differs from replay input")
        game = games.get(window.game)
        if game is None:
            raise ValueError("scheduled window has no supplied game adapter")
        payload_sha256 = window_payload_sha256(window, game)
        if record.get("payload_sha256") != payload_sha256:
            raise ValueError("schedule window payload differs from replay input")
        receipt_record = receipt_window_index.get(identity)
        if (not isinstance(receipt_record, Mapping)
                or receipt_record.get("payload_sha256") != payload_sha256):
            raise ValueError("window is not bound to an exact episode replay receipt")
        receipt_sha256 = receipt_record.get("episode_receipt_sha256")
        if not _is_sha256(receipt_sha256):
            raise ValueError("window receipt index has an invalid episode receipt digest")
        if episode_receipt_index.get((window.game, window.episode_id)) != receipt_sha256:
            raise ValueError("window is not bound to its parent episode receipt")
        receipt_hashes.append(receipt_sha256)
    return tuple(receipt_hashes)


def _is_sha256(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _observed_mask_counts(batch: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    preflight = preflight_batch(batch)
    return {
        str(horizon): {
            field: int(preflight["counts"][horizon][field])
            for field in ("valid_nonterminal", "terminal_masked",
                          "missing_or_truncated", "invalid_transition")
        }
        for horizon in (1, 2, 4)
    }


def validate_actual_mask_roster(
    declared_mask_counts_by_arm: Mapping[str, Any],
    actual_mask_counts: Mapping[str, Any],
) -> None:
    """Reject any schedule mask declaration that differs from actual adapter data."""
    if set(declared_mask_counts_by_arm) != set(ARMS):
        raise ValueError("schedule mask roster must contain all six arms")
    for arm in ARMS:
        if declared_mask_counts_by_arm[arm] != actual_mask_counts:
            raise ValueError("declared schedule masks differ from replayed batch masks")
        if declared_mask_counts_by_arm[arm]["4"]["valid_nonterminal"] < 1 \
                and arm == "direct-leaf-value":
            raise ValueError("direct-leaf update has no valid nonterminal H4 leaf")


def compute_receipt_bound_panel_batch(
    manifest: Mapping[str, Any],
    receipt_index: TrainReplayReceiptIndex,
    windows: Sequence[Window],
    games: Mapping[str, BoardGame],
    models: Mapping[str, object],
    *,
    seed_ordinal: int,
    update_index: int,
) -> ReceiptBoundBatchResult:
    """Validate one frozen schedule row before the paired no-update call.

    The manifest validator checks the declared whole-schedule structure. This
    seam then proves that the requested ordered row is the supplied windows,
    each window is included in an exact-rule replay receipt in the supplied
    train index, the actual adapter mask equals the declaration, and the
    model initialization seed matches the row. It does not prevent unrelated
    callers from invoking ``loss_grad`` directly; a trainer must make this its
    only scheduled entry point.
    """
    if not isinstance(receipt_index, TrainReplayReceiptIndex):
        raise ValueError("scheduled call requires a replay-audited train receipt index")
    schedule_receipt = validate_schedule_manifest(manifest)
    if type(seed_ordinal) is not int or not 0 <= seed_ordinal < len(manifest["seeds"]):
        raise ValueError("seed ordinal is outside the validated schedule")
    if type(update_index) is not int or not 1 <= update_index <= 87:
        raise ValueError("update index is outside the validated schedule")
    seed_record = manifest["seeds"][seed_ordinal]
    update = seed_record["updates"][update_index - 1]

    per_window_receipts = validate_window_receipt_binding(
        update["window_ids"], windows, receipt_index.window_records,
        receipt_index.episode_receipt_sha256, games)
    ordered_receipts = tuple(dict.fromkeys(per_window_receipts))

    for arm in ARMS:
        config = getattr(models.get(arm), "config", None)
        if getattr(config, "arm", None) != arm or getattr(config, "seed", None) != seed_record["model_seed"]:
            raise ValueError("model identity/seed does not match the frozen schedule row")

    batch = windows_to_model_batch(list(windows), dict(games), required_split="train")
    actual_masks = _observed_mask_counts(batch)
    validate_actual_mask_roster(update["mask_counts_by_arm"], actual_masks)

    scheduled = compute_scheduled_panel_batch(
        list(windows), dict(games), models,
        seed_ordinal=seed_ordinal, update_index=update_index,
    )
    if scheduled.batch_payload_sha256 != update["batch_payload_sha256"]:
        raise ValueError("scheduled call digest differs from the frozen manifest row")
    return ReceiptBoundBatchResult(
        scheduled=scheduled,
        schedule_sha256=str(schedule_receipt["schedule_sha256"]),
        ordered_episode_receipt_sha256=ordered_receipts,
    )
