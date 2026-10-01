# V2.8 learned-match evaluator review 01

**Date:** 2026-10-01

**Review:** independent, read-only, gpt-6-luna / high
**Scope:** paired-game evaluator, locked schedule/commitment linkage, inference budgets, replay and receipt checks.

## Findings and disposition

The first review identified two release blockers and one replay-validation gap:

1. The evaluator treated the tracked commitment wrapper as though it contained schedule rows, while the analysis command consumed the separate ignored `{manifest, blocks}` artifact. Their receipt hashes could not agree. The loader now resolves the wrapper's in-repository artifact path, verifies byte count and SHA-256, requires exact agreement between the raw manifest and tracked commitment, regenerates and hashes all 9,600 rows, checks the generator source hash, and checks the pinned analysis source hash. The evaluator receipt binds the raw schedule artifact hash used by analysis.
2. The per-move limits were implicit defaults, not part of the prefit protocol. The commitment wrapper now declares V01's 2-second and 500,000-transition limits. The loader checks those values and confirmatory execution rejects any other budget.
3. Successful move transcripts and failed attempts needed stronger independent replay checks. Replay now validates per-move elapsed time and transition counts, reconciles per-player counters, and records/reconciles the timing and transitions of forfeiting attempts. Illegal-action and timeout forfeits were specifically probed.

The follow-up review then found a separate P1 in the analysis handoff: the analysis CLI did not enforce the pinned analysis-source SHA in the wrapper, which could allow a post-outcome change to the decision rule. The analyzer now independently resolves and fingerprints the raw schedule artifact, checks its manifest and generator hash, validates the fixed match budget and its own source SHA against the wrapper, and only then accepts the evaluator receipt. A tampered-analysis-source test covers the fail-closed path.

The final independent review found no remaining P1/P2 issue in this evaluator and analysis integrity scope. The combined evaluator, analysis, and schedule-power suites passed **19/19 tests**; both CLI help checks passed; the timeout-forfeit replay passed; and evaluator and analyzer independently loaded the same 9,600 schedule rows with raw-artifact SHA-256 `f18efbcac1524098933b5a838dfe0201d94bc8aaec8ca3db3c84`.

## Evidence limits

This is software and protocol validation only. The locked results are still prefit: no project-data checkpoint exists, DEV09's manifest remains `training_approved: false`, no JEPA or control has been fit, and no model-match outcome was produced. The evaluator only compares learned checkpoints from a fixed 20-seed panel on the two tested games from their adapter initial states, with both color assignments and a common two-ply minimax planner. It does not test opponent behavior prediction, equilibrium, exploitability, cross-game transfer, or general game strength. Passing evaluator tests is not evidence that JEPA beats either baseline or that the proposed contribution is novel. The analysis CLI has not yet been run end-to-end on genuine evaluator outcomes because there are none.

The current local shell could syntax-compile the changed Python files but lacked NumPy/pytest, so the 7/7 execution result comes from the independent reviewer's available test runtime. The unfinished model-blind proxy run remains separately preserved as a 4,839-row ignored `.tmp` file; it is not an evaluator result or a completed runtime gate.
