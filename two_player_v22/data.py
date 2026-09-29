"""Standalone train-label redaction and development export; loaders never read parents."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from . import METHOD_VERSION
from two_player.data import digest, code_commit
from two_player_v2 import GAMES_V2
from two_player_v2.data import (load_dataset as parent_load, batch_arrays as parent_batch,
                                source_identity as parent_sources, node_id, state_from, closure)

DATA_VERSION = "standalone-label-access-v22.0"
ROOT_FIELDS = {"game", "trajectory", "state", "actions", "split", "canonical_key", "root_id"}
DEV_ROOT_FIELDS = ROOT_FIELDS | {"oracle_values", "beyond_depth"}
NODE_FIELDS = {"game", "state", "legal", "optimal", "value", "terminal", "value_labelled", "policy_labelled"}
FORK_FIELDS = {"root_id", "game", "split", "node_ids", "actions"}


def source_identity():
    root = Path(__file__).resolve().parents[1]
    paths = set(parent_sources()) | {"two_player_v22/data.py", "two_player_v22/__init__.py", "docs/METHOD_V22.md"}
    return {p: hashlib.sha256((root/p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in sorted(paths)}


def independent_root_id(root):
    return digest([root["game"], root["trajectory"], root["state"]])


def _parameters(fraction, label_seed):
    if type(fraction) not in (int, float) or fraction not in (.25, 1.0):
        raise ValueError("Only frozen label fractions 0.25 and 1.0 are supported")
    if type(label_seed) is not int or label_seed < 0:
        raise ValueError("Label seed must be a nonnegative integer")


def _selected(roots, fraction, label_seed):
    result = {}
    for name in GAMES_V2:
        group = [r for r in roots if r["game"] == name]
        if not group:
            raise ValueError("Missing game roots")
        ordered = sorted(group, key=lambda r: digest([label_seed, name, r["trajectory"], r["state"]]))
        result[name] = sorted(r["root_id"] for r in ordered[:math.ceil(fraction*len(group))])
    return result


def _known_keys(payload, selected):
    root_ids = {rid for group in selected.values() for rid in group}
    known = set()
    for fork in payload["forks"]:
        if fork["root_id"] in root_ids:
            for nid in fork["node_ids"]:
                if nid is not None:
                    node = payload["nodes"][nid]
                    known.add((node["game"], GAMES_V2[node["game"]].canonical_key(state_from(node["state"]))))
    return known


def _prepare(parent, fraction, label_seed, split="train"):
    """Pure preparation helper. Only the builder has access to parent labels."""
    _parameters(fraction, label_seed)
    root_map, roots = {}, []
    for original in parent["roots"]:
        if original["split"] != split:
            raise ValueError("Parent includes another split")
        fields = DEV_ROOT_FIELDS if split == "development" else ROOT_FIELDS
        root = {key: deepcopy(original[key]) for key in fields}
        if split == "train":
            root["root_id"] = independent_root_id(root)
        if original["root_id"] in root_map:
            raise ValueError("Duplicate parent root identifier")
        root_map[original["root_id"]] = root["root_id"]
        roots.append(root)
    forks = []
    for original in parent["forks"]:
        if original["split"] != split:
            raise ValueError("Parent fork includes another split")
        fork = {key: deepcopy(original[key]) for key in FORK_FIELDS}
        fork["root_id"] = root_map[original["root_id"]]
        forks.append(fork)
    nodes = {nid: {key: deepcopy(node[key]) for key in NODE_FIELDS-{"value_labelled", "policy_labelled"}}
             for nid, node in parent["nodes"].items()}
    payload = {"roots": roots, "forks": forks, "nodes": nodes}
    selected = _selected(roots, fraction, label_seed)
    known = _known_keys(payload, selected)
    for node in nodes.values():
        game = GAMES_V2[node["game"]]
        key = (node["game"], game.canonical_key(state_from(node["state"])))
        terminal = node["terminal"]
        labelled = terminal or key in known
        node["value_labelled"] = bool(labelled)
        node["policy_labelled"] = bool(labelled and not terminal)
        if not labelled:
            node["value"] = 0
            node["optimal"] = []
        if terminal:
            node["optimal"] = []
    return payload, selected


def _inspect(payload, fraction, label_seed, split, selected):
    """Reconstruct labels' availability and full legal closures without any parent."""
    if set(payload) != {"roots", "nodes", "forks"}:
        raise ValueError("Unexpected payload fields")
    if split not in ("train", "development") or (split == "development" and fraction != 1):
        raise ValueError("Invalid artifact split/fraction")
    roots, nodes, forks = payload["roots"], payload["nodes"], payload["forks"]
    by_root = {}
    root_fields = ROOT_FIELDS if split == "train" else DEV_ROOT_FIELDS
    for root in roots:
        if set(root) != root_fields or root["split"] != split:
            raise ValueError("Forbidden root fields or split")
        game = GAMES_V2[root["game"]]
        state = state_from(root["state"])
        if set(root["state"]) != {"board", "player"} or root["canonical_key"] != game.canonical_key(state):
            raise ValueError("Invalid root state/canonical identity")
        if tuple(root["actions"]) != game.legal_actions(state) or game.terminal(state) is not None:
            raise ValueError("Root actions/terminal mismatch")
        if not isinstance(root["trajectory"], str) or not root["trajectory"]:
            raise ValueError("Missing trajectory identity")
        if split == "train" and root["root_id"] != independent_root_id(root):
            raise ValueError("Root identity must not include oracle labels")
        if root["root_id"] in by_root:
            raise ValueError("Duplicate root identity")
        if split == "development":
            if type(root["beyond_depth"]) is not bool or len(root["oracle_values"]) != len(root["actions"]):
                raise ValueError("Invalid development oracle targets")
            if any(type(v) is not int or v not in (-1, 0, 1) for v in root["oracle_values"]):
                raise ValueError("Invalid development action utility")
        by_root[root["root_id"]] = root
    if selected != _selected(roots, fraction, label_seed):
        raise ValueError("Selected root mask differs from frozen state-only rule")
    node_keys = {}
    for nid, node in nodes.items():
        if set(node) != NODE_FIELDS or set(node["state"]) != {"board", "player"}:
            raise ValueError("Forbidden node fields")
        game = GAMES_V2[node["game"]]
        state = state_from(node["state"])
        if nid != node_id(node["game"], state) or tuple(node["legal"]) != game.legal_actions(state):
            raise ValueError("Node state identity/legal actions mismatch")
        terminal = game.terminal(state)
        if type(node["terminal"]) is not bool or node["terminal"] != (terminal is not None):
            raise ValueError("Terminal flag disagrees with rules")
        if type(node["value_labelled"]) is not bool or type(node["policy_labelled"]) is not bool:
            raise ValueError("Label availability must be boolean")
        if type(node["value"]) is not int or node["value"] not in (-1, 0, 1):
            raise ValueError("Invalid utility target")
        optimal = node["optimal"]
        if not isinstance(optimal, list) or any(type(a) is not int for a in optimal) or len(set(optimal)) != len(optimal):
            raise ValueError("Invalid policy target")
        if not set(optimal) <= set(node["legal"]):
            raise ValueError("Policy target contains illegal action")
        if terminal is not None:
            if not node["value_labelled"] or node["policy_labelled"] or optimal or node["value"] != state.player*terminal:
                raise ValueError("Free terminal labels disagree with rules")
        elif node["policy_labelled"] and not optimal:
            raise ValueError("Known nonterminal policy has no optimal action")
        if not node["value_labelled"] and node["value"] != 0:
            raise ValueError("Hidden utility must be zero-redacted")
        if not node["policy_labelled"] and optimal:
            raise ValueError("Hidden policy must be empty-redacted")
        node_keys[nid] = (node["game"], game.canonical_key(state))
    used, observed = set(), defaultdict(set)
    for fork in forks:
        if set(fork) != FORK_FIELDS or fork["split"] != split or fork["root_id"] not in by_root:
            raise ValueError("Forbidden fork fields or root/split mismatch")
        root = by_root[fork["root_id"]]
        if fork["game"] != root["game"] or len(fork["node_ids"]) != 3 or len(fork["actions"]) != 2:
            raise ValueError("Invalid fork structure")
        ids, actions = fork["node_ids"], fork["actions"]
        if ids[0] != node_id(root["game"], state_from(root["state"])):
            raise ValueError("Fork does not start at its root")
        key = (tuple(ids), tuple(actions))
        if key in observed[fork["root_id"]]:
            raise ValueError("Duplicate fork")
        observed[fork["root_id"]].add(key)
        game = GAMES_V2[fork["game"]]
        for horizon, action in enumerate(actions):
            if action is None:
                if horizon != 1 or ids[2] is not None or not nodes[ids[1]]["terminal"]:
                    raise ValueError("Invalid missing transition target")
                continue
            if type(action) is not int:
                raise ValueError("Invalid action type")
            before = state_from(nodes[ids[horizon]]["state"])
            if node_id(fork["game"], game.transition(before, action)) != ids[horizon+1]:
                raise ValueError("Illegal or mismatched transition")
        used.update(nid for nid in ids if nid is not None)
    if used != set(nodes):
        raise ValueError("Missing or orphaned nodes")
    for rid, root in by_root.items():
        _, expected, _ = closure(root["game"], state_from(root["state"]))
        if observed[rid] != {(tuple(ids), tuple(actions)) for ids, actions in expected}:
            raise ValueError("Incomplete legal root closure")
    known = _known_keys(payload, selected)
    mask = {}
    for nid, node in nodes.items():
        key = node_keys[nid]
        expected_value = node["terminal"] or key in known
        expected_policy = not node["terminal"] and key in known
        if (node["value_labelled"], node["policy_labelled"]) != (expected_value, expected_policy):
            raise ValueError("Global canonical label availability mismatch")
        item = [node["value_labelled"], node["policy_labelled"], node["terminal"]]
        if key in mask and mask[key] != item:
            raise ValueError("Duplicate canonical state has inconsistent masks")
        mask[key] = item
    mask_hash = digest([[name, key, *value] for (name, key), value in sorted(mask.items())])
    counts = {}
    for name in GAMES_V2:
        rows = [(key, value) for (game_name, key), value in mask.items() if game_name == name]
        nonterminal = [value for _, value in rows if not value[2]]
        unknown = sum(not value[0] for value in nonterminal)
        group = {"root_count": sum(r["game"] == name for r in roots), "selected_roots": len(selected[name]),
                 "unique_nonterminal_states": len(nonterminal),
                 "labelled_nonterminal_values": sum(value[0] for value in nonterminal),
                 "labelled_nonterminal_policies": sum(value[1] for value in nonterminal),
                 "unlabelled_nonterminal_states": unknown,
                 "unlabelled_nonterminal_fraction": unknown/len(nonterminal) if nonterminal else 0,
                 "free_terminal_states": sum(value[2] for _, value in rows), "horizons": {}}
        for h in range(3):
            ids = [f["node_ids"][h] for f in forks if f["game"] == name and f["node_ids"][h] is not None]
            keys = {node_keys[nid] for nid in ids}
            group["horizons"][str(h)] = {
                "valid_occurrences": len(ids), "unique_canonical_states": len(keys),
                "labelled_value_occurrences": sum(nodes[nid]["value_labelled"] for nid in ids),
                "labelled_policy_occurrences": sum(nodes[nid]["policy_labelled"] for nid in ids),
                "unique_nonterminal_values": sum(mask[key][0] and not mask[key][2] for key in keys),
                "unique_nonterminal_policies": sum(mask[key][1] for key in keys),
                "unique_unlabelled_nonterminal": sum(not mask[key][0] and not mask[key][2] for key in keys),
                "unique_free_terminal": sum(mask[key][2] for key in keys)}
        counts[name] = group
    errors = [name+": fewer than 50% nonterminal states remain unlabeled" for name, row in counts.items()
              if split == "train" and fraction == .25 and row["unlabelled_nonterminal_fraction"] < .5]
    return {"status": "FAILED" if errors else "PASSED", "errors": errors,
            "counts": counts, "canonical_label_mask_sha256": mask_hash}


def _build(parent_dataset, output, fraction, label_seed, split):
    _parameters(fraction, label_seed)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    source = source_identity()
    parent = parent_load(parent_dataset, split)
    payload, selected = _prepare(parent, fraction, label_seed, split)
    audit = _inspect(payload, fraction, label_seed, split, selected)
    if audit["status"] != "PASSED":
        (output/"failed-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        raise ValueError("Label-access readiness audit failed")
    if source_identity() != source:
        raise ValueError("Source changed during artifact preparation")
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    manifest = {"version": DATA_VERSION, "method": METHOD_VERSION, "split": split,
                "role": "redacted-training" if split == "train" else "standalone-development",
                "fraction": float(fraction), "label_seed": label_seed,
                "parent_dataset_fingerprint": parent["manifest"]["dataset_fingerprint"],
                "parent_audit_status": parent["manifest"]["audit"]["status"],
                "original_oracle_costs": deepcopy(parent["manifest"].get("oracle", {})),
                "source_identity": source, "code_commit": code_commit(), "selected_root_ids": selected,
                "canonical_label_mask_sha256": audit["canonical_label_mask_sha256"], "audit": audit,
                "root_count": len(payload["roots"]), "node_count": len(payload["nodes"]),
                "fork_count": len(payload["forks"]),
                "artifacts": {"data.json": {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}},
                "provenance": {"source": "project-owned solved bank; simulated label access",
                               "public_data_license": "NOT_ASSIGNED", "external_data": False,
                               "local_research_authorized": True, "oracle_compute_savings_claimed": False}}
    manifest["dataset_fingerprint"] = digest({key: value for key, value in manifest.items() if key != "code_commit"})
    (output/"data.json").write_bytes(raw)
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return manifest


def build_dataset(parent_dataset, output, fraction, label_seed=271828):
    return _build(parent_dataset, output, fraction, label_seed, "train")


def build_development(parent_dataset, output):
    return _build(parent_dataset, output, 1., 271828, "development")


def verify_bytes(directory):
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    if (manifest["version"] != DATA_VERSION or manifest["method"] != METHOD_VERSION
            or manifest["source_identity"] != source_identity() or manifest["audit"]["status"] != "PASSED"
            or manifest["parent_audit_status"] != "PASSED"):
        raise ValueError("Artifact version, source or audit mismatch")
    _parameters(manifest["fraction"], manifest["label_seed"])
    if manifest["role"] != {"train": "redacted-training", "development": "standalone-development"}.get(manifest["split"]):
        raise ValueError("Invalid artifact role/split")
    identity = {key: value for key, value in manifest.items() if key not in ("code_commit", "dataset_fingerprint")}
    if digest(identity) != manifest["dataset_fingerprint"] or set(manifest["artifacts"]) != {"data.json"}:
        raise ValueError("Manifest fingerprint/inventory changed")
    raw = (directory/"data.json").read_bytes()
    expected = manifest["artifacts"]["data.json"]
    if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError("Artifact bytes changed")
    return manifest, raw


def load_dataset(directory, split="train"):
    if split not in ("train", "development"):
        raise ValueError("Selection/final access is not authorized")
    manifest, raw = verify_bytes(directory)
    if manifest["split"] != split:
        raise ValueError("Artifact does not contain the requested split")
    payload = json.loads(raw)
    audit = _inspect(payload, manifest["fraction"], manifest["label_seed"], split, manifest["selected_root_ids"])
    if audit != manifest["audit"] or audit["canonical_label_mask_sha256"] != manifest["canonical_label_mask_sha256"]:
        raise ValueError("Reconstructed label mask/readiness audit differs")
    if any(manifest[key] != len(payload[field]) for key, field in
           (("root_count", "roots"), ("node_count", "nodes"), ("fork_count", "forks"))):
        raise ValueError("Artifact counters disagree")
    return {**payload, "manifest": manifest}


def batch_arrays(dataset, indices):
    indices = list(indices)
    result = parent_batch(dataset, indices)
    shape = result["valid"].shape
    result["value_labelled"] = np.zeros(shape, dtype=bool)
    result["policy_labelled"] = np.zeros(shape, dtype=bool)
    for i, index in enumerate(indices):
        fork = dataset["forks"][int(index)]
        for h, nid in enumerate(fork["node_ids"]):
            if nid is not None:
                node = dataset["nodes"][nid]
                result["value_labelled"][i, h] = node["value_labelled"]
                result["policy_labelled"][i, h] = node["policy_labelled"]
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    parser.add_argument("output")
    parser.add_argument("--fraction", type=float, choices=(.25, 1.), default=.25)
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    result = build_development(args.parent, args.output) if args.development else build_dataset(args.parent, args.output, args.fraction)
    print(json.dumps({"output": str(Path(args.output).resolve()), "split": result["split"],
                      "dataset_fingerprint": result["dataset_fingerprint"], "audit": result["audit"]}, indent=2))
