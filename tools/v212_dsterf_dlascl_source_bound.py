"""Conditional DLASCL source bound for DSTERF's tridiagonal scaling path."""
from __future__ import annotations

import json

from .v212_dsterf_helper_source_bound import source_bound as dsterf_helper_bound


MATRIX_ORDER = 32
MAX_ACTIVE_BLOCKS = MATRIX_ORDER // 2

DSTERF_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d9/df2/dsterf_8f_source.html"
)
DLASCL_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "de/d3c/dlascl_8f_source.html"
)
DLAMCH_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d5/dd4/dlamch_8f_source.html"
)


def source_bound() -> dict:
    """Bound DSTERF scaling arithmetic for finite N=32 tridiagonal blocks.

    Every scaled block has order at least two. DSTERF makes two input scaling
    calls (D and E) and one restore call (D). Under the declared binary64
    assumptions all three DLASCL ratios fit its one-pass range.
    """
    blocks = MAX_ACTIVE_BLOCKS
    dlascl_calls_per_block = 3
    dlascl_calls = blocks * dlascl_calls_per_block

    # The largest total vector length occurs when all 32 entries belong to
    # active blocks: D is scaled twice, while E is scaled once and has one
    # fewer element than each block. For B blocks, total elements = 3N-B.
    scaled_vector_elements = 3 * MATRIX_ORDER - blocks
    # For one DLASCL call with one scaling pass, the general Mx1 path costs M
    # element multiplications, two scalar pass operations, one ratio divide,
    # and one per-call reciprocal divide: M+4. Its DLAMCH('S') helper adds
    # epsilon*0.5 and 1/huge under binary64: two more arithmetic operations.
    dlascl_scalar_ops_per_call = 4
    dlascl_dlamch_s_ops_per_call = 2
    dlascl_arithmetic = scaled_vector_elements + dlascl_calls * (
        dlascl_scalar_ops_per_call + dlascl_dlamch_s_ops_per_call
    )

    prior = dsterf_helper_bound()["supplement_to_dsterf_iteration_bound"]
    combined_arithmetic = (
        prior["combined_partial_arithmetic_flops_excluding_powers"]
        + dlascl_arithmetic
    )
    combined_power_sites = prior["combined_power_sites"]
    combined_sqrt_calls = prior["combined_sqrt_calls"]

    return {
        "schema": "caissa.v212.dsterf-dlascl-source-bound.v01",
        "source_references": {
            "dsterf_lapack_3_12_1": DSTERF_SOURCE,
            "dlascl_lapack_3_12_1": DLASCL_SOURCE,
            "dlamch_lapack_3_12_1": DLAMCH_SOURCE,
        },
        "conditional_assumptions": {
            "matrix_order": MATRIX_ORDER,
            "machine_model": "IEEE 754 binary64 with gradual subnormals",
            "dsterf_diagonal_and_subdiagonal": "finite; active block norm is positive",
            "dsterf_maximum_active_blocks": blocks,
            "active_block_order": "at least two; singleton blocks skip DLANST and scaling",
            "dlascl_iteration_derivation": (
                "DSTERF's ssfmax/safmax and ssfmin/eps2 targets keep both input "
                "and restore scale ratios within the DLASCL smlnum..bignum range"
            ),
            "ratio_envelopes": {
                "large_norm_branch": "each input/restore ratio lies between 1 and <2**515 in magnitude",
                "small_norm_branch": "each input/restore ratio lies between 1 and <2**669 in magnitude",
                "dlascl_ieee64_safe_ratio_interval": "[2**-970, 2**970]",
            },
        },
        "path_upper_bounds": {
            "scaled_blocks": blocks,
            "dlascl_calls_per_scaled_block": {
                "input_scale_D": 1,
                "input_scale_E": 1,
                "restore_scale_D": 1,
            },
            "dlascl_calls": dlascl_calls,
            "iterations_per_call": 1,
            "scaled_vector_elements_across_calls": scaled_vector_elements,
            "note": "marginal maxima are conservative and need not occur on the same input except where the aggregate formula states otherwise",
        },
        "source_arithmetic_upper": {
            "dlascl_element_multiplications": scaled_vector_elements,
            "dlascl_scalar_operations_per_call": dlascl_scalar_ops_per_call,
            "dlascl_call_scalar_operations": dlascl_calls * dlascl_scalar_ops_per_call,
            "dlamch_S_helper_operations": dlascl_calls * dlascl_dlamch_s_ops_per_call,
            "add_subtract_multiply_divide": dlascl_arithmetic,
            "scalar_power_sites_separate": 0,
            "square_root_calls_separate": 0,
        },
        "combined_partial_dsterf_candidate": {
            "base_scope": "DSTERF iteration + DLAE2 + conditional DLAMCH/DLAPY2 supplement",
            "combined_arithmetic_flops_excluding_powers": combined_arithmetic,
            "combined_power_sites": combined_power_sites,
            "sensitivity_if_each_power_is_one_multiply": combined_arithmetic + combined_power_sites,
            "combined_sqrt_calls": combined_sqrt_calls,
            "warning": "partial reference-source candidate; not actual linked/runtime work",
        },
        "excluded_or_unresolved": [
            "whether the future linked LAPACK follows these sources and machine assumptions",
            "DLANST norm-scan and DLASRT sort comparison/index/memory work",
            "all non-FLOP work, runtime dispatch, compiler lowering, and executed-byte identity",
            "this DLASCL path derivation has not received independent review",
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
