# Exploratory two-player JEPA pilot — 2026-09-29

**Result: the pilot establishes executable, audited multi-game training, but does
not establish a JEPA planning benefit.** The exact-state search diagnostic is at
a ceiling for every learned variant. Hybrid predicted-latent planning makes some
Reversi errors that direct re-encoding avoids. Larger training and confirmation
do not proceed on this evidence; the next milestone is benchmark redesign.

This is an actual 21-run experiment, separate from fixture tests. It is not a
match tournament, exploitability evaluation, model-selection study or final test.

## Protocol and provenance

- Source commit: `66ff9f27b25bc8d0bfc92628976a91c122724f87`.
- Training source SHA: `c22863ccaf6c1edacc115f7090e6294b1d280d441d3b5df70159acdec34578a2`.
- Dataset fingerprint: `7430e1cd7204ca09c6c7b730e694282435a7e91bfc8e8938f2554563707584e8`.
- Frozen v1 plus pre-fitting v1.1/v1.2 amendments; seeds 17,29,43; seven variants;
  latent32; 10 epochs; batch64; Adam0.001; 180 steps and 11,290 record exposures
  per run. One shared set of weights covers all three training games.
- Environment: CPython3.11.9, NumPy2.4.6, Windows, AMD Ryzen AI5 340 (6 cores,
  12 logical processors), 16,418,648,064 bytes physical memory, one BLAS thread.
- Exact source/config/data/checkpoint/schedule hashes, all per-seed metrics and
  conditional bootstrap intervals are in
  [the aggregate receipt](validation/TWO_PLAYER_PILOT_20260929.json).
- Local trajectories: `chess_data/two-player-pilot-v12/`. Local checkpoints,
  epoch losses, frozen schedule and detailed decisions:
  `chess_data/two-player-runs-v12/`. These generated artifacts remain ignored.

Data was generated from project-owned rules, random play and immediate-win
preference, not human or optimal play. No external data was downloaded or used.
Local research use is authorized; a public generated-artifact license has not
been assigned. Only aggregate measurements and hashes are published.

## Data feasibility and negative audit result

The first whole-game audit failed the predeclared phase-coverage gate. Its
manifest remains at `chess_data/two-player-pilot-v1/manifest.json`, fingerprint
`c506b7907bc0917addb8478d3ea69331a2db31dbcd7d29c1318efeef901f5dda`.
No training consumed that failed version. Before fitting, v1.2 narrowed all
splits to root ply/area >=1/3; this limits claims to middle/late local planning.

The passing version contains 800 generated trajectories, 747 symmetry-unique
trajectories and 2,572 retained records. Exclusions: 53 duplicate trajectories,
3,502 early-context records outside scope, and 667 records with cross-split
context/H1/H2 overlap. These categories use different counting units; do not add
trajectory and record counts. All legal trajectories and outcomes were replayed.

| Game | Train | Validation | Selection | Locked final | Transfer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tic-tac-toe 3x3 | 183 | 30 | 63 | 83 | — |
| Gravity connect-3 4x4 | 300 | 41 | 40 | 51 | — |
| Reversi 4x4 | 646 | 79 | 143 | 135 | — |
| Gravity connect-3 3x4 | — | — | — | — | 778 |

Training is sample-weighted toward Reversi. Selection/final predictions: **zero**.
Identity/rules audits inspect those splits without scoring models on them.

## Planning diagnostic and uncertainty

Before scoring, select up to24 symmetry-unique positions per game by SHA order,
with at most4 empty cells. Depth2 max-min uses exact legal transitions, node1024
and time1s caps. The oracle exhaustively solves these tiny positions using the
same adapter. Regret is best oracle action value minus the selected action's
oracle value, in [0,2]; lower is better. This is not a win-rate or Elo metric.

| Game | Scheduled positions | Trajectory support in representation evaluation | Positions with neural leaves | Positions with unequal oracle action values |
| --- | ---: | ---: | ---: | ---: |
| Tic-tac-toe | 18 | 11 | 12 | 15 |
| Connect3 | 2 | 11 | 0 | 1 |
| Reversi4 | 24 | 15 | 18 | 3 |
| Held-out connect3 size | 24 | 183 | 12 | 12 |

**Every exact-state learned variant has zero regret at all three seeds.** This
ceiling prevents identifying a JEPA advantage. The no-model zero-leaf baseline
also has zero regret except Reversi (1/24). The tiny connect3 sample never queries
a neural leaf. Do not treat identical results or a degenerate bootstrap interval
as evidence of equivalence or successful transfer.

Hybrid mean Reversi regret is shown as each seed, avoiding a misleading pooled
confidence claim. All other games have zero hybrid regret for every variant.

| Variant | Seed17 | Seed29 | Seed43 |
| --- | ---: | ---: | ---: |
| Full JEPA | 0.0417 | 0.1250 | 0.0417 |
| H1 recurrent inference | 0.1250 | 0.0417 | 0.1250 |
| No-response | 0 | 0.0833 | 0.0833 |
| No-variance | 0.0417 | 0.1250 | 0.0417 |
| Direct policy/value, exact re-encoding | 0 | 0 | 0 |
| Decoded dynamics | 0.1250 | 0.0417 | 0.0417 |
| Value-only dynamics | 0.0417 | 0.0417 | 0.0417 |

There were 2,856 learned planner decisions (21 runs x68 positions x2 tracks),
plus68 no-model decisions, with zero censored/failed decisions. Seeds share one
small schedule, so decisions are not independent replicates. These descriptive
differences do not justify statistical superiority or rejection of JEPA generally.
There are no confirmatory p-values or post-hoc opening replacements.

## Representation and resources

Across 84 game/variant/seed evaluations, effective rank was 8.210–12.188; no
predeclared collapse alert fired. NLL/MRR/top1 describe imitation of synthetic
behavior, and value MSE uses its Monte Carlo outcome, not minimax truth. H1/H2
latent errors are recorded but are not directly comparable across independently
learned target representations/objectives.

For full JEPA, per-seed policy NLL ranges were 1.2194–1.2720 (tic-tac-toe),
1.2549–1.2793 (connect3), 0.4910–0.5087 (Reversi), 1.0925–1.0985 (held-out size).
Value MSE ranges were 0.9195–0.9410, 0.9449–0.9607, 0.7298–0.7347 and
1.0536–1.0726 respectively. The receipt retains all variants, horizon counts,
covariance and norm diagnostics. NLL/value uncertainty uses500 trajectory-cluster
bootstrap replicates with seed901, conditional on the development dataset.
Three training seeds do not establish population-level reliability; the ranges
above are descriptive, not confidence intervals. Calibration, tactical strata,
few-shot transfer and full opponent robustness remain unevaluated.

Each run took 8.84–18.64s (total training251.21s); maximum traced allocations were
16,966,858 bytes. This is tracemalloc memory, not process RSS. Early runs overlapped
regression tests; timings include audit/serialization and tracing. No dedicated
hardware speed or exact-FLOP claim is permitted. Local run artifacts occupy
11,245,483 bytes at receipt generation. All models allocate20,360 parameters;
active tensor counts differ and include masked rows. Full and no-var seed17
parameters differ by at most3.19e-7: this experiment barely exercises the variance
penalty and cannot establish its usefulness or dispensability.

## Verification, decision and remaining work

87 unittests pass (52.122s), standalone core checks pass, and source release smoke
passes all13 fixture checks. Tests cover all5,478 reachable tic-tac-toe states,
rule/symmetry/perspective properties, seven-variant numerical gradients, resume,
serialization corruption, leakage and budget edges. Reviewer findings and
remaining limitations are in [the independent review](INDEPENDENT_REVIEW_20260929.md).
Tests are not research performance evidence; no new installer was built.

The broad-benefit kill criterion is not met: no gain over direct/decoded controls
across two game families is shown. **Freeze this pilot as negative/inconclusive
feasibility evidence and pivot the next milestone to a discriminating development
benchmark**, rather than scale epochs or open final predictions. Freeze a new
protocol before new fitting, using sufficient positions with nonterminal leaves,
meaningful oracle gaps beyond search depth, independent rules and game-balanced
support. Add a recurrent multi-step-trained consistency control and dedicated
compute tracks. A larger full-game study, held-out family, few-shot adaptation,
opponent/reference matches and confirmatory power analysis remain necessary.

This project has reached an auditable exploratory milestone, not Q1 submission
readiness. The research hypothesis, novelty and useful transfer remain unproven.
