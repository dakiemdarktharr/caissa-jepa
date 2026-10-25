"""Hard transition-budget minimax interval candidate for synthetic fixtures.

Unlike the expansion-count candidate, this budget includes every rule
transition, including all root actions. It does not impose a wall-time bound:
terminal checks and legal-action enumeration are still cooperative Python work.
"""
from .games import GameSpec, State
from .v212_minimax_bounds_v01 import MinimaxBounds, RegretInterval, ValueInterval


def minimax_transition_bounds(game: GameSpec, state: State,
                              executed_action: int,
                              transition_budget: int) -> MinimaxBounds:
    """Return sound W/D/L intervals without exceeding rule-transition budget.

    Every expanded nonterminal node is admitted atomically only if the budget
    can cover all of its legal successor transitions. If not, that node stays
    unresolved at [-1,+1]. The complete root action set is mandatory, so a
    budget smaller than the number of root actions is rejected.
    """
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
    transitions = len(root_actions)
    expanded = 0

    def visit(node: State) -> ValueInterval:
        nonlocal remaining, transitions, expanded
        outcome = game.terminal(node)
        if outcome is not None:
            value = state.player * outcome
            return ValueInterval(value, value)

        actions = tuple(game.legal_actions(node))
        if not actions:
            raise ValueError("nonterminal state has no legal actions")
        if len(actions) > remaining:
            return ValueInterval(-1, 1)

        # Reserve the entire successor set before recursing: never propagate
        # an expanded node from a partial list of legal children.
        remaining -= len(actions)
        transitions += len(actions)
        expanded += 1
        children = [visit(game.transition(node, action)) for action in actions]
        if node.player == state.player:
            return ValueInterval(max(child.lower for child in children),
                                 max(child.upper for child in children))
        return ValueInterval(min(child.lower for child in children),
                             min(child.upper for child in children))

    action_values = []
    for action in root_actions:
        child = game.transition(state, action)
        action_values.append((action, visit(child)))

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
