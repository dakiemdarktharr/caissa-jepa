# CAISSA-JEPA research roadmap

Updated: 2026-10-02. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

## Research objective

Falsifiable hypothesis: an EMA-target JEPA that predicts future latent states conditioned on both players' ordered actions can improve planning under a fixed compute budget over matched non-JEPA baselines, with the benefit retained across a declared family of deterministic, alternating-turn, fully observed, finite-action, zero-sum games. Current evidence does not support this hypothesis. The immediate aim is to determine whether there is a defensible mechanism worth testing, not to tune until a development win appears.

Keep distinct: (a) behavioral prediction for a particular opponent, (b) worst-case optimal-reply modeling, (c) minimax/equilibrium search, and (d) expectation under an uncalibrated policy distribution. Current V2.8/V2.9 is (b)+(c), a depth-two max-min cutoff with a learned leaf evaluator. It is not (a), a full equilibrium solver, or exploitability evaluation.

## Workstreams and gates

| Order | Workstream and deliverable | Acceptance criteria | Relative effort / dependency |
| --- | --- | --- | --- |
| 0 | Provenance and durable memory: `GROUND_TRUTH.md`, Obsidian mirror, Git inventory | Ground Truth states repo/data/results truth; Markdown mirror hash-verified; only `main`; no unknown files overwritten | Small; continuous |
| 1 | Research positioning: `docs/RELATED_WORK.md`, primary-source search log | Cover JEPA/world models, game planning, board-game transfer, objective/gradient routing; describe search limits; make no unsupported novelty claim | Medium; ongoing |
| 2 | Method diagnosis V2.10: frozen gradient-alignment diagnostic spec and implementation | Decomposed loss gradients sum numerically to the existing total; diagnostics report cosine/norm/interference by shared encoder, game and seed on train-only batches; no optimizer update and no locked data access | Medium; depends on V2.9 negative result and new code review |
| 3 | Mechanism decision gate | Proceed only if negative JEPA-vs-task gradient alignment is stable across seeds/batches and is concentrated in shared parameters; otherwise reject gradient-conflict explanation and choose a different hypothesis | Small; depends on workstream 2 |
| 4 | Bounded development experiment, only if gate 3 passes | Compare raw reply-JEPA, predeclared encoder-only conflict-projected JEPA, task-value dynamics and direct leaf; same data, initialization, updates, compute/search, held-out development situations, seeds and rules; independent pre-fit review | Large; new grant, protocol, power/compute check and run artifacts required |
| 5 | Model selection and locked confirmatory evaluation | Separate untouched data/situations, independent schedule, predeclared primary regret/strength metric, practical margin, power, multiplicity, censoring and stop rule; no reuse for tuning | Large; only after development nomination and review |
| 6 | Generalization and paper package | Test held-out variants and multiple admitted games, strength/search costs, representation diagnostics, robustness, negative results, data/license statements, reproducibility and threat-to-validity | Large; after method survives confirmation |

## V2.9 disposition

The frozen three-epoch recipe failed its nomination screen. Under the shared two-ply max-min planner, the JEPA-minus-task-value mean paired score was -0.1375 on Connect4-6x7, +0.0125 on Reversi6, and -0.0625 macro over 20 checkpoint-seed clusters. The artifact has 160 complete paired blocks/320 games, no forfeits/censors, balanced JEPA seat swaps, and schedule-order/replay integrity checks. The outcome starts from fixed standard initial states; uncertainty intervals are exploratory and conditional on scheduled seeds. The JEPA/task-value planner CPU ratios were 1.025 and 1.005. Thus greater search CPU does not explain the result. This is evidence against the tested recipe, not proof against JEPA generally. Stop duration-only tuning.

The machine-readable analysis is `docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json`; raw fit/match/checkpoint artifacts remain ignored. The result is development evidence, not confirmatory inference.

## V2.10 candidate: diagnose before intervening

Candidate mechanism: the model's shared encoder receives gradients from legal-policy/value targets and from reply-set latent prediction. If the latter repeatedly conflicts with decision-task gradients, it may impair minimax-relevant value features despite good latent prediction. First compute gradients independently on the exact same train-only batches, decomposed into policy, root-value, observed-leaf-value, reply-JEPA, and latent-regularizer terms. Do not read historical `train_metrics`/loss curves or locked V08 records. This diagnostic makes no optimizer update and selects no model.

If and only if that predeclared diagnostic gate passes, a subsequent version may apply conflict projection only to the JEPA gradient on shared online-encoder parameters, leaving its predictor-specific gradient intact. The update rule, thresholds, hyperparameters, sample, seeds, and controls must be frozen before any fit. Compare at least raw JEPA, routed JEPA, task-value-dynamics, and direct leaf, on a fresh development schedule and with equal measured training/search budgets. This family is not claimed novel: PCGrad/CAGrad and gradient routing in JEPA Policy are prior art. Any defensible contribution would have to be a demonstrated, reproducible incremental benefit in the explicitly zero-sum reply-set setting and survive strong matched controls.

The diagnostic validated decomposition against the existing summed gradient (real-batch maximum relative error 5.15e-18), used frozen train-only inputs and model/panel hashes, and sampled all 20 seeds × two games × ten disjoint batches of 30 roots. All 400 cells were present with zero invalid/skipped roots and finite values. The frozen gate required, in both games, a seed-level median cosine below -0.05, a 95% seed-cluster interval wholly below zero, and at least 15/20 seeds with conflicts in at least six of ten batches. It failed every criterion: Connect4 median -0.0293, CI [-0.0483, 0.1560], 13/20 persistent-conflict seeds; Reversi6 median -0.0402, CI [-0.0651, 0.1064], 12/20. The correct decision is `stop_gradient_conflict_candidate`; do not fit a projected variant or search for post-hoc subgroups. Full outputs are in [the diagnostic artifact](docs/validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json), independently audited in [the review note](docs/V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md).

The next low-cost model-selection test is to raise the reply-JEPA coefficient from 1.0 to 8.0. At coefficient 1.0, the diagnostic's batch median encoder-gradient norm ratio `||g_JEPA|| / ||g_task||` was 0.049 in Connect4 and 0.045 in Reversi6, while the angle screen found no persistent conflict. Scaling by eight targets a material but still sub-task gradient contribution; it is a hypothesis motivated by a frozen diagnostic, not an outcome-selected subgroup. Compare the resulting fit panel against the already matched V2.9 task-value and direct-leaf arms on the same declared match schedule and compute accounting. Freeze all settings before fitting; retain V2.9's +0.05 per-game and macro nomination margin as an engineering screen, not confirmatory significance. Stop if the improvement is unstable, compute-inefficient, or depends on one game/seed.

This coefficient adjustment is ordinary objective-weight calibration, not a unique method contribution. Minimax-critical reply weighting remains an alternative only after more review: opponent-conditioned latent planning already appears in two-player MuZero and [Vector Quantized Models for Planning](https://proceedings.mlr.press/v139/ozair21a.html); value-sensitive model fitting and latent value alignment are established in [VaGraM](https://openreview.net/forum?id=4-D6CZkRXxI), [Value-Aligned World Models](https://proceedings.mlr.press/v306/jiang26ai.html), and policy-aware simulator learning. Any later variant must beat equally decision-aware non-JEPA controls and establish its specific incremental difference. No current method is certified novel.

## Kill criteria

- Stop active-superiority claims if a predeclared development candidate does not beat both task-value and direct-leaf at the chosen practical margin in every primary game, or if the effect depends on one seed, one game, extra compute, or post-hoc exclusions.
- Stop gradient-routing work if the diagnosis fails its frozen gate, or if projection does not improve the primary decision metric at equal compute.
- Narrow to a benchmark/methodological negative-result paper if no JEPA-specific mechanism survives matched controls and independent replication.
- Stop/pivot if exact search dominates under the relevant budget, legal/rule/data audit fails, held-out evaluation leaks, or a data license is unclear.
- Do not claim generic two-player coverage: hidden information, simultaneous actions, chance, general-sum utility, behavioral opponent forecasting, and equilibrium/exploitability guarantees need separate methods and evaluations.

## Data, compute, and reproducibility gates

Only locally generated, audited development data with clear provenance is currently used. Do not use third-party data until primary-source license/terms, training rights, redistribution and derivative-output rights are documented. Each manifest must pin SHA-256, parser/rules version, counts, provenance, split, and trajectory/event grouping. Keep raw data, checkpoints, caches, and logs outside Git and the Obsidian mirror. No paid compute or service without explicit authorization.

Before a training panel, freeze the objective, config, data fingerprint, exact split, seed schedule, schedule hash, compute caps, failure/censor policy and source commit; run the locked environment tests and independent review. A development result can nominate a model-selection study only. Confirmatory data stays unopened until all choices are frozen.

## Current status and professor-facing claim

The implementation and evaluation harness can test a narrow JEPA hypothesis, but current measured results do not show JEPA superiority. V2.9 is a negative/mixed development result; V2.10 rejects the gradient-conflict explanation for the tested checkpoints and train-root distribution. The next scientific decision is a separately frozen, development-only test of whether minimax-critical reply emphasis improves the latent planner beyond both uniform-reply JEPA and objective-matched non-JEPA controls. No novelty, cross-game transfer, equilibrium, exploitability, or Q1-readiness claim is established.
