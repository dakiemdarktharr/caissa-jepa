#!/usr/bin/env python3
"""Exhaustively scan integer outer-R assurance candidates (analytic only).

This searches a finite, caller-selected R interval for the first value whose
dependence-robust union lower bound reaches a proposed assurance target. It
does not select or approve R and generates no simulation data or outcomes.
"""

from __future__ import annotations

import argparse
import json
import math
from decimal import Decimal
from statistics import NormalDist

try:
    from .v212_calibration_assurance import (
        binomial_cdf_decimal,
        binomial_cdf_downward,
        calculate,
    )
except ImportError:
    from v212_calibration_assurance import (
        binomial_cdf_decimal,
        binomial_cdf_downward,
        calculate,
    )


def _initial_cutoff(n: int, p_bad: float, alpha: float) -> int:
    """Cornish-Fisher/continuity-corrected seed for exact local adjustment."""
    mean = n * p_bad
    sd = math.sqrt(n * p_bad * (1.0 - p_bad))
    z = NormalDist().inv_cdf(alpha)
    skew = (1.0 - 2.0 * p_bad) / sd if sd else 0.0
    quantile = mean + sd * (z + skew * (z * z - 1.0) / 6.0) - 0.5
    return max(-1, min(n, math.floor(quantile)))


def exact_cutoff_near(n: int, p_bad: float, alpha: float) -> int:
    """Adjust an approximation until the exact float tail brackets alpha."""
    cutoff = _initial_cutoff(n, p_bad, alpha)
    while cutoff >= 0 and binomial_cdf_downward(n, p_bad, cutoff) > alpha:
        cutoff -= 1
    while cutoff < n and binomial_cdf_downward(n, p_bad, cutoff + 1) <= alpha:
        cutoff += 1
    return cutoff


def scan(
    r_min: int,
    r_max: int,
    *,
    endpoints: int = 69,
    cells: int = 39,
    bootstrap_replicates: int = 10_000,
    contrasts: int = 15,
    assurance_target: float = 0.80,
) -> dict[str, object]:
    if r_min < 1 or r_max < r_min:
        raise ValueError("require 1 <= r_min <= r_max")
    if endpoints < 1 or cells < 1 or bootstrap_replicates < 1 or contrasts < 1:
        raise ValueError("counts must be positive")
    if not 0.0 < assurance_target < 1.0:
        raise ValueError("assurance_target must be strictly between 0 and 1")

    alpha = 0.05 / endpoints
    rows: list[dict[str, int | float]] = []
    for n in range(r_min, r_max + 1):
        cutoff = exact_cutoff_near(n, 0.06, alpha)
        individual = binomial_cdf_downward(n, 0.05, cutoff)
        lower = 1.0 - endpoints * (1.0 - individual)
        rows.append({
            "outer_datasets_per_cell": n,
            "largest_accepted_failure_count": cutoff,
            "individual_boundary_pass_assurance": individual,
            "dependence_robust_union_lower_bound": lower,
            "passes_target": lower >= assurance_target,
        })

    qualifying = [row for row in rows if row["passes_target"]]
    first = qualifying[0] if qualifying else None
    checked: list[dict[str, object]] = []
    if first is not None:
        n0 = int(first["outer_datasets_per_cell"])
        for n in range(max(r_min, n0 - 2), min(r_max, n0 + 2) + 1):
            row = next(item for item in rows if item["outer_datasets_per_cell"] == n)
            cutoff = int(row["largest_accepted_failure_count"])
            exact = calculate([n], endpoints, cells, bootstrap_replicates, contrasts)["results"][0]
            bad_decimal = binomial_cdf_decimal(n, 0.06, cutoff)
            next_decimal = binomial_cdf_decimal(n, 0.06, cutoff + 1)
            pass_decimal = binomial_cdf_decimal(n, 0.05, cutoff)
            checked.append({
                **row,
                "cutoff_matches_reference": cutoff == exact["largest_accepted_failure_count"],
                "decimal_cutoff_valid": (
                    bad_decimal <= Decimal("0.05") / endpoints
                    and next_decimal > Decimal("0.05") / endpoints
                ),
                "decimal_individual_assurance": str(pass_decimal),
                "decimal_union_lower_bound": str(
                    Decimal(1)
                    - endpoints * (1 - pass_decimal)
                ),
                "reference_union_lower_bound": exact["dependence_robust_union_lower_bound"],
            })
            if not checked[-1]["cutoff_matches_reference"] or not checked[-1]["decimal_cutoff_valid"]:
                raise ArithmeticError(f"high-precision cutoff verification failed at R={n}")

    # Keep all cutoff changes and near-target candidates as an auditable compact summary.
    transitions = []
    for index, row in enumerate(rows):
        if index == 0 or row["largest_accepted_failure_count"] != rows[index - 1]["largest_accepted_failure_count"]:
            transitions.append({
                "R": row["outer_datasets_per_cell"],
                "cutoff": row["largest_accepted_failure_count"],
                "union_lower_bound": row["dependence_robust_union_lower_bound"],
            })
    return {
        "purpose": "finite integer-R analytic assurance scan; no simulation or outcomes",
        "range_inclusive": [r_min, r_max],
        "endpoint_count": endpoints,
        "cell_count": cells,
        "bonferroni_alpha": alpha,
        "bad_boundary_rate": 0.06,
        "pass_boundary_rate": 0.05,
        "assurance_target_proposal": assurance_target,
        "integer_values_scanned": len(rows),
        "first_qualifying_within_range": first,
        "qualifying_count_within_range": len(qualifying),
        "cutoff_transitions": transitions,
        "high_precision_neighborhood": checked,
        "scope": "The first qualifying R is only first within the searched interval and is not an adopted precision rule.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r-min", type=int, required=True)
    parser.add_argument("--r-max", type=int, required=True)
    parser.add_argument("--endpoints", type=int, default=69)
    parser.add_argument("--cells", type=int, default=39)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--contrasts", type=int, default=15)
    parser.add_argument("--assurance-target", type=float, default=0.80)
    parser.add_argument("--output", choices=("json",), default="json")
    args = parser.parse_args()
    print(json.dumps(scan(
        args.r_min,
        args.r_max,
        endpoints=args.endpoints,
        cells=args.cells,
        bootstrap_replicates=args.bootstrap_replicates,
        contrasts=args.contrasts,
        assurance_target=args.assurance_target,
    ), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
