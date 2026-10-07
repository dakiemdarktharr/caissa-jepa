"""Source-cardinality bounds for DSTERF's DLANST and DLASRT helper calls.

This reports scan, absolute-value, comparison-site, and sort-call bounds in
their native non-FLOP units. It deliberately does not estimate elapsed time,
linked-library work, or a complete eigensolver counter.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
DLANST_SOURCE = (
    "https://netlib.org/lapack/explore-html/d0/d90/dlanst_8f_source.html"
)
DLASRT_SOURCE = (
    "https://netlib.org/lapack/explore-html/df/ddf/dlasrt_8f_source.html"
)
DSTERF_SOURCE = (
    "https://netlib.org/lapack/explore-html/d9/df2/dsterf_8f_source.html"
)


def source_bound(n: int = MATRIX_ORDER) -> dict:
    """Return conservative call and source-site cardinalities at order ``n``."""
    if type(n) is not int or n < 2:
        raise ValueError("n must be an integer greater than one")

    # DSTERF's active blocks are disjoint, have order >= 2, and singleton
    # blocks bypass DLANST. For B active blocks, sum(k)=K<=n and
    # sum(k-1)=K-B. The maximum scan totals occur with one active block.
    active_blocks = n // 2
    dlanst_calls = active_blocks
    diagonal_abs_values = n
    offdiagonal_abs_values = n - 1
    dlanst_loop_iterations = n - 1
    dlanst_relational_comparison_sites = 2 * (n - 1)
    dlanst_disnan_call_sites = 2 * (n - 1)

    # On successful DSTERF completion, the source calls DLASRT once on all N
    # diagonal/eigenvalue entries. DLASRT is quicksort with insertion sort for
    # partitions of length <= 21. We bound the call and input size only; the
    # value-dependent comparison/partition workload is not assigned a bound.
    return {
        "schema": "caissa.v212.dsterf-scan-sort-source-bound.v01",
        "source_references": {
            "dsterf_lapack_3_12_1": DSTERF_SOURCE,
            "dlanst_lapack_3_12_1": DLANST_SOURCE,
            "dlasrt_lapack_3_12_1": DLASRT_SOURCE,
        },
        "assumptions": {
            "matrix_order": n,
            "reference_source_version": "LAPACK 3.12.1",
            "active_dsterf_blocks": "disjoint, each of order at least two",
            "dlanst_call_condition": "DSTERF skips singleton blocks",
            "dlasrt_call_condition": "one call only on successful DSTERF completion",
        },
        "dlanst_norm_m_cardinality_upper": {
            "calls": dlanst_calls,
            "diagonal_abs_evaluations": diagonal_abs_values,
            "offdiagonal_abs_evaluations": offdiagonal_abs_values,
            "total_abs_evaluations": diagonal_abs_values + offdiagonal_abs_values,
            "loop_iterations": dlanst_loop_iterations,
            "relational_comparison_sites": dlanst_relational_comparison_sites,
            "disnan_call_sites": dlanst_disnan_call_sites,
            "add_subtract_multiply_divide_operations": 0,
            "maxima_note": (
                "call count is maximized by 16 order-2 blocks, while the "
                "aggregate scan maxima are maximized by one order-32 block"
            ),
        },
        "dlasrt_increasing_cardinality_upper": {
            "successful_path_calls": 1,
            "input_elements_per_call": n,
            "quicksort_partition_threshold_parameter": 20,
            "insertion_sort_partition_max_length": 21,
            "comparison_and_partition_work": "not derived; value-dependent path",
            "add_subtract_multiply_divide_operations": 0,
        },
        "exclusions": [
            "compiler-specific .OR. evaluation and DISNAN implementation cost",
            "DLASRT comparison, index, branch, swap, and memory-operation totals",
            "other DSTERF arithmetic and helpers",
            "actual linked LAPACK identity, dispatch, and runtime behavior",
            "complete eigensolver or six-arm counter coverage",
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
