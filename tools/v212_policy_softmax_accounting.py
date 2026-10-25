"""Source-level elementwise inventory for the V2.12 policy softmax path.

This subcounter covers fixed-shape policy-logit masking, row-max comparison
candidates, normalization, NLL elementwise work, and the policy-gradient
label subtraction. The two denominator reductions and NLL mean belong to the
separate reduction-shape inventory; matmuls and all other graph work are
excluded. No logits or model values are created or executed here.
"""
from __future__ import annotations

import json


BATCH = 64
POLICY = 65
DEFAULT_SCHEDULE_UPDATES = 20 * 87


def accounting(scheduled_updates: int = DEFAULT_SCHEDULE_UPDATES) -> dict:
    """Count policy-softmax elementwise work for one batch and schedule."""
    if type(scheduled_updates) is not int or scheduled_updates <= 0:
        raise ValueError("scheduled_updates must be a positive integer")

    logit_elements = BATCH * POLICY
    row_elements = BATCH
    per_invocation = {
        "policy_logit_elements": logit_elements,
        "mask_select_elements": logit_elements,
        "row_max_reductions": row_elements,
        "candidate_row_max_comparisons": BATCH * (POLICY - 1),
        "shift_subtractions": logit_elements,
        "exp_elements": logit_elements,
        "probability_divisions": logit_elements,
        "policy_gradient_batch_normalization_divisions": logit_elements,
        "nll_log_elements": row_elements,
        "nll_residual_subtractions": row_elements,
        "policy_label_gradient_subtractions": row_elements,
        "denominator_reductions_owned_by_reduction_inventory": 2,
        "nll_mean_reduction_owned_by_reduction_inventory": 1,
    }
    per_arm_schedule = {
        key: value * scheduled_updates
        for key, value in per_invocation.items()
        if key not in {
            "denominator_reductions_owned_by_reduction_inventory",
            "nll_mean_reduction_owned_by_reduction_inventory",
        }
    }
    per_arm_schedule.update({
        "denominator_reduction_invocations_owned_by_reduction_inventory": (
            per_invocation["denominator_reductions_owned_by_reduction_inventory"]
            * scheduled_updates
        ),
        "nll_mean_reduction_invocations_owned_by_reduction_inventory": (
            per_invocation["nll_mean_reduction_owned_by_reduction_inventory"]
            * scheduled_updates
        ),
    })
    return {
        "schema": "caissa.v212.policy-softmax-elementwise.v01",
        "scope": "fixed-shape root policy softmax/NLL elementwise work per 64-window invocation, per arm",
        "scheduled_updates_per_arm": scheduled_updates,
        "per_invocation": per_invocation,
        "schedule_per_arm": per_arm_schedule,
        "counting_assumptions": [
            "A max over 65 values per row has 64 candidate pairwise comparisons; this is a semantic comparison count, not a loaded NumPy kernel instruction count.",
            "Exp and log values are reported as transcendental element counts, not converted to FLOPs.",
            "One shift subtraction, probability division, NLL residual subtraction, and label-gradient subtraction is counted per corresponding array element.",
            "The two exp_logits denominator sums and the NLL mean are excluded here and owned by the separate reduction inventory.",
            "Policy-head and reverse-pass matrix products are excluded and owned by the matmul inventory.",
        ],
        "limitations": [
            "Source-level shape formula only; no logits, model, data, or mask schedule was evaluated.",
            "The schedule total assumes the fixed 64-row policy path executes for every scheduled update in all six arms.",
            "This subcounter overlaps no reduction or matmul subtotal and cannot establish total six-arm compute parity or authorize a profile/fit.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
