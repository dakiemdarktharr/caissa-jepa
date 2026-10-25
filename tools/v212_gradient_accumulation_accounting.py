"""Array-addition inventory for V2.12 loss-gradient accumulation sites.

Counts one candidate addition per output element for explicit in-place
``+=`` array accumulation and the raw-state decoder-gradient merge in
``V212Model.loss_grad``. The root regularizer's ``dz0 += 0.1 * dreg`` is
excluded because it is already owned by the regularizer inventory. No model
or numeric data is evaluated here.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import (
    ARMS, JEPA_HORIZONS, _active_prefix_rows, _validated_masks,
)


HORIZONS = (1, 2, 4)
LATENT = 32
FEATURES = 198
POLICY = 65
PREDICTOR_INPUT = 104


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    _, masks = _validated_masks(valid_by_horizon)
    rows = {h: int(masks[h].sum()) for h in HORIZONS}
    if arm == "direct-leaf-value" and rows[4] == 0:
        raise ValueError("direct-leaf schedule requires at least one valid H4 row")

    active_rows = _active_prefix_rows(masks)
    counts = {
        "policy_parameter_gradient_buffer_additions": LATENT * POLICY + POLICY,
        "policy_root_latent_gradient_additions": 64 * LATENT,
        "root_value_parameter_gradient_buffer_additions": LATENT + 1,
        "root_value_latent_gradient_additions": 64 * LATENT,
        "horizon_value_parameter_gradient_buffer_additions": 0,
        "outcome_state_gradient_accumulation_additions": 0,
        "latent_target_state_gradient_accumulation_additions": 0,
        "raw_target_feature_gradient_accumulation_additions": 0,
        "recurrent_decoder_feature_gradient_merge_additions": 0,
        "recurrent_parameter_gradient_buffer_additions": 0,
        "recurrent_state_gradient_accumulation_additions": 0,
        "initial_encoder_latent_gradient_merge_additions": 0,
        "final_encoder_parameter_gradient_buffer_additions": FEATURES * LATENT + LATENT,
        "direct_leaf_parameter_gradient_buffer_additions": 0,
    }

    if arm == "direct-leaf-value":
        counts["direct_leaf_parameter_gradient_buffer_additions"] = (
            LATENT + 1 + FEATURES * LATENT + LATENT
        )
    else:
        for horizon in HORIZONS:
            count = rows[horizon]
            if count:
                counts["horizon_value_parameter_gradient_buffer_additions"] += LATENT + 1
                counts["outcome_state_gradient_accumulation_additions"] += count * LATENT

        if arm == "recursive-raw-state":
            target_horizons = HORIZONS
            for horizon in target_horizons:
                if rows[horizon]:
                    counts["raw_target_feature_gradient_accumulation_additions"] += (
                        rows[horizon] * FEATURES
                    )
        else:
            target_horizons = JEPA_HORIZONS.get(arm, ())
            for horizon in target_horizons:
                if rows[horizon]:
                    counts["latent_target_state_gradient_accumulation_additions"] += (
                        rows[horizon] * LATENT
                    )

        for step in range(1, 5):
            count = active_rows[step]
            if not count:
                continue
            if arm == "recursive-raw-state":
                counts["recurrent_decoder_feature_gradient_merge_additions"] += (
                    count * FEATURES
                )
                counts["recurrent_parameter_gradient_buffer_additions"] += (
                    2 * FEATURES * LATENT + FEATURES + LATENT
                    + PREDICTOR_INPUT * LATENT + LATENT
                )
            else:
                counts["recurrent_parameter_gradient_buffer_additions"] += (
                    PREDICTOR_INPUT * LATENT + LATENT
                )
            counts["recurrent_state_gradient_accumulation_additions"] += count * LATENT

        # The graph merges dstate[0] into the root latent gradient after the
        # reverse loop, even for a batch with no active rollout rows.
        counts["initial_encoder_latent_gradient_merge_additions"] = 64 * LATENT

    return {
        "schema": "caissa.v212.gradient-accumulation-accounting.v01",
        "arm": arm,
        "scope": "candidate array additions at loss-gradient accumulation sites per 64-window invocation",
        "valid_rows_by_horizon": rows,
        "active_prefix_rows_by_step": active_rows,
        "candidate_array_additions_per_invocation": counts,
        "candidate_array_additions_total": sum(counts.values()),
        "counting_assumptions": [
            "Each array in-place += or explicit same-shape gradient merge performs one candidate addition per output element.",
            "A parameter gradient accumulator is counted once per executed source update, independent of matrix/reduction work that produced its RHS.",
            "The active-prefix row count is the union of all valid horizons at or beyond each recurrent step.",
            "Direct-leaf schedules must have at least one valid H4 row under the accepted profile protocol.",
        ],
        "limitations": [
            "Candidate source-shape accounting only; it does not trace NumPy kernels or establish total six-arm FLOPs.",
            "The regularizer-owned root latent-gradient accumulation is excluded to avoid overlap with its elementwise inventory.",
            "Matrix products, reductions, elementwise scaling, residuals/squares, allocation, copies, and optimizer arithmetic are excluded.",
            "No loaded-runtime profile, selected-window mask schedule, or parity gate is represented by the illustrative masks.",
        ],
    }


def accounting(valid_by_horizon: dict[int, np.ndarray] | None = None) -> dict:
    if valid_by_horizon is None:
        valid_by_horizon = {h: np.ones(64, dtype=bool) for h in HORIZONS}
    per_arm = {arm: inventory(arm, valid_by_horizon) for arm in ARMS}
    return {
        "schema": "caissa.v212.gradient-accumulation-panel.v01",
        "mask_fixture": "all 64 rows valid at H1/H2/H4; illustrative only",
        "arms": per_arm,
        "panel_total_additions_per_arm": {
            arm: details["candidate_array_additions_total"]
            for arm, details in per_arm.items()
        },
        "limitations": [
            "Full-valid synthetic mask formula only; not the frozen 20×87 schedule.",
            "These totals cover only array accumulation additions and are not total arm compute or a parity result.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
