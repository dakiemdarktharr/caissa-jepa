"""Numerical checks and representation diagnostics; never experimental evidence."""
import copy
import os
import platform
import subprocess
import sys
import numpy as np
from model_registry import parameter_names


def loss_gradients(model, samples):
    clone = copy.deepcopy(model)
    gradients = {}
    clone._adam = lambda values, rate: gradients.update({k: v.copy() for k, v in values.items()})
    metrics = clone.train_batch(samples, 0.0)
    return metrics["loss"], gradients


def finite_difference_check(model, samples, epsilon=0.002, directions=2):
    _, gradients = loss_gradients(model, samples)
    rng = np.random.default_rng(71)
    checks = []
    for name in parameter_names(model):
        weights = getattr(model, name)
        gradient = gradients.get(name, np.zeros_like(weights))
        for index in range(directions):
            direction = rng.normal(size=weights.shape).astype(weights.dtype)
            # Include a coordinate where the analytic derivative is largest.
            if index == 0:
                direction.fill(0)
                direction.flat[int(np.argmax(np.abs(gradient)))] = 1
            else:
                direction /= max(1.0, np.linalg.norm(direction))
            losses = []
            for sign in (-1, 1):
                clone = copy.deepcopy(model)
                setattr(clone, name, weights + sign * epsilon * direction)
                losses.append(loss_gradients(clone, samples)[0])
            numerical = (losses[1] - losses[0]) / (2 * epsilon)
            analytic = float(np.sum(gradient * direction))
            error = abs(analytic - numerical)
            checks.append({"parameter": name, "direction": index, "analytic": analytic,
                           "numerical": numerical, "absolute_error": error,
                           "passed": bool(error <= .002 + .025 * max(abs(analytic), abs(numerical)))})
    return checks


def latent_diagnostics(latent, targets=None):
    latent = np.asarray(latent, dtype=np.float64)
    if latent.ndim != 2 or len(latent) < 1 or not np.all(np.isfinite(latent)):
        raise ValueError("Expected a nonempty finite matrix of latent states")
    centered = latent - latent.mean(axis=0)
    covariance = centered.T @ centered / max(1, len(latent) - 1)
    eigenvalues = np.maximum(0, np.linalg.eigvalsh(covariance))
    probabilities = eigenvalues / max(1e-30, eigenvalues.sum())
    rank = float(np.exp(-np.sum(probabilities[probabilities > 0] * np.log(probabilities[probabilities > 0])))) if eigenvalues.sum() else 0.0
    return {"samples": len(latent), "variance": latent.var(axis=0).tolist(),
            "covariance": covariance.tolist(), "effective_rank": rank,
            "latent_norm_mean": float(np.linalg.norm(latent, axis=1).mean()),
            "target_error": None if targets is None else float(np.mean((latent - np.asarray(targets)) ** 2))}


def seed_stability(reports):
    if len(reports) < 3 or len({r["seed"] for r in reports}) != len(reports):
        raise ValueError("Seed stability requires at least three distinct model seeds")
    values = np.asarray([r["metric"] for r in reports], dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Non-finite seed metric")
    return {"seeds": [r["seed"] for r in reports], "mean": float(values.mean()),
            "sample_std": float(values.std(ddof=1)), "min": float(values.min()), "max": float(values.max())}


def reproducibility_manifest(model_config, dataset_fingerprint, split_fingerprint, seeds, search, referee, metrics, stopping_rule):
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {"schema_version": 1, "research_name": "MARS-JEPA Chess", "git_commit": commit,
            "protocol_version": 2, "python": sys.version, "numpy": np.__version__,
            "os": platform.platform(), "cpu": platform.processor(), "gpu": "not used by NumPy trainer",
            "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
            "seeds": list(seeds), "dataset_fingerprint": dataset_fingerprint,
            "split_fingerprint": split_fingerprint, "model": model_config,
            "search": search, "referee": referee, "metric_definitions": metrics, "stopping_rule": stopping_rule}
