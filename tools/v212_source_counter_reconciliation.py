"""Source-hash-bound candidate crosswalk from AST sites to V2.12 subcounters.

The mapping is intentionally conservative. A candidate owner means a relevant
subcounter exists; it does not certify that the AST site's shape, branch, or
runtime work is fully counted. The report is not a complete FLOP counter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .v212_source_operation_inventory import collect_source_inventory


SCHEMA = "caissa.v212.source-counter-reconciliation.v02"
ANALYSIS_SOURCE_PATHS = (
    "tools/v212_source_operation_inventory.py",
    "tools/v212_source_counter_reconciliation.py",
)


def _source_record(root: Path, relative_path: str) -> dict:
    path = root / relative_path
    if not path.is_file():
        return {"exists": False, "source_sha256": None}
    return {
        "exists": True,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _site_disposition(module: str, site: dict) -> dict:
    node = site["node"]
    detail = site["detail"]
    if (module == "two_player/v212_model.py" and node == "Compare"
            and site.get("function") in {"preflight_batch", "_finite_array"}):
        return {
            "status": "candidate_owner_partial",
            "owner": "tools/v212_preflight_scan_accounting.py",
            "scope": "source-shaped comparison cardinalities and helper call count only; reductions, membership internals, invalid-path short-circuiting, and runtime cost remain open",
        }
    if node == "BinOp" and detail == "MatMult":
        return {
            "status": "candidate_owner",
            "owner": "tools/v212_model_matmul_flop_accounting.py",
            "scope": "explicit dense @ sites; analytical shape formula only",
        }
    if (module == "two_player/v212_scratch_optimizer.py"
            and site.get("function") == "scratch_adam_ema_step"
            and node == "BinOp" and detail in {"Add", "Sub", "Mult", "Div"}):
        return {
            "status": "candidate_owner",
            "owner": "tools/v212_optimizer_flop_accounting.py",
            "scope": (
                "scratch Adam/clipping/EMA arithmetic; analytical expression-shape owner, "
                "with the clipping division represented by its branch interval"
            ),
        }
    if module == "two_player/v212_model.py" and node == "BinOp":
        source = site["source"]
        function = site.get("function")
        if function == "preflight_batch" and detail in {"BitAnd", "BitOr"}:
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_preflight_bitwise_accounting.py",
                "scope": "Boolean bitwise output-element cardinality only; comparisons, inversion, reductions, indexing, and runtime costs remain open",
            }
        if detail in {"Add", "Sub", "Mult", "Div"}:
            if (detail == "Add" and " @ p[" in source and " + p[" in source
                    and function in {"_encode", "_value", "loss_grad"}):
                return {
                    "status": "candidate_owner",
                    "owner": "tools/v212_model_activation_flop_accounting.py",
                    "scope": "affine bias-addition site; shape totals are partial and separate from matmul work",
                }
            if function == "loss_grad":
                if (detail == "Sub" and (
                        source.startswith("masked_logits - np.max(")
                        or source.startswith("np.log(exp_logits.sum(axis=1)) - shifted")
                )) or (detail == "Div" and source.startswith("exp_logits / exp_logits.sum(")):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_policy_softmax_accounting.py",
                        "scope": "policy shift/probability/NLL elementwise site; reductions remain separately owned",
                    }
                if detail == "Sub" and (
                        source.startswith("root_value - np.asarray(")
                        or source in {"pred - labels", "pred_value - future_value[mask, h - 1]",
                                      "xhat - future_x[mask, horizon - 1]",
                                      "states[horizon][mask] - target"}
                ):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_model_loss_residual_accounting.py",
                        "scope": "objective residual subtraction shape; mask-dependent totals remain partial",
                    }
                if detail == "Sub" and source.startswith("1.0 - ") and " ** 2" in source:
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_model_activation_flop_accounting.py",
                        "scope": "explicit tanh-derivative one-minus-square subtraction; overlaps the square owner",
                    }
                if detail == "Mult" and (
                        source.startswith("2.0 / n * root_delta[:, None]")
                        or source.startswith("2.0 / len(pred) * delta[:, None]")
                        or source.startswith("2.0 * scale * delta[:, None]")
                        or source.startswith("dv @ p['vw'].T * (1.0 - ")
                        or source.startswith("dstate[step][rows] * (1.0 - ")
                        or source.startswith("dxhat @ p['dw'].T * (1.0 - ")
                        or source.startswith("dz0 * (1.0 - ")
                ):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_model_activation_flop_accounting.py",
                        "scope": "value-gradient scale or explicit tanh-derivative array multiply; source-shape candidate",
                    }
                if detail == "Mult" and source == "0.1 * dreg":
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_regularizer_elementwise_accounting.py",
                        "scope": "root regularizer gradient scaling; excluded from the general gradient-buffer subtotal",
                    }
                if detail == "Add" and source.startswith("raw_feature_grads[") and " + de @ " in source:
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_gradient_accumulation_accounting.py",
                        "scope": "raw decoder feature-gradient merge addition; source-shape candidate",
                    }
                if detail == "Add" and source.startswith("policy_loss + root_loss"):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_regularizer_elementwise_accounting.py",
                        "scope": "base plus weighted regularizer scalar objective; source-level scalar subtotal",
                    }
                if detail == "Mult" and source in {"0.1 * variance_loss", "0.01 * covariance_loss"}:
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_regularizer_elementwise_accounting.py",
                        "scope": "weighted regularizer scalar objective/metric; source-level scalar subtotal",
                    }
                if detail == "Add" and source.startswith("outcome_loss + rollout_loss"):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_objective_scalar_accounting.py",
                        "scope": "pooled rollout objective scalar accumulation; branch counts remain mask-dependent",
                    }
                if detail == "Mult" and "HORIZON_WEIGHTS[h] * int(preflight['valid'][h].sum())" == source:
                    return {
                        "status": "candidate_owner_partial",
                        "owner": "tools/v212_objective_scalar_accounting.py",
                        "scope": "horizon denominator scalar multiplication; Python sum/control overhead remains open",
                    }
                if detail == "Div" and (
                        source in {"2.0 / n", "2.0 / len(pred)", "weight / outcome_den",
                                   "weight / target_den", "np.sum(delta ** 2) / FEATURE_SIZE",
                                   "np.sum(delta ** 2) / d", "2.0 * scale / FEATURE_SIZE",
                                   "2.0 * scale / d"}
                ):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_objective_scalar_accounting.py",
                        "scope": "objective denominator or gradient-coefficient scalar division; branch/mask schedule remains unbound",
                    }
                if detail == "Mult" and (
                        source in {"2.0 * scale", "scale * float(np.sum(delta ** 2))",
                                   "scale * float(np.sum(delta ** 2) / FEATURE_SIZE)",
                                   "scale * float(np.sum(delta ** 2) / d)"}
                ):
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_objective_scalar_accounting.py",
                        "scope": "objective scalar coefficient/loss weighting; branch/mask schedule remains unbound",
                    }
                if detail == "Mult" and source in {
                        "2.0 * scale / FEATURE_SIZE * delta",
                        "2.0 * scale / d * delta"}:
                    return {
                        "status": "candidate_owner",
                        "owner": "tools/v212_objective_gradient_elementwise_accounting.py",
                        "scope": "pooled latent/raw target-gradient coefficient-times-residual array site",
                    }
            if ((function == "preflight_batch"
                 and source in {"terminal_idx + 1", "horizon - 1"})
                    or (function == "_active_prefix_masks" and source == "step + 1")
                    or (function == "__init__" and source in {
                        "d + ACTION_SIZE", "d + ACTION_SIZE + 1",
                        "d + ACTION_SIZE + 1 + 6"})):
                return {
                    "status": "reported_separately",
                    "owner": None,
                    "scope": "integer shape, horizon, or index arithmetic; outside FP FLOP totals",
                }
            if function == "weight" and source == "1.0 / fan_in":
                return {
                    "status": "reported_separately",
                    "owner": None,
                    "scope": "parameter-initialization scalar division; outside per-update objective/optimizer totals",
                }
            if function == "loss_grad" and (
                    source == "[z0] + [np.zeros((n, d), dtype=np.float64) for _ in range(4)]"
                    or source == "[None] * 4"
                    or source in {"step + 1", "h - 1", "horizon - 1", "step - 1"}
            ):
                return {
                    "status": "reported_separately",
                    "owner": None,
                    "scope": "Python list construction or integer state/horizon indexing arithmetic; not FP FLOPs",
                }
    if module == "two_player/v212_model.py" and site.get("function") == "_regularize":
        if node == "BinOp" and detail in {"Add", "Sub", "Mult", "Div"}:
            if site["source"] in {"d * n", "n * d"}:
                return {
                    "status": "reported_separately",
                    "owner": "tools/v212_regularizer_elementwise_accounting.py",
                    "scope": "integer scalar shape product; reported separately, not a FLOP",
                }
            if "spectrum" in site["source"] or "probabilities" in site["source"]:
                return {
                    "status": "candidate_owner",
                    "owner": "tools/v212_effective_rank_branch_accounting.py",
                    "scope": "effective-rank normalization/product arithmetic; branch and selected-count bounds apply",
                }
            return {
                "status": "candidate_owner",
                "owner": "tools/v212_regularizer_elementwise_accounting.py",
                "scope": "regularizer elementwise/scalar arithmetic; exclude delegated squares, reductions, and matmuls",
            }
        if node == "UnaryOp" and detail == "USub":
            if site["source"] == "-2.0":
                return {
                    "status": "reported_separately",
                    "owner": "tools/v212_regularizer_elementwise_accounting.py",
                    "scope": "negative scalar literal; no separate runtime FLOP under the source-level convention",
                }
            if site["source"].startswith("-np.sum(probabilities * np.log(probabilities))"):
                return {
                    "status": "reported_separately",
                    "owner": "tools/v212_effective_rank_branch_accounting.py",
                    "scope": "effective-rank unary negation; reported separately from FLOPs",
                }
    if node == "BinOp" and detail == "Pow":
        if module == "two_player/v212_model.py":
            return {
                "status": "candidate_owner",
                "owner": "tools/v212_model_square_flop_accounting.py",
                "scope": "fixed array-square semantic convention; overlaps other subcounters",
            }
        return {
            "status": "reported_separately",
            "owner": "tools/v212_optimizer_flop_accounting.py",
            "scope": "scalar Adam bias-correction powers; excluded from candidate FLOPs",
        }
    if node == "AugAssign":
        target = site.get("target", "")
        if target.startswith("grad[") or target.startswith("dstate[") or target.startswith("raw_feature_grads["):
            owner = "tools/v212_gradient_accumulation_accounting.py"
            scope = "candidate array-buffer additions; source-shape only"
        elif target == "dlogits" or target.startswith("dlogits["):
            owner = "tools/v212_policy_softmax_accounting.py"
            scope = "candidate policy-gradient normalization/label update"
        elif target == "dz" or (target == "dz0" and "dreg" in site["source"]):
            owner = "tools/v212_regularizer_elementwise_accounting.py"
            scope = "candidate regularizer-gradient accumulation/scaling"
        elif target == "dz0":
            owner = "tools/v212_gradient_accumulation_accounting.py"
            scope = "candidate raw-state gradient-buffer accumulation"
        elif target in {"total", "outcome_loss", "raw_loss", "rollout_loss"}:
            owner = "tools/v212_objective_scalar_accounting.py"
            scope = "candidate scalar objective accumulation"
        elif target.startswith("metrics["):
            return {
                "status": "explicitly_unresolved_non_fp",
                "owner": None,
                "scope": "integer telemetry/count accumulation, outside FLOPs",
            }
        else:
            owner = None
            scope = "no current owner identified for this augmented assignment target"
        return {
            "status": "candidate_owner" if owner else "explicitly_unresolved",
            "owner": owner,
            "scope": scope,
        }
    if node == "Call":
        target = detail
        if target == "np.linalg.eigvalsh":
            return {
                "status": "blocking_unresolved",
                "owner": None,
                "scope": "linked LAPACK/eigensolver implementation and operation bound",
            }
        if target == "z0.std":
            return {
                "status": "candidate_owner_runtime_unverified",
                "owner": "tools/v212_model_reduction_shape_accounting.py",
                "scope": "source-expanded NumPy 2.4.6 path; locked loaded runtime not verified",
            }
        if (site.get("function") == "_finite_array"
                and target in {"np.all", "np.isfinite"}):
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_preflight_scan_accounting.py",
                "scope": "associated with seven-array finite-check input cardinalities; boolean all-reduction and runtime cost are not separately counted",
            }
        if site.get("function") == "preflight_batch" and target.endswith(".sum"):
            return {
                "status": "explicitly_unresolved_non_fp",
                "owner": None,
                "scope": "mask/count cardinality in preflight; not currently assigned a runtime-cost owner",
            }
        if (site.get("function") == "loss_grad"
                and target in {"valid.sum", "preflight['valid'][h].sum", "mask.sum"}):
            return {
                "status": "explicitly_unresolved_non_fp",
                "owner": None,
                "scope": "Boolean mask/count cardinality; not a floating-point reduction FLOP or currently costed site",
            }
        if (site.get("function") == "scratch_adam_ema_step"
                and target == "np.sum" and "value * value" in site["source"]):
            return {
                "status": "candidate_owner",
                "owner": "tools/v212_optimizer_flop_accounting.py",
                "scope": "scratch optimizer global-norm square/reduction path; analytical arithmetic only",
            }
        if target in {"np.mean", "z.mean", "z0.mean", "spectrum.sum"} or target.endswith(".sum"):
            return {
                "status": "candidate_owner",
                "owner": "tools/v212_model_reduction_shape_accounting.py",
                "scope": "candidate reduction shapes/additions/divisions; loaded kernels unverified",
            }
        if target == "sum":
            if "HORIZON_WEIGHTS" in site["source"]:
                return {
                    "status": "candidate_owner_partial",
                    "owner": "tools/v212_objective_scalar_accounting.py",
                    "scope": "horizon denominator scalar construction; Python iteration/control cost open",
                }
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_model_reduction_shape_accounting.py",
                "scope": "Python scalar reduction candidate; context/site reconciliation required",
            }
        if target == "np.count_nonzero" and site.get("function") == "preflight_batch":
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_preflight_scan_accounting.py",
                "scope": "action scan cardinality only; not runtime/FLOPs or full predicate cost",
            }
        if target == "np.tanh":
            return {
                "status": "reported_separately",
                "owner": "tools/v212_model_activation_flop_accounting.py",
                "scope": "activation element counts; tanh transcendental cost not converted to FLOPs",
            }
        if target == "np.maximum" and site.get("function") == "_regularize":
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_regularizer_elementwise_accounting.py",
                "scope": "regularizer max-comparison cardinality; library cost not a FLOP count",
            }
        if target in {"np.exp", "np.log", "np.sqrt", "np.max"}:
            return {
                "status": "reported_separately_or_partially_bounded_non_fp",
                "owner": None,
                "scope": "transcendental/comparison cardinalities appear in specialized inventories; no common FLOP conversion",
            }
        if (site.get("function") == "preflight_batch"
                and target in {"np.any", "np.all", "np.isfinite", "np.isin", "np.issubdtype", "np.flatnonzero"}):
            return {
                "status": "candidate_owner_partial",
                "owner": "tools/v212_preflight_scan_accounting.py",
                "scope": "some preflight scan cardinalities only; predicate/index/control coverage incomplete",
            }
        if target in {"np.any", "np.all", "np.isfinite", "np.isin", "np.issubdtype", "np.flatnonzero"} or target.endswith(".any"):
            return {
                "status": "explicitly_unresolved_non_fp",
                "owner": None,
                "scope": "predicate/index scan in this function is not covered by the preflight-only cardinality subcounter",
            }
        if target == "np.asarray":
            return {
                "status": "explicitly_unresolved",
                "owner": None,
                "scope": "input-dependent dtype conversion/copy behavior is not currently costed",
            }
        if target in {"np.zeros", "np.zeros_like", "np.arange", "np.logical_or.reduce", "np.diag", "np.concatenate"} or target.endswith(".copy") or target.endswith(".tolist"):
            return {
                "status": "explicitly_unresolved_non_fp",
                "owner": None,
                "scope": "allocation/copy/shape/indexing/serialization behavior; not currently costed",
            }
        return {
            "status": "explicitly_unresolved",
            "owner": None,
            "scope": "call semantics or cost not mapped by the current partial ledger",
        }
    if node in {"Compare", "BoolOp", "If", "IfExp", "For", "While", "ListComp", "DictComp", "GeneratorExp", "Return", "Raise"}:
        return {
            "status": "explicitly_unresolved_non_fp",
            "owner": None,
            "scope": "predicate/control-flow/iteration cardinality is not a FLOP count and is incompletely costed",
        }
    if node == "Subscript":
        return {
            "status": "explicitly_unresolved_non_fp",
            "owner": None,
            "scope": "indexing/gather/scatter/copy behavior is not fully inventoried",
        }
    if node in {"UnaryOp", "AugAssign"} or (node == "BinOp" and detail in {"Add", "Sub", "Mult", "Div"}):
        return {
            "status": "explicitly_unresolved_or_context_owned",
            "owner": None,
            "scope": "arithmetic syntax needs parent-expression/shape ownership reconciliation",
        }
    return {
        "status": "explicitly_unresolved",
        "owner": None,
        "scope": "no current ledger disposition",
    }


def reconcile_source(repo_root: str | Path = ".") -> dict:
    root = Path(repo_root)
    inventory = collect_source_inventory(root)
    modules = {}
    status_counts = {}
    owner_counts = {}
    for name, module in inventory["modules"].items():
        sites = []
        for site in module["sites"]:
            disposition = _site_disposition(name, site)
            row = {**site, **disposition}
            sites.append(row)
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
            owner = row["owner"] or "<none>"
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
        modules[name] = {
            "source_sha256": module["source_sha256"],
            "syntax_site_count": module["syntax_site_count"],
            "sites": sites,
        }
    candidate_owner_paths = sorted({
        site["owner"]
        for module in modules.values()
        for site in module["sites"]
        if site["owner"] is not None
    })
    analysis_source_hashes = {
        path: _source_record(root, path) for path in ANALYSIS_SOURCE_PATHS
    }
    candidate_owner_source_hashes = {
        path: _source_record(root, path) for path in candidate_owner_paths
    }
    report = {
        "schema": SCHEMA,
        "scope": "static candidate ownership crosswalk for AST sites in the model and scratch optimizer",
        "interpretation": (
            "candidate owner dispositions only; partial owner means limited source-shape coverage; "
            "unresolved entries remain open; this is not a complete counter or execution trace"
        ),
        "modules": modules,
        "analysis_source_hashes": analysis_source_hashes,
        "candidate_owner_source_hashes": candidate_owner_source_hashes,
        "disposition_counts": dict(sorted(status_counts.items())),
        "candidate_owner_or_none_site_counts": dict(sorted(owner_counts.items())),
        "coverage": {
            "all_inventory_sites_have_a_disposition": True,
            "all_analysis_sources_present": all(
                record["exists"] for record in analysis_source_hashes.values()
            ),
            "all_candidate_owner_sources_present": all(
                record["exists"]
                for record in candidate_owner_source_hashes.values()
            ),
            "all_sites_have_a_validated_cost_owner": False,
            "full_counter": False,
            "parity_eligible": False,
            "graph_freeze_eligible": False,
            "open_requirements": [
                "validate each candidate owner against expression context and component overlap",
                "resolve the linked LAPACK eigensolver and actual NumPy reduction/runtime identity",
                "count or conservatively bound non-FP, allocation, indexing, and control-flow work",
                "bind the reviewed counter to an integrated frozen trainer/schedule trace",
            ],
        },
    }
    digest_payload = json.dumps(report, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False).encode("utf-8")
    report["crosswalk_sha256"] = hashlib.sha256(digest_payload).hexdigest()
    return report


if __name__ == "__main__":
    print(json.dumps(reconcile_source(), sort_keys=True, indent=2,
                     ensure_ascii=False, allow_nan=False))
