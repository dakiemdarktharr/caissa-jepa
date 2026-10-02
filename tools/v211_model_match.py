"""Matched V2.11 development evaluator; never opens the locked schedule."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import v29_model_match as base_match
from two_player.games import BoardGame
from two_player.v28_model import Config, METHOD_VERSION, Model, _model_code_sha256
from two_player.v28_train import _runtime_identity
from two_player.v210_gradient_diagnostic import load_weights_only
from two_player.v211_development import (DATASET_ROOT, MODEL_CONFIG, ROOT as PROJECT,
                                         RUN_CONFIG, SCHEDULE_COMPARISONS, SEEDS,
                                         development_schedule, validate_spec)

MAX_MOVE_SECONDS = 2.0
MAX_NODES = 500_000
VARIANTS = ("reply-jepa-lambda8", "reply-jepa-lambda1-v29",
            "task-value-dynamics-v29", "direct-leaf-v29")
V29_SPEC_PATH = ROOT / "docs" / "validation" / "V29_DEV_FIT_PANEL_V01.json"
V29_LEDGER_PATH = ROOT / "chess_data" / "v29_fit_panel_dev01" / "panel.json"
V29_APPROVAL_PATH = ROOT / "chess_data" / "v29_data_dev09_approval.json"


def _sha(path: Path, *, normalize_text=False) -> str:
    raw = Path(path).read_bytes()
    if normalize_text:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _json_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  allow_nan=False).encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value):
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


def _verify_supervisor_attestation(panel: dict, panel_root: Path) -> None:
    attestation = panel.get("supervisor_attestation")
    expected_status = panel_root.with_suffix(".supervisor.json").resolve()
    if (not isinstance(attestation, dict)
            or Path(attestation.get("status_path", "")).resolve() != expected_status
            or not expected_status.is_file()
            or _sha(expected_status) != attestation.get("status_sha256")):
        raise ValueError("candidate fit ledger lacks a valid supervisor status hash")
    status = json.loads(expected_status.read_text(encoding="utf-8"))
    supervisor_hash = _sha(ROOT / "tools" / "v211_development_panel_supervisor.py")
    helper_hash = _sha(ROOT / "tools" / "v29_development_panel_supervisor.py")
    runner_hash = _sha(ROOT / "tools" / "v211_run_development_panel.py")
    samples = status.get("preflight_samples")
    if (status.get("schema") != "caissa-jepa-v211-panel-supervisor-v01"
            or status.get("status") != "complete"
            or status.get("fit_started") is not True
            or status.get("return_code") != 0
            or status.get("termination_reason") is not None
            or status.get("output") != str(panel_root.resolve())
            or status.get("supervisor_sha256") != supervisor_hash
            or status.get("resource_helper_sha256") != helper_hash
            or status.get("runner_sha256") != runner_hash
            or status.get("memory_gate_bytes") != 2_000_000_000
            or status.get("available_memory_floor_bytes") != 1_000_000_000
            or status.get("process_commit_limit_bytes") != 1_300_000_000
            or status.get("process_cpu_limit_seconds") != 4 * 60 * 60
            or status.get("panel_wall_limit_seconds") != 6 * 60 * 60
            or not isinstance(samples, list) or len(samples) != 4
            or any(row.get("available_physical_bytes", 0) < 2_000_000_000
                   for row in samples)
            or not isinstance(status.get("peak_working_set_bytes"), int)
            or status.get("peak_working_set_bytes", -1) < 0
            or status.get("elapsed_seconds", float("inf")) > 6 * 60 * 60):
        raise ValueError("V2.11 fit supervisor did not meet the frozen resource gate")
    expected_values = {
        "supervisor_code_sha256": supervisor_hash,
        "resource_helper_sha256": helper_hash,
        "runner_code_sha256": runner_hash,
        "job_object_assigned": True,
        "process_commit_limit_bytes": 1_300_000_000,
        "process_cpu_limit_seconds": 4 * 60 * 60,
        "available_memory_floor_bytes": 1_000_000_000,
        "memory_gate_bytes": 2_000_000_000,
        "stable_preflight_samples": samples,
        "peak_working_set_bytes": status["peak_working_set_bytes"],
        "elapsed_seconds": status["elapsed_seconds"],
        "termination_reason": None,
    }
    if any(attestation.get(key) != value for key, value in expected_values.items()):
        raise ValueError("panel supervisor attestation does not match its status receipt")


def _baseline_panels():
    spec = validate_spec()
    ledger_path = (ROOT / spec["baseline_panel"]["path"]).resolve()
    if ROOT.resolve() not in ledger_path.parents or _sha(ledger_path) != spec[
            "baseline_panel"]["sha256"]:
        raise ValueError("V2.9 completed baseline ledger hash mismatch")
    if _sha(V29_SPEC_PATH, normalize_text=True) != spec["baseline_panel"][
            "baseline_fit_spec_sha256"]:
        raise ValueError("V2.9 baseline fit specification hash mismatch")
    if _sha(V29_APPROVAL_PATH) != spec["parent_v29_approval_sha256"]:
        raise ValueError("V2.9 development approval hash differs from V2.11 spec")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if (ledger.get("status") != "completed" or ledger.get("locked_final_access") is not False
            or ledger.get("allowed_training_split") != "train"
            or ledger.get("dataset_fingerprint") != spec["dataset"][
                "expected_identity"]["dataset_fingerprint"]
            or ledger.get("panel_spec_sha256") != spec["baseline_panel"][
                "baseline_fit_spec_sha256"]
            or ledger.get("model_code_sha256") != _sha(
                ROOT / "two_player" / "v28_model.py", normalize_text=True)
            or ledger.get("trainer_code_sha256") != _sha(
                ROOT / "two_player" / "v28_train.py", normalize_text=True)
            or ledger.get("data_audit_code_sha256") != _sha(
                ROOT / "two_player" / "v28_data.py", normalize_text=True)
            or ledger.get("requirements_lock_sha256") != _sha(
                ROOT / "requirements-research-lock.txt", normalize_text=True)
            or ledger.get("panel_runner_code_sha256") != _sha(
                ROOT / "tools" / "v29_run_development_panel.py",
                normalize_text=True)
            or ledger.get("panel_supervisor_code_sha256") != _sha(
                ROOT / "tools" / "v29_development_panel_supervisor.py",
                normalize_text=True)):
        raise ValueError("V2.9 baseline ledger scope or status is invalid")
    rows = ledger.get("runs")
    expected = {(seed, variant) for seed in SEEDS for variant in
                ("reply-jepa", "task-value-dynamics", "direct-leaf")}
    indexed = {}
    for row in rows if isinstance(rows, list) else ():
        key = row.get("seed"), row.get("variant")
        if key not in expected or key in indexed or row.get("status") != "completed":
            raise ValueError("V2.9 baseline ledger contains a missing/duplicate run")
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError("V2.9 baseline ledger does not contain all 60 controls")
    return ledger_path, ledger, indexed


def _load_sanitized(path: Path, config: Config, expected_hash: str, *, receipt=None):
    """Load only online/EMA arrays; never deserialize NPZ metadata/history."""
    model = load_weights_only(path, config, expected_hash)
    model.training_state = {"completed_epochs": RUN_CONFIG["epochs"], "history": []}
    model.step = RUN_CONFIG["updates_per_checkpoint"]
    model._checkpoint_path = str(path.resolve())
    if receipt is not None:
        # Keep only fields consumed by provenance and panel summaries.
        model._training_receipt = receipt
    return model


def _receipt_identity(path: Path, expected: dict):
    """Hash-bind the receipt and parse only effective_run before history starts."""
    if _sha(path) != expected["receipt_sha256"]:
        raise ValueError("fit receipt bytes differ from the hash-bound panel ledger")
    effective = _extract_effective_run(path)
    wanted_model = {**expected["model_config"], "seed": expected["seed"],
                    "variant": expected["variant"]}
    if (effective.get("method") != METHOD_VERSION
            or effective.get("fit_scope") != "development-only"
            or effective.get("development_approval_sha256") !=
            expected["approval_sha256"]
            or effective.get("dataset_fingerprint") !=
            expected["dataset_fingerprint"]
            or effective.get("model") != wanted_model
            or effective.get("run") != {"epochs": RUN_CONFIG["epochs"],
                                         "shuffle_seed": RUN_CONFIG["shuffle_seed"]}
            or effective.get("runtime") != _runtime_identity()):
        raise ValueError("checkpoint effective-run identity or runtime mismatch")
    return {"fit_scope": "development-only",
            "development_approval_sha256": expected["approval_sha256"],
            "dataset_fingerprint": expected["dataset_fingerprint"],
            "dataset_sha256": expected["records_sha256"],
            "audit_sha256": expected["audit_sha256"],
            "split": "train",
            "variant": expected["variant"],
            "model_code_sha256": _sha(
                ROOT / "two_player" / "v28_model.py", normalize_text=True),
            "trainer_code_sha256": _sha(
                ROOT / "two_player" / "v28_train.py", normalize_text=True),
            "checkpoint_sha256": expected["checkpoint_sha256"],
            "optimizer_step": RUN_CONFIG["updates_per_checkpoint"],
            "completed_epochs": RUN_CONFIG["epochs"],
            "effective_run": effective}


def verify_baseline_runtime() -> dict:
    """Check all hash-bound V2.9 control runtimes before starting a V2.11 fit."""
    spec = validate_spec()
    _, _, rows = _baseline_panels()
    v29_spec = json.loads(V29_SPEC_PATH.read_text(encoding="utf-8"))
    data = spec["dataset"]["expected_identity"]
    common = {"dataset_fingerprint": data["dataset_fingerprint"],
              "records_sha256": data["records_sha256"],
              "audit_sha256": data["audit_sha256"],
              "approval_sha256": _sha(V29_APPROVAL_PATH)}
    expected_runtime = _runtime_identity()
    for seed in SEEDS:
        for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
            row = rows[(seed, variant)]
            receipt_path = Path(row["receipt"]).resolve()
            expected_root = (V29_LEDGER_PATH.parent / str(seed) / variant).resolve()
            if (receipt_path != expected_root / "checkpoint.npz.receipt.json"
                    or _sha(receipt_path) != row["receipt_sha256"]):
                raise ValueError("V2.9 runtime receipt path/hash mismatch")
            identity = _receipt_identity(receipt_path, {
                **common, "seed": seed, "variant": variant,
                "model_config": v29_spec["matched_model_config"],
                "checkpoint_sha256": row["checkpoint_sha256"],
                "receipt_sha256": row["receipt_sha256"]})
            if identity["effective_run"].get("runtime") != expected_runtime:
                raise ValueError("V2.9 control runtime differs from current runtime")
    return expected_runtime


def _extract_effective_run(path: Path) -> dict:
    """Read/parse just the effective_run JSON object, stopping before history."""
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            stripped = line.lstrip()
            if stripped.startswith('"history"'):
                raise ValueError("fit receipt places history before effective_run")
            if stripped.startswith('"effective_run"'):
                prefix = line.split(":", 1)[1].strip()
                value = []
                depth = 0
                in_string = False
                escaped = False

                def consume(chunk):
                    nonlocal depth, in_string, escaped
                    for char in chunk:
                        value.append(char)
                        if in_string:
                            if escaped:
                                escaped = False
                            elif char == "\\":
                                escaped = True
                            elif char == '"':
                                in_string = False
                        elif char == '"':
                            in_string = True
                        elif char in "{[":
                            depth += 1
                        elif char in "}]":
                            depth -= 1
                            if depth < 0:
                                raise ValueError("malformed effective_run JSON value")

                consume(prefix)
                while depth > 0:
                    char = stream.read(1)
                    if not char:
                        raise ValueError("truncated effective_run JSON value")
                    consume(char)
                if in_string or depth != 0:
                    raise ValueError("malformed effective_run JSON value")
                result = json.loads("".join(value).rstrip().rstrip(","))
                if not isinstance(result, dict):
                    raise ValueError("effective_run must be a JSON object")
                return result
    raise ValueError("fit receipt has no effective_run before history")


def _load_candidate(root: Path, seed: int, row: dict, identity: dict):
    checkpoint = Path(row["checkpoint"]).resolve()
    receipt_path = Path(row["receipt"]).resolve()
    data_root = (ROOT / "chess_data").resolve()
    if data_root not in checkpoint.parents or data_root not in receipt_path.parents:
        raise ValueError("candidate checkpoint/receipt escapes ignored output area")
    expected_root = root.resolve() / str(seed) / "reply-jepa"
    if checkpoint != expected_root / "checkpoint.npz" or receipt_path != (
            expected_root / "checkpoint.npz.receipt.json"):
        raise ValueError("candidate ledger path does not match its seed/arm directory")
    if (_sha(checkpoint) != row["checkpoint_sha256"]
            or _sha(receipt_path) != row["receipt_sha256"]):
        raise ValueError("candidate checkpoint/receipt differs from fit ledger")
    expected = {**identity, "seed": seed, "variant": "reply-jepa",
                "model_config": MODEL_CONFIG,
                "checkpoint_sha256": row["checkpoint_sha256"]}
    expected["receipt_sha256"] = row["receipt_sha256"]
    receipt = _receipt_identity(receipt_path, expected)
    cfg = Config(variant="reply-jepa", seed=seed, **MODEL_CONFIG)
    model = _load_sanitized(checkpoint, cfg, row["checkpoint_sha256"], receipt=receipt)
    model._training_receipt_path = str(receipt_path)
    return model


def _load_controls(baseline_rows: dict, data: dict):
    controls = {seed: {} for seed in SEEDS}
    v29_spec = json.loads(V29_SPEC_PATH.read_text(encoding="utf-8"))
    v29_cfg = v29_spec["matched_model_config"]
    parent_approval_sha = _sha(V29_APPROVAL_PATH)
    for seed in SEEDS:
        for public_name, variant in (("reply-jepa-lambda1-v29", "reply-jepa"),
                                     ("task-value-dynamics-v29", "task-value-dynamics"),
                                     ("direct-leaf-v29", "direct-leaf")):
            row = baseline_rows[(seed, variant)]
            checkpoint = Path(row["checkpoint"]).resolve()
            receipt_path = Path(row["receipt"]).resolve()
            root = (ROOT / "chess_data").resolve()
            if root not in checkpoint.parents or root not in receipt_path.parents:
                raise ValueError("V2.9 baseline artifact escapes ignored chess_data")
            expected_root = (V29_LEDGER_PATH.parent / str(seed) / variant).resolve()
            if checkpoint != expected_root / "checkpoint.npz" or receipt_path != (
                    expected_root / "checkpoint.npz.receipt.json"):
                raise ValueError("V2.9 control path does not match committed seed/arm")
            if (_sha(checkpoint) != row.get("checkpoint_sha256")
                    or _sha(receipt_path) != row.get("receipt_sha256")):
                raise ValueError("V2.9 control checkpoint/receipt hash mismatch")
            expected = {**data, "seed": seed, "variant": variant,
                        "model_config": v29_cfg,
                        "checkpoint_sha256": row["checkpoint_sha256"],
                        "approval_sha256": parent_approval_sha}
            expected["receipt_sha256"] = row["receipt_sha256"]
            receipt = _receipt_identity(receipt_path, expected)
            config = Config(variant=variant, seed=seed, **v29_cfg)
            model = _load_sanitized(checkpoint, config, row["checkpoint_sha256"],
                                    receipt=receipt)
            model._training_receipt_path = str(receipt_path)
            controls[seed][public_name] = model
    return controls


def _game(name: str) -> BoardGame:
    if name == "connect4-gravity-6x7":
        return BoardGame(name, 6, 7, 4, True)
    if name == "reversi6":
        return BoardGame(name, 6, 6, reversi=True)
    raise ValueError("V2.11 schedule has an unsupported game")


def _play_block(block: dict, candidate: Model, control: Model) -> dict:
    game = _game(block["game"])
    seed, match_seed = block["checkpoint_seed"], block["match_seed"]
    plus = base_match._play_game(game, candidate, control,
                                 checkpoint_seed=seed, match_seed=match_seed,
                                 max_move_seconds=MAX_MOVE_SECONDS, max_nodes=MAX_NODES)
    minus = base_match._play_game(game, control, candidate,
                                  checkpoint_seed=seed, match_seed=match_seed,
                                  max_move_seconds=MAX_MOVE_SECONDS, max_nodes=MAX_NODES)
    for result in (plus, minus):
        if not base_match._verify_game(game, result, max_move_seconds=MAX_MOVE_SECONDS,
                                       max_nodes=MAX_NODES):
            raise RuntimeError("V2.11 game failed independent transcript replay")
    return {**{key: block[key] for key in (
        "block_id", "game", "comparison", "checkpoint_seed", "match_seed")},
        "status": "model_forfeit" if "model_forfeit" in
        (plus["status"], minus["status"]) else "complete",
        "external_censored": False,
        "candidate_score": (plus["score_plus"] + 1.0 - minus["score_plus"]) / 2.0,
        "plus_game": plus,
        "minus_game": minus}


def run_schedule(candidate_panel_root, approval_path, output_path):
    spec = validate_spec()
    output_path = Path(output_path).resolve()
    data_root = (ROOT / "chess_data").resolve()
    if data_root not in output_path.parents or output_path.exists():
        raise ValueError("V2.11 match output requires a fresh ignored path")
    candidate_panel_root = Path(candidate_panel_root).resolve()
    if data_root not in candidate_panel_root.parents:
        raise ValueError("V2.11 candidate panel must be under ignored chess_data")
    candidate_ledger_path = candidate_panel_root / "panel.json"
    if not candidate_ledger_path.is_file():
        raise FileNotFoundError("completed V2.11 candidate fit ledger is required")
    candidate_ledger_sha = _sha(candidate_ledger_path)
    panel = json.loads(candidate_ledger_path.read_text(encoding="utf-8"))
    _verify_supervisor_attestation(panel, candidate_panel_root)
    approval_path = Path(approval_path).resolve()
    if (ROOT.resolve() / "chess_data") not in approval_path.parents:
        raise ValueError("V2.11 approval must remain under ignored chess_data")
    if (panel.get("status") != "complete" or panel.get("locked_final_access") is not False
            or panel.get("allowed_training_split") != "train"
            or panel.get("dataset_fingerprint") != spec["dataset"][
                "expected_identity"]["dataset_fingerprint"]
            or panel.get("dataset_manifest_sha256") != spec["dataset"][
                "expected_identity"]["manifest_sha256"]
            or panel.get("records_sha256") != spec["dataset"][
                "expected_identity"]["records_sha256"]
            or panel.get("audit_sha256") != spec["dataset"][
                "expected_identity"]["audit_sha256"]
            or len(panel.get("runs", [])) != len(SEEDS)
            or panel.get("panel_spec_sha256") != _sha(
                ROOT / "docs" / "validation" / "V211_JEPA_WEIGHT_CALIBRATION_V01.json")
            or panel.get("method_sha256") != _sha(
                ROOT / "docs" / "METHOD_V211_JEPA_WEIGHT_CALIBRATION.md",
                normalize_text=True)
            or panel.get("loader_code_sha256") != _sha(
                ROOT / "two_player" / "v211_development.py", normalize_text=True)
            or panel.get("panel_runner_code_sha256") != _sha(
                ROOT / "tools" / "v211_run_development_panel.py", normalize_text=True)
            or panel.get("model_code_sha256") != _sha(
                ROOT / "two_player" / "v28_model.py", normalize_text=True)
            or panel.get("trainer_code_sha256") != _sha(
                ROOT / "two_player" / "v28_train.py", normalize_text=True)
            or panel.get("data_audit_code_sha256") != _sha(
                ROOT / "two_player" / "v28_data.py", normalize_text=True)
            or panel.get("requirements_lock_sha256") != _sha(
                ROOT / "requirements-research-lock.txt", normalize_text=True)
            or panel.get("runtime_identity") != _runtime_identity()
            or panel.get("approval_sha256") != _sha(approval_path)):
        raise ValueError("V2.11 candidate ledger is incomplete or stale")
    candidate_rows = {}
    for row in panel["runs"]:
        seed = row.get("seed")
        if (seed not in SEEDS or seed in candidate_rows
                or row.get("variant") != "reply-jepa"
                or row.get("status") != "completed"
                or row.get("completed_epochs") != RUN_CONFIG["epochs"]
                or row.get("optimizer_step") != RUN_CONFIG["updates_per_checkpoint"]):
            raise ValueError("V2.11 candidate ledger run inventory is invalid")
        candidate_rows[seed] = row
    if set(candidate_rows) != set(SEEDS):
        raise ValueError("V2.11 candidate ledger omits a seed")
    expected_data = spec["dataset"]["expected_identity"]
    identity = {"dataset_fingerprint": expected_data["dataset_fingerprint"],
                "records_sha256": expected_data["records_sha256"],
                "audit_sha256": expected_data["audit_sha256"],
                "approval_sha256": panel["approval_sha256"]}
    candidates = {seed: _load_candidate(candidate_panel_root, seed,
                                        candidate_rows[seed], identity)
                  for seed in SEEDS}
    _, baseline_ledger, baseline_rows = _baseline_panels()
    base_identity = {"dataset_fingerprint": expected_data["dataset_fingerprint"],
                     "records_sha256": expected_data["records_sha256"],
                     "audit_sha256": expected_data["audit_sha256"],
                     "approval_sha256": _sha(V29_APPROVAL_PATH)}
    controls = _load_controls(baseline_rows, base_identity)
    schedule = development_schedule()
    if len(schedule) != spec["schedule"]["blocks"] or _json_sha(schedule) != spec[
            "schedule"]["schedule_sha256"]:
        raise ValueError("V2.11 schedule does not match frozen hash")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    partial = output_path.with_suffix(output_path.suffix + ".partial.jsonl")
    receipt_path = output_path.with_suffix(output_path.suffix + ".receipt.json")
    if any(path.exists() for path in (temporary, partial, receipt_path)):
        raise FileExistsError("V2.11 match artifact path already exists")
    header = {"schema": "caissa-jepa-v211-development-match-v01",
              "record_type": "manifest", "status": "complete schedule required",
              "schedule_sha256": _json_sha(schedule), "block_count": len(schedule),
              "max_move_seconds": MAX_MOVE_SECONDS, "max_nodes_per_move": MAX_NODES,
              "candidate_panel_sha256": candidate_ledger_sha,
              "baseline_panel_sha256": _sha(V29_LEDGER_PATH),
              "locked_final_access": False, "confirmatory": False}
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    completed = forfeits = 0
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(header, sort_keys=True, allow_nan=False) + "\n")
            for block in schedule:
                seed = block["checkpoint_seed"]
                control = controls[seed][block["comparison"]]
                record = _play_block(block, candidates[seed], control)
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                completed += 1
                forfeits += record["status"] == "model_forfeit"
                if completed % 5 == 0:
                    stream.flush()
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if temporary.exists():
            temporary.replace(partial)
        raise
    temporary.replace(output_path)
    receipt = {"schema": "caissa-jepa-v211-development-match-v01-receipt",
               "status": "complete", "confirmatory": False,
               "schedule_sha256": _json_sha(schedule), "block_count": completed,
               "game_count": completed * 2, "model_forfeit_blocks": forfeits,
               "artifact_sha256": _sha(output_path),
               "artifact_bytes": output_path.stat().st_size,
               "wall_seconds": time.perf_counter() - started_wall,
               "cpu_seconds": time.process_time() - started_cpu,
               "candidate_panel_sha256": candidate_ledger_sha,
               "baseline_panel_sha256": _sha(V29_LEDGER_PATH),
               "model_match_source_sha256": _sha(Path(__file__), normalize_text=True),
               "checkpoint_sha256": {
                   str(seed): {name: _sha(Path(model._checkpoint_path))
                               for name, model in {
                                   "reply-jepa-lambda8": candidates[seed],
                                   **controls[seed]}.items()} for seed in SEEDS}}
    _atomic_json(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_panel_root", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_schedule(args.candidate_panel_root, args.approval, args.output),
                     sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
