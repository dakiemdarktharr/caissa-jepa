"""Reduction-shape inventory for the V2.12 objective source.

This tool records the shapes and branches of NumPy reductions in the no-update
objective, including the pinned NumPy 2.4.6 ``std`` implementation's mean,
squared deviations, sum, variance division, and square root. Counts remain
candidate arithmetic, not accepted runtime FLOPs; linked-LAPACK work is not
covered.
"""
from __future__ import annotations

import json
from math import prod

import numpy as np

from .v212_model_matmul_flop_accounting import (
    ARMS, JEPA_HORIZONS, _validated_masks,
)


BATCH = 64
LATENT = 32
POLICY = 65
FEATURES = 198
HORIZONS = (1, 2, 4)
SHARED_PARAMETER_SHAPES = {
    "ew": (FEATURES, LATENT), "eb": (LATENT,),
    "pw": (LATENT, POLICY), "pb": (POLICY,),
    "vw": (LATENT, 1), "vb": (1,),
}
PREDICTOR_PARAMETER_SHAPES = {"fw": (104, LATENT), "fb": (LATENT,)}
DECODER_PARAMETER_SHAPES = {"dw": (LATENT, FEATURES), "db": (FEATURES,)}


def _shape_reduction(shape: tuple[int, ...], axis: int | None) -> tuple[int, int]:
    input_elements = prod(shape)
    if axis is None:
        return input_elements, 1
    normalized_axis = axis if axis >= 0 else len(shape) + axis
    if normalized_axis < 0 or normalized_axis >= len(shape):
        raise ValueError("reduction axis is outside the input rank")
    output_elements = prod(shape[:normalized_axis] + shape[normalized_axis + 1:])
    return input_elements, output_elements


def inventory(arm: str, valid_by_horizon: dict[int, np.ndarray], *,
              effective_rank_active: bool = True,
              effective_rank_nonzero_eigenvalues: int = 32) -> dict:
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    if type(effective_rank_active) is not bool:
        raise ValueError("effective_rank_active must be Boolean")
    if (type(effective_rank_nonzero_eigenvalues) is not int
            or not 0 <= effective_rank_nonzero_eigenvalues <= LATENT):
        raise ValueError("effective-rank active count must be between 0 and 32")
    _, masks = _validated_masks(valid_by_horizon)
    rows = {h: int(masks[h].sum()) for h in HORIZONS}
    records = []

    def add(site: str, kind: str, shape: tuple[int, ...], axis: int | None = None,
            calls: int = 1) -> None:
        if type(calls) is not int or calls < 0:
            raise ValueError("reduction call count must be a nonnegative integer")
        inputs, outputs = _shape_reduction(shape, axis)
        records.append({
            "site": site,
            "kind": kind,
            "input_shape": list(shape),
            "axis": axis,
            "calls": calls,
            "input_elements_per_call": inputs,
            "output_elements_per_call": outputs,
            "candidate_additions": max(inputs - outputs, 0) * calls,
            "candidate_mean_divisions": outputs * calls if kind == "mean" else 0,
        })

    # Root regularization and policy/value diagnostics run for every arm.
    add("regularizer.centered_batch_mean", "mean", (BATCH, LATENT), axis=0)
    add("regularizer.coordinate_variance_mean", "mean", (BATCH, LATENT), axis=0)
    add("regularizer.variance_loss_mean", "mean", (LATENT,))
    add("regularizer.covariance_loss_sum", "sum", (LATENT, LATENT))
    add("regularizer.spectrum_sum", "sum", (LATENT,))
    rank_calls = int(effective_rank_active)
    add("regularizer.effective_rank_entropy_sum", "sum",
        (effective_rank_nonzero_eigenvalues,), calls=rank_calls)
    add("policy.softmax_denominator_for_probabilities", "sum",
        (BATCH, POLICY), axis=1)
    add("policy.softmax_denominator_for_nll", "sum",
        (BATCH, POLICY), axis=1)
    add("policy.nll_batch_mean", "mean", (BATCH,))
    add("root_value.mse_batch_mean", "mean", (BATCH,))
    add("diagnostic.latent_mean", "mean", (BATCH, LATENT), axis=0)
    add("policy.bias_gradient_sum", "sum", (BATCH, POLICY), axis=0)
    add("root_value.bias_gradient_sum", "sum", (BATCH, 1), axis=0)

    # NumPy 2.4.6 _std -> _var computes a keepdims mean, centers each input,
    # squares the deviations in place, sums them, divides by the population
    # count (ddof=0), and takes sqrt. z0 is float64 with shape (64, 32).
    std_elements = BATCH * LATENT
    add("diagnostic.latent_std.internal_mean", "mean",
        (BATCH, LATENT), axis=0)
    add("diagnostic.latent_std.squared_deviation_sum", "sum",
        (BATCH, LATENT), axis=0)

    gradient_shapes = dict(SHARED_PARAMETER_SHAPES)
    if arm != "direct-leaf-value":
        gradient_shapes.update(PREDICTOR_PARAMETER_SHAPES)
    if arm == "recursive-raw-state":
        gradient_shapes.update(DECODER_PARAMETER_SHAPES)
    for name, shape in gradient_shapes.items():
        add(f"diagnostic.gradient_norm_sum.{name}", "sum", shape)
    tensor_count = len(gradient_shapes)
    records.append({
        "site": "diagnostic.gradient_norm_python_scalar_sum",
        "kind": "python_scalar_sum",
        "input_shape": [tensor_count],
        "axis": None,
        "calls": 1,
        "input_elements_per_call": tensor_count,
        "output_elements_per_call": 1,
        # Python's sum(iterable) initializes its accumulator at integer zero,
        # then adds every yielded scalar, including the first norm term.
        "candidate_additions": tensor_count,
        "candidate_mean_divisions": 0,
    })

    if arm == "direct-leaf-value":
        leaf_rows = rows[4]
        add("direct_leaf.mse_mean", "mean", (leaf_rows,), calls=int(leaf_rows > 0))
        if leaf_rows:
            add("direct_leaf.value_bias_gradient_sum", "sum", (leaf_rows, 1), axis=0)
            add("direct_leaf.encoder_bias_gradient_sum", "sum",
                (leaf_rows, LATENT), axis=0)
    else:
        for h in HORIZONS:
            count = rows[h]
            calls = int(count > 0)
            add(f"outcome.h{h}.batch_mean", "mean", (count,), calls=calls)
            add(f"outcome.h{h}.pooled_sum", "sum", (count,), calls=calls)
            if count:
                add(f"outcome.h{h}.value_bias_gradient_sum", "sum",
                    (count, 1), axis=0)

        for h in JEPA_HORIZONS.get(arm, ()):
            count = rows[h] * LATENT
            calls = int(rows[h] > 0)
            add(f"latent.h{h}.batch_mean", "mean", (count,), calls=calls)
            add(f"latent.h{h}.pooled_sum", "sum", (count,), calls=calls)

        if arm == "recursive-raw-state":
            for h in HORIZONS:
                count = rows[h] * FEATURES
                calls = int(rows[h] > 0)
                add(f"raw_state.h{h}.batch_mean", "mean", (count,), calls=calls)
                add(f"raw_state.h{h}.pooled_sum", "sum", (count,), calls=calls)

        active_rows = {
            step: int(np.logical_or.reduce(
                [masks[h] for h in HORIZONS if h >= step]).sum())
            for step in range(1, 5)
        }
        for step, active_count in active_rows.items():
            calls = int(active_count > 0)
            if arm == "recursive-raw-state":
                add(f"backward.raw_encoder_bias_gradient_sum.step_{step}",
                    "sum", (active_count, LATENT), axis=0, calls=calls)
                add(f"backward.decoder_bias_gradient_sum.step_{step}",
                    "sum", (active_count, FEATURES), axis=0, calls=calls)
            add(f"backward.predictor_bias_gradient_sum.step_{step}",
                "sum", (active_count, LATENT), axis=0, calls=calls)

    add("backward.root_encoder_bias_gradient_sum", "sum",
        (BATCH, LATENT), axis=0)
    candidate_additions = sum(r["candidate_additions"] for r in records)
    candidate_divisions = sum(r["candidate_mean_divisions"] for r in records)
    std_candidate_subtractions = std_elements
    std_candidate_square_multiplications = std_elements
    std_candidate_variance_divisions = LATENT
    std_sqrt_transcendentals = LATENT
    return {
        "schema": "caissa.v212.model-reduction-shapes.v03",
        "scope": "shape inventory of source NumPy mean/sum calls in one 64-window objective invocation",
        "arm": arm,
        "horizon_valid_rows": rows,
        "gradient_tensor_count": tensor_count,
        "reduction_sites": records,
        "candidate_additions": candidate_additions,
        "candidate_mean_divisions": candidate_divisions,
        "latent_std_candidate_operations": {
            "input_shape": [BATCH, LATENT],
            "axis": 0,
            "ddof": 0,
            "mean_reduction_additions": (BATCH - 1) * LATENT,
            "mean_divisions": LATENT,
            "deviation_subtractions": std_candidate_subtractions,
            "squared_deviation_square_operations": std_candidate_square_multiplications,
            "squared_deviation_reduction_additions": (BATCH - 1) * LATENT,
            "population_variance_divisions": std_candidate_variance_divisions,
            "sqrt_transcendentals": std_sqrt_transcendentals,
            "candidate_fp_add_subtract_multiply_divide": (
                2 * (BATCH - 1) * LATENT + 2 * std_elements
                + LATENT + std_candidate_variance_divisions),
        },
        "data_dependent_branches": {
            "effective_rank_entropy_reduction_active": effective_rank_active,
            "effective_rank_entropy_input_elements": (
                effective_rank_nonzero_eigenvalues if effective_rank_active else 0),
        },
        "counting_assumptions": [
            "For an ordinary reduction, candidate additions are input_elements minus output_elements; the summation tree is not fixed here.",
            "The Python scalar gradient-norm sum counts one addition per parameter tensor because built-in sum starts at integer zero.",
            "A mean is provisionally modeled as one division per output element after its reduction.",
            "The two softmax denominator sums are separate source calls and are counted separately.",
            "The latent std expansion follows NumPy 2.4.6 _std/_var for float64 shape (64,32), axis 0, ddof 0; each square is provisionally one multiplication and each sqrt is reported separately.",
        ],
        "limitations": [
            "Analytical shape inventory only; no objective graph or data was executed.",
            "Candidate add/divide counts require independent review and a pinned NumPy reduction implementation before any D03 profile.",
            "The source-level std path is expanded, but the actually loaded NumPy build/reduction kernel, eigvalsh/LAPACK arithmetic, effective-rank transcendental costs, and other elementwise work remain unresolved or excluded.",
            "Boolean/integer preflight reductions and integer horizon-denominator sums are outside this floating-point inventory.",
            "This subcounter cannot establish total six-arm compute parity or authorize profile/fit.",
        ],
    }


def full_valid_batch(arm: str, *, effective_rank_active: bool = True,
                     effective_rank_nonzero_eigenvalues: int = 32) -> dict:
    full = np.ones(BATCH, dtype=bool)
    return inventory(arm, {h: full for h in HORIZONS},
                     effective_rank_active=effective_rank_active,
                     effective_rank_nonzero_eigenvalues=effective_rank_nonzero_eigenvalues)


if __name__ == "__main__":
    print(json.dumps({arm: full_valid_batch(arm) for arm in ARMS},
                     sort_keys=True, indent=2, allow_nan=False))
