"""Common-omitted-work sensitivity for the V2.12 six-arm partial ledger.

This is an algebraic sensitivity, not a FLOP counter or parity decision. It
asks how much hypothetical *identical* omitted work per update would be needed
to dilute the current source-covered subtotal range to the D03 tolerance. It
does not assert that omitted operations exist or are equal across arms.
"""
from __future__ import annotations

from .v212_partial_flop_ledger import accounting


SCHEMA = "caissa.v212.parity-shared-work-sensitivity.v01"
LEDGER_SCHEMA = "caissa.v212.partial-flop-owner-ledger.v01"
ARMS = (
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
)


def sensitivity(ledger: dict | None = None, tolerance_basis_points: int = 500) -> dict:
    """Return the common omitted work needed under an explicitly equal-cost assumption.

    ``tolerance_basis_points=500`` encodes the D03 range tolerance of 5%.
    The ledger's per-arm source-covered intervals are treated adversarially:
    largest upper endpoint versus smallest lower endpoint.
    """
    if type(tolerance_basis_points) is not int or not 1 <= tolerance_basis_points < 10_000:
        raise ValueError("tolerance_basis_points must be an integer in [1, 9999]")
    report = accounting() if ledger is None else ledger
    if report.get("schema") != LEDGER_SCHEMA:
        raise ValueError("unsupported source-covered ledger schema")
    arm_reports = report.get("arms")
    if not isinstance(arm_reports, dict) or set(arm_reports) != set(ARMS):
        raise ValueError("ledger must contain exactly the frozen six arms")
    if any(not isinstance(arm_reports[arm], dict) for arm in ARMS):
        raise ValueError("each arm ledger must be a mapping")
    update_count = report.get("scheduled_updates_not_aggregated")
    if type(update_count) is not int or update_count <= 0:
        raise ValueError("ledger must provide a positive scheduled-update count")

    intervals = {}
    for arm in ARMS:
        interval = arm_reports[arm].get("partial_source_candidate_flops")
        if not isinstance(interval, dict):
            raise ValueError(f"missing partial source interval for {arm}")
        lower, upper = interval.get("lower"), interval.get("upper")
        if (type(lower) is not int or type(upper) is not int
                or lower <= 0 or upper < lower):
            raise ValueError(f"invalid partial source interval for {arm}")
        intervals[arm] = {"lower": lower, "upper": upper}

    max_arm = max(ARMS, key=lambda arm: intervals[arm]["upper"])
    min_arm = min(ARMS, key=lambda arm: intervals[arm]["lower"])
    largest_upper = intervals[max_arm]["upper"]
    smallest_lower = intervals[min_arm]["lower"]
    # (max + C) / (min + C) <= 1 + t/bp
    numerator = (largest_upper * 10_000
                 - smallest_lower * (10_000 + tolerance_basis_points))
    common_per_update = (
        0 if numerator <= 0 else
        (numerator + tolerance_basis_points - 1) // tolerance_basis_points
    )
    common_schedule = common_per_update * update_count
    return {
        "schema": SCHEMA,
        "scope": "hypothetical identical omitted FP addition to all six source-covered per-update intervals",
        "input_mask_fixture": report.get("mask_fixture"),
        "tolerance_basis_points": tolerance_basis_points,
        "source_covered_intervals_per_invocation": intervals,
        "widest_endpoints": {
            "max_upper_arm": max_arm,
            "max_upper": largest_upper,
            "min_lower_arm": min_arm,
            "min_lower": smallest_lower,
        },
        "common_omitted_flops_required_per_update": common_per_update,
        "scheduled_updates_not_aggregated": update_count,
        "common_omitted_flops_if_same_fixture_repeated_for_all_updates": common_schedule,
        "assumptions": [
            "the omitted FP count is exactly equal across all six arms",
            "the same per-invocation mask context and branch intervals apply to every scheduled update",
            "the source-covered partial intervals themselves are valid candidates",
        ],
        "interpretation": (
            "sensitivity only; omitted arm-specific work, actual masks, runtime kernels, and LAPACK can change the result"
        ),
        "coverage": {
            "full_counter": False,
            "parity_decision": False,
            "profile_authorized": False,
            "fit_authorized": False,
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(sensitivity(), sort_keys=True, indent=2, allow_nan=False))
