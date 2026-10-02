"""Train-split-only V2.11 grant and frozen protocol validation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import v28_data, v29_development

ROOT = Path(__file__).resolve().parents[1]
METHOD_PATH = ROOT / "docs" / "METHOD_V211_JEPA_WEIGHT_CALIBRATION.md"
SPEC_PATH = ROOT / "docs" / "validation" / "V211_JEPA_WEIGHT_CALIBRATION_V01.json"
DATASET_ROOT = (ROOT / "chess_data" / "v28_data_dev09").resolve()
V29_APPROVAL_PATH = ROOT / "chess_data" / "v29_data_dev09_approval.json"
APPROVAL_SCHEMA = "caissa-jepa-v211-development-fit-approval-v01"
PROTOCOL = "V211_JEPA_WEIGHT_CALIBRATION_V01"
SEEDS = (17, 29, 43, 59, 71, 83, 97, 109, 127, 139,
         151, 167, 181, 197, 211, 227, 241, 257, 271, 283)
MODEL_CONFIG = {"latent": 32, "learning_rate": 0.001, "ema": 0.99,
                "batch_size": 64, "jepa_weight": 8.0,
                "variance_weight": 0.1, "covariance_weight": 0.01,
                "target_std": 0.1}
RUN_CONFIG = {"epochs": 3, "shuffle_seed": 701, "updates_per_checkpoint": 87}
SCHEDULE_COMPARISONS = ("reply-jepa-lambda1-v29", "task-value-dynamics-v29",
                        "direct-leaf-v29")
SCHEDULE_SHA256 = "c6574b28767dc29e80c3bfd2ad158c58528561a8dc2c5393c86d54534f33bc2e"


def _sha(path: Path, *, normalize_text=False) -> str:
    raw = Path(path).read_bytes()
    if normalize_text:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def development_schedule() -> list[dict]:
    from tools.v28_match_power import make_schedule

    spec = validate_spec()
    schedule = make_schedule(
        comparisons=tuple(spec["schedule"]["comparisons"]),
        matches_per_checkpoint=spec["schedule"]["matches_per_checkpoint_game_control"],
        first_match_seed=spec["schedule"]["first_match_seed"],
        order_seed=spec["schedule"]["order_seed"])
    if (len(schedule) != spec["schedule"]["blocks"]
            or _canonical_sha(schedule) != SCHEDULE_SHA256
            or spec["schedule"]["schedule_sha256"] != SCHEDULE_SHA256):
        raise ValueError("V2.11 match schedule differs from frozen commitment")
    return schedule


def validate_spec() -> dict:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if (spec.get("schema") != "caissa-jepa-v211-development-panel-v01"
            or spec.get("status") !=
            "frozen pre-fit development specification pending independent review"
            or spec.get("protocol") != PROTOCOL
            or spec.get("games") != ["connect4-gravity-6x7", "reversi6"]
            or spec.get("dataset", {}).get("id") != "dev09-v1"
            or spec.get("dataset", {}).get("root") != "chess_data/v28_data_dev09"
            or spec.get("dataset", {}).get("fit_split") != "train"
            or spec.get("dataset", {}).get("forbidden_splits") !=
            ["validation", "selection", "locked-final"]
            or spec.get("dataset", {}).get("expected_training_approved_manifest") is not False
            or spec.get("dataset", {}).get("expected_identity") != v29_development.EXPECTED_DATA
            or spec.get("method") != "v28-supervised-reply-set-model-v02-prototype"
            or spec.get("checkpoint_seeds") != list(SEEDS)
            or spec.get("model_config") != MODEL_CONFIG
            or spec.get("run_config") != RUN_CONFIG
            or spec.get("controls") != list(SCHEDULE_COMPARISONS)
            or spec.get("schedule", {}).get("schedule_sha256") != SCHEDULE_SHA256
            or spec.get("schedule", {}).get("blocks") != 240
            or spec.get("schedule", {}).get("total_games") != 480
            or spec.get("schedule", {}).get("matches_per_checkpoint_game_control") != 2
            or spec.get("schedule", {}).get("first_match_seed") != 35_010_000
            or spec.get("schedule", {}).get("order_seed") != 28_110_000
            or spec.get("schedule", {}).get("comparisons") != list(SCHEDULE_COMPARISONS)
            or spec.get("planner", {}).get("per_move_wall_seconds") != 2.0
            or spec.get("planner", {}).get("transition_cap") != 500_000
            or spec.get("primary_development_screen", {}).get(
                "practical_margin") != 0.05):
        raise ValueError("V2.11 spec differs from frozen method constants")
    for relative, expected in spec["shared_source_sha256_lf_normalized"].items():
        if _sha(ROOT / relative, normalize_text=True) != expected:
            raise ValueError(f"shared source fingerprint changed: {relative}")
    baseline = spec["baseline_panel"]
    baseline_path = (ROOT / baseline["path"]).resolve()
    if ROOT.resolve() not in baseline_path.parents or _sha(baseline_path) != baseline["sha256"]:
        raise ValueError("completed V2.9 baseline fit ledger is absent or changed")
    if _sha(V29_APPROVAL_PATH) != spec["parent_v29_approval_sha256"]:
        raise ValueError("V2.9 development grant hash differs from frozen V2.11 spec")
    return spec


def _expected_data() -> dict:
    return dict(v29_development.EXPECTED_DATA)


def issue_approval(dataset_dir, output_path=None) -> dict:
    """Issue a distinct V2.11 train-only grant after the V2.9 audit is replayed."""
    spec = validate_spec()
    dataset_dir = Path(dataset_dir).resolve()
    if dataset_dir != DATASET_ROOT:
        raise ValueError("V2.11 grant is limited to audited DEV09")
    # The established loader replays the audited source and returns train records only.
    records, fingerprint, parent_approval_sha = v29_development.load_development_split(
        dataset_dir, "train", V29_APPROVAL_PATH)
    if (fingerprint != spec["dataset"]["expected_identity"]["dataset_fingerprint"]
            or not records or any(row.get("split") != "train" for row in records)):
        raise ValueError("DEV09 train-only replay does not match the frozen identity")
    output_path = (ROOT / "chess_data" / "v211_data_dev09_approval.json"
                   if output_path is None else Path(output_path).resolve())
    data_root = (ROOT / "chess_data").resolve()
    if data_root not in output_path.parents:
        raise ValueError("V2.11 approval must remain under ignored chess_data")
    if output_path.exists():
        raise FileExistsError("refusing to replace a prior V2.11 approval")
    approval = {
        "schema": APPROVAL_SCHEMA,
        "scope": "development-only",
        "protocol": PROTOCOL,
        "fit_split": "train",
        "forbidden_splits": ["validation", "selection", "locked-final"],
        "training_approved_manifest": False,
        "dataset": _expected_data(),
        "method_sha256": _sha(METHOD_PATH, normalize_text=True),
        "panel_spec_sha256": _sha(SPEC_PATH),
        "loader_sha256": _sha(Path(__file__), normalize_text=True),
        "parent_v29_approval_sha256": parent_approval_sha,
        "authorization_basis": "User's ongoing authorization for local V2 development; no production or confirmation scope.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp",
                                     dir=output_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(approval, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"path": str(output_path), "sha256": _sha(output_path),
            "records": len(records), "scope": approval["scope"]}


def load_train_split(dataset_dir, approval_path):
    """Validate the V2.11 grant and return only the audited train split."""
    validate_spec()
    dataset_dir = Path(dataset_dir).resolve()
    if dataset_dir != DATASET_ROOT:
        raise ValueError("V2.11 loader is limited to audited DEV09")
    approval_path = Path(approval_path).resolve()
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    _, _, parent_approval_sha = v29_development.load_development_split(
        dataset_dir, "train", V29_APPROVAL_PATH)
    expected = {
        "schema": APPROVAL_SCHEMA,
        "scope": "development-only",
        "protocol": PROTOCOL,
        "fit_split": "train",
        "forbidden_splits": ["validation", "selection", "locked-final"],
        "training_approved_manifest": False,
        "dataset": _expected_data(),
        "method_sha256": _sha(METHOD_PATH, normalize_text=True),
        "panel_spec_sha256": _sha(SPEC_PATH),
        "loader_sha256": _sha(Path(__file__), normalize_text=True),
        "parent_v29_approval_sha256": parent_approval_sha,
        "authorization_basis": "User's ongoing authorization for local V2 development; no production or confirmation scope.",
    }
    if approval != expected:
        raise ValueError("V2.11 data grant is stale or differs from frozen scope")
    records, fingerprint, _ = v29_development.load_development_split(
        dataset_dir, "train", V29_APPROVAL_PATH)
    return records, fingerprint, _sha(approval_path)
