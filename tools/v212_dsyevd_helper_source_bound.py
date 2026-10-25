"""Conditional source bound for DLAMCH/DLANSY helpers used by reference DSYEVD.

This inventories only the reference LAPACK 3.12.1 call path for N=32,
JOBZ='N', under an IEEE binary64 machine model. It is not linked-runtime
attestation and is not a complete eigensolver count.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
TRIANGLE_ENTRIES = MATRIX_ORDER * (MATRIX_ORDER + 1) // 2
SOURCES = {
    "dsyevd": "https://www.netlib.org/lapack/explore-html/d1/da2/dsyevd_8f_source.html",
    "dlamch": "https://www.netlib.org/lapack/explore-html/d5/dd4/dlamch_8f_source.html",
    "dlansy": "https://www.netlib.org/lapack/explore-html/d1/d25/dlansy_8f_source.html",
}


def source_bound() -> dict:
    """Bound direct FP arithmetic in DSYEVD's DLAMCH and DLANSY helper calls."""
    # Reference DLAMCH computes eps=epsilon(0)*0.5 on each call. For the
    # 'S' call it also computes 1/huge; under IEEE binary64 this is below
    # tiny(0), so the safe-minimum adjustment branch is not taken. For 'P',
    # it multiplies eps by radix. The two calls therefore total 3 multiplies
    # and 1 divide under the declared source/machine model.
    dlamch_multiplications = 3
    dlamch_divisions = 1

    return {
        "schema": "caissa.v212.dsyevd-helper-source-bound.v01",
        "source_references": SOURCES,
        "conditional_assumptions": {
            "reference_lapack_version": "3.12.1",
            "machine_model": "IEEE 754 binary64 with gradual subnormals",
            "dlamch_safe_minimum_adjustment": "1/huge(0) < tiny(0), therefore skipped",
            "input_matrix": "finite; DSYEVD receives a finite 32x32 symmetric matrix",
        },
        "path": {
            "matrix_order": MATRIX_ORDER,
            "jobz": "N",
            "dlamch_calls": ["S", "P"],
            "dlansy_call": "DLANSY('M', UPLO, 32, A, LDA, WORK)",
            "dlansy_matrix_entries_scanned": TRIANGLE_ENTRIES,
        },
        "covered_source_arithmetic_interval": {
            "additions": {"minimum": 0, "maximum": 0},
            "subtractions": {"minimum": 0, "maximum": 0},
            "multiplications": {
                "minimum": dlamch_multiplications,
                "maximum": dlamch_multiplications,
            },
            "divisions": {
                "minimum": dlamch_divisions,
                "maximum": dlamch_divisions,
            },
            "combined_add_subtract_multiply_divide": {
                "minimum": dlamch_multiplications + dlamch_divisions,
                "maximum": dlamch_multiplications + dlamch_divisions,
            },
        },
        "separately_reported_non_flop_work": {
            "dlansy_abs_intrinsic_calls": TRIANGLE_ENTRIES,
            "dlansy_max_comparison_sites": TRIANGLE_ENTRIES,
            "dlansy_nan_predicate_calls": TRIANGLE_ENTRIES,
            "dlansy_indexing_and_matrix_reads": TRIANGLE_ENTRIES,
            "non_short_circuit_fortran_logical_evaluation": "implementation-sensitive and not counted as FLOPs",
        },
        "scope_and_ownership": {
            "source_arithmetic_owner": "this helper subcounter only",
            "do_not_double_count_dsyevd_driver_sites": True,
            "dlansy_add_subtract_multiply_divide": 0,
            "dlansy_is_not_the_spectrum_eigensolver": True,
        },
        "excluded_or_unresolved": [
            "actual NumPy-linked LAPACK identity, dispatch, and executed bytes",
            "compiler/runtime lowering of Fortran intrinsics and logical expressions",
            "DLASCL (reported separately), DSYTRD, its helpers, and DSTERF",
            "this conditional source bound has not received independent review",
        ],
        "eligibility": {
            "complete_dsyevd_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(), sort_keys=True, indent=2, allow_nan=False))
