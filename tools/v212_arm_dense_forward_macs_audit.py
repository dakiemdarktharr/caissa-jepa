"""Static dense forward-MAC inventory for the proposed V2.12 arm panel.

This is architecture arithmetic only. It does not execute a model, count
backward/optimizer/elementwise work, or demonstrate the v04 FLOP-parity gate.
"""
from __future__ import annotations

import json


ENCODER = (198, 32)
POLICY_HEAD = (32, 65)
VALUE_HEAD = (32, 1)
PREDICTOR = (104, 32)
DECODER = (32, 198)
HORIZONS = (1, 2, 4)
TRANSITION_STEPS = max(HORIZONS)


def macs(layer: tuple[int, int]) -> int:
    fan_in, fan_out = layer
    if type(fan_in) is not int or type(fan_out) is not int:
        raise TypeError("layer dimensions must be integers")
    if fan_in <= 0 or fan_out <= 0:
        raise ValueError("layer dimensions must be positive")
    return fan_in * fan_out


def inventory() -> dict:
    """Return MACs per fully valid, nonterminal training window.

    Counts dense matrix multiply-accumulates only, once per forward pass.
    A MAC is not silently converted to two FLOPs; callers can apply a stated
    convention if they need a FLOP estimate.
    """
    root_and_task_heads = (
        macs(ENCODER) + macs(POLICY_HEAD) + macs(VALUE_HEAD)
    )
    # Reaching horizon 4 requires calls at steps 1, 2, 3, and 4. Step 3 is
    # recursive state construction even though it has no direct horizon loss.
    recursive_predictor = TRANSITION_STEPS * macs(PREDICTOR)
    rollout_value_heads = len(HORIZONS) * macs(VALUE_HEAD)
    latent_target_encodes = macs(ENCODER)
    # Raw-state recurrence decodes/re-encodes every transition, including the
    # unsupervised intermediate step 3 needed to construct horizon 4.
    raw_decode_and_reencode = TRANSITION_STEPS * (
        macs(DECODER) + macs(ENCODER)
    )
    direct_leaf_encode = macs(ENCODER) + macs(VALUE_HEAD)

    counts = {
        "multi-step-jepa": (root_and_task_heads + recursive_predictor
                            + rollout_value_heads
                            + len(HORIZONS) * latent_target_encodes),
        "single-pair-jepa": (root_and_task_heads + recursive_predictor
                             + rollout_value_heads + latent_target_encodes),
        "recursive-raw-state": (root_and_task_heads + recursive_predictor
                                + rollout_value_heads
                                + raw_decode_and_reencode),
        "value-only-latent-rollout": (root_and_task_heads
                                       + recursive_predictor
                                       + rollout_value_heads),
        "direct-leaf-value": root_and_task_heads + direct_leaf_encode,
        "single-horizon-jepa": (root_and_task_heads + recursive_predictor
                                + rollout_value_heads + latent_target_encodes),
    }
    reference = counts["multi-step-jepa"]
    return {
        "schema": "caissa.v212.arm-dense-forward-macs-audit.v01",
        "scope": "per fully valid nonterminal four-ply training window with 1/2/4 targets",
        "counting_unit": "dense matrix multiply-accumulates (MACs)",
        "layer_dimensions": {
            "encoder": list(ENCODER),
            "policy_head": list(POLICY_HEAD),
            "value_head": list(VALUE_HEAD),
            "predictor": list(PREDICTOR),
            "raw_decoder": list(DECODER),
        },
        "arm_dense_forward_macs": counts,
        "relative_to_multi_step_jepa": {
            arm: (count / reference) - 1.0 for arm, count in counts.items()
        },
        "included_operations": {
            "shared_root_encoder_and_policy_value_heads": 1,
            "transition_steps_per_predictive_arm": TRANSITION_STEPS,
            "recursive_predictor_calls_per_predictive_arm": TRANSITION_STEPS,
            "rollout_value_head_calls_per_predictive_arm": len(HORIZONS),
            "ema_target_encoder_calls": {
                "multi-step-jepa": len(HORIZONS),
                "single-pair-jepa": 1,
                "single-horizon-jepa": 1,
                "recursive-raw-state": 0,
                "value-only-latent-rollout": 0,
            },
            "raw_decoder_and_online_reencoder_calls": TRANSITION_STEPS,
            "direct_leaf_exact_encoder_and_value_calls": 1,
        },
        "limitations": [
            "Static graph interpretation of METHOD_SPEC_V212-04 plus the unadopted raw-state wiring draft.",
            "No activations, bias additions, loss/reduction, masks, backward pass, optimizer, EMA update, data movement, or padding effects are counted.",
            "All three horizons are assumed valid and nonterminal; masks can change executed work.",
            "This inventory is not a training-FLOP measurement or parity decision.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), sort_keys=True, indent=2, allow_nan=False))
