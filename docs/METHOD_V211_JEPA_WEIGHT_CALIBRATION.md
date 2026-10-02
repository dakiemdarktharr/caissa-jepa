# V2.11 method: reply-set JEPA loss calibration

**Status:** frozen pre-fit development/model-selection protocol and implementation, independently reviewed with no remaining P1/P2/P3 blockers. A V2.11 train-only grant is issued at `chess_data/v211_data_dev09_approval.json` (1,797 audited train records; SHA-256 `9d7d876fcb94ea67eb90fddb391cd5516f30acda8e25e3041140051134bb0adc`). The first local stable-memory screen failed; the supervised runner must meet its memory gate before fit. This protocol does not authorize confirmatory or locked-final evaluation.

## Research question and falsifiable hypothesis

Does increasing the loss coefficient on the existing reply-set JEPA objective from 1 to 8 improve fixed-budget two-ply max-min game score over (a) the same JEPA model trained at coefficient 1, (b) task-value-dynamics without JEPA, and (c) direct exact-leaf value, on both audited development games, without exceeding the frozen training/search compute caps?

The prospective rationale is limited: in the V2.10 no-update diagnostic, the median batchwise shared-encoder gradient-norm ratios `||g_J||/||g_task||` were 0.04937 for Connect4-6x7 and 0.04550 for Reversi6. Multiplying the JEPA coefficient by 8 would imply median norm ratios near 0.395 and 0.364 under local linear scaling. This is a calibration hypothesis only; it does not align gradient directions or establish a strength gain. V2.10's frozen conflict gate failed, so gradient projection is not part of V2.11.

## Scope and estimand

The primary domain remains deterministic, alternating-turn, fully observed, finite-action, zero-sum games with explicit legal actions and terminal rules. The tested adapters are Connect4 gravity 6x7 and Reversi6. The data are audited synthetic self-play from the local DEV09 dataset; they are not human-play data. Hidden-information, simultaneous-action, stochastic, and non-zero-sum games are outside this protocol.

The tested planner is fixed two-ply max-min over legal own actions and legal opponent replies. It models an adversarial worst-case legal reply; it does not predict a particular opponent's behavior, optimize expected return under an uncalibrated opponent policy, or compute equilibrium/exploitability. For each paired block, the score is the mean of the two color-swapped game scores minus 0.5. Report per-game and equal-weight two-game macro effects by checkpoint initialization seed, intervals over those 20 seed clusters, all forfeits/timeouts, and measured train/search compute.

## Controlled intervention and arms

The sole intervention is `jepa_weight=8.0` for the `reply-jepa` training arm instead of V2.9's `jepa_weight=1.0`. Architecture, optimizer, learning rate, EMA, batch size, variance/covariance terms, training examples and order, three epochs (87 updates), 20 initialization seeds, game adapters, planner, and move budget remain fixed. The fit is fresh from the same seeded initialization recipe; V2.9 checkpoints are not warm starts.

Compare the λ=8 candidate against three frozen arms: the existing same-seed V2.9 reply-JEPA λ=1 checkpoints, existing same-seed V2.9 task-value-dynamics checkpoints, and existing same-seed V2.9 direct-leaf checkpoints. Reuse is allowed only after a weights/receipt-only verifier confirms checkpoint and receipt hashes, seed, dataset, run, model code, adapter, and planner identity against their completed V2.9 ledgers. Do not inspect training-loss histories. No checkpoint is rewritten.

## Data, fit, and access boundary

Fit only the audited `train` split of DEV09 (`chess_data/v28_data_dev09`), pinned by the identity in `docs/validation/V211_JEPA_WEIGHT_CALIBRATION_V01.json`. Use 20 seeds `17,29,43,59,71,83,97,109,127,139,151,167,181,197,211,227,241,257,271,283`, three epochs, batch size 64, shuffle seed 701, and 87 updates per checkpoint. The new grant must bind the exact V2.11 method and panel-spec hashes and permit only train-split fitting. Validation and selection records, V08 outcomes, all training-loss histories, and locked-final records are forbidden inputs to fitting, model nomination, and this development match analysis. Evaluation uses only the new, committed match schedule and model files/receipts.

Do not download third-party data or use paid compute or external services. Keep all outputs under a fresh ignored `chess_data/v211_*` root. The Windows supervisor requires four stable 20-second samples with at least 2.0 GB available physical memory, caps the fit child at 1.3 GB committed memory and four CPU hours, stops reactively below 1.0 GB available physical memory, and caps total wall time at six hours. It launches below normal priority and preserves logs/status under ignored data. The fit child requires both the supervisor's one-run token and Windows Job Object membership. Before reading train data, the runner checks runtime parity against all 60 hash-bound V2.9 control receipts. On success, the supervisor hashes its status receipt and adds its source identity, job limits, stable preflight samples, peak working-set diagnostic and termination state to the panel ledger; Job Object committed-memory enforcement is a separate measure, and the matcher checks this attestation before accepting the candidate panel. The match verifier SHA-256-checks fit receipts against their hash-bound ledgers but parses only the `effective_run` JSON value up to (not including) the embedded training history. It loads only online and EMA parameter arrays from checkpoint NPZ files and never decodes their metadata. Fail closed on identity mismatch, pre-existing output, nonfinite values, invalid action/transition, resource guard, data-boundary violation, or incomplete seed/game/control grid. Never retry into an existing output root.

## Frozen development match design

The fresh schedule contains 240 paired blocks: 20 checkpoint seeds × 2 games × 3 controls × 2 match seeds per cell. Each block has two color-swapped games, for 480 games total. Match seeds begin at 35,010,000; the schedule's independently seeded row order and SHA-256 are frozen in the V2.11 panel JSON before outcomes. V2.11 matches use the same game situations, planner implementation, legal-action handling, deterministic tie-breaking, search transition cap, and 2-second per-move wall cap for every arm. Record realized transitions and CPU/wall time by seat. Paired checkpoint seeds and block match seeds are shared across all arms.

This is a bounded development/model-selection sample. The two adapter initial positions and repeated seed clusters do not support claims about broad position populations or training-seed population effects. The new match-seed block prevents reuse of the V2.9 schedule; it does not by itself remove situation-sampling limitations.

## Frozen nomination screen

Nominate λ=8 for a separately preregistered confirmatory study only if all screens pass:

1. Candidate-minus-control mean paired score is at least +0.05 separately on each game and in the equal-weight macro, against each of all three controls.
2. Every comparison has a complete 20-seed paired grid, reports seed-cluster uncertainty and per-seed effects, and has no unreported exclusion or schedule replacement. A nominally positive point estimate with a seed-cluster 95% interval spanning zero is described as uncertain development evidence, not a win; the confirmatory design must still be frozen independently.
3. The sum of candidate fit wall-seconds is no more than 3.5× task-value-dynamics fit time, and mean planner CPU per game-seat is no more than 1.25× each control in each game.
4. All four arms pass receipt, checkpoint, runtime, finite-output, rule, pairing, and access-boundary checks.

Any failed screen stops λ-only tuning. No hyperparameter subgroup search, post-hoc seed removal, alternate primary metric, or opening/situation replacement is allowed. Even a full pass only nominates a candidate; it does not establish JEPA superiority, exploitability, equilibrium quality, transfer, or Q1 publication readiness. If the candidate fails, report the negative/mixed result and use independent prospective evidence to choose whether to shrink the claim or design a materially different intervention.

## Reproducibility and reporting

Record Git commit, code/method/panel/data/approval/runtime fingerprints, seed, config, schedule hash, checkpoint/receipt hashes, match count, completed/skipped/forfeited/censored count and reason, search transitions, CPU/wall time, per-seed scores, game-level estimates, macro estimate, and seed-cluster uncertainty. Training diagnostics may be preserved in the ignored run artifact for engineering, but are not a selection metric and must not be inspected to choose this recipe. The report must state data are local synthetic self-play, identify the actual controls and planner, and distinguish development nomination from confirmation.

## Novelty boundary

The tested change is ordinary loss-weight calibration, not a new JEPA objective, gradient algorithm, opponent model, minimax algorithm, or equilibrium solver. Opponent-conditioned latent planning and value-aligned world-model losses have prior art. V2.11 can provide evidence only about whether this already-defined reply-set latent predictor contributes under one fixed-budget two-game development comparison. Any later research claim requires a broader related-work review, independent confirmation, cross-game or variant transfer, and stronger situation coverage.
