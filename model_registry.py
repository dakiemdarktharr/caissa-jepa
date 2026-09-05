"""Shared experiment model registry for the CAISSA-JEPA GUI and arena.

The registry deliberately contains only models that have an implementation in
this repository.  A model is not shown as ready for arena play until its
checkpoint exists and can be loaded by the corresponding engine wrapper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


TRAINING_MODEL_DEFINITIONS = (
    {
        "id": "a-jepa-h1",
        "label": "JEPA One-Step EMA",
        "architecture": "adversarial-jepa",
        "variant": "h1",
        "filename": "caissa_a_jepa_h1.npz",
        "trainable": True,
    },
    {
        "id": "a-jepa-v7",
        "label": "JEPA Multi-Horizon Response EMA",
        "architecture": "adversarial-jepa",
        "variant": "full",
        "filename": "caissa_a_jepa_v7.npz",
        "trainable": True,
    },
    {
        "id": "lejepa-sigreg",
        "label": "LeJEPA SIGReg No-EMA",
        "architecture": "lejepa",
        "variant": "sigreg",
        "filename": "lejepa_sigreg.npz",
        "trainable": True,
    },
    {
        "id": "policy-value-v1",
        "label": "Direct Policy / Value v1",
        "architecture": "policy-value",
        "variant": "direct",
        "filename": "policy_value_baseline.npz",
        "trainable": True,
    },
    {
        "id": "nnue-style-v1",
        "label": "NNUE-style + Alpha-Beta v1",
        "architecture": "nnue",
        "variant": "nnue",
        "filename": "nnue_style_baseline.npz",
        "trainable": True,
    },
)


def _alpha_beta_spec() -> dict:
    return {
        "id": "alpha-beta",
        "label": "Classical Alpha-Beta",
        "architecture": "alpha-beta",
        "variant": "reference",
        "filename": "",
        "path": None,
        "trainable": False,
    }


def _legacy_jepa_spec(project_dir: Path) -> dict:
    return {
        "id": "legacy-caissa-jepa",
        "label": "Legacy CAISSA-JEPA v6",
        "architecture": "legacy-jepa",
        "variant": "legacy",
        "filename": "caissa_jepa.npz",
        "path": Path(project_dir) / "chess_data" / "caissa_jepa.npz",
        "trainable": False,
    }


def training_model_specs(project_dir: Path) -> list[dict]:
    """Return independent, resolved model specifications for the GUI."""
    root = Path(project_dir)
    return [
        {**definition, "path": root / "chess_data" / definition["filename"]}
        for definition in TRAINING_MODEL_DEFINITIONS
    ]


def arena_model_specs(project_dir: Path) -> list[dict]:
    """Return ready checkpoints plus the deterministic alpha-beta reference."""
    ready = [
        spec
        for spec in training_model_specs(project_dir)
        if spec["path"].exists()
    ]
    return [_alpha_beta_spec(), *ready]


def spec_by_id(project_dir: Path, model_id: str) -> Optional[dict]:
    """Resolve a trainable or arena model by its stable id."""
    for spec in [
        *training_model_specs(project_dir),
        _alpha_beta_spec(),
    ]:
        if spec["id"] == model_id:
            return spec
    return None
