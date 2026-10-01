"""Deterministic match-block commitments and conservative prefit power scenarios.

This module contains no model code and reads no outcomes. Its schedule is a
commitment aid only; it does not certify that the evaluator is implemented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from statistics import NormalDist
from pathlib import Path


GAMES = ("connect4-gravity-6x7", "reversi6")
CHECKPOINT_SEEDS = (17, 29, 43, 59, 71, 83, 97, 109, 127, 139,
                    151, 167, 181, 197, 211, 227, 241, 257, 271, 283)
COMPARISONS = ("task-value-dynamics", "direct-exact-leaf-value")
MATCHES_PER_CHECKPOINT = 120
FIRST_MATCH_SEED = 32_000_000
MARGIN = 0.05
FAMILYWISE_ALPHA = 0.05
POWER_TARGET = 0.80


def _canonical_hash(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def required_independent_blocks(sd, true_effect, margin=MARGIN,
                                alpha=FAMILYWISE_ALPHA, comparisons=2,
                                power=POWER_TARGET):
    """Bonferroni-conservative normal-approximation sample size.

    The primary interval is two-sided and family-wise. An alternative exactly
    on the practical margin cannot have 80% power to put its lower bound above
    that margin, so such scenarios are intentionally rejected.
    """
    if (sd <= 0 or true_effect <= margin or not 0 < alpha < 1
            or comparisons < 1 or not 0.5 < power < 1):
        raise ValueError("invalid SD/effect/margin/multiplicity/power")
    normal = NormalDist()
    z_critical = normal.inv_cdf(1 - alpha / (2 * comparisons))
    z_power = normal.inv_cdf(power)
    return math.ceil(((z_critical + z_power) * sd / (true_effect - margin)) ** 2)


def power_at_planned_blocks(sd, true_effect, blocks,
                            margin=MARGIN, alpha=FAMILYWISE_ALPHA,
                            comparisons=len(COMPARISONS)):
    """Conservative marginal power at the Bonferroni one-sided threshold."""
    if (sd <= 0 or true_effect <= margin or blocks < 1
            or not 0 < alpha < 1 or comparisons < 1):
        raise ValueError("invalid SD/effect/margin/multiplicity/block count")
    normal = NormalDist()
    critical = normal.inv_cdf(1 - alpha / (2 * comparisons))
    noncentrality = math.sqrt(blocks) * (true_effect - margin) / sd
    return normal.cdf(noncentrality - critical)


def power_scenarios():
    scenarios = []
    planned_blocks = len(CHECKPOINT_SEEDS) * MATCHES_PER_CHECKPOINT
    for sd in (0.25, 0.40, 0.50):
        for effect in (0.10, 0.15, 0.20):
            marginal_power = power_at_planned_blocks(sd, effect, planned_blocks)
            scenarios.append({
                "paired_block_sd": sd,
                "true_effect": effect,
                "practical_margin": MARGIN,
                "excess_over_margin": round(effect - MARGIN, 10),
                "required_independent_blocks": required_independent_blocks(sd, effect),
                "planned_blocks_per_game_comparison": planned_blocks,
                "marginal_power_at_planned_blocks": marginal_power,
                "joint_power_lower_bound_both_controls": max(
                    0.0, 1 - len(COMPARISONS) * (1 - marginal_power)),
                "approximation": "two-sided normal interval; Bonferroni alpha/2 per comparison",
            })
    return scenarios


def make_schedule(games=GAMES, checkpoint_seeds=CHECKPOINT_SEEDS,
                  comparisons=COMPARISONS,
                  matches_per_checkpoint=MATCHES_PER_CHECKPOINT,
                  first_match_seed=FIRST_MATCH_SEED, order_seed=28094080):
    """Build every color-swapped block; keep match seeds common across arms."""
    games = tuple(games)
    checkpoint_seeds = tuple(checkpoint_seeds)
    comparisons = tuple(comparisons)
    if (not games or len(set(games)) != len(games)
            or not checkpoint_seeds or len(set(checkpoint_seeds)) != len(checkpoint_seeds)
            or not comparisons or len(set(comparisons)) != len(comparisons)
            or matches_per_checkpoint < 1 or first_match_seed < 1):
        raise ValueError("invalid or duplicate schedule dimensions")
    rows = []
    for game in games:
        for comparison in comparisons:
            for checkpoint_index, checkpoint_seed in enumerate(checkpoint_seeds):
                for offset in range(matches_per_checkpoint):
                    match_seed = first_match_seed + checkpoint_index * matches_per_checkpoint + offset
                    block = {
                        "game": game,
                        "comparison": comparison,
                        "checkpoint_seed": checkpoint_seed,
                        "match_seed": match_seed,
                        "start": "adapter_initial_state",
                        "color_assignments": [1, -1],
                        "block_outcome": "mean_of_two_jepa_game_scores_minus_0.5",
                    }
                    block["block_id"] = _canonical_hash(block)
                    rows.append(block)
    random.Random(order_seed).shuffle(rows)
    return rows


def create_manifest():
    rows = make_schedule()
    scenarios = power_scenarios()
    conservative = next(row for row in scenarios
                        if row["paired_block_sd"] == 0.50 and row["true_effect"] == 0.10)
    manifest = {
        "schema": "caissa-jepa-v28-locked-match-schedule-v1",
        "status": "prefit commitment only; evaluator and power gate not yet passed",
        "primary_games": list(GAMES),
        "checkpoint_seeds": list(CHECKPOINT_SEEDS),
        "comparisons": list(COMPARISONS),
        "matches_per_checkpoint_game_comparison": MATCHES_PER_CHECKPOINT,
        "first_match_seed": FIRST_MATCH_SEED,
        "block_count": len(rows),
        "game_blocks_per_comparison": len(CHECKPOINT_SEEDS) * MATCHES_PER_CHECKPOINT,
        "blocks_sha256": _canonical_hash(rows),
        "row_order_seed": 28094080,
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1], text=True).strip(),
        "schedule_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "paired_score_definition": "mean(score_jepa_color_plus, score_jepa_color_minus) - 0.5",
        "practical_margin": MARGIN,
        "familywise_alpha": FAMILYWISE_ALPHA,
        "scenario_power": scenarios,
        "conservative_case": conservative,
        "claim_limit": "conditional on the frozen checkpoint panel and tested games/controls; not population training-seed generalization or exploitability",
    }
    return manifest, rows


def write_commitment(path):
    manifest, rows = create_manifest()
    payload = {"manifest": manifest, "blocks": rows}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(path)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(write_commitment(args.output), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
