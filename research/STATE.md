# Counterplay current state

Updated 2026-10-25 (Asia/Saigon). This file is the compact continuation entry
point; resolve claims using linked versioned evidence rather than chat memory.

- **Scientific status:** pre-training. Counterplay is a proposed
  outcome-independent study of critical opponent replies. Chess is a staged
  extension. No accepted current corpus or integrated production trainer.
- **Immediate blockers:** confirmed covariance-gradient weighting defect;
  prospective protocol; dataset/split/window contract; trainer/evaluator
  integration; trustworthy references and analysis validation. Recording
  metrics does not close these issues.
- **Budget and agents:** $50/month compute ceiling. No rental initiated.
  Approved lead: `gpt-6.1-sol` / `xhigh`; all workers and reviewers:
  `gpt-6-luna` / `xhigh`. No silent substitution or repeat model approval.
  Startup instructions are in `docs/COUNTERPLAY_AGENTIC_START_PROMPT.md`;
  no subagents or training were launched while preparing that prompt.
- **README publication rule:** every new commit refreshes the marked status
  section with actual metrics/progress, evidence links and next action. The
  checkpoint CLI checks that refresh; unavailable metrics remain missing.
- **Backup decision:** user chose GitHub only, with large artifacts local.
  Source, notes and reviewed small result snapshots are to be pushed every
  verified milestone and at a 15-minute active-work target. Raw data, weights,
  environments, logs and unreleased results are not protected by this choice.
- **Verified earlier remote checkpoint:** `0ce359a6c0b811d478f9a4e90f2cded2f68833e9`
  on `origin/main`, destination `dakiemdarktharr/caissa-jepa`. It contains the
  original audit, data-readiness note and first workflow design. The containing
  commit of this file records the subsequent evidence milestone.
- **Verified implementation checkpoint:** `49f9f05f597c250bdab2815b5e3bc29950f53a9c`
  was pushed normally and freshly cloned from GitHub. Five source hashes and
  14 focused tests pass in that clone, on the same host/environment. See
  `docs/validation/GITHUB_RECOVERY_2026-10-25.json`. A later checkpoint-tool
  compatibility correction accepts standard CSV CRLF bytes while still
  rejecting actual trailing spaces; its 15-test receipt and exact source
  hashes are in `docs/validation/WORKFLOW_CHECKPOINT_CRLF_2026-10-25.json`.
- **New implementation:** durable `research_ledger.py`, objective measurement
  adapter, ledger CLI, and explicit-file Git checkpoint CLI. Producers and
  scheduled invocation must be wired into the future runner. No unattended
  scheduler or automatic training process is running.
- **Verification:** focused tests exercise acknowledged-event recovery after
  process exit, concurrency, duplicate/conflicting replay, integrity checks,
  missingness, locked-output withholding/release, real-objective output
  equivalence, Git round-trip recovery, exclusions and divergence rejection.
  The original milestone receipt records 14 passing tests; the subsequent
  regression suite records 15. The first checksummed `research/results/`
  snapshot preserves five workflow events; a later snapshot adds the failed
  publication and its regression verification, preserving seven events.
  These are infrastructure measurements, not scientific training outcomes.
  The README publication gate subsequently passed 17 focused tests; its
  initial fixture error and correction are both retained in
  `docs/validation/WORKFLOW_README_GATE_2026-10-25.json` and the linked first
  attempt. The latest snapshot has 10 unique events across 2 workflow runs.
- **Data:** active checkout contains only 12 old compute-pilot artifacts.
  A separate local archive contains about 933 MB of historical experiments;
  selected DEV09/V2 bytes were matched to original hashes. Neither is an
  accepted corpus for the revised study. No audited current chess corpus found.
- **Next action:** adopt the prospective study protocol and complete Review 1;
  then fix and numerically verify the covariance gradient. Freeze the data
  contract, build a small audited corpus, and integrate the trainer with all
  required logging/checkpoint hooks before any production training.
- **Export scale gate:** the current exporter writes the full database and
  fails above its cap. Implement verified bounded segments/rotation with
  linked provenance and complete analysis coverage before long runs.

Read next:

1. [Workflow research audit](../docs/COUNTERPLAY_WORKFLOW_RESEARCH_AUDIT_2026-10-25.md)
2. [Metrics and recovery contract](../docs/COUNTERPLAY_METRICS_AND_RECOVERY_2026-10-25.md)
3. [Updated workflow](../docs/COUNTERPLAY_AGENTIC_WORKFLOW_2026-10-25.md)
4. [Scientific project review](../docs/PROJECT_REVIEW_2026-10-25.md)
5. [Data-readiness note](../docs/COUNTERPLAY_CHESS_AND_DATA_READINESS_2026-10-25.md)
