"""Fail-closed, deterministic V2.8 supervised-prototype training runtime.

The public entry point loads only the audited train split. The data manifest
must carry explicit training approval; this module does not set that flag.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

import numpy as np

from .v28_data import load_split
from .v28_development import load_development_split
from .v28_model import Config, METHOD_VERSION, Model, _model_code_sha256, build_batch


@dataclass(frozen=True)
class RunConfig:
    epochs: int = 1
    shuffle_seed: int = 701

    def __post_init__(self):
        if type(self.epochs) is not int or self.epochs < 1:
            raise ValueError("epochs must be a positive integer")
        if type(self.shuffle_seed) is not int or self.shuffle_seed < 0:
            raise ValueError("shuffle seed must be a nonnegative integer")


def _canonical_sha256(value) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _runtime_identity():
    root = Path(__file__).resolve().parents[1]
    lockfile = root / "requirements-research-lock.txt"
    if not lockfile.is_file():
        raise FileNotFoundError("research runtime lockfile is required for V2.8 training")
    return {"requirements_lock_sha256": hashlib.sha256(
                lockfile.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "numpy_version": np.__version__,
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine()}


def _train_epoch(model: Model, records, *, epoch_index: int, shuffle_seed: int):
    """Private unit-test primitive; production fitting enters through train_dataset."""
    if type(epoch_index) is not int or epoch_index < 0:
        raise ValueError("epoch index must be a nonnegative integer")
    if type(shuffle_seed) is not int or shuffle_seed < 0:
        raise ValueError("shuffle seed must be a nonnegative integer")
    if not records:
        raise ValueError("cannot train an empty record set")
    if any(record.get("split") != "train" for record in records):
        raise ValueError("trainer accepts train split records only")

    rng = np.random.default_rng(np.random.SeedSequence(
        [shuffle_seed, epoch_index, model.config.seed]))
    order = rng.permutation(len(records))
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    weighted = {}
    total_roots = 0
    branches = nonterminal_branches = terminal_observed = updates = 0
    for start in range(0, len(order), model.config.batch_size):
        indices = order[start:start + model.config.batch_size]
        batch_records = [records[int(index)] for index in indices]
        batch = build_batch(batch_records)
        metrics = model._update(batch)
        roots = len(batch_records)
        total_roots += roots
        updates += 1
        branches += int(metrics["branches"])
        nonterminal_branches += int(metrics["nonterminal_branches"])
        terminal_observed += int(metrics.get("observed_terminal_exact_count", 0))
        for key, value in metrics.items():
            if key in ("roots", "branches", "nonterminal_branches",
                       "observed_terminal_exact_count", "gradient_norm"):
                continue
            if type(value) not in (int, float) or not math.isfinite(value):
                raise FloatingPointError(f"nonfinite/non-scalar epoch metric: {key}")
            weighted[key] = weighted.get(key, 0.0) + float(value) * roots
    summary = {key: value / total_roots for key, value in sorted(weighted.items())}
    order_sha = hashlib.sha256(np.asarray(order, dtype=np.int64).tobytes()).hexdigest()
    summary.update({"epoch_index": epoch_index, "roots": total_roots,
                    "updates": updates, "branches": branches,
                    "nonterminal_branches": nonterminal_branches,
                    "observed_terminal_exact_count": terminal_observed,
                    "shuffle_seed": shuffle_seed,
                    "order_sha256": order_sha,
                    "metric_semantics": "root_weighted_pre_update_minibatch_train",
                    "wall_seconds": time.perf_counter() - started_wall,
                    "cpu_seconds": time.process_time() - started_cpu,
                    "last_gradient_norm": float(metrics["gradient_norm"])})
    if any(not math.isfinite(value) for value in summary.values()
           if isinstance(value, float)):
        raise FloatingPointError("nonfinite V2.8 epoch summary")
    return summary, [int(index) for index in order]


def train_dataset(dataset_dir, checkpoint_path, *, model_config=Config(),
                  run_config=RunConfig(), resume=False):
    """Train approved DEV data and checkpoint only at committed epoch boundaries.

    A fresh run refuses an existing checkpoint. Resume requires the exact same
    method, code, model config, dataset/audit fingerprints, split and run config.
    """
    dataset_dir = Path(dataset_dir)
    checkpoint_path = Path(checkpoint_path)
    # This loader rejects training_approved=false, failed audits, source changes,
    # locked-final data, and artifacts whose hashes no longer match.
    records, dataset_fingerprint = load_split(dataset_dir, "train")
    return _fit_records(dataset_dir, checkpoint_path, records, dataset_fingerprint,
                        model_config=model_config, run_config=run_config,
                        resume=resume, fit_scope="approved-training",
                        development_approval_sha256=None,
                        development_approval_path=None)


def train_development_dataset(dataset_dir, checkpoint_path, *, approval_path,
                              model_config=Config(), run_config=RunConfig(),
                              resume=False):
    """Fit the audited train split under a separately hashed dev-only grant."""
    dataset_dir = Path(dataset_dir)
    checkpoint_path = Path(checkpoint_path)
    records, dataset_fingerprint, approval_sha = load_development_split(
        dataset_dir, "train", approval_path)
    return _fit_records(dataset_dir, checkpoint_path, records, dataset_fingerprint,
                        model_config=model_config, run_config=run_config,
                        resume=resume, fit_scope="development-only",
                        development_approval_sha256=approval_sha,
                        development_approval_path=str(Path(approval_path).resolve()))


def _fit_records(dataset_dir, checkpoint_path, records, dataset_fingerprint, *,
                 model_config, run_config, resume, fit_scope,
                 development_approval_sha256, development_approval_path):
    checkpoint_path = Path(checkpoint_path)
    receipt_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".receipt.json")
    if type(resume) is not bool:
        raise ValueError("resume must be a boolean")
    if (checkpoint_path.exists() or receipt_path.exists()) and not resume:
        raise FileExistsError("fresh run refuses an existing checkpoint")
    if resume and not checkpoint_path.is_file():
        raise FileNotFoundError("resume requested but checkpoint does not exist")
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    dataset_sha = manifest["artifacts"]["records.jsonl"]["sha256"]
    audit_sha = _canonical_sha256(manifest["audit"])
    effective_run = {"method": METHOD_VERSION, "model": asdict(model_config),
                     "run": asdict(run_config),
                     "fit_scope": fit_scope,
                     "development_approval_sha256": development_approval_sha256,
                     "development_approval_path": development_approval_path,
                     "runtime": _runtime_identity(),
                     "dataset_fingerprint": dataset_fingerprint}
    identity = {"dataset_sha256": dataset_sha, "audit_sha256": audit_sha,
                "run_config_sha256": _canonical_sha256(effective_run),
                "split": "train"}

    if resume:
        model = Model.load(checkpoint_path, model_config, identity)
    else:
        model = Model(model_config)
    completed = model.training_state["completed_epochs"]
    if completed > run_config.epochs:
        raise ValueError("checkpoint has more epochs than the requested run")

    for epoch_index in range(completed, run_config.epochs):
        summary, _ = _train_epoch(model, records, epoch_index=epoch_index,
                                  shuffle_seed=run_config.shuffle_seed)
        next_state = {"completed_epochs": epoch_index + 1,
                      "history": model.training_state["history"] + [summary]}
        model.save(checkpoint_path, identity, training_state=next_state)
        model.training_state = next_state
        _write_receipt(receipt_path, _make_receipt(
            model, checkpoint_path, identity, dataset_fingerprint, dataset_sha,
            audit_sha, effective_run))
    receipt = _make_receipt(model, checkpoint_path, identity, dataset_fingerprint,
                            dataset_sha, audit_sha, effective_run)
    _write_receipt(receipt_path, receipt)
    return {"method": METHOD_VERSION, "variant": model_config.variant,
            "fit_scope": fit_scope,
            "development_approval_sha256": development_approval_sha256,
            "dataset_fingerprint": dataset_fingerprint,
            "dataset_sha256": dataset_sha, "audit_sha256": audit_sha,
            "run_config_sha256": identity["run_config_sha256"],
            "checkpoint": str(checkpoint_path), "step": model.step,
            "completed_epochs": model.training_state["completed_epochs"],
            "checkpoint_sha256": receipt["checkpoint_sha256"],
            "receipt": str(receipt_path), "history": model.training_state["history"]}


def _make_receipt(model, checkpoint_path, identity, dataset_fingerprint,
                  dataset_sha, audit_sha, effective_run):
    return {"schema": "caissa-jepa-v28-train-receipt-v1",
            "method": METHOD_VERSION, "variant": model.config.variant,
            "fit_scope": effective_run["fit_scope"],
            "development_approval_sha256": effective_run[
                "development_approval_sha256"],
            "dataset_fingerprint": dataset_fingerprint,
            "dataset_sha256": dataset_sha, "audit_sha256": audit_sha,
            "split": "train", "run_config_sha256": identity["run_config_sha256"],
            "effective_run": effective_run,
            "model_code_sha256": _model_code_sha256(),
            "trainer_code_sha256": hashlib.sha256(
                Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "checkpoint_sha256": hashlib.sha256(Path(checkpoint_path).read_bytes()).hexdigest(),
            "optimizer_step": model.step,
            "completed_epochs": model.training_state["completed_epochs"],
            "history": model.training_state["history"],
            "evaluation": None,
            "metric_semantics": (
                "root-weighted mean of per-minibatch training metrics measured "
                "immediately before each optimizer update; no held-out evaluation")}


def _write_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset")
    parser.add_argument("checkpoint")
    parser.add_argument("--variant", choices=("reply-jepa", "task-value-dynamics",
                                                "direct-leaf"), default="reply-jepa")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--latent", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--shuffle-seed", type=int, default=701)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--development-approval", type=Path,
                        help="fit only train split under a bound development-only approval")
    args = parser.parse_args()
    model_config = Config(variant=args.variant, seed=args.seed, latent=args.latent)
    run_config = RunConfig(epochs=args.epochs, shuffle_seed=args.shuffle_seed)
    if args.development_approval:
        result = train_development_dataset(
            args.dataset, args.checkpoint, approval_path=args.development_approval,
            model_config=model_config, run_config=run_config, resume=args.resume)
    else:
        result = train_dataset(args.dataset, args.checkpoint, model_config=model_config,
                               run_config=run_config, resume=args.resume)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
