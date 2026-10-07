"""Source-shaped counts for the repeated V2.12 model preflight scan.

This reports only input cardinalities and predicate-element counts visible in
``preflight_batch``. It is not a kernel trace, runtime-cost estimate, dataset
preflight count, or FLOP counter.
"""
from __future__ import annotations

from two_player.games import ACTION_SIZE, FEATURE_SIZE


SCHEMA = "caissa.v212.preflight-scan-accounting.v01"
HORIZON_STEPS = 4


def accounting(batch_size: int = 64) -> dict:
    """Return source-level preflight scan cardinalities for one model call."""
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    n = batch_size
    numeric_finite_arrays = {
        "x": n * FEATURE_SIZE,
        "policy": n,
        "value": n,
        "actions": n * HORIZON_STEPS * ACTION_SIZE,
        "actors": n * HORIZON_STEPS,
        "future_x": n * HORIZON_STEPS * FEATURE_SIZE,
        "future_value": n * HORIZON_STEPS,
    }
    action_elements = n * HORIZON_STEPS * ACTION_SIZE
    action_rows = n * HORIZON_STEPS
    return {
        "schema": SCHEMA,
        "scope": "one successful valid-batch preflight_batch path inside one loss_grad invocation",
        "batch_size": n,
        "model_loss_grad_preflight_calls": 1,
        "numeric_finite_check_arrays": len(numeric_finite_arrays),
        "numeric_finite_check_elements_by_array": numeric_finite_arrays,
        "numeric_finite_check_elements": sum(numeric_finite_arrays.values()),
        "action_count_nonzero_input_elements": action_elements,
        "action_count_nonzero_output_rows": action_rows,
        "action_domain_predicate_element_evaluations": 4 * action_elements,
        "action_row_count_predicate_evaluations": action_rows,
        "predicate_count_assumption": (
            "counts assume a valid batch reaches every conditional operand; invalid batches may short-circuit earlier"
        ),
        "coverage": {
            "complete_preflight_inventory": False,
            "units": "array input elements, output rows, and predicate-element evaluations; not FLOPs",
            "omitted": [
                "legal-action, value-domain, actor-role, transition, and mask predicates",
                "row-wise terminal scans, indexing, allocation, copies, and control flow",
                "NumPy implementation/runtime cost and one-time dataset-level preflight",
            ],
        },
    }
