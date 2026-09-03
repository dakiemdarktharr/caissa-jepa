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
    resume = bool(getattr(arguments, "resume", False))
    progress_interval = float(getattr(arguments, "progress_interval", 10.0))
    allow_dataset_change = bool(getattr(arguments, "allow_dataset_change", False))
    dataset_dir = Path(arguments.dataset)
    model_path = Path(arguments.model)
    checkpoint_exists = model_path.exists()
    if resume and not checkpoint_exists:
        raise FileNotFoundError(f"Không thể resume: chưa có checkpoint {model_path}")
    fingerprint = dataset_manifest_fingerprint(dataset_dir)
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
    else:
        model = DirectPolicyValueBaseline(
            model_path,
            latent_size=arguments.latent_size,
        )
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
        })
        if latest is not None:
            report["latest_metrics"] = latest
        atomic_json(report_path, report)
        last_progress_write = now
        if progress_callback is not None:
            progress_callback(report.copy())

    try:
        if progress_callback is not None:
            progress_callback(report.copy())
        for epoch_offset in range(arguments.epochs):
            epoch = completed_epochs + epoch_offset + 1
            train_values = []
            for index, batch in enumerate(batches(dataset_dir, "train", arguments.batch_size, arguments.seed + epoch, arguments.validation_percent), 1):
                train_values.append(model.train_batch(batch, arguments.learning_rate))
                save_progress(epoch, "train", index, train_values[-1])
                if arguments.max_train_batches and index >= arguments.max_train_batches:
                    break
            validation_values = []
            for index, batch in enumerate(batches(dataset_dir, "validation", arguments.batch_size, arguments.seed, arguments.validation_percent), 1):
                validation_values.append(model.evaluate_batch(batch))
                save_progress(epoch, "validation", index, validation_values[-1])
                if arguments.max_validation_batches and index >= arguments.max_validation_batches:
                    break
            model.save()
            epoch_report = {
                "epoch": epoch,
                "trained_steps": model.trained_steps,
                "train": mean_metrics(train_values),
                "validation": mean_metrics(validation_values),
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
            "status": "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "FAILED",
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
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--latent-size", type=int, default=96)
    parser.add_argument(
        "--architecture",
        choices=("adversarial-jepa", "lejepa", "policy-value"),
        default="adversarial-jepa",
    )
    parser.add_argument(
        "--model-variant",
        choices=("h1", "h1-h2", "full", "no-response", "sigreg", "direct"),
        default="full",
    )
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-train-batches", type=int, default=0)
    parser.add_argument("--max-validation-batches", type=int, default=0)
    parser.add_argument("--allow-dataset-change", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Tiếp tục từ checkpoint và training report hiện có")
    parser.add_argument("--progress-interval", type=float, default=10.0, help="Số giây tối thiểu giữa hai lần ghi heartbeat")
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
