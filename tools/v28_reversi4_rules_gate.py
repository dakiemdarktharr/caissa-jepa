"""Model-blind exhaustive rules audit for the project-owned Reversi4 adapter.

The independent coordinate-ray oracle here is original project code. It is used
only to compare rules, action legality and deterministic transitions; this tool
does not generate training data or evaluate a model.
"""

import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from two_player.games import BoardGame, State


GAME = BoardGame("reversi4-gate", 4, 4, 0, reversi=True)
DIRECTIONS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))


@lru_cache(maxsize=None)
def reference_flips(state, action):
    row, col = divmod(action, 4)
    if not (0 <= row < 4 and 0 <= col < 4) or state.board[row * 4 + col] != 0:
        return ()
    flips = []
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        ray = []
        while 0 <= r < 4 and 0 <= c < 4 and state.board[r * 4 + c] == -state.player:
            ray.append(r * 4 + c)
            r += dr
            c += dc
        if ray and 0 <= r < 4 and 0 <= c < 4 and state.board[r * 4 + c] == state.player:
            flips.extend(ray)
    return tuple(flips)


@lru_cache(maxsize=None)
def reference_placements(state):
    moves = []
    for index, value in enumerate(state.board):
        if value == 0 and reference_flips(state, index):
            row, col = divmod(index, 4)
            moves.append(row * 8 + col)
    return tuple(moves)


@lru_cache(maxsize=None)
def reference_terminal(state):
    if reference_placements(state) or reference_placements(State(state.board, -state.player)):
        return None
    score = sum(state.board)
    return (score > 0) - (score < 0)


@lru_cache(maxsize=None)
def reference_legal_actions(state):
    if reference_terminal(state) is not None:
        return ()
    placements = reference_placements(state)
    return placements if placements else (64,)


def reference_transition(state, action):
    if action not in reference_legal_actions(state):
        raise ValueError("illegal reference action")
    if action == 64:
        return State(state.board, -state.player)
    row, col = divmod(action, 8)
    index = row * 4 + col
    board = list(state.board)
    board[index] = state.player
    for flipped in reference_flips(state, index):
        board[flipped] = state.player
    return State(tuple(board), -state.player)


def audit(state_limit=None):
    if state_limit is not None and (type(state_limit) is not int or state_limit < 1):
        raise ValueError("state_limit must be a positive integer or None")
    began = time.perf_counter()
    cpu_began = time.process_time()
    initial = GAME.initial()
    pending = [initial]
    visited = set()
    state_hash = hashlib.sha256()
    legal_actions = 0
    transitions = 0
    terminal_states = 0
    forced_pass_states = 0
    two_ply_pairs = 0
    max_branching = 0
    max_features_abs = 0.0

    while pending:
        if state_limit is not None and len(visited) >= state_limit:
            break
        state = pending.pop()
        key = (state.board, state.player)
        if key in visited:
            continue
        visited.add(key)
        terminal = GAME.terminal(state)
        reference_outcome = reference_terminal(state)
        if terminal != reference_outcome:
            raise AssertionError(f"terminal mismatch at {key}: {terminal} != {reference_outcome}")
        actions = GAME.legal_actions(state)
        expected_actions = reference_legal_actions(state)
        if actions != expected_actions:
            raise AssertionError(f"legal-action mismatch at {key}: {actions} != {expected_actions}")
        features = GAME.features(state)
        if features.shape != (198,) or not all(map(lambda x: x == x and abs(x) < float("inf"), features)):
            raise AssertionError("invalid feature vector")
        max_features_abs = max(max_features_abs, float(abs(features).max()))
        if terminal is not None:
            terminal_states += 1
        else:
            legal_actions += len(actions)
            max_branching = max(max_branching, len(actions))
            if actions == (64,):
                forced_pass_states += 1
            for action in actions:
                next_state = GAME.transition(state, action)
                reference_next = reference_transition(state, action)
                if next_state != reference_next:
                    raise AssertionError(f"transition mismatch at {key}, action={action}")
                transitions += 1
                pending.append(next_state)
                if GAME.terminal(next_state) is None:
                    replies = GAME.legal_actions(next_state)
                    two_ply_pairs += len(replies)
        state_hash.update(json.dumps([list(state.board), state.player], separators=(",", ":")).encode())
        state_hash.update(b"\n")

    peak_bytes = None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCountersEx(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]

        counters = ProcessMemoryCountersEx()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        current_process = kernel32.GetCurrentProcess
        current_process.restype = wintypes.HANDLE
        get_memory = psapi.GetProcessMemoryInfo
        get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCountersEx), wintypes.DWORD]
        get_memory.restype = wintypes.BOOL
        if get_memory(current_process(), ctypes.byref(counters), counters.cb):
            peak_bytes = int(counters.PeakWorkingSetSize)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    source_paths = (ROOT / "tools" / "v28_reversi4_rules_gate.py", ROOT / "two_player" / "games.py")
    source_sha256 = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in source_paths}
    config = {"game": GAME.name, "rows": GAME.rows, "cols": GAME.cols,
              "directions": DIRECTIONS, "rules_version": "tiny-rules-v1"}
    return {
        "schema": "caissa-v28-reversi4-rules-gate-01",
        "stage": "model-blind exhaustive rules/runtime audit",
        "claim_status": "rules/transition evidence only; no data-split, strength, or JEPA claim",
        "source_commit": commit,
        "source_sha256": source_sha256,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "game": {"name": GAME.name, "rules_version": "tiny-rules-v1", "rows": 4, "cols": 4,
                 "players": 2, "alternating": True, "fully_observed": True,
                 "deterministic": True, "zero_sum": True},
        "environment": {"python": platform.python_version(), "cpu_seconds": time.process_time() - cpu_began,
                         "wall_seconds": time.perf_counter() - began, "peak_working_set_bytes": peak_bytes},
        "coverage": {"reachable_states_including_terminal": len(visited), "terminal_states": terminal_states,
                     "nonterminal_states": len(visited) - terminal_states, "legal_actions_checked": legal_actions,
                     "transitions_differentially_checked": transitions, "forced_pass_states": forced_pass_states,
                     "complete_two_ply_reply_pairs": two_ply_pairs, "maximum_legal_branching": max_branching,
                     "max_absolute_feature": max_features_abs, "reachable_state_set_sha256": state_hash.hexdigest(),
                     "complete_enumeration": not pending},
        "checks": {"terminal_outcome": "pass", "legal_actions_and_forced_pass": "pass",
                   "all_reachable_legal_transitions": "pass", "feature_shape_and_finiteness": "pass"},
        "not_yet_audited": ["trajectory/event split and leakage", "opponent bank and evaluation power",
                            "JEPA versus direct baseline compute parity", "cross-game generalization"],
        "training_started": False,
        "data_generated": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit()
    raw = json.dumps(receipt, indent=2, allow_nan=False).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "states": receipt["coverage"]["reachable_states_including_terminal"],
                      "transitions": receipt["coverage"]["transitions_differentially_checked"],
                      "two_ply_pairs": receipt["coverage"]["complete_two_ply_reply_pairs"],
                      "sha256": hashlib.sha256(raw).hexdigest()}, allow_nan=False))


if __name__ == "__main__":
    main()
