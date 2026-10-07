"""Mask-parameterized residual and squared-error inventory for V2.12.

This is a source-derived shape subcounter for loss residuals and the repeated
elementwise square expressions in the current no-update graph. It does not
execute the graph or count reductions, scalar weighting, gradients, regularizer
work, softmax, activations, matmuls, eigensolver, optimizer, or preflight.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import (
    ARMS, JEPA_HORIZONS, _validated_masks,
)


FEATURES = 198
LATENT = 32
HORIZONS = (1, 2, 4)


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    batch_size, masks = _validated_masks(valid_by_horizon)
    rows = {h: int(masks[h].sum()) for h in HORIZONS}

    subtraction_elements = {"root_value": batch_size}
    square_elements = {"root_value": batch_size}

    if arm == "direct-leaf-value":
        subtraction_elements["direct_leaf_value"] = rows[4]
        square_elements["direct_leaf_value"] = rows[4]
    else:
        for horizon in HORIZONS:
            count = rows[horizon]
            subtraction_elements[f"rollout_value_h{horizon}"] = count
            # The source computes delta**2 once for the per-horizon mean and
            # again for the pooled weighted sum.
            square_elements[f"rollout_value_h{horizon}"] = 2 * count

        for horizon in JEPA_HORIZONS.get(arm, ()):
            count = rows[horizon] * LATENT
            subtraction_elements[f"latent_roll_h{horizon}"] = count
            square_elements[f"latent_roll_h{horizon}"] = 2 * count

        if arm == "recursive-raw-state":
            for horizon in HORIZONS:
                count = rows[horizon] * FEATURES
                subtraction_elements[f"raw_state_h{horizon}"] = count
                square_elements[f"raw_state_h{horizon}"] = 2 * count

    residual_subtractions = sum(subtraction_elements.values())
    square_ops = sum(square_elements.values())
    return {
        "schema": "caissa.v212.model-loss-residual-shapes.v01",
        "scope": "array residual subtractions and repeated squared-error elements in one 64-window objective invocation",
        "arm": arm,
        "horizon_valid_rows": rows,
        "residual_subtractions_by_loss_site": subtraction_elements,
        "residual_subtraction_flops": residual_subtractions,
        "square_operations_by_loss_site": square_elements,
        "square_operation_elements": square_ops,
        "flops_if_each_square_is_counted_as_one_multiply": (
            residual_subtractions + square_ops),
        "limitations": [
            "Shape inventory only; no masks were inferred from game data and the model graph was not executed.",
            "An approved review accepts one candidate multiplication per fixed-shape square element under a semantic source-level convention; this does not characterize the loaded NumPy power kernel.",
            "NumPy means/sums, scalar coefficients and weighted accumulation are excluded from this subcounter.",
            "Gradient, softmax, regularizer, derivative, bias, matmul, eigensolver/LAPACK, optimizer, preflight, runtime and non-FLOP work are excluded.",
            "This cannot establish total six-arm compute parity or authorize a profile/fit.",
        ],
    }


def full_valid_batch(arm: str) -> dict:
    full = np.ones(64, dtype=bool)
    return inventory(arm, {h: full for h in HORIZONS})


if __name__ == "__main__":
    print(json.dumps({arm: full_valid_batch(arm) for arm in ARMS},
                     sort_keys=True, indent=2, allow_nan=False))
