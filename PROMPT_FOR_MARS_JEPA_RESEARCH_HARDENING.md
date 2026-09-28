# Implementation prompt: MARS-JEPA research hardening

You are the senior implementation engineer and research-methodology engineer
for the repository at:

`C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa`

Your job is to make a careful, reviewable code change, not to manufacture
experimental evidence. Inspect the repository and current working tree first.
Preserve unrelated user changes. Do not use `git reset --hard`, destructive
checkout commands, force-push, or broad global replacements.

The project is being narrowed and renamed at the research level to:

## MARS-JEPA Chess

**MARS-JEPA: Multi-Horizon Action-Conditioned Response-Aware State Prediction
for Resource-Bounded Zero-Sum Chess**

The acronym means:

- M: Multi-horizon prediction, currently H1/H2/H4.
- A: Action-conditioned latent prediction.
- R: Response-aware modelling of the opponent's reply.
- S: Future-state prediction.

Chess is the current deterministic two-player zero-sum testbed. Do not claim a
generic architecture for every two-player game until another game has been
implemented and evaluated. Keep `CAISSA-JEPA` only as a legacy package,
executable, installer, and storage identifier where changing it would break
compatibility.

The production dataset was intentionally deleted before this task because its
manifest, parser coverage, duplicate handling, and split validity were not
trusted. Do not download, crawl, regenerate, or train on a production dataset
in this task. Temporary fixtures are allowed and required for tests.

## Required workflow

1. Read the current source, tests, README, research protocol, release notes,
   dataset-audit report, and `docs/RESEARCH_IDENTITY.md`.
2. Inspect `git status --short --branch`, current branch, remotes, and recent
   commits before editing.
3. Create or use the branch
   `codex/mars-jepa-research-hardening` without rewriting existing history.
4. Implement the sections below in small, testable changes.
5. Run the full test suite and focused tests after each major group.
6. Inspect the final diff for stale claims, secrets, generated artifacts, and
   accidental dataset files.
7. Commit and push only after all feasible acceptance criteria pass.

## 1. Establish the new research identity

Update research-facing documentation and metadata to MARS-JEPA Chess:

- README title and research description.
- `docs/RESEARCH_IDENTITY.md` and related protocol documents.
- experiment manifests, model labels, result tables, and paper-facing strings.
- GUI research labels where applicable, keeping all application UI text in
  English.

Do not blindly rename Python modules, package imports, executable paths, or
storage directories. Preserve backward compatibility for `CAISSA-JEPA` and
document the compatibility boundary. Remove or replace any stale
`Response-JEPA` research name introduced by an earlier partial rename.

The documentation must state that the intended contribution is a falsifiable
response-aware, multi-horizon planning hypothesis. It must not claim Q1
readiness, generic two-player transfer, or superiority over Stockfish.

## 2. Make missing-data behavior safe

The following locations may be absent after the intentional cleanup:

- `D:\CAISSA-JEPA\fen_dataset`
- `D:\CAISSA-JEPA\datasets\...`
- source or per-user dataset junctions

Implement safe behavior when no dataset is available:

- Training controls show a clear English message telling the user to select or
  download a verified dataset.
- No stale junction, old manifest, cache, or checkpoint is silently selected.
- A missing or changed dataset fingerprint invalidates training and
  confirmatory evaluation.
- Existing checkpoints are not deleted, but are marked incompatible/unverified
  until their dataset fingerprint matches.
- Temporary test fixtures remain inside test-created temporary directories.

Add tests for missing path, broken junction, stale `dataset_location.json`,
missing manifest, and checkpoint/dataset fingerprint mismatch.

## 3. Rebuild the dataset integrity gate

Inspect and improve `dataset_integrity.py`, `fen_dataset_tool.py`,
`tools/audit_pipeline_dataset.py`, `training_runtime.py`, and related tests.

Implement a versioned audit pipeline that:

- Recomputes shard SHA-256, byte size, row count, position count, and
  unfinished-row count from actual files.
- Rejects manifests whose aggregate values differ from the scan.
- Uses canonical game identity based on normalized move sequence plus stable
  provenance, not raw PGN headers alone.
- Detects duplicate games and duplicate positions before splitting.
- Produces a quarantine/provenance report for every excluded item.
- Creates deterministic train, validation, and locked final-test manifests.
- Groups by canonical game/event identity and verifies no cross-split position
  overlap.
- Stores schema version, source hashes, split policy, code version, license
  metadata, and complete dataset fingerprint atomically.
- Fails closed before cache preparation or training if any integrity check
  fails.

Add parser fixtures and explicit skip-reason counters for:

- `O-O` and `O-O-O`;
- promotions;
- en-passant;
- castling rights;
- checkmate/stalemate;
- malformed and unsupported moves.

Do not silently discard parser failures. The audit must make it possible to
quantify the fraction and type of skipped games.

Transition validation must compare complete supported FEN semantics: board,
side to move, castling rights, en-passant target, halfmove clock, and fullmove
number. If repetition history cannot be reconstructed from the dataset,
document that limitation, add an explicit feature/evaluation policy, and do
not present the model as fully history-aware.

## 4. Repair training reliability

Inspect `train_caissa_v7.py`, `training_runtime.py`, `runtime_safety.py`, GUI
workers, and checkpoint tests.

The installed app previously produced five `FAILED` reports with zero steps
and an opaque `FileExistsError`. Fix the behavior as follows:

- Fresh training and resume must be explicit modes.
- Existing checkpoint collisions must explain the resolved model, generation,
  lock, cache, and dataset paths.
- Every failure report must include phase, PID, run ID, dataset fingerprint,
  model configuration, and full traceback.
- A zero-step run must be reported as failed, interrupted, or skipped—not
  trained.
- Test a fresh run, collision, explicit resume, interruption, rollback, and
  recovery for every registered model using only temporary fixtures.
- Preserve atomic generation commits and verify recovery after simulated
  partial writes.
- Make per-model time budgets fair. A shared global deadline must not allow an
  early cache job or queue item to consume another model's reserved budget.
- Ready-cache checks must validate checksum, metadata, version, source
  fingerprint, and complete record count—not only file existence and length.
- Directory-size and ETA reporting must recursively sum files and label small
  pilot estimates as pilot estimates.

## 5. Make the MARS-JEPA ablation matrix real

The current documentation and implementation disagree about available model
variants. Implement and test these research-facing entries:

1. `h1`: one-step action-conditioned response-aware JEPA.
2. `h1-h2`: H1 and H2 response-aware prediction.
3. `full`: H1, H2, and H4 prediction.
4. `no-response`: matched JEPA with opponent-response conditioning removed.
5. `lejepa-inspired`: clearly labelled unless the objective is made faithful.
6. `direct-policy-value`: non-JEPA control.
7. `nnue-style`: local control, not Stockfish NNUE.

For each entry, expose a stable registry ID, CLI/GUI selection, configuration
schema, parameter count, feature declaration, checkpoint fingerprint, and
serialization round trip. Keep compatibility aliases for existing checkpoint
names. If an entry cannot be implemented correctly, remove it from every
documentation and UI surface instead of leaving a fictional ablation.

## 6. Resolve the central MARS scientific mismatch

The current inference code evaluates a minimum over many legal opponent replies,
while training usually observes only one historical reply. This mismatch must
be resolved before the method is called adversarial or worst-case.

Choose one solution and document why it is valid:

- Train on enumerated or sampled legal counterfactual response branches with
  correctly constructed targets; or
- Learn a calibrated response distribution/quantile and use expected or
  quantile aggregation at inference; or
- Restrict inference to the response distribution actually learned and rename
  the claim so it is not worst-case adversarial.

Do not fabricate multi-horizon outcome labels for counterfactual branches.
Missing targets must be represented explicitly and excluded from the relevant
loss. Add tests proving that response aggregation, target construction, and
side-to-move signs are correct.

Add hard legal negatives or all-legal-move evaluation. Random negative action
sampling must not be the only policy test. Report top-1, top-5, MRR/NLL,
value MSE, WDL/Brier score, calibration, and separate tactical/endgame
strata.

## 7. Validate representation and manual gradients

- Add finite-difference checks for all manual NumPy gradient paths.
- Add latent variance, covariance, effective-rank, latent-norm, target-error,
  and seed-stability diagnostics.
- Ensure side-to-move normalization and any board symmetries have correct
  action transforms.
- Either implement LeJEPA faithfully with an equation-to-code mapping and
  tests, or retain `LeJEPA-inspired` everywhere and remove theoretical claims.
- Separate representation quality, supervised policy/value quality, and
  end-to-end playing strength in the evaluation API and documentation.

## 8. Turn model-v-model into a confirmatory protocol

Inspect `arena_protocol.py`, `arena_research.py`, `arena_store.py`, and the
model-match workers.

Implement a versioned protocol with:

- independently pinned UCI referee binary, version, SHA-256, options, and
  time budget;
- fail-closed behavior and `ranking_ready=false` when no independent referee
  is available;
- at least 50 diverse opening positions for smoke tests and at least 100 for a
  final confirmatory run;
- color-swapped paired games;
- at least three model seeds;
- fixed search/time/node budgets and deterministic protocol metadata;
- exactly one predeclared primary metric;
- paired confidence intervals and correction for secondary/multiple
  comparisons;
- explicit treatment of timeouts, illegal moves, cancellations, and max-ply
  truncation as censored/error outcomes, never silent draws.

Separate these experiment families:

- representation/latent prediction ablations;
- policy/value prediction ablations;
- same-search architecture comparisons;
- complete end-to-end engine strength comparisons.

Do not call the arena winner statistically validated until every confirmatory
condition is satisfied.

Repair `ArenaHistory` so partial iterator consumption cannot leave SQLite
connections open on Windows. Add regression tests for early termination,
cleanup, idempotent import, and concurrent read/write.

## 9. Reproducibility and paper guardrails

Add a reproducibility manifest containing:

- Git commit and protocol version;
- Python, NumPy, OS, CPU/GPU, and thread settings;
- random seeds;
- dataset and split fingerprints;
- model architecture/configuration and parameter count;
- search configuration;
- referee binary hash and options;
- metric definitions and stopping rules.

Update research docs with explicit kill criteria. If `full` does not beat
`h1`, `h1-h2`, and `no-response` under matched data, parameters, search, and
compute with uncertainty intervals, narrow or pivot the contribution. Do not
hide a negative result.

## 10. Verification requirements

Run at minimum:

`python -B -m unittest discover -v`

`git diff --check`

Also run focused tests for dataset integrity, missing data, parser edge cases,
all model variants, gradient checks, fresh/resume training, checkpoint
recovery, cache invalidation, arena statistics, referee gating, SQLite cleanup,
and release self-test using temporary fixtures.

Do not run production training or download the deleted dataset. Do not add
`.jsonl`, `.npz`, `.sqlite`, `.db`, cache, checkpoint, build, or log artifacts
to Git. Respect the existing `.gitignore`.

## 11. Commit and GitHub handoff

Before committing:

- inspect the complete diff;
- preserve unrelated working-tree changes;
- verify no secrets or user data are included;
- verify the new project name and all claims are consistent;
- report any unresolved blocker honestly.

Commit the implementation on:

`codex/mars-jepa-research-hardening`

Use this commit message:

`research: harden MARS-JEPA validation pipeline`

Inspect `git remote -v` and push the branch to the configured GitHub remote.
Never force-push. Report the exact branch, commit hash, push result, tests
passed/failed, and remaining scientific blockers. If authentication or network
access prevents pushing, report the exact error and do not claim success.

The final report must explicitly say that no production training or valid
model-v-model result was created in this task because the dataset was
intentionally removed.
