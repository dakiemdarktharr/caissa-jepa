"""Hard-budget minimax intervals with a single frontier-aware critical PV.

This isolated synthetic candidate shares the conservative interval backups
from v01 but uses a single tied continuation per endpoint and cached frontier
counts. It is not FSSS-Minimax and carries no claim of expansion optimality.
"""
from dataclasses import dataclass, field

from .games import GameSpec, State
from .v212_minimax_bounds_v01 import MinimaxBounds, RegretInterval, ValueInterval


@dataclass
class _Node:
    state: State
    interval: ValueInterval
    frontier_count: int
    expanded: bool = False
    children: list[tuple[int, "_Node"]] = field(default_factory=list)
    parent: "_Node | None" = None


def _terminal_interval(game: GameSpec, state: State, root_player: int):
    outcome = game.terminal(state)
    if outcome is None:
        return None
    value = root_player * outcome
    return ValueInterval(value, value)


def minimax_single_pv_bounds(game: GameSpec, state: State,
                             executed_action: int,
                             transition_budget: int) -> MinimaxBounds:
    """Return sound intervals under a hard rule-transition cap.

    Every root action is transitioned. Each further expansion is admitted only
    when all of its legal successors fit the remaining budget. The schedule
    cycles over executed/root lower/upper endpoints and follows one
    bound-critical path, preferring tied branches with more unresolved
    frontier nodes. Bound and frontier-count backups update only ancestors.
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

    root_player = state.player
    remaining = transition_budget - len(root_actions)
    transition_count = 0
    expanded_count = 0
    root_node = _Node(state, ValueInterval(-1, 1), 0, expanded=True)
    root_children: list[tuple[int, _Node]] = []
    frontier_nodes: list[_Node] = []
    for action in root_actions:
        child_state = game.transition(state, action)
        transition_count += 1
        interval = _terminal_interval(game, child_state, root_player)
        frontier_count = 0 if interval is not None else 1
        child = _Node(
            child_state, interval or ValueInterval(-1, 1), frontier_count,
            parent=root_node)
        root_children.append((action, child))
        if frontier_count:
            frontier_nodes.append(child)
    root_node.children = root_children
    root_node.frontier_count = sum(child.frontier_count
                                   for _, child in root_children)

    def backup_ancestors(node: _Node | None) -> None:
        while node is not None:
            if node.expanded:
                values = [child.interval for _, child in node.children]
                if node.state.player == root_player:
                    node.interval = ValueInterval(max(x.lower for x in values),
                                                  max(x.upper for x in values))
                else:
                    node.interval = ValueInterval(min(x.lower for x in values),
                                                  min(x.upper for x in values))
                node.frontier_count = sum(child.frontier_count
                                          for _, child in node.children)
            node = node.parent

    def critical_leaf(node: _Node, endpoint: str) -> _Node | None:
        while node.expanded:
            if not node.children:
                return None
            maximizing = node.state.player == root_player
            values = [getattr(child.interval, endpoint)
                      for _, child in node.children]
            critical_value = max(values) if maximizing else min(values)
            eligible = [child for _, child in node.children
                        if child.frontier_count
                        and getattr(child.interval, endpoint) == critical_value]
            if not eligible:
                return None
            # max() preserves the first item on a count tie, so legal-action
            # order remains the final deterministic tie-break.
            node = max(eligible, key=lambda child: child.frontier_count)
        return node if node.frontier_count else None

    def choose_leaf(endpoint: str, root_target: bool) -> _Node | None:
        if root_target:
            values = [getattr(child.interval, endpoint)
                      for _, child in root_children]
            critical_value = max(values)
            eligible = [child for _, child in root_children
                        if child.frontier_count
                        and getattr(child.interval, endpoint) == critical_value]
            if not eligible:
                return None
            start = max(eligible, key=lambda child: child.frontier_count)
        else:
            start = next(child for action, child in root_children
                         if action == executed_action)
        return critical_leaf(start, endpoint)

    target_cycle = (("upper", False), ("lower", True),
                    ("lower", False), ("upper", True))
    cursor = 0
    while remaining:
        selected = None
        for offset in range(len(target_cycle)):
            endpoint, root_target = target_cycle[(cursor + offset) % len(target_cycle)]
            candidate = choose_leaf(endpoint, root_target)
            if candidate is None:
                continue
            actions = tuple(game.legal_actions(candidate.state))
            if not actions:
                raise ValueError("nonterminal state has no legal actions")
            if len(actions) <= remaining:
                selected = (candidate, actions)
                cursor = (cursor + offset + 1) % len(target_cycle)
                break
        if selected is None:
            # Bound-critical paths can become temporarily non-refinable while
            # other unresolved frontiers remain. Use a deterministic FIFO
            # fallback rather than silently leaving most of the cap unused.
            for candidate in frontier_nodes:
                if candidate.expanded or not candidate.frontier_count:
                    continue
                actions = tuple(game.legal_actions(candidate.state))
                if len(actions) <= remaining:
                    selected = (candidate, actions)
                    break
            if selected is None:
                break

        node, actions = selected
        remaining -= len(actions)
        transition_count += len(actions)
        expanded_count += 1
        node.children = []
        for action in actions:
            child_state = game.transition(node.state, action)
            interval = _terminal_interval(game, child_state, root_player)
            frontier_count = 0 if interval is not None else 1
            child = _Node(
                child_state, interval or ValueInterval(-1, 1), frontier_count,
                parent=node)
            node.children.append((action, child))
            if frontier_count:
                frontier_nodes.append(child)
        node.expanded = True
        backup_ancestors(node)

    action_values = [(action, child.interval) for action, child in root_children]
    executed = dict(action_values)[executed_action]
    regret = RegretInterval(
        max(0, root_node.interval.lower - executed.upper),
        min(2, root_node.interval.upper - executed.lower),
    )
    return MinimaxBounds(root_player, tuple(action_values), root_node.interval,
                         regret, expanded_count, transition_count)
