# V2.8 data, opponent, split, and power protocol v0.1

**Status: pre-fit protocol proposal; not yet implemented, independently approved, or a training authorization.** No learned result has been inspected under this protocol. Any change after viewing learned development outcomes requires a new version and retention of all prior attempts.

## Claim and game scope

The candidate question is whether complete legal-reply-set JEPA latents improve exact-root minimax action selection over matched non-JEPA value/dynamics controls at the same inference and training budgets. The planned primary outcome is root-level exact minimax regret. The game scope remains two-player, alternating-turn, fully observed, deterministic, zero-sum games with exact legal actions and terminal rules. The current feasibility candidates are gravity Connect4 4x5 and Reversi6 only. Any result applies to these games and the admitted root distributions; it does not imply all two-player games.

The planner assumes a worst-case legal reply and computes a shallow max-min approximation. It does not predict a named opponent's behavior, take an uncalibrated policy expectation, prove equilibrium, or estimate exploitability. Behavior policies below generate training trajectories and calibrate separate matchup robustness; those uses remain distinct.

## Data source and provenance

Use only new project-generated self-play trajectories from the project's own versioned game rules and policy code. Do not ingest public games or third-party databases for this candidate. For every trajectory, record game/rules version and code hash, generator/policy-family IDs and hashes, root seed, episode index, player-to-policy assignment, ordered actions, terminal result, replay status, and source commit. A manifest pins artifact SHA-256, parser/schema version, environment, counts, rejected rows, and data fingerprint. Raw trajectories and checkpoints remain outside Git. The generated artifacts have no assigned redistribution license; do not publish them until a license and sharing policy are explicitly chosen.

The DEV06 model-blind root/action-value bank is exposed development material. Never reuse it as training, model-selection, or locked-final data. Generate disjoint banks under new schedules for each stage. Exact game rules may enumerate the complete legal `(own action, reply)` successor set on demand, but every such counterfactual branch inherits the source trajectory's group and split. No observed opponent action is used as a worst-case label.

## Opponent-policy design

Policy families are data-collection/evaluation agents, not latent opponent-response targets. Before generating model-facing data, pin at least four independently implemented behavior families that work on both games: uniform legal random; immediate-win/block tactical; position-heuristic; and bounded-search policy with a frozen node/time budget. Freeze policy source hashes, tie-breaking, randomness, seat schedule, and terminal handling. Version/hash each family independently. Each self-play episode records the two assigned families, and every family must appear in both seats in development schedule construction.

Training trajectories may use the declared training-family subset. An in-distribution validation set may share those families but must use disjoint episodes and seeds. The model-selection set uses a disjoint opponent-family subset. The locked-final set uses opponent families and root seeds unseen in training, validation, and selection. Report each family and seat separately. If a purported holdout family is a wrapper around a training policy with only a seed or parameter tweak, it is not a valid family holdout. Before fitting, reference agents must show that the suite is non-saturated and that seat effects are below the predeclared tolerance; otherwise revise only through a new model-blind protocol version.

These policies support robustness checks and collection diversity. The primary worst-case planner comparison still enumerates every legal reply using exact rules. Win rate against a fixed policy suite is secondary and must not be described as minimax value, behavioral prediction quality, exploitability, or equilibrium performance.

## Grouped splits and leakage audit

Create the split manifest at whole-trajectory level before extracting positions or legal counterfactual branches. Use separate IDs for train, in-distribution validation, model-selection, and locked-final. Split additionally by opponent family for the designated holdouts. Symmetry transforms, player/seat swaps, duplicate trajectories, state contexts, H1/H2 targets, and every counterfactual reply branch stay in the same connected group.

Audit exact serialized states and canonical state keys under every legal board symmetry and role swap. Check state-to-target, target-to-target, and branch-to-branch overlap across all splits. If a shared initial state or common prefix causes cross-split leakage, exclude that position consistently or group the connected episodes together; never keep the record in whichever split produces better support. Report raw and retained counts, deduplication/quarantine reasons, phase/game/family/seat strata, and per-split trajectory support. Zero cross-split overlap is required for every retained context, target, and branch key. Failed overlap, illegal transitions, malformed terminal results, or a dataset/source fingerprint mismatch blocks training.

The primary representation/planning scope is predeclared middle-to-late local positions with exact root action values. Whole-game strength is a separate claim and requires a separately powered match protocol. A final bank is generated and hash-committed only after method, configuration, and analysis code are frozen; it is never used to tune a model or select an opponent.

## Pre-fit power and model-selection gates

The existing gate's 100 unique roots and 50 beyond-depth roots per game are support floors only. Use a fresh model-blind schedule to estimate paired root-level variance, trajectory clustering, game/seat effects, and censoring. Predeclare the smallest scientifically meaningful reduction in minimax regret, desired power (at least 80%), family-wise alpha 0.05, multiplicity correction, training seeds, root/opponent counts, confidence interval method, timeout rule, and stopping rule before fitting. The five-point match-score margin from earlier drafts is not automatically a regret margin; justify any conversion from exact normalized utility and lock it before learned outcomes. A power simulation with chosen non-learned effect sizes is a planning assumption, not evidence of achieved power or a substitute for confirmatory results.

The confirmatory primary metric is paired root minimax regret, `V*(s) - V*(s, a_hat)`, using complete exact oracle action values and a fixed game/root weighting chosen in advance. Lower is better. Pair decisions by root, role/seat transformation, and model seed; use uncertainty clustered at trajectory and training-seed levels, report per-game estimates, and adjust the three primary JEPA-versus-control comparisons with Holm family-wise correction. No post-hoc root removal, game reweighting, opponent replacement, timeout recoding, or seed selection is allowed. Fixed-suite match win rate and exact action-ranking accuracy are secondary.

The main learned controls are: (1) direct encoded exact leaf-state value with the same planner and terminal handling; (2) matched non-JEPA task-value latent dynamics; and (3) decoded-state prediction with the same value head. Include a no-JEPA-at-inference ablation to isolate representation regularization from model-based planning. A direct KLENT-style policy/Q learner is an additional strong no-search control, not a substitute for same-search controls. Every arm sees the same trajectories, roots, branch exposure, legal transitions, terminal labels, optimizer schedule, training seeds, search budget, and inference censoring policy. Report both equal-update and equal-measured-compute tracks, including data generation cost, wall time, peak memory, parameters, encoder/predictor/value calls, and search nodes.

## Promotion and kill criteria

Do not begin training until (a) rule/reference differential validation passes on the frozen generators, (b) manifest and provenance checks pass, (c) zero-leakage grouped splits pass with support in every declared stratum, (d) opponent-family and seat schedules are non-saturated, (e) model-blind power/sample-size simulation reaches the predeclared target within available local compute, and (f) an independent implementation/protocol review finds no unresolved blocker.

Promote no JEPA-superiority claim unless the locked-final primary regret difference favors JEPA against each primary same-search control, its multiplicity-adjusted interval excludes zero, it exceeds the predeclared practical margin, and there is no material adverse game/seat/seed stratum, differential censoring, or latent collapse. Otherwise retain the result as negative or inconclusive and change the method only as a new version. If the support/power/compute gate is impossible for the two candidate games, narrow the claim or pivot before training; do not silently substitute an easier benchmark or spend on cloud compute.

## Source boundary

This protocol responds to the 2026-09-30 independent split review at `docs/V28_SPLIT_PROTOCOL_REVIEW_01.md`, the corrected DEV06 feasibility receipt, and the prior-art review in `docs/RELATED_WORK.md`. It is a proposed pre-fit design. It does not mean the data pipeline exists, the opponent suite has passed, the sample size is adequate, the method is novel, or JEPA beats a baseline.
