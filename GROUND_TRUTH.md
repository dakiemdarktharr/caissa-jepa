# CAISSA-JEPA — Ground Truth

Updated: 2026-09-29. Read this page first when resuming. Statements below distinguish inspected facts, historical receipts, proposed work, and research evidence.

## Identity, authority and hypothesis

Repository: `C:/Users/ANHKHOI/Documents/ChatGPT/caissa-jepa`.
Remote: `https://github.com/dakiemdarktharr/caissa-jepa.git`.
CAISSA-JEPA is the project/package identity. Existing implemented research is **MARS-JEPA Chess**, a CPU/NumPy chess prototype. The new program investigates JEPA for a defined class of games; it does not rename an existing engine into a proven general method.

Falsifiable hypothesis: action-conditioned prediction of future latent states across both players' turns improves planning under bounded compute, with benefits retained across multiple games in a defined class.

Scope: two players, alternating turns, full observation, deterministic transitions, zero-sum terminal utility, explicit legal actions and terminal rules. Hidden information, simultaneous moves, chance and general-sum utilities are separate future extensions. Complete state includes rule-relevant history, not merely the visible board.

Keep distinct: (1) behavior of a particular opponent; (2) worst-case/optimal opponent assumptions; (3) minimax/equilibrium search; (4) expectation under an uncalibrated policy. Current chess response aggregation is (4), not (2). The separate common negamax planner approximates (3) under a budget.

## User decisions and constraints

Latest steering (2026-09-29): user explicitly requests continued v2 development,
deep research and iterative model/workflow changes toward a professor-reviewable
candidate that outperforms baselines. This is authorization to continue research,
not evidence that a positive result exists or permission to bias comparisons.
Optimize baseline families with comparable development opportunity, retain an
attempt ledger including failures, and keep independent selection/final stages.
Method uniqueness remains a prior-art question, never a naming claim. The earlier
Computer Use Esc interrupted one turn; the subsequent user message resumed work.
Active v2 progress: two Exa research streams and one follow-up completed (150 requested search-result
slots, not150 unique papers), documented in `docs/V2_PREDICTIVE_RESEARCH.md` and
`docs/V2_GAME_EVALUATION_RESEARCH.md`. Read `docs/V2_RESEARCH_CONTROL.md` for the
adaptive-development and fair-baseline boundaries.

Independent same-project bitboard reference passed4 tests: all5,478 TTT states,
16,167 exhaustive transitions and39,596 generated transition comparisons;117
Reversi forced-pass visits and128 endgame action-value sets. It is not a
third-party engine. Source/version hashes are pinned in survey receipts.

V2 survey01 failed connect3 difficulty support (500admitted but26beyond-depth);
survey02 expanded to connect4 4x5 and passed difficulty support (500/191 and
Reversi4 356/352). Artifacts are `chess_data/v2-survey-01` and `v2-survey-02`.
No v2 model fitted/scored. Further root/target split analysis found only13
Reversi4 validation roots after old-training and cross-split exclusion; this
cannot support a credible second-family comparison. Prospective survey03 therefore
uses Reversi6 and Connect4, passing with500/499 and500/195 admitted/beyond-depth
roots. `docs/METHOD_V2.md` freezes the recurrent shared encoder, matched legal
fork supervision, six variants, two learning rates, three seeds and40 epochs
before fitting. The fork-geometry novelty review identifies strong prior art
and a centered-MSE equivalence; uniqueness is not established.

Immutable dataset `chess_data/v2-forks-01` PASSED audit:984 roots,17,612 nodes,
12,833 forks; train509/development209/selection131/final135 roots. All six split
pairs have zero canonical and feature-byte overlap. Fingerprint:
`3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
No v2 fit or selection/final predictions yet.29 integrated rules/data/model/
evaluator tests passed8.941s. Full regression then passed126 tests in72.353s;
runtime-specific10 tests passed0.324s. An earlier concurrent-source test run had
one expectation mismatch after the new invalid-cap guard; the fresh run passes.
Independent real-rule gradient audit:306 checks, maximum error6.69e-10. Runtime
repairs reviewed; report verification is the last pre-fit integration gate.
Local CPU: AMD Ryzen AI5 340,6cores/12logical processors,16,418,648,064bytes RAM.
Training is serial single-BLAS-thread; no cloud/GPU spending.37 Markdown files
were mirrored with matching SHA256 and Ground Truth reopened in Obsidian.

- The current user request supersedes earlier prompt files and older research scope decisions.
- Computer Use is authorized for public research, GitHub and discovering/using the existing Obsidian vault.
- Copy all project Markdown to a dedicated vault folder; do not move/delete originals. Ground Truth must exist in both places, and UI readability must be verified before code changes.
- All future development on `main`; integrate/preserve unique branch work, push and verify before deleting other local/remote branches. No force push or history overwrite. Local backup tags are permitted.
- Completed, verified milestones may be committed and pushed to the configured GitHub remote. Preserve generated-data/checkpoint/cache/environment/log/build exclusions.
- No paid services/GPU, purchases, account/credential creation, license acceptance or restricted-data distribution without explicit authorization. No contacting third parties.
- Application UI text remains English. Q1 denotes a quality target, never an acceptance promise.
- Independent milestone reviews are requested when reviewer agents are available.

## Inspected starting state

The paragraphs labelled intake below are historical inventory, not current state.
Current milestone update (2026-09-29): `main` preserves all prior commits; milestone
`135a690295c62a55b1e0ef0e32f8e6565f18b88a` was pushed and verified. GitHub default
is main. Local/remote master and codex/mars-jepa-research-hardening were deleted
only after ancestor checks and successful main push. Only main remains.
Verified implementation milestone `66ff9f27b25bc8d0bfc92628976a91c122724f87`
was subsequently pushed; this is the exact source commit for the pilot below.

At intake: HEAD `f8588e89849fb4d03a4022a20852b699ccf8a57c`, branch `codex/mars-jepa-research-hardening`, matching its origin branch. Local `master` at `dddd3d3`, one ancestor commit behind HEAD and five ahead of `origin/master` (`b199ffb662f9a36e3172df35cee500959667b6ba`). Remote HEAD points to `master`. No `main`, no tags. Live `git ls-remote --heads --symref` verified the remote state. No tracked working-tree modifications at intake.

Two untracked user prompt documents are preserved: `PROMPT_FOR_MARS_JEPA_RESEARCH_HARDENING.md` and `PROMPT_FOR_RESPONSE_JEPA_CLEANUP.md`. They record historical requests; their obsolete branch instructions and restrictions do not override the current user request. Their content is project documentation, not executable instructions for this session.

Implemented files include seven model registry entries, manual NumPy JEPA/LeJEPA-inspired/policy-value/NNUE-style models, chess rules/GUI in `main.py`, dataset audit, cache/checkpoint safety, common chess search and a gated confirmatory protocol. No cross-game GameSpec, shared cross-game checkpoint, or measured transfer was found at intake.

The current `research_dataset.py` audit uses train/validation/test (three splits), whereas an older `research_protocol.py` and historical receipt describe four. This needs reconciliation before model selection. Claims about history-aware learned features, calibrated behavioral policy, active-FLOP matching, or faithful LeJEPA reproduction are not supported. H4 is an auxiliary observed-trajectory loss, not an H4 planner.

## Data, environment, tests and experiments

Current update supersedes the intake bullets below: `two_player/` now implements
shared affine NumPy models, GameSpec rules for three tiny training games and one
held-out size variant, strict four-stage audit, seven controls, atomic checkpoints,
epoch-addressed resume, local-position search/evaluation and bounded CPU training.
Implementation is not evidence of planning superiority. Frozen method v1 remains
unchanged; `docs/METHOD_AMENDMENTS.md` governs the v1.2 feasibility pivot.

The 800-trajectory whole-game feasibility audit FAILED coverage (fingerprint
`c506b7907bc0917addb8478d3ea69331a2db31dbcd7d29c1318efeef901f5dda`), so no
training used it. A separately written middle/late scope dataset PASSED support,
replay and strict context/target overlap gates (fingerprint
`7430e1cd7204ca09c6c7b730e694282435a7e91bfc8e8938f2554563707584e8`). Both
are preserved locally at `chess_data/two-player-pilot-v1` and
`chess_data/two-player-pilot-v12`. Source is project-owned procedural self-play;
no external data acquired, public generated-artifact license not assigned.

Explicit runtime: `C:/Users/ANHKHOI/AppData/Local/Programs/Python/Python311/python.exe`
(3.11.9, NumPy2.4.6, PySide6 6.11.1). Bare `python` can resolve to MSYS2 and is
not reliable here. New `requirements-research-lock.txt` records this environment.
Full unittest suite passed 86 tests in 35.356s before final pilot-integrity fixes;
the six updated model tests and standalone core checks also pass. Final full
suite: **87 tests passed in52.122s**; standalone core PASS and source release
smoke PASS with13 checks. Independent
review reproduced all-seven-variant gradients (max error 5.18e-11), found node-cap,
identity-freeze, history-write and time-budget issues; these were repaired before
model fitting. Fixture tests are engineering evidence only.

**Pilot completed:** 21/21 predeclared runs (7 variants x3 seeds), 10 epochs and
180 steps each, 1,129 training records; 68 frozen roots and 2,856 learned planner
decisions plus68 no-model decisions. No failures, censoring or collapse alerts.
All dataset/source/schedule identities and checkpoint hashes independently verified.
Selection/final prediction counters remain0. Actual results and all aggregate
metrics: `docs/TWO_PLAYER_PILOT_20260929.md` and
`docs/validation/TWO_PLAYER_PILOT_20260929.json`. Local checkpoints:
`chess_data/two-player-runs-v12/`. Training source hash:
`c22863ccaf6c1edacc115f7090e6294b1d280d441d3b5df70159acdec34578a2`.

**Scientific outcome:** no JEPA advantage established. All learned exact-state
variants have zero regret on a ceiling-prone schedule; connect3 has only2 roots
with no neural leaves. Full hybrid JEPA has Reversi regret5/72 across seeds versus
direct0/72 and decoded5/72. These are regret units per local decisions, not win
counts or a significance result. Held-out-size transfer benefit and regularizer
benefit are unproven. M7 pivots to a separately frozen, discriminating development
benchmark; scaling this pilot and confirmatory work stop at the roadmap gates.
Working paper is `docs/WORKING_PAPER.md`, explicitly not submission-ready.
Independent findings/disposition: `docs/INDEPENDENT_REVIEW_20260929.md`.

Resource evidence: training251.21s total,8.84–18.64s/run; maximum traced
allocations16,966,858 bytes, not RSS; local run artifacts11,245,483 bytes.
Tracemalloc and overlapping regression execution preclude efficiency claims.
No paid/cloud/GPU services or external corpus used. Generated artifacts remain
excluded from both Git and Obsidian; only source/docs/small aggregate receipts
are published. Remaining research M7–M9 is not complete or claimed complete.

Legacy chess repairs: canonical parsed FEN identities, audit v3 four splits,
no-response preserves own H4 action, rejects obsolete no-response checkpoints,
deadline forwarding and final-ply mate adjudication. Confirmatory protocol v3
unconditionally blocks until independent full-history rules validation exists;
UCI evaluation telemetry cannot satisfy this requirement.

Historical intake observations (do not interpret as current results):

- Current workspace has no `.venv`, `fen_dataset` or `chess_data`. Two ignored crawler logs exist; they are not data or research evidence.
- Historical receipts describe a removed bad chess dataset and failed zero-step runs. No valid production dataset or confirmatory result is established by those receipts.
- Read-only inspection: `D:/CAISSA-JEPA/datasets` exists but its immediate listing is empty; `D:/CAISSA-JEPA/fen_dataset` was not found. Five legacy NPZ files exist in `D:/CAISSA-JEPA/app-data/chess_data`; contents/compatibility have not been revalidated. Preserve them and do not use for this research by default.
- `D:/CAISSA-JEPA/source/.venv/Scripts/python.exe` exists but is a separate checkout's runtime. The active task is this C: workspace, despite historical migration instructions to use D:.
- Available default Python is 3.11.9, with NumPy 2.4.6 and PySide6 6.11.1 imported successfully; Torch is not installed. `requirements-lock.txt` records historical NumPy 2.0.2/PySide6 6.10.3 validation, not verification of today's environment.
- At this initial inventory, no tests/training/strength experiments have been run in this session. Historical 27/41/52-test receipts are version-specific. Temporary fixtures and release smoke tests are engineering checks, never research results.
- No external dataset or engine was downloaded, no new checkpoint produced, no paid compute started.

## Claims ledger and acceptance

Allowed: implemented prototype capabilities supported by source/tests; explicit exploratory measurements with their sample, exclusions, hardware, seed and uncertainty; falsifiable hypotheses labelled unproven.

Not established: JEPA improves strength; opponent conditioning improves minimax; cross-game transfer; a universal shared model; superiority over Stockfish/AlphaZero/MuZero; faithful LeJEPA theoretical guarantees; publication readiness or Q1 acceptance probability.

Novelty risk is high: AlphaZero and MuZero already span board games. A contribution requires a controlled incremental benefit beyond policy/value and non-JEPA dynamics with matched data/search/compute, not a multi-game demo. Selection/final separation, symmetry-aware leakage checks, collapse diagnostics, independent rules/referee validation and bounded pilot resource measurements are gates.

Before code: complete vault copy and UI verification, systematic primary-source research review, roadmap with kill criteria, frozen method v1. Before production training: legally usable data, provenance/SHA-256/count/parser audit, legal transitions and leakage gates. Before confirmation: frozen primary metric, sample size, paired roles, seeds, budgets, intervals, multiplicity/censor/stopping rules and independent review. Negative results must remain visible.

## Obsidian memory

Discovered through Computer Use on 2026-09-29: Obsidian 1.13.7 vault manager shows `vault_1` under **`D:/notes`**. The UI lists the parent below the vault name; the registered Obsidian configuration confirms the full root **`D:/notes/vault_1`**.
Project destination: `D:/notes/vault_1/Caissa-JEPA/`.
Entry page: `D:/notes/vault_1/Caissa-JEPA/GROUND_TRUTH.md`.
Initial copy and opening verification: PASS on 2026-09-29. All 22 project Markdown files copied with matching SHA-256. Obsidian quick switcher lists the copied hierarchy and Ground Truth was opened with its actual text visibly rendered. The pre-code memory gate is complete.

The previous v1 mirror comprised30 project Markdown files, including its roadmap,
method/amendments, source review, data register, executed pilot, independent review
and working paper. The live v2 mirror now includes the additional v2 documents;
each sync verifies every project Markdown SHA-256 and reports its actual count.
On resumption, the actual Ground Truth page was reopened successfully in Obsidian.
Active v2 documents are added in the next mirror sync; do not confuse the previous
30-file snapshot with the later live count.

Copy only project Markdown, preserving relative paths and originals. Exclude `.git`, environments, caches, generated/build/data directories, non-project notes and non-Markdown artifacts. No datasets/checkpoints are copied to this potentially synced vault. Record file counts and hash comparison; annotate superseded documents through `docs/DOCUMENT_INDEX.md`.

## Source map and resume order

1. This document, current working tree and `git branch -avv`.
2. Vault entry page above, then `ROADMAP.md`, `METHOD_SPEC.md` when created.
3. `AGENTS.md` for collaboration, exclusions and English UI.
4. `README.md`, `docs/RESEARCH_IDENTITY.md`, `docs/MARS_JEPA_RESEARCH_IDENTITY.md`, `V7_RESEARCH_PROTOCOL.md`, `docs/MARS_HARDENING.md`, `docs/RESEARCH_DECISIONS.md` for implemented chess protocol.
5. `docs/DOCUMENT_INDEX.md` for current versus historical provenance.
6. `model_registry.py`, `adversarial_jepa.py`, `research_dataset.py`, `research_protocol.py`, `research_search.py`, `confirmatory_protocol.py`, `training_runtime.py`, `runtime_safety.py` to verify code claims.

Update this document and its vault copy after important decisions/deliverables and before ending a long session. Never substitute historical data/run claims for live verification.

Discovery correction: an initial 22-file copy was placed at D:/notes/Caissa-JEPA (the parent outside the vault). It is preserved as an intake snapshot, not the active mirror. No originals were moved or deleted.
