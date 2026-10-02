"""No-update gradient decomposition for the V2.10 diagnostic protocol."""
from __future__ import annotations

from copy import copy
from dataclasses import replace
import hashlib
from pathlib import Path

import numpy as np

from .v28_model import Model


def load_weights_only(path, config, expected_sha256):
    """Load online/EMA weights without decoding checkpoint metadata/history."""
    path = Path(path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError("checkpoint artifact hash differs from the pinned ledger")
    model = Model(config)
    with np.load(path, allow_pickle=False) as archive:
        parameter_keys = {"p_" + key for key in model.params}
        target_keys = {"t_" + key for key in model.target}
        optimizer_keys = {"m_" + key for key in model.m} | {
            "v_" + key for key in model.v}
        if set(archive.files) != parameter_keys | target_keys | optimizer_keys | {"metadata"}:
            raise ValueError("checkpoint tensor inventory differs from the model")
        for prefix, group in (("p_", model.params), ("t_", model.target)):
            for key, template in group.items():
                value = archive[prefix + key]
                if (value.shape != template.shape or value.dtype != np.float64
                        or not np.all(np.isfinite(value))):
                    raise ValueError("invalid weights-only checkpoint tensor")
                group[key] = value.copy()
    return model

def decompose_reply_jepa_gradients(model, batch):
    """Separate task, regularizer, and reply-JEPA gradients on one snapshot."""
    if model.config.variant != "reply-jepa":
        raise ValueError("gradient decomposition requires reply-jepa")

    def evaluate(config):
        view = copy(model)
        view.config = config
        return view.loss_grad(batch)

    task_config = replace(model.config, variant="task-value-dynamics",
                          variance_weight=0.0, covariance_weight=0.0)
    regularized_config = replace(model.config, variant="task-value-dynamics")
    task_metrics, task = evaluate(task_config)
    regularized_metrics, task_and_regularizer = evaluate(regularized_config)
    total_metrics, total = model.loss_grad(batch)

    components = {
        "decision_task": task,
        "regularizer": {key: task_and_regularizer[key] - task[key]
                        for key in model.params},
        "reply_jepa": {key: total[key] - task_and_regularizer[key]
                       for key in model.params},
    }
    errors = []
    for key in model.params:
        summed = sum((part[key] for part in components.values()),
                     np.zeros_like(model.params[key]))
        scale = max(float(np.linalg.norm(total[key])), 1.0)
        errors.append(float(np.linalg.norm(summed - total[key]) / scale))
    metrics = {
        "decision_task_loss": float(task_metrics["policy_nll"]
                                     + task_metrics["root_value_mse"]
                                     + task_metrics["observed_leaf_value_mse"]),
        "regularizer_loss": float(regularized_metrics["variance_loss"]
                                  + regularized_metrics["covariance_loss"]),
        "reply_jepa_loss": float(total_metrics["reply_jepa_loss"]),
        "aggregate_loss": float(total_metrics["loss"]),
        "gradient_sum_relative_error": max(errors, default=0.0),
        "roots": int(total_metrics["roots"]),
        "branches": int(total_metrics["branches"]),
        "nonterminal_branches": int(total_metrics["nonterminal_branches"]),
    }
    if (not np.isfinite(metrics["gradient_sum_relative_error"])
            or any(not np.all(np.isfinite(value))
                   for part in components.values() for value in part.values())):
        raise FloatingPointError("nonfinite decomposed gradient")
    return metrics, components


def encoder_alignment(components, encoder_keys=("ew", "eb")):
    """Report cosine, dot product and norms over online-encoder parameters."""
    task = np.concatenate([components["decision_task"][key].reshape(-1)
                           for key in encoder_keys])
    jepa = np.concatenate([components["reply_jepa"][key].reshape(-1)
                           for key in encoder_keys])
    task_norm = float(np.linalg.norm(task))
    jepa_norm = float(np.linalg.norm(jepa))
    dot = float(np.dot(task, jepa))
    denominator = task_norm * jepa_norm
    cosine = None if denominator <= 1e-30 else dot / denominator
    return {"cosine": cosine, "dot": dot,
            "task_norm": task_norm, "jepa_norm": jepa_norm,
            "task_zero": task_norm <= 1e-30,
            "jepa_zero": jepa_norm <= 1e-30}
