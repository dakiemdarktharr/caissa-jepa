# Pipeline audit — 2026-09-13

## Scope and verdict

This is a diagnostic audit and migration, not an implementation of the proposed
research/training fixes. Production datasets and checkpoint contents were not
rewritten and no production training or tournament was started.

The existing 41 unit tests plus core assertions pass using the recreated D:
environment. Two new read-only audit tests pass. Installed EXE self-test passes
five-model train/resume, Qt/assets, image ZIP validation and arena JSONL/PGN
persistence on temporary fixtures. These passes do NOT clear the production
training failures or establish full-dataset/paper readiness.

## Dataset evidence

The audit reads all 17 manifest-listed JSONL shards. Their hashes and byte sizes
match their manifest entries, but aggregate metadata is stale:

| Measure | Manifest | Actual scan |
|---|---:|---:|
| Game rows | 95,577 | 90,003 |
| Positions | 8,819,061 | 8,284,410 |
| JSONL bytes | 4,294,932,427 | 4,035,308,412 |

There are 90,001 distinct game hashes: two repeated rows (0.002222%), with
identical content after source provenance is excluded. Repeats are at
`fen_games_00002.jsonl:1` (first at shard 1, line 247) and
`fen_games_00004.jsonl:5461` (first at shard 3, line 2139).
No on-disk JSONL shard is unlisted. No row has a non-list `positions` field.
The current hash split assigns 80,879 game rows to train and 9,124 to validation;
this does not prove independence at the chess-position level.
Results are 37,476 white wins, 30,731 black wins, 21,787 draws and 9 unfinished
games. The cache worker already skips unfinished results; that is a working
guard, not evidence that all labels or FEN transitions are valid.

## Findings, primary correction and fallback

Proposals below are NOT applied to application code. Severity/confidence are
about the observed defect or risk, not a promise that an untested fix works.

| ID / severity | Evidence and impact | Primary correction | Fallback |
|---|---|---|---|
| P01 High, confirmed failure; cause unresolved | All five installed-app training reports show `FAILED`, `FileExistsError(17, ...)`, phase `starting`, zero steps. Reports omit failing path/traceback. Temporary EXE tests pass, so the same production failure has not been reproduced. | Persist full traceback and resolved dataset/cache/checkpoint paths; reproduce with a temporary checkpoint and a copy of the failing layout, then fix the specific conflicting filesystem operation and add a frozen regression. Do not attribute it to a junction without proof. | Run the source GUI in the verified D: environment after dataset validation; retain failed generations. This is an alternate diagnostic route, not a verified fix for the production error. |
| P02 High, confirmed | Aggregate manifest counters exceed all actual shard records. `ShardedDatasetWriter._needs_reconciliation()` returns false on this dataset: it compares filenames/open-part bytes, not aggregate counters. This can misstate target completion and sample totals. | Reconcile immutable per-shard counts/hashes into an atomically published manifest; add a pre-training validation gate and regression for stale counters with unchanged filenames. | Preserve the original and create a separate audited dataset version from existing valid rows; mark it COMPLETE at its real size instead of claiming the 4-GiB target. |
| P03 Medium, confirmed | Two repeated game hashes; strict `verify` exits on the first duplicate. Identical-hash rows stay in one split but are overweighted. | Deduplicate into new shards with an exclusion/provenance ledger; rebuild the ingestion index, manifest and caches together; verify idempotent restart. | Quarantine duplicate rows in a derived training view and report exclusions; never silently alter archived raw PGN. |
| P04 High scientific risk, structural | `game_hash` hashes raw PGN text and `stable_split` has only train/validation. Equivalent games with different headers can get different identities; no independent final test is defined here. Actual cross-split position leakage has not been measured. | Canonical game identity, position/trajectory overlap audit, grouped temporal/event splits, and a locked final test protocol before model selection. | Describe current results as exploratory and use a separately curated, untouched confirmation set. |
| P05 High completeness risk, structural | GUI workers share one semaphore and the same eight-hour cutoff. Later models can exhaust the budget while queued; an eight-hour stop does not guarantee five epochs for every model. | Measure representative phase costs, schedule models fairly in epoch slices, and perform an admission check against total cache + five-model training + persistence cost. Optimize only after profiling. | Use one explicitly labeled equal-budget subset for all models, or request a longer full-data budget. Never report partial epochs as completed. |
| P06 Medium integrity risk, structural | Ready-cache checks verify existence/output length but do not fully validate metadata or same-length cache corruption before reuse. Frame parsing catches some corruption later. | Versioned checksummed metadata/frames with validation on opening and atomic shard publication. | Quarantine/rebuild only the failed cache shard; preserve training generations and mark the run interrupted rather than swallowing corruption. |
| P07 Medium reporting risk, confirmed code | `benchmark_training_runtime.py` reports `cache.path.stat().st_size` although the cache is a directory. That is not total cache storage. A 16-game warm-cache benchmark is also not an end-to-end ETA. | Sum cache file sizes and benchmark representative strata, cold preparation, validation, checkpoint I/O and all five models. | Suppress the misleading storage field and retain only explicitly scoped microbenchmark timings. |
| P08 Medium, observed configuration | No reference-engine config was found in installed app data. The code falls back to `Classical referee (uncalibrated)`; its bar must not be interpreted as a calibrated win probability. | Pin and validate an independent UCI engine/hash/budget and record per-position WDL/score provenance. | Keep the clearly labeled classical pawn-score display or show unavailable; do not use it for strong accuracy claims. |
| P09 High scientific limitation, confirmed code | Arena is continuous/exploratory. `ranking_ready` is always false; paired descriptive intervals are explicitly not sequential evidence. Selecting the current leader is not a validated winner. | Predefine primary metric, independent confirmation matches, seeds/openings, stopping rule, multiplicity policy and handling of failures/censored games. Separate model representation and search-budget comparisons. | Report W/D/L, complete color pairs, censoring bounds and descriptive intervals without a superiority claim. |
| P10 Medium metric risk, confirmed code | Action-ranking catches sample errors and reports skipped samples; a limited run takes the first eligible positions. A small successful sample can be unrepresentative. | Seeded stratified evaluation, minimum coverage, explicit invalid-label thresholds and immutable test identity. | Publish evaluated/skipped counts and label prefix-only results as smoke measurements; fail the paper pipeline below minimum coverage. |

## Checks that passed and limits

Verified: legal moves/hash/parser/SQLite tests, resumable HTTP Range fixture,
atomic manifest polling, shared-cache cancel/release, checksum rejection,
checkpoint generation rollback including optimizer/EMA, five-model save/load,
frozen openings, read-only paired arena, exact SAN/PGN logging, stopped-game
replay, deduplicated result history, referee POV, UCI timeout/cancel fixture,
monitor switching and individual model plots, ZIP path/image validation.

Not verified: all production FEN transitions, semantic labels, temporal or
position-level leakage, full 4-GB preparation plus 25 full epochs, long-running
memory/disk/ETA behavior, real Stockfish integration, real model strength,
manual mouse coverage, or live-site download blocking. No win-rate ranking is
inferable from fixture tests or the zero-step production checkpoints.

Reproduction/evidence (relative to the D: source checkout):

- `tools/audit_pipeline_dataset.py` — inspectable, read-only full shard audit.
- `test_pipeline_audit.py` — read-only guarantee and stale-counter reproduction.
- `build/pipeline-dataset-audit-20260913.json` — full profile and duplicate locations.
- `build/pipeline-tests-20260913.log`, `build/pipeline-safety-20260913.log`.
- `build/pipeline-installed-smoke-20260913.json` — installed EXE fixture receipt.
- Installed training reports preserved under `../app-data/chess_data/`.

The data-quality skill guided full-record counts, duplicate classification,
separation of observed defects from unmeasured risks, and preservation of source
data. Migration does not silently repair the experimental dataset.
