"""Source-level elementwise arithmetic inventory for V2.12 regularization.

Counts arithmetic surrounding, but not including, already-inventoried
reductions, array squares, matrix products, or the linked eigensolver. Counts
are candidate per-element operations for one fixed 64×32 root latent batch;
no model or numeric data is evaluated.
"""
from __future__ import annotations

import json


BATCH = 64
LATENT = 32
DEFAULT_SCHEDULE_UPDATES = 20 * 87


def accounting(scheduled_updates: int = DEFAULT_SCHEDULE_UPDATES) -> dict:
    if type(scheduled_updates) is not int or scheduled_updates <= 0:
        raise ValueError("scheduled_updates must be a positive integer")

    centered = BATCH * LATENT
    covariance = LATENT * LATENT
    per_invocation = {
        "candidate_fp_array_additions": LATENT + 2 * centered,
        "candidate_fp_array_subtractions": centered + covariance + LATENT,
        "candidate_fp_array_multiplications": (
            2 * LATENT + 3 * centered
        ),
        "candidate_fp_array_divisions": centered + covariance + centered,
        "candidate_fp_scalar_additions": 3,
        "candidate_fp_scalar_multiplications": 4,
        "candidate_fp_scalar_divisions": 1,
        "integer_scalar_shape_multiplications": 2,
        "maximum_output_elements_not_converted_to_flops": 2 * LATENT,
        "candidate_maximum_comparisons": 2 * LATENT,
        "sqrt_output_elements_not_converted_to_flops": LATENT,
        "squared_array_elements_owned_by_square_inventory": (
            centered + LATENT + covariance
        ),
        "reductions_owned_by_reduction_inventory": 5,
        "matmuls_owned_by_matmul_inventory": 2,
        "linked_eigensolver_calls_not_counted": 1,
    }
    per_arm_schedule = {
        key: value * scheduled_updates
        for key, value in per_invocation.items()
    }
    return {
        "schema": "caissa.v212.regularizer-elementwise.v01",
        "scope": "regularizer elementwise arithmetic and scalar objective weighting per fixed 64×32 root latent invocation, per arm",
        "scheduled_updates_per_arm": scheduled_updates,
        "per_invocation": per_invocation,
        "schedule_per_arm": per_arm_schedule,
        "counting_assumptions": [
            "Each broadcast elementwise add/subtract/multiply/divide counts one candidate operation per output element.",
            "The dz regularization path has 32 coefficient multiplies, 2,048 centered-array multiplies, 32 denominator-scale multiplies, and 2,048 divisions; its covariance-gradient path has 2,048 multiplies and 2,048 divisions.",
            "The 1,024 covariance normalization divisions and 1,024 off-diagonal subtractions are counted; the covariance matmul is not.",
            "The scalar total-loss expression contributes three additions and two multiplications; the separately materialized weighted metrics add two scalar multiplications.",
            "The root variance-gradient scale contributes 2,048 multiplications and 2,048 accumulation additions.",
            "Maximum comparisons, square roots, reductions, squares, matmuls, and eigensolver work are listed separately to prevent double counting.",
            "The two shape products d*n and n*d are Python integer operations, reported separately from FP arithmetic.",
        ],
        "limitations": [
            "Source-shape accounting only; the current NumPy/Python runtime and kernels were not executed or fingerprinted.",
            "Candidate ordinary reduction work belongs to the reduction inventory; squared elements overlap the unified square inventory; both dense products overlap the matmul inventory.",
            "Does not count np.linalg.eigvalsh/LAPACK, transcendental costs, complete graph work, or non-FLOP validation and indexing.",
            "This subcounter cannot establish total six-arm compute parity or authorize a profile/fit.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
