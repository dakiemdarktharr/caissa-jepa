"""Sound, budgeted minimax value intervals for tiny-game research fixtures.

This module is an isolated verifier/candidate, not part of training or model
evaluation. The root legal-action set is always enumerated. A deterministic
depth-first expansion budget applies below the root; every unexpanded
nonterminal state remains the conservative W/D/L interval [-1, +1].
"""
from dataclasses import dataclass
from typing import Optional

from .games import GameSpec, State


LOWER_UTILITY = -1
UPPER_UTILITY = 1


@dataclass(frozen=True)
class ValueInterval:
    lower: int
    upper: int

    def __post_init__(self):
        if self.lower not in (-1, 0, 1) or self.upper not in (-1, 0, 1):
            raise ValueError("W/D/L interval endpoints must be in {-1, 0, +1}")
        if self.lower > self.upper:
            raise ValueError("interval lower endpoint exceeds upper endpoint")


@dataclass(frozen=True)
class RegretInterval:
    lower: int
    upper: int


@dataclass(frozen=True)
class MinimaxBounds:
    root_player: int
    action_values: tuple[tuple[int, ValueInterval], ...]
    root_value: ValueInterval
    regret: RegretInterval
    expanded_nodes: int
    transition_count: int


def minimax_bounds(game: GameSpec, state: State, executed_action: int,
                   expansion_budget: int) -> MinimaxBounds:
    """Bound full-game minimax values using a deterministic DFS node budget.

    The root is not charged against ``expansion_budget``: its complete legal
    action list is needed to report every root action. Expansions are counted
    only when a nonterminal descendant's complete legal successor set is
    visited. Terminal checks and transitions do not consume the node budget.
    """
    if type(expansion_budget) is not int or expansion_budget < 0:
        raise ValueError("expansion_budget must be a nonnegative integer")
    game.validate(state)
    if game.terminal(state) is not None:
        raise ValueError("root state must be nonterminal")
    root_actions = tuple(game.legal_actions(state))
    if not root_actions:
        raise ValueError("nonterminal root has no legal actions")
    if type(executed_action) is not int:
        raise ValueError("executed_action must be an integer action ID")
    if executed_action not in root_actions:
        raise ValueError("executed_action must be legal at the root")

    remaining = expansion_budget
    expanded = 0
    transitions = 0

    def visit(node: State) -> ValueInterval:
        nonlocal remaining, expanded, transitions
        outcome = game.terminal(node)
        if outcome is not None:
            value = state.player * outcome
            return ValueInterval(value, value)
        if remaining == 0:
            return ValueInterval(LOWER_UTILITY, UPPER_UTILITY)

        actions = tuple(game.legal_actions(node))
        if not actions:
            raise ValueError("nonterminal state has no legal actions")
        remaining -= 1
        expanded += 1
        children = []
        for action in actions:
            child = game.transition(node, action)
            transitions += 1
            children.append(visit(child))
        if node.player == state.player:
            return ValueInterval(max(child.lower for child in children),
                                 max(child.upper for child in children))
        return ValueInterval(min(child.lower for child in children),
                             min(child.upper for child in children))

    action_values = []
    for action in root_actions:
        child = game.transition(state, action)
        transitions += 1
        action_values.append((action, visit(child)))

    root_value = ValueInterval(
        max(value.lower for _, value in action_values),
        max(value.upper for _, value in action_values),
    )
    action_map = dict(action_values)
    executed = action_map[executed_action]
    regret = RegretInterval(
        max(0, root_value.lower - executed.upper),
        min(2, root_value.upper - executed.lower),
    )
    return MinimaxBounds(state.player, tuple(action_values), root_value, regret,
                         expanded, transitions)
