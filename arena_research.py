"""Common referee evaluation, UCI transport and reproducible match statistics."""
from __future__ import annotations

import hashlib
import json
import math
import os
import queue
import subprocess
import threading
import time
from functools import lru_cache
from pathlib import Path


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=64)
def _cached_hash(path, size, modified):
    return file_sha256(path)


def cached_sha256(path):
    path = Path(path).resolve()
    stat = path.stat()
    return _cached_hash(str(path), stat.st_size, stat.st_mtime_ns)


def arena_signature(specs, database_path):
    paths = [s['path'] for s in specs if s.get('path')]
    config_dir = paths[0].parent if paths else Path(database_path).parent
    config = config_dir / 'arena_reference.json'
    paths.append(config)
    reference_path = os.environ.get('CAISSA_REFERENCE_ENGINE', '')
    if config.exists():
        try:
            reference_path = json.loads(config.read_text(encoding='utf-8')).get('path', reference_path)
        except (OSError, ValueError):
            pass
    if reference_path:
        paths.append(Path(reference_path))
    paths += [Path(database_path), Path(str(database_path) + '-wal')]
    return {str(p): [p.stat().st_size, p.stat().st_mtime_ns] for p in paths if p.exists()}


def parse_uci_info(line, turn):
    words = line.split()
    result = {}
    sign = 1 if turn == "white" else -1
    for key in ("depth", "seldepth", "nodes", "nps", "time"):
        if key in words:
            result[key] = int(words[words.index(key) + 1])
    if "score" in words:
        index = words.index("score")
        kind, value = words[index + 1:index + 3]
        if kind == "cp":
            result["cp_white"] = sign * int(value)
        elif kind == "mate":
            result["mate_white"] = sign * int(value)
        bound = "lowerbound" if "lowerbound" in words else "upperbound" if "upperbound" in words else "exact"
        if sign == -1:
            bound = {"lowerbound": "upperbound", "upperbound": "lowerbound"}.get(bound, bound)
        result["bound"] = bound
    if "wdl" in words:
        index = words.index("wdl")
        wdl = list(map(int, words[index + 1:index + 4]))
        if len(wdl) == 3 and sum(wdl) > 0 and min(wdl) >= 0:
            result["wdl_white"] = wdl if sign == 1 else wdl[::-1]
    if "pv" in words:
        result["pv"] = words[words.index("pv") + 1:]
    return result


class UCIReferee:
    """One pinned local engine, bounded reads, no shell, no contestant feedback."""
    def __init__(self, path, milliseconds=150, *, command=None):
        self.path = str(Path(path).resolve(strict=True))
        self.milliseconds = milliseconds
        self.lines = queue.Queue()
        self.name = Path(path).stem
        self.digest = file_sha256(path)
        self.process = subprocess.Popen(
            command or [self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.send("uci")
            for line in self.until("uciok", 8):
                if line.startswith("id name "):
                    self.name = line[8:]
            for command in ("setoption name Threads value 1", "setoption name Hash value 32",
                            "setoption name UCI_ShowWDL value true", "isready"):
                self.send(command)
            self.until("readyok", 8)
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                self.lines.put(line.strip())
        finally:
            self.lines.put(None)

    def send(self, command):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def until(self, token, timeout, stop_event=None):
        deadline = time.monotonic() + timeout
        received = []
        while time.monotonic() < deadline:
            if stop_event and stop_event.is_set():
                raise InterruptedError("Reference analysis cancelled")
            try:
                line = self.lines.get(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("Reference engine closed its output")
            received.append(line)
            if line.startswith(token):
                return received
        raise TimeoutError(f"Reference engine timeout waiting for {token}")

    def evaluate(self, moves, turn, stop_event=None):
        self.send("setoption name Clear Hash")
        self.send("position startpos" + (" moves " + " ".join(moves) if moves else ""))
        self.send(f"go movetime {self.milliseconds}")
        lines = self.until("bestmove", self.milliseconds / 1000 + 5, stop_event)
        result = {"source": self.name, "engine_sha256": self.digest, "budget_ms": self.milliseconds}
        for line in lines:
            words = line.split()
            principal = "multipv" not in words or words[words.index("multipv") + 1] == "1"
            if line.startswith("info ") and " score " in line and principal:
                parsed = parse_uci_info(line, turn)
                if "cp_white" in parsed or "mate_white" in parsed:
                    result.pop("cp_white", None)
                    result.pop("mate_white", None)
                    result.pop("wdl_white", None)
                    result.update(parsed)
        if "cp_white" not in result and "mate_white" not in result:
            raise RuntimeError("Reference engine returned no score")
        return result

    def close(self):
        if self.process.poll() is None:
            try:
                self.send("quit")
                self.process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()


class Referee:
    def __init__(self, project_dir):
        self.uci = None
        self.error = None
        config = Path(project_dir) / "chess_data/arena_reference.json"
        path = os.environ.get("CAISSA_REFERENCE_ENGINE", "")
        if config.exists():
            path = json.loads(config.read_text(encoding="utf-8")).get("path", path)
        if path:
            try:
                self.uci = UCIReferee(path)
            except Exception as error:
                self.error = str(error)

    def evaluate(self, snapshot, moves, stop_event):
        from main import vitriengine
        started = time.monotonic()
        engine = vitriengine(snapshot, 0.05, stop_event)
        legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        if not legal or engine.is_draw_search() or engine.halfmove_clock >= 100:
            white_score = 0.5
            if not legal and engine.is_king_in_check(engine.turn):
                white_score = 0.0 if engine.turn == "white" else 1.0
            return {"source": "Exact rules", "terminal": True, "expected_score_white": white_score,
                    "wdl_white": [1000, 0, 0] if white_score == 1 else [0, 0, 1000] if white_score == 0 else [0, 1000, 0],
                    "seconds": time.monotonic() - started}
        if self.uci:
            try:
                result = self.uci.evaluate(moves, engine.turn, stop_event)
                result["seconds"] = time.monotonic() - started
                return result
            except Exception as error:
                self.error = str(error)
                self.uci.close()
                self.uci = None
        result = engine.tim_nuoc_di_tot_nhat()
        return {"source": "Classical referee (uncalibrated)", "cp_white": result["score_white"] * 100,
                "depth": result["depth"], "nodes": result["nodes"], "bound": "search estimate",
                "seconds": time.monotonic() - started, "reference_error": self.error}

    def close(self):
        if self.uci:
            self.uci.close()


def evaluation_display(evaluation):
    """Return White fill and text; cp compression never labelled probability."""
    if not evaluation:
        return 0.5, "Pending"
    if "wdl_white" in evaluation:
        w, d, l = evaluation["wdl_white"]
        expected = (w + d / 2) / (w + d + l)
        return expected, f"White score {expected:.1%}"
    if "mate_white" in evaluation:
        mate = evaluation["mate_white"]
        return (1.0 if mate > 0 else 0.0), f"Mate {mate:+d}"
    cp = evaluation.get("cp_white")
    if cp is None:
        return 0.5, "Unavailable"
    return 0.5 + 0.5 * math.tanh(cp / 400), f"{cp / 100:+.2f} pawns"


def completed_records(history):
    unique = {}
    for index, item in enumerate(history):
        if item.get("result") not in ("1-0", "0-1", "1/2-1/2") or item.get("cancelled") or item.get("error") or item.get("reason") == "MAX_PLIES":
            continue
        key = (item.get("series_id"), item.get("match_seed"), item.get("white_model_id"), item.get("black_model_id"))
        if key[0] is None or key[1] is None:
            key = ("legacy", index)
        unique[key] = item
    return list(unique.values())


def matchup_statistics(history, first, second):
    records = [r for r in completed_records(history)
               if {r.get("white_model_id"), r.get("black_model_id")} == {first, second}]
    w = d = l = 0
    pairs = {}
    for r in records:
        score = 0.5 if r["result"] == "1/2-1/2" else float((r["result"] == "1-0") == (r["white_model_id"] == first))
        w += score == 1
        d += score == 0.5
        l += score == 0
        if r.get("series_id") and r.get("paired_colors"):
            key = (r["series_id"], r["match_seed"])
            pairs.setdefault(key, {})[r["white_model_id"]] = score
    complete_pairs = [sum(p.values()) / 2 for p in pairs.values() if len(p) == 2]
    n = len(records)
    score = (w + d * 0.5) / n if n else None
    elo = 400 * math.log10(score / (1 - score)) if score is not None and 0 < score < 1 else None
    # Hoeffding bound over independent opening pairs, valid for values in [0,1].
    # Fixed-sample descriptive bound, not sequential evidence or an SPRT.
    ci = None
    if complete_pairs:
        mean = sum(complete_pairs) / len(complete_pairs)
        epsilon = math.sqrt(math.log(40) / (2 * len(complete_pairs)))
        ci = [max(0, mean - epsilon), min(1, mean + epsilon)]
    return {"games": n, "wins": w, "draws": d, "losses": l, "score": score, "elo": elo,
            "pairs": len(complete_pairs), "score_ci95": ci, "ci_method": "pair Hoeffding; fixed sample"}
