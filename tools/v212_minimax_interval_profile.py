"""Reproducible, synthetic-only transition profile for minimax intervals.

Runs the opening state of Connect Four 6x7 and Reversi6 in memory under fixed
transition caps. It loads no model/data, creates no schedule, and writes only
JSONL to stdout. Timings are single-run diagnostics, not benchmark estimates.
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
from two_player.v212_minimax_transition_balanced_bounds_v01 import (
    minimax_transition_balanced_bounds,
)


CAPS = (4096, 16384, 65536)
SOURCES = (
    Path(__file__),
    ROOT / "two_player/games.py",
    ROOT / "two_player/v212_minimax_bounds_v01.py",
    ROOT / "two_player/v212_minimax_transition_bounds_v01.py",
    ROOT / "two_player/v212_minimax_transition_balanced_bounds_v01.py",
)
GAMES = (
    BoardGame("synthetic-connect4-6x7", 6, 7, 4, gravity=True),
    BoardGame("synthetic-reversi6", 6, 6, 0, reversi=True),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_manifest():
    return {str(path.relative_to(ROOT)): sha256(path) for path in SOURCES}


def main():
    manifest = source_manifest()
    common = {
        "schema": "v212.minimax_interval_profile_v01",
        "profile_kind": "single-run synthetic opening-state diagnostic",
        "rules_version": RULES_VERSION,
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": __import__("os").cpu_count(),
        "model_calls": 0,
        "source_sha256": manifest,
    }
    print(json.dumps({"record_type": "profile_manifest", **common},
                     sort_keys=True))

    for game in GAMES:
        state = game.initial()
        actions = game.legal_actions(state)
        for cap in CAPS:
            started = time.perf_counter()
            result = minimax_transition_balanced_bounds(
                game, state, actions[0], cap)
            elapsed = time.perf_counter() - started
            widths = [interval.upper - interval.lower
                      for _, interval in result.action_values]
            print(json.dumps({
                "record_type": "synthetic_root_measurement",
                "game": game.name,
                "root_state_sha256": hashlib.sha256(
                    repr((game.name, state)).encode("ascii")).hexdigest(),
                "root_action_count": len(actions),
                "transition_budget": cap,
                "rule_transition_calls": result.transition_count,
                "expanded_nonterminal_descendants": result.expanded_nodes,
                "root_value_interval_width": result.root_value.upper
                - result.root_value.lower,
                "mean_root_action_interval_width": sum(widths) / len(widths),
                "point_identified_root_action_fraction": sum(
                    width == 0 for width in widths) / len(widths),
                "wall_seconds_single_run": elapsed,
            }, sort_keys=True))


if __name__ == "__main__":
    main()
