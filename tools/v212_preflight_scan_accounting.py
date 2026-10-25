"""Source-shaped counts for the repeated V2.12 model preflight scan.

This reports only input cardinalities and predicate-element counts visible in
``preflight_batch``. It is not a kernel trace, runtime-cost estimate, dataset
preflight count, or FLOP counter.
"""
from __future__ import annotations

from two_player.games import ACTION_SIZE, FEATURE_SIZE


SCHEMA = "caissa.v212.preflight-scan-accounting.v01"
HORIZON_STEPS = 4
FINITE_ARRAY_CALLS_PER_PREFLIGHT = 12
PREFLIGHT_HORIZONS = (1, 2, 4)


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
    array_comparisons = {
        "action_range_and_binary_checks": 4 * action_elements,
        "policy_index_range": 2 * n,
        "actor_alternation": n * (HORIZON_STEPS - 1),
        "one_hot_count_domains": action_rows,
    }
    horizon_mask_inversions = n * len(PREFLIGHT_HORIZONS) * 5
    boolean_inversions_by_family = {
        "legal_and_value_masks": 2 * n + n + n * HORIZON_STEPS,
        "transition_masks": 3 * action_rows,
        "horizon_masks": horizon_mask_inversions,
    }
    fixed_boolean_inversion_elements = sum(boolean_inversions_by_family.values())
    actor_membership_inversion_elements = {
        "minimum": 0,
        "maximum": action_rows,
        "assumption": "selected actor rows equal transition_exists.sum(); no positive lower bound is implied",
    }
    scalar_shape_comparison_site_calls = 3 + FINITE_ARRAY_CALLS_PER_PREFLIGHT
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
        "comparison_elements_by_site_family": array_comparisons,
        "array_comparison_element_evaluations": sum(array_comparisons.values()),
        "boolean_invert_ast_site_count": 13,
        "boolean_invert_site_occurrences_per_successful_call": 8 + 5 * len(PREFLIGHT_HORIZONS),
        "boolean_invert_elements_by_family": boolean_inversions_by_family,
        "fixed_boolean_invert_output_elements": fixed_boolean_inversion_elements,
        "selected_actor_membership_invert_output_elements": actor_membership_inversion_elements,
        "boolean_invert_output_elements_interval": {
            "minimum": fixed_boolean_inversion_elements,
            "maximum": fixed_boolean_inversion_elements + action_rows,
        },
        "scalar_shape_comparison_site_calls": scalar_shape_comparison_site_calls,
        "finite_array_shape_comparison_calls": FINITE_ARRAY_CALLS_PER_PREFLIGHT,
        "comparison_ast_site_count": 13,
        "comparison_ast_site_occurrences_per_successful_call": 12 + FINITE_ARRAY_CALLS_PER_PREFLIGHT,
        "predicate_count_assumption": (
            "array counts assume a successful batch reaches all predicate operands; invalid batches may short-circuit earlier; one-hot count comparisons operate on disjoint present/absent transitions"
        ),
        "coverage": {
            "complete_preflight_inventory": False,
            "units": "array input elements, output rows, and predicate-element evaluations; not FLOPs",
            "omitted": [
                "legal-action and value-domain reductions/membership internals, actor-role validity checks, transition/terminal predicates, and mask reductions",
                "row-wise terminal scans, indexing, allocation, copies, and control flow",
                "NumPy implementation/runtime cost and one-time dataset-level preflight",
            ],
        },
    }
