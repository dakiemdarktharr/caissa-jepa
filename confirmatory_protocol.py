"""Fail-closed confirmatory contracts, separate from exploratory GUI matches."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import math
from contextlib import contextmanager
import numpy as np
from dataset_integrity import sha256_file

VERSION = 2
FAMILIES = ("representation", "policy-value", "same-search", "engine-strength")
CENSORED = {"MAX_PLIES", "TIMEOUT", "ILLEGAL_MOVE", "CANCELLED", "ERROR", "CENSORED"}


@contextmanager
def pinned_referee(config):
    from arena_research import UCIReferee
    if not all(config.get(k) for k in ("path", "sha256", "version", "options", "milliseconds")) or not config.get("independent"):
        raise ValueError("Independent referee configuration is incomplete")
    if not isinstance(config["milliseconds"], (int, float)) or config["milliseconds"] <= 0:
        raise ValueError("Referee time budget must be positive")
    path = Path(config["path"]).resolve(strict=True)
    if sha256_file(path) != config["sha256"]:
        raise ValueError("Referee binary checksum mismatch")
    engine = UCIReferee(path, milliseconds=config["milliseconds"], options=config["options"])
    try:
        if engine.name != config["version"] or engine.digest != config["sha256"]:
            raise ValueError("Live UCI referee version/hash does not match the pinned identity")
        yield engine
    finally:
        engine.close()


def protocol_manifest(family="same-search", final=False):
    from arena_protocol import OPENINGS, SUITE_HASH
    if family not in FAMILIES:
        raise ValueError("Unknown experiment family")
    return {"version": VERSION, "research_name": "MARS-JEPA Chess", "family": family,
            "final": final, "opening_suite_sha256": SUITE_HASH,
            "openings": [{"name": n, "uci": line} for n, line in OPENINGS[:100 if final else 50]],
            "opening_diversity_verified": False,
            "seeds": [20260903, 20260913, 20260923], "paired_colors": True,
            "search": {"algorithm": "mars-common-negamax-v1", "move_seconds": .25, "nodes": 1000, "threads": 1, "max_plies": 300, "overrun_tolerance_seconds": .05},
            "primary_metric": "paired_game_score", "secondary_correction": "Holm alpha=0.05",
            "confidence_interval": "fixed-sample opening-cluster bootstrap, all seeds kept together, 10000 resamples, seed=71",
            "stopping_rule": "all scheduled opening/seed/color pairs, no optional stopping or replacement",
            "failure_policy": "timeout/illegal/cancellation/max-ply/error are censored; any incomplete pair blocks confirmatory ranking",
            "referee": {}, "dataset_fingerprint": None, "split_fingerprint": None,
            "models": [], "ranking_ready": False}


def protocol_errors(protocol, verify_binary=True):
    errors = []
    if protocol.get("version") != VERSION or protocol.get("family") not in FAMILIES:
        errors.append("Unsupported protocol or experiment family")
    openings = protocol.get("openings", [])
    required = 100 if protocol.get("final") else 50
    if len(openings) < required or len({o.get("uci") for o in openings}) != len(openings):
        errors.append("Insufficient distinct opening positions")
    # Different move orders can reach identical boards: verify complete legal replay.
    from main import pgnparser, vitriengine, text_thanh_move
    boards = set()
    for opening in openings:
        engine = vitriengine(pgnparser().tao_snapshot_ban_dau(), .01)
        try:
            for uci in opening["uci"].split():
                move = text_thanh_move(uci, engine.turn)
                if move not in engine.lay_tat_ca_nuoc_di_hop_le(engine.turn):
                    raise ValueError("Illegal opening")
                engine.thuc_hien_nuoc_di(move)
            boards.add((tuple(engine.board), engine.turn, tuple(engine.castling_rights.items()), engine.en_passant_target))
        except (ValueError, KeyError, TypeError):
            errors.append("Illegal opening sequence")
    if len(boards) < required:
        errors.append("Insufficient unique legal opening boards")
    if not protocol.get("opening_diversity_verified"):
        errors.append("Opening diversity has not been independently reviewed")
    if len(set(protocol.get("seeds", []))) < 3 or not protocol.get("paired_colors"):
        errors.append("Three model seeds and swapped-color pairs are required")
    if protocol.get("primary_metric") != "paired_game_score":
        errors.append("Exactly one predeclared primary metric is required")
    if not protocol.get("dataset_fingerprint") or not protocol.get("split_fingerprint"):
        errors.append("Missing verified dataset/split fingerprint")
    search = protocol.get("search", {})
    if any(not isinstance(search.get(k), (float, int)) or search[k] <= 0 for k in ("move_seconds", "nodes", "threads", "max_plies")):
        errors.append("Fixed positive search/time/node budgets required")
    if search.get("algorithm") in (None, "must be pinned per experiment"):
        errors.append("Search algorithm is not pinned")
    referee = protocol.get("referee", {})
    if not all(referee.get(k) for k in ("path", "sha256", "version", "options", "milliseconds")) or not referee.get("independent"):
        errors.append("Independent referee binary/version/hash/options/time are not pinned")
    elif verify_binary:
        try:
            with pinned_referee(referee):
                pass
        except (OSError, ValueError, RuntimeError, TimeoutError) as error:
            errors.append("Referee verification failed: " + str(error))
    if protocol.get("dataset_path") and protocol.get("audit_path"):
        try:
            from research_dataset import verify_plan
            plan = verify_plan(protocol["dataset_path"], protocol["audit_path"])
            if plan["dataset_fingerprint"] != protocol.get("dataset_fingerprint") or sha256_file(protocol["audit_path"]) != protocol.get("split_fingerprint"):
                errors.append("Dataset/split fingerprint changed")
        except (OSError, ValueError, KeyError) as error:
            errors.append("Dataset audit invalid: " + str(error))
    else:
        errors.append("Live dataset and audit paths are required")
    models = protocol.get("models", [])
    if len(models) < 2 or any(not m.get("checkpoint_sha256") or not m.get("configuration_sha256") or
                               m.get("dataset_fingerprint") != protocol.get("dataset_fingerprint") for m in models):
        errors.append("Frozen matching model identities are required")
    for model in models:
        seed_checkpoints = model.get("seed_checkpoints", {})
        if set(seed_checkpoints) != {str(seed) for seed in protocol.get("seeds", [])}:
            errors.append("Every model requires a frozen checkpoint for each declared seed")
        for seed, checkpoint in seed_checkpoints.items():
            try:
                if sha256_file(checkpoint["path"]) != checkpoint["sha256"]:
                    errors.append("Model checkpoint changed")
                    continue
                from model_registry import spec_by_id, create_model, model_manifest
                spec = spec_by_id(Path.cwd(), model["registry_id"])
                loaded = create_model({**spec, "path": Path(checkpoint["path"])}, create_if_missing=False)
                config = model_manifest(spec, loaded)
                if loaded.seed != int(seed) or loaded.trained_steps <= 0 or loaded.dataset_fingerprint != protocol.get("dataset_fingerprint"):
                    errors.append("Model seed/training/data identity mismatch")
                if config["parameters"] != model.get("parameter_count") or config["configuration_sha256"] != checkpoint.get("configuration_sha256"):
                    errors.append("Actual checkpoint configuration/parameter count mismatch")
            except (OSError, ValueError, KeyError, TypeError):
                errors.append("Model seed checkpoint is unavailable or incompatible")
    if protocol.get("family") == "same-search" and (len({m.get("parameter_count") for m in models}) != 1 or any(not m.get("parameter_count") for m in models)):
        errors.append("Same-search comparison requires matched declared parameter counts")
    return errors


def gate(protocol):
    errors = protocol_errors(protocol)
    return {"ranking_ready": False, "protocol_ready": not errors, "errors": errors}


def holm_adjust(p_values):
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    result, previous = [0.0] * len(ordered), 0.0
    for rank, (index, value) in enumerate(ordered):
        if not 0 <= value <= 1:
            raise ValueError("Invalid p-value")
        previous = max(previous, min(1.0, (len(ordered) - rank) * value))
        result[index] = previous
    return result


def paired_interval(records, seed=71, repetitions=10000):
    clusters = defaultdict(list)
    pairs = defaultdict(list)
    for record in records:
        if record.get("reason") in CENSORED or record.get("cancelled") or record.get("error") or record.get("result") not in ("1-0", "0-1", "1/2-1/2"):
            continue
        pairs[(record["opening_id"], record["model_seed"])].append(record)
    for (opening, seed_id), pair in pairs.items():
        if len(pair) != 2 or {r["candidate_color"] for r in pair} != {"white", "black"}:
            continue
        scores = []
        for record in pair:
            white_score = {"1-0": 1., "0-1": 0., "1/2-1/2": .5}[record["result"]]
            scores.append(white_score if record["candidate_color"] == "white" else 1 - white_score)
        clusters[opening].append(float(np.mean(scores)))
    if not clusters:
        return {"score": None, "ci95": None, "complete_pairs": 0}
    values = np.array([np.mean(v) for v in clusters.values()])
    rng = np.random.default_rng(seed)
    sampled = values[rng.integers(len(values), size=(repetitions, len(values)))].mean(axis=1)
    bootstrap = np.quantile(sampled, [.025, .975])
    radius = math.sqrt(math.log(40) / (2 * len(values)))
    interval = [max(0., min(float(bootstrap[0]), float(values.mean())-radius)),
                min(1., max(float(bootstrap[1]), float(values.mean())+radius))]
    return {"score": float(values.mean()), "ci95": interval,
            "interval_scope": "fixed checkpoint seed cohort; opening-cluster bootstrap with conservative bounded-score envelope",
            "complete_pairs": sum(map(len, clusters.values())), "independent_openings": len(values)}


def confirmatory_result(protocol, records):
    errors = protocol_errors(protocol)
    expected = {(i, seed, color) for i in range(len(protocol.get("openings", []))) for seed in protocol.get("seeds", []) for color in ("white", "black")}
    observed = Counter((r.get("opening_id"), r.get("model_seed"), r.get("candidate_color")) for r in records)
    if set(observed) != expected or any(n != 1 for n in observed.values()):
        errors.append("Scheduled opening/seed/color pairs are incomplete or duplicated")
    if any(r.get("reason") in CENSORED or r.get("cancelled") or r.get("error") or r.get("result") not in ("1-0", "0-1", "1/2-1/2") for r in records):
        errors.append("Censored/error outcomes prevent a complete confirmatory result")
    protocol_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    if any(r.get("search_configuration") != protocol.get("search") or
           r.get("referee_sha256") != protocol.get("referee", {}).get("sha256") or
           r.get("dataset_fingerprint") != protocol.get("dataset_fingerprint") or
           not r.get("budget_enforcement_verified") for r in records):
        errors.append("Per-game search/referee/data identities or budget enforcement are missing")
    if any(r.get("protocol_sha256") != protocol_hash for r in records):
        errors.append("Game protocol identity mismatch")
    stats = paired_interval(records) if records and not errors else {"score": None, "ci95": None}
    return {**stats, "ranking_ready": not errors, "errors": errors, "protocol_sha256": protocol_hash}


def run_protocol(protocol, play_pair=None, stop_event=None):
    """Run a predeclared schedule through a measured paired-game adapter.

    The adapter must enforce protocol search/node/time limits and return complete
    measured game records. The exploratory GUI is deliberately not such an adapter.
    No unmeasured budget fields are filled in by this coordinator.
    """
    errors = protocol_errors(protocol)
    if errors:
        raise ValueError("Confirmatory run blocked: " + "; ".join(errors))
    if play_pair is None:
        from research_search import play_pair as measured_pair
        play_pair = lambda p, opening, seed: measured_pair(p, opening, seed, stop_event)
    records = []
    for opening_id, opening in enumerate(protocol["openings"]):
        for seed in protocol["seeds"]:
            if stop_event is not None and stop_event.is_set():
                return {"ranking_ready": False, "status": "CANCELLED", "records": records}
            pair = play_pair(protocol, opening_id, seed)
            if len(pair) != 2:
                raise ValueError("Paired game adapter must return both color outcomes, including errors")
            records.extend(pair)
    return {**confirmatory_result(protocol, records), "records": records}
