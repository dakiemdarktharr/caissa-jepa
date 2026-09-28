"""Frozen v2 depth-two evaluators; no dataset loading or final-set access.

Exact rules determine every branch and terminal outcome. Neural leaves are batched
within one root. Time limits are cooperative: a NumPy call cannot be interrupted,
but an overrun is censored before its predictions can become a scored decision.
"""
import time
from types import SimpleNamespace

import numpy as np

from two_player.games import ACTION_SIZE, State
from two_player_v2 import GAMES_V2


GAMES = GAMES_V2
ALLOWED_SPLITS = frozenset(("development", "transfer"))


class _Censored(Exception):
    pass


def _array(value, shape, name):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"Invalid {name} shape or non-finite values")
    return result


def plan_root(root, model=None, *, track="exact", max_nodes=4096,
              max_seconds=1.0, games=None, clock=None, allow_train=False):
    """Return one complete/censored/error record, with no partial-tree scoring.

    `nodes` counts exact transitions, including terminal children, not the root.
    A limit exactly equal to a complete tree's count permits its evaluation.
    Exact ties choose the first action in the frozen root action list, which must
    equal the adapter's action order. Oracle values are root-mover values.
    """
    if root.get("split") not in ALLOWED_SPLITS and not (allow_train and root.get("split") == "train"):
        raise ValueError("Only development/transfer roots or explicit train diagnostics may be scored")
    if track not in ("exact", "hybrid"):
        raise ValueError("Unknown evaluation track")
    if type(max_nodes) is not int or max_nodes < 1:
        raise ValueError("max_nodes must be a positive integer")
    if not np.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("max_seconds must be finite and positive")
    clock = clock or time.perf_counter
    start = clock()
    record = {"game": root.get("game"), "root_id": root.get("root_id"),
              "trajectory": root.get("trajectory"), "track": track,
              "split": root.get("split"),
              "beyond_depth": bool(root.get("beyond_depth", False)),
              "status": "error", "reason": None, "action": None,
              "regret": None, "optimal": None, "nodes": 0,
              "transitions": 0, "leafcount": 0, "neural_leaves": 0,
              "neuralcounts": {"encoder_calls": 0, "encoder_states": 0,
                               "rollout_calls": 0, "predictor_steps": 0,
                               "value_calls": 0, "value_states": 0}}

    def time_check():
        if clock() - start >= max_seconds:
            raise _Censored("time_budget")

    def step(game, state, action):
        time_check()
        if record["nodes"] >= max_nodes:
            raise _Censored("node_budget")
        child = game.transition(state, action)
        record["nodes"] += 1
        record["transitions"] += 1
        time_check()
        return child

    try:
        time_check()
        game = (GAMES if games is None else games)[root["game"]]
        state = State(tuple(root["state"]["board"]), root["state"]["player"])
        game.validate(state)
        if game.terminal(state) is not None:
            raise ValueError("Evaluation root must be nonterminal")
        actions = tuple(root["actions"])
        if any(type(a) is not int for a in actions) or actions != game.legal_actions(state):
            raise ValueError("Root actions do not match the frozen legal action order")
        truth = _array(root["oracle_values"], (len(actions),), "oracle values")
        if not len(actions) or not np.isin(truth, (-1, 0, 1)).all():
            raise ValueError("Invalid exact root utility labels")
        # Each own action has a list of root-perspective reply values. Terminal
        # own actions are represented by a singleton and do not invent a reply.
        branches, leaves = [], []
        for own_action in actions:
            child = step(game, state, own_action)
            outcome = game.terminal(child)
            if outcome is not None:
                branches.append([float(state.player * outcome)])
                record["leafcount"] += 1
                continue
            replies = game.legal_actions(child)
            if not replies:
                raise ValueError("Nonterminal child has no legal reply")
            values = []
            branches.append(values)
            for reply in replies:
                successor = step(game, child, reply)
                outcome = game.terminal(successor)
                record["leafcount"] += 1
                if outcome is not None:
                    values.append(float(state.player * outcome))
                else:
                    values.append(0.0)
                    leaves.append((len(branches)-1, len(values)-1, successor,
                                   own_action, reply))
        record["neural_leaf_candidates"] = len(leaves)
        if leaves and model is not None:
            time_check()
            counts = record["neuralcounts"]
            direct = getattr(getattr(model, "config", SimpleNamespace()), "variant", "direct") == "direct"
            if track == "exact" or direct:
                x = np.stack([game.features(leaf[2]) for leaf in leaves])
                time_check()
                counts["encoder_calls"] += 1
                counts["encoder_states"] += len(leaves)
                z = np.asarray(model.encode(x), dtype=np.float64)
            else:
                counts["encoder_calls"] += 1
                counts["encoder_states"] += 1
                initial_z = np.asarray(model.encode(game.features(state)[None]), dtype=np.float64)
                time_check()
                if initial_z.ndim != 2 or initial_z.shape[0] != 1 or not np.isfinite(initial_z).all():
                    raise ValueError("Invalid initial latent representation")
                action_vectors = np.zeros((len(leaves), 2, ACTION_SIZE))
                for i, leaf in enumerate(leaves):
                    action_vectors[i, 0, leaf[3]] = 1.0
                    action_vectors[i, 1, leaf[4]] = 1.0
                counts["rollout_calls"] += 1
                counts["predictor_steps"] += 2 * len(leaves)
                z = np.asarray(model.rollout(np.repeat(initial_z, len(leaves), axis=0),
                                             action_vectors, horizon=2), dtype=np.float64)
            time_check()
            if z.ndim != 2 or z.shape[0] != len(leaves) or not np.isfinite(z).all():
                raise ValueError("Invalid leaf latent representation")
            counts["value_calls"] += 1
            counts["value_states"] += len(leaves)
            predicted = _array(model.value(z), (len(leaves), 1), "leaf values")[:, 0]
            if np.any(np.abs(predicted) > 1 + 1e-12):
                raise ValueError("Leaf values outside utility range")
            time_check()
            record["neural_leaves"] = len(leaves)
            for leaf, value in zip(leaves, predicted):
                # Two alternating plies restore the root player's perspective.
                if leaf[2].player != state.player:
                    raise ValueError("Unexpected player after two plies")
                branches[leaf[0]][leaf[1]] = float(value)
        time_check()
        estimates = np.asarray([min(reply_values) for reply_values in branches])
        selected = int(np.argmax(estimates))
        regret = float(np.max(truth) - truth[selected])
        record.update(status="complete", action=actions[selected], regret=regret,
                      optimal=bool(regret == 0), action_estimates=estimates.tolist(),
                      oracle_gap=float(np.max(truth)-np.min(truth)))
    except _Censored as exc:
        record.update(status="censored", reason=str(exc))
    except Exception as exc:
        record.update(status="error", reason=f"{type(exc).__name__}: {exc}")
    record["seconds"] = float(clock() - start)
    if record["status"] == "complete" and record["seconds"] >= max_seconds:
        record.update(status="censored", reason="time_budget", action=None,
                      regret=None, optimal=None)
        record.pop("action_estimates", None)
    return record


def evaluate(roots, model=None, *, tracks=("exact", "hybrid"), **kwargs):
    """Preserve each root in order, including errors/censors, for every track."""
    roots = list(roots)
    if any(root.get("split") not in ALLOWED_SPLITS and not
           (kwargs.get("allow_train", False) and root.get("split") == "train") for root in roots):
        raise ValueError("Selection/final evaluation is not authorized")
    tracks = tuple(tracks)
    if not tracks or len(set(tracks)) != len(tracks) or any(t not in ("exact", "hybrid") for t in tracks):
        raise ValueError("Tracks must be unique exact/hybrid entries")
    return [plan_root(root, model, track=track, **kwargs)
            for root in roots for track in tracks]


def _geometry(z):
    z = np.asarray(z, dtype=np.float64)
    if z.ndim != 2 or not np.isfinite(z).all():
        raise ValueError("Invalid representation for geometry")
    centered = z - z.mean(axis=0, keepdims=True) if len(z) else z
    spectrum = np.linalg.svd(centered, compute_uv=False)**2 if len(z) else np.array([])
    spectrum = spectrum[spectrum > 0]
    probs = spectrum/spectrum.sum() if len(spectrum) and spectrum.sum() else np.array([])
    return {"samples": len(z), "dimensions": z.shape[1],
            "effective_rank": float(np.exp(-np.sum(probs*np.log(probs)))) if len(probs) else 0.0,
            "mean_std": float(np.std(z, axis=0).mean()) if len(z) else None,
            "median_std": float(np.median(np.std(z, axis=0))) if len(z) else None,
            "mean_norm": float(np.linalg.norm(z, axis=1).mean()) if len(z) else None}


def representation(model, batch):
    """Descriptive metrics for one caller-selected game group, not inference.

    Counts are encoded state occurrences (fork repetitions included), not unique
    positions or independent samples. Horizon errors compare predictions with
    current online encodings; they are not the EMA/projected training objective.
    This function receives arrays only: the caller must enforce split authority.
    """
    x = np.asarray(batch["x"], dtype=np.float64)
    if x.ndim != 3 or x.shape[1:] != (3, 198):
        raise ValueError("Invalid feature batch shape")
    n = len(x)
    valid = np.asarray(batch["valid"])
    legal = np.asarray(batch["legal"])
    if valid.shape != (n, 3) or valid.dtype != np.bool_ or legal.shape != (n, 3, 65):
        raise ValueError("Invalid validity/legal masks")
    if not np.isin(legal, (0, 1)).all() or np.any(valid[:, 1:] & ~valid[:, :-1]):
        raise ValueError("Invalid masks or missing predecessor")
    legal = legal.astype(bool)
    policy = _array(batch["policy"], (n, 3, 65), "policy targets")
    values = _array(batch["value"], (n, 3, 1), "value targets")
    actions = _array(batch["actions"], (n, 2, 65), "actions")
    if not np.isfinite(x[valid]).all() or np.any(np.abs(values[valid]) > 1):
        raise ValueError("Invalid active features or value targets")
    if np.any(policy < 0) or np.any(policy[~legal] != 0):
        raise ValueError("Policy target assigns mass to illegal actions")
    active_policy = legal.any(axis=2) & valid
    if not np.allclose(policy.sum(axis=2)[active_policy], 1):
        raise ValueError("Active policy targets must sum to one")
    result = {"forks": n, "samples": int(valid.sum()),
              "missing_states": int((~valid).sum()),
              "policy_samples": int(active_policy.sum()),
              "terminal_samples": int((valid & ~legal.any(axis=2)).sum()),
              "value_mse": None, "policy_nll": None, "policy_mrr": None,
              "policy_top1_optimal": None, "horizons": {}}
    if not valid.any():
        result["unprojected"] = None
        return result
    z = np.asarray(model.encode(x[valid]), dtype=np.float64)
    if z.ndim != 2 or len(z) != valid.sum() or not np.isfinite(z).all():
        raise ValueError("Invalid online encodings")
    predicted_value = _array(model.value(z), (len(z), 1), "predicted values")
    result["value_mse"] = float(np.mean((predicted_value-values[valid])**2))
    result["unprojected"] = _geometry(z)
    if callable(getattr(model, "project", None)):
        result["projected"] = _geometry(model.project(z))
    else:
        result["projected"] = None
    logits = _array(model.policy_logits(z), (len(z), 65), "policy logits")
    selected = active_policy[valid]
    if selected.any():
        masks, target = legal[valid][selected], policy[valid][selected]
        scores = np.where(masks, logits[selected], -np.inf)
        shifted = scores - scores.max(axis=1, keepdims=True)
        log_prob = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
        result["policy_nll"] = float(-np.sum(target*np.where(target > 0, log_prob, 0))/len(target))
        chosen = scores.argmax(axis=1)
        result["policy_top1_optimal"] = float(np.mean(target[np.arange(len(target)), chosen] > 0))
        order = np.argsort(-scores, axis=1, kind="stable")
        first_optimal = np.argmax(np.take_along_axis(target, order, axis=1) > 0, axis=1)+1
        result["policy_mrr"] = float(np.mean(1/first_optimal))
    direct = getattr(getattr(model, "config", SimpleNamespace()), "variant", "direct") == "direct"
    if not direct:
        all_z = np.zeros((n, 3, z.shape[1]))
        all_z[valid] = z
        for horizon in (1, 2):
            mask = valid[:, 0] & valid[:, horizon]
            count = int(mask.sum())
            error = None
            if count:
                predicted = _array(model.rollout(all_z[mask, 0], actions[mask], horizon=horizon),
                                   (count, z.shape[1]), "predicted horizon latents")
                error = float(np.mean((predicted-all_z[mask, horizon])**2))
            result["horizons"][str(horizon)] = {"samples": count, "online_latent_mse": error}
    return result
