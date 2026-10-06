#!/usr/bin/env python3
"""Deterministic audit for the proposed root-quality/yield stress.

This tool evaluates covariance, logistic-selection integrals, and conditional
ordinal-score targets. It uses no RNG and generates no slots, roots, scores,
outcomes, or calibration datasets. Its output is not an accepted simulator
manifest or a research-gate decision.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable, Sequence

if __package__:
    from .v212_calibration_assurance import calculate as calculate_assurance
    from .v212_calibration_profile_audit import ARM_IDS, BANDS, profile_manifest
else:
    from v212_calibration_assurance import calculate as calculate_assurance
    from v212_calibration_profile_audit import ARM_IDS, BANDS, profile_manifest


TARGET_Q = 0.40
ROOT_QUALITY_VARIANCE = 0.375
ROOT_QUALITY_LOADINGS = (0.5, 0.5, -0.5, -0.5, -0.5, -0.5, -0.5)
GAMMAS = (-1.0, 1.0)
INTEGRATION_DOMAIN = (-10.0, 10.0)
INTEGRATION_INTERVALS = (4096, 8192)
INTEGRATION_TOL = 1e-10
INTERCEPT_BRACKET = (-8.0, 8.0)
INTERCEPT_TOL = 1e-12
INTERCEPT_WIDTH_TOL = 1e-12
ETA_BRACKET = (-8.0, 8.0)
ETA_TOL = 1e-10
ETA_WIDTH_TOL = 1e-12
MAX_BISECTION_STEPS = 256
TAU = 0.25
BETA = 0.15
TARGET_CASES = (
    ("N-GLOBAL-ROOTQ-NEG", -1.0, 0.0, "null"),
    ("N-GLOBAL-ROOTQ-POS", 1.0, 0.0, "null"),
    ("A-BOUNDARY-ROOTQ-NEG", -1.0, 0.05, "alternative"),
    ("A-BOUNDARY-ROOTQ-POS", 1.0, 0.05, "alternative"),
)
CONTRASTS = tuple(
    (candidate, control)
    for control in (f"C{i}" for i in range(1, 6))
    for candidate in ("V1", "V2")
)


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _logistic(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def simpson_integral(function: Callable[[float], float], intervals: int) -> float:
    """Composite Simpson integral over the frozen [-10,10] domain."""
    if intervals < 2 or intervals % 2:
        raise ValueError("Simpson interval count must be a positive even integer")
    lower, upper = INTEGRATION_DOMAIN
    step = (upper - lower) / intervals
    terms = [function(lower), function(upper)]
    terms.extend(
        (4.0 if index % 2 else 2.0) * function(lower + index * step)
        for index in range(1, intervals)
    )
    return math.fsum(terms) * step / 3.0


def _normal_expectation(function: Callable[[float], float], intervals: int) -> float:
    return simpson_integral(
        lambda value: _normal_pdf(value) * function(value), intervals
    )


def solve_validity_intercept(gamma: float, intervals: int) -> dict[str, float | int]:
    """Solve E[logistic(a + gamma H)] = TARGET_Q for standard-normal H."""
    low, high = INTERCEPT_BRACKET

    def probability(intercept: float) -> float:
        return _normal_expectation(
            lambda value: _logistic(intercept + gamma * value), intervals
        )

    if not probability(low) <= TARGET_Q <= probability(high):
        raise ValueError("marginal yield target is not bracketed")
    for steps in range(1, MAX_BISECTION_STEPS + 1):
        middle = (low + high) / 2.0
        achieved = probability(middle)
        residual = achieved - TARGET_Q
        if abs(residual) <= INTERCEPT_TOL or high - low <= INTERCEPT_WIDTH_TOL:
            return {
                "intercept": middle,
                "marginal_validity": achieved,
                "absolute_residual": abs(residual),
                "bracket_width": high - low,
                "bisection_steps": steps,
            }
        if achieved < TARGET_Q:
            low = middle
        else:
            high = middle
    raise ArithmeticError("validity-intercept bisection did not converge")


def expected_ordinal_score_difference(
    eta: float, tau: float = TAU, beta: float = BETA, sigma: float = 1.0
) -> float:
    """Draft-02 seat-averaged W/D/L score expectation for a normal margin."""
    if sigma <= 0 or tau < 0:
        raise ValueError("sigma must be positive and tau nonnegative")

    def cdf(value: float) -> float:
        return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))

    values = []
    for seat in (-1.0, 1.0):
        shifted = eta + beta * seat
        values.append(
            1.0 - cdf((tau - shifted) / sigma) - cdf((-tau - shifted) / sigma)
        )
    return math.fsum(values) / 2.0


def selected_root_moments(
    gamma: float, intercept: float, intervals: int
) -> dict[str, float]:
    """First and second moments of H conditional on slot validity."""
    def weight(value: float) -> float:
        return _logistic(intercept + gamma * value) / TARGET_Q

    mean = _normal_expectation(lambda value: value * weight(value), intervals)
    second = _normal_expectation(lambda value: value * value * weight(value), intervals)
    return {
        "mean": mean,
        "second_moment": second,
        "variance": second - mean * mean,
    }


def conditional_score_mean(
    eta: float,
    gamma: float,
    intercept: float,
    sigma_rest: float,
    intervals: int,
) -> float:
    """Ordinal score mean after selection on the shared root factor."""
    root_sd = math.sqrt(ROOT_QUALITY_VARIANCE)
    return _normal_expectation(
        lambda value: (
            _logistic(intercept + gamma * value)
            * expected_ordinal_score_difference(
                eta + root_sd * value, tau=TAU, beta=BETA, sigma=sigma_rest
            )
            / TARGET_Q
        ),
        intervals,
    )


def solve_conditional_eta(
    target: float,
    gamma: float,
    intercept: float,
    sigma_rest: float,
    intervals: int,
) -> dict[str, float | int]:
    """Solve the mean target under the selected-root distribution."""
    if not -1.0 < target < 1.0:
        raise ValueError("target mean must be strictly between -1 and 1")
    low, high = ETA_BRACKET
    low_value = conditional_score_mean(
        low, gamma, intercept, sigma_rest, intervals
    )
    high_value = conditional_score_mean(
        high, gamma, intercept, sigma_rest, intervals
    )
    if not low_value <= target <= high_value:
        raise ValueError("conditional target is not attainable in eta bracket")

    for steps in range(1, MAX_BISECTION_STEPS + 1):
        middle = (low + high) / 2.0
        achieved = conditional_score_mean(
            middle, gamma, intercept, sigma_rest, intervals
        )
        residual = achieved - target
        if abs(residual) <= ETA_TOL or high - low <= ETA_WIDTH_TOL:
            return {
                "eta": middle,
                "target_mean": target,
                "achieved_mean": achieved,
                "absolute_residual": abs(residual),
                "bracket_width": high - low,
                "bisection_steps": steps,
            }
        if achieved < target:
            low = middle
        else:
            high = middle
    raise ArithmeticError("conditional eta bisection did not converge")


def _cholesky_positive(matrix: Sequence[Sequence[float]]) -> bool:
    """Check positive definiteness of a small symmetric covariance matrix."""
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix):
        return False
    lower = [[0.0] * size for _ in range(size)]
    try:
        for row in range(size):
            for column in range(row + 1):
                if not math.isclose(
                    matrix[row][column], matrix[column][row], abs_tol=1e-12
                ):
                    return False
                residual = matrix[row][column] - math.fsum(
                    lower[row][k] * lower[column][k] for k in range(column)
                )
                if row == column:
                    if residual <= 0:
                        return False
                    lower[row][column] = math.sqrt(residual)
                else:
                    lower[row][column] = residual / lower[column][column]
    except (ArithmeticError, ZeroDivisionError):
        return False
    return True


def _margin_variance(covariance: Sequence[Sequence[float]], pair: tuple[str, str]) -> float:
    candidate, control = pair
    c_index = ARM_IDS.index(candidate)
    o_index = ARM_IDS.index(control)
    return (
        covariance[c_index][c_index]
        + covariance[o_index][o_index]
        - 2.0 * covariance[c_index][o_index]
    )


def _quality_covariance() -> list[list[float]]:
    return [
        [
            ROOT_QUALITY_VARIANCE * ROOT_QUALITY_LOADINGS[i] * ROOT_QUALITY_LOADINGS[j]
            for j in range(len(ARM_IDS))
        ]
        for i in range(len(ARM_IDS))
    ]


def _root_covariance_manifest() -> dict[str, object]:
    p2 = profile_manifest()["profiles"]["P2"]
    bands: dict[str, object] = {}
    quality_covariance = _quality_covariance()
    for band in BANDS:
        original = p2["bands"][band]["components"]["root_slot"]["covariance"]
        remaining = [[0.5 * value for value in row] for row in original]
        total = [
            [remaining[i][j] + quality_covariance[i][j] for j in range(len(ARM_IDS))]
            for i in range(len(ARM_IDS))
        ]
        pair_variances = {
            f"{candidate}-{control}": _margin_variance(total, (candidate, control))
            for candidate, control in CONTRASTS
        }
        remaining_pair_variances = {
            f"{candidate}-{control}": _margin_variance(remaining, (candidate, control))
            for candidate, control in CONTRASTS
        }
        if not _cholesky_positive(total):
            raise ArithmeticError(f"total root-slot covariance is not positive definite: {band}")
        if any(not math.isclose(value, 0.75, abs_tol=1e-12) for value in pair_variances.values()):
            raise ArithmeticError(f"root-slot margin variance changed in band {band}")
        bands[band] = {
            "original_root_slot_covariance": original,
            "remaining_root_slot_covariance": remaining,
            "root_quality_covariance": quality_covariance,
            "total_root_slot_covariance": total,
            "remaining_pair_margin_variances": remaining_pair_variances,
            "total_pair_margin_variances": pair_variances,
            "positive_definite": True,
        }
    return {
        "arm_order": list(ARM_IDS),
        "root_quality_loadings": list(ROOT_QUALITY_LOADINGS),
        "root_quality_pair_margin_variance": ROOT_QUALITY_VARIANCE,
        "bands": bands,
    }


def _solve_at_order(
    gamma: float, target: float, intervals: int, sigma_rest: float
) -> dict[str, object]:
    intercept = solve_validity_intercept(gamma, intervals)
    eta = solve_conditional_eta(
        target, gamma, intercept["intercept"], sigma_rest, intervals
    )
    return {
        "validity": intercept,
        "selected_root_moments": selected_root_moments(
            gamma, intercept["intercept"], intervals
        ),
        "conditional_target": eta,
    }


def build_manifest() -> dict[str, object]:
    profiles = profile_manifest()["profiles"]["P2"]["bands"]
    if not all(
        math.isclose(
            profiles[band]["mean_pair_latent_margin_variance_V"], 1.0,
            rel_tol=1e-12, abs_tol=1e-12
        )
        for band in BANDS
    ):
        raise ArithmeticError("P2 base latent margin variance must equal one")

    total_v = 1.0
    sigma_rest = math.sqrt(1.0 + total_v - ROOT_QUALITY_VARIANCE)
    covariance = _root_covariance_manifest()
    integration_results: dict[tuple[float, float], dict[str, object]] = {}
    for _, gamma, target, _ in TARGET_CASES:
        key = (gamma, target)
        if key in integration_results:
            continue
        by_order = {
            str(intervals): _solve_at_order(gamma, target, intervals, sigma_rest)
            for intervals in INTEGRATION_INTERVALS
        }
        coarse, fine = (
            by_order[str(intervals)] for intervals in INTEGRATION_INTERVALS
        )
        a_delta = abs(
            coarse["validity"]["intercept"] - fine["validity"]["intercept"]
        )
        q_delta = abs(
            coarse["validity"]["marginal_validity"]
            - fine["validity"]["marginal_validity"]
        )
        eta_delta = abs(
            coarse["conditional_target"]["eta"]
            - fine["conditional_target"]["eta"]
        )
        mean_delta = abs(
            coarse["conditional_target"]["achieved_mean"]
            - fine["conditional_target"]["achieved_mean"]
        )
        deltas = {
            "intercept": a_delta,
            "marginal_validity": q_delta,
            "eta": eta_delta,
            "achieved_mean": mean_delta,
        }
        if max(deltas.values()) > INTEGRATION_TOL:
            raise ArithmeticError(f"integration orders do not converge: {deltas}")
        integration_results[key] = {
            "gamma": gamma,
            "target_mean": target,
            "by_interval_count": by_order,
            "absolute_order_differences": deltas,
            "converged": True,
        }

    rows = []
    for scenario_id, gamma, target, family in TARGET_CASES:
        solved = integration_results[(gamma, target)]
        fine = solved["by_interval_count"][str(INTEGRATION_INTERVALS[-1])]
        for band in BANDS:
            for candidate, control in CONTRASTS:
                rows.append({
                    "scenario_id": scenario_id,
                    "family": family,
                    "profile": "P2",
                    "band": band,
                    "candidate_control": f"{candidate}-{control}",
                    "gamma": gamma,
                    "target_mean": target,
                    "policy_pair_validity_q": TARGET_Q,
                    "solved": fine["conditional_target"],
                    "integration_order_differences": solved["absolute_order_differences"],
                })

    null_count = sum(family == "null" for _, _, _, family in TARGET_CASES)
    alternative_count = sum(family == "alternative" for _, _, _, family in TARGET_CASES)
    cells = 31 + len(TARGET_CASES)
    null_scenarios = 26 + null_count
    endpoints = null_scenarios + cells
    if (cells, null_scenarios, endpoints, len(rows)) != (35, 28, 63, 120):
        raise ArithmeticError("root-quality scenario/end-point mapping is inconsistent")

    assurance = calculate_assurance(
        [18_000, 18_200], endpoints=endpoints, cells=cells,
        bootstrap_replicates=10_000, contrasts=15
    )
    return {
        "schema": "caissa.v212.root-quality-calibration-audit.v01",
        "source_addendum": "docs/V212_CALIBRATION_ROOT_QUALITY_STRESS_DESIGN_01_DRAFT.md",
        "status": "deterministic proposal audit only; no random draws or simulation; not accepted",
        "runtime": {"python_version": sys.version.split()[0]},
        "integration": {
            "method": "composite Simpson rule against the standard-normal density",
            "domain": list(INTEGRATION_DOMAIN),
            "interval_counts": list(INTEGRATION_INTERVALS),
            "absolute_order_tolerance": INTEGRATION_TOL,
            "omitted_two_sided_normal_tail_probability": math.erfc(10.0 / math.sqrt(2.0)),
        },
        "target_q": TARGET_Q,
        "gamma_values": list(GAMMAS),
        "tau": TAU,
        "seat_advantage_beta": BETA,
        "root_quality_variance": ROOT_QUALITY_VARIANCE,
        "sigma_rest": sigma_rest,
        "covariance_manifest": covariance,
        "scenario_counts": {
            "base_scenarios": 31,
            "added_scenarios": len(TARGET_CASES),
            "total_scenarios": cells,
            "null_scenarios": null_scenarios,
            "alternative_scenarios": alternative_count + 5,
            "outer_mc_endpoints": endpoints,
        },
        "quadrature_solutions": list(integration_results.values()),
        "conditional_target_rows": rows,
        "assurance": assurance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=("json",), default="json")
    parser.parse_args()
    print(json.dumps(build_manifest(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
