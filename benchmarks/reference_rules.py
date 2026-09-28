"""Independent same-project tiny-game reference; NOT a third-party referee.

No imports from the research adapters, learned models, or NumPy. Boards use two
contiguous row-major bitboards; actions are cell indices, with -1 for forced
pass. Utilities are absolute player +1; solver values are player-to-move.
Differential agreement strengthens engineering evidence, not external validation.
"""
from dataclasses import asdict, dataclass
from functools import cached_property
import hashlib
import json
import math
from pathlib import Path
import time

REFERENCE_VERSION = "independent-bitboard-v1"
PASS = -1


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


@dataclass(frozen=True)
class ReferenceState:
    plus: int
    minus: int
    player: int = 1


@dataclass(frozen=True)
class ReferenceGame:
    rows: int
    cols: int
    k: int = 3
    gravity: bool = False
    reversi: bool = False

    def __post_init__(self):
        if any(type(x) is not int for x in (self.rows, self.cols, self.k)):
            raise ValueError("Integer rule dimensions are required")
        if not 2 <= self.rows <= 8 or not 2 <= self.cols <= 8:
            raise ValueError("Supported boards are 2..8 cells per dimension")
        if type(self.gravity) is not bool or type(self.reversi) is not bool:
            raise ValueError("Rule flags must be boolean")
        if self.reversi:
            if self.rows != 4 or self.cols != 4 or self.gravity or self.k != 0:
                raise ValueError("Reference Reversi is pinned to 4x4, k=0")
        elif not 2 <= self.k <= max(self.rows, self.cols):
            raise ValueError("Invalid connection length")

    @property
    def full_mask(self):
        return (1 << (self.rows * self.cols)) - 1

    def validate(self, state):
        if not isinstance(state, ReferenceState):
            raise ValueError("Expected ReferenceState")
        if any(type(x) is not int for x in (state.plus, state.minus, state.player)):
            raise ValueError("State bitboards/player must be integers")
        if state.player not in (-1, 1) or min(state.plus, state.minus) < 0:
            raise ValueError("Invalid player or negative bitboard")
        if state.plus & state.minus or (state.plus | state.minus) & ~self.full_mask:
            raise ValueError("Overlapping or out-of-board pieces")

    def from_board(self, board, player=1):
        if len(board) != self.rows * self.cols or any(type(v) is not int or v not in (-1, 0, 1) for v in board):
            raise ValueError("Invalid external board")
        state = ReferenceState(sum(1 << i for i, v in enumerate(board) if v == 1),
                               sum(1 << i for i, v in enumerate(board) if v == -1), player)
        self.validate(state)
        return state

    def board(self, state):
        self.validate(state)
        return tuple(1 if state.plus & (1 << i) else -1 if state.minus & (1 << i) else 0
                     for i in range(self.rows * self.cols))

    def initial(self):
        if self.reversi:
            return ReferenceState((1 << 6) | (1 << 9), (1 << 5) | (1 << 10))
        return ReferenceState(0, 0)

    @cached_property
    def winning_masks(self):
        # Construct complete rows/columns/diagonals, then their k-cell windows.
        if self.reversi:
            return ()
        lines = [[r * self.cols + c for c in range(self.cols)] for r in range(self.rows)]
        lines += [[r * self.cols + c for r in range(self.rows)] for c in range(self.cols)]
        for slope in (-1, 1):
            for offset in range(-self.rows, self.cols + self.rows):
                line = [r * self.cols + (offset + slope * r) for r in range(self.rows)
                        if 0 <= offset + slope * r < self.cols]
                if len(line) >= self.k:
                    lines.append(line)
        return tuple(sorted({sum(1 << cell for cell in line[start:start + self.k])
                             for line in lines for start in range(len(line) - self.k + 1)}))

    @cached_property
    def shifts(self):
        # Source masks prevent bit shifts from wrapping across row boundaries.
        return tuple((dr * self.cols + dc,
                      sum(1 << (r * self.cols + c) for r in range(self.rows) for c in range(self.cols)
                          if 0 <= r + dr < self.rows and 0 <= c + dc < self.cols))
                     for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)

    @staticmethod
    def _shift(bits, shift, sources):
        bits &= sources
        return bits << shift if shift >= 0 else bits >> -shift

    def captures(self, state, action):
        if type(action) is not int or not 0 <= action < self.rows * self.cols:
            return 0
        placed = 1 << action
        if placed & (state.plus | state.minus):
            return 0
        mine, opponent = (state.plus, state.minus) if state.player == 1 else (state.minus, state.plus)
        result = 0
        for shift, sources in self.shifts:
            cursor = self._shift(placed, shift, sources)
            captured = 0
            while cursor & opponent:
                captured |= cursor
                cursor = self._shift(cursor, shift, sources)
            if cursor & mine:
                result |= captured
        return result

    def placement_mask(self, state):
        empty = self.full_mask ^ (state.plus | state.minus)
        if self.reversi:
            return sum(1 << a for a in _bits(empty) if self.captures(state, a))
        if not self.gravity:
            return empty
        result = 0
        for c in range(self.cols):
            column = sum(1 << (r * self.cols + c) for r in range(self.rows))
            available = column & empty
            if available:
                result |= 1 << (available.bit_length() - 1)
        return result

    def terminal(self, state):
        """Absolute +1 outcome, or None. Reversi ends when neither can place."""
        self.validate(state)
        if self.reversi:
            other = ReferenceState(state.plus, state.minus, -state.player)
            if self.placement_mask(state) or self.placement_mask(other):
                return None
            difference = state.plus.bit_count() - state.minus.bit_count()
            return (difference > 0) - (difference < 0)
        plus_wins = any(state.plus & mask == mask for mask in self.winning_masks)
        minus_wins = any(state.minus & mask == mask for mask in self.winning_masks)
        if plus_wins and minus_wins:
            raise ValueError("Both players winning is unreachable under these rules")
        if plus_wins or minus_wins:
            return 1 if plus_wins else -1
        return 0 if state.plus | state.minus == self.full_mask else None

    def legal_actions(self, state):
        if self.terminal(state) is not None:
            return ()
        placements = tuple(_bits(self.placement_mask(state)))
        return placements if placements else (PASS,)

    def transition(self, state, action):
        if type(action) is not int or action not in self.legal_actions(state):
            raise ValueError("Illegal action or terminal transition")
        if action == PASS:
            return ReferenceState(state.plus, state.minus, -state.player)
        added = 1 << action
        flipped = self.captures(state, action) if self.reversi else 0
        if state.player == 1:
            return ReferenceState(state.plus | added | flipped, state.minus & ~flipped, -1)
        return ReferenceState(state.plus & ~flipped, state.minus | added | flipped, 1)

    def identity(self):
        source = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
        config = {"reference_version": REFERENCE_VERSION, **asdict(self),
                  "action_encoding": "contiguous row-major; forced pass=-1",
                  "terminal_utility": "absolute player +1; solver player-to-move",
                  "independence": "separate same-project implementation, not a third-party engine"}
        return {"config": config,
                "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "source_sha256": hashlib.sha256(source).hexdigest()}


class ReferenceBudgetExceeded(RuntimeError):
    """No approximate value is returned or cached for an incomplete subtree."""


class ReferenceSolver:
    """Bounded memoized exact negamax. Each public query has a fresh budget.

    A maximum value of +1 permits exact early termination. Cached values are
    exact, never alpha-beta bounds. action_values evaluates every legal action.
    Cache reuse and all counts are reported; costs are not benchmark timing.
    """
    def __init__(self, game, node_limit=500_000, time_limit=10., cache_limit=500_000):
        if type(node_limit) is not int or node_limit < 1 or type(cache_limit) is not int or cache_limit < 0:
            raise ValueError("Invalid solver node/cache budget")
        if not math.isfinite(time_limit) or not 0 < time_limit <= 60:
            raise ValueError("Solver time budget must be in (0, 60] seconds")
        self.game = game
        self.node_limit = node_limit
        self.time_limit = time_limit
        self.cache_limit = cache_limit
        self.cache = {}
        self.last_stats = {}

    def _visit(self, state):
        if time.perf_counter() >= self._deadline:
            raise ReferenceBudgetExceeded("Reference solver time budget exhausted")
        if state in self.cache:
            self.last_stats["cache_hits"] += 1
            return self.cache[state]
        if self.last_stats["nodes"] >= self.node_limit:
            raise ReferenceBudgetExceeded("Reference solver node budget exhausted")
        self.last_stats["nodes"] += 1
        terminal = self.game.terminal(state)
        if terminal is not None:
            self.last_stats["terminal_nodes"] += 1
            result = state.player * terminal
        else:
            result = -1
            for action in self.game.legal_actions(state):
                self.last_stats["transitions"] += 1
                result = max(result, -self._visit(self.game.transition(state, action)))
                if result == 1:
                    break
        if len(self.cache) < self.cache_limit:
            self.cache[state] = result
        return result

    def _query(self, state, all_actions):
        self.game.validate(state)
        started = time.perf_counter()
        self._deadline = started + self.time_limit
        self.last_stats = {"nodes": 0, "cache_hits": 0, "transitions": 0,
                           "terminal_nodes": 0, "complete": False}
        try:
            if all_actions:
                result = {}
                for action in self.game.legal_actions(state):
                    self.last_stats["transitions"] += 1
                    result[action] = -self._visit(self.game.transition(state, action))
            else:
                result = self._visit(state)
            if time.perf_counter() >= self._deadline:
                raise ReferenceBudgetExceeded("Late reference solver return")
            self.last_stats["complete"] = True
            return result
        finally:
            self.last_stats.update(seconds=time.perf_counter() - started, cache_entries=len(self.cache),
                                   node_limit=self.node_limit, time_limit=self.time_limit)

    def value(self, state):
        return self._query(state, False)

    def action_values(self, state):
        return self._query(state, True)
