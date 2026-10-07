"""Pure in-memory conversion of replay-audited train windows to model arrays.

This adapter performs no file I/O, window selection, or training. Callers must
obtain windows from the exact-rule trajectory auditor; it rechecks each local
transition before emitting a batch, but does not replace episode-level replay
or authorize access to a training dataset.
"""
from __future__ import annotations

import numpy as np

from .games import ACTION_SIZE, FEATURE_SIZE, BoardGame
from .v212_model import preflight_batch
from .v212_trajectory_audit import TARGET_HORIZONS, Window


def windows_to_model_batch(windows: tuple[Window, ...] | list[Window],
                           games: dict[str, BoardGame], *,
                           required_split: str = "train") -> dict[str, np.ndarray]:
    """Convert audited windows to the exact fixed-batch schema expected by v06.

    Only training-split windows are accepted by default. States/outcomes come
    from the audited windows; unavailable post-terminal or truncated entries
    are zero-padded and distinguished by explicit existence masks. The result
    is passed through `preflight_batch` before it is returned.
    """
    if not isinstance(windows, (tuple, list)) or not windows:
        raise ValueError("windows must be a nonempty sequence")
    if required_split != "train":
        raise ValueError("model training batches require the train split")

    n = len(windows)
    batch = {
        "x": np.zeros((n, FEATURE_SIZE), dtype=np.float64),
        "legal": np.zeros((n, ACTION_SIZE), dtype=bool),
        "policy": np.zeros(n, dtype=np.int64),
        "value": np.zeros(n, dtype=np.float64),
        "actions": np.zeros((n, 4, ACTION_SIZE), dtype=np.float64),
        "actors": np.zeros((n, 4), dtype=np.float64),
        "future_x": np.zeros((n, 4, FEATURE_SIZE), dtype=np.float64),
        "future_value": np.zeros((n, 4), dtype=np.float64),
        "transition_exists": np.zeros((n, 4), dtype=bool),
        "transition_valid": np.zeros((n, 4), dtype=bool),
        "target_exists": np.zeros((n, 4), dtype=bool),
        "terminal": np.zeros((n, 4), dtype=bool),
    }

    for row, window in enumerate(windows):
        if not isinstance(window, Window) or window.split != required_split:
            raise ValueError("every window must belong to the required split")
        game = games.get(window.game)
        if game is None:
            raise ValueError("unknown window game")
        if (type(window.episode_outcome) is not int
                or window.episode_outcome not in (-1, 0, 1)):
            raise ValueError("window outcome must be an absolute terminal result")
        if (not window.states or not window.actions
                or len(window.states) != len(window.actions) + 1
                or len(window.actions) > 4):
            raise ValueError("window state/action path length mismatch")
        if game.terminal(window.states[0]) is not None:
            raise ValueError("window cannot start at a terminal state")

        root = window.states[0]
        batch["x"][row] = game.features(root)
        legal_actions = game.legal_actions(root)
        if not legal_actions:
            raise ValueError("window root has no legal action")
        batch["legal"][row, list(legal_actions)] = True
        batch["policy"][row] = window.actions[0]
        batch["value"][row] = root.player * window.episode_outcome

        for step, action in enumerate(window.actions):
            state = window.states[step]
            successor = window.states[step + 1]
            game.validate(state)
            game.validate(successor)
            if game.transition(state, action) != successor:
                raise ValueError("window contains an illegal or altered transition")
            if successor.player != -state.player:
                raise ValueError("window actor role did not alternate")
            batch["actions"][row, step, action] = 1.0
            batch["actors"][row, step] = state.player
            batch["transition_exists"][row, step] = True
            batch["transition_valid"][row, step] = True

        for step, state in enumerate(window.states[1:]):
            batch["future_x"][row, step] = game.features(state)
            batch["future_value"][row, step] = state.player * window.episode_outcome
            batch["target_exists"][row, step] = True
            batch["terminal"][row, step] = game.terminal(state) is not None

    preflight = preflight_batch(batch)
    for row, window in enumerate(windows):
        model_valid = tuple(
            horizon for horizon in TARGET_HORIZONS
            if preflight["valid"][horizon][row])
        if model_valid != window.valid_targets:
            raise ValueError("auditor/model valid-target mask mismatch")
        model_terminal = tuple(
            (horizon, int(window.states[horizon].player * window.episode_outcome))
            for horizon in TARGET_HORIZONS
            if horizon < len(window.states)
            and batch["terminal"][row, horizon - 1])
        if model_terminal != window.terminal_targets:
            raise ValueError("auditor/model terminal-target mask mismatch")
    return batch
