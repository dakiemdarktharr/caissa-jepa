"""Shared NumPy model for the V2.8 reply-set JEPA and matched controls.

This module defines training/inference components only. It does not load a
dataset, authorize fitting, or claim that any arm outperforms another.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from .games import ACTION_SIZE, FEATURE_SIZE, State
from .v28_data import V28_GAMES

METHOD_VERSION = "v28-supervised-reply-set-model-v02-prototype"
VARIANTS = ("reply-jepa", "task-value-dynamics", "direct-leaf")
RULE_DESC_SIZE = 6
ACTION_PAIR_SIZE = 2 * ACTION_SIZE
_IDENTITY_KEYS = {"dataset_sha256", "audit_sha256", "split"}


@dataclass(frozen=True)
class Config:
    variant: str = "reply-jepa"
    seed: int = 17
    latent: int = 32
    learning_rate: float = 0.001
    ema: float = 0.99
    batch_size: int = 64
    jepa_weight: float = 1.0
    variance_weight: float = 0.1
    covariance_weight: float = 0.01
    target_std: float = 0.1

    def __post_init__(self):
        if self.variant not in VARIANTS or type(self.seed) is not int:
            raise ValueError("invalid V2.8 variant or seed")
        if self.latent < 2 or self.batch_size < 2:
            raise ValueError("latent width and batch size are too small")
        if not np.isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("learning rate must be finite and positive")
        if not 0 <= self.ema < 1:
            raise ValueError("EMA coefficient must be in [0, 1)")
        if (not np.isfinite(self.jepa_weight) or self.jepa_weight < 0
                or not np.isfinite(self.variance_weight) or self.variance_weight < 0
                or not np.isfinite(self.covariance_weight) or self.covariance_weight < 0
                or not np.isfinite(self.target_std) or self.target_std <= 0):
            raise ValueError("invalid objective weights or variance target")


def state_from(data):
    if isinstance(data, State):
        return data
    return State(tuple(data["board"]), data["player"])


def _one_hot(actions):
    result = np.zeros(ACTION_SIZE, dtype=np.float64)
    result[actions] = 1.0
    return result


def build_batch(records):
    """Expand each observed training root into every legal two-ply branch."""
    if not records:
        raise ValueError("empty V2.8 training batch")
    roots_x = []
    legal_masks = []
    policy_targets = []
    values = []
    branch_roots = []
    branch_actions = []
    branch_x = []
    branch_nonterminal = []
    observed_branch = np.full(len(records), -1, dtype=np.int64)
    for root_index, record in enumerate(records):
        if record.get("split") != "train":
            raise ValueError("training batch builder accepts train split records only")
        game_name = record.get("game")
        if game_name not in V28_GAMES:
            raise ValueError("unknown V2.8 game adapter")
        game = V28_GAMES[game_name]
        state = state_from(record["state"])
        game.validate(state)
        if game.terminal(state) is not None:
            raise ValueError("terminal state cannot be a training root")
        legal = tuple(game.legal_actions(state))
        action = record.get("action")
        value = record.get("value")
        if type(action) is not int or action not in legal:
            raise ValueError("observed policy action is illegal")
        if type(value) not in (int, float) or not np.isfinite(value) or value not in (-1, 0, 1):
            raise ValueError("invalid side-to-move outcome target")
        roots_x.append(game.features(state))
        legal_masks.append([candidate in legal for candidate in range(ACTION_SIZE)])
        policy_targets.append(action)
        values.append([value])
        observed_action = action
        observed_reply = record.get("reply")
        observed_leaf = state_from(record["future2"]) if record.get("future2") is not None else None
        if (observed_leaf is None) != (observed_reply is None):
            raise ValueError("observed reply and two-ply target must be present together")
        after_observed = game.transition(state, observed_action)
        if record.get("next") is not None:
            observed_next = state_from(record["next"])
            game.validate(observed_next)
            if observed_next != after_observed:
                raise ValueError("observed one-ply target disagrees with exact rules")
        if observed_leaf is not None:
            if game.terminal(after_observed) is not None:
                raise ValueError("two-ply target follows a terminal own action")
            game.validate(observed_leaf)
            if type(observed_reply) is not int:
                raise ValueError("observed opponent reply must be an integer action")
            if observed_reply not in game.legal_actions(after_observed):
                raise ValueError("observed opponent reply is illegal")
        for own_action in legal:
            after_own = game.transition(state, own_action)
            if game.terminal(after_own) is not None:
                continue
            replies = tuple(game.legal_actions(after_own))
            if not replies:
                raise ValueError("nonterminal state has no legal opponent reply")
            for reply in replies:
                leaf = game.transition(after_own, reply)
                if own_action == observed_action and reply == observed_reply and observed_leaf is not None:
                    if leaf != observed_leaf:
                        raise ValueError("observed two-ply leaf disagrees with exact rules")
                    observed_branch[root_index] = len(branch_x)
                branch_roots.append(root_index)
                branch_actions.append((_one_hot((own_action,)), _one_hot((reply,))))
                branch_x.append(game.features(leaf))
                branch_nonterminal.append(game.terminal(leaf) is None)
        if observed_leaf is not None and observed_branch[root_index] < 0:
            raise ValueError("observed legal two-ply target is missing from reply closure")
    if not branch_x:
        raise ValueError("batch has no nonterminal two-ply branches")
    actions = np.zeros((len(records), 2, ACTION_SIZE), dtype=np.float64)
    for index, record in enumerate(records):
        actions[index, 0] = _one_hot((record["action"],))
        if record.get("reply") is not None:
            actions[index, 1] = _one_hot((record["reply"],))
    return {
        "x": np.asarray(roots_x, dtype=np.float64),
        "legal": np.asarray(legal_masks, dtype=bool),
        "policy": np.asarray(policy_targets, dtype=np.int64),
        "value": np.asarray(values, dtype=np.float64),
        "actions": actions,
        "branch_roots": np.asarray(branch_roots, dtype=np.int64),
        "branch_actions": np.asarray(branch_actions, dtype=np.float64),
        "branch_x": np.asarray(branch_x, dtype=np.float64),
        "branch_nonterminal": np.asarray(branch_nonterminal, dtype=bool),
        "observed_branch": observed_branch,
        "roots": len(records),
    }


class Model:
    def __init__(self, config=Config()):
        self.config = config
        self.step = 0
        rng = np.random.default_rng(config.seed)
        d = config.latent
        predictor_in = d + ACTION_PAIR_SIZE + RULE_DESC_SIZE
        def weight(n, m):
            return rng.normal(0.0, np.sqrt(1.0 / n), size=(n, m)).astype(np.float64)
        self.params = {
            "ew": weight(FEATURE_SIZE, d), "eb": np.zeros(d),
            "pw": weight(d, ACTION_SIZE), "pb": np.zeros(ACTION_SIZE),
            "vw": weight(d, 1), "vb": np.zeros(1),
            "gw": weight(predictor_in, d), "gb": np.zeros(d),
        }
        self.target = {key: self.params[key].copy() for key in ("ew", "eb")}
        self.m = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.v = {key: np.zeros_like(value) for key, value in self.params.items()}

    def encode(self, features, *, target=False):
        weights = self.target if target else self.params
        return np.tanh(np.asarray(features, dtype=np.float64) @ weights["ew"] + weights["eb"])

    def value(self, latent):
        return np.tanh(latent @ self.params["vw"] + self.params["vb"])

    def predictor_input(self, latent, action_pair, features):
        return np.concatenate((latent, action_pair.reshape(len(latent), -1),
                               features[:, 192:192 + RULE_DESC_SIZE]), axis=1)

    def predict_latent(self, latent, action_pair, features):
        inputs = self.predictor_input(latent, action_pair, features)
        return np.tanh(inputs @ self.params["gw"] + self.params["gb"])

    def branch_value(self, game, state, action, reply, leaf):
        """Return an exact terminal or learned nonterminal score for one branch."""
        game.validate(state)
        if game.terminal(state) is not None or state.player not in (-1, 1):
            raise ValueError("invalid planning root")
        after = game.transition(state, action)
        if game.terminal(after) is not None:
            if reply is not None or leaf not in (None, after):
                raise ValueError("immediate terminal action has no reply branch")
            return float(state.player * game.terminal(after))
        if type(reply) is not int or reply not in game.legal_actions(after):
            raise ValueError("planner reply is not legal")
        expected = game.transition(after, reply)
        if expected != leaf:
            raise ValueError("planner branch does not match exact transition")
        if game.terminal(leaf) is not None:
            return float(state.player * game.terminal(leaf))
        x = game.features(state)[None, :]
        z = self.encode(x)
        pair = np.zeros((1, 2, ACTION_SIZE), dtype=np.float64)
        pair[0, 0, action] = 1.0
        pair[0, 1, reply] = 1.0
        leaf_x = game.features(leaf)[None, :]
        if self.config.variant != "direct-leaf":
            return float(self.value(self.predict_latent(z, pair, x))[0, 0])
        return float(self.value(self.encode(leaf_x))[0, 0])

    def plan_action(self, game, state):
        """Choose max-min action using exact rules and learned nonterminal leaves."""
        game.validate(state)
        if game.terminal(state) is not None:
            raise ValueError("cannot plan from a terminal root")
        legal = tuple(game.legal_actions(state))
        if not legal:
            raise ValueError("nonterminal root has no legal actions")
        action_values = {}
        for action in legal:
            after = game.transition(state, action)
            if game.terminal(after) is not None:
                action_values[action] = float(state.player * game.terminal(after))
                continue
            replies = tuple(game.legal_actions(after))
            if not replies:
                raise ValueError("nonterminal opponent state has no legal replies")
            action_values[action] = min(
                self.branch_value(game, state, action, reply,
                                  game.transition(after, reply))
                for reply in replies)
        selected = max(legal, key=lambda action: action_values[action])
        return selected, action_values

    def loss_grad(self, batch):
        p = self.params
        x = batch["x"]
        n = len(x)
        d = self.config.latent
        z = self.encode(x)
        grad = {key: np.zeros_like(value) for key, value in p.items()}
        dz = np.zeros_like(z)

        logits = z @ p["pw"] + p["pb"]
        logits = np.where(batch["legal"], logits, -np.inf)
        max_logits = np.max(logits, axis=1, keepdims=True)
        shifted = logits - max_logits
        exp_logits = np.exp(shifted)
        probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        log_norm = np.log(exp_logits.sum(axis=1, keepdims=True))
        policy_loss = float(np.mean(log_norm[:, 0] - shifted[np.arange(n), batch["policy"]]))
        dlogits = probs
        dlogits[np.arange(n), batch["policy"]] -= 1.0
        dlogits /= n
        grad["pw"] += z.T @ dlogits
        grad["pb"] += dlogits.sum(axis=0)
        dz += dlogits @ p["pw"].T

        root_value = self.value(z)
        root_delta = root_value - batch["value"]
        root_loss = float(np.mean(root_delta ** 2))
        droot = (2.0 / n) * root_delta * (1.0 - root_value ** 2)
        grad["vw"] += z.T @ droot
        grad["vb"] += droot.sum(axis=0)
        dz += droot @ p["vw"].T

        branch_roots = batch["branch_roots"]
        branch_x = batch["branch_x"]
        branch_actions = batch["branch_actions"]
        branch_z = z[branch_roots]
        branch_inputs = self.predictor_input(branch_z, branch_actions, branch_x)
        branch_nonterminal = batch["branch_nonterminal"]
        total = policy_loss + root_loss
        metrics = {"policy_nll": policy_loss, "root_value_mse": root_loss,
                   "roots": n, "branches": len(branch_roots),
                   "nonterminal_branches": int(branch_nonterminal.sum())}

        if self.config.variant != "direct-leaf":
            predicted = np.tanh(branch_inputs @ p["gw"] + p["gb"])
        else:
            predicted = None
        if self.config.variant == "reply-jepa":
            target = self.encode(branch_x, target=True)
            branch_loss = 0.0
            dlatent = np.zeros_like(predicted)
            valid_roots = np.unique(branch_roots[branch_nonterminal])
            if len(valid_roots):
                delta = predicted - target
                for root_id in valid_roots:
                    members = branch_nonterminal & (branch_roots == root_id)
                    root_delta = delta[members]
                    branch_loss += float(np.mean(root_delta ** 2) / len(valid_roots))
                    dlatent[members] = (2.0 * root_delta / d
                                        / (len(valid_roots) * int(members.sum())))
                total += self.config.jepa_weight * branch_loss
                dlatent *= self.config.jepa_weight
                dgate = dlatent * (1.0 - predicted ** 2)
                grad["gw"] += branch_inputs.T @ dgate
                grad["gb"] += dgate.sum(axis=0)
                dz_branch = dgate @ p["gw"][:d].T
                np.add.at(dz, branch_roots, dz_branch)
            metrics["reply_jepa_loss"] = branch_loss
        else:
            metrics["reply_jepa_loss"] = 0.0

        observed = batch["observed_branch"]
        observed_roots = np.flatnonzero(observed >= 0)
        if len(observed_roots):
            branch_ids = observed[observed_roots]
            labels = batch["value"][observed_roots]
            nonterminal_observed = branch_nonterminal[branch_ids]
            terminal_observed = int((~nonterminal_observed).sum())
            observed_loss = 0.0
            active_ids = branch_ids[nonterminal_observed]
            if self.config.variant != "direct-leaf" and len(active_ids):
                selected_latent = predicted[active_ids]
                branch_value = self.value(selected_latent)
                delta = branch_value - labels[nonterminal_observed]
                observed_loss = float(np.mean(delta ** 2))
                dv = (2.0 / len(active_ids)) * delta * (1.0 - branch_value ** 2)
                grad["vw"] += selected_latent.T @ dv
                grad["vb"] += dv.sum(axis=0)
                dselected = dv @ p["vw"].T
                dselected *= (1.0 - selected_latent ** 2)
                dgate = np.zeros_like(predicted)
                dgate[active_ids] += dselected
                grad["gw"] += branch_inputs.T @ dgate
                grad["gb"] += dgate.sum(axis=0)
                np.add.at(dz, branch_roots, dgate @ p["gw"][:d].T)
            elif self.config.variant == "direct-leaf" and len(active_ids):
                selected_x = branch_x[active_ids]
                selected_latent = self.encode(selected_x)
                branch_value = self.value(selected_latent)
                delta = branch_value - labels[nonterminal_observed]
                observed_loss = float(np.mean(delta ** 2))
                dv = (2.0 / len(active_ids)) * delta * (1.0 - branch_value ** 2)
                grad["vw"] += selected_latent.T @ dv
                grad["vb"] += dv.sum(axis=0)
                dleaf = dv @ p["vw"].T
                dleaf *= (1.0 - selected_latent ** 2)
                grad["ew"] += selected_x.T @ dleaf
                grad["eb"] += dleaf.sum(axis=0)
            total += observed_loss
            metrics["observed_leaf_value_mse"] = observed_loss
            metrics["observed_terminal_exact_count"] = terminal_observed
        else:
            metrics["observed_leaf_value_mse"] = 0.0

        centered = z - z.mean(axis=0, keepdims=True)
        std = np.sqrt(np.mean(centered ** 2, axis=0) + 1e-4)
        shortfall = np.maximum(0.0, self.config.target_std - std)
        variance_loss = self.config.variance_weight * float(np.mean(shortfall ** 2))
        total += variance_loss
        dz += (-2.0 * self.config.variance_weight * shortfall[None, :]
               * centered / (d * n * std[None, :]))
        covariance = centered.T @ centered / n
        off_diagonal = covariance - np.diag(np.diag(covariance))
        covariance_loss = (self.config.covariance_weight
                           * float(np.sum(off_diagonal ** 2)) / d)
        total += covariance_loss
        dz += (4.0 * self.config.covariance_weight
               * centered @ off_diagonal / (n * d))
        de = dz * (1.0 - z ** 2)
        grad["ew"] += x.T @ de
        grad["eb"] += de.sum(axis=0)
        metrics.update(loss=float(total), variance_loss=variance_loss,
                       covariance_loss=covariance_loss,
                       latent_mean_std=float(np.std(z, axis=0).mean()),
                       effective_rank=_effective_rank(z))
        if not np.isfinite(total) or any(not np.all(np.isfinite(g)) for g in grad.values()):
            raise FloatingPointError("nonfinite V2.8 loss or gradient")
        return metrics, grad

    def update(self, batch):
        metrics, gradients = self.loss_grad(batch)
        norm = float(np.sqrt(sum(np.sum(gradient ** 2) for gradient in gradients.values())))
        scale = min(1.0, 5.0 / max(norm, 1e-12))
        self.step += 1
        for key in self.params:
            gradient = gradients[key] * scale
            self.m[key] = 0.9 * self.m[key] + 0.1 * gradient
            self.v[key] = 0.999 * self.v[key] + 0.001 * gradient ** 2
            m_hat = self.m[key] / (1.0 - 0.9 ** self.step)
            v_hat = self.v[key] / (1.0 - 0.999 ** self.step)
            self.params[key] -= self.config.learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8)
        for key in self.target:
            self.target[key] = (self.config.ema * self.target[key]
                                + (1.0 - self.config.ema) * self.params[key])
        if any(not np.all(np.isfinite(array)) for group in
               (self.params, self.target, self.m, self.v) for array in group.values()):
            raise FloatingPointError("nonfinite V2.8 optimizer/checkpoint state")
        metrics["gradient_norm"] = norm
        return metrics

    def parameter_counts(self):
        active = {"ew", "eb", "pw", "pb", "vw", "vb"}
        if self.config.variant != "direct-leaf":
            active |= {"gw", "gb"}
        return {"allocated": sum(value.size for value in self.params.values()),
                "active": sum(self.params[key].size for key in active)}

    def save(self, path, identity):
        _validate_checkpoint_identity(identity)
        path = Path(path)
        arrays = {prefix + key: value for prefix, group in
                  (("p_", self.params), ("t_", self.target),
                   ("m_", self.m), ("v_", self.v)) for key, value in group.items()}
        hashes = {key: hashlib.sha256(value.tobytes()).hexdigest()
                  for key, value in arrays.items()}
        metadata = {"method": METHOD_VERSION, "config": asdict(self.config),
                    "identity": identity, "step": self.step, "array_hashes": hashes,
                    "code_sha256": _model_code_sha256()}
        arrays["metadata"] = np.asarray(json.dumps(metadata, sort_keys=True, allow_nan=False))
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                         dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                np.savez_compressed(stream, **arrays)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path, config, identity):
        _validate_checkpoint_identity(identity)
        with np.load(path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata"]))
            if (metadata.get("method") != METHOD_VERSION
                    or metadata.get("config") != asdict(config)
                    or metadata.get("identity") != identity
                    or metadata.get("code_sha256") != _model_code_sha256()):
                raise ValueError("checkpoint code/config/data/objective identity mismatch")
            model = cls(config)
            groups = (("p_", model.params), ("t_", model.target),
                      ("m_", model.m), ("v_", model.v))
            expected = {prefix + key for prefix, group in groups for key in group}
            if set(archive.files) != expected | {"metadata"}:
                raise ValueError("checkpoint tensor inventory mismatch")
            hashes = metadata.get("array_hashes")
            if not isinstance(hashes, dict) or set(hashes) != expected:
                raise ValueError("checkpoint checksum inventory mismatch")
            for prefix, group in groups:
                for key, target_array in group.items():
                    full_key = prefix + key
                    value = archive[full_key]
                    if (value.shape != target_array.shape or value.dtype != np.float64
                            or not np.all(np.isfinite(value))
                            or hashlib.sha256(value.tobytes()).hexdigest() != hashes[full_key]):
                        raise ValueError("invalid or corrupted checkpoint array")
                    group[key] = value.copy()
            if type(metadata.get("step")) is not int or metadata["step"] < 0:
                raise ValueError("invalid optimizer step")
            model.step = metadata["step"]
            return model


def _effective_rank(latent):
    centered = latent - latent.mean(axis=0, keepdims=True)
    covariance = centered.T @ centered / max(1, len(centered))
    eigenvalues = np.linalg.eigvalsh(covariance)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    total = float(eigenvalues.sum())
    if total <= 1e-12:
        return 0.0
    probabilities = eigenvalues[eigenvalues > 1e-12] / total
    return float(np.exp(-np.sum(probabilities * np.log(probabilities))))


def _model_code_sha256():
    root = Path(__file__).resolve().parents[1]
    paths = (Path(__file__), root / "two_player" / "v28_data.py",
             root / "two_player" / "games.py")
    content = {path.name: hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
               for path in paths}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_checkpoint_identity(identity):
    if not isinstance(identity, dict) or not _IDENTITY_KEYS <= set(identity):
        raise ValueError("checkpoint identity requires dataset, audit, and split fields")
    for field in ("dataset_sha256", "audit_sha256"):
        value = identity.get(field)
        if (not isinstance(value, str) or len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError(f"checkpoint identity has invalid {field}")
    if identity.get("split") != "train":
        raise ValueError("checkpoint identity must identify the train split")
