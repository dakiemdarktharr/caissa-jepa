"""Shared experiment model registry for the MARS-JEPA Chess GUI and arena.

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
        "label": "MARS-JEPA H1 Response EMA",
        "architecture": "adversarial-jepa",
        "variant": "h1",
        "filename": "caissa_a_jepa_h1.npz",
        "trainable": True,
    },
    {
        "id": "a-jepa-v7",
        "label": "MARS-JEPA H1/H2/H4 Response EMA",
        "architecture": "adversarial-jepa",
        "variant": "full",
        "filename": "caissa_a_jepa_v7.npz",
        "trainable": True,
    },
    {
        "id": "a-jepa-h1-h2", "label": "MARS-JEPA H1/H2 Response EMA",
        "architecture": "adversarial-jepa", "variant": "h1-h2",
        "filename": "caissa_a_jepa_h1_h2.npz", "trainable": True,
    },
    {
        "id": "a-jepa-no-response", "label": "MARS-JEPA No Response EMA",
        "architecture": "adversarial-jepa", "variant": "no-response",
        "filename": "caissa_a_jepa_no_response.npz", "trainable": True,
    },
    {
        "id": "lejepa-sigreg",
        "label": "LeJEPA-inspired SIGReg No-EMA",
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
    ready = []
    try:
        from research_dataset import resolve_dataset, verify_plan
        import json
        dataset = resolve_dataset(project_dir)
        location = json.loads((Path(project_dir) / "chess_data/dataset_location.json").read_text(encoding="utf-8"))
        fingerprint = verify_plan(dataset, location["split_plan"])["dataset_fingerprint"]
        for spec in training_model_specs(project_dir):
            if spec["path"].exists():
                model = create_model(spec, create_if_missing=False)
                if model.dataset_fingerprint == fingerprint and model.trained_steps > 0:
                    ready.append({**spec, "verification": "VERIFIED_DATASET"})
    except (OSError, ValueError, KeyError, TypeError):
        pass  # No legacy checkpoint is silently presented as verified.
    return [_alpha_beta_spec(), *ready]


def spec_by_id(project_dir: Path, model_id: str) -> Optional[dict]:
    """Resolve a trainable or arena model by its stable id."""
    model_id = MODEL_ALIASES.get(model_id, model_id)
    for spec in [
        *training_model_specs(project_dir),
        _alpha_beta_spec(),
    ]:
        if spec["id"] == model_id:
            return spec
    return None


MODEL_ALIASES = {
    "h1": "a-jepa-h1", "h1-h2": "a-jepa-h1-h2", "full": "a-jepa-v7",
    "no-response": "a-jepa-no-response", "lejepa-inspired": "lejepa-sigreg",
    "direct-policy-value": "policy-value-v1", "nnue-style": "nnue-style-v1",
}


def create_model(spec, latent_size=96, create_if_missing=True):
    from adversarial_jepa import AdversarialJEPA
    from lejepa import LeJEPA
    from policy_value_baseline import DirectPolicyValueBaseline
    from nnue_baseline import NNUEStyleBaseline
    cls = {"adversarial-jepa": AdversarialJEPA, "lejepa": LeJEPA,
           "policy-value": DirectPolicyValueBaseline, "nnue": NNUEStyleBaseline}[spec["architecture"]]
    kwargs = dict(latent_size=latent_size, create_if_missing=create_if_missing)
    if spec["architecture"] != "policy-value":
        kwargs["variant"] = spec["variant"]
    return cls(spec["path"], **kwargs)


def model_manifest(spec, model):
    import hashlib
    import json
    config = {"schema_version": 1, "research_name": "MARS-JEPA Chess",
              "registry_id": spec["id"], "architecture": spec["architecture"],
              "variant": spec["variant"], "latent_size": model.latent_size, "seed": model.seed,
              "objective_version": 3, "response_aggregation": "learned behavioral policy expectation; uncalibrated",
              "ema_decay": getattr(model, "ema_decay", None), "sigreg_weight": getattr(model, "sigreg_weight", None),
              "features": {"coordinate_system": "king-conditioned side-to-move features" if spec["architecture"] == "nnue" else "absolute board; no symmetry augmentation",
                           "history_aware": False, "clock_features": False,
                           "horizons": list(getattr(model, "enabled_horizons", (1, 2, 4) if spec["architecture"] == "lejepa" else ())),
                           "response_conditioned": getattr(model, "response_conditioned", spec["architecture"] == "lejepa")},
              "parameters": sum(getattr(model, n).size for n in parameter_names(model)),
              "dataset_fingerprint": model.dataset_fingerprint}
    config["configuration_sha256"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    return config


def parameter_names(model):
    for attribute in ("trainable_names", "names", "parameter_names"):
        if hasattr(model, attribute):
            return getattr(model, attribute)
    raise TypeError("Model does not declare its parameters")
