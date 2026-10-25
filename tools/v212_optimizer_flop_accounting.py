"""Source-derived arithmetic inventory for the V2.12 scratch Adam/EMA step.

This is an analytical subcomponent of the future training-FLOP counter. It
does not execute the optimizer, consume model/data values, or update arrays.
It excludes objective-graph arithmetic and all non-FLOP validation/copy work.
"""
from __future__ import annotations

import json


ARMS = (
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
)
EMA_ARMS = frozenset(("multi-step-jepa", "single-pair-jepa",
                      "single-horizon-jepa"))

SHARED_PARAMETERS = 198 * 32 + 32 + 32 * 65 + 65 + 32 + 1
PREDICTOR_PARAMETERS = 104 * 32 + 32
DECODER_PARAMETERS = 32 * 198 + 198
EMA_PARAMETERS = 198 * 32 + 32
PARAMETER_TENSORS = {
    "multi-step-jepa": 8,
    "single-pair-jepa": 8,
    "recursive-raw-state": 10,
    "value-only-latent-rollout": 8,
    "direct-leaf-value": 6,
    "single-horizon-jepa": 8,
}


def _parameters(arm: str) -> int:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    count = SHARED_PARAMETERS
    if arm != "direct-leaf-value":
        count += PREDICTOR_PARAMETERS
    if arm == "recursive-raw-state":
        count += DECODER_PARAMETERS
    return count


def _one_update(arm: str) -> dict:
    n = _parameters(arm)
    m = EMA_PARAMETERS if arm in EMA_ARMS else 0
    tensor_keys = PARAMETER_TENSORS[arm]
    ema_keys = 2 if arm in EMA_ARMS else 0

    # Count array-element arithmetic in the helper's actual expression order.
    # The global norm performs N multiplies and N total additions: N-K inside
    # the per-tensor NumPy reductions plus K scalar additions in Python sum.
    additions = 4 * n + m
    subtractions = n + 2 * tensor_keys + 2 + ema_keys
    multiplications = 8 * n + 2 * m
    divisions_without_clip = 3 * n
    base_flops = (additions + subtractions + multiplications
                  + divisions_without_clip)

    return {
        "trainable_coordinates": n,
        "trainable_parameter_tensors": tensor_keys,
        "ema_coordinates": m,
        "ema_parameter_tensors": ema_keys,
        "floating_point_arithmetic": {
            "additions": additions,
            "subtractions": subtractions,
            "multiplications": multiplications,
            "divisions_excluding_clip_scale": divisions_without_clip,
            "clip_scale_divisions": {"norm_le_5": 0, "norm_gt_5": 1},
            "total_flops": {"norm_le_5": base_flops,
                            "norm_gt_5": base_flops + 1},
        },
        "global_clipping_branch": {
            "norm_le_5": {
                "clip_scale_divisions": 0,
                "gradient_scale_multiplications": n,
            },
            "norm_gt_5": {
                "clip_scale_divisions": 1,
                "gradient_scale_multiplications": n,
            },
            "note": (
                "The source materializes grads[key] * clip_scale in both branches; "
                "only computing 5.0 / gradient_norm is branch-dependent."
            ),
        },
        "separately_reported_operations": {
            "scalar_powers": 2,
            "square_roots": n + 1,
            "second_moment_nonnegative_comparisons": n,
            "clip_threshold_comparisons": 1,
            "finite_value_predicates": 7 * n + 2 * m + 1,
        },
        "scalar_subtraction_breakdown": {
            "bias_correction_denominators": 2,
            "adam_coefficients_once_per_parameter_tensor": 2 * tensor_keys,
            "ema_coefficient_once_per_target_tensor": ema_keys,
        },
        "excluded_non_flop_work": [
            "input/output array copies and allocations",
            "dtype, key, and shape validation",
            "finite-check reductions and boolean any/all reductions",
            "dictionary iteration, indexing, and Python control flow",
        ],
    }


def accounting() -> dict:
    """Return one-update formulas and 20×87 scratch-schedule intervals."""
    updates = 20 * 87
    per_arm = {}
    for arm in ARMS:
        row = _one_update(arm)
        bounds = row["floating_point_arithmetic"]["total_flops"]
        row["twenty_seed_87_update_optimizer_only_flop_interval"] = {
            "lower": bounds["norm_le_5"] * updates,
            "upper": bounds["norm_gt_5"] * updates,
        }
        per_arm[arm] = row
    return {
        "schema": "caissa.v212.scratch-adam-ema-arithmetic-inventory.v01",
        "scope": "one scratch optimizer update; 20 seeds × 87 updates is an optimizer-only analytical interval",
        "source_anchor": "two_player/v212_scratch_optimizer.py:scratch_adam_ema_step",
        "counting_convention": "one FP add/subtract/multiply/divide is one FLOP; powers and square roots are reported separately",
        "schedule_updates": updates,
        "arms": per_arm,
        "limitations": [
            "Analytical source formula only; this module does not execute or instrument the optimizer.",
            "The interval covers only the norm-dependent clipping division branch.",
            "The objective graph, LAPACK eigensolver, masks, trainer, and complete non-FLOP coverage are not counted.",
            "These optimizer-only intervals cannot establish six-arm total-FLOP parity or authorize a profile/fit.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
