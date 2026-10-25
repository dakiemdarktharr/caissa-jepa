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
- **Budget:** $50/month compute ceiling. No rental initiated. Agent models and
  reasoning levels still require explicit approval; no subagents launched.
- **Backup decision:** user chose GitHub only, with large artifacts local.
  Source, notes and reviewed small result snapshots are to be pushed every
  verified milestone and at a 15-minute active-work target. Raw data, weights,
  environments, logs and unreleased results are not protected by this choice.
- **Verified earlier remote checkpoint:** `0ce359a6c0b811d478f9a4e90f2cded2f68833e9`
  on `origin/main`, destination `dakiemdarktharr/caissa-jepa`. It contains the
  original audit, data-readiness note and first workflow design. The containing
  commit of this file records the subsequent instrumentation/audit milestone.
- **New implementation:** durable `research_ledger.py`, objective measurement
  adapter, ledger CLI, and explicit-file Git checkpoint CLI. Producers and
  scheduled invocation must be wired into the future runner. No unattended
  scheduler or automatic training process is running.
- **Verification:** focused tests exercise acknowledged-event recovery after
  process exit, concurrency, duplicate/conflicting replay, integrity checks,
  missingness, locked-output withholding/release, real-objective output
  equivalence, Git round-trip recovery, exclusions and divergence rejection.
  The milestone receipt records the executed count and source hashes.
- **Data:** active checkout contains only 12 old compute-pilot artifacts.
  A separate local archive contains about 933 MB of historical experiments;
  selected DEV09/V2 bytes were matched to original hashes. Neither is an
  accepted corpus for the revised study. No audited current chess corpus found.
- **Next action:** adopt the prospective study protocol and complete Review 1;
  then fix and numerically verify the covariance gradient. Freeze the data
  contract, build a small audited corpus, and integrate the trainer with all
  required logging/checkpoint hooks before any production training.

Read next:

1. [Workflow research audit](../docs/COUNTERPLAY_WORKFLOW_RESEARCH_AUDIT_2026-10-25.md)
2. [Metrics and recovery contract](../docs/COUNTERPLAY_METRICS_AND_RECOVERY_2026-10-25.md)
3. [Updated workflow](../docs/COUNTERPLAY_AGENTIC_WORKFLOW_2026-10-25.md)
4. [Scientific project review](../docs/PROJECT_REVIEW_2026-10-25.md)
5. [Data-readiness note](../docs/COUNTERPLAY_CHESS_AND_DATA_READINESS_2026-10-25.md)
