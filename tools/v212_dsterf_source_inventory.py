"""Composition report for the partial LAPACK reference DSTERF inventory."""
from __future__ import annotations

import json

from .v212_dsterf_dlascl_source_bound import source_bound as dlascl_bound
from .v212_dsterf_helper_source_bound import source_bound as helper_bound
from .v212_dsterf_iteration_bound import source_bound as iteration_bound
from .v212_dsterf_scan_sort_source_bound import source_bound as scan_sort_bound


MATRIX_ORDER = 32
MAXIT_PER_EIGENVALUE = 30


def source_inventory() -> dict:
    """Compose non-overlapping reference-source DSTERF sub-inventories.

    The result is conditional source accounting, not a complete runtime or
    eigensolver counter. Non-FLOP work remains in native units.
    """
    iteration = iteration_bound(MATRIX_ORDER, MAXIT_PER_EIGENVALUE)
    helpers = helper_bound()
    scaling = dlascl_bound()
    scans_sorts = scan_sort_bound(MATRIX_ORDER)

    iteration_arithmetic = iteration[
        "dsterf_source_visible_upper_flops_excluding_powers"
    ]
    helper_arithmetic = helpers["source_arithmetic_upper"][
        "add_subtract_multiply_divide"
    ]
    scale_arithmetic = scaling["source_arithmetic_upper"][
        "add_subtract_multiply_divide"
    ]
    arithmetic_total = (
        iteration_arithmetic + helper_arithmetic + scale_arithmetic
    )

    iteration_nonflop = iteration["separately_reported_non_flop_arithmetic"]
    helper_nonflop = helpers["source_arithmetic_upper"]
    dlanst = scans_sorts["dlanst_norm_m_cardinality_upper"]
    dlasrt = scans_sorts["dlasrt_increasing_cardinality_upper"]
    power_sites = (
        iteration_nonflop["scalar_power_sites_max"]
        + helper_nonflop["scalar_square_power_sites_separate"]
    )
    sqrt_calls = (
        iteration_nonflop["square_root_calls_upper_bound"]
        + helper_nonflop["square_root_calls_separate"]
    )

    return {
        "schema": "caissa.v212.dsterf-source-inventory.v01",
        "reference_source_version": "LAPACK 3.12.1",
        "matrix_order": MATRIX_ORDER,
        "iteration_cap": MATRIX_ORDER * MAXIT_PER_EIGENVALUE,
        "non_overlapping_source_components": {
            "dsterf_direct_plus_dlae2_arithmetic": iteration_arithmetic,
            "setup_dlamch_plus_dlapy2_arithmetic": helper_arithmetic,
            "dlascl_plus_per_call_dlamch_arithmetic": scale_arithmetic,
            "dlanst_norm_m_arithmetic": dlanst[
                "add_subtract_multiply_divide_operations"
            ],
            "dlasrt_arithmetic": dlasrt[
                "add_subtract_multiply_divide_operations"
            ],
        },
        "conditional_source_arithmetic_candidate": {
            "add_subtract_multiply_divide_upper": arithmetic_total,
            "scalar_power_sites_separate": power_sites,
            "sensitivity_if_each_power_maps_to_one_multiply": (
                arithmetic_total + power_sites
            ),
            "square_root_calls_separate": sqrt_calls,
        },
        "non_flop_source_activity": {
            "dlanst_calls_upper": dlanst["calls"],
            "dlanst_abs_evaluations_upper": dlanst["total_abs_evaluations"],
            "dlanst_relational_comparison_sites_upper": dlanst[
                "relational_comparison_sites"
            ],
            "dlanst_disnan_call_sites_upper": dlanst["disnan_call_sites"],
            "dlasrt_success_path_calls": dlasrt["successful_path_calls"],
            "dlasrt_input_elements": dlasrt["input_elements_per_call"],
            "dlasrt_array_value_comparisons_upper": dlasrt[
                "data_comparisons_upper"
            ],
            "dlasrt_partition_i_lt_j_integer_checks_upper": dlasrt[
                "quicksort_i_lt_j_integer_comparisons_upper"
            ],
        },
        "excluded_or_unresolved": [
            "actual linked LAPACK identity, dispatch, compiler lowering, and executed bytes",
            "DISNAN implementation and compiler-specific logical evaluation",
            "DLASRT integer/control comparisons beyond the reported i<j checks, indexing, swaps, and memory operations",
            "all DSYEVD/DSYTRD work and NumPy wrapper/runtime operations",
            "complete six-arm counter, parity, and training/profile eligibility",
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
    print(json.dumps(source_inventory(), sort_keys=True, indent=2, allow_nan=False))
