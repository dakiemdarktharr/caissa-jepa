"""Deterministic syntax-site inventory for the V2.12 model/update source.

This is a completeness aid for static counter review, not an operation counter.
AST syntax alone cannot decide floating-point dtype, executed branches, NumPy
kernel work, LAPACK implementation, or whether an expression is a FLOP.
"""
from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path


SCHEMA = "caissa.v212.source-operation-inventory.v01"
SOURCE_PATHS = (
    "two_player/v212_model.py",
    "two_player/v212_scratch_optimizer.py",
)
SITE_NODE_TYPES = (
    ast.BinOp,
    ast.AugAssign,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.If,
    ast.IfExp,
    ast.Return,
    ast.Raise,
    ast.For,
    ast.While,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Subscript,
    ast.Call,
)


def _operator_name(node: ast.AST) -> str:
    return type(node).__name__


def _syntax_sites(source: str, filename: str) -> list[dict]:
    tree = ast.parse(source, filename=filename)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, SITE_NODE_TYPES):
            continue
        if isinstance(node, ast.BinOp):
            detail = _operator_name(node.op)
        elif isinstance(node, ast.AugAssign):
            detail = _operator_name(node.op)
        elif isinstance(node, ast.UnaryOp):
            detail = _operator_name(node.op)
        elif isinstance(node, ast.BoolOp):
            detail = _operator_name(node.op)
        elif isinstance(node, ast.Compare):
            detail = [_operator_name(op) for op in node.ops]
        elif isinstance(node, ast.Call):
            detail = ast.unparse(node.func)
        elif isinstance(node, ast.Subscript):
            detail = ast.unparse(node)
        else:
            detail = type(node).__name__
        sites.append({
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "node": type(node).__name__,
            "detail": detail,
            "source": ast.unparse(node),
            "semantic_classification": "unresolved_by_syntax_inventory",
        })
    return sorted(sites, key=lambda row: (
        row["line"], row["end_line"], row["node"], str(row["detail"]), row["source"]))


def inventory_sources(sources: dict[str, str]) -> dict:
    """Inventory source text by relative path without importing project code."""
    modules = {}
    for filename in sorted(sources):
        source = sources[filename]
        if not isinstance(source, str):
            raise TypeError("source values must be text")
        raw = source.encode("utf-8")
        sites = _syntax_sites(source, filename)
        call_sites = [row for row in sites if row["node"] == "Call"]
        call_targets = Counter(row["detail"] for row in call_sites)
        modules[filename] = {
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "syntax_site_count": len(sites),
            "site_counts_by_node": dict(sorted(Counter(row["node"] for row in sites).items())),
            "binary_operators_by_syntax": dict(sorted(Counter(
                row["detail"] for row in sites if row["node"] == "BinOp").items())),
            "augmented_assignment_operators_by_syntax": dict(sorted(Counter(
                row["detail"] for row in sites if row["node"] == "AugAssign").items())),
            "unary_operators_by_syntax": dict(sorted(Counter(
                row["detail"] for row in sites if row["node"] == "UnaryOp").items())),
            "call_targets": [
                {"target": target, "count": count,
                 "lines": sorted(row["line"] for row in call_sites if row["detail"] == target)}
                for target, count in sorted(call_targets.items())
            ],
            "sites": sites,
        }
    return {
        "schema": SCHEMA,
        "scope": "AST syntax sites in the named model and scratch optimizer source files",
        "interpretation": (
            "syntax-only inventory; every site remains semantically unresolved here; "
            "not a FLOP count, execution trace, or parity result"
        ),
        "modules": modules,
        "coverage": {
            "complete_for_listed_ast_node_types": True,
            "complete_operation_semantics": False,
            "parity_eligible": False,
            "graph_freeze_eligible": False,
        },
    }


def collect_source_inventory(repo_root: str | Path = ".") -> dict:
    root = Path(repo_root)
    sources = {
        path: (root / path).read_text(encoding="utf-8")
        for path in SOURCE_PATHS
    }
    return inventory_sources(sources)


def canonical_sha256(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    report = collect_source_inventory()
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
