"""Explicitly scoped development-only data authorization and loading."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import v28_data


APPROVAL_SCHEMA = "caissa-jepa-v29-development-fit-approval-v01"
PROTOCOL = "V29_THREE_EPOCH_DEVELOPMENT_AMENDMENT_01"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = PROJECT_ROOT / "docs" / "V29_THREE_EPOCH_DEVELOPMENT_AMENDMENT_01.md"
PANEL_SPEC = PROJECT_ROOT / "docs" / "validation" / "V29_DEV_FIT_PANEL_V01.json"
DATASET_ROOT = (PROJECT_ROOT / "chess_data" / "v28_data_dev09").resolve()
EXPECTED_DATA = {
    "manifest_sha256": "f8b2a9dd152840a30ab3e1250d17e1336ae265f774fdc05b8590098e4614146e",
    "source_sha256": "55ab1f05e83e837118385846e068aac32a25232a5aaa3b8a7dd244dd2a8c6dcc",
    "dataset_fingerprint": "cf1f408356058eae5224249010008c47a23a6d8f2a8c8530990388cc179b8c40",
    "audit_sha256": "8431a2c5f627518f1161b5f5a4789f02e3edcc6a3fd41de458a5acdf4c92ed2e",
    "records_sha256": "7955cbf753fcc2a0ae6507fa7e73570cba7635b1ee31ae7553463914e7fd5cf9",
    "trajectories_sha256": "3a8e5851ccdfd0a489881e679aac083512d10521dbb3c01b534793d8ffc92c29",
}
EXPECTED_PAIRING = (
    "same initialization seed, records, root expansion, minibatch order, "
    "optimizer updates, and planner across all three variants")
EXPECTED_MODEL_CONFIG = {
    "latent": 32, "learning_rate": 0.001, "ema": 0.99,
    "batch_size": 64, "jepa_weight": 1.0, "variance_weight": 0.1,
    "covariance_weight": 0.01, "target_std": 0.1}
EXPECTED_RUN_CONFIG = {"epochs": 3, "shuffle_seed": 701}
EXPECTED_SCHEDULE = {
    "command_mode": "--development", "matches_per_checkpoint": 2,
    "first_match_seed": 35000000, "order_seed": 28094083,
    "block_count": 160,
    "schedule_sha256": "0cc972d755154f047d66c4abcc926c543a6020d1f5f55fb1ea6f9834294c0d46",
    "comparisons": ["task-value-dynamics", "direct-exact-leaf-value"],
    "color_assignments": [1, -1],
}
EXPECTED_INTERPRETATION = (
    "Bounded development/model-selection evidence only; never confirmatory.")
EXPECTED_GATES = {
    "fit_pass": ("All 60 fresh checkpoints have finite receipts, identical matched run/data identity, "
                 "exactly three completed epochs, and development-only scope."),
    "development_match_pass": ("Only after the complete three-epoch fit panel; replay all 160 paired "
                               "blocks and report each game/control, censor/forfeit count, "
                               "seed-cluster uncertainty, and measured training/search compute."),
    "superiority_claim": ("Never from this panel; requires a new, frozen, independently "
                          "reviewed confirmatory run on the unopened V08 schedule and "
                          "beating both controls at its meaningful margin."),
}
EXPECTED_P_HACKING_BOUNDARY = (
    "Only training duration changes from V2.8. Any later objective, architecture, data, or budget "
    "change requires a new pre-outcome versioned specification; do not inspect V08.")
EXPECTED_SELECTION_RULE = (
    "Nominate only if V2.9 JEPA-minus-task-value score is at least +0.05 on each game and the "
    "equal-weight macro; it improves at least +0.05 over V2.8 on each game; "
    "JEPA/task-value ratio of the hash-bound sum of per-fit wall seconds is at most 3.5; "
    "and mean planner CPU per game-seat for JEPA/task-value "
    "is at most 1.25 in each game. Otherwise stop duration-only tuning. Direct-exact-leaf is "
    "secondary; future confirmation must beat both non-JEPA controls at the meaningful margin. "
    "Nomination is exploratory, not superiority.")
_DEV09_REPLAY_CACHE: dict[tuple, tuple[list[dict], dict]] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha256_source(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _canonical_sha256(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _bound_data(manifest_path: Path, manifest: dict) -> dict:
    return {
        "manifest_sha256": _sha256(manifest_path),
        "source_sha256": manifest.get("source_sha256"),
        "dataset_fingerprint": manifest.get("audit", {}).get("dataset_fingerprint"),
        "audit_sha256": _canonical_sha256(manifest.get("audit")),
        "records_sha256": manifest.get("artifacts", {}).get(
            "records.jsonl", {}).get("sha256"),
        "trajectories_sha256": manifest.get("artifacts", {}).get(
            "trajectories.jsonl", {}).get("sha256"),
    }


def validate_development_spec() -> dict:
    """Validate every frozen field, not just the model hyperparameters."""
    spec = json.loads(PANEL_SPEC.read_text(encoding="utf-8"))
    expected_dataset = {
        "id": "dev09-v1", "root": "chess_data/v28_data_dev09",
        "fit_split": "train", "diagnostic_split": "validation",
        "selection_split": "selection", "locked_final_access": False,
        "expected_training_approved_manifest": False,
        "expected_identity": EXPECTED_DATA,
    }
    if (spec.get("schema") != "caissa-jepa-v29-development-panel-v01"
            or spec.get("status") != "pre-outcome development specification"
            or spec.get("amendment") != PROTOCOL
            or spec.get("dataset") != expected_dataset
            or spec.get("method") != "v28-supervised-reply-set-model-v02-prototype"
            or spec.get("variants") != ["reply-jepa", "task-value-dynamics", "direct-leaf"]
            or spec.get("checkpoint_seeds") != [17, 29, 43, 59, 71, 83, 97, 109,
                                                127, 139, 151, 167, 181, 197, 211,
                                                227, 241, 257, 271, 283]
            or spec.get("matched_model_config") != EXPECTED_MODEL_CONFIG
            or spec.get("matched_run_config") != EXPECTED_RUN_CONFIG
            or spec.get("pairing") != EXPECTED_PAIRING
            or spec.get("development_match_schedule") != EXPECTED_SCHEDULE
            or spec.get("interpretation") != EXPECTED_INTERPRETATION
            or spec.get("gates") != EXPECTED_GATES
            or spec.get("p_hacking_boundary") != EXPECTED_P_HACKING_BOUNDARY
            or spec.get("selection_rule") != EXPECTED_SELECTION_RULE):
        raise ValueError("development fit specification differs from the frozen panel")
    return spec


def development_schedule() -> list[dict]:
    """Return only the exact, hash-pinned exploratory match schedule."""
    from tools.v28_match_power import make_schedule

    spec = validate_development_spec()
    schedule_spec = spec["development_match_schedule"]
    rows = make_schedule(matches_per_checkpoint=2, first_match_seed=35000000,
                         order_seed=28094083)
    if (len(rows) != schedule_spec["block_count"]
            or _canonical_sha256(rows) != schedule_spec["schedule_sha256"]):
        raise ValueError("development match schedule differs from the frozen hash")
    return rows


def issue_development_approval(dataset_dir, output_path=None) -> dict:
    """Write the one prefit DEV09 grant without changing its source manifest."""
    expected_dataset = DATASET_ROOT
    dataset_dir = Path(dataset_dir).resolve()
    if dataset_dir != expected_dataset:
        raise ValueError("development grant issuer is limited to the audited DEV09 dataset")
    output_path = (PROJECT_ROOT / "chess_data" / "v29_data_dev09_approval.json"
                   if output_path is None else Path(output_path)).resolve()
    if PROJECT_ROOT / "chess_data" not in output_path.parents:
        raise ValueError("development approval must stay under ignored chess_data")
    if output_path.exists():
        raise FileExistsError("refusing to replace an existing development approval")
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != v28_data.DATA_VERSION
            or manifest.get("audit_passed") is not True
            or manifest.get("training_approved") is not False
            or manifest.get("source_sha256") != v28_data.source_hash()
            or manifest.get("policy_family_hashes") != v28_data._policy_family_hashes()
            or manifest.get("audit", {}).get("status") != "PASSED"):
        raise ValueError("DEV09 source, audit, or production-approval state is invalid")
    for name, identity in manifest.get("artifacts", {}).items():
        artifact_path = dataset_dir / name
        if (not artifact_path.is_file() or _sha256(artifact_path) != identity.get("sha256")
                or artifact_path.stat().st_size != identity.get("bytes")):
            raise ValueError("DEV09 artifact is missing or differs from its manifest")
    trajectory_rows = [json.loads(line) for line in
                       (dataset_dir / "trajectories.jsonl").read_text(
                           encoding="utf-8").splitlines()]
    model_records, actual_audit = v28_data.audit(trajectory_rows)
    if (actual_audit != manifest.get("audit")
            or v28_data.digest(model_records) != actual_audit.get("records_fingerprint")):
        raise ValueError("DEV09 full replay audit no longer matches its manifest")
    for split in ("train", "validation", "selection", "locked-final"):
        for game_name in v28_data.V28_GAMES:
            support = manifest["audit"].get("support", {}).get(f"{game_name}/{split}", {})
            if not support or type(support.get("records")) is not int:
                raise ValueError("DEV09 per-game/split support report is incomplete")
            if split == "locked-final" and support["records"] != 0:
                raise ValueError("development grant refuses nonempty locked-final data")
    panel = validate_development_spec()
    if _bound_data(manifest_path, manifest) != EXPECTED_DATA:
        raise ValueError("DEV09 data identity differs from the pinned development dataset")
    approval = {
        "schema": APPROVAL_SCHEMA,
        "scope": "development-only",
        "protocol": PROTOCOL,
        "authorization_basis": (
            "User instruction to continue V2 development; does not approve production or confirmation."),
        "fit_split": "train",
        "evaluation_splits": ["validation", "selection"],
        "training_approved_manifest": False,
        "dataset": _bound_data(manifest_path, manifest),
        "amendment_sha256": _sha256_source(AMENDMENT),
        "panel_spec_sha256": _sha256_source(PANEL_SPEC),
        "loader_sha256": _sha256_source(Path(__file__)),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output_path.name + ".", suffix=".tmp",
                                     dir=output_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(approval, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if output_path.exists():
            raise FileExistsError("refusing to replace an existing development approval")
        os.replace(temp_name, output_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return {"path": str(output_path), "sha256": _sha256(output_path),
            "scope": approval["scope"], "dataset": approval["dataset"]}


def load_development_split(dataset_dir, split, approval_path):
    """Read an audited non-final split under the exact development grant."""
    if split not in ("train", "validation", "selection"):
        raise ValueError("Development loader refuses locked-final/test data")
    root = Path(dataset_dir).resolve()
    if root != DATASET_ROOT:
        raise ValueError("development loader is limited to the exact audited DEV09 dataset")
    manifest_path = root / "manifest.json"
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    approval_path = Path(approval_path)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    expected = {
        "schema": APPROVAL_SCHEMA,
        "scope": "development-only",
        "protocol": PROTOCOL,
        "fit_split": "train",
        "evaluation_splits": ["validation", "selection"],
        "training_approved_manifest": False,
        "dataset": _bound_data(manifest_path, manifest),
        "amendment_sha256": _sha256_source(AMENDMENT),
        "panel_spec_sha256": _sha256_source(PANEL_SPEC),
        "loader_sha256": _sha256_source(Path(__file__)),
    }
    validate_development_spec()
    if any(approval.get(key) != value for key, value in expected.items()):
        raise ValueError("Development approval is missing, stale, or bound to different data")
    if expected["dataset"] != EXPECTED_DATA:
        raise ValueError("Development dataset differs from the pinned DEV09 identity")
    if split != "train" and split not in approval["evaluation_splits"]:
        raise ValueError("Development approval does not allow this evaluation split")
    if (manifest.get("schema") != v28_data.DATA_VERSION
            or manifest.get("audit_passed") is not True
            or manifest.get("training_approved") is not False
            or manifest.get("source_sha256") != v28_data.source_hash()
            or manifest.get("policy_family_hashes") != v28_data._policy_family_hashes()
            or "records.jsonl" not in manifest.get("artifacts", {})):
        raise ValueError("Development dataset failed source/approval identity checks")
    for name, identity in manifest["artifacts"].items():
        raw = (root / name).read_bytes()
        if (hashlib.sha256(raw).hexdigest() != identity.get("sha256")
                or len(raw) != identity.get("bytes")):
            raise ValueError("Development dataset artifact bytes changed")
    cache_key = (
        expected["dataset"]["manifest_sha256"],
        expected["dataset"]["source_sha256"],
        expected["dataset"]["records_sha256"],
        expected["dataset"]["trajectories_sha256"],
        expected["dataset"]["audit_sha256"],
        expected["loader_sha256"],
    )
    cached = _DEV09_REPLAY_CACHE.get(cache_key)
    if cached is None:
        trajectories = (root / "trajectories.jsonl").read_text(
            encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in trajectories]
        records, actual = v28_data.audit(rows)
    else:
        records, actual = cached
    if (actual != manifest.get("audit")
            or v28_data.digest(records) != actual.get("records_fingerprint")
            or actual.get("status") != "PASSED"):
        raise ValueError("Development dataset replay audit failed")
    if cached is None:
        _DEV09_REPLAY_CACHE[cache_key] = (records, actual)
    locked = [row for row in records if row.get("split") == "locked-final"]
    if locked:
        raise ValueError("Development loader refuses nonempty locked-final data")
    return ([row for row in records if row.get("split") == split],
            actual["dataset_fingerprint"], _sha256(approval_path))


def train_development_dataset(dataset_dir, checkpoint_path, *, approval_path,
                              model_config, run_config, resume=False):
    """Train using the V2.9 grant while sharing the audited V2.8 trainer."""
    from . import v28_train

    records, fingerprint, approval_sha = load_development_split(
        dataset_dir, "train", approval_path)
    return v28_train._fit_records(
        dataset_dir, checkpoint_path, records, fingerprint,
        model_config=model_config, run_config=run_config, resume=resume,
        fit_scope="development-only",
        development_approval_sha256=approval_sha,
        development_approval_path=str(Path(approval_path).resolve()))
