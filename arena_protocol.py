"""Frozen, paired opening suite and versioned research protocol identity."""
import hashlib
import json
from pathlib import Path

OPENINGS = (
    ("Ruy Lopez", "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5"),
    ("Italian", "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3 g8f6 d2d3 d7d6 e1g1 e8g8"),
    ("Sicilian Najdorf", "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6 f1e2 e7e5"),
    ("Queen's Gambit", "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7 e2e3 e8g8 g1f3 h7h6"),
    ("King's Indian", "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6 g1f3 e8g8 f1e2 e7e5"),
    ("English", "c2c4 e7e5 b1c3 g8f6 g1f3 b8c6 g2g3 f8b4 f1g2 e8g8 e1g1 e5e4"),
)
SUITE_HASH = hashlib.sha256(json.dumps(OPENINGS).encode()).hexdigest()


def opening_for(seed):
    name, line = OPENINGS[int(seed) % len(OPENINGS)]
    return name, line.split()


def build_identity(resource_root):
    root = Path(resource_root)
    manifest = root / "build_manifest.json"
    if manifest.exists():
        return hashlib.sha256(manifest.read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for file in sorted(root.glob("*.py")):
        if file.name.startswith("test_"):
            continue
        digest.update(file.name.encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()
