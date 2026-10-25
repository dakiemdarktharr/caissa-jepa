from __future__ import annotations

import unittest

from tools.v212_openblas_dnrm2_binary_bound import (
    _instruction_mnemonics,
    _discover_kernel_symbols,
    _require_exact_kernel_inventory,
    _x87_math_counts,
    kernel_operations,
    source_bound,
)


class OpenBlasDnrm2BinaryBoundTests(unittest.TestCase):
    def test_objdump_parser_counts_instruction_lines_only(self):
        disassembly = """\
  1000: d8 c8                      fmul   %st(0),%st
  1002: de c1                      faddp  %st,%st(1)
  1004: d9 fa                      fsqrt
  1006: <dnrm2_k_HASWELL+0x6>:
"""
        mnemonics = _instruction_mnemonics(disassembly)
        self.assertEqual(mnemonics, ["fmul", "faddp", "fsqrt"])
        self.assertEqual(
            _x87_math_counts(mnemonics), {"faddp": 1, "fmul": 1, "fsqrt": 1}
        )

    def test_nm_inventory_requires_exact_defined_kernel_set(self):
        nm_output = """\
0000000000acbc00 T dnrm2_k_HASWELL
0000000000822e00 T dnrm2_k_NEHALEM
000000000068a600 T dnrm2_k_PRESCOTT
0000000000973400 T dnrm2_k_SANDYBRIDGE
0000000000c70a00 T dnrm2_k_SKYLAKEX
0000000000ffffff T unrelated_symbol
"""
        discovered = _discover_kernel_symbols(nm_output)
        self.assertEqual(len(discovered), 5)
        self.assertEqual(_require_exact_kernel_inventory(discovered), discovered)
        with self.assertRaisesRegex(ValueError, "unexpected=.*dnrm2_k_EXTRA"):
            _require_exact_kernel_inventory([*discovered, "dnrm2_k_EXTRA"])
        with self.assertRaisesRegex(ValueError, "missing=.*dnrm2_k_HASWELL"):
            _require_exact_kernel_inventory(
                [symbol for symbol in discovered if symbol != "dnrm2_k_HASWELL"]
            )

    def test_short_vector_fastpath_bypasses_kernel(self):
        self.assertEqual(
            kernel_operations(1),
            {
                "kernel_dispatched": False,
                "absolute_value_fastpath_calls": 1,
                "floating_additions": 0,
                "floating_multiplications": 0,
                "square_root_calls": 0,
            },
        )

    def test_eight_element_kernel_and_tail_operation_counts(self):
        self.assertEqual(
            kernel_operations(8),
            {
                "kernel_dispatched": True,
                "absolute_value_fastpath_calls": 0,
                "floating_additions": 11,
                "floating_multiplications": 8,
                "square_root_calls": 1,
            },
        )
        self.assertEqual(kernel_operations(10)["floating_additions"], 13)
        self.assertEqual(kernel_operations(30)["floating_additions"], 33)

    def test_n32_two_pass_candidate_bound(self):
        report = source_bound()
        self.assertEqual(report["compiled_kernel_variants_inspected"], [
            "PRESCOTT", "NEHALEM", "SANDYBRIDGE", "HASWELL", "SKYLAKEX"
        ])
        self.assertEqual(report["maximum_dlarfg_dnrm2_function_invocations"], 60)
        self.assertEqual(report["maximum_dispatched_kernel_invocations"], 58)
        self.assertEqual(report["length_one_absolute_value_fastpaths"], 2)
        self.assertEqual(report["dnrm2_candidate_fp_upper"]["floating_additions"], 1_102)
        self.assertEqual(report["dnrm2_candidate_fp_upper"]["floating_multiplications"], 928)
        self.assertEqual(report["dnrm2_candidate_fp_upper"]["total_add_multiply_flops"], 2_030)
        self.assertEqual(report["dnrm2_candidate_fp_upper"]["square_root_calls"], 58)
        self.assertFalse(report["eligibility"]["complete_dnrm2_runtime_bound"])

    def test_bad_lengths_and_call_counts_rejected(self):
        for n in (0, 1, 2, True, 32.0):
            with self.subTest(n=n), self.assertRaises(ValueError):
                source_bound(n)
        for calls in (0, 3, True, 1.0):
            with self.subTest(calls=calls), self.assertRaises(ValueError):
                source_bound(32, calls)
        with self.assertRaises(ValueError):
            kernel_operations(0)


if __name__ == "__main__":
    unittest.main()
