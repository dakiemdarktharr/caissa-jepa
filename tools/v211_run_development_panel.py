"""Run the frozen train-only V2.11 lambda-8 development fit panel."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from two_player.v28_model import Config, METHOD_VERSION
from two_player.v28_train import RunConfig, _fit_records, _runtime_identity
from two_player.v211_development import (DATASET_ROOT, MODEL_CONFIG, ROOT as PROJECT,
                                         RUN_CONFIG, SEEDS, load_train_split,
                                         validate_spec)


def _is_current_process_in_job() -> bool:
    if os.name != "nt":
        return False
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE,
                                        ctypes.POINTER(wintypes.BOOL)]
    kernel32.IsProcessInJob.restype = wintypes.BOOL
    in_job = wintypes.BOOL()
    if not kernel32.IsProcessInJob(kernel32.GetCurrentProcess(), None,
                                   ctypes.byref(in_job)):
        raise ctypes.WinError(ctypes.get_last_error())
    return bool(in_job.value)


def _sha(path: Path, *, normalize_text=False) -> str:
    raw = Path(path).read_bytes()
    if normalize_text:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_panel(dataset_dir, approval_path, output_root, *, supervision_token):
    child_token = os.environ.get("CAISSA_V211_SUPERVISOR_TOKEN", "")
    if (not isinstance(supervision_token, str) or len(supervision_token) != 64
            or not secrets.compare_digest(child_token, supervision_token)):
        raise PermissionError("V2.11 fitting must run under the resource supervisor")
    if not _is_current_process_in_job():
        raise PermissionError("V2.11 fitting process is not assigned to a Windows Job Object")
    spec = validate_spec()
    from tools.v211_model_match import verify_baseline_runtime
    verify_baseline_runtime()
    dataset_dir = Path(dataset_dir).resolve()
    approval_path = Path(approval_path).resolve()
    output_root = Path(output_root).resolve()
    data_root = (PROJECT / "chess_data").resolve()
    if dataset_dir != DATASET_ROOT:
        raise ValueError("V2.11 panel accepts only audited DEV09")
    if data_root not in output_root.parents or output_root.exists():
        raise ValueError("V2.11 outputs require a fresh ignored chess_data root")
    if (output_root == DATASET_ROOT or DATASET_ROOT in output_root.parents
            or output_root in DATASET_ROOT.parents):
        raise ValueError("V2.11 output root overlaps the audited dataset")
    records, fingerprint, approval_sha = load_train_split(dataset_dir, approval_path)
    if fingerprint != spec["dataset"]["expected_identity"]["dataset_fingerprint"]:
        raise ValueError("V2.11 train split fingerprint differs from protocol")
    runspec = {k: RUN_CONFIG[k] for k in ("epochs", "shuffle_seed")}
    run_config = RunConfig(**runspec)
    if run_config.epochs != 3:
        raise ValueError("V2.11 must make exactly 87 updates per seed")

    panel = {
        "schema": "caissa-jepa-v211-development-fit-panel-result-v01",
        "status": "running",
        "protocol": "V211_JEPA_WEIGHT_CALIBRATION_V01",
        "method": METHOD_VERSION,
        "started_unix": time.time(),
        "commit": __import__("subprocess").check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dataset_fingerprint": fingerprint,
        "dataset_manifest_sha256": spec["dataset"]["expected_identity"]["manifest_sha256"],
        "records_sha256": spec["dataset"]["expected_identity"]["records_sha256"],
        "audit_sha256": spec["dataset"]["expected_identity"]["audit_sha256"],
        "approval_sha256": approval_sha,
        "method_sha256": _sha(PROJECT / "docs" / "METHOD_V211_JEPA_WEIGHT_CALIBRATION.md",
                               normalize_text=True),
        "panel_spec_sha256": _sha(PROJECT / "docs" / "validation" /
                                  "V211_JEPA_WEIGHT_CALIBRATION_V01.json"),
        "loader_code_sha256": _sha(PROJECT / "two_player" / "v211_development.py",
                                    normalize_text=True),
        "panel_runner_code_sha256": _sha(Path(__file__), normalize_text=True),
        "model_code_sha256": _sha(PROJECT / "two_player" / "v28_model.py",
                                   normalize_text=True),
        "trainer_code_sha256": _sha(PROJECT / "two_player" / "v28_train.py",
                                     normalize_text=True),
        "data_audit_code_sha256": _sha(PROJECT / "two_player" / "v28_data.py",
                                        normalize_text=True),
        "requirements_lock_sha256": _sha(PROJECT / "requirements-research-lock.txt",
                                          normalize_text=True),
        "runtime_identity": _runtime_identity(),
        "allowed_training_split": "train",
        "locked_final_access": False,
        "runs": [],
    }
    output_root.mkdir(parents=True, exist_ok=False)
    ledger_path = output_root / "panel.json"
    _atomic_json(ledger_path, panel)

    try:
        for seed in SEEDS:
            item = {"seed": seed, "variant": "reply-jepa", "status": "running"}
            panel["runs"].append(item)
            started_wall, started_cpu = time.perf_counter(), time.process_time()
            _atomic_json(ledger_path, panel)
            checkpoint = output_root / str(seed) / "reply-jepa" / "checkpoint.npz"
            try:
                config = Config(variant="reply-jepa", seed=seed, **MODEL_CONFIG)
                # The fit routine writes its usual checkpoint receipt with history;
                # this panel ledger records no losses/history and never reads them.
                result = _fit_records(
                    dataset_dir, checkpoint, records, fingerprint,
                    model_config=config, run_config=run_config, resume=False,
                    fit_scope="development-only",
                    development_approval_sha256=approval_sha,
                    development_approval_path=str(approval_path))
                receipt_path = checkpoint.with_suffix(checkpoint.suffix + ".receipt.json")
                step = result["step"]
                completed_epochs = result["completed_epochs"]
                del result
                wall = time.perf_counter() - started_wall
                cpu = time.process_time() - started_cpu
                if (completed_epochs != RUN_CONFIG["epochs"] or step !=
                        RUN_CONFIG["updates_per_checkpoint"] or not checkpoint.is_file()
                        or not receipt_path.is_file() or not math.isfinite(wall)
                        or not math.isfinite(cpu) or wall <= 0 or cpu < 0):
                    raise ValueError("fit result failed epoch/update/finite receipt checks")
                item.update({"status": "completed",
                             "checkpoint": str(checkpoint),
                             "checkpoint_sha256": _sha(checkpoint),
                             "receipt": str(receipt_path),
                             "receipt_sha256": _sha(receipt_path),
                             "completed_epochs": completed_epochs,
                             "optimizer_step": step,
                             "fit_wall_seconds": wall,
                             "fit_cpu_seconds": cpu})
            except BaseException as exc:
                item.update({"status": "failed", "error_type": type(exc).__name__,
                             "error": str(exc),
                             "fit_wall_seconds": time.perf_counter() - started_wall})
                panel["status"] = "failed"
                panel["updated_unix"] = time.time()
                _atomic_json(ledger_path, panel)
                raise
            _atomic_json(ledger_path, panel)
    except BaseException:
        if panel["status"] == "running":
            panel["status"] = "interrupted_or_failed"
            panel["updated_unix"] = time.time()
            _atomic_json(ledger_path, panel)
        raise

    if (len(panel["runs"]) != len(SEEDS)
            or any(row.get("status") != "completed" for row in panel["runs"])):
        raise ValueError("V2.11 fit panel is incomplete")
    panel["status"] = "complete"
    panel["completed_unix"] = time.time()
    _atomic_json(ledger_path, panel)
    return {"status": panel["status"], "ledger": str(ledger_path),
            "ledger_sha256": _sha(ledger_path), "fit_count": len(panel["runs"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--supervision-token", required=True)
    args = parser.parse_args()
    print(json.dumps(run_panel(args.dataset, args.approval, args.output_root,
                               supervision_token=args.supervision_token),
                     sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
