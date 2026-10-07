"""Pure in-memory V2.12 synthetic trajectory/window audit primitives.

This module deliberately performs no file I/O and imports no training code.
It is a software-contract fixture, not a V2.12 data generator or approval gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .games import BoardGame, State, RULES_VERSION


SPLITS = ("train", "development", "selection", "locked-final")
TARGET_HORIZONS = (1, 2, 4)
WINDOW_PLIES = 4


@dataclass(frozen=True)
class Window:
    game: str
    episode_id: str
    split: str
    episode_outcome: int
    start_ply: int
    states: tuple[State, ...]
    actions: tuple[int, ...]
    valid_targets: tuple[int, ...]
    terminal_targets: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class AuditResult:
    windows: tuple[Window, ...]
    valid_targets_by_horizon: dict[int, int]
    terminal_targets_by_horizon: dict[int, int]
    masked_targets_by_horizon: dict[int, int]
    state_keys_by_window: tuple[tuple[str, ...], ...]


def _game_identity(game: BoardGame) -> tuple[Any, ...]:
    """Identify the rule adapter, not just its caller-supplied display name."""
    return (RULES_VERSION, game.name, game.rows, game.cols, game.k,
            game.gravity, game.reversi)


def window_payload_sha256(window: Window, game: BoardGame) -> str:
    """Hash the exact in-memory window fields together with adapter identity.

    This is a content identity helper, not an audit: callers must still obtain
    windows from ``audit_trajectories`` and use the model-batch adapter to
    replay transitions and verify the declared target masks.
    """
    if not isinstance(window, Window) or not isinstance(game, BoardGame):
        raise TypeError("window and game must be audited V2.12 primitives")
    if window.game != game.name:
        raise ValueError("window/game identity mismatch")
    payload = {
        "schema": "caissa.v212.window-payload.v01",
        "adapter": _game_identity(game),
        "window": {
            "game": window.game,
            "episode_id": window.episode_id,
            "split": window.split,
            "episode_outcome": window.episode_outcome,
            "start_ply": window.start_ply,
            "states": [
                {"board": list(state.board), "player": state.player}
                for state in window.states
            ],
            "actions": list(window.actions),
            "valid_targets": list(window.valid_targets),
            "terminal_targets": [list(item) for item in window.terminal_targets],
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _state_keys(game: BoardGame, state: State) -> tuple[str, str]:
    """Return separate raw and canonical keys, independent of lineage."""
    raw = json.dumps([state.board, state.player], separators=(",", ":"))
    identity = json.dumps(_game_identity(game), separators=(",", ":"))
    raw_key = hashlib.sha256((identity + "|raw|" + raw).encode("utf-8")).hexdigest()
    canonical_key = hashlib.sha256(
        (identity + "|canonical|" + game.canonical_key(state)).encode("utf-8")
    ).hexdigest()
    return raw_key, canonical_key


def _window_signature(game: BoardGame, states: tuple[State, ...],
                      actions: tuple[int, ...]) -> str:
    """Canonicalize one ordered window under game symmetries and role swap."""
    candidates = []
    for mapping in game.transforms():
        mapped_states = []
        mapped_actions = []
        for index, state in enumerate(states):
            transformed, _ = game.transform(state, 64, mapping)
            mapped_states.append(transformed)
            if index < len(actions):
                _, action = game.transform(state, actions[index], mapping)
                mapped_actions.append(action)
        for role_sign in (1, -1):
            path = [(tuple(role_sign * value for value in state.board),
                     role_sign * state.player) for state in mapped_states]
            candidates.append((path, tuple(mapped_actions)))
    canonical = (_game_identity(game), min(candidates))
    return hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode(
        "utf-8")).hexdigest()


def _validate_episode(game: BoardGame, episode: dict[str, Any]) -> tuple[State, ...]:
    episode_id = episode.get("episode_id")
    if not isinstance(episode_id, str) or not episode_id:
        raise ValueError("episode_id must be a nonempty string")
    if episode.get("split") not in SPLITS:
        raise ValueError("unknown split")
    states = tuple(episode.get("states", ()))
    actions = tuple(episode.get("actions", ()))
    if not states or len(states) != len(actions) + 1:
        raise ValueError("state/action path length mismatch")
    if type(episode.get("outcome")) is not int or episode["outcome"] not in (-1, 0, 1):
        raise ValueError("outcome must be an absolute terminal result")
    for state in states:
        if not isinstance(state, State):
            raise ValueError("trajectory contains a non-State value")
        game.validate(state)
    if game.terminal(states[0]) is not None:
        raise ValueError("trajectory starts at a terminal state")
    for index, action in enumerate(actions):
        if game.terminal(states[index]) is not None:
            raise ValueError("actions continue after a terminal state")
        if game.transition(states[index], action) != states[index + 1]:
            raise ValueError("illegal or altered replay transition")
        if states[index + 1].player != -states[index].player:
            raise ValueError("actor role did not alternate")
    exact_outcome = game.terminal(states[-1])
    if exact_outcome is None or exact_outcome != episode["outcome"]:
        raise ValueError("episode outcome does not match terminal rules")
    return states


def _cross_split_overlaps(records: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Return (key, first_split, second_split) content-key collisions."""
    owner: dict[str, str] = {}
    overlaps = set()
    for record in records:
        split = record["split"]
        for key in record["state_keys"]:
            previous = owner.setdefault(key, split)
            if previous != split:
                overlaps.add((key, previous, split))
    return sorted(overlaps)


def audit_trajectories(episodes: list[dict[str, Any]],
                       games: dict[str, BoardGame]) -> AuditResult:
    """Replay and audit all in-memory episodes before returning any windows.

    Episodes require `game`, `episode_id`, `split`, `states`, `actions`, and
    exact terminal `outcome`. A failure raises `ValueError`; no partial windows
    escape and this function never writes files.
    """
    validated = []
    episode_splits: dict[str, str] = {}
    for episode in episodes:
        game_name = episode.get("game")
        if game_name not in games:
            raise ValueError("unknown game")
        game = games[game_name]
        states = _validate_episode(game, episode)
        episode_id = episode["episode_id"]
        if episode_id in episode_splits:
            if episode_splits[episode_id] != episode["split"]:
                raise ValueError("episode lineage crosses split assignments")
            raise ValueError("duplicate episode_id")
        episode_splits[episode_id] = episode["split"]
        validated.append((game, episode, states))

    pending: list[Window] = []
    identity_records = []
    signatures: dict[tuple[str, str], tuple[str, int]] = {}
    for game, episode, states in validated:
        actions = tuple(episode["actions"])
        split = episode["split"]
        for start in range(len(actions)):
            stop = min(start + WINDOW_PLIES, len(actions))
            window_states = states[start:stop + 1]
            window_actions = actions[start:stop]
            valid_targets = []
            terminal_targets = []
            for horizon in TARGET_HORIZONS:
                index = start + horizon
                if index >= len(states):
                    continue
                terminal = game.terminal(states[index])
                if terminal is None:
                    valid_targets.append(horizon)
                else:
                    terminal_targets.append((horizon,
                                             states[index].player * terminal))
            signature = _window_signature(game, window_states, window_actions)
            owner_key = (json.dumps(_game_identity(game)), signature)
            prior = signatures.get(owner_key)
            if prior is not None:
                raise ValueError("duplicate canonical window")
            signatures[owner_key] = (episode["episode_id"], start)
            keys = tuple(key for state in window_states
                         for key in _state_keys(game, state))
            identity_records.append({"split": split, "state_keys": keys})
            pending.append(Window(game.name, episode["episode_id"], split,
                                  episode["outcome"], start,
                                  window_states, window_actions,
                                  tuple(valid_targets), tuple(terminal_targets)))

    if _cross_split_overlaps(identity_records):
        raise ValueError("context/window state overlaps across split assignments")

    valid_counts = {horizon: 0 for horizon in TARGET_HORIZONS}
    terminal_counts = {horizon: 0 for horizon in TARGET_HORIZONS}
    masked_counts = {horizon: 0 for horizon in TARGET_HORIZONS}
    for window in pending:
        for horizon in TARGET_HORIZONS:
            if horizon in window.valid_targets:
                valid_counts[horizon] += 1
            elif any(target_horizon == horizon
                     for target_horizon, _ in window.terminal_targets):
                terminal_counts[horizon] += 1
            else:
                masked_counts[horizon] += 1
    return AuditResult(tuple(pending), valid_counts, terminal_counts,
                       masked_counts,
                       tuple(record["state_keys"] for record in identity_records))


def audit_synthetic_key_records(records: list[dict[str, Any]]) -> None:
    """Fixture hook for the split-key predicate, including isolated H4 cases."""
    if _cross_split_overlaps(records):
        raise ValueError("context/window state overlaps across split assignments")
