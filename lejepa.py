"""LeJEPA-style action-conditioned predictor for the chess experiment.

This is a small NumPy adaptation of the LeJEPA objective to symbolic chess
states. It keeps one encoder and action-conditioned future predictors, but it
does not create an EMA/teacher encoder. SIGReg is implemented as a fixed
random-slice characteristic-function matching loss against an isotropic
standard Gaussian, which keeps the implementation deterministic and
dependency-free for this repository.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Union

import numpy as np

from adversarial_jepa import ACTION_SIZE, STATE_SIZE, encode_action, encode_snapshot


MODEL_VERSION = 1
MODEL_VARIANT = "sigreg"
HORIZONS = (1, 2, 4)
HORIZON_WEIGHTS = {1: 1.0, 2: 0.75, 4: 0.50}


class LeJEPA:
    """Lean action-conditioned JEPA with SIGReg and no EMA target network."""

    predictor_names = (
        "predictor_w1",
        "predictor_b1",
        "predictor_w2",
        "predictor_b2",
        "predictor_w4",
        "predictor_b4",
    )
    parameter_names = (
        "encoder_w",
        "encoder_b",
        *predictor_names,
        "value_w",
        "value_b",
        "policy_action_w",
    )

    def __init__(
        self,
        model_path: Union[str, Path],
        latent_size: int = 96,
        create_if_missing: bool = True,
        variant: str = MODEL_VARIANT,
    ) -> None:
        if variant != MODEL_VARIANT:
            raise ValueError(f"Unknown LeJEPA variant: {variant}")
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.latent_size = int(latent_size)
        self.variant = variant
        self.trained_steps = 0
        self.adam_step = 0
        self.adam_m: dict[str, np.ndarray] = {}
        self.adam_v: dict[str, np.ndarray] = {}
        self.dataset_fingerprint = ""
        self.seed = 20260903
        self.sigreg_weight = 0.20
        self.sigreg_slices_count = 32
        self.sigreg_t = np.array((0.5, 1.0, 1.5, 2.0), dtype=np.float32)

        if self.model_path.exists():
            self.load()
        elif create_if_missing:
            self._initialize()
        else:
            raise FileNotFoundError(self.model_path)

    def _initialize(self) -> None:
        generator = np.random.default_rng(self.seed)
        self.encoder_w = (
            generator.standard_normal((STATE_SIZE, self.latent_size))
            * math.sqrt(2.0 / STATE_SIZE)
        ).astype(np.float32)
        self.encoder_b = np.zeros(self.latent_size, dtype=np.float32)

        for horizon, action_count in ((1, 1), (2, 2), (4, 4)):
            input_size = self.latent_size + action_count * ACTION_SIZE
            scale = math.sqrt(2.0 / input_size)
            setattr(
                self,
                f"predictor_w{horizon}",
                (
                    generator.standard_normal((input_size, self.latent_size))
                    * scale
                ).astype(np.float32),
            )
            setattr(
                self,
                f"predictor_b{horizon}",
                np.zeros(self.latent_size, dtype=np.float32),
            )

        self.value_w = (
            generator.standard_normal((self.latent_size, 1))
            * math.sqrt(2.0 / self.latent_size)
        ).astype(np.float32)
        self.value_b = np.zeros(1, dtype=np.float32)
        self.policy_action_w = (
            generator.standard_normal((ACTION_SIZE, self.latent_size))
            * math.sqrt(2.0 / ACTION_SIZE)
        ).astype(np.float32)
        slices = generator.standard_normal(
            (self.sigreg_slices_count, self.latent_size)
        ).astype(np.float32)
        slices /= np.linalg.norm(slices, axis=1, keepdims=True) + 1e-8
        self.sigreg_slices = slices

    def load(self) -> None:
        with np.load(self.model_path, allow_pickle=False) as data:
            if int(data["model_version"][0]) != MODEL_VERSION:
                raise ValueError("Not a supported LeJEPA checkpoint")
            stored_variant = (
                str(data["model_variant"][0])
                if "model_variant" in data
                else MODEL_VARIANT
            )
            if stored_variant != self.variant:
                raise ValueError(
                    f"Checkpoint variant mismatch: requested={self.variant}, "
                    f"checkpoint={stored_variant}"
                )
            self.latent_size = int(data["latent_size"][0])
            self.trained_steps = int(data["trained_steps"][0])
            self.seed = int(data["seed"][0]) if "seed" in data else self.seed
            self.adam_step = int(data["adam_step"][0])
            self.dataset_fingerprint = str(data["dataset_fingerprint"][0])
            self.sigreg_weight = float(
                data["sigreg_weight"][0]
                if "sigreg_weight" in data
                else 0.20
            )
            self.sigreg_slices_count = int(
                data["sigreg_slices_count"][0]
                if "sigreg_slices_count" in data
                else 32
            )
            self.sigreg_t = (
                data["sigreg_t"]
                if "sigreg_t" in data
                else np.array((0.5, 1.0, 1.5, 2.0), dtype=np.float32)
            ).astype(np.float32)
            for name in self.parameter_names:
                setattr(self, name, data[name].astype(np.float32))
                m_key = "adam_m_" + name
                v_key = "adam_v_" + name
                if m_key in data and v_key in data:
                    self.adam_m[name] = data[m_key].astype(np.float32)
                    self.adam_v[name] = data[v_key].astype(np.float32)
            self.sigreg_slices = data["sigreg_slices"].astype(np.float32)

    def save(self) -> None:
        temporary = self.model_path.with_suffix(".tmp.npz")
        payload = {
            "model_version": np.array([MODEL_VERSION], dtype=np.int64),
            "model_variant": np.array([self.variant]),
            "latent_size": np.array([self.latent_size], dtype=np.int64),
            "trained_steps": np.array([self.trained_steps], dtype=np.int64),
            "seed": np.array([self.seed], dtype=np.int64),
            "adam_step": np.array([self.adam_step], dtype=np.int64),
            "dataset_fingerprint": np.array([self.dataset_fingerprint]),
            "sigreg_weight": np.array([self.sigreg_weight], dtype=np.float32),
            "sigreg_slices_count": np.array(
                [self.sigreg_slices_count], dtype=np.int64
            ),
            "sigreg_t": self.sigreg_t,
            "sigreg_slices": self.sigreg_slices,
        }
        for name in self.parameter_names:
            payload[name] = getattr(self, name)
            if name in self.adam_m and name in self.adam_v:
                payload["adam_m_" + name] = self.adam_m[name]
                payload["adam_v_" + name] = self.adam_v[name]
        np.savez_compressed(temporary, **payload)
        temporary.replace(self.model_path)

    def encode(self, states: np.ndarray) -> np.ndarray:
        return np.tanh(states @ self.encoder_w + self.encoder_b)

    def value(self, latent: np.ndarray) -> np.ndarray:
        return np.tanh(latent @ self.value_w + self.value_b)

    def _adam(self, gradients: dict[str, np.ndarray], learning_rate: float) -> None:
        self.adam_step += 1
        for name, gradient in gradients.items():
            gradient = np.clip(gradient, -1.0, 1.0).astype(np.float32)
            if name not in self.adam_m:
                self.adam_m[name] = np.zeros_like(gradient)
                self.adam_v[name] = np.zeros_like(gradient)
            self.adam_m[name] = 0.9 * self.adam_m[name] + 0.1 * gradient
            self.adam_v[name] = 0.999 * self.adam_v[name] + 0.001 * gradient * gradient
            m_hat = self.adam_m[name] / (1.0 - 0.9**self.adam_step)
            v_hat = self.adam_v[name] / (1.0 - 0.999**self.adam_step)
            setattr(
                self,
                name,
                getattr(self, name)
                - learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8),
            )

    def _sigreg(self, embeddings: np.ndarray) -> tuple[float, np.ndarray]:
        """Match characteristic functions of random slices to N(0, 1)."""
        projected = embeddings @ self.sigreg_slices.T
        arguments = projected[:, :, None] * self.sigreg_t[None, None, :]
        cos_mean = np.mean(np.cos(arguments), axis=0)
        sin_mean = np.mean(np.sin(arguments), axis=0)
        gaussian_cos = np.exp(-0.5 * self.sigreg_t * self.sigreg_t)[None, :]
        cos_error = cos_mean - gaussian_cos
        sin_error = sin_mean
        loss = float(np.mean(cos_error * cos_error + sin_error * sin_error))

        sample_count = max(1, embeddings.shape[0])
        slice_count = max(1, self.sigreg_slices.shape[0])
        point_count = max(1, self.sigreg_t.shape[0])
        projected_gradient = (
            2.0
            / (sample_count * slice_count * point_count)
            * (
                -np.sin(arguments) * self.sigreg_t[None, None, :] * cos_error[None, :, :]
                + np.cos(arguments) * self.sigreg_t[None, None, :] * sin_error[None, :, :]
            )
        )
        embedding_gradient = projected_gradient.sum(axis=2) @ self.sigreg_slices
        return loss, embedding_gradient.astype(np.float32)

    def _prepare_batch(self, samples: list[dict]) -> dict:
        states = np.stack([encode_snapshot(item["state"]) for item in samples])
        next_states = np.stack([encode_snapshot(item["next_state"]) for item in samples])
        own_actions = np.stack([encode_action(item["own_action"]) for item in samples])
        negative_actions = np.stack(
            [encode_action(item["negative_action"]) for item in samples]
        )
        opponent_actions = np.stack([
            encode_action(item["opponent_action"])
            if item["opponent_action"]
            else np.zeros(ACTION_SIZE, dtype=np.float32)
            for item in samples
        ])
        next_our_actions = np.stack([
            encode_action(item["next_our_action"])
            if item["next_our_action"]
            else np.zeros(ACTION_SIZE, dtype=np.float32)
            for item in samples
        ])
        second_opponent_actions = np.stack([
            encode_action(item["second_opponent_action"])
            if item["second_opponent_action"]
            else np.zeros(ACTION_SIZE, dtype=np.float32)
            for item in samples
        ])
        future2_states = np.stack([
            encode_snapshot(item["future2"] or item["next_state"])
            for item in samples
        ])
        future4_states = np.stack([
            encode_snapshot(item["future4"] or item["next_state"])
            for item in samples
        ])
        batch_size = len(samples)
        return {
            "states": states,
            "next_states": next_states,
            "future2_states": future2_states,
            "future4_states": future4_states,
            "own_actions": own_actions,
            "negative_actions": negative_actions,
            "action_sets": {
                1: [own_actions],
                2: [own_actions, opponent_actions],
                4: [
                    own_actions,
                    opponent_actions,
                    next_our_actions,
                    second_opponent_actions,
                ],
            },
            "future2_mask": np.array(
                [item["future2"] is not None for item in samples],
                dtype=np.float32,
            )[:, None],
            "future4_mask": np.array(
                [item["future4"] is not None for item in samples],
                dtype=np.float32,
            )[:, None],
            "outcomes": np.array(
                [item["outcome"] for item in samples], dtype=np.float32
            )[:, None],
            "batch_size": batch_size,
        }

    def _predict(
        self,
        latent: np.ndarray,
        action_set: list[np.ndarray],
        horizon: int,
    ) -> np.ndarray:
        combined = np.concatenate([latent] + action_set, axis=1)
        return np.tanh(
            combined @ getattr(self, f"predictor_w{horizon}")
            + getattr(self, f"predictor_b{horizon}")
        )

    def _forward(self, batch: dict) -> dict:
        latent = self.encode(batch["states"])
        targets = {
            1: self.encode(batch["next_states"]),
            2: self.encode(batch["future2_states"]),
            4: self.encode(batch["future4_states"]),
        }
        masks = {
            1: np.ones((batch["batch_size"], 1), dtype=np.float32),
            2: batch["future2_mask"],
            4: batch["future4_mask"],
        }
        predictions = {
            horizon: self._predict(latent, batch["action_sets"][horizon], horizon)
            for horizon in HORIZONS
        }
        losses = {}
        for horizon in HORIZONS:
            error = (predictions[horizon] - targets[horizon]) * masks[horizon]
            denominator = max(
                1.0,
                float(np.sum(masks[horizon])) * self.latent_size,
            )
            losses[horizon] = float(np.sum(error * error) / denominator)

        value_prediction = self.value(latent)
        value_error = value_prediction - batch["outcomes"]
        value_loss = float(np.mean(value_error * value_error))
        positive_embed = batch["own_actions"] @ self.policy_action_w
        negative_embed = batch["negative_actions"] @ self.policy_action_w
        scale = math.sqrt(self.latent_size)
        positive_score = np.sum(latent * positive_embed, axis=1) / scale
        negative_score = np.sum(latent * negative_embed, axis=1) / scale
        eligible = np.any(batch["own_actions"] != batch["negative_actions"], axis=1)
        margins = np.where(eligible, 0.20 - positive_score + negative_score, 0.0)
        ranking_loss = float(np.mean(np.maximum(0.0, margins)))
        sigreg_input = np.concatenate([latent] + [targets[h] for h in HORIZONS], axis=0)
        sigreg_loss, sigreg_gradient = self._sigreg(sigreg_input)
        return {
            "latent": latent,
            "targets": targets,
            "masks": masks,
            "predictions": predictions,
            "losses": losses,
            "value_prediction": value_prediction,
            "value_error": value_error,
            "positive_embed": positive_embed,
            "negative_embed": negative_embed,
            "margins": margins,
            "sigreg_input": sigreg_input,
            "sigreg_loss": sigreg_loss,
            "sigreg_gradient": sigreg_gradient,
        }

    def _metrics(self, batch: dict, forward: dict) -> dict:
        losses = forward["losses"]
        margins = forward["margins"]
        latent = forward["latent"]
        total_loss = (
            sum(HORIZON_WEIGHTS[h] * losses[h] for h in HORIZONS)
            + float(np.mean(forward["value_error"] ** 2))
            + 0.25 * float(np.mean(np.maximum(0.0, margins)))
            + self.sigreg_weight * forward["sigreg_loss"]
        )
        covariance = np.cov(latent, rowvar=False) if latent.shape[0] > 1 else np.zeros((self.latent_size, self.latent_size))
        effective_rank = float(
            np.trace(covariance) ** 2
            / max(1e-8, np.trace(covariance @ covariance))
        )
        return {
            "loss": float(total_loss),
            "latent_loss": float(sum(HORIZON_WEIGHTS[h] * losses[h] for h in HORIZONS)),
            "latent_loss_h1": losses[1],
            "latent_loss_h2": losses[2],
            "latent_loss_h4": losses[4],
            "h1_loss": losses[1],
            "h2_loss": losses[2],
            "h4_loss": losses[4],
            "value_loss": float(np.mean(forward["value_error"] ** 2)),
            "ranking_loss": float(np.mean(np.maximum(0.0, margins))),
            "sigreg_loss": float(forward["sigreg_loss"]),
            "ranking_accuracy": float(np.sum((margins <= 0) & np.any(batch["own_actions"] != batch["negative_actions"], axis=1)) / max(1, np.sum(np.any(batch["own_actions"] != batch["negative_actions"], axis=1)))),
            "h2_coverage": float(np.mean(forward["masks"][2])),
            "h4_coverage": float(np.mean(forward["masks"][4])),
            "latent_std": float(np.mean(np.std(latent, axis=0))),
            "latent_std_mean": float(np.mean(np.std(latent, axis=0))),
            "effective_rank": effective_rank,
        }

    def train_batch(self, samples: list[dict], learning_rate: float = 5e-4) -> dict:
        if not samples:
            raise ValueError("Empty batch")
        # Refresh random directions per update; seed + step makes resume reproducible.
        rng = np.random.default_rng(self.seed + self.trained_steps)
        slices = rng.normal(size=self.sigreg_slices.shape).astype(np.float32)
        self.sigreg_slices = slices / np.maximum(np.linalg.norm(slices, axis=1, keepdims=True), 1e-8)
        batch = self._prepare_batch(samples)
        forward = self._forward(batch)
        batch_size = batch["batch_size"]
        latent = forward["latent"]
        gradients: dict[str, np.ndarray] = {}
        latent_gradient = np.zeros_like(latent)
        target_gradients = {
            horizon: np.zeros_like(forward["targets"][horizon])
            for horizon in HORIZONS
        }

        for horizon in HORIZONS:
            prediction = forward["predictions"][horizon]
            error = (
                prediction - forward["targets"][horizon]
            ) * forward["masks"][horizon]
            denominator = max(
                1.0,
                float(np.sum(forward["masks"][horizon])) * self.latent_size,
            )
            weighted = HORIZON_WEIGHTS[horizon]
            prediction_gradient = 2.0 * weighted * error / denominator
            pre_gradient = prediction_gradient * (1.0 - prediction * prediction)
            combined = np.concatenate([latent] + batch["action_sets"][horizon], axis=1)
            weight_name = f"predictor_w{horizon}"
            bias_name = f"predictor_b{horizon}"
            gradients[weight_name] = combined.T @ pre_gradient
            gradients[bias_name] = np.sum(pre_gradient, axis=0)
            latent_gradient += pre_gradient @ getattr(self, weight_name)[: self.latent_size].T
            target_gradients[horizon] -= 2.0 * weighted * error / denominator

        sigreg_gradient = forward["sigreg_gradient"].copy()
        sigreg_gradient *= self.sigreg_weight
        latent_gradient += sigreg_gradient[:batch_size]
        offset = batch_size
        for horizon in HORIZONS:
            target_gradients[horizon] += sigreg_gradient[offset : offset + batch_size]
            offset += batch_size

        value_prediction = forward["value_prediction"]
        value_error = forward["value_error"]
        value_pre_gradient = (
            2.0 * value_error * (1.0 - value_prediction * value_prediction) / batch_size
        )
        gradients["value_w"] = latent.T @ value_pre_gradient
        gradients["value_b"] = np.sum(value_pre_gradient, axis=0)
        latent_gradient += value_pre_gradient @ self.value_w.T

        positive_embed = forward["positive_embed"]
        negative_embed = forward["negative_embed"]
        margins = forward["margins"]
        active = (margins > 0).astype(np.float32)[:, None]
        ranking_gradient = active / batch_size
        scale = math.sqrt(self.latent_size)
        latent_gradient += 0.25 * ranking_gradient * (
            -positive_embed + negative_embed
        ) / scale
        gradients["policy_action_w"] = 0.25 * (
            batch["own_actions"].T @ (-ranking_gradient * latent / scale)
            + batch["negative_actions"].T @ (ranking_gradient * latent / scale)
        )

        pre_context = latent_gradient * (1.0 - latent * latent)
        gradients["encoder_w"] = batch["states"].T @ pre_context
        gradients["encoder_b"] = np.sum(pre_context, axis=0)
        for horizon, state_key in (
            (1, "next_states"),
            (2, "future2_states"),
            (4, "future4_states"),
        ):
            target = forward["targets"][horizon]
            pre_target = target_gradients[horizon] * (1.0 - target * target)
            gradients["encoder_w"] += batch[state_key].T @ pre_target
            gradients["encoder_b"] += np.sum(pre_target, axis=0)

        gradients["encoder_w"] = gradients["encoder_w"].astype(np.float32)
        gradients["encoder_b"] = gradients["encoder_b"].astype(np.float32)
        gradient_norm = math.sqrt(
            sum(float(np.sum(value * value)) for value in gradients.values())
        )
        self._adam(gradients, learning_rate)
        self.trained_steps += 1
        metrics = self._metrics(batch, forward)
        metrics["gradient_norm"] = gradient_norm
        return metrics

    def evaluate_batch(self, samples: list[dict]) -> dict:
        if not samples:
            raise ValueError("Empty batch")
        batch = self._prepare_batch(samples)
        return self._metrics(batch, self._forward(batch))

    def danh_gia_snapshot(self, snapshot: dict) -> float:
        encoded = self.encode(encode_snapshot(snapshot)[None, :])
        return float(self.value(encoded)[0, 0])

    def score_legal_moves(
        self,
        snapshot: dict,
        legal_moves: list[tuple[int, int, str]],
        temperature: float = 0.25,
    ) -> tuple[list[float], list[float], float]:
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
