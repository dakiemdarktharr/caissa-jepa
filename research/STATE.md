# Counterplay current state

Updated 2026-10-25T11:22:35.082485+07:00 (Asia/Saigon). Continue from evidence, not chat history.

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
- **Immediate next task:** repair I01 in `two_player/v212_model.py`; reproduce
  the old covariance mismatch, then verify full-objective numerical derivatives
  for all six affected arms and all parameter tensors with frozen EMA targets,
  covariance-active and mixed-mask fixtures. Tolerance is absolute 1e-7 plus
  relative 1e-4. Update affected source-bound accounting expectations without
  inventing compute totals. Independent inspection and actual checks required.
- **Subsequent Review 2 work:** freeze/generate bounded fresh data and selected
  H1/H2/H4 windows, validate rules/references and overlap/support; integrate
  trainer/evaluator and Adam/EMA/RNG/cursor checkpoint-resume; wire and verify
  every measurement boundary, resources and export segmentation. Only then a
  bounded development pilot, followed by synthetic analysis validation and
  Review 3 freeze before locked evaluation.
- **Verified workflow checks:** 17/17 ledger/checkpoint tests pass with 0
  failures/errors/skips, 0.801 seconds on 2026-10-25. Two protocol versions
  parse; 31 unique issue IDs preserve I01-I30 and W13. Detailed receipt:
  [bootstrap](../docs/validation/CP01_BOOTSTRAP_2026-10-25.json). Full repository
  suite not rerun; historical missing-artifact/Windows limitations remain.
- **Measurement:** durable journal `chess_data/research_metrics.sqlite` verified;
  latest [snapshot](../research/results/snapshot-93f01ce1daaf4409e6d4dffd1981a707158947d59832b98226d02d5b1cb7d75d/snapshot.json) has 15 unique
  events across 3 workflow runs. Cumulative snapshots need deduplication.
  The exporter still needs bounded segmentation before long production runs.
- **Agents/budget:** requested lead `gpt-6.1-sol` / `xhigh`; explicitly created
  reviewer `gpt-6-luna` / `xhigh`, no recursive delegation. Runtime attestation,
  actual tokens and billing are not exposed and remain null. Preserve settings.
  $50/month compute ceiling; no rental initiated or paid offer selected.
- **Last verified prior remote:** `71a92754230715f1fe4538554a2eac49a155dd97`
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
