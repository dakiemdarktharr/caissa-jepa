"""Recompute aggregate compute summaries from a V2.12 pilot receipt."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

from two_player.v212_pilot import (
    ARMS,
    build_root_schedule,
    verify_receipt,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_v01_source_compat(path: Path) -> str:
    """Recreate the v01 run's trailing blank line removed for repository hygiene."""
    payload = path.read_bytes()
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("unexpected v01 source EOF normalization")
    return hashlib.sha256(payload + b"\n").hexdigest()


def _nearest_rank(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def _summarize(results: list[dict]) -> dict:
    walls = [float(row["wall_seconds"]) for row in results]
    node_counts = [row["node_visits"] for row in results]
    transition_counts = [row["transition_calls"] for row in results]
    model_counts = [row["model_calls"] for row in results]
    rss = [row["peak_sampled_rss_bytes"] for row in results]
    return {
        "cells": len(results),
        "depth_four_complete": sum(row["completed_depth"] == 4 for row in results),
        "budget_stopped": sum(row["stop_reason"] != "depth_4_complete" for row in results),
        "node_visits": {
            "median": statistics.median(node_counts),
            "p90_nearest_rank": _nearest_rank(node_counts, 0.90),
            "max": max(node_counts),
        },
        "transition_calls": {"median": statistics.median(transition_counts),
                              "max": max(transition_counts)},
        "model_calls": {"median": statistics.median(model_counts),
                        "max": max(model_counts)},
        "wall_seconds": {
            "median": statistics.median(walls),
            "p90_nearest_rank": _nearest_rank(walls, 0.90),
            "max": max(walls),
        },
        "peak_sampled_rss_bytes": {"max": max(rss)},
    }


def summarize(receipt: dict) -> dict:
    verify_receipt(receipt)
    results = receipt["results"]
    by_variant = {
        variant: _summarize([row for row in results if row["variant"] == variant])
        for variant in receipt["variants"]
    }
    by_arm = {
        arm: _summarize([row for row in results if row["arm"] == arm])
        for arm in ARMS
    }
    return {
        "summary_version": "v212-compute-only-summary-v01",
        "status": receipt["status"],
        "receipt_schedule_sha256": receipt["schedule_sha256"],
        "receipt_protocol_sha256": receipt["protocol_sha256"],
        "receipt_pilot_source_sha256": receipt["pilot_source_sha256"],
        "receipt_runner_source_sha256": receipt["runner_source_sha256"],
        "receipt_rules_source_sha256": receipt["rules_source_sha256"],
        "receipt_sha256": None,
        "runtime": receipt["runtime"],
        "limits": {
            "node_cap": receipt["node_cap"],
            "wall_cap_seconds": receipt["wall_cap_seconds"],
            "rss_cap_bytes": receipt["rss_cap_bytes"],
        },
        "overall": _summarize(results),
        "by_variant": by_variant,
        "by_arm": by_arm,
        "guardrails": receipt["guardrails"],
    }


def verify_artifact(receipt: dict, receipt_path: Path, repository: Path) -> None:
    """Authenticate the reproducible schedule and source files for a receipt."""
    expected_roots = [root.public_record() for root in build_root_schedule()]
    if receipt.get("root_schedule") != expected_roots:
        raise ValueError("receipt root schedule does not match regenerated roots")
    source_paths = {
        "protocol_sha256": "docs/V212_COMPUTE_PILOT_V01.md",
        "pilot_source_sha256": "two_player/v212_pilot.py",
        "runner_source_sha256": "tools/v212_random_weight_compute_pilot.py",
        "rules_source_sha256": "two_player/games.py",
    }
    for receipt_key, relative_path in source_paths.items():
        source_path = repository / relative_path
        if receipt_key in {"pilot_source_sha256", "runner_source_sha256"}:
            accepted = {_sha256_file(source_path),
                        _sha256_v01_source_compat(source_path)}
        else:
            accepted = {_sha256_file(source_path)}
        if receipt.get(receipt_key) not in accepted:
            raise ValueError(f"receipt source hash mismatch for {relative_path}")
    if not receipt_path.is_file():
        raise ValueError("receipt file is missing")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        raise SystemExit("usage: python -m tools.v212_compute_pilot_summary RECEIPT.json SUMMARY.json")
    repository = Path(__file__).resolve().parents[1]
    receipt_path = (repository / args[0]).resolve()
    summary_path = (repository / args[1]).resolve()
    ignored_root = (repository / "chess_data").resolve()
    if receipt_path.parent != ignored_root or summary_path.parent != ignored_root:
        raise SystemExit("receipt and summary must remain directly under ignored chess_data/")
    if summary_path.exists():
        raise SystemExit("refusing to overwrite an existing summary")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verify_artifact(receipt, receipt_path, repository)
    summary = summarize(receipt)
    summary["receipt_sha256"] = _sha256_file(receipt_path)
    temporary = summary_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(summary_path)
    print(json.dumps({"summary": str(summary_path),
                      "receipt_sha256": summary["receipt_sha256"],
                      "root_arm_cells": summary["overall"]["cells"],
                      "depth_four_complete": summary["overall"]["depth_four_complete"],
                      "max_wall_seconds": summary["overall"]["wall_seconds"]["max"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
