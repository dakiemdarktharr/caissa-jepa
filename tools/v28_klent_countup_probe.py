"""Exploratory synthetic convergence probe for the clean-room KLENT baseline.

This is a baseline implementation check on a tiny procedural game, not a
CAISSA-JEPA result, board-game benchmark, or paper-scale KLENT reproduction.
"""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from two_player.games import FEATURE_SIZE, State
from two_player.klent_model import (
    KLENTConfig,
    KLENTModel,
    collect_selfplay_batch,
    fit_selfplay_batch,
)


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CountUpGame:
    name = "count-up-N7-k2"

    def initial(self):
        return State((0,), 1)

    def terminal(self, state):
        return None if state.board[0] < 7 else -state.player

    def legal_actions(self, state):
        return (0, 1) if self.terminal(state) is None else ()

    def transition(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal count-up action")
        return State((state.board[0] + action + 1,), -state.player)

    def features(self, state):
        values = np.zeros(FEATURE_SIZE, dtype=np.float64)
        values[state.board[0]] = 1.0
        return values


def exact_regularized_solution(game, alpha):
    """Backward-induction quantal-response fixed point for Count Up."""
    policy = {}
    q_values = {}
    values = {}
    for count in reversed(range(7)):
        actions = game.legal_actions(State((count,), 1))
        q = []
        for action in actions:
            next_count = count + action + 1
            q.append(1.0 if next_count >= 7 else -values[next_count])
        q = np.asarray(q, dtype=np.float64)
        probabilities = np.exp(q / alpha - np.max(q / alpha))
        probabilities /= probabilities.sum()
        policy[count] = probabilities
        q_values[count] = q
        values[count] = float(probabilities @ q)
    return policy, q_values, values


def evaluate(model, game, exact_policy, exact_q):
    rows = []
    for count in range(7):
        state = State((count,), 1)
        actions = game.legal_actions(state)
        features = game.features(state)[None, :]
        legal = np.zeros((1, 65), dtype=bool)
        legal[0, list(actions)] = True
        policy_target, _ = model.improvement_target(features, legal)
        _, predicted_q = model.predict(features, legal)
        predicted_policy = policy_target[0, list(actions)]
        rows.append({
            "count": count,
            "policy_total_variation": float(0.5 * np.abs(predicted_policy - exact_policy[count]).sum()),
            "policy_brier": float(np.mean((predicted_policy - exact_policy[count]) ** 2)),
            "q_mae": float(np.mean(np.abs(predicted_q[0, list(actions)] - exact_q[count]))),
            "predicted_policy": predicted_policy.tolist(),
            "target_policy": exact_policy[count].tolist(),
            "predicted_q": predicted_q[0, list(actions)].tolist(),
            "target_q": exact_q[count].tolist(),
        })
    return {
        "mean_policy_total_variation": float(np.mean([row["policy_total_variation"] for row in rows])),
        "mean_policy_brier": float(np.mean([row["policy_brier"] for row in rows])),
        "mean_q_mae": float(np.mean([row["q_mae"] for row in rows])),
        "states": rows,
    }


def run(phases=400, seeds=(17, 29, 43), episodes_per_phase=16):
    if phases < 1 or episodes_per_phase < 1:
        raise ValueError("phases and episodes per phase must be positive")
    game = CountUpGame()
    alpha, beta = 0.5, 1.0
    exact_policy, exact_q, _ = exact_regularized_solution(game, alpha)
    runs = []
    for seed in seeds:
        model = KLENTModel(KLENTConfig(seed=seed, latent=8, alpha=alpha, beta=beta))
        snapshots = []
        start_wall = time.perf_counter()
        start_cpu = time.process_time()
        transitions = 0
        optimizer_steps_before = model.step
        for phase in range(phases):
            collected = collect_selfplay_batch(
                game, model, episodes=episodes_per_phase,
                seed=seed * 100000 + phase,
            )
            transitions += collected["transitions"]
            fit = fit_selfplay_batch(
                model, collected, epochs=1, batch_size=64,
                seed=seed * 1000000 + phase,
            )
            if (phase + 1) % max(1, phases // 4) == 0 or phase + 1 == phases:
                snapshots.append({
                    "phase": phase + 1,
                    "examples_in_phase": collected["transitions"],
                    "fit_loss": fit["history"][-1]["loss"],
                    "evaluation": evaluate(model, game, exact_policy, exact_q),
                })
        runs.append({
            "seed": seed,
            "episodes": phases * episodes_per_phase,
            "transitions": transitions,
            "optimizer_steps": model.step - optimizer_steps_before,
            "wall_seconds": time.perf_counter() - start_wall,
            "cpu_seconds": time.process_time() - start_cpu,
            "final": evaluate(model, game, exact_policy, exact_q),
            "development_snapshots": snapshots,
        })
    source_files = (
        ROOT / "two_player" / "klent_baseline.py",
        ROOT / "two_player" / "klent_model.py",
        ROOT / "tools" / "v28_klent_countup_probe.py",
    )
    config = {"alpha": alpha, "beta": beta, "lambda": float(np.exp(-1 / 8)),
              "latent": 8, "episodes_per_phase": episodes_per_phase, "phases": phases,
              "seeds": list(seeds)}
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {
        "stage": "exploratory synthetic baseline convergence check",
        "claim_status": "engineering/fidelity evidence only; no game-strength or JEPA comparison",
        "source_commit": commit,
        "source_sha256": {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in source_files},
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "game": {"name": game.name, "states": 7, "actions": [1, 2], "deterministic": True},
        "dataset": "generated online from a seven-state project-owned test game; no external data",
        "dataset_split": "not applicable; this is an implementation check, not a generalization experiment",
        "config": config,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "exact_target": "backward-induction quantal-response fixed point at entropy temperature alpha",
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phases", type=int, default=400)
    parser.add_argument("--episodes-per-phase", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.phases, episodes_per_phase=args.episodes_per_phase)
    raw = json.dumps(receipt, indent=2, allow_nan=False).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(args.output)
    print(json.dumps({
        "output": str(args.output),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "runs": len(receipt["runs"]),
        "episodes_per_seed": args.phases * args.episodes_per_phase,
    }, allow_nan=False))


if __name__ == "__main__":
    main()
