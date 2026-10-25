"""Finite-difference verification for the Counterplay V2.12 objective.

This is a synthetic mathematical check only. It does not fit parameters,
read research data, create checkpoints, or report an experimental result.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import time

import numpy as np

from two_player.v212_model import ARMS, HORIZONS, V212Config, V212Model, preflight_batch


EPSILON = 1e-6
ABS_TOLERANCE = 1e-7
REL_TOLERANCE = 1e-4


def _synthetic_batch():
    fixture_path = Path(__file__).resolve().parents[1] / "tests" / "test_v212_model.py"
    spec = importlib.util.spec_from_file_location("counterplay_gradient_fixture", fixture_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the reviewed synthetic gradient fixture")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    return fixture.synthetic_batch()


def _mixed_horizon_batch():
    batch = _synthetic_batch()
    # Row 0 supports H1/H2/H4, row 1 supports H1/H2, and row 2 supports H1.
    # A missing transition also removes all later action and actor records.
    for row, first_missing_step in ((1, 2), (2, 1)):
        batch["transition_exists"][row, first_missing_step:] = False
        batch["transition_valid"][row, first_missing_step:] = False
        batch["target_exists"][row, first_missing_step:] = False
        batch["actions"][row, first_missing_step:] = 0.0
        batch["actors"][row, first_missing_step:] = 0.0
    masks = preflight_batch(batch)["valid"]
    counts = {h: int(masks[h].sum()) for h in HORIZONS}
    if counts != {1: 3, 2: 2, 4: 1}:
        raise AssertionError(f"unexpected mixed horizon masks: {counts}")
    return batch, counts


def _activity(model, batch):
    z = model._encode(batch["x"])
    centered = z - z.mean(axis=0, keepdims=True)
    std = np.sqrt(np.mean(centered ** 2, axis=0) + 1e-4)
    shortfall = np.maximum(0.0, 0.1 - std)
    covariance = centered.T @ centered / len(centered)
    offdiag = covariance - np.diag(np.diag(covariance))
    return {
        "variance_active_coordinates": int(np.count_nonzero(shortfall)),
        "covariance_loss_unweighted": float(np.sum(offdiag ** 2) / z.shape[1]),
    }


def run_checks():
    """Run coordinate and directional checks for every trainable tensor."""
    mixed, mask_counts = _mixed_horizon_batch()
    covariance = _synthetic_batch()
    covariance["x"] *= 10.0
    scenarios = (
        ("variance-active-mixed-masks", mixed, 31),
        ("covariance-active-x10-seed9", covariance, 9),
    )
    checks = []
    coverage = {}
    start = time.perf_counter()
    for scenario, batch, seed in scenarios:
        for arm in ARMS:
            model = V212Model(V212Config(arm=arm, seed=seed))
            activity = _activity(model, batch)
            if scenario.startswith("variance") and not activity["variance_active_coordinates"]:
                raise AssertionError("variance fixture did not activate the variance penalty")
            if scenario.startswith("covariance") and activity["covariance_loss_unweighted"] <= 1e-6:
                raise AssertionError("x*10 fixture did not activate covariance penalty")
            target_before = {key: value.copy() for key, value in model.target.items()}
            _, gradients = model.loss_grad(batch)
            case_coverage = []
            for tensor_name, parameter in model.params.items():
                analytic_gradient = gradients[tensor_name]
                coordinate = np.unravel_index(
                    int(np.argmax(np.abs(analytic_gradient))), analytic_gradient.shape
                )
                original = float(parameter[coordinate])
                try:
                    parameter[coordinate] = original + EPSILON
                    plus = model.loss_grad(batch)[0]["loss"]
                    parameter[coordinate] = original - EPSILON
                    minus = model.loss_grad(batch)[0]["loss"]
                finally:
                    parameter[coordinate] = original
                numeric = float((plus - minus) / (2.0 * EPSILON))
                analytic = float(analytic_gradient[coordinate])
                tolerance = ABS_TOLERANCE + REL_TOLERANCE * max(abs(analytic), abs(numeric))
                checks.append({
                    "scenario": scenario, "arm": arm, "tensor": tensor_name,
                    "kind": "coordinate", "coordinate": [int(value) for value in coordinate],
                    "analytic": analytic, "numeric": numeric,
                    "absolute_error": abs(analytic - numeric),
                    "tolerance": tolerance,
                    "normalized_error": abs(analytic - numeric) / tolerance,
                    "passed": abs(analytic - numeric) <= tolerance,
                })

                direction_rng = np.random.default_rng(
                    seed * 1_000_003 + ARMS.index(arm) * 1009 + len(case_coverage)
                )
                direction_origin = parameter.copy()
                direction = direction_rng.normal(size=parameter.shape)
                direction /= np.linalg.norm(direction)
                analytic_directional = float(np.sum(analytic_gradient * direction))
                try:
                    parameter[...] += EPSILON * direction
                    plus = model.loss_grad(batch)[0]["loss"]
                    parameter[...] -= 2.0 * EPSILON * direction
                    minus = model.loss_grad(batch)[0]["loss"]
                finally:
                    parameter[...] = direction_origin
                numeric_directional = float((plus - minus) / (2.0 * EPSILON))
                tolerance = ABS_TOLERANCE + REL_TOLERANCE * max(
                    abs(analytic_directional), abs(numeric_directional)
                )
                checks.append({
                    "scenario": scenario, "arm": arm, "tensor": tensor_name,
                    "kind": "directional", "analytic": analytic_directional,
                    "numeric": numeric_directional,
                    "absolute_error": abs(analytic_directional - numeric_directional),
                    "tolerance": tolerance,
                    "normalized_error": abs(analytic_directional - numeric_directional) / tolerance,
                    "passed": abs(analytic_directional - numeric_directional) <= tolerance,
                })
                case_coverage.append(tensor_name)
            for key, value in model.target.items():
                np.testing.assert_array_equal(value, target_before[key])
            coverage[f"{scenario}/{arm}"] = case_coverage
    elapsed = time.perf_counter() - start
    errors = [item["normalized_error"] for item in checks]
    return {
        "checks": checks,
        "coverage": coverage,
        "coverage_arm_scenarios": len(coverage),
        "coverage_tensor_count": sum(len(tensors) for tensors in coverage.values()),
        "finite_difference_checks": len(checks),
        "worst_normalized_error": max(errors, default=0.0),
        "failures": [item for item in checks if not item["passed"]],
        "seconds": elapsed,
        "epsilon": EPSILON,
        "absolute_tolerance": ABS_TOLERANCE,
        "relative_tolerance": REL_TOLERANCE,
        "mixed_horizon_mask_counts": mask_counts,
        "scenario_activity": {
            scenario: _activity(V212Model(V212Config(arm=ARMS[0], seed=seed)), batch)
            for scenario, batch, seed in scenarios
        },
        "synthetic_only": True,
        "optimizer_updates": 0,
    }


def main():
    report = run_checks()
    print(json.dumps(report, sort_keys=True, indent=2))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
