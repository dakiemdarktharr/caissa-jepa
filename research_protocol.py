"""Versioned chess-only split plans and preregistered confirmation settings.

A generated plan is not evidence of model superiority or paper readiness.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from dataset_integrity import validate_dataset, sha256_file
from runtime_safety import atomic_json
from arena_protocol import OPENINGS, SUITE_HASH

SEEDS = (20260903, 20260913, 20260923)


def canonical_game_identity(game):
    # PGN comments, headers and source provenance do not change identity.
    # Include FEN transitions so a partial trajectory cannot alias a full game.
    trajectory = [(p.get("ply"), " ".join(p["fen"].split()[:4]), p["action_uci"],
                   " ".join(p["next_fen"].split()[:4])) for p in game["positions"]]
    return hashlib.sha256(json.dumps(trajectory, separators=(",", ":")).encode()).hexdigest()


def confirmation_protocol():
    from confirmatory_protocol import protocol_manifest
    return {**protocol_manifest(final=True), "ranking_allowed": False}


def build_split_plan(dataset, output):
    dataset, output = Path(dataset).resolve(strict=True), Path(output).resolve()
    if output == dataset or dataset in output.parents:
        raise ValueError("Research plan must be outside the dataset")
    output.mkdir(parents=True, exist_ok=False)
    receipt = validate_dataset(dataset)
    manifest = json.loads((dataset / "dataset_manifest.json").read_text(encoding="utf-8"))
    def rows():
        for shard in manifest["shards"]:
            with (dataset / shard["path"]).open("rb") as handle:
                for raw in handle:
                    yield json.loads(raw)
    groups, games, identities = defaultdict(list), {}, {}
    exclusions, canonical_duplicates = {}, []
    for game in rows():
        key = game["game_hash"]
        identity = canonical_game_identity(game)
        if identity in identities:
            exclusions[key] = "duplicate canonical trajectory"
            canonical_duplicates.append({"game_hash": key, "first": identities[identity], "identity": identity})
            continue
        identities[identity] = key
        headers = game.get("headers", {})
        date = headers.get("Date", "")
        event = headers.get("Event", "").strip()
        if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", date) or not event or event == "?":
            exclusions[key] = "missing temporal/event metadata"
            continue
        if headers.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
            exclusions[key] = "unfinished result"
            continue
        # Entire named event/site/year remains together, even across dates.
        group = (event.casefold(), headers.get("Site", "").strip().casefold(), date[:4])
        groups[group].append((date, key))
        games[key] = identity
    ordered = sorted(groups, key=lambda group: (max(date for date, _ in groups[group]), group))
    total = sum(len(groups[g]) for g in ordered)
    assignments, boundaries = {}, []
    count = 0
    for group in ordered:
        fraction = count / max(1, total)
        split = "train" if fraction < .8 else "validation" if fraction < .9 else "selection" if fraction < .95 else "test"
        for date, key in groups[group]:
            assignments[key] = split
        count += len(groups[group])
        boundaries.append({"event": group, "date_end": max(d for d, _ in groups[group]), "split": split, "games": len(groups[group])})
    assignments.update({key: "excluded" for key in exclusions})
    counts = dict(Counter(assignments.values()))
    # Disk-backed exact overlap audit keeps memory independent of position count.
    database = sqlite3.connect(str(output / "position_overlap.sqlite"))
    database.execute("CREATE TABLE positions (identity BLOB PRIMARY KEY, split_mask INTEGER, beyond_opening_mask INTEGER) WITHOUT ROWID")
    bits = {"train": 1, "validation": 2, "selection": 4, "test": 8}
    batch = []
    processed = 0
    for game in rows():
        split = assignments[game["game_hash"]]
        if split not in bits:
            continue
        bit = bits[split]
        for p in game["positions"]:
            # Include context and all prediction targets, not just input boards.
            for field in ("fen", "next_fen", "future2_fen", "future4_fen"):
                if p.get(field):
                    identity = hashlib.sha256(" ".join(p[field].split()[:4]).encode()).digest()
                    batch.append((identity, bit, bit if p.get("ply", 0) >= 12 else 0))
            processed += 1
            if len(batch) >= 20000:
                database.executemany("INSERT INTO positions VALUES (?,?,?) ON CONFLICT(identity) DO UPDATE SET split_mask=split_mask|excluded.split_mask, beyond_opening_mask=beyond_opening_mask|excluded.beyond_opening_mask", batch)
                database.commit()
                batch = []
        if processed and processed % 100000 < len(game["positions"]):
            print(json.dumps({"leakage_positions_processed": processed}), flush=True)
    if batch:
        database.executemany("INSERT INTO positions VALUES (?,?,?) ON CONFLICT(identity) DO UPDATE SET split_mask=split_mask|excluded.split_mask, beyond_opening_mask=beyond_opening_mask|excluded.beyond_opening_mask", batch)
    database.commit()
    overlaps = {}
    for a, abit in bits.items():
        for b, bbit in bits.items():
            if abit >= bbit:
                continue
            mask = abit | bbit
            overlaps[a + "/" + b] = {"all": database.execute("SELECT COUNT(*) FROM positions WHERE split_mask & ? = ?", (mask, mask)).fetchone()[0],
                                      "both_beyond_ply_12": database.execute("SELECT COUNT(*) FROM positions WHERE beyond_opening_mask & ? = ?", (mask, mask)).fetchone()[0]}
    database.close()
    plan = {"version": 1, "dataset_manifest_sha256": receipt["manifest_sha256"], "seed_policy": SEEDS,
            "split_policy": "Chronological event groups by latest date; approximate 80/10/5/5 game proportions",
            "assignments": assignments, "counts": counts, "event_groups": boundaries,
            "canonical_duplicate_count": len(canonical_duplicates), "canonical_duplicates": canonical_duplicates,
            "exclusions": exclusions, "position_overlap": overlaps,
            "position_identity": "SHA-256 of first four FEN fields; context and all prediction targets; en-passant field retained",
            "locked_final_test": True, "research_ready": False,
            "limitations": ["Observed position overlap must be addressed or disclosed before confirmatory claims", "Event groups may span dates; ordering by final date does not guarantee strict global temporal separation", "Canonical identity is observed full trajectory, not a legal replay proof", "No independent reference engine configured"]}
    if any(not counts.get(s) for s in bits):
        plan["limitations"].append("At least one required split is empty")
    atomic_json(output / "split_plan.json", plan)
    atomic_json(output / "experiment_manifest.json", {"protocol": confirmation_protocol(),
                "dataset_manifest_sha256": receipt["manifest_sha256"], "split_plan_sha256": sha256_file(output / "split_plan.json"),
                "status": "DESIGN_AND_AUDIT_ONLY", "checkpoint_hashes": {}, "measurements": []})
    return {"counts": counts, "canonical_duplicates": len(canonical_duplicates), "position_overlap": overlaps, "research_ready": False}
