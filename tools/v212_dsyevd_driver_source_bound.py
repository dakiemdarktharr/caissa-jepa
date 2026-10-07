"""Partial source-site bound for reference DSYEVD's eigenvalues-only path.

This covers DSYEVD's visible scalar arithmetic and the reference DSCAL vector
multiply called when the matrix is rescaled. It does not count helper bodies
or represent the NumPy-linked LAPACK runtime.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
DSYEVD_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d1/da2/dsyevd_8f_source.html"
)
DSCAL_SOURCE = "https://www.netlib.org/blas/dscal.f"


def source_bound(n: int = MATRIX_ORDER) -> dict:
    """Return source-visible driver arithmetic for the fixed N=32 JOBZ='N' path."""
    if type(n) is not int or n != MATRIX_ORDER:
        raise ValueError("this bound is pinned to matrix order 32")

    # DSYEVD computes smlnum=safmin/eps and bignum=1/smlnum, then
    # rmin=sqrt(smlnum), rmax=sqrt(bignum). When scaling, it additionally
    # computes sigma and later 1/sigma before calling DSCAL on W.
    base_divisions = 2
    conditional_scale_divisions = 2
    rescale_vector_multiplications_upper = n
    return {
        "schema": "caissa.v212.dsyevd-driver-source-bound.v01",
        "source_references": {
            "dsyevd_lapack_3_12_1": DSYEVD_SOURCE,
            "reference_dscal": DSCAL_SOURCE,
        },
        "path": {
            "matrix_order": n,
            "jobz": "N",
            "eigenvectors_computed": False,
            "dsyevd_calls_dsyevd_route": ["DSYTRD", "DSTERF"],
            "matrix_scaling_condition": "0 < anrm < rmin or anrm > rmax",
        },
        "scope": (
            "DSYEVD source-visible add/subtract/multiply/divide sites plus "
            "reference DSCAL vector multiplications on the N=32 eigenvalues-only path"
        ),
        "covered_source_arithmetic_interval": {
            "additions": {"minimum": 0, "maximum": 0},
            "subtractions": {"minimum": 0, "maximum": 0},
            "multiplications": {
                "minimum": 0,
                "maximum": rescale_vector_multiplications_upper,
            },
            "divisions": {
                "minimum": base_divisions,
                "maximum": base_divisions + conditional_scale_divisions,
            },
            "combined_add_subtract_multiply_divide": {
                "minimum": base_divisions,
                "maximum": (
                    base_divisions
                    + conditional_scale_divisions
                    + rescale_vector_multiplications_upper
                ),
            },
        },
        "separately_reported_non_flop_work": {
            "square_root_calls": {"minimum": 2, "maximum": 2},
            "integer_workspace_and_index_arithmetic": "excluded",
            "comparisons_and_branches": "excluded",
        },
        "source_call_inventory": {
            "DLAMCH_calls": 2,
            "DLANSY_calls": 1,
            "DLASCL_calls_for_matrix_scaling": {"minimum": 0, "maximum": 1},
            "DSYTRD_calls": 1,
            "DSTERF_calls_for_JOBZ_N": 1,
            "DSCAL_calls_for_eigenvalue_rescaling": {
                "minimum": 0,
                "maximum": 1,
            },
            "DSCAL_vector_multiplications_when_not_fast_returning": n,
        },
        "excluded_or_unresolved": [
            "DLAMCH, DLANSY, and DLASCL helper arithmetic and non-FP work",
            "DSYTRD, its reflector helpers, and DSTERF internals (separate partial tools exist)",
            "NumPy wrapper, actual linked-library dispatch, and execution-byte identity",
            "comparisons, indexing, integer operations, memory work, and compiler transformations",
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
