# Why learn latent transitions when the rules are already cheap?

2026-09-29. Source-based positioning written while V2.5 grid05 runs, without
reading partial outcomes. This note adds interpretation to
[the frozen method](METHOD_V25.md) and [the design review](V25_ROBUST_PREDICTION_RESEARCH.md);
it neither changes that comparison nor selects a subsequent model.

## The defensible opportunity

Known transitions remove the need to learn game rules. They do not remove the
cost of evaluating positions or the statistical difficulty of learning useful
features. An action-conditioned auxiliary could improve a value representation;
alternatively, a cheaper latent predictor could approximate expensive successor
encodings. These are separate hypotheses. The present exact-rule, depth-two
experiment can distinguish them only within its small near-terminal distribution.

| Observation, if established | Supported interpretation | Unestablished claim |
| --- | --- | --- |
| Lower regret with exact successor encodings | Training improved the representation/value estimator under the same tree | Learned transitions are needed at inference |
| Better hybrid regret and smaller backed-up value error | Predicted features preserve decision-relevant information better | Rules can be discarded; equilibrium is solved |
| Better regret at matched measured latency | A local computation–quality advantage | Universal acceleration or amortized training savings |
| Success on these two trained games | Evidence across these two adapters/distributions | Unseen-game transfer, full-game strength, or general two-player applicability |

The strongest objection is straightforward: exact transitions are already
correct, and a direct value network can spend all its capacity learning the
quantity used by search. Predicting additional latent coordinates may consume
capacity, introduce irrelevant constraints, or reduce error without changing
the minimizing reply. Full oracle supervision makes that objection especially
strong. The recurrent policy/value, scalar-tail, reconstruction, and scaled-loss
controls therefore test substantive alternatives, rather than serving as weak
baselines.

## What the primary sources actually establish

**MuZero** learns reward, policy, and value predictions without requiring
observation reconstruction or pointwise latent alignment. Its board-game
success already invalidates novelty based merely on learned planning across
games. The authors suggest that repeated model applications may cache
computation and deepen understanding; this is an interpretation, not proof that
a latent transition beats every cheap rules engine. Its self-play/search
training regime also differs fundamentally from our fixed supervised bank.
[Schrittwieser et al., Sections 1–4](https://arxiv.org/html/1911.08265v2).

**Planning has several roles.** Hamrick et al. separately study planning for
learning targets, data collection, and evaluation. Training-time planning is
valuable in their experiments; test-time planning matters especially in some
domains, including Go. Our fixed oracle labels and trajectories exclude the
target-improvement and exploration feedback loops. We cannot attribute their
benefits to our auxiliary loss or expect them from shallow inference alone.
[Hamrick et al., Section 4](https://arxiv.org/html/2011.04021v2).

**RePAIR** predicts masked chess representations through bidirectional sequence
repair, with the first and last states available. It uses neither explicit
actions nor engine labels. Its loss comparison selects short-plus-long
reconstruction without the additional JEPA loss, given similar performance and
fewer constraints. Its reconstruction and semantic-clustering evidence does
not establish competitive planning. It is relevant representation-learning
precedent, but its future context must not enter a causal inference planner.
This result is also not evidence that every JEPA objective fails.
[Koller et al., Sections III–V and Table I](https://arxiv.org/html/2606.11860v1).

**Other chess work narrows the terminology.** The original
[JEPA-chess repository](https://github.com/CCranney/JEPA-chess) explicitly places
playing ability outside its initial focus. SOLIS learns a value-aligned
contrastive representation using Stockfish-labelled positions, then encodes
enumerated legal successor boards during beam search. Thus, planning with
latent evaluations need not use learned transition dynamics; teacher
supervision and successor encoding remain material costs.
[SOLIS, Sections 3–4](https://arxiv.org/html/2506.04892v1).

**Representation fidelity is insufficient.** Guei et al. inspect MuZero through
reconstruction in Go, Gomoku, and Atari; long unrolls become less accurate while
planning can remain useful. Table I sets their state-consistency coefficient
to zero for board games. That configuration is not a causal ablation proving
consistency harmful, but it prevents citing this paper as a board-game JEPA
success. Their player-dependent unroll errors also motivate separating horizons
and roles rather than pooling every latent residual.
[Guei et al., Sections III–IV](https://arxiv.org/html/2411.04580v2).

## A cost crossover, not a timing result

The actual [evaluator](../two_player_v2/evaluate.py) retains all exact legal
branches and terminal overrides in both tracks. Let `L > 0` be the number of
nonterminal H2 leaves. Let `C_rules` include shared transitions, legality,
terminal checks, and backup; `F(k)`, `E(k)`, `P(k)`, and `V(k)` denote costs of
features, encoding, one predictor step, and value evaluation for a batch of
`k` states. Let `H_exact/H_hybrid` include other allocation/dispatch overhead.

```text
T_exact  = C_rules + F(L) + E(L) + V(L) + H_exact
T_hybrid = C_rules + F(1) + E(1) + 2 P(L) + V(L) + H_hybrid
```

Hybrid currently repeats H1 prediction for each reply; it does not share those
prefixes. Its crossover requires

```text
F(L) + E(L) - F(1) - E(1) > 2 P(L) + H_hybrid - H_exact.
```

No rule-transition cost disappears. For `L=0`, both skip neural evaluation.
The direct family uses exact encoding in both tracks.

Under an illustrative linear cost model, ignoring features, overhead,
nonlinearities, biases and memory, the frozen encoder uses
`198×128 + 128×64 = 33,536` affine multiply-accumulates per state. Its predictor
uses `129×50 + 50×64 = 9,650` per step. The affine-only crossover is
`L > 33,536/(33,536−19,300) ≈ 2.36`, hence `L≥3`. This is arithmetic accounting,
**not measured acceleration**: batching, cache locality, allocations, and the
shared rules cost can dominate. Exact-state caching and incremental feature
updates must remain available to the baseline. Any future prefix-sharing
optimization requires a new fair timing comparison.

Even a positive inference difference must amortize additional training cost:
for `Q` decisions, `Q(T_exact−T_hybrid) > additional training cost`. If the
latency difference is nonpositive, this route offers no computational payoff.
Equal update counts alone do not equalize auxiliary-loss training expense.

## Finite diagnostics and rejection conditions

After the complete frozen grid, the following would test claims without choosing
a new architecture:

1. **Compute:** freeze checkpoints and a development timing schedule; measure
   warmed, paired latency by `L=0/1/2/≥3`, game and branching, with the same
   threads, caching and terminal handling. Reject a speed claim if hybrid has
   no decision-quality/latency advantage against the optimized exact baseline.
2. **Mechanism:** compare exact re-encoding and predicted leaves for each fixed
   checkpoint. Inspect reply-minimum errors, decision flips, head norms and
   encoded-target oracle errors. Lower latent MSE without improved backup or
   regret rejects the proposed practical mechanism. A scalar or scaled-loss
   explanation limits claims of representation-specific benefit. Different
   latent scales must not be interpreted as comparable absolute quality.
3. **Statistical scope:** only a future prespecified label-budget comparison
   could establish label efficiency. Require equal access to unlabelled
   transitions, oracle labels, tuning trials and compute accounting. Unseen
   variants and longer horizons are separate tests, not implications of
   success on this bank. None is authorized here as a replacement endpoint.

## Adaptive development remains development

Freezing 42 cells prevents within-grid opportunism; it does not undo earlier
choices informed by the same development bank. Root-paired intervals describe
these roots and fixed seeds, not uncertainty over the entire adaptive research
process. Selection over noisy validation scores can itself overfit, as
[Cawley and Talbot](https://jmlr.csail.mit.edu/papers/volume11/cawley10a/cawley10a.pdf)
demonstrate. Formal reusable-holdout guarantees require specific mechanisms;
ordinary repeated inspection is not
[Thresholdout](https://proceedings.neurips.cc/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf).

Any successful development screen would justify one bounded, declared next
evaluation, with protected selection/final data still closed until its protocol
permits access. All negative grids and operational failures remain visible.
Scientific value requires an identifiable advantage and a credible scope of
generalization; neither the JEPA name nor a favourable development comparison
settles novelty or publication readiness.
