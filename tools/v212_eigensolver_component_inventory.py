"""Aggregate separately owned reference-source eigensolver sub-bounds.

This is an accounting bridge across pinned source families. Its sum is not a
single-implementation total, a linked-runtime bound, or full counter coverage.
"""
from __future__ import annotations

import json

from .v212_dnrm2_reference_source_bound import source_bound as dnrm2_bound
from .v212_dlarfg_dlapy2_helper_bound import source_bound as dlarfg_helpers_bound
from .v212_dsterf_source_inventory import source_inventory as dsterf_inventory
from .v212_dsyevd_source_inventory import source_inventory as dsyevd_inventory
from .v212_dsytd2_rank_update_bound import source_bound as dsytd2_bound


MATRIX_ORDER = 32


def source_inventory() -> dict:
    """Sum only disjoint candidate-owner fields; keep conditional maxima explicit."""
    dsyevd = dsyevd_inventory()
    dsytd2 = dsytd2_bound(MATRIX_ORDER)
    dlarfg_helpers = dlarfg_helpers_bound()
    dnrm2 = dnrm2_bound(MATRIX_ORDER)
    dsterf = dsterf_inventory()

    dsyevd_interval = dsyevd["conditional_source_arithmetic_interval"][
        "add_subtract_multiply_divide"
    ]
    components = {
        "dsyevd_driver_and_conditional_scaling": {
            "minimum": dsyevd_interval["minimum"],
            "maximum": dsyevd_interval["maximum"],
            "power_sites": 0,
            "square_root_calls": dsyevd[
                "conditional_source_arithmetic_interval"
            ]["square_root_calls"]["maximum"],
            "source_family": "Netlib LAPACK 3.12.1 reference DSYEVD/DLASCL/DLAMCH and reference DSCAL",
        },
        "dsytd2_rank_updates_and_dlarfg_direct_sites": {
            "minimum": 0,
            "maximum": dsytd2["combined_partial_source_flops_excluding_unresolved_helpers"],
            "power_sites": 0,
            "square_root_calls": 0,
            "source_family": "OpenBLAS v0.3.31 DSYTD2/DLARFG source plus Netlib reference BLAS formulas",
        },
        "dlarfg_dlapy2_dlamch_helpers": {
            "minimum": 0,
            "maximum": dlarfg_helpers["covered_helper_arithmetic"][
                "combined_add_subtract_multiply_divide_upper"
            ],
            "power_sites": dlarfg_helpers["covered_helper_arithmetic"][
                "dlapy2_scalar_square_power_sites_separate"
            ],
            "square_root_calls": dlarfg_helpers["covered_helper_arithmetic"][
                "square_root_calls_upper"
            ],
            "source_family": "Netlib LAPACK 3.12.1 reference DLARFG/DLAPY2/DLAMCH",
        },
        "dlarfg_dnrm2_helper": {
            "minimum": 0,
            "maximum": dnrm2["source_arithmetic_upper"]["add_subtract_multiply_divide"],
            "power_sites": dnrm2["source_arithmetic_upper"][
                "scalar_square_power_sites_separate"
            ],
            "square_root_calls": dnrm2["source_arithmetic_upper"][
                "square_root_calls_separate"
            ],
            "source_family": "Netlib LAPACK 3.12.1 reference DNRM2 source; alternative to the binary-kernel candidate",
        },
        "dsterf_and_separately_owned_helpers": {
            "minimum": 0,
            "maximum": dsterf["conditional_source_arithmetic_candidate"][
                "add_subtract_multiply_divide_upper"
            ],
            "power_sites": dsterf["conditional_source_arithmetic_candidate"][
                "scalar_power_sites_separate"
            ],
            "square_root_calls": dsterf["conditional_source_arithmetic_candidate"][
                "square_root_calls_separate"
            ],
            "source_family": "OpenBLAS v0.3.31 DSTERF/DLAE2 source plus Netlib LAPACK 3.12.1 helper sources",
        },
    }

    component_sum_upper = sum(row["maximum"] for row in components.values())
    power_sites_upper = sum(row["power_sites"] for row in components.values())
    square_roots_upper = sum(row["square_root_calls"] for row in components.values())
    return {
        "schema": "caissa.v212.eigensolver-component-inventory.v01",
        "matrix_order": MATRIX_ORDER,
        "covered_reference_source_components": components,
        "sum_of_component_maxima": {
            "add_subtract_multiply_divide": component_sum_upper,
            "power_sites_separate": power_sites_upper,
            "sensitivity_if_each_power_maps_to_one_multiply": (
                component_sum_upper + power_sites_upper
            ),
            "square_root_calls_separate": square_roots_upper,
            "interpretation": (
                "Conservative sum of heterogeneous, conditional source-component maxima; "
                "component maxima may not be jointly attainable. This is only the sum "
                "of currently covered candidate source work."
            ),
        },
        "provenance_caveat": (
            "The components mix OpenBLAS v0.3.31 LAPACK-derived sources, Netlib LAPACK "
            "3.12.1 reference sources, and Netlib reference-BLAS formulas. Exact source "
            "identity across the assembled path and loaded-runtime identity are not established."
        ),
        "excluded_or_unresolved": [
            "uncovered comparison, integer/control, indexing, conversion, and memory work",
            "actual NumPy-linked LAPACK/BLAS identity, dispatch, compiler lowering, and executed bytes",
            "NumPy wrapper/runtime work and exact invocation-path reconciliation",
            "architecture-specific DNRM2 binary candidate (alternative, not additive to reference DNRM2)",
            "any work outside the listed source owners; this is not a full eigensolver or counter bound",
        ],
        "eligibility": {
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "graph_freeze": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_inventory(), sort_keys=True, indent=2, allow_nan=False))
