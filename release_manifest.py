"""Generate source provenance before packaging (never include user data)."""
import hashlib
import json
import platform
from pathlib import Path


def generate():
    root = Path(__file__).resolve().parent
    files = sorted(p for p in root.glob("*.py") if not p.name.startswith("test_"))
    payload = {"version": "7.1", "python": platform.python_version(),
               "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    target = root / "build" / "build_manifest.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    generate()
