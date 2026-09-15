"""Common chess search and paired execution adapter for protocol version 2.

Budgets count explicit search-tree nodes, not neural matrix operations. Neural
work is charged to wall time. A late return beyond the declared tolerance is a
censored timeout; no such game can establish confirmatory ranking.
"""
import hashlib
import json
import math
import time
from main import pgnparser, vitriengine, text_thanh_move, move_thanh_text
from adversarial_jepa import snapshot_from_engine
from model_registry import spec_by_id, create_model
from pathlib import Path

ALGORITHM = "mars-common-negamax-v1"


class BudgetEnd(Exception):
    pass


def search_move(model, snapshot, config):
    start = time.perf_counter()
    deadline = start + config["move_seconds"]
    engine = vitriengine(snapshot, config["move_seconds"])
    legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
    if not legal:
        raise ValueError("Cannot search a terminal position")
    nodes = 0
    def check():
        if nodes >= config["nodes"] or time.perf_counter() >= deadline:
            raise BudgetEnd()
    # Every architecture gets the same root-ordering interface and exact search.
    # Forward-pass cost and internal JEPA response enumeration consume wall time.
    ordered = legal
    try:
        check()
        _, priors, _ = model.score_legal_moves(snapshot, legal)
        ordered = [legal[i] for i in sorted(range(len(legal)), key=lambda i: (-priors[i], i))]
        check()
    except BudgetEnd:
        pass
    best, completed_depth = ordered[0], 0
    def negamax(depth, alpha, beta):
        nonlocal nodes
        check(); nodes += 1
        moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        if not moves:
            return -1.0 if engine.is_king_in_check(engine.turn) else 0.0
        if engine.is_draw_search() or engine.halfmove_clock >= 100:
            return 0.0
        if depth == 0:
            value = float(model.danh_gia_snapshot(snapshot_from_engine(engine)))
            if not math.isfinite(value):
                raise ValueError("Non-finite model value")
            check_time = time.perf_counter()
            if check_time >= deadline:
                raise BudgetEnd()
            return value
        value = -math.inf
        for move in moves:
            undo = engine.thuc_hien_nuoc_di(move)
            try:
                score = -negamax(depth-1, -beta, -alpha)
            finally:
                engine.hoan_tac_nuoc_di(undo)
            value = max(value, score); alpha = max(alpha, score)
            if alpha >= beta:
                break
        return value
    for depth in range(1, config.get("depth_cap", 64)+1):
        candidate, value = best, -math.inf
        try:
            for move in ordered:
                undo = engine.thuc_hien_nuoc_di(move)
                try:
                    score = -negamax(depth-1, -math.inf, -value)
                finally:
                    engine.hoan_tac_nuoc_di(undo)
                if score > value:
                    value, candidate = score, move
            best, completed_depth = candidate, depth
        except BudgetEnd:
            break
    seconds = time.perf_counter() - start
    return best, {"nodes": nodes, "seconds": seconds, "completed_depth": completed_depth,
                  "timeout": seconds > config["move_seconds"] + config.get("overrun_tolerance_seconds", 0),
                  "node_budget": config["nodes"], "time_budget": config["move_seconds"]}


def play_pair(protocol, opening_id, seed, stop_event=None):
    from confirmatory_protocol import pinned_referee
    from dataset_integrity import sha256_file
    if protocol["family"] not in ("same-search", "engine-strength") or protocol["search"]["algorithm"] != ALGORITHM:
        raise ValueError("This paired adapter requires the common negamax search protocol")
    if len(protocol["models"]) != 2:
        raise ValueError("A paired comparison requires exactly two frozen models")
    models = []
    for item in protocol["models"]:
        spec = spec_by_id(Path.cwd(), item["registry_id"])
        if not spec:
            raise ValueError("Unregistered research model")
        checkpoint = item["seed_checkpoints"][str(seed)]
        if sha256_file(checkpoint["path"]) != checkpoint["sha256"]:
            raise ValueError("Checkpoint changed before paired execution")
        model = create_model({**spec, "path": Path(checkpoint["path"])}, create_if_missing=False)
        if model.seed != seed or model.dataset_fingerprint != protocol["dataset_fingerprint"] or model.trained_steps <= 0:
            raise ValueError("Checkpoint seed/data/training identity mismatch")
        models.append(model)
    records = []
    protocol_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    with pinned_referee(protocol["referee"]) as referee:
        for candidate_color in ("white", "black"):
            engine = vitriengine(pgnparser().tao_snapshot_ban_dau(), .01)
            engine.position_counts[engine.tao_key_position()] = 1
            moves = protocol["openings"][opening_id]["uci"].split()
            for uci in moves:
                engine.thuc_hien_nuoc_di(text_thanh_move(uci, engine.turn))
            result, reason = "*", "MAX_PLIES"
            telemetry = []
            try:
                for _ in range(protocol["search"]["max_plies"]):
                    if stop_event is not None and stop_event.is_set():
                        reason = "CANCELLED"
                        break
                    legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
                    if not legal:
                        result = ("0-1" if engine.turn == "white" else "1-0") if engine.is_king_in_check(engine.turn) else "1/2-1/2"
                        reason = "CHECKMATE" if result != "1/2-1/2" else "STALEMATE"
                        break
                    if engine.is_draw_search() or engine.halfmove_clock >= 100:
                        result, reason = "1/2-1/2", "RULE_DRAW"
                        break
                    model = models[0 if engine.turn == candidate_color else 1]
                    move, measured = search_move(model, snapshot_from_engine(engine), protocol["search"])
                    telemetry.append(measured)
                    if move not in legal:
                        reason = "ILLEGAL_MOVE"; break
                    if measured["timeout"] or measured["nodes"] > protocol["search"]["nodes"]:
                        reason = "TIMEOUT"; break
                    engine.thuc_hien_nuoc_di(move)
                    moves.append(move_thanh_text(move))
                    measured["uci"] = moves[-1]
                    measured["referee"] = referee.evaluate(moves, engine.turn, stop_event)
            except InterruptedError:
                reason = "CANCELLED"
            except Exception as error:
                reason = "ERROR"
                telemetry.append({"error": repr(error), "traceback": __import__("traceback").format_exc()})
            records.append({"opening_id": opening_id, "model_seed": seed, "candidate_color": candidate_color,
                            "result": result, "reason": reason, "move_records": telemetry,
                            "protocol_sha256": protocol_hash, "search_configuration": protocol["search"],
                            "referee_sha256": protocol["referee"]["sha256"],
                            "dataset_fingerprint": protocol["dataset_fingerprint"],
                            "budget_enforcement_verified": True})
    return records
