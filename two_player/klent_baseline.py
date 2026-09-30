"""Clean-room KLENT-style target utilities for two-player self-play.

This module implements published policy-improvement and lambda-return
equations with CAISSA's explicit player-to-move perspective convention. It is
not the authors' source code or a reproduction of their experiment.
"""

import numpy as np


def regularized_policy_target(policy, q_values, legal_mask, *, alpha=0.03, beta=0.1):
    """Compute the reverse-KL/entropy policy-improvement target.

    Inputs may have any matching leading batch dimensions; the final axis is
    the fixed action space. Illegal actions must have zero input probability
    and receive zero output probability. Every row must contain at least one
    legal action and legal input probabilities must be normalized.
    """
    policy = np.asarray(policy, dtype=np.float64)
    q_values = np.asarray(q_values, dtype=np.float64)
    legal = np.asarray(legal_mask, dtype=bool)
    if policy.ndim < 1 or policy.shape != q_values.shape or policy.shape != legal.shape:
        raise ValueError("policy, Q values, and legal mask must have the same non-scalar shape")
    if not np.isfinite(alpha) or alpha <= 0 or not np.isfinite(beta) or beta < 0:
        raise ValueError("alpha must be positive and beta must be nonnegative")
    if not np.all(np.isfinite(policy)) or not np.all(np.isfinite(q_values)):
        raise ValueError("policy and Q values must be finite")
    counts = legal.sum(axis=-1)
    if np.any(counts == 0):
        raise ValueError("each state must have at least one legal action")
    if np.any(policy < 0) or np.any(policy[~legal] != 0):
        raise ValueError("policy must be nonnegative and assign zero probability to illegal actions")
    row_sums = policy.sum(axis=-1)
    if not np.allclose(row_sums, 1.0, rtol=1e-10, atol=1e-12):
        raise ValueError("each input policy row must sum to one")
    if np.any(policy[legal] <= 0):
        raise ValueError("policy must assign positive probability to every legal action")

    logits = np.full(policy.shape, -np.inf, dtype=np.float64)
    logits[legal] = (q_values[legal] + beta * np.log(policy[legal])) / (alpha + beta)
    maxima = np.max(logits, axis=-1, keepdims=True)
    weights = np.where(legal, np.exp(logits - maxima), 0.0)
    normalizer = weights.sum(axis=-1, keepdims=True)
    target = weights / normalizer
    if not np.all(np.isfinite(target)):
        raise FloatingPointError("policy target contains nonfinite values")
    return target


def alternating_lambda_returns(
    rewards,
    next_player_values,
    terminal_successors,
    *,
    lam=np.exp(-1.0 / 8.0),
    gamma=1.0,
):
    """Return targets for a complete alternating zero-sum episode.

    ``rewards[t]`` is the immediate reward from the actor-at-t perspective.
    ``next_player_values[t]`` is the bootstrap value from the next state's
    player-to-move perspective. The perspective changes every ply, so the
    nonterminal bootstrap and the next lambda return both change sign. A true
    terminal successor suppresses all bootstrap terms. The final transition
    must be terminal; truncated episodes are rejected.
    """
    rewards = np.asarray(rewards, dtype=np.float64)
    values = np.asarray(next_player_values, dtype=np.float64)
    terminal = np.asarray(terminal_successors, dtype=bool)
    if rewards.ndim != 1 or rewards.size == 0 or values.shape != rewards.shape or terminal.shape != rewards.shape:
        raise ValueError("rewards, next-player values, and terminal flags must be nonempty matching vectors")
    if not np.all(np.isfinite(rewards)) or not np.all(np.isfinite(values)):
        raise ValueError("rewards and bootstrap values must be finite")
    if not np.isfinite(lam) or not 0 <= lam <= 1 or not np.isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError("lambda and gamma must be finite values in [0, 1]")
    if not terminal[-1]:
        raise ValueError("complete episode must end at a terminal successor")

    returns = np.empty_like(rewards)
    for t in range(rewards.size - 1, -1, -1):
        if terminal[t]:
            returns[t] = rewards[t]
        else:
            tail = (1.0 - lam) * values[t] + lam * returns[t + 1]
            returns[t] = rewards[t] - gamma * tail
    return returns
