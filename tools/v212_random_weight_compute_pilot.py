"""Run the frozen V2.12 compute-only random-weight pilot.

Example (fresh ignored output only):
    .venv/bin/python -B -m tools.v212_random_weight_compute_pilot \
        chess_data/v212_random_weight_compute_pilot_01.json
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time

# Keep numerical inference deterministic and single-threaded on the shared host.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np

from two_player.games import BoardGame
from two_player.v212_pilot import (
    ARMS,
    PILOT_VERSION,
    VARIANTS,
    RandomInferenceModel,
    _warmup,
    build_root_schedule,
    create_receipt,
    run_root_arm,
    verify_receipt,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _counters(model: RandomInferenceModel) -> dict:
    return {
        "encoder_calls": model.calls.encoder_calls,
        "predictor_calls": model.calls.predictor_calls,
        "decoder_calls": model.calls.decoder_calls,
        "value_calls": model.calls.value_calls,
        "model_calls": model.calls.model_calls,
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: python -m tools.v212_random_weight_compute_pilot OUTPUT.json")

    repository = Path(__file__).resolve().parents[1]
    output = (repository / args[0]).resolve()
    ignored_root = (repository / "chess_data").resolve()
    if output.parent != ignored_root or output.suffix != ".json":
        raise SystemExit("output must be a new .json file directly under ignored chess_data/")
    if output.exists():
        raise SystemExit("refusing to overwrite an existing pilot output")
    output.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    roots = build_root_schedule()
    schedule_generation_seconds = time.perf_counter() - started
    games = {game.name: game for game in VARIANTS}
    models = {arm: RandomInferenceModel(arm) for arm in ARMS}

    warmups = {}
    first_root = roots[0]
    for arm in ARMS:
        model = models[arm]
        model.reset_calls()
        warmup_started = time.perf_counter()
        _warmup(games[first_root.variant], first_root, model)
        warmups[arm] = {
            **_counters(model),
            "wall_seconds": time.perf_counter() - warmup_started,
            "transition_calls": 1 if arm != "direct-leaf-value" else 0,
        }
        model.reset_calls()

    source_root = repository
    source_hashes = {
        "protocol": _sha256_file(source_root / "docs/V212_COMPUTE_PILOT_V01.md"),
        "pilot_source": _sha256_file(source_root / "two_player/v212_pilot.py"),
        "runner_source": _sha256_file(Path(__file__).resolve()),
        "rules_source": _sha256_file(source_root / "two_player/games.py"),
    }

    results = []
    for root in roots:
        game = games[root.variant]
        for arm in ARMS:
            results.append(run_root_arm(game, root, models[arm]))

    receipt = create_receipt(results, roots, source_hashes)
    receipt["schedule_generation_seconds"] = schedule_generation_seconds
    receipt["warmups"] = warmups
    verify_receipt(receipt)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(output)

    max_wall = max(result["wall_seconds"] for result in results)
    max_nodes = max(result["node_visits"] for result in results)
    completed = sum(result["completed_depth"] == 4 for result in results)
    capped = sum(result["stop_reason"] != "depth_4_complete" for result in results)
    print(json.dumps({
        "status": "compute_only_no_training",
        "pilot_version": PILOT_VERSION,
        "output": str(output),
        "schedule_sha256": receipt["schedule_sha256"],
        "root_arm_cells": len(results),
        "depth_four_complete": completed,
        "budget_stopped": capped,
        "max_wall_seconds": round(max_wall, 6),
        "max_node_visits": max_nodes,
        "numpy": np.__version__,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
