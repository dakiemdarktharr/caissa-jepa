# Prompt for the implementation conversation

You are the implementation engineer for the repository at
`C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa`.

The project has been reviewed as a potential Q1 research project. Implement
the following changes carefully, verify them, commit the completed changes,
and push them to the configured GitHub remote. Do not claim that the project
is Q1-ready merely because the tests pass.

## Research identity and scope

Rename the research-facing project to:

**Response-JEPA Chess**

Subtitle:

**Opponent-Aware Multi-Horizon JEPA for Resource-Bounded Zero-Sum Chess
Planning**

This is intentionally a chess-specific deterministic two-player zero-sum
testbed. Do not describe the current system as a generic architecture for all
two-player games. Keep `CAISSA-JEPA` only as a backward-compatible package,
executable, installer, or storage identifier until a verified migration is
possible.

Update research-facing README headings, documentation titles, experiment
manifests, result labels, and paper-facing strings to use the new name. Keep
application UI text in English. Do not perform a blind global rename of paths
or Python imports; preserve compatibility and add explicit migration aliases
where needed. The existing `docs/RESEARCH_IDENTITY.md` is the source of truth.

## Dataset state and safety

The known-bad datasets were intentionally deleted before this task. Do not
download or regenerate a production dataset in this conversation. Do not add
datasets, checkpoints, caches, SQLite databases, or logs to Git.

The implementation must handle a missing dataset cleanly and fail closed:

1. Display a clear English message explaining that the dataset must be
   selected or downloaded before training.
2. Never silently fall back to an old dataset path, junction, stale cache, or
   checkpoint trained from another dataset.
3. Never start training when the manifest, shard hashes, aggregate counts, or
   dataset fingerprint cannot be verified.
4. Keep old checkpoints on disk unless a specific migration requires moving
   them; mark them incompatible with a missing or changed dataset rather than
   deleting them.

Implement or repair a reproducible dataset-audit pipeline with these rules:

- Recompute actual shard byte counts, row counts, position counts, hashes, and
  unfinished-row counts from the files.
- Compare recomputed values with the manifest and reject mismatches before
  training.
- Use a canonical game identity based on normalized move sequence and stable
  provenance fields, not only raw PGN/header text.
- Detect and quarantine duplicate games and duplicate positions. Produce a
  provenance report explaining every removed or quarantined item.
- Create explicit train, validation, and locked final-test manifests. Split
  by canonical game/event identity and run a cross-split position-overlap
  audit. The final test must never be used for tuning.
- Add parser fixtures for `O-O`, `O-O-O`, promotions, en-passant, castling
  rights, checkmate, and malformed moves. Record skipped-game reasons and
  quantify parser loss.
- Validate complete FEN semantics during transition checks, including board,
  side to move, castling rights, en-passant target, halfmove clock, and
  fullmove number. Add repetition/history handling or explicitly document and
  test the supported limitation.
- Write manifests atomically with schema version, source hashes, code version,
  split policy, license/provenance metadata, and deterministic fingerprints.

Add unit tests using temporary fixtures for every rule above. Tests must not
require the deleted production dataset.

## Training reliability

Fix the unresolved production training failure in which all five installed
training reports failed with `FileExistsError` at zero steps.

Requirements:

- Make fresh training versus explicit resume an unambiguous user choice.
- Report the resolved model path, checkpoint path, generation path, lock path,
  cache path, dataset fingerprint, PID, phase, and complete traceback on any
  failure.
- A stale lock or existing checkpoint must produce an actionable diagnostic,
  not an opaque `repr(error)`.
- Verify that a clean temporary run works for every registered model variant,
  including initial checkpoint creation, interruption, rollback, and explicit
  resume.
- Do not report a model as trained if it completed zero optimization steps.
- Keep atomic checkpoint generation/rollback behavior and test crash-safe
  recovery.
- Ensure GUI worker scheduling gives each selected model a fair, explicit
  budget; do not let one queue or cache task consume another model's budget.
- Repair cache validation so readiness checks verify checksum and complete
  metadata, not only file existence and output length.
- Fix training-runtime storage/ETA reporting so directory size is summed
  recursively and benchmark estimates are clearly labelled as pilot-only.

## Make the research matrix real and truthful

The documentation currently claims `H1+H2` and `no-response` variants, while
the active registry/CLI does not expose them. Resolve this mismatch by either
implementing and testing the complete matrix below, or removing unsupported
claims everywhere. Prefer implementing it because the matrix is necessary for
the paper:

- `h1`: one-step response-aware JEPA
- `h1-h2`: one- and two-step response-aware JEPA
- `full`: H1+H2+H4
- `no-response`: matched JEPA without opponent-response conditioning
- LeJEPA control, explicitly labelled `LeJEPA-inspired` unless the
  implementation is made faithful to the cited method
- direct policy/value control
- NNUE-style local control

Every model must have a stable registry name, configuration schema, parameter
count, feature declaration, checkpoint fingerprint, and CLI/GUI entry. Update
all docs and tests to match the actual matrix.

## Fix the central scientific mismatch

The current inference path takes a minimum over all legal opponent replies,
but training observes only one historical opponent reply. This cannot remain
unqualified as an adversarial learned architecture.

Choose and implement one defensible solution, document it with equations and
tests, and use the same objective in training and inference:

1. Train on an enumerated or sampled legal counterfactual response set with
   correct target construction; or
2. Replace the hard minimum with a calibrated learned opponent-response
   distribution/quantile objective supported by the training data; or
3. Restrict inference to the response distribution actually learned and rename
   the method so it is not presented as worst-case adversarial planning.

The chosen solution must include an ablation showing the effect of response
conditioning and response aggregation separately from the search algorithm.
Do not use random negatives as the only policy evaluation. Add hard legal
negatives or all-legal-move evaluation and report top-1, top-5, MRR/NLL and
value metrics.

## Representation and LeJEPA correctness

- Add missing state information required for the supported chess rules, or
  state a tested limitation and exclude affected claims from the evaluation.
- Add finite-difference gradient checks for every manual NumPy gradient path.
- For LeJEPA, either implement the cited objective faithfully with a clear
  mapping from equations to code, or keep the `LeJEPA-inspired` label and
  remove theoretical/faithful-reproduction claims.
- Add collapse diagnostics: variance, covariance, effective rank, latent
  norms, target error, and seed-to-seed stability.
- Separate representation metrics, supervised policy/value metrics, and
  end-to-end playing strength. Never use playing strength alone as proof of a
  better representation.

## Confirmatory model-v-model protocol

Turn the current exploratory arena into a reproducible confirmatory protocol:

- Use an independently pinned UCI referee, including binary hash, version,
  options, and time budget. If it is unavailable, mark the run exploratory and
  keep `ranking_ready=false`.
- Use a versioned opening suite with at least 50 diverse positions for smoke
  testing and at least 100 diverse positions for the final confirmatory run.
- Pair colors and opening positions, use fixed compute/time budgets, repeat
  across at least three model seeds, and record all seeds in the manifest.
- Define one primary metric before running the comparison. Report paired
  confidence intervals, win/draw/loss or WDL metrics, and an appropriate
  multiple-comparison correction for secondary metrics.
- Treat timeouts, cancellations, illegal moves, and max-ply truncation as
  censored/error outcomes, not silent draws.
- Separate `representation/search ablation` from `whole-system strength`
  comparisons. Match parameters, data, search, and compute wherever the
  comparison claims an architectural effect.
- Do not label a leader statistically validated unless all confirmatory
  criteria are satisfied.

Repair `ArenaHistory` resource lifecycle so iterators cannot leave SQLite
connections open after partial consumption. Add regression tests for early
iterator termination, idempotent import, concurrent read/write, and cleanup on
Windows.

## Documentation and scientific guardrails

Update the research protocol to state clearly:

- The primary claim is Response-JEPA Chess, not generic two-player JEPA.
- The contribution is a falsifiable response-aware multi-horizon planning
  hypothesis.
- No superiority claim is allowed without a clean dataset version, locked
  final test, independent referee, fixed protocol, and repeated seeds.
- The current prototype is not Q1-ready until those gates pass.
- Include kill criteria: if `full` does not beat `h1`, `h1-h2`, and
  `no-response` under matched compute with uncertainty intervals, narrow or
  pivot the paper claim.

Add a reproducibility manifest containing Git commit, Python/NumPy versions,
OS, CPU/GPU, thread counts, random seeds, dataset fingerprints, model config,
search config, referee hash, and protocol version.

## Verification and GitHub handoff

Before committing:

1. Preserve unrelated user changes; do not use `git reset --hard`, force-push,
   or overwrite remote history.
2. Run the full test suite:

   `python -B -m unittest discover -v`

3. Add and run focused tests for dataset gates, all model variants, training
   fresh/resume, checkpoint recovery, arena protocol, referee availability,
   SQLite cleanup, and missing-dataset behavior.
4. Run the available release/self-test command using temporary fixtures only.
5. Run `git diff --check` and inspect the final diff for stale claims,
   generated artifacts, secrets, and accidental data files.
6. Do not download or regenerate the deleted dataset as part of verification.

Create a branch named `codex/response-jepa-research-cleanup`, unless an
existing user branch is already in active use. Commit with a clear message,
for example:

`research: harden Response-JEPA Chess validation pipeline`

Inspect `git remote -v`, push the branch to the configured GitHub remote, and
report the exact branch, commit hash, push result, tests run, and any remaining
blockers. If GitHub authentication or remote access blocks the push, do not
pretend it succeeded; report the exact command and error.

Do not claim that training or model-v-model results exist in this task: the
production dataset was intentionally removed and will be reloaded later.
