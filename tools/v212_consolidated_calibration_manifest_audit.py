#!/usr/bin/env python3
"""Build a deterministic parameter manifest for calibration draft 03.

The audit joins the existing mean/covariance/root-quality audits into one
39-cell × 16-policy-pair × 3-band × 10-contrast candidate manifest. It uses
no RNG and creates no slots, roots, scores, outcomes, or simulation datasets.
The result is proposal-only and is not a frozen simulator input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .v212_calibration_profile_audit import BANDS, profile_manifest
    from .v212_calibration_target_audit import build_manifest as build_base_targets
    from .v212_root_quality_calibration_audit import build_manifest as build_root_quality
    from .v212_root_quality_yield_interaction_audit import (
        build_manifest as build_interaction,
    )
    from .v212_calibration_assurance_search import scan as scan_assurance
else:
    from v212_calibration_profile_audit import BANDS, profile_manifest
    from v212_calibration_target_audit import build_manifest as build_base_targets
    from v212_root_quality_calibration_audit import build_manifest as build_root_quality
    from v212_root_quality_yield_interaction_audit import (
        build_manifest as build_interaction,
    )
    from v212_calibration_assurance_search import scan as scan_assurance


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_IDS = ("bounded-search", "positional", "tactical", "uniform")
POLICY_PAIRS = tuple((first, second) for first in POLICY_IDS for second in POLICY_IDS)
POLICY_GROUPS = {
    "low_yield": tuple(range(8)),
    "high_yield": tuple(range(8, 16)),
}
EXPECTED_SCENARIOS = 39
EXPECTED_ROWS = EXPECTED_SCENARIOS * 16 * len(BANDS) * 10
SOURCE_PATHS = (
    "docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_03.md",
    "docs/METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md",
    "tools/v212_calibration_profile_audit.py",
    "tools/v212_calibration_target_audit.py",
    "tools/v212_root_quality_calibration_audit.py",
    "tools/v212_root_quality_yield_interaction_audit.py",
    "tools/v212_calibration_assurance.py",
    "tools/v212_calibration_assurance_search.py",
    "tools/v212_consolidated_calibration_manifest_audit.py",
    "tests/test_v212_consolidated_calibration_manifest_audit.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_identity() -> dict[str, str | None]:
    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args], cwd=REPO_ROOT, check=True,
                capture_output=True, text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return result.stdout.strip()

    return {
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "working_tree_porcelain": git("status", "--porcelain"),
    }


def _hash_inventory() -> dict[str, str]:
    return {name: _sha256(REPO_ROOT / name) for name in SOURCE_PATHS}


def _check_pair_yield_targets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair_yield_cells = {
        "N-GLOBAL-YIELD", "A-BOUNDARY-YIELD",
        "N-GLOBAL-YIELD-ROOTQ-NEG", "N-GLOBAL-YIELD-ROOTQ-POS",
        "A-BOUNDARY-YIELD-ROOTQ-NEG", "A-BOUNDARY-YIELD-ROOTQ-POS",
    }
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row["cell_id"] in pair_yield_cells:
            key = (
                row["cell_id"], row["occupancy_band"],
                row["candidate_control"], row["policy_pair_group"],
            )
            buckets.setdefault(key, []).append(row)

    checks: list[dict[str, Any]] = []
    for cell in sorted(pair_yield_cells):
        expected_global = 0.0 if cell.startswith("N-") else 0.05
        for band in BANDS:
            for contrast_index in range(1, 6):
                for candidate in ("V1", "V2"):
                    contrast = f"{candidate}-C{contrast_index}"
                    groups = {}
                    for group in ("low_yield", "high_yield"):
                        members = buckets.get((cell, band, contrast, group), [])
                        if len(members) != 8:
                            raise ArithmeticError(
                                f"{cell}/{band}/{contrast}/{group} must expand to 8 ordered pairs"
                            )
                        targets = {member["population_mean_target"] for member in members}
                        weights = {member["accepted_policy_group_weight"] for member in members}
                        if len(targets) != 1 or len(weights) != 1:
                            raise ArithmeticError("policy-group target or weight is inconsistent")
                        groups[group] = (targets.pop(), weights.pop())
                    weighted = (
                        groups["low_yield"][0] * groups["low_yield"][1]
                        + groups["high_yield"][0] * groups["high_yield"][1]
                    )
                    if not abs(weighted - expected_global) <= 1e-14:
                        raise ArithmeticError(
                            f"{cell}/{band}/{contrast} group targets do not recover global target"
                        )
                    checks.append({
                        "cell_id": cell,
                        "occupancy_band": band,
                        "candidate_control": contrast,
                        "weighted_conditional_target": weighted,
                        "declared_global_target": expected_global,
                        "accepted_group_weights": {
                            "low_yield": groups["low_yield"][1],
                            "high_yield": groups["high_yield"][1],
                        },
                    })
    if len(checks) != len(pair_yield_cells) * len(BANDS) * 10:
        raise ArithmeticError("pair-yield target crosswalk is incomplete")
    return checks


def _base_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in manifest["scenarios"]:
        for solved in scenario["solved_eta_rows"]:
            for pair_index in solved["policy_pair_indices"]:
                first, second = POLICY_PAIRS[pair_index]
                rows.append({
                    "cell_id": scenario["scenario_id"],
                    "family": scenario["family"],
                    "profile": scenario["profile"],
                    "occupancy_band": solved["band"],
                    "candidate_control": solved["candidate_control"],
                    "ordered_policy_pair": [first, second],
                    "policy_pair_group": (
                        "low_yield" if pair_index < 8 else "high_yield"
                    ) if scenario["scenario_id"] in {
                        "N-GLOBAL-YIELD", "A-BOUNDARY-YIELD"
                    } else "ordinary",
                    "slot_validity_q": solved["slot_validity_q"],
                    "accepted_policy_group_weight": (
                        0.25 if pair_index < 8 else 0.75
                    ) if scenario["scenario_id"] in {
                        "N-GLOBAL-YIELD", "A-BOUNDARY-YIELD"
                    } else 1.0,
                    "population_mean_target": solved["population_mean_target"],
                    "eta": solved["eta"],
                    "achieved_mean": solved["achieved_mean"],
                    "absolute_target_residual": solved["absolute_residual"],
                    "sigma": solved["sigma"],
                    "sigma_rest": None,
                    "tau": solved["tau"],
                    "seat_advantage_beta": solved["beta"],
                    "root_quality": None,
                    "target_source": "profile-and-target audit; ordinary or policy-pair yield",
                })
    return rows


def _root_quality_rows(
    manifest: dict[str, Any], *, interaction: bool
) -> list[dict[str, Any]]:
    if interaction:
        rows_in = manifest["conditional_target_rows"]
        solution_index = {
            (row["q"], row["gamma"], row["conditional_target_mean"]): row
            for row in manifest["solutions"]
        }
    else:
        rows_in = manifest["conditional_target_rows"]
        solution_index = {
            (row["gamma"], row["target_mean"]): row
            for row in manifest["quadrature_solutions"]
        }

    rows: list[dict[str, Any]] = []
    for source in rows_in:
        q = source.get("slot_validity_q", source.get("policy_pair_validity_q"))
        gamma = source["gamma"]
        target = source["target_mean"]
        if interaction:
            solution = solution_index[(q, gamma, target)]
            fine = solution["by_interval_count"]["8192"]
            pair_indices = POLICY_GROUPS[source["policy_pair_group"]]
            group_weight = source["accepted_group_weight"]
            integration_solution = {
                "by_interval_count": solution["by_interval_count"],
                "selected_root_moments": fine["selected_root_moments"],
                "absolute_order_differences": solution[
                    "absolute_order_differences"
                ],
            }
        else:
            solution = solution_index[(gamma, target)]
            fine = solution["by_interval_count"]["8192"]
            pair_indices = tuple(range(16))
            group_weight = 1.0
            integration_solution = {
                "by_interval_count": solution["by_interval_count"],
                "selected_root_moments": fine["selected_root_moments"],
                "absolute_order_differences": solution[
                    "absolute_order_differences"
                ],
            }
        for pair_index in pair_indices:
            first, second = POLICY_PAIRS[pair_index]
            rows.append({
                "cell_id": source["scenario_id"],
                "family": source["family"],
                "profile": "P2",
                "occupancy_band": source["band"],
                "candidate_control": source["candidate_control"],
                "ordered_policy_pair": [first, second],
                "policy_pair_group": source.get("policy_pair_group", "ordinary"),
                "slot_validity_q": q,
                "accepted_policy_group_weight": group_weight,
                "population_mean_target": target,
                "eta": source["solved"]["eta"],
                "achieved_mean": source["solved"]["achieved_mean"],
                "absolute_target_residual": source["solved"]["absolute_residual"],
                "sigma": None,
                "sigma_rest": manifest["sigma_rest"],
                "tau": manifest["tau"],
                "seat_advantage_beta": manifest["seat_advantage_beta"],
                "root_quality": {
                    "gamma": gamma,
                    "variance": manifest["root_quality_variance"],
                    "loadings": list((0.5, 0.5, -0.5, -0.5, -0.5, -0.5, -0.5)),
                    "validity_intercept_by_order": {
                        n: values["validity"]["intercept"]
                        for n, values in integration_solution[
                            "by_interval_count"
                        ].items()
                    },
                    "selected_root_moments_by_order": {
                        n: values["selected_root_moments"]
                        for n, values in integration_solution[
                            "by_interval_count"
                        ].items()
                    },
                    "integration_order_differences": integration_solution[
                        "absolute_order_differences"
                    ],
                },
                "target_source": (
                    "pair-yield × root-quality audit"
                    if interaction else "uniform-yield root-quality audit"
                ),
            })
    return rows


def build_manifest() -> dict[str, Any]:
    profiles = profile_manifest()
    base = build_base_targets()
    root_quality = build_root_quality()
    interaction = build_interaction()
    assurance_search = scan_assurance(
        1, 18_600, endpoints=69, cells=39,
        bootstrap_replicates=10_000, contrasts=15, assurance_target=0.80,
    )
    assurance_search_bytes = json.dumps(
        assurance_search, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    assurance_search_sha256 = hashlib.sha256(assurance_search_bytes).hexdigest()

    rows = (
        _base_rows(base)
        + _root_quality_rows(root_quality, interaction=False)
        + _root_quality_rows(interaction, interaction=True)
    )
    row_keys = [(
        row["cell_id"], tuple(row["ordered_policy_pair"]),
        row["occupancy_band"], row["candidate_control"],
    ) for row in rows]
    if len(rows) != EXPECTED_ROWS or len(set(row_keys)) != EXPECTED_ROWS:
        raise ArithmeticError(
            f"expected {EXPECTED_ROWS} unique target rows, got {len(rows)}"
        )

    scenario_ids = [scenario["scenario_id"] for scenario in base["scenarios"]]
    scenario_ids.extend(row["scenario_id"] for row in root_quality["conditional_target_rows"]
                        if row["scenario_id"] not in scenario_ids)
    scenario_ids.extend(row["scenario_id"] for row in interaction["conditional_target_rows"]
                        if row["scenario_id"] not in scenario_ids)
    if len(scenario_ids) != EXPECTED_SCENARIOS or len(set(scenario_ids)) != EXPECTED_SCENARIOS:
        raise ArithmeticError("the merged manifest must contain 39 unique cell IDs")

    null_count = sum(cell.startswith("N-") for cell in scenario_ids)
    alternative_count = sum(cell.startswith("A-") for cell in scenario_ids)
    if (null_count, alternative_count) != (30, 9):
        raise ArithmeticError("merged null/alternative inventory mismatch")
    max_residual = max(row["absolute_target_residual"] for row in rows)
    if max_residual > 1e-10:
        raise ArithmeticError("one or more target solver residuals exceed 1e-10")
    pair_yield_checks = _check_pair_yield_targets(rows)

    covariance = {
        "ordinary_profiles": profiles,
        "root_quality_p2": root_quality["covariance_manifest"],
        "interaction_p2": interaction["root_covariance_manifest"],
    }
    if covariance["root_quality_p2"] != covariance["interaction_p2"]:
        raise ArithmeticError("P2 root-quality covariance differs across the two audits")

    return {
        "schema": "caissa.v212.consolidated-calibration-candidate-manifest.v01",
        "status": (
            "deterministic parameter audit only; proposal is unapproved; "
            "not a frozen simulator manifest; no random draws or outcomes"
        ),
        "protocol": "docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_03.md",
        "scenario_ids": scenario_ids,
        "scenario_counts": {
            "total": len(scenario_ids),
            "null": null_count,
            "alternative": alternative_count,
            "fwer_endpoints": null_count,
            "simultaneous_coverage_endpoints": len(scenario_ids),
            "total_outer_assurance_endpoints": null_count + len(scenario_ids),
            "policy_pairs_per_cell": len(POLICY_PAIRS),
            "occupancy_bands": list(BANDS),
            "atomic_contrasts": 10,
            "macro_contrasts_derived": 5,
            "conditional_target_rows": len(rows),
            "maximum_absolute_target_residual": max_residual,
            "pair_yield_weighted_target_checks": len(pair_yield_checks),
        },
        "ordered_policy_pair_ids": [
            {
                "index": index,
                "plus_seat_policy": first,
                "minus_seat_policy": second,
                "yield_group": (
                    "low_yield" if index < 8 else "high_yield"
                ),
            }
            for index, (first, second) in enumerate(POLICY_PAIRS)
        ],
        "profile_tau": {"P1": 0.15, "P2": 0.25, "P3": 0.40, "P4": 0.75, "P5": 0.40},
        "score_cutpoints": {
            profile: {"win_if_z_greater_than": tau,
                     "loss_if_z_less_than": -tau,
                     "draw_interval_inclusive": [-tau, tau]}
            for profile, tau in {
                "P1": 0.15, "P2": 0.25, "P3": 0.40,
                "P4": 0.75, "P5": 0.40,
            }.items()
        },
        "analysis_and_schedule_parameters": {
            "seed_clusters": 20,
            "accepted_slots_per_variant_band": 16,
            "candidate_slots_per_variant_band": 64,
            "variants": ["connect4-8x8-k4", "reversi8"],
            "outer_replication_candidate_range_scanned": [1, 18_600],
            "inner_bootstrap_replicates_proposal": 10_000,
            "outer_replication_selected": None,
            "assurance_target_is_proposal_only": 0.80,
        },
        "assurance_search": assurance_search,
        "assurance_search_sha256": assurance_search_sha256,
        "covariance_manifests": covariance,
        "pair_yield_weighted_target_checks": pair_yield_checks,
        "quadrature_settings": {
            "method": "composite Simpson rule against standard-normal density",
            "domain": [-10.0, 10.0],
            "interval_counts": [4096, 8192],
            "maximum_absolute_order_difference": 1e-10,
            "root_quality_only": root_quality["quadrature_solutions"],
            "pair_yield_root_quality": interaction["solutions"],
        },
        "source_hashes_sha256": _hash_inventory(),
        "runtime": {
            "python_version": sys.version.split()[0],
            "implementation": sys.implementation.name,
            "platform": platform.platform(),
            "git": _git_identity(),
        },
        "cells": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", choices=("json",), default="json")
    args = parser.parse_args()
    if args.output == "json":
        print(json.dumps(build_manifest(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
