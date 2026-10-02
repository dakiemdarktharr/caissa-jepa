"""Paired complete-game development evaluator for the V2.9 fit panel.

The result is a measurement of these particular fitted checkpoints under the
frozen two-ply minimax planner; it is not evidence of equilibrium or opponent
behavior prediction. Do not run against the locked schedule before the V02
artifact freeze and independent prefit gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from two_player.games import BoardGame
from two_player.v28_model import Config, METHOD_VERSION, Model, _model_code_sha256
from two_player.v29_development import (EXPECTED_DATA, EXPECTED_MODEL_CONFIG,
                                        EXPECTED_RUN_CONFIG, development_schedule)
from tools.v28_match_power import (CHECKPOINT_SEEDS, COMPARISONS, GAMES,
                                   make_schedule)
from two_player import v28_train

PROTOCOL = "v29-three-epoch-development-match-v01"
MAX_MOVE_SECONDS = 2.0
MAX_NODES_PER_MOVE = 500_000
TIE_SEED_OFFSET = 80_928
LOCKED_BUDGET = {"max_move_seconds": MAX_MOVE_SECONDS,
                 "max_nodes_per_move": MAX_NODES_PER_MOVE}


def _json_sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_locked_schedule(commitment_path):
    """Resolve the committed wrapper to its ignored, locally frozen schedule."""
    commitment_path = Path(commitment_path)
    wrapper = json.loads(commitment_path.read_text(encoding="utf-8"))
    artifact = wrapper.get("artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
        raise ValueError("commitment wrapper lacks a schedule artifact reference")
    schedule_path = (ROOT / artifact["path"]).resolve()
    if ROOT.resolve() not in schedule_path.parents:
        raise ValueError("committed schedule artifact escapes the repository")
    raw_bytes = schedule_path.read_bytes()
    if (len(raw_bytes) != artifact.get("bytes")
            or hashlib.sha256(raw_bytes).hexdigest() != artifact.get("sha256")):
        raise ValueError("local locked schedule differs from committed artifact fingerprint")
    schedule_data = json.loads(raw_bytes)
    manifest = schedule_data.get("manifest", {})
    rows = schedule_data.get("blocks")
    commitment = wrapper.get("commitment", {})
    schedule_code_sha = _sha_file(ROOT / "tools" / "v28_match_power.py")
    learned_protocol = wrapper.get("learned_match_protocol", {})
    if (learned_protocol.get("protocol") != PROTOCOL
            or learned_protocol.get("budget") != LOCKED_BUDGET
            or not isinstance(rows, list) or rows != make_schedule()
            or manifest != commitment
            or manifest.get("blocks_sha256") != _json_sha(rows)
            or manifest.get("schedule_code_sha256") != schedule_code_sha
            or wrapper.get("analysis_code_sha256") != _sha_file(
                ROOT / "tools" / "v28_match_analysis.py")):
        raise ValueError("locked schedule differs from the committed design/code")
    return schedule_data, rows, hashlib.sha256(raw_bytes).hexdigest()


class _MeteredGame:
    """Count exact game transitions requested by the common planner."""
    def __init__(self, game):
        self._game = game
        self.transitions = 0

    def __getattr__(self, name):
        value = getattr(self._game, name)
        if name != "transition":
            return value

        def counted_transition(state, action):
            self.transitions += 1
            return value(state, action)
        return counted_transition


def load_model_policy(checkpoint_path, receipt_path):
    """Load a checkpoint only when its durable trainer receipt matches bytes."""
    checkpoint_path, receipt_path = Path(checkpoint_path), Path(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "caissa-jepa-v28-train-receipt-v1":
        raise ValueError("unsupported or missing training receipt")
    if receipt.get("method") != METHOD_VERSION or receipt.get("evaluation") is not None:
        raise ValueError("receipt method/evaluation state is not eligible for matching")
    if receipt.get("checkpoint_sha256") != _sha_file(checkpoint_path):
        raise ValueError("checkpoint bytes do not match the training receipt")
    effective = receipt.get("effective_run")
    if not isinstance(effective, dict) or effective.get("method") != METHOD_VERSION:
        raise ValueError("receipt lacks the effective V2.8 run identity")
    if _json_sha(effective) != receipt.get("run_config_sha256"):
        raise ValueError("receipt effective run does not match its run-configuration hash")
    if effective.get("dataset_fingerprint") != receipt.get("dataset_fingerprint"):
        raise ValueError("receipt effective run dataset fingerprint mismatch")
    if receipt.get("fit_scope") != effective.get("fit_scope"):
        raise ValueError("receipt fit scope does not match effective run identity")
    if (effective.get("fit_scope") == "development-only"
            and receipt.get("development_approval_sha256") !=
            effective.get("development_approval_sha256")):
        raise ValueError("development receipt approval hash mismatch")
    if effective.get("fit_scope") == "development-only":
        approval_path = effective.get("development_approval_path")
        if (not isinstance(approval_path, str) or not Path(approval_path).is_file()
                or _sha_file(approval_path) != effective.get(
                    "development_approval_sha256")):
            raise ValueError("development approval artifact is missing or changed")
        approval = json.loads(Path(approval_path).read_text(encoding="utf-8"))
        data_identity = approval.get("dataset", {})
        from two_player import v29_development as development
        approval_code_current = (
            approval.get("schema") == development.APPROVAL_SCHEMA
            and approval.get("protocol") == development.PROTOCOL
            and approval.get("scope") == "development-only"
            and approval.get("training_approved_manifest") is False
            and approval.get("loader_sha256") == development._sha256_source(
                Path(development.__file__))
            and approval.get("amendment_sha256") == development._sha256_source(
                development.AMENDMENT)
            and approval.get("panel_spec_sha256") == development._sha256_source(
                development.PANEL_SPEC))
        if not approval_code_current:
            raise ValueError("development approval is stale for current review artifacts")
        if data_identity != development.EXPECTED_DATA:
            raise ValueError("development approval is not bound to pinned DEV09 data")
        if (data_identity.get("records_sha256") != receipt.get("dataset_sha256")
                or data_identity.get("audit_sha256") != receipt.get("audit_sha256")
                or data_identity.get("dataset_fingerprint") !=
                receipt.get("dataset_fingerprint")):
            raise ValueError("development approval does not authorize receipt data")
    trainer_sha = hashlib.sha256(
        Path(v28_train.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if (receipt.get("model_code_sha256") != _model_code_sha256()
            or receipt.get("trainer_code_sha256") != trainer_sha):
        raise ValueError("receipt model/trainer source identity mismatch")
    model_config = Config(**effective["model"])
    if model_config.variant != receipt.get("variant"):
        raise ValueError("receipt model variant/config mismatch")
    identity = {"dataset_sha256": receipt["dataset_sha256"],
                "audit_sha256": receipt["audit_sha256"],
                "run_config_sha256": receipt["run_config_sha256"],
                "split": receipt["split"]}
    model = Model.load(checkpoint_path, model_config, identity)
    if model.step != receipt.get("optimizer_step"):
        raise ValueError("receipt optimizer step does not match checkpoint")
    if model.training_state["completed_epochs"] != receipt.get("completed_epochs"):
        raise ValueError("receipt epoch count does not match checkpoint")
    model._checkpoint_path = str(checkpoint_path)
    model._training_receipt_path = str(receipt_path)
    model._training_receipt = receipt
    return model


def _state_hash(state):
    return _json_sha({"board": list(state.board), "player": state.player})


def _play_game(game, plus_policy, minus_policy, *, checkpoint_seed, match_seed,
               max_move_seconds=MAX_MOVE_SECONDS,
               max_nodes=MAX_NODES_PER_MOVE):
    state = game.initial()
    transcript = []
    counts = {"plus": {"transitions": 0, "decision_calls": 0,
                        "branch_value_calls": 0, "latent_evaluations": 0,
                        "wall_seconds": 0.0, "cpu_seconds": 0.0},
              "minus": {"transitions": 0, "decision_calls": 0,
                         "branch_value_calls": 0, "latent_evaluations": 0,
                         "wall_seconds": 0.0, "cpu_seconds": 0.0}}
    while game.terminal(state) is None:
        role = "plus" if state.player == 1 else "minus"
        policy = plus_policy if role == "plus" else minus_policy
        before_hash = _state_hash(state)
        legal = tuple(game.legal_actions(state))
        if not legal:
            raise RuntimeError("nonterminal game state has no legal actions")
        metered = _MeteredGame(game)
        branch_counts = {"calls": 0, "latent": 0}
        original_branch_value = getattr(policy, "branch_value", None)
        if original_branch_value is not None:
            def counted_branch_value(*args, **kwargs):
                branch_counts["calls"] += 1
                if game.terminal(args[-1]) is None:
                    branch_counts["latent"] += 1
                return original_branch_value(*args, **kwargs)
            policy.branch_value = counted_branch_value
        wall_start, cpu_start = time.perf_counter(), time.process_time()
        try:
            action, values = policy.plan_action(metered, state)
        finally:
            if original_branch_value is not None:
                policy.branch_value = original_branch_value
        if type(action) is int and action in legal:
            if (not isinstance(values, dict) or set(values) != set(legal)
                    or any(not isinstance(value, (int, float)) or not math.isfinite(value)
                           for value in values.values())):
                raise ValueError("planner action-value map is malformed")
            best_value = max(values.values())
            tied_actions = sorted(candidate for candidate, value in values.items()
                                  if value == best_value)
            tie_rng = np.random.default_rng(np.random.SeedSequence(
                [checkpoint_seed, match_seed, TIE_SEED_OFFSET, len(transcript)]))
            action = int(tie_rng.choice(tied_actions))
        wall, cpu = time.perf_counter() - wall_start, time.process_time() - cpu_start
        counts[role]["decision_calls"] += 1
        counts[role]["transitions"] += metered.transitions
        counts[role]["branch_value_calls"] += branch_counts["calls"]
        counts[role]["latent_evaluations"] += branch_counts["latent"]
        counts[role]["wall_seconds"] += wall
        counts[role]["cpu_seconds"] += cpu
        if (wall > max_move_seconds or metered.transitions > max_nodes):
            return {"status": "model_forfeit",
                    "score_plus": 0.0 if role == "plus" else 1.0,
                    "forfeit_role": role,
                    "forfeit_reason": "move wall-time or transition-node budget exceeded",
                    "forfeit_details": {"wall_seconds": wall,
                                         "cpu_seconds": cpu,
                                         "wall_limit_seconds": max_move_seconds,
                                         "transitions": metered.transitions,
                                         "node_limit": max_nodes,
                                         "state_sha256": before_hash},
                    "transcript": transcript, "compute": counts,
                    "terminal_utility_plus": None}
        if type(action) is not int or action not in legal:
            return {"status": "model_forfeit",
                    "score_plus": 0.0 if role == "plus" else 1.0,
                    "forfeit_role": role,
                    "forfeit_reason": "illegal action",
                    "forfeit_details": {"action": action if type(action) is int else None,
                                         "returned_action_type": type(action).__name__,
                                         "legal_actions": list(legal),
                                         "wall_seconds": wall,
                                         "cpu_seconds": cpu,
                                         "transitions": metered.transitions,
                                         "state_sha256": before_hash},
                    "transcript": transcript, "compute": counts,
                    "terminal_utility_plus": None}
        after = game.transition(state, action)
        transcript.append({"ply": len(transcript), "player": state.player,
                           "state_sha256": before_hash, "legal_actions": list(legal),
                           "action": action, "action_value": float(values[action]),
                           "next_state_sha256": _state_hash(after),
                           "planner_transitions": metered.transitions,
                           "decision_wall_seconds": wall,
                           "decision_cpu_seconds": cpu})
        state = after
    utility = game.terminal(state)
    return {"status": "complete", "score_plus": (utility + 1) / 2,
            "forfeit_role": None, "forfeit_reason": None,
            "forfeit_details": None, "transcript": transcript,
            "compute": counts, "terminal_utility_plus": utility,
            "terminal_state_sha256": _state_hash(state)}


def _verify_game(game, record, *, max_move_seconds=MAX_MOVE_SECONDS,
                 max_nodes=MAX_NODES_PER_MOVE):
    if record.get("status") not in ("complete", "model_forfeit"):
        return False
    state = game.initial()
    measured = {1: {"transitions": 0, "decision_calls": 0,
                    "wall_seconds": 0.0, "cpu_seconds": 0.0},
                -1: {"transitions": 0, "decision_calls": 0,
                     "wall_seconds": 0.0, "cpu_seconds": 0.0}}
    for expected_ply, move in enumerate(record.get("transcript", [])):
        legal = tuple(game.legal_actions(state))
        wall = move.get("decision_wall_seconds")
        cpu = move.get("decision_cpu_seconds")
        transitions = move.get("planner_transitions")
        if (move.get("ply") != expected_ply or move.get("player") != state.player
                or move.get("state_sha256") != _state_hash(state)
                or move.get("legal_actions") != list(legal)
                or type(move.get("action")) is not int or move["action"] not in legal
                or not isinstance(move.get("action_value"), (int, float))
                or not math.isfinite(move["action_value"])
                or not isinstance(wall, (int, float)) or not math.isfinite(wall)
                or wall < 0 or wall > max_move_seconds
                or not isinstance(cpu, (int, float)) or not math.isfinite(cpu) or cpu < 0
                or type(transitions) is not int or not (0 <= transitions <= max_nodes)):
            return False
        role = measured[state.player]
        role["transitions"] += transitions
        role["decision_calls"] += 1
        role["wall_seconds"] += wall
        role["cpu_seconds"] += cpu
        state = game.transition(state, move["action"])
        if move.get("next_state_sha256") != _state_hash(state):
            return False
    if record["status"] == "model_forfeit":
        details = record.get("forfeit_details")
        if not isinstance(details, dict):
            return False
        expected_role = "plus" if state.player == 1 else "minus"
        wall, cpu = details.get("wall_seconds"), details.get("cpu_seconds")
        transitions = details.get("transitions")
        if (record.get("forfeit_role") != expected_role
                or game.terminal(state) is not None
                or details.get("state_sha256") != _state_hash(state)
                or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall < 0
                or not isinstance(cpu, (int, float)) or not math.isfinite(cpu) or cpu < 0
                or type(transitions) is not int or transitions < 0):
            return False
        failed = measured[state.player]
        failed["transitions"] += transitions
        failed["decision_calls"] += 1
        failed["wall_seconds"] += wall
        failed["cpu_seconds"] += cpu
    compute = record.get("compute")
    if not isinstance(compute, dict):
        return False
    for player, name in ((1, "plus"), (-1, "minus")):
        actual = compute.get(name)
        expected = measured[player]
        if not isinstance(actual, dict):
            return False
        if any(actual.get(key) != value for key, value in expected.items()
               if key not in ("wall_seconds", "cpu_seconds")):
            return False
        for key in ("branch_value_calls", "latent_evaluations"):
            if type(actual.get(key)) is not int or actual[key] < 0:
                return False
        for key in ("wall_seconds", "cpu_seconds"):
            value = actual.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                return False
            if value + 1e-9 < expected[key]:
                return False
    if record["status"] == "model_forfeit":
        details = record.get("forfeit_details")
        role = "plus" if state.player == 1 else "minus"
        if (not isinstance(details, dict) or record.get("forfeit_role") != role
                or game.terminal(state) is not None
                or details.get("state_sha256") != _state_hash(state)):
            return False
        if record.get("forfeit_reason") == "illegal action":
            legal = tuple(game.legal_actions(state))
            action = details.get("action")
            if (details.get("legal_actions") != list(legal)
                    or (type(action) is int and action in legal)
                    or (action is None and details.get("returned_action_type") == "int")):
                return False
        elif record.get("forfeit_reason") == "move wall-time or transition-node budget exceeded":
            wall = details.get("wall_seconds")
            transitions = details.get("transitions")
            if (not isinstance(wall, (int, float)) or not math.isfinite(wall)
                    or type(transitions) is not int
                    or details.get("wall_limit_seconds") != max_move_seconds
                    or details.get("node_limit") != max_nodes
                    or not (wall > max_move_seconds or transitions > max_nodes)):
                return False
        else:
            return False
        expected_score = 0.0 if role == "plus" else 1.0
        current_player = 1 if role == "plus" else -1
        counts = compute[role]
        expected_calls = measured[current_player]["decision_calls"]
        if counts["decision_calls"] != expected_calls:
            return False
        decision_wall, decision_cpu = details.get("wall_seconds"), details.get("cpu_seconds")
        decision_transitions = details.get("transitions")
        if (not isinstance(decision_wall, (int, float)) or not math.isfinite(decision_wall)
                or decision_wall < 0
                or not isinstance(decision_cpu, (int, float))
                or not math.isfinite(decision_cpu) or decision_cpu < 0
                or type(decision_transitions) is not int or decision_transitions < 0
                or decision_wall != details["wall_seconds"]
                or decision_cpu != details["cpu_seconds"]
                or decision_transitions != details["transitions"]
                or counts["transitions"] != measured[current_player]["transitions"]
                or counts["wall_seconds"] + 1e-9 < measured[current_player]["wall_seconds"]
                or counts["cpu_seconds"] + 1e-9 < measured[current_player]["cpu_seconds"]):
            return False
        return record.get("score_plus") == expected_score
    utility = game.terminal(state)
    if utility is None or utility != record.get("terminal_utility_plus"):
        return False
    return (record.get("terminal_state_sha256") == _state_hash(state)
            and record.get("score_plus") == (utility + 1) / 2)


def play_paired_block(schedule_row, jepa, control, *, max_move_seconds=MAX_MOVE_SECONDS,
                      max_nodes=MAX_NODES_PER_MOVE):
    comparison = schedule_row["comparison"]
    control_variant = {"task-value-dynamics": "task-value-dynamics",
                       "direct-exact-leaf-value": "direct-leaf"}.get(comparison)
    if control_variant is None or control.config.variant != control_variant:
        raise ValueError("control checkpoint does not match committed comparison")
    if jepa.config.variant != "reply-jepa":
        raise ValueError("candidate checkpoint is not reply-set JEPA")
    game = {"connect4-gravity-6x7": BoardGame("connect4-gravity-6x7", 6, 7, 4, True),
            "reversi6": BoardGame("reversi6", 6, 6, reversi=True)}.get(
                schedule_row["game"])
    if game is None:
        raise ValueError("game is outside the frozen V2.8 schedule")
    seed = schedule_row["match_seed"]
    checkpoint_seed = schedule_row["checkpoint_seed"]
    plus_game = _play_game(game, jepa, control, checkpoint_seed=checkpoint_seed,
                           match_seed=seed, max_move_seconds=max_move_seconds,
                           max_nodes=max_nodes)
    minus_game = _play_game(game, control, jepa, checkpoint_seed=checkpoint_seed,
                            match_seed=seed, max_move_seconds=max_move_seconds,
                            max_nodes=max_nodes)
    for record in (plus_game, minus_game):
        if not _verify_game(game, record, max_move_seconds=max_move_seconds,
                            max_nodes=max_nodes):
            raise RuntimeError("match transcript failed independent rules replay")
    score_plus = plus_game["score_plus"]
    score_minus = 1.0 - minus_game["score_plus"]
    status = ("model_forfeit" if "model_forfeit" in
              (plus_game["status"], minus_game["status"]) else "complete")
    return {**{key: schedule_row[key] for key in
                ("block_id", "game", "comparison", "checkpoint_seed", "match_seed")},
            "status": status, "external_censored": False,
            "score_plus": score_plus, "score_minus": score_minus,
            "paired_score_d": (score_plus + score_minus) / 2 - 0.5,
            "plus_assignment": {"jepa_player": 1, "jepa": plus_game,
                                "control": control_variant},
            "minus_assignment": {"jepa_player": -1, "jepa": minus_game,
                                 "control": control_variant},
            "max_move_seconds": max_move_seconds, "max_nodes_per_move": max_nodes}


def run_schedule(schedule, policy_panels, output_path, *, max_move_seconds=MAX_MOVE_SECONDS,
                 max_nodes=MAX_NODES_PER_MOVE, confirmatory=False,
                 commitment_sha256=None, development_panel_root=None):
    """Run a supplied complete schedule; publish only a full atomic output."""
    if confirmatory:
        raise ValueError("V2.9 evaluator is development-only and blocks locked V08")
    _validate_schedule(schedule)
    if (not math.isfinite(max_move_seconds) or max_move_seconds <= 0
            or type(max_nodes) is not int or max_nodes < 1):
        raise ValueError("invalid per-move inference budget")
    if type(confirmatory) is not bool:
        raise ValueError("confirmatory must be a boolean")
    if not confirmatory and schedule != development_schedule():
        raise ValueError("development mode requires the exact hash-pinned exploratory schedule")
    if not confirmatory and development_panel_root is None:
        raise ValueError("development match requires its completed fit-panel ledger")
    if confirmatory and (not isinstance(commitment_sha256, str)
                         or len(commitment_sha256) != 64
                         or any(character not in "0123456789abcdef" for character in
                                commitment_sha256)):
        raise ValueError("confirmatory mode requires the frozen commitment file hash")
    if confirmatory and (max_move_seconds != LOCKED_BUDGET["max_move_seconds"]
                         or max_nodes != LOCKED_BUDGET["max_nodes_per_move"]):
        raise ValueError("confirmatory inference budget differs from frozen protocol")
    if not confirmatory and (max_move_seconds != LOCKED_BUDGET["max_move_seconds"]
                             or max_nodes != LOCKED_BUDGET["max_nodes_per_move"]):
        raise ValueError("development inference budget differs from frozen protocol")
    _validate_panels(policy_panels)
    fit_scopes = {model._training_receipt.get("fit_scope")
                  for panel in policy_panels.values() for model in panel.values()}
    expected_scope = "approved-training" if confirmatory else "development-only"
    if fit_scopes != {expected_scope}:
        raise ValueError(f"{expected_scope} checkpoints are required for this schedule mode")
    if not confirmatory:
        _validate_completed_development_ledger(development_panel_root, policy_panels)
    panel_ledger_path = Path(development_panel_root).resolve() / "panel.json"
    panel_ledger_sha256 = _sha_file(panel_ledger_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    partial = output_path.with_suffix(output_path.suffix + ".partial.jsonl")
    receipt_path = output_path.with_suffix(output_path.suffix + ".receipt.json")
    if (output_path.exists() or temporary.exists() or partial.exists()
            or receipt_path.exists()):
        raise FileExistsError("refusing to overwrite a previous match artifact")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    completed = 0
    forfeit_rows = 0
    header = {"schema": PROTOCOL, "record_type": "manifest",
                  "method": METHOD_VERSION, "block_count": len(schedule),
                  "schedule_sha256": _json_sha(schedule),
                  "max_move_seconds": max_move_seconds,
                  "max_nodes_per_move": max_nodes,
                  "outcomes_are_locked": confirmatory,
                  "commitment_sha256": commitment_sha256,
                  "interpretation": "paired checkpoint-panel score versus two same-search controls"}
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(header, sort_keys=True, allow_nan=False) + "\n")
            for block in schedule:
                seed = block["checkpoint_seed"]
                panel = policy_panels[seed]
                jepa = panel["reply-jepa"]
                control_name = {"task-value-dynamics": "task-value-dynamics",
                                "direct-exact-leaf-value": "direct-leaf"}[block["comparison"]]
                result = play_paired_block(block, jepa, panel[control_name],
                                           max_move_seconds=max_move_seconds,
                                           max_nodes=max_nodes)
                stream.write(json.dumps(result, sort_keys=True, allow_nan=False) + "\n")
                forfeit_rows += result["status"] == "model_forfeit"
                completed += 1
                if completed % 10 == 0:
                    stream.flush()
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if temporary.exists():
            temporary.replace(partial)
        raise
    temporary.replace(output_path)
    artifact_sha = _sha_file(output_path)
    receipt = {"schema": f"{PROTOCOL}-receipt", "status": "complete",
               "block_count": completed,
               "wall_seconds": time.perf_counter() - started_wall,
               "cpu_seconds": time.process_time() - started_cpu,
               "schedule_sha256": _json_sha(schedule),
               "artifact_sha256": artifact_sha,
               "artifact_bytes": output_path.stat().st_size,
               "max_move_seconds": max_move_seconds,
               "max_nodes_per_move": max_nodes,
               "confirmatory": confirmatory,
               "commitment_sha256": commitment_sha256,
               "model_match_source_sha256": _sha_file(__file__),
               "panel_ledger_sha256": panel_ledger_sha256,
               "panel_checkpoint_sha256": {
                   str(seed): {variant: _sha_file(
                       policy_panels[seed][variant]._checkpoint_path)
                       for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf")}
                   for seed in CHECKPOINT_SEEDS},
               "panel_training_receipt_sha256": {
                   str(seed): {variant: _sha_file(
                       policy_panels[seed][variant]._training_receipt_path)
                       for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf")}
                   for seed in CHECKPOINT_SEEDS},
               "panel_run_identity": {
                   str(seed): {variant: {
                       "dataset_fingerprint": policy_panels[seed][variant]._training_receipt[
                           "dataset_fingerprint"],
                       "dataset_sha256": policy_panels[seed][variant]._training_receipt[
                           "dataset_sha256"],
                       "audit_sha256": policy_panels[seed][variant]._training_receipt[
                           "audit_sha256"],
                       "run_config_sha256": policy_panels[seed][variant]._training_receipt[
                           "run_config_sha256"],
                       "model_code_sha256": policy_panels[seed][variant]._training_receipt[
                           "model_code_sha256"],
                       "trainer_code_sha256": policy_panels[seed][variant]._training_receipt[
                           "trainer_code_sha256"],
                       "optimizer_step": policy_panels[seed][variant].step,
                       "completed_epochs": policy_panels[seed][variant].training_state[
                           "completed_epochs"]}
                       for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf")}
                   for seed in CHECKPOINT_SEEDS},
               "external_censored_block_rows": 0,
               "model_forfeit_rows": forfeit_rows,
               "interpretation": "learned checkpoint-panel match results; not equilibrium/exploitability"}
    receipt_path = output_path.with_suffix(output_path.suffix + ".receipt.json")
    fd, receipt_tmp = tempfile.mkstemp(prefix=receipt_path.name + ".", suffix=".tmp",
                                       dir=output_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2,
                                    allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(receipt_tmp, receipt_path)
    finally:
        if os.path.exists(receipt_tmp):
            os.unlink(receipt_tmp)
    return receipt


def _panel_from_root(root):
    panels = {}
    for seed in CHECKPOINT_SEEDS:
        panels[seed] = {}
        for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf"):
            base = Path(root) / str(seed) / variant
            checkpoint = base / "checkpoint.npz"
            receipt = base / "checkpoint.npz.receipt.json"
            model = load_model_policy(checkpoint, receipt)
            if (model.config.seed != seed or model.config.variant != variant
                    or model.training_state["completed_epochs"] < 1):
                raise ValueError("panel checkpoint seed/variant/training-state mismatch")
            panels[seed][variant] = model
    _validate_panels(panels)
    return panels


def _sha_source(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _validate_completed_development_ledger(root, panels):
    """Require the immutable panel receipt before development matches begin."""
    from two_player.v29_development import (PANEL_SPEC, validate_development_spec)

    root = Path(root).resolve()
    ledger_path = root / "panel.json"
    if not ledger_path.is_file():
        raise ValueError("development match requires a completed panel.json ledger")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    spec = validate_development_spec()
    requirements_lock = ROOT / "requirements-research-lock.txt"
    approval_path = Path(ledger.get("approval_path", "")).resolve()
    expected_runs = {(seed, variant) for seed in CHECKPOINT_SEEDS
                     for variant in ("reply-jepa", "task-value-dynamics", "direct-leaf")}
    rows = ledger.get("runs")
    if (ledger.get("schema") != "caissa-jepa-v29-development-fit-panel-result-v01"
            or ledger.get("status") != "completed"
            or ledger.get("expected_runs") != len(expected_runs)
            or not isinstance(rows, list) or len(rows) != len(expected_runs)
            or ledger.get("method") != METHOD_VERSION
            or ledger.get("panel_spec_sha256") != _sha_source(PANEL_SPEC)
            or ledger.get("dataset_manifest_sha256") != EXPECTED_DATA["manifest_sha256"]
            or ledger.get("dataset_fingerprint") != EXPECTED_DATA["dataset_fingerprint"]
            or ledger.get("records_sha256") != EXPECTED_DATA["records_sha256"]
            or ledger.get("audit_sha256") != EXPECTED_DATA["audit_sha256"]
            or ledger.get("model_code_sha256") != _sha_source(
                ROOT / "two_player" / "v28_model.py")
            or ledger.get("trainer_code_sha256") != _sha_source(
                ROOT / "two_player" / "v28_train.py")
            or ledger.get("panel_runner_code_sha256") != _sha_source(
                ROOT / "tools" / "v29_run_development_panel.py")
            or ledger.get("panel_supervisor_code_sha256") != _sha_source(
                ROOT / "tools" / "v29_development_panel_supervisor.py")
            or ledger.get("data_audit_code_sha256") != _sha_source(
                ROOT / "two_player" / "v28_data.py")
            or not requirements_lock.is_file()
            or ledger.get("requirements_lock_sha256") != _sha_source(requirements_lock)
            or not approval_path.is_file()
            or _sha_file(approval_path) != ledger.get("approval_sha256")):
        raise ValueError("development fit ledger is incomplete or stale")
    seen = set()
    approval_sha = ledger.get("approval_sha256")
    if (not isinstance(approval_sha, str) or len(approval_sha) != 64
            or ledger.get("allowed_training_split") != "train"
            or ledger.get("locked_final_access") is not False):
        raise ValueError("development fit ledger scope/approval is invalid")
    for row in rows:
        key = (row.get("seed"), row.get("variant"))
        if key not in expected_runs or key in seen or row.get("status") != "completed":
            raise ValueError("development fit ledger run inventory is invalid")
        seen.add(key)
        model = panels[key[0]][key[1]]
        checkpoint = (root / str(key[0]) / key[1] / "checkpoint.npz").resolve()
        receipt_path = checkpoint.with_suffix(checkpoint.suffix + ".receipt.json")
        model_checkpoint = Path(getattr(model, "_checkpoint_path", "")).resolve()
        model_receipt = Path(getattr(model, "_training_receipt_path", "")).resolve()
        if (model_checkpoint != checkpoint or model_receipt != receipt_path
                or _sha_file(model_checkpoint) != row.get("checkpoint_sha256")
                or _sha_file(model_receipt) != row.get("receipt_sha256")
                or Path(row.get("checkpoint", "")).resolve() != checkpoint
                or Path(row.get("receipt", "")).resolve() != receipt_path
                or row.get("checkpoint_sha256") != _sha_file(checkpoint)
                or row.get("receipt_sha256") != _sha_file(receipt_path)
                or row.get("completed_epochs") != EXPECTED_RUN_CONFIG["epochs"]
                or row.get("optimizer_step") != model.step
                or model._training_receipt.get("development_approval_sha256") != approval_sha
                or model._training_receipt.get("dataset_fingerprint") !=
                EXPECTED_DATA["dataset_fingerprint"]):
            raise ValueError("development fit ledger row differs from checkpoint receipt")
        history_resources = [
            {key: epoch[key] for key in (
                "epoch_index", "updates", "wall_seconds", "cpu_seconds",
                "order_sha256")}
            for epoch in model._training_receipt.get("history", [])]
        if (len(history_resources) != EXPECTED_RUN_CONFIG["epochs"]
                or row.get("training_epoch_resources") != history_resources):
            raise ValueError("panel epoch resources differ from hashed training receipt")
    if seen != expected_runs:
        raise ValueError("development fit ledger omits planned checkpoints")
    return ledger


def _validate_schedule(schedule):
    if not isinstance(schedule, (list, tuple)) or not schedule:
        raise ValueError("match schedule must be a nonempty list")
    identifiers = set()
    cells = {}
    for row in schedule:
        if not isinstance(row, dict):
            raise ValueError("malformed match schedule row")
        block = dict(row)
        block_id = block.pop("block_id", None)
        if block_id != _json_sha(block) or block_id in identifiers:
            raise ValueError("schedule row hash is invalid or duplicated")
        identifiers.add(block_id)
        key = (row.get("game"), row.get("comparison"), row.get("checkpoint_seed"))
        if (key[0] not in GAMES or key[1] not in COMPARISONS
                or key[2] not in CHECKPOINT_SEEDS):
            raise ValueError("schedule row is outside the frozen V2.8 design")
        if (row.get("start") != "adapter_initial_state"
                or row.get("color_assignments") != [1, -1]):
            raise ValueError("schedule start/color assignment differs from protocol")
        match_seed = row.get("match_seed")
        if type(match_seed) is not int:
            raise ValueError("match seed must be an integer")
        cells.setdefault(key, set()).add(match_seed)
    seeds = {row["checkpoint_seed"] for row in schedule}
    expected_cells = len(GAMES) * len(COMPARISONS) * len(seeds)
    if len(seeds) != len(CHECKPOINT_SEEDS) or len(cells) != expected_cells:
        raise ValueError("schedule is missing a game/control/checkpoint cell")
    cell_match_counts = {len(matches) for matches in cells.values()}
    if len(cell_match_counts) != 1:
        raise ValueError("schedule does not contain balanced paired match seeds")
    for seed in seeds:
        match_sets = {tuple(sorted(cells[(game, comparison, seed)]))
                      for game in GAMES for comparison in COMPARISONS}
        if len(match_sets) != 1:
            raise ValueError("paired game/control cells do not share match seeds")


def _validate_panels(policy_panels):
    if set(policy_panels) != set(CHECKPOINT_SEEDS):
        raise ValueError("checkpoint panel must contain exactly the frozen seed list")
    variants = {"reply-jepa", "task-value-dynamics", "direct-leaf"}
    global_config = None
    global_epochs = None
    global_step = None
    global_run = None
    global_data = None
    development_approval_sha = None
    development_config = {
        **EXPECTED_MODEL_CONFIG,
    }
    for seed, panel in policy_panels.items():
        if set(panel) != variants:
            raise ValueError("each checkpoint needs all three matched model arms")
        models = list(panel.values())
        reference = models[0]
        base_config = {key: value for key, value in reference.config.__dict__.items()
                       if key not in ("variant", "seed")}
        reference_epochs = reference.training_state["completed_epochs"]
        reference_step = reference.step
        reference_receipt = getattr(reference, "_training_receipt", None)
        if reference_receipt is None or not getattr(reference, "_training_receipt_path", None):
            raise ValueError("production match requires each training receipt")
        effective_reference = {key: value for key, value in
                               reference_receipt["effective_run"].items()
                               if key != "model"}
        data_reference = tuple(reference_receipt[field] for field in
                               ("dataset_fingerprint", "dataset_sha256", "audit_sha256"))
        is_development = reference_receipt.get("fit_scope") == "development-only"
        if is_development:
            if (reference_epochs != EXPECTED_RUN_CONFIG["epochs"]
                    or data_reference != (EXPECTED_DATA["dataset_fingerprint"],
                                          EXPECTED_DATA["records_sha256"],
                                          EXPECTED_DATA["audit_sha256"])
                    or effective_reference.get("run") != EXPECTED_RUN_CONFIG
                    or base_config != development_config):
                raise ValueError("development checkpoint differs from the frozen fit panel")
            approval_sha = reference_receipt.get("development_approval_sha256")
            if (not isinstance(approval_sha, str) or len(approval_sha) != 64
                    or (development_approval_sha is not None
                        and approval_sha != development_approval_sha)):
                raise ValueError("development panel does not share one approval identity")
            development_approval_sha = approval_sha
        if global_config is None:
            global_config, global_epochs, global_step = base_config, reference_epochs, reference_step
            global_run, global_data = effective_reference, data_reference
        elif (base_config != global_config or reference_epochs != global_epochs
              or reference_step != global_step or effective_reference != global_run
              or data_reference != global_data):
            raise ValueError("checkpoint seed panel is not globally matched")
        for variant, model in panel.items():
            config = {key: value for key, value in model.config.__dict__.items()
                      if key not in ("variant", "seed")}
            receipt = getattr(model, "_training_receipt", None)
            if receipt is None or not getattr(model, "_training_receipt_path", None):
                raise ValueError("production match requires each training receipt")
            if (model.config.seed != seed or model.config.variant != variant
                    or config != base_config
                    or model.training_state["completed_epochs"] < 1
                    or model.training_state["completed_epochs"] != reference_epochs
                    or model.step != reference_step):
                raise ValueError("checkpoint panel is not matched on seed/config/training")
            if is_development and (
                    receipt.get("fit_scope") != "development-only"
                    or receipt.get("development_approval_sha256") !=
                    development_approval_sha
                    or receipt.get("dataset_fingerprint") != EXPECTED_DATA[
                        "dataset_fingerprint"]
                    or receipt.get("dataset_sha256") != EXPECTED_DATA["records_sha256"]
                    or receipt.get("audit_sha256") != EXPECTED_DATA["audit_sha256"]
                    or receipt.get("split") != "train"
                    or receipt.get("effective_run", {}).get("run") != EXPECTED_RUN_CONFIG
                    or {key: value for key, value in receipt.get(
                        "effective_run", {}).get("model", {}).items()
                        if key not in ("variant", "seed")} != development_config):
                raise ValueError("development arm differs from frozen scope/data/config")
            if reference_receipt is not None and receipt is not None:
                for field in ("dataset_fingerprint", "dataset_sha256", "audit_sha256",
                              "effective_run"):
                    left, right = reference_receipt[field], receipt[field]
                    if field == "effective_run":
                        left = {key: value for key, value in left.items()
                                if key != "model"}
                        right = {key: value for key, value in right.items()
                                 if key != "model"}
                    if left != right:
                        raise ValueError("checkpoint arms use different data/run identities")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--commitment", type=Path,
                        default=ROOT / "docs" / "validation" /
                        "V28_MATCH_SCHEDULE_V08_COMMITMENT.json")
    parser.add_argument("--development", action="store_true",
                        help="use a disjoint small seed schedule; never a locked confirmation")
    args = parser.parse_args()
    if not args.development:
        parser.error("V2.9 matcher is development-only; it cannot access locked V08")
    schedule = development_schedule()
    commitment_sha = None
    panels = _panel_from_root(args.runs_root)
    receipt = run_schedule(schedule, panels, args.output,
                           confirmatory=False,
                           commitment_sha256=commitment_sha,
                           development_panel_root=args.runs_root)
    print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
