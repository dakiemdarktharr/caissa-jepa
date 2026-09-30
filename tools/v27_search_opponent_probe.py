"""Model-blind bounded-search opponent and rules feasibility probe for V2.7."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.reference_rules import ReferenceGame
from benchmarks.v27_search_opponent import DepthLimitedOpponent

SEEDS = (270701, 270702)
PAIRINGS = (("random", "random"), ("search", "random"),
            ("search", "center"), ("search", "search"))
GAME_CONFIGS = (
    ("connect4-gravity-8x8", ReferenceGame(8, 8, 4, gravity=True)),
    ("reversi8", ReferenceGame(8, 8, 0, reversi=True)),
)
MAX_DEPTH = 3
NODE_LIMIT = 500


def choose(game, state, policy, rng, search):
    legal = game.legal_actions(state)
    if policy == "random":
        return rng.choice(legal), None
    if policy == "search":
        action = search.choose_action(state, rng)
        stats = {"nodes": search.stats.nodes,
                 "completed_depth": search.stats.completed_depth,
                 "exhausted": search.stats.exhausted}
        return action, stats
    if policy != "center":
        raise ValueError(f"Unknown policy {policy!r}")
    if game.reversi:
        corners = {0, game.cols - 1, (game.rows - 1) * game.cols,
                   game.rows * game.cols - 1}
        action = min(legal, key=lambda a: (a not in corners,
                                           abs(2 * (a % game.cols) - (game.cols - 1)), a))
    else:
        action = min(legal, key=lambda a: (
            abs(2 * (a % game.cols) - (game.cols - 1)), a
        ))
    return action, None


def play(game, seed, plus_policy, minus_policy):
    # Keep the RNG stream attached to the absolute seat so swapping policies
    # does not also silently swap or shift the randomness source.
    seat_rng = {1: random.Random(seed + 1), -1: random.Random(seed + 2)}
    state = game.initial()
    plies = 0
    search_nodes = []
    search_depths = []
    exhausted = 0
    while game.terminal(state) is None:
        if plies > game.rows * game.cols + 4:
            raise RuntimeError("Game exceeded finite placement/pass bound")
        policy = plus_policy if state.player == 1 else minus_policy
        action, stats = choose(game, state, policy, seat_rng[state.player],
                               DepthLimitedOpponent(game, MAX_DEPTH, NODE_LIMIT)
                               if policy == "search" else None)
        if action not in game.legal_actions(state):
            raise RuntimeError("Policy returned an illegal action")
        if stats:
            search_nodes.append(stats["nodes"])
            search_depths.append(stats["completed_depth"])
            exhausted += stats["exhausted"]
        state = game.transition(state, action)
        plies += 1
    board = bytes(value + 1 for value in game.board(state))
    encoded = board + bytes((1 if state.player == 1 else 0,))
    return {
        "outcome_plus_perspective": game.terminal(state),
        "plies": plies,
        "final_state_sha256": hashlib.sha256(encoded).hexdigest(),
        "search_calls": len(search_nodes),
        "search_nodes": sum(search_nodes),
        "mean_search_depth": (sum(search_depths) / len(search_depths)
                              if search_depths else None),
        "node_cap_exhaustions": exhausted,
    }


def run_probe():
    started = time.perf_counter()
    matches = []
    for game_name, game in GAME_CONFIGS:
        for pairing_index, (first, second) in enumerate(PAIRINGS):
            for seed in SEEDS:
                for seat_swap in (False, True):
                    plus, minus = ((second, first) if seat_swap else (first, second))
                    actual_seed = seed + pairing_index * 10_000
                    matches.append({
                        "game": game_name,
                        "pairing": f"{first}-vs-{second}",
                        "seat_swap": seat_swap,
                        "seed": actual_seed,
                        **play(game, actual_seed, plus, minus),
                    })
    summary = {}
    for game_name, _ in GAME_CONFIGS:
        rows = [row for row in matches if row["game"] == game_name]
        summary[game_name] = {
            "matches": len(rows),
            "wins_plus": sum(row["outcome_plus_perspective"] == 1 for row in rows),
            "draws": sum(row["outcome_plus_perspective"] == 0 for row in rows),
            "wins_minus": sum(row["outcome_plus_perspective"] == -1 for row in rows),
            "mean_plies": sum(row["plies"] for row in rows) / len(rows),
            "search_calls": sum(row["search_calls"] for row in rows),
            "search_node_cap_exhaustions": sum(row["node_cap_exhaustions"] for row in rows),
        }
    return {
        "pilot_version": "v2-seat-seeded-tie-order",
        "stage": "exploratory model-blind bounded-search opponent feasibility; not a strength benchmark",
        "rules_source": "project-owned independent bitboard ReferenceGame; differential agreement with BoardGame is not external validation",
        "game_configs": [name for name, _ in GAME_CONFIGS],
        "pairings": [list(pairing) for pairing in PAIRINGS],
        "base_seeds": list(SEEDS),
        "search": {"max_depth": MAX_DEPTH, "per_move_node_limit": NODE_LIMIT,
                   "ordering": "center-first; reversi corners-first; randomized within equal-priority groups",
                   "randomness": "independent deterministic RNG streams attached to absolute seat; same base seed for paired seat swaps"},
        "source_sha256": {
            "probe": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "search_opponent": hashlib.sha256((ROOT / "benchmarks" / "v27_search_opponent.py").read_bytes()).hexdigest(),
            "reference_rules": hashlib.sha256((ROOT / "benchmarks" / "reference_rules.py").read_bytes()).hexdigest(),
        },
        "matches": matches,
        "summary": summary,
        "elapsed_seconds": time.perf_counter() - started,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "claim_limit": "Two seeds and a shallow handcrafted evaluator do not establish opponent strength, JEPA benefit, or Q1 readiness.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_probe()
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")


if __name__ == "__main__":
    main()
