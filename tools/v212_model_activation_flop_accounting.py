"""Mask-parameterized activation and bias arithmetic for the V2.12 graph.

This subcounter covers affine bias additions, tanh calls, and the explicit
elementwise tanh-derivative arithmetic. It does not execute the model or count
loss/reduction/preflight/eigensolver/optimizer operations.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import (
    ARMS, JEPA_HORIZONS, _active_prefix_rows, _validated_masks,
)


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    batch_size, masks = _validated_masks(valid_by_horizon)
    valid_rows = {h: int(masks[h].sum()) for h in (1, 2, 4)}
    active_rows = _active_prefix_rows(masks)

    # Every affine result receives one vectorized bias addition. Policy logits
    # are the only shared affine head without a following tanh.
    bias_adds = {
        "root_encoder": batch_size * 32,
        "policy_head": batch_size * 65,
        "root_value_head": batch_size,
    }
    tanh_elements = {
        "root_encoder": batch_size * 32,
        "root_value_head": batch_size,
    }
    derivative_elements = {
        "root_encoder": batch_size * 32,
        "root_value_head": batch_size,
    }
    # The value-loss heads scale their incoming delta before multiplying by
    # the tanh derivative. Keep these operations separate from the derivative
    # site itself so the count cannot be mistaken for (1-z**2) arithmetic.
    gradient_scale_elements = {"root_value_head": batch_size}

    if arm == "direct-leaf-value":
        leaf_rows = valid_rows[4]
        bias_adds["direct_leaf_encoder"] = leaf_rows * 32
        bias_adds["direct_leaf_value_head"] = leaf_rows
        tanh_elements["direct_leaf_encoder"] = leaf_rows * 32
        tanh_elements["direct_leaf_value_head"] = leaf_rows
        derivative_elements["direct_leaf_encoder"] = leaf_rows * 32
        derivative_elements["direct_leaf_value_head"] = leaf_rows
        gradient_scale_elements["direct_leaf_value_head"] = leaf_rows
    else:
        for step in range(1, 5):
            rows = active_rows[step]
            bias_adds[f"predictor_step_{step}"] = rows * 32
            tanh_elements[f"predictor_step_{step}"] = rows * 32
            derivative_elements[f"predictor_step_{step}"] = rows * 32
            if arm == "recursive-raw-state":
                bias_adds[f"raw_decoder_step_{step}"] = rows * 198
                bias_adds[f"raw_reencoder_step_{step}"] = rows * 32
                tanh_elements[f"raw_reencoder_step_{step}"] = rows * 32
                derivative_elements[f"raw_reencoder_step_{step}"] = rows * 32

        for horizon in (1, 2, 4):
            rows = valid_rows[horizon]
            bias_adds[f"rollout_value_h{horizon}"] = rows
            tanh_elements[f"rollout_value_h{horizon}"] = rows
            derivative_elements[f"rollout_value_h{horizon}"] = rows
            gradient_scale_elements[f"rollout_value_h{horizon}"] = rows

        for horizon in JEPA_HORIZONS.get(arm, ()):
            rows = valid_rows[horizon]
            bias_adds[f"ema_target_encoder_h{horizon}"] = rows * 32
            tanh_elements[f"ema_target_encoder_h{horizon}"] = rows * 32

    tanh_derivative_flops = 3 * sum(derivative_elements.values())
    gradient_scale_multiplications = sum(gradient_scale_elements.values())
    return {
        "schema": "caissa.v212.model-activation-bias-flops.v01",
        "scope": "affine bias additions, tanh element counts, explicit tanh-derivative arithmetic, and pre-derivative value-gradient scaling in one 64-window invocation",
        "arm": arm,
        "horizon_valid_rows": valid_rows,
        "active_prefix_rows": active_rows,
        "bias_additions_by_call_site": bias_adds,
        "bias_addition_flops": sum(bias_adds.values()),
        "tanh_elements_by_call_site": tanh_elements,
        "tanh_calls_element_count": sum(tanh_elements.values()),
        "tanh_derivative_elements_by_call_site": derivative_elements,
        "tanh_derivative_flops": tanh_derivative_flops,
        "tanh_derivative_breakdown": {
            "squares_as_multiplications": sum(derivative_elements.values()),
            "one_minus_square_subtractions": sum(derivative_elements.values()),
            "gradient_multiplications": sum(derivative_elements.values()),
        },
        "pre_derivative_gradient_scale_elements_by_call_site": gradient_scale_elements,
        "pre_derivative_gradient_scale_multiplications": gradient_scale_multiplications,
        "counted_activation_gradient_array_flops": (
            tanh_derivative_flops + gradient_scale_multiplications),
        "limitations": [
            "Analytical shape count only; the objective graph was not executed.",
            "Tanh calls are reported as nonlinear operations, not FLOPs.",
            "The separately reported upstream gradient scales cover the array multiply of delta by a loss coefficient; scalar coefficient construction is outside this subcounter.",
            "Other elementwise loss/gradient arithmetic, reductions, eigvalsh/LAPACK, matmuls, preflight, optimizer, and runtime work are excluded.",
            "Masks must come from an exact-rule-audited schedule before any D03 profile.",
            "This subcounter cannot establish total training-FLOP parity or authorize profile/fit.",
        ],
    }


def full_valid_batch(arm: str) -> dict:
    full = np.ones(64, dtype=bool)
    return inventory(arm, {1: full, 2: full, 4: full})


if __name__ == "__main__":
    print(json.dumps({arm: full_valid_batch(arm) for arm in ARMS},
                     sort_keys=True, indent=2, allow_nan=False))
