"""Parameterized source bound for reference DLASCL's DSYEVD matrix path.

The helper's loop count depends on machine parameters and scaling inputs. This
module deliberately does not guess that count or claim a finite total bound.
For a caller-supplied number of executed scaling iterations, it counts only
source-visible add/subtract/multiply/divide operations on an N=32 triangular
matrix path. It is not evidence about the loaded LAPACK implementation.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
DLASCL_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "de/d3c/dlascl_8f_source.html"
)


def source_bound(iterations: int) -> dict:
    """Return a conditional bound for one nonempty upper/lower triangle call."""
    if type(iterations) is not int or iterations < 0:
        raise ValueError("iterations must be a nonnegative integer")

    triangle_entries = MATRIX_ORDER * (MATRIX_ORDER + 1) // 2
    # Each loop pass scales all 528 stored triangle entries, computes cfrom1
    # (one multiply) and cto1 (one divide), and may compute a final ratio
    # (at most one more divide). bignum=1/smlnum is initialized once per call.
    per_iteration_matrix_multiplications = triangle_entries
    per_iteration_scalar_operations = 2
    one_final_ratio_division = 1
    one_bignum_initialization_division = 1
    maximum = (
        iterations
        * (per_iteration_matrix_multiplications + per_iteration_scalar_operations)
        + one_final_ratio_division
        + one_bignum_initialization_division
        if iterations
        else 0
    )

    return {
        "schema": "caissa.v212.dlascl-iteration-bound.v01",
        "source_reference": DLASCL_SOURCE,
        "path": {
            "matrix_order": MATRIX_ORDER,
            "storage": "upper-or-lower-triangle",
            "stored_matrix_entries_per_pass": triangle_entries,
            "executed_scaling_iterations": iterations,
        },
        "scope": "source-visible add/subtract/multiply/divide only",
        "covered_source_arithmetic_interval": {
            "additions": {"minimum": 0, "maximum": 0},
            "subtractions": {"minimum": 0, "maximum": 0},
            "multiplications": {
                "minimum": 0,
                "maximum": iterations * triangle_entries + iterations,
            },
            "divisions": {
                "minimum": 0,
                "maximum": iterations + (2 if iterations else 0),
            },
            "combined_add_subtract_multiply_divide": {
                "minimum": 0,
                "maximum": maximum,
            },
        },
        "bound_formula_for_positive_iterations": "530*iterations + 2",
        "excluded_or_unresolved": [
            "a justified upper bound on iterations from the actual DLAMCH values and caller scale ratio",
            "DLAMCH, comparisons, branches, indexing, integer arithmetic, and memory work",
            "actual linked-library dispatch and executed-byte identity",
            "the rest of DSYEVD, DSYTRD, and DSTERF (separately inventoried partial scopes)",
        ],
        "eligibility": {
            "finite_total_dlascl_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(1), sort_keys=True, indent=2, allow_nan=False))
