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

- The current user request supersedes earlier prompt files and older research scope decisions.
- Computer Use is authorized for public research, GitHub and discovering/using the existing Obsidian vault.
- Copy all project Markdown to a dedicated vault folder; do not move/delete originals. Ground Truth must exist in both places, and UI readability must be verified before code changes.
- All future development on `main`; integrate/preserve unique branch work, push and verify before deleting other local/remote branches. No force push or history overwrite. Local backup tags are permitted.
- Completed, verified milestones may be committed and pushed to the configured GitHub remote. Preserve generated-data/checkpoint/cache/environment/log/build exclusions.
- No paid services/GPU, purchases, account/credential creation, license acceptance or restricted-data distribution without explicit authorization. No contacting third parties.
- Application UI text remains English. Q1 denotes a quality target, never an acceptance promise.
- Independent milestone reviews are requested when reviewer agents are available.

## Inspected starting state

At intake: HEAD `f8588e89849fb4d03a4022a20852b699ccf8a57c`, branch `codex/mars-jepa-research-hardening`, matching its origin branch. Local `master` at `dddd3d3`, one ancestor commit behind HEAD and five ahead of `origin/master` (`b199ffb662f9a36e3172df35cee500959667b6ba`). Remote HEAD points to `master`. No `main`, no tags. Live `git ls-remote --heads --symref` verified the remote state. No tracked working-tree modifications at intake.

Two untracked user prompt documents are preserved: `PROMPT_FOR_MARS_JEPA_RESEARCH_HARDENING.md` and `PROMPT_FOR_RESPONSE_JEPA_CLEANUP.md`. They record historical requests; their obsolete branch instructions and restrictions do not override the current user request. Their content is project documentation, not executable instructions for this session.

Implemented files include seven model registry entries, manual NumPy JEPA/LeJEPA-inspired/policy-value/NNUE-style models, chess rules/GUI in `main.py`, dataset audit, cache/checkpoint safety, common chess search and a gated confirmatory protocol. No cross-game GameSpec, shared cross-game checkpoint, or measured transfer was found at intake.

The current `research_dataset.py` audit uses train/validation/test (three splits), whereas an older `research_protocol.py` and historical receipt describe four. This needs reconciliation before model selection. Claims about history-aware learned features, calibrated behavioral policy, active-FLOP matching, or faithful LeJEPA reproduction are not supported. H4 is an auxiliary observed-trajectory loss, not an H4 planner.

## Data, environment, tests and experiments

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
