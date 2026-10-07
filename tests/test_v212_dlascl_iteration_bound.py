import unittest

from tools.v212_dlascl_iteration_bound import (
    dsyevd_ieee_binary64_bound,
    source_bound,
)


class DlasclIterationBoundTests(unittest.TestCase):
    def test_zero_iterations_has_no_arithmetic(self):
        result = source_bound(0)
        self.assertEqual(
            result["covered_source_arithmetic_interval"][
                "combined_add_subtract_multiply_divide"
            ]["maximum"],
            0,
        )

    def test_positive_iteration_formula(self):
        for iterations in (1, 2, 5):
            with self.subTest(iterations=iterations):
                result = source_bound(iterations)
                operations = result["covered_source_arithmetic_interval"]
                self.assertEqual(
                    operations["multiplications"]["maximum"], 529 * iterations
                )
                self.assertEqual(
                    operations["divisions"]["maximum"], iterations + 2
                )
                self.assertEqual(
                    operations["combined_add_subtract_multiply_divide"]["maximum"],
                    530 * iterations + 2,
                )
                self.assertFalse(result["eligibility"]["finite_total_dlascl_bound"])

    def test_rejects_non_integer_or_negative_iterations(self):
        for invalid in (-1, 1.5, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    source_bound(invalid)

    def test_ieee_binary64_dsyevd_path_has_one_conditional_pass(self):
        result = dsyevd_ieee_binary64_bound()
        self.assertEqual(
            result["derived_dsyevd_scaling"][
                "maximum_scaling_iterations_per_call"
            ],
            1,
        )
        self.assertEqual(
            result["covered_source_arithmetic_interval"][
                "combined_add_subtract_multiply_divide"
            ]["maximum"],
            532,
        )
        self.assertFalse(result["eligibility"]["actual_runtime_attested"])
        self.assertTrue(
            result["eligibility"][
                "finite_total_dlascl_bound_under_declared_assumptions"
            ]
        )


if __name__ == "__main__":
    unittest.main()
