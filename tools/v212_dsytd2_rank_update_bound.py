"""Reference-source rank-update subtotal for unblocked DSYTD2.

This counts only the DSYMV/DDOT/scalar/DAXPY/DSYR2 work in the active
DSYTD2 reflector updates. DLARFG and all of its helpers are excluded; this is
not a DSYTRD or eigensolver bound and does not describe a loaded BLAS binary.
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

    total = sum(row["rank_update_flops_upper"] for row in per_order)
    return {
        "schema": "caissa.v212.dsytd2-rank-update-bound.v01",
        "source_reference": (
            "https://github.com/OpenMathLib/OpenBLAS/blob/v0.3.31/"
            "lapack-netlib/SRC/dsytd2.f"
        ),
        "reference_blas_sources": {
            "dsymv": "https://www.netlib.org/blas/dsymv.f",
            "ddot": "https://www.netlib.org/blas/ddot.f",
            "daxpy": "https://www.netlib.org/blas/daxpy.f",
            "dsyr2": "https://www.netlib.org/blas/dsyr2.f",
        },
        "scope": (
            "reference-source proxy for active unblocked DSYTD2 rank updates; "
            "DLARFG, DSYTRD wrapper, DSYEVD, DSTERF, and loaded runtime excluded"
        ),
        "matrix_order": n,
        "active_reflector_orders_included": [2, n - 1],
        "maximum_reference_rank_update_flops_excluding_dlarfg": total,
        "per_active_order": per_order,
        "assumptions": [
            "lower-triangle reference DSYTD2 path; upper path has the same shapes",
            "all reflector updates are active, which bounds TAUI-dependent skips",
            "DSYR2 uses its full triangular update path; zero-column skips can only lower work",
            "reference BLAS source expressions are used as a semantic proxy, not as a linked-kernel trace",
        ],
        "unresolved_or_excluded": [
            "DLARFG and DNRM2/DLAMCH/DLAPY2/DSCAL helper arithmetic",
            "DSYTRD block-size selection and blocked DLATRD/DSYR2K paths",
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
