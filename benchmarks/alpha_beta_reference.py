"""Bounded exact alpha-beta oracle over the independent reference rules.

This improves query efficiency only; the game implementation remains the
project-owned ``ReferenceGame``. Every returned action value is exact. A budget
exhaustion raises and never returns a partial action-value map.
"""
from dataclasses import dataclass
import math
import time

from .reference_rules import ReferenceBudgetExceeded, ReferenceState


EXACT, LOWER, UPPER = 0, 1, 2


@dataclass(frozen=True)
class Entry:
    value: int
    bound: int
    best_action: int | None


class AlphaBetaReferenceSolver:
    """Negamax alpha-beta with bound-aware transpositions and fail-closed caps."""

    def __init__(self, game, node_limit=500_000, time_limit=10., cache_limit=500_000):
        if type(node_limit) is not int or node_limit < 1:
            raise ValueError("Invalid node limit")
        if type(cache_limit) is not int or cache_limit < 0:
            raise ValueError("Invalid cache limit")
        if not math.isfinite(time_limit) or not 0 < time_limit <= 60:
            raise ValueError("Time limit must be in (0, 60]")
        self.game = game
        self.node_limit = node_limit
        self.time_limit = time_limit
        self.cache_limit = cache_limit
        self.table = {}
        self.last_stats = {}

    def _check(self):
        if time.perf_counter() >= self._deadline:
            raise ReferenceBudgetExceeded("Alpha-beta time budget exhausted")
        if self.last_stats["nodes"] >= self.node_limit:
            raise ReferenceBudgetExceeded("Alpha-beta node budget exhausted")

    def _search(self, state, alpha, beta):
        self._check()
        terminal = self.game.terminal(state)
        if terminal is not None:
            self.last_stats["terminal_nodes"] += 1
            return state.player * terminal

        original_alpha, original_beta = alpha, beta
        entry = self.table.get(state)
        if entry is not None:
            self.last_stats["cache_hits"] += 1
            if entry.bound == EXACT:
                return entry.value
            if entry.bound == LOWER:
                alpha = max(alpha, entry.value)
            else:
                beta = min(beta, entry.value)
            if alpha >= beta:
                return entry.value

        self.last_stats["nodes"] += 1
        actions = list(self.game.legal_actions(state))
        if entry is not None and entry.best_action in actions:
            actions.remove(entry.best_action)
            actions.insert(0, entry.best_action)
        # Stable center-first tie-break is deterministic and only changes speed.
        actions.sort(key=lambda a: (abs((a % self.game.cols) - self.game.cols // 2), a))
        if entry is not None and entry.best_action in actions:
            actions.remove(entry.best_action)
            actions.insert(0, entry.best_action)

        best_value = -2
        best_action = None
        for action in actions:
            self.last_stats["transitions"] += 1
            value = -self._search(self.game.transition(state, action), -beta, -alpha)
            if value > best_value:
                best_value, best_action = value, action
            alpha = max(alpha, value)
            if alpha >= beta:
                self.last_stats["cutoffs"] += 1
                break

        if best_value <= original_alpha:
            bound = UPPER
        elif best_value >= original_beta:
            bound = LOWER
        else:
            bound = EXACT
        if len(self.table) < self.cache_limit:
            previous = self.table.get(state)
            # Never replace an exact entry with a weaker bound.
            if previous is None or bound == EXACT or previous.bound != EXACT:
                self.table[state] = Entry(best_value, bound, best_action)
        return best_value

    def _begin(self):
        self._deadline = time.perf_counter() + self.time_limit
        self.last_stats = {"nodes": 0, "transitions": 0, "terminal_nodes": 0,
                           "cache_hits": 0, "cutoffs": 0, "complete": False}

    def value(self, state):
        self.game.validate(state)
        self._begin()
        try:
            value = self._search(state, -2, 2)
            if time.perf_counter() >= self._deadline:
                raise ReferenceBudgetExceeded("Late alpha-beta return")
            self.last_stats["complete"] = True
            return value
        finally:
            self.last_stats.update(seconds=time.perf_counter() - (self._deadline-self.time_limit),
                                   node_limit=self.node_limit, time_limit=self.time_limit,
                                   cache_entries=len(self.table))

    def action_values(self, state):
        self.game.validate(state)
        self._begin()
        started = self._deadline - self.time_limit
        try:
            result = {}
            for action in self.game.legal_actions(state):
                self._check()
                self.last_stats["transitions"] += 1
                result[action] = -self._search(self.game.transition(state, action), -2, 2)
            if time.perf_counter() >= self._deadline:
                raise ReferenceBudgetExceeded("Late alpha-beta return")
            self.last_stats["complete"] = True
            return result
        finally:
            self.last_stats.update(seconds=time.perf_counter() - started,
                                   node_limit=self.node_limit, time_limit=self.time_limit,
                                   cache_entries=len(self.table))
