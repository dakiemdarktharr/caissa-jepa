# Counterplay current state

Updated 2026-10-25T11:51:14.155765+07:00 (Asia/Saigon). Continue from evidence, not chat history.

- **Current gate:** Review 1 accepted the new outcome-independent CP-01 v2
  empirical design for entry to foundation work / Review 2. The original
  conditional review and targeted closure are preserved in
  [Review 1](reviews/REVIEW1_CP01_2026-10-25.md) and
  [closure receipt](../docs/validation/CP01_REVIEW1_CLOSURE_2026-10-25.json).
  No pilot or locked study is authorized by that disposition.
- **Design:** same-size Connect Four 6x7 and Reversi6; common terminal-solved
  fork utilities; signed magnitude-matched scalar repairs at reference-critical
  versus noncritical replies. Primary estimates are conditional and missing
  when any seed has zero matches or unresolved matching. Every scheduled root
  remains in coverage-adjusted policy bounds. No latent-information causal
  claim, JEPA-win requirement or board-size-transfer primary. Five arms and
  H2 primary; H4/play separately costed. Chess readiness decision before Review 3.
  See [contribution](CONTRIBUTION.md), [protocol](protocol.yaml),
  [prior work](PRIOR_WORK.md), [decisions](decisions.md), [issues](issues.csv).
- **Scientific execution:** pre-training; 0 revised-study fits and 0 matches.
  Loss/regret/critical-reply preservation/Elo not measured. Final counts/seeds
  are not frozen. One development-data construction attempt failed reference yield; no accepted corpus or integrated production trainer,
  paid rental, or locked-result access. Historical protocols and results remain
  intact and are not this study's confirmation.
- **I01 closed on synthetic correctness:** covariance derivative coefficient
  corrected to match the declared loss. All 192 numerical probes pass over six
  arms and every trainable tensor; baseline had 35 failures. The original
  encoder coordinate independently passes on all six arms. See
  [repair receipt](../docs/validation/CP01_GRADIENT_REPAIR_2026-10-25.json).
- **First actual data feasibility:** source `09f18a5cf5e9a827ce526997714a035d4b07175e`,
  [receipt](../docs/validation/CP01_DATA_ATTEMPT1_2026-10-25.json), data hash
  `442e97c0d685494df753a5723a0bb3389ad4e960ad6ac3c52e416256217b650b`.
  164 episodes; 256 train / 64 development windows; zero prohibited selected
  target/root collisions. All 57 attempted references completed. Pairable
  roots: C4 0/7 (43/50 episodes no late candidate); Reversi 11/50. Required
  5/game floor failed. 15.551 s wall, 15.392 s CPU, 80,281,600-byte peak RSS.
  Raw data remain ignored at `chess_data/cp01-dev-attempt1/data.json`.
- **Immediate next task:** after publishing this clean source, run the one
  final amended screen: `timeout 330s env OPENBLAS_NUM_THREADS=1
  OMP_NUM_THREADS=1 .venv/bin/python -B -m tools.counterplay_data
  chess_data/cp01-dev-attempt2 --receipt
  docs/validation/CP01_DATA_ATTEMPT2_2026-10-25.json --run-id cp01-data-attempt2`.
  [Independent design review](reviews/CP01_FEASIBILITY_DESIGN_2026-10-25.md)
  accepts CP-01 v3 for this invocation only. C4 empties 8->12, same episodes
  and seed namespace, caps unchanged; Reversi stays at 6. Cumulative builder
  CPU cap 300 seconds, first batch charged 15.391540855 seconds. New gate:
  at least 2 roots/game and 20% of pairable roots with potential nonzero
  same-sign residual domain support. This is not actual model matching/power.
  If either gate fails, retire the two-game matched mechanism design before
  trainer construction and write the scoped feasibility report. Do not retry:
  the one-shot stop is an operator/protocol constraint, not a lock in code.
- **Subsequent Review 2 work:** freeze/generate bounded fresh data and selected
  H1/H2/H4 windows, validate rules/references and overlap/support; integrate
  trainer/evaluator and Adam/EMA/RNG/cursor checkpoint-resume; wire and verify
  every measurement boundary, resources and export segmentation. Only then a
  bounded development pilot, followed by synthetic analysis validation and
  Review 3 freeze before locked evaluation.
- **Verified checks:** 41/41 scoped tests pass, 0 failures/errors/skips, 1.275 s
  on 2026-10-25. See [producer-test receipt](../docs/validation/CP01_DATA_PRODUCER_TESTS_2026-10-25.json).
  Earlier 17-test workflow and 38-test foundation receipts remain dated history;
  full repository suite not rerun. Initial syntax/fixture errors are retained.
- **Measurement:** journal verified; latest [snapshot](../research/results/snapshot-99c0eb8a7253a461cc664ec05785b009802040e65faa991f0d0738d4fe66fd9f/snapshot.json)
  contains 34 unique events across 6 runs (workflow plus development data). Failures and unavailable
  agent usage remain recorded. No trained-model results. Bounded export
  segmentation still required before long production runs.
- **Agents/budget:** requested lead `gpt-6.1-sol` / `xhigh`; explicitly created
  reviewer `gpt-6-luna` / `xhigh`, no recursive delegation. Runtime attestation,
  actual tokens and billing are not exposed and remain null. Preserve settings.
  $50/month compute ceiling; no rental initiated or paid offer selected.
- **Last verified prior remote:** `d2d12f29761f0e745d9c32a2b8df434cb6d1a84a`
  on `origin/main`, `git@github.com:dakiemdarktharr/caissa-jepa.git`, verified
  2026-10-25. Bootstrap system SSH permissions and sandbox DNS initially failed;
  command-level `GIT_SSH_COMMAND='ssh -F /dev/null'` with network access worked.
  Use the checkpoint CLI, normal push, then verify/report the new hash. Do not
  chase the containing commit hash with documentation-only commit loops.
- **Preservation:** every new commit refreshes README's marked status, selecting
  only reviewed small files. GitHub only; raw data, weights, environments,
  logs and unreleased outcomes remain ignored/local and can be lost. Earlier
  recovery at `49f9f05` freshly cloned five files and passed 14 tests on this
  same host/environment; that is not full-machine or trainer recovery.
  The historical Windows Obsidian vault is unavailable here; canonical notes
  remain in Git. No unattended scheduler/service is installed.
