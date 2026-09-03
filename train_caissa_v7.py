"""Reproducible trainer for the FEN-based CAISSA A-JEPA v7 dataset."""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

from adversarial_jepa import (
    AdversarialJEPA,
    dataset_manifest_fingerprint,
    iter_dataset_games,
    sample_from_dataset_position,
    stable_split,
)
from policy_value_baseline import DirectPolicyValueBaseline


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


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def train(arguments: argparse.Namespace) -> int:
    # Preserve the programmatic API used by early v7 scripts, which did not
    # yet have an explicit architecture argument.
    architecture = getattr(arguments, "architecture", "adversarial-jepa")
    dataset_dir = Path(arguments.dataset)
    model_path = Path(arguments.model)
    fingerprint = dataset_manifest_fingerprint(dataset_dir)
    if architecture == "adversarial-jepa":
        model = AdversarialJEPA(model_path, latent_size=arguments.latent_size)
    else:
        model = DirectPolicyValueBaseline(
            model_path,
            latent_size=arguments.latent_size,
        )
    if model.dataset_fingerprint and model.dataset_fingerprint != fingerprint and not arguments.allow_dataset_change:
        raise RuntimeError(
            "Dataset fingerprint khác checkpoint. Dùng checkpoint mới hoặc "
            "--allow-dataset-change sau khi đã ghi nhận lý do thí nghiệm."
        )
    model.dataset_fingerprint = fingerprint
    report_path = model_path.with_suffix(".training.json")
    report = {
        "model": str(model_path),
        "dataset": str(dataset_dir),
        "dataset_fingerprint": fingerprint,
        "seed": arguments.seed,
        "architecture": architecture,
        "batch_size": arguments.batch_size,
        "learning_rate": arguments.learning_rate,
        "validation_percent": arguments.validation_percent,
        "epochs": [],
    }
    for epoch in range(1, arguments.epochs + 1):
        train_values = []
        for index, batch in enumerate(batches(dataset_dir, "train", arguments.batch_size, arguments.seed + epoch, arguments.validation_percent), 1):
            train_values.append(model.train_batch(batch, arguments.learning_rate))
            if arguments.max_train_batches and index >= arguments.max_train_batches:
                break
        validation_values = []
        for index, batch in enumerate(batches(dataset_dir, "validation", arguments.batch_size, arguments.seed, arguments.validation_percent), 1):
            validation_values.append(model.evaluate_batch(batch))
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
        atomic_json(report_path, report)
        print(json.dumps(epoch_report, ensure_ascii=False, sort_keys=True))
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
        choices=("adversarial-jepa", "policy-value"),
        default="adversarial-jepa",
    )
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-train-batches", type=int, default=0)
    parser.add_argument("--max-validation-batches", type=int, default=0)
    parser.add_argument("--allow-dataset-change", action="store_true")
    return parser


def main() -> int:
    if hasattr(__import__("sys").stdout, "reconfigure"):
        __import__("sys").stdout.reconfigure(encoding="utf-8", errors="replace")
    arguments = build_parser().parse_args()
    if arguments.epochs <= 0 or arguments.batch_size <= 0:
        raise ValueError("epochs và batch-size phải lớn hơn 0")
    if not 0 < arguments.validation_percent < 100:
        raise ValueError("validation-percent phải nằm trong khoảng 1..99")
    return train(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
