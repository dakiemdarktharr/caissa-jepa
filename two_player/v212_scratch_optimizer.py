"""Pure one-step V2.12 optimizer arithmetic for compute-only dry runs.

This module has no model, data, trainer, checkpoint, or persistent state. It
returns new arrays and never mutates its inputs.
"""
from __future__ import annotations

import numpy as np

from .v212_model import ARMS, EMA_ARMS


LEARNING_RATE = 0.001
BETA1 = 0.9
BETA2 = 0.999
ADAM_EPSILON = 1e-8
GRADIENT_CLIP_NORM = 5.0
EMA_DECAY = 0.99
_EMA_KEYS = frozenset(("ew", "eb"))


def _copy_finite_group(group, label, expected_keys=None):
    if not isinstance(group, dict):
        raise TypeError(f"{label} must be a dict of arrays")
    if expected_keys is not None and set(group) != set(expected_keys):
        raise ValueError(f"{label} keys do not match parameters")
    copied = {}
    for key, value in group.items():
        array = np.asarray(value, dtype=np.float64)
        if not np.all(np.isfinite(array)):
            raise FloatingPointError(f"{label}[{key}] contains nonfinite values")
        copied[key] = array.copy()
    return copied


def scratch_adam_ema_step(arm, parameters, gradients, first_moment,
                          second_moment, step, target):
    """Compute one clipped Adam update and optional encoder EMA into new arrays.

    `arm` selects the frozen V2.12 variant. `step` is the one-based optimizer
    step. EMA arms require `target` to contain only `ew` and `eb`; all other
    arms require an empty target. No returned arrays alias or mutate inputs.
    """
    if arm not in ARMS:
        raise ValueError("arm is not a frozen V2.12 arm")
    if type(step) is not int or step < 1:
        raise ValueError("step must be a positive integer")
    params = _copy_finite_group(parameters, "parameters")
    keys = set(params)
    grads = _copy_finite_group(gradients, "gradients", keys)
    first = _copy_finite_group(first_moment, "first_moment", keys)
    second = _copy_finite_group(second_moment, "second_moment", keys)
    targets = _copy_finite_group(target, "target")
    expected_target_keys = _EMA_KEYS if arm in EMA_ARMS else frozenset()
    if set(targets) != expected_target_keys:
        raise ValueError("target keys do not match the frozen arm's EMA contract")

    for group_name, group in (("gradients", grads), ("first_moment", first),
                              ("second_moment", second), ("target", targets)):
        for key, value in group.items():
            if key not in params or value.shape != params[key].shape:
                raise ValueError(f"{group_name}[{key}] shape does not match parameter")
    if any(np.any(value < 0.0) for value in second.values()):
        raise ValueError("second_moment values must be nonnegative")

    gradient_norm = float(np.sqrt(sum(float(np.sum(value * value))
                                      for value in grads.values())))
    if not np.isfinite(gradient_norm):
        raise FloatingPointError("global gradient norm is nonfinite")
    clip_scale = (GRADIENT_CLIP_NORM / gradient_norm
                  if gradient_norm > GRADIENT_CLIP_NORM else 1.0)

    first_next, second_next, params_next = {}, {}, {}
    bias1 = 1.0 - BETA1 ** step
    bias2 = 1.0 - BETA2 ** step
    for key in params:
        clipped = grads[key] * clip_scale
        first_next[key] = BETA1 * first[key] + (1.0 - BETA1) * clipped
        second_next[key] = BETA2 * second[key] + (1.0 - BETA2) * clipped * clipped
        first_hat = first_next[key] / bias1
        second_hat = second_next[key] / bias2
        params_next[key] = (params[key] - LEARNING_RATE * first_hat
                            / (np.sqrt(second_hat) + ADAM_EPSILON))

    target_next = {
        key: EMA_DECAY * targets[key] + (1.0 - EMA_DECAY) * params_next[key]
        for key in targets
    }
    for group_name, group in (("parameters_next", params_next),
                              ("first_moment_next", first_next),
                              ("second_moment_next", second_next),
                              ("target_next", target_next)):
        if any(not np.all(np.isfinite(value)) for value in group.values()):
            raise FloatingPointError(f"{group_name} contains nonfinite values")

    return {
        "parameters": params_next,
        "first_moment": first_next,
        "second_moment": second_next,
        "target": target_next,
        "gradient_norm": gradient_norm,
        "clip_scale": float(clip_scale),
        "step": step,
    }
