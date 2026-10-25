# Counterplay current state

Updated 2026-10-25T11:36:05.964856+07:00 (Asia/Saigon). Continue from evidence, not chat history.

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
  are not frozen. No accepted current corpus, integrated production trainer,
  paid rental, or locked-result access. Historical protocols and results remain
  intact and are not this study's confirmation.
- **I01 closed on synthetic correctness:** covariance derivative coefficient
  corrected to match the declared loss. All 192 numerical probes pass over six
  arms and every trainable tensor; baseline had 35 failures. The original
  encoder coordinate independently passes on all six arms. See
  [repair receipt](../docs/validation/CP01_GRADIENT_REPAIR_2026-10-25.json).
- **Immediate next task:** close the target-count correction from the independent data-foundation review of
  `counterplay/data.py`, `tools/counterplay_data.py`, and the
  [data contract](data_contract.json), then generate one pinned bounded
  development corpus. [Review](reviews/DATA_FOUNDATION_CP01_2026-10-25.md) conditionally permits
  one feasibility batch; explicit H1/H2/H4 support/missing counts must be added
  before acceptance. This is not a pilot training grant. Construction is
  capped at 100 reference-candidate episodes plus 64 training episodes and
  300 CPU seconds, with complete reference failures/yield retained. No actual
  corpus generation has run yet. Exact H4-nonterminal training banks are an
  explicitly narrower initial population; count terminal/short exclusions.
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
- **Measurement:** journal verified; latest [snapshot](../research/results/snapshot-aac52d91312e03b6911f8d2f4151d7c102c1a62fad3414476764e1f94e19a3c4/snapshot.json)
  contains 22 unique events across 4 workflow runs. Failures and unavailable
  agent usage remain recorded. No trained-model results. Bounded export
  segmentation still required before long production runs.
- **Agents/budget:** requested lead `gpt-6.1-sol` / `xhigh`; explicitly created
  reviewer `gpt-6-luna` / `xhigh`, no recursive delegation. Runtime attestation,
  actual tokens and billing are not exposed and remain null. Preserve settings.
  $50/month compute ceiling; no rental initiated or paid offer selected.
- **Last verified prior remote:** `5378c0ce3c51fb1a04723a2b2b30d4a573d953a0`
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
