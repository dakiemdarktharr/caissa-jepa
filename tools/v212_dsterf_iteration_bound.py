"""Conservative DSTERF loop-arithmetic bound for the V2.12 32x32 spectrum.

This covers source-visible floating add/subtract/multiply/divide sites in the
reference OpenBLAS 0.3.31 DSTERF iteration and scans, plus a separate bound
for its DLAE2 helper calls. It deliberately excludes DSYEVD/DSYTRD and other
helper implementations, so it is not a complete eigensolver bound or runtime
counter.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32
MAXIT_PER_EIGENVALUE = 30
MAX_ITERATIONS = MATRIX_ORDER * MAXIT_PER_EIGENVALUE


def source_bound(n: int = MATRIX_ORDER, maxit: int = MAXIT_PER_EIGENVALUE) -> dict:
    """Bound non-scaling DSTERF-path arithmetic plus separately counted DLAE2.

    DSTERF's QL and QR inner-loop bodies each have at most 12 add/subtract/
    multiply/divide operations per element. The optional ``C == 0`` path uses
    one multiply, while the other path uses one multiply and one division, so
    the latter is the conservative choice. The shift setup costs eight such
    operations and the two post-loop assignments cost two. Each shifted
    iteration can also perform up to ``n - 1`` convergence checks, with two
    multiplications per check. Initial block-split scans advance past the
    previous split, so across all blocks they inspect at most ``n - 1``
    subdiagonal entries total.
    """
    if type(n) is not int or n < 2:
        raise ValueError("n must be an integer greater than one")
    if type(maxit) is not int or maxit <= 0:
        raise ValueError("maxit must be a positive integer")

    iterations = n * maxit
    inner_loop_length = n - 1
    inner_body_ops = 12
    shift_setup_ops = 8
    post_loop_ops = 2
    convergence_check_multiplies = 2
    initial_block_scan_checks = n - 1
    initial_block_scan_multiplies = (
        initial_block_scan_checks * convergence_check_multiplies
    )
    eigenvalue_completion_search_checks = n * (n - 1)
    eigenvalue_completion_search_multiplies = (
        eigenvalue_completion_search_checks * convergence_check_multiplies
    )
    max_e_squared_power_sites = n - 1
    setup_divisions = 3
    dlae2_max_calls = n // 2
    dlae2_ops_per_call = 13
    dlae2_max_flops = dlae2_max_calls * dlae2_ops_per_call
    dsterf_setup_and_noniterative_flops = (
        initial_block_scan_multiplies
        + eigenvalue_completion_search_multiplies
        + setup_divisions
        + dlae2_max_flops
    )
    per_iteration_inner_flops = inner_loop_length * inner_body_ops
    per_iteration_convergence_scan_flops = (
        inner_loop_length * convergence_check_multiplies
    )
    per_iteration_flops = (
        shift_setup_ops
        + post_loop_ops
        + per_iteration_inner_flops
        + per_iteration_convergence_scan_flops
    )
    iterative_flops = iterations * per_iteration_flops

    return {
        "schema": "caissa.v212.dsterf-iteration-bound.v01",
        "source_reference": (
            "https://github.com/OpenMathLib/OpenBLAS/blob/v0.3.31/"
            "lapack-netlib/SRC/dsterf.f"
        ),
        "dlae2_source_reference": (
            "https://github.com/OpenMathLib/OpenBLAS/blob/v0.3.31/"
            "lapack-netlib/SRC/dlae2.f"
        ),
        "scope": (
            "source-visible DSTERF add/subtract/multiply/divide upper bound "
            "plus separately bounded DLAE2 calls; excludes other helpers and "
            "the surrounding eigensolver"
        ),
        "matrix_order": n,
        "maxit_per_eigenvalue": maxit,
        "max_iterations": iterations,
        "per_iteration": {
            "maximum_inner_loop_length": inner_loop_length,
            "inner_loop_body_flops_per_element": inner_body_ops,
            "shift_setup_flops": shift_setup_ops,
            "post_loop_flops": post_loop_ops,
            "convergence_scan_multiplications_per_element": (
                convergence_check_multiplies
            ),
            "inner_loop_flops": per_iteration_inner_flops,
            "convergence_scan_flops": per_iteration_convergence_scan_flops,
            "upper_flops": per_iteration_flops,
        },
        "noniterative_upper_bound": {
            "initial_block_split_checks": initial_block_scan_checks,
            "initial_block_split_flops": initial_block_scan_multiplies,
            "eigenvalue_completion_search_checks": eigenvalue_completion_search_checks,
            "eigenvalue_completion_search_flops": eigenvalue_completion_search_multiplies,
            "subdiagonal_scalar_power_sites": max_e_squared_power_sites,
            "setup_divisions": setup_divisions,
            "dlae2_max_calls": dlae2_max_calls,
            "dlae2_flops_per_call_upper_bound": dlae2_ops_per_call,
            "dlae2_flops_upper_bound": dlae2_max_flops,
            "upper_flops": dsterf_setup_and_noniterative_flops,
        },
        "dsterf_source_visible_upper_flops_excluding_powers": (
            iterative_flops + dsterf_setup_and_noniterative_flops
        ),
        "dsterf_source_visible_upper_if_each_power_maps_to_multiply": (
            iterative_flops + dsterf_setup_and_noniterative_flops
            + 1 + dlae2_max_calls + max_e_squared_power_sites
        ),
        "separately_reported_non_flop_arithmetic": {
            "scalar_power_sites_max": (
                1 + dlae2_max_calls + max_e_squared_power_sites
            ),
            "square_root_calls_upper_bound": (
                iterations + 2 * dlae2_max_calls
                + 2 * initial_block_scan_checks + 2
            ),
            "dlapy2_calls_upper_bound": iterations,
            "comparisons_and_branches": "not converted to FLOPs",
        },
        "excluded_helpers_and_paths": [
            "DSYEVD argument/setup/scaling/rescaling and NumPy wrapper",
            "DSYTRD blocked/unblocked reduction and its DSYTD2/DLATRD/DSYR2K paths",
            "DLASCL scaling and DLANST norm scan inside DSTERF",
            "DLAMCH and DLAPY2 helper arithmetic/transcendentals",
            "DLASRT sorting and all integer/indexing/control-flow work",
            "actual linked OpenBLAS build identity in a future D03 profile",
        ],
        "eligibility": {
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(source_bound(), sort_keys=True, indent=2, allow_nan=False))
