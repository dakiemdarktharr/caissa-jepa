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


def load_model(path: Path, architecture: str, model_variant: str = "full"):
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
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
    return DirectPolicyValueBaseline(path, create_if_missing=False)


def evaluate(dataset: Path, model_path: Path, architecture: str, split: str, validation_percent: int, maximum_positions: int, model_variant: str = "full") -> dict:
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
    model = load_model(model_path, architecture, model_variant)
    started = time.perf_counter()
    total = top1 = top5 = 0
    nll = 0.0
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
                total += 1
                top1 += int(rank == 0)
                top5 += int(rank < 5)
                nll -= math.log(max(1e-8, priors[expected_index]))
                if maximum_positions and total >= maximum_positions:
                    break
            except Exception:
                skipped += 1
        if maximum_positions and total >= maximum_positions:
            break
    elapsed = max(1e-9, time.perf_counter() - started)
    return {
        "architecture": architecture,
        "model_variant": model_variant,
        "checkpoint": str(model_path),
        "split": split,
        "positions": total,
        "skipped": skipped,
        "top1_accuracy": top1 / max(1, total),
        "top5_accuracy": top5 / max(1, total),
        "mean_nll": nll / max(1, total),
        "seconds": elapsed,
        "positions_per_second": total / elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--architecture", choices=("adversarial-jepa", "lejepa", "policy-value"), required=True)
    parser.add_argument(
        "--model-variant",
        choices=("h1", "h1-h2", "full", "no-response", "sigreg", "direct"),
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
