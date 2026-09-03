"""CAISSA-JEPA v7: action-sequence and opponent-conditioned chess JEPA.

This module intentionally keeps exact chess rules outside the learned model.
Rules enumerate legal action/response branches; the model learns a compact
representation and robust branch score.  It is a research baseline, not a
claim of superiority over direct policy/value learning.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Iterator, Optional, Union

import numpy as np

from main import pgnparser, text_thanh_move, vitriengine


MODEL_VERSION = 7
STATE_SIZE = 12 * 64 + 1 + 4 + 8
ACTION_SIZE = 64 + 64 + 5
PIECE_ORDER = "PNBRQKpnbrqk"

MODEL_VARIANTS = {
    "h1": {
        "enabled_horizons": (1,),
        "response_conditioned": True,
    },
    "h1-h2": {
        "enabled_horizons": (1, 2),
        "response_conditioned": True,
    },
    "full": {
        "enabled_horizons": (1, 2, 4),
        "response_conditioned": True,
    },
    "no-response": {
        "enabled_horizons": (1, 2, 4),
        "response_conditioned": False,
    },
}


def dataset_manifest_fingerprint(dataset_dir: Path) -> str:
    manifest = dataset_dir / "dataset_manifest.json"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def iter_dataset_games(dataset_dir: Path) -> Iterator[dict]:
    manifest = json.loads((dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    for shard in manifest.get("shards", []):
        with (dataset_dir / shard["path"]).open("rb") as handle:
            for raw_line in handle:
                yield json.loads(raw_line)


def stable_split(game_hash: str, validation_percent: int = 10) -> str:
    bucket = int(game_hash[:8], 16) % 100
    return "validation" if bucket < validation_percent else "train"


def snapshot_from_fen(fen: str) -> dict:
    return pgnparser().fen_thanh_snapshot(fen)


def move_from_uci(uci: Optional[str], side: str):
    if not uci:
        return None
    return text_thanh_move(uci, side)


def encode_snapshot(snapshot: dict) -> np.ndarray:
    vector = np.zeros(STATE_SIZE, dtype=np.float32)
    piece_map = {piece: index for index, piece in enumerate(PIECE_ORDER)}
    for square, piece in enumerate(snapshot["board"]):
        if piece != ".":
            vector[piece_map[piece] * 64 + square] = 1.0
    offset = 12 * 64
    vector[offset] = 1.0 if snapshot["turn"] == "white" else -1.0
    offset += 1
    for key in ("white_kingside", "white_queenside", "black_kingside", "black_queenside"):
        vector[offset] = float(snapshot["castling_rights"].get(key, False))
        offset += 1
    en_passant = snapshot.get("en_passant_target")
    if en_passant is not None:
        vector[offset + en_passant % 8] = 1.0
    return vector


def encode_action(move) -> np.ndarray:
    vector = np.zeros(ACTION_SIZE, dtype=np.float32)
    from_index, to_index, promotion = move
    vector[from_index] = 1.0
    vector[64 + to_index] = 1.0
    promotion_map = {"Q": 0, "R": 1, "B": 2, "N": 3, None: 4}
    vector[128 + promotion_map[promotion.upper() if promotion else None]] = 1.0
    return vector


def snapshot_from_engine(engine: vitriengine) -> dict:
    return {
        "board": engine.board.copy(),
        "turn": engine.turn,
        "castling_rights": engine.castling_rights.copy(),
        "en_passant_target": engine.en_passant_target,
        "halfmove_clock": engine.halfmove_clock,
        "position_counts": engine.position_counts.copy(),
    }


def sample_from_dataset_position(position: dict, random_generator: np.random.Generator) -> Optional[dict]:
    """Convert one portable FEN record into a checked training sample."""
    try:
        state = snapshot_from_fen(position["fen"])
        next_state = snapshot_from_fen(position["next_fen"])
        own_action = move_from_uci(position["action_uci"], state["turn"])
        if own_action is None:
            return None
        engine = vitriengine(state, 0.02)
        legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
        if own_action not in legal_moves:
            return None
        alternatives = [move for move in legal_moves if move != own_action]
        negative_action = alternatives[int(random_generator.integers(len(alternatives)))] if alternatives else own_action
        opponent_action = move_from_uci(position.get("opponent_action_uci"), "black" if state["turn"] == "white" else "white")
        next_our_action = move_from_uci(position.get("next_our_action_uci"), state["turn"])
        second_opponent_action = move_from_uci(position.get("second_opponent_action_uci"), "black" if state["turn"] == "white" else "white")
        future2 = snapshot_from_fen(position["future2_fen"]) if position.get("future2_fen") else None
        future4 = snapshot_from_fen(position["future4_fen"]) if position.get("future4_fen") else None
        return {
            "state": state,
            "next_state": next_state,
            "future2": future2,
            "future4": future4,
            "own_action": own_action,
            "opponent_action": opponent_action,
            "next_our_action": next_our_action,
            "second_opponent_action": second_opponent_action,
            "negative_action": negative_action,
            "outcome": float(position["outcome_pov"]),
        }
    except (KeyError, TypeError, ValueError):
        return None


class AdversarialJEPA:
    """Small NumPy A-JEPA baseline with exact response-branch scoring."""

    trainable_names = (
        "encoder_w", "encoder_b", "predictor_w1", "predictor_b1",
        "predictor_w2", "predictor_b2", "predictor_w4", "predictor_b4",
        "value_w", "value_b", "policy_action_w",
    )

    def __init__(
        self,
        model_path: Union[Path, str],
        latent_size: int = 96,
        create_if_missing: bool = True,
        variant: str = "full",
    ) -> None:
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.latent_size = int(latent_size)
        self.trained_steps = 0
        self.adam_step = 0
        self.adam_m: dict[str, np.ndarray] = {}
        self.adam_v: dict[str, np.ndarray] = {}
        self.dataset_fingerprint = ""
        self.seed = 20260903
        if variant not in MODEL_VARIANTS:
            raise ValueError(f"Unknown A-JEPA model variant: {variant}")
        self.variant = variant
        self.enabled_horizons = MODEL_VARIANTS[variant]["enabled_horizons"]
        self.response_conditioned = MODEL_VARIANTS[variant]["response_conditioned"]
        if self.model_path.exists():
            self.load()
        elif create_if_missing:
            self._initialize()
        else:
            raise FileNotFoundError(self.model_path)

    def _initialize(self) -> None:
        generator = np.random.default_rng(self.seed)
        self.encoder_w = (generator.standard_normal((STATE_SIZE, self.latent_size)) * math.sqrt(2 / STATE_SIZE)).astype(np.float32)
        self.encoder_b = np.zeros(self.latent_size, dtype=np.float32)
        self.target_w = self.encoder_w.copy()
        self.target_b = self.encoder_b.copy()
        for horizon, action_count in ((1, 1), (2, 2), (4, 4)):
            width = self.latent_size + ACTION_SIZE * action_count
            setattr(self, f"predictor_w{horizon}", (generator.standard_normal((width, self.latent_size)) * math.sqrt(2 / width)).astype(np.float32))
            setattr(self, f"predictor_b{horizon}", np.zeros(self.latent_size, dtype=np.float32))
        self.value_w = (generator.standard_normal((self.latent_size, 1)) * math.sqrt(2 / self.latent_size)).astype(np.float32)
        self.value_b = np.zeros(1, dtype=np.float32)
        self.policy_action_w = (generator.standard_normal((ACTION_SIZE, self.latent_size)) * math.sqrt(2 / ACTION_SIZE)).astype(np.float32)

    def load(self) -> None:
        with np.load(self.model_path, allow_pickle=False) as data:
            version = int(data["model_version"][0])
            if version != MODEL_VERSION:
                raise ValueError(f"Checkpoint không phải A-JEPA v{MODEL_VERSION}: v{version}")
            self.latent_size = int(data["latent_size"][0])
            for name in self.trainable_names + ("target_w", "target_b"):
                setattr(self, name, data[name].astype(np.float32))
            self.trained_steps = int(data["trained_steps"][0])
            self.adam_step = int(data["adam_step"][0])
            self.dataset_fingerprint = str(data["dataset_fingerprint"][0])
            self.seed = int(data["seed"][0])
            stored_variant = "full"
            if "model_variant" in data:
                stored_variant = str(data["model_variant"][0])
            if stored_variant not in MODEL_VARIANTS:
                raise ValueError(f"Unknown checkpoint variant: {stored_variant}")
            if stored_variant != self.variant:
                raise ValueError(
                    f"Checkpoint variant mismatch: requested={self.variant}, "
                    f"checkpoint={stored_variant}"
                )
            self.variant = stored_variant
            self.enabled_horizons = MODEL_VARIANTS[stored_variant]["enabled_horizons"]
            self.response_conditioned = MODEL_VARIANTS[stored_variant]["response_conditioned"]
            for name in self.trainable_names:
                m_key, v_key = "adam_m_" + name, "adam_v_" + name
                if m_key in data and v_key in data:
                    self.adam_m[name] = data[m_key].astype(np.float32)
                    self.adam_v[name] = data[v_key].astype(np.float32)

    def save(self) -> None:
        temporary = self.model_path.with_suffix(".tmp.npz")
        payload = {
            "model_version": np.array([MODEL_VERSION], dtype=np.int64),
            "latent_size": np.array([self.latent_size], dtype=np.int64),
            "trained_steps": np.array([self.trained_steps], dtype=np.int64),
            "adam_step": np.array([self.adam_step], dtype=np.int64),
            "dataset_fingerprint": np.array([self.dataset_fingerprint]),
            "seed": np.array([self.seed], dtype=np.int64),
            "model_variant": np.array([self.variant]),
            "target_w": self.target_w,
            "target_b": self.target_b,
        }
        for name in self.trainable_names:
            payload[name] = getattr(self, name)
            if name in self.adam_m:
                payload["adam_m_" + name] = self.adam_m[name]
                payload["adam_v_" + name] = self.adam_v[name]
        np.savez_compressed(temporary, **payload)
        temporary.replace(self.model_path)

    def encode(self, states: np.ndarray, target: bool = False) -> np.ndarray:
        weights = self.target_w if target else self.encoder_w
        bias = self.target_b if target else self.encoder_b
        return np.tanh(states @ weights + bias)

    def value(self, latent: np.ndarray) -> np.ndarray:
        return np.tanh(latent @ self.value_w + self.value_b)

    def _predict(self, latent: np.ndarray, actions: list[np.ndarray], horizon: int) -> np.ndarray:
        combined = np.concatenate([latent] + actions, axis=1)
        return np.tanh(combined @ getattr(self, f"predictor_w{horizon}") + getattr(self, f"predictor_b{horizon}"))

    def _adam(self, gradients: dict[str, np.ndarray], learning_rate: float) -> None:
        self.adam_step += 1
        for name, gradient in gradients.items():
            gradient = np.clip(gradient, -1.0, 1.0).astype(np.float32)
            if name not in self.adam_m:
                self.adam_m[name] = np.zeros_like(gradient)
                self.adam_v[name] = np.zeros_like(gradient)
            self.adam_m[name] = 0.9 * self.adam_m[name] + 0.1 * gradient
            self.adam_v[name] = 0.999 * self.adam_v[name] + 0.001 * gradient * gradient
            m_hat = self.adam_m[name] / (1 - 0.9**self.adam_step)
            v_hat = self.adam_v[name] / (1 - 0.999**self.adam_step)
            setattr(self, name, getattr(self, name) - learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8))

    def train_batch(self, samples: list[dict], learning_rate: float = 5e-4) -> dict:
        if not samples:
            raise ValueError("Batch rỗng")
        batch_size = len(samples)
        states = np.stack([encode_snapshot(item["state"]) for item in samples])
        next_states = np.stack([encode_snapshot(item["next_state"]) for item in samples])
        own_actions = np.stack([encode_action(item["own_action"]) for item in samples])
        negative_actions = np.stack([encode_action(item["negative_action"]) for item in samples])
        outcomes = np.array([item["outcome"] for item in samples], dtype=np.float32)[:, None]
        opponent_mask = np.array([
            item["future2"] is not None
            and (not self.response_conditioned or item["opponent_action"] is not None)
            for item in samples
        ], dtype=np.float32)[:, None]
        horizon4_mask = np.array([
            item["future4"] is not None
            and (
                not self.response_conditioned
                or (
                    item["opponent_action"] is not None
                    and item["next_our_action"] is not None
                    and item["second_opponent_action"] is not None
                )
            )
            for item in samples
        ], dtype=np.float32)[:, None]
        opponent_actions = np.stack([encode_action(item["opponent_action"]) if item["opponent_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        next_our_actions = np.stack([encode_action(item["next_our_action"]) if item["next_our_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        second_opponent_actions = np.stack([encode_action(item["second_opponent_action"]) if item["second_opponent_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        future2_states = np.stack([encode_snapshot(item["future2"] or item["next_state"]) for item in samples])
        future4_states = np.stack([encode_snapshot(item["future4"] or item["next_state"]) for item in samples])

        latent = self.encode(states)
        targets = {
            1: self.encode(next_states, target=True),
            2: self.encode(future2_states, target=True),
            4: self.encode(future4_states, target=True),
        }
        neutral_action = np.zeros(ACTION_SIZE, dtype=np.float32)
        action_sets = {
            1: [own_actions],
            2: [own_actions, opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0)],
            4: [
                own_actions,
                opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
                next_our_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
                second_opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
            ],
        }
        masks = {
            1: np.ones((batch_size, 1), dtype=np.float32),
            2: opponent_mask if 2 in self.enabled_horizons else np.zeros((batch_size, 1), dtype=np.float32),
            4: horizon4_mask if 4 in self.enabled_horizons else np.zeros((batch_size, 1), dtype=np.float32),
        }
        weights = {1: 1.0, 2: 0.75, 4: 0.50}
        gradients: dict[str, np.ndarray] = {}
        latent_gradient = np.zeros_like(latent)
        losses: dict[int, float] = {}

        for horizon in (1, 2, 4):
            prediction = self._predict(latent, action_sets[horizon], horizon)
            mask = masks[horizon]
            denominator = max(1.0, float(np.sum(mask)) * self.latent_size)
            error = (prediction - targets[horizon]) * mask
            losses[horizon] = float(np.sum(error * error) / denominator)
            prediction_gradient = 2.0 * weights[horizon] * error / denominator
            pre_gradient = prediction_gradient * (1.0 - prediction * prediction)
            combined = np.concatenate([latent] + action_sets[horizon], axis=1)
            weight_name, bias_name = f"predictor_w{horizon}", f"predictor_b{horizon}"
            gradients[weight_name] = combined.T @ pre_gradient
            gradients[bias_name] = np.sum(pre_gradient, axis=0)
            latent_gradient += pre_gradient @ getattr(self, weight_name)[:self.latent_size].T

        value_prediction = self.value(latent)
        value_error = value_prediction - outcomes
        value_loss = float(np.mean(value_error * value_error))
        value_pre_gradient = 2.0 * value_error * (1.0 - value_prediction * value_prediction) / batch_size
        gradients["value_w"] = latent.T @ value_pre_gradient
        gradients["value_b"] = np.sum(value_pre_gradient, axis=0)
        latent_gradient += value_pre_gradient @ self.value_w.T

        positive_embed = own_actions @ self.policy_action_w
        negative_embed = negative_actions @ self.policy_action_w
        scale = math.sqrt(self.latent_size)
        positive_score = np.sum(latent * positive_embed, axis=1) / scale
        negative_score = np.sum(latent * negative_embed, axis=1) / scale
        margins = 0.20 - positive_score + negative_score
        active = (margins > 0).astype(np.float32)[:, None]
        ranking_loss = float(np.mean(np.maximum(0.0, margins)))
        ranking_gradient = active / batch_size
        latent_gradient += 0.25 * ranking_gradient * (-positive_embed + negative_embed) / scale
        gradients["policy_action_w"] = 0.25 * (
            own_actions.T @ (-ranking_gradient * latent / scale)
            + negative_actions.T @ (ranking_gradient * latent / scale)
        )

        variance = np.var(latent, axis=0)
        low_variance = variance < 0.05
        variance_loss = float(np.mean(np.maximum(0.0, 0.05 - variance)))
        if np.any(low_variance):
            centered = latent - np.mean(latent, axis=0, keepdims=True)
            variance_gradient = np.zeros_like(latent)
            variance_gradient[:, low_variance] = -2 * centered[:, low_variance] / (batch_size * self.latent_size)
            latent_gradient += 0.05 * variance_gradient

        pre_encoder_gradient = latent_gradient * (1.0 - latent * latent)
        gradients["encoder_w"] = states.T @ pre_encoder_gradient
        gradients["encoder_b"] = np.sum(pre_encoder_gradient, axis=0)
        gradient_norm = math.sqrt(sum(float(np.sum(value * value)) for value in gradients.values()))
        self._adam(gradients, learning_rate)
        self.target_w = 0.995 * self.target_w + 0.005 * self.encoder_w
        self.target_b = 0.995 * self.target_b + 0.005 * self.encoder_b
        self.trained_steps += 1
        return {
            "loss": sum(weights[horizon] * losses[horizon] for horizon in (1, 2, 4)) + value_loss + ranking_loss + variance_loss,
            "h1_loss": losses[1], "h2_loss": losses[2], "h4_loss": losses[4],
            "value_loss": value_loss, "ranking_loss": ranking_loss,
            "variance_loss": variance_loss,
            "ranking_accuracy": float(np.mean(margins <= 0)),
            "h2_coverage": float(np.mean(opponent_mask)),
            "h4_coverage": float(np.mean(horizon4_mask)),
            "latent_std": float(np.mean(np.std(latent, axis=0))),
            "gradient_norm": gradient_norm,
        }

    def evaluate_batch(self, samples: list[dict]) -> dict:
        """Held-out metrics with no optimizer, EMA, or checkpoint mutation."""
        if not samples:
            raise ValueError("Batch rỗng")
        batch_size = len(samples)
        states = np.stack([encode_snapshot(item["state"]) for item in samples])
        next_states = np.stack([encode_snapshot(item["next_state"]) for item in samples])
        own_actions = np.stack([encode_action(item["own_action"]) for item in samples])
        negative_actions = np.stack([encode_action(item["negative_action"]) for item in samples])
        outcomes = np.array([item["outcome"] for item in samples], dtype=np.float32)[:, None]
        opponent_mask = np.array([
            item["future2"] is not None
            and (not self.response_conditioned or item["opponent_action"] is not None)
            for item in samples
        ], dtype=np.float32)[:, None]
        horizon4_mask = np.array([
            item["future4"] is not None
            and (
                not self.response_conditioned
                or (
                    item["opponent_action"] is not None
                    and item["next_our_action"] is not None
                    and item["second_opponent_action"] is not None
                )
            )
            for item in samples
        ], dtype=np.float32)[:, None]
        opponent_actions = np.stack([encode_action(item["opponent_action"]) if item["opponent_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        next_our_actions = np.stack([encode_action(item["next_our_action"]) if item["next_our_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        second_opponent_actions = np.stack([encode_action(item["second_opponent_action"]) if item["second_opponent_action"] else np.zeros(ACTION_SIZE, dtype=np.float32) for item in samples])
        future2_states = np.stack([encode_snapshot(item["future2"] or item["next_state"]) for item in samples])
        future4_states = np.stack([encode_snapshot(item["future4"] or item["next_state"]) for item in samples])
        latent = self.encode(states)
        targets = {
            1: self.encode(next_states, target=True),
            2: self.encode(future2_states, target=True),
            4: self.encode(future4_states, target=True),
        }
        neutral_action = np.zeros(ACTION_SIZE, dtype=np.float32)
        action_sets = {
            1: [own_actions],
            2: [own_actions, opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0)],
            4: [
                own_actions,
                opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
                next_our_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
                second_opponent_actions if self.response_conditioned else np.repeat(neutral_action[None, :], batch_size, axis=0),
            ],
        }
        masks = {
            1: np.ones((batch_size, 1), dtype=np.float32),
            2: opponent_mask if 2 in self.enabled_horizons else np.zeros((batch_size, 1), dtype=np.float32),
            4: horizon4_mask if 4 in self.enabled_horizons else np.zeros((batch_size, 1), dtype=np.float32),
        }
        losses = {}
        for horizon in (1, 2, 4):
            prediction = self._predict(latent, action_sets[horizon], horizon)
            mask = masks[horizon]
            losses[horizon] = float(np.sum(((prediction - targets[horizon]) * mask) ** 2) / max(1.0, float(np.sum(mask)) * self.latent_size))
        value_prediction = self.value(latent)
        value_loss = float(np.mean((value_prediction - outcomes) ** 2))
        positive_score = np.sum(latent * (own_actions @ self.policy_action_w), axis=1) / math.sqrt(self.latent_size)
        negative_score = np.sum(latent * (negative_actions @ self.policy_action_w), axis=1) / math.sqrt(self.latent_size)
        margins = 0.20 - positive_score + negative_score
        ranking_loss = float(np.mean(np.maximum(0.0, margins)))
        return {
            "loss": losses[1] + losses[2] + losses[4] + value_loss + ranking_loss,
            "h1_loss": losses[1], "h2_loss": losses[2], "h4_loss": losses[4],
            "value_loss": value_loss, "ranking_loss": ranking_loss,
            "ranking_accuracy": float(np.mean(margins <= 0)),
            "h2_coverage": float(np.mean(opponent_mask)),
            "h4_coverage": float(np.mean(horizon4_mask)),
            "latent_std": float(np.mean(np.std(latent, axis=0))),
        }

    def danh_gia_snapshot(self, snapshot: dict) -> float:
        latent = self.encode(encode_snapshot(snapshot)[None, :])
        return float(self.value(latent)[0, 0])

    def score_legal_moves(
        self,
        snapshot: dict,
        legal_moves: list,
        temperature: float = 0.25,
        max_opponent_branches: Optional[int] = None,
    ) -> tuple[list[float], list[float], float]:
        """Robust action priors by explicitly pooling opponent replies.

        The returned score is the minimum predicted root-perspective value over
        legal opponent responses.  ``max_opponent_branches`` is opt-in only;
        leaving it None evaluates every legal response.
        """
        if not legal_moves:
            return [], [], 1.0
        root_latent = self.encode(encode_snapshot(snapshot)[None, :])
        raw_scores = []
        for move in legal_moves:
            engine = vitriengine(snapshot, 0.02)
            undo = engine.thuc_hien_nuoc_di(move)
            try:
                replies = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
                terminal = 0.0 if engine.is_draw_search() else None
                if not replies:
                    terminal = -1.0 if engine.is_king_in_check(engine.turn) else 0.0
                if terminal is not None:
                    raw_scores.append(terminal)
                    continue
                if max_opponent_branches is not None:
                    replies = replies[:max(1, max_opponent_branches)]
                response_batch = np.stack([encode_action(reply) for reply in replies])
                own_batch = np.repeat(encode_action(move)[None, :], len(replies), axis=0)
                latent_batch = np.repeat(root_latent, len(replies), axis=0)
                predicted = self._predict(latent_batch, [own_batch, response_batch], 2)
                branch_values = self.value(predicted)[:, 0]
                raw_scores.append(float(np.min(branch_values)))
            finally:
                engine.hoan_tac_nuoc_di(undo)
        scores = np.array(raw_scores, dtype=np.float32)
        stable = (scores - np.max(scores)) / max(0.03, float(temperature))
        priors = np.exp(stable)
        priors /= np.sum(priors) + 1e-8
        entropy = -float(np.sum(priors * np.log(priors + 1e-8)))
        if len(priors) > 1:
            entropy /= math.log(len(priors))
        return raw_scores, priors.tolist(), entropy
