"""Read-only training gate and explicitly versioned, deduplicated datasets."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from runtime_safety import atomic_json


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_dataset(dataset, check_duplicates=True, progress=None, allow_staging=False):
    root = Path(dataset).resolve(strict=True)
    manifest_path = root / "dataset_manifest.json"
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    totals = {"games": 0, "positions": 0, "written_bytes": 0}
    errors, shards, seen = [], [], set()
    listed = []
    for item in manifest.get("shards", []):
        path = (root / item["path"]).resolve(strict=True)
        if root not in path.parents or path in listed:
            raise ValueError("Duplicate or escaping shard path: " + item["path"])
        listed.append(path)
        digest = hashlib.sha256()
        games = positions = size = unfinished = 0
        with path.open("rb") as handle:
            for raw in handle:
                digest.update(raw)
                size += len(raw)
                if not raw.endswith(b"\n"):
                    errors.append("Unfinished JSONL row: " + str(path))
                row = json.loads(raw)
                unfinished += row.get("headers", {}).get("Result") not in ("1-0", "0-1", "1/2-1/2")
                key = row.get("game_hash")
                if not isinstance(key, str) or len(key) < 8 or not isinstance(row.get("positions"), list):
                    raise ValueError("Invalid game row: " + str(path))
                int(key[:8], 16)
                if check_duplicates and key in seen:
                    errors.append("Duplicate game hash: " + key)
                seen.add(key)
                games += 1
                positions += len(row["positions"])
        actual = {"path": item["path"], "games": games, "positions": positions,
                  "bytes": size, "sha256": digest.hexdigest(), "unfinished_rows": unfinished}
        for field in ("bytes", "sha256", "games", "positions", "unfinished_rows"):
            if field in ("bytes", "sha256") or field in item:
                if item.get(field) != actual[field]:
                    errors.append(f"Shard {item['path']} {field} mismatch")
        totals["games"] += games
        totals["positions"] += positions
        totals["written_bytes"] += size
        shards.append(actual)
        if progress:
            progress({"phase": "validating_dataset", "validated_shards": len(shards),
                      "validation_shards_total": len(manifest.get("shards", []))})
    if "unfinished_rows" in manifest and manifest["unfinished_rows"] != sum(s["unfinished_rows"] for s in shards):
        errors.append("Aggregate unfinished_rows mismatch")
    if not shards:
        errors.append("Dataset contains no shards")
    extras = [str(p) for p in (root / "shards").glob("*.jsonl") if p.resolve() not in listed]
    if extras or list((root / "shards").glob("*.part")):
        errors.append("Unlisted or unfinished shards")
    for key, value in totals.items():
        if manifest.get(key) != value:
            errors.append(f"Aggregate {key}: manifest={manifest.get(key)}, actual={value}")
    if manifest.get("shard_count", len(shards)) != len(shards):
        errors.append("Shard count mismatch")
    allowed_statuses = ("COMPLETE", "TARGET_REACHED", "DERIVING") if allow_staging else ("COMPLETE", "TARGET_REACHED")
    if manifest.get("status") not in allowed_statuses:
        errors.append("Dataset is not complete")
    if manifest.get("status") == "TARGET_REACHED" and totals["written_bytes"] < manifest.get("target_bytes", 0):
        errors.append("Target bytes have not been reached")
    provenance = manifest.get("provenance", {})
    if provenance.get("ledger_sha256") and sha256_file(root / "provenance.jsonl") != provenance["ledger_sha256"]:
        errors.append("Provenance ledger checksum mismatch")
    if manifest_path.read_bytes() != original:
        raise RuntimeError("Dataset manifest changed during validation")
    return {"version": 1, "dataset": str(root), "manifest_sha256": hashlib.sha256(original).hexdigest(),
            "actual": totals, "shard_count": len(shards), "shards": shards, "errors": errors,
            "status": "PASSED" if not errors else "FAILED",
            "scope": "All rows, aggregate counts, sizes, SHA-256 and game hashes; not legal replay"}


def validate_dataset(dataset, progress=None):
    receipt = inspect_dataset(dataset, progress=progress)
    if receipt["errors"]:
        raise ValueError("Dataset integrity failed; use a separately audited derived version. " + "; ".join(receipt["errors"][:8]))
    return receipt


def derive_dataset(source, destination):
    """Never edits the source. Publish manifest only after all output verifies."""
    source = Path(source).resolve(strict=True)
    destination = Path(destination).resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError("Derived dataset must be separate from raw data")
    # Fail instead of overwriting an existing version, including an interrupted one.
    destination.mkdir(parents=True, exist_ok=False)
    original = (source / "dataset_manifest.json").read_bytes()
    manifest = json.loads(original)
    (destination / "shards").mkdir()
    seen, entries = {}, []
    totals = {"games": 0, "positions": 0, "written_bytes": 0}
    excluded = 0
    with (destination / "provenance.jsonl").open("w", encoding="utf-8") as ledger:
        for index, item in enumerate(manifest["shards"], 1):
            path = (source / item["path"]).resolve(strict=True)
            if source not in path.parents:
                raise ValueError("Shard escapes raw root")
            target = destination / "shards" / f"fen_games_{index:05d}.jsonl"
            input_hash, output_hash = hashlib.sha256(), hashlib.sha256()
            input_bytes = games = positions = size = 0
            with path.open("rb") as src, target.open("xb") as out:
                for number, raw in enumerate(src, 1):
                    input_hash.update(raw)
                    input_bytes += len(raw)
                    row = json.loads(raw)
                    key = row["game_hash"]
                    content = dict(row)
                    content.pop("source", None)
                    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
                    location = {"shard": item["path"], "line": number}
                    if key in seen:
                        first, previous = seen[key]
                        if previous != digest:
                            raise ValueError("Conflicting duplicate game hash: " + key)
                        ledger.write(json.dumps({"action": "exclude_duplicate", "game_hash": key,
                                                 "source": location, "first": first}) + "\n")
                        excluded += 1
                        continue
                    if not isinstance(row.get("positions"), list):
                        raise ValueError("Invalid positions list")
                    seen[key] = (location, digest)
                    out.write(raw)
                    output_hash.update(raw)
                    size += len(raw)
                    games += 1
                    positions += len(row["positions"])
            if input_hash.hexdigest() != item["sha256"] or input_bytes != item["bytes"]:
                raise ValueError("Raw shard integrity mismatch: " + item["path"])
            entries.append({"path": target.relative_to(destination).as_posix(), "bytes": size,
                            "games": games, "positions": positions, "sha256": output_hash.hexdigest()})
            totals["games"] += games
            totals["positions"] += positions
            totals["written_bytes"] += size
            ledger.write(json.dumps({"action": "derive_shard", "source": item, "output": entries[-1]}) + "\n")
            print(json.dumps({"derived_shards": index, "excluded_rows": excluded}), flush=True)
    if (source / "dataset_manifest.json").read_bytes() != original:
        raise RuntimeError("Raw manifest changed during derivation")
    result = {**manifest, **totals, "status": "COMPLETE", "shards": entries, "shard_count": len(entries),
              "open_shard_bytes": 0, "open_shard_games": 0, "open_shard_positions": 0,
              "derived_version": 1, "provenance": {"source": str(source),
              "source_manifest_sha256": hashlib.sha256(original).hexdigest(), "excluded_duplicate_rows": excluded,
              "ledger_sha256": sha256_file(destination / "provenance.jsonl")}}
    # A staging manifest makes interrupted output ineligible for training.
    atomic_json(destination / "dataset_manifest.json", {**result, "status": "DERIVING"})
    receipt = inspect_dataset(destination, allow_staging=True)
    if receipt["errors"]:
        raise ValueError("Derived validation failed: " + "; ".join(receipt["errors"]))
    atomic_json(destination / "dataset_manifest.json", result)
    receipt["manifest_sha256"] = sha256_file(destination / "dataset_manifest.json")
    atomic_json(destination / "audit_receipt.json", receipt)
    return receipt
