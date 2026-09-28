"""Coherent legal symmetries for v2.1 training forks; no labels are generated."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib

import numpy as np

from two_player_v2 import GAMES_V2


@lru_cache(maxsize=None)
def _transform_count(name):
    return len(GAMES_V2[name].transforms())


@lru_cache(maxsize=None)
def _descriptors(name):
    game = GAMES_V2[name]
    result = np.array([game.rows/8, game.cols/8, game.k/8,
                       not game.reversi, game.reversi, game.gravity])
    result.setflags(write=False)
    return result


def augmentation_plan(forks, indices, seed, epoch):
    """Independent epoch-addressed RNG, identical across variants/rates/weights."""
    if type(seed) is not int or seed < 0 or type(epoch) is not int or epoch < 0:
        raise ValueError("Seed and epoch must be nonnegative integers")
    indices = np.asarray(indices)
    if indices.ndim != 1 or indices.dtype.kind not in "iu":
        raise ValueError("Fork indices must be a one-dimensional integer array")
    if np.any(indices < 0) or np.any(indices >= len(forks)):
        raise ValueError("Fork index outside dataset")
    rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2211]))
    transforms = np.empty(len(indices), dtype=np.int64)
    counts = Counter()
    for draw, index in enumerate(indices):
        fork = forks[int(index)]
        if fork["split"] != "train":
            raise ValueError("Only training forks may be augmented")
        name = fork["game"]
        transform = int(rng.integers(_transform_count(name)))
        transforms[draw] = transform
        counts[f"{name}/{transform}"] += 1
    return transforms, {"version": "legal-symmetries-v21", "samples": len(indices),
                        "seed": seed, "epoch": epoch, "rng_namespace": 2211,
                        "transform_counts": dict(sorted(counts.items())),
                        "transform_sha256": hashlib.sha256(transforms.astype("<i8").tobytes()).hexdigest(),
                        "index_sha256": hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest()}


@lru_cache(maxsize=None)
def _inverse_permutations(name, transform_id):
    game = GAMES_V2[name]
    transforms = game.transforms()
    if transform_id < 0 or transform_id >= len(transforms):
        raise ValueError("Transform is not a legal game symmetry")
    mapping = transforms[transform_id]
    forward = np.arange(65)
    for original, destination in enumerate(mapping):
        old_r, old_c = divmod(original, game.cols)
        new_r, new_c = divmod(destination, game.cols)
        forward[old_r*8+old_c] = new_r*8+new_c
    if not np.array_equal(np.sort(forward), np.arange(65)) or forward[64] != 64:
        raise ValueError("Invalid cell/action permutation")
    inverse_action = np.argsort(forward)
    inverse_features = np.concatenate([inverse_action[:64]+offset for offset in (0, 64, 128)]
                                      + [np.arange(192, 198)])
    inverse_action.setflags(write=False)
    inverse_features.setflags(write=False)
    return inverse_action, inverse_features


def augment(batch, game_names, transform_ids):
    """Copy a batch and permute complete forks without changing value/metadata.

    One transform applies to root, child and successor, both action slots, and
    every legal/policy vector. Padding, the six game descriptors, pass64, missing
    slots and relative player perspective remain unchanged. Input is not mutated.
    Additional metadata fields are copied without reinterpretation.
    """
    x = np.asarray(batch["x"])
    if x.ndim != 3 or x.shape[1:] != (3, 198):
        raise ValueError("Expected features with shape N,3,198")
    n = len(x)
    game_names = list(game_names)
    transforms = np.asarray(transform_ids)
    if len(game_names) != n or transforms.shape != (n,) or transforms.dtype.kind not in "iu":
        raise ValueError("Game/transform schedule must match batch rows")
    expected = {"valid": (n, 3), "legal": (n, 3, 65), "policy": (n, 3, 65),
                "value": (n, 3, 1), "actions": (n, 2, 65)}
    arrays = {key: np.asarray(batch[key]) for key in expected}
    if any(arrays[key].shape != shape for key, shape in expected.items()):
        raise ValueError("Invalid training batch shape")
    if arrays["valid"].dtype != np.bool_:
        raise ValueError("Validity mask must be boolean")
    if not np.isfinite(x).all() or any(not np.isfinite(arrays[key]).all() for key in expected):
        raise ValueError("Non-finite augmentation input")
    result = {key: value.copy() if isinstance(value, np.ndarray) else deepcopy(value)
              for key, value in batch.items()}
    # Ensure list-like inputs also produce independent numeric output arrays.
    result["x"] = x.copy()
    result.update({key: value.copy() for key, value in arrays.items()})
    groups = {}
    for row, (name, transform_id) in enumerate(zip(game_names, transforms)):
        groups.setdefault((name, int(transform_id)), []).append(row)
    for (name, transform_id), rows in groups.items():
        inverse_actions, inverse_features = _inverse_permutations(name, transform_id)
        expected_descriptors = _descriptors(name)
        selected_x = x[rows]
        if not np.all(selected_x[arrays["valid"][rows]][:, 192:] == expected_descriptors):
            raise ValueError("Game name does not match encoded state descriptors")
        result["x"][rows] = np.take(selected_x, inverse_features, axis=-1)
        for key in ("legal", "policy", "actions"):
            result[key][rows] = np.take(arrays[key][rows], inverse_actions, axis=-1)
    return result
