"""Source-level branch bounds for V2.12 effective-rank arithmetic.

This excludes the preceding covariance/eigensolver path. Reduction additions
use the accepted analytical candidate convention, not a loaded-kernel claim.
"""
from __future__ import annotations

import json


LATENT = 32
DEFAULT_SCHEDULE_UPDATES = 20 * 87


def branch_work(*, active: bool, selected_eigenvalues: int) -> dict:
    """Count source operation sites for one ``_regularize`` rank branch."""
    if type(active) is not bool:
        raise ValueError("active must be Boolean")
    if type(selected_eigenvalues) is not int or not 0 <= selected_eigenvalues <= LATENT:
        raise ValueError("selected_eigenvalues must be an integer in [0, 32]")
    if active and selected_eigenvalues == 0:
        raise ValueError("an active effective-rank branch requires a selected eigenvalue")
    if not active and selected_eigenvalues != 0:
        raise ValueError("an inactive spectrum-sum branch cannot select eigenvalues")
    if not active:
        return {
            "active": False,
            "selected_eigenvalues": 0,
            "candidate_fp_additions": 0,
            "fp_multiplications": 0,
            "fp_divisions": 0,
            "log_calls": 0,
            "exp_calls": 0,
            "comparisons": 1,
            "unary_negations": 0,
        }
    count = selected_eigenvalues
    return {
        "active": True,
        "selected_eigenvalues": count,
        "candidate_fp_additions": count - 1,
        "fp_multiplications": count,
        "fp_divisions": count,
        "log_calls": count,
        "exp_calls": 1,
        # One spectrum-sum threshold comparison plus one per latent entry.
        "comparisons": LATENT + 1,
        "unary_negations": 1,
    }


def schedule_bounds(scheduled_updates: int = DEFAULT_SCHEDULE_UPDATES) -> dict:
    """Bound only effective-rank branch work over updates for one arm."""
    if type(scheduled_updates) is not int or scheduled_updates <= 0:
        raise ValueError("scheduled_updates must be a positive integer")
    inactive = branch_work(active=False, selected_eigenvalues=0)
    active_low = branch_work(active=True, selected_eigenvalues=1)
    active_high = branch_work(active=True, selected_eigenvalues=LATENT)

    def combine(*keys: str) -> dict[str, int]:
        return {
            key: scheduled_updates * inactive[key]
            for key in keys
        } | {
            f"upper_{key}": scheduled_updates * active_high[key]
            for key in keys
        }

    return {
        "schema": "caissa.v212.effective-rank-branch-bounds.v01",
        "scope": "effective-rank branch only, per arm; excludes eigensolver and fixed spectrum sum",
        "scheduled_updates_per_arm": scheduled_updates,
        "per_invocation": {
            "inactive_spectrum_sum_branch": inactive,
            "active_selected_count_bounds": {
                "minimum_selected_eigenvalues": 1,
                "maximum_selected_eigenvalues": LATENT,
                "minimum_active": active_low,
                "maximum_active": active_high,
            },
        },
        "schedule_interval_per_arm": {
            "candidate_fp_additions": combine("candidate_fp_additions"),
            "fp_multiplications": combine("fp_multiplications"),
            "fp_divisions": combine("fp_divisions"),
            "log_calls": combine("log_calls"),
            "exp_calls": combine("exp_calls"),
            "comparisons": combine("comparisons"),
            "unary_negations": combine("unary_negations"),
        },
        "limitations": [
            "Branch formulas follow the current source expressions only; no covariance or model was evaluated.",
            "Ordinary reduction additions are candidate counts under input_elements minus output_elements, not exact NumPy kernel counts.",
            "Does not bound np.linalg.eigvalsh, spectrum construction/sum, complete model work, or cross-arm parity.",
            "Does not establish the actual number of active branches in an unfrozen mask/data schedule.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(schedule_bounds(), sort_keys=True, indent=2, allow_nan=False))
