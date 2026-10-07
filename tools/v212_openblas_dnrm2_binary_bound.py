"""DNRM2 FP-instruction bound for one observed scipy-openblas binary.

The formulas reproduce static objdump inspection of the five x86_64
``dnrm2_k`` symbols in the observed NumPy Linux wheel. The exported wrapper
dispatches through a function pointer, so this report does not attest which
kernel a future or even the observed process selected. It is not a portable
OpenBLAS source bound or a D03 runtime receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


MATRIX_ORDER = 32
OBSERVED_BINARY_SHA256 = (
    "05c9f9eb89ee68a4b9d673184fa91c99587e736392c0c2d49180a8aa5303d080"
)
KERNEL_VARIANTS = (
    "PRESCOTT",
    "NEHALEM",
    "SANDYBRIDGE",
    "HASWELL",
    "SKYLAKEX",
)
EXPECTED_STATIC_OPCODE_COUNTS = {
    "fmul": 18,
    "faddp": 21,
    "fsqrt": 1,
}


def _instruction_mnemonics(disassembly: str) -> list[str]:
    """Extract instruction mnemonics from GNU objdump's disassembly lines."""
    result = []
    for line in disassembly.splitlines():
        match = re.match(
            r"^\s*[0-9a-fA-F]+:\s+(?:(?:[0-9a-fA-F]{2})\s+)+"
            r"([a-zA-Z][a-zA-Z0-9.]*)\b",
            line,
        )
        if match:
            result.append(match.group(1).lower())
    return result


def _x87_math_counts(mnemonics: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for mnemonic in mnemonics:
        if re.fullmatch(r"f(?:add|sub|mul|div|sqrt)[a-z]*", mnemonic):
            counts[mnemonic] = counts.get(mnemonic, 0) + 1
    return dict(sorted(counts.items()))


def _discover_kernel_symbols(nm_output: str) -> list[str]:
    """Collect every defined nm symbol using the DNRM2 kernel prefix."""
    found = set()
    for line in nm_output.splitlines():
        fields = line.split()
        if fields and fields[-1].startswith("dnrm2_k_"):
            found.add(fields[-1])
    return sorted(found)


def _require_exact_kernel_inventory(discovered: list[str]) -> list[str]:
    expected = sorted(f"dnrm2_k_{variant}" for variant in KERNEL_VARIANTS)
    if discovered != expected:
        missing = sorted(set(expected) - set(discovered))
        unexpected = sorted(set(discovered) - set(expected))
        raise ValueError(
            "DNRM2 kernel symbol inventory mismatch: "
            f"missing={missing}, unexpected={unexpected}"
        )
    return expected


def audit_static_binary(binary_path: str | Path) -> dict:
    """Verify the observed wheel artifact and static kernel opcodes.

    This reads the binary and asks nm/objdump to inspect symbols/disassembly;
    it never loads or executes the shared library.
    """
    path = Path(binary_path)
    if not path.is_file():
        raise ValueError("binary_path must name an existing file")
    binary_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if binary_hash != OBSERVED_BINARY_SHA256:
        raise ValueError("binary SHA-256 does not match the observed artifact")
    nm_path = shutil.which("nm")
    objdump_path = shutil.which("objdump")
    if nm_path is None or objdump_path is None:
        raise RuntimeError("GNU nm and objdump are required for static audit")
    tool_versions = {}
    for name, executable in (("nm", nm_path), ("objdump", objdump_path)):
        version_result = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        tool_versions[name] = version_result.stdout.splitlines()[0]
    nm_output = subprocess.run(
        [nm_path, "-a", "--defined-only", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    discovered = _discover_kernel_symbols(nm_output)
    expected_symbols = _require_exact_kernel_inventory(discovered)

    per_symbol = {}
    for symbol in expected_symbols:
        disassembly = subprocess.run(
            [objdump_path, "-d", f"--disassemble={symbol}", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        counts = _x87_math_counts(_instruction_mnemonics(disassembly))
        if counts != EXPECTED_STATIC_OPCODE_COUNTS:
            raise ValueError(
                f"unexpected static x87 opcode counts for {symbol}: {counts}"
            )
        per_symbol[symbol] = {
            "x87_math_instruction_counts": counts,
            "objdump_stdout_sha256": hashlib.sha256(
                disassembly.encode("utf-8")
            ).hexdigest(),
        }
    return {
        "binary_basename": path.name,
        "binary_sha256": binary_hash,
        "tool_versions": tool_versions,
        "nm_discovered_dnrm2_kernel_symbols": discovered,
        "inspected_expected_symbols": expected_symbols,
        "per_symbol_static_trace": per_symbol,
        "runtime_dispatch_selection_attested": False,
        "library_loaded_or_executed": False,
    }


def kernel_operations(vector_length: int) -> dict:
    """Count x87 add/multiply/sqrt operations on the unit-stride path.

    Static disassembly has an eight-element loop: two groups of four squares
    each update four accumulators (8 multiplies, 8 adds); the tail contributes
    one multiply/add per element; and the four accumulators are finally
    reduced by three additions. The exported wrapper bypasses the kernel for
    length one and returns the absolute value directly.
    """
    if type(vector_length) is not int or vector_length < 1:
        raise ValueError("vector_length must be a positive integer")
    if vector_length == 1:
        return {
            "kernel_dispatched": False,
            "absolute_value_fastpath_calls": 1,
            "floating_additions": 0,
            "floating_multiplications": 0,
            "square_root_calls": 0,
        }
    full_blocks, tail = divmod(vector_length, 8)
    return {
        "kernel_dispatched": True,
        "absolute_value_fastpath_calls": 0,
        "floating_additions": 8 * full_blocks + tail + 3,
        "floating_multiplications": vector_length,
        "square_root_calls": 1,
    }


def source_bound(n: int = MATRIX_ORDER, max_norm_calls_per_reflector: int = 2) -> dict:
    """Bound maximum DLARFG DNRM2 work for q=1..N-2 vector lengths.

    ``max_norm_calls_per_reflector=2`` models DLARFG's initial DNRM2 plus its
    second DNRM2 after an underflow-rescaling path. The result is a
    binary-disassembly-specific candidate bound. Comparisons, integer/index
    work, memory operations, and dispatch are not FLOPs and remain separate.
    """
    if type(n) is not int or n < 3:
        raise ValueError("n must be an integer of at least three")
    if type(max_norm_calls_per_reflector) is not int or not 1 <= max_norm_calls_per_reflector <= 2:
        raise ValueError("max_norm_calls_per_reflector must be 1 or 2")

    lengths = range(1, n - 1)
    one_pass = [kernel_operations(q) for q in lengths]
    calls_per_reflector = max_norm_calls_per_reflector
    reflector_count = n - 2
    all_invocation_count = reflector_count * calls_per_reflector
    kernel_invocation_count = sum(
        result["kernel_dispatched"] for result in one_pass
    ) * calls_per_reflector
    absolute_fastpath_count = sum(
        result["absolute_value_fastpath_calls"] for result in one_pass
    ) * calls_per_reflector
    additions_per_pass = sum(result["floating_additions"] for result in one_pass)
    multiplications_per_pass = sum(
        result["floating_multiplications"] for result in one_pass
    )
    square_roots_per_pass = sum(result["square_root_calls"] for result in one_pass)

    return {
        "schema": "caissa.v212.openblas-dnrm2-binary-bound.v01",
        "observed_artifact": {
            "basename": "libscipy_openblas64_-32a4b2a6.so",
            "sha256": OBSERVED_BINARY_SHA256,
            "reported_build": "scipy-openblas 0.3.31.188.0; DYNAMIC_ARCH; observed config Haswell",
        },
        "scope": (
            "static objdump operation-count candidate for unit-stride DNRM2 "
            "on listed x86_64 kernel variants in this exact observed binary"
        ),
        "matrix_order": n,
        "reflector_vector_length_range_inclusive": [1, n - 2],
        "max_norm_calls_per_reflector": calls_per_reflector,
        "maximum_dlarfg_dnrm2_function_invocations": all_invocation_count,
        "maximum_dispatched_kernel_invocations": kernel_invocation_count,
        "length_one_absolute_value_fastpaths": absolute_fastpath_count,
        "compiled_kernel_variants_inspected": list(KERNEL_VARIANTS),
        "static_disassembly_instructions_per_loop_body": {
            "x87_multiply_instructions": 8,
            "x87_add_instructions": 8,
            "x87_sqrt_instructions": 1,
            "loop_elements": 8,
            "final_accumulator_additions": 3,
        },
        "dnrm2_candidate_fp_upper": {
            "floating_additions": additions_per_pass * calls_per_reflector,
            "floating_multiplications": multiplications_per_pass * calls_per_reflector,
            "total_add_multiply_flops": (
                additions_per_pass + multiplications_per_pass
            ) * calls_per_reflector,
            "square_root_calls": square_roots_per_pass * calls_per_reflector,
            "one_pass_per_reflector_set": {
                "floating_additions": additions_per_pass,
                "floating_multiplications": multiplications_per_pass,
                "total_add_multiply_flops": additions_per_pass + multiplications_per_pass,
                "square_root_calls": square_roots_per_pass,
            },
        },
        "assumptions": [
            "DLARFG calls DNRM2 with unit stride and vector lengths 1..N-2",
            "at most two DNRM2 calls per nontrivial DLARFG invocation",
            "for lengths >=2, the dispatcher selects one of the five inspected kernel symbols",
            "each listed kernel's loop and tail operations match the inspected objdump trace",
        ],
        "unresolved_or_excluded": [
            "the indirect dnrm2_k function pointer selected at runtime",
            "execution-byte attestation and applicability to another wheel/runtime/architecture",
            "DNRM2 comparisons, integer/index work, memory traffic, and wrapper dispatch work",
            "DLAMCH and DLAPY2 helper internals",
            "DSYEVD/DSYTRD/DSTERF complete path and full eigensolver accounting",
        ],
        "eligibility": {
            "complete_dnrm2_runtime_bound": False,
            "complete_eigensolver_bound": False,
            "full_counter": False,
            "parity_eligible": False,
            "profile_or_fit_authorized": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit-binary",
        help="statically verify the exact observed shared-library binary",
    )
    args = parser.parse_args()
    report = source_bound()
    if args.audit_binary:
        report["static_binary_audit"] = audit_static_binary(args.audit_binary)
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
