"""Reproduce exploratory V2.6 exact-oracle cost probes.

The report contains completion/coverage and whether root action outcomes vary,
never exact action values or saved positions. It is not a dataset builder or
training command.
"""
import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.alpha_beta_reference import AlphaBetaReferenceSolver
from benchmarks.reference_rules import ReferenceGame, ReferenceBudgetExceeded
from two_player.games import BoardGame


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def connect4_roots(count=24, schedule_seed=26092926):
    game = BoardGame("connect4-4x5", 4, 5, 4)
    schedule_rng = random.Random(schedule_seed)
    for index in range(count):
        seed = 270000 + index
        target_ply = schedule_rng.randint(5, 11)
        rng = random.Random(seed)
        state = game.initial()
        for ply in range(target_ply):
            if game.terminal(state) is not None:
                break
            state = game.transition(state, rng.choice(game.legal_actions(state)))
        yield index, seed, target_ply, state


def reversi_roots(size, count=8):
    game = BoardGame(f"reversi{size}", size, size, 0, reversi=True)
    for index in range(count):
        seed = 280000 + size * 100 + index
        rng = random.Random(seed)
        state = game.initial()
        candidate = None
        for ply in range(size * size * 2 + 3):
            if game.terminal(state) is not None:
                break
            if state.board.count(0) <= 8 and candidate is None:
                candidate = (ply, state)
            state = game.transition(state, rng.choice(game.legal_actions(state)))
        if candidate is None:
            yield index, seed, None, None
        else:
            yield index, seed, candidate[0], candidate[1]


def inspect_root(adapter, reference, index, seed, ply, state, nodes, seconds):
    row = {"index": index, "seed": seed, "target_ply": ply,
           "terminal": state is None or adapter.terminal(state) is not None}
    if row["terminal"]:
        return row
    row["legal_actions"] = len(adapter.legal_actions(state))
    row["empty_cells"] = state.board.count(0)
    if adapter.name.startswith("connect4"):
        h2 = 0
        for action in adapter.legal_actions(state):
            child = adapter.transition(state, action)
            if adapter.terminal(child) is not None:
                continue
            for reply in adapter.legal_actions(child):
                leaf = adapter.transition(child, reply)
                h2 += adapter.terminal(leaf) is None
        row["nonterminal_h2_pairs"] = h2

    solver = AlphaBetaReferenceSolver(reference, node_limit=nodes,
                                      time_limit=seconds, cache_limit=nodes)
    started = time.perf_counter()
    try:
        values = solver.action_values(reference.from_board(state.board, state.player))
        row["complete"] = True
        row["distinct_action_outcomes"] = len(set(values.values()))
        row["informative"] = len(set(values.values())) > 1
    except ReferenceBudgetExceeded:
        row["complete"] = False
        row["distinct_action_outcomes"] = None
        row["informative"] = None
    row["nodes"] = solver.last_stats["nodes"]
    row["seconds"] = round(time.perf_counter() - started, 6)
    # Deliberately do not return/cache action values in this report.
    return row


def run(game_name, count, schedule_seed, nodes, seconds):
    if game_name == "connect4-4x5":
        adapter = BoardGame(game_name, 4, 5, 4)
        reference = ReferenceGame(4, 5, 4)
        roots = connect4_roots(count, schedule_seed)
    elif game_name in ("reversi6", "reversi8"):
        size = int(game_name[-1])
        adapter = BoardGame(game_name, size, size, 0, reversi=True)
        reference = ReferenceGame(size, size, 0, reversi=True)
        roots = reversi_roots(size, count)
    else:
        raise ValueError("Unsupported exploratory game")
    rows = [inspect_root(adapter, reference, *root, nodes, seconds) for root in roots]
    eligible = [row for row in rows if not row["terminal"]]
    completed = [row for row in eligible if row["complete"]]
    return {
        "stage": "exploratory model-blind oracle cost; exact action values are not retained",
        "game": game_name,
        "schedule_seed": schedule_seed if game_name == "connect4-4x5" else None,
        "candidate_count": count,
        "budget": {"nodes": nodes, "seconds": seconds},
        "summary": {
            "nonterminal_candidates": len(eligible),
            "completed": len(completed),
            "timeouts": len(eligible) - len(completed),
            "informative_completed": sum(row["informative"] is True for row in completed),
        },
        "roots": rows,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {
            "probe": sha256(__file__),
            "adapter": sha256(ROOT / "two_player/games.py"),
            "reference_rules": sha256(ROOT / "benchmarks/reference_rules.py"),
            "alpha_beta": sha256(ROOT / "benchmarks/alpha_beta_reference.py"),
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "claim_limit": "A tiny exploratory sample is not a solvability estimate, benchmark, or learned-model result.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=("connect4-4x5", "reversi6", "reversi8"))
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--schedule-seed", type=int, default=26092926)
    parser.add_argument("--nodes", type=int, default=100_000)
    parser.add_argument("--seconds", type=float, default=1.0)
    args = parser.parse_args()
    if args.count < 1 or args.nodes < 1 or not 0 < args.seconds <= 60:
        parser.error("count/nodes must be positive and seconds must be in (0,60]")
    print(json.dumps(run(args.game, args.count, args.schedule_seed,
                         args.nodes, args.seconds), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
