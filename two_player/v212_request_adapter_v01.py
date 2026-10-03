"""Request-anchored V2.12 random-weight inference adapter (design v01).

This feasibility adapter is separate from the frozen v01/v02 pilot runners.
It accepts one synthetic legal root, returns one legal action in memory, and
records only compute counters. It has no dataset, optimizer, score, or receipt
writer. Production use requires an outer systemd scope with a verified finite
memory.max and ``memory.oom.group=0``; see ``verify_memory_scope``.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

from .games import BoardGame, State
from .v212_pilot import (
    ARMS,
    RSS_CAP_BYTES,
    Counters,
    PilotBudgetStop,
    RandomInferenceModel,
    Root,
    VARIANTS,
    _sample_rss_bytes,
    _state_sha256,
)

PILOT_VERSION = "v212-request-adapter-v01"
NODE_CAP = 10_000
PLANNER_SECONDS = 5.0
RESPONSE_SECONDS = 6.0
EXPECTED_MEMORY_MAX = int(1.5 * 1024**3)


def current_cgroup_info(proc_cgroup: Path = Path("/proc/self/cgroup"),
                        cgroup_root: Path = Path("/sys/fs/cgroup")) -> dict[str, Any]:
    """Read the unified cgroup's finite memory bound and event counters."""
    unified = None
    for line in proc_cgroup.read_text(encoding="utf-8").splitlines():
        hierarchy, controllers, relative = line.split(":", 2)
        if hierarchy == "0" and controllers == "":
            unified = relative
            break
    if unified is None or not unified.startswith("/"):
        raise RuntimeError("process is not in a readable cgroup-v2 hierarchy")
    root = cgroup_root.resolve()
    leaf = (root / unified.lstrip("/")).resolve()
    if leaf != root and root not in leaf.parents:
        raise RuntimeError("cgroup path escapes the cgroup-v2 mount")
    raw_limit = (leaf / "memory.max").read_text(encoding="ascii").strip()
    if raw_limit == "max" or not raw_limit.isdecimal():
        raise RuntimeError("cgroup memory.max is not finite")
    events = {}
    for line in (leaf / "memory.events").read_text(encoding="ascii").splitlines():
        key, value = line.split()
        events[key] = int(value)
    oom_group = (leaf / "memory.oom.group").read_text(encoding="ascii").strip()
    if oom_group not in {"0", "1"}:
        raise RuntimeError("cgroup memory.oom.group value is invalid")
    return {"path": unified, "memory_max": int(raw_limit),
            "memory_oom_group": int(oom_group), "events": events}


def verify_memory_scope(expected: int = EXPECTED_MEMORY_MAX,
                        proc_cgroup: Path = Path("/proc/self/cgroup"),
                        cgroup_root: Path = Path("/sys/fs/cgroup")) -> dict[str, Any]:
    info = current_cgroup_info(proc_cgroup, cgroup_root)
    if info["memory_max"] != expected:
        raise RuntimeError(
            f"memory.max={info['memory_max']} does not match required {expected}"
        )
    if info["memory_oom_group"] != 0:
        raise RuntimeError("memory.oom.group must be 0 so the supervisor survives")
    return info


def _search_action(game: BoardGame, root: Root, model: RandomInferenceModel,
                   request_started: float, planner_deadline: float,
                   node_cap: int, rss_cap_bytes: int,
                   setup_rss_bytes: int = 0) -> dict[str, Any]:
    """Four-ply minimax with request-anchored stop checks and action response."""
    if root.variant != game.name or game.terminal(root.state) is not None:
        raise ValueError("request root does not match game or is terminal")
    if _state_sha256(game, root.state) != root.state_sha256:
        raise ValueError("request root fingerprint mismatch")
    if type(node_cap) is not int or node_cap <= 0:
        raise ValueError("node cap must be a positive integer")
    if type(rss_cap_bytes) is not int or rss_cap_bytes <= 0:
        raise ValueError("RSS cap must be a positive integer")

    model.reset_calls()
    counters: Counters = model.calls
    counters.peak_sampled_rss_bytes = setup_rss_bytes
    root_player = root.state.player
    legal_root = tuple(game.legal_actions(root.state))
    if not legal_root:
        raise ValueError("nonterminal request root has no legal action")
    last_completed_action = legal_root[0]
    completed_depth = 0
    stop_reason = "depth_4_complete"

    def sample_memory() -> None:
        current = _sample_rss_bytes()
        counters.peak_sampled_rss_bytes = max(
            counters.peak_sampled_rss_bytes, current
        )
        if current > rss_cap_bytes:
            raise PilotBudgetStop("rss_cap")

    def check_budget() -> None:
        if counters.node_visits >= node_cap:
            raise PilotBudgetStop("node_cap")
        if time.monotonic() >= planner_deadline:
            raise PilotBudgetStop("wall_cap")

    try:
        sample_memory()
        check_budget()
        root_features = game.features(root.state)
        descriptor = root_features[192:198]
        root_latent = (
            None if model.arm == "direct-leaf-value"
            else model.encode(root_features)
        )
        check_budget()
    except PilotBudgetStop as stop:
        stop_reason = stop.reason
        root_latent = None
        descriptor = None

    def search(state: State, remaining: int, alpha: float, beta: float,
               latent) -> float:
        check_budget()
        counters.node_visits += 1
        if counters.node_visits % 256 == 0:
            sample_memory()
        terminal = game.terminal(state)
        if terminal is not None:
            counters.terminal_nodes += 1
            return float(root_player * terminal)
        if remaining == 0:
            latent_at_leaf = (
                model.encode(game.features(state))
                if model.arm == "direct-leaf-value" else latent
            )
            return float(root_player * state.player * model.value(latent_at_leaf))

        maximizing = state.player == root_player
        best = -math.inf if maximizing else math.inf
        actions = tuple(game.legal_actions(state))
        if not actions:
            raise RuntimeError("reachable nonterminal node has no legal action")
        for action in actions:
            counters.transition_calls += 1
            child = game.transition(state, action)
            child_latent = None
            if game.terminal(child) is None and model.arm != "direct-leaf-value":
                child_latent = model.advance(latent, action, state.player, descriptor)
            score = search(child, remaining - 1, alpha, beta, child_latent)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if alpha >= beta:
                break
        return best

    if stop_reason == "depth_4_complete":
        for depth in range(1, 5):
            iteration_values = {}
            alpha = -math.inf
            beta = math.inf
            try:
                check_budget()
                counters.node_visits += 1
                if counters.node_visits % 256 == 0:
                    sample_memory()
                for action in legal_root:
                    counters.transition_calls += 1
                    child = game.transition(root.state, action)
                    child_latent = None
                    if (game.terminal(child) is None
                            and model.arm != "direct-leaf-value"):
                        child_latent = model.advance(
                            root_latent, action, root.state.player, descriptor
                        )
                    iteration_values[action] = search(
                        child, depth - 1, alpha, beta, child_latent
                    )
                    alpha = max(alpha, iteration_values[action])
            except PilotBudgetStop as stop:
                stop_reason = stop.reason
                break
            if not iteration_values:
                stop_reason = "no_completed_root_action"
                break
            completed_depth = depth
            last_completed_action = max(
                legal_root, key=iteration_values.__getitem__
            )

    try:
        sample_memory()
    except PilotBudgetStop as stop:
        stop_reason = stop.reason
    wall_seconds = max(0.0, time.monotonic() - request_started)
    return {
        "action": last_completed_action,
        "completed_depth": completed_depth,
        "stop_reason": stop_reason,
        "node_visits": counters.node_visits,
        "transition_calls": counters.transition_calls,
        "encoder_calls": counters.encoder_calls,
        "predictor_calls": counters.predictor_calls,
        "decoder_calls": counters.decoder_calls,
        "value_calls": counters.value_calls,
        "model_calls": counters.model_calls,
        "terminal_nodes": counters.terminal_nodes,
        "peak_sampled_rss_bytes": counters.peak_sampled_rss_bytes,
        "search_wall_seconds": wall_seconds,
    }


def _worker_main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        game = next(game for game in VARIANTS
                    if game.name == request["variant"])
        root = Root(
            variant=game.name,
            target_ply=request["target_ply"],
            episode_seed=request["root_seed"],
            state_sha256=request["root_state_sha256"],
            state=State(tuple(request["board"]), request["player"]),
        )
        scope = verify_memory_scope(request["expected_memory_max"])
        if scope["path"] != request["expected_cgroup_path"]:
            raise RuntimeError("worker did not inherit the request cgroup")
        rss_before_model = _sample_rss_bytes()
        model = RandomInferenceModel(request["arm"], request["model_seed"])
        rss_after_model = _sample_rss_bytes()
        reply = _search_action(
            game, root, model, request["request_started"],
            request["planner_deadline"],
            request["node_cap"], request["rss_cap_bytes"],
            max(rss_before_model, rss_after_model),
        )
        reply["worker_cgroup_path"] = scope["path"]
        reply["worker_memory_max"] = scope["memory_max"]
        sys.stdout.write(json.dumps(reply, separators=(",", ":")))
        return 0
    except Exception as error:  # Send a bounded error marker, never a traceback.
        sys.stdout.write(json.dumps({"worker_error": type(error).__name__}))
        return 1


def _run_worker_process(command: list[str], payload: dict[str, Any],
                        response_deadline: float) -> dict[str, Any]:
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, start_new_session=True,
        close_fds=True,
    )
    try:
        stdout, _ = process.communicate(
            json.dumps(payload, separators=(",", ":")),
            timeout=max(0.0, response_deadline - time.monotonic()),
        )
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            stdout, _ = process.communicate(timeout=0.05)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout = ""
        return {"timed_out": True, "returncode": process.poll(),
                "worker_reaped": process.returncode is not None,
                "stdout": stdout}
    try:
        parsed = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        return {"invalid_worker_response": True,
                "returncode": process.returncode}
    return {"timed_out": False, "returncode": process.returncode,
            "reply": parsed}


def run_move_request(game: BoardGame, root: Root, arm: str,
                     model_seed: int, *,
                     node_cap: int = NODE_CAP,
                     planner_seconds: float = PLANNER_SECONDS,
                     response_seconds: float = RESPONSE_SECONDS,
                     rss_cap_bytes: int = RSS_CAP_BYTES) -> dict[str, Any]:
    """Supervise one request; return the action transiently and counters only."""
    request_started = time.monotonic()
    if not math.isfinite(planner_seconds) or planner_seconds <= 0:
        raise ValueError("planner deadline must be finite and positive")
    if not math.isfinite(response_seconds) or response_seconds <= planner_seconds:
        raise ValueError("response deadline must exceed planner deadline")
    if arm not in ARMS or type(model_seed) is not int:
        raise ValueError("invalid random-inference model identity")
    if type(node_cap) is not int or node_cap <= 0:
        raise ValueError("node cap must be a positive integer")
    if type(rss_cap_bytes) is not int or rss_cap_bytes <= 0:
        raise ValueError("RSS cap must be a positive integer")
    if root.variant != game.name or game.terminal(root.state) is not None:
        raise ValueError("request root does not match the game or is terminal")
    legal = tuple(game.legal_actions(root.state))
    if not legal:
        raise ValueError("request root has no legal action")
    fallback_action = legal[0]

    scope = verify_memory_scope()
    expected_path = scope["path"]
    expected_max = scope["memory_max"]
    before_events = scope["events"]
    cgroup_record = {
        "path": expected_path,
        "memory_max": expected_max,
        "memory_oom_group": scope["memory_oom_group"],
        "events_before": before_events,
    }

    payload = {
        "variant": game.name,
        "target_ply": root.target_ply,
        "root_seed": root.episode_seed,
        "root_state_sha256": root.state_sha256,
        "board": list(root.state.board),
        "player": root.state.player,
        "arm": arm,
        "model_seed": model_seed,
        "request_started": request_started,
        "planner_deadline": request_started + planner_seconds,
        "node_cap": node_cap,
        "rss_cap_bytes": rss_cap_bytes,
        "expected_cgroup_path": expected_path,
        "expected_memory_max": expected_max,
    }
    command = [sys.executable, "-m", "two_player.v212_request_adapter_v01",
               "--worker"]
    supervised = _run_worker_process(
        command, payload, request_started + response_seconds
    )
    elapsed = max(0.0, time.monotonic() - request_started)
    scope_delta = {}
    try:
        after_scope = verify_memory_scope()
        if after_scope["path"] != expected_path:
            raise RuntimeError("request supervisor left its bounded cgroup")
        scope_delta = {
            key: after_scope["events"].get(key, 0) - before_events.get(key, 0)
            for key in after_scope["events"]
        }
        cgroup_record["events_after"] = after_scope["events"]
        cgroup_record["events_delta"] = scope_delta
    except (OSError, RuntimeError, ValueError):
        return {"status": "forfeit", "reason": "cgroup_audit_failure",
                "action": None, "request_wall_seconds": elapsed,
                "cgroup": cgroup_record}
    oom_delta = scope_delta.get("oom_kill", 0) + scope_delta.get("oom_group_kill", 0)
    if oom_delta > 0:
        return {"status": "forfeit", "reason": "memory_cgroup_oom",
                "action": None, "request_wall_seconds": elapsed,
                "worker_returncode": supervised.get("returncode"),
                "cgroup_event_delta": scope_delta,
                "cgroup": cgroup_record}
    if supervised.get("timed_out") or elapsed >= response_seconds:
        timeout_reason = (
            "response_watchdog_timeout" if supervised.get("worker_reaped")
            else "watchdog_cleanup_unconfirmed"
        )
        return {"status": "forfeit", "reason": timeout_reason,
                "action": None, "request_wall_seconds": elapsed,
                "worker_returncode": supervised.get("returncode"),
                "worker_reaped": supervised.get("worker_reaped"),
                "cgroup_event_delta": scope_delta,
                "cgroup": cgroup_record}
    if supervised.get("invalid_worker_response") or supervised.get("returncode") != 0:
        return {"status": "forfeit", "reason": "worker_failure", "action": None,
                "request_wall_seconds": elapsed,
                "worker_returncode": supervised.get("returncode"),
                "cgroup_event_delta": scope_delta,
                "cgroup": cgroup_record}
    reply = supervised["reply"]
    if "worker_error" in reply:
        return {"status": "forfeit", "reason": "worker_failure", "action": None,
                "request_wall_seconds": elapsed,
                "worker_error": reply["worker_error"],
                "cgroup_event_delta": scope_delta,
                "cgroup": cgroup_record}
    if (
        reply.get("worker_cgroup_path") != expected_path
        or reply.get("worker_memory_max") != expected_max
    ):
        return {"status": "forfeit", "reason": "cgroup_inheritance_failure",
                "action": None, "request_wall_seconds": elapsed,
                "cgroup": cgroup_record}
    action = reply.get("action")
    if type(action) is not int or action not in legal:
        return {"status": "forfeit", "reason": "invalid_action", "action": None,
                "request_wall_seconds": elapsed, "cgroup": cgroup_record}

    depth = reply.get("completed_depth")
    reason = reply.get("stop_reason")
    if type(depth) is not int or not 0 <= depth <= 4:
        return {"status": "forfeit", "reason": "invalid_worker_response",
                "action": None, "request_wall_seconds": elapsed,
                "cgroup": cgroup_record}
    if depth == 0 and action != fallback_action:
        return {"status": "forfeit", "reason": "invalid_fallback_action",
                "action": None, "request_wall_seconds": elapsed,
                "cgroup": cgroup_record}
    if reason == "depth_4_complete" and depth == 4:
        status = "response"
    elif reason in {"node_cap", "wall_cap", "rss_cap",
                    "no_completed_root_action"}:
        status = "completed_with_budget_stop" if depth == 4 else "controlled_fallback"
    else:
        return {"status": "forfeit", "reason": "invalid_worker_response",
                "action": None, "request_wall_seconds": elapsed,
                "cgroup": cgroup_record}
    return {
        "status": status,
        "reason": reason,
        "action": action,  # Transient response only; never add to pilot receipts.
        "request_wall_seconds": elapsed,
        "planner_wall_seconds": reply.get("search_wall_seconds"),
        "completed_depth": depth,
        "worker_returncode": supervised["returncode"],
        "cgroup_event_delta": scope_delta,
        "cgroup": cgroup_record,
        "counters": {key: value for key, value in reply.items()
                      if key not in {"action", "worker_cgroup_path",
                                     "worker_memory_max"}},
    }


if __name__ == "__main__" and "--worker" in sys.argv:
    raise SystemExit(_worker_main())
