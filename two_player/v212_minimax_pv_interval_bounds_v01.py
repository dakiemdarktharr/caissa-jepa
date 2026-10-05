"""Hard-budget minimax interval refinement along bound-critical PVs.

This is an isolated synthetic research candidate, not a selected reference
policy. It alternates deterministic lower/upper principal-variation targets
for the root value and the executed root action. Every expanded nonterminal
node still enumerates its complete legal successor set.
"""
from dataclasses import dataclass, field

from .games import GameSpec, State
from .v212_minimax_bounds_v01 import MinimaxBounds, RegretInterval, ValueInterval


@dataclass
class _Node:
    state: State
    interval: ValueInterval
    expanded: bool = False
    children: list[tuple[int, "_Node"]] = field(default_factory=list)
    parent: "_Node | None" = None


def _terminal_interval(game: GameSpec, node: State, root_player: int):
    outcome = game.terminal(node)
    if outcome is None:
        return None
    value = root_player * outcome
    return ValueInterval(value, value)


def minimax_pv_interval_bounds(game: GameSpec, state: State,
                               executed_action: int,
                               transition_budget: int) -> MinimaxBounds:
    """Return sound W/D/L intervals under a hard rule-transition cap.

    Root transitions are mandatory and consume budget. Thereafter, the solver
    cycles through lower/upper critical paths for the root value and executed
    action. A node is expanded only when its full legal successor set fits in
    the remaining budget. Ties follow the game's stable legal-action order.
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
    transitions = 0
    expanded = 0
    root_node = _Node(state, ValueInterval(-1, 1), expanded=True)
    root_children: list[tuple[int, _Node]] = []
    for action in root_actions:
        child_state = game.transition(state, action)
        transitions += 1
        interval = _terminal_interval(game, child_state, root_player)
        if interval is None:
            interval = ValueInterval(-1, 1)
        root_children.append((action, _Node(child_state, interval,
                                            parent=root_node)))
    root_node.children = root_children

    def backup_path(node: _Node | None) -> None:
        while node is not None:
            if node.expanded:
                values = [child.interval for _, child in node.children]
                if node.state.player == root_player:
                    node.interval = ValueInterval(max(x.lower for x in values),
                                                  max(x.upper for x in values))
                else:
                    node.interval = ValueInterval(min(x.lower for x in values),
                                                  min(x.upper for x in values))
            node = node.parent

    def critical_leaves(node: _Node, endpoint: str):
        if not node.expanded:
            if game.terminal(node.state) is None:
                yield node
            return
        if not node.children:
            return
        maximizing = node.state.player == root_player
        endpoint_values = [getattr(child.interval, endpoint)
                           for _, child in node.children]
        critical_value = (max(endpoint_values) if maximizing
                          else min(endpoint_values))
        # Preserve every tied bound-critical continuation. Choosing only the
        # first tied child can repeatedly land on a resolved leaf and leave
        # other equally influential frontier leaves untouched.
        for _, child in node.children:
            if getattr(child.interval, endpoint) == critical_value:
                # Yield lazily: a candidate is expanded before traversing
                # other tied continuations, avoiding a full-tree scan per
                # expansion when many frontier bounds are identical.
                yield from critical_leaves(child, endpoint)

    def choose_paths(endpoint: str, *, root_target: bool):
        if root_target:
            values = [getattr(node.interval, endpoint)
                      for _, node in root_children]
            critical_value = max(values)
            candidates = [node for _, node in root_children
                          if getattr(node.interval, endpoint) == critical_value]
        else:
            candidates = [node for action, node in root_children
                          if action == executed_action]
        for candidate in candidates:
            yield from critical_leaves(candidate, endpoint)

    # Each pass gives direct attention to regret's selected-action value and
    # the root optimum. The fixed order is part of this candidate's policy.
    target_cycle = (("upper", False), ("lower", True),
                    ("lower", False), ("upper", True))
    cursor = 0
    while remaining:
        selected = None
        checked: set[int] = set()
        for offset in range(len(target_cycle)):
            endpoint, root_target = target_cycle[(cursor + offset) % len(target_cycle)]
            for candidate in choose_paths(endpoint, root_target=root_target):
                if id(candidate) in checked:
                    continue
                checked.add(id(candidate))
                actions = tuple(game.legal_actions(candidate.state))
                if not actions:
                    raise ValueError("nonterminal state has no legal actions")
                if len(actions) <= remaining:
                    selected = (candidate, actions)
                    cursor = (cursor + offset + 1) % len(target_cycle)
                    break
            if selected is not None:
                break
        if selected is None:
            break

        node, actions = selected
        remaining -= len(actions)
        transitions += len(actions)
        expanded += 1
        node.children = []
        for action in actions:
            child_state = game.transition(node.state, action)
            interval = _terminal_interval(game, child_state, root_player)
            if interval is None:
                interval = ValueInterval(-1, 1)
            node.children.append((action, _Node(child_state, interval,
                                                parent=node)))
        node.expanded = True
        backup_path(node)

    root_values = [(action, node.interval) for action, node in root_children]
    root_interval = root_node.interval
    executed = dict(root_values)[executed_action]
    regret = RegretInterval(
        max(0, root_interval.lower - executed.upper),
        min(2, root_interval.upper - executed.lower),
    )
    return MinimaxBounds(root_player, tuple(root_values), root_interval, regret,
                         expanded, transitions)
