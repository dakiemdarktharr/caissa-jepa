"""Versioned, project-generated V2.8 trajectories and strict pre-fit audit.

This module is data plumbing only. It does not train a model, construct a
locked-final bank, or authorize training.
"""
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from .games import BoardGame, State
from .data import digest

DATA_VERSION = "v28-procedural-trajectories-v09"
RULES_VERSION = "v28-boardgame-adapters-v1"
MIN_PHASE_FRACTION = 1 / 3
POLICIES = ("uniform", "tactical", "positional", "bounded-search")
SPLITS = ("train", "validation", "selection", "locked-final")
GENERATION_PROTOCOLS = {
    "unit-diagnostic": {"episodes": 1, "seed": 883001, "records_allowed": False,
                         "splits": ("train", "validation", "selection")},
    "dev09-v1": {"episodes": 48, "seed": 28094007, "records_allowed": True,
                 "splits": ("train", "validation", "selection")},
}
V28_GAMES = {
    "connect4-gravity-6x7": BoardGame("connect4-gravity-6x7", 6, 7, 4, gravity=True),
    "reversi6": BoardGame("reversi6", 6, 6, 0, reversi=True),
}


def _raw_key(game, state):
    return digest((game.name, state.board, state.player))


def _normal_key(game, state):
    return game.canonical_key(state)


def _terminal_value(game, state):
    result = game.terminal(state)
    return None if result is None else state.player * result


def _line_score(game, state, player):
    """Bounded handcrafted policy heuristic; never used as a research label."""
    if game.reversi:
        board = state.board
        corners = (0, game.cols - 1, (game.rows - 1) * game.cols,
                   game.rows * game.cols - 1)
        corner = sum(board[i] == player for i in corners) - sum(board[i] == -player for i in corners)
        edges = [r * game.cols + c for r in range(game.rows) for c in range(game.cols)
                 if r in (0, game.rows - 1) or c in (0, game.cols - 1)]
        edge = sum(board[i] == player for i in edges) - sum(board[i] == -player for i in edges)
        mobility = len(game.placements(State(board, player))) - len(game.placements(State(board, -player)))
        discs = sum(board) * player
        return 25 * corner + 4 * edge + 2 * mobility + discs
    score = 0
    for r in range(game.rows):
        for c in range(game.cols - game.k + 1):
            segment = [state.board[r * game.cols + c + j] for j in range(game.k)]
            score += _segment_score(segment, player)
    for r in range(game.rows - game.k + 1):
        for c in range(game.cols):
            segment = [state.board[(r + j) * game.cols + c] for j in range(game.k)]
            score += _segment_score(segment, player)
    for r in range(game.rows - game.k + 1):
        for c in range(game.cols - game.k + 1):
            segment = [state.board[(r + j) * game.cols + c + j] for j in range(game.k)]
            score += _segment_score(segment, player)
        for c in range(game.k - 1, game.cols):
            segment = [state.board[(r + j) * game.cols + c - j] for j in range(game.k)]
            score += _segment_score(segment, player)
    return score + sum((game.cols - abs(game.cols - 1 - 2 * (i % game.cols))) * x * player
                       for i, x in enumerate(state.board))


def _segment_score(segment, player):
    own = sum(v == player for v in segment)
    other = sum(v == -player for v in segment)
    if own and other:
        return 0
    if own:
        return 4 ** own
    if other:
        return -(4 ** other)
    return 0


def _bounded_search(game, state, rng, node_cap=192, depth=4):
    count = [0]

    def negamax(current, remaining, alpha, beta):
        count[0] += 1
        terminal = _terminal_value(game, current)
        if terminal is not None:
            return terminal * 10000
        if remaining == 0 or count[0] >= node_cap:
            return _line_score(game, current, current.player)
        actions = game.legal_actions(current)
        values = []
        for action in actions:
            child = game.transition(current, action)
            value = -negamax(child, remaining - 1, -beta, -alpha)
            values.append((value, action))
            alpha = max(alpha, value)
            if alpha >= beta or count[0] >= node_cap:
                break
        return max(values)[0] if values else _line_score(game, current, current.player)

    scored = []
    alpha = -10**12
    for action in game.legal_actions(state):
        child = game.transition(state, action)
        score = -negamax(child, depth - 1, -10**12, -alpha)
        scored.append((score, action))
        alpha = max(alpha, score)
        if count[0] >= node_cap:
            break
    best = max(score for score, _ in scored)
    choices = [action for score, action in scored if score == best]
    return int(rng.choice(choices)), count[0]


def choose_action(game, state, family, rng):
    legal = game.legal_actions(state)
    if not legal:
        raise ValueError("Policy asked to act in terminal state")
    if family == "uniform":
        return int(rng.choice(legal)), 0
    if family == "bounded-search":
        return _bounded_search(game, state, rng)
    if family == "tactical":
        wins = [a for a in legal if game.terminal(game.transition(state, a)) == state.player]
        if wins:
            return int(rng.choice(wins)), 0
        blocks = []
        for action in legal:
            child = game.transition(state, action)
            if not any(game.terminal(game.transition(child, reply)) == -state.player
                       for reply in game.legal_actions(child)):
                blocks.append(action)
        return int(rng.choice(blocks or legal)), 0
    if family == "positional":
        wins = [a for a in legal if game.terminal(game.transition(state, a)) == state.player]
        candidates = wins or list(legal)
        def score(action):
            child = game.transition(state, action)
            terminal = _terminal_value(game, child)
            return terminal * 10000 if terminal is not None else _line_score(game, child, state.player)
        scores = np.asarray([score(a) for a in candidates], dtype=np.float64)
        scale = float(scores.std())
        normalized = (scores - scores.mean()) / max(scale, 1.0)
        logits = normalized / 0.75
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        return int(rng.choice(candidates, p=probabilities)), 0
    raise ValueError("Unknown behavior-policy family")


def _policy_pair(split, episode):
    if split in ("train", "validation"):
        return ("uniform", "tactical") if episode % 2 == 0 else ("tactical", "uniform")
    if split == "selection":
        return ("positional", "positional")
    if split == "locked-final":
        return ("bounded-search", "bounded-search")
    raise ValueError("Unknown split")


def generate_trajectory(game, split, episode, seed):
    if game.name not in V28_GAMES or split not in SPLITS or episode < 0:
        raise ValueError("Invalid game/split/episode")
    family_pair = _policy_pair(split, episode)
    rng = np.random.default_rng(np.random.SeedSequence([seed, episode, game.rows, game.cols]))
    state = game.initial()
    actions = []
    search_nodes = 0
    while game.terminal(state) is None:
        seat = 0 if state.player == 1 else 1
        action, nodes = choose_action(game, state, family_pair[seat], rng)
        search_nodes += nodes
        actions.append(action)
        state = game.transition(state, action)
        if len(actions) > 2 * game.rows * game.cols + 2:
            raise RuntimeError("Game exceeded its finite-placement bound")
    return {"schema": DATA_VERSION, "game": game.name, "split": split,
            "source_split": split,
            "episode": episode, "seed": seed, "policies_by_player": {"+1": family_pair[0], "-1": family_pair[1]},
            "actions": actions, "outcome": game.terminal(state),
            "search_nodes": search_nodes, "policy_family_hashes": _policy_family_hashes(),
            "provenance": "project-owned rules and policies; generated self-play"}


def replay(row):
    if row.get("schema") != DATA_VERSION or row.get("game") not in V28_GAMES:
        raise ValueError("Unknown schema or game")
    if (type(row.get("seed")) is not int or type(row.get("episode")) is not int
            or row["episode"] < 0 or row.get("source_split") not in SPLITS
            or row.get("provenance") != "project-owned rules and policies; generated self-play"
            or row.get("policy_family_hashes") != _policy_family_hashes()):
        raise ValueError("Missing or mismatched generated-trajectory lineage")
    game = V28_GAMES[row["game"]]
    regenerated = generate_trajectory(game, row["source_split"], row["episode"], row["seed"])
    for field in ("actions", "outcome", "policies_by_player", "search_nodes"):
        if regenerated[field] != row.get(field):
            raise ValueError(f"Trajectory does not reproduce from declared policy/seed: {field}")
    state = game.initial()
    states = [state]
    for action in row["actions"]:
        state = game.transition(state, action)
        states.append(state)
    outcome = game.terminal(state)
    if outcome is None or outcome != row.get("outcome"):
        raise ValueError("Unfinished trajectory or terminal label mismatch")
    return states


def trajectory_fingerprint(game, states, actions, outcome):
    transformed = []
    for mapping in game.transforms():
        mapped_actions = [game.transform(states[i], action, mapping)[1]
                          for i, action in enumerate(actions)]
        mapped_states = [game.transform(state, 64, mapping)[0] for state in states]
        for role_sign in (1, -1):
            path = [(tuple(role_sign * cell for cell in state.board), state.player * role_sign)
                    for state in mapped_states]
            transformed.append((path, tuple(mapped_actions), outcome * role_sign))
    return digest((game.name, min(transformed)))


def _closure_keys(game, state):
    keys = set()
    def add_state(candidate):
        keys.add(("raw", _raw_key(game, candidate)))
        keys.add(("normal", _normal_key(game, candidate)))
        for mapping in game.transforms():
            transformed, _ = game.transform(candidate, 64, mapping)
            for role_sign in (1, -1):
                board = tuple(role_sign * cell for cell in transformed.board)
                keys.add(("role-symmetry", digest((game.name, board,
                                                    transformed.player * role_sign))))
    for own in game.legal_actions(state):
        after_own = game.transition(state, own)
        add_state(after_own)
        replies = game.legal_actions(after_own)
        if not replies:
            continue
        for reply in replies:
            leaf = game.transition(after_own, reply)
            add_state(leaf)
    return keys


def _build_records_unchecked(rows, min_phase=1/3):
    records = []
    rejection = Counter()
    fingerprints = {}
    for row_index, row in enumerate(rows):
        try:
            game = V28_GAMES[row["game"]]
            states = replay(row)
            split = row["split"]
            policies = row["policies_by_player"]
            if split not in SPLITS or not isinstance(policies, dict) or set(policies) != {"+1", "-1"}:
                raise ValueError("Missing or malformed policy-family metadata")
            expected = {"train": {"uniform", "tactical"},
                        "validation": {"uniform", "tactical"},
                        "selection": {"positional"},
                        "locked-final": {"bounded-search"}}[split]
            if set(policies.values()) != expected:
                raise ValueError("Policy-family assignment does not match frozen split")
        except (KeyError, TypeError, ValueError):
            rejection["illegal_or_malformed_trajectory"] += 1
            continue
        fingerprint = trajectory_fingerprint(game, states, row["actions"], row["outcome"])
        if fingerprint in fingerprints:
            rejection["duplicate_symmetry_or_role_trajectory"] += 1
            continue
        fingerprints[fingerprint] = (row["split"], row_index)
        for ply, action in enumerate(row["actions"]):
            if ply / (game.rows * game.cols) < min_phase:
                continue
            future = states[ply + 2] if ply + 2 < len(states) else None
            state = states[ply]
            target = states[ply + 1]
            if game.transition(state, action) != target:
                raise ValueError("Illegal H1 trajectory target")
            reply = row["actions"][ply + 1] if future is not None else None
            if future is not None and game.transition(target, reply) != future:
                raise ValueError("Illegal H2 trajectory target")
            records.append({"game": row["game"], "split": row["split"],
                            "trajectory": fingerprint, "source_row": row_index,
                            "ply": ply, "phase_fraction": ply / (game.rows * game.cols),
                            "policies_by_player": dict(policies),
                            "state": asdict(state), "action": action,
                            "next": asdict(target), "reply": reply,
                            "future2": asdict(future) if future is not None else None,
                            "value": state.player * row["outcome"]})
    return records, dict(rejection)


def audit(rows, min_phase=MIN_PHASE_FRACTION):
    if min_phase != MIN_PHASE_FRACTION:
        raise ValueError("Audit phase threshold is frozen by the active protocol")
    counts = Counter()
    errors = []
    seen = set()
    fingerprint_split = {}
    trajectories = []
    for index, row in enumerate(rows):
        try:
            states = replay(row)
            game = V28_GAMES[row["game"]]
            if row["split"] not in SPLITS:
                raise ValueError("Unknown split")
            expected = {"train": {"uniform", "tactical"},
                        "validation": {"uniform", "tactical"},
                        "selection": {"positional"},
                        "locked-final": {"bounded-search"}}[row["split"]]
            policy_map = row["policies_by_player"]
            if not isinstance(policy_map, dict) or set(policy_map) != {"+1", "-1"}:
                raise ValueError("Policy metadata must contain exactly +1 and -1 seats")
            policies = set(policy_map.values())
            if policies != expected:
                raise ValueError("Opponent family leaked across frozen split")
            if row["split"] in ("train", "validation") and set(policy_map.values()) != {"uniform", "tactical"}:
                raise ValueError("Both mandatory development families must occupy the two seats")
            fingerprint = trajectory_fingerprint(game, states, row["actions"], row["outcome"])
            if fingerprint in seen:
                counts["duplicate_trajectory"] += 1
                if fingerprint_split[fingerprint] != row["split"]:
                    counts["duplicate_cross_split"] += 1
                continue
            seen.add(fingerprint)
            fingerprint_split[fingerprint] = row["split"]
            trajectories.append((index, fingerprint, row, states))
            counts[(row["game"], row["split"], "trajectories")] += 1
        except (KeyError, TypeError, ValueError) as error:
            counts["illegal_or_malformed_trajectory"] += 1
            errors.append({"row": index, "reason": str(error)})
    records, _duplicate_rejection = _build_records_unchecked(rows, min_phase)
    owners = {}
    overlap = Counter()
    branch_count = Counter()
    branch_set = defaultdict(set)
    split_families = defaultdict(set)
    split_seats = defaultdict(Counter)
    trajectory_keys = defaultdict(set)
    for _, fingerprint, row, states in trajectories:
        game = V28_GAMES[row["game"]]
        split = row["split"]
        split_families[(row["game"], split)].update(row["policies_by_player"].values())
        for seat, family in row["policies_by_player"].items():
            split_seats[(row["game"], split)][(seat, family)] += 1
        for ply in range(len(row["actions"])):
            if ply / (game.rows * game.cols) < min_phase:
                continue
            root = states[ply]
            keys = {("raw", _raw_key(game, root)), ("normal", _normal_key(game, root))}
            if ply + 1 < len(states):
                keys |= {("raw", _raw_key(game, states[ply+1])),
                         ("normal", _normal_key(game, states[ply+1]))}
            if ply + 2 < len(states):
                keys |= {("raw", _raw_key(game, states[ply+2])),
                         ("normal", _normal_key(game, states[ply+2]))}
            closure = _closure_keys(game, root)
            keys |= closure
            branch_count[(row["game"], split)] += len(closure)
            branch_set[(row["game"], split)].update(closure)
            for key in keys:
                trajectory_keys[fingerprint].add((row["game"], key))
                old = owners.get((row["game"], key))
                if old is not None and old != split:
                    overlap[(row["game"], old, split)] += 1
                else:
                    owners[(row["game"], key)] = split
    if counts["illegal_or_malformed_trajectory"]:
        errors.append({"reason": "illegal or malformed trajectories"})
    if counts["duplicate_cross_split"]:
        errors.append({"reason": "duplicate trajectory crosses split boundary"})
    support = {}
    for game_name in V28_GAMES:
        for split in SPLITS:
            items = [r for r in records if r["game"] == game_name and r["split"] == split]
            n_trajectories = counts[(game_name, split, "trajectories")]
            h2 = sum(r["future2"] is not None for r in items)
            support[f"{game_name}/{split}"] = {
                "records": len(items), "trajectories": n_trajectories,
                "h2_records": h2, "counterfactual_branch_states": branch_count[(game_name, split)],
                "unique_branch_keys": len(branch_set[(game_name, split)]),
                "policy_families": sorted(split_families[(game_name, split)])}
            mandatory = {"train": {"uniform", "tactical"}, "validation": {"uniform", "tactical"},
                         "selection": {"positional"}, "locked-final": {"bounded-search"}}[split]
            if n_trajectories and split_families[(game_name, split)] != mandatory:
                errors.append({"reason": "mandatory policy-family coverage failed", "group": f"{game_name}/{split}"})
            seat_counts = split_seats[(game_name, split)]
            for family in mandatory:
                if n_trajectories and any(seat_counts[(seat, family)] == 0 for seat in ("+1", "-1")):
                    errors.append({"reason": "policy family missing from a player seat", "group": f"{game_name}/{split}", "family": family})
            if split != "locked-final" and (n_trajectories < 8 or len(items) < 64 or h2 < 16):
                errors.append({"reason": "support floor failed", "group": f"{game_name}/{split}"})
            if split == "locked-final" and n_trajectories and (n_trajectories < 8 or len(items) < 64 or h2 < 16):
                errors.append({"reason": "locked-final support floor failed", "group": f"{game_name}/{split}"})
    if overlap:
        errors.append({"reason": "cross-split raw/canonical/context/target/counterfactual overlap",
                       "pairs": {"|".join(k): v for k, v in overlap.items()}})
    parent = {fingerprint: fingerprint for fingerprint in trajectory_keys}
    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    def union(left, right):
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a
    key_groups = defaultdict(list)
    for fingerprint, keys in trajectory_keys.items():
        for key in keys:
            key_groups[key].append(fingerprint)
    for fingerprints_for_key in key_groups.values():
        for other in fingerprints_for_key[1:]:
            union(fingerprints_for_key[0], other)
    components = defaultdict(list)
    row_by_fingerprint = {fingerprint: row for _, fingerprint, row, _ in trajectories}
    for fingerprint in parent:
        components[find(fingerprint)].append(fingerprint)
    mixed = []
    by_game_components = defaultdict(list)
    for members in components.values():
        rows_in_component = [row_by_fingerprint[key] for key in members]
        splits_in_component = sorted({row["split"] for row in rows_in_component})
        games_in_component = sorted({row["game"] for row in rows_in_component})
        families = sorted({family for row in rows_in_component
                           for family in row.get("policies_by_player", {}).values()})
        for game_name in games_in_component:
            by_game_components[game_name].append(len(members))
        if len(splits_in_component) > 1:
            mixed.append({"trajectories": len(members), "splits": splits_in_component,
                          "games": games_in_component, "policy_families": families,
                          "fingerprints": sorted(members)})
    report = {"schema": DATA_VERSION, "rules_version": RULES_VERSION,
              "games": {k: asdict(v) for k, v in V28_GAMES.items()},
              "input_trajectories": len(rows), "unique_trajectories": len(trajectories),
              "record_count": len(records), "counts": {"|".join(map(str, k)) if isinstance(k, tuple) else k: v for k, v in counts.items()},
              "support": support, "cross_split_overlap": {"|".join(k): v for k, v in overlap.items()},
              "overlap_components": {"count": len(components),
                                     "largest": max((len(x) for x in components.values()), default=0),
                                     "mixed_split_count": len(mixed), "components": [
                                         {"trajectories": len(members),
                                          "splits": sorted({row_by_fingerprint[key]["split"] for key in members}),
                                          "games": sorted({row_by_fingerprint[key]["game"] for key in members}),
                                          "policy_families": sorted({family for key in members for family in row_by_fingerprint[key].get("policies_by_player", {}).values()}),
                                          "fingerprints": sorted(members)}
                                         for members in sorted(components.values(), key=lambda x: min(x))],
                                     "mixed_split_examples": mixed,
                                     "by_game_sizes": {k: sorted(v, reverse=True)
                                                       for k, v in by_game_components.items()}},
              "min_phase_fraction": min_phase, "errors": errors,
              "status": "PASSED" if not errors else "FAILED",
              "trajectory_fingerprint": digest(sorted(seen)),
              "records_fingerprint": digest(records)}
    report["dataset_fingerprint"] = digest(report)
    return (records if report["status"] == "PASSED" else []), report


def build_records(rows, min_phase=MIN_PHASE_FRACTION):
    """Public record builder that fails closed unless the full data gate passes."""
    if min_phase != MIN_PHASE_FRACTION:
        raise ValueError("Record phase threshold is frozen by the active protocol")
    records, report = audit(rows, min_phase)
    if report["status"] != "PASSED":
        raise ValueError("Refusing to expose model-facing records before data audit passes")
    return records, {"audit_fingerprint": report["dataset_fingerprint"]}


def _component_assign(rows, min_phase=1/3):
    """Assign complete overlap components after constructing all leak keys."""
    unique = {}
    lineage_by_fp = defaultdict(list)
    states_by_fp = {}
    quarantined = []
    for index, row in enumerate(rows):
        try:
            game = V28_GAMES[row["game"]]
            states = replay(row)
            fp = trajectory_fingerprint(game, states, row["actions"], row["outcome"])
            if fp in unique:
                lineage_by_fp[fp].append(dict(row))
                continue
            unique[fp] = dict(row)
            lineage_by_fp[fp].append(dict(row))
            states_by_fp[fp] = states
        except (KeyError, TypeError, ValueError):
            quarantined.append({"row": index, "reason": "malformed candidate"})
    parent = {fp: fp for fp in unique}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    key_owner = {}
    for fp, row in unique.items():
        game = V28_GAMES[row["game"]]
        states = states_by_fp[fp]
        keys = set()
        for ply in range(len(row["actions"])):
            if ply / (game.rows * game.cols) < min_phase:
                continue
            root = states[ply]
            for state in states[ply:min(ply + 3, len(states))]:
                keys.add((row["game"], "raw", _raw_key(game, state)))
                for mapping in game.transforms():
                    transformed, _ = game.transform(state, 64, mapping)
                    for sign in (1, -1):
                        board = tuple(sign * cell for cell in transformed.board)
                        keys.add((row["game"], "normalized", digest((board, transformed.player * sign))))
            for kind, value in _closure_keys(game, root):
                keys.add((row["game"], kind, value))
        for key in keys:
            prior = key_owner.setdefault(key, fp)
            if prior != fp:
                union(prior, fp)
    groups = defaultdict(list)
    for fp in unique:
        groups[find(fp)].append(fp)
    assigned = []
    component_receipt = []
    assigned_family_counts = defaultdict(int)
    eligible_family_totals = Counter()
    for members in groups.values():
        family_set = {family for fp in members for lineage in lineage_by_fp[fp]
                      for family in lineage.get("policies_by_player", {}).values()}
        game_set = {unique[fp]["game"] for fp in members}
        if family_set == {"uniform", "tactical"} and len(game_set) == 1:
            eligible_family_totals[(next(iter(game_set)), "training_validation")] += len(members)
    split_families = {"train": {"uniform", "tactical"}, "validation": {"uniform", "tactical"},
                      "selection": {"positional"}, "locked-final": {"bounded-search"}}
    for members in sorted(groups.values(), key=lambda xs: min(xs)):
        rows_in_group = [unique[fp] for fp in members]
        all_lineage = [lineage for fp in members for lineage in lineage_by_fp[fp]]
        source_splits = sorted({r["split"] for r in all_lineage})
        families = {f for r in all_lineage for f in r.get("policies_by_player", {}).values()}
        compatible = [s for s in split_families if families == split_families[s] and s != "locked-final"]
        # Training and validation share a family set; a component may be assigned to one only.
        if families == {"uniform", "tactical"}:
            game_name = rows_in_group[0]["game"]
            current_validation = assigned_family_counts[(game_name, "validation")]
            target_validation = 0.25 * eligible_family_totals[(game_name, "training_validation")]
            target_split = "validation" if current_validation < target_validation else "train"
            assigned_family_counts[(game_name, target_split)] += len(members)
        elif families == {"positional"}:
            target_split = "selection"
        else:
            target_split = None
        if target_split is None or len(compatible) == 0:
            quarantined.append({"component": sorted(members), "families": sorted(families),
                                "source_splits": source_splits, "reason": "incompatible family component"})
        else:
            for row in rows_in_group:
                output = dict(row)
                output["split"] = target_split
                assigned.append(output)
        component_receipt.append({"fingerprints": sorted(members), "source_splits": source_splits,
                                  "policy_families": sorted(families), "assigned_split": target_split,
                                  "lineage_rows": len(all_lineage), "quarantined": target_split is None})
    return assigned, {"components": component_receipt, "quarantined": quarantined}


def source_hash():
    paths = [Path(__file__), Path(__file__).parent / "games.py", Path(__file__).parent / "data.py"]
    return digest({p.name: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                   for p in paths})


def code_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def generate_dataset(directory, *, protocol_id, episodes_per_game_split, seed,
                     splits=("train", "validation", "selection")):
    protocol = GENERATION_PROTOCOLS.get(protocol_id)
    if protocol is None or episodes_per_game_split != protocol["episodes"] or seed != protocol["seed"]:
        raise ValueError("Generation must match a named, frozen quota/seed protocol")
    if tuple(splits) != protocol["splits"]:
        raise ValueError("Generation split schedule must exactly match the frozen protocol")
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError(directory)
    started = time.perf_counter()
    candidates = []
    for game_index, game in enumerate(V28_GAMES.values()):
        for split_index, split in enumerate(splits):
            for episode in range(episodes_per_game_split):
                episode_seed = seed + game_index * 1_000_000 + split_index * 100_000
                candidates.append(generate_trajectory(game, split, episode, episode_seed))
    rows, assignment = _component_assign(candidates)
    records, report = audit(rows)
    if assignment["quarantined"]:
        report["errors"].append({"reason": "component-first assignment quarantined candidate components",
                                 "quarantined_components": len(assignment["quarantined"])})
    report["status"] = "PASSED" if not report["errors"] else "FAILED"
    report["dataset_fingerprint"] = digest({k: v for k, v in report.items() if k != "dataset_fingerprint"})
    artifacts = {}
    directory.mkdir(parents=True, exist_ok=False)
    output_items = [("trajectories.jsonl", rows)]
    # Model-facing rows are published only after the complete pre-fit audit passes.
    if report["status"] == "PASSED" and protocol["records_allowed"]:
        output_items.append(("records.jsonl", records))
    for name, items in output_items:
        path = directory / name
        path.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in items), encoding="utf-8")
        artifacts[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "bytes": path.stat().st_size, "rows": len(items)}
    manifest = {"schema": DATA_VERSION, "protocol_id": protocol_id,
                "source_sha256": source_hash(),
                "code_commit": code_commit(), "seed": seed,
                "episodes_per_game_split": episodes_per_game_split,
                "splits": list(splits), "generator": "project-owned self-play only",
                "external_data": False, "redistribution_license": "unassigned; do not distribute",
                "python": platform.python_version(), "numpy": np.__version__,
                "policy_family_hashes": _policy_family_hashes(),
                "component_assignment": assignment,
                "artifacts": artifacts, "audit": report,
                "seconds": time.perf_counter() - started,
                "audit_passed": report["status"] == "PASSED",
                "training_approved": False}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_split(directory, split):
    if split not in ("train", "validation", "selection"):
        raise ValueError("Loader refuses locked-final/test data and unsupported split")
    root = Path(directory)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("audit_passed") is not True or manifest.get("training_approved") is not True:
        raise ValueError("Dataset has not passed audit and explicit training approval")
    if manifest["schema"] != DATA_VERSION or manifest["source_sha256"] != source_hash():
        raise ValueError("Dataset/source identity mismatch")
    if manifest.get("policy_family_hashes") != _policy_family_hashes():
        raise ValueError("Opponent-policy implementation identity mismatch")
    if "records.jsonl" not in manifest["artifacts"]:
        raise ValueError("Audited model-facing records are absent")
    for name, item in manifest["artifacts"].items():
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            raise ValueError("Dataset artifact bytes changed")
    rows = [json.loads(line) for line in (root / "trajectories.jsonl").read_text(encoding="utf-8").splitlines()]
    records, actual = audit(rows)
    if actual != manifest["audit"] or digest(records) != actual["records_fingerprint"]:
        raise ValueError("Replay/data-audit identity mismatch")
    if actual["status"] != "PASSED":
        raise ValueError("Pre-fit data gate failed: " + json.dumps(actual["errors"], sort_keys=True))
    return [r for r in records if r["split"] == split], actual["dataset_fingerprint"]


def _policy_family_hashes():
    """Stable source identities; family names alone are not provenance."""
    module_hash = hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    sources = {"uniform": "rng.choice(legal)",
               "tactical": "immediate-win; one-ply-reply-block; random-ties",
               "positional": "handcrafted-heuristic-standardized-softmax-temperature-0.75",
               "bounded-search": "negamax-alpha-beta-depth4-nodecap192"}
    return {name: hashlib.sha256((DATA_VERSION + ":" + module_hash + ":" + source).encode()).hexdigest()
            for name, source in sources.items()}
