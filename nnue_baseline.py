"""Compact NNUE-style value network for the CAISSA-JEPA chess benchmark.

This is an experiment-friendly NumPy implementation, not a Stockfish-compatible
``.nnue`` file reader.  It keeps the defining comparison properties of NNUE:
 sparse king-conditioned board features, a small clipped non-linearity, a scalar
 position evaluator, and an alpha-beta consumer in the arena.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Union

import numpy as np


MODEL_VERSION = 1
MODEL_VARIANT = "nnue"
PIECE_TYPES = "PNBRQK"
PIECE_PLANE_COUNT = 12
KING_BUCKET_COUNT = 16
PIECE_FEATURE_SIZE = KING_BUCKET_COUNT * PIECE_PLANE_COUNT * 64
FEATURE_SIZE = PIECE_FEATURE_SIZE + 4 + 8
EVALUATION_SCALE = 1000.0


def _mirror_rank(square: int) -> int:
    row, column = divmod(int(square), 8)
    return (7 - row) * 8 + column


def _king_bucket(board, turn: str) -> int:
    king_piece = "K" if turn == "white" else "k"
    king_square = next(
        (index for index, piece in enumerate(board) if piece == king_piece),
        0,
    )
    if turn != "white":
        king_square = _mirror_rank(king_square)
    row, column = divmod(king_square, 8)
    # Four rank bands and four files after horizontal reflection give a
    # compact 16-bucket approximation of Stockfish's king buckets.
    return (row // 2) * 4 + min(column, 7 - column)


def active_feature_indices(snapshot: dict) -> np.ndarray:
    """Return sparse HalfKP-inspired features in side-to-move perspective."""
    turn = snapshot["turn"]
    side_is_white = turn == "white"
    king_bucket = _king_bucket(snapshot["board"], turn)
    indices: list[int] = []

    for square, piece in enumerate(snapshot["board"]):
        if piece == ".":
            continue
        piece_type = PIECE_TYPES.find(piece.upper())
        if piece_type < 0:
            continue
        own_piece = piece.isupper() if side_is_white else piece.islower()
        plane = piece_type if own_piece else 6 + piece_type
        normalized_square = square if side_is_white else _mirror_rank(square)
        indices.append(
            (king_bucket * PIECE_PLANE_COUNT + plane) * 64
            + normalized_square
        )

    rights = snapshot.get("castling_rights", {})
    if side_is_white:
        own_rights = ("white_kingside", "white_queenside")
        opponent_rights = ("black_kingside", "black_queenside")
    else:
        own_rights = ("black_kingside", "black_queenside")
        opponent_rights = ("white_kingside", "white_queenside")

    rights_offset = PIECE_FEATURE_SIZE
    for offset, key in enumerate((*own_rights, *opponent_rights)):
        if rights.get(key, False):
            indices.append(rights_offset + offset)

    en_passant = snapshot.get("en_passant_target")
    if en_passant is not None:
        indices.append(rights_offset + 4 + int(en_passant) % 8)

    return np.asarray(sorted(set(indices)), dtype=np.int64)


def encode_snapshot(snapshot: dict) -> np.ndarray:
    vector = np.zeros(FEATURE_SIZE, dtype=np.float32)
    vector[active_feature_indices(snapshot)] = 1.0
    return vector


class NNUEStyleBaseline:
    """Small trainable NNUE-style evaluator with a stable trainer interface."""

    parameter_names = ("input_w", "input_b", "output_w", "output_b")

    def __init__(
        self,
        model_path: Union[str, Path],
        latent_size: int = 96,
        create_if_missing: bool = True,
        variant: str = MODEL_VARIANT,
    ) -> None:
        if variant != MODEL_VARIANT:
            raise ValueError(f"Unknown NNUE variant: {variant}")
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.hidden_size = int(latent_size)
        if self.hidden_size <= 0:
            raise ValueError("NNUE hidden size must be positive")
        self.latent_size = self.hidden_size
        self.variant = variant
        self.trained_steps = 0
        self.adam_step = 0
        self.adam_m: dict[str, np.ndarray] = {}
        self.adam_v: dict[str, np.ndarray] = {}
        self.dataset_fingerprint = ""
        self.seed = 20260903

        if self.model_path.exists():
            self.load()
        elif create_if_missing:
            self._initialize()
        else:
            raise FileNotFoundError(self.model_path)

    def _initialize(self) -> None:
        generator = np.random.default_rng(self.seed)
        self.input_w = (
            generator.standard_normal((FEATURE_SIZE, self.hidden_size))
            * math.sqrt(2.0 / FEATURE_SIZE)
        ).astype(np.float32)
        self.input_b = np.zeros(self.hidden_size, dtype=np.float32)
        self.output_w = (
            generator.standard_normal((self.hidden_size, 1))
            * math.sqrt(2.0 / self.hidden_size)
        ).astype(np.float32)
        self.output_b = np.zeros(1, dtype=np.float32)

    def load(self) -> None:
        with np.load(self.model_path, allow_pickle=False) as data:
            if int(data["model_version"][0]) != MODEL_VERSION:
                raise ValueError("Not a supported NNUE-style checkpoint")
            stored_variant = (
                str(data["model_variant"][0])
                if "model_variant" in data
                else MODEL_VARIANT
            )
            if stored_variant != MODEL_VARIANT:
                raise ValueError(f"Unknown NNUE checkpoint variant: {stored_variant}")
            self.hidden_size = int(data["hidden_size"][0])
            self.latent_size = self.hidden_size
            self.trained_steps = int(data["trained_steps"][0])
            self.seed = int(data["seed"][0]) if "seed" in data else self.seed
            self.adam_step = int(data["adam_step"][0])
            self.dataset_fingerprint = str(data["dataset_fingerprint"][0])
            for name in self.parameter_names:
                setattr(self, name, data[name].astype(np.float32))
                m_key = "adam_m_" + name
                v_key = "adam_v_" + name
                if m_key in data and v_key in data:
                    self.adam_m[name] = data[m_key].astype(np.float32)
                    self.adam_v[name] = data[v_key].astype(np.float32)

    def save(self) -> None:
        temporary = self.model_path.with_suffix(".tmp.npz")
        payload = {
            "model_version": np.array([MODEL_VERSION], dtype=np.int64),
            "model_variant": np.array([MODEL_VARIANT]),
            "feature_size": np.array([FEATURE_SIZE], dtype=np.int64),
            "hidden_size": np.array([self.hidden_size], dtype=np.int64),
            "trained_steps": np.array([self.trained_steps], dtype=np.int64),
            "seed": np.array([self.seed], dtype=np.int64),
            "adam_step": np.array([self.adam_step], dtype=np.int64),
            "dataset_fingerprint": np.array([self.dataset_fingerprint]),
            "evaluation_scale": np.array([EVALUATION_SCALE], dtype=np.float32),
        }
        for name in self.parameter_names:
            payload[name] = getattr(self, name)
            if name in self.adam_m and name in self.adam_v:
                payload["adam_m_" + name] = self.adam_m[name]
                payload["adam_v_" + name] = self.adam_v[name]
        np.savez_compressed(temporary, **payload)
        temporary.replace(self.model_path)

    def _prepare_batch(self, samples: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        features = np.stack([encode_snapshot(item["state"]) for item in samples])
        targets = np.clip(
            np.asarray([item["outcome"] for item in samples], dtype=np.float32),
            -1.0,
            1.0,
        )[:, None]
        return features, targets

    def _sparse_batch(self, samples):
        indices = [active_feature_indices(item["state"]) for item in samples]
        pre = np.stack([self.input_b + self.input_w[index].sum(axis=0) for index in indices])
        hidden = self._squared_clipped_relu(pre)
        pre_value = hidden @ self.output_w + self.output_b
        targets = np.clip(np.asarray([s["outcome"] for s in samples], dtype=np.float32), -1, 1)[:, None]
        return indices, targets, {"pre_activation": pre, "hidden": hidden,
                                  "pre_value": pre_value, "value": np.tanh(pre_value)}

    @staticmethod
    def _squared_clipped_relu(pre_activation: np.ndarray) -> np.ndarray:
        clipped = np.clip(pre_activation, 0.0, 1.0)
        return clipped * clipped

    @staticmethod
    def _squared_clipped_relu_gradient(pre_activation: np.ndarray) -> np.ndarray:
        clipped = np.clip(pre_activation, 0.0, 1.0)
        return 2.0 * clipped * (pre_activation > 0.0) * (pre_activation < 1.0)

    def _forward(self, features: np.ndarray) -> dict[str, np.ndarray]:
        pre_activation = features @ self.input_w + self.input_b
        hidden = self._squared_clipped_relu(pre_activation)
        pre_value = hidden @ self.output_w + self.output_b
        value = np.tanh(pre_value)
        return {
            "pre_activation": pre_activation,
            "hidden": hidden,
            "pre_value": pre_value,
            "value": value,
        }

    def _forward_active(self, indices: np.ndarray) -> dict[str, np.ndarray]:
        """Evaluate sparse features without materializing a dense board vector."""
        pre_activation = self.input_b + np.sum(self.input_w[indices], axis=0)
        hidden = self._squared_clipped_relu(pre_activation)
        pre_value = hidden @ self.output_w + self.output_b
        value = np.tanh(pre_value)
        return {
            "pre_activation": pre_activation,
            "hidden": hidden,
            "pre_value": pre_value,
            "value": value,
        }

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

    def _metrics(
        self,
        targets: np.ndarray,
        forward: dict[str, np.ndarray],
    ) -> dict:
        value = forward["value"]
        error = value - targets
        loss = float(np.mean(error * error))
        predicted_sign = value >= 0.0
        target_sign = targets >= 0.0
        return {
            "loss": loss,
            "value_loss": loss,
            "value_accuracy": float(np.mean(predicted_sign == target_sign)),
            "mean_value": float(np.mean(value)),
            "hidden_active_fraction": float(np.mean(forward["pre_activation"] > 0.0)),
            "hidden_saturated_fraction": float(np.mean(forward["pre_activation"] >= 1.0)),
        }

    def train_batch(self, samples: list[dict], learning_rate: float = 5e-4) -> dict:
        if not samples:
            raise ValueError("Empty batch")
        indices, targets, forward = self._sparse_batch(samples)
        batch_size = len(samples)
        value = forward["value"]
        error = value - targets
        value_pre_gradient = 2.0 * error * (1.0 - value * value) / batch_size
        gradients = {
            "output_w": forward["hidden"].T @ value_pre_gradient,
            "output_b": np.sum(value_pre_gradient, axis=0),
        }
        hidden_gradient = value_pre_gradient @ self.output_w.T
        pre_gradient = hidden_gradient * self._squared_clipped_relu_gradient(
            forward["pre_activation"]
        )
        # Preserve dense Adam momentum semantics, but avoid the enormous dense
        # input matrix and its matrix multiplications.
        gradients["input_w"] = np.zeros_like(self.input_w)
        for index, gradient in zip(indices, pre_gradient):
            np.add.at(gradients["input_w"], index, gradient)
        gradients["input_b"] = np.sum(pre_gradient, axis=0)
        gradient_norm = math.sqrt(
            sum(float(np.sum(value * value)) for value in gradients.values())
        )
        self._adam(gradients, learning_rate)
        self.trained_steps += 1
        metrics = self._metrics(targets, forward)
        metrics["gradient_norm"] = gradient_norm
        return metrics

    def evaluate_batch(self, samples: list[dict]) -> dict:
        if not samples:
            raise ValueError("Empty batch")
        _, targets, forward = self._sparse_batch(samples)
        return self._metrics(targets, forward)

    def _predict_features(self, indices: np.ndarray) -> float:
        value = self._forward_active(indices)["value"]
        return float(np.ravel(value)[0])

    def danh_gia_snapshot(self, snapshot: dict) -> float:
        """Return value from the side-to-move perspective in [-1, 1]."""
        return self._predict_features(active_feature_indices(snapshot))

    def danh_gia_engine(self, engine) -> float:
        snapshot = {
            "board": engine.board,
            "turn": engine.turn,
            "castling_rights": engine.castling_rights,
            "en_passant_target": engine.en_passant_target,
        }
        return self.danh_gia_snapshot(snapshot)

    def evaluate_engine_score(self, engine) -> float:
        """Return a centipawn-like score for the existing alpha-beta search."""
        return self.danh_gia_engine(engine) * EVALUATION_SCALE

    def score_legal_moves(
        self,
        snapshot: dict,
        legal_moves: list[tuple[int, int, str]],
        temperature: float = 0.25,
    ) -> tuple[list[float], list[float], float]:
        """Expose a compatible policy view for diagnostics, not arena search."""
        if not legal_moves:
            return [], [], 1.0
        from main import vitriengine

        scores = []
        for move in legal_moves:
            child = vitriengine(snapshot, 0.02)
            child.thuc_hien_nuoc_di(move)
            scores.append(-self.danh_gia_engine(child))
        score_array = np.asarray(scores, dtype=np.float32)
        shifted = (score_array - np.max(score_array)) / max(0.03, temperature)
        priors = np.exp(shifted - np.max(shifted))
        priors /= np.sum(priors) + 1e-8
        entropy = -float(np.sum(priors * np.log(priors + 1e-8)))
        if len(priors) > 1:
            entropy /= math.log(len(priors))
        return scores, priors.tolist(), entropy
