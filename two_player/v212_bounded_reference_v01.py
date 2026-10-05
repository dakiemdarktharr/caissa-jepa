"""Exact fixed-horizon alpha-beta values for an explicitly pinned evaluator.

This is a research implementation candidate. Each legal root action is
queried independently with a full window, so every returned Q value is exact
for the declared finite horizon/evaluator. It is not a full-game oracle and
does not choose or endorse a production h_ref.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .games import GameSpec, State


SCHEMA = "caissa.v212.bounded-reference.v01"
VALUE_SCALE = 10_000
_INF = VALUE_SCALE + 1
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ReferenceError(ValueError):
    """The requested bounded-reference contract is invalid or incomplete."""


class ReferenceBudgetExceeded(ReferenceError):
    """The complete bounded-reference value table did not fit its cap."""


@dataclass(frozen=True)
class BoundedReferenceResult:
    schema: str
    game: str
    root_sha256: str
    root_player: int
    horizon_plies: int
    evaluator_source_sha256: str
    evaluator_config_sha256: str
    action_values: tuple[tuple[int, int], ...]
    root_value: int
    best_actions: tuple[int, ...]
    transition_count: int
    node_count: int
    source_sha256: str


LeafEvaluator = Callable[[GameSpec, State, int], int]


def bounded_reference_values(
        game: GameSpec, state: State, *, horizon_plies: int,
        evaluator: LeafEvaluator, evaluator_source_sha256: str,
        evaluator_config_sha256: str,
        transition_budget: int | None = None) -> BoundedReferenceResult:
    """Compute exact fixed-horizon Q values for every legal root action.

    ``horizon_plies`` includes the root action. Terminal outcomes override the
    leaf evaluator and are scaled to +/-VALUE_SCALE (draw=0). Nonterminal
    horizon leaves must return an integer strictly inside that range. Every
    root action receives an independent full-window search; no incumbent root
    alpha is shared between actions. A hard transition cap aborts the entire
    result rather than returning a partial table or mixing bounds with scores.
    """
    if type(horizon_plies) is not int or horizon_plies < 1:
        raise ReferenceError("horizon_plies must be a positive integer")
    for value, label in ((evaluator_source_sha256, "evaluator source hash"),
                         (evaluator_config_sha256, "evaluator config hash")):
        if not isinstance(value, str) or not _HEX64.fullmatch(value):
            raise ReferenceError(f"{label} must be lowercase SHA-256 hex")
    if transition_budget is not None:
        if type(transition_budget) is not int or transition_budget < 0:
            raise ReferenceError("transition_budget must be a nonnegative integer")

    game.validate(state)
    if game.terminal(state) is not None:
        raise ReferenceError("root state must be nonterminal")
    root_actions = tuple(game.legal_actions(state))
    if not root_actions or len(set(root_actions)) != len(root_actions):
        raise ReferenceError("root legal-action set is empty or duplicated")
    if any(type(action) is not int for action in root_actions):
        raise ReferenceError("root legal actions must be integer IDs")
    if transition_budget is not None and transition_budget < len(root_actions):
        raise ReferenceBudgetExceeded(
            "transition_budget cannot cover the complete root action set")

    root_player = state.player
    transitions = 0
    nodes = 0

    def leaf_value(current: State) -> int:
        value = evaluator(game, current, root_player)
        if (type(value) is not int or not -VALUE_SCALE < value < VALUE_SCALE):
            raise ReferenceError(
                "leaf evaluator must return a non-Boolean integer strictly inside the terminal range")
        return value

    def search(current: State, plies_left: int, alpha: int, beta: int) -> int:
        nonlocal nodes, transitions
        nodes += 1
        outcome = game.terminal(current)
        if outcome is not None:
            return root_player * outcome * VALUE_SCALE
        if plies_left == 0:
            return leaf_value(current)

        actions = tuple(game.legal_actions(current))
        if not actions:
            raise ReferenceError("nonterminal state has no legal actions")
        maximizing = current.player == root_player
        value = -_INF if maximizing else _INF
        for action in actions:
            if type(action) is not int:
                raise ReferenceError("legal actions must be integer IDs")
            if transition_budget is not None and transitions >= transition_budget:
                raise ReferenceBudgetExceeded(
                    "transition budget exhausted before complete root values")
            child = game.transition(current, action)
            transitions += 1
            score = search(child, plies_left - 1, alpha, beta)
            if maximizing:
                value = max(value, score)
                alpha = max(alpha, value)
            else:
                value = min(value, score)
                beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    action_values = []
    for action in root_actions:
        if transition_budget is not None and transitions >= transition_budget:
            raise ReferenceBudgetExceeded(
                "transition budget exhausted before complete root values")
        child = game.transition(state, action)
        transitions += 1
        # Each root action gets a fresh full window; fail-soft bounds from a
        # previous root action can never leak into this exact Q table.
        value = search(child, horizon_plies - 1, -_INF, _INF)
        action_values.append((action, value))

    root_value = max(value for _, value in action_values)
    best_actions = tuple(action for action, value in action_values
                         if value == root_value)
    root_identity = {
        "game": game.name,
        "canonical_game_state_key": game.canonical_key(state),
        "board": list(state.board),
        "player": root_player,
    }
    root_sha256 = hashlib.sha256(
        json.dumps(root_identity, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("ascii")
    ).hexdigest()
    try:
        source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError as exc:
        raise ReferenceError("bounded-reference source digest unavailable") from exc

    return BoundedReferenceResult(
        schema=SCHEMA,
        game=game.name,
        root_sha256=root_sha256,
        root_player=root_player,
        horizon_plies=horizon_plies,
        evaluator_source_sha256=evaluator_source_sha256,
        evaluator_config_sha256=evaluator_config_sha256,
        action_values=tuple(action_values),
        root_value=root_value,
        best_actions=best_actions,
        transition_count=transitions,
        node_count=nodes,
        source_sha256=source_sha256,
    )
