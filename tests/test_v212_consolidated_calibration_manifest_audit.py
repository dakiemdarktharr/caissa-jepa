from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tools.v212_consolidated_calibration_manifest_audit import (
    EXPECTED_ROWS,
    POLICY_PAIRS,
    REPO_ROOT,
    build_manifest,
)


class ConsolidatedCalibrationManifestAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_manifest()

    def test_complete_inventory_pair_order_and_cell_balancing(self) -> None:
        manifest = self.manifest
        counts = manifest["scenario_counts"]
        self.assertEqual((counts["total"], counts["null"], counts["alternative"]), (39, 30, 9))
        self.assertEqual(counts["total_outer_assurance_endpoints"], 69)
        self.assertEqual(counts["conditional_target_rows"], EXPECTED_ROWS)
        self.assertEqual(counts["pair_yield_weighted_target_checks"], 180)
        self.assertEqual(len(manifest["pair_yield_weighted_target_checks"]), 180)
        self.assertTrue(all(
            abs(row["weighted_conditional_target"] - row["declared_global_target"]) <= 1e-14
            for row in manifest["pair_yield_weighted_target_checks"]
        ))
        self.assertEqual(len(manifest["cells"]), EXPECTED_ROWS)
        self.assertEqual(len(manifest["scenario_ids"]), 39)
        self.assertEqual(len(set(manifest["scenario_ids"])), 39)
        self.assertEqual(len(manifest["ordered_policy_pair_ids"]), 16)
        self.assertEqual(
            [tuple((x["plus_seat_policy"], x["minus_seat_policy"]))
             for x in manifest["ordered_policy_pair_ids"]],
            list(POLICY_PAIRS),
        )
        self.assertEqual(
            [x["yield_group"] for x in manifest["ordered_policy_pair_ids"]],
            ["low_yield"] * 8 + ["high_yield"] * 8,
        )
        per_cell: dict[str, set[tuple[tuple[str, str], str, str]]] = {}
        for row in manifest["cells"]:
            per_cell.setdefault(row["cell_id"], set()).add((
                tuple(row["ordered_policy_pair"]),
                row["occupancy_band"],
                row["candidate_control"],
            ))
            self.assertLessEqual(row["absolute_target_residual"], 1e-10)
        self.assertEqual(set(per_cell), set(manifest["scenario_ids"]))
        self.assertTrue(all(len(keys) == 16 * 3 * 10 for keys in per_cell.values()))

    def test_pair_yield_and_root_quality_rows_keep_distinct_parameters(self) -> None:
        def row(cell: str, pair: tuple[str, str]) -> dict[str, object]:
            return next(
                item for item in self.manifest["cells"]
                if item["cell_id"] == cell
                and tuple(item["ordered_policy_pair"]) == pair
                and item["occupancy_band"] == "low"
                and item["candidate_control"] == "V1-C1"
            )

        low = row("N-GLOBAL-YIELD", ("bounded-search", "uniform"))
        high = row("N-GLOBAL-YIELD", ("tactical", "uniform"))
        self.assertEqual((low["slot_validity_q"], high["slot_validity_q"]), (0.20, 0.60))
        self.assertEqual((low["population_mean_target"], high["population_mean_target"]), (-0.15, 0.05))
        self.assertAlmostEqual(
            0.25 * low["population_mean_target"] + 0.75 * high["population_mean_target"],
            0.0,
        )
        quality = row("N-GLOBAL-ROOTQ-POS", ("uniform", "tactical"))
        self.assertEqual(quality["slot_validity_q"], 0.40)
        self.assertEqual(quality["root_quality"]["gamma"], 1.0)
        self.assertIsNone(quality["sigma"])
        self.assertAlmostEqual(quality["sigma_rest"] ** 2, 1.625)
        self.assertIn("8192", quality["root_quality"]["validity_intercept_by_order"])
        interaction = row(
            "A-BOUNDARY-YIELD-ROOTQ-NEG", ("uniform", "uniform")
        )
        self.assertEqual(interaction["slot_validity_q"], 0.60)
        self.assertEqual(interaction["population_mean_target"], 0.10)
        self.assertEqual(interaction["root_quality"]["gamma"], -1.0)

    def test_source_fingerprints_and_closed_candidate_status(self) -> None:
        manifest = self.manifest
        self.assertIn("unapproved", manifest["status"])
        self.assertIsNone(manifest["analysis_and_schedule_parameters"]["outer_replication_selected"])
        self.assertEqual(
            manifest["assurance_search"]["first_qualifying_within_range"][
                "outer_datasets_per_cell"
            ],
            18_378,
        )
        canonical_search = json.dumps(
            manifest["assurance_search"], sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(canonical_search).hexdigest(),
            manifest["assurance_search_sha256"],
        )
        for name, expected in manifest["source_hashes_sha256"].items():
            digest = hashlib.sha256((REPO_ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(digest, expected)
        self.assertEqual(
            manifest["covariance_manifests"]["root_quality_p2"],
            manifest["covariance_manifests"]["interaction_p2"],
        )
        self.assertIn("no random draws", manifest["covariance_manifests"]["ordinary_profiles"]["purpose"])


if __name__ == "__main__":
    unittest.main()
