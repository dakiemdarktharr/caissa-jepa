"""Generate one pinned, bounded development corpus with durable receipts.

Run as `python -m tools.counterplay_data`. Data remain local and ignored;
only the compact --receipt is intended for reviewed Git publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

import numpy as np

from counterplay.data import build, fingerprint
from research_ledger import Ledger, file_sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("counterplay/data.py", "two_player/games.py", "two_player/v28_data.py",
           "two_player/v212_trajectory_audit.py", "two_player/v212_window_batch.py",
           "two_player/v212_model.py", "benchmarks/reference_rules.py",
           "research/protocol.yaml", "research/data_contract.json",
           "research_ledger.py", "tools/counterplay_data.py")


def write_new(path, value):
    """Exclusive durable file; a new attempt never overwrites older evidence."""
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def prepare(destination, receipt, *, run_id, seed=2026102501):
    destination, receipt = Path(destination).resolve(), Path(receipt).resolve()
    if destination.exists() or receipt.exists():
        raise ValueError("fresh output and receipt paths required")
    # An ignored destination is required to preserve the declared storage plan.
    relative = destination.relative_to(ROOT)
    if not relative.parts or relative.parts[0] != "chess_data":
        raise ValueError("raw data destination must be inside ignored chess_data")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if status:
        raise ValueError("data generation requires a clean pinned source checkpoint")
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"):
        if os.environ.get(name) != "1":
            raise ValueError("set BLAS and OMP threads to one before process startup")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    sources = {name: file_sha256(ROOT / name) for name in SOURCES}
    contract = json.loads((ROOT / "research/data_contract.json").read_text())
    recipe = contract["pilot_recipe"]
    if seed != recipe["corpus_seed"]:
        raise ValueError("this executable supports only the frozen development recipe")
    environment = {"python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
                   "threads": 1, "memory_limit_bytes": 2 * 1024**3}
    # Hard address-space limit on this Linux process; sampled RSS is separate.
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    destination.mkdir(parents=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with Ledger(ROOT / "chess_data/research_metrics.sqlite") as ledger:
        prep_id = run_id + ":preparation"
        ledger.create_run({"run_id": prep_id, "phase": "workflow", "protocol_id": "counterplay-cp01-v2",
                           "code_commit": commit, "config": {"recipe": recipe, "sources": sources},
                           "inputs": {"protocol": sources["research/protocol.yaml"],
                                      "data_contract": sources["research/data_contract.json"]},
                           "environment": environment})
        ledger.record(prep_id, "start", "dataset_start", metrics={"seed": seed},
                      dimensions={"source_clean": True, "destination": str(relative)},
                      note="No training or locked data; one bounded model-blind construction batch")
        try:
            data = build(seed, train_episodes=recipe["train_episodes_per_game"],
                         development_episodes=recipe["development_episodes_per_game"],
                         train_cap=recipe["train_windows_per_game"],
                         development_cap=recipe["development_windows_per_game"], cpu_seconds=300)
            cpu_seconds = data.pop("cpu_seconds")
            # Timing is evidence, but is not part of deterministic corpus bytes.
            root_times = {r["root_id"]: r["reference"].pop("wall_seconds")
                          for r in data["roots"] if "reference" in r}
            write_new(destination / "data.json", data)
            payload_hash = file_sha256(destination / "data.json")
            audit = data["audit"]
            acceptable = data["window_count_gate"] and data["reference_yield_gate"]
            result = {"schema": "counterplay.data-receipt.v1", "phase": "development-data-feasibility",
                      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                      "code_commit": commit, "source_clean_at_start": True, "source_hashes": sources,
                      "data_sha256": payload_hash, "raw_data_path": str(relative / "data.json"),
                      "config": recipe, "environment": environment, "audit": audit,
                      "window_count_gate": data["window_count_gate"],
                      "reference_yield_gate": data["reference_yield_gate"],
                      "status": "construction_gates_passed" if acceptable else "failed_feasibility_gate",
                      "acceptance": "Independent Review 2 still required before pilot",
                      "wall_seconds": time.perf_counter() - started, "cpu_seconds": cpu_seconds,
                      "reference_wall_seconds_by_root": root_times,
                      "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                      "fits": 0, "matches": 0, "reference_descendant_overlap": None,
                      "missing_reason": "reference-descendant overlap not yet measured; no whole-tree-disjointness claim",
                      "rental_usd": None, "rental_missing_reason": "local CPU; provider billing is not exposed or estimated",
                      "storage": "raw data local-only; exact recovery requires regeneration and hash verification"}
            write_new(receipt, result)
            manifest = {"run_id": run_id, "parent_id": prep_id, "phase": "development",
                        "protocol_id": "counterplay-cp01-v2", "code_commit": commit,
                        "seed": seed, "arm": "model-blind-data", "config": {"recipe": recipe},
                        "inputs": {"dataset": payload_hash, "split": fingerprint({e["episode_id"]: e["role"] for e in data["episodes"]}),
                                   "protocol": sources["research/protocol.yaml"]}, "environment": environment}
            ledger.create_run(manifest)
            ledger.record(run_id, "completed-batch", "dataset_audit", metrics={"counts": audit,
                          "cpu_seconds": cpu_seconds, "wall_seconds": result["wall_seconds"],
                          "peak_rss_bytes": result["peak_rss_bytes"], "fits": 0, "matches": 0},
                          dimensions={"status": result["status"], "receipt_sha256": file_sha256(receipt)})
            if not acceptable:
                ledger.record(run_id, "feasibility-failed", "failure", metrics={"accepted_corpora": 0},
                              note="Preserved original batch; no root/seed replacement; diagnose before any revision")
            return result
        except BaseException as error:
            ledger.record(prep_id, "failure", "failure", metrics={"accepted_corpora": 0},
                          dimensions={"exception": type(error).__name__}, note=str(error))
            failure = destination / "failure.json"
            if not failure.exists():
                write_new(failure, {"run_id": prep_id, "code_commit": commit, "sources": sources,
                                    "exception": type(error).__name__, "reason": str(error),
                                    "wall_seconds": time.perf_counter() - started})
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    result = prepare(args.destination, args.receipt, run_id=args.run_id)
    print(json.dumps({k: result[k] for k in ("status", "data_sha256", "window_count_gate", "reference_yield_gate", "wall_seconds")}))
    return 0 if result["status"] == "construction_gates_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
