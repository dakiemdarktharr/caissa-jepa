"""Indexed arena summaries; JSONL and PGN remain portable full-fidelity exports."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class ArenaHistory:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY, digest TEXT UNIQUE NOT NULL,
                    series TEXT, white_id TEXT, black_id TEXT, summary TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS match_series ON matches(series,white_id,black_id);
                CREATE TABLE IF NOT EXISTS import_cursor (path TEXT PRIMARY KEY, offset INTEGER);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _insert(db, item):
        encoded = json.dumps(item, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        # Never retain per-move telemetry in the monitor's long-lived history.
        summary = {k: v for k, v in item.items() if k not in ("moves", "san_moves", "move_records")}
        db.execute("INSERT OR IGNORE INTO matches(digest,series,white_id,black_id,summary) VALUES(?,?,?,?,?)",
                   (digest, item.get("series_id"), item.get("white_model_id"), item.get("black_model_id"), json.dumps(summary)))

    def append(self, item):
        with self.connect() as db:
            self._insert(db, item)

    def import_jsonl(self, source):
        source = Path(source)
        if not source.exists():
            return
        with self.connect() as db, source.open("rb") as handle:
            key = str(source.resolve())
            previous = db.execute("SELECT offset FROM import_cursor WHERE path=?", (key,)).fetchone()
            offset = previous[0] if previous else 0
            if offset > source.stat().st_size:
                offset = 0
            handle.seek(offset)
            for line in handle:
                if not line.endswith(b"\n"):
                    break  # an interrupted append is not a committed record
                offset += len(line)
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        self._insert(db, item)
                except (ValueError, UnicodeDecodeError):
                    continue
            db.execute("INSERT OR REPLACE INTO import_cursor VALUES(?,?)", (key, offset))

    def __len__(self):
        with self.connect() as db:
            return db.execute("SELECT count(*) FROM matches").fetchone()[0]

    def __iter__(self):
        with self.connect() as db:
            limit = db.execute("SELECT coalesce(max(id),0) FROM matches").fetchone()[0]
        cursor = 0
        while cursor < limit:
            with self.connect() as db:
                rows = db.execute("SELECT id,summary FROM matches WHERE id>? AND id<=? ORDER BY id LIMIT 128",
                                  (cursor, limit)).fetchall()
            if not rows:
                return
            # No connection survives a yield, including partial consumption.
            for cursor, summary in rows:
                yield json.loads(summary)

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                return [self[i] for i in range(start, stop, step)]
            with self.connect() as db:
                return [json.loads(row[0]) for row in db.execute(
                    "SELECT summary FROM matches ORDER BY id LIMIT ? OFFSET ?", (max(0, stop-start), start))]
        if index < 0:
            index += len(self)
        with self.connect() as db:
            row = db.execute("SELECT summary FROM matches ORDER BY id LIMIT 1 OFFSET ?", (index,)).fetchone()
        if row is None:
            raise IndexError(index)
        return json.loads(row[0])
