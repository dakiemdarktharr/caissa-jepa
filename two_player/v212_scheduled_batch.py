"""No-update boundary for one paired V2.12 scheduled six-arm batch.

The caller supplies already audited in-memory windows. This module performs no
file I/O, selection, optimizer update, checkpointing, schedule generation, or
training. A future trainer/profile must route every scheduled model invocation
through this boundary and bind its returned identity to the frozen manifest.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType

import numpy as np

from .games import BoardGame
from .v212_model import ARMS
from .v212_schedule_manifest import scheduled_batch_payload_sha256
from .v212_trajectory_audit import Window, window_payload_sha256
from .v212_window_batch import windows_to_model_batch


TRAIN_GAME_SPECS = {
    "connect4-gravity-6x7": (6, 7, 4, True, False),
    "reversi6": (6, 6, 0, False, True),
}
PAIRED_SEEDS = 20
UPDATES_PER_SEED = 87
WINDOWS_PER_GAME = 32


@dataclass(frozen=True)
class ScheduledBatchResult:
    """One no-update paired graph call and its manifest-bindable identity."""

    seed_ordinal: int
    update_index: int
    ordered_window_ids: tuple[tuple[str, str, int], ...]
    ordered_window_payload_sha256: tuple[str, ...]
    window_order_sha256: str
    batch_payload_sha256: str
    by_arm: dict[str, tuple[dict, dict[str, np.ndarray]]]


def _validate_game_adapters(games: Mapping[str, BoardGame]) -> None:
    if not isinstance(games, Mapping) or set(games) != set(TRAIN_GAME_SPECS):
        raise ValueError("games must contain exactly the two V2.12 training adapters")
    for name, spec in TRAIN_GAME_SPECS.items():
        game = games[name]
        if not isinstance(game, BoardGame) or game.name != name:
            raise ValueError("training adapter identity mismatch")
        actual = (game.rows, game.cols, game.k, game.gravity, game.reversi)
        if actual != spec:
            raise ValueError("training adapter rules do not match V2.12 variants")


def compute_scheduled_panel_batch(
    windows: Sequence[Window],
    games: Mapping[str, BoardGame],
    models: Mapping[str, object],
    *,
    seed_ordinal: int,
    update_index: int,
) -> ScheduledBatchResult:
    """Run one same-window, six-arm loss/gradient call without updating state.

    Unlike ``loss_grad(batch)``, this scheduled seam accepts windows rather
    than a caller-assembled ndarray dictionary, materializes them once through
    the audited-window adapter, enforces the 20-seed/87-update identity range,
    and shares the same read-only batch object across all six arms. It does not
    establish that the windows came from an accepted manifest or episode
    replay; a future caller must bind the returned ordered IDs/digest to those
    receipts and must not call ``loss_grad`` directly for scheduled work.
    """
    if type(seed_ordinal) is not int or not 0 <= seed_ordinal < PAIRED_SEEDS:
        raise ValueError("seed ordinal must be in the frozen 0..19 range")
    if type(update_index) is not int or not 1 <= update_index <= UPDATES_PER_SEED:
        raise ValueError("update index must be in the frozen 1..87 range")
    if not isinstance(windows, (tuple, list)) or len(windows) != 64:
        raise ValueError("scheduled update requires exactly 64 audited windows")
    _validate_game_adapters(games)
    if not isinstance(models, Mapping) or set(models) != set(ARMS):
        raise ValueError("scheduled panel must include exactly all six V2.12 arms")

    window_ids = []
    game_counts = {name: 0 for name in TRAIN_GAME_SPECS}
    for window in windows:
        if not isinstance(window, Window):
            raise ValueError("scheduled input must contain audited Window records")
        if window.split != "train" or window.game not in TRAIN_GAME_SPECS:
            raise ValueError("scheduled windows must be train rows from both training games")
        if type(window.episode_id) is not str or not window.episode_id:
            raise ValueError("scheduled window needs a stable episode identity")
        if type(window.start_ply) is not int or window.start_ply < 0:
            raise ValueError("scheduled window needs a nonnegative start ply")
        game_counts[window.game] += 1
        window_ids.append((window.game, window.episode_id, window.start_ply))
    if any(count != WINDOWS_PER_GAME for count in game_counts.values()):
        raise ValueError("scheduled update must contain exactly 32 windows per game")
    if len(set(window_ids)) != 64:
        raise ValueError("scheduled update contains duplicate window identities")

    paired_model_seeds = set()
    for arm in ARMS:
        model = models[arm]
        config = getattr(model, "config", None)
        if getattr(config, "arm", None) != arm:
            raise ValueError("model arm identity does not match the six-arm roster")
        seed = getattr(config, "seed", None)
        if type(seed) is not int:
            raise ValueError("each model must expose an integer paired initialization seed")
        paired_model_seeds.add(seed)
        if not callable(getattr(model, "loss_grad", None)):
            raise ValueError("each model must expose the no-update loss_grad method")
    if len(paired_model_seeds) != 1:
        raise ValueError("all six arms must use the same paired initialization seed")

    batch_arrays = windows_to_model_batch(windows, games, required_split="train")
    # Freeze the single adapter result before any arm sees it, preventing a
    # caller/model from changing later arms' inputs within this panel call.
    for value in batch_arrays.values():
        value.setflags(write=False)
    batch = MappingProxyType(batch_arrays)

    ordered_ids = tuple(window_ids)
    canonical = json.dumps(ordered_ids, separators=(",", ":"), ensure_ascii=False)
    order_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload_hashes = tuple(
        window_payload_sha256(window, games[window.game]) for window in windows
    )
    payload_digest = scheduled_batch_payload_sha256(
        seed_ordinal, update_index,
        list(zip(ordered_ids, payload_hashes)))
    results = {}
    for arm in ARMS:
        metrics, gradients = models[arm].loss_grad(batch)
        if not isinstance(metrics, dict) or metrics.get("arm") != arm:
            raise ValueError("loss_grad returned metrics for the wrong arm")
        if not isinstance(gradients, dict):
            raise ValueError("loss_grad must return a gradient mapping")
        results[arm] = (metrics, gradients)

    return ScheduledBatchResult(
        seed_ordinal=seed_ordinal,
        update_index=update_index,
        ordered_window_ids=ordered_ids,
        ordered_window_payload_sha256=payload_hashes,
        window_order_sha256=order_digest,
        batch_payload_sha256=payload_digest,
        by_arm=results,
    )
