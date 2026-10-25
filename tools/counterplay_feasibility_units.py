"""Export compact development-feasibility analysis units, without board data.

This never reads a locked run. Call from a pinned revision after publishing
the producing batch's receipt. Raw inputs must match that receipt's hash.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess

from counterplay.data import potential_nonzero_signed_support
from research_ledger import Ledger, file_sha256


def export_units(receipt_path, output):
    root = Path(__file__).resolve().parents[1]
    receipt_path, output = Path(receipt_path), Path(output)
    receipt = json.loads(receipt_path.read_text())
    if receipt["phase"] != "development-data-feasibility":
        raise ValueError("only explicitly development-data feasibility receipts")
    raw = root / receipt["raw_data_path"]
    if file_sha256(raw) != receipt["data_sha256"]:
        raise ValueError("raw dataset bytes do not match the published receipt")
    if output.exists():
        raise ValueError("new output path required")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if status:
        raise ValueError("export requires clean pinned analysis source")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    data = json.loads(raw.read_text())
    records = []
    for row in data["roots"]:
        complete = row["status"] == "complete"
        values = row.get("reference", {}).get("rows", [])
        pair = row.get("primary_pair")
        records.append({"attempt": receipt["run_id"], "source_commit": receipt["code_commit"],
                        "game": row["game"], "episode_group": row["episode_id"],
                        "root_id": row["root_id"], "source_ply": row["ply"],
                        "empty_cells": row["state"]["board"].count(0), "status": row["status"],
                        "pairable": int(bool(pair)) if complete else None,
                        "potential_nonzero_signed_support": int(potential_nonzero_signed_support(values, pair)) if complete else None,
                        "reference_entries": len(values) if complete else None,
                        "reference_nodes": row.get("reference", {}).get("nodes"),
                        "reference_wall_seconds": receipt["reference_wall_seconds_by_root"].get(row["root_id"]),
                        "missing_reason": "" if complete else row.get("reason", "failed reference")})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]) if records else ["attempt"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    with Ledger(root / "chess_data/research_metrics.sqlite") as ledger:
        run_id = receipt["run_id"] + ":unit-export"
        ledger.create_run({"run_id": run_id, "phase": "workflow", "protocol_id": "counterplay-feasibility-units-v1",
                           "code_commit": commit, "config": {"board_data_exported": False},
                           "inputs": {"receipt": file_sha256(receipt_path), "raw_dataset": receipt["data_sha256"],
                                      "exporter": file_sha256(__file__)}, "environment": receipt["environment"]})
        ledger.record(run_id, "export", "analysis_units", metrics={"root_rows": len(records)},
                      dimensions={"output_sha256": file_sha256(output), "phase": "development-data-feasibility"})
    return {"root_rows": len(records), "output_sha256": file_sha256(output), "analysis_commit": commit}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    print(json.dumps(export_units(args.receipt, args.output)))


if __name__ == "__main__":
    main()
