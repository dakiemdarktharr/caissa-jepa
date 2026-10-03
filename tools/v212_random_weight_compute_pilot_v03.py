"""Run the V03 no-training compute pilot with durable per-cell progress."""
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

from two_player.v212_pilot import ARMS, VARIANTS, RandomInferenceModel, _warmup
from two_player.v212_pilot_v02 import (
    INIT_SEEDS,
    NODE_CAP,
    RSS_CAP_BYTES,
    WALL_CAP_SECONDS,
    build_root_schedule_v02,
    create_receipt as create_receipt_v02,
    schedule_sha256_v02,
    source_sha256,
    verify_receipt_v02,
)
from two_player.v212_pilot_v03 import (
    PILOT_VERSION,
    ReceiptPublicationUncertain,
    append_progress_record,
    create_progress_journal,
    run_root_arm_v03,
    write_new_receipt_atomic,
)


def _runtime() -> dict:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


def _verify_v03_receipt(receipt: dict) -> None:
    if receipt.get("pilot_version") != PILOT_VERSION:
        raise ValueError("unexpected V03 pilot version")
    schedule_sha = receipt.get("schedule_source_sha256")
    if (not isinstance(schedule_sha, str) or len(schedule_sha) != 64
            or any(char not in "0123456789abcdef" for char in schedule_sha)):
        raise ValueError("invalid V02 schedule-source SHA-256")
    legacy = dict(receipt)
    legacy.pop("schedule_source_sha256")
    legacy["pilot_version"] = "v212-random-weight-compute-pilot-v02"
    legacy["results"] = [dict(row) for row in receipt.get("results", [])]
    for row in legacy["results"]:
        if (row.get("completed_depth") == 4
                and row.get("stop_reason") == "wall_cap"):
            # V02 tied the stop label rigidly to completed depth; V03 keeps the
            # actual post-search wall-cap observation in its own receipt.
            row["stop_reason"] = "depth_4_complete"
    verify_receipt_v02(legacy)
    if any(row.get("stop_reason") == "rss_cap" for row in receipt["results"]):
        raise ValueError("RSS-stopped schedules must remain partial progress journals")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(
            "usage: python -m tools.v212_random_weight_compute_pilot_v03 OUTPUT.json"
        )

    repository = Path(__file__).resolve().parents[1]
    output = (repository / args[0]).resolve()
    ignored_root = (repository / "chess_data").resolve()
    if output.parent != ignored_root or output.suffix != ".json":
        raise SystemExit("output must be a .json file directly under ignored chess_data/")
    progress_path = output.with_suffix(".progress.jsonl")
    if output.exists() or progress_path.exists():
        raise SystemExit("refusing to overwrite an existing pilot output or progress journal")
    started = time.perf_counter()
    roots = build_root_schedule_v02()
    schedule_generation_seconds = time.perf_counter() - started
    games = {game.name: game for game in VARIANTS}
    repository_root = repository
    source_hashes = {
        "protocol": source_sha256(repository_root / "docs/V212_COMPUTE_PILOT_V03.md"),
        "pilot_source": source_sha256(repository_root / "two_player/v212_pilot_v03.py"),
        "runner_source": source_sha256(Path(__file__).resolve()),
        "shared_pilot_source": source_sha256(repository_root / "two_player/v212_pilot.py"),
        "schedule_source": source_sha256(repository_root / "two_player/v212_pilot_v02.py"),
        "rules_source": source_sha256(repository_root / "two_player/games.py"),
    }
    manifest = {
        "record_type": "manifest",
        "pilot_version": PILOT_VERSION,
        "schedule_sha256": schedule_sha256_v02(roots),
        "expected_cells": len(roots) * len(ARMS) * len(INIT_SEEDS),
        "source_sha256": source_hashes,
        "root_schedule": [root.public_record() for root in roots],
    }
    results = []
    final_receipt_written = False
    journal_created = False
    try:
        create_progress_journal(progress_path, manifest)
        journal_created = True
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
        for scheduled in roots:
            game = games[scheduled.root.variant]
            for seed in INIT_SEEDS:
                for arm in ARMS:
                    result = run_root_arm_v03(
                        game, scheduled.root, models[(arm, seed)]
                    )
                    row = {
                        "root_ordinal": scheduled.ordinal,
                        "initialization_seed": seed,
                        **result,
                    }
                    results.append(row)
                    append_progress_record(progress_path, {
                        "record_type": "cell",
                        "sequence": len(results),
                        "result": row,
                    })
                    if result["stop_reason"] == "rss_cap":
                        append_progress_record(progress_path, {
                            "record_type": "terminal",
                            "status": "stopped_safety",
                            "measured_cells": len(results),
                            "failure_kind": "rss_cap",
                        })
                        print(json.dumps({
                            "status": "stopped_safety",
                            "pilot_version": PILOT_VERSION,
                            "progress_journal": str(progress_path),
                            "measured_cells": len(results),
                            "failure_kind": "rss_cap",
                        }, sort_keys=True))
                        return 2

        receipt = create_receipt_v02(
            results, roots, source_hashes, warmups, _runtime(),
            schedule_generation_seconds,
        )
        receipt["pilot_version"] = PILOT_VERSION
        receipt["schedule_source_sha256"] = source_hashes["schedule_source"]
        _verify_v03_receipt(receipt)
        write_new_receipt_atomic(output, receipt)
        final_receipt_written = True
        try:
            append_progress_record(progress_path, {
                "record_type": "terminal",
                "status": "complete",
                "measured_cells": len(results),
                "receipt": str(output),
            })
        except OSError:
            # The already-fsynced final receipt is authoritative if only the
            # optional terminal journal marker cannot be appended.
            pass
    except BaseException as error:
        if final_receipt_written:
            # The verified, fsynced final JSON receipt is authoritative; an
            # optional terminal journal marker must not downgrade completion.
            return 0
        if journal_created:
            try:
                uncertain_receipt = isinstance(error, ReceiptPublicationUncertain)
                append_progress_record(progress_path, {
                    "record_type": "terminal",
                    "status": (
                        "publication_uncertain" if uncertain_receipt else
                        "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit))
                        else "failed"
                    ),
                    "measured_cells": len(results),
                    "failure_kind": type(error).__name__,
                    **({"receipt": str(error.path)} if uncertain_receipt else {}),
                })
            except BaseException:
                pass
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        print(json.dumps({
            "status": "publication_uncertain"
            if isinstance(error, ReceiptPublicationUncertain) else "failed",
            "pilot_version": PILOT_VERSION,
            "progress_journal": str(progress_path),
            **({"receipt": str(error.path)}
               if isinstance(error, ReceiptPublicationUncertain) else {}),
            "measured_cells": len(results),
            "failure_kind": type(error).__name__,
        }, sort_keys=True), file=sys.stderr)
        return 1

    completed = sum(row["completed_depth"] == 4 for row in results)
    print(json.dumps({
        "status": "compute_only_no_training",
        "pilot_version": PILOT_VERSION,
        "output": str(output),
        "progress_journal": str(progress_path),
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
