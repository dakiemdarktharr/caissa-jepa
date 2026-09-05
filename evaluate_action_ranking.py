"""Held-out action-ranking evaluation for CAISSA A-JEPA and policy/value baselines."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from adversarial_jepa import AdversarialJEPA, iter_dataset_games, move_from_uci, snapshot_from_fen, stable_split
from main import vitriengine
from policy_value_baseline import DirectPolicyValueBaseline
from lejepa import LeJEPA
from nnue_baseline import NNUEStyleBaseline
from arena_research import file_sha256
from adversarial_jepa import dataset_manifest_fingerprint
from train_caissa_v7 import atomic_json


def load_model(path: Path, architecture: str, model_variant: str = "full"):
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
    if architecture == "nnue" and model_variant == "full":
        model_variant = "nnue"
    if architecture == "adversarial-jepa":
        return AdversarialJEPA(
            path,
            create_if_missing=False,
            variant=model_variant,
        )
    if architecture == "lejepa":
        return LeJEPA(
            path,
            create_if_missing=False,
            variant=model_variant,
        )
    if architecture == "nnue":
        return NNUEStyleBaseline(
            path,
            create_if_missing=False,
            variant=model_variant,
        )
    if architecture == "policy-value":
        return DirectPolicyValueBaseline(path, create_if_missing=False)
    raise ValueError(f"Unknown architecture: {architecture}")


def evaluate(dataset: Path, model_path: Path, architecture: str, split: str, validation_percent: int, maximum_positions: int, model_variant: str = "full") -> dict:
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
    if architecture == "nnue" and model_variant == "full":
        model_variant = "nnue"
    model = load_model(model_path, architecture, model_variant)
    started = time.perf_counter()
    total = top1 = top5 = 0
    nll = reciprocal_rank = value_mse = 0.0
    errors = []
    skipped = 0
    for game in iter_dataset_games(dataset):
        if stable_split(game["game_hash"], validation_percent) != split:
            continue
        for position in game["positions"]:
            try:
                state = snapshot_from_fen(position["fen"])
                expected = move_from_uci(position["action_uci"], state["turn"])
                engine = vitriengine(state, 0.02)
                legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
                if expected not in legal:
                    skipped += 1
                    continue
                _, priors, _ = model.score_legal_moves(state, legal)
                ordered = sorted(range(len(legal)), key=lambda index: priors[index], reverse=True)
                expected_index = legal.index(expected)
                rank = ordered.index(expected_index)
                reciprocal_rank += 1 / (rank + 1)
                value_mse += (model.danh_gia_snapshot(state) - float(position["outcome_pov"])) ** 2
                total += 1
                top1 += int(rank == 0)
                top5 += int(rank < 5)
                nll -= math.log(max(1e-8, priors[expected_index]))
                if maximum_positions and total >= maximum_positions:
                    break
            except Exception as error:
                skipped += 1
                if len(errors) < 3:
                    errors.append(str(error))
        if maximum_positions and total >= maximum_positions:
            break
    elapsed = max(1e-9, time.perf_counter() - started)
    result = {
        "architecture": architecture,
        "model_variant": model_variant,
        "checkpoint": str(model_path),
        "checkpoint_sha256": file_sha256(model_path),
        "dataset_fingerprint": dataset_manifest_fingerprint(dataset),
        "validation_percent": validation_percent,
        "trained_steps": model.trained_steps,
        "status": "COMPLETE" if total else "NO_VALID_SAMPLES",
        "errors_sample": errors,
        "split": split,
        "positions": total,
        "skipped": skipped,
        "top1_accuracy": top1 / total if total else None,
        "top5_accuracy": top5 / total if total else None,
        "mean_nll": nll / total if total else None,
        "mean_reciprocal_rank": reciprocal_rank / total if total else None,
        "value_mse": value_mse / total if total else None,
        "seconds": elapsed,
        "positions_per_second": total / elapsed,
    }
    atomic_json(model_path.with_suffix(".evaluation.json"), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--architecture", choices=("adversarial-jepa", "lejepa", "policy-value", "nnue"), required=True)
    parser.add_argument(
        "--model-variant",
        choices=("h1", "h1-h2", "full", "no-response", "sigreg", "direct", "nnue"),
        default="full",
    )
    parser.add_argument("--split", choices=("train", "validation"), default="validation")
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-positions", type=int, default=1000)
    arguments = parser.parse_args()
    result = evaluate(
        Path(arguments.dataset), Path(arguments.model), arguments.architecture,
        arguments.split, arguments.validation_percent, arguments.max_positions,
        arguments.model_variant,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
