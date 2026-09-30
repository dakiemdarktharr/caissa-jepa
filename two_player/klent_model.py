"""Small shared-backbone policy/Q learner for the KLENT-style baseline.

The implementation is a CPU feasibility model, not a paper-scale ResNet or a
reproduction of the authors' experimental results. Policy and Q heads are
separate over one shared tanh encoder, as specified in the source paper.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import time

import numpy as np

from .games import ACTION_SIZE, FEATURE_SIZE, RULES_VERSION
from .klent_baseline import regularized_policy_target
from .klent_baseline import alternating_lambda_returns


@dataclass(frozen=True)
class KLENTConfig:
    seed: int = 17
    latent: int = 32
    learning_rate: float = 1e-3
    alpha: float = 0.03
    beta: float = 0.1
    lambda_: float = float(np.exp(-1.0 / 8.0))

    def __post_init__(self):
        if type(self.seed) is not int or self.latent < 2:
            raise ValueError("seed and latent dimension must be valid")
        if not np.isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("learning rate must be finite and positive")
        if not np.isfinite(self.alpha) or self.alpha <= 0 or not np.isfinite(self.beta) or self.beta < 0:
            raise ValueError("alpha must be positive and beta nonnegative")
        if not np.isfinite(self.lambda_) or not 0 <= self.lambda_ <= 1:
            raise ValueError("lambda must be finite and in [0, 1]")


class KLENTModel:
    """Shared encoder with legal policy and action-value heads."""

    def __init__(self, config=KLENTConfig()):
        self.config = config
        self.step = 0
        rng = np.random.default_rng(config.seed)
        d = config.latent

        def weight(inputs, outputs):
            return rng.normal(0.0, np.sqrt(1.0 / inputs), (inputs, outputs))

        self.params = {
            "ew": weight(FEATURE_SIZE, d),
            "eb": np.zeros(d),
            "pw": weight(d, ACTION_SIZE),
            "pb": np.zeros(ACTION_SIZE),
            "qw": weight(d, ACTION_SIZE),
            "qb": np.zeros(ACTION_SIZE),
        }
        self.first = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.second = {key: np.zeros_like(value) for key, value in self.params.items()}

    def _arrays(self, x, legal):
        x = np.asarray(x, dtype=np.float64)
        legal = np.asarray(legal, dtype=bool)
        if x.ndim != 2 or x.shape[1] != FEATURE_SIZE:
            raise ValueError("state features must have shape [batch, FEATURE_SIZE]")
        if legal.shape != (len(x), ACTION_SIZE) or not len(x):
            raise ValueError("legal masks must have shape [batch, ACTION_SIZE] and be nonempty")
        if not np.all(np.isfinite(x)) or np.any(legal.sum(axis=1) == 0):
            raise ValueError("features must be finite and each row needs a legal action")
        return x, legal

    @staticmethod
    def _softmax(logits, legal):
        masked = np.where(legal, logits, -np.inf)
        shifted = masked - np.max(masked, axis=1, keepdims=True)
        weights = np.where(legal, np.exp(shifted), 0.0)
        return weights / weights.sum(axis=1, keepdims=True)

    def predict(self, x, legal):
        """Return current policy and Q arrays; illegal policy entries are zero."""
        x, legal = self._arrays(x, legal)
        p = self.params
        z = np.tanh(x @ p["ew"] + p["eb"])
        policy = self._softmax(z @ p["pw"] + p["pb"], legal)
        q_values = z @ p["qw"] + p["qb"]
        return policy, q_values

    def improvement_target(self, x, legal):
        policy, q_values = self.predict(x, legal)
        target = regularized_policy_target(
            policy, q_values, legal, alpha=self.config.alpha, beta=self.config.beta
        )
        value = np.sum(target * np.where(legal, q_values, 0.0), axis=1)
        return target, value

    def loss_grad(self, batch):
        x, legal = self._arrays(batch["x"], batch["legal"])
        n = len(x)
        actions = np.asarray(batch["action"])
        policy_target = np.asarray(batch["policy_target"], dtype=np.float64)
        q_target = np.asarray(batch["q_target"], dtype=np.float64)
        if actions.shape != (n,) or actions.dtype.kind not in "iu":
            raise ValueError("actions must be an integer vector with one action per row")
        if policy_target.shape != (n, ACTION_SIZE) or q_target.shape != (n,):
            raise ValueError("policy/Q targets have the wrong batch shape")
        if np.any(actions < 0) or np.any(actions >= ACTION_SIZE):
            raise ValueError("action index is outside the action space")
        rows = np.arange(n)
        if np.any(~legal[rows, actions]):
            raise ValueError("sampled Q action must be legal")
        if not np.all(np.isfinite(policy_target)) or not np.all(np.isfinite(q_target)):
            raise ValueError("targets must be finite")
        if np.any(policy_target < 0) or np.any(policy_target[~legal] != 0):
            raise ValueError("policy target must be nonnegative and zero on illegal actions")
        if not np.allclose(policy_target.sum(axis=1), 1.0, rtol=1e-10, atol=1e-12):
            raise ValueError("policy target rows must sum to one")

        p = self.params
        gradients = {key: np.zeros_like(value) for key, value in p.items()}
        z = np.tanh(x @ p["ew"] + p["eb"])
        logits = z @ p["pw"] + p["pb"]
        predicted_policy = self._softmax(logits, legal)
        log_prob = np.zeros_like(predicted_policy)
        log_prob[legal] = np.log(predicted_policy[legal])
        policy_loss = float(-np.sum(policy_target * log_prob) / n)
        dlogits = (predicted_policy - policy_target) / n
        gradients["pw"] = z.T @ dlogits
        gradients["pb"] = dlogits.sum(axis=0)
        dz = dlogits @ p["pw"].T

        q_values = z @ p["qw"] + p["qb"]
        q_error = q_values[rows, actions] - q_target
        q_loss = float(np.mean(q_error**2))
        dq = np.zeros_like(q_values)
        dq[rows, actions] = 2.0 * q_error / n
        gradients["qw"] = z.T @ dq
        gradients["qb"] = dq.sum(axis=0)
        dz += dq @ p["qw"].T

        dz_pre = dz * (1.0 - z**2)
        gradients["ew"] = x.T @ dz_pre
        gradients["eb"] = dz_pre.sum(axis=0)
        total = policy_loss + q_loss
        if not np.isfinite(total) or any(not np.all(np.isfinite(g)) for g in gradients.values()):
            raise FloatingPointError("nonfinite KLENT-style loss or gradient")
        return {"loss": total, "policy_loss": policy_loss, "q_loss": q_loss}, gradients

    def update(self, batch):
        metrics, gradients = self.loss_grad(batch)
        norm = np.sqrt(sum(np.sum(grad * grad) for grad in gradients.values()))
        self.step += 1
        lr = self.config.learning_rate
        for key in self.params:
            grad = gradients[key]
            self.first[key] = 0.9 * self.first[key] + 0.1 * grad
            self.second[key] = 0.999 * self.second[key] + 0.001 * grad**2
            first = self.first[key] / (1.0 - 0.9**self.step)
            second = self.second[key] / (1.0 - 0.999**self.step)
            self.params[key] -= lr * first / (np.sqrt(second) + 1e-8)
        metrics["gradient_norm"] = float(norm)
        metrics["step"] = self.step
        return metrics

    def parameter_counts(self):
        return {"parameters": sum(value.size for value in self.params.values()),
                "optimizer_states": sum(value.size for value in self.first.values()) * 2,
                "active": sum(value.size for value in self.params.values())}

    def config_dict(self):
        return asdict(self.config)


def _legal_mask(actions):
    actions = tuple(actions)
    if not actions or any(type(action) is not int or not 0 <= action < ACTION_SIZE for action in actions):
        raise ValueError("nonterminal game state must expose valid legal action indices")
    mask = np.zeros(ACTION_SIZE, dtype=bool)
    mask[list(actions)] = True
    return mask


def collect_selfplay_episode(game, model, rng, *, max_plies=256):
    """Collect one complete current-policy episode and detached KLENT targets."""
    state = game.initial()
    states = []
    policies = []
    actions = []
    values = []
    rewards = []
    terminal_successors = []
    replay = []
    plies = 0
    while True:
        result = game.terminal(state)
        if result is not None:
            if not states:
                raise ValueError("game initial state cannot already be terminal")
            break
        if plies >= max_plies:
            raise TimeoutError("self-play episode exceeded its predeclared ply cap")
        legal_actions = game.legal_actions(state)
        legal = _legal_mask(legal_actions)
        features = np.asarray(game.features(state), dtype=np.float64)
        if features.shape != (FEATURE_SIZE,) or not np.all(np.isfinite(features)):
            raise ValueError("game adapter returned invalid state features")
        policy, q_values = model.predict(features[None, :], legal[None, :])
        policy_target = regularized_policy_target(
            policy, q_values, legal[None, :],
            alpha=model.config.alpha, beta=model.config.beta,
        )[0]
        state_value = float(np.sum(policy_target * np.where(legal, q_values[0], 0.0)))
        action = int(rng.choice(np.arange(ACTION_SIZE), p=policy_target))
        actor = state.player
        replay.append({"board": list(state.board), "player": actor, "action": action})
        next_state = game.transition(state, action)
        next_result = game.terminal(next_state)
        reward = 0.0 if next_result is None else float(actor * next_result)
        states.append((features, legal, policy_target, action))
        policies.append(policy_target)
        actions.append(action)
        values.append(state_value)
        rewards.append(reward)
        terminal_successors.append(next_result is not None)
        state = next_state
        plies += 1

    next_values = np.zeros(len(states), dtype=np.float64)
    for index in range(len(states) - 1):
        if not terminal_successors[index]:
            next_values[index] = values[index + 1]
    returns = alternating_lambda_returns(
        rewards, next_values, terminal_successors, lam=model.config.lambda_, gamma=1.0
    )
    model_digest = hashlib.sha256()
    for name in sorted(model.params):
        model_digest.update(name.encode("utf-8"))
        model_digest.update(np.asarray(model.params[name]).tobytes(order="C"))
    model_digest.update(json.dumps(model.config_dict(), sort_keys=True).encode("utf-8"))
    rules_version = getattr(game, "rules_version", RULES_VERSION)
    game_name = getattr(game, "name", type(game).__name__)
    identity_payload = {
        "game": game_name,
        "rules_version": rules_version,
        "behavior_model_sha256": model_digest.hexdigest(),
        "replay": replay,
        "outcome": int(game.terminal(state)),
    }
    trajectory_sha256 = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "x": np.stack([row[0] for row in states]),
        "legal": np.stack([row[1] for row in states]),
        "policy_target": np.stack(policies),
        "action": np.asarray(actions, dtype=np.int64),
        "q_target": returns,
        "rewards": np.asarray(rewards, dtype=np.float64),
        "terminal_successors": np.asarray(terminal_successors, dtype=bool),
        "outcome": int(game.terminal(state)),
        "plies": plies,
        "game_name": game_name,
        "rules_version": rules_version,
        "behavior_model_sha256": model_digest.hexdigest(),
        "player_sequence": [row["player"] for row in replay],
        "trajectory_sha256": trajectory_sha256,
    }


def collect_selfplay_batch(game, model, *, episodes, seed, max_plies=256):
    """Collect an on-policy batch before fitting, matching KLENT's two phases."""
    if type(episodes) is not int or episodes < 1 or type(seed) is not int:
        raise ValueError("episodes and seed must be positive integers")
    rng = np.random.default_rng(seed)
    began = time.perf_counter()
    trajectories = [
        collect_selfplay_episode(game, model, rng, max_plies=max_plies)
        for _ in range(episodes)
    ]
    return {
        "trajectories": trajectories,
        "episodes": episodes,
        "transitions": sum(row["plies"] for row in trajectories),
        "collection_seconds": time.perf_counter() - began,
        "collection_seed": seed,
    }


def fit_selfplay_batch(model, batch, *, epochs, batch_size, seed):
    """Fit detached policy/return targets from a collected on-policy batch."""
    if type(epochs) is not int or epochs != 1 or type(batch_size) is not int or batch_size < 1:
        raise ValueError("on-policy KLENT fitting requires exactly one epoch and a positive batch size")
    trajectories = batch.get("trajectories")
    if not trajectories:
        raise ValueError("cannot fit an empty self-play batch")
    arrays = {
        name: np.concatenate([trajectory[name] for trajectory in trajectories], axis=0)
        for name in ("x", "legal", "policy_target", "action", "q_target")
    }
    rng = np.random.default_rng(seed)
    history = []
    began = time.perf_counter()
    for _ in range(epochs):
        order = rng.permutation(len(arrays["x"]))
        epoch_metrics = []
        for start in range(0, len(order), batch_size):
            indices = order[start : start + batch_size]
            item = {name: value[indices] for name, value in arrays.items()}
            epoch_metrics.append(model.update(item))
        history.append({
            "epoch": len(history) + 1,
            "updates": len(epoch_metrics),
            "loss": float(np.mean([row["loss"] for row in epoch_metrics])),
            "policy_loss": float(np.mean([row["policy_loss"] for row in epoch_metrics])),
            "q_loss": float(np.mean([row["q_loss"] for row in epoch_metrics])),
        })
    return {
        "history": history,
        "training_examples": len(arrays["x"]),
        "fit_seconds": time.perf_counter() - began,
        "optimizer_steps": model.step,
    }
