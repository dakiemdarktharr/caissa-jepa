"""Held-out action-ranking evaluation for CAISSA A-JEPA and policy/value baselines."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
import numpy as np
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


def evaluate(dataset: Path, model_path: Path, architecture: str, split: str, validation_percent: int, maximum_positions: int, model_variant: str = "full", split_plan=None, fixture_only=False) -> dict:
    if architecture == "lejepa" and model_variant == "full":
        model_variant = "sigreg"
    if architecture == "nnue" and model_variant == "full":
        model_variant = "nnue"
    from dataset_integrity import validate_dataset
    from research_dataset import verify_plan, verify_temporary_fixture, checkpoint_compatibility
    validate_dataset(dataset)
    fixture = verify_temporary_fixture(dataset, fixture_only)
    plan = verify_plan(dataset, split_plan) if split_plan else None
    if not plan and not fixture:
        raise ValueError("Evaluation requires a verified locked research split plan")
    if split == "test":
        raise ValueError("Locked final-test evaluation requires a preregistered confirmatory runner; exploratory CLI cannot open it")
    model = load_model(model_path, architecture, model_variant)
    fingerprint = plan["dataset_fingerprint"] if plan else dataset_manifest_fingerprint(dataset)
    if not fixture and not checkpoint_compatibility(model, fingerprint)["compatible"]:
        raise ValueError("Checkpoint dataset fingerprint incompatible/unverified")
    strata = defaultdict(list)
    predictions, observed, latent_states = [], [], []
    skip_reasons = Counter()
    started = time.perf_counter()
    total = top1 = top5 = 0
    nll = reciprocal_rank = value_mse = 0.0
    errors = []
    skipped = 0
    for game in iter_dataset_games(dataset):
        if (plan["assignments"][game["game_hash"]] if plan else stable_split(game["game_hash"], validation_percent)) != split:
            continue
        included = set(plan["included_position_indices"].get(game["game_hash"], [])) if plan else None
        for position_index, position in enumerate(game["positions"]):
            if included is not None and position_index not in included:
                continue
            try:
                state = snapshot_from_fen(position["fen"])
                expected = move_from_uci(position["action_uci"], state["turn"])
                engine = vitriengine(state, 0.02)
                legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
                if expected not in legal:
                    skipped += 1
                    skip_reasons["illegal_expected_action"] += 1
                    continue
                _, priors, _ = model.score_legal_moves(state, legal)
                ordered = sorted(range(len(legal)), key=lambda index: priors[index], reverse=True)
                expected_index = legal.index(expected)
                rank = ordered.index(expected_index)
                value = model.danh_gia_snapshot(state)
                outcome = float(position["outcome_pov"])
                squared_error = (value - outcome) ** 2
                if not math.isfinite(value) or len(priors) != len(legal) or not np.all(np.isfinite(priors)):
                    raise ValueError("Non-finite or incomplete model predictions")
                label = {1.: 0, 0.: 1, -1.: 2}[outcome]
                value = float(np.clip(value, -1, 1))
                latent = None
                if hasattr(model, "encode"):
                    from adversarial_jepa import encode_snapshot
                    latent = model.encode(encode_snapshot(state)[None, :])[0]
                    if not np.all(np.isfinite(latent)):
                        raise ValueError("Non-finite latent state")
                tactical = engine.is_king_in_check(engine.turn) or any(m[2] or state["board"][m[1]] != "." for m in legal)
                endgame = sum(p != "." for p in state["board"]) <= 7
                metrics = [int(rank == 0), int(rank < 5), 1/(rank+1), -math.log(max(1e-8, priors[expected_index])), squared_error]
                strata["tactical" if tactical else "non_tactical"].append(metrics)
                strata["endgame" if endgame else "non_endgame"].append(metrics)
                if latent is not None:
                    latent_states.append(latent)
                predictions.append([max(value, 0), 1 - abs(value), max(-value, 0)])
                observed.append(label)
                reciprocal_rank += 1 / (rank + 1)
                value_mse += squared_error
                total += 1
                top1 += int(rank == 0)
                top5 += int(rank < 5)
                nll -= math.log(max(1e-8, priors[expected_index]))
                if maximum_positions and total >= maximum_positions:
                    break
            except Exception as error:
                skipped += 1
                skip_reasons[type(error).__name__] += 1
                if len(errors) < 3:
                    errors.append(str(error))
        if maximum_positions and total >= maximum_positions:
            break
    elapsed = max(1e-9, time.perf_counter() - started)
    probabilities = np.asarray(predictions)
    calibration = []
    brier = ece = None
    if len(predictions):
        labels = np.eye(3)[observed]
        brier = float(np.mean(np.sum((probabilities - labels)**2, axis=1)))
        confidence = probabilities.max(axis=1)
        correct = probabilities.argmax(axis=1) == observed
        ece = 0.0
        for lower in np.arange(0, 1, .1):
            selected = (confidence >= lower) & (confidence < lower+.1 if lower < .9 else confidence <= 1)
            if selected.any():
                acc, conf = float(correct[selected].mean()), float(confidence[selected].mean())
                ece += float(selected.mean()) * abs(acc-conf)
                calibration.append({"lower": float(lower), "count": int(selected.sum()), "accuracy": acc, "confidence": conf})
    from research_diagnostics import latent_diagnostics
    result = {
        "research_name": "MARS-JEPA Chess", "experiment_family": "policy-value",
        "ranking_ready": False, "fixture_only": fixture,
        "wdl_probability_policy": "uncalibrated scalar surrogate [max(v,0),1-|v|,max(-v,0)]; no learned WDL head",
        "wdl_brier": brier, "wdl_ece": ece, "calibration_bins": calibration,
        "strata": {k: {"positions": len(v), **dict(zip(("top1", "top5", "mrr", "nll", "value_mse"), np.mean(v, axis=0).tolist()))} for k,v in strata.items()},
        "representation": latent_diagnostics(latent_states) if latent_states else None,
        "engine_strength": {"status": "NOT_MEASURED"}, "skip_reason_counts": dict(skip_reasons),
        "architecture": architecture,
        "model_variant": model_variant,
        "checkpoint": str(model_path),
        "checkpoint_sha256": file_sha256(model_path),
        "dataset_fingerprint": fingerprint,
        "validation_percent": validation_percent,
        "trained_steps": model.trained_steps,
        "status": "PARTIAL_WITH_ERRORS" if skipped else "COMPLETE" if total else "NO_VALID_SAMPLES",
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
    parser.add_argument("--split-plan", required=True)
    parser.add_argument("--validation-percent", type=int, default=10)
    parser.add_argument("--max-positions", type=int, default=1000)
    arguments = parser.parse_args()
    result = evaluate(
        Path(arguments.dataset), Path(arguments.model), arguments.architecture,
        arguments.split, arguments.validation_percent, arguments.max_positions,
        arguments.model_variant, split_plan=arguments.split_plan,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
