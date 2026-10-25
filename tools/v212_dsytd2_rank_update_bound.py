"""Reference-source rank-update subtotal for unblocked DSYTD2.

This counts DSYMV/DDOT/scalar/DAXPY/DSYR2 work in active DSYTD2 reflector
updates, plus DLARFG's direct scalar sites and its DSCAL vector multiplies.
DNRM2 and other helper arithmetic remain excluded; this is not a complete
DSYTRD/eigensolver bound and does not describe a loaded BLAS binary.
"""
from __future__ import annotations

import json


MATRIX_ORDER = 32


def source_bound(n: int = MATRIX_ORDER) -> dict:
    """Return a reference-BLAS source-proxy upper subtotal for DSYTD2.

    For a lower-triangle DSYTD2 update at active order ``m``, reference BLAS
    source gives DSYMV ``2*m**2 + 3*m``, DDOT ``2*m``, DAXPY ``2*m``, and
    DSYR2 at most ``2*m**2 + 4*m`` operations. The DSYTD2 scalar ALPHA
    expression contributes two multiplications. The m=1 reflector has
    TAUI=0 and skips this update, so only m=2..n-1 are included.

    DLARFG is called for the same reflector sizes. Excluding called helper
    arithmetic, the source sites have at most 21 vector multiplies per
    element (20 underflow-rescale DSCAL passes plus the final DSCAL), and
    66 direct scalar FLOPs per nontrivial call under KNT=20. DNRM2,
    DLAMCH, and DLAPY2 internals remain explicitly excluded.
    """
    if type(n) is not int or n < 3:
        raise ValueError("n must be an integer of at least three")

    per_order = []
    for m in range(2, n):
        dsymv = 2 * m * m + 3 * m
        ddot = 2 * m
        scalar_alpha = 2
        daxpy = 2 * m
        dsyr2 = 2 * m * m + 4 * m
        per_order.append({
            "active_order": m,
            "dsymv_flops": dsymv,
            "ddot_flops": ddot,
            "scalar_alpha_flops": scalar_alpha,
            "daxpy_flops": daxpy,
            "dsyr2_flops_upper": dsyr2,
            "rank_update_flops_upper": (
                dsymv + ddot + scalar_alpha + daxpy + dsyr2
            ),
        })

    rank_update_total = sum(row["rank_update_flops_upper"] for row in per_order)
    dlarfg_q_sum = sum(m - 1 for m in range(2, n))
    dlarfg_calls = max(n - 2, 0)
    dlarfg_vector_scaling_flops = 21 * dlarfg_q_sum
    dlarfg_direct_scalar_flops = 66 * dlarfg_calls
    dlarfg_partial_total = (
        dlarfg_vector_scaling_flops + dlarfg_direct_scalar_flops
    )
    total = rank_update_total + dlarfg_partial_total
    return {
        "schema": "caissa.v212.dsytd2-partial-bound.v02",
        "source_reference": (
            "https://github.com/OpenMathLib/OpenBLAS/blob/v0.3.31/"
            "lapack-netlib/SRC/dsytd2.f"
        ),
        "dlarfg_source_reference": (
            "https://github.com/OpenMathLib/OpenBLAS/blob/v0.3.31/"
            "lapack-netlib/SRC/dlarfg.f"
        ),
        "reference_blas_sources": {
            "dsymv": "https://www.netlib.org/blas/dsymv.f",
            "ddot": "https://www.netlib.org/blas/ddot.f",
            "daxpy": "https://www.netlib.org/blas/daxpy.f",
            "dsyr2": "https://www.netlib.org/blas/dsyr2.f",
            "dscal": "https://www.netlib.org/blas/dscal.f",
        },
        "scope": (
            "reference-source proxy for active unblocked DSYTD2 rank updates "
            "and DLARFG direct sites/DSCAL vector operations; unresolved helpers, "
            "DSYTRD wrapper, DSYEVD, DSTERF, and loaded runtime excluded"
        ),
        "matrix_order": n,
        "active_reflector_orders_included": [2, n - 1],
        "reference_rank_update_flops_upper": rank_update_total,
        "per_active_order": per_order,
        "dlarfg_partial_upper_excluding_helper_internals": {
            "nontrivial_calls_upper": dlarfg_calls,
            "vector_elements_per_pass": dlarfg_q_sum,
            "underflow_scaling_passes_per_call_upper": 20,
            "dscal_vector_passes_per_call_upper": 21,
            "dscal_vector_multiply_flops_upper": dlarfg_vector_scaling_flops,
            "direct_scalar_flops_per_nontrivial_call_upper": 66,
            "direct_scalar_flops_upper": dlarfg_direct_scalar_flops,
            "partial_flops_upper": dlarfg_partial_total,
        },
        "combined_partial_source_flops_excluding_unresolved_helpers": total,
        "assumptions": [
            "lower-triangle reference DSYTD2 path; upper path has the same shapes",
            "all reflector updates are active, which bounds TAUI-dependent skips",
            "DSYR2 uses its full triangular update path; zero-column skips can only lower work",
            "reference BLAS source expressions are used as a semantic proxy, not as a linked-kernel trace",
        ],
        "unresolved_or_excluded": [
            "DNRM2, DLAMCH, and DLAPY2 helper internals and non-FP behavior",
            "linked/architecture-dispatched BLAS kernels; reference BLAS formulas are a semantic proxy",
            "actual linked DSYTRD block-size selection; blocked DLATRD/DSYR2K work if that path is used",
            "DSYEVD scaling/wrapper, DSTERF (bounded separately), and other eigensolver paths",
            "actual NumPy-linked BLAS/LAPACK binary and architecture-dispatched kernels",
            "comparisons, indexing, branches, memory traffic, and compiler transformations",
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
