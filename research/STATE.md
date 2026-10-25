# Counterplay current state

Updated 2026-10-25T11:57:10.863347+07:00 (Asia/Saigon). Continue from evidence, not chat history.

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
- **Frozen stop applied:** final C4<=12 screen from
  `c0503beeee856a51a781c9c2ea29b0434475f490` completes 59/59 references but
  fails reference and necessary sign-support gates: C4 0/9 pairable and zero
  potential nonzero common-sign roots; Reversi 11/50 pairable, four potential.
  16.308 s wall / 16.143 s CPU, 80,220,160-byte peak RSS. Cumulative construction
  CPU 31.534437001 s. Both attempts use exactly the same original 164 episodes.
  See [final disposition](../docs/validation/CP01_FINAL_SCREEN_DISPOSITION_2026-10-25.json).
  **No third screen and no trainer construction for this retired design.**
- **Current adopted deliverable:** bounded feasibility technical report under
  CP-D006 and [analysis scope](feasibility_analysis.json). The original learned
  mechanism study is unexecuted, not a completed negative JEPA comparison.
  Review 2 did not approve a pilot; Review 3/final locked study not reached.
  All production trainer/evaluator, recovery/export scaling and inferential
  analysis hooks remain requirements for a future separate study.
- **Immediate next task:** publish this failed-batch milestone, then export
  both receipts' per-root units with `tools.counterplay_feasibility_units` to
  `/tmp` while the analysis source is clean; copy reviewed small CSVs into
  `research/results/`. Complete `paper/counterplay-feasibility.md` and PDF,
  generated tables/figure, claim map and reproduction instructions, then obtain
  fresh independent scoped Review 4 and verify GitHub recovery. Do not claim
  novelty, model performance, population prevalence, equivalence or independent
  replication from the finite dependent screens. Future Reversi-only work
  requires a new prospective protocol and is outside this retired design.
- **Verified checks:** 41/41 scoped tests pass, 0 failures/errors/skips, 1.275 s
  on 2026-10-25. See [producer-test receipt](../docs/validation/CP01_DATA_PRODUCER_TESTS_2026-10-25.json).
  Earlier 17-test workflow and 38-test foundation receipts remain dated history;
  full repository suite not rerun. Initial syntax/fixture errors are retained.
- **Measurement:** journal verified; latest [snapshot](../research/results/snapshot-d3324954d19c278095d0f88ade020bffe478a49e2b976de521b3a6f29ea4e75b/snapshot.json)
  contains 41 unique events across 8 runs (workflow plus development data). Failures and unavailable
  agent usage remain recorded. No trained-model results. Bounded export
  segmentation still required before long production runs.
- **Agents/budget:** requested lead `gpt-6.1-sol` / `xhigh`; explicitly created
  reviewer `gpt-6-luna` / `xhigh`, no recursive delegation. Runtime attestation,
  actual tokens and billing are not exposed and remain null. Preserve settings.
  $50/month compute ceiling; no rental initiated or paid offer selected.
- **Last verified prior remote:** `c0503beeee856a51a781c9c2ea29b0434475f490`
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
