"""Run the frozen, train-split-only V2.8 development fit panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from two_player.v28_model import Config, METHOD_VERSION
from two_player.v28_train import RunConfig, train_development_dataset
from two_player.v28_development import (DATASET_ROOT, EXPECTED_DATA,
                                        EXPECTED_MODEL_CONFIG, EXPECTED_RUN_CONFIG,
                                        validate_development_spec)
from tools.v28_match_power import CHECKPOINT_SEEDS

SPEC_PATH = ROOT / "docs" / "validation" / "V28_DEV_FIT_PANEL_V01.json"
VARIANTS = ("reply-jepa", "task-value-dynamics", "direct-leaf")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha256_source(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _validate_spec(spec):
    frozen = validate_development_spec()
    if spec != frozen or (spec.get("method") != METHOD_VERSION
                          or tuple(spec.get("variants", ())) != VARIANTS
                          or tuple(spec.get("checkpoint_seeds", ())) != CHECKPOINT_SEEDS):
        raise ValueError("development fit specification differs from the frozen panel")


def run_panel(dataset_dir, approval_path, output_root):
    dataset_dir = Path(dataset_dir).resolve()
    approval_path = Path(approval_path).resolve()
    output_root = Path(output_root).resolve()
    data_root = (ROOT / "chess_data").resolve()
    if dataset_dir != DATASET_ROOT:
        raise ValueError("development panel is limited to the exact audited DEV09 dataset")
    if data_root not in output_root.parents:
        raise ValueError("development checkpoints must stay under ignored chess_data")
    if output_root.exists():
        raise FileExistsError("refusing to overwrite a previous development panel")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    _validate_spec(spec)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_sha = _sha256(approval_path)
    if (approval.get("scope") != "development-only"
            or approval.get("protocol") != "V28_DEVELOPMENT_FIT_AMENDMENT_01"
            or approval.get("fit_split") != "train"
            or approval.get("training_approved_manifest") is not False):
        raise ValueError("panel requires the explicit development-only approval")
    spec_sha = _sha256_source(SPEC_PATH)
    trainer_sha = _sha256_source(ROOT / "two_player" / "v28_train.py")
    model_sha = _sha256_source(ROOT / "two_player" / "v28_model.py")
    source_sha = _sha256_source(ROOT / "two_player" / "v28_data.py")
    panel_runner_sha = _sha256_source(Path(__file__))
    lock_path = ROOT / "requirements-research-lock.txt"
    if not lock_path.is_file():
        raise FileNotFoundError("research runtime lockfile is required")
    panel = {
        "schema": "caissa-jepa-v28-development-fit-panel-result-v01",
        "status": "running",
        "method": METHOD_VERSION,
        "started_unix": time.time(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dataset_manifest_sha256": approval["dataset"]["manifest_sha256"],
        "dataset_fingerprint": approval["dataset"]["dataset_fingerprint"],
        "records_sha256": approval["dataset"]["records_sha256"],
        "audit_sha256": approval["dataset"]["audit_sha256"],
        "approval_path": str(approval_path),
        "approval_sha256": approval_sha,
        "panel_spec_sha256": spec_sha,
        "model_code_sha256": model_sha,
        "trainer_code_sha256": trainer_sha,
        "panel_runner_code_sha256": panel_runner_sha,
        "data_audit_code_sha256": source_sha,
        "requirements_lock_sha256": _sha256_source(lock_path),
        "allowed_training_split": "train",
        "locked_final_access": False,
        "runs": [],
    }
    output_root.mkdir(parents=True, exist_ok=False)
    manifest_path = output_root / "panel.json"
    _atomic_json(manifest_path, panel)
    config_values = spec["matched_model_config"]
    run_config = RunConfig(**spec["matched_run_config"])
    try:
        for seed in CHECKPOINT_SEEDS:
            for variant in VARIANTS:
                item = {"seed": seed, "variant": variant, "status": "running"}
                panel["runs"].append(item)
                _atomic_json(manifest_path, panel)
                checkpoint = output_root / str(seed) / variant / "checkpoint.npz"
                started = time.perf_counter()
                try:
                    result = train_development_dataset(
                        dataset_dir, checkpoint, approval_path=approval_path,
                        model_config=Config(variant=variant, seed=seed,
                                            **config_values),
                        run_config=run_config)
                    receipt_path = Path(result["receipt"])
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                    if (result["fit_scope"] != "development-only"
                            or receipt.get("fit_scope") != "development-only"
                            or receipt.get("development_approval_sha256") != approval_sha
                            or result["completed_epochs"] != 1
                            or receipt.get("dataset_fingerprint") !=
                            panel["dataset_fingerprint"]
                            or receipt.get("dataset_sha256") != EXPECTED_DATA["records_sha256"]
                            or receipt.get("audit_sha256") != EXPECTED_DATA["audit_sha256"]
                            or receipt.get("split") != "train"
                            or receipt.get("effective_run", {}).get("model") != {
                                **config_values, "variant": variant, "seed": seed}
                            or receipt.get("effective_run", {}).get("run") !=
                            EXPECTED_RUN_CONFIG
                            or receipt.get("completed_epochs") != 1
                            or any(not math.isfinite(float(v))
                                   for v in receipt["history"][0].values()
                                   if type(v) in (int, float))):
                        raise ValueError("fit receipt failed panel scope/numeric checks")
                    item.update({"status": "completed",
                                 "checkpoint": str(checkpoint),
                                 "checkpoint_sha256": _sha256(checkpoint),
                                 "receipt": str(receipt_path),
                                 "receipt_sha256": _sha256(receipt_path),
                                 "completed_epochs": result["completed_epochs"],
                                 "optimizer_step": receipt["optimizer_step"],
                                 "train_metrics": receipt["history"][0],
                                 "wall_seconds": time.perf_counter() - started})
                except BaseException as exc:
                    item.update({"status": "failed",
                                 "error_type": type(exc).__name__,
                                 "error": str(exc),
                                 "wall_seconds": time.perf_counter() - started})
                    panel["status"] = "failed"
                    panel["failed_unix"] = time.time()
                    _atomic_json(manifest_path, panel)
                    raise
                _atomic_json(manifest_path, panel)
    except BaseException:
        if panel["status"] == "running":
            panel["status"] = "interrupted_or_failed"
            panel["updated_unix"] = time.time()
            _atomic_json(manifest_path, panel)
        raise
    expected = len(CHECKPOINT_SEEDS) * len(VARIANTS)
    if (len(panel["runs"]) != expected
            or any(item.get("status") != "completed" for item in panel["runs"])):
        panel["status"] = "failed"
        panel["reason"] = "panel run inventory incomplete"
        _atomic_json(manifest_path, panel)
        raise RuntimeError("development panel did not complete all planned fits")
    panel["status"] = "completed"
    panel["completed_unix"] = time.time()
    panel["expected_runs"] = expected
    _atomic_json(manifest_path, panel)
    return panel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run_panel(args.dataset, args.approval, args.output)
    print(json.dumps({"status": result["status"],
                      "expected_runs": result["expected_runs"],
                      "output": str(args.output)}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
