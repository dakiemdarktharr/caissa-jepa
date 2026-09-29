"""Serial, non-reentrant replacement of exactly two frozen runtime bindings."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
from threading import Lock

from two_player_v25 import runtime as original_runtime
from .monitor import process_peak_rss

ROOT = Path(__file__).resolve().parents[1]
_ORIGINAL_SOURCE = original_runtime.runtime_source
_ORIGINAL_MONITOR = original_runtime.process_peak_rss
_LOCK = Lock()


def runtime_source():
    """Original source inventory plus all repair sources and the amendment."""
    result = _ORIGINAL_SOURCE()
    additions = {p.relative_to(ROOT).as_posix() for p in Path(__file__).parent.rglob('*.py')}
    additions.add('docs/V25_RUNTIME_AMENDMENT.md')
    for path in sorted(additions):
        if path in result:
            raise ValueError('Repair inventory overlaps frozen source: '+path)
        result[path] = hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    return dict(sorted(result.items()))


@contextmanager
def repaired_bindings():
    """Restore both original functions even on BaseException.

    This context is for a serial run or serial strict verification. Nested and
    overlapping contexts fail before changing globals. Unrecognized prior
    monkeypatches are rejected rather than silently restored over.
    """
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('V25 repair bindings are serial and non-reentrant')
    try:
        if (original_runtime.runtime_source is not _ORIGINAL_SOURCE
                or original_runtime.process_peak_rss is not _ORIGINAL_MONITOR):
            raise RuntimeError('Frozen runtime already has unexpected bindings')
        try:
            original_runtime.runtime_source = runtime_source
            original_runtime.process_peak_rss = process_peak_rss
            yield
        finally:
            original_runtime.runtime_source = _ORIGINAL_SOURCE
            original_runtime.process_peak_rss = _ORIGINAL_MONITOR
    finally:
        _LOCK.release()
