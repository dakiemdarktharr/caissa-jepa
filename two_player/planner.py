"""Exact-legal two-ply max-min planner with learned nonterminal leaf scores.

The callback must return a value from the root player's perspective. Legality,
transitions, and terminal outcomes always come from the game adapter.
"""
from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class PlanResult:
    action: int
    action_values: dict
    root_actions_evaluated: int
    reply_branches_evaluated: int
    immediate_terminal_actions: int
    terminal_reply_branches: int
    nonterminal_leaf_evaluations: int


def plan_depth_two(game, state, score_leaf: Callable) -> PlanResult:
    """Choose argmax_a min_b using terminal utility or ``score_leaf``.

    A terminal successor immediately after the root action is scored directly
    and has no reply minimization. A forced pass is handled as an ordinary
    legal reply by the game adapter.
    """
    game.validate(state)
    if game.terminal(state) is not None:
        raise ValueError("Cannot plan from a terminal state")
    root_player = state.player
    actions = tuple(game.legal_actions(state))
    if not actions:
        raise ValueError("Nonterminal state has no legal actions")

    action_values = {}
    reply_branches = 0
    immediate_terminal = 0
    terminal_replies = 0
    nonterminal_leaves = 0
    for action in actions:
        child = game.transition(state, action)
        child_outcome = game.terminal(child)
        if child_outcome is not None:
            action_values[action] = float(root_player * child_outcome)
            immediate_terminal += 1
            continue

        replies = tuple(game.legal_actions(child))
        if not replies:
            raise ValueError("Nonterminal reply state has no legal actions")
        reply_values = []
        for reply in replies:
            leaf = game.transition(child, reply)
            outcome = game.terminal(leaf)
            reply_branches += 1
            if outcome is not None:
                value = float(root_player * outcome)
                terminal_replies += 1
            else:
                value = float(score_leaf(state, action, reply, leaf))
                if not math.isfinite(value) or not -1.0 <= value <= 1.0:
                    raise ValueError("Leaf score must be finite and in [-1, 1]")
                nonterminal_leaves += 1
            reply_values.append(value)
        action_values[action] = min(reply_values)

    # Stable tie-break follows the adapter's legal-action order.
    selected = max(actions, key=lambda action: action_values[action])
    return PlanResult(selected, action_values, len(actions), reply_branches,
                      immediate_terminal, terminal_replies, nonterminal_leaves)
