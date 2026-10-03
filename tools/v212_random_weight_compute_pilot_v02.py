"""Run the frozen V2.12 v02 no-training random-weight compute pilot.

All output is fresh JSON beneath ignored ``chess_data/``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import sys
import time

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np

from two_player.games import BoardGame
from two_player.v212_pilot import ARMS, VARIANTS, RandomInferenceModel, _warmup, run_root_arm
from two_player.v212_pilot_v02 import (
    INIT_SEEDS,
    PILOT_VERSION,
    RSS_CAP_BYTES,
    WALL_CAP_SECONDS,
    NODE_CAP,
    build_root_schedule_v02,
    create_receipt,
    source_sha256,
    verify_receipt_v02,
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(
            "usage: python -m tools.v212_random_weight_compute_pilot_v02 OUTPUT.json"
        )

    repository = Path(__file__).resolve().parents[1]
    output = (repository / args[0]).resolve()
    ignored_root = (repository / "chess_data").resolve()
    if output.parent != ignored_root or output.suffix != ".json":
        raise SystemExit("output must be a new .json file directly under ignored chess_data/")
    if output.exists():
        raise SystemExit("refusing to overwrite an existing pilot output")
    output.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    roots = build_root_schedule_v02()
    schedule_generation_seconds = time.perf_counter() - started
    games = {game.name: game for game in VARIANTS}
    models = {(arm, seed): RandomInferenceModel(arm, seed=seed)
              for seed in INIT_SEEDS for arm in ARMS}

    warmups = {}
    first_root = roots[0].root
    for seed in INIT_SEEDS:
        for arm in ARMS:
            model = models[(arm, seed)]
            model.reset_calls()
            warmup_start = time.perf_counter()
            _warmup(games[first_root.variant], first_root, model)
            warmups[f"{seed}:{arm}"] = {
                "initialization_seed": seed,
                "arm": arm,
                "encoder_calls": model.calls.encoder_calls,
                "predictor_calls": model.calls.predictor_calls,
                "decoder_calls": model.calls.decoder_calls,
                "value_calls": model.calls.value_calls,
                "model_calls": model.calls.model_calls,
                "transition_calls": 1 if arm != "direct-leaf-value" else 0,
                "wall_seconds": time.perf_counter() - warmup_start,
                "warmup_root_state_sha256": first_root.state_sha256,
            }
            model.reset_calls()

    source_root = repository
    source_hashes = {
        "protocol": source_sha256(source_root / "docs/V212_COMPUTE_PILOT_V02.md"),
        "pilot_source": source_sha256(source_root / "two_player/v212_pilot_v02.py"),
        "runner_source": source_sha256(Path(__file__).resolve()),
        "shared_pilot_source": source_sha256(source_root / "two_player/v212_pilot.py"),
        "rules_source": source_sha256(source_root / "two_player/games.py"),
    }

    results = []
    for scheduled in roots:
        game = games[scheduled.root.variant]
        for seed in INIT_SEEDS:
            for arm in ARMS:
                result = run_root_arm(game, scheduled.root, models[(arm, seed)])
                results.append({
                    "root_ordinal": scheduled.ordinal,
                    "initialization_seed": seed,
                    **result,
                })

    receipt = create_receipt(
        results,
        roots,
        source_hashes,
        warmups,
        {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
        schedule_generation_seconds,
    )
    verify_receipt_v02(receipt)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(output)

    completed = sum(row["completed_depth"] == 4 for row in results)
    print(json.dumps({
        "status": "compute_only_no_training",
        "pilot_version": PILOT_VERSION,
        "output": str(output),
        "schedule_sha256": receipt["schedule_sha256"],
        "root_arm_initialization_cells": len(results),
        "depth_four_complete": completed,
        "budget_stopped": len(results) - completed,
        "max_wall_seconds": max(row["wall_seconds"] for row in results),
        "max_node_visits": max(row["node_visits"] for row in results),
        "max_sampled_rss_bytes": max(row["peak_sampled_rss_bytes"] for row in results),
        "caps": {"nodes": NODE_CAP, "wall_seconds": WALL_CAP_SECONDS,
                 "rss_bytes": RSS_CAP_BYTES},
        "numpy": np.__version__,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
