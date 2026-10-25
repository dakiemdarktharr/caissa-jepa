"""Source-shape inventory for fixed array-square sites in the V2.12 graph.

Under the independently reviewed semantic convention, each fixed-shape array
expression ``x ** 2`` contributes one candidate multiplication per element.
This is not a claim about NumPy's loaded power-loop implementation. Scalar
bias-correction powers are outside this inventory.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import (
    ARMS, JEPA_HORIZONS, _active_prefix_rows, _validated_masks,
)


BATCH = 64
LATENT = 32
FEATURES = 198
HORIZONS = (1, 2, 4)
SHARED_PARAMETER_SHAPES = {
    "ew": (FEATURES, LATENT), "eb": (LATENT,),
    "pw": (LATENT, 65), "pb": (65,), "vw": (LATENT, 1), "vb": (1,),
}
PREDICTOR_PARAMETER_SHAPES = {"fw": (104, LATENT), "fb": (LATENT,)}
DECODER_PARAMETER_SHAPES = {"dw": (LATENT, FEATURES), "db": (FEATURES,)}


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    """Count source ``** 2`` array elements for one 64-window invocation."""
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    batch_size, masks = _validated_masks(valid_by_horizon)
    valid_rows = {h: int(masks[h].sum()) for h in HORIZONS}
    active_rows = _active_prefix_rows(masks)
    sites: dict[str, int] = {
        "regularizer.centered_variance": BATCH * LATENT,
        "regularizer.shortfall_variance": LATENT,
        # The vectorized square includes zero-valued diagonal entries.
        "regularizer.offdiag_covariance": LATENT * LATENT,
        "root_value_mse": batch_size,
        "root_value_tanh_derivative": batch_size,
    }

    if arm == "direct-leaf-value":
        leaves = valid_rows[4]
        sites.update({
            "direct_leaf_value_mse": leaves,
            "direct_leaf_value_tanh_derivative": leaves,
            "direct_leaf_encoder_tanh_derivative": leaves * LATENT,
        })
    else:
        for horizon in HORIZONS:
            rows = valid_rows[horizon]
            sites[f"rollout_value_h{horizon}.per_horizon_mse"] = rows
            sites[f"rollout_value_h{horizon}.pooled_loss"] = rows
            sites[f"rollout_value_h{horizon}.tanh_derivative"] = rows

        for horizon in JEPA_HORIZONS.get(arm, ()):
            elements = valid_rows[horizon] * LATENT
            sites[f"latent_roll_h{horizon}.per_horizon_mse"] = elements
            sites[f"latent_roll_h{horizon}.pooled_loss"] = elements

        if arm == "recursive-raw-state":
            for horizon in HORIZONS:
                elements = valid_rows[horizon] * FEATURES
                sites[f"raw_state_h{horizon}.per_horizon_mse"] = elements
                sites[f"raw_state_h{horizon}.pooled_loss"] = elements

        for step, rows in active_rows.items():
            if arm == "recursive-raw-state":
                sites[f"raw_state_reverse.step_{step}.reencoded_state_tanh_derivative"] = rows * LATENT
                sites[f"raw_state_reverse.step_{step}.predictor_tanh_derivative"] = rows * LATENT
            else:
                sites[f"latent_reverse.step_{step}.predictor_tanh_derivative"] = rows * LATENT

    sites["root_encoder_tanh_derivative"] = batch_size * LATENT

    gradient_shapes = dict(SHARED_PARAMETER_SHAPES)
    if arm != "direct-leaf-value":
        gradient_shapes.update(PREDICTOR_PARAMETER_SHAPES)
    if arm == "recursive-raw-state":
        gradient_shapes.update(DECODER_PARAMETER_SHAPES)
    sites["diagnostic.gradient_norm_parameter_squares"] = sum(
        int(np.prod(shape)) for shape in gradient_shapes.values())

    return {
        "schema": "caissa.v212.model-square-shapes.v01",
        "scope": "fixed array-square source sites in one 64-window loss_grad invocation",
        "arm": arm,
        "horizon_valid_rows": valid_rows,
        "active_prefix_rows": active_rows,
        "square_multiplication_elements_by_site": sites,
        "candidate_square_multiplications": sum(sites.values()),
        "source_square_site_count": 20,
        "counting_convention": (
            "one candidate multiplication per element for each fixed-shape array ** 2; "
            "semantic source-level conversion only, not a loaded NumPy kernel claim"
        ),
        "limitations": [
            "Analytical shape inventory only; no objective graph or data was executed.",
            "The inventory does not count reductions that consume squared arrays or any other FLOPs.",
            "The source AST guard must be updated if a square site is added, removed, or moved to a new shape family.",
            "Scalar powers, including Adam bias-correction powers, are reported separately and excluded.",
            "This subcounter does not establish total six-arm compute parity or authorize a profile/fit.",
        ],
    }


def full_valid_batch(arm: str) -> dict:
    full = np.ones(BATCH, dtype=bool)
    return inventory(arm, {h: full for h in HORIZONS})


if __name__ == "__main__":
    print(json.dumps({arm: full_valid_batch(arm) for arm in ARMS},
                     sort_keys=True, indent=2, allow_nan=False))
