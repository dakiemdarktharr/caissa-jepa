---
title: Counterplay — Continuous metrics, GitHub preservation, and recovery
date: 2026-10-25
tags: [counterplay, metrics, reproducibility, recovery]
---

**Contract:** record measurements at their producing boundary, retain their
identity/denominator and failures, export compact analysis-ready evidence,
and verify its GitHub checkpoint. Agents do not reconstruct missing scientific
numbers from memory. “Continuous” means event-based and scheduled collection
during execution, not an LLM watching every log line or an always-running
service that has not been installed.

The user selected **GitHub only** for now. Large datasets, weights, environments
and raw logs remain local and ignored. No new storage account, upload, rental,
background service or scientific experiment is authorized by this document.

**1. Identity that accompanies every observation**

Run/attempt/parent IDs; phase (workflow, synthetic smoke, development or locked
evaluation); protocol/version and SHA-256; exact Git commit and dirty-tree
status; model arm and initialization seed; corpus/split/generator identities;
configuration and schedule; environment (Python/libraries, CPU/GPU, OS,
threads, precision and deterministic settings); wall-clock UTC and monotonic
durations; checkpoint and reference identities; metric definition/version,
unit, population and aggregation rule.

Scientific runs require a clean pinned source tree or an explicitly archived
patch identity, not merely a nearby Git commit. The ledger records supplied
identities; it does not authenticate files unless the caller computes and
checks their hashes. Repeated attempts retain distinct attempt IDs and a
parent/cause. Replaying the same event key is idempotent only when the
measurement content is identical; conflicting reuse fails.

**2. What to record and how often**

| Boundary | Required paper/evidence measurements | Cadence / unit |
| --- | --- | --- |
| Dataset preparation | Raw/retained episodes and windows per game/split/policy; exclusions by reason; duplicates; prohibited and permitted overlap; legal replay failures; H1/H2/H4 eligible/missing/terminal counts; label provenance and generation/reference cost | Every completed shard or bounded episode batch, and final manifest; counts are integers with explicit denominators |
| Objective / optimizer | Total and component losses, declared weights, policy NLL, root/rollout value MSE, latent/raw prediction losses by horizon, gradient norms before/after clipping, clipping scale, learning rate, update/epoch, consumed-window count, target masks/counts, optimizer/EMA settings | Every optimizer update for cheap scalars; objective-only calls are labelled separately. Store batch size/weight so later averages are correct |
| Representation diagnostics | Latent mean/std, variance/covariance terms, effective rank and covariance spectrum, collapse/finite checks | At declared validation/checkpoint intervals; retain already-computed diagnostics. Charge extra diagnostic cost. Raw latent MSE is not an uncalibrated cross-arm leaderboard |
| Development validation | Prespecified loss, policy/value and decision metrics; split/checkpoint identity; count and missingness | Fixed validation schedule, not chosen when results look good. Never train on validation/selection/final records |
| Root/intervention evaluation | Corpus/game/seed/root/episode-group IDs; reference class/horizon; action regret, decision agreement, tie-aware critical-reply preservation; natural/repair/control condition; margin/support strata; matching and unmatched counts; validity/timeout status | Every root × checkpoint × declared condition. Preserve paired units, reference scale and weights; separate exact solved, finite-horizon and engine-reference outcomes |
| Chess / paired play | Opening-group, pair, seed, opponent/checkpoint and colors; W/D/L; game score; completed/incomplete pair; illegal move, timeout, truncation and failure reason; search/time/node budget | Every game and completed pair. Elo derived from score with paired uncertainty; endpoints with no finite estimate are null, not arbitrary capped ratings |
| Resources | Wall/CPU seconds, RSS bytes, device/precision/threads, model and exact-rule calls, nodes, throughput; GPU memory/utilization only if used; storage bytes and measured rental/transfer cost | Cheap resource samples initially every 30 seconds, plus stage/run boundaries. A sampling interval does not prove true peak RSS or hard memory containment |
| Agent work | Task/role and approved model/effort; input/output/cached tokens and actual bill when exposed; tool calls/errors; retries; elapsed time; accepted/rejected deliverables and reasons; source search/retrieval identities | Each task/handoff and consequential decision. Unexposed token/billing fields remain null with a reason. Do not invent retrospective counts |
| Integrity / recovery | Journal verification, pending export count, export hashes, local/remote Git commits, push time/status, last verified off-device checkpoint, restore test outcome | Every export/push and milestone; declare a missed checkpoint immediately when discovered |
| Paper | Claim ID, result table/row, code/config/input identity, estimator and uncertainty, figure script, citation URL/DOI and checked supporting passage, deviations/limitations | Every quantitative figure/table and substantive claim revision |

These cadences are initial operating choices, to be profiled before the
scientific protocol freezes. “Every update” is appropriate for these small
models; avoid storing full tensors each step. Target logging overhead below
2% of measured end-to-end pilot time; this is an unmeasured target. If batching
events is necessary, declare the new flush interval and its loss window before
production, never silently drop fields or change scientific sampling.

Failed/nonfinite values are recorded as missing with a reason plus a failure
event. Zero is a measured value, not the default for unavailable data. Rates
retain numerator and denominator; distributions retain independent-unit rows
or sufficient statistics justified for the prespecified analysis. Preserve
counts for every omitted, invalid and unrun cell. A single grand mean cannot
support the crossed seed/root analysis proposed for this paper.

**3. Storage and release boundaries**

| Material | Local storage | GitHub preservation |
| --- | --- | --- |
| Source, tests, protocol, state, decisions, citations, paper text | Repository | Commit/push after checks and review |
| Full measurement event journal | Ignored `chess_data/research_metrics.sqlite` and its SQLite sidecars | Never force-add the database; export reviewed small snapshots |
| Compact derived results sufficient for paper analysis | `research/results/` snapshots, with checksums and phase labels | Reviewed JSON/CSV, normally ≤2 MB per snapshot; partition/aggregate by a declared rule rather than dropping failed rows |
| Dataset shards, model/optimizer/EMA checkpoints, raw logs, full traces | Existing ignored artifact paths | Local-only under the user's choice; preserve recipes, seeds, manifests and hashes in Git |
| Locked evaluation output | Journal/private local artifacts until protocol release | Export withheld by default; explicit release record binds run manifests and a review receipt. Do not read or publish protected results to complete a backup task |
| Obsidian notes | Local vault mirror | Canonical Markdown copies also committed to Git; the vault on the same laptop is not independent protection |

Compact result exports may include anonymized root/episode/pair identifiers
and derived per-unit metrics needed for inference. They must not contain board
corpora, hidden raw labels, private data, credentials or bulky traces. Public
content review remains necessary; the exporter does not know the scientific
or privacy meaning of arbitrary fields. Private deliberation is not a metric.

The exporter includes an event-oriented CSV plus a canonical JSON snapshot;
the JSON is the authoritative representation. Metric-specific long tables and
paper figures are produced by the adopted analysis scripts. The library's
required-metric declarations check presence for configured event kinds; they
do not by themselves establish legality, semantic correctness, coverage of
every producer, or statistical validity.

**4. GitHub checkpoint policy**

Target a safe checkpoint **every 15 minutes of active work when meaningful
changes exist**, at each verified milestone, immediately before/after a costly
experiment batch, before shutdown/handoff, and before ending the session.
This is a recovery-point target conditional on connectivity and an active
executor. It is not a promise that sleeping/offline hardware pushes changes.
No empty commits or LLM wakeups solely to report unchanged state.

At a checkpoint:

1. Flush/verify measurements and prepare an immutable reviewed export. Keep
   full local artifacts excluded and protected results withheld.
2. Save the current state, unfinished work, exact next action, and evidence
   pointers. Refresh the README's marked status section in every new commit:
   date/timezone, stage/change, measured metrics with evidence, scoped checks,
   blockers and next action. If no experiment ran, state that and retain the
   last verified measurements with dates. Keep locked results withheld. Run
   the checks appropriate to changed code/data/analysis.
3. Inspect the explicit selected files. Commit source, notes and small results
   with an accurate milestone or incomplete-work description. If a source
   change is not validated, do not label it ready for experiments; preserve a
   clear work-in-progress handoff and choose the last validated run revision.
4. Check the destination and push normally to the configured branch. Verify
   remote identity against the committed snapshot. A local commit alone is
   not a completed checkpoint.
5. Record success or the unresolved failure. Network failure leaves a pending
   checkpoint; divergence requires normal reconciliation, never force-push.
   Do not start another costly batch when the required prior checkpoint has
   not reached GitHub. A running batch may finish its safe local checkpoint;
   preserve its status and exposure window.

Use `tools/research_checkpoint.py` for explicit existing files. It refuses
pre-staged work, ignored artifacts, wrong destinations, oversized files and
non-fast-forward pushes, and requires a refreshed README status section for
each new commit. The lead still verifies the metric evidence; a changed
section alone does not prove accuracy. Retrying a push with no new commit
does not require a README edit. Record the prior verified remote hash in the
README, then verify/report the new hash after pushing and carry it into the
next substantive update; do not create self-referential commit loops.
The tool does not schedule itself or claim scientific
validation. If a commit/check fails after staging, inspect and preserve the
index; the tool deliberately does not reset the user's work. Deletions or
other unusual changes need the ordinary reviewed Git workflow.

No OS service or agent automation was installed in this milestone. During
interactive work, the standing AGENTS instructions enforce the checkpoints.
When the actual experiment runner exists, its event loop must invoke the
export/checkpoint boundary at the declared cadence with one authorized
publisher, rather than creating a second competing Git writer. Verify that
integration before unattended experiments.

**5. Recovery procedure after losing the chat or machine**

1. Clone `https://github.com/dakiemdarktharr/caissa-jepa` on replacement
   hardware. Verify the expected branch/commit and read `research/STATE.md`,
   AGENTS, current protocol, and the latest validation/backup receipts.
2. Verify exported snapshot checksums and run/attempt identities. A restored
   journal is optional; immutable JSON/CSV snapshots preserve published
   evidence. Never fabricate a completed run from an absent terminal event.
3. Recreate the pinned environment and run core/ledger tests. Missing optional
   historical artifacts are explicitly missing, not silently regenerated
   under old identities.
4. Recover source/configuration, decisions, paper drafts and exported results
   from Git. Checkpoint weights, full raw data and unreleased/unexported metrics
   that existed only locally are lost. Hashes identify missing bytes; they do
   not reconstruct them.
5. If source recipes/data access still exist, regenerate in a new attempt and
   verify identities. Exact byte reproduction is conditional on determinism,
   original dependencies and source availability. Retrain when weights are
   gone; record new cost/results instead of claiming exact resume.
6. Resume an optimizer only with the complete compatible model, optimizer,
   EMA, RNG, sampler/order/cursor and protocol state. An available model weight
   file alone is insufficient. Otherwise restart a separately identified run.
7. Preserve failed/interrupted history and resume the declared plan without
   tuning against recovered final results. Perform a fresh restore check at
   each major milestone and before a long unattended run.

With GitHub-only storage, a complete manuscript can often be reconstructed
from pushed compact analysis rows and scripts even if expensive retraining is
needed for exact model reproduction. This is conditional on those rows
actually being exported and pushed. It is not full disaster protection.

**6. Implemented API and remaining integration**

The standard-library `research_ledger.py` uses transactional SQLite with FULL
synchronization, verifies manifest/event hashes, and rejects conflicting event
replay. The original raw database remains ignored. Export files are written
to a temporary directory, synchronized, and published as a checksummed
immutable snapshot. No external tracking service is required.

Typical producer integration:

```python
from research_ledger import Ledger, measured_objective

with Ledger("chess_data/research_metrics.sqlite") as ledger:
    ledger.create_run(frozen_manifest)
    metrics, gradients = measured_objective(
        ledger, run_id, "attempt1:objective:0", 0, model, batch
    )
    # The future trainer performs its separately validated optimizer update,
    # then records optimizer metrics and checkpoint/state identities here.
```

The snippet is an integration pattern, not a runnable scientific recipe:
manifest, model, batch and authorization must already exist. The adapter only
measures the current no-update objective, whose known covariance-gradient bug
remains unresolved. Recording a metric does not make the objective correct.

CLI boundaries:

```bash
.venv/bin/python -B tools/research_ledger.py create research/run-manifest.json
.venv/bin/python -B tools/research_ledger.py record RUN_ID research/event.json
.venv/bin/python -B tools/research_ledger.py verify
.venv/bin/python -B tools/research_ledger.py export research/results
.venv/bin/python -B tools/research_checkpoint.py --message "Record verified milestone" --push README.md research/STATE.md
```

The example manifest/event paths are supplied by the runner, not existing
scientific datasets. Select every intended export file explicitly when
checkpointing; the final command above publishes only README, state and any
already-committed ancestors, not an unlisted export directory.

Before production readiness, test all actual producer hooks, optimizer/EMA
resume equivalence, sampling cadence and overhead, scheduled export and push,
resource stop behavior, locked-result release, analysis-table regeneration,
and clean-machine restoration. This milestone implements and tests the
primitives, records workflow evidence, and publishes it; it does not claim a
complete trainer or an already-running autonomous workflow.
