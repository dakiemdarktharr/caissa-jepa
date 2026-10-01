"""Fixed-schedule model-blind roots, rule differential, and exact-label gate.

Outputs are exploratory feasibility receipts/root banks, never learned results.
Run only with project-owned rules and local compute; timeouts stay in the bank.
"""
import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.alpha_beta_reference import AlphaBetaReferenceSolver
from benchmarks.reference_rules import ReferenceBudgetExceeded, ReferenceGame
from two_player.games import BoardGame, State


GAMES = {
    "connect4-gravity-4x5": (BoardGame("connect4-gravity-4x5", 4, 5, 4, gravity=True),
                             ReferenceGame(4, 5, 4, gravity=True)),
    "reversi6": (BoardGame("reversi6", 6, 6, 0, reversi=True),
                 ReferenceGame(6, 6, 0, reversi=True)),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schedule_roots(game_name, count, schedule_seed, first_trajectory_seed,
                   min_ply=5, max_ply=11, reversi_empty_min=5, reversi_empty_max=8,
                   max_episodes=100_000):
    """Predeclare one uniform-legal self-play root candidate per episode seed."""
    adapter, _ = GAMES[game_name]
    schedule = random.Random(schedule_seed)
    rows, rejected = [], []
    seen = set()
    attempts = 0
    for offset in range(max_episodes):
        if len(rows) >= count:
            break
        attempts += 1
        episode_seed = first_trajectory_seed + offset
        rng = random.Random(episode_seed)
        state = adapter.initial()
        if game_name.startswith("connect4"):
            target = schedule.randint(min_ply, max_ply)
            for _ in range(target):
                if adapter.terminal(state) is not None:
                    break
                state = adapter.transition(state, rng.choice(adapter.legal_actions(state)))
            ply = sum(cell != 0 for cell in state.board)
            schedule_tag = {"target_ply": target}
        else:
            target = schedule.randint(reversi_empty_min, reversi_empty_max)
            ply = 0
            while adapter.terminal(state) is None and state.board.count(0) > target:
                state = adapter.transition(state, rng.choice(adapter.legal_actions(state)))
                ply += 1
            schedule_tag = {"target_empties": target}
        if adapter.terminal(state) is not None:
            rejected.append({"trajectory_seed": episode_seed, "schedule": schedule_tag,
                             "disposition": "terminal_candidate"})
            continue
        key = adapter.canonical_key(state)
        if key in seen:
            rejected.append({"trajectory_seed": episode_seed, "schedule": schedule_tag,
                             "disposition": "duplicate_symmetry_candidate",
                             "canonical_key": key})
            continue
        seen.add(key)
        rows.append({"index": len(rows), "trajectory_seed": episode_seed,
                     "ply": ply, "state": state, "schedule": schedule_tag,
                     "canonical_key": key, "disposition": "scheduled_root"})
    return rows, rejected, attempts


def action_to_reference(adapter, action):
    if action == 64:
        return -1
    row, col = divmod(action, 8)
    return row * adapter.cols + col


def action_to_adapter(adapter, action):
    if action == -1:
        return 64
    row, col = divmod(action, adapter.cols)
    return row * 8 + col


def compare_rules(adapter, reference, state):
    ref_state = reference.from_board(state.board, state.player)
    if reference.terminal(ref_state) != adapter.terminal(state):
        raise AssertionError("terminal outcome disagreement")
    expected = tuple(sorted(action_to_adapter(adapter, a) for a in reference.legal_actions(ref_state)))
    actual = tuple(sorted(adapter.legal_actions(state)))
    if expected != actual:
        raise AssertionError(f"legal action disagreement: adapter={actual}, reference={expected}")
    compared = 0
    for action in actual:
        left = adapter.transition(state, action)
        right = reference.transition(ref_state, action_to_reference(adapter, action))
        if left.board != reference.board(right) or left.player != right.player:
            raise AssertionError(f"first transition disagreement at action {action}")
        if adapter.terminal(left) != reference.terminal(right):
            raise AssertionError(f"terminal disagreement after root action {action}")
        if reference.terminal(right) is None:
            expected_replies = tuple(sorted(action_to_adapter(adapter, a)
                                            for a in reference.legal_actions(right)))
            actual_replies = tuple(sorted(adapter.legal_actions(left)))
            if expected_replies != actual_replies:
                raise AssertionError("reply legal-action disagreement")
            for reply in actual_replies:
                l2 = adapter.transition(left, reply)
                r2 = reference.transition(right, action_to_reference(adapter, reply))
                if l2.board != reference.board(r2) or l2.player != r2.player:
                    raise AssertionError(f"second transition disagreement at {action},{reply}")
                if adapter.terminal(l2) != reference.terminal(r2):
                    raise AssertionError("two-ply terminal disagreement")
                compared += 1
        compared += 1
    return compared


def depth_two_values(adapter, state):
    """Terminal-aware, zero-cutoff max-min labels used only for beyond-depth."""
    root_player = state.player
    result = {}
    for action in adapter.legal_actions(state):
        child = adapter.transition(state, action)
        outcome = adapter.terminal(child)
        if outcome is not None:
            result[action] = root_player * outcome
            continue
        reply_values = []
        for reply in adapter.legal_actions(child):
            leaf = adapter.transition(child, reply)
            outcome = adapter.terminal(leaf)
            reply_values.append(root_player * outcome if outcome is not None else 0)
        result[action] = min(reply_values)
    return result


def state_fingerprints(adapter, state):
    raw = {"board": list(state.board), "player": state.player}
    relative = {"board": [cell * state.player for cell in state.board], "player": 1}
    return {"raw": digest(raw), "role_normalized": digest(relative),
            "symmetry_normalized": adapter.canonical_key(state)}


def inspect_root(adapter, reference, row, node_limit, time_limit, cache_limit):
    state = row["state"]
    rule_pairs = compare_rules(adapter, reference, state)
    h2 = depth_two_values(adapter, state)
    branch_fingerprints = []
    for action in adapter.legal_actions(state):
        child = adapter.transition(state, action)
        branch_fingerprints.append({"depth": 1, "action": action,
                                    "terminal": adapter.terminal(child) is not None,
                                    **state_fingerprints(adapter, child)})
        if adapter.terminal(child) is None:
            for reply in adapter.legal_actions(child):
                leaf = adapter.transition(child, reply)
                branch_fingerprints.append({"depth": 2, "action": action,
                                            "reply": reply,
                                            "terminal": adapter.terminal(leaf) is not None,
                                            **state_fingerprints(adapter, leaf)})
    solver = AlphaBetaReferenceSolver(reference, node_limit=node_limit,
                                      time_limit=time_limit, cache_limit=cache_limit)
    started = time.perf_counter()
    try:
        ref_values = solver.action_values(reference.from_board(state.board, state.player))
        values = {action_to_adapter(adapter, action): int(value)
                  for action, value in ref_values.items()}
        complete = len(values) == len(adapter.legal_actions(state))
        if not complete:
            raise AssertionError("oracle returned an incomplete legal root action map")
        beyond = len(set(h2.values())) == 1 and len(set(values.values())) > 1
        exact_variable = len(set(values.values())) > 1
        error = None
    except ReferenceBudgetExceeded as exc:
        values, complete, beyond, exact_variable = None, False, None, None
        error = str(exc)
    return {
        "index": row["index"], "trajectory_seed": row["trajectory_seed"],
        "ply": row["ply"], "schedule": row["schedule"],
        "canonical_key": row["canonical_key"],
        "root_state_fingerprints": state_fingerprints(adapter, state),
        "legal_root_actions": len(adapter.legal_actions(state)),
        "two_ply_branch_keys": len(branch_fingerprints),
        "unique_two_ply_leaf_keys": len({branch["symmetry_normalized"]
                                         for branch in branch_fingerprints if branch["depth"] == 2}),
        "branch_state_fingerprints": branch_fingerprints,
        "rule_comparisons": rule_pairs,
        "rule_differential_pass": True,
        "depth2_action_values": h2,
        "exact_root_action_values": values,
        "exact_complete": complete,
        "exact_action_values_variable": exact_variable,
        "beyond_depth": beyond,
        "oracle_error": error,
        "oracle_nodes": solver.last_stats.get("nodes", 0),
        "oracle_seconds": round(time.perf_counter() - started, 6),
    }


def run(game_name, count, schedule_seed, first_seed, nodes, seconds, cache,
        min_ply, max_ply, reversi_empty_min, reversi_empty_max,
        max_episodes=100_000):
    adapter, reference = GAMES[game_name]
    scheduled, rejected, attempts = schedule_roots(
        game_name, count, schedule_seed, first_seed, min_ply, max_ply,
        reversi_empty_min, reversi_empty_max, max_episodes)
    roots = []
    for row in scheduled:
        state = row.pop("state")
        record = inspect_root(adapter, reference, {**row, "state": state}, nodes, seconds, cache)
        record["board"] = list(state.board)
        record["player"] = state.player
        roots.append(record)
    completed = [row for row in roots if row["exact_complete"]]
    result = {
        "schema": "caissa-jepa-v28-modelblind-gate-v1",
        "stage": "exploratory fixed-schedule model-blind feasibility; no training",
        "game": game_name,
        "schedule": {"candidate_quota": count, "attempts": attempts,
                     "schedule_seed": schedule_seed, "first_trajectory_seed": first_seed,
                     "connect4_target_ply": [min_ply, max_ply] if game_name.startswith("connect4") else None,
                     "reversi_target_empties": [reversi_empty_min, reversi_empty_max] if game_name == "reversi6" else None,
                     "behavior_policy": "project-owned uniform over legal actions",
                     "unique_symmetry_roots": len(roots)},
        "oracle_budget": {"nodes": nodes, "seconds_per_root": seconds, "cache_entries": cache,
                          "coverage_rule": "100% of the fixed scheduled root population or gate failure; no solver-success filtering"},
        "summary": {"scheduled_roots": len(roots),
                    "requested_unique_roots": count,
                    "candidate_quota_pass": len(roots) == count,
                    "complete_exact_maps": len(completed),
                    "timeouts_or_failures": len(roots) - len(completed),
                    "variable_exact_labels": sum(row["exact_action_values_variable"] is True for row in completed),
                    "beyond_depth_roots": sum(row["beyond_depth"] is True for row in completed),
                    "support_floor_pass": (len(roots) >= 100 and
                                           sum(row["beyond_depth"] is True for row in completed) >= 50),
                    "rule_comparison_pairs": sum(row["rule_comparisons"] for row in roots),
                    "all_roots_rule_valid": bool(roots) and all(row["rule_differential_pass"] for row in roots),
                    "oracle_coverage_pass": (len(roots) == count and bool(roots) and len(completed) == len(roots)),
                    "gate_pass": (len(roots) == count and bool(roots) and len(completed) == len(roots)
                                  and len(roots) >= 100
                                  and sum(row["beyond_depth"] is True for row in completed) >= 50
                                  and all(row["rule_differential_pass"] for row in roots))},
        "discarded_candidates": rejected,
        "roots": roots,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {"gate": source_hash(__file__),
                          "adapter": source_hash(ROOT / "two_player/games.py"),
                          "planner": source_hash(ROOT / "two_player/planner.py"),
                          "reference_rules": source_hash(ROOT / "benchmarks/reference_rules.py"),
                          "alpha_beta": source_hash(ROOT / "benchmarks/alpha_beta_reference.py")},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "claim_limit": "Self-generated root/oracle feasibility only; not training data quality, model performance, power, or JEPA advantage.",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=tuple(GAMES))
    parser.add_argument("output", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--schedule-seed", type=int, default=28093030)
    parser.add_argument("--first-seed", type=int, default=29000000)
    parser.add_argument("--nodes", type=int, default=500_000)
    parser.add_argument("--seconds", type=float, default=2.0)
    parser.add_argument("--cache", type=int, default=500_000)
    parser.add_argument("--min-ply", type=int, default=5)
    parser.add_argument("--max-ply", type=int, default=11)
    parser.add_argument("--reversi-empty-min", type=int, default=5)
    parser.add_argument("--reversi-empty-max", type=int, default=8)
    parser.add_argument("--max-episodes", type=int, default=100_000)
    args = parser.parse_args()
    if (args.count < 1 or args.nodes < 1 or args.cache < 0
            or not 0 < args.seconds <= 60 or args.max_ply < args.min_ply
            or args.reversi_empty_max < args.reversi_empty_min or args.max_episodes < 1):
        parser.error("invalid count, budget, or schedule bounds")
    report = run(args.game, args.count, args.schedule_seed, args.first_seed,
                 args.nodes, args.seconds, args.cache, args.min_ply, args.max_ply,
                 args.reversi_empty_min, args.reversi_empty_max, args.max_episodes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps(report["summary"], indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
