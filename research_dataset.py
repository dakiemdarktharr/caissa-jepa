"""Version 2 research audit. No acquisition, training or implicit data discovery."""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime
import numpy as np
from dataset_integrity import inspect_dataset, sha256_file
from runtime_safety import atomic_json

AUDIT_VERSION = 2
SPLITS = ("train", "validation", "test")
FEN_FIELDS = ("fen", "next_fen", "future2_fen", "future4_fen")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def game_identity(game):
    positions = game["positions"]
    sequence = game.get("canonical_moves") or [p["action_uci"].lower() for p in positions]
    trajectory = digest([" ".join(game.get("initial_fen", positions[0]["fen"]).split()), sequence])
    headers = game.get("headers", {})
    provenance = {k: str(headers.get(k, "")).strip().casefold() for k in ("Event", "Site", "Date", "Round")}
    return digest([trajectory, provenance]), trajectory


def position_keys(position):
    # Ignore clocks for leakage detection; retain all six fields for legality.
    return {" ".join(position[f].split()[:4]) for f in FEN_FIELDS if position.get(f)}


def resolve_dataset(project, explicit=None):
    project = Path(project)
    location = project / "chess_data" / "dataset_location.json"
    if explicit is not None:
        candidate = Path(explicit)
    elif location.exists():
        value = json.loads(location.read_text(encoding="utf-8"))
        candidate = Path(value["path"])
        if not candidate.is_absolute():
            raise ValueError("Dataset location must be an absolute path; select a verified dataset")
    else:
        raise FileNotFoundError("No verified dataset selected. Select or download a verified dataset.")
    try:
        candidate = candidate.resolve(strict=True)
        if not candidate.is_dir() or not (candidate / "dataset_manifest.json").is_file():
            raise FileNotFoundError(str(candidate))
    except OSError as error:
        raise FileNotFoundError("No verified dataset available. Select or download a verified dataset. " + str(candidate)) from error
    return candidate


def checkpoint_compatibility(model, fingerprint):
    verified = bool(fingerprint and model.dataset_fingerprint and model.dataset_fingerprint == fingerprint)
    return {"compatible": verified, "status": "VERIFIED" if verified else "INCOMPATIBLE_OR_UNVERIFIED",
            "checkpoint_dataset_fingerprint": model.dataset_fingerprint,
            "current_dataset_fingerprint": fingerprint}


def audit_dataset(dataset):
    from adversarial_jepa import iter_dataset_games, sample_from_dataset_position
    root = Path(dataset).resolve(strict=True)
    receipt = inspect_dataset(root)
    def rows():
        return iter_dataset_games(root)
    errors = list(receipt["errors"])
    quarantine, reasons, duplicates = [], Counter(), Counter()
    games, groups, trajectories, canonical = {}, defaultdict(list), {}, {}
    group_dates = {}
    position_occurrences = Counter()
    unfinished = 0
    def reject(game, reason, index=None, detail=None):
        reasons[reason] += 1
        item = {"game_hash": game["game_hash"], "source": game.get("source", {}), "reason": reason}
        if index is not None:
            item["position_index"] = index
        if detail:
            item["detail"] = detail
        quarantine.append(item)
    for game in rows():
        key = game["game_hash"]
        if game.get("headers", {}).get("Result") not in ("1-0", "0-1", "1/2-1/2"):
            unfinished += 1
            reject(game, "unfinished_result")
            continue
        if not game.get("positions"):
            reject(game, "empty_game")
            continue
        try:
            identity, trajectory = game_identity(game)
        except (ValueError, KeyError, TypeError) as error:
            reject(game, "malformed_game", detail=str(error))
            continue
        if identity in canonical or trajectory in trajectories:
            duplicates["games"] += 1
            reject(game, "duplicate_normalized_move_sequence", detail=trajectories.get(trajectory, canonical.get(identity)))
            continue
        canonical[identity] = key
        trajectories[trajectory] = key
        headers = game.get("headers", {})
        event = tuple(str(headers.get(k, "")).strip().casefold() for k in ("Event", "Site")) + (str(headers.get("Date", ""))[:4],)
        date = str(headers.get("Date", ""))
        try:
            datetime.strptime(date, "%Y.%m.%d")
            valid_date = True
        except ValueError:
            valid_date = False
        if not event[0] or not valid_date:
            reject(game, "missing_event_provenance")
            continue
        valid = []
        for index, position in enumerate(game["positions"]):
            try:
                sample = sample_from_dataset_position(position, np.random.default_rng(0))
            except Exception as error:
                sample = None
            expected_outcome = {"1-0": 1, "0-1": -1, "1/2-1/2": 0}[game["headers"]["Result"]]
            if sample is not None:
                expected_outcome *= 1 if sample["state"]["turn"] == "white" else -1
                if sample["outcome"] != expected_outcome or position.get("side_to_move", sample["state"]["turn"]) != sample["state"]["turn"]:
                    sample = None
            if sample is None:
                reject(game, "invalid_complete_fen_transition_or_target", index)
                continue
            valid.append(index)
            position_occurrences.update(position_keys(position))
        if not valid:
            reject(game, "no_valid_positions")
            continue
        games[key] = {"indices": valid, "canonical_identity": identity}
        groups[event].append(key)
        group_dates[event] = max(group_dates.get(event, ""), date)
    # Assign complete event groups before removing position overlap. Never move a
    # held-out record into training to improve sample counts.
    ordered = sorted(groups, key=lambda e: (group_dates[e], e))
    assignments = {game["game_hash"]: "excluded" for game in rows()}
    for index, group in enumerate(ordered):
        fraction = index / max(1, len(ordered))
        split = "train" if fraction < .8 else "validation" if fraction < .9 else "test"
        for key in groups[group]:
            assignments[key] = split
    # Held-out ownership wins. Exclude whole training records if any context or
    # target overlaps another split. Also deduplicate repeated input positions.
    used, kept, per_split = {}, {}, Counter()
    input_seen = set()
    for split in reversed(SPLITS):
        for game in rows():
            key = game["game_hash"]
            if key not in games or assignments[key] != split:
                continue
            for index in games[key]["indices"]:
                position = game["positions"][index]
                keys = position_keys(position)
                if any(k in used and used[k] != split for k in keys):
                    reject(game, "cross_split_position_overlap", index)
                    continue
                input_key = " ".join(position["fen"].split()[:4])
                if input_key in input_seen:
                    duplicates["positions"] += 1
                    reject(game, "duplicate_input_position", index)
                    continue
                kept.setdefault(key, []).append(index)
                per_split[split] += 1
                input_seen.add(input_key)
                used.update({k: split for k in keys})
    manifest = json.loads((root / "dataset_manifest.json").read_text(encoding="utf-8"))
    parser_report = []
    parser_ledger = root / "parser_quarantine.jsonl"
    if parser_ledger.exists():
        if sha256_file(parser_ledger) != manifest.get("parser_quarantine_sha256"):
            errors.append("Parser quarantine checksum missing or changed")
        with parser_ledger.open(encoding="utf-8") as handle:
            parser_report = [json.loads(line) for line in handle]
    elif manifest.get("parser_quarantine_sha256"):
        errors.append("Parser quarantine ledger missing")
    licenses = manifest.get("license_metadata", [])
    if not licenses or any(not x.get("license") or x.get("license") == "UNKNOWN" or not x.get("source_sha256") for x in licenses):
        errors.append("Missing verified source hashes or license metadata")
    if unfinished:
        errors.append("Unfinished rows must be excluded in a new audited dataset")
    if reasons["invalid_complete_fen_transition_or_target"]:
        errors.append("Invalid transitions must be quarantined in a new audited dataset")
    for split in SPLITS:
        if not per_split[split]:
            errors.append("Empty disjoint split: " + split)
    source_manifest = receipt["manifest_sha256"]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = "UNAVAILABLE"
    code_hash = digest({name: sha256_file(Path(__file__).parent / name) for name in
                        ("research_dataset.py", "dataset_integrity.py", "adversarial_jepa.py", "fen_dataset_tool.py", "main.py")})
    plan = {"schema_version": AUDIT_VERSION, "research_name": "MARS-JEPA Chess",
            "dataset_manifest_sha256": source_manifest, "source_hashes": receipt["shards"],
            "actual": {**receipt["actual"], "unfinished_rows": unfinished},
            "code_commit": commit, "audit_code_sha256": code_hash, "license_metadata": licenses,
            "split_policy": "chronological event groups 80/10/10; held-out position ownership; no clock-based leakage evasion",
            "assignments": assignments, "included_position_indices": kept,
            "split_position_counts": dict(per_split), "locked_final_test": True,
            "cross_split_position_overlap": 0, "duplicate_counts": dict(duplicates),
            "position_occurrences_before_splitting": sum(position_occurrences.values()),
            "repeated_position_keys_before_splitting": sum(n > 1 for n in position_occurrences.values()),
            "skip_reason_counts": dict(reasons), "quarantine": quarantine,
            "parser_skip_reason_counts": dict(Counter(item["reason"] for item in parser_report)),
            "parser_quarantine": parser_report, "parser_runs": manifest.get("parser_runs", []),
            "history_policy": "Six FEN fields validated. Repetition history unavailable; model has no clocks/history features. Exact game referee owns draw rules.",
            "errors": errors, "status": "PASSED" if not errors else "FAILED"}
    if sha256_file(root / "dataset_manifest.json") != source_manifest:
        raise ValueError("Dataset manifest changed during research audit")
    if any(sha256_file(root / shard["path"]) != shard["sha256"] for shard in receipt["shards"]):
        raise ValueError("Dataset source changed during research audit")
    plan["dataset_fingerprint"] = digest(plan)
    return plan


def publish_audit(dataset, output):
    output = Path(output).resolve()
    root = Path(dataset).resolve(strict=True)
    if output == root or root in output.parents:
        raise ValueError("Audit output must be outside source dataset")
    plan = audit_dataset(root)
    atomic_json(output, plan)
    return plan


def verify_plan(dataset, plan_path):
    actual = audit_dataset(dataset)
    stored = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if actual != stored or actual["status"] != "PASSED":
        raise ValueError("Research audit/split fingerprint invalid or changed: " + "; ".join(actual["errors"][:5]))
    return actual


def verify_temporary_fixture(dataset, enabled):
    if not enabled:
        return False
    root = Path(dataset).resolve(strict=True)
    temporary = Path(tempfile.gettempdir()).resolve()
    if temporary not in root.parents:
        raise ValueError("Fixture-only training is restricted to a test-created temporary directory")
    return True
