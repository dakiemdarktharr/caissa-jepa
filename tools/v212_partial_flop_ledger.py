"""Owner-reconciled partial FLOP ledger for one V2.12 model invocation.

This composes only source-level FP arithmetic with a sole owner in the current
subcounter suite. The result is deliberately marked incomplete: it does not
represent the frozen 20×87 schedule, loaded NumPy/LAPACK kernels, or total
training FLOPs and cannot establish six-arm compute parity.
"""
from __future__ import annotations

import json

import numpy as np

from . import (
    v212_effective_rank_branch_accounting as effective_rank,
    v212_gradient_accumulation_accounting as gradient_accumulation,
    v212_model_activation_flop_accounting as activation,
    v212_model_loss_residual_accounting as residual,
    v212_model_matmul_flop_accounting as matmul,
    v212_model_reduction_shape_accounting as reduction,
    v212_model_square_flop_accounting as squares,
    v212_objective_gradient_elementwise_accounting as target_gradient,
    v212_objective_scalar_accounting as objective_scalar,
    v212_optimizer_flop_accounting as optimizer,
    v212_policy_softmax_accounting as policy,
    v212_regularizer_elementwise_accounting as regularizer,
)


SCHEMA = "caissa.v212.partial-flop-owner-ledger.v01"
ARMS = matmul.ARMS
HORIZONS = matmul.HORIZONS
SCHEDULE_UPDATES = 20 * 87

OWNERSHIP = {
    "explicit_dense_matmuls": "model_matmul_flops",
    "fixed_array_square_sites": "model_square_multiplications",
    "loss_residual_subtractions": "loss_residual_subtractions",
    "affine_bias_and_activation_derivatives": "activation_excluding_squares",
    "ordinary_reduction_additions_and_divisions": "ordinary_reductions",
    "policy_softmax_nll_elementwise": "policy_elementwise",
    "root_regularizer_elementwise": "regularizer_elementwise",
    "pooled_horizon_objective_scalars": "horizon_objective_scalars",
    "gradient_buffer_additions": "gradient_accumulation",
    "target_gradient_coefficient_multiplications": "target_gradient_multiplications",
    "scratch_adam_ema": "optimizer_interval",
    "effective_rank_selected_set": "effective_rank_interval",
}


def _all_valid_masks() -> dict[int, np.ndarray]:
    return {h: np.ones(64, dtype=bool) for h in HORIZONS}


def _sum_fields(row: dict, names: tuple[str, ...]) -> int:
    return sum(row[name] for name in names)


def _arm_inventory(arm: str, masks: dict[int, np.ndarray]) -> dict:
    mm = matmul.inventory(arm, masks)
    sq = squares.inventory(arm, masks)
    rs = residual.inventory(arm, masks)
    act = activation.inventory(arm, masks)
    red = reduction.inventory(
        arm, masks, effective_rank_active=False,
        effective_rank_nonzero_eigenvalues=0,
    )
    pol = policy.accounting(scheduled_updates=1)["per_invocation"]
    reg = regularizer.accounting(scheduled_updates=1)["per_invocation"]
    scalar = objective_scalar.inventory(arm, masks)
    accum = gradient_accumulation.inventory(arm, masks)
    target = target_gradient.inventory(arm, masks)

    ordinary = red["candidate_addition_owner_totals"]["reduction_inventory"]
    std = red["latent_std_candidate_operations"]["owner_components"]
    derivative_without_square = (
        act["tanh_derivative_flops"]
        - act["tanh_derivative_breakdown"]["squares_as_multiplications"]
    )
    components = {
        "model_matmul_flops": mm["all_explicit_matmul_flops"],
        "model_square_multiplications": sq["candidate_square_multiplications"],
        "loss_residual_subtractions": rs["residual_subtraction_flops"],
        "activation_excluding_squares": (
            act["bias_addition_flops"] + derivative_without_square
            + act["pre_derivative_gradient_scale_multiplications"]
        ),
        "ordinary_reductions": (
            ordinary
            + red["candidate_mean_divisions_owner_total"]
            + std["latent_std_elementwise_deviation_subtractions"]
            + std["latent_std_population_variance_divisions"]
        ),
        "policy_elementwise": _sum_fields(pol, (
            "shift_subtractions", "probability_divisions",
            "policy_gradient_batch_normalization_divisions",
            "nll_residual_subtractions", "policy_label_gradient_subtractions",
        )),
        "regularizer_elementwise": _sum_fields(reg, (
            "candidate_fp_array_additions", "candidate_fp_array_subtractions",
            "candidate_fp_array_multiplications", "candidate_fp_array_divisions",
            "candidate_fp_scalar_additions", "candidate_fp_scalar_multiplications",
            "candidate_fp_scalar_divisions",
        )),
        "horizon_objective_scalars": scalar["candidate_fp_scalar_operations_total"],
        "gradient_accumulation": accum["candidate_array_additions_total"],
        "target_gradient_multiplications": target["candidate_array_multiplications_total"],
    }

    rank_low = effective_rank.branch_work(active=False, selected_eigenvalues=0)
    rank_high = effective_rank.branch_work(active=True, selected_eigenvalues=32)
    opt = optimizer._one_update(arm)["floating_point_arithmetic"]["total_flops"]
    branch_intervals = {
        "effective_rank_interval": {
            "lower": rank_low["candidate_fp_additions"]
                     + rank_low["fp_multiplications"]
                     + rank_low["fp_divisions"],
            "upper": rank_high["candidate_fp_additions"]
                     + rank_high["fp_multiplications"]
                     + rank_high["fp_divisions"],
            "scope": "selected-set arithmetic only; excludes comparisons/log/exp and eigensolver",
        },
        "optimizer_interval": {
            "lower": opt["norm_le_5"],
            "upper": opt["norm_gt_5"],
            "scope": "one scratch Adam/EMA invocation; zero norm is in norm_le_5",
        },
    }
    known_base = sum(components.values())
    lower = known_base + branch_intervals["effective_rank_interval"]["lower"] \
        + branch_intervals["optimizer_interval"]["lower"]
    upper = known_base + branch_intervals["effective_rank_interval"]["upper"] \
        + branch_intervals["optimizer_interval"]["upper"]
    return {
        "components_candidate_flops": components,
        "branch_candidate_flop_intervals": branch_intervals,
        "partial_source_candidate_flops": {"lower": lower, "upper": upper},
        "non_flop_or_unconverted_work": {
            "tanh_elements": act["tanh_calls_element_count"],
            "policy_max_comparisons": pol["candidate_row_max_comparisons"],
            "policy_exp_elements": pol["exp_elements"],
            "policy_log_elements": pol["nll_log_elements"],
            "regularizer_max_comparisons": reg["candidate_maximum_comparisons"],
            "regularizer_sqrt_elements": reg["sqrt_output_elements_not_converted_to_flops"],
            "latent_std_sqrt_calls": std["transcendental_sqrt_calls"],
            "effective_rank_log_calls": [rank_low["log_calls"], rank_high["log_calls"]],
            "effective_rank_exp_calls": [rank_low["exp_calls"], rank_high["exp_calls"]],
            "optimizer_scalar_powers": 2,
            "optimizer_square_roots": optimizer._one_update(arm)[
                "separately_reported_operations"]["square_roots"
            ],
        },
    }


def accounting(valid_by_horizon: dict[int, np.ndarray] | None = None) -> dict:
    """Compose the currently owned candidate components for one invocation.

    If masks are omitted, all-valid 64-row masks are used as an illustrative
    formula fixture only. No schedule-level multiplication is performed.
    """
    if valid_by_horizon is None:
        valid_by_horizon = _all_valid_masks()
        fixture = "illustrative all-64-valid masks at H1/H2/H4"
    else:
        fixture = "caller-supplied masks; must be replay-derived before D03 use"
    per_arm = {arm: _arm_inventory(arm, valid_by_horizon) for arm in ARMS}
    return {
        "schema": SCHEMA,
        "scope": "owner-reconciled source-covered candidate FP arithmetic for one 64-window model and scratch-optimizer invocation",
        "mask_fixture": fixture,
        "scheduled_updates_not_aggregated": SCHEDULE_UPDATES,
        "ownership": dict(OWNERSHIP),
        "arms": per_arm,
        "coverage": {
            "complete": False,
            "parity_eligible": False,
            "graph_freeze_eligible": False,
            "excluded_or_unresolved": [
                "np.linalg.eigvalsh and actual linked LAPACK operation bounds",
                "loaded NumPy reduction/tree and actual runtime/backend fingerprints",
                "scalar powers and transcendental FLOP conversion",
                "comparisons, integer/indexing, finite checks, preflight and control-flow work",
                "copies, allocations, validation, serialization and unsupported operators",
                "replay-derived 20-seed × 87-update masks and mask-dependent schedule aggregation",
                "integrated trainer trace binding adapter, objective, optimizer and scheduled updates",
            ],
            "warning": "These partial intervals are not total training FLOPs and cannot establish the ≤5% parity gate.",
            "interval_semantics": "Bounds cover only the listed source-owned candidate components; they are not bounds on total training FLOPs.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(accounting(), sort_keys=True, indent=2, allow_nan=False))
