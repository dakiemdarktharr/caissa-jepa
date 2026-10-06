#!/usr/bin/env python3
"""Reproduce the analytic outer-replication assurance in V2.12 draft 02.

This computes binomial tails only. It does not generate synthetic datasets,
roots, model outputs, scores, or outcomes.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from decimal import Decimal, localcontext


def _validate(n: int, p: float, k: int) -> None:
    if n < 1:
        raise ValueError("n must be positive")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    if k < -1 or k > n:
        raise ValueError("k must be in [-1, n]")


def binomial_cdf_downward(n: int, p: float, k: int) -> float:
    """Evaluate P[X <= k] by starting at P[X=k] and recurring downward."""
    _validate(n, p, k)
    if k < 0 or p == 0.0:
        return 0.0 if k < 0 else 1.0
    if p == 1.0:
        return 0.0 if k < n else 1.0
    if k == n:
        return 1.0
    if k > n * p:
        return 1.0 - binomial_cdf_downward(n, 1.0 - p, n - k - 1)

    log_pk = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )
    term = math.exp(log_pk)
    terms = [term]
    for i in range(k, 0, -1):
        term *= (i / (n - i + 1)) * ((1.0 - p) / p)
        terms.append(term)
    return math.fsum(terms)


def binomial_cdf_logsum(n: int, p: float, k: int) -> float:
    """Evaluate the same tail with a log-PMF/log-sum-exp calculation."""
    _validate(n, p, k)
    if k < 0 or p == 0.0:
        return 0.0 if k < 0 else 1.0
    if p == 1.0:
        return 0.0 if k < n else 1.0

    logs = [
        math.lgamma(n + 1)
        - math.lgamma(i + 1)
        - math.lgamma(n - i + 1)
        + i * math.log(p)
        + (n - i) * math.log1p(-p)
        for i in range(k + 1)
    ]
    pivot = max(logs)
    return math.exp(pivot) * math.fsum(math.exp(x - pivot) for x in logs)


def binomial_cdf_decimal(n: int, p: float | Decimal, k: int) -> Decimal:
    """Evaluate the tail at 60-digit precision using exact integer choose(n,k)."""
    p_decimal = p if isinstance(p, Decimal) else Decimal(str(p))
    _validate(n, float(p_decimal), k)
    with localcontext() as context:
        context.prec = 60
        q_decimal = Decimal(1) - p_decimal
        if k < 0:
            return Decimal(0)
        if p_decimal == 0:
            return Decimal(1)
        if p_decimal == 1:
            return Decimal(0) if k < n else Decimal(1)
        if k == n:
            return Decimal(1)
        if Decimal(k) > n * p_decimal:
            return Decimal(1) - binomial_cdf_decimal(
                n, q_decimal, n - k - 1
            )

        term = (
            Decimal(math.comb(n, k))
            * p_decimal**k
            * q_decimal ** (n - k)
        )
        terms = [term]
        for i in range(k, 0, -1):
            term *= Decimal(i) * q_decimal / (Decimal(n - i + 1) * p_decimal)
            terms.append(term)
        return sum(terms, Decimal(0))


def _largest_accepted_count(n: int, p_bad: float, alpha: float) -> int:
    """Largest k whose one-sided CP failure tail is at most alpha."""
    lo, hi = -1, n
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if binomial_cdf_downward(n, p_bad, mid) <= alpha:
            lo = mid
        else:
            hi = mid
    return lo


def _assurance_row(
    n: int,
    endpoints: int,
    cells: int,
    bootstrap_replicates: int,
    contrasts: int,
) -> dict[str, int | float]:
    alpha = 0.05 / endpoints
    cutoff = _largest_accepted_count(n, 0.06, alpha)
    cdf_bad_down = binomial_cdf_downward(n, 0.06, cutoff)
    cdf_bad_log = binomial_cdf_logsum(n, 0.06, cutoff)
    cdf_next_down = binomial_cdf_downward(n, 0.06, cutoff + 1)
    cdf_next_log = binomial_cdf_logsum(n, 0.06, cutoff + 1)
    pass_down = binomial_cdf_downward(n, 0.05, cutoff)
    pass_log = binomial_cdf_logsum(n, 0.05, cutoff)
    alpha_decimal = Decimal("0.05") / Decimal(endpoints)
    cdf_bad_decimal = binomial_cdf_decimal(n, Decimal("0.06"), cutoff)
    cdf_next_decimal = binomial_cdf_decimal(n, Decimal("0.06"), cutoff + 1)
    pass_decimal = binomial_cdf_decimal(n, Decimal("0.05"), cutoff)
    if cdf_bad_decimal > alpha_decimal or cdf_next_decimal <= alpha_decimal:
        raise ArithmeticError("high-precision cutoff does not satisfy its tails")
    if not (
        math.isclose(cdf_bad_down, cdf_bad_log, rel_tol=5e-11, abs_tol=1e-14)
        and math.isclose(cdf_next_down, cdf_next_log, rel_tol=5e-11, abs_tol=1e-14)
        and math.isclose(pass_down, pass_log, rel_tol=5e-11, abs_tol=1e-14)
        and math.isclose(cdf_bad_down, float(cdf_bad_decimal), rel_tol=1e-9)
        and math.isclose(cdf_next_down, float(cdf_next_decimal), rel_tol=1e-9)
        and math.isclose(pass_down, float(pass_decimal), rel_tol=1e-9)
    ):
        raise ArithmeticError("independent binomial-tail methods disagree")
    if cdf_bad_down > alpha or cdf_next_down <= alpha:
        raise ArithmeticError("acceptance cutoff does not satisfy its defining tails")

    union_lower = Decimal(1) - Decimal(endpoints) * (Decimal(1) - pass_decimal)
    bootstrap_work = cells * n * bootstrap_replicates
    return {
        "outer_datasets_per_cell": n,
        "endpoint_count": endpoints,
        "bonferroni_alpha": alpha,
        "largest_accepted_failure_count": cutoff,
        "bad_boundary_tail_at_cutoff_p_0_06": str(cdf_bad_decimal),
        "bad_boundary_tail_at_next_count_p_0_06": str(cdf_next_decimal),
        "individual_pass_assurance_at_p_0_05": str(pass_decimal),
        "dependence_robust_union_lower_bound": str(union_lower),
        "cells": cells,
        "inner_bootstrap_replicates_per_dataset": bootstrap_replicates,
        "total_inner_bootstrap_replicates": bootstrap_work,
        "max_contrast_evaluations": bootstrap_work * contrasts,
    }


def calculate(
    replications: Sequence[int],
    endpoints: int = 57,
    cells: int = 31,
    bootstrap_replicates: int = 10_000,
    contrasts: int = 15,
) -> dict[str, object]:
    if endpoints < 1 or cells < 1 or bootstrap_replicates < 1 or contrasts < 1:
        raise ValueError("counts must be positive")
    return {
        "purpose": "analytic binomial precision only; no simulation or outcomes",
        "bad_boundary_rate": 0.06,
        "pass_boundary_rate": 0.05,
        "results": [
            _assurance_row(n, endpoints, cells, bootstrap_replicates, contrasts)
            for n in replications
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replications", nargs="+", type=int, default=[6000, 18000])
    parser.add_argument("--endpoints", type=int, default=57)
    parser.add_argument("--cells", type=int, default=31)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--contrasts", type=int, default=15)
    args = parser.parse_args()
    print(
        json.dumps(
            calculate(
                args.replications,
                endpoints=args.endpoints,
                cells=args.cells,
                bootstrap_replicates=args.bootstrap_replicates,
                contrasts=args.contrasts,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
