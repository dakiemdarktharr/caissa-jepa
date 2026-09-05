"""Reproducible trainer for the FEN-based CAISSA A-JEPA v7 dataset."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
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


def atomic_json(path: Path, payload: dict, replace_attempts: int = 8) -> None:
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


def train(arguments: argparse.Namespace, progress_callback: Optional[Callable[[dict], None]] = None) -> int:
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
    deadline_epoch = time.time() + budget_hours * 3600.0 if budget_hours > 0 else None
    dataset_dir = Path(arguments.dataset)
    model_path = Path(arguments.model)
    checkpoint_exists = model_path.exists()
    if resume and not checkpoint_exists:
        raise FileNotFoundError(f"Không thể resume: chưa có checkpoint {model_path}")
    fingerprint = dataset_manifest_fingerprint(dataset_dir)
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
    if not checkpoint_exists:
        model.seed = arguments.seed
        model._initialize()
    else:
        # Older baseline checkpoints omitted seed; the checked run report is authoritative.
        model.seed = arguments.seed
    if model.dataset_fingerprint and model.dataset_fingerprint != fingerprint and not allow_dataset_change:
        raise RuntimeError(
            "Dataset fingerprint khác checkpoint: "
            f"checkpoint={model.dataset_fingerprint}, current={fingerprint}. "
            "Dùng checkpoint mới hoặc --allow-dataset-change sau khi đã ghi "
            "nhận lý do thí nghiệm."
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
        "model": str(model_path),
        "dataset": str(dataset_dir),
        "dataset_fingerprint": fingerprint,
        "seed": arguments.seed,
        "architecture": architecture,
        "model_variant": model_variant,
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
        "runtime_version": 2,
        "objective_version": 2,
        "resume_policy": "restart unfinished epoch from saved weights",
        "eta_seconds": None,
        "estimated_finish_timestamp": None,
        "progress_percent": 0.0,
        "cache_workers": cache_workers,
        "time_budget_hours": budget_hours,
    })
    atomic_json(report_path, report)
    last_progress_write = 0.0

    def save_progress(epoch: int, phase: str, batch_index: int, latest: Optional[dict] = None) -> None:
        nonlocal last_progress_write
        now = time.monotonic()
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
            "rows_per_second": arguments.batch_size / max(1e-9, float(np.mean(eta.times[phase]))),
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
        if deadline_epoch and time.time() >= deadline_epoch:
            raise TimeoutError("Training time budget exceeded")

    try:
        check_deadline()
        if progress_callback is not None:
            progress_callback(report.copy())
        def cache_progress(payload):
            report.update(payload)
            report["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            atomic_json(report_path, report)
            if progress_callback:
                progress_callback(report.copy())
        cache = SampleCache(dataset_dir, fingerprint, arguments.validation_percent, cache_progress, workers=cache_workers, deadline_epoch=deadline_epoch).prepare()
        phase_batches = {
            phase: min(math.ceil(cache.counts[phase] / arguments.batch_size), limit)
            if limit else math.ceil(cache.counts[phase] / arguments.batch_size)
            for phase, limit in (("train", arguments.max_train_batches), ("validation", arguments.max_validation_batches))
        }
        if not phase_batches["train"]:
            raise ValueError("No valid training samples in this split")
        eta = TrainingETA(phase_batches, arguments.epochs)
        report.update({"split_positions": cache.counts, "skipped_samples": cache.skipped, "cache_workers": cache_workers,
                       "cache_path": str(cache.path), "time_budget_hours": budget_hours, **eta.fields()})
        for epoch_offset in range(arguments.epochs):
            check_deadline()
            epoch = completed_epochs + epoch_offset + 1
            train_values = MetricMean()
            tick = time.monotonic()
            for index, batch in enumerate(cache.batches("train", arguments.batch_size, arguments.seed + epoch), 1):
                check_deadline()
                latest = model.train_batch(batch, arguments.learning_rate)
                train_values.add(latest, len(batch))
                eta.observe("train", time.monotonic() - tick)
                tick = time.monotonic()
                save_progress(epoch, "train", index, latest)
                if arguments.max_train_batches and index >= arguments.max_train_batches:
                    break
            validation_values = MetricMean()
            tick = time.monotonic()
            for index, batch in enumerate(cache.batches("validation", arguments.batch_size, arguments.seed), 1):
                check_deadline()
                latest = model.evaluate_batch(batch)
                validation_values.add(latest, len(batch))
                eta.observe("validation", time.monotonic() - tick)
                tick = time.monotonic()
                save_progress(epoch, "validation", index, latest)
                if arguments.max_validation_batches and index >= arguments.max_validation_batches:
                    break
            model.save()
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
            atomic_json(report_path, report)
            if progress_callback is not None:
                progress_callback(report.copy())
            print(json.dumps(epoch_report, ensure_ascii=False, sort_keys=True))
        report.update({
            "status": "COMPLETE",
            "phase": "complete",
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trained_steps": model.trained_steps,
            "eta_seconds": 0.0,
            "estimated_finish_timestamp": time.time(),
            "progress_percent": 100.0,
        })
        atomic_json(report_path, report)
        if progress_callback is not None:
            progress_callback(report.copy())
    except BaseException as error:
        try:
            model.save()
        except Exception:
            pass
        report.update({
            "status": "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "TIME_BUDGET_EXCEEDED" if isinstance(error, TimeoutError) else "FAILED",
            "error": repr(error),
            "trained_steps": model.trained_steps,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        atomic_json(report_path, report)
        raise
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", default="chess_data/caissa_a_jepa_v7.npz")
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
        choices=("h1", "full", "sigreg", "direct", "nnue"),
        default="full",
    )
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-train-batches", type=int, default=0)
    parser.add_argument("--max-validation-batches", type=int, default=0)
    parser.add_argument("--allow-dataset-change", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Tiếp tục từ checkpoint và training report hiện có")
    parser.add_argument("--progress-interval", type=float, default=10.0, help="Số giây tối thiểu giữa hai lần ghi heartbeat")
    parser.add_argument("--cache-workers", type=int, default=0, help="Cache worker processes; 0 = auto, up to 8")
    parser.add_argument("--time-budget-hours", type=float, default=8.0, help="Hard wall-clock budget including cache and training")
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
