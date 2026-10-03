"""Verify and summarize a V2.12 v02 compute-only receipt."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

from two_player.v212_pilot_v02 import (
    build_root_schedule_v02,
    verify_receipt_v02,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_v01_shared_source_compat(path: Path) -> str:
    """Recreate the v01 shared source EOF bytes used by the v02 run."""
    payload = path.read_bytes()
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("unexpected v01 shared-source EOF normalization")
    return hashlib.sha256(payload + b"\n").hexdigest()


def _nearest_rank(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def _summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"cells": 0}
    measures = {
        "wall_seconds": [float(row["wall_seconds"]) for row in rows],
        "node_visits": [row["node_visits"] for row in rows],
        "transition_calls": [row["transition_calls"] for row in rows],
        "model_calls": [row["model_calls"] for row in rows],
        "peak_sampled_rss_bytes": [row["peak_sampled_rss_bytes"] for row in rows],
    }
    return {
        "cells": len(rows),
        "depth_four_complete": sum(row["completed_depth"] == 4 for row in rows),
        "safety_stopped": sum(row["stop_reason"] != "depth_4_complete" for row in rows),
        "stop_reasons": {
            reason: sum(row["stop_reason"] == reason for row in rows)
            for reason in sorted({row["stop_reason"] for row in rows})
        },
        "completed_depth_counts": {
            str(depth): sum(row["completed_depth"] == depth for row in rows)
            for depth in sorted({row["completed_depth"] for row in rows})
        },
        "measurements": {
            name: {
                "p50_nearest_rank": _nearest_rank(values, 0.50),
                "p90_nearest_rank": _nearest_rank(values, 0.90),
                "p95_nearest_rank": _nearest_rank(values, 0.95),
                "p99_nearest_rank": _nearest_rank(values, 0.99),
                "max": max(values),
            }
            for name, values in measures.items()
        },
    }


def _summarize_warmups(rows: list[dict]) -> dict:
    if not rows:
        return {"cells": 0}
    fields = ("wall_seconds", "transition_calls", "encoder_calls",
              "predictor_calls", "decoder_calls", "value_calls", "model_calls")
    return {
        "cells": len(rows),
        "measurements": {
            field: {
                "p50_nearest_rank": _nearest_rank([row[field] for row in rows], 0.50),
                "p90_nearest_rank": _nearest_rank([row[field] for row in rows], 0.90),
                "p95_nearest_rank": _nearest_rank([row[field] for row in rows], 0.95),
                "p99_nearest_rank": _nearest_rank([row[field] for row in rows], 0.99),
                "max": max(row[field] for row in rows),
            }
            for field in fields
        },
    }


def _group(results: list[dict], key_fn) -> dict:
    buckets = defaultdict(list)
    for row in results:
        buckets[key_fn(row)].append(row)
    return {"|".join(map(str, key if isinstance(key, tuple) else (key,))):
            _summarize(rows) for key, rows in sorted(buckets.items())}


def _group_warmups(rows: list[dict], key_fn) -> dict:
    buckets = defaultdict(list)
    for row in rows:
        buckets[key_fn(row)].append(row)
    return {"|".join(map(str, key if isinstance(key, tuple) else (key,))):
            _summarize_warmups(group) for key, group in sorted(buckets.items())}


def summarize(receipt: dict) -> dict:
    verify_receipt_v02(receipt)
    results = receipt["results"]
    warmups = list(receipt["warmups"].values())
    return {
        "summary_version": "v212-compute-only-summary-v02",
        "status": receipt["status"],
        "schedule_sha256": receipt["schedule_sha256"],
        "receipt_sha256": None,
        "summary_source_sha256": None,
        "source_hashes": {
            "protocol": receipt["protocol_sha256"],
            "pilot": receipt["pilot_source_sha256"],
            "runner": receipt["runner_source_sha256"],
            "shared_pilot": receipt["shared_pilot_source_sha256"],
            "rules": receipt["rules_source_sha256"],
        },
        "runtime": receipt["runtime"],
        "caps": {
            "node_cap": receipt["node_cap"],
            "wall_cap_seconds": receipt["wall_cap_seconds"],
            "rss_cap_bytes": receipt["rss_cap_bytes"],
        },
        "guardrails": receipt["guardrails"],
        "overall": _summarize(results),
        "by_variant": _group(results, lambda row: row["variant"]),
        "by_arm": _group(results, lambda row: row["arm"]),
        "by_initialization_seed": _group(
            results, lambda row: row["initialization_seed"]),
        "by_target_ply": _group(results, lambda row: row["root_target_ply"]),
        "by_variant_arm": _group(results,
                                  lambda row: (row["variant"], row["arm"])),
        "by_variant_seed": _group(results,
                                   lambda row: (row["variant"],
                                                row["initialization_seed"])),
        "by_arm_seed": _group(results,
                               lambda row: (row["arm"],
                                            row["initialization_seed"])),
        "warmups": {
            "separate_from_measured_cells": True,
            "overall": _summarize_warmups(warmups),
            "by_arm": _group_warmups(warmups, lambda row: row["arm"]),
            "by_initialization_seed": _group_warmups(
                warmups, lambda row: row["initialization_seed"]),
            "records": receipt["warmups"],
        },
    }


def verify_artifact(receipt: dict, receipt_path: Path, repository: Path) -> None:
    verify_receipt_v02(receipt)
    expected_roots = [root.public_record() for root in build_root_schedule_v02()]
    if receipt["root_schedule"] != expected_roots:
        raise ValueError("receipt schedule differs from reconstructed roots")
    sources = {
        "protocol_sha256": "docs/V212_COMPUTE_PILOT_V02.md",
        "pilot_source_sha256": "two_player/v212_pilot_v02.py",
        "runner_source_sha256": "tools/v212_random_weight_compute_pilot_v02.py",
        "shared_pilot_source_sha256": "two_player/v212_pilot.py",
        "rules_source_sha256": "two_player/games.py",
    }
    for receipt_key, relative_path in sources.items():
        source_path = repository / relative_path
        accepted = {_sha256_file(source_path)}
        if receipt_key == "shared_pilot_source_sha256":
            accepted.add(_sha256_v01_shared_source_compat(source_path))
        if receipt.get(receipt_key) not in accepted:
            raise ValueError(f"source hash mismatch for {relative_path}")
    if not receipt_path.is_file():
        raise ValueError("receipt file is missing")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        raise SystemExit(
            "usage: python -m tools.v212_compute_pilot_v02_summary RECEIPT.json SUMMARY.json"
        )
    repository = Path(__file__).resolve().parents[1]
    ignored_root = (repository / "chess_data").resolve()
    receipt_path = (repository / args[0]).resolve()
    summary_path = (repository / args[1]).resolve()
    if receipt_path.parent != ignored_root or summary_path.parent != ignored_root:
        raise SystemExit("receipt and summary must remain directly under ignored chess_data/")
    if summary_path.exists():
        raise SystemExit("refusing to overwrite an existing summary")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verify_artifact(receipt, receipt_path, repository)
    summary = summarize(receipt)
    summary["receipt_sha256"] = _sha256_file(receipt_path)
    summary["summary_source_sha256"] = _sha256_file(Path(__file__).resolve())
    temporary = summary_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(summary_path)
    print(json.dumps({
        "summary": str(summary_path),
        "receipt_sha256": summary["receipt_sha256"],
        "cells": summary["overall"]["cells"],
        "depth_four_complete": summary["overall"]["depth_four_complete"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
