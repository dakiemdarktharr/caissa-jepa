"""Locked V2.8 match-score analysis, conditional on a fixed checkpoint panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.v28_match_power import (
    CHECKPOINT_SEEDS, COMPARISONS, FIRST_MATCH_SEED, GAMES,
    MATCHES_PER_CHECKPOINT, MARGIN, make_schedule,
)

BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 28094081


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _score(value):
    return type(value) in (int, float) and math.isfinite(value) and value in (0, 0.5, 1)


def expected_blocks():
    return make_schedule()


def validate_outcomes(schedule_rows, outcomes):
    """Require every frozen block, with all-arm external failures censored."""
    expected = {row["block_id"]: row for row in schedule_rows}
    actual = {}
    for row in outcomes:
        if not isinstance(row, dict) or row.get("block_id") not in expected:
            raise ValueError("unknown or malformed outcome block")
        block_id = row["block_id"]
        if block_id in actual:
            raise ValueError("duplicate outcome block")
        if any(row.get(key) != expected[block_id][key]
               for key in ("game", "comparison", "checkpoint_seed", "match_seed")):
            raise ValueError("outcome block identity differs from locked schedule")
        external = row.get("external_censored")
        if type(external) is not bool:
            raise ValueError("external_censored must be a boolean")
        if external:
            if "score_plus" in row or "score_minus" in row:
                raise ValueError("externally censored blocks cannot contain scores")
        else:
            if not _score(row.get("score_plus")) or not _score(row.get("score_minus")):
                raise ValueError("complete block must contain two legal scores in {0, .5, 1}")
            if row.get("status") not in ("complete", "model_forfeit"):
                raise ValueError("model failures must be retained as complete outcomes/forfeits")
        actual[block_id] = row
    if set(actual) != set(expected):
        raise ValueError("locked schedule has missing outcome blocks; do not replace or drop them")
    grouped = defaultdict(list)
    for row in outcomes:
        grouped[(row["checkpoint_seed"], row["match_seed"])].append(row)
    for group in grouped.values():
        if len(group) != len(GAMES) * len(COMPARISONS):
            raise ValueError("paired seed block is incomplete across games or controls")
        flags = {row["external_censored"] for row in group}
        if len(flags) != 1:
            raise ValueError("external failure must censor all arms and games in a paired block")
    return actual


def _mean(values):
    return sum(values) / len(values) if values else math.nan


def _sample_variance(values):
    if len(values) < 2:
        return math.nan
    center = _mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def _holm(pvalues):
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted = {}
    running = 0.0
    total = len(ordered)
    for index, (name, pvalue) in enumerate(ordered):
        running = max(running, min(1.0, (total - index) * pvalue))
        adjusted[name] = running
    return adjusted


def analyze(schedule_rows, outcomes, *, bootstrap_replicates=BOOTSTRAP_REPLICATES,
            bootstrap_seed=BOOTSTRAP_SEED):
    if bootstrap_replicates < 1000:
        raise ValueError("hierarchical sensitivity requires at least 1000 replicates")
    games = tuple(sorted({row["game"] for row in schedule_rows}))
    comparisons = tuple(sorted({row["comparison"] for row in schedule_rows}))
    checkpoint_seeds = tuple(sorted({row["checkpoint_seed"] for row in schedule_rows}))
    if len(games) != 2 or len(comparisons) != 2 or len(checkpoint_seeds) < 2:
        raise ValueError("analysis requires two games, two controls, and multiple checkpoints")
    indexed = validate_outcomes(schedule_rows, outcomes)
    schedule_by_id = {row["block_id"]: row for row in schedule_rows}
    strata = defaultdict(lambda: defaultdict(list))
    game_color = defaultdict(lambda: defaultdict(list))
    forfeits = defaultdict(int)
    censored = 0
    for row in indexed.values():
        if row["external_censored"]:
            censored += 1
            continue
        block = schedule_by_id[row["block_id"]]
        game, comparison, checkpoint, match = (
            block["game"], block["comparison"], block["checkpoint_seed"], block["match_seed"])
        plus, minus = row["score_plus"], row["score_minus"]
        difference = (plus + minus) / 2 - 0.5
        strata[(comparison, game)][checkpoint].append((match, difference))
        game_color[(comparison, game)]["plus"].append(plus - 0.5)
        game_color[(comparison, game)]["minus"].append(minus - 0.5)
        if row["status"] == "model_forfeit":
            forfeits[(comparison, game)] += 1

    checkpoint_means = {}
    checkpoint_variances = {}
    game_estimates = {}
    color_estimates = {}
    for comparison in COMPARISONS:
        for game in GAMES:
            means, variances = [], []
            for checkpoint in CHECKPOINT_SEEDS:
                records = sorted(strata[(comparison, game)].get(checkpoint, []))
                values = [value for _, value in records]
                if len(values) < 2:
                    raise ValueError("too few uncensored match seeds in a checkpoint stratum")
                means.append(_mean(values))
                variances.append(_sample_variance(values) / len(values))
            checkpoint_means[(comparison, game)] = means
            checkpoint_variances[(comparison, game)] = variances
            game_estimates[(comparison, game)] = _mean(means)
            color_estimates[(comparison, game, "plus")] = _mean(game_color[(comparison, game)]["plus"])
            color_estimates[(comparison, game, "minus")] = _mean(game_color[(comparison, game)]["minus"])

    effects, standard_errors, z_scores, raw_p = {}, {}, {}, {}
    for comparison in COMPARISONS:
        # Common match-seed offsets across games are retained within each paired block.
        per_checkpoint = []
        for checkpoint in CHECKPOINT_SEEDS:
            by_match = {}
            for game in GAMES:
                records = strata[(comparison, game)].get(checkpoint, [])
                by_match[game] = {match: value for match, value in records}
            shared = sorted(set(by_match[GAMES[0]]) & set(by_match[GAMES[1]]))
            if len(shared) < 2 or any(set(by_match[game]) != set(shared) for game in GAMES):
                raise ValueError("external censoring must preserve balanced paired game schedules")
            per_checkpoint.append([
                sum(by_match[game][match] for game in GAMES) / len(GAMES)
                for match in shared
            ])
        checkpoint_means_for_pair = [_mean(values) for values in per_checkpoint]
        effect = _mean(checkpoint_means_for_pair)
        variance = sum(_sample_variance(values) / len(values)
                       for values in per_checkpoint) / (len(CHECKPOINT_SEEDS) ** 2)
        se = math.sqrt(variance)
        if not math.isfinite(se) or se <= 0:
            raise ValueError("invalid standard error")
        z = (effect - MARGIN) / se
        pvalue = 1 - NormalDist().cdf(z)
        effects[comparison] = effect
        standard_errors[comparison] = se
        z_scores[comparison] = z
        raw_p[comparison] = pvalue

    adjusted_p = _holm(raw_p)
    z_bonferroni = NormalDist().inv_cdf(1 - 0.05 / len(COMPARISONS))
    lower_bounds = {name: effects[name] - z_bonferroni * standard_errors[name]
                    for name in COMPARISONS}

    seed_aggregates = {}
    for comparison in COMPARISONS:
        seed_aggregates[comparison] = {}
        for checkpoint in CHECKPOINT_SEEDS:
            by_game = []
            for game in GAMES:
                records = strata[(comparison, game)].get(checkpoint, [])
                by_game.append(_mean([value for _, value in records]))
            seed_aggregates[comparison][checkpoint] = _mean(by_game)

    guardrails = {
        "game_means_at_least_minus_0_02": all(
            game_estimates[(comparison, game)] >= -0.02
            for comparison in COMPARISONS for game in GAMES),
        "color_means_at_least_minus_0_02": all(
            color_estimates[(comparison, game, color)] >= -0.02
            for comparison in COMPARISONS for game in GAMES for color in ("plus", "minus")),
        "at_most_five_checkpoint_aggregates_below_minus_0_10": all(
            sum(1 for value in per_control.values() if value < -0.10) <= 5
            for per_control in seed_aggregates.values()),
        "no_checkpoint_aggregate_below_minus_0_25": all(
            value >= -0.25 for per_control in seed_aggregates.values()
            for value in per_control.values()),
    }
    superiority = all(adjusted_p[name] <= 0.05 for name in COMPARISONS)
    return {
        "schema": "caissa-jepa-v28-match-analysis-v1",
        "status": "analyzed; confirmatory claim requires locked protocol and independent review",
        "inference_scope": "conditional on the fixed 20-checkpoint panel",
        "primary_margin": MARGIN,
        "primary_effects": {
            name: {"mean_d": effects[name], "standard_error": standard_errors[name],
                   "z_vs_margin": z_scores[name], "p_one_sided_vs_margin": raw_p[name],
                   "p_holm": adjusted_p[name], "one_sided_bonferroni_lower": lower_bounds[name],
                   "game_mean_d": {game: game_estimates[(name, game)] for game in GAMES}}
            for name in COMPARISONS
        },
        "color_means": {
            f"{name}/{game}/{color}": color_estimates[(name, game, color)]
            for name in COMPARISONS for game in GAMES for color in ("plus", "minus")
        },
        "checkpoint_guardrails": seed_aggregates,
        "guardrails": guardrails,
        "superiority_pass": superiority and all(guardrails.values()),
        "external_censored_block_rows": censored,
        "model_forfeit_rows": {f"{name}/{game}": forfeits[(name, game)]
                                for name in COMPARISONS for game in GAMES},
        "bootstrap_sensitivity": _hierarchical_bootstrap(
            strata, bootstrap_replicates, bootstrap_seed),
    }


def _hierarchical_bootstrap(strata, replicates, seed):
    """Resample fixed-panel checkpoint seeds and paired match blocks as sensitivity."""
    import random
    rng = random.Random(seed)
    output = {name: [] for name in COMPARISONS}
    for _ in range(replicates):
        sampled_checkpoints = [rng.choice(CHECKPOINT_SEEDS) for _ in CHECKPOINT_SEEDS]
        sampled_rows = []
        for checkpoint in sampled_checkpoints:
            records = strata[(COMPARISONS[0], GAMES[0])].get(checkpoint, [])
            match_ids = [match for match, _ in records]
            if not match_ids:
                raise ValueError("hierarchical bootstrap has an empty checkpoint stratum")
            sampled_matches = [rng.choice(match_ids) for _ in match_ids]
            sampled_rows.append((checkpoint, sampled_matches))
        for comparison in COMPARISONS:
            game_values = []
            for game in GAMES:
                sampled_means = []
                for checkpoint, sampled_matches in sampled_rows:
                    records = dict(strata[(comparison, game)].get(checkpoint, []))
                    sampled = [records[match] for match in sampled_matches]
                    sampled_means.append(_mean(sampled))
                game_values.append(_mean(sampled_means))
            output[comparison].append(_mean(game_values))
    return {name: {"seed": seed, "replicates": replicates,
                   "percentile_95": [sorted(values)[int(.025 * (replicates - 1))],
                                     sorted(values)[int(.975 * (replicates - 1))]],
                   "interpretation": "sensitivity only; does not replace conditional primary inference"}
            for name, values in output.items()}


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("outcomes", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    schedule_data = json.loads(args.schedule.read_text(encoding="utf-8"))
    schedule_rows = schedule_data.get("blocks", [])
    if not schedule_rows or schedule_rows != make_schedule():
        parser.error("schedule does not match the frozen generator/commitment")
    canonical = json.dumps(schedule_rows, sort_keys=True, separators=(",", ":"),
                           allow_nan=False).encode("utf-8")
    if schedule_data.get("manifest", {}).get("blocks_sha256") != sha256_bytes(canonical):
        parser.error("schedule commitment hash mismatch")
    outcome_bytes = args.outcomes.read_bytes()
    outcomes = read_jsonl(args.outcomes)
    result = analyze(schedule_rows, outcomes)
    result["schedule_blocks_sha256"] = schedule_data["manifest"]["blocks_sha256"]
    result["analysis_code_sha256"] = sha256_bytes(Path(__file__).read_bytes())
    result["outcomes_sha256"] = sha256_bytes(outcome_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"status": result["status"], "superiority_pass": result["superiority_pass"],
                      "primary_effects": result["primary_effects"],
                      "guardrails": result["guardrails"]}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
