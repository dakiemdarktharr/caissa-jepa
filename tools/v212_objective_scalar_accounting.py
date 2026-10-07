"""Scalar arithmetic inventory for V2.12 horizon objective weighting.

This source-shape subcounter covers scalar denominator weights, per-horizon
scales, loss accumulation, and scalar gradient coefficients in ``loss_grad``.
Array arithmetic, reductions, the root regularizer's total-loss weighting,
matrix products, and diagnostics belong to other inventories. No model or
numeric data is evaluated here.
"""
from __future__ import annotations

import json

import numpy as np

from .v212_model_matmul_flop_accounting import ARMS, JEPA_HORIZONS, _validated_masks


HORIZONS = (1, 2, 4)


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray]) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    _, masks = _validated_masks(valid_by_horizon)
    rows = {h: int(masks[h].sum()) for h in HORIZONS}
    if arm == "direct-leaf-value" and rows[4] == 0:
        raise ValueError("direct-leaf schedule requires at least one valid H4 row")

    counts = {
        "root_value_gradient_coefficient_divisions": 1,
        "denominator_weight_multiplications": 0,
        "denominator_python_sum_additions": 0,
        "per_horizon_scale_divisions": 0,
        "pooled_loss_scalar_multiplications": 0,
        "pooled_loss_scalar_divisions": 0,
        "pooled_loss_accumulation_additions": 0,
        "gradient_coefficient_scalar_multiplications": 0,
        "gradient_coefficient_scalar_divisions": 0,
        "combined_objective_additions": 0,
    }

    if arm == "direct-leaf-value":
        # The H4 guard guarantees a nonempty leaf for each accepted batch.
        counts["gradient_coefficient_scalar_divisions"] += 1  # 2.0 / len(pred)
        counts["combined_objective_additions"] += 1  # total += leaf_loss
    else:
        rollout_horizons = JEPA_HORIZONS.get(arm, ())
        target_horizons = HORIZONS if arm == "recursive-raw-state" else rollout_horizons

        # Both denominator comprehensions run even when the result is zero.
        for denominator_horizons in (HORIZONS, target_horizons):
            counts["denominator_weight_multiplications"] += len(denominator_horizons)
            counts["denominator_python_sum_additions"] += len(denominator_horizons)

        outcome_calls = sum(rows[h] > 0 for h in HORIZONS)
        target_calls = sum(rows[h] > 0 for h in target_horizons)
        counts["per_horizon_scale_divisions"] = outcome_calls + target_calls
        counts["pooled_loss_scalar_multiplications"] = outcome_calls + target_calls
        counts["pooled_loss_scalar_divisions"] = target_calls
        counts["pooled_loss_accumulation_additions"] = outcome_calls + target_calls

        # Outcome gradients form (2 * scale); target gradients form
        # ((2 * scale) / feature_or_latent_width).
        counts["gradient_coefficient_scalar_multiplications"] = outcome_calls + target_calls
        counts["gradient_coefficient_scalar_divisions"] = target_calls
        # outcome_loss + rollout_loss + raw_loss, then total += that value.
        counts["combined_objective_additions"] = 3

    return {
        "schema": "caissa.v212.objective-scalar-accounting.v01",
        "arm": arm,
        "scope": "scalar horizon-objective weighting and gradient coefficients per 64-window scheduled invocation",
        "valid_rows_by_horizon": rows,
        "candidate_fp_scalar_operations_per_invocation": counts,
        "candidate_fp_scalar_operations_total": sum(counts.values()),
        "counting_assumptions": [
            "Python built-in sum over k weighted terms contributes k scalar additions, including the addition to its initial zero.",
            "The outcome and target denominator comprehensions execute for every non-direct-leaf call, including empty-mask batches.",
            "A per-horizon scale and loss accumulation execute only when that horizon mask is nonempty.",
            "Each enabled nonempty latent/raw target loss divides its pooled squared-error sum by target width before scalar weighting.",
            "The shared root-value gradient always constructs the scalar coefficient 2.0 / batch_size once.",
            "The direct-leaf scheduled contract requires nonempty valid H4; its coefficient is one scalar division and total += leaf_loss is one scalar addition.",
            "Counts include only Python/NumPy scalar arithmetic explicitly identified in the pooled horizon objective; array elementwise work and reductions are delegated.",
        ],
        "limitations": [
            "This is a source-level candidate subcounter, not a loaded-runtime trace.",
            "The denominator combines float horizon weights with integer mask counts; the listed multiplications and additions are scalar floating-point candidates under the declared convention.",
            "Does not count branch/control/indexing, int mask counts, array operations, reductions, regularizer weighting, policy/root base losses, matrix products, or optimizer work.",
            "It cannot establish full graph coverage, six-arm compute parity, or authorize profiling or fitting.",
        ],
    }


def accounting(valid_by_horizon: dict[int, np.ndarray] | None = None) -> dict:
    if valid_by_horizon is None:
        valid_by_horizon = {h: np.ones(64, dtype=bool) for h in HORIZONS}
    return {
        "schema": "caissa.v212.objective-scalar-panel.v01",
        "mask_fixture": "all 64 rows valid at H1/H2/H4; illustrative only",
        "arms": {arm: inventory(arm, valid_by_horizon) for arm in ARMS},
        "panel_total_operations_per_arm": {
            arm: inventory(arm, valid_by_horizon)["candidate_fp_scalar_operations_total"]
            for arm in ARMS
        },
        "limitations": [
            "Full-valid synthetic mask formula only; not the frozen schedule or a parity result.",
            "The per-arm totals cover only this scalar horizon-objective subcounter and are not comparable as total training compute.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
