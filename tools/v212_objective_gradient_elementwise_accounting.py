"""Elementwise multiplications for pooled latent/raw target gradients.

Counts the per-coordinate multiply of each enabled target-gradient scale by
its residual in ``V212Model.loss_grad``. Outcome-value gradient scaling is
already in the activation inventory; reductions, residuals, squares, scalar
coefficient construction, and the accumulation additions are owned elsewhere.
No model or numeric data is evaluated here.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import ARMS, JEPA_HORIZONS, _validated_masks


HORIZONS = (1, 2, 4)
FEATURES = 198
LATENT = 32


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    _, masks = _validated_masks(valid_by_horizon)
    rows = {h: int(masks[h].sum()) for h in HORIZONS}
    if arm == "direct-leaf-value" and rows[4] == 0:
        raise ValueError("direct-leaf schedule requires at least one valid H4 row")

    if arm == "recursive-raw-state":
        enabled = HORIZONS
        width = FEATURES
        target_kind = "raw_feature"
    else:
        enabled = JEPA_HORIZONS.get(arm, ())
        width = LATENT
        target_kind = "latent"
    per_horizon = {h: rows[h] * width for h in enabled}
    total = sum(per_horizon.values())
    return {
        "schema": "caissa.v212.objective-gradient-elementwise.v01",
        "arm": arm,
        "scope": "one candidate array multiplication per enabled target-gradient residual coordinate, per 64-window invocation",
        "target_kind": target_kind,
        "enabled_target_horizons": list(enabled),
        "valid_rows_by_horizon": rows,
        "candidate_multiplications_by_horizon": per_horizon,
        "candidate_array_multiplications_total": total,
        "counting_assumptions": [
            "Each enabled target gradient materializes one elementwise scalar-coefficient-times-residual array before adding it into its gradient accumulator.",
            "Only nonempty target horizons execute the gradient expression; the 64-row adapter/profile contract is validated separately.",
            "Outcome-value gradient scaling is owned by the activation subcounter and is excluded here.",
        ],
        "limitations": [
            "Source-shape candidate only; no model, data, runtime kernel, or selected mask schedule is executed.",
            "Scalar coefficient construction, residual subtraction, reduction/square work, gradient accumulation additions, activation derivatives, and matrix products are separately owned.",
            "This subcounter cannot establish complete graph coverage, compute parity, or authorize profiling or fitting.",
        ],
    }


def accounting(valid_by_horizon: dict[int, np.ndarray] | None = None) -> dict:
    if valid_by_horizon is None:
        valid_by_horizon = {h: np.ones(64, dtype=bool) for h in HORIZONS}
    per_arm = {arm: inventory(arm, valid_by_horizon) for arm in ARMS}
    return {
        "schema": "caissa.v212.objective-gradient-elementwise-panel.v01",
        "mask_fixture": "all 64 rows valid at H1/H2/H4; illustrative only",
        "arms": per_arm,
        "panel_total_multiplications_per_arm": {
            arm: details["candidate_array_multiplications_total"]
            for arm, details in per_arm.items()
        },
        "limitations": [
            "Full-valid synthetic mask formula only; not the frozen 20×87 schedule.",
            "Per-arm counts cover only this target-gradient multiplier and are not total training FLOPs.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
