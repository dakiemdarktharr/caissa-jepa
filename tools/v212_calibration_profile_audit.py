#!/usr/bin/env python3
"""Audit analytic covariance profiles from V2.12 calibration draft 02.

This serializes deterministic covariance/variance calculations only. It does
not draw random values or create datasets, roots, model outputs, scores, or
outcomes, and it does not authorize calibration.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence


ARM_IDS = ("V1", "V2", "C1", "C2", "C3", "C4", "C5")
PAIRS = tuple((v, c) for v in ARM_IDS[:2] for c in ARM_IDS[2:])
BANDS = ("low", "middle", "high")
SEED_RHO = 0.35
SLOT_RHO = 0.15
INTERACTION_RHO = -0.10
MATCHUP_RHO = -0.05
P5_SCALES = (1.50, 1.25, 0.75, 0.75, 0.75, 0.75, 0.75)

PROFILE_FRACTIONS = {
    "P1": {band: (0.75, 0.15, 0.10) for band in BANDS},
    "P2": {band: (0.15, 0.75, 0.10) for band in BANDS},
    "P3": {band: (1 / 3, 1 / 3, 1 / 3) for band in BANDS},
    "P4": {band: (0.10, 0.10, 0.80) for band in BANDS},
    "P5": {
        "low": (0.60, 0.20, 0.20),
        "middle": (1 / 3, 1 / 3, 1 / 3),
        "high": (0.20, 0.60, 0.20),
    },
}


def equicorrelation(size: int, rho: float) -> list[list[float]]:
    if size < 2 or not -1 / (size - 1) < rho < 1:
        raise ValueError("equicorrelation parameter is outside the PD range")
    return [[1.0 if i == j else rho for j in range(size)] for i in range(size)]


def _pair_margins(covariance: Sequence[Sequence[float]]) -> dict[str, float]:
    result = {}
    for candidate_index, candidate in enumerate(ARM_IDS[:2]):
        for control_index, control in enumerate(ARM_IDS[2:], start=2):
            variance = (
                covariance[candidate_index][candidate_index]
                + covariance[control_index][control_index]
                - 2 * covariance[candidate_index][control_index]
            )
            if variance <= 0:
                raise ArithmeticError("candidate-control margin variance is not positive")
            result[f"{candidate}-{control}"] = variance
    return result


def _scaled_covariance(
    target_mean_margin_variance: float,
    rho: float,
    scales: Sequence[float],
) -> tuple[list[list[float]], float, dict[str, float]]:
    correlation = equicorrelation(len(scales), rho)
    raw = [
        [scales[i] * correlation[i][j] * scales[j] for j in range(len(scales))]
        for i in range(len(scales))
    ]
    raw_margins = _pair_margins(raw)
    raw_mean = math.fsum(raw_margins.values()) / len(raw_margins)
    if raw_mean <= 0 or target_mean_margin_variance <= 0:
        raise ValueError("target and unscaled mean margin variances must be positive")
    scale_k = target_mean_margin_variance / raw_mean
    covariance = [[scale_k * value for value in row] for row in raw]
    margins = _pair_margins(covariance)
    if not _cholesky_positive(covariance):
        raise ArithmeticError("generated arm covariance is not positive definite")
    return covariance, scale_k, margins


def _cholesky_positive(matrix: Sequence[Sequence[float]]) -> bool:
    """Return whether a symmetric matrix admits a positive Cholesky factor."""
    try:
        _cholesky_factor(matrix)
    except (ValueError, ArithmeticError):
        return False
    return True


def _cholesky_factor(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    """Compute a deterministic lower Cholesky factor for a PD matrix."""
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    lower = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            if not math.isclose(matrix[i][j], matrix[j][i], abs_tol=1e-12):
                raise ValueError("matrix must be symmetric")
            residual = matrix[i][j] - math.fsum(
                lower[i][k] * lower[j][k] for k in range(j)
            )
            if i == j:
                if residual <= 0:
                    raise ArithmeticError("matrix is not positive definite")
                lower[i][j] = math.sqrt(residual)
            else:
                lower[i][j] = residual / lower[j][j]
    return lower


def profile_manifest() -> dict[str, object]:
    """Build the deterministic profile covariance audit manifest."""
    profiles: dict[str, object] = {}
    for profile, band_fractions in PROFILE_FRACTIONS.items():
        bands: dict[str, object] = {}
        for band in BANDS:
            seed_fraction, slot_fraction, interaction_fraction = band_fractions[band]
            scales = P5_SCALES if profile == "P5" else (1.0,) * len(ARM_IDS)
            components = {}
            for name, target, rho in (
                ("seed", seed_fraction, SEED_RHO),
                ("root_slot", slot_fraction, SLOT_RHO),
                ("seed_slot_arm", interaction_fraction / 2, INTERACTION_RHO),
            ):
                covariance, scale_k, pair_variances = _scaled_covariance(
                    target, rho, scales
                )
                components[name] = {
                    "target_mean_pair_margin_variance": target,
                    "equicorrelation": rho,
                    "scale_k": scale_k,
                    "covariance": covariance,
                    "pair_margin_variances": pair_variances,
                }
            matchup_variance = interaction_fraction / 2
            matchup_corr = equicorrelation(len(PAIRS), MATCHUP_RHO)
            matchup_cov = [
                [matchup_variance * value for value in row]
                for row in matchup_corr
            ]
            if not _cholesky_positive(matchup_cov):
                raise ArithmeticError("generated matchup covariance is not positive definite")
            matchup_pairs = {f"{v}-{c}": matchup_variance for v, c in PAIRS}
            components["matchup"] = {
                "target_pair_margin_variance": matchup_variance,
                "equicorrelation": MATCHUP_RHO,
                "covariance": matchup_cov,
                "pair_margin_variances": matchup_pairs,
            }
            total_variances = {
                pair: math.fsum(
                    components[name]["pair_margin_variances"][pair]
                    for name in components
                )
                for pair in matchup_pairs
            }
            mean_total = math.fsum(total_variances.values()) / len(total_variances)
            bands[band] = {
                "fractions_seed_root_slot_seed_slot": list(band_fractions),
                "components": components,
                "pair_latent_margin_variance_V": total_variances,
                "pair_sigma_including_unit_game_residual": {
                    pair: math.sqrt(1 + variance)
                    for pair, variance in total_variances.items()
                },
                "mean_pair_latent_margin_variance_V": mean_total,
            }
        seed_factors = {
            band: _cholesky_factor(bands[band]["components"]["seed"]["covariance"])
            for band in BANDS
        }
        cross_band = {}
        for left_band in BANDS:
            cross_band[left_band] = {}
            for right_band in BANDS:
                left = seed_factors[left_band]
                right = seed_factors[right_band]
                cross_band[left_band][right_band] = [
                    [
                        math.fsum(left[i][k] * right[j][k] for k in range(len(ARM_IDS)))
                        for j in range(len(ARM_IDS))
                    ]
                    for i in range(len(ARM_IDS))
                ]
        profiles[profile] = {
            "bands": bands,
            "cross_band_seed_covariance_Lg_LhT": cross_band,
        }

    return {
        "schema": "caissa.v212.calibration-profile-variance-audit.v01",
        "source_protocol": "docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_02.md",
        "purpose": "deterministic covariance arithmetic only; no random draws or simulation",
        "arm_order": list(ARM_IDS),
        "candidate_control_pairs": [f"{v}-{c}" for v, c in PAIRS],
        "profiles": profiles,
        "checks": {
            "ordinary_profiles_mean_V_equals_one": all(
                math.isclose(
                profiles[profile]["bands"][band]["mean_pair_latent_margin_variance_V"],
                    1.0,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for profile in ("P1", "P2", "P3", "P4")
                for band in BANDS
            ),
            "all_profile_pair_sigmas_positive": all(
                sigma > 0
                for profile in profiles.values()
                for band in profile["bands"].values()
                for sigma in band["pair_sigma_including_unit_game_residual"].values()
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=("json",), default="json")
    parser.parse_args()
    print(json.dumps(profile_manifest(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
