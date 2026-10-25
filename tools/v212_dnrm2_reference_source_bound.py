"""Reference DNRM2 source-operation bound for DLARFG's N=32 call shapes.

This covers Netlib LAPACK 3.12.1's three-accumulator BLAS DNRM2 source only.
It is a semantic source bound, not an architecture-dispatched kernel trace.
Scalar ``**2`` sites and square-root calls are reported separately.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
MAX_CALLS_PER_REFLECTOR = 2
DNRM2_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d6/de0/dnrm2_8f90_source.html"
)
DLARFG_SOURCE = (
    "https://www.netlib.org/lapack/explore-html/"
    "d7/da9/dlarfg_8f_source.html"
)


def _one_call_upper(length: int) -> tuple[int, int, int]:
    """Return (add/sub/mul/div, scalar powers, square roots) upper bounds."""
    if length == 1:
        # One element can enter only one scaling class. The maximum is the
        # small/large accumulation multiply+add, one scale division, and the
        # final scale multiply; all paths use the final square root.
        return 4, 1, 1
    # At most two add/multiply arithmetic sites per vector element, plus five
    # combine/scale operations. One element power is possible per input; the
    # small+mid accumulator combine adds two more scalar powers. In that
    # combine path the final and two intermediate square-root calls execute.
    return 2 * length + 5, length + 2, 3


def source_bound(n: int = MATRIX_ORDER, calls_per_reflector: int = MAX_CALLS_PER_REFLECTOR) -> dict:
    """Return source bounds for reflectors m=2..N-1 and DNRM2 lengths 1..N-2."""
    if type(n) is not int or n != MATRIX_ORDER:
        raise ValueError("this inventory is pinned to DLARFG order 32")
    if type(calls_per_reflector) is not int or calls_per_reflector < 0:
        raise ValueError("calls_per_reflector must be a nonnegative integer")

    by_reflector = []
    for reflector_order in range(2, n):
        length = reflector_order - 1
        one_call = _one_call_upper(length)
        by_reflector.append({
            "reflector_order": reflector_order,
            "dnrm2_vector_length": length,
            "calls_upper": calls_per_reflector,
            "arithmetic_flops_upper": calls_per_reflector * one_call[0],
            "scalar_square_power_sites_upper": calls_per_reflector * one_call[1],
            "square_root_calls_upper": calls_per_reflector * one_call[2],
            "one_call_upper": {
                "arithmetic_flops": one_call[0],
                "scalar_square_power_sites": one_call[1],
                "square_root_calls": one_call[2],
            },
        })

    total_arithmetic = sum(row["arithmetic_flops_upper"] for row in by_reflector)
    total_powers = sum(row["scalar_square_power_sites_upper"] for row in by_reflector)
    total_sqrts = sum(row["square_root_calls_upper"] for row in by_reflector)
    return {
        "schema": "caissa.v212.dnrm2-reference-source-bound.v01",
        "source_references": {
            "dnrm2_lapack_3_12_1": DNRM2_SOURCE,
            "dlarfg_lapack_3_12_1": DLARFG_SOURCE,
        },
        "scope": "three-accumulator reference DNRM2; source-level upper bound for DLARFG call shapes",
        "assumptions": {
            "matrix_order": n,
            "reflector_orders": [2, n - 1],
            "dnrm2_vector_lengths": [1, n - 2],
            "incx": 1,
            "calls_per_reflector_upper": calls_per_reflector,
            "machine_specific_dispatch": "not modeled; this is not a loaded-kernel trace",
        },
        "per_reflector": by_reflector,
        "source_arithmetic_upper": {
            "add_subtract_multiply_divide": total_arithmetic,
            "scalar_square_power_sites_separate": total_powers,
            "sensitivity_if_each_power_is_one_multiply": total_arithmetic + total_powers,
            "square_root_calls_separate": total_sqrts,
        },
        "call_shape_summary": {
            "total_calls_upper": calls_per_reflector * (n - 2),
            "length_one_calls_upper": calls_per_reflector,
            "length_greater_than_one_calls_upper": calls_per_reflector * (n - 3),
            "reference_length_one_fast_return": False,
            "length_one_note": "the reference source still executes one accumulation and the final sqrt/scale path",
        },
        "separate_from_binary_candidate": {
            "binary_candidate_tool": "tools/v212_openblas_dnrm2_binary_bound.py",
            "additive": False,
            "reason": "source-level reference and architecture-specific disassembly are alternative implementation accounts, not components to sum",
        },
        "excluded_or_unresolved": [
            "actual linked BLAS symbol, architecture dispatch, and executed bytes",
            "comparisons, branches, absolute-value intrinsics, indexing, and memory operations",
            "compiler transformations and whether scalar powers lower to multiplies",
            "this source candidate has not received independent review",
        ],
        "eligibility": {
            "complete_dlarfg_bound": False,
            "complete_dsytrd_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(), sort_keys=True, indent=2, allow_nan=False))
