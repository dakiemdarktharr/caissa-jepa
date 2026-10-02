"""Audit V2.11 development matches and apply the frozen nomination screen."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import v211_model_match
from two_player.v211_development import (RUN_CONFIG, SCHEDULE_COMPARISONS,
                                         SEEDS, development_schedule,
                                         validate_spec)

T95_DF19 = 2.093024054
GAMES = ("connect4-gravity-6x7", "reversi6")
CONTROL_TO_ARM = {"reply-jepa-lambda1-v29": "reply-jepa",
                  "task-value-dynamics-v29": "task-value-dynamics",
                  "direct-leaf-v29": "direct-leaf"}


def _sha(path: Path, *, normalize_text=False) -> str:
    raw = Path(path).read_bytes()
    if normalize_text:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  allow_nan=False).encode("utf-8")).hexdigest()


def _game(name):
    from two_player.games import BoardGame
    if name == "connect4-gravity-6x7":
        return BoardGame(name, 6, 7, 4, True)
    if name == "reversi6":
        return BoardGame(name, 6, 6, reversi=True)
    raise ValueError("unexpected game in V2.11 match artifact")


def _mean_interval(values):
    if len(values) != len(SEEDS) or any(not math.isfinite(x) for x in values):
        raise ValueError("interval requires one finite paired effect per seed")
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(len(values))
    radius = T95_DF19 * se
    return {"mean": mean, "seed_cluster_sd": sd, "seed_cluster_se": se,
            "t95_ci": [mean - radius, mean + radius],
            "positive_seed_clusters": sum(value > 0 for value in values),
            "seed_clusters": len(values),
            "interval_scope": "unadjusted two-sided t interval over checkpoint initialization seeds"}


def _validate_row(row, block):
    if (any(row.get(key) != block[key] for key in (
            "block_id", "game", "comparison", "checkpoint_seed", "match_seed"))
            or row.get("external_censored") is not False
            or row.get("status") not in ("complete", "model_forfeit")):
        raise ValueError("match row differs from committed block or censor policy")
    game = _game(block["game"])
    for key in ("plus_game", "minus_game"):
        if not v211_model_match.base_match._verify_game(
                game, row.get(key, {}), max_move_seconds=2.0, max_nodes=500_000):
            raise ValueError("game transcript does not pass independent rules replay")
    plus = row["plus_game"]["score_plus"]
    minus_as_candidate = 1.0 - row["minus_game"]["score_plus"]
    expected = (plus + minus_as_candidate) / 2.0
    if not math.isclose(row.get("candidate_score", float("nan")), expected,
                        rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("paired candidate score is not color-swap correct")
    return expected - 0.5


def _model_compute(row):
    """Return candidate/control CPU from their assigned player seats."""
    plus, minus = row["plus_game"], row["minus_game"]
    candidate_cpu = (plus["compute"]["plus"]["cpu_seconds"]
                     + minus["compute"]["minus"]["cpu_seconds"])
    control_cpu = (plus["compute"]["minus"]["cpu_seconds"]
                   + minus["compute"]["plus"]["cpu_seconds"])
    return candidate_cpu, control_cpu


def analyze(match_path, receipt_path, candidate_panel_root, approval_path):
    spec = validate_spec()
    match_path, receipt_path = Path(match_path).resolve(), Path(receipt_path).resolve()
    candidate_panel_root = Path(candidate_panel_root).resolve()
    ledger_path = candidate_panel_root / "panel.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    candidate_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    v211_model_match._verify_supervisor_attestation(candidate_ledger,
                                                    candidate_panel_root)
    schedule = development_schedule()
    lines = match_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("empty V2.11 match artifact")
    header = json.loads(lines[0])
    rows = [json.loads(line) for line in lines[1:]]
    observed = [tuple(row.get(key) for key in (
        "block_id", "game", "comparison", "checkpoint_seed", "match_seed"))
        for row in rows]
    expected = [tuple(block[key] for key in (
        "block_id", "game", "comparison", "checkpoint_seed", "match_seed"))
        for block in schedule]
    artifact_sha = _sha(match_path)
    if (len(rows) != 240 or observed != expected or len(set(observed)) != 240
            or header.get("schedule_sha256") != _canonical_sha(schedule)
            or header.get("block_count") != 240
            or header.get("confirmatory") is not False
            or header.get("locked_final_access") is not False
            or header.get("max_move_seconds") != 2.0
            or header.get("max_nodes_per_move") != 500_000
            or header.get("schema") != "caissa-jepa-v211-development-match-v01"
            or receipt.get("schema") !=
            "caissa-jepa-v211-development-match-v01-receipt"
            or receipt.get("status") != "complete"
            or receipt.get("confirmatory") is not False
            or receipt.get("block_count") != 240 or receipt.get("game_count") != 480
            or receipt.get("schedule_sha256") != header.get("schedule_sha256")
            or receipt.get("artifact_sha256") != artifact_sha
            or receipt.get("artifact_bytes") != match_path.stat().st_size
            or receipt.get("candidate_panel_sha256") != _sha(ledger_path)
            or receipt.get("baseline_panel_sha256") != _sha(
                v211_model_match.V29_LEDGER_PATH)
            or receipt.get("model_match_source_sha256") != _sha(
                ROOT / "tools" / "v211_model_match.py", normalize_text=True)
            or receipt.get("model_forfeit_blocks") != sum(
                row.get("status") == "model_forfeit" for row in rows)):
        raise ValueError("match rows, source, panel, or receipt are not committed V2.11")
    if candidate_ledger.get("approval_sha256") != _sha(Path(approval_path)):
        raise ValueError("candidate panel is not bound to the supplied data grant")

    effects = {game: {control: {seed: [] for seed in SEEDS}
                      for control in SCHEDULE_COMPARISONS} for game in GAMES}
    cpu = {game: {control: {"candidate": 0.0, "control": 0.0, "seat_count": 0}
                  for control in SCHEDULE_COMPARISONS} for game in GAMES}
    for block, row in zip(schedule, rows):
        difference = _validate_row(row, block)
        effects[block["game"]][block["comparison"]][
            block["checkpoint_seed"]].append(difference)
        candidate_cpu, control_cpu = _model_compute(row)
        stats = cpu[block["game"]][block["comparison"]]
        stats["candidate"] += candidate_cpu
        stats["control"] += control_cpu
        stats["seat_count"] += 2
    if any(len(effects[g][c][seed]) != 2 for g in GAMES
           for c in SCHEDULE_COMPARISONS for seed in SEEDS):
        raise ValueError("V2.11 match panel is incomplete")

    summaries, gate = {}, {}
    seed_macro = {control: [] for control in SCHEDULE_COMPARISONS}
    for control in SCHEDULE_COMPARISONS:
        summaries[control] = {}
        for game in GAMES:
            per_seed = {seed: statistics.mean(effects[game][control][seed])
                        for seed in SEEDS}
            summaries[control][game] = _mean_interval(list(per_seed.values()))
        for seed in SEEDS:
            seed_macro[control].append(statistics.mean(
                statistics.mean(effects[game][control][seed]) for game in GAMES))
        summaries[control]["equal_weight_macro"] = _mean_interval(seed_macro[control])

    panel_rows = {row["seed"]: row for row in candidate_ledger["runs"]}
    _, baseline, baseline_rows = v211_model_match._baseline_panels()
    candidate_fit = sum(float(panel_rows[seed]["fit_wall_seconds"]) for seed in SEEDS)
    task_fit = sum(float(baseline_rows[(seed, "task-value-dynamics")]["wall_seconds"])
                   for seed in SEEDS)
    fit_ratio = candidate_fit / task_fit
    all_margin_screens = True
    all_compute_screens = True
    for control in SCHEDULE_COMPARISONS:
        control_summary = summaries[control]
        game_margin = {game: control_summary[game]["mean"] >= 0.05 for game in GAMES}
        macro_margin = control_summary["equal_weight_macro"]["mean"] >= 0.05
        candidate_compute_pass = True
        compute_summary = {}
        for game in GAMES:
            cell = cpu[game][control]
            candidate_per_seat = cell["candidate"] / cell["seat_count"]
            control_per_seat = cell["control"] / cell["seat_count"]
            ratio = (candidate_per_seat / control_per_seat
                     if control_per_seat > 0 else float("inf"))
            passed = math.isfinite(ratio) and ratio <= 1.25
            candidate_compute_pass &= passed
            compute_summary[game] = {"candidate_cpu_per_game_seat": candidate_per_seat,
                                     "control_cpu_per_game_seat": control_per_seat,
                                     "candidate_to_control_ratio": ratio,
                                     "cap": 1.25, "passed": passed,
                                     "game_seats": cell["seat_count"]}
        summaries[control]["realized_compute"] = compute_summary
        summaries[control]["nomination_margin_screen"] = {
            "each_game": game_margin, "macro": macro_margin,
            "passed": all(game_margin.values()) and macro_margin}
        all_margin_screens &= summaries[control]["nomination_margin_screen"]["passed"]
        all_compute_screens &= candidate_compute_pass
        gate[control] = {"game_margin": game_margin, "macro_margin": macro_margin,
                         "compute": candidate_compute_pass}
    fit_pass = math.isfinite(fit_ratio) and fit_ratio <= 3.5
    forfeits = sum(row.get("status") == "model_forfeit" for row in rows)
    nomination = (all_margin_screens and all_compute_screens and fit_pass
                  and forfeits == 0)
    return {
        "schema": "caissa-jepa-v211-development-analysis-v01",
        "status": "complete exploratory development analysis",
        "protocol": "V211_JEPA_WEIGHT_CALIBRATION_V01",
        "confirmatory": False,
        "claim_limit": "No JEPA superiority, equilibrium, exploitability, transfer, novelty, or Q1-readiness claim follows from this development analysis.",
        "sample": {"paired_blocks": len(rows), "games": 2 * len(rows),
                   "checkpoint_seeds": len(SEEDS), "match_seeds": 40,
                   "forfeit_blocks": forfeits, "censored_blocks": 0},
        "fit_compute": {"candidate_fit_wall_seconds": candidate_fit,
                        "task_value_control_fit_wall_seconds": task_fit,
                        "candidate_to_task_value_ratio": fit_ratio,
                        "cap": 3.5, "passed": fit_pass},
        "comparisons": summaries,
        "nomination": {"nominated_for_separate_confirmatory_design": nomination,
                       "all_margin_screens": all_margin_screens,
                       "all_search_compute_screens": all_compute_screens,
                       "zero_forfeits": forfeits == 0,
                       "per_control": gate,
                       "interpretation": "nomination is exploratory only; no screen is a confirmatory superiority test"},
        "source_artifacts": {"match_sha256": artifact_sha,
                             "match_receipt_sha256": _sha(receipt_path),
                             "candidate_panel_sha256": _sha(ledger_path),
                             "baseline_panel_sha256": _sha(v211_model_match.V29_LEDGER_PATH),
                             "analysis_source_sha256": _sha(Path(__file__))}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("candidate_panel_root", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = analyze(args.match, args.receipt, args.candidate_panel_root, args.approval)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "nominated": result["nomination"][
                          "nominated_for_separate_confirmatory_design"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
