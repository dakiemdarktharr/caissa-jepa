import unittest

from tools.v212_dlascl_iteration_bound import source_bound


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


if __name__ == "__main__":
    unittest.main()
