"""Small model-blind match-schedule feasibility probe for the V2.7 proposal.

This is not a benchmark, strength estimate, training-data generator, or JEPA
experiment. It checks that project-owned larger variants terminate, seat-swapped
paired games can be replayed deterministically, and a tiny fixed opponent set
produces nonconstant outcomes within local CPU time.
"""
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

from two_player.games import BoardGame


SEEDS = tuple(range(701, 709))
POLICIES = ("random", "sanity-heuristic")
PAIRINGS = (("random", "random"), ("sanity-heuristic", "sanity-heuristic"),
            ("sanity-heuristic", "random"))
GAME_CONFIGS = (
    ("connect4-gravity-8x8", BoardGame("connect4-gravity-8x8", 8, 8, 4, gravity=True)),
    ("reversi8", BoardGame("reversi8", 8, 8, 0, reversi=True)),
)


def choose_action(game: BoardGame, state, policy: str, rng: random.Random) -> int:
    legal = game.legal_actions(state)
    if policy == "random" or legal == (64,):
        return rng.choice(legal)
    if policy != "sanity-heuristic":
        raise ValueError(f"Unknown pilot policy: {policy}")

    scored = []
    for action in legal:
        child = game.transition(state, action)
        outcome = game.terminal(child)
        score = 1000 if outcome == state.player else 0
        if outcome is None and game.gravity:
            # Penalize any move that leaves an immediate winning reply.
            if any(game.terminal(game.transition(child, reply)) == child.player
                   for reply in game.legal_actions(child)):
                score -= 900
        if outcome is None and game.reversi:
            row, col = divmod(action, 8)
            corners = ((0, 0), (0, game.cols - 1),
                       (game.rows - 1, 0), (game.rows - 1, game.cols - 1))
            score += 20 if (row, col) in corners else 0
            score += len(game.flips(state, action))
        scored.append((score, action))
    best = max(score for score, _ in scored)
    return rng.choice([action for score, action in scored if score == best])


def play(game: BoardGame, seed: int, plus_policy: str, minus_policy: str) -> dict:
    if plus_policy not in POLICIES or minus_policy not in POLICIES:
        raise ValueError("Unsupported pilot policy")
    rng = random.Random(seed)
    state = game.initial()
    plies = 0
    while game.terminal(state) is None:
        if plies > game.rows * game.cols + 4:
            raise RuntimeError("Game exceeded the finite placement/pass bound")
        policy = plus_policy if state.player == 1 else minus_policy
        state = game.transition(state, choose_action(game, state, policy, rng))
        plies += 1
    board_bytes = bytes((value + 1) for value in state.board)
    return {
        "outcome_plus_perspective": game.terminal(state),
        "plies": plies,
        "final_state_sha256": hashlib.sha256(
            board_bytes + bytes([1 if state.player == 1 else 0])
        ).hexdigest(),
    }


def run_probe() -> dict:
    rows = []
    started = time.perf_counter()
    for game_name, game in GAME_CONFIGS:
        for pairing_index, (first, second) in enumerate(PAIRINGS):
            for seed in SEEDS:
                for seat_swap in (False, True):
                    plus, minus = (second, first) if seat_swap else (first, second)
                    # Independent deterministic stream for the swapped-seat game.
                    actual_seed = seed + (100_000 if seat_swap else 0) + pairing_index * 10_000
                    result = play(game, actual_seed, plus, minus)
                    rows.append({
                        "game": game_name,
                        "pairing": f"{first}-vs-{second}",
                        "seat_swap": seat_swap,
                        "seed": actual_seed,
                        **result,
                    })
    summary = {}
    for game_name, _ in GAME_CONFIGS:
        game_rows = [row for row in rows if row["game"] == game_name]
        summary[game_name] = {
            "games": len(game_rows),
            "wins_plus": sum(row["outcome_plus_perspective"] == 1 for row in game_rows),
            "draws": sum(row["outcome_plus_perspective"] == 0 for row in game_rows),
            "wins_minus": sum(row["outcome_plus_perspective"] == -1 for row in game_rows),
            "mean_plies": sum(row["plies"] for row in game_rows) / len(game_rows),
        }
    return {
        "stage": "exploratory model-blind match feasibility; not a strength benchmark",
        "rules_source": "project-owned two_player.games.BoardGame",
        "game_configs": [name for name, _ in GAME_CONFIGS],
        "policies": list(POLICIES),
        "pairings_per_game": [list(pairing) for pairing in PAIRINGS],
        "base_seeds": list(SEEDS),
        "seat_schedule": "both assignments for every pairing/seed; seat-swapped assignment uses a disjoint deterministic RNG stream",
        "summary": summary,
        "matches": rows,
        "elapsed_seconds": time.perf_counter() - started,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "claim_limit": "Small hand-coded sanity opponents and 8 seeds do not estimate strength, demonstrate JEPA benefit, or support a Q1 claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON receipt path")
    args = parser.parse_args()
    result = run_probe()
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")


if __name__ == "__main__":
    main()
