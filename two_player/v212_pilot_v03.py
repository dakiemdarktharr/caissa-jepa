"""Versioned RSS-safe wrapper for the no-training V2.12 compute pilot.

V02 remains immutable for receipt reproducibility. This module fixes its RSS
guard escape paths and provides append-only progress records for a V03 runner.
It does not add data, score, outcome, optimizer, or checkpoint access.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Callable

from .v212_pilot import (
    NODE_CAP,
    RSS_CAP_BYTES,
    WALL_CAP_SECONDS,
    Counters,
    PilotBudgetStop,
    RandomInferenceModel,
    Root,
    _sample_rss_bytes,
)

PILOT_VERSION = "v212-random-weight-compute-pilot-v03"


def run_root_arm_v03(
    game,
    root: Root,
    model: RandomInferenceModel,
    *,
    node_cap: int = NODE_CAP,
    wall_cap_seconds: float = WALL_CAP_SECONDS,
    rss_cap_bytes: int = RSS_CAP_BYTES,
    rss_sampler: Callable[[], int] = _sample_rss_bytes,
) -> dict:
    """Run one compute-only cell, converting every RSS crossing to a row.

    The RSS check is sampled and cooperative, not a hard memory ceiling. The
    caller must still run this inside an independently enforced memory limit.
    """
    if root.variant != game.name or game.terminal(root.state) is not None:
        raise ValueError("pilot root does not match the game or is terminal")
    if type(node_cap) is not int or node_cap <= 0:
        raise ValueError("node cap must be a positive integer")
    if not math.isfinite(wall_cap_seconds) or wall_cap_seconds <= 0:
        raise ValueError("wall cap must be finite and positive")
    if type(rss_cap_bytes) is not int or rss_cap_bytes <= 0:
        raise ValueError("RSS cap must be a positive integer")

    model.reset_calls()
    counters: Counters = model.calls
    start = time.perf_counter()
    deadline = start + wall_cap_seconds
    root_player = root.state.player
    root_features = game.features(root.state)
    descriptor = root_features[192:198]
    legal_root = tuple(game.legal_actions(root.state))
    if not legal_root:
        raise ValueError("nonterminal pilot root has no legal action")

    def sample_memory() -> None:
        current = rss_sampler()
        if type(current) is not int or current < 0:
            raise ValueError("RSS sampler returned an invalid byte count")
        counters.peak_sampled_rss_bytes = max(
            counters.peak_sampled_rss_bytes, current
        )
        if current > rss_cap_bytes:
            raise PilotBudgetStop("rss_cap")

    completed_depth = 0
    last_completed_action = legal_root[0]
    stop_reason = "depth_4_complete"
    root_latent = None

    try:
        # Enforce the cap at entry, before encoding or search work.
        sample_memory()
        if time_reached(deadline):
            raise PilotBudgetStop("wall_cap")
        if model.arm != "direct-leaf-value":
            root_latent = model.encode(root_features)
    except PilotBudgetStop as stop:
        stop_reason = stop.reason

    def check_budget() -> None:
        if counters.node_visits >= node_cap:
            raise PilotBudgetStop("node_cap")
        if time_reached(deadline):
            raise PilotBudgetStop("wall_cap")

    def search(state, remaining: int, alpha: float, beta: float,
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
            latent_at_leaf = (model.encode(game.features(state))
                              if model.arm == "direct-leaf-value" else latent)
            value = model.value(latent_at_leaf)
            return float(root_player * state.player * value)

        maximizing = state.player == root_player
        best = -math.inf if maximizing else math.inf
        actions = tuple(game.legal_actions(state))
        if not actions:
            raise RuntimeError("reachable nonterminal search node has no legal action")
        for action in actions:
            counters.transition_calls += 1
            child = game.transition(state, action)
            child_terminal = game.terminal(child)
            child_latent = None
            if child_terminal is None and model.arm != "direct-leaf-value":
                child_latent = model.advance(
                    latent, action, state.player, descriptor
                )
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
                    child_terminal = game.terminal(child)
                    child_latent = None
                    if (child_terminal is None
                            and model.arm != "direct-leaf-value"):
                        child_latent = model.advance(
                            root_latent, action, root.state.player, descriptor
                        )
                    score = search(child, depth - 1, alpha, beta, child_latent)
                    iteration_values[action] = score
                    alpha = max(alpha, score)
            except PilotBudgetStop as stop:
                stop_reason = stop.reason
                break
            if not iteration_values:
                stop_reason = "no_completed_root_action"
                break
            completed_depth = depth
            last_completed_action = max(legal_root, key=iteration_values.__getitem__)

    # Final sampling is deliberately fail-closed but never escapes without a
    # diagnostic row. A post-search crossing can coexist with depth 4 complete.
    # A sampled crossing is already decisive. Avoid another sampler call that
    # could fail and erase the known RSS-stop row before it reaches the journal.
    if stop_reason != "rss_cap":
        try:
            sample_memory()
        except PilotBudgetStop as stop:
            stop_reason = stop.reason

    elapsed = max(0.0, time.perf_counter() - start)
    if elapsed >= wall_cap_seconds and stop_reason == "depth_4_complete":
        stop_reason = "wall_cap"
    return {
        "variant": game.name,
        "arm": model.arm,
        "root_target_ply": root.target_ply,
        "root_state_sha256": root.state_sha256,
        "completed_depth": completed_depth,
        "fallback_used": completed_depth < 4,
        "fallback_action_available": last_completed_action in legal_root,
        "stop_reason": stop_reason,
        "node_visits": counters.node_visits,
        "transition_calls": counters.transition_calls,
        "encoder_calls": counters.encoder_calls,
        "predictor_calls": counters.predictor_calls,
        "decoder_calls": counters.decoder_calls,
        "value_calls": counters.value_calls,
        "model_calls": counters.model_calls,
        "terminal_nodes": counters.terminal_nodes,
        "wall_seconds": elapsed,
        "peak_sampled_rss_bytes": counters.peak_sampled_rss_bytes,
    }


def time_reached(deadline: float) -> bool:
    # Kept as a tiny wrapper so deterministic unit tests can patch one clock.
    return time.perf_counter() >= deadline


def append_progress_record(path: Path, record: dict) -> None:
    """Append one compact JSONL record and sync it before returning."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _jsonl_payload(record)
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)


def create_progress_journal(path: Path, manifest: dict) -> None:
    """Create a new journal with its manifest as the first durable record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _jsonl_payload(manifest)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    fsync_directory(path.parent)


def _jsonl_payload(record: dict) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def fsync_directory(path: Path) -> None:
    directory_fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class ReceiptPublicationUncertain(OSError):
    """The verified receipt is linked, but its directory entry was not synced."""

    def __init__(self, path: Path, cause: OSError):
        super().__init__(f"receipt linked but directory fsync failed: {cause}")
        self.path = path


def write_new_receipt_atomic(path: Path, payload: dict) -> None:
    """Create a final receipt atomically without replacing an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, sort_keys=True, indent=2,
                          allow_nan=False) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        try:
            os.unlink(temporary)
            fsync_directory(path.parent)
        except OSError as error:
            # Any failure after publication leaves a visible receipt whose
            # durability/reconciliation state must be explicit to the caller.
            raise ReceiptPublicationUncertain(path, error) from error
    finally:
        if os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                # Preserve the primary write/link/fsync error; a leftover temp
                # file is harmless and remains visible for manual cleanup.
                pass
