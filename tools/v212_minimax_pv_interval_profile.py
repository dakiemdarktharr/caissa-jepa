"""Synthetic-only same-cap comparison of three minimax interval schedules.

Profiles only the standard opening positions for Connect Four 6x7 and
Reversi6. Single-run wall times are diagnostic. This is not a benchmark-root
sample and cannot set or revise a model inference cap.
"""
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy

from two_player.games import BoardGame, RULES_VERSION
from two_player.v212_minimax_transition_bounds_v01 import minimax_transition_bounds
from two_player.v212_minimax_transition_balanced_bounds_v01 import (
    minimax_transition_balanced_bounds,
)
from two_player.v212_minimax_pv_interval_bounds_v01 import (
    minimax_pv_interval_bounds,
)


CAPS = (4096,)
SOURCES = (
    Path(__file__),
    ROOT / "two_player/games.py",
    ROOT / "two_player/v212_minimax_bounds_v01.py",
    ROOT / "two_player/v212_minimax_transition_bounds_v01.py",
    ROOT / "two_player/v212_minimax_transition_balanced_bounds_v01.py",
    ROOT / "two_player/v212_minimax_pv_interval_bounds_v01.py",
)
GAMES = (
    BoardGame("synthetic-connect4-6x7", 6, 7, 4, gravity=True),
    BoardGame("synthetic-reversi6", 6, 6, 0, reversi=True),
)
SCHEDULES = (
    ("transition-dfs", minimax_transition_bounds),
    ("root-balanced-dfs", minimax_transition_balanced_bounds),
    ("pv-bound-critical", minimax_pv_interval_bounds),
)


def source_manifest():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCES
    }


def main():
    manifest = source_manifest()
    print(json.dumps({
        "record_type": "profile_manifest",
        "schema": "v212.minimax_pv_interval_profile_v01",
        "profile_kind": "single-run synthetic opening-state schedule comparison",
        "rules_version": RULES_VERSION,
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "model_calls": 0,
        "source_sha256": manifest,
    }, sort_keys=True))

    for game in GAMES:
        state = game.initial()
        actions = game.legal_actions(state)
        for budget in CAPS:
            for schedule, solver in SCHEDULES:
                started = time.perf_counter()
                result = solver(game, state, actions[0], budget)
                elapsed = time.perf_counter() - started
                widths = [value.upper - value.lower
                          for _, value in result.action_values]
                print(json.dumps({
                    "record_type": "synthetic_root_measurement",
                    "game": game.name,
                    "schedule": schedule,
                    "root_state_sha256": hashlib.sha256(
                        repr((game.name, state)).encode("ascii")).hexdigest(),
                    "root_action_count": len(actions),
                    "transition_budget": budget,
                    "rule_transition_calls": result.transition_count,
                    "expanded_nonterminal_descendants": result.expanded_nodes,
                    "unused_transition_budget": budget - result.transition_count,
                    "root_value_interval_width": (
                        result.root_value.upper - result.root_value.lower),
                    "mean_root_action_interval_width": sum(widths) / len(widths),
                    "point_identified_root_action_fraction": (
                        sum(width == 0 for width in widths) / len(widths)),
                    "executed_action_regret_interval": [
                        result.regret.lower, result.regret.upper],
                    "wall_seconds_single_run": elapsed,
                }, sort_keys=True))


if __name__ == "__main__":
    main()
