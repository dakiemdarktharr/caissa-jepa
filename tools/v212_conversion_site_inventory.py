"""Source-site inventory for explicit numeric conversions in the V2.12 graph.

This reports Python/NumPy conversion requests for counter coverage review. It
does not infer whether an array is copied or cast at runtime, nor does it
assign a FLOP or elapsed-time cost.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


SCHEMA = "caissa.v212.conversion-site-inventory.v01"
SOURCE_PATHS = (
    "two_player/v212_model.py",
    "two_player/v212_scratch_optimizer.py",
)
TARGETS = {"float": "python_scalar_float", "int": "python_scalar_int",
           "np.asarray": "numpy_array_dtype_request"}


def _target(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    return None


def inventory_sources(sources: dict[str, str]) -> dict:
    """Inventory explicit float/int/asarray calls without importing source."""
    modules = {}
    for filename in sorted(sources):
        source = sources[filename]
        if not isinstance(source, str):
            raise TypeError("source values must be text")
        tree = ast.parse(source, filename=filename)
        functions = [node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        sites = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = _target(node.func)
            if target not in TARGETS:
                continue
            function = next((fn.name for fn in sorted(
                (candidate for candidate in functions
                 if candidate.lineno <= node.lineno <= getattr(candidate, "end_lineno", candidate.lineno)),
                key=lambda candidate: getattr(candidate, "end_lineno", candidate.lineno) - candidate.lineno)),
                None)
            dtype = next((ast.unparse(keyword.value) for keyword in node.keywords
                          if keyword.arg == "dtype"), None)
            sites.append({
                "line": node.lineno,
                "function": function,
                "target": target,
                "category": TARGETS[target],
                "dtype_argument": dtype,
                "source": ast.unparse(node),
                "runtime_cast_or_copy_proven": False,
            })
        sites.sort(key=lambda row: (row["line"], row["target"], row["source"]))
        raw = source.encode("utf-8")
        modules[filename] = {
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "site_count": len(sites),
            "sites_by_category": {
                category: sum(row["category"] == category for row in sites)
                for category in sorted(set(TARGETS.values()))
            },
            "sites": sites,
        }
    return {
        "schema": SCHEMA,
        "scope": "explicit float(), int(), and np.asarray() calls in the model and scratch-optimizer source",
        "interpretation": (
            "source-call inventory only; actual dtype changes, allocations, copies, "
            "runtime costs, and FLOP status are not inferred"
        ),
        "modules": modules,
        "coverage": {
            "all_matching_ast_calls_listed": True,
            "runtime_conversion_behavior_verified": False,
            "full_counter": False,
            "parity_eligible": False,
            "graph_freeze_eligible": False,
        },
    }


def collect_conversion_inventory(repo_root: str | Path = ".") -> dict:
    root = Path(repo_root)
    return inventory_sources({
        path: (root / path).read_text(encoding="utf-8")
        for path in SOURCE_PATHS
    })


def canonical_sha256(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    print(json.dumps(collect_conversion_inventory(), sort_keys=True, indent=2,
                     ensure_ascii=False, allow_nan=False))
