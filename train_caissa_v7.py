"""MARS-JEPA Chess verified FEN trainer (legacy train_caissa_v7 entry point)."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import uuid
import traceback
import copy
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from adversarial_jepa import (
    AdversarialJEPA,
    dataset_manifest_fingerprint,
    iter_dataset_games,
    sample_from_dataset_position,
    stable_split,
)
from policy_value_baseline import DirectPolicyValueBaseline
from lejepa import LeJEPA
from nnue_baseline import NNUEStyleBaseline
from training_runtime import SampleCache, MetricMean, TrainingETA
from runtime_safety import FileLease, atomic_json, checkpoint_commit, restore_committed, path_diagnostics


def mean_metrics(values: list[dict]) -> dict:
    if not values:
        return {}
    keys = sorted({key for item in values for key in item})
    return {
        key: float(sum(item[key] for item in values if key in item) / sum(1 for item in values if key in item))
        for key in keys
    }


def batches(dataset_dir: Path, split: str, batch_size: int, seed: int, validation_percent: int):
    generator = np.random.default_rng(seed)
    pending = []
    for game in iter_dataset_games(dataset_dir):
        if stable_split(game["game_hash"], validation_percent) != split:
            continue
        for position in game["positions"]:
            sample = sample_from_dataset_position(position, generator)
            if sample is None:
                continue
            pending.append(sample)
            if len(pending) == batch_size:
                yield pending
                pending = []
    if pending:
        yield pending


def read_json_with_retry(path: Path, attempts: int = 8) -> dict:
    for attempt in range(attempts):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (PermissionError, json.JSONDecodeError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(0.05 * (2**attempt), 1.0))
    raise AssertionError("unreachable")


def _legacy_atomic_json(path: Path, payload: dict, replace_attempts: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    for attempt in range(replace_attempts):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 == replace_attempts:
                raise
            time.sleep(min(0.05 * (2**attempt), 1.0))


def train(arguments: argparse.Namespace, progress_callback=None):
    try:
        return _train_with_lease(arguments, progress_callback)
    except BaseException as error:
        # Failures acquiring the lease must never overwrite its owner's report.
        # A separate per-attempt receipt still makes those failures diagnosable.
        model = Path(arguments.model).resolve()
        run_id = getattr(arguments, "run_id", uuid.uuid4().hex)
        failure = {"status": "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "FAILED",
                   "phase": getattr(arguments, "phase", "preflight"), "pid": os.getpid(), "run_id": run_id,
                   "dataset_fingerprint": getattr(arguments, "verified_dataset_fingerprint", None),
                   "model_configuration": {k: getattr(arguments, k, None) for k in ("architecture", "model_variant", "latent_size", "seed", "resume")},
                   "path_diagnostics": path_diagnostics(arguments), "error": repr(error), "traceback": traceback.format_exc()}
        try:
            atomic_json(model.with_name(model.stem + ".failure-" + run_id + ".json"), failure)
        except OSError:
            pass  # Callback remains available if even the output parent is unavailable.
        if progress_callback:
            progress_callback(failure)
        raise


def _train_with_lease(arguments: argparse.Namespace, progress_callback: Optional[Callable[[dict], None]] = None) -> int:
    run_id = uuid.uuid4().hex
    arguments.run_id = run_id
    arguments.phase = "preflight"
    if getattr(arguments, "model_id", None):
        from model_registry import spec_by_id
        spec = spec_by_id(Path.cwd(), arguments.model_id)
        if spec is None or not spec["trainable"]:
            raise ValueError("Unknown trainable model ID")
        arguments.architecture, arguments.model_variant = spec["architecture"], spec["variant"]
    path = Path(arguments.model).resolve()
    # Only the lease owner may publish the canonical training report.
    with FileLease(path.with_suffix(".writer.lock")):
        diagnostics = path_diagnostics(arguments)
        try:
            if not getattr(arguments, "resume", False) and path.exists() and not getattr(arguments, "archive_existing", False):
                raise FileExistsError("NEW training requires a new checkpoint path; select Resume for existing weights")
            if getattr(arguments, "resume", False):
                committed = restore_committed(path)
                if committed is not None:
                    atomic_json(path.with_suffix(".training.json"), committed)
            return _train_locked(arguments, progress_callback)
        except BaseException as error:
            report_path = path.with_suffix(".training.json")
            try:
                report = read_json_with_retry(report_path) if report_path.exists() else {}
            except Exception:
                report = {}
            report.update({"status": "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else
                           "TIME_BUDGET_EXCEEDED" if isinstance(error, TimeoutError) else "FAILED",
                           "error": repr(error),
                           "traceback": traceback.format_exc(),
                           "error_type": type(error).__name__, "error_filename": str(getattr(error, "filename", "") or ""),
                           "path_diagnostics": diagnostics,
                           "run_id": run_id, "pid": os.getpid(),
                           "phase": getattr(arguments, "phase", "preflight"),
                           "dataset_fingerprint": report.get("dataset_fingerprint") or None,
                           "model_configuration": {k: getattr(arguments, k, None) for k in
                               ("architecture", "model_variant", "latent_size", "seed", "resume")}})
            report.setdefault("completed_epochs", 0)
            report.setdefault("trained_steps", 0)
            try:
                atomic_json(report_path, report)
            except OSError as reporting_error:
                if progress_callback:
                    progress_callback({**report, "report_write_error": repr(reporting_error)})
            raise


def _train_locked(arguments, progress_callback=None):
    # Preserve the programmatic API used by early v7 scripts, which did not
    # yet have an explicit architecture argument.
    architecture = getattr(arguments, "architecture", "adversarial-jepa")
    model_variant = getattr(arguments, "model_variant", "full")
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
    elif architecture == "policy-value" and model_variant == "full":
        model_variant = "direct"
    elif architecture == "nnue" and model_variant == "full":
        model_variant = "nnue"
    resume = bool(getattr(arguments, "resume", False))
    progress_interval = float(getattr(arguments, "progress_interval", 10.0))
    allow_dataset_change = bool(getattr(arguments, "allow_dataset_change", False))
    cache_workers = int(getattr(arguments, "cache_workers", 0) or 0)
    budget_hours = float(getattr(arguments, "time_budget_hours", 8.0) or 0.0)
    if getattr(arguments, "deadline_epoch", None) is not None:
        raise ValueError("Shared/global deadlines are unsupported. Use the per-model active training time budget.")
    deadline_epoch = None
    explicit_deadline = deadline_epoch is not None
    # Cooperative cutoff reserves time for persistence/shutdown. This is not
    # an OS-enforced kill: disk stalls may still exceed the reserve.
    cutoff = deadline_epoch - min(30.0, budget_hours * 180.0) if deadline_epoch else None
    if getattr(arguments, "allow_dataset_change", False):
        raise ValueError("Dataset fingerprint overrides are disabled. Use matching verified data or a new checkpoint.")
    if arguments.epochs <= 0 or arguments.batch_size <= 0:
        raise ValueError("epochs and batch-size must be positive; zero-step runs cannot complete")
    arguments.phase = "validating_dataset"
    from research_dataset import resolve_dataset, verify_plan, verify_temporary_fixture
    dataset_dir = resolve_dataset(Path.cwd(), arguments.dataset)
    model_path = Path(arguments.model).resolve()
    checkpoint_exists = model_path.exists()
    if resume and not checkpoint_exists:
        raise FileNotFoundError(f"Cannot resume: checkpoint does not exist: {model_path}")
    from dataset_integrity import validate_dataset
    validation_started = time.perf_counter()
    integrity_receipt = validate_dataset(dataset_dir, progress_callback)
    integrity_seconds = time.perf_counter() - validation_started
    fingerprint = dataset_manifest_fingerprint(dataset_dir)
    split_plan = None
    split_plan_hash = None
    fixture_only = verify_temporary_fixture(dataset_dir, getattr(arguments, "fixture_only", False))
    if getattr(arguments, "split_plan", None) and not fixture_only:
        split_plan = verify_plan(dataset_dir, arguments.split_plan)
        from dataset_integrity import sha256_file
        split_plan_hash = sha256_file(arguments.split_plan)
        fingerprint = split_plan["dataset_fingerprint"]
    elif not fixture_only:
        raise ValueError("Training requires a verified version-2 research audit and locked split plan. Select or download a verified dataset.")
    elif getattr(arguments, "split_plan", None):
        split_plan = read_json_with_retry(Path(arguments.split_plan))
        from dataset_integrity import sha256_file
        import hashlib
        split_plan_hash = sha256_file(arguments.split_plan)
        fingerprint = hashlib.sha256((fingerprint + split_plan_hash).encode()).hexdigest()
    arguments.verified_dataset_fingerprint = fingerprint
    archived_checkpoint = None
    if getattr(arguments, "archive_existing", False):
        if resume:
            raise ValueError("Archive-existing is only valid in fresh mode")
        if checkpoint_exists:
            from runtime_safety import archive_checkpoint
            archived_checkpoint = archive_checkpoint(model_path)
            checkpoint_exists = False
    previous_report_path = model_path.with_suffix(".training.json")
    if checkpoint_exists and previous_report_path.exists():
        previous_report = read_json_with_retry(previous_report_path)
        if previous_report.get("validation_percent", arguments.validation_percent) != arguments.validation_percent:
            raise ValueError("Resume requires the original validation split; use a new checkpoint")
        if previous_report.get("seed", arguments.seed) != arguments.seed:
            raise ValueError("Resume requires the original seed; use a new checkpoint")
    if architecture == "adversarial-jepa":
        model = AdversarialJEPA(
            model_path,
            latent_size=arguments.latent_size,
            variant=model_variant,
        )
    elif architecture == "lejepa":
        model = LeJEPA(
            model_path,
            latent_size=arguments.latent_size,
            variant=model_variant,
        )
    elif architecture == "nnue":
        model = NNUEStyleBaseline(
            model_path,
            latent_size=arguments.latent_size,
            variant=model_variant,
        )
    elif architecture == "policy-value":
        model = DirectPolicyValueBaseline(
            model_path,
            latent_size=arguments.latent_size,
        )
    else:
        raise ValueError(f"Unknown architecture: {architecture}")
    for option, field, applicable, default in (("ema_decay", "ema_decay", architecture == "adversarial-jepa", .995),
                                               ("sigreg_weight", "sigreg_weight", architecture == "lejepa", .2)):
        value = getattr(arguments, option, None)
        if value is None:
            continue
        if not applicable or not math.isfinite(value) or value < 0 or (option == "ema_decay" and value >= 1):
            raise ValueError("Invalid ablation setting: " + option)
        if checkpoint_exists and not math.isclose(float(getattr(model, field, default)), value, rel_tol=1e-6, abs_tol=1e-8):
            raise ValueError("Resume must preserve " + option + "; use a new checkpoint")
        setattr(model, field, value)
    if not checkpoint_exists:
        model.seed = arguments.seed
        model._initialize()
    else:
        # Older baseline checkpoints omitted seed; the checked run report is authoritative.
        model.seed = arguments.seed
    if checkpoint_exists and model.dataset_fingerprint != fingerprint:
        raise RuntimeError(
            "Dataset fingerprint differs from checkpoint: "
            f"checkpoint={model.dataset_fingerprint}, current={fingerprint}. "
            "Existing checkpoint is incompatible/unverified. Select matching verified data or a new checkpoint."
        )
    model.dataset_fingerprint = fingerprint
    report_path = model_path.with_suffix(".training.json")
    if resume and report_path.exists():
        report = read_json_with_retry(report_path)
    else:
        report = {"epochs": []}
    completed_epochs = int(report.get("completed_epochs", len(report.get("epochs", []))))
    if checkpoint_exists:
        report.setdefault("continuations", []).append({
            "from_step": model.trained_steps, "previous_runtime_version": report.get("runtime_version", 1),
            "runtime_version": 2, "objective_version": 2,
            "note": "Weighted objectives corrected; old loss curves are not directly comparable. Fresh training is recommended for the paper.",
        })
    report.update({
        "run_id": arguments.run_id,
        "research_name": "MARS-JEPA Chess",
        "fixture_only": fixture_only,
        "archived_checkpoint": archived_checkpoint,
        "pid": os.getpid(),
        "model": str(model_path),
        "dataset": str(dataset_dir),
        "path_diagnostics": path_diagnostics(arguments),
        "dataset_fingerprint": fingerprint,
        "dataset_validation": integrity_receipt,
        "dataset_validation_seconds": integrity_seconds,
        "split_plan_sha256": split_plan_hash,
        "split_policy": "locked research split plan" if split_plan else "legacy hash train/validation; exploratory only",
        "seed": arguments.seed,
        "architecture": architecture,
        "model_variant": model_variant,
        "ablation": {"ema_decay": getattr(model, "ema_decay", None), "sigreg_weight": getattr(model, "sigreg_weight", None)},
        "batch_size": arguments.batch_size,
        "learning_rate": arguments.learning_rate,
        "validation_percent": arguments.validation_percent,
        "requested_epochs": arguments.epochs,
        "resume": resume,
        "status": "RUNNING",
        "started_at": report.get("started_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        "starting_epoch": completed_epochs,
        "target_epoch": completed_epochs + arguments.epochs,
        "current_epoch": completed_epochs + 1,
        "current_batch": 0,
        "phase": "starting",
        "completed_epochs": completed_epochs,
        "trained_steps": model.trained_steps,
        "runtime_version": 3,
        "objective_version": 2,
        "resume_policy": "rollback unfinished epoch to committed generation (optimizer and EMA included)",
        "eta_seconds": None,
        "estimated_finish_timestamp": None,
        "progress_percent": 0.0,
        "cache_workers": cache_workers,
        "time_budget_hours": budget_hours,
        "budget_protocol": getattr(arguments, "budget_protocol", "active training time; queue and preparation excluded"),
        "queue_seconds": float(getattr(arguments, "queue_seconds", 0.0)),
        "phase_seconds": {"cache": 0.0, "train": 0.0, "validation": 0.0, "checkpoint_io": 0.0},
        "deadline_epoch": deadline_epoch,
    })
    for stale_key in ("error", "traceback", "error_type", "error_filename", "budget_completion"):
        report.pop(stale_key, None)
    report.pop("finished_at", None)
    from model_registry import training_model_specs, model_manifest
    from research_diagnostics import reproducibility_manifest
    spec = next(item for item in training_model_specs(model_path.parent.parent)
                if item["architecture"] == architecture and item["variant"] == (model_variant if architecture != "policy-value" else "direct"))
    report["model_configuration"] = model_manifest(spec, model)
    report["reproducibility"] = reproducibility_manifest(
        report["model_configuration"], fingerprint, split_plan_hash, [arguments.seed],
        {"status": "not applicable to training"}, {"status": "not used for historical supervision"},
        {"loss": "objective-specific weighted mean", "strength": "not measured"},
        {"epochs": arguments.epochs, "training_hours": budget_hours, "early_stopping": False})
    arguments.phase = "checkpoint_commit"
    checkpoint_commit(model, report.copy())
    starting_steps = model.trained_steps
    committed_steps = model.trained_steps
    committed_report = copy.deepcopy(report)
    atomic_json(report_path, report)
    last_progress_write = 0.0

    def save_progress(epoch: int, phase: str, batch_index: int, latest: Optional[dict] = None) -> None:
        nonlocal last_progress_write
        now = time.perf_counter()
        if batch_index != 1 and now - last_progress_write < progress_interval:
            return
        report.update({
            "status": "RUNNING",
            "current_epoch": epoch,
            "phase": phase,
            "current_batch": batch_index,
            "trained_steps": model.trained_steps,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **eta.fields(),
            "phase_batches": phase_batches[phase],
            "rows_per_second": eta.rows_per_second(phase),
        })
        if latest is not None:
            report["latest_metrics"] = latest
            if isinstance(latest.get("loss"), (int, float)):
                report.setdefault("plot_history", []).append({"step": model.trained_steps, "phase": phase, "loss": latest["loss"]})
                report["plot_history"] = report["plot_history"][-600:]
        atomic_json(report_path, report)
        last_progress_write = now
        if progress_callback is not None:
            progress_callback(report.copy())

    def check_deadline() -> None:
        stop = getattr(arguments, "stop_event", None)
        if stop is not None and stop.is_set():
            raise KeyboardInterrupt("Training stopped")
        if cutoff and time.time() >= cutoff:
            raise TimeoutError("Training time budget exceeded")

    try:
        check_deadline()
        if progress_callback is not None:
            progress_callback(report.copy())
        def cache_progress(payload):
            check_deadline()
            report.update(payload)
            report["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            atomic_json(report_path, report)
            if progress_callback:
                progress_callback(report.copy())
        arguments.phase = "cache_preparation"
        preparation_started = time.perf_counter()
        preparation_cutoff = cutoff if explicit_deadline else time.time() + float(getattr(arguments, "cache_budget_hours", 8.0)) * 3600
        cache = SampleCache(dataset_dir, fingerprint, arguments.validation_percent, cache_progress, workers=cache_workers, deadline_epoch=preparation_cutoff, split_plan=split_plan).prepare()
        report["phase_seconds"]["cache"] = time.perf_counter() - preparation_started
        if not explicit_deadline:
            deadline_epoch = time.time() + budget_hours * 3600.0 if budget_hours > 0 else None
            cutoff = deadline_epoch - min(30.0, budget_hours * 180.0) if deadline_epoch else None
        report["deadline_epoch"] = deadline_epoch
        report["budget_started_at"] = time.time()
        report["validation_available"] = bool(cache.counts["validation"])
        report["experiment_status"] = "EXPLORATORY"

        phase_batches = {
            phase: min(math.ceil(cache.counts[phase] / arguments.batch_size), limit)
            if limit else math.ceil(cache.counts[phase] / arguments.batch_size)
            for phase, limit in (("train", arguments.max_train_batches), ("validation", arguments.max_validation_batches))
        }
        if not phase_batches["train"]:
            raise ValueError("No valid training samples in this split")
        eta = TrainingETA(phase_batches, arguments.epochs)
        report.update({"split_positions": cache.counts, "skipped_samples": cache.skipped, "cache_workers": cache_workers,
                       "cache_path": str(cache.path), "time_budget_hours": budget_hours,
                       "cache_shards_completed": len(cache.manifest["shards"]), "cache_shards_total": len(cache.manifest["shards"]),
                       "prepared_positions": sum(s["source_positions"] for s in cache.manifest["shards"]),
                       "valid_cache_positions": sum(cache.counts.values()), **eta.fields()})
        for epoch_offset in range(arguments.epochs):
            check_deadline()
            epoch = completed_epochs + epoch_offset + 1
            train_values = MetricMean()
            tick = time.perf_counter()
            for index, batch in enumerate(cache.batches("train", arguments.batch_size, arguments.seed + epoch), 1):
                check_deadline()
                arguments.phase = "training"
                latest = model.train_batch(batch, arguments.learning_rate)
                train_values.add(latest, len(batch))
                report["phase_seconds"]["train"] += time.perf_counter() - tick
                eta.observe("train", time.perf_counter() - tick, len(batch))
                tick = time.perf_counter()
                save_progress(epoch, "train", index, latest)
                if arguments.max_train_batches and index >= arguments.max_train_batches:
                    break
            validation_values = MetricMean()
            tick = time.perf_counter()
            for index, batch in enumerate(cache.batches("validation", arguments.batch_size, arguments.seed), 1):
                check_deadline()
                arguments.phase = "validation"
                latest = model.evaluate_batch(batch)
                validation_values.add(latest, len(batch))
                report["phase_seconds"]["validation"] += time.perf_counter() - tick
                eta.observe("validation", time.perf_counter() - tick, len(batch))
                tick = time.perf_counter()
                save_progress(epoch, "validation", index, latest)
                if arguments.max_validation_batches and index >= arguments.max_validation_batches:
                    break
            epoch_report = {
                "epoch": epoch,
                "trained_steps": model.trained_steps,
                "train": train_values.result(),
                "validation": validation_values.result(),
            }
            report["epochs"].append(epoch_report)
            report.update({
                "completed_epochs": epoch,
                "trained_steps": model.trained_steps,
                "phase": "epoch_complete",
                "current_epoch": epoch,
                "current_batch": 0,
                "latest_metrics": epoch_report,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **eta.fields(),
            })
            arguments.phase = "checkpoint_commit"
            checkpoint_started = time.perf_counter()
            checkpoint_commit(model, report.copy())
            report["phase_seconds"]["checkpoint_io"] += time.perf_counter() - checkpoint_started
            committed_steps = model.trained_steps
            committed_report = copy.deepcopy(report)
            atomic_json(report_path, report)
            if progress_callback is not None:
                progress_callback(report.copy())
            if __import__("sys").stdout is not None:
                print(json.dumps(epoch_report, ensure_ascii=False, sort_keys=True))
        if model.trained_steps <= starting_steps:
            raise ValueError("Zero-step run cannot be reported as trained")
        report.update({
            "status": "COMPLETE",
            "phase": "complete",
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trained_steps": model.trained_steps,
            "budget_completion": "COMPLETE",
            "eta_seconds": 0.0,
            "estimated_finish_timestamp": time.time(),
            "progress_percent": 100.0,
        })
        atomic_json(report_path, report)
        if progress_callback is not None:
            progress_callback(report.copy())
    except BaseException as error:
        report["completed_epochs"] = committed_report["completed_epochs"]
        report["epochs"] = committed_report["epochs"]
        report.update({
            "status": "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "TIME_BUDGET_EXCEEDED" if isinstance(error, TimeoutError) else "FAILED",
            "error": repr(error),
            "traceback": traceback.format_exc(),
            "budget_completion": "PARTIAL",
            "uncommitted_steps_discarded": model.trained_steps - committed_steps,
            "trained_steps": committed_steps,
            "resume_policy": "rollback unfinished epoch to committed generation (optimizer and EMA included)",
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        atomic_json(report_path, report)
        raise
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", default="chess_data/caissa_a_jepa_v7.npz")
    parser.add_argument("--model-id", help="Stable registry ID or research alias (h1, h1-h2, full, no-response, lejepa-inspired, direct-policy-value, nnue-style)")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--latent-size", type=int, default=96)
    parser.add_argument(
        "--architecture",
        choices=("adversarial-jepa", "lejepa", "policy-value", "nnue"),
        default="adversarial-jepa",
    )
    parser.add_argument(
        "--model-variant",
        choices=("h1", "h1-h2", "full", "no-response", "sigreg", "direct", "nnue"),
        default="full",
    )
    parser.add_argument("--ema-decay", type=float, help="JEPA EMA decay; 0 disables averaging with the same architecture/objective")
    parser.add_argument("--sigreg-weight", type=float, help="LeJEPA SIGReg weight; 0 disables this regularizer")
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-train-batches", type=int, default=0)
    parser.add_argument("--max-validation-batches", type=int, default=0)
    parser.add_argument("--allow-dataset-change", action="store_true", help="Deprecated: always rejected")
    parser.add_argument("--split-plan", help="Locked research split plan; selection and test games are never trained")
    parser.add_argument("--archive-existing", action="store_true", help="Fresh mode only: preserve existing weights/reports in a separate archive before starting")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fresh", action="store_true", help="Explicit fresh mode; checkpoint path must be unused")
    mode.add_argument("--resume", action="store_true", help="Explicitly resume an existing checkpoint and matching dataset")
    parser.add_argument("--progress-interval", type=float, default=10.0, help="Minimum seconds between heartbeat writes")
    parser.add_argument("--cache-workers", type=int, default=0, help="Cache worker processes; 0 = conservative auto, up to 2")
    parser.add_argument("--time-budget-hours", type=float, default=8.0, help="Cooperative active training budget excluding queue and preparation; reserves shutdown time")
    return parser


def main() -> int:
    if hasattr(__import__("sys").stdout, "reconfigure"):
        __import__("sys").stdout.reconfigure(encoding="utf-8", errors="replace")
    arguments = build_parser().parse_args()
    if arguments.epochs <= 0 or arguments.batch_size <= 0 or arguments.progress_interval <= 0:
        raise ValueError("epochs và batch-size phải lớn hơn 0")
    if not 0 < arguments.validation_percent < 100:
        raise ValueError("validation-percent phải nằm trong khoảng 1..99")
    return train(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
