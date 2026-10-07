"""Mask-parameterized dense-matmul inventory for the V2.12 model graph.

Counts only explicit ``@`` calls in ``V212Model.loss_grad`` and its helpers.
It does not execute the model, infer masks from data, count elementwise/reduction
or eigensolver work, or constitute the complete D03 training-FLOP counter.
"""
from __future__ import annotations

import json

import numpy as np


ARMS = (
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
)
JEPA_HORIZONS = {
    "multi-step-jepa": (1, 2, 4),
    "single-pair-jepa": (2,),
    "single-horizon-jepa": (1,),
}
HORIZONS = (1, 2, 4)
FEATURES = 198
LATENT = 32
POLICY = 65
PREDICTOR_INPUT = 104
TRANSITIONS = 4

FORWARD_CATEGORIES = frozenset((
    "root_encoder_forward", "policy_head_forward", "root_value_forward",
    "predictor_forward", "rollout_value_forward",
    "ema_target_encoder_forward", "raw_decoder_forward",
    "raw_reencoder_forward", "direct_leaf_encoder_forward",
    "direct_leaf_value_forward",
))


def _validated_masks(valid_by_horizon) -> tuple[int, dict[int, np.ndarray]]:
    if not isinstance(valid_by_horizon, dict) or set(valid_by_horizon) != set(HORIZONS):
        raise ValueError("valid_by_horizon must map exactly horizons 1, 2, and 4")
    masks = {}
    n = None
    for horizon in HORIZONS:
        mask = np.asarray(valid_by_horizon[horizon])
        if mask.ndim != 1 or mask.dtype != np.dtype(bool):
            raise ValueError("each horizon mask must be a one-dimensional Boolean array")
        if n is None:
            n = len(mask)
        if len(mask) != n:
            raise ValueError("horizon masks must have the same batch length")
        masks[horizon] = mask
    if n != 64:
        raise ValueError("D03 matmul accounting requires the fixed batch size of 64")
    return n, masks


def _active_prefix_rows(masks: dict[int, np.ndarray]) -> dict[int, int]:
    return {
        step: int(np.logical_or.reduce(
            [masks[h] for h in HORIZONS if h >= step]).sum())
        for step in range(1, TRANSITIONS + 1)
    }


def _matmul(rows: int, fan_in: int, fan_out: int) -> int:
    return rows * fan_in * fan_out


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    """Count explicit dense matrix products for one 64-window scheduled batch.

    FLOPs use ``2*m*k*n`` for ``[m,k] @ [k,n]``. A category with zero rows is
    skipped by the graph and contributes zero calls and zero FLOPs.
    """
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    batch_size, masks = _validated_masks(valid_by_horizon)
    horizon_rows = {h: int(masks[h].sum()) for h in HORIZONS}
    active_rows = _active_prefix_rows(masks)
    macs: dict[str, int] = {}
    calls: dict[str, int] = {}

    def add(name: str, rows: int, fan_in: int, fan_out: int) -> None:
        macs[name] = rows * fan_in * fan_out
        calls[name] = int(rows > 0)

    # Shared root encoder, task heads, anti-collapse covariance path, and
    # reverse-mode matrix products in V212Model.loss_grad.
    add("root_encoder_forward", batch_size, FEATURES, LATENT)
    add("policy_head_forward", batch_size, LATENT, POLICY)
    add("root_value_forward", batch_size, LATENT, 1)
    add("covariance_forward", batch_size, LATENT, LATENT)
    add("covariance_gradient", batch_size, LATENT, LATENT)
    add("policy_weight_gradient", batch_size, LATENT, POLICY)
    add("policy_latent_gradient", batch_size, POLICY, LATENT)
    add("root_value_weight_gradient", batch_size, LATENT, 1)
    add("root_value_latent_gradient", batch_size, 1, LATENT)
    add("root_encoder_weight_gradient", batch_size, FEATURES, LATENT)

    if arm == "direct-leaf-value":
        rows = horizon_rows[4]
        add("direct_leaf_encoder_forward", rows, FEATURES, LATENT)
        add("direct_leaf_value_forward", rows, LATENT, 1)
        add("direct_leaf_value_weight_gradient", rows, LATENT, 1)
        add("direct_leaf_value_latent_gradient", rows, 1, LATENT)
        add("direct_leaf_encoder_weight_gradient", rows, FEATURES, LATENT)
    else:
        for step in range(1, TRANSITIONS + 1):
            rows = active_rows[step]
            add("predictor_forward_step_" + str(step), rows,
                PREDICTOR_INPUT, LATENT)
            add("predictor_weight_gradient_step_" + str(step), rows,
                PREDICTOR_INPUT, LATENT)
            add("predictor_input_gradient_step_" + str(step), rows,
                LATENT, LATENT)
            if arm == "recursive-raw-state":
                add("raw_decoder_forward_step_" + str(step), rows,
                    LATENT, FEATURES)
                add("raw_reencoder_forward_step_" + str(step), rows,
                    FEATURES, LATENT)
                add("raw_reencoder_feature_gradient_step_" + str(step), rows,
                    LATENT, FEATURES)
                add("raw_reencoder_weight_gradient_step_" + str(step), rows,
                    FEATURES, LATENT)
                add("raw_decoder_weight_gradient_step_" + str(step), rows,
                    LATENT, FEATURES)
                add("raw_decoder_latent_gradient_step_" + str(step), rows,
                    FEATURES, LATENT)

        for horizon in HORIZONS:
            rows = horizon_rows[horizon]
            add("rollout_value_forward_h" + str(horizon), rows, LATENT, 1)
            add("rollout_value_weight_gradient_h" + str(horizon), rows,
                LATENT, 1)
            add("rollout_value_latent_gradient_h" + str(horizon), rows,
                1, LATENT)

        for horizon in JEPA_HORIZONS.get(arm, ()):
            add("ema_target_encoder_forward_h" + str(horizon),
                horizon_rows[horizon], FEATURES, LATENT)

    forward_macs = sum(value for name, value in macs.items()
                       if name in FORWARD_CATEGORIES
                       or any(name.startswith(prefix + "_step_")
                              for prefix in ("predictor_forward",
                                             "raw_decoder_forward",
                                             "raw_reencoder_forward"))
                       or name.startswith("rollout_value_forward_h")
                       or name.startswith("ema_target_encoder_forward_h"))
    covariance_macs = macs["covariance_forward"] + macs["covariance_gradient"]
    total_macs = sum(macs.values())
    return {
        "schema": "caissa.v212.model-dense-matmul-flops.v01",
        "scope": "explicit dense matrix products in one 64-window no-update objective invocation",
        "arm": arm,
        "horizon_valid_rows": horizon_rows,
        "active_prefix_rows": active_rows,
        "matmul_call_counts": calls,
        "matmul_macs_by_call_site": macs,
        "projection_forward_macs": forward_macs,
        "covariance_matmul_macs": covariance_macs,
        "all_explicit_matmul_macs": total_macs,
        "projection_forward_flops": 2 * forward_macs,
        "covariance_matmul_flops": 2 * covariance_macs,
        "all_explicit_matmul_flops": 2 * total_macs,
        "limitations": [
            "Analytical shape inventory; the objective graph was not executed.",
            "Excludes elementwise/reduction arithmetic, activations, eigvalsh/LAPACK, preflight, optimizer, and non-FLOP work.",
            "Masks must come from a separately authorized, exact-rule-audited schedule before a D03 profile.",
            "Explicit matmul counts do not establish total training-FLOP parity or authorize a profile/fit.",
        ],
    }


def full_valid_batch(arm: str) -> dict:
    """Convenience architecture check; this does not create game positions."""
    full = np.ones(64, dtype=bool)
    return inventory(arm, {1: full, 2: full, 4: full})


if __name__ == "__main__":
    print(json.dumps({arm: full_valid_batch(arm) for arm in ARMS},
                     sort_keys=True, indent=2, allow_nan=False))
