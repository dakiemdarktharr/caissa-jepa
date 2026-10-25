from __future__ import annotations

import math
import unittest

from tools.v212_calibration_profile_audit import (
    BANDS,
    PAIRS,
    PROFILE_FRACTIONS,
    _cholesky_positive,
    equicorrelation,
    profile_manifest,
)


class CalibrationProfileAuditTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_labels_scope(self) -> None:
        first = profile_manifest()
        second = profile_manifest()
        self.assertEqual(first, second)
        self.assertIn("no random draws or simulation", first["purpose"])
        self.assertEqual(first["candidate_control_pairs"], [f"{v}-{c}" for v, c in PAIRS])

    def test_ordinary_profiles_have_unit_mean_margin_variance(self) -> None:
        manifest = profile_manifest()
        self.assertTrue(manifest["checks"]["ordinary_profiles_mean_V_equals_one"])
        for profile in ("P1", "P2", "P3", "P4"):
            for band in BANDS:
                row = manifest["profiles"][profile]["bands"][band]
                self.assertAlmostEqual(row["mean_pair_latent_margin_variance_V"], 1.0)
                for variance in row["pair_latent_margin_variance_V"].values():
                    self.assertAlmostEqual(variance, 1.0)
                for sigma in row["pair_sigma_including_unit_game_residual"].values():
                    self.assertAlmostEqual(sigma, math.sqrt(2.0))

    def test_component_pair_variances_match_profile_targets(self) -> None:
        manifest = profile_manifest()
        for profile, band_rows in manifest["profiles"].items():
            for band, row in band_rows["bands"].items():
                seed, slot, interaction = PROFILE_FRACTIONS[profile][band]
                expected = {
                    "seed": seed,
                    "root_slot": slot,
                    "seed_slot_arm": interaction / 2,
                    "matchup": interaction / 2,
                }
                for name, target in expected.items():
                    component = row["components"][name]
                    values = list(component["pair_margin_variances"].values())
                    self.assertAlmostEqual(sum(values) / len(values), target)

    def test_p5_preserves_mean_budget_with_pair_heterogeneity(self) -> None:
        manifest = profile_manifest()
        for band in BANDS:
            row = manifest["profiles"]["P5"]["bands"][band]
            self.assertAlmostEqual(row["mean_pair_latent_margin_variance_V"], 1.0)
        high_band = manifest["profiles"]["P5"]["bands"]["high"]
        values = list(high_band["pair_latent_margin_variance_V"].values())
        self.assertGreater(max(values), min(values))
        for pair in ("V1-C1", "V1-C2"):
            self.assertNotEqual(
                high_band["pair_latent_margin_variance_V"][pair],
                high_band["pair_latent_margin_variance_V"]["V2-C1"],
            )

    def test_cross_band_seed_covariance_matches_shared_latent_rule(self) -> None:
        manifest = profile_manifest()
        for profile_id, profile in manifest["profiles"].items():
            cross = profile["cross_band_seed_covariance_Lg_LhT"]
            for left in BANDS:
                for right in BANDS:
                    matrix = cross[left][right]
                    reverse = cross[right][left]
                    for i in range(len(matrix)):
                        for j in range(len(matrix)):
                            self.assertAlmostEqual(matrix[i][j], reverse[j][i])
                    if left == right:
                        expected = profile["bands"][left]["components"]["seed"]["covariance"]
                        for i in range(len(matrix)):
                            for j in range(len(matrix)):
                                self.assertAlmostEqual(matrix[i][j], expected[i][j])
            if profile_id in {"P1", "P2", "P3", "P4"}:
                low_middle = cross["low"]["middle"]
                low_cov = profile["bands"]["low"]["components"]["seed"]["covariance"]
                for i in range(len(low_middle)):
                    for j in range(len(low_middle)):
                        self.assertAlmostEqual(low_middle[i][j], low_cov[i][j])

    def test_covariance_construction_uses_positive_definite_ranges(self) -> None:
        self.assertTrue(_cholesky_positive(equicorrelation(7, 0.35)))
        self.assertTrue(_cholesky_positive(equicorrelation(10, -0.05)))
        with self.assertRaises(ValueError):
            equicorrelation(10, -0.12)


if __name__ == "__main__":
    unittest.main()
