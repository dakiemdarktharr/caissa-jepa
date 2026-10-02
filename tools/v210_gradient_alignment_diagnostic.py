"""Run the frozen V2.10 no-update train-only gradient diagnostic."""
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

import numpy as np

from two_player.v28_data import V28_GAMES, digest
from two_player.v28_model import Config, _model_code_sha256
from two_player.v29_development import (DATASET_ROOT, load_development_split)
from two_player.v210_gradient_diagnostic import (decompose_reply_jepa_gradients,
                                                  load_weights_only,
                                                  encoder_alignment)


SEEDS = (17, 29, 43, 59, 71, 83, 97, 109, 127, 139,
         151, 167, 181, 197, 211, 227, 241, 257, 271, 283)
ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 30
BATCHES_PER_GAME_SEED = 10
T95_DF19 = 2.093024054408263
EXPECTED_PANEL_SHA256 = "b26504104ebde23967d142f01b3842b9e8309a2eb80337736e43c95f6c8f4d72"
PANEL_RESULT = ROOT / "chess_data" / "v29_fit_panel_dev01" / "panel.json"
APPROVAL = ROOT / "chess_data" / "v29_data_dev09_approval.json"
DATASET = DATASET_ROOT
SPEC = ROOT / "docs" / "METHOD_V210_GRADIENT_DIAGNOSTIC.md"
FIT_SPEC = ROOT / "docs" / "validation" / "V29_DEV_FIT_PANEL_V01.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def canonical_hash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise FileExistsError(f"refusing to overwrite diagnostic result: {path}")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _checkpoint_items(panel):
    if panel.get("status") != "completed":
        raise ValueError("V2.9 panel is not fully complete")
    found = {}
    for item in panel.get("runs", []):
        if item.get("variant") == "reply-jepa":
            if item.get("status") != "completed":
                raise ValueError("reply-JEPA panel arm has an incomplete fit")
            key = int(item["seed"])
            if key in found:
                raise ValueError("duplicate reply-JEPA seed in fit ledger")
            found[key] = item
    if tuple(sorted(found)) != tuple(sorted(SEEDS)):
        raise ValueError("reply-JEPA seed inventory differs from frozen protocol")
    return found


def _load_checkpoint(seed, item, panel, fit_spec):
    checkpoint = Path(item["checkpoint"]).resolve()
    receipt_path = Path(item["receipt"]).resolve()
    data_root = (ROOT / "chess_data").resolve()
    if data_root not in checkpoint.parents or data_root not in receipt_path.parents:
        raise ValueError("checkpoint or receipt escapes ignored chess_data")
    if sha256(checkpoint) != item.get("checkpoint_sha256"):
        raise ValueError("reply-JEPA checkpoint hash differs from fit ledger")
    if sha256(receipt_path) != item.get("receipt_sha256"):
        raise ValueError("reply-JEPA receipt hash differs from fit ledger")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("checkpoint_sha256") != item.get("checkpoint_sha256")
            or receipt.get("fit_scope") != "development-only"
            or receipt.get("split") != "train"
            or receipt.get("variant") != "reply-jepa"
            or receipt.get("completed_epochs") != 3
            or receipt.get("optimizer_step") != 87
            or receipt.get("dataset_fingerprint") != panel.get("dataset_fingerprint")
            or receipt.get("method") != "v28-supervised-reply-set-model-v02-prototype"
            or receipt.get("model_code_sha256") != _model_code_sha256()
            or receipt.get("trainer_code_sha256") != source_hash(
                ROOT / "two_player" / "v28_train.py")
            or panel.get("data_audit_code_sha256") != source_hash(
                ROOT / "two_player" / "v28_data.py")):
        raise ValueError("checkpoint receipt identity is invalid")
    config_values = fit_spec["matched_model_config"]
    config = Config(variant="reply-jepa", seed=seed, **config_values)
    if receipt.get("effective_run", {}).get("model") != {
            **config_values, "variant": "reply-jepa", "seed": seed}:
        raise ValueError("checkpoint config differs from frozen fit panel")
    if (receipt.get("dataset_sha256") != panel.get("records_sha256")
            or receipt.get("audit_sha256") != panel.get("audit_sha256")):
        raise ValueError("checkpoint data identity differs from the frozen fit panel")
    # Artifact and receipt hashes bind the parameters. Load only p_/t_ arrays;
    # do not deserialize checkpoint metadata or its embedded training history.
    model = load_weights_only(checkpoint, config, item["checkpoint_sha256"])
    return model, sha256(receipt_path)


def _select_roots(records, game_name):
    candidates = [row for row in records if row.get("game") == game_name]
    keyed = []
    for row in candidates:
        record_id = digest(row)
        keyed.append((hashlib.sha256(("caissa-v210-roots-v01:" + record_id)
                                     .encode("ascii")).hexdigest(),
                      record_id, row))
    keyed.sort(key=lambda item: item[0])
    required = BATCH_SIZE * BATCHES_PER_GAME_SEED
    if len(keyed) < required:
        raise ValueError(f"{game_name} has {len(keyed)} train roots; {required} required")
    chosen = keyed[:required]
    return [row for _, _, row in chosen], canonical_hash(
        [record_id for _, record_id, _ in chosen])


def _ci95(values):
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(SEEDS),) or not np.all(np.isfinite(array)):
        raise ValueError("cluster summary requires one finite value per seed")
    mean = float(array.mean())
    sem = float(array.std(ddof=1) / math.sqrt(len(array)))
    radius = T95_DF19 * sem
    return {"mean": mean, "lower": mean - radius, "upper": mean + radius,
            "seed_clusters": len(array), "method": "unadjusted two-sided t interval, df=19"}


def _all_screens_passed(summaries):
    return all(all(game["screen"].values()) for game in summaries.values())


def run(output: Path):
    output = output.resolve()
    data_root = (ROOT / "chess_data").resolve()
    if data_root not in output.parents:
        raise ValueError("diagnostic output must be under ignored chess_data")
    if output.exists():
        raise FileExistsError("refusing to overwrite a prior diagnostic directory")
    if source_hash(PANEL_RESULT) != EXPECTED_PANEL_SHA256:
        raise ValueError("V2.9 fit-panel ledger hash differs from the frozen input")
    panel = json.loads(PANEL_RESULT.read_text(encoding="utf-8"))
    if source_hash(FIT_SPEC) != panel.get("panel_spec_sha256"):
        raise ValueError("V2.9 fit specification differs from the panel-bound hash")
    fit_spec = json.loads(FIT_SPEC.read_text(encoding="utf-8"))
    checkpoint_items = _checkpoint_items(panel)
    if not APPROVAL.is_file():
        raise FileNotFoundError("the existing development-only data approval is absent")
    records, dataset_fingerprint, approval_sha = load_development_split(
        DATASET, "train", APPROVAL)
    if dataset_fingerprint != panel.get("dataset_fingerprint"):
        raise ValueError("audited train split differs from V2.9 fit panel")

    selected = {name: _select_roots(records, name) for name in V28_GAMES}
    # Validate and weights-only load every frozen checkpoint before computing
    # the first gradient, so a late bad receipt cannot leave a partial metric.
    models = {}
    checkpoint_hashes = {}
    receipt_hashes = {}
    for seed in SEEDS:
        model, receipt_sha = _load_checkpoint(seed, checkpoint_items[seed],
                                              panel, fit_spec)
        models[seed] = model
        checkpoint_hashes[str(seed)] = checkpoint_items[seed]["checkpoint_sha256"]
        receipt_hashes[str(seed)] = receipt_sha
    per_game_seed = {name: [] for name in V28_GAMES}
    batch_rows = []
    started = time.perf_counter()
    for seed in SEEDS:
        model = models[seed]
        for game_name in V28_GAMES:
            roots, _ = selected[game_name]
            seed_rows = []
            for batch_index in range(BATCHES_PER_GAME_SEED):
                batch_records = roots[batch_index * BATCH_SIZE:(batch_index + 1) * BATCH_SIZE]
                from two_player.v28_model import build_batch
                batch = build_batch(batch_records)
                before_step = model.step
                before_target = {key: value.copy() for key, value in model.target.items()}
                metrics, components = decompose_reply_jepa_gradients(model, batch)
                if (metrics["gradient_sum_relative_error"] > 1e-7
                        or model.step != before_step
                        or any(not np.array_equal(model.target[key], value)
                               for key, value in before_target.items())):
                    raise ValueError("gradient diagnostic altered state or failed decomposition")
                alignment = encoder_alignment(components)
                row = {"seed": seed, "game": game_name,
                       "batch": batch_index,
                       "cosine": alignment["cosine"],
                       "dot": alignment["dot"],
                       "task_norm": alignment["task_norm"],
                       "jepa_norm": alignment["jepa_norm"],
                       "task_zero": alignment["task_zero"],
                       "jepa_zero": alignment["jepa_zero"],
                       "gradient_sum_relative_error": metrics[
                           "gradient_sum_relative_error"],
                       "roots": metrics["roots"],
                       "branches": metrics["branches"],
                       "nonterminal_branches": metrics["nonterminal_branches"],
                       "terminal_branches": (metrics["branches"]
                                              - metrics["nonterminal_branches"]),
                       "invalid_or_skipped_roots": 0}
                batch_rows.append(row)
                seed_rows.append(row)
            cosines = [row["cosine"] for row in seed_rows if row["cosine"] is not None]
            if len(cosines) != BATCHES_PER_GAME_SEED:
                raise ValueError("zero-norm gradient encountered; frozen gate cannot be evaluated")
            per_game_seed[game_name].append({
                "seed": seed,
                "median_cosine": float(np.median(cosines)),
                "mean_cosine": float(np.mean(cosines)),
                "conflict_batches": sum(value < 0 for value in cosines),
                "batch_count": len(cosines),
            })
    summaries = {}
    for game_name, rows in per_game_seed.items():
        seed_medians = [row["median_cosine"] for row in rows]
        ci = _ci95(seed_medians)
        overall_median = float(np.median(seed_medians))
        persistent = sum(row["conflict_batches"] >= 6 for row in rows)
        summaries[game_name] = {
            "median_of_seed_medians": overall_median,
            "seed_cluster_mean_ci95": ci,
            "seeds_with_conflict_in_at_least_6_of_10_batches": persistent,
            "per_seed": rows,
            "screen": {
                "median_below_minus_0_05": overall_median < -0.05,
                "ci95_upper_below_zero": ci["upper"] < 0,
                "at_least_15_of_20_seed_conflict_fractions_over_half": persistent >= 15,
            },
        }
    all_pass = _all_screens_passed(summaries)
    result = {
        "schema": "caissa-jepa-v210-gradient-alignment-diagnostic-v01",
        "status": "diagnostic_complete",
        "interpretation": "No-update mechanism diagnostic only; not a strength or superiority result.",
        "next_step": "eligible_for_separate_intervention_preregistration" if all_pass
                     else "stop_gradient_conflict_candidate",
        "screen_passed": all_pass,
        "scope": {"fit_or_optimizer_updates": False,
                  "data_split_read": "train",
                  "locked_final_read": False,
                  "historical_train_metrics_or_loss_curves_read": False,
                  "checkpoints": "V2.9 reply-JEPA only; hash-validated, no performance selection",
                  "gradient_scope": "online encoder ew/eb; no predictor-only parameters"},
        "protocol": {"seed_list": list(SEEDS), "batch_size": BATCH_SIZE,
                     "batches_per_game_seed": BATCHES_PER_GAME_SEED,
                     "t95_df19": T95_DF19,
                     "roots_per_game": BATCH_SIZE * BATCHES_PER_GAME_SEED,
                     "root_observations": len(SEEDS) * len(V28_GAMES)
                     * BATCH_SIZE * BATCHES_PER_GAME_SEED,
                     "invalid_or_skipped_roots": 0,
                      "model_config": fit_spec["matched_model_config"],
                     "source_sha256": {
                         "method_spec": source_hash(SPEC),
                         "fit_panel_spec": source_hash(FIT_SPEC),
                         "diagnostic_module": source_hash(
                             ROOT / "two_player" / "v210_gradient_diagnostic.py"),
                         "runner": source_hash(Path(__file__)),
                         "model": source_hash(ROOT / "two_player" / "v28_model.py"),
                         "data_loader": source_hash(ROOT / "two_player" / "v28_data.py"),
                         "game_rules": source_hash(ROOT / "two_player" / "games.py"),
                         "trainer": source_hash(ROOT / "two_player" / "v28_train.py"),
                         "development_grant_loader": source_hash(
                             ROOT / "two_player" / "v29_development.py")}},
        "inputs": {"panel_sha256": sha256(PANEL_RESULT),
                   "dataset_fingerprint": dataset_fingerprint,
                   "approval_sha256": approval_sha,
                   "selected_train_record_ids_sha256": {
                       game: selected[game][1] for game in V28_GAMES},
                   "checkpoint_sha256_by_seed": checkpoint_hashes,
                   "receipt_sha256_by_seed": receipt_hashes,
                   "commit": subprocess.check_output(
                       ["git", "rev-parse", "HEAD"], cwd=ROOT,
                       text=True).strip()},
        "results": summaries,
        "batch_diagnostics": batch_rows,
        "wall_seconds": time.perf_counter() - started,
    }
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / "gradient_alignment.json", result)
    return {"status": result["status"], "screen_passed": all_pass,
            "next_step": result["next_step"],
            "output": str(output / "gradient_alignment.json"),
            "wall_seconds": result["wall_seconds"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
