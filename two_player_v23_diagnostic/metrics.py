"""Fixed unaugmented training diagnostics; no fitting, loading or planning."""
import json
import math
import time

import numpy as np

from tools.diagnose_v21_value_alignment import diagnostic
from two_player_v2 import GAMES_V2
from two_player_v2.data import state_from

GAMES = tuple(sorted(GAMES_V2))
BATCH_SIZE = 128


def _deadline(deadline):
    if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ValueError("A finite absolute diagnostic deadline is required")
    if time.perf_counter() >= deadline:
        raise TimeoutError("Snapshot diagnostic deadline exceeded")


def _geometry(z):
    """Entropy of normalized squared singular values, matching v2 geometry."""
    z = np.asarray(z, dtype=np.float64)
    if z.ndim != 2 or not len(z) or not z.shape[1] or not np.isfinite(z).all():
        raise ValueError("Invalid raw-node latent geometry")
    centered = z-z.mean(axis=0, keepdims=True)
    spectrum = np.linalg.svd(centered, compute_uv=False)**2
    spectrum = spectrum[spectrum > 0]
    probs = spectrum/spectrum.sum() if len(spectrum) else np.array([])
    std = np.std(z, axis=0)
    return {"samples": len(z), "dimensions": z.shape[1],
            "effective_rank": float(np.exp(-np.sum(probs*np.log(probs)))) if len(probs) else 0.,
            "mean_std": float(std.mean()), "median_std": float(np.median(std)),
            "weighting": "Every unique raw training node once; no canonical-orbit or fork weighting"}


def snapshot_metrics(model, train, deadline):
    """Measure one checkpoint on the caller's audited, full-label train export.

    The runtime verifies artifact identity and rules before this function. These
    local guards reject another split or missing labels before any encoding.
    Geometry weights raw node IDs once, including terminals. S excludes terminal
    targets and weights roots equally within each game/horizon, then its four
    supported components equally. Latent MSE in ``fit`` is not scale comparable
    across different models/capacities. This function does not update model state.
    """
    _deadline(deadline)
    manifest = train.get("manifest", {})
    if (manifest.get("role") != "redacted-training" or manifest.get("split") != "train"
            or manifest.get("fraction") != 1.):
        raise ValueError("Snapshot metrics accept only standalone full-label training")
    if (not train["roots"] or not train["forks"] or not train["nodes"]
            or any(r.get("split") != "train" for r in train["roots"])
            or any(f.get("split") != "train" for f in train["forks"])
            or set(r["game"] for r in train["roots"]) != set(GAMES)
            or set(n["game"] for n in train["nodes"].values()) != set(GAMES)):
        raise ValueError("Invalid training-only game/split inventory")
    if any(n.get("value_labelled") is not True
           or n.get("policy_labelled") is not (not n["terminal"])
           for n in train["nodes"].values()):
        raise ValueError("Snapshot diagnostics require every available oracle label")
    fit = diagnostic(model, train, saved=None, batch_size=BATCH_SIZE, deadline=deadline)
    _deadline(deadline)
    components = {}
    for game in GAMES:
        components[game] = {}
        for horizon in ("1", "2"):
            group = fit["games"][game]["horizons"][horizon]["nonterminal"]
            value = group["equal_root"]["encoded_oracle_mse"]
            if (group["roots_with_targets"] <= 0 or group["transition_targets"] <= 0
                    or value is None or not math.isfinite(value) or value < 0):
                raise ValueError("Every S game/horizon requires nonterminal target support")
            components[game][horizon] = {"encoded_oracle_mse": float(value),
                "root_count": group["root_count"], "roots_with_targets": group["roots_with_targets"],
                "transition_targets": group["transition_targets"]}
    geometry, collapse = {}, []
    for game in GAMES:
        nodes = [node for _, node in sorted(train["nodes"].items()) if node["game"] == game]
        chunks = []
        for begin in range(0, len(nodes), BATCH_SIZE):
            _deadline(deadline)
            group = nodes[begin:begin+BATCH_SIZE]
            x = np.stack([GAMES_V2[game].features(state_from(node["state"])) for node in group])
            z = np.asarray(model.encode(x), dtype=np.float64)
            if z.ndim != 2 or len(z) != len(group) or not np.isfinite(z).all():
                raise ValueError("Invalid encoded raw training nodes")
            chunks.append(z)
        _deadline(deadline)
        stats = _geometry(np.concatenate(chunks, axis=0))
        stats["terminal_nodes"] = sum(bool(n["terminal"]) for n in nodes)
        stats["nonterminal_nodes"] = len(nodes)-stats["terminal_nodes"]
        geometry[game] = stats
        if stats["effective_rank"] < 2 or stats["median_std"] < 1e-3:
            collapse.append({"game": game, "space": "unprojected", "samples": stats["samples"],
                             "effective_rank": stats["effective_rank"], "median_std": stats["median_std"]})
        _deadline(deadline)
    result = {"fit": fit, "geometry": geometry, "collapse": collapse,
              "S": float(np.mean([components[g][h]["encoded_oracle_mse"]
                                    for g in GAMES for h in ("1", "2")])),
              "S_components": components, "S_component_count": 4,
              "S_weighting": "Equal games and H1/H2; equal roots with nonterminal targets within each component",
              "counts": {"roots": len(train["roots"]), "forks": len(train["forks"]),
                         "unique_raw_nodes": len(train["nodes"])},
              "raw_latent_mse_limitation": "No common strategic scale across models or capacities"}
    # Catch nonfinite geometry or helper output, including diagnostics not in S.
    json.dumps(result, allow_nan=False)
    _deadline(deadline)
    return result
