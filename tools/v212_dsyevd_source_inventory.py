"""Compose the conditional reference DSYEVD JOBZ='N' source inventory."""
from __future__ import annotations

import json

from .v212_dlascl_iteration_bound import (
    dsyevd_ieee_binary64_bound as dlascl_bound,
)
from .v212_dsyevd_driver_source_bound import source_bound as driver_bound
from .v212_dsyevd_helper_source_bound import source_bound as helper_bound


MATRIX_ORDER = 32
DLAMCH_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/d5/dd4/dlamch_8f_source.html"
)


def source_inventory() -> dict:
    """Return a non-overlapping DSYEVD-only arithmetic and call inventory.

    DSYTRD and DSTERF are called by the driver but remain separate routines;
    their work is not included here.
    """
    driver = driver_bound(MATRIX_ORDER)
    helpers = helper_bound()
    matrix_scale = dlascl_bound()

    driver_range = driver["covered_source_arithmetic_interval"][
        "combined_add_subtract_multiply_divide"
    ]
    helper_ops = helpers["covered_source_arithmetic_interval"][
        "combined_add_subtract_multiply_divide"
    ]["maximum"]
    scale_ops = matrix_scale["covered_source_arithmetic_interval"][
        "combined_add_subtract_multiply_divide"
    ]["maximum"]
    scale_calls = driver["source_call_inventory"]["DLASCL_calls_for_matrix_scaling"]
    # The DLASCL source bound counts its routine body but excludes its own
    # DLAMCH('S') helper. On the finite IEEE binary64 path, that call computes
    # epsilon*0.5 and 1/huge, two arithmetic operations; the adjustment branch
    # is skipped because 1/huge < tiny.
    dlascl_dlamch_ops_per_call = 2
    minimum = driver_range["minimum"] + helper_ops
    maximum = (
        driver_range["maximum"]
        + helper_ops
        + scale_ops
        + scale_calls["maximum"] * dlascl_dlamch_ops_per_call
    )

    return {
        "schema": "caissa.v212.dsyevd-source-inventory.v01",
        "reference_source_version": "LAPACK 3.12.1",
        "matrix_order": MATRIX_ORDER,
        "jobz": "N",
        "source_references": {
            "dsyevd": driver["source_references"]["dsyevd_lapack_3_12_1"],
            "dscal": driver["source_references"]["reference_dscal"],
            "dlamch": DLAMCH_SOURCE,
        },
        "non_overlapping_components": {
            "driver_direct_and_dscal": {
                "minimum": driver_range["minimum"],
                "maximum": driver_range["maximum"],
            },
            "driver_dlamch_s_and_p_plus_dlansy_m": helper_ops,
            "conditional_dlascl_body": {
                "calls": scale_calls,
                "arithmetic_upper_per_call": scale_ops,
            },
            "conditional_dlascl_dlamch_s_helper": {
                "operations_per_call": dlascl_dlamch_ops_per_call,
                "maximum_operations": (
                    scale_calls["maximum"] * dlascl_dlamch_ops_per_call
                ),
            },
        },
        "conditional_source_arithmetic_interval": {
            "add_subtract_multiply_divide": {
                "minimum": minimum,
                "maximum": maximum,
            },
            "square_root_calls": driver["separately_reported_non_flop_work"][
                "square_root_calls"
            ],
        },
        "non_flop_helper_activity": {
            "dlamch_driver_calls": helpers["path"]["dlamch_calls"],
            "dlansy_m_triangle_entries": helpers["path"][
                "dlansy_matrix_entries_scanned"
            ],
            "dlascl_matrix_scale_calls": scale_calls,
            "dlascl_dlamch_s_calls_if_scaled": 1,
            "dscal_rescale_calls": driver["source_call_inventory"][
                "DSCAL_calls_for_eigenvalue_rescaling"
            ],
            "dscal_rescale_vector_multiplications": driver[
                "source_call_inventory"
            ]["DSCAL_vector_multiplications_when_not_fast_returning"],
        },
        "excluded_or_unresolved": [
            "DSYTRD and its reflector/BLAS helper paths (separately inventoried)",
            "DSTERF and its helpers (separately inventoried)",
            "actual linked LAPACK/BLAS identity, dispatch, compiler lowering, and executed bytes",
            "DLAMCH/DLANSY/DLASCL comparisons, integer/indexing, and memory work",
            "NumPy wrapper/runtime work and full eigensolver/counter coverage",
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
    print(json.dumps(source_inventory(), sort_keys=True, indent=2, allow_nan=False))
