"""Root-balanced hard-transition minimax interval candidate.

The deterministic allocator divides transitions remaining after mandatory root
enumeration as evenly as possible across root actions, with remainder assigned
in root legal-action order. Each root branch is searched independently by the
hard-cap DFS solver; child-player intervals are sign-reversed back to the
original root player's perspective.
"""
from .games import GameSpec, State
from .v212_minimax_bounds_v01 import MinimaxBounds, RegretInterval, ValueInterval
from .v212_minimax_transition_bounds_v01 import minimax_transition_bounds


def minimax_transition_balanced_bounds(
        game: GameSpec, state: State, executed_action: int,
        transition_budget: int) -> MinimaxBounds:
    """Bound every root action under an evenly split hard transition cap."""
    if type(transition_budget) is not int or transition_budget < 0:
        raise ValueError("transition_budget must be a nonnegative integer")
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
    if transition_budget < len(root_actions):
        raise ValueError("transition_budget cannot cover the complete root action set")

    remaining = transition_budget - len(root_actions)
    quotient, remainder = divmod(remaining, len(root_actions))
    action_values = []
    expanded = 0
    transitions = len(root_actions)

    for index, action in enumerate(root_actions):
        child = game.transition(state, action)
        outcome = game.terminal(child)
        if outcome is not None:
            value = state.player * outcome
            action_values.append((action, ValueInterval(value, value)))
            continue

        branch_budget = quotient + (index < remainder)
        child_actions = tuple(game.legal_actions(child))
        if not child_actions:
            raise ValueError("nonterminal root child has no legal actions")
        if branch_budget < len(child_actions):
            action_values.append((action, ValueInterval(-1, 1)))
            continue

        branch = minimax_transition_bounds(game, child, child_actions[0],
                                           branch_budget)
        # The branch solver values the child state from its side-to-move
        # perspective, which is the opposite of the original root player.
        action_values.append((action, ValueInterval(-branch.root_value.upper,
                                                    -branch.root_value.lower)))
        # The subsolver excludes its input root from its own count; here that
        # state is a descendant of the original root and was fully expanded.
        expanded += branch.expanded_nodes + 1
        transitions += branch.transition_count

    root_value = ValueInterval(
        max(value.lower for _, value in action_values),
        max(value.upper for _, value in action_values),
    )
    executed = dict(action_values)[executed_action]
    regret = RegretInterval(
        max(0, root_value.lower - executed.upper),
        min(2, root_value.upper - executed.lower),
    )
    return MinimaxBounds(state.player, tuple(action_values), root_value, regret,
                         expanded, transitions)
