#!/usr/bin/env python3
"""Deterministic audit for a proposed policy-yield × root-quality stress.

The tool evaluates logistic-selection intercepts, selected-root moments,
conditional ordinal-score targets, covariance preservation, endpoint assurance,
and workload. It uses no RNG and creates no candidate slots, roots, scores,
outcomes, or calibration datasets. Its output is not an accepted simulator
manifest or research-gate decision.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

if __package__:
    from .v212_calibration_assurance import calculate as calculate_assurance
    from .v212_calibration_profile_audit import BANDS
    from .v212_root_quality_calibration_audit import (
        CONTRASTS,
        INTEGRATION_DOMAIN,
        INTEGRATION_INTERVALS,
        INTERCEPT_BRACKET,
        INTERCEPT_TOL,
        INTERCEPT_WIDTH_TOL,
        MAX_BISECTION_STEPS,
        ROOT_QUALITY_VARIANCE,
        TAU,
        BETA,
        _normal_pdf,
        _logistic,
        _root_covariance_manifest,
        expected_ordinal_score_difference,
        simpson_integral,
    )
else:
    from v212_calibration_assurance import calculate as calculate_assurance
    from v212_calibration_profile_audit import BANDS
    from v212_root_quality_calibration_audit import (
        CONTRASTS,
        INTEGRATION_DOMAIN,
        INTEGRATION_INTERVALS,
        INTERCEPT_BRACKET,
        INTERCEPT_TOL,
        INTERCEPT_WIDTH_TOL,
        MAX_BISECTION_STEPS,
        ROOT_QUALITY_VARIANCE,
        TAU,
        BETA,
        _normal_pdf,
        _logistic,
        _root_covariance_manifest,
        expected_ordinal_score_difference,
        simpson_integral,
    )


GAMMAS = (-1.0, 1.0)
PAIR_GROUPS = (
    {"name": "low_yield", "q": 0.20, "preselection_weight": 0.5, "mean_offset": -0.15},
    {"name": "high_yield", "q": 0.60, "preselection_weight": 0.5, "mean_offset": 0.05},
)
SCENARIOS = (
    ("N-GLOBAL-YIELD-ROOTQ-NEG", "null", 0.0, -1.0),
    ("N-GLOBAL-YIELD-ROOTQ-POS", "null", 0.0, 1.0),
    ("A-BOUNDARY-YIELD-ROOTQ-NEG", "alternative", 0.05, -1.0),
    ("A-BOUNDARY-YIELD-ROOTQ-POS", "alternative", 0.05, 1.0),
)
ETA_BRACKET = (-8.0, 8.0)
ETA_TOL = 1e-10
ETA_WIDTH_TOL = 1e-12
INTEGRATION_TOL = 1e-10
SIGMA_REST = math.sqrt(1.0 + 1.0 - ROOT_QUALITY_VARIANCE)
ASSURANCE_REPLICATIONS = (18_000, 18_200, 18_400, 18_450, 18_500, 18_600)


def _normal_weighted(function, intervals: int) -> float:
    return simpson_integral(
        lambda value: _normal_pdf(value) * function(value), intervals
    )


def solve_validity_intercept(
    q: float, gamma: float, intervals: int
) -> dict[str, float | int]:
    """Solve E[logistic(a + gamma H)] = q for H standard normal."""
    if not 0.0 < q < 1.0:
        raise ValueError("marginal validity target must be strictly between 0 and 1")
    low, high = INTERCEPT_BRACKET

    def probability(intercept: float) -> float:
        return _normal_weighted(
            lambda value: _logistic(intercept + gamma * value), intervals
        )

    if not probability(low) <= q <= probability(high):
        raise ValueError("marginal yield target is not bracketed")
    for steps in range(1, MAX_BISECTION_STEPS + 1):
        middle = (low + high) / 2.0
        achieved = probability(middle)
        residual = achieved - q
        if abs(residual) <= INTERCEPT_TOL or high - low <= INTERCEPT_WIDTH_TOL:
            return {
                "intercept": middle,
                "target_q": q,
                "achieved_q": achieved,
                "absolute_residual": abs(residual),
                "bracket_width": high - low,
                "bisection_steps": steps,
            }
        if achieved < q:
            low = middle
        else:
            high = middle
    raise ArithmeticError("validity-intercept bisection did not converge")


def selected_root_moments(
    q: float, gamma: float, intercept: float, intervals: int
) -> dict[str, float]:
    """Moments of H conditional on validity for one policy-pair yield rate."""
    weight = lambda value: _logistic(intercept + gamma * value) / q
    mean = _normal_weighted(lambda value: value * weight(value), intervals)
    second = _normal_weighted(lambda value: value * value * weight(value), intervals)
    return {"mean": mean, "second_moment": second, "variance": second - mean * mean}


def conditional_score_mean(
    eta: float, q: float, gamma: float, intercept: float, intervals: int
) -> float:
    """Ordinal score mean after selection on H within the policy-pair group."""
    root_sd = math.sqrt(ROOT_QUALITY_VARIANCE)
    return _normal_weighted(
        lambda value: (
            _logistic(intercept + gamma * value)
            * expected_ordinal_score_difference(
                eta + root_sd * value, tau=TAU, beta=BETA, sigma=SIGMA_REST
            )
            / q
        ),
        intervals,
    )


def solve_conditional_eta(
    target: float, q: float, gamma: float, intercept: float, intervals: int
) -> dict[str, float | int]:
    """Calibrate one success-conditional mean under H | valid, pair group."""
    if not -1.0 < target < 1.0:
        raise ValueError("target mean must be strictly between -1 and 1")
    low, high = ETA_BRACKET
    low_value = conditional_score_mean(low, q, gamma, intercept, intervals)
    high_value = conditional_score_mean(high, q, gamma, intercept, intervals)
    if not low_value <= target <= high_value:
        raise ValueError("conditional target is not attainable in eta bracket")
    for steps in range(1, MAX_BISECTION_STEPS + 1):
        middle = (low + high) / 2.0
        achieved = conditional_score_mean(middle, q, gamma, intercept, intervals)
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


def _target_for_group(global_target: float, group: dict[str, float | str]) -> float:
    return global_target + float(group["mean_offset"])


def _build_solution(q: float, gamma: float, target: float, intervals: int) -> dict[str, object]:
    intercept = solve_validity_intercept(q, gamma, intervals)
    eta = solve_conditional_eta(target, q, gamma, intercept["intercept"], intervals)
    return {
        "validity": intercept,
        "selected_root_moments": selected_root_moments(
            q, gamma, intercept["intercept"], intervals
        ),
        "conditional_target": eta,
    }


def build_manifest() -> dict[str, object]:
    group_mass = [float(group["preselection_weight"]) * float(group["q"]) for group in PAIR_GROUPS]
    marginal_q = math.fsum(group_mass)
    accepted_weights = [mass / marginal_q for mass in group_mass]
    if not math.isclose(marginal_q, 0.40, rel_tol=0.0, abs_tol=1e-15):
        raise ArithmeticError("pair-yield mixture does not preserve marginal q=0.40")
    if not all(math.isclose(x, y, rel_tol=0.0, abs_tol=1e-15)
               for x, y in zip(accepted_weights, (0.25, 0.75))):
        raise ArithmeticError("success-conditional policy-pair weights changed")

    solutions: dict[tuple[float, float, float], dict[str, object]] = {}
    for _, _, global_target, gamma in SCENARIOS:
        for group in PAIR_GROUPS:
            q = float(group["q"])
            target = _target_for_group(global_target, group)
            key = (q, gamma, target)
            if key in solutions:
                continue
            by_order = {
                str(intervals): _build_solution(q, gamma, target, intervals)
                for intervals in INTEGRATION_INTERVALS
            }
            coarse, fine = (by_order[str(n)] for n in INTEGRATION_INTERVALS)
            order_differences = {
                "intercept": abs(
                    coarse["validity"]["intercept"] - fine["validity"]["intercept"]
                ),
                "achieved_q": abs(
                    coarse["validity"]["achieved_q"] - fine["validity"]["achieved_q"]
                ),
                "selected_root_mean": abs(
                    coarse["selected_root_moments"]["mean"]
                    - fine["selected_root_moments"]["mean"]
                ),
                "selected_root_second_moment": abs(
                    coarse["selected_root_moments"]["second_moment"]
                    - fine["selected_root_moments"]["second_moment"]
                ),
                "selected_root_variance": abs(
                    coarse["selected_root_moments"]["variance"]
                    - fine["selected_root_moments"]["variance"]
                ),
                "eta": abs(
                    coarse["conditional_target"]["eta"]
                    - fine["conditional_target"]["eta"]
                ),
                "achieved_mean": abs(
                    coarse["conditional_target"]["achieved_mean"]
                    - fine["conditional_target"]["achieved_mean"]
                ),
            }
            if max(order_differences.values()) > INTEGRATION_TOL:
                raise ArithmeticError(f"integration orders do not converge: {order_differences}")
            solutions[key] = {
                "q": q,
                "gamma": gamma,
                "conditional_target_mean": target,
                "by_interval_count": by_order,
                "absolute_order_differences": order_differences,
                "converged": True,
            }

    rows = []
    for scenario_id, family, global_target, gamma in SCENARIOS:
        for group in PAIR_GROUPS:
            q = float(group["q"])
            target = _target_for_group(global_target, group)
            solution = solutions[(q, gamma, target)]
            fine = solution["by_interval_count"][str(INTEGRATION_INTERVALS[-1])]
            for band in BANDS:
                for candidate, control in CONTRASTS:
                    rows.append({
                        "scenario_id": scenario_id,
                        "family": family,
                        "profile": "P2",
                        "band": band,
                        "candidate_control": f"{candidate}-{control}",
                        "policy_pair_group": group["name"],
                        "slot_validity_q": q,
                        "accepted_group_weight": accepted_weights[
                            0 if group["name"] == "low_yield" else 1
                        ],
                        "gamma": gamma,
                        "target_mean": target,
                        "solved": fine["conditional_target"],
                        "integration_order_differences": solution[
                            "absolute_order_differences"
                        ],
                    })

    null_scenarios = 26 + 2 + sum(family == "null" for _, family, _, _ in SCENARIOS)
    alternatives = 5 + 2 + sum(family == "alternative" for _, family, _, _ in SCENARIOS)
    cells = 31 + 4 + len(SCENARIOS)
    endpoints = null_scenarios + cells
    if (cells, null_scenarios, alternatives, endpoints, len(rows)) != (39, 30, 9, 69, 240):
        raise ArithmeticError("scenario, endpoint, or target-row inventory is inconsistent")

    assurance = calculate_assurance(
        list(ASSURANCE_REPLICATIONS), endpoints=endpoints, cells=cells,
        bootstrap_replicates=10_000, contrasts=15
    )
    return {
        "schema": "caissa.v212.root-quality-yield-interaction-audit.v01",
        "source_design": "docs/V212_CALIBRATION_ROOT_QUALITY_YIELD_INTERACTION_DESIGN_01_DRAFT.md",
        "status": "deterministic proposal audit only; no random draws or simulation; not accepted",
        "runtime": {
            "python_version": sys.version.split()[0],
            "implementation": sys.implementation.name,
            "platform": sys.platform,
        },
        "integration": {
            "method": "composite Simpson rule against the standard-normal density",
            "domain": list(INTEGRATION_DOMAIN),
            "interval_counts": list(INTEGRATION_INTERVALS),
            "absolute_order_tolerance": INTEGRATION_TOL,
            "intercept_absolute_residual_tolerance": INTERCEPT_TOL,
            "intercept_bracket_width_tolerance": INTERCEPT_WIDTH_TOL,
            "eta_absolute_residual_tolerance": ETA_TOL,
            "eta_bracket_width_tolerance": ETA_WIDTH_TOL,
        },
        "policy_pair_groups": [
            {**group, "accepted_weight": accepted_weights[index]}
            for index, group in enumerate(PAIR_GROUPS)
        ],
        "marginal_validity_q": marginal_q,
        "gamma_values": list(GAMMAS),
        "root_quality_variance": ROOT_QUALITY_VARIANCE,
        "sigma_rest": SIGMA_REST,
        "tau": TAU,
        "seat_advantage_beta": BETA,
        "root_covariance_manifest": _root_covariance_manifest(),
        "scenario_counts": {
            "draft_02_base_scenarios": 31,
            "root_quality_isolation_scenarios": 4,
            "interaction_scenarios": len(SCENARIOS),
            "total_scenarios": cells,
            "null_scenarios": null_scenarios,
            "alternative_scenarios": alternatives,
            "outer_mc_endpoints": endpoints,
            "conditional_target_rows": len(rows),
        },
        "solutions": list(solutions.values()),
        "conditional_target_rows": rows,
        "accepted_target_checks": [
            {
                "scenario_id": scenario_id,
                "gamma": gamma,
                "declared_global_target": target,
                "weighted_pair_conditional_target": math.fsum(
                    accepted_weights[index]
                    * _target_for_group(target, group)
                    for index, group in enumerate(PAIR_GROUPS)
                ),
            }
            for scenario_id, _, target, gamma in SCENARIOS
        ],
        "assurance": assurance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=("json",), default="json")
    parser.parse_args()
    print(json.dumps(build_manifest(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
