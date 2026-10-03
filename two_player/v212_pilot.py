"""No-training, random-weight compute instrumentation for the V2.12 pilot.

This module intentionally has no dataset, checkpoint, optimizer, score ledger,
or fitting imports. It uses only exact project-owned game rules, synthetic
legal roots, and freshly initialized NumPy weights.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import time
from typing import Callable

import numpy as np

from .games import ACTION_SIZE, FEATURE_SIZE, BoardGame, State

PILOT_VERSION = "v212-random-weight-compute-pilot-v01"
ROOT_PLIES = (0, 8, 16, 24)
ARMS = (
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state-dynamics",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
)
VARIANTS = (
    BoardGame("connect4-gravity-6x7", 6, 7, 4, gravity=True),
    BoardGame("connect4-gravity-8x8", 8, 8, 4, gravity=True),
    BoardGame("reversi6", 6, 6, 0, reversi=True),
    BoardGame("reversi8", 8, 8, 0, reversi=True),
)
RANDOM_WEIGHT_SEED = 212701
NODE_CAP = 500_000
WALL_CAP_SECONDS = 8.0
RSS_CAP_BYTES = int(1.5 * 1024**3)
MAX_SEEDS_PER_PLY = 64


@dataclass(frozen=True)
class Root:
    variant: str
    target_ply: int
    episode_seed: int
    state_sha256: str
    state: State

    def public_record(self) -> dict:
        return {
            "variant": self.variant,
            "target_ply": self.target_ply,
            "episode_seed": self.episode_seed,
            "state_sha256": self.state_sha256,
        }


@dataclass
class Counters:
    node_visits: int = 0
    transition_calls: int = 0
    encoder_calls: int = 0
    predictor_calls: int = 0
    decoder_calls: int = 0
    value_calls: int = 0
    terminal_nodes: int = 0
    peak_sampled_rss_bytes: int = 0

    @property
    def model_calls(self) -> int:
        return (self.encoder_calls + self.predictor_calls + self.decoder_calls
                + self.value_calls)


class PilotBudgetStop(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _sha256_json(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _state_sha256(game: BoardGame, state: State) -> str:
    return _sha256_json({
        "rules_version": "tiny-rules-v1",
        "variant": game.name,
        "board": state.board,
        "player": state.player,
    })


def build_root_schedule() -> tuple[Root, ...]:
    """Return one deterministic reachable nonterminal state at each target ply."""
    roots = []
    for variant_index, game in enumerate(VARIANTS):
        for target_ply in ROOT_PLIES:
            first_seed = 66271 + 1000 * variant_index + 100 * target_ply
            selected = None
            for episode_seed in range(first_seed, first_seed + MAX_SEEDS_PER_PLY):
                rng = random.Random(episode_seed)
                state = game.initial()
                for _ in range(target_ply):
                    if game.terminal(state) is not None:
                        break
                    legal = game.legal_actions(state)
                    if not legal:
                        raise RuntimeError("reachable nonterminal root has no legal action")
                    state = game.transition(state, rng.choice(legal))
                if game.terminal(state) is None:
                    selected = Root(game.name, target_ply, episode_seed,
                                    _state_sha256(game, state), state)
                    break
            if selected is None:
                raise RuntimeError(
                    f"no nonterminal {game.name} root found at ply {target_ply} "
                    f"within {MAX_SEEDS_PER_PLY} frozen seeds"
                )
            roots.append(selected)
    return tuple(roots)


def schedule_sha256(roots: tuple[Root, ...]) -> str:
    return _sha256_json([root.public_record() for root in roots])


def _weight(seed: int, fan_in: int, fan_out: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0 / math.sqrt(fan_in),
                      size=(fan_in, fan_out)).astype(np.float64)


class RandomInferenceModel:
    """Small v04-shaped inference model; parameters are never updated."""

    def __init__(self, arm: str, seed: int = RANDOM_WEIGHT_SEED):
        if arm not in ARMS:
            raise ValueError("unknown V2.12 pilot arm")
        self.arm = arm
        latent = 32
        self.encoder_w = _weight(seed + 1, FEATURE_SIZE, latent)
        self.encoder_b = np.zeros(latent, dtype=np.float64)
        self.predictor_w = _weight(seed + 2, latent + ACTION_SIZE + 1 + 6, latent)
        self.predictor_b = np.zeros(latent, dtype=np.float64)
        self.decoder_w = (
            _weight(seed + 3, latent + ACTION_SIZE + 1 + 6, FEATURE_SIZE)
            if arm == "recursive-raw-state-dynamics" else None
        )
        self.decoder_b = (np.zeros(FEATURE_SIZE, dtype=np.float64)
                          if self.decoder_w is not None else None)
        self.value_w = _weight(seed + 4, latent, 1)
        self.value_b = np.zeros(1, dtype=np.float64)
        self.calls = Counters()

    def reset_calls(self) -> None:
        self.calls = Counters()

    def encode(self, features: np.ndarray) -> np.ndarray:
        self.calls.encoder_calls += 1
        result = np.tanh(np.asarray(features, dtype=np.float64) @ self.encoder_w
                         + self.encoder_b)
        if not np.isfinite(result).all():
            raise FloatingPointError("nonfinite random encoder output")
        return result

    @staticmethod
    def _predictor_input(latent: np.ndarray, action: int, actor: int,
                         descriptor: np.ndarray) -> np.ndarray:
        action_hot = np.zeros(ACTION_SIZE, dtype=np.float64)
        action_hot[action] = 1.0
        return np.concatenate((latent, action_hot, np.asarray([actor]), descriptor))

    def advance(self, latent: np.ndarray, action: int, actor: int,
                descriptor: np.ndarray) -> np.ndarray:
        inputs = self._predictor_input(latent, action, actor, descriptor)
        if self.arm == "recursive-raw-state-dynamics":
            self.calls.decoder_calls += 1
            predicted_features = np.tanh(inputs @ self.decoder_w + self.decoder_b)
            if not np.isfinite(predicted_features).all():
                raise FloatingPointError("nonfinite random raw-state output")
            return self.encode(predicted_features)
        self.calls.predictor_calls += 1
        predicted = np.tanh(inputs @ self.predictor_w + self.predictor_b)
        if not np.isfinite(predicted).all():
            raise FloatingPointError("nonfinite random latent prediction")
        return predicted

    def value(self, latent: np.ndarray) -> float:
        self.calls.value_calls += 1
        result = float(np.tanh(latent @ self.value_w + self.value_b)[0])
        if not math.isfinite(result) or not -1.0 <= result <= 1.0:
            raise FloatingPointError("invalid random value output")
        return result


def _sample_rss_bytes() -> int:
    try:
        with open("/proc/self/status", encoding="ascii") as stream:
            for line in stream:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    # Linux reports ru_maxrss in KiB. This is a process high-water fallback.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)


def _warmup(game: BoardGame, root: Root, model: RandomInferenceModel) -> None:
    features = game.features(root.state)
    latent = model.encode(features)
    if model.arm != "direct-leaf-value":
        action = game.legal_actions(root.state)[0]
        child = game.transition(root.state, action)
        if game.terminal(child) is None:
            next_latent = model.advance(latent, action, root.state.player,
                                        features[192:198])
            model.value(next_latent)
        else:
            model.value(latent)
    else:
        model.value(latent)


def run_root_arm(game: BoardGame, root: Root, model: RandomInferenceModel,
                 *, node_cap: int = NODE_CAP, wall_cap_seconds: float = WALL_CAP_SECONDS,
                 rss_cap_bytes: int = RSS_CAP_BYTES) -> dict:
    """Run iterative-depth alpha-beta and return compute counters only."""
    if root.variant != game.name or game.terminal(root.state) is not None:
        raise ValueError("pilot root does not match the game or is terminal")
    if type(node_cap) is not int or node_cap <= 0:
        raise ValueError("node cap must be a positive integer")
    if not math.isfinite(wall_cap_seconds) or wall_cap_seconds <= 0:
        raise ValueError("wall cap must be finite and positive")
    if type(rss_cap_bytes) is not int or rss_cap_bytes <= 0:
        raise ValueError("RSS cap must be a positive integer")

    model.reset_calls()
    counters = model.calls
    start = time.perf_counter()
    deadline = start + wall_cap_seconds
    counters.peak_sampled_rss_bytes = _sample_rss_bytes()
    root_player = root.state.player
    root_features = game.features(root.state)
    descriptor = root_features[192:198]
    root_latent = (None if model.arm == "direct-leaf-value"
                   else model.encode(root_features))
    legal_root = tuple(game.legal_actions(root.state))
    if not legal_root:
        raise ValueError("nonterminal pilot root has no legal action")

    def check_budget() -> None:
        if counters.node_visits >= node_cap:
            raise PilotBudgetStop("node_cap")
        if time.perf_counter() >= deadline:
            raise PilotBudgetStop("wall_cap")

    def sample_memory() -> None:
        current = _sample_rss_bytes()
        counters.peak_sampled_rss_bytes = max(counters.peak_sampled_rss_bytes, current)
        if current > rss_cap_bytes:
            raise PilotBudgetStop("rss_cap")

    def search(state: State, remaining: int, alpha: float, beta: float,
               latent: np.ndarray | None) -> float:
        check_budget()
        counters.node_visits += 1
        if counters.node_visits % 256 == 0:
            sample_memory()
        terminal = game.terminal(state)
        if terminal is not None:
            counters.terminal_nodes += 1
            return float(root_player * terminal)
        if remaining == 0:
            if model.arm == "direct-leaf-value":
                latent_at_leaf = model.encode(game.features(state))
            else:
                latent_at_leaf = latent
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

    completed_depth = 0
    last_completed_action = legal_root[0]
    stop_reason = "depth_4_complete"
    for depth in range(1, 5):
        iteration_values = {}
        alpha = -math.inf
        beta = math.inf
        try:
            check_budget()
            counters.node_visits += 1  # The root state is a visited search node.
            if counters.node_visits % 256 == 0:
                sample_memory()
            for action in legal_root:
                counters.transition_calls += 1
                child = game.transition(root.state, action)
                child_terminal = game.terminal(child)
                child_latent = None
                if child_terminal is None and model.arm != "direct-leaf-value":
                    child_latent = model.advance(root_latent, action,
                                                 root.state.player, descriptor)
                score = search(child, depth - 1, alpha, beta, child_latent)
                iteration_values[action] = score
                alpha = max(alpha, score)
        except PilotBudgetStop as stop:
            stop_reason = stop.reason
            break
        # The action is intentionally discarded. Only completion depth is kept.
        if not iteration_values:
            stop_reason = "no_completed_root_action"
            break
        completed_depth = depth
        last_completed_action = max(legal_root, key=iteration_values.__getitem__)

    sample_memory()
    elapsed = time.perf_counter() - start
    counters.peak_sampled_rss_bytes = max(counters.peak_sampled_rss_bytes,
                                          _sample_rss_bytes())
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


def create_receipt(results: list[dict], roots: tuple[Root, ...],
                   source_hashes: dict[str, str]) -> dict:
    root_records = [root.public_record() for root in roots]
    return {
        "pilot_version": PILOT_VERSION,
        "status": "compute_only_no_training",
        "protocol_sha256": source_hashes["protocol"],
        "pilot_source_sha256": source_hashes["pilot_source"],
        "runner_source_sha256": source_hashes["runner_source"],
        "rules_source_sha256": source_hashes["rules_source"],
        "schedule_sha256": schedule_sha256(roots),
        "random_weight_seed": RANDOM_WEIGHT_SEED,
        "node_cap": NODE_CAP,
        "wall_cap_seconds": WALL_CAP_SECONDS,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "max_seeds_per_ply": MAX_SEEDS_PER_PLY,
        "root_plies": list(ROOT_PLIES),
        "variants": [game.name for game in VARIANTS],
        "arms": list(ARMS),
        "root_schedule": root_records,
        "expected_root_arm_cells": len(roots) * len(ARMS),
        "measured_root_arm_cells": len(results),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
        "guardrails": {
            "training_data_opened": False,
            "outcome_labels_read": False,
            "optimizer_updates": 0,
            "trained_checkpoints_saved": 0,
            "game_scores_recorded": False,
            "selected_actions_or_values_recorded": False,
            "locked_final_access": False,
        },
        "results": results,
    }


def verify_receipt(receipt: dict) -> None:
    if receipt.get("status") != "compute_only_no_training":
        raise ValueError("unexpected pilot receipt status")
    results = receipt.get("results")
    roots = receipt.get("root_schedule")
    if not isinstance(results, list) or not isinstance(roots, list):
        raise ValueError("missing pilot schedule/results")
    expected = len(roots) * len(ARMS)
    if receipt.get("expected_root_arm_cells") != expected:
        raise ValueError("expected root-arm cell count mismatch")
    if receipt.get("measured_root_arm_cells") != expected or len(results) != expected:
        raise ValueError("incomplete root-arm pilot")
    if receipt.get("schedule_sha256") != _sha256_json(roots):
        raise ValueError("root schedule hash mismatch")
    root_keys = {(r["variant"], r["target_ply"], r["state_sha256"]) for r in roots}
    if len(root_keys) != len(roots):
        raise ValueError("duplicate root schedule entry")
    expected_schedule = {(game.name, ply) for game in VARIANTS for ply in ROOT_PLIES}
    if {(r["variant"], r["target_ply"]) for r in roots} != expected_schedule:
        raise ValueError("root schedule does not cover each variant and frozen ply")
    expected_cells = {(variant, root_hash, arm)
                      for variant, _ply, root_hash in root_keys for arm in ARMS}
    keys = {(r["variant"], r["root_state_sha256"], r["arm"]) for r in results}
    if len(keys) != len(results) or keys != expected_cells:
        raise ValueError("root-arm schedule coverage mismatch")
    if set(receipt.get("arms", ())) != set(ARMS):
        raise ValueError("arm roster mismatch")
    if set(receipt.get("variants", ())) != {game.name for game in VARIANTS}:
        raise ValueError("variant roster mismatch")
    if any(r.get("node_visits", 0) > NODE_CAP for r in results):
        raise ValueError("node cap exceeded")
    if any(r.get("wall_seconds", math.inf) > WALL_CAP_SECONDS + 0.05 for r in results):
        raise ValueError("wall cap exceeded beyond reporting tolerance")
    if any(r.get("peak_sampled_rss_bytes", RSS_CAP_BYTES + 1) > RSS_CAP_BYTES
           for r in results):
        raise ValueError("sampled RSS cap exceeded")
    forbidden = {"score", "game_score", "outcome", "selected_action", "action_values",
                 "winner", "utility"}
    if any(forbidden.intersection(result) for result in results):
        raise ValueError("outcome or action-selection field present in pilot results")
    integer_fields = ("node_visits", "transition_calls", "encoder_calls",
                      "predictor_calls", "decoder_calls", "value_calls",
                      "model_calls", "terminal_nodes", "peak_sampled_rss_bytes",
                      "completed_depth")
    for result in results:
        if any(type(result.get(field)) is not int or result[field] < 0
               for field in integer_fields):
            raise ValueError("invalid integer compute measurement")
        if not math.isfinite(result.get("wall_seconds", math.nan)):
            raise ValueError("nonfinite wall-time measurement")
        if result["model_calls"] != sum(result[field] for field in (
            "encoder_calls", "predictor_calls", "decoder_calls", "value_calls")):
            raise ValueError("model-call total mismatch")
        if not 0 <= result["completed_depth"] <= 4:
            raise ValueError("invalid completed depth")
        if result.get("fallback_used") != (result["completed_depth"] < 4):
            raise ValueError("fallback state does not match completed depth")
        if result.get("fallback_action_available") is not True:
            raise ValueError("no internal legal fallback action was retained")
    guards = receipt.get("guardrails", {})
    expected_guards = {
        "training_data_opened": False,
        "outcome_labels_read": False,
        "optimizer_updates": 0,
        "trained_checkpoints_saved": 0,
        "game_scores_recorded": False,
        "selected_actions_or_values_recorded": False,
        "locked_final_access": False,
    }
    if guards != expected_guards:
        raise ValueError("pilot guardrail receipt mismatch")
