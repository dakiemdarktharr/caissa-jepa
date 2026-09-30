"""Deterministic bounded search policy for V2.7 opponent-bank feasibility.

Uses the project's independent bitboard reference rules, not learned outputs.
This lightweight evaluator is a pilot opponent only; it is not an engine-strength
reference or an independent external referee.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

class _BudgetExhausted(Exception):
    pass


@dataclass
class SearchStats:
    completed_depth: int = 0
    nodes: int = 0
    cutoffs: int = 0
    exhausted: bool = False


class DepthLimitedOpponent:
    """Iterative-deepening negamax with fail-soft alpha-beta and node cap."""

    def __init__(self, game, max_depth: int = 3, node_limit: int = 20_000):
        if type(max_depth) is not int or max_depth < 1:
            raise ValueError("max_depth must be a positive integer")
        if type(node_limit) is not int or node_limit < 1:
            raise ValueError("node_limit must be a positive integer")
        self.game = game
        self.max_depth = max_depth
        self.node_limit = node_limit
        self.stats = SearchStats()

    def _evaluate(self, state) -> int:
        terminal = self.game.terminal(state)
        if terminal is not None:
            return state.player * terminal * 100_000

        if self.game.reversi:
            board = self.game.board(state)
            me = state.player
            occupied = sum(value != 0 for value in board)
            difference = sum(board) * me
            mobility = len(self.game.legal_actions(state)) - len(
                self.game.legal_actions(type(state)(state.plus, state.minus, -state.player))
            )
            corners = (0, self.game.cols - 1,
                       (self.game.rows - 1) * self.game.cols,
                       self.game.rows * self.game.cols - 1)
            corner_balance = sum(board[index] == me for index in corners) - sum(
                board[index] == -me for index in corners
            )
            # Disc count matters more near the end; mobility and corners matter
            # throughout. Keep the scale far below a terminal win/loss.
            disc_weight = 1 + occupied // 8
            return disc_weight * difference + 5 * mobility + 30 * corner_balance

        mine = state.plus if state.player == 1 else state.minus
        theirs = state.minus if state.player == 1 else state.plus
        value = 0
        for mask in self.game.winning_masks:
            own = (mine & mask).bit_count()
            other = (theirs & mask).bit_count()
            if own and other:
                continue
            if own:
                value += 3 ** own
            elif other:
                value -= 3 ** other
        for index in range(self.game.rows * self.game.cols):
            row, col = divmod(index, self.game.cols)
            cell_weight = max(1, self.game.cols - abs(2 * col - (self.game.cols - 1)))
            if mine & (1 << index):
                value += cell_weight
            elif theirs & (1 << index):
                value -= cell_weight
        return value

    def _visit(self, state, depth: int, alpha: int, beta: int) -> int:
        if self.stats.nodes >= self.node_limit:
            raise _BudgetExhausted
        self.stats.nodes += 1
        terminal = self.game.terminal(state)
        if terminal is not None or depth == 0:
            return self._evaluate(state)
        actions = self.game.legal_actions(state)
        best = -200_000
        for action in actions:
            child = self.game.transition(state, action)
            value = -self._visit(child, depth - 1, -beta, -alpha)
            if value > best:
                best = value
            if value > alpha:
                alpha = value
            if alpha >= beta:
                self.stats.cutoffs += 1
                break
        return best

    def _canonical_reversi(self, state):
        """Normalize role and board orientation, retaining every canonical map.

        Randomly choosing among tied canonical maps makes decisions equivariant
        in distribution when a position has spatial symmetries. The internal
        search then sees the same player-relative canonical board for color and
        dihedral transforms of the original position.
        """
        if self.game.rows != self.game.cols:
            raise ValueError("Reversi symmetry normalization requires a square board")
        board = self.game.board(state)
        best_board = None
        best_mappings = []
        for mirror in (False, True):
            for rotation in range(4):
                mapping = []
                for row in range(self.game.rows):
                    for col in range(self.game.cols):
                        rr, cc = row, (self.game.cols - 1 - col if mirror else col)
                        for _ in range(rotation):
                            rr, cc = cc, self.game.rows - 1 - rr
                        mapping.append(rr * self.game.cols + cc)
                relative = [0] * len(board)
                for old, new in enumerate(mapping):
                    relative[new] = board[old] * state.player
                candidate = tuple(relative)
                if best_board is None or candidate < best_board:
                    best_board = candidate
                    best_mappings = [tuple(mapping)]
                elif candidate == best_board:
                    best_mappings.append(tuple(mapping))
        canonical_state = self.game.from_board(best_board, player=1)
        return canonical_state, tuple(best_mappings)

    def _choose_in_frame(self, state, rng: random.Random | None) -> int:
        legal = self.game.legal_actions(state)
        if not legal:
            raise ValueError("Cannot choose an action from a terminal state")
        best_action = legal[0]
        for depth in range(1, self.max_depth + 1):
            iteration_action = best_action
            iteration_value = -200_000
            alpha = -200_000
            try:
                if self.game.reversi:
                    corners = {0, self.game.cols - 1,
                               (self.game.rows - 1) * self.game.cols,
                               self.game.rows * self.game.cols - 1}
                    priority = lambda a: (a not in corners,
                                          abs(2 * (a % self.game.cols) - (self.game.cols - 1)))
                else:
                    priority = lambda a: (abs(2 * (a % self.game.cols) - (self.game.cols - 1)),)
                groups = {}
                for action in legal:
                    groups.setdefault(priority(action), []).append(action)
                actions = []
                for key in sorted(groups):
                    group = sorted(groups[key])
                    if rng is not None:
                        rng.shuffle(group)
                    actions.extend(group)
                for action in actions:
                    value = -self._visit(
                        self.game.transition(state, action), depth - 1,
                        -200_000, -alpha,
                    )
                    if value > iteration_value:
                        iteration_value, iteration_action = value, action
                    alpha = max(alpha, value)
            except _BudgetExhausted:
                self.stats.exhausted = True
                break
            best_action = iteration_action
            self.stats.completed_depth = depth
        return best_action

    def choose_action(self, state, rng: random.Random | None = None) -> int:
        legal = self.game.legal_actions(state)
        if not legal:
            raise ValueError("Cannot choose an action from a terminal state")
        self.stats = SearchStats()
        if not self.game.reversi:
            return self._choose_in_frame(state, rng)

        canonical_state, mappings = self._canonical_reversi(state)
        mapping = rng.choice(mappings) if rng is not None else mappings[0]
        canonical_action = self._choose_in_frame(canonical_state, rng)
        if canonical_action == -1:
            return -1
        inverse = {new: old for old, new in enumerate(mapping)}
        action = inverse[canonical_action]
        if action not in legal:
            raise RuntimeError("Canonical search returned an illegal original-frame action")
        return action
