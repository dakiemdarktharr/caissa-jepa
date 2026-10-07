"""Conditional DLARFG/DLAPY2 helper arithmetic bound for the V2.12 N=32 path.

Counts only the reference-source helper bodies and their DLAMCH calls. The
existing DSYTD2 partial tool owns DLARFG's direct scalar sites and DSCAL vector
operations; DNRM2 remains a separate conditional binary/source sub-bound.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
DLARFG_CALLS = MATRIX_ORDER - 2
DLAPY2_CALLS_PER_DLARFG_UPPER = 2
SOURCES = {
    "dlarfg_lapack_3_12_1": "https://www.netlib.org/lapack/explore-html/d7/da9/dlarfg_8f_source.html",
    "dlapy2_lapack_3_12_1": "https://www.netlib.org/lapack/explore-html/d5/d7c/dlapy2_8f_source.html",
    "dlamch_lapack_3_12_1": "https://www.netlib.org/lapack/explore-html/d5/dd4/dlamch_8f_source.html",
}


def source_bound(
    dlarfg_calls: int = DLARFG_CALLS,
    dlapy2_calls_per_dlarfg: int = DLAPY2_CALLS_PER_DLARFG_UPPER,
) -> dict:
    """Return helper-only counts under explicit IEEE binary64 assumptions."""
    for name, value in (
        ("dlarfg_calls", dlarfg_calls),
        ("dlapy2_calls_per_dlarfg", dlapy2_calls_per_dlarfg),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")

    # DLAPY2 source has one z/w divide, one 1+(z/w)**2 addition, and one
    # multiplication by sqrt(...). The scalar square is a separate power site.
    dlapy2_body_flops_per_call = 3
    scalar_square_power_sites_per_call = 1
    square_root_calls_per_call = 1
    # Every DLAPY2 invocation calls DLAMCH('O'), whose rounded IEEE reference
    # path computes epsilon(zero)*0.5, one multiplication.
    dlamch_overflow_flops_per_call = 1
    # DLARFG itself calls DLAMCH('S') and ('E') once each on the nontrivial
    # path. Under IEEE binary64: 'S' computes eps*0.5 and 1/huge (2 ops),
    # 'E' computes eps*0.5 (1 op). The direct S/E ratio at the call site is
    # owned by the existing DLARFG direct-site inventory, not counted here.
    dlamch_s_and_e_flops_per_dlarfg = 3

    dlapy2_calls = dlarfg_calls * dlapy2_calls_per_dlarfg
    body_total = dlapy2_calls * dlapy2_body_flops_per_call
    dlapy2_dlamch_total = dlapy2_calls * dlamch_overflow_flops_per_call
    dlarfg_dlamch_total = dlarfg_calls * dlamch_s_and_e_flops_per_dlarfg
    total = body_total + dlapy2_dlamch_total + dlarfg_dlamch_total
    power_sites = dlapy2_calls * scalar_square_power_sites_per_call
    return {
        "schema": "caissa.v212.dlarfg-dlapy2-helper-bound.v01",
        "source_references": SOURCES,
        "conditional_assumptions": {
            "machine_model": "IEEE 754 binary64 with gradual subnormals and round-to-nearest",
            "source_path": "reference LAPACK 3.12.1 DLARFG, DLAPY2, and DLAMCH",
            "inputs": "finite DLARFG alpha/xnorm; no NaN helper path",
        },
        "path": {
            "matrix_order": MATRIX_ORDER,
            "nontrivial_dlarfg_calls_upper": dlarfg_calls,
            "dlapy2_calls_per_dlarfg_upper": dlapy2_calls_per_dlarfg,
            "dlapy2_calls_upper": dlapy2_calls,
            "why_at_most_two_dlapy2_calls": "initial beta, plus one recomputation after the bounded underflow-rescaling loop",
        },
        "covered_helper_arithmetic": {
            "dlapy2_body_flops_per_call": dlapy2_body_flops_per_call,
            "dlapy2_body_flops_upper": body_total,
            "dlamch_overflow_flops_per_dlapy2_call": dlamch_overflow_flops_per_call,
            "dlamch_overflow_flops_upper": dlapy2_dlamch_total,
            "dlarfg_dlamch_s_and_e_flops_per_call": dlamch_s_and_e_flops_per_dlarfg,
            "dlarfg_dlamch_s_and_e_flops_upper": dlarfg_dlamch_total,
            "combined_add_subtract_multiply_divide_upper": total,
            "dlapy2_scalar_square_power_sites_separate": power_sites,
            "sensitivity_if_each_scalar_square_is_one_multiply": total + power_sites,
            "square_root_calls_upper": dlapy2_calls * square_root_calls_per_call,
        },
        "ownership": {
            "additional_to_dsytd2_partial_source_bound": True,
            "dlarfg_direct_scalar_sites": "owned by v212_dsytd2_rank_update_bound.py; do not add here",
            "dscal_vector_multiplications": "owned by v212_dsytd2_rank_update_bound.py; do not add here",
            "dnrm2": "separate and unresolved from the reference-source subtotal",
        },
        "excluded_or_unresolved": [
            "actual linked LAPACK/DLAMCH source, compiler lowering, and loaded-runtime identity",
            "DNRM2 helper body and architecture dispatch",
            "DLAPY2/DLAMCH comparisons, NaN predicates, branches, memory work, and intrinsics outside the FLOP convention",
            "this helper sub-bound has not received independent review",
        ],
        "eligibility": {
            "complete_dsytd2_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(), sort_keys=True, indent=2, allow_nan=False))
