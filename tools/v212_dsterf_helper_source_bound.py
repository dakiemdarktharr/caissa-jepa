"""Conditional helper-source bound for the reference DSTERF N=32 path.

This supplements ``v212_dsterf_iteration_bound`` only for its DLAMCH setup
calls and the DLAPY2 calls made by shifted QL/QR iterations. Scaling, norm
scans, sorting, and loaded-library/runtime behavior remain outside the bound.
"""
from __future__ import annotations

import json

from .v212_dsterf_iteration_bound import source_bound as dsterf_source_bound


MATRIX_ORDER = 32
MAXIT_PER_EIGENVALUE = 30
MAX_DSTERF_ITERATIONS = MATRIX_ORDER * MAXIT_PER_EIGENVALUE
DLAPY2_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d5/d7c/dlapy2_8f_source.html"
)
DLAMCH_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d5/dd4/dlamch_8f_source.html"
)
DSTERF_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d9/df2/dsterf_8f_source.html"
)


def source_bound() -> dict:
    """Bound reference-source helper work under IEEE binary64 assumptions."""
    base = dsterf_source_bound(MATRIX_ORDER, MAXIT_PER_EIGENVALUE)
    base_arithmetic = base["dsterf_source_visible_upper_flops_excluding_powers"]
    base_power_sites = base["separately_reported_non_flop_arithmetic"][
        "scalar_power_sites_max"
    ]
    base_sqrt_calls = base["separately_reported_non_flop_arithmetic"][
        "square_root_calls_upper_bound"
    ]
    # DSTERF calls DLAMCH('E'), ('S'), and ('O') once in setup. The reference
    # source computes epsilon*0.5 for each; 'S' also computes 1/huge, whose
    # IEEE binary64 result is below tiny so its adjustment branch is skipped.
    dsterf_dlamch_multiplications = 3
    dsterf_dlamch_divisions = 1

    # Each nondegenerate DLAPY2 call has one z/w divide, one 1+(z/w)**2 add,
    # one multiply by sqrt(...), one separately counted power and one sqrt.
    # Its unconditional DLAMCH('O') call adds epsilon*0.5: one multiplication.
    dlapy2_calls = MAX_DSTERF_ITERATIONS
    dlapy2_body_arithmetic_per_call = 3
    dlapy2_dlamch_multiplications_per_call = 1
    dlapy2_power_sites_per_call = 1
    dlapy2_sqrt_calls_per_call = 1

    dlapy2_body_arithmetic = dlapy2_calls * dlapy2_body_arithmetic_per_call
    dlapy2_dlamch_multiplications = (
        dlapy2_calls * dlapy2_dlamch_multiplications_per_call
    )
    total_arithmetic = (
        dsterf_dlamch_multiplications
        + dsterf_dlamch_divisions
        + dlapy2_body_arithmetic
        + dlapy2_dlamch_multiplications
    )
    power_sites = dlapy2_calls * dlapy2_power_sites_per_call
    sqrt_calls = dlapy2_calls * dlapy2_sqrt_calls_per_call

    return {
        "schema": "caissa.v212.dsterf-helper-source-bound.v01",
        "source_references": {
            "dsterf_lapack_3_12_1": DSTERF_SOURCE,
            "dlapy2_lapack_3_12_1": DLAPY2_SOURCE,
            "dlamch_lapack_3_12_1": DLAMCH_SOURCE,
        },
        "scope": (
            "reference DLAMCH setup and DLAPY2 helpers called by DSTERF; "
            "source-level conditional candidate, not linked-runtime evidence"
        ),
        "assumptions": {
            "matrix_order": MATRIX_ORDER,
            "dsterf_maxit_per_eigenvalue": MAXIT_PER_EIGENVALUE,
            "dsterf_shift_iterations_upper": MAX_DSTERF_ITERATIONS,
            "dlamch_machine_model": "IEEE 754 binary64 with gradual subnormals",
            "dlamch_safe_minimum_branch": "1/huge < tiny, so DLAMCH('S') adjustment is skipped",
            "input_to_dlapy2": "finite, non-NaN values; conservative nondegenerate arithmetic path",
        },
        "helper_calls": {
            "dsterf_direct_dlamch": {"E": 1, "S": 1, "O": 1},
            "dlapy2_calls_upper": dlapy2_calls,
            "dlamch_O_calls_from_dlapy2_upper": dlapy2_calls,
        },
        "source_arithmetic_upper": {
            "add_subtract_multiply_divide": total_arithmetic,
            "dsterf_setup_dlamch_multiplications": dsterf_dlamch_multiplications,
            "dsterf_setup_dlamch_divisions": dsterf_dlamch_divisions,
            "dlapy2_body_arithmetic": dlapy2_body_arithmetic,
            "dlapy2_dlamch_O_multiplications": dlapy2_dlamch_multiplications,
            "scalar_square_power_sites_separate": power_sites,
            "sensitivity_if_each_power_is_one_multiply": total_arithmetic + power_sites,
            "square_root_calls_separate": sqrt_calls,
        },
        "supplement_to_dsterf_iteration_bound": {
            "base_tool": "tools/v212_dsterf_iteration_bound.py",
            "base_arithmetic_flops_excluding_powers": base_arithmetic,
            "combined_partial_arithmetic_flops_excluding_powers": (
                base_arithmetic + total_arithmetic
            ),
            "base_power_sites": base_power_sites,
            "combined_power_sites": base_power_sites + power_sites,
            "combined_sensitivity_if_each_power_is_one_multiply": (
                base_arithmetic + total_arithmetic + base_power_sites + power_sites
            ),
            "base_sqrt_calls": base_sqrt_calls,
            "combined_sqrt_calls": base_sqrt_calls + sqrt_calls,
            "additive_to_base_source_scope": True,
        },
        "excluded_or_unresolved": [
            "DLASCL scaling calls and their iteration/helper arithmetic",
            "DLANST('M') scan and DLASRT sort comparison/index/memory work",
            "actual linked LAPACK/BLAS symbols, dispatch, and executed bytes",
            "compiler lowering and all comparison, branch, indexing, and memory work",
            "this DSTERF helper sub-bound has not received independent review",
        ],
        "eligibility": {
            "complete_dsterf_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(), sort_keys=True, indent=2, allow_nan=False))
