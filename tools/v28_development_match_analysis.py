"""Integrity-check and summarize the exploratory V2.8 development match.

This analyzer is deliberately separate from the locked V08 confirmatory
analyzer. It reports per-checkpoint-seed contrasts, simple cluster intervals,
and realized per-arm search compute. It never reads fit losses or labels these
development outcomes confirmatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from two_player.games import BoardGame
from two_player.v28_development import development_schedule
from tools.v28_model_match import _verify_game


PANEL_SEEDS = (17, 29, 43, 59, 71, 83, 97, 109, 127, 139,
               151, 167, 181, 197, 211, 227, 241, 257, 271, 283)
ARMS = ("reply-jepa", "task-value-dynamics", "direct-leaf")
COMPARISON_TO_ARM = {"task-value-dynamics": "task-value-dynamics",
                     "direct-exact-leaf-value": "direct-leaf"}
T_CRITICAL_DF19 = 2.093024054
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 28_094_082
# The match artifact was produced before this analyzer existed. Pin its source
# identity explicitly so later evaluator edits cannot silently rebind V01.
MATCHER_SOURCE_SHA256 = (
    "075d3257efc88deeb49ea08899615767aeca97931acc954de26b177f24886a40"
)
GAME_RULES_SOURCE_SHA256 = (
    "fbdce0893f6dcc76d30b71d4391842abbcd7c15a0d1a9e20c40077457e273d3a"
)
COMPUTE_FIELDS = ("decision_calls", "branch_value_calls", "latent_evaluations",
                  "transitions", "cpu_seconds", "wall_seconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mean_interval(values: list[float]) -> dict:
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(len(values))
    margin = T_CRITICAL_DF19 * se
    return {"mean": mean, "seed_cluster_sd": sd, "seed_cluster_se": se,
            "t95_ci": [mean - margin, mean + margin],
            "positive_seed_clusters": sum(value > 0 for value in values),
            "seed_clusters": len(values)}


def _bootstrap_ci(values: list[float], rng: random.Random) -> list[float]:
    n = len(values)
    samples = sorted(statistics.mean(rng.choice(values) for _ in range(n))
                     for _ in range(BOOTSTRAP_REPLICATES))
    return [samples[int(0.025 * BOOTSTRAP_REPLICATES)],
            samples[int(0.975 * BOOTSTRAP_REPLICATES) - 1]]


def _game_for_name(name: str) -> BoardGame:
    games = {
        "connect4-gravity-6x7": BoardGame(name, 6, 7, 4, True),
        "reversi6": BoardGame(name, 6, 6, reversi=True),
    }
    try:
        return games[name]
    except KeyError:
        raise ValueError("match artifact contains an unpinned game") from None


def _validate_game_record(game: BoardGame, record: dict) -> float:
    score = record.get("score_plus")
    if (type(score) not in (int, float) or not math.isfinite(score)
            or score not in (0, 0.5, 1)):
        raise ValueError("game score is outside the zero-sum terminal score domain")
    utility = record.get("terminal_utility_plus")
    if type(utility) is not int or utility not in (-1, 0, 1):
        raise ValueError("game record has an invalid terminal utility")
    if not _verify_game(game, record, max_move_seconds=2.0, max_nodes=500_000):
        raise ValueError("game transcript fails replay or terminal-score validation")
    return float(score)


def _validate_panel_bindings(panel_root: Path, ledger: dict,
                             match_receipt: dict) -> None:
    """Fail closed unless the exact 60 trained artifacts match both ledgers."""
    expected = {(seed, arm) for seed in PANEL_SEEDS for arm in ARMS}
    entries = ledger.get("runs")
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise ValueError("development panel run inventory is invalid")

    indexed = {}
    for row in entries:
        key = (row.get("seed"), row.get("variant"))
        if key not in expected or key in indexed or row.get("status") != "completed":
            raise ValueError("development panel has duplicate or unexpected runs")
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError("development panel omits a planned seed/arm")

    match_checkpoints = match_receipt.get("panel_checkpoint_sha256")
    match_receipts = match_receipt.get("panel_training_receipt_sha256")
    match_identities = match_receipt.get("panel_run_identity")
    expected_nested_keys = {str(seed) for seed in PANEL_SEEDS}
    if any(not isinstance(value, dict) or set(value) != expected_nested_keys
           for value in (match_checkpoints, match_receipts, match_identities)):
        raise ValueError("match receipt panel bindings have incomplete seed coverage")
    if any(set(value[str(seed)]) != set(ARMS)
           for value in (match_checkpoints, match_receipts, match_identities)
           for seed in PANEL_SEEDS):
        raise ValueError("match receipt panel bindings have unexpected arms")

    identity_fields = ("dataset_fingerprint", "dataset_sha256", "audit_sha256",
                       "run_config_sha256", "model_code_sha256",
                       "trainer_code_sha256", "optimizer_step", "completed_epochs")
    for seed, arm in sorted(expected):
        row = indexed[(seed, arm)]
        checkpoint = (panel_root / str(seed) / arm / "checkpoint.npz").resolve()
        training_receipt_path = Path(str(checkpoint) + ".receipt.json")
        if (Path(row.get("checkpoint", "")).resolve() != checkpoint
                or Path(row.get("receipt", "")).resolve() != training_receipt_path
                or not checkpoint.is_file() or not training_receipt_path.is_file()):
            raise ValueError("panel ledger paths do not bind to expected artifacts")
        checkpoint_sha = _sha256(checkpoint)
        training_receipt_sha = _sha256(training_receipt_path)
        if (row.get("checkpoint_sha256") != checkpoint_sha
                or row.get("receipt_sha256") != training_receipt_sha):
            raise ValueError("panel ledger artifact hash mismatch")

        training = json.loads(training_receipt_path.read_text(encoding="utf-8"))
        if (training.get("schema") != "caissa-jepa-v28-train-receipt-v1"
                or training.get("checkpoint_sha256") != checkpoint_sha
                or training.get("variant") != arm
                or training.get("fit_scope") != "development-only"
                or training.get("split") != "train"
                or training.get("development_approval_sha256") !=
                ledger.get("approval_sha256")
                or training.get("dataset_fingerprint") !=
                ledger.get("dataset_fingerprint")
                or training.get("dataset_sha256") != ledger.get("records_sha256")
                or training.get("audit_sha256") != ledger.get("audit_sha256")
                or training.get("optimizer_step") != row.get("optimizer_step")
                or training.get("completed_epochs") != row.get("completed_epochs")):
            raise ValueError("panel training receipt differs from its ledger identity")
        if training.get("effective_run", {}).get("fit_scope") != "development-only":
            raise ValueError("panel effective run is outside development scope")

        identity = {field: training[field] for field in identity_fields}
        try:
            bound_checkpoint = match_checkpoints[str(seed)][arm]
            bound_receipt = match_receipts[str(seed)][arm]
            bound_identity = match_identities[str(seed)][arm]
        except (KeyError, TypeError):
            raise ValueError("match receipt panel bindings omit a seed/arm") from None
        if (bound_checkpoint != checkpoint_sha
                or bound_receipt != training_receipt_sha
                or bound_identity != identity):
            raise ValueError("match receipt does not bind the audited panel artifacts")


def analyze(match_path: Path, panel_root: Path) -> dict:
    match_path = match_path.resolve()
    receipt_path = match_path.with_suffix(match_path.suffix + ".receipt.json")
    ledger_path = panel_root.resolve() / "panel.json"
    for required in (match_path, receipt_path, ledger_path):
        if not required.is_file():
            raise FileNotFoundError(required)

    lines = match_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("development match output is empty")
    header, *rows = (json.loads(line) for line in lines)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    schedule = development_schedule()
    expected_rows = [tuple(row[key] for key in
                           ("block_id", "game", "comparison", "checkpoint_seed",
                            "match_seed")) for row in schedule]
    observed_rows = [tuple(row.get(key) for key in
                           ("block_id", "game", "comparison", "checkpoint_seed",
                            "match_seed")) for row in rows]
    if (len(rows) != 160 or len(set(observed_rows)) != 160
            or observed_rows != expected_rows
            or header.get("block_count") != 160
            or header.get("schedule_sha256") != _canonical_sha(schedule)
            or header.get("outcomes_are_locked") is not False
            or header.get("max_move_seconds") != 2.0
            or header.get("max_nodes_per_move") != 500_000):
        raise ValueError("outcomes do not match the pinned exploratory schedule")
    if (receipt.get("schema") != "v28-learned-model-match-v01-receipt"
            or receipt.get("status") != "complete"
            or receipt.get("confirmatory") is not False
            or receipt.get("commitment_sha256") is not None
            or receipt.get("block_count") != 160
            or receipt.get("artifact_bytes") != match_path.stat().st_size
            or receipt.get("schedule_sha256") != header.get("schedule_sha256")
            or receipt.get("artifact_sha256") != _sha256(match_path)
            or receipt.get("max_move_seconds") != header.get("max_move_seconds")
            or receipt.get("max_nodes_per_move") != header.get("max_nodes_per_move")
            or receipt.get("model_match_source_sha256") != MATCHER_SOURCE_SHA256
            or _sha256(ROOT / "two_player" / "games.py") !=
            GAME_RULES_SOURCE_SHA256
            or receipt.get("model_forfeit_rows") != 0
            or receipt.get("external_censored_block_rows") != 0):
        raise ValueError("match receipt, bytes, or evaluator source identity is invalid")
    if (ledger.get("schema") !=
            "caissa-jepa-v28-development-fit-panel-result-v01"
            or ledger.get("status") != "completed"
            or ledger.get("expected_runs") != 60
            or len(ledger.get("runs", [])) != 60
            or ledger.get("locked_final_access") is not False):
        raise ValueError("development panel is incomplete or has locked-final access")
    _validate_panel_bindings(panel_root.resolve(), ledger, receipt)

    cells: dict[tuple[str, str, int], list[float]] = {}
    compute: dict[tuple[str, str, str], dict[str, list[float]]] = {}
    censored = forfeits = 0
    for row in rows:
        if row.get("status") != "complete":
            forfeits += row.get("status") == "model_forfeit"
            raise ValueError("development schedule contains a non-complete match block")
        if row.get("external_censored") is not False:
            censored += 1
            raise ValueError("development schedule contains a censored block")
        if (row.get("max_move_seconds") != 2.0
                or row.get("max_nodes_per_move") != 500_000):
            raise ValueError("a block used a different planner budget")
        plus = row["plus_assignment"]
        minus = row["minus_assignment"]
        control_arm = COMPARISON_TO_ARM.get(row["comparison"])
        if (plus.get("jepa_player") != 1 or minus.get("jepa_player") != -1
                or plus.get("control") != control_arm
                or minus.get("control") != control_arm):
            raise ValueError("paired color assignment or control identity is invalid")
        jepa_plus = plus["jepa"]
        jepa_minus = minus["jepa"]
        if (jepa_plus.get("status") != "complete"
                or jepa_minus.get("status") != "complete"):
            forfeits += 1
            raise ValueError("a model forfeited a paired match")
        game = _game_for_name(row["game"])
        raw_plus_score = _validate_game_record(game, jepa_plus)
        raw_minus_score = _validate_game_record(game, jepa_minus)
        score_plus = raw_plus_score
        score_minus = 1.0 - raw_minus_score
        delta = (score_plus + score_minus) / 2 - 0.5
        if (not math.isclose(delta, float(row["paired_score_d"]), abs_tol=1e-12)
                or not math.isclose(score_plus, float(row["score_plus"]), abs_tol=1e-12)
                or not math.isclose(score_minus, float(row["score_minus"]), abs_tol=1e-12)
                or not math.isclose(raw_plus_score, float(row["score_plus"]), abs_tol=1e-12)
                or not math.isclose(1.0 - raw_minus_score,
                                    float(row["score_minus"]), abs_tol=1e-12)):
            raise ValueError("paired score does not recompute from the seat-swapped games")
        cells.setdefault((row["game"], row["comparison"],
                          row["checkpoint_seed"]), []).append(delta)

        # Each stored game record has plus/minus compute totals. The JEPA arm
        # changes seat across the pair; attribute both arms to their own seat.
        for game_record, jepa_seat in ((jepa_plus, "plus"),
                                       (jepa_minus, "minus")):
            control_seat = "minus" if jepa_seat == "plus" else "plus"
            for arm, seat in (("reply-jepa", jepa_seat),
                              (control_arm, control_seat)):
                metrics = game_record["compute"][seat]
                target = compute.setdefault((row["game"], row["comparison"], arm),
                                            {key: [] for key in COMPUTE_FIELDS})
                for key in COMPUTE_FIELDS:
                    target[key].append(float(metrics[key]))

    if receipt.get("model_forfeit_rows") != forfeits or receipt.get(
            "external_censored_block_rows") != censored:
        raise ValueError("match receipt censor/forfeit counts do not agree with rows")
    games = sorted({row["game"] for row in rows})
    comparisons = sorted({row["comparison"] for row in rows})
    if games != ["connect4-gravity-6x7", "reversi6"] or comparisons != sorted(
            COMPARISON_TO_ARM):
        raise ValueError("game/control strata differ from the frozen V2.8 design")
    if any(len(cells[(game, comp, seed)]) != 2
           for game in games for comp in comparisons for seed in PANEL_SEEDS):
        raise ValueError("each game/control/checkpoint seed must contain two blocks")

    rng = random.Random(BOOTSTRAP_SEED)
    contrasts = []
    seed_effects: dict[tuple[str, int], float] = {}
    for game in games:
        for comp in comparisons:
            per_seed = {seed: statistics.mean(cells[(game, comp, seed)])
                        for seed in PANEL_SEEDS}
            seed_effects[(comp, game)] = per_seed
            result = _mean_interval(list(per_seed.values()))
            result.update({"game": game, "control": comp,
                           "blocks": len(rows) // 4,
                           "bootstrap_95ci": _bootstrap_ci(
                               list(per_seed.values()), rng)})
            contrasts.append(result)
    for comp in comparisons:
        per_seed = [statistics.mean(seed_effects[(comp, game)][seed]
                                    for game in games) for seed in PANEL_SEEDS]
        result = _mean_interval(per_seed)
        result.update({"game": "macro_average_across_two_games", "control": comp,
                       "blocks": len(rows) // 2,
                       "bootstrap_95ci": _bootstrap_ci(per_seed, rng)})
        contrasts.append(result)

    realized_compute = []
    for (game, comp, arm), values in sorted(compute.items()):
        realized_compute.append({
            "game": game, "control": comp, "arm": arm,
            "game_seat_observations": len(values["decision_calls"]),
            "totals": {key: sum(series) for key, series in values.items()},
            "means_per_game_seat": {
                key: statistics.mean(series) for key, series in values.items()},
        })

    return {
        "schema": "caissa-jepa-v28-development-match-analysis-v01",
        "status": "exploratory_only",
        "interpretation": (
            "Fixed checkpoint strength under a shared two-ply minimax planner; "
            "not opponent-behavior prediction, equilibrium, exploitability, "
            "cross-game transfer, or confirmatory evidence."),
        "panel": {"status": ledger["status"], "completed_runs": len(ledger["runs"]),
                  "checkpoint_seeds": list(PANEL_SEEDS),
                  "dataset_fingerprint": ledger["dataset_fingerprint"],
                  "commit": ledger["commit"]},
        "analysis_source_sha256": _sha256(Path(__file__)),
        "game_rules_source_sha256": GAME_RULES_SOURCE_SHA256,
        "matches": {"path": str(match_path), "sha256": _sha256(match_path),
                    "receipt_sha256": _sha256(receipt_path),
                    "schedule_sha256": header["schedule_sha256"],
                    "evaluator_source_sha256": receipt["model_match_source_sha256"],
                    "blocks": len(rows), "paired_games": len(rows) * 2,
                    "forfeits": forfeits, "censored_blocks": censored,
                    "max_move_seconds": 2.0,
                    "max_nodes_per_move": 500_000,
                    "wall_seconds": receipt["wall_seconds"],
                    "cpu_seconds": receipt["cpu_seconds"],
                    "outcomes_are_locked": False},
        "uncertainty": {
            "primary_unit": "checkpoint seed; paired match seeds averaged per cell",
            "sampling_scope": ("conditional on the two scheduled match seeds per "
                               "checkpoint-seed/game/control cell; does not separately "
                               "estimate match-seed or situation-sampling uncertainty"),
            "cluster_t_interval": "unadjusted two-sided 95% t interval, df=19",
            "cluster_bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "interval": "unadjusted percentile 95% interval",
                "multiplicity_adjusted": False},
            "interpretation": "exploratory; do not use for superiority claims"},
        "contrasts": contrasts,
        "realized_search_compute": realized_compute,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match_output", type=Path)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = analyze(args.match_output, args.panel_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "contrasts": result["contrasts"],
                      "output": str(args.output)}, sort_keys=True, indent=2,
                     allow_nan=False))


if __name__ == "__main__":
    main()
