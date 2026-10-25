# CAISSA-JEPA master handoff

Prepared **2026-10-25 (Asia/Ho_Chi_Minh)** for continuing in a fresh project or
chat. Repository: [dakiemdarktharr/caissa-jepa](https://github.com/dakiemdarktharr/caissa-jepa),
branch `main`. This is a source, evidence, and continuation handoff; it does not
approve a research run or change a frozen method.

## Start here

The active work is **V2.12-06 alternating-player multi-step JEPA**, currently
at the implementation/audit stage before training. The goal is a reproducible
planning advantage over matched non-JEPA controls under declared compute and
data budgets. **No JEPA superiority, confirmatory result, broad transfer,
algorithmic novelty, or publication readiness has been established.**

The latest research history in GitHub ends on 2026-10-07. This handoff reconciles
that history on 2026-10-25; it introduces no new experimental result. There is
a no-update six-arm objective/manual-gradient graph, a scratch optimizer,
receipt/schedule boundaries, partial compute inventories, and extensive
synthetic tests. There is **no exclusive integrated V2.12 production trainer**,
accepted production corpus, complete training-compute counter, or passed
six-arm parity gate. Graph freeze is **NO**; the ≤5% training-FLOP gate is
**untested and unpassed**. Training, matches, production root/corpus generation,
calibration simulation, live adapter integration, and OOM tests retain their
separate protocol/authorization gates.

Read in this order:

1. [AGENTS.md](AGENTS.md): collaboration and publication rules.
2. This handoff, then [resume prompt](docs/handoff/RESUME_PROMPT.md).
3. [Current method V2.12-06](METHOD_SPEC_V212.md) and
   [Adam/EMA amendment](docs/METHOD_SPEC_V212_V06_ADAM_EMA_AMENDMENT.md).
4. [Pre-fit decision register](docs/V212_PREFIT_ACTION_REGRET_DECISION_REGISTER_DRAFT_01.md),
   [FLOP protocol D03](docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md), and
   [counter coverage audit](docs/V212_FLOP_COUNTER_COVERAGE_AUDIT_DRAFT_01.md).
5. [Ground Truth](GROUND_TRUTH.md) and [roadmap](ROADMAP.md) for the full dated
   decision trail, using the relevant workstream sections rather than assuming
   every old “current” paragraph still applies.
6. [Verification receipt](docs/handoff/VERIFICATION_2026-10-25.md) and
   [repository inventory](docs/handoff/REPOSITORY_INVENTORY_2026-10-25.json).

## Provenance and reconciliation

The incoming local checkout was at `0cba5d6` with seven pending files. GitHub
was **415 commits ahead**, at
`a11668982eabebab7e6925e058eddb80a93df0d8`. The local files were older
continuations of work already developed further on GitHub.

- `e3d73bd`: preserves all seven incoming files in a checkpoint commit.
- `4d67caf50a183396dfb6f032c56ddad6595b6442`: merges the checkpoint and GitHub
  history. Its tracked tree exactly matches `a116689`; the newer GitHub
  versions resolve the six conflicts. The symmetry test was already identical.
- The subsequent handoff commit adds this package and navigation/status notes.
  Both histories remain reachable; no remote history is rewritten.

The preserved files were `ROADMAP.md`, the counterfactual-support protocol,
root-sampling draft 01, duplicate/overlap audit, request-adapter v01, and its
request/symmetry tests. Retrieve an original without changing the working tree
with `git show e3d73bd:path/to/file`. Do not restore these older files over the
current implementation as a way of resuming.

The JSON inventory binds the **627 tracked files at the merge commit** to
relative paths, sizes, and SHA-256 hashes. It also inventories the local
excluded pilot files by metadata/hash. Handoff documents added afterward are
versioned by their containing Git commit. This preserves project content and
documented decisions; private chat transcripts, external vault contents, and
files absent from this machine are not represented as exported material.

## Research trajectory and established results

All performance results below are historical development evidence, not newly
recomputed in this handoff. Raw experiments remain excluded from Git.

| Stage | What happened | Continue from |
| --- | --- | --- |
| Legacy chess / V7 | PySide6 chess application, dataset tools, training/arena infrastructure. Separate from the active two-game study. Legacy confirmation remains blocked by independent full-history rule validation. | [V7 protocol](V7_RESEARCH_PROTOCOL.md), [research decisions](docs/RESEARCH_DECISIONS.md) |
| Initial two-player pilot | 21 runs; diagnostic search ceiling and no demonstrated JEPA advantage. | [Pilot report](docs/TWO_PLAYER_PILOT_20260929.md) |
| V2, V2.1, V2.2 | Recurrent reply-fork study, symmetry/weight grid, then restricted-label study. No promotion of a JEPA advantage. | [V2 results](docs/V2_GRID01_RESULTS.md), [V2.1 results](docs/V21_GRID02_RESULTS.md), [V2.2 results](docs/V22_GRID03_RESULTS.md) |
| V2.3–V2.4 | Training-fit and order diagnostics; not strength studies. A material order obstruction was not established. | [V2.3](docs/V23_FIT_DIAGNOSTIC.md), [V2.4](docs/V24_ORDER_RESULTS.md) |
| V2.5 | Small exact-state descriptive gain did not establish a JEPA-tail mechanism; hybrid latent planning failed its primary comparator gate. Preserve grid04 failure and grid05 outcome. | [Verified grid05](docs/V25_GRID05_RESULTS.md), [failure audit](docs/V25_GRID04_FAILURE_AUDIT.md) |
| V2.6–V2.7 | Larger-board/transfer proposals and oracle-cost feasibility; exact-label cost and prior art forced redesign. | [V2.6 method](docs/METHOD_V26.md), [V2.7 positioning](docs/V27_RESEARCH_POSITIONING.md) |
| V2.8 | 60 fits and 160 paired development blocks. JEPA minus task-value macro score −0.01875; no observed advantage. | [Analysis receipt](docs/validation/V28_DEVELOPMENT_MATCH_ANALYSIS_V01.json) |
| V2.9 | Three-epoch duration probe: 60 fits, 160 paired blocks/320 games. JEPA minus task-value: Connect4 −0.1375, Reversi6 +0.0125, macro −0.0625. Nomination failed; stop duration-only tuning. | [Analysis receipt](docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json) |
| V2.10 | Train-only gradient decomposition, no optimizer update. All 400 cells were present; the frozen conflict gate failed in both games. Do not pursue a projected-gradient variant from this diagnosis. | [Independent review](docs/V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md), [receipt](docs/validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json) |
| V2.11 | λ=8 calibration: 20 fits, 240 paired blocks/480 games. Macro contrasts −0.04375 vs λ=1 JEPA, −0.0500 vs task-value, −0.0375 vs direct leaf. All nomination gates failed; stop λ-only tuning. | [Result and audit](docs/V211_DEVELOPMENT_RESULT_REVIEW_01.md) |
| V2.12 | Multi-step candidate; no fitted-model strength result. V02 random-weight compute pilot completed 1,152/1,152 depth-four cells: p90 0.7970 s, max 3.7419 s, 12 cells above 2 s. | [V02 report](docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md), [current method](METHOD_SPEC_V212.md) |

Keep the negative rule-only Reversi8 2-second p90 finding. V02 is synthetic,
single-host random-weight instrumentation, not fitted-model runtime evidence.
The proposed 10,000-node/5-second planner cap and 6-second response deadline
are not established operational guarantees. V03 repairs sampled RSS stop and
receipt handling as a versioned candidate; its full pilot has not been cleared
or run. Do not rerun or rewrite hash-bound V01/V02 receipts in place.

Prior-art positioning is in [RELATED_WORK](docs/RELATED_WORK.md) and the
[V2.12 crosswalk](docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md). These record targeted
searches, not an exhaustive review or a new October 25 literature search.
Recursive JEPA, learned-model planning, adversarial board-game models, and
transfer are existing work. Any contribution must survive the declared matched
controls; naming a combination is not a novelty result.

## Current method and terminology

Training sizes are Connect Four 6×7/k4 and Reversi6. Held-out sizes are Connect
Four 8×8/k4 and Reversi8. This is within-family board-size transfer, not proof
of cross-family generalization. Features have 198 coordinates, latents have
32, actions use a shared 65-entry vocabulary, and Reversi pass is action 64.

The six arms are multi-step JEPA, single-pair JEPA, recursive raw-state
dynamics, value-only latent rollout, direct-leaf value, and single-horizon
JEPA. The candidate predicts recursively at 1/2/4 plies, with exact rules
providing legal branches and terminal utility. Values are trained on the
declared policy-mixture terminal outcomes; max/min backup over those leaves
does not make them exact minimax values or an opponent-specific model.

The adopted raw-state contract is `F → D → E`: predict decoded features,
re-encode them for recurrence, and preserve the specified backward/mask paths.
V06 fixes Adam/clipping/EMA semantics. The method calls for 928 selected windows
per training game, balanced 64-window batches, 29 batches/epoch, 87 updates
over three epochs, and 20 paired seeds. These counts are specifications, not
evidence that an accepted corpus or replay-derived schedule exists.

The primary development endpoint is paired game score against all five
controls on both held-out sizes and the equal-weight macro. The method's
nomination rule includes ≥+0.05 contrasts, positive familywise intervals,
Holm-adjusted tests, completeness, no forfeits, and passing compute gates.
Regret is secondary. Exact fixed-horizon regret, interval regret, and solved
full-game regret are distinct quantities. A nomination would only justify a
new confirmatory study.

**Version-name trap:** `METHOD_SPEC_V212.md` is adopted **v06**; archived v04
and v05 specs are immutable history. The separate
`METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md` is an **unadopted root proposal**,
not the adopted raw-state v05. Several historical documents still say
“current v04.” Read their disposition against v06 and the decision register;
do not infer adoption from a filename, date, or a passing helper test.

## Implementation map and remaining boundaries

| Workstream | Source entry points | Current boundary / next evidence |
| --- | --- | --- |
| Rules and exact reference | `two_player/games.py`, `benchmarks/reference_rules.py`, `benchmarks/alpha_beta_reference.py` | Exact legal rules underpin all work; bounded reference values are not full-game solutions. |
| Objective and optimizer | `two_player/v212_model.py`, `two_player/v212_scratch_optimizer.py` | Synthetic-tested no-update loss/manual gradients and pure scratch step. No integrated trainer or persistent training run. |
| Windows and provenance | `two_player/v212_trajectory_audit.py`, `v212_episode_replay_receipt.py`, `v212_window_batch.py` | Exact-rule in-memory checks and receipts do not authenticate external source files or establish production corpus completeness. |
| Schedule binding | `two_player/v212_schedule_manifest.py`, `v212_scheduled_batch.py`, `v212_receipt_bound_schedule.py` | Immutable schedule/mask boundaries and one-batch integration fixtures exist. The real replay-derived 20×87 schedule and exclusive call path are absent. |
| Compute accounting | `tools/v212_partial_flop_ledger.py`, `v212_source_operation_inventory.py`, `v212_source_counter_reconciliation.py`, `v212_conversion_site_inventory.py`, related accounting helpers | Partial source ownership only. Full counter, linked eigensolver coverage, runtime identity, and actual all-arm parity remain unresolved. |
| Runtime observation | `tools/v212_runtime_observation.py`, `two_player/v212_runtime_observation_v01.py` | Package/mapped-file observations are not atomic attestation of executed interpreter/native bytes. |
| Compute pilots | `two_player/v212_pilot.py`, `v212_pilot_v02.py`, `v212_pilot_v03.py`; corresponding tools | V01/V02 historical reports; V03 candidate not cleared for a live full run. RSS remains sampled/cooperative. |
| Request/worker supervision | `two_player/v212_request_adapter_v01.py`, `v212_request_adapter_v02.py`, `v212_armed_service_smoke_v01.py`, `v212_armed_worker_bootstrap_v02.py`, `v212_worker_ipc.py` | Same-cgroup adapters are not integrated with the external armed supervisor. Offline v02 bootstrap binding is not full controller/runtime proof. |
| Supervision receipts | `two_player/v212_live_supervision_v01.py`, `v212_supervision_collector_v01.py`, `v212_supervision_receipt_v02.py`, `v212_supervision_receipt_v03.py` | One historical synthetic normal-exit service run and many mocks; failure composition, recovery, OOM attribution, and full v02 integration remain open. |
| Root/calibration proposals | `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md`, root draft/calibration D03, `tools/v212_*calibration*.py` | Static analytic audits do not run a calibration simulation or approve the root population. |
| Regret/diagnostics | `two_player/v212_bounded_reference_v01.py`, `v212_minimax*`; action-sensitivity/regret drafts | Estimands and helper bounds exist; reference identity, charged work, failure rules, feasibility and adoption remain open. |
| Historical pipelines | `two_player_v2/`, `two_player_v21/`, `two_player_v22/`, `two_player_v23_diagnostic/`, `two_player_v24_probe/`, `two_player_v25/`, `two_player_v25r/`; `two_player/v28_*`, `v29_*`, `v210_*`, `v211_*` | Preserve historical models, source hashes, results, and failed gates. Do not substitute these for a V2.12 trainer. |
| Legacy desktop application | `app_entry.py`, `main.py`, `research_ui.py`, `train_caissa_v7.py`, `arena_research.py`, `fen_dataset_tool.py`, `model_registry.py`, `runtime_safety.py` | Separate Qt/chess workflow with its own dependencies and validation history. |

## Prioritized continuation

1. **Re-establish the exact snapshot.** Verify branch/remote, local changes,
   Python/NumPy, and the handoff receipt. Run synthetic checks. Inventory
   available artifacts before invoking any historical result verifier.
2. **Produce a bounded six-arm/trainer integration review.** Keep the v06
   objective and scratch semantics intact. Close the bypass between receipt-
   bound batches and direct model calls; specify source authentication,
   selected windows, exact replay, immutable 20×87 masks, 32-per-game batches,
   and a valid nonterminal H4 leaf in every direct-leaf batch. Implement only
   the separately authorized scope; synthetic tests do not authorize a corpus.
3. **Close compute coverage before profiling.** Resolve outstanding source
   owners and the actual `eigvalsh`/LAPACK/BLAS dispatch or accepted full-schedule
   bounds. Include forward/backward, diagnostics, clipping, Adam and EMA;
   report comparisons/conversions/indexing separately. Bind the runtime and
   traces. D03 preregistration acceptance is not profile execution permission.
   Measure `(max F - min F) / min F ≤ 0.05` over all 20×87 updates only after
   its prerequisites pass. Raw-state dense-forward MAC inflation is a risk,
   not a total-FLOP verdict. A failure requires a versioned redesign/review.
4. **Resolve the data/root/inference protocol.** Separate source-row uniqueness,
   content duplicates, prohibited split overlaps, and repeated root-slot draws.
   Design02 proposes 48 accepted slots per held-out variant, 16 per occupancy
   band from 64 candidates; repeated boards remain distinct draws. Population,
   equal-band weights, six-stratum under-yield disposition, the ≥40 minimum,
   schedule-pass target and finite-sample bootstrap validity remain unaccepted.
   Calibration D03 is an abstract proposal, not validation or run authority.
5. **Finish external supervision as a separate workstream.** Follow the
   [failure test plan](docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md),
   including a caller deadline for raw-stdin EOF, manager/journal/counter
   failures, exact request/response/runtime binding, receipt certainty, and
   retained reconciliation handles. Preserve v01/v02 distinctions. Do not
   infer OOM survival from `memory.oom.group=0` or run live faults to fill a
   handoff gap.
6. **Obtain the applicable independent dispositions and a separate pre-fit
   grant.** Freeze hashes and all controls before any production experiment.
   No post-outcome changes to roots, horizons, controls, caps, exclusions or
   nomination rules. Preserve failed gates and stop criteria.

The [pre-fit register](docs/V212_PREFIT_ACTION_REGRET_DECISION_REGISTER_DRAFT_01.md)
is the decision checklist. The [generation compatibility audit](docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md)
and [generation receipt crosswalk](docs/V212_GENERATION_RECEIPT_AUDITOR_CROSSWALK_DRAFT_01.md)
explain why fixture helpers cannot be treated as a production generator.
Counterfactual support, latent sensitivity, and regret have separate
denominators and evidence requirements; do not merge them into one score.

## Recreate the workspace

Use a full clone to retain the checkpoint and historical source references:

```bash
git clone https://github.com/dakiemdarktharr/caissa-jepa.git
cd caissa-jepa
git switch main
git status --short
git log -5 --oneline
```

The current Linux checkout has **CPython 3.11.9 / NumPy 2.4.6** in `.venv`.
It has no PySide6. Recreate environments; do not copy `.venv` across machines.
For the NumPy-only research checks, with `uv` installed:

```bash
uv python install 3.11.9
uv venv --python 3.11.9 .venv
uv pip install --python .venv/bin/python 'numpy==2.4.6'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m unittest discover -s tests -p 'test_v212*.py' -v
```

This is a convenience setup, not a frozen training-runtime attestation.
`requirements-research-lock.txt` pins NumPy 2.4.6 and PySide6 6.11.1 for the
historical Windows research/GUI environment. To include the GUI, install that
file instead of only NumPy. `requirements-lock.txt` is the older Windows V7
runtime (NumPy 2.0.2/PySide6 6.10.3); `requirements.txt` is unpinned minimum
compatibility; `requirements-build.txt` is for packaging. Do not combine the
two locks or silently replace the research lock with the legacy one.

On Windows, use `.venv\Scripts\python.exe` and set
`$env:OPENBLAS_NUM_THREADS='1'` and `$env:OMP_NUM_THREADS='1'` in PowerShell.
The Windows panel supervisors are not Linux entry points. Linux cgroup/systemd
helpers require their separate reviewed host contract. A clone can run source
and synthetic tests; it cannot recreate missing empirical results by itself.

For the legacy GUI, after installing Qt dependencies, the entry point is
`python app_entry.py`; Windows launcher/build scripts remain at the root.
GUI/build tests were not run in this handoff. Do not interpret old README
training commands as authorization to launch an active V2.12 study.

## What transfers through GitHub, and what does not

Git transfers tracked source, tests, specifications, research decisions,
curated JSON/Markdown validation receipts, figures, Qt assets, and full commit
history. The existing `.gitignore` is unchanged.

| Excluded material | This host at handoff | Recovery rule |
| --- | --- | --- |
| `chess_data/` | 12 V2.12 V01/V02 compute-pilot JSON/summary files, 1,702,737 bytes total | Per-file paths, sizes and hashes are in the inventory. Copy separately only with a storage/transfer plan; do not force-add. |
| V2.8/DEV09 data, V2.9 panel/checkpoints, V2.11 panel/matches | Not present in this checkout | Recover from the original experiment machine or backup, matching original receipt hashes. Do not regenerate in place to satisfy a verifier. |
| Legacy chess data/FEN databases/checkpoints and archive | Not present here | Historical locations are documented in the migration notes below; their availability was not verified on October 25. |
| `.venv/`, Python caches | Local environment/cache only | Rebuild; package/runtime identity must be rechecked. |
| `downloads/`, `fen_dataset/`, `build/`, `dist/`, `installer-output/` | Not part of this publication; main listed directories absent locally | Source/build recipes remain in Git. Recover required artifacts separately. |
| Logs, `.jsonl`, `.npz`, `.sqlite`, `.db`, `prepared-v*/`, `*.generations/`, crawl caches | Existing exclusions retained | Store and restore separately after an agreed plan; no large generated artifacts uploaded. |
| Obsidian and chat history | No vault or transcript export performed | Existing Markdown in the repo is the durable project record. External vault sync is deferred. |

Historical migration references: [Windows workspace migration](docs/WORKSPACE_MIGRATION.md),
[D-drive data migration](docs/D_DRIVE_DATASET_MIGRATION.md),
[data sources/license register](docs/DATA_SOURCES.md). Old paths such as
`C:/Users/ANHKHOI/Documents/ChatGPT/caissa-jepa`, `D:/CAISSA-JEPA`,
`D:/notes/vault_1/Caissa-JEPA`, and `chess_data/legacy_chess_robot_app_20260912/`
describe earlier machines/archives, not files verified present here.

Do not delete this checkout or original experiment storage on the assumption
that GitHub contains the excluded files. For a later artifact migration:
inventory the original paths, agree on storage, copy with source/target hashes,
verify provenance without opening protected outcomes, then update the handoff.

## Collaboration rules to carry into the new project

- Commit completed project changes after appropriate verification. For a
  requested GitHub publication, verify the configured destination, use a
  normal push, and verify the resulting remote hash. Never force-push without
  explicit authorization.
- Preserve generated-artifact exclusions and ask for a storage plan before a
  separate large-artifact upload. Keep application UI text in English.
- Do not create agents/subagents unless the user approves the exact model and
  reasoning effort. Old reviewer mentions are history, not approval to spawn
  one now. This handoff used no subagents.
- Keep commands noninteractive/background where practical, preserve frozen
  protocols and receipts, and keep research claims bounded to their evidence.
- Continue with source review, synthetic verification, and concrete reviewable
  work within existing scope. Do not treat this migration/publication request
  as a new experiment grant or reopen locked-final data.

The next chat can start by pasting the [resume prompt](docs/handoff/RESUME_PROMPT.md).
Use the [verification receipt](docs/handoff/VERIFICATION_2026-10-25.md) for the
actual tests and limitations of this publication, rather than historical test
counts embedded elsewhere.
