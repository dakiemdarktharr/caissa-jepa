"""Build a resumable, FEN-centred chess dataset from public PGN archives.

This tool deliberately uses documented public downloads and behaves like a
polite bulk-data client: bounded retries, exponential backoff, Retry-After,
HTTP Range resume, checksums when supplied, and a persistent local manifest.
It does not bypass logins, CAPTCHAs, robots policies, or access controls.

The output is JSONL, one complete game per line.  Each game contains FEN
positions, UCI actions, action-response sequences and result labels from the
side-to-move perspective.  Keeping complete games together makes interrupted
writes recoverable without producing duplicate partial samples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Optional

from main import json_thanh_snapshot, pgnparser


SCHEMA_VERSION = 1
DEFAULT_TARGET_BYTES = 4 * 1024**3
DEFAULT_SHARD_BYTES = 256 * 1024**2
TWIC_ARCHIVE_PAGE = "https://theweekinchess.com/twic"
TWIC_ZIP_TEMPLATE = "https://theweekinchess.com/zips/twic{issue}g.zip"
USER_AGENT = "CAISSA-JEPA-v7-dataset-builder/1.0 (+research; respectful-bulk-download)"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_json_write(path: Path, payload: object, replace_attempts: int = 8) -> None:
    """Persist JSON without exposing a partial document to status readers.

    Windows may reject a rename for a brief moment while an antivirus scanner
    or a concurrent status reader still has the previous manifest open.  The
    content is already fsynced in the temporary file, so retrying the rename
    is safe and preserves the all-or-nothing manifest contract.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    for attempt in range(replace_attempts):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 == replace_attempts:
                raise
            time.sleep(min(0.05 * (2**attempt), 1.0))


def read_json_with_retry(path: Path, attempts: int = 8) -> dict:
    """Read a manifest while a Windows writer may briefly hold a file lock."""
    for attempt in range(attempts):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (PermissionError, json.JSONDecodeError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(0.05 * (2**attempt), 1.0))
    raise AssertionError("unreachable")


def parse_size_gb(value: float) -> int:
    if value <= 0:
        raise ValueError("Dung lượng mục tiêu phải lớn hơn 0")
    return int(value * 1024**3)


def parse_titles(value: str) -> set[str]:
    titles = {item.strip().upper() for item in value.split(",") if item.strip()}
    if not titles:
        raise ValueError("Cần ít nhất một title, ví dụ GM hoặc GM,WGM")
    return titles


def title_matches(value: str, allowed_titles: set[str]) -> bool:
    tokens = set(re.split(r"[^A-Za-z]+", value.upper()))
    return bool(tokens & allowed_titles)


def result_for_side(result: str, side: str) -> int:
    if result == "1-0":
        return 1 if side == "white" else -1
    if result == "0-1":
        return 1 if side == "black" else -1
    return 0


def snapshot_to_fen(snapshot: dict, fullmove_number: int) -> str:
    """Return a complete FEN while preserving the parser's rule semantics."""
    parser = pgnparser()
    fields = parser.snapshot_thanh_fen(snapshot).split()
    fields[-1] = str(snapshot.get("fullmove_number", max(1, fullmove_number)))
    return " ".join(fields)


def iter_pgn_games(handle: BinaryIO) -> Iterator[str]:
    """Stream PGN games without loading a full archive in memory."""
    current: list[str] = []
    saw_event = False

    for raw_line in handle:
        line = raw_line.decode("utf-8-sig", errors="replace")
        if line.lstrip().startswith('[Event "'):
            if current:
                yield "".join(current)
            current = [line]
            saw_event = True
        elif current:
            current.append(line)

    if current:
        yield "".join(current)
    elif not saw_event:
        return


@contextmanager
def open_pgn_members(path: Path) -> Iterator[Iterable[tuple[str, Iterator[str]]]]:
    """Yield named PGN streams from a plain PGN/TXT file or a ZIP archive."""
    suffix = path.suffix.lower()
    if suffix != ".zip":
        with path.open("rb") as handle:
            yield [(path.name, iter_pgn_games(handle))]
        return

    archive = zipfile.ZipFile(path)
    members = [
        member for member in archive.namelist()
        if member.lower().endswith((".pgn", ".txt"))
    ]
    if not members:
        archive.close()
        raise ValueError(f"{path} không chứa file PGN/TXT")

    def sources() -> Iterator[tuple[str, Iterator[str]]]:
        for member in members:
            handle = archive.open(member)
            try:
                yield member, iter_pgn_games(handle)
            finally:
                handle.close()

    try:
        yield sources()
    finally:
        archive.close()


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    bytes_written: int
    sha256: str
    etag: Optional[str]


class ResilientDownloader:
    """HTTP downloader with resume and rate-limit aware retry behaviour."""

    def __init__(
        self,
        timeout_seconds: float = 45.0,
        retries: int = 6,
        backoff_seconds: float = 2.0,
    ) -> None:
        self.timeout_seconds = max(5.0, float(timeout_seconds))
        self.retries = max(0, int(retries))
        self.backoff_seconds = max(0.25, float(backoff_seconds))

    def _wait_seconds(self, error: BaseException, attempt: int) -> float:
        retry_after = None
        if isinstance(error, urllib.error.HTTPError):
            retry_after = error.headers.get("Retry-After")
        if retry_after:
            try:
                return min(300.0, max(1.0, float(retry_after)))
            except ValueError:
                pass
        return min(120.0, self.backoff_seconds * (2**attempt))

    def download(
        self,
        url: str,
        destination: Path,
        expected_sha256: Optional[str] = None,
    ) -> DownloadResult:
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".part")

        if destination.exists():
            actual = self.file_sha256(destination)
            if expected_sha256 and actual.lower() != expected_sha256.lower():
                raise ValueError(f"Checksum không khớp cho file đã tồn tại: {destination}")
            return DownloadResult(destination, destination.stat().st_size, actual, None)

        for attempt in range(self.retries + 1):
            resume_from = partial.stat().st_size if partial.exists() else 0
            headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
            if resume_from:
                headers["Range"] = f"bytes={resume_from}-"
            request = urllib.request.Request(url, headers=headers)

            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    status = getattr(response, "status", response.getcode())
                    append = status == 206 and resume_from > 0
                    if status not in (200, 206):
                        raise urllib.error.HTTPError(url, status, "Unexpected status", response.headers, None)

                    mode = "ab" if append else "wb"
                    with partial.open(mode) as output:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            output.write(chunk)
                        output.flush()
                        os.fsync(output.fileno())

                    actual = self.file_sha256(partial)
                    if expected_sha256 and actual.lower() != expected_sha256.lower():
                        raise ValueError(f"Checksum không khớp: {url}")
                    partial.replace(destination)
                    return DownloadResult(
                        destination,
                        destination.stat().st_size,
                        actual,
                        response.headers.get("ETag"),
                    )
            except urllib.error.HTTPError as error:
                retriable = error.code in (408, 425, 429, 500, 502, 503, 504)
                if not retriable or attempt >= self.retries:
                    raise RuntimeError(f"Tải thất bại ({error.code}) {url}") from error
                wait = self._wait_seconds(error, attempt)
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                if attempt >= self.retries:
                    raise RuntimeError(f"Tải thất bại sau retry: {url}") from error
                wait = self._wait_seconds(error, attempt)

            print(f"Retry {attempt + 1}/{self.retries} sau {wait:.1f}s: {url}", file=sys.stderr)
            time.sleep(wait)

        raise AssertionError("unreachable")

    @staticmethod
    def file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()

    def read_text(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")


class DatasetState:
    """Idempotency state separate from the training data itself."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_games (
                game_hash TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                position_count INTEGER NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def is_processed(self, game_hash: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM processed_games WHERE game_hash = ?",
            (game_hash,),
        ).fetchone() is not None

    def mark_processed(self, game_hash: str, source_name: str, positions: int) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO processed_games(
                game_hash, source_name, position_count, completed_at
            ) VALUES (?, ?, ?, ?)
            """,
            (game_hash, source_name, positions, utc_now()),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


class ShardedDatasetWriter:
    """Atomic shard writer; unfinished game lines remain recoverable in .part."""

    def __init__(
        self,
        output_dir: Path,
        target_bytes: int,
        shard_bytes: int,
        allowed_titles: set[str],
    ) -> None:
        self.output_dir = output_dir
        self.shard_dir = output_dir / "shards"
        self.manifest_path = output_dir / "dataset_manifest.json"
        self.target_bytes = target_bytes
        self.shard_bytes = min(shard_bytes, target_bytes)
        self.allowed_titles = sorted(allowed_titles)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()
        self.current_shard = int(self.manifest.get("current_shard", 1))
        self.current_bytes = self._part_path().stat().st_size if self._part_path().exists() else 0
        self.total_bytes = int(self.manifest.get("written_bytes", 0))
        self.games = int(self.manifest.get("games", 0))
        self.positions = int(self.manifest.get("positions", 0))
        self.open_shard_games = int(self.manifest.get("open_shard_games", 0))
        self.open_shard_positions = int(self.manifest.get("open_shard_positions", 0))
        if self._needs_reconciliation():
            self._reconcile_from_disk()

    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            return read_json_with_retry(self.manifest_path)
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": utc_now(),
            "format": "JSONL; one fully self-contained game per line",
            "target_bytes": self.target_bytes,
            "shard_bytes": self.shard_bytes,
            "allowed_titles": self.allowed_titles,
            "written_bytes": 0,
            "games": 0,
            "positions": 0,
            "current_shard": 1,
            "shards": [],
            "sources": [],
        }

    def _part_path(self) -> Path:
        return self.shard_dir / f"fen_games_{self.current_shard:05d}.jsonl.part"

    def _final_path(self) -> Path:
        return self.shard_dir / f"fen_games_{self.current_shard:05d}.jsonl"

    @staticmethod
    def _shard_number(path: Path) -> int:
        matched = re.search(r"(\d{5})\.jsonl(?:\.part)?$", path.name)
        if not matched:
            raise ValueError(f"Tên shard không hợp lệ: {path.name}")
        return int(matched.group(1))

    @staticmethod
    def _count_complete_games(path: Path) -> tuple[int, int]:
        games = 0
        positions = 0
        with path.open("rb") as handle:
            for raw_line in handle:
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if row.get("game_hash") and isinstance(row.get("positions"), list):
                    games += 1
                    positions += len(row["positions"])
        return games, positions

    def _needs_reconciliation(self) -> bool:
        final_paths = sorted(self.shard_dir.glob("*.jsonl"))
        actual_final = [str(path.relative_to(self.output_dir)).replace("\\", "/") for path in final_paths]
        listed_final = [item.get("path") for item in self.manifest.get("shards", [])]
        if actual_final != listed_final:
            return True
        entries = self.manifest.get("shards", [])
        for field, shard_field, open_field in (("written_bytes", "bytes", "open_shard_bytes"),
                                               ("games", "games", "open_shard_games"),
                                               ("positions", "positions", "open_shard_positions")):
            if all(shard_field in item for item in entries):
                actual = sum(int(item[shard_field]) for item in entries) + int(self.manifest.get(open_field, 0))
                if self.manifest.get(field) != actual:
                    return True
        if any(path.stat().st_size != entry.get("bytes") for path, entry in zip(final_paths, entries)):
            return True
        part = self._part_path()
        stored_bytes = self.manifest.get("open_shard_bytes")
        if stored_bytes is None:
            return bool(final_paths or part.exists())
        return int(stored_bytes) != (part.stat().st_size if part.exists() else 0)

    def _reconcile_from_disk(self) -> None:
        """Repair counters after an interrupted manifest update.

        A game line is fsynced before the manifest is advanced.  Therefore a
        crash in that small interval leaves data that must be counted again,
        rather than silently undercounting the target or writing duplicates.
        This slower full scan is only used for legacy or inconsistent state.
        """
        final_paths = sorted(self.shard_dir.glob("*.jsonl"))
        part_paths = sorted(self.shard_dir.glob("*.jsonl.part"))
        self.manifest["shards"] = []
        self.total_bytes = 0
        self.games = 0
        self.positions = 0
        for path in final_paths:
            game_count, position_count = self._count_complete_games(path)
            self.total_bytes += path.stat().st_size
            self.games += game_count
            self.positions += position_count
            self.manifest["shards"].append({
                "path": str(path.relative_to(self.output_dir)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": ResilientDownloader.file_sha256(path),
                "games": game_count, "positions": position_count,
            })
        if part_paths:
            current = max(part_paths, key=self._shard_number)
            self.current_shard = self._shard_number(current)
            self.current_bytes = current.stat().st_size
            self.open_shard_games, self.open_shard_positions = self._count_complete_games(current)
            self.total_bytes += self.current_bytes
            self.games += self.open_shard_games
            self.positions += self.open_shard_positions
        else:
            self.current_shard = (max(map(self._shard_number, final_paths)) + 1) if final_paths else 1
            self.current_bytes = 0
            self.open_shard_games = 0
            self.open_shard_positions = 0

    def recover_part_games(self) -> Iterator[tuple[str, str, int]]:
        """Recover fully written game lines after a crash; ignore a truncated tail."""
        for partial in sorted(self.shard_dir.glob("*.jsonl.part")):
            with partial.open("rb") as handle:
                for raw_line in handle:
                    try:
                        row = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    game_hash = row.get("game_hash")
                    source_name = row.get("source", {}).get("name", "recovered")
                    position_count = len(row.get("positions", []))
                    if game_hash and position_count:
                        yield game_hash, source_name, position_count

    def _finalize_current_shard(self) -> None:
        partial = self._part_path()
        if not partial.exists() or partial.stat().st_size == 0:
            return
        final = self._final_path()
        partial.replace(final)
        self.manifest["shards"].append({
            "path": str(final.relative_to(self.output_dir)).replace("\\", "/"),
            "bytes": final.stat().st_size,
            "sha256": ResilientDownloader.file_sha256(final),
            "games": self.open_shard_games, "positions": self.open_shard_positions,
        })
        self.current_shard += 1
        self.current_bytes = 0
        self.open_shard_games = 0
        self.open_shard_positions = 0

    def register_source(self, source: dict) -> None:
        existing = {json.dumps(item, sort_keys=True) for item in self.manifest["sources"]}
        encoded = json.dumps(source, sort_keys=True)
        if encoded not in existing:
            self.manifest["sources"].append(source)

    def write_game(self, game: dict) -> bool:
        encoded = (
            json.dumps(game, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if len(encoded) > self.shard_bytes:
            raise ValueError("Một game vượt shard size; hãy tăng --shard-mb")
        if self.total_bytes + len(encoded) > self.target_bytes:
            return False
        if self.current_bytes and self.current_bytes + len(encoded) > self.shard_bytes:
            self._finalize_current_shard()

        with self._part_path().open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        self.current_bytes += len(encoded)
        self.total_bytes += len(encoded)
        self.games += 1
        self.positions += len(game["positions"])
        self.open_shard_games += 1
        self.open_shard_positions += len(game["positions"])
        self._save_manifest("IN_PROGRESS")
        return True

    def _save_manifest(self, status: str) -> None:
        if status == "TARGET_REACHED" and self.total_bytes < self.target_bytes:
            status = "COMPLETE"
        self.manifest.update({
            "schema_version": SCHEMA_VERSION,
            "updated_at": utc_now(),
            "status": status,
            "written_bytes": self.total_bytes,
            "games": self.games,
            "positions": self.positions,
            "current_shard": self.current_shard,
            "open_shard_bytes": self.current_bytes,
            "open_shard_games": self.open_shard_games,
            "open_shard_positions": self.open_shard_positions,
        })
        atomic_json_write(self.manifest_path, self.manifest)

    def close(self, status: str) -> None:
        self._finalize_current_shard()
        self._save_manifest(status)


class FenDatasetBuilder:
    def __init__(
        self,
        output_dir: Path,
        target_bytes: int,
        shard_bytes: int,
        allowed_titles: set[str],
        only_gm_actions: bool,
    ) -> None:
        self.parser = pgnparser()
        self.allowed_titles = allowed_titles
        self.only_gm_actions = only_gm_actions
        self.writer = ShardedDatasetWriter(
            output_dir, target_bytes, shard_bytes, allowed_titles
        )
        self.state = DatasetState(output_dir / "dataset_state.sqlite")
        for game_hash, source_name, positions in self.writer.recover_part_games():
            self.state.mark_processed(game_hash, source_name, positions)

    def close(self, status: str) -> None:
        from dataset_integrity import sha256_file
        ledger = self.writer.output_dir / "parser_quarantine.jsonl"
        if ledger.exists():
            self.writer.manifest["parser_quarantine_sha256"] = sha256_file(ledger)
        self.writer.close(status)
        self.state.close()

    def _game_payload(self, game_text: str, source: dict) -> Optional[dict]:
        self.last_skip_reason = None
        headers = self.parser.doc_headers(game_text)
        if headers.get("Variant", "Standard").casefold() not in ("standard", "chess"):
            self.last_skip_reason = "unsupported_variant"
            return None
        white_gm = title_matches(headers.get("WhiteTitle", ""), self.allowed_titles)
        black_gm = title_matches(headers.get("BlackTitle", ""), self.allowed_titles)
        if not (white_gm or black_gm):
            self.last_skip_reason = "no_eligible_player"
            return None

        parsed = self.parser.parse_game(game_text)
        records = parsed["records"]
        if not records:
            self.last_skip_reason = "empty_game"
            return None
        if parsed["result"] not in ("1-0", "0-1", "1/2-1/2"):
            self.last_skip_reason = "unfinished_result"
            return None

        digest = sha256_bytes(game_text.encode("utf-8"))
        positions = []
        for index, record in enumerate(records):
            actor_is_gm = white_gm if record["side"] == "white" else black_gm
            if self.only_gm_actions and not actor_is_gm:
                continue
            position = json_thanh_snapshot(record["position_json"])
            next_position = json_thanh_snapshot(record["next_position_json"])
            future2 = None
            future4 = None
            opponent_action = None
            next_our_action = None
            second_opponent_action = None
            if index + 1 < len(records):
                opponent_action = records[index + 1]["move_text"]
                future2 = snapshot_to_fen(
                    json_thanh_snapshot(records[index + 1]["next_position_json"]),
                    index // 2 + 2,
                )
            if index + 2 < len(records):
                next_our_action = records[index + 2]["move_text"]
            if index + 3 < len(records):
                second_opponent_action = records[index + 3]["move_text"]
                future4 = snapshot_to_fen(
                    json_thanh_snapshot(records[index + 3]["next_position_json"]),
                    index // 2 + 3,
                )
            positions.append({
                "ply": index,
                "fen": snapshot_to_fen(position, index // 2 + 1),
                "action_uci": record["move_text"],
                "next_fen": snapshot_to_fen(next_position, index // 2 + 1),
                "opponent_action_uci": opponent_action,
                "next_our_action_uci": next_our_action,
                "second_opponent_action_uci": second_opponent_action,
                "future2_fen": future2,
                "future4_fen": future4,
                "side_to_move": record["side"],
                "outcome_pov": result_for_side(parsed["result"], record["side"]),
                "actor_is_gm": actor_is_gm,
                "opening": record["is_opening"],
            })

        if not positions:
            return None
        return {
            "schema_version": SCHEMA_VERSION,
            "game_hash": digest,
            "initial_fen": snapshot_to_fen(json_thanh_snapshot(records[0]["position_json"]), 1),
            "canonical_moves": [r["move_text"].lower() for r in records],
            "source": source,
            "headers": {
                key: headers.get(key, "")
                for key in ("Event", "Site", "Date", "Round", "White", "Black", "WhiteTitle", "BlackTitle", "WhiteElo", "BlackElo", "Result")
            },
            "white_is_gm": white_gm,
            "black_is_gm": black_gm,
            "positions": positions,
        }

    def ingest_path(self, path: Path, source: dict) -> dict:
        stats = {"seen": 0, "accepted": 0, "skipped": 0, "duplicates": 0, "positions": 0, "full": False, "skip_reasons": {}}
        from dataset_integrity import sha256_file
        source = {**source, "sha256": sha256_file(path), "license": source.get("license", "UNKNOWN")}
        def quarantine(reason, text, member, detail=None):
            stats["skip_reasons"][reason] = stats["skip_reasons"].get(reason, 0) + 1
            entry = {"schema_version": 2, "reason": reason, "raw_pgn_sha256": sha256_bytes(text.encode()),
                     "source": member, "detail": detail}
            with (self.writer.output_dir / "parser_quarantine.jsonl").open("a", encoding="utf-8") as ledger:
                ledger.write(json.dumps(entry, sort_keys=True) + "\n")
        license_item = {"source_sha256": source["sha256"], "license": source["license"], "name": source.get("name")}
        metadata = self.writer.manifest.setdefault("license_metadata", [])
        if license_item not in metadata:
            metadata.append(license_item)
        self.writer.register_source(source)
        with open_pgn_members(path) as members:
            for member_name, games in members:
                member_source = dict(source)
                member_source["member"] = member_name
                for game_text in games:
                    stats["seen"] += 1
                    try:
                        payload = self._game_payload(game_text, member_source)
                    except Exception as error:
                        reason = "unsupported_move" if "@" in str(error) or "0000" in str(error) else "malformed_or_illegal_move"
                        quarantine(reason, game_text, member_source, str(error))
                        print(f"Parser rejected game: {error}", file=sys.stderr)
                        stats["skipped"] += 1
                        continue
                    if payload is None:
                        quarantine(self.last_skip_reason or "no_eligible_positions", game_text, member_source)
                        stats["skipped"] += 1
                        continue
                    if self.state.is_processed(payload["game_hash"]):
                        quarantine("duplicate_raw_game", game_text, member_source)
                        stats["duplicates"] += 1
                        continue
                    if not self.writer.write_game(payload):
                        stats["full"] = True
                        self.writer.manifest.setdefault("parser_runs", []).append(stats.copy())
                        return stats
                    self.state.mark_processed(
                        payload["game_hash"], source.get("name", path.name), len(payload["positions"])
                    )
                    stats["accepted"] += 1
                    stats["positions"] += len(payload["positions"])
        self.writer.manifest.setdefault("parser_runs", []).append(stats.copy())
        return stats


def find_latest_twic(downloader: ResilientDownloader) -> int:
    page = downloader.read_text(TWIC_ARCHIVE_PAGE)
    issues = [int(value) for value in re.findall(r"twic(\d+)g\.zip", page, re.IGNORECASE)]
    if not issues:
        raise RuntimeError("Không tìm thấy TWIC issue mới nhất")
    return max(issues)


def command_ingest(arguments: argparse.Namespace) -> int:
    builder = FenDatasetBuilder(
        Path(arguments.output),
        parse_size_gb(arguments.target_gb),
        int(arguments.shard_mb * 1024**2),
        parse_titles(arguments.titles),
        arguments.only_gm_actions,
    )
    status = "COMPLETE"
    try:
        for input_name in arguments.input:
            input_path = Path(input_name)
            source = {"name": arguments.source_name or input_path.name, "path": str(input_path.resolve())}
            stats = builder.ingest_path(input_path, source)
            print(json.dumps(stats, ensure_ascii=False))
            if stats["full"]:
                status = "TARGET_REACHED"
                break
    finally:
        builder.close(status)
    return 0


def command_crawl_twic(arguments: argparse.Namespace) -> int:
    output = Path(arguments.output)
    downloader = ResilientDownloader(arguments.timeout, arguments.retries, arguments.backoff)
    latest = arguments.latest if arguments.latest is not None else find_latest_twic(downloader)
    builder = FenDatasetBuilder(
        output,
        parse_size_gb(arguments.target_gb),
        int(arguments.shard_mb * 1024**2),
        parse_titles(arguments.titles),
        arguments.only_gm_actions,
    )
    download_dir = output / "downloads"
    status = "COMPLETE"
    try:
        for issue in range(latest, arguments.oldest - 1, -1):
            url = TWIC_ZIP_TEMPLATE.format(issue=issue)
            destination = download_dir / f"twic{issue}g.zip"
            try:
                result = downloader.download(url, destination)
            except RuntimeError as error:
                print(f"TWIC {issue}: {error}", file=sys.stderr)
                continue
            source = {
                "name": "TWIC",
                "issue": issue,
                "url": url,
                "download_sha256": result.sha256,
                "license_note": "Verify TWIC redistribution terms before publishing raw or derived data.",
            }
            stats = builder.ingest_path(destination, source)
            print(f"TWIC {issue}: " + json.dumps(stats, ensure_ascii=False))
            if stats["full"]:
                status = "TARGET_REACHED"
                break
            time.sleep(max(0.0, arguments.request_gap))
    finally:
        builder.close(status)
    return 0


def command_status(arguments: argparse.Namespace) -> int:
    manifest = Path(arguments.output) / "dataset_manifest.json"
    if not manifest.exists():
        print("Chưa có dataset manifest")
        return 1
    print(json.dumps(read_json_with_retry(manifest), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_verify(arguments: argparse.Namespace) -> int:
    root = Path(arguments.output)
    manifest_path = root / "dataset_manifest.json"
    manifest = read_json_with_retry(manifest_path)
    seen: set[str] = set()
    games = 0
    positions = 0
    byte_count = 0
    for shard in manifest.get("shards", []):
        path = root / shard["path"]
        if not path.exists():
            raise RuntimeError(f"Thiếu shard: {path}")
        actual_hash = ResilientDownloader.file_sha256(path)
        if actual_hash != shard["sha256"]:
            raise RuntimeError(f"Checksum shard không khớp: {path}")
        with path.open("rb") as handle:
            for raw_line in handle:
                row = json.loads(raw_line)
                game_hash = row["game_hash"]
                if game_hash in seen:
                    raise RuntimeError(f"Game trùng: {game_hash}")
                seen.add(game_hash)
                games += 1
                positions += len(row["positions"])
                byte_count += len(raw_line)
    if games != manifest.get("games") or positions != manifest.get("positions"):
        raise RuntimeError("Manifest count không khớp với shard")
    if byte_count != manifest.get("written_bytes"):
        raise RuntimeError("Manifest byte count không khớp với shard")
    print(json.dumps({"games": games, "positions": positions, "bytes": byte_count, "status": "OK"}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def shared(command: argparse.ArgumentParser) -> None:
        command.add_argument("--output", default="fen_dataset")
        command.add_argument("--target-gb", type=float, default=4.0)
        command.add_argument("--shard-mb", type=float, default=256.0)
        command.add_argument("--titles", default="GM", help="Ví dụ: GM hoặc GM,WGM")
        command.add_argument("--only-gm-actions", action="store_true")

    ingest = subparsers.add_parser("ingest", help="Chuẩn hoá PGN/ZIP có sẵn thành FEN dataset")
    shared(ingest)
    ingest.add_argument("--input", nargs="+", required=True)
    ingest.add_argument("--source-name", default=None)
    ingest.set_defaults(function=command_ingest)

    crawl = subparsers.add_parser("crawl-twic", help="Tải tuần tự TWIC với resume rồi chuẩn hoá FEN")
    shared(crawl)
    crawl.add_argument("--latest", type=int, default=None)
    crawl.add_argument("--oldest", type=int, default=1200)
    crawl.add_argument("--timeout", type=float, default=45.0)
    crawl.add_argument("--retries", type=int, default=6)
    crawl.add_argument("--backoff", type=float, default=2.0)
    crawl.add_argument("--request-gap", type=float, default=1.0)
    crawl.set_defaults(function=command_crawl_twic)

    status = subparsers.add_parser("status", help="Hiển thị dataset manifest")
    status.add_argument("--output", default="fen_dataset")
    status.set_defaults(function=command_status)

    verify = subparsers.add_parser("verify", help="Kiểm tra checksum/count/duplicate của shard đã hoàn tất")
    verify.add_argument("--output", default="fen_dataset")
    verify.set_defaults(function=command_verify)
    return parser


def main() -> int:
    # Windows consoles can still default to cp1252.  The CLI intentionally
    # contains Vietnamese diagnostics, so force a safe UTF-8 text stream when
    # the runtime supports reconfiguration.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    arguments = build_parser().parse_args()
    return arguments.function(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
