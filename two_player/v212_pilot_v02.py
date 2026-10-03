"""Expanded no-training V2.12 random-weight compute-pilot instrumentation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random

from .v212_pilot import (
    ARMS,
    MAX_SEEDS_PER_PLY,
    ROOT_PLIES,
    VARIANTS,
    RandomInferenceModel,
    Root,
    _sha256_json,
    _state_sha256,
    build_root_schedule,
    run_root_arm,
)

INIT_SEEDS = (212701, 212702, 212703)
ROOTS_PER_VARIANT = 16
ROOT_COUNT_BY_PLY = {0: 1, 8: 5, 16: 5, 24: 5}
ADDITIONAL_SEED_BASE = 80_000
NODE_CAP = 500_000
WALL_CAP_SECONDS = 8.0
RSS_CAP_BYTES = int(1.5 * 1024**3)
PILOT_VERSION = "v212-random-weight-compute-pilot-v02"


@dataclass(frozen=True)
class ScheduledRoot:
    ordinal: int
    root: Root

    def public_record(self) -> dict:
        return {"root_ordinal": self.ordinal, **self.root.public_record()}


def _state_at_ply(game, target_ply: int, episode_seed: int):
    rng = random.Random(episode_seed)
    state = game.initial()
    for _ in range(target_ply):
        if game.terminal(state) is not None:
            return None
        actions = game.legal_actions(state)
        if not actions:
            raise RuntimeError("reachable nonterminal root has no legal action")
        state = game.transition(state, rng.choice(actions))
    return None if game.terminal(state) is not None else state


def build_root_schedule_v02() -> tuple[ScheduledRoot, ...]:
    """Retain each v01 root and append roots from globally disjoint seed windows."""
    v01_roots = {
        (root.variant, root.target_ply): root for root in build_root_schedule()
    }
    scheduled: list[ScheduledRoot] = []
    for variant_index, game in enumerate(VARIANTS):
        selected_hashes: set[str] = set()
        for ply_index, target_ply in enumerate(ROOT_PLIES):
            first = v01_roots[(game.name, target_ply)]
            if first.state_sha256 in selected_hashes:
                raise RuntimeError("duplicate v01 root fingerprint within variant")
            selected_hashes.add(first.state_sha256)
            scheduled.append(ScheduledRoot(0, first))

            count = ROOT_COUNT_BY_PLY[target_ply]
            if count == 1:
                continue
            nonzero_ply_index = ply_index - 1
            for ordinal in range(1, count):
                range_index = ((variant_index * (len(ROOT_PLIES) - 1)
                                + nonzero_ply_index) * (count - 1)
                               + ordinal - 1)
                first_seed = ADDITIONAL_SEED_BASE + MAX_SEEDS_PER_PLY * range_index
                selected = None
                for episode_seed in range(first_seed,
                                          first_seed + MAX_SEEDS_PER_PLY):
                    state = _state_at_ply(game, target_ply, episode_seed)
                    if state is None:
                        continue
                    fingerprint = _state_sha256(game, state)
                    if fingerprint in selected_hashes:
                        continue
                    selected = Root(game.name, target_ply, episode_seed,
                                    fingerprint, state)
                    break
                if selected is None:
                    raise RuntimeError(
                        f"no distinct nonterminal {game.name} root at ply "
                        f"{target_ply} in frozen seed window {range_index}"
                    )
                selected_hashes.add(selected.state_sha256)
                scheduled.append(ScheduledRoot(ordinal, selected))
    return tuple(scheduled)


def schedule_sha256_v02(roots: tuple[ScheduledRoot, ...]) -> str:
    return _sha256_json([root.public_record() for root in roots])


def source_sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_receipt(results: list[dict], roots: tuple[ScheduledRoot, ...],
                   source_hashes: dict[str, str], warmups: dict,
                   runtime: dict, schedule_generation_seconds: float = 0.0) -> dict:
    root_records = [root.public_record() for root in roots]
    return {
        "pilot_version": PILOT_VERSION,
        "status": "compute_only_no_training",
        "protocol_sha256": source_hashes["protocol"],
        "pilot_source_sha256": source_hashes["pilot_source"],
        "runner_source_sha256": source_hashes["runner_source"],
        "shared_pilot_source_sha256": source_hashes["shared_pilot_source"],
        "rules_source_sha256": source_hashes["rules_source"],
        "schedule_sha256": schedule_sha256_v02(roots),
        "init_seeds": list(INIT_SEEDS),
        "node_cap": NODE_CAP,
        "wall_cap_seconds": WALL_CAP_SECONDS,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "max_seeds_per_root": MAX_SEEDS_PER_PLY,
        "root_count_by_ply": {str(ply): count
                               for ply, count in ROOT_COUNT_BY_PLY.items()},
        "additional_seed_base": ADDITIONAL_SEED_BASE,
        "root_plies": list(ROOT_PLIES),
        "variants": [game.name for game in VARIANTS],
        "arms": list(ARMS),
        "root_schedule": root_records,
        "expected_cells": len(roots) * len(ARMS) * len(INIT_SEEDS),
        "measured_cells": len(results),
        "runtime": runtime,
        "schedule_generation_seconds": schedule_generation_seconds,
        "guardrails": {
            "training_data_opened": False,
            "outcome_labels_read": False,
            "optimizer_updates": 0,
            "trained_checkpoints_saved": 0,
            "game_scores_recorded": False,
            "selected_actions_or_values_recorded": False,
            "locked_final_access": False,
        },
        "warmups": warmups,
        "results": results,
    }


def verify_receipt_v02(receipt: dict) -> None:
    expected_receipt_fields = {
        "pilot_version", "status", "protocol_sha256", "pilot_source_sha256",
        "runner_source_sha256", "shared_pilot_source_sha256", "rules_source_sha256",
        "schedule_sha256", "init_seeds", "node_cap", "wall_cap_seconds",
        "rss_cap_bytes", "max_seeds_per_root", "root_count_by_ply",
        "additional_seed_base", "root_plies", "variants", "arms",
        "root_schedule", "expected_cells", "measured_cells", "runtime",
        "schedule_generation_seconds", "guardrails", "warmups", "results",
    }
    if set(receipt) != expected_receipt_fields:
        raise ValueError("receipt fields differ from the frozen schema")
    if receipt.get("pilot_version") != PILOT_VERSION:
        raise ValueError("unexpected v02 pilot version")
    if receipt.get("status") != "compute_only_no_training":
        raise ValueError("unexpected pilot status")
    roots = build_root_schedule_v02()
    records = [root.public_record() for root in roots]
    if receipt.get("root_schedule") != records:
        raise ValueError("root schedule differs from deterministic reconstruction")
    if receipt.get("schedule_sha256") != schedule_sha256_v02(roots):
        raise ValueError("root schedule hash mismatch")
    if len(roots) != len(VARIANTS) * ROOTS_PER_VARIANT:
        raise ValueError("root schedule cell count mismatch")
    if receipt.get("init_seeds") != list(INIT_SEEDS):
        raise ValueError("random initialization roster mismatch")
    if receipt.get("arms") != list(ARMS):
        raise ValueError("arm roster mismatch")
    if receipt.get("variants") != [game.name for game in VARIANTS]:
        raise ValueError("variant roster mismatch")
    runtime = receipt.get("runtime")
    if (not isinstance(runtime, dict)
            or set(runtime) != {"python", "numpy", "platform", "machine", "cpu_count"}
            or any(not isinstance(runtime.get(key), str) or not runtime[key]
                   for key in ("python", "numpy", "platform", "machine"))
            or type(runtime.get("cpu_count")) is not int
            or runtime["cpu_count"] <= 0):
        raise ValueError("runtime fields differ from the frozen schema")
    expected_metadata = {
        "node_cap": NODE_CAP,
        "wall_cap_seconds": WALL_CAP_SECONDS,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "max_seeds_per_root": MAX_SEEDS_PER_PLY,
        "root_count_by_ply": {str(ply): count
                               for ply, count in ROOT_COUNT_BY_PLY.items()},
        "additional_seed_base": ADDITIONAL_SEED_BASE,
        "root_plies": list(ROOT_PLIES),
    }
    if any(receipt.get(key) != value for key, value in expected_metadata.items()):
        raise ValueError("receipt caps or sampling metadata differ from protocol")
    for key in ("protocol_sha256", "pilot_source_sha256", "runner_source_sha256",
                "shared_pilot_source_sha256", "rules_source_sha256",
                "schedule_sha256"):
        value = receipt.get(key)
        if (not isinstance(value, str) or len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError(f"invalid SHA-256 field: {key}")
    results = receipt.get("results")
    expected_count = len(roots) * len(ARMS) * len(INIT_SEEDS)
    if (not isinstance(results, list)
            or receipt.get("expected_cells") != expected_count
            or receipt.get("measured_cells") != expected_count
            or len(results) != expected_count):
        raise ValueError("incomplete root-arm-initialization coverage")
    expected_keys = {
        (root.root.variant, root.root.state_sha256, root.ordinal,
         root.root.target_ply, arm, seed)
        for root in roots for arm in ARMS for seed in INIT_SEEDS
    }
    actual_keys = {
        (row.get("variant"), row.get("root_state_sha256"),
         row.get("root_ordinal"), row.get("root_target_ply"),
         row.get("arm"), row.get("initialization_seed"))
        for row in results
    }
    if len(actual_keys) != len(results) or actual_keys != expected_keys:
        raise ValueError("root-arm-initialization cells do not match schedule")
    result_fields = {
        "root_ordinal", "initialization_seed", "variant", "arm",
        "root_target_ply", "root_state_sha256", "completed_depth",
        "fallback_used", "fallback_action_available", "stop_reason",
        "node_visits", "transition_calls", "encoder_calls", "predictor_calls",
        "decoder_calls", "value_calls", "model_calls", "terminal_nodes",
        "wall_seconds", "peak_sampled_rss_bytes",
    }
    integer_fields = ("root_ordinal", "root_target_ply", "initialization_seed",
                      "completed_depth", "node_visits", "transition_calls",
                      "encoder_calls", "predictor_calls", "decoder_calls",
                      "value_calls", "model_calls", "terminal_nodes",
                      "peak_sampled_rss_bytes")
    stop_reasons = {"depth_4_complete", "node_cap", "wall_cap", "rss_cap",
                    "no_completed_root_action"}
    for row in results:
        if set(row) != result_fields:
            raise ValueError("result fields differ from the frozen compute schema")
        if type(row.get("fallback_used")) is not bool:
            raise ValueError("invalid fallback flag")
        if any(type(row.get(name)) is not int or row[name] < 0
               for name in integer_fields):
            raise ValueError("invalid integer measurement")
        if (not math.isfinite(row.get("wall_seconds", math.nan))
                or row["wall_seconds"] < 0):
            raise ValueError("invalid wall time")
        if row.get("stop_reason") not in stop_reasons:
            raise ValueError("unknown stop reason")
        if row["completed_depth"] > 4:
            raise ValueError("completed depth exceeds four")
        if (row["stop_reason"] == "depth_4_complete") != (
            row["completed_depth"] == 4
        ):
            raise ValueError("completion depth and stop reason disagree")
        if row["node_visits"] > NODE_CAP:
            raise ValueError("node safety ceiling exceeded")
        if row["wall_seconds"] > WALL_CAP_SECONDS + 0.05:
            raise ValueError("wall safety ceiling exceeded")
        if row["peak_sampled_rss_bytes"] > RSS_CAP_BYTES:
            raise ValueError("sampled RSS safety ceiling exceeded")
        call_sum = sum(row[name] for name in ("encoder_calls", "predictor_calls",
                                              "decoder_calls", "value_calls"))
        if row["model_calls"] != call_sum:
            raise ValueError("model-call total mismatch")
        if row["terminal_nodes"] > row["node_visits"]:
            raise ValueError("terminal node count exceeds visited nodes")
        if row.get("fallback_used") != (row["completed_depth"] < 4):
            raise ValueError("fallback state mismatch")
        if row.get("fallback_action_available") is not True:
            raise ValueError("no internal legal fallback action was retained")
    if receipt.get("guardrails") != {
        "training_data_opened": False,
        "outcome_labels_read": False,
        "optimizer_updates": 0,
        "trained_checkpoints_saved": 0,
        "game_scores_recorded": False,
        "selected_actions_or_values_recorded": False,
        "locked_final_access": False,
    }:
        raise ValueError("pilot guardrail receipt mismatch")
    warmups = receipt.get("warmups")
    expected_warmups = {f"{seed}:{arm}" for seed in INIT_SEEDS for arm in ARMS}
    if not isinstance(warmups, dict) or set(warmups) != expected_warmups:
        raise ValueError("warm-up roster mismatch")
    warmup_root_hash = records[0]["state_sha256"]
    warmup_fields = {
        "initialization_seed", "arm", "encoder_calls", "predictor_calls",
        "decoder_calls", "value_calls", "model_calls", "transition_calls",
        "wall_seconds", "warmup_root_state_sha256",
    }
    for key, warmup in warmups.items():
        if set(warmup) != warmup_fields:
            raise ValueError("warm-up fields differ from the frozen compute schema")
        if (warmup.get("warmup_root_state_sha256") != warmup_root_hash
                or warmup.get("arm") not in ARMS
                or warmup.get("initialization_seed") not in INIT_SEEDS):
            raise ValueError("warm-up root or model identity mismatch")
        if key != f"{warmup['initialization_seed']}:{warmup['arm']}":
            raise ValueError("warm-up key does not match its model identity")
        for field in ("encoder_calls", "predictor_calls", "decoder_calls",
                      "value_calls", "model_calls", "transition_calls"):
            if type(warmup.get(field)) is not int or warmup[field] < 0:
                raise ValueError("invalid warm-up call count")
        if warmup["model_calls"] != sum(warmup[field] for field in (
            "encoder_calls", "predictor_calls", "decoder_calls", "value_calls")):
            raise ValueError("warm-up model-call total mismatch")
        if not math.isfinite(warmup.get("wall_seconds", math.nan)):
            raise ValueError("nonfinite warm-up wall time")
        if warmup["wall_seconds"] < 0:
            raise ValueError("negative warm-up wall time")
    if (not math.isfinite(receipt["schedule_generation_seconds"])
            or receipt["schedule_generation_seconds"] < 0):
        raise ValueError("invalid schedule-generation wall time")
