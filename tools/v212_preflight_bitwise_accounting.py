"""Source-shape cardinalities for Boolean bitwise operators in preflight.

This counts output elements for the explicit ``&`` and ``|`` AST sites in
``preflight_batch``. It is a native element-cardinality inventory, not a FLOP
count or a NumPy runtime-cost estimate. Comparisons, Boolean inversion,
reductions, indexing, and control flow remain separate.
"""
from __future__ import annotations

import json

from two_player.games import ACTION_SIZE


SCHEMA = "caissa.v212.preflight-bitwise-cardinality.v01"
HORIZON_STEPS = 4
HORIZONS = (1, 2, 4)


def accounting(batch_size: int = 64) -> dict:
    """Return output-element cardinalities for one structurally valid batch."""
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    n = batch_size
    action_elements = n * HORIZON_STEPS * ACTION_SIZE
    per_site = {
        "transition_consistency_and_invalid_mask": 2 * n * HORIZON_STEPS,
        "role_pair_and_alternation_masks": 2 * n * (HORIZON_STEPS - 1),
        "action_range_or": action_elements,
        "action_binary_and": action_elements,
        "horizon_complete_prefix_and": n * sum(HORIZONS),
        "horizon_validity_and": 2 * n * len(HORIZONS),
        "missing_target_count_and_or": 3 * n * len(HORIZONS),
    }
    total = sum(per_site.values())
    expected = 556 * n
    if total != expected:
        raise AssertionError("preflight bitwise cardinality formula is inconsistent")

    return {
        "schema": SCHEMA,
        "scope": "explicit Boolean BitAnd/BitOr output elements in one preflight_batch call",
        "batch_size": n,
        "source_bitwise_ast_sites": 12,
        "output_elements_by_site_family": per_site,
        "total_output_elements": total,
        "units": "Boolean-array output elements; not FLOPs or runtime instructions",
        "assumptions": [
            "The successful path reaches all fixed-shape mask expressions.",
            "Each BitAnd/BitOr output has the broadcast shape shown by its source operands.",
            "Horizon expressions execute once for each configured horizon (1, 2, 4).",
            "Python short-circuit and rejection paths can skip later expressions on malformed batches.",
        ],
        "coverage": {
            "all_preflight_bitand_bitor_sites_reconciled": True,
            "comparison_element_evaluations_counted": False,
            "boolean_inversion_elements_counted": False,
            "reduction_indexing_and_control_cost_counted": False,
            "runtime_cost_verified": False,
            "complete_preflight_inventory": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
