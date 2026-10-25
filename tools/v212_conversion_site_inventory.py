"""Source-site inventory for explicit numeric conversions in the V2.12 graph.

This reports Python/NumPy conversion requests for counter coverage review. It
does not infer whether an array is copied or cast at runtime, nor does it
assign a FLOP or elapsed-time cost.
"""
from __future__ import annotations

import ast
import hashlib
import json
from math import prod
from pathlib import Path

from tools.v212_optimizer_flop_accounting import accounting as optimizer_accounting
from two_player.games import ACTION_SIZE, FEATURE_SIZE


SCHEMA = "caissa.v212.conversion-site-inventory.v01"
SOURCE_PATHS = (
    "two_player/v212_model.py",
    "two_player/v212_scratch_optimizer.py",
)
TARGETS = {"float": "python_scalar_float", "int": "python_scalar_int",
           "np.asarray": "numpy_array_dtype_request"}
BATCH_SIZE = 64
TRANSITION_SLOTS = 4


def array_request_cardinality(batch_size: int = BATCH_SIZE) -> dict:
    """Count fixed-shape element slots presented at the V2.12 asarray sites.

    This counts requested output shapes by source call/branch. It does not
    infer runtime casts, hidden NumPy temporaries, or elapsed work.
    """
    if type(batch_size) is not int or batch_size != BATCH_SIZE:
        raise ValueError("the current V2.12 conversion fixture is fixed at batch 64")

    preflight_fields = (
        ("x", (batch_size, FEATURE_SIZE), "float64"),
        ("legal", (batch_size, ACTION_SIZE), "bool"),
        ("policy", (batch_size,), "int64"),
        ("value", (batch_size,), "float64"),
        ("actions", (batch_size, TRANSITION_SLOTS, ACTION_SIZE), "float64"),
        ("actors", (batch_size, TRANSITION_SLOTS), "float64"),
        ("future_x", (batch_size, TRANSITION_SLOTS, FEATURE_SIZE), "float64"),
        ("future_value", (batch_size, TRANSITION_SLOTS), "float64"),
        ("transition_exists", (batch_size, TRANSITION_SLOTS), "bool"),
        ("transition_valid", (batch_size, TRANSITION_SLOTS), "bool"),
        ("target_exists", (batch_size, TRANSITION_SLOTS), "bool"),
        ("terminal", (batch_size, TRANSITION_SLOTS), "bool"),
    )
    preflight_finite_elements = sum(prod(shape) for _, shape, _ in preflight_fields)
    preflight_initial_x_elements = batch_size * FEATURE_SIZE
    preflight_elements = preflight_finite_elements + preflight_initial_x_elements

    loss_common = {
        "x": batch_size * FEATURE_SIZE,
        "legal": batch_size * ACTION_SIZE,
        "policy": batch_size,
        "value": batch_size,
    }
    loss_direct_leaf = {
        "future_x": batch_size * TRANSITION_SLOTS * FEATURE_SIZE,
        "future_value": batch_size * TRANSITION_SLOTS,
    }
    loss_predictive = {
        "actions": batch_size * TRANSITION_SLOTS * ACTION_SIZE,
        "actors": batch_size * TRANSITION_SLOTS,
        "future_x": batch_size * TRANSITION_SLOTS * FEATURE_SIZE,
        "future_value": batch_size * TRANSITION_SLOTS,
    }
    common_elements = sum(loss_common.values())
    direct_leaf_elements = sum(loss_direct_leaf.values())
    predictive_elements = sum(loss_predictive.values())

    optimizer = optimizer_accounting()["arms"]
    per_arm = {}
    for arm, row in optimizer.items():
        trainable = row["trainable_coordinates"]
        trainable_tensors = row["trainable_parameter_tensors"]
        ema = row["ema_coordinates"]
        ema_tensors = row["ema_parameter_tensors"]
        optimizer_elements = 4 * trainable + ema
        optimizer_asarray_calls = 4 * trainable_tensors + ema_tensors
        leaf = arm == "direct-leaf-value"
        model_loss_elements = common_elements + (
            direct_leaf_elements if leaf else predictive_elements
        )
        model_loss_calls = 4 + (2 if leaf else 4)
        model_elements = preflight_elements + model_loss_elements
        per_arm[arm] = {
            "model": {
                "preflight_asarray_calls": 13,
                "preflight_requested_elements": preflight_elements,
                "loss_grad_asarray_calls": model_loss_calls,
                "loss_grad_requested_elements": model_loss_elements,
                "requested_elements_total": model_elements,
                "loss_grad_branch": "direct_leaf" if leaf else "predictive_and_other_arms",
            },
            "scratch_optimizer": {
                "asarray_call_invocations": optimizer_asarray_calls,
                "requested_elements": optimizer_elements,
                "explicit_copy_output_elements": optimizer_elements,
                "assumption": (
                    "frozen arm parameter shapes; four parameter/gradient/moment groups; "
                    "EMA target group is empty or has ew and eb"
                ),
            },
            "total_requested_asarray_elements": model_elements + optimizer_elements,
            "explicit_optimizer_copy_output_elements": optimizer_elements,
        }

    return {
        "schema": "caissa.v212.array-conversion-cardinality.v01",
        "scope": "source-requested output element slots at explicit np.asarray calls, for one 64-window invocation",
        "units": "array element slots; not casts, bytes, FLOPs, or runtime cost",
        "batch_size": batch_size,
        "preflight_finite_array_shapes_and_dtypes": [
            {"field": key, "shape": list(shape), "dtype": dtype,
             "output_elements": prod(shape)}
            for key, shape, dtype in preflight_fields
        ],
        "preflight": {
            "initial_x_asarray_calls": 1,
            "initial_x_requested_elements": preflight_initial_x_elements,
            "finite_array_helper_calls": len(preflight_fields),
            "finite_array_helper_requested_elements": preflight_finite_elements,
            "requested_elements_total": preflight_elements,
        },
        "loss_grad": {
            "common_calls": len(loss_common),
            "common_requested_elements": common_elements,
            "direct_leaf_branch_calls": len(loss_direct_leaf),
            "direct_leaf_branch_requested_elements": direct_leaf_elements,
            "other_arm_branch_calls": len(loss_predictive),
            "other_arm_branch_requested_elements": predictive_elements,
        },
        "per_arm": per_arm,
        "limitations": [
            "NumPy may return a view/alias or allocate/cast depending on input dtype, type, and layout.",
            "The model path has no explicit copy at these call sites; the optimizer separately calls array.copy().",
            "This does not include hidden temporaries, memory traffic, allocator/runtime overhead, or conversions outside the named source files.",
            "Parameter-shape totals assume the frozen v06 arm tensors; this is not an executed optimizer trace.",
        ],
        "eligibility": {
            "runtime_casts_verified": False,
            "complete_counter": False,
            "parity_eligible": False,
            "graph_freeze_eligible": False,
        },
    }


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
        "array_request_cardinality": array_request_cardinality(),
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
