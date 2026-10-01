"""Model-blind paired-match evaluator for the V2.8 procedural board games.

This pilot evaluates only project-owned heuristic proxy policies. It is a
rules/replay/runtime diagnostic, not an evaluation of learned controls or JEPA.
Its schedule is disjoint from both data-generation and locked V08 seeds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

import numpy as np

from two_player.v28_data import POLICIES, V28_GAMES, choose_action

PROTOCOL = "v28-modelblind-match-pilot-v01"
CHECKPOINT_SEEDS = (17, 29, 43, 59, 71, 83, 97, 109, 127, 139,
                    151, 167, 181, 197, 211, 227, 241, 257, 271, 283)
PROXY_COMPARISONS = ("independent-tape-self-play", "reversed-tape-self-play")
MATCHES_PER_CHECKPOINT = 120
FIRST_MATCH_SEED = 33_000_000
SEARCH_POLICY = "bounded-search"
MAX_MOVE_SECONDS = 2.0


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _state_payload(state):
    return {"board": list(state.board), "player": state.player}


def _state_hash(state) -> str:
    return _sha(_canonical(_state_payload(state)))


def make_schedule(*, matches_per_checkpoint=MATCHES_PER_CHECKPOINT,
                  checkpoint_seeds=CHECKPOINT_SEEDS,
                  first_match_seed=FIRST_MATCH_SEED):
    if matches_per_checkpoint < 1 or first_match_seed < 1:
        raise ValueError("invalid pilot schedule dimensions")
    if not checkpoint_seeds or len(set(checkpoint_seeds)) != len(checkpoint_seeds):
        raise ValueError("checkpoint seeds must be nonempty and unique")
    rows = []
    for game in V28_GAMES:
        for comparison in PROXY_COMPARISONS:
            for checkpoint_index, checkpoint_seed in enumerate(checkpoint_seeds):
                for offset in range(matches_per_checkpoint):
                    match_seed = first_match_seed + checkpoint_index * matches_per_checkpoint + offset
                    row = {
                        "protocol": PROTOCOL,
                        "game": game,
                        "candidate_proxy": SEARCH_POLICY,
                        "comparison": comparison,
                        "checkpoint_seed": checkpoint_seed,
                        "match_seed": match_seed,
                        "color_assignments": [1, -1],
                    }
                    row["block_id"] = _sha(_canonical(row))
                    rows.append(row)
    return rows


def play_game(game, candidate_family, opponent_family, candidate_player,
              match_seed, checkpoint_seed, *, max_move_seconds=MAX_MOVE_SECONDS,
              candidate_rng_offset=1, opponent_rng_offset=2):
    if candidate_family not in POLICIES or opponent_family not in POLICIES:
        raise ValueError("unknown project-owned proxy policy")
    if candidate_player not in (-1, 1) or max_move_seconds <= 0:
        raise ValueError("invalid player assignment or move timeout")
    state = game.initial()
    transcript = []
    nodes = {"candidate": 0, "opponent": 0}
    elapsed = {"candidate": 0.0, "opponent": 0.0}
    rngs = {
        "candidate": np.random.default_rng(np.random.SeedSequence(
            [match_seed, checkpoint_seed, candidate_rng_offset])),
        "opponent": np.random.default_rng(np.random.SeedSequence(
            [match_seed, checkpoint_seed, opponent_rng_offset])),
    }
    plies = 0
    while game.terminal(state) is None:
        role = "candidate" if state.player == candidate_player else "opponent"
        family = candidate_family if role == "candidate" else opponent_family
        before = _state_hash(state)
        legal = tuple(game.legal_actions(state))
        if not legal:
            raise RuntimeError("nonterminal game state has no legal actions")
        started = time.perf_counter()
        action, action_nodes = choose_action(game, state, family, rngs[role])
        move_seconds = time.perf_counter() - started
        elapsed[role] += move_seconds
        if move_seconds > max_move_seconds:
            return {
                "candidate_score": 0.0 if role == "candidate" else 1.0,
                "candidate_family": candidate_family,
                "opponent_family": opponent_family,
                "candidate_player": candidate_player,
                "forfeit": role,
                "forfeit_reason": "proxy move timeout",
                "forfeit_details": {
                    "role": role,
                    "family": family,
                    "player": state.player,
                    "legal_actions": list(legal),
                    "late_action": action if type(action) is int else None,
                    "state_sha256": before,
                    "elapsed_seconds": move_seconds,
                    "limit_seconds": max_move_seconds,
                    "search_nodes": int(action_nodes),
                },
                "plies": plies,
                "transcript": transcript,
                "runtime_seconds": elapsed,
                "search_nodes": nodes,
            }
        if type(action) is not int or action not in legal:
            raise RuntimeError("proxy selected an illegal action")
        child = game.transition(state, action)
        nodes[role] += int(action_nodes)
        transcript.append({
            "role": role,
            "family": family,
            "player": state.player,
            "legal_actions": list(legal),
            "action": action,
            "before_sha256": before,
            "after_sha256": _state_hash(child),
            "elapsed_seconds": move_seconds,
            "search_nodes": int(action_nodes),
        })
        state = child
        plies += 1
        if plies > 2 * game.rows * game.cols + 2:
            raise RuntimeError("game exceeded finite-placement/pass bound")
    outcome = game.terminal(state)
    score = 0.5 if outcome == 0 else float(outcome == candidate_player)
    return {
        "candidate_score": score,
        "candidate_family": candidate_family,
        "opponent_family": opponent_family,
        "candidate_player": candidate_player,
        "outcome_absolute_player": outcome,
        "final_state": _state_payload(state),
        "final_state_sha256": _state_hash(state),
        "plies": plies,
        "transcript": transcript,
        "runtime_seconds": elapsed,
        "search_nodes": nodes,
        "forfeit": None,
    }


def play_paired_block(schedule_row, *, max_move_seconds=MAX_MOVE_SECONDS):
    game = V28_GAMES[schedule_row["game"]]
    if schedule_row["comparison"] not in PROXY_COMPARISONS:
        raise ValueError("unknown proxy comparison")
    opponent = SEARCH_POLICY
    candidate_rng_offset, opponent_rng_offset = (
        (1, 2) if schedule_row["comparison"] == "independent-tape-self-play"
        else (2, 1)
    )
    common = (game, SEARCH_POLICY, opponent, schedule_row["match_seed"],
              schedule_row["checkpoint_seed"])
    plus = play_game(common[0], common[1], common[2], 1, common[3], common[4],
                     max_move_seconds=max_move_seconds,
                     candidate_rng_offset=candidate_rng_offset,
                     opponent_rng_offset=opponent_rng_offset)
    minus = play_game(common[0], common[1], common[2], -1, common[3], common[4],
                      max_move_seconds=max_move_seconds,
                      candidate_rng_offset=candidate_rng_offset,
                      opponent_rng_offset=opponent_rng_offset)
    paired = (plus["candidate_score"] + minus["candidate_score"]) / 2 - 0.5
    result = {
        "block_id": schedule_row["block_id"],
        "game": schedule_row["game"],
        "comparison": schedule_row["comparison"],
        "checkpoint_seed": schedule_row["checkpoint_seed"],
        "match_seed": schedule_row["match_seed"],
        "candidate_proxy": SEARCH_POLICY,
        "opponent_proxy": opponent,
        "rng_design": schedule_row["comparison"],
        "candidate_scores_by_player": {"+1": plus["candidate_score"],
                                        "-1": minus["candidate_score"]},
        "paired_score_d": paired,
        "games": {"candidate_starts_plus": plus,
                  "candidate_starts_minus": minus},
    }
    return result


def verify_game_record(game, record, candidate_player):
    """Replay every recorded action and confirm state hashes and outcome."""
    state = game.initial()
    for step in record.get("transcript", []):
        expected_role = "candidate" if state.player == candidate_player else "opponent"
        expected_family = record.get(f"{expected_role}_family")
        if step.get("before_sha256") != _state_hash(state):
            return False
        legal = tuple(game.legal_actions(state))
        if list(legal) != step.get("legal_actions") or step.get("action") not in legal:
            return False
        if (step.get("player") != state.player or step.get("role") != expected_role
                or step.get("family") != expected_family):
            return False
        state = game.transition(state, step["action"])
        if step.get("after_sha256") != _state_hash(state):
            return False
    if record.get("forfeit") is not None:
        details = record.get("forfeit_details")
        if (not isinstance(details, dict)
                or details.get("role") not in {"candidate", "opponent"}
                or type(details.get("player")) is not int
                or details.get("player") != state.player
                or details.get("state_sha256") != _state_hash(state)
                or details.get("legal_actions") != list(game.legal_actions(state))
                or details.get("limit_seconds", 0) <= 0
                or details.get("elapsed_seconds", 0) <= details.get("limit_seconds", 0)
                or record.get("candidate_player") != candidate_player
                or record.get("forfeit") != details.get("role")):
            return False
        role = "candidate" if state.player == candidate_player else "opponent"
        score = 0.0 if role == "candidate" else 1.0
        late_action = details.get("late_action")
        if late_action is not None and late_action not in game.legal_actions(state):
            return False
        return (details["role"] == role and record.get("candidate_score") == score
                and record.get("forfeit_reason") == "proxy move timeout")
    outcome = game.terminal(state)
    if outcome is None or record.get("outcome_absolute_player") != outcome:
        return False
    expected_score = 0.5 if outcome == 0 else float(outcome == candidate_player)
    return (record.get("final_state") == _state_payload(state)
            and record.get("final_state_sha256") == _state_hash(state)
            and record.get("candidate_score") == expected_score)


def verify_block(schedule_row, result):
    if result.get("block_id") != schedule_row.get("block_id"):
        return False
    game = V28_GAMES[schedule_row["game"]]
    plus = result.get("games", {}).get("candidate_starts_plus")
    minus = result.get("games", {}).get("candidate_starts_minus")
    if not isinstance(plus, dict) or not isinstance(minus, dict):
        return False
    if not verify_game_record(game, plus, 1) or not verify_game_record(game, minus, -1):
        return False
    expected = (plus["candidate_score"] + minus["candidate_score"]) / 2 - 0.5
    return result.get("paired_score_d") == expected


def run_pilot(output_path: Path, *, blocks=12):
    """Run a disjoint proxy schedule, streaming transcripts and saving hashes."""
    dimensions = len(V28_GAMES) * len(PROXY_COMPARISONS)
    if type(blocks) is not int or blocks < dimensions or blocks % dimensions:
        raise ValueError("pilot blocks must be a positive multiple of all game/comparison cells")
    per_cell = blocks // dimensions
    checkpoint_count = min(len(CHECKPOINT_SEEDS), per_cell)
    matches_per_checkpoint = per_cell // checkpoint_count
    if checkpoint_count * matches_per_checkpoint != per_cell:
        raise ValueError("pilot size must divide evenly across checkpoint strata")
    schedule = make_schedule(
        matches_per_checkpoint=matches_per_checkpoint,
        checkpoint_seeds=CHECKPOINT_SEEDS[:checkpoint_count],
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    partial = output_path.with_suffix(output_path.suffix + ".partial.jsonl")
    receipt_path = output_path.with_suffix(output_path.suffix + ".receipt.json")
    source_sha = _sha(Path(__file__).read_bytes())
    schedule_sha = _sha(_canonical(schedule))
    summary_values = {}
    completed = 0
    started = time.perf_counter()
    cpu_started = time.process_time()
    header = {
        "schema": PROTOCOL,
        "record_type": "manifest",
        "status": "exploratory proxy pilot; no learned models or V08 outcomes",
        "source_sha256": source_sha,
        "schedule_sha256": schedule_sha,
        "block_count": len(schedule),
        "games": list(V28_GAMES),
        "comparisons": list(PROXY_COMPARISONS),
        "candidate_proxy": SEARCH_POLICY,
        "max_move_seconds": MAX_MOVE_SECONDS,
        "seed_range": [min(row["match_seed"] for row in schedule),
                       max(row["match_seed"] for row in schedule)],
    }
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(header, sort_keys=True, allow_nan=False) + "\n")
            for row in schedule:
                block_started = time.perf_counter()
                block_cpu = time.process_time()
                result = play_paired_block(row)
                if not verify_block(row, result):
                    raise RuntimeError("paired match replay failed; study version invalid")
                result["block_wall_seconds"] = time.perf_counter() - block_started
                result["block_cpu_seconds"] = time.process_time() - block_cpu
                result["record_type"] = "outcome"
                stream.write(json.dumps(result, sort_keys=True, allow_nan=False) + "\n")
                completed += 1
                summary_values.setdefault((row["game"], row["comparison"]), []).append(
                    result["paired_score_d"])
                if completed % 100 == 0:
                    stream.flush()
        elapsed = time.perf_counter() - started
        cpu_elapsed = time.process_time() - cpu_started
        temporary.replace(output_path)
    except BaseException:
        if temporary.exists():
            temporary.replace(partial)
        raise

    artifact_hash = hashlib.sha256()
    with output_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            artifact_hash.update(chunk)
    artifact_bytes = output_path.stat().st_size
    summary = []
    for (game_name, comparison), values in sorted(summary_values.items()):
        summary.append({
            "game": game_name,
            "comparison": comparison,
            "blocks": len(values),
            "mean_paired_score_d": statistics.fmean(values),
            "sample_sd_paired_score_d": statistics.stdev(values) if len(values) > 1 else None,
            "positive_blocks": sum(value > 0 for value in values),
            "zero_blocks": sum(value == 0 for value in values),
            "negative_blocks": sum(value < 0 for value in values),
        })
    receipt = {
        "schema": f"{PROTOCOL}-receipt",
        "status": header["status"],
        "block_count": completed,
        "wall_seconds": elapsed,
        "cpu_seconds": cpu_elapsed,
        "source_sha256": source_sha,
        "schedule_sha256": schedule_sha,
        "artifact": {"path": str(output_path), "bytes": artifact_bytes,
                     "sha256": artifact_hash.hexdigest()},
        "descriptive_proxy_summary": summary,
        "interpretation": "Proxy-policy rules, replay, runtime and variance diagnostic only; not a learned-model result, treatment effect, or primary V08 power estimate.",
    }
    receipt_tmp = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
    receipt_tmp.write_text(json.dumps(receipt, sort_keys=True, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")
    receipt_tmp.replace(receipt_path)
    return {"schema": PROTOCOL, "status": header["status"],
            "block_count": completed, "wall_seconds": elapsed,
            "cpu_seconds": cpu_elapsed, "source_sha256": source_sha,
            "schedule_sha256": schedule_sha, "artifact_sha256": artifact_hash.hexdigest(),
            "artifact_bytes": artifact_bytes, "receipt_path": str(receipt_path),
            "summary": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--blocks", type=int, default=12)
    args = parser.parse_args()
    result = run_pilot(args.output, blocks=args.blocks)
    print(json.dumps({"protocol": PROTOCOL,
                      "status": result["status"],
                      "block_count": result["block_count"],
                      "wall_seconds": result["wall_seconds"],
                      "cpu_seconds": result["cpu_seconds"],
                      "artifact_bytes": result["artifact_bytes"],
                      "source_sha256": result["source_sha256"],
                      "receipt_path": result["receipt_path"],
                      "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
