"""Direct policy/value baseline for fair CAISSA-JEPA comparisons."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Union

import numpy as np

from adversarial_jepa import ACTION_SIZE, STATE_SIZE, encode_action, encode_snapshot


MODEL_VERSION = 1


class DirectPolicyValueBaseline:
    """Same state/action capacity class as v7, without future prediction."""

    names = ("encoder_w", "encoder_b", "value_w", "value_b", "policy_action_w")

    def __init__(self, model_path: Union[str, Path], latent_size: int = 96, create_if_missing: bool = True):
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.latent_size = latent_size
        self.trained_steps = 0
        self.adam_step = 0
        self.adam_m = {}
        self.adam_v = {}
        self.dataset_fingerprint = ""
        self.seed = 20260903
        if self.model_path.exists():
            self.load()
        elif create_if_missing:
            self._initialize()
        else:
            raise FileNotFoundError(self.model_path)

    def _initialize(self):
        generator = np.random.default_rng(self.seed)
        self.encoder_w = (generator.standard_normal((STATE_SIZE, self.latent_size)) * math.sqrt(2 / STATE_SIZE)).astype(np.float32)
        self.encoder_b = np.zeros(self.latent_size, dtype=np.float32)
        self.value_w = (generator.standard_normal((self.latent_size, 1)) * math.sqrt(2 / self.latent_size)).astype(np.float32)
        self.value_b = np.zeros(1, dtype=np.float32)
        self.policy_action_w = (generator.standard_normal((ACTION_SIZE, self.latent_size)) * math.sqrt(2 / ACTION_SIZE)).astype(np.float32)

    def load(self):
        with np.load(self.model_path, allow_pickle=False) as data:
            if int(data["model_version"][0]) != MODEL_VERSION:
                raise ValueError("Không phải checkpoint direct policy/value baseline")
            self.latent_size = int(data["latent_size"][0])
            self.trained_steps = int(data["trained_steps"][0])
            self.adam_step = int(data["adam_step"][0])
            self.dataset_fingerprint = str(data["dataset_fingerprint"][0])
            for name in self.names:
                setattr(self, name, data[name].astype(np.float32))
                if "adam_m_" + name in data:
                    self.adam_m[name] = data["adam_m_" + name].astype(np.float32)
                    self.adam_v[name] = data["adam_v_" + name].astype(np.float32)

    def save(self):
        temporary = self.model_path.with_suffix(".tmp.npz")
        payload = {
            "model_version": np.array([MODEL_VERSION], dtype=np.int64),
            "latent_size": np.array([self.latent_size], dtype=np.int64),
            "trained_steps": np.array([self.trained_steps], dtype=np.int64),
            "adam_step": np.array([self.adam_step], dtype=np.int64),
            "dataset_fingerprint": np.array([self.dataset_fingerprint]),
        }
        for name in self.names:
            payload[name] = getattr(self, name)
            if name in self.adam_m:
                payload["adam_m_" + name] = self.adam_m[name]
                payload["adam_v_" + name] = self.adam_v[name]
        np.savez_compressed(temporary, **payload)
        temporary.replace(self.model_path)

    def encode(self, states):
        return np.tanh(states @ self.encoder_w + self.encoder_b)

    def value(self, latent):
        return np.tanh(latent @ self.value_w + self.value_b)

    def _adam(self, gradients, learning_rate):
        self.adam_step += 1
        for name, gradient in gradients.items():
            gradient = np.clip(gradient, -1, 1).astype(np.float32)
            if name not in self.adam_m:
                self.adam_m[name] = np.zeros_like(gradient)
                self.adam_v[name] = np.zeros_like(gradient)
            self.adam_m[name] = 0.9 * self.adam_m[name] + 0.1 * gradient
            self.adam_v[name] = 0.999 * self.adam_v[name] + 0.001 * gradient * gradient
            m_hat = self.adam_m[name] / (1 - 0.9**self.adam_step)
            v_hat = self.adam_v[name] / (1 - 0.999**self.adam_step)
            setattr(self, name, getattr(self, name) - learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8))

    def _metrics(self, samples, update=False, learning_rate=5e-4):
        states = np.stack([encode_snapshot(item["state"]) for item in samples])
        positive_actions = np.stack([encode_action(item["own_action"]) for item in samples])
        negative_actions = np.stack([encode_action(item["negative_action"]) for item in samples])
        targets = np.array([item["outcome"] for item in samples], dtype=np.float32)[:, None]
        batch_size = len(samples)
        latent = self.encode(states)
        value = self.value(latent)
        value_error = value - targets
        value_loss = float(np.mean(value_error * value_error))
        positive_embed = positive_actions @ self.policy_action_w
        negative_embed = negative_actions @ self.policy_action_w
        scale = math.sqrt(self.latent_size)
        margins = 0.20 - np.sum(latent * positive_embed, axis=1) / scale + np.sum(latent * negative_embed, axis=1) / scale
        ranking_loss = float(np.mean(np.maximum(0, margins)))
        variance = np.var(latent, axis=0)
        variance_loss = float(np.mean(np.maximum(0, 0.05 - variance)))
        metrics = {
            "loss": value_loss + ranking_loss + variance_loss,
            "value_loss": value_loss,
            "ranking_loss": ranking_loss,
            "variance_loss": variance_loss,
            "ranking_accuracy": float(np.mean(margins <= 0)),
            "latent_std": float(np.mean(np.std(latent, axis=0))),
        }
        if not update:
            return metrics
        value_pre = 2 * value_error * (1 - value * value) / batch_size
        gradients = {
            "value_w": latent.T @ value_pre,
            "value_b": np.sum(value_pre, axis=0),
        }
        latent_gradient = value_pre @ self.value_w.T
        active = (margins > 0).astype(np.float32)[:, None] / batch_size
        latent_gradient += 0.25 * active * (-positive_embed + negative_embed) / scale
        gradients["policy_action_w"] = 0.25 * (
            positive_actions.T @ (-active * latent / scale)
            + negative_actions.T @ (active * latent / scale)
        )
        low = variance < 0.05
        if np.any(low):
            centered = latent - np.mean(latent, axis=0, keepdims=True)
            latent_gradient[:, low] += -0.1 * centered[:, low] / (batch_size * self.latent_size)
        pre = latent_gradient * (1 - latent * latent)
        gradients["encoder_w"] = states.T @ pre
        gradients["encoder_b"] = np.sum(pre, axis=0)
        metrics["gradient_norm"] = math.sqrt(sum(float(np.sum(grad * grad)) for grad in gradients.values()))
        self._adam(gradients, learning_rate)
        self.trained_steps += 1
        return metrics

    def train_batch(self, samples, learning_rate=5e-4):
        return self._metrics(samples, True, learning_rate)

    def evaluate_batch(self, samples):
        return self._metrics(samples, False)

    def danh_gia_snapshot(self, snapshot):
        return float(self.value(self.encode(encode_snapshot(snapshot)[None, :]))[0, 0])

    def score_legal_moves(self, snapshot, legal_moves, temperature=0.25):
        if not legal_moves:
            return [], [], 1.0
        latent = self.encode(encode_snapshot(snapshot)[None, :])
        actions = np.stack([encode_action(move) for move in legal_moves])
        scores = (actions @ self.policy_action_w @ latent[0]) / math.sqrt(self.latent_size)
        shifted = (scores - np.max(scores)) / max(0.03, temperature)
        priors = np.exp(shifted)
        priors /= np.sum(priors) + 1e-8
        entropy = -float(np.sum(priors * np.log(priors + 1e-8)))
        if len(priors) > 1:
            entropy /= math.log(len(priors))
        return scores.tolist(), priors.tolist(), entropy
