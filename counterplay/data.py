"""Bounded CP-01 behavior data and complete, terminal-solved H2 references.

No model fitting or locked-data generation. Source checkpoints, corpus
acceptance and Review 2 are separate from these construction primitives.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import time

import numpy as np

from benchmarks.reference_rules import (PASS, ReferenceBudgetExceeded,
                                       ReferenceGame, ReferenceSolver)
from two_player.games import BoardGame, State
from two_player.v28_data import choose_action
from two_player.v212_trajectory_audit import Window, _window_signature
from two_player.v212_window_batch import windows_to_model_batch

GAMES = {
    "connect4-6x7": BoardGame("connect4-6x7", 6, 7, 4, gravity=True),
    "reversi6": BoardGame("reversi6", 6, 6, 0, reversi=True),
}
CONTRACT = "counterplay-data-cp01-v1"
PAIRS = (("uniform", "uniform"), ("uniform", "tactical"),
         ("tactical", "uniform"), ("tactical", "tactical"))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def seed_for(*parts):
    return int(fingerprint([CONTRACT, *parts])[:16], 16)


def state_dict(state):
    return {"board": list(state.board), "player": state.player}


def state_from(row):
    return State(tuple(row["board"]), row["player"])


def reference_game(game):
    return ReferenceGame(game.rows, game.cols, game.k, game.gravity, game.reversi)


def adapter_action(game, action):
    return 64 if action == PASS else (action // game.cols) * 8 + action % game.cols


def audit_state(game, state):
    """Compare every legal transition to the independent bitboard rules."""
    ref = reference_game(game)
    other = ref.from_board(state.board, state.player)
    if ref.terminal(other) != game.terminal(state):
        raise ValueError("independent terminal mismatch")
    actions = ref.legal_actions(other)
    if sorted(adapter_action(game, a) for a in actions) != sorted(game.legal_actions(state)):
        raise ValueError("independent legal-action mismatch")
    for action in actions:
        child = ref.transition(other, action)
        actual = game.transition(state, adapter_action(game, action))
        if actual != State(ref.board(child), child.player):
            raise ValueError("independent transition mismatch")
    return len(actions)


def generate_episode(game, corpus_seed, role, index):
    if role not in ("train", "development"):
        raise ValueError("only train/development roles; locked generation is gated")
    rng = np.random.default_rng(seed_for(corpus_seed, role, game.name, index))
    policies = PAIRS[index % len(PAIRS)]
    states, actions = [game.initial()], []
    for _ in range(2 * game.rows * game.cols + 3):
        state = states[-1]
        if game.terminal(state) is not None:
            break
        family = policies[0 if state.player == 1 else 1]
        action, _ = choose_action(game, state, family, rng)
        actions.append(action)
        states.append(game.transition(state, action))
    else:
        raise ValueError("episode exceeded finite game-length bound")
    outcome = game.terminal(states[-1])
    if outcome is None:
        raise ValueError("episode did not terminate")
    return {"episode_id": f"{corpus_seed}:{role}:{game.name}:{index}",
            "game": game.name, "role": role, "index": index,
            "seed": seed_for(corpus_seed, role, game.name, index),
            "policies": list(policies), "states": [state_dict(s) for s in states],
            "actions": actions, "outcome": outcome}


def replay_episode(episode):
    game = GAMES[episode["game"]]
    states = [state_from(s) for s in episode["states"]]
    if not states or states[0] != game.initial() or len(states) != len(episode["actions"]) + 1:
        raise ValueError("episode initial state or length mismatch")
    comparisons = 0
    for i, state in enumerate(states):
        comparisons += audit_state(game, state)
        if i < len(episode["actions"]):
            if game.transition(state, episode["actions"][i]) != states[i + 1]:
                raise ValueError("episode replay mismatch")
    if game.terminal(states[-1]) != episode["outcome"] or episode["outcome"] is None:
        raise ValueError("episode terminal outcome mismatch")
    return states, comparisons


def episode_content(episode):
    game = GAMES[episode["game"]]
    states = tuple(state_from(s) for s in episode["states"])
    return _window_signature(game, states, tuple(episode["actions"]))


def candidate_root(episode, corpus_seed, max_empty):
    game = GAMES[episode["game"]]
    candidates = []
    for ply, value in enumerate(episode["states"]):
        state = state_from(value)
        if (game.terminal(state) is None and state.board.count(0) <= max_empty
                and len(game.legal_actions(state)) >= 2):
            key = game.canonical_key(state)
            order = fingerprint([corpus_seed, episode["episode_id"], key])
            candidates.append((order, ply, state, key))
    if not candidates:
        return None
    _, ply, state, key = min(candidates)
    return {"root_id": key, "game": game.name, "episode_id": episode["episode_id"],
            "ply": ply, "state": state_dict(state)}


def solved_fork(game, state, *, node_cap=100_000, seconds=2.0):
    """Return a complete q(a,b) table or raise; never return partial bounds.

    Every opponent action table is queried independently. The total node/time
    budgets cover all own actions and terminal branches of this one root.
    """
    if type(node_cap) is not int or node_cap < 1 or not 0 < seconds <= 60:
        raise ValueError("invalid reference budget")
    started = time.perf_counter()
    ref = reference_game(game)
    solver = ReferenceSolver(ref, node_limit=node_cap, time_limit=seconds,
                             cache_limit=node_cap)
    root_player = state.player
    if game.terminal(state) is not None:
        raise ValueError("reference root is terminal")
    nodes = transitions = 0
    rows = []
    for action in sorted(game.legal_actions(state)):
        child = game.transition(state, action)
        transitions += 1
        outcome = game.terminal(child)
        if outcome is not None:
            rows.append({"a": action, "b": None, "q": root_player * outcome,
                         "terminal": True})
            continue
        remaining = seconds - (time.perf_counter() - started)
        if remaining <= 0 or nodes >= node_cap:
            raise TimeoutError("complete fork reference budget exhausted")
        solver.node_limit = node_cap - nodes
        solver.time_limit = remaining
        values = solver.action_values(ref.from_board(child.board, child.player))
        nodes += solver.last_stats["nodes"]
        transitions += solver.last_stats["transitions"]
        for reply, value in sorted(values.items()):
            b = adapter_action(game, reply)
            leaf = game.transition(child, b)
            rows.append({"a": action, "b": b, "q": -value,
                         "terminal": game.terminal(leaf) is not None})
    if time.perf_counter() - started > seconds:
        raise TimeoutError("late complete fork reference return")
    return {"rows": rows, "nodes": nodes, "reference_transitions": transitions,
            "wall_seconds": time.perf_counter() - started,
            "reference_class": "terminal-solved", "root_player": root_player}


def critical_pair(rows):
    """CP-01 v2 reference-only primary candidate; terminal entries stay exact."""
    groups = {}
    for row in rows:
        groups.setdefault(row["a"], []).append(row)
    Q = {a: min(r["q"] for r in group) for a, group in groups.items()}
    optimum = max(Q.values())
    candidates = []
    for a, group in groups.items():
        ordered = sorted(group, key=lambda r: (r["q"], -1 if r["b"] is None else r["b"]))
        if len(ordered) < 2 or Q[a] >= optimum:
            continue
        c, second = ordered[:2]
        if (c["b"] is None or c["terminal"] or second["q"] - c["q"] < 0.5
                or second["q"] < optimum):
            continue
        controls = [r["b"] for r in group if r["b"] != c["b"] and not r["terminal"]
                    and r["q"] - c["q"] >= 0.5]
        if controls:
            candidates.append({"a": a, "b": c["b"], "controls": sorted(controls)})
    return min(candidates, key=lambda r: (r["a"], r["b"])) if candidates else None


def selected_windows(episodes, forbidden_keys, cap, corpus_seed, seen_content=None):
    if type(cap) is not int or cap < 32 or cap % 32:
        raise ValueError("per-game window cap must be a positive multiple of 32")
    seen_content = set() if seen_content is None else seen_content
    candidates, counts = {}, Counter()
    for episode in episodes:
        game = GAMES[episode["game"]]
        states = [state_from(s) for s in episode["states"]]
        for ply in range(len(episode["actions"])):
            counts["raw_windows"] += 1
            path = states[ply:ply + 5]
            for horizon in (1, 2, 4):
                prefix = path[1:horizon + 1]
                if any(game.terminal(s) is not None for s in prefix):
                    counts[f"raw_h{horizon}_terminal_masked"] += 1
                elif len(prefix) == horizon:
                    counts[f"raw_h{horizon}_valid_nonterminal"] += 1
                else:
                    counts[f"raw_h{horizon}_missing_or_truncated"] += 1
            if len(path) != 5 or game.terminal(path[-1]) is not None:
                counts["terminal_or_short_window"] += 1
                continue
            if any(game.canonical_key(s) in forbidden_keys for s in path):
                counts["eval_root_collision"] += 1
                continue
            actions = tuple(episode["actions"][ply:ply + 4])
            content = fingerprint([_window_signature(game, tuple(path), actions),
                                   path[0].player * episode["outcome"]])
            if content in seen_content:
                counts["cross_role_content_collision"] += 1
                continue
            source = f"{episode['episode_id']}:{ply}"
            if content not in candidates:
                candidates[content] = {"content_id": content, "episode_id": episode["episode_id"],
                                       "game": game.name, "role": episode["role"], "ply": ply,
                                       "states": [state_dict(s) for s in path], "actions": list(actions),
                                       "outcome": episode["outcome"], "source_ids": []}
            else:
                counts["within_role_content_duplicate"] += 1
            candidates[content]["source_ids"].append(source)
    ordered = sorted(candidates, key=lambda c: fingerprint([corpus_seed, episodes[0]["role"], c])) if episodes else []
    selected = [candidates[c] for c in ordered[:cap]]
    counts["unique_eligible_windows"] = len(candidates)
    counts["selected_windows"] = len(selected)
    counts["unselected_unique_windows"] = max(0, len(candidates) - cap)
    for horizon in (1, 2, 4):
        for status in ("valid_nonterminal", "terminal_masked", "missing_or_truncated"):
            counts.setdefault(f"raw_h{horizon}_{status}", 0)
            counts[f"selected_h{horizon}_{status}"] = len(selected) if status == "valid_nonterminal" else 0
    return selected, dict(counts)


def model_batch(windows):
    """Use the existing exact-replay adapter, including mask verification."""
    converted = []
    for row in windows:
        converted.append(Window(row["game"], row["episode_id"], "train", row["outcome"],
                                row["ply"], tuple(state_from(s) for s in row["states"]),
                                tuple(row["actions"]), (1, 2, 4), ()))
    return windows_to_model_batch(converted, GAMES)


def build(corpus_seed, *, train_episodes=32, development_episodes=50,
          train_cap=128, development_cap=32, cpu_seconds=300.0):
    """Construct one bounded development corpus in memory; no files or fits.

    A small fixture may override counts; production recipes bind exact values.
    All generated trajectories receive independent rules replay. No final data.
    """
    if (type(corpus_seed) is not int or type(train_episodes) is not int
            or type(development_episodes) is not int or train_episodes < 1
            or development_episodes < 1 or cpu_seconds <= 0):
        raise ValueError("invalid bounded construction config")
    started = time.process_time()
    episodes, roots, banks, audits = [], [], {}, {}
    episode_owners, root_keys, train_content = set(), set(), set()
    for role, count in (("train", train_episodes), ("development", development_episodes)):
        for name, game in GAMES.items():
            stats = Counter()
            for index in range(count):
                if time.process_time() - started >= cpu_seconds:
                    raise TimeoutError("corpus construction CPU limit; no corpus accepted")
                episode = generate_episode(game, corpus_seed, role, index)
                states, comparisons = replay_episode(episode)
                stats["generated_episodes"] += 1
                stats["replayed_states"] += len(states)
                stats["independent_transition_comparisons"] += comparisons
                stats[f"policy_pair_{index % 4}"] += 1
                identity = episode_content(episode)
                if role == "development" and identity in episode_owners:
                    stats["cross_role_duplicate_episode"] += 1
                    continue
                if role == "train":
                    episode_owners.add(identity)
                episodes.append(episode)
                stats["retained_episodes"] += 1
                if role != "development":
                    continue
                root = candidate_root(episode, corpus_seed, 8 if game.gravity else 6)
                if root is None:
                    stats["no_candidate_root"] += 1
                    continue
                if root["root_id"] in root_keys:
                    stats["duplicate_root"] += 1
                    continue
                root_keys.add(root["root_id"])
                stats["attempted_unique_roots"] += 1
                try:
                    root["reference"] = solved_fork(game, state_from(root["state"]))
                    root["primary_pair"] = critical_pair(root["reference"]["rows"])
                    root["status"] = "complete"
                    stats["complete_references"] += 1
                    stats["reference_pairable_roots"] += root["primary_pair"] is not None
                except (TimeoutError, ReferenceBudgetExceeded) as error:
                    root["status"] = "failed"
                    root["reason"] = str(error)
                    stats["failed_references"] += 1
                roots.append(root)
            audits[f"{role}:{name}"] = dict(stats)
    for role, cap in (("train", train_cap), ("development", development_cap)):
        banks[role] = []
        for name in GAMES:
            subset = [e for e in episodes if e["role"] == role and e["game"] == name]
            selected, counts = selected_windows(subset, root_keys, cap, corpus_seed,
                                                train_content if role == "development" else None)
            banks[role].extend(selected)
            audits[f"{role}:{name}"].update(counts)
            if role == "train":
                train_content.update(r["content_id"] for r in selected)
            audits[f"{role}:{name}"]["requested_windows"] = cap
            support = Counter()
            for row in selected:
                for ply, (a, state) in enumerate(zip(row["actions"], row["states"])):
                    support[f"ply{ply + 1}:actor{state['player']}:action{a}"] += 1
            audits[f"{role}:{name}"]["action_role_ply_support"] = dict(sorted(support.items()))
    sufficient = all(v["selected_windows"] == v["requested_windows"] for v in audits.values())
    reference_gate = all(
        audits[f"development:{name}"].get("reference_pairable_roots", 0) >= 5
        and audits[f"development:{name}"].get("complete_references", 0)
        >= 0.9 * max(1, audits[f"development:{name}"].get("attempted_unique_roots", 0))
        for name in GAMES)
    return {"contract_id": CONTRACT, "corpus_seed": corpus_seed, "episodes": episodes,
            "windows": banks, "roots": roots, "audit": audits,
            "window_count_gate": sufficient, "reference_yield_gate": reference_gate,
            "cpu_seconds": time.process_time() - started,
            "acceptance": "requires independent Review 2; construction gates alone are insufficient"}
