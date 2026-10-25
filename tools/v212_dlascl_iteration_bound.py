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


def dsyevd_ieee_binary64_bound() -> dict:
    """Return a conditional one-pass bound for DSYEVD's scale call.

    This derives an iteration count from the reference DSYEVD/DLAMCH/DLANSY
    source under explicit IEEE binary64 assumptions. It does not attest that
    the NumPy-linked LAPACK uses this implementation or those machine values.
    """
    result = source_bound(1)
    result["schema"] = "caissa.v212.dlascl-dsyevd-ieee-binary64-bound.v01"
    result["conditional_source_references"] = {
        "dsyevd_lapack_3_12_1": (
            "https://www.netlib.org/lapack/explore-html/"
            "d1/da2/dsyevd_8f_source.html"
        ),
        "dlamch_lapack_3_12_1": (
            "https://www.netlib.org/lapack/explore-html/"
            "d5/dd4/dlamch_8f_source.html"
        ),
        "dlansy_lapack_3_12_1": (
            "https://www.netlib.org/lapack/explore-html/"
            "d1/d25/dlansy_8f_source.html"
        ),
        "dlascl_lapack_3_12_1": DLASCL_SOURCE,
    }
    result["path"]["iteration_basis"] = "derived from DSYEVD scale ratio under declared assumptions"
    result["conditional_machine_and_input_assumptions"] = {
        "format": "IEEE 754 binary64 with gradual subnormals",
        "finite_input_matrix": True,
        "dlansy_norm": "reference DLANSY('M') returns max(abs(A(i,j)))",
        "dlamch_safe_minimum": "2**-1022",
        "dlamch_precision": "2**-52",
        "least_positive_subnormal": "2**-1074",
        "largest_finite_value": "strictly below 2**1024",
    }
    result["derived_dsyevd_scaling"] = {
        "dsyevd_smlnum": "2**-970",
        "dsyevd_bignum": "2**970",
        "rmin": "2**-485",
        "rmax": "2**485",
        "sigma_if_anrm_below_rmin": "1 < sigma <= 2**589",
        "sigma_if_anrm_above_rmax": "2**-539 < sigma < 1",
        "dlascl_local_limits": (
            "under IEEE binary64 DLASCL uses smlnum=DLAMCH('S')=2**-1022 "
            "and bignum=1/smlnum=2**1022"
        ),
        "conclusion": (
            "both DSYEVD sigma branches are inside DSYEVD's own scaling "
            "thresholds; DLASCL completes its loop on the first pass"
        ),
        "maximum_scaling_calls": 1,
        "maximum_scaling_iterations_per_call": 1,
    }
    result["eligibility"]["finite_total_dlascl_bound_under_declared_assumptions"] = True
    result["eligibility"]["actual_runtime_attested"] = False
    result["excluded_or_unresolved"] = [
        "whether the loaded NumPy-linked LAPACK follows these reference sources and IEEE binary64 assumptions",
        "DLAMCH, comparisons, branches, indexing, integer arithmetic, and memory work",
        "the rest of DSYEVD, DSYTRD, and DSTERF (separately inventoried partial scopes)",
    ]
    return result


if __name__ == "__main__":
    print(json.dumps(dsyevd_ieee_binary64_bound(), sort_keys=True, indent=2, allow_nan=False))
