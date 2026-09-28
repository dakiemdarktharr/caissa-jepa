"""Exact tiny-game adapters. Project-owned implementation; no external engine.

State is immutable, player is absolute +/-1, reward is absolute +1 perspective.
Action IDs use an 8x8 grid; 64 is the forced Reversi pass.
"""
from dataclasses import dataclass
from typing import Protocol, Optional
import hashlib
import json
import numpy as np

RULES_VERSION = "tiny-rules-v1"
ACTION_SIZE = 65
FEATURE_SIZE = 198  # 3*64 + rows/cols/k + placement/reversi/gravity


@dataclass(frozen=True)
class State:
    board: tuple
    player: int = 1


class GameSpec(Protocol):
    name: str
    rows: int
    cols: int
    def initial(self) -> State: ...
    def legal_actions(self, state: State) -> tuple: ...
    def transition(self, state: State, action: int) -> State: ...
    def terminal(self, state: State) -> Optional[int]: ...
    def canonical_key(self, state: State) -> str: ...


@dataclass(frozen=True)
class BoardGame:
    name: str
    rows: int
    cols: int
    k: int = 3
    gravity: bool = False
    reversi: bool = False

    def __post_init__(self):
        if not 2 <= self.rows <= 8 or not 2 <= self.cols <= 8:
            raise ValueError("Board dimensions must be between 2 and 8")
        if self.reversi and (self.rows != self.cols or self.rows % 2 or self.gravity):
            raise ValueError("Reversi requires an even square without gravity")
        if not self.reversi and not 2 <= self.k <= max(self.rows, self.cols):
            raise ValueError("Invalid connection target")

    def validate(self, state):
        if state.player not in (-1, 1) or len(state.board) != self.rows*self.cols:
            raise ValueError("State shape/player mismatch")
        if any(type(x) is not int or x not in (-1, 0, 1) for x in state.board):
            raise ValueError("Board must contain integer -1/0/+1")

    def initial(self):
        board = [0] * (self.rows*self.cols)
        if self.reversi:
            m = self.rows//2
            for r, c, v in ((m-1,m-1,-1), (m,m,-1), (m-1,m,1), (m,m-1,1)):
                board[r*self.cols+c] = v
        return State(tuple(board))

    def flips(self, state, action):
        r, c = divmod(action, 8)
        if not (0 <= r < self.rows and 0 <= c < self.cols) or state.board[r*self.cols+c]:
            return ()
        flips = []
        for dr, dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            rr, cc, line = r+dr, c+dc, []
            while 0 <= rr < self.rows and 0 <= cc < self.cols and state.board[rr*self.cols+cc] == -state.player:
                line.append(rr*self.cols+cc)
                rr, cc = rr+dr, cc+dc
            if line and 0 <= rr < self.rows and 0 <= cc < self.cols and state.board[rr*self.cols+cc] == state.player:
                flips.extend(line)
        return tuple(flips)

    def placements(self, state):
        if self.reversi:
            return tuple(r*8+c for r in range(self.rows) for c in range(self.cols) if self.flips(state,r*8+c))
        if self.gravity:
            result=[]
            for c in range(self.cols):
                for r in reversed(range(self.rows)):
                    if not state.board[r*self.cols+c]:
                        result.append(r*8+c)
                        break
            return tuple(result)
        return tuple(r*8+c for r in range(self.rows) for c in range(self.cols) if not state.board[r*self.cols+c])

    def terminal(self, state):
        self.validate(state)
        if self.reversi:
            if self.placements(state) or self.placements(State(state.board,-state.player)):
                return None
            score=sum(state.board)
            return (score>0)-(score<0)
        for r in range(self.rows):
            for c in range(self.cols):
                v=state.board[r*self.cols+c]
                if not v:
                    continue
                for dr,dc in ((0,1),(1,0),(1,1),(1,-1)):
                    if 0 <= r+(self.k-1)*dr < self.rows and 0 <= c+(self.k-1)*dc < self.cols:
                        if all(state.board[(r+i*dr)*self.cols+c+i*dc]==v for i in range(self.k)):
                            return v
        return None if 0 in state.board else 0

    def legal_actions(self, state):
        if self.terminal(state) is not None:
            return ()
        actions=self.placements(state)
        return actions if actions else (64,)

    def transition(self, state, action):
        if type(action) is not int or action not in self.legal_actions(state):
            raise ValueError("Illegal action or transition from terminal state")
        if action == 64:
            return State(state.board,-state.player)
        r,c=divmod(action,8)
        board=list(state.board)
        board[r*self.cols+c]=state.player
        if self.reversi:
            for index in self.flips(state,action):
                board[index]=state.player
        return State(tuple(board),-state.player)

    def transforms(self):
        # Rectangles allow flips/180 degrees; gravity allows horizontal only.
        maps=[]
        for rotation in (range(4) if self.rows==self.cols and not self.gravity else (0,)):
            for mirror in (False,True):
                mapping=[]
                for r in range(self.rows):
                    for c in range(self.cols):
                        rr,cc=r,self.cols-1-c if mirror else c
                        for _ in range(rotation):
                            rr,cc=cc,self.rows-1-rr
                        mapping.append(rr*self.cols+cc)
                maps.append(tuple(mapping))
        if self.rows!=self.cols and not self.gravity:
            maps.extend(tuple((self.rows-1-i//self.cols)*self.cols+i%self.cols for i in m) for m in list(maps))
        return tuple(maps)

    def transform(self,state,action,mapping):
        board=[0]*len(state.board)
        for i,j in enumerate(mapping):
            board[j]=state.board[i]
        if action==64:
            transformed=64
        else:
            r,c=divmod(action,8)
            rr,cc=divmod(mapping[r*self.cols+c],self.cols)
            transformed=rr*8+cc
        return State(tuple(board),state.player),transformed

    def canonical_key(self,state):
        self.validate(state)
        boards=[]
        for mapping in self.transforms():
            board=[0]*len(state.board)
            for i,j in enumerate(mapping):
                board[j]=state.board[i]*state.player
            boards.append(tuple(board))
        identity=(RULES_VERSION,self.rows,self.cols,self.k,self.gravity,self.reversi,min(boards))
        return hashlib.sha256(json.dumps(identity,separators=(',',':')).encode()).hexdigest()

    def features(self,state):
        self.validate(state)
        result=np.zeros(FEATURE_SIZE,dtype=np.float64)
        for r in range(self.rows):
            for c in range(self.cols):
                cell=r*8+c
                v=state.board[r*self.cols+c]*state.player
                result[cell]=v==1
                result[64+cell]=v==-1
                result[128+cell]=1
        result[192:]=[self.rows/8,self.cols/8,self.k/8,not self.reversi,self.reversi,self.gravity]
        return result


GAMES={
    'tic-tac-toe': BoardGame('tic-tac-toe',3,3),
    'connect3': BoardGame('connect3',4,4,3,gravity=True),
    'reversi4': BoardGame('reversi4',4,4,0,reversi=True),
    'connect3-heldout': BoardGame('connect3-heldout',3,4,3,gravity=True),
}


def exact_value(game,state,cache=None):
    """Unbudgeted tiny-game oracle; callers must restrict the state-space size."""
    if cache is None:
        cache={}
    key=(game,state)
    if key in cache:
        return cache[key]
    outcome=game.terminal(state)
    if outcome is not None:
        value=state.player*outcome
    else:
        value=max(-exact_value(game,game.transition(state,a),cache) for a in game.legal_actions(state))
    cache[key]=value
    return value
