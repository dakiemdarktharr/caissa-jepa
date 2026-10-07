"""No-update NumPy objective graph for the frozen V2.12 six-arm study.

This module consumes an already materialized trajectory minibatch and returns
losses and gradients. It deliberately contains no dataset loader, optimizer,
checkpoint writer, inference planner, or fitting loop. It does not authorize
training or imply an empirical result.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .games import ACTION_SIZE, FEATURE_SIZE

LATENT_SIZE = 32
HORIZONS = (1, 2, 4)
HORIZON_WEIGHTS = {1: 1.0, 2: 0.5, 4: 0.25}
ARMS = (
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
)
_JEPA_HORIZONS = {
    "multi-step-jepa": (1, 2, 4),
    "single-pair-jepa": (2,),
    "single-horizon-jepa": (1,),
}


@dataclass(frozen=True)
class V212Config:
    arm: str = "multi-step-jepa"
    seed: int = 17
    latent: int = LATENT_SIZE

    def __post_init__(self):
        if self.arm not in ARMS:
            raise ValueError("unknown V2.12 arm")
        if type(self.seed) is not int or self.latent != LATENT_SIZE:
            raise ValueError("V2.12 requires an integer seed and latent width 32")


def _finite_array(batch, key, shape, dtype=None):
    value = np.asarray(batch[key], dtype=dtype)
    if value.shape != shape:
        raise ValueError(f"{key} must have shape {shape}")
    if np.issubdtype(value.dtype, np.number) and not np.all(np.isfinite(value)):
        raise ValueError(f"{key} contains nonfinite values")
    return value


def preflight_batch(batch):
    """Validate one fixed trajectory minibatch and return its target masks.

    Required arrays are roots x, legal mask, root action/outcome, four actions
    and actors, exact future features/outcomes, transition-exists and
    transition-valid flags, target-exists and terminal flags. This is an
    in-memory structural check, not a trajectory generator or exact-rules
    validator.
    """
    if not isinstance(batch, dict):
        raise TypeError("batch must be a mapping")
    x = np.asarray(batch.get("x"), dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != FEATURE_SIZE or len(x) == 0:
        raise ValueError("x must be a nonempty [batch, 198] array")
    n = len(x)
    _finite_array(batch, "x", (n, FEATURE_SIZE), np.float64)
    legal = _finite_array(batch, "legal", (n, ACTION_SIZE), bool)
    policy = _finite_array(batch, "policy", (n,), np.int64)
    value = _finite_array(batch, "value", (n,), np.float64)
    actions = _finite_array(batch, "actions", (n, 4, ACTION_SIZE), np.float64)
    actors = _finite_array(batch, "actors", (n, 4), np.float64)
    future_x = _finite_array(batch, "future_x", (n, 4, FEATURE_SIZE), np.float64)
    future_value = _finite_array(batch, "future_value", (n, 4), np.float64)
    transition_exists = _finite_array(batch, "transition_exists", (n, 4), bool)
    transition_valid = _finite_array(batch, "transition_valid", (n, 4), bool)
    target_exists = _finite_array(batch, "target_exists", (n, 4), bool)
    terminal = _finite_array(batch, "terminal", (n, 4), bool)
    if np.any(~legal.any(axis=1)) or np.any(policy < 0) or np.any(policy >= ACTION_SIZE):
        raise ValueError("each root needs legal actions and an in-range policy action")
    if np.any(~legal[np.arange(n), policy]):
        raise ValueError("recorded root action is not legal")
    if np.any(~np.isin(value, (-1.0, 0.0, 1.0))) or np.any(~np.isin(future_value, (-1.0, 0.0, 1.0))):
        raise ValueError("outcome targets must be in {-1, 0, 1}")
    if np.any(transition_valid & ~transition_exists):
        raise ValueError("a nonexistent transition cannot be marked valid")
    invalid = transition_exists & ~transition_valid
    for row in range(n):
        terminal_steps = np.flatnonzero(terminal[row])
        if not len(terminal_steps):
            continue
        terminal_idx = int(terminal_steps[0])
        if not (transition_exists[row, terminal_idx] and target_exists[row, terminal_idx]):
            raise ValueError("terminal target must have an existing valid transition")
        if (transition_exists[row, terminal_idx + 1:].any()
                or target_exists[row, terminal_idx + 1:].any()):
            raise ValueError("trajectory cannot contain transitions or targets after terminal")
    if np.any(~np.isin(actors[transition_exists], (-1.0, 1.0))):
        raise ValueError("actor roles must alternate between -1 and +1")
    role_pairs = transition_exists[:, 1:] & transition_exists[:, :-1]
    if np.any((actors[:, 1:] != -actors[:, :-1]) & role_pairs):
        raise ValueError("actor roles must alternate on every transition")
    if (np.any((actions < 0.0) | (actions > 1.0))
            or np.any((actions != 0.0) & (actions != 1.0))
            or np.any(actions.sum(axis=2)[transition_exists] != 1.0)
            or np.any(actions.sum(axis=2)[~transition_exists] != 0.0)):
        raise ValueError("each recorded action must be a one-hot vector")

    valid = {}
    counts = {}
    for horizon in HORIZONS:
        idx = horizon - 1
        complete = (transition_exists[:, :horizon] & transition_valid[:, :horizon]).all(axis=1)
        present = target_exists[:, idx]
        terminal_by_horizon = terminal[:, :horizon].any(axis=1)
        valid[horizon] = complete & present & ~terminal_by_horizon
        terminal_confirmed = np.zeros(n, dtype=bool)
        for row in np.flatnonzero(terminal_by_horizon):
            terminal_idx = int(np.flatnonzero(terminal[row, :horizon])[0])
            terminal_confirmed[row] = (
                target_exists[row, terminal_idx]
                and transition_exists[row, :terminal_idx + 1].all()
                and transition_valid[row, :terminal_idx + 1].all())
        counts[horizon] = {
            "valid_nonterminal": int(valid[horizon].sum()),
            "terminal_masked": int(terminal_confirmed.sum()),
            "missing_or_truncated": int((~terminal_confirmed
                                          & ~invalid[:, :horizon].any(axis=1)
                                          & (~complete | ~present)).sum()),
            "invalid_transition": int(invalid[:, :horizon].sum()),
        }
    if (not invalid.any() and not any(mask.any() for mask in valid.values())):
        raise ValueError("minibatch has zero valid nonterminal targets")
    return {"valid": valid,
            "active": _active_prefix_masks(transition_exists, transition_valid,
                                           target_exists, terminal),
            "counts": counts}


def _active_prefix_masks(transition_exists, transition_valid, target_exists, terminal):
    """Rows on which predicting each next state is permitted by v05."""
    n = transition_exists.shape[0]
    active = {}
    prefix_ok = np.ones(n, dtype=bool)
    terminal_seen = np.zeros(n, dtype=bool)
    for step in range(4):
        prefix_ok &= transition_exists[:, step] & transition_valid[:, step]
        terminal_seen |= terminal[:, step]
        active[step + 1] = prefix_ok & target_exists[:, step] & ~terminal_seen
    return active


class V212Model:
    """One arm's stateless-forward, manual-backward objective graph."""

    def __init__(self, config=V212Config()):
        self.config = config
        rng = np.random.default_rng(config.seed)
        d = config.latent

        def weight(fan_in, fan_out):
            return rng.normal(0.0, np.sqrt(1.0 / fan_in), (fan_in, fan_out)).astype(np.float64)

        # Keep common tensors and RNG order identical for paired arm seeds.
        self.params = {
            "ew": weight(FEATURE_SIZE, d), "eb": np.zeros(d),
            "pw": weight(d, ACTION_SIZE), "pb": np.zeros(ACTION_SIZE),
            "vw": weight(d, 1), "vb": np.zeros(1),
        }
        if config.arm != "direct-leaf-value":
            self.params["fw"] = weight(d + ACTION_SIZE + 1 + 6, d)
            self.params["fb"] = np.zeros(d)
        if config.arm == "recursive-raw-state":
            self.params["dw"] = weight(d, FEATURE_SIZE)
            self.params["db"] = np.zeros(FEATURE_SIZE)
        self.target = ({key: self.params[key].copy() for key in ("ew", "eb")}
                       if config.arm in _JEPA_HORIZONS else {})

    def _encode(self, x, *, target=False):
        p = self.target if target else self.params
        return np.tanh(x @ p["ew"] + p["eb"])

    def _value(self, z):
        p = self.params
        return np.tanh(z @ p["vw"] + p["vb"])

    def _predictor_input(self, z, actions, actors, descriptors):
        return np.concatenate((z, actions, actors[:, None], descriptors), axis=1)

    def _regularize(self, z):
        """V2.8-pinned root variance/covariance losses and their gradients."""
        d, n = z.shape[1], len(z)
        centered = z - z.mean(axis=0, keepdims=True)
        std = np.sqrt(np.mean(centered ** 2, axis=0) + 1e-4)
        shortfall = np.maximum(0.0, 0.1 - std)
        variance = float(np.mean(shortfall ** 2))
        dz = -2.0 * shortfall[None, :] * centered / (d * n * std[None, :])
        covariance = centered.T @ centered / n
        offdiag = covariance - np.diag(np.diag(covariance))
        covariance_loss = float(np.sum(offdiag ** 2) / d)
        dz += 4.0 * centered @ offdiag / (n * d)
        return variance, covariance_loss, dz

    def loss_grad(self, batch):
        """Return objective metrics and gradients; never changes model weights."""
        preflight = preflight_batch(batch)
        if any(count["invalid_transition"] for count in preflight["counts"].values()):
            raise ValueError("fixed minibatch contains an invalid selected transition")
        if not any(mask.any() for mask in preflight["valid"].values()):
            raise ValueError("minibatch has zero valid nonterminal targets")
        if (self.config.arm == "direct-leaf-value"
                and not preflight["valid"][4].any()):
            raise ValueError("direct-leaf minibatch has no valid nonterminal four-ply leaf")
        p = self.params
        x = np.asarray(batch["x"], dtype=np.float64)
        n, d = len(x), self.config.latent
        legal = np.asarray(batch["legal"], dtype=bool)
        policy = np.asarray(batch["policy"], dtype=np.int64)
        z0 = self._encode(x)
        grad = {key: np.zeros_like(value) for key, value in p.items()}
        dz0 = np.zeros_like(z0)

        logits = z0 @ p["pw"] + p["pb"]
        masked_logits = np.where(legal, logits, -np.inf)
        shifted = masked_logits - np.max(masked_logits, axis=1, keepdims=True)
        exp_logits = np.exp(shifted)
        probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        policy_loss = float(np.mean(np.log(exp_logits.sum(axis=1)) - shifted[np.arange(n), policy]))
        dlogits = probs
        dlogits[np.arange(n), policy] -= 1.0
        dlogits /= n
        grad["pw"] += z0.T @ dlogits
        grad["pb"] += dlogits.sum(axis=0)
        dz0 += dlogits @ p["pw"].T

        root_value = self._value(z0)[:, 0]
        root_delta = root_value - np.asarray(batch["value"], dtype=np.float64)
        root_loss = float(np.mean(root_delta ** 2))
        droot = (2.0 / n) * root_delta[:, None] * (1.0 - root_value[:, None] ** 2)
        grad["vw"] += z0.T @ droot
        grad["vb"] += droot.sum(axis=0)
        dz0 += droot @ p["vw"].T

        variance_loss, covariance_loss, dreg = self._regularize(z0)
        dz0 += 0.1 * dreg
        total = policy_loss + root_loss + 0.1 * variance_loss + 0.01 * covariance_loss
        metrics = {
            "arm": self.config.arm, "policy_nll": policy_loss,
            "root_value_mse": root_loss, "variance_loss": 0.1 * variance_loss,
            "covariance_loss": 0.01 * covariance_loss,
            "valid_target_counts": preflight["counts"],
            "executed_predictor_calls": 0,
            "executed_decoder_reencoder_calls": 0,
            "ema_target_encoder_calls": 0,
        }

        # Cache each recurrent state and local Jacobian inputs. Gradients from
        # every selected horizon are accumulated, then backpropagated once.
        if self.config.arm == "direct-leaf-value":
            future_x = np.asarray(batch["future_x"], dtype=np.float64)
            valid = preflight["valid"][4]
            leaf_loss = 0.0
            if valid.any():
                leaf_x = future_x[valid, 3]
                leaf_z = self._encode(leaf_x)
                pred = self._value(leaf_z)[:, 0]
                labels = np.asarray(batch["future_value"], dtype=np.float64)[valid, 3]
                delta = pred - labels
                leaf_loss = float(np.mean(delta ** 2))
                dv = (2.0 / len(pred)) * delta[:, None] * (1.0 - pred[:, None] ** 2)
                grad["vw"] += leaf_z.T @ dv
                grad["vb"] += dv.sum(axis=0)
                dz = (dv @ p["vw"].T) * (1.0 - leaf_z ** 2)
                grad["ew"] += leaf_x.T @ dz
                grad["eb"] += dz.sum(axis=0)
            total += leaf_loss
            metrics["direct_leaf_value_mse"] = leaf_loss
            metrics["extra_leaf_encoder_calls"] = int(valid.sum())
        else:
            raw = self.config.arm == "recursive-raw-state"
            actions = np.asarray(batch["actions"], dtype=np.float64)
            actors = np.asarray(batch["actors"], dtype=np.float64)
            future_x = np.asarray(batch["future_x"], dtype=np.float64)
            future_value = np.asarray(batch["future_value"], dtype=np.float64)
            descriptors = x[:, 192:198]
            active_steps = preflight["active"]
            states = [z0] + [np.zeros((n, d), dtype=np.float64) for _ in range(4)]
            inputs = [None] * 4
            predicted_latents = [np.zeros((n, d), dtype=np.float64) for _ in range(4)]
            predicted_features = ([np.zeros((n, FEATURE_SIZE), dtype=np.float64)
                                   for _ in range(4)] if raw else None)
            active_indices = [np.flatnonzero(active_steps[h]) for h in range(1, 5)]
            for step, rows in enumerate(active_indices):
                if not len(rows):
                    continue
                inp = self._predictor_input(states[step][rows], actions[rows, step],
                                            actors[rows, step], descriptors[rows])
                pre = inp @ p["fw"] + p["fb"]
                pred_z = np.tanh(pre)
                inputs[step] = inp
                predicted_latents[step][rows] = pred_z
                if raw:
                    xhat = pred_z @ p["dw"] + p["db"]
                    states[step + 1][rows] = np.tanh(xhat @ p["ew"] + p["eb"])
                    predicted_features[step][rows] = xhat
                    metrics["executed_decoder_reencoder_calls"] += len(rows)
                else:
                    states[step + 1][rows] = pred_z
                metrics["executed_predictor_calls"] += len(rows)

            dstate = [np.zeros_like(z) for z in states]
            rollout_loss = 0.0
            outcome_loss = 0.0
            raw_loss = 0.0
            rollout_horizons = _JEPA_HORIZONS.get(self.config.arm, ())
            raw_feature_grads = ([np.zeros_like(future_x[:, step]) for step in range(4)]
                                 if raw else None)
            outcome_den = sum(HORIZON_WEIGHTS[h] * int(preflight["valid"][h].sum()) for h in HORIZONS)
            if outcome_den:
                for h in HORIZONS:
                    mask = preflight["valid"][h]
                    if not mask.any():
                        continue
                    weight = HORIZON_WEIGHTS[h]
                    scale = weight / outcome_den
                    pred_value = self._value(states[h][mask])[:, 0]
                    delta = pred_value - future_value[mask, h - 1]
                    outcome_loss += scale * float(np.sum(delta ** 2))
                    dv = 2.0 * scale * delta[:, None] * (1.0 - pred_value[:, None] ** 2)
                    grad["vw"] += states[h][mask].T @ dv
                    grad["vb"] += dv.sum(axis=0)
                    dstate[h][mask] += dv @ p["vw"].T

            # JEPA/raw losses use one pooled weighted-example denominator across enabled horizons.
            target_den = sum(HORIZON_WEIGHTS[h] * int(preflight["valid"][h].sum())
                             for h in (HORIZONS if raw else rollout_horizons))
            if target_den:
                # Accumulate direct objective values and per-state gradients.
                for horizon in (HORIZONS if raw else rollout_horizons):
                    mask = preflight["valid"][horizon]
                    if not mask.any():
                        continue
                    weight = HORIZON_WEIGHTS[horizon]
                    scale = weight / target_den
                    if raw:
                        xhat = predicted_features[horizon - 1][mask]
                        delta = xhat - future_x[mask, horizon - 1]
                        raw_loss += scale * float(np.sum(delta ** 2) / FEATURE_SIZE)
                        raw_feature_grads[horizon - 1][mask] += (
                            2.0 * scale / FEATURE_SIZE) * delta
                    else:
                        target = self._encode(future_x[mask, horizon - 1], target=True)
                        metrics["ema_target_encoder_calls"] += int(mask.sum())
                        delta = states[horizon][mask] - target
                        rollout_loss += scale * float(np.sum(delta ** 2) / d)
                        dstate[horizon][mask] += (2.0 * scale / d) * delta

            metrics["rollout_value_mse"] = outcome_loss
            metrics["latent_roll_loss"] = rollout_loss
            metrics["raw_state_loss"] = raw_loss
            total += outcome_loss + rollout_loss + raw_loss

            # Reverse the recurrent chain, including F -> D -> E for raw-state.
            for step in range(4, 0, -1):
                rows = active_indices[step - 1]
                if not len(rows):
                    continue
                if raw:
                    xhat = predicted_features[step - 1][rows]
                    pred_z = predicted_latents[step - 1][rows]
                    znext = states[step][rows]
                    de = dstate[step][rows] * (1.0 - znext ** 2)
                    dxhat = raw_feature_grads[step - 1][rows] + de @ p["ew"].T
                    grad["ew"] += xhat.T @ de
                    grad["eb"] += de.sum(axis=0)
                    grad["dw"] += pred_z.T @ dxhat
                    grad["db"] += dxhat.sum(axis=0)
                    dpre = (dxhat @ p["dw"].T) * (1.0 - pred_z ** 2)
                else:
                    dpre = dstate[step][rows] * (1.0 - states[step][rows] ** 2)
                grad["fw"] += inputs[step - 1].T @ dpre
                grad["fb"] += dpre.sum(axis=0)
                dstate[step - 1][rows] += dpre @ p["fw"][:d].T
            dz0 += dstate[0]

        enc_delta = dz0 * (1.0 - z0 ** 2)
        grad["ew"] += x.T @ enc_delta
        grad["eb"] += enc_delta.sum(axis=0)
        metrics["loss"] = float(total)
        metrics["gradient_norm"] = float(np.sqrt(sum(np.sum(g ** 2) for g in grad.values())))
        metrics["parameter_count"] = int(sum(v.size for v in p.values()))
        if not np.isfinite(total) or any(not np.all(np.isfinite(g)) for g in grad.values()):
            raise FloatingPointError("nonfinite V2.12 loss or gradient")
        return metrics, grad

    def parameter_counts(self):
        return {
            "online": int(sum(v.size for v in self.params.values())),
            "ema_target": int(sum(v.size for v in self.target.values())),
            "trainable": int(sum(v.size for v in self.params.values())),
        }
