"""Deterministic in-memory receipts for exact-rule replayed V2.12 episodes.

This module does no file I/O, selection, generation, or training. A receipt
binds canonical episode-record content to one exact-rule audit and its derived
window payload digests; it does not identify source-file bytes or authenticate
who supplied the record.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .games import BoardGame
from .v212_trajectory_audit import (
    _game_identity,
    audit_trajectories,
    window_payload_sha256,
)


RECEIPT_SCHEMA = "caissa.v212.episode-replay-receipt.v01"
_EPISODE_FIELDS = {"game", "episode_id", "split", "states", "actions", "outcome"}


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_episode_replay_receipt(
    episode: Mapping[str, Any], game: BoardGame,
) -> dict[str, Any]:
    """Replay one complete episode and return a content-bound receipt.

    Strict fields prevent unbound metadata from being mistaken as part of the
    receipt. The episode digest covers the canonical in-memory record, exact
    adapter identity, complete state/action path, and absolute outcome. Each
    derived window is listed with its own payload digest.
    """
    if not isinstance(episode, Mapping) or set(episode) != _EPISODE_FIELDS:
        raise ValueError("episode must contain exactly the replay receipt fields")
    if not isinstance(game, BoardGame) or episode["game"] != game.name:
        raise ValueError("episode/game identity mismatch")

    audited = audit_trajectories([dict(episode)], {game.name: game})
    return _build_receipt_from_audited_windows(episode, game, audited.windows)


def _build_receipt_from_audited_windows(
    episode: Mapping[str, Any], game: BoardGame, windows: tuple,
) -> dict[str, Any]:
    """Assemble a receipt from windows returned by the exact-rule auditor."""
    states = tuple(episode["states"])
    actions = tuple(episode["actions"])
    episode_payload = {
        "schema": "caissa.v212.episode-payload.v01",
        "adapter": list(_game_identity(game)),
        "game": episode["game"],
        "episode_id": episode["episode_id"],
        "split": episode["split"],
        "states": [
            {"board": list(state.board), "player": state.player}
            for state in states
        ],
        "actions": list(actions),
        "outcome": episode["outcome"],
    }
    windows = [
        {
            "id": [window.game, window.episode_id, window.start_ply],
            "payload_sha256": window_payload_sha256(window, game),
        }
        for window in windows
    ]
    body = {
        "schema": RECEIPT_SCHEMA,
        "game": game.name,
        "episode_id": episode["episode_id"],
        "split": episode["split"],
        "rules_identity": list(_game_identity(game)),
        "episode_payload_sha256": _canonical_sha256(episode_payload),
        "window_records": windows,
    }
    return {**body, "receipt_sha256": _canonical_sha256(body)}


def validate_episode_replay_receipt(
    receipt: Mapping[str, Any], episode: Mapping[str, Any], game: BoardGame,
) -> str:
    """Rebuild and compare a receipt against the complete in-memory episode."""
    expected = build_episode_replay_receipt(episode, game)
    if not isinstance(receipt, Mapping) or dict(receipt) != expected:
        raise ValueError("episode replay receipt does not match exact-rule replay")
    return expected["receipt_sha256"]
