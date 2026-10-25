#!/usr/bin/env python3
"""Audit scenario means and eta calibration for V2.12 draft 02.

This is a deterministic parameter calculation. It does not sample random
effects, slots, roots, game outcomes, or calibration datasets.
"""

from __future__ import annotations

import argparse
import json
import math

if __package__:
    from .v212_calibration_profile_audit import BANDS, profile_manifest
else:
    from v212_calibration_profile_audit import BANDS, profile_manifest


CONTRAST_ORDER = tuple((candidate, control) for control in (f"C{i}" for i in range(1, 6))
                       for candidate in ("V1", "V2"))
POLICY_PAIR_INDEX = tuple(range(16))
PROFILE_TAU = {"P1": 0.15, "P2": 0.25, "P3": 0.40, "P4": 0.75, "P5": 0.40}
BETA = 0.15
ETA_BRACKET = (-8.0, 8.0)
ETA_ABS_TOL = 1e-10
ETA_WIDTH_TOL = 1e-12
MAX_BISECTION_STEPS = 256


def _zero_means() -> dict[str, float]:
    return {f"{v}-{c}": 0.0 for v, c in CONTRAST_ORDER}


def _base_scenarios() -> list[dict[str, object]]:
    scenarios: list[dict[str, object]] = []
    for index in range(1, 6):
        scenarios.append({
            "scenario_id": f"N-GLOBAL-{index:02d}",
            "family": "null_global",
            "profile": f"P{index}",
            "means_by_band": {band: _zero_means() for band in BANDS},
        })

    for zero_index in range(10):
        means = _zero_means()
        means.update({pair: 0.075 for pair in means})
        zero_pair = CONTRAST_ORDER[zero_index]
        means[f"{zero_pair[0]}-{zero_pair[1]}"] = 0.0
        scenarios.append({
            "scenario_id": f"N-ATOMIC-{zero_index + 1:02d}",
            "family": "null_atomic",
            "profile": f"P{zero_index % 5 + 1}",
            "means_by_band": {band: dict(means) for band in BANDS},
        })

    for control_index in range(5):
        means = {pair: 0.075 for pair in _zero_means()}
        control = f"C{control_index + 1}"
        means[f"V1-{control}"] = 0.10
        means[f"V2-{control}"] = -0.10
        scenarios.append({
            "scenario_id": f"N-MACRO-{control_index + 1:02d}",
            "family": "null_macro",
            "profile": f"P{control_index + 1}",
            "means_by_band": {band: dict(means) for band in BANDS},
            "reviewable_convention": "variant-1:+0.10; variant-2:-0.10 for the null macro pair",
        })

    for control_index in range(5):
        means = {pair: 0.075 for pair in _zero_means()}
        control = f"C{control_index + 1}"
        for candidate in ("V1", "V2"):
            means[f"{candidate}-{control}"] = 0.0
        scenarios.append({
            "scenario_id": f"N-CONTROL-{control_index + 1:02d}",
            "family": "null_control",
            "profile": f"P{control_index + 1}",
            "means_by_band": {band: dict(means) for band in BANDS},
        })

    for scenario_id, target, profile in (
        ("A-BOUNDARY", 0.05, "P1"),
        ("A-MODERATE", 0.075, "P2"),
        ("A-LARGE", 0.10, "P3"),
    ):
        means = {pair: target for pair in _zero_means()}
        scenarios.append({
            "scenario_id": scenario_id,
            "family": "alternative",
            "profile": profile,
            "means_by_band": {band: dict(means) for band in BANDS},
        })

    hetero = {}
    for band, offset in zip(BANDS, (0.10, 0.0, -0.10)):
        hetero[band] = {}
        for control_index in range(5):
            control = f"C{control_index + 1}"
            for candidate_index, candidate in enumerate(("V1", "V2")):
                base = (
                    (0.10, 0.05)[candidate_index]
                    if control_index in (0, 2, 4)
                    else (0.05, 0.10)[candidate_index]
                )
                hetero[band][f"{candidate}-{control}"] = base + offset
    scenarios.append({
        "scenario_id": "A-HETERO",
        "family": "alternative_heterogeneous",
        "profile": "P5",
        "means_by_band": hetero,
    })

    for scenario_id, family, profile, target in (
        ("N-GLOBAL-YIELD", "null_global_yield_stress", "P5", 0.0),
        ("A-BOUNDARY-YIELD", "alternative_yield_stress", "P1", 0.05),
    ):
        means = {pair: target for pair in _zero_means()}
        scenarios.append({
            "scenario_id": scenario_id,
            "family": family,
            "profile": profile,
            "means_by_band": {band: dict(means) for band in BANDS},
        })
    return scenarios


def _profile_mapping(scenarios: list[dict[str, object]]) -> None:
    ids = [scenario["scenario_id"] for scenario in scenarios]
    if len(ids) != 31 or len(set(ids)) != 31:
        raise ArithmeticError("scenario inventory must contain exactly 31 unique IDs")
    if sum(str(scenario["family"]).startswith("null_") for scenario in scenarios) != 26:
        # 25 principal nulls plus one global/yield null cell.
        raise ArithmeticError("null scenario inventory does not match draft 02")


def expected_score_difference(eta: float, tau: float, beta: float, sigma: float) -> float:
    """Evaluate the seat-averaged ordinal-score mean using stdlib math.erf."""
    if sigma <= 0 or tau < 0:
        raise ValueError("sigma must be positive and tau nonnegative")

    def cdf(value: float) -> float:
        return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))

    seat_means = []
    for seat in (-1.0, 1.0):
        shifted = eta + beta * seat
        seat_means.append(
            1.0 - cdf((tau - shifted) / sigma) - cdf((-tau - shifted) / sigma)
        )
    return math.fsum(seat_means) / 2.0


def solve_eta(target: float, tau: float, beta: float, sigma: float) -> dict[str, float | int]:
    """Bisection over the predeclared bracket and stopping tolerances."""
    if not -1.0 < target < 1.0:
        raise ValueError("target mean must be strictly between -1 and 1")
    low, high = ETA_BRACKET
    f_low = expected_score_difference(low, tau, beta, sigma)
    f_high = expected_score_difference(high, tau, beta, sigma)
    if not f_low <= target <= f_high:
        raise ValueError("target is unattainable within the frozen eta bracket")

    for steps in range(1, MAX_BISECTION_STEPS + 1):
        middle = (low + high) / 2.0
        achieved = expected_score_difference(middle, tau, beta, sigma)
        residual = achieved - target
        if abs(residual) <= ETA_ABS_TOL or high - low <= ETA_WIDTH_TOL:
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
    raise ArithmeticError("eta bisection did not meet a frozen stopping condition")


def _policy_target_groups(scenario_id: str) -> list[dict[str, object]]:
    if scenario_id in ("N-GLOBAL-YIELD", "A-BOUNDARY-YIELD"):
        return [
            {"policy_pair_indices": list(range(8)), "q": 0.20, "mean_offset": -0.15},
            {"policy_pair_indices": list(range(8, 16)), "q": 0.60, "mean_offset": 0.05},
        ]
    return [{"policy_pair_indices": list(POLICY_PAIR_INDEX), "q": 0.40, "mean_offset": 0.0}]


def build_manifest() -> dict[str, object]:
    profiles = profile_manifest()["profiles"]
    scenarios = _base_scenarios()
    _profile_mapping(scenarios)
    solved_scenarios = []
    for scenario in scenarios:
        profile_id = scenario["profile"]
        tau = PROFILE_TAU[profile_id]
        groups = _policy_target_groups(scenario["scenario_id"])
        solved = []
        for pair in CONTRAST_ORDER:
            for band in BANDS:
                target = scenario["means_by_band"][band][f"{pair[0]}-{pair[1]}"]
                sigma = profiles[profile_id]["bands"][band][
                    "pair_sigma_including_unit_game_residual"
                ][f"{pair[0]}-{pair[1]}"]
                for group in groups:
                    adjusted_target = target + group["mean_offset"]
                    result = solve_eta(adjusted_target, tau, BETA, sigma)
                    solved.append({
                        "candidate_control": f"{pair[0]}-{pair[1]}",
                        "band": band,
                        "tau": tau,
                        "beta": BETA,
                        "policy_pair_indices": group["policy_pair_indices"],
                        "slot_validity_q": group["q"],
                        "population_mean_target": adjusted_target,
                        "sigma": sigma,
                        **result,
                    })
        solved_scenarios.append({
            **scenario,
            "tau": tau,
            "beta": BETA,
            "solved_eta_rows": solved,
        })

    all_rows = [row for scenario in solved_scenarios for row in scenario["solved_eta_rows"]]
    return {
        "schema": "caissa.v212.calibration-target-audit.v01",
        "source_protocol": "docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_02.md",
        "status": "analytical proposal audit; no random draws; not an accepted simulator manifest",
        "cdf_implementation": "Python math.erf normal CDF",
        "eta_bracket": list(ETA_BRACKET),
        "absolute_residual_tolerance": ETA_ABS_TOL,
        "bracket_width_tolerance": ETA_WIDTH_TOL,
        "atomic_contrast_order": [f"{v}-{c}" for v, c in CONTRAST_ORDER],
        "policy_pair_indices_are_abstract": True,
        "reviewable_open_convention": (
            "N-MACRO uses the explicit draft assumption +0.10 for variant 1 and "
            "-0.10 for variant 2; this proposed convention needs independent disposition "
            "before any simulation"
        ),
        "scenario_count": len(solved_scenarios),
        "solved_eta_row_count": len(all_rows),
        "maximum_absolute_residual": max(row["absolute_residual"] for row in all_rows),
        "scenarios": solved_scenarios,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=("json",), default="json")
    parser.parse_args()
    print(json.dumps(build_manifest(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
