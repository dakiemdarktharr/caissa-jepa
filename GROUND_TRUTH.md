# CAISSA-JEPA — Ground Truth


## Latest continuation delta (2026-10-03; root-bootstrap source audit)

- Checked the primary sources cited for the proposed stratified crossed bootstrap. Owen (2007) gives a mean-consistency result for row/column resampling in crossed random-effects models; MacKinnon, Nielsen, and Webb (2021) derive asymptotic conditions for specific two-way cluster-robust regression inference. Preston's rescaled bootstrap addresses stratified multistage sampling without replacement; MacKinnon and Webb (2018) address few treated clusters in linear treatment models.
- These sources motivate respecting crossed/stratified structure but do not establish finite-sample coverage or type-I error control for the proposed 20 model seeds, 16 slots per occupancy band, paired seats, 15 contrasts, max-|T| intervals, and centered bootstrap tests. Holm adjustment requires valid input p-values; more bootstrap replicates reduce Monte Carlo error but do not add independent sampling units.
- Added a remote-only statistical source audit draft. It calls for independent review of whether a design-matched synthetic coverage/power study is needed, with scenarios and acceptance criteria frozen in advance. This is an open validation item, not proof the bootstrap is invalid. No roots were generated and no outcomes were accessed; no method or gate changed.
- Checkout remains untouched with pre-existing modified/untracked files; Obsidian remains deferred. Sources: [Owen](https://arxiv.org/abs/0712.1111), [MacKinnon et al.](https://doi.org/10.1080/07350015.2019.1677473), [Preston](https://www150.statcan.gc.ca/n1/pub/12-001-x/2009002/article/11044-eng.pdf), [MacKinnon & Webb](https://doi.org/10.1111/ectj.12107).



## Latest continuation delta (2026-10-03; executable game-model prior-art check)

- Read Lehrach et al., *Code World Models for General Game Playing* (ICLR 2026), from the official proceedings and primary arXiv source. It synthesizes executable Python rules/transition/legal-action models from game descriptions and sample trajectories, then uses MCTS for perfect-information games and ISMCTS for imperfect-information games. Its ten-game suite includes Connect Four and four paper-created games; it reports matching/beating Gemini 2.5 Pro on nine of ten.
- This further closes broad claims to model-based search or general game-model planning. It is materially distinct from CAISSA: LLM-generated executable code rather than learned neural latent dynamics/JEPA, and a general-LLM policy baseline rather than compute-matched learned-dynamics controls. The paper's trajectory-derived checks do not guarantee unseen-state rule correctness. No CAISSA benchmark/result is implied.
- No gates, code, data, outcomes, training, or local checkout changed. Obsidian remains deferred. Sources: [official ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/d8a12fde9e72444e1b356e8c37e53753-Abstract-Conference.html), [arXiv](https://arxiv.org/abs/2510.04542).



## Latest continuation delta (2026-10-03; LAMIR game-model prior-art refresh)

- Read the primary-source paper by Kubíček and Lisý, *Look-ahead Reasoning with a Learned Model in Imperfect Information Games* (LAMIR), arXiv:2510.05048; the paper identifies itself as published at ICLR 2026.
- LAMIR learns latent representations for both players' information sets, predicts next abstract states from joint actions together with reward, termination and legal actions, and uses a learned abstraction with depth-limited CFR+ look-ahead. It reports lower exploitability than concurrent RNaD on smaller games and up to 80% head-to-head wins in larger games. These published claims were not independently reproduced.
- Novelty positioning is narrowed: learned latent game models plus look-ahead, and alternating/zero-sum game domain alone, are not new. LAMIR is imperfect-information, simultaneous-action/no-chance, MuZero-inspired rather than JEPA, and uses equilibrium-oriented CFR+; it does not test CAISSA's deterministic fully observed exact-rule board-game setup or JEPA-versus-matched-control regret question. That difference is a candidate empirical question, not an established novelty claim. V2.12 max/min remains a heuristic, not a Nash solver.
- No source, data, model, outcome, method, or gate changed. No training, scoring, or match occurred. Obsidian remains deferred. Source: [primary paper](https://arxiv.org/abs/2510.05048).


## Latest continuation delta (2026-10-03; lattice memory.peak probe)

- A no-inference process ran in a disposable user systemd scope with `MemoryMax=1536M`; it reported the same cgroup's `memory.max=1610612736`, `memory.peak` present, `memory.oom.group=0`, and a 5,529,600-byte current/peak reading.
- Systemd subsequently reported the scope `LoadState=not-found` and `ActiveState=inactive`. Log: `/tmp/caissa_v212_memory_peak_audit.log`.
- This confirms interface availability and scope cleanup only. It does not measure inference memory/headroom, verify peak-reset semantics under a workload, or demonstrate supervisor survival under all OOM victim choices. No model, request worker, pilot, or project data was used.

## Prior continuation delta (2026-10-03; cgroup memory and OOM policy audit)

- The current compute-budget amendment v05 calls sampled RSS a hard process safety stop, but the code samples process RSS and the host audit says that sampling is not a hard limit. Linux cgroup v2 documents `memory.max` as the hard-limit/OOM mechanism and `memory.high` as throttling/reclaim.
- The adapter requires `memory.oom.group=0` with an error claiming this makes the supervisor survive. Kernel semantics do not guarantee that: zero avoids indivisible group killing, but any eligible process in the cgroup may still be selected. The lattice child OOM probe showed one surviving-parent case only.
- Added an unreviewed v06 compute-budget correction draft and clarified the adapter error message/test. Proposed node/time caps are unchanged; no operational budget, pilot, or fit authorization follows.
- Scratch verification copied exact remote adapter/test blobs (Git blob IDs `9dbf3b75dd5526d1577e7c9cdfd3dcf4313543cf` and `3df288c070da39ef98146ee85bb6a9337266c22c`) to `/tmp`, changed only the OOM wording/assertion, and passed the seven adapter tests in 0.331 seconds. Log: `/tmp/caissa_v212_oom_audit.log`. The project worktree was not edited.
- The next runtime gate needs external OOM supervision/receipt handling, actual `memory.peak` availability evidence, and separate worker-OOM/watchdog integration tests, all without training or outcome access.

## Prior continuation delta (2026-10-03; counterfactual-support count audit)

- Further self-audit found “multiple independent episodes” in the support draft was stronger than the implemented definition, which only counted distinct episode IDs. The draft now reports distinct IDs, declared seeds, policy-pair/seat diversity, and repeated trajectory/prefix content separately; it makes no statistical-independence claim.
- Remote-only documentation update based on source-level protocol review. No code, local checkout state, data, pilot, or experiment artifact changed; no tests or outcome access were performed.

## Prior continuation delta (2026-10-03; alpha-beta root-score contract audit)

- Read-only inspection of the lattice checkout found `main` at `0cba5d646db40f4da0ef07e1d84c26b098580b2e`, four commits behind `origin/main`, with pre-existing modified `ROADMAP.md` and `docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md`, plus untracked root-sampling draft, duplicate/overlap audit, request-adapter code/tests, and symmetry tests. The checkout was left untouched; remote GitHub remains authoritative for this update.
- Source audit of frozen `two_player/v212_pilot.py` found the runner passes the incumbent root alpha through later root-action searches and discards its per-action value map after selection. Under alpha-beta cutoffs, a returned non-selected action value can be an upper bound rather than its exact fixed-depth value. The compute-only pilot publishes no action-score ledger, so this does not alter prior receipts or compute findings.
- Updated `docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md` to require exact/bound/missing status and provenance, prohibit point-ranking or point-regret from bounds, and leave the exact all-action diagnostic and separate budget for independent review. This is a draft clarification only.
- No tests, inference, pilot, data generation, training, match, or outcome access occurred in this documentation/source-audit step. Existing gates and negative results remain unchanged.

## Prior latest continuation delta (2026-10-03; request scope and related-work update)

## Latest continuation delta (2026-10-03; request scope and related-work update)

- The latest remote checkpoint before this delta was `6c671e3e4e57abc3310a8f8563568f2add7b7e6d` on `main`; updates were made only to research documentation through the authenticated GitHub integration. No local checkout, source code, generated data, or experiment state was changed.
- The request adapter focused suite passed 20/20 after adding a bounded parent/child scope-inheritance test; compile and `git diff --check` passed. Frozen V02 pilot files remain unchanged.
- A no-inference subprocess preflight inside a disposable lattice 1.5 GiB scope verified parent and spawned preflight worker had the same cgroup path, `memory.max=1610612736`, and `memory.oom.group=0`. The scope was removed. This did not execute a request, model inference, or pilot cell.
- A targeted first-party literature check added Nam et al., Causal-JEPA (ICML 2026/PMLR), as adjacent work on object-level masking and counterfactual-like prediction queries. It does not evaluate complete legal-action branches or exact adversarial board-game transitions, so the V2.12 counterfactual-support protocol gap remains open.
- Adapter independent review, end-to-end request timing/headroom, report/receipt integration, trajectory generation and split audits remain open. No data generation, training, match, or outcome inspection occurred. Do not treat this checkpoint as pilot authorization.

## Prior latest continuation delta (2026-10-03; V2.12 RSS guard-path audit)

## Latest continuation delta (2026-10-03; V2.12 RSS guard-path audit)

- At continuation start, verified `/home/koi/src/caissa-jepa`, branch `main`, HEAD and `origin/main` `e5b02d0ddb91abf824a3df3dd3b0194a4f643627`, clean; remote is `https://github.com/dakiemdarktharr/caissa-jepa.git`.
- Read-only source review confirmed the V02 RSS check is sampled/cooperative rather than a hard ceiling. The entry sample records but does not enforce the cap; checks occur every 256 nodes; if an over-cap condition remains at the unconditional final sample, `PilotBudgetStop` escapes its handler and the V02 runner does not write an aggregate receipt. Focused tests exercise node cap but not RSS entry/periodic/final paths. No process memory watchdog is present.
- This does not invalidate the completed V02 report: its maximum sampled RSS is 50,212,864 bytes versus the 1.5 GiB cap, and no over-cap event was reported. Before any future cap-stressed pilot, make a versioned guard/reporting change, test all RSS paths, and verify an OS/process memory bound if claiming a hard cap. Do not mutate or rerun the hash-bound V02 report in place. Request-to-response watchdog and data-generation gates remain open; no training or data creation occurred.
- Details are in `docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md`. Background source review PIDs/logs: `91281` (`/tmp/caissa_cont3_source_review.log`), `91312` and `91350` (`/tmp/caissa_cont3_implreview.log`, `/tmp/caissa_cont3_implreview2.log`), `91541` and `91597` (`/tmp/caissa_cont3_rss_audit.log`, `/tmp/caissa_cont3_budgettests.log`).

## Prior continuation delta (2026-10-03; adversarial board-game prior-art check)

- At continuation start, verified checkout `/home/koi/src/caissa-jepa`, branch `main`, HEAD and `origin/main` `87450b311ace159514d33f5a92d834b1b02e7074`, clean; remote remains `https://github.com/dakiemdarktharr/caissa-jepa.git`.
- A targeted Exa search ran 13 queries across JEPA-in-games, adversarial board-game world models, and latent planning/transfer, requesting 92 results before deduplication. This is a lead-generation/search pass, not a systematic review.
- First-party code review of [WorldModel-ConnectX](https://github.com/alextitonis/WorldModel-ConnectX) found the closest directly verified adversarial board-game latent-model/search setting in this pass. Its self-supervised encoder/dynamics model uses shared-encoder latent targets and a three-step unroll, without an EMA target; the training `step` bundles a fixed opponent response. Its deployed minimax uses exact legal board transitions and the learned value head at leaves; its latent-beam search is a separate comparison baseline. The README's headline and detailed method describe this distinction inconsistently, so the code path controls the interpretation. The public README/repo results are author-reported and not independently reproduced here.
- [SOLIS](https://arxiv.org/abs/2506.04892) is adjacent board-game latent planning: a Stockfish-value-aligned contrastive chess encoder and six-ply beam, without learned action-conditioned transition dynamics or explicit alternating minimax. Its reported Elo is not independently verified here.
- Novelty consequence: learned latent models with adversarial board search, and latent-guided planning in a board game, cannot be claimed as new settings. Neither source evaluates the specific V2.12 EMA-target JEPA loss with matched non-JEPA/exact-state controls. The research gate is unchanged; no training, match, score, data generation, or protocol change occurred. Obsidian remains deferred.
- Search and first-party method distinctions are documented in `docs/RELATED_WORK.md`, `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`, and `ROADMAP.md`. Background command PIDs/logs: skill read `87677` (`/tmp/caissa_search_skill.md`); repo snapshot `87679` (`/tmp/caissa_repo_state.log`); diff review `88626` (`/tmp/caissa_current_research.verify.log`, `/tmp/caissa_current_research.patch`).

## Prior continuation delta (2026-10-03; V2.12 drafts and literature refresh)

- Verified checkout: `/home/koi/src/caissa-jepa`, `main` at `16bcdeefd42ad065a7d38c24557909477bfe8407`, matching `origin/main`; working tree was clean before this documentation update. Remote is `https://github.com/dakiemdarktharr/caissa-jepa.git`.
- The random-weight no-training compute pilot v02 completed 1,152/1,152 depth-four cells under its safety ceilings. Twelve cells exceeded 2 seconds; maximum was 3.7419 seconds, 7,224 nodes, 20,891 model calls, and 50,212,864 sampled RSS bytes. This is synthetic-state, single-host instrumentation, not trained-model runtime, playing strength, or a common operational budget. The 10,000-node/5-second planner cap and 6-second response deadline remain reviewed proposals pending request-to-search headroom implementation verification.
- `docs/METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md` and `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` remain design drafts. The proposed 48 roots per held-out variant, 64 candidate slots per occupancy band, phase bands, and symmetry uniqueness policy are not frozen or verified; no roots or training trajectories were generated. The synthetic-only trajectory auditor is implemented and reviewed, but does not authorize corpus generation or fitting.
- Static source review confirms `audit_trajectories` constructs H0–H4 windows only in memory from caller-supplied synthetic episode fixtures. It is not a production corpus generator; its unconditional duplicate-window rejection also remains distinct from draft v05's diagnostic-only policy for canonical-equivalent content and needs explicit reconciliation before production reuse.
- A follow-on source pass mapped the random-weight pilot's timing boundary: schedule/model construction and warmup precede `run_root_arm`; validation/model reset precede its timer; RSS is sampled at timer start, every 256 search nodes, and at return; and the pilot returns counters rather than a response action. This does not verify the request-anchored 5s/6s operational deadlines or watchdog.
- A targeted full-text check of PiJEPA (arXiv:2603.25981v1) confirmed autoregressive multi-step JEPA latent prediction used with action-sequence planning. Its policy-guided MPPI and continuous single-agent navigation differ from V2.12's exact legal discrete max/min setup, but reduce novelty room for JEPA-rollout-plus-planning. The bounded crosswalk is `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`; independent source/code fact-check found no concrete correction. This is not a design approval; no fit or superiority evidence follows.
- The expanded primary-source pass covered Value-Guided JEPA Planning, H-JEPA, Delta-JEPA, WA-JEPA, and ActSWM. ActSWM is the closest game-domain JEPA prior found so far (single-agent open-world Minecraft control, not zero-sum board play); its frozen action readout and recorded-versus-all-zero rollout separation further narrow novelty claims. Any V2.12 diagnostic should compare same-root legal alternatives only when exact-rule consequences differ, and pair latent separation with exact-state/value/ranking evidence; latent distance alone is insufficient. Updated scope and distinctions are in the crosswalk and `docs/RELATED_WORK.md`; this is not a novelty finding or gate approval.
- The 2026-10-03 literature update in `docs/RELATED_WORK.md` records Semigroup-JEPA as direct prior art for recursive multi-step JEPA rollout training, and Action-Conditioned Predictive Consistency as adjacent prior art for paired rollout diagnostics. Neither supplies board-game/minimax evidence or validates a V2.12 advantage. An aggregator-only “JEPA-Chess” record had no verifiable primary Zenodo/DOI source and is explicitly excluded as evidence.
- No training, match, score, or confirmatory outcome was accessed or generated in this continuation. The user has deferred Obsidian; no vault was opened or changed. Generated data, checkpoints, caches, environments, and logs remain excluded from Git.

## Latest continuation delta (2026-10-02; completed V2.9 and next research gate)

- V2.9 completed its 60-fit panel and frozen development match. Independent review of the saved analyzer and raw schedule found no P1/P2 findings: 160 unique scheduled blocks in exact order, 40 per game/control cell, complete pairs, balanced JEPA seat swaps, no forfeits/censors, and transcript replay validation. Reviewer notes all matches begin at fixed standard initial positions, limiting starting-position generalization.
- The pinned analysis artifact is `docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json`, status `exploratory_only`; artifact SHA-256 is `e0c0c0dd512068d0917d9774cef23772e1543a2029c4e35fc807c5f16c8491b3`. JEPA-minus-task-value score was Connect4 -0.1375 (seed-cluster unadjusted t95% CI [-0.2480,-0.0270]), Reversi6 +0.0125 ([-0.1104,+0.1354]), macro -0.0625 ([-0.1296,+0.0046]). The frozen nomination gate fails. JEPA vs direct leaf was near parity (macro -0.00625). Planner CPU ratios vs task-value were 1.0249 and 1.0050. No claim of superiority, confirmation, equilibrium, exploitability, broad transfer, or Q1 readiness is supported.
- A 2026-10-02 targeted primary-source search added Soemers et al. (arXiv:2102.12375) and Ben-Assayag & El-Yaniv (arXiv:2107.08387) on game/variant and small-to-large board transfer; and PCGrad (NeurIPS 2020), CAGrad (NeurIPS 2021), and JEPA Policy (arXiv:2609.09630) on gradient conflict/routing. These are prior art: neither transfer nor gradient routing can be the novelty claim by itself. The update is recorded in `docs/RELATED_WORK.md`; it remains a targeted, non-exhaustive search.
- Independent reviewer diagnosis is explicitly hypothetical, not causal: the reply-set latent objective may interfere with shared encoder policy/value gradients. A new pre-implementation protocol, `docs/METHOD_V210_GRADIENT_DIAGNOSTIC.md`, specifies a train-only, no-optimizer-update gradient decomposition/alignment diagnostic and conservative stop/proceed gate. It does not authorize another model fit. Proceed to a routed intervention only if all gates pass and a separately reviewed development preregistration is frozen. If the diagnostic fails, stop this candidate without subgroup hunting.
- `ROADMAP.md` now sequences diagnostics, mechanism decision, conditional development experiment, model selection, locked confirmation, and paper package, with explicit deliverables, acceptance criteria, relative effort, and kill criteria. Professor-facing result is updated in `docs/PROFESSOR_BRIEF_V2.md`.
- In this continuation shell/PowerShell commands are run hidden/noninteractive in the background to keep the desktop available, per user's instruction. Existing V2.9 test verification remains 20/20 V2.9 and 96/96 V2.8 in Python 3.11.9 / NumPy 2.4.6; the artifact analyzer run and independent replay review completed. Latest source commit/remote hash before these documentation updates was `5a2b0561b8c05cc8d72a060b33798dd2925debbc`; working tree now contains only the intended result/documentation changes, pending test, vault sync, commit and normal push.
- Obsidian destination remains the previously UI-discovered `D:\notes\vault_1\Caissa-JEPA\`. Use the existing hidden sync script and verify source/destination hashes, backup any differing note without overwriting its prior contents, and record final count/status here. Do not reopen Obsidian UI while honoring the screen-availability preference.
- Obsidian sync completed at 2026-10-02 14:44 local time: copied 114 Markdown files, backed up 4 differing prior notes under `D:\notes\vault_1\Caissa-JEPA\_sync_history\20261002-144431-v28-hardening-preflight\`, with zero hash mismatches. Verified matching SHA-256 and presence of Ground Truth, roadmap, V2.10 method note, professor brief, and related-work review in the vault. Existing earlier Obsidian UI verification established that the Ground Truth page opens and is readable; this update stayed in the background so the desktop remains available. The machine-readable validation JSON is intentionally not mirrored by the Markdown-only vault sync.
- The V2.10 helper and runner are implemented in `two_player/v210_gradient_diagnostic.py` and `tools/v210_gradient_alignment_diagnostic.py`, with tests in `tests/test_v210_gradient_diagnostic.py`. To preserve V2.9 checkpoint provenance, `two_player/v28_model.py` and its pinned source hash were not changed; decomposition evaluates shallow config views over the frozen model. The diagnostic uses 20 hash-verified V2.9 reply-JEPA checkpoints, 640 deterministic hash-selected train roots/game, and 10 batches/seed/game, with no optimizer, EMA, or checkpoint write. Targeted tests pass (V2.10 2/2, V2.8 model 15/15, V2.9 20/20) in the locked runtime, and `git diff --check` passes. An independent review is pending; do not launch until it reports the runner and data boundaries safe.
- V2.10 review by the existing approved `gpt-6-luna/high` reviewer resolved all four initial P2 findings: receipt hash is panel-bound; V2.10 and data-loader source hashes are recorded; diagnostic metrics match the implemented encoder-only protocol; and checkpoint loading bypasses metadata/history, reading only ledger-hash-verified p_/t_ arrays. Unit test uses deliberately invalid metadata JSON. Reviewer found no P1/P2 and approved the train-only/no-update diagnostic. A first hidden launch exposed only an import bug before data access; the root constant was fixed and reviewer confirmed no new issue. The corrected launch then stopped before checkpoint or gradient evaluation because train support is 307 Connect4 roots and 1,490 Reversi6 roots, fewer than 640 needed/game. No gradient result exists. The feasibility receipt is `docs/validation/V210_DIAGNOSTIC_PREFLIGHT_01.json`; failed stderr is ignored under `chess_data`.
- A support-only amendment `docs/V210_GRADIENT_DIAGNOSTIC_AMENDMENT_01.md` now freezes 300 hash-selected roots/game in ten non-overlapping batches of 30, retaining the 20 seeds and original 6/10 conflict gate. The smaller minibatch’s added gradient noise is a limitation. This change was made before any gradient outcome; the corrected root and batch count require independent review before a new diagnostic run.
- The `dev03` amended launch passed sample support but stopped before parameter load/gradient because runner expected a data-audit source hash in the individual fit receipt rather than the panel ledger. The `dev04` launch passed support and panel-bound checkpoint/receipt hashes but requested the frozen model config from the result panel, which binds the separate input spec instead. Neither loaded checkpoint arrays or computed gradients. Receipts are `docs/validation/V210_DIAGNOSTIC_PREFLIGHT_02.json` and `_03.json`. Runner now checks the V2.9 fit-spec SHA against the panel and reads its config from that file; it preloads/verifies all 20 weights-only checkpoints before computing any gradient. This small provenance fix is under independent review; run only after review passes.

Updated: 2026-10-02. Read this page first when resuming. Statements below distinguish inspected facts, historical receipts, proposed work, and research evidence.

## Current correction (2026-10-02; V2.9 supervisor review)

- The current uncommitted V2.9 panel supervisor has passed an independent `gpt-6-luna/high` review with no P1/P2 findings. It applies a stdin release handshake after Job Object assignment, per-process and per-job commit limits, per-process user CPU and wall-time limits, a one-second reactive free-RAM guard, and a fresh source-hash check immediately before launch. It records lifecycle/resource data only and requires a complete 60-fit ledger before reporting success.
- The 1.3 GB commit cap and four CPU-hour cap are protective policy limits, not empirically calibrated limits. Pilot 03 measured peak working set (859,336,704 bytes), which is not a measurement of commit usage; reviewer found no commit peak evidence or CPU-cap stress test. The six-hour wall ceiling is conservative relative to the small V2.8 fit panel, but is not a scientific result.
- The sandbox initially denied access to the `.venv` base interpreter, but elevated noninteractive verification succeeded: Python 3.11.9 and NumPy 2.4.6 match the research lock exactly. In that runtime, 20 V2.9 tests pass, 96 V2.8 regression tests pass, and `py_compile` / `git diff --check` pass. Runtime is ready for the frozen panel; the earlier bundled Python 3.12.14 / NumPy 2.3.5 test run was supplemental only.
- Reviewed supervisor milestone is committed and pushed on `main` as `03df5fb8075f8aad407cb100fdf5dc7bef696a3c`; direct `git ls-remote origin refs/heads/main` returned the same hash. Working tree is clean, with only `main`, `origin/main`, and `origin/HEAD -> origin/main` present. The Obsidian Markdown sync at 2026-10-02 13:44 copied 113 files, backed up 4 differing prior notes, and reported 0 hash mismatches; copy the post-commit Ground Truth update once more before ending.
- No 60-fit V2.9 panel or match has run as of this note. Pilot 03 remains compute-only. Do not inspect `train_metrics` or access V08. Next: launch the frozen train-only panel using the reviewed supervisor and fresh output root; continue without paid compute, external services, or protocol drift.
- Correction after that snapshot: hidden supervisor PID 42068 was launched on fresh ignored `chess_data/v29_fit_panel_dev01`; it passed the four-sample 2 GB gate and completed all 60/60 fits with return code 0 and no fit failures. The completed panel ledger SHA-256 is `b26504104ebde23967d142f01b3842b9e8309a2eb80337736e43c95f6c8f4d72`; its split/access fields report train-only and `locked_final_access=false`. The 160-block/320-game disjoint development evaluator was then launched hidden as PID 38260 to `chess_data/v29_development_matches_v01.jsonl`, with receipt `chess_data/v29_development_matches_v01.receipt.json`. It is in progress; do not inspect partial match outcomes or training metrics. No strength result is available yet. Supervisor status is `chess_data/v29_fit_panel_dev01.supervisor.json`.
- A 2026-10-02 targeted primary-source follow-up was added to `docs/RELATED_WORK.md`: Value-Guided JEPA, RC-aux, Temporal-Distance JEPA, VJEPA, and Agentic-JEPA. This raises the bar for value-, reachability-, temporal-, and multi-horizon-aware JEPA claims; it does not establish whether the narrower two-player perfect-information contribution is novel. A systematic citation search remains outstanding.

## Latest continuation delta (2026-10-02; V2.9 frozen probe implementation, pre-fit)

- User clarified the active target: iterate V2 until a JEPA workflow shows a reproducible advantage over non-JEPA baselines; V2 must demonstrate that comparison. User also instructed that every shell/PowerShell command run in the background/noninteractive so the desktop remains available. Continue to honor this for all command execution.
- V2.8 remains the latest measured outcome and did not show a JEPA advantage over task-value-dynamics. V2.9 is a **pre-fit exploratory test**, not a result or novelty claim. It changes only training duration from one to three epochs for each of the three matched arms, keeping train-only audited DEV09 data, model/loss/configuration, initialization seeds, optimizer, schedule, and shared search fixed. Because this change is only an optimization-exposure test, it is not by itself a unique algorithmic contribution or Q1 claim.
- The V2.9 amendment and panel spec freeze 60 fresh fits (20 seeds × 3 arms, 87 updates each) and 160 paired blocks/320 games on Connect4 gravity 6×7 and Reversi6. The match schedule SHA-256 is `0cc972d755154f047d66c4abcc926c543a6020d1f5f55fb1ea6f9834294c0d46`; it is separate from V2.8 and V08. The V08 confirmatory route is blocked in both the CLI and callable API.
- The selection screen is frozen in both the spec and analyzer: at least +0.05 JEPA−task-value on both games and macro; at least +0.05 improvement from V2.8 per game; hash-bound sum of fit wall seconds ratio ≤3.5; and planner CPU/game-seat ratio ≤1.25 in both games. Passing only nominates a separately reviewed model-selection study; it is not confirmation. Any failed screen stops duration-only tuning.
- Earlier preflight had reported the ignored `.venv` as Python 3.11.9 + NumPy 2.4.6, but on this continuation its launcher could not start because that base interpreter path is now absent. See the current correction above; bundled Python 3.12.14 / NumPy 2.3.5 is suitable for tests run here, not a substitute for the frozen research runtime.
- No 60-fit V2.9 panel or match has run. Pilot 01 aborted before model construction at 1,173,504,000 bytes RAM and pilot 02 at 1,322,954,752 bytes after a prior check had briefly seen 2,516,246,528; their ignored receipts are `chess_data/v29_fit_compute_pilot_01/pilot_status.json` and `.../pilot_02/pilot_status.json`. Pilot 03 passed after four 20-second-spaced free-memory checks between 2,127,196,160 and 2,708,635,648 bytes. A fresh `reply-jepa` seed-1009 train-only fit completed exactly 3 epochs/87 updates in 65.619 wall seconds / 60.469 CPU seconds, peak working set 859,336,704 bytes under its 1.3 GB and 600-second guards. This is compute-only feasibility; no strength/loss metrics were disclosed or used. Checkpoint SHA-256 `f1d45de6878abf62190aae53d5b2901c56f1db54630ad22899d1410ace89235d`; receipt SHA-256 `eb7459472dbeac6545d191f876f7562b3ff51f232e387996a32ab53acf270061`; source commit `c0a26a05184d5b2aa5c6a208cdf203b5ec2e9eda`. Panel fit is now ready to run under a new process-level memory/CPU supervisor, which is being independently reviewed.
- Protocol milestone `e857fdfaf812a992aac86f3f10ec90673ed4e334`, grant/preflight update `6812960039f4e8f9652087cc2881c9798f9f68d7`, runtime update `c0a26a05184d5b2aa5c6a208cdf203b5ec2e9eda`, and reviewed panel supervisor `03df5fb8075f8aad407cb100fdf5dc7bef696a3c` were pushed normally with remote hashes verified. Only `main` exists locally/remotely (`origin/HEAD -> origin/main`). Do not create another branch, force-push, or delete `main`.
- Obsidian Markdown mirror is `D:\notes\vault_1\Caissa-JEPA\`. The 2026-10-02 full-project sync copied 113 Markdown files with 0 SHA-256 mismatches; the latest sweep backup is `_sync_history/20261002-131727-v28-hardening-preflight/`. Earlier differing notes were preserved under `_sync_history/20261002-125123-v28-hardening-preflight/`, `_sync_history/20261002-125241-v28-hardening-preflight/`, `_sync_history/20261002-130458-v28-hardening-preflight/`, and `_sync_history/20261002-131023-v28-hardening-preflight/`. The Ground Truth was separately recopied and hash-verified after later status edits under the same authorized vault; the current app UI was not reopened after the user's request to keep the desktop free. Earlier visible Obsidian verification is recorded below. JSON panel specifications are not part of the Markdown-only mirror.

## Latest continuation delta (2026-10-02; V2.8 development match complete)

- User-directed objective remains to find a JEPA workflow that demonstrably beats strong, matched non-JEPA baselines before promoting a candidate. The completed V2.8 outcome is mixed and does **not** demonstrate that result. No current claim of JEPA superiority, broad transfer, opponent-specific behavior prediction, equilibrium/exploitability, algorithmic novelty, or Q1 readiness is supported.
- V2.8 development-only training completed 60/60 fits: 20 checkpoint seeds × `reply-jepa`, `task-value-dynamics`, and `direct-leaf`; all used DEV09 train only, one epoch, one shared matched recipe, and approval V04. The panel ledger is local/ignored at `chess_data/v28_fit_panel_dev01/panel.json`; dataset `training_approved` remains false and the locked-final split was not accessed. During a PowerShell summary check, the full panel ledger was inadvertently printed, including its training-only diagnostic fields. Those values were not used to choose a recipe, edit the method, or make the comparative inference; the current result is based only on paired match outcomes. Do not inspect/use those train diagnostics for future model selection. The separate seed-1009 resource pilot is not in this panel or any comparison.
- The exact disjoint `--development` schedule completed 160/160 paired blocks (320 games), two games (`connect4-gravity-6x7`, `reversi6`), two controls, 20 paired checkpoint seeds, with 2-second / 500,000-transition per-move caps, 0 forfeits and 0 censored blocks. Raw output and its receipt are ignored local files `chess_data/v28_development_matches_v01.jsonl` and `.receipt.json`. The verified hash-pinned summary and script are `docs/validation/V28_DEVELOPMENT_MATCH_ANALYSIS_V01.json` and `tools/v28_development_match_analysis.py`.
- Exploratory score difference is defined as JEPA's paired game score minus 0.5, averaging the two seat-swapped games and then the two match seeds within each checkpoint seed. Macro-averaged over the two game strata, JEPA vs task-value-dynamics was **−0.01875** (unadjusted 95% seed-cluster t CI **[−0.08248, 0.04498]**); Connect4 was −0.0125 and Reversi6 −0.025. Vs direct-exact-leaf it was **+0.0875** (CI **[−0.00947, 0.18447]**); Connect4 +0.1875 (CI [0.03625, 0.33875]) and Reversi6 −0.0125 (CI [−0.13536, 0.11036]). There are 20 seed clusters; intervals are unadjusted and the 160-block schedule is exploratory, not powered confirmation. Positive estimates occur on Connect4 vs direct-exact-leaf, while the task-value-dynamics macro estimate is negative and Reversi6 has no observed edge. The intervals are conditional on the two scheduled match seeds per cell and do not separately estimate match-seed or situation-sampling uncertainty.
- Same planner and per-move caps do not imply equal realized compute. The summary records decision calls, model evaluations, game transitions and measured wall/CPU time by game/control/arm. Interpret this as fixed-checkpoint strength under a shared two-ply minimax planner, not opponent-behavior prediction, equilibrium or exploitability. Independent `gpt-6-luna/high` review initially found incomplete panel binding and absent semantic score replay; both were fixed with exact seed/arm coverage, artifact/run-identity hashes, pinned evaluator/rules sources, legal transcript replay and terminal utility checks. Final re-review found no P1/P2; the analyzer also passed over the actual 60-fit ledger and 160-block match artifact. Reviewer did not inspect or use training diagnostics.
- Fresh cache benchmark under grant V04 passed: full DEV09 replay/audit 47.239 s, second in-process train/validation split access 0.034 s, with 1,797 train and 619 validation records and consistent identity. Approval V03 is stale after the loader change and is retained unchanged; V04 SHA-256 is `fa05ebe2d23e24c68165e9da30482c5d35705e25e92ff23673fa65f3d59afa86`.
- V2.8 tests passed 90/90 after cache hardening. Full repository regression previously ran 416 tests: 396 passed, 20 legacy GUI/trainer errors from missing `PySide6` in the selected Python runtime. The development fit and match completed successfully; these results are not evidence of model quality. Cache milestone commit `aaccbf1f62c18b5ffa0426e421529685aed99e27` is pushed to `origin/main`; at that point local/remote branch inventory contained only `main`, and the working tree was clean. New analysis/doc changes in this continuation are not yet committed.
- The fresh primary-source search recorded policy-aware simulator learning (Dann et al., arXiv:2605.29032v3) and ICML 2026 latent-space value alignment in `docs/RELATED_WORK.md`. This raises novelty risk for generic adversarial or value-weighted prediction; it does not establish novelty for CAISSA. Broader backward/forward-citation review remains outstanding.
- The next proposed work is a new pre-fit versioned development amendment/spec to test whether one epoch underfits: a three-epoch matched fit for every arm, changing duration only, with a new exploratory schedule, explicit selection/stopping rules and measured-compute report. Do not start that fit until its spec/approval and reviewer gate are frozen. If JEPA still does not improve over task-value dynamics in both games at acceptable cost, redesign or narrow rather than continue blind duration tuning. Keep the V08 schedule unopened.
- User decisions still in force: use Computer Use/Obsidian as project memory; only keep `main`; commit completed verified milestones and push them normally to GitHub; no force-push/history overwrite; preserve untracked/ignored data, checkpoints and logs; keep shell/PowerShell work noninteractive/in the background so the desktop remains free. Agent use must follow the user-approved model/effort; `gpt-6-luna/high` was approved. No external purchase, paid compute, restricted data, account or third-party contact is authorized.
- Repo root is `C:\Users\ANHKHOI\Documents\ChatGPT\caissa-jepa`; remote is `origin` at `https://github.com/dakiemdarktharr/caissa-jepa.git`; discovered Obsidian vault/project folder is `D:\notes\vault_1\Caissa-JEPA\`. On 2026-10-02 the updated project Markdown was copied to the vault with 112 files, 0 SHA-256 mismatches, and 4 differing prior files backed up (no deletions) under `_sync_history/20261002-114156-v28-hardening-preflight/`. The Obsidian UI was not reopened during this latest work to preserve screen availability; prior visible verification and vault readability are documented in the history below, and current on-disk hashes were verified.
- `ROADMAP.md` now gives the next gates. Existing V1/V2 method notes, historical validation records, related work, and restrictions below remain original sources; older continuation snapshots are historical and are superseded by this section.

## Historical continuation snapshot (2026-10-02; pre-panel V2.8 development gate hardening; superseded above)

- User-directed V2 target remains strict: demonstrate JEPA advantage over matched non-JEPA baselines before promoting a candidate. V2.8 DEV09 fits/matches are only exploratory development/model-selection evidence; no superiority, transfer, equilibrium, exploitability, novelty, or Q1-readiness claim is supported.
- Re-reviewed DEV09 fit-gate code after independent review found receipt-hash, ledger, and model-to-ledger binding gaps. Current code binds the grant to the exact `chess_data/v28_data_dev09` path and pinned manifest/source/dataset/audit/records/trajectories hashes; validates every frozen panel field; forces the hash-pinned 160-block development schedule and inference budget; verifies `effective_run` against the trainer's canonical `run_config_sha256`; requires a completed 60-row `panel.json` ledger; and binds every model checkpoint and receipt path/hash to that ledger. The user-approved independent reviewer (`gpt-6-luna/high`) reports no remaining P1/P2 in the supported CLI/API path. Hard-interruption reconciliation is not implemented; partial ledgers are preserved and a retry must use a fresh output root.
- Focused V2.8 regression passed 41 tests after the receipt/ledger hardening, and the broader V2.8 suite passed **90/90 tests in 25.693 seconds** after the replay-cache change. The independent `gpt-6-luna/high` reviewer found no P1/P2 in the matcher gates or cache/data path. Full repository regression ran 416 tests in 160.890 seconds: 396 passed and 20 errored because the selected Python runtime lacks `PySide6` for legacy GUI/trainer setup tests. No V2.8 test failed. Final compile and diff checks after the cache change are recorded in the latest check logs.
- Before the fresh V03 grant below, no approval or training fit existed in this continuation. One compute-only fit later completed as described below; it is not comparative evidence. The default ignored DEV09 approval at `chess_data/v28_data_dev09_approval.json` is stale after source/specification changes and is retained unchanged. V03 model-blind proxy remains an incomplete prefix, unrelated to the V03 grant artifact.
- After the hardening commit was pushed, grant attempts found existing stale ignored approvals V01 (SHA-256 `eb80a6f6c745814c0acac9f77eabe50d2cac988e5d8cfda592fdbde864cd2268`) and V02 (SHA-256 `ce5c2e110aacb6add2b6636f5ef175df289410749c8a4aaab3a2185795f35545`); both are retained unchanged. Development-only V03 was issued at `chess_data/v28_data_dev09_approval_v03.json` (SHA-256 `9fd9ed50786a3bfa2db240e27e963e8948a1a07eaa60dc7a73014732a7ce7733`). Its pre-cache replay preflight passed for 1,797 train records and DEV09 fingerprint `cf1f408356058eae5224249010008c47a23a6d8f2a8c8530990388cc179b8c40`. V03 is now stale after the reviewed hash-keyed replay cache; retain it unchanged and issue a fresh grant after committing this version.
- Compute pilot attempt 01 stopped at argument parsing (wrong positional CLI syntax); it created no checkpoint or receipt and was retained at ignored `chess_data/v28_fit_compute_pilot_01/`. Pilot 02 completed one `reply-jepa` train-split fit with seed 1009 (outside the 20 panel seeds) and one epoch. The monitor recorded 74.428 seconds wall, 790,220,800-byte peak working set, BelowNormal priority while running, and no memory/time guard trigger. Checkpoint and receipt exist under `chess_data/v28_fit_compute_pilot_02/`. The trainer stdout/receipt includes loss diagnostics, but those were not inspected for selection; this is a resource feasibility attempt only, not a comparison or evidence of advantage. The next panel has not started.
- Working tree contains the uncommitted V2.8 development authorization/matcher/panel changes plus earlier uncommitted V2.8 trainer/docs changes. Branch inventory at continuation start was local `main` and `origin/main` only, both at `186f14a4f098c4e78ed2a50abaadaa5bad0a0cd3`; remote is `origin` at `https://github.com/dakiemdarktharr/caissa-jepa.git`. Do not commit/push until full regression and final review complete.
- User's latest UI instruction is to run shell/PowerShell commands hidden in the background. Obsidian vault path is the previously discovered `D:\notes\vault_1\Caissa-JEPA\`; the desktop Obsidian page was not reopened in this continuation to keep the user's screen free. Earlier hash verification and visible reading are recorded in the history below. Mirror this new continuation delta after the milestone is stable.
- Protocol hardening commit `5f2c7535107e0815849d5960c2728d4c2178df25` and Ground Truth preflight commit `3734cb1acd30a46fb07a62753613c2e1d3e558bb` were pushed and verified on `origin/main`; only local `main` and `origin/main` remain. The Obsidian mirror at `D:\notes\vault_1\Caissa-JEPA\` has 112 Markdown files copied with zero hash mismatches; three differing prior vault files were backed up under `_sync_history/20261002-105244-v28-hardening-preflight/`. The UI was not reopened to preserve the user's screen. Cache review and 90/90 V2.8 tests are complete. Next: commit/push the cache update, issue a fresh grant, benchmark repeated loader calls in one process, then launch the frozen 60-fit panel at below-normal local priority with monitoring. Do not read V08 outcomes.

## Continuation delta (2026-10-01; follows the earlier latest-session delta)

- The targeted search updated `docs/RELATED_WORK.md` and `ROADMAP.md` with a decision-focused prior-art comparison and stronger JEPA falsification panel. Initial interim Obsidian sync hashes and superseded vault copies are retained in the dated `_sync_history/2026-10-01-v28-v03-lit-update*` folders; see the latest verified sync record below for current files.
- The Obsidian app UI was not reopened during this continuation because the user asked that the desktop remain available. Disk-level readability and hashes are verified; current in-app visual verification is not.
- User's latest operating instruction: all command/PowerShell-like work should run in the background so the desktop remains available. Continue honoring the earlier authorization to use only `main`, push completed work normally, mirror project Markdown into the Obsidian vault, and continue V2 until a credible research outcome; do not spawn self-created agents unless the user approves model and effort. The user approved `gpt-6-luna/high` for agents created by us, but no agent was needed for this continuation.
- Resumed V03 supervisor status was `running`, heartbeat `2026-10-01T12:08:03Z`, elapsed wall `751.218 s`, temporary artifact 12,805,029 bytes, and runner CPU approximately 719.28 seconds. Supervisor PID 21940 and runner PID 52724 were alive; stdout/stderr were empty. No terminal receipt/result existed at this observation. A rising temporary JSONL is progress only and is not evidence about learned models.
- Follow-up at `2026-10-01T12:12:49Z`: supervisor status still `running`, heartbeat current, elapsed wall 1,036.546 seconds, and supervisor-reported artifact bytes 17,880,073. The supervisor JSON still binds the same source and schedule hashes. Direct process enumeration was denied by Windows access control during this check, so current liveness is inferred from the advancing atomic heartbeat; no final artifact/receipt has been observed. Do not treat this as a completed run.
- Targeted primary-source search added a planning-benefit/objective-alignment section to `docs/RELATED_WORK.md`, based on official NeurIPS proceedings for reward-free offline latent-dynamics planning and PLSM, official ICML/PMLR DINO-WM, and the primary MuZero source. The update sharpens the experimental design: latent prediction error is not a proxy for strategic improvement; compare JEPA with same-backbone policy/value, task-prediction dynamics, recurrent consistency, feature-transition, and exact-state controls at equal updates and equal measured compute. The strongest matched task-prediction control is a kill gate. This is a literature/design update, not a result or novelty claim.
- A further deep search verified Kubíček & Lisý's LAMIR as an ICLR 2026 paper using joint-action latent game dynamics, legal-action/termination/reward prediction, learned information-set abstraction and depth-limited solving. It reports lower exploitability than RNaD on small games under sufficient capacity and up to 80% head-to-head versus RNaD on large games; the large experiment used substantial GPU/CPU resources. This is a close learned-model/game-theoretic precedent but not JEPA, and its abstraction primarily addresses imperfect-information state growth absent in CAISSA's core. The task-value-dynamics arm is a compact non-JEPA control, not a LAMIR replication. No CAISSA result has been observed. Full comparison and scope are in `docs/RELATED_WORK.md` and `ROADMAP.md`.
- At the `2026-10-01T12:18:35Z` observation, V03 remained `running`; supervisor elapsed wall time was 1,382.5 seconds and its output byte counter was 23,742,975. Heartbeat and the same code/schedule hashes were current. This remains only an exploratory proxy run; wait for terminal verification before evaluating its runtime/variance gate.
- Obsidian sync subsequently completed for the latest Ground Truth, Roadmap and Related Work files in `D:\notes\vault_1\Caissa-JEPA\`; all three read back as non-empty Markdown and matched their repo SHA-256 at copy time. Roadmap hash `49DC1A68544B4BF9D260009A728E1F5AC4D7C7BDE1F28F05C93F376A3A12ED9D`; Related Work hash `A0EA8E778B37603E807CE848E92E3C291EA518369B44DACDE21DDB54B0BEF328`; the corresponding Ground Truth hash at that sync was `DE07A091C221C3D9D38A9E21BE0AD24CFD496A72549B8B0657BE7876696AC04D` before this sync-record line was added. Previous versions are preserved in `_sync_history/2026-10-01-v28-v03-deepsearch/`.
- The professor briefing `docs/PROFESSOR_BRIEF_V2.md` now begins with a current V2.8 status: no V2.8 model/checkpoint/result exists; the current run is only a proxy feasibility pilot; the learned-model superiority hypothesis and exact scope are stated explicitly; transfer is marked as a separate, unproven objective. This is a proposal/status note, not a positive-results paper.
- At `2026-10-01T12:33:34Z`, V03 was still `running`; elapsed wall was 2,281.4 seconds, 1,830 JSONL lines including the manifest, and runner CPU 2,043.6 seconds. Both runner and supervisor heartbeats were current and the runner remained at `BelowNormal` priority. A temporary hidden audit process (PID 18696) is waiting for terminal status, then will check receipt/fingerprints/schedule and independently replay every completed block into ignored `chess_data/v28_modelblind_proxy_v03_independent_audit.json`. The script does not edit source or data; its result is a proxy audit only, not learned-model evidence.
- Documentation commit `81e6f9e20839d625e34c83cf3860b8532da9724e` was pushed normally to `origin/main`; local `main`, `origin/main`, and `git ls-remote` agreed, with only main branches present at verification.
- The latest Obsidian sync also copied `docs/PROFESSOR_BRIEF_V2.md` and this Ground Truth into `D:\notes\vault_1\Caissa-JEPA\`; both hashes matched their repo versions at copy time and both opened as non-empty Markdown. Professor briefing SHA-256 is `80A3304A98BAC293228CC9387BBE4E809CB16E83460F7317DF69F3BC81401D0C`; Ground Truth matched SHA `5E7C33690B1FEC3AD53BF3EB33E1BB77C2FCB2B72A4A9B988B2B9545F875BA2B` before this sync-record line. Pre-update copies were preserved in `_sync_history/2026-10-01-v28-v03-professor-update/`.
- Because V03 depends on fixed code fingerprints, only documentation was changed during the run. Before declaring any pilot outcome, independently inspect supervisor terminal status/receipt/source fingerprints, parse the full output, replay every block, and calculate the predeclared runtime/variance gate. Even a pass is infrastructure feasibility only; it does not approve production training or establish JEPA superiority.

## Latest session delta (2026-10-01; overrides conflicting status below)

- The reviewed supervisor/document milestone is committed on `main` as `05246a165ce11d47bec18b87e619663fa605bf9d` (`Harden model-blind pilot supervision`) and was pushed normally. `git ls-remote` confirmed `origin/main` at the same hash; only local `main` and `origin/main` are present, and the working tree was clean at launch.
- The evaluator milestone (`1da7104`), evaluator publication record (`6c0afd5`), V01 partial audit (`078c91e`), and V02 launch record (`0918d3d`) were pushed normally to `origin/main`. V02 stopped abnormally after 616 of 9,600 proxy blocks. The preserved ignored partial is `chess_data/v28_modelblind_proxy_v02_current.jsonl.partial.jsonl` (12,637,953 bytes; SHA-256 `B0EDD59C509EFD4DA4C970F76A06740E843FDA50F82CE8086A2EF897C17DA9C0`); all 616 rows pass current replay/schema checks and form the exact schedule prefix. There is no final artifact or receipt. Its 552-byte stderr is a truncated traceback with no exception type/message; watchdog status is stale and terminal capture is incomplete. The cause and which process stopped first are unknown. Preserve V02 and V01 without resuming/appending. Full evidence and limits are in `docs/V28_MODELBLIND_V02_INTERRUPTION_AUDIT_01.md`. No runtime/power gate or JEPA effect is established.
- A fresh V03 9,600-block proxy pilot is running under hidden supervisor PID 21940 and runner PID 52724. It writes only to ignored `chess_data/v28_modelblind_proxy_v03_current.jsonl`, with a 14,400-second user-CPU Job Object limit and 15-second atomic heartbeat. Runner SHA-256 is `8aabca47ae6835666acd7d2b6ac5373c8b0f7c8c1808102811f09b90d88669be`, selected schedule SHA-256 is `80a5f741c6bf94e4fb93664e503158a91e959c28015b45e2a9ba9d28e4fe084f`, and code fingerprint SHA-256 is `e76b61442998c07676243b686637064858ed16fdb902a3fa759152fba04930de`. It is exploratory proxy-policy runtime/variance work, with no learned models or JEPA estimate. Preserve V01/V02 unchanged and do not use smoke/pilot rows as learned-model evidence.
- Added `tools/v28_modelblind_pilot_supervisor.py` with a hidden child runner, Windows CPU Job Object, collision-safe preflight, periodic atomic heartbeat, and terminal artifact/receipt/schedule/source verification. The final code fingerprint includes the supervisor, pilot entry point, and policy/rule dependency modules; it records Python and NumPy versions and fails closed if source changes during a run. After independent review found four P2 gaps, they were fixed and reviewed again. The revised supervisor completed an 8-block nested-path smoke run. All 8 records replay and terminal sidecar/receipt/artifact identities agree; artifact SHA-256 is `b692d7a9c717a2282f205f59fb46db1a8e6a472a5e8ecd45d6d81ade8f6ffecf`, selected schedule SHA is `6340b946050e708fbcec597bd05b5b7b802dcfa30b50c9a9ff111ffecd548f2b`. The focused supervisor/evaluator/analysis/power suite passes 24/24; independent supervisor review found no remaining P1/P2 in its code/test scope. See `docs/V28_MODELBLIND_SUPERVISOR_REVIEW_01.md`. Smoke evidence is lifecycle verification only, not a runtime/power gate. The Windows Job Object accepted the smoke child, but its time-cap behavior was not separately tested. A full 9,600-block pilot has not restarted.
- The learned-match evaluator and analyzer are prefit infrastructure only. Independent review also caught a P1 in the analysis handoff because it did not enforce its frozen source hash; this is now fixed by independently validating the wrapper, raw artifact fingerprint, row manifest, generator, protocol budget, and analyzer source before consuming outcomes. Evaluator replay validates successful moves and accounts for failed attempts. The approved reviewer used `gpt-6-luna/high`: the combined evaluator/analysis/power suite passed 19/19, both CLI help checks and timeout-forfeit replay passed, and evaluator/analyzer independently loaded all 9,600 locked rows with the same raw SHA. No P1/P2 remains in the reviewed integrity path; no real outcome exists for end-to-end statistical analysis. See `docs/V28_MODEL_MATCH_EVALUATOR_REVIEW_01.md`.
- A targeted primary-source deep-search refresh on 2026-10-01 added Zhang et al.'s V-JEPA Policy preprint (submitted 2026-09-29) and Terver et al.'s JEPA-world-model planning ablation study v4/TMLR to `docs/RELATED_WORK.md`. V-JEPA Policy couples future-latent prediction to an action expert for continuous robot control; the TMLR study explicitly separates model, objective and planner effects. Both strengthen prior-art and ablation requirements, while neither tests alternating two-player zero-sum games. Generic action-conditioned latent prediction, predicted-latent action generation, and latent planning remain non-novel claims; the game-specific incremental benefit is still unverified.
- The local `py -3.9` runtime remains syntax-check-only because it has no NumPy. The bundled workspace Python 3.12.14 has NumPy 2.3.5; with it, the focused supervisor/evaluator/analysis/power suite passes 24/24, and the 8-row nested-path supervisor smoke artifact replays against its exact generated schedule. No project-data fit or learned match has run.
- Full repository discovery in that bundled environment ran 407 tests and ended with 20 errors. The errors arise from PySide6 being unavailable or incomplete in this runtime (`ModuleNotFoundError` and Qt dummy-stub imports), affecting GUI and unrelated legacy trainer tests. The focused V2.8 evaluator/power/supervisor suite passes as recorded above; no package was installed.
- The model-blind 9,600-block proxy runner is no longer running. The ignored `.tmp` has 4,839 parseable JSON records: a manifest plus 4,838 exact schedule-prefix rows, with no duplicates or missing prefix IDs. Independent audit verified 4,837/4,838 rows after supplying obsolete implied schema fields; one reversed-tape Connect4 opponent-timeout row lacks `forfeit_details` and is unverifiable. Runner-source hash differs from current code; there is no receipt/final file and no watchdog completion report. The 2,400 clean independent-tape Connect4 blocks have descriptive mean `d=-0.00917`, SD `0.30114`; the 2,399 valid reversed-tape blocks have `d=+0.00917`, SD `0.30120`. Their near-opposite values reflect same-policy self-play/tape relabeling, not a JEPA effect. Reversi has only 38 prefix rows and is insufficient for runtime/variance inference. Preserve the artifact unchanged; do not resume or count it as a completed gate. Full audit and SHA values are in `docs/V28_MODELBLIND_PARTIAL_AUDIT_01.md`.
- Locked learned-model matches have not run: DEV09 remains unapproved for training, no project-data checkpoint exists, and no JEPA superiority claim is supported. The evaluator's paired score is conditional on the fixed trained checkpoint panel and tested game initial states; it does not measure opponent behavior, equilibrium, exploitability, cross-game transfer, or general game strength.
- The Obsidian mirror remains `D:\notes\vault_1\Caissa-JEPA\`. Eight prior project-note copies were preserved under `_sync_history/2026-10-01-v28-v02/`; their SHA-256 values are `CDC5729EBB1E8CC8C5E6053ACF4200651A05D72F8189D96EE76EC321DF76B47F`, `89776DAFEB4D9C541C4BBC43BD60B9A6E936D7704453FC601E72E83B6B933691`, `2AB5EF6395BC36C4FE3E9B808D19819DA6459259DA32F54F513894F14859A442`, `7917A2764B98FA5EB1CB292AFA257DBD4585861B8F5489086FC884385DDF21C2`, `E0496B7B57FFE69A7BB73544FD274CE18CAB8A916C35A3F80EB9E3B645D01F1B`, `A0D90029938E9EDC49F12527AF524B76834ED5BDFF78AB43EFDFD0CE489831DE`, `359D827699CAE72D64520578F4626D545EA3911C362BB567F96D844AEC90613C`, and `29C2EB1730FAA3444D230B4F66DFF196FBDF3A2CBF6750F885CB43F2AAC151B1`. The current Ground Truth and `docs/RELATED_WORK.md` were refreshed and hash-verified after the deep-search update. All 110 current project Markdown files were mirrored with zero mismatches; the vault has 221 Markdown files including those eight preserved copies. Ground Truth, Roadmap, interruption audit, supervisor review, and related-work review are readable from disk. Vault-only notes remain untouched; interrupted and smoke-run JSONL artifacts/logs are not mirrored. Computer Use initialization failed with `failed to write kernel assets: The system cannot find the path specified`; the vault had been opened and verified in an earlier session. Shell commands are run hidden/in the background at the user's request so the desktop remains available.

The following older “Current verified state” text records earlier milestones and contains interim statuses that this delta supersedes. Use the dated continuation records and the latest delta above for current worktree, runtime, reviewer, and pilot status.

## Current verified state (2026-10-01; refreshed after DEV10 root-oracle pilot)

- The V2.8 paired-match protocol milestone is committed and pushed to `origin/main` as `fc2612a3ca348bdcc4c9e015d1401933bc8ba268`; the verified branch inventory contains only local `main` and `origin/main`, and the working tree was clean after push. No branch was created or deleted.
- The last environment-complete full regression passed 381 tests in 128.652 seconds before the V08 analysis additions. In the current available Python runtime, all 45 V2.8 tests pass and all 18 focused V08 power/analysis/model-blind tests pass. Root discovery ran 371 tests in 162.177 seconds but ended with 20 errors because PySide6 is unavailable in that Python 3.14 runtime; NumPy is available. No dependency was installed. Logs remain in system temp, outside Git.
- The corrected model-blind exact-oracle gate passed for gravity Connect4 4x5 (100/100 exact maps; 72 variable labels; 53 beyond-depth roots) and Reversi6 (150/150; 54; 54) under 200k nodes, 2 seconds, and 500k cache entries. This establishes feasibility only.
- V2.8 DEV01–DEV04 failed model-blind split/support gates. DEV05 used 96 candidate episodes per game/split and wrote trajectories only, but its original support-floor check was defective: it inspected only empty locked-final. The recorded Connect4 counts were train 9/2 records, validation 4/20, selection 9/26; it also reported seat-coverage failures and one quarantined mixed-family component. Independent review invalidated its pass status. DEV01 and DEV02–DEV05 diagnostics and hashes are retained in `docs/validation/`; local full trajectories/manifests remain ignored under their matching `chess_data/v28_data_dev*/` folders. No model-facing records were published.
- The implementation now checks support floors inside each game/split, regenerates each trajectory from required source split/seed/episode/policy hashes, locks generation to named quota/seed protocols, preserves duplicate family lineage before component quarantine, and withholds records on any failure. Tests cover support floors, regenerable lineage, component assignment, duplicate paths, and fail-closed publication. The stochastic positional policy remains an explicitly versioned softmax over a standardized heuristic.
- DEV06's reported pass is excluded from fitting because it did not enforce exact splits. DEV07 stopped before output on valid Reversi passes. After correcting both plus the reviewed threshold override, DEV09 (`dev09-v1`, schema v09, seed `28094007`, quota 48, exact ordered train/validation/selection, phase `1/3`) passed full prefit data audit for Connect4 6x7 and Reversi6. It produced 3,531 records across 284 unique trajectories; train/validation/selection support is C4 `72/24/44` trajectories and `307/128/139` records, Reversi `72/24/48` and `1490/491/976`. Independent replay and artifact/source SHA checks matched receipt `docs/validation/V28_DATA_SPLIT_DEV09.json`. Raw files/manifests remain ignored in `chess_data/v28_data_dev09/`. Training is not approved and no model was fit.
- DEV10 extended the model-blind exact-root gate to Connect4 gravity 6x7. It used five scheduled roots at plies 5–11, 500,000-node/500,000-cache/two-second root budgets and an independent reference-rule differential. Rule checks passed 5/5; the oracle returned complete root action maps for 0/5. This is a budget-specific feasibility result, not proof that 6x7 exact labels are impossible. Method V05 and protocol V08 pivot the primary endpoint to paired color-swapped complete-game score.
- Protocol V08 defines a fixed panel of 20 checkpoints, 120 unique match seeds per checkpoint/game/control, a +0.05 practical score margin, stratified standard errors, one-sided boundary tests with Holm correction, simultaneous bounds and explicit timeout/replay failure rules. `tools/v28_match_power.py` produces 9,600 paired blocks; the commitment receipt binds schedule rows, generator and analysis hashes. In the conservative scenario (SD .50, effect .10, margin .05), planned 2,400 blocks give marginal power .9961 per control and a dependence-free joint lower bound .9921. The independent method reviewer verified these values, hashes and schedule, with no P1-or-higher blocker. The matched-game evaluator and four-hour nonlearned runtime/power gate have not run.
- No V2.8 JEPA or matched baseline has been trained; no V2.8 checkpoint or JEPA-over-baseline result exists. DEV09 remains prefit data-feasibility only; `training_approved` remains false. Training is blocked on evaluator implementation, nonlearned schedule/runtime/power, and independent review. No claim of superiority, verified novelty, cross-game transfer, exploitability, or Q1 readiness is supported. A dataset pass alone does not authorize training.
- Primary-source review identifies critical novelty risk for generic action-conditioned/joint-action JEPA, opponent-state prediction, and imagined self-play. Deep Latent Competition and MA-JEPA are recorded in `docs/RELATED_WORK.md`; the reply-set JEPA/minimax gap remains unverified.
- Obsidian vault is `D:\notes\vault_1\Caissa-JEPA\`. This session copied 110 project Markdown files preserving relative paths and verified zero SHA-256 mismatches; `GROUND_TRUTH.md` exists there and reads successfully. The vault had been discovered and opened in Obsidian in the prior verified session; this session did not foreground its UI so the user's desktop remained available. User requires hidden/background shell commands, only `main`, preservation and normal push of completed changes, Obsidian as project memory, and no paid services, restricted data, unapproved licenses, or external contact.

### V2.8 model prototype audit and V02 separation (2026-10-01)

- The V02 implementation milestone is committed on `main` as `70025d54d6ff4669771e23b7a66e520a8080dff0` (`Add supervised reply-set JEPA V02 prototype`), pushed normally to `origin/main`, and the remote `refs/heads/main` hash was verified equal. The branch inventory still contains only local `main` and `origin/main`; no other branches were created or deleted. The commit passed focused and complete V2.8 test suites and the independent V02 implementation/method review. Generated proxy output remains ignored and is not part of the commit.
- Independent review found two implementation bugs, now fixed: terminal H2 examples crashed value training rather than taking exact terminal utility, and non-unit JEPA weights incorrectly scaled observed-H2 gradients. Observed H1/H2 states are now replay-validated. A second independent review judged the separate supervised V02 question defensible for the paired-match endpoint, with required additional coverage.
- Frozen `docs/METHOD_V28_PLANNER_V01.md` remains unchanged. The implementation does not implement V01's KLENT policy/Q improvement and alternating lambda-return objective. The new `docs/METHOD_V28_SUPERVISED_V02_AMENDMENT.md` explicitly versions the code-aligned behavior-action CE + root-outcome MSE + observed-H2 value loss + complete reply-set JEPA candidate. It is a prefit draft, not independently signed off or frozen. KLENT is secondary only; V08's primary contrast remains the candidate against both task-value dynamics and direct-leaf controls. No model was fitted and no checkpoint or learned result exists.
- Focused model and model-blind runner tests pass 18/18; after adding the train runtime, all current V2.8 suites pass 67/67 in the available runtime. Coverage includes a terminal H2 record from Reversi self-play; planner exact scores for terminal win/loss/draw cases and their color-swapped roots; nonterminal branch-value invariance under color/role swap; forced Reversi pass as both root action and opponent reply; mismatched H1/H2 rejection; finite differences for every parameter tensor/bias across all three arms, including JEPA weights 0, 0.5 and 1; shared-loss invariance and EMA-target immutability; deterministic train-epoch fixture behavior; explicit manifest-approval refusal; and SHA-256 dataset/audit/run-config plus train-split checkpoint identity. These are engineering checks, not evidence of strength. Independent V02 method/code review found no P1 finding before the final nonterminal symmetry test; the recorded P2 perspective coverage gap was addressed by that test.
- New `two_player/v28_train.py` and `tests/test_v28_train.py` are currently uncommitted. The runtime uses only `load_split(..., "train")`, which rejects DEV09 while `training_approved` is false; the flag was not changed. It seeds each epoch shuffle deterministically, writes optimizer/model state atomically at epoch boundaries, and requires exact dataset/audit/objective/code/model/run-config identity to resume. The independent review of these new runtime/checkpoint changes is pending. No fit or checkpoint was produced.
- The 9,600-block model-blind proxy run remains active as an exploratory runtime/paired-variance diagnostic, not a JEPA test. It was launched from source before the latest runner/model validation edits. At the last check process 46188 had used about 3,338 CPU seconds and streamed 51,735,729 bytes to the ignored partial file `chess_data/v28_modelblind_proxy_v01_full.jsonl.tmp`; a hidden watchdog will stop it at four CPU-hours and preserve partial output if it has not completed. Its 19,200 games compare project-owned bounded-search self-play under two tie-randomization pairings, not learned arms. The V08 runtime/power gate is therefore still pending.
- No current full-suite run has been repeated after these files were added. The available Python 3.14 runtime previously lacked PySide6 and the broad suite exited with 20 GUI-related errors; a historical environment-complete 381-test run predates these changes.
- The Obsidian vault remains `D:\notes\vault_1\Caissa-JEPA\`. The source has 112 project Markdown files. The latest hidden Python mirror pass copied all 112 preserving relative paths; SHA-256 verification found zero missing/mismatched files and confirmed Ground Truth, the V02 method amendment, and its review note. Existing vault content was not deleted. The vault had previously been opened and verified in Obsidian; keep the desktop UI free during background shell work.

The continuation paragraphs below are historical. Later dated entries supersede their interim branch, test, novelty, data, and gate status.

**Historical continuation state (2026-09-30):** canonicalization, exploratory pilot receipt,
and initial novelty re-audit were committed on `main` as
`cc3cb127819ac8e9a24446f7a02fc748e6d4cb06`; publication status was recorded in
`8796a8f5fe9d027db06a339fc6e9563aeead7b91`. Both were pushed fast-forward and
the latter matched the remote SHA at verification. Current working-tree changes
extend the prior-art audit with Athénan, *Minimax Strikes Back*, AAAI-25
Markov-game abstraction, board-game transfer, PCZero and ICML-26 regularized
game learning, and revise the candidate's model-blind gate. This documentation
milestone was committed as `cfb709fd00612d02c3459252c508f5b7ea71ef52`, pushed
normally to `origin/main`, and verified against the remote SHA. The latest
documentation copy was synced to Obsidian. The focused search suite passes 5 tests; full
regression passed **330 tests in 150.012 seconds**.
An independent review using the user-approved gpt-6-luna/high configuration
found no blocking finding. The previous Obsidian sync contained 78 Markdown
files with matching hashes; it needs refresh after these latest edits.
The latest pilot is exploratory only: 32
receipt rows over two seeds took 51.19 seconds; shallow search beat each sanity
opponent 4/4 in sampled pairings. Identical-policy Reversi self-play has only
two unique trajectories (the seat-swap rows duplicate each game): V2 had
minus-seat wins 2/2, and the canonicalized version plus-seat wins 2/2. Seat
effects remain unresolved. Reversi node-cap hits fell from 116 to 68, but
match trajectories and search calls changed, so this is not an efficiency
claim. No JEPA model has been trained and no JEPA-over-baseline result exists.

Independent review found (a) duplicated identical-policy self-play rows being
too easily read as four independent games and (b) no explicit assertion for the
four tied canonical maps on the symmetric initial Reversi board. Documentation
now reports two unique seeds/trajectories, and the focused test asserts the
four-map case. Reviewer found no canonicalization defect, receipt hash mismatch,
or commit-blocking fairness issue. The updated focused suite passes 5 tests in
0.621 seconds; full suite passed 330 tests in 150.012 seconds immediately before
that assertion-only test edit.

The 2026-09-30 prior-art re-audit adds Deep Latent Competition, the recent
MA-JEPA preprint, AAR/AI's learned ranking/value/search combination, and
Athénan (JMLR 2026), a direct two-player perfect-information zero-sum game
method using tree-bootstrapped value learning with minimax. Athénan reports
strong results across Go, Hex, Othello, Arimaa and other games, so it is a key
non-JEPA baseline. Its AAMAS 2023 follow-up *Minimax Strikes Back* compares
Athénan with Polygames/AlphaZero and reports much lower state-data generation
cost in its setup. Generic opponent-action-conditioned latent prediction or
tree-state supervision is not a novelty claim. The only retained candidate is
complete legal-reply-set prediction plus a separately evaluated minimax
action-order objective; distinctness is unverified, oracle feasibility is not
passed, and training is not yet justified by evidence. Approximate zero-sum
Markov-game abstraction and direct game/variant policy-value transfer are also
prior art, so neither latent compression nor transfer alone is a contribution.
Before coding or fitting, the next gate is a source-level design and measurable
comparison that distinguishes this candidate from Athénan-style tree-value
learning, minimax-Q/abstraction, direct policy-value transfer, and task/feature
prediction at matched compute. If no fair incremental claim survives, stop or
pivot to a benchmark paper. Any future method comparison must include these
controls. See
`docs/V27_PRIOR_ART_REAUDIT_20260930.md` and
`docs/V27_RESEARCH_POSITIONING.md`.

The preceding committed V2.7 positioning milestone passed 325
tests in 128.753 seconds on Python 3.11.9. The targeted primary-source review
now also records the distinction between learned opponent-behavior models
(He et al., ICML 2016), game-theoretic robust MBRL (Rajeswaran et al., ICML
2020), fixed-suite match estimation, and worst-case/equilibrium planning. See
`docs/V27_RESEARCH_POSITIONING.md`. This milestone still contains no trained
JEPA or superiority evidence.

The V2.7 positioning and bounded-search feasibility milestones are commits
`c71d97a85d3218569f25e39cadfc7ccc410d9631` and
`59b7698093809f0e90934c4934975876842158dc`, respectively, both pushed to
`origin/main` and verified against remote SHAs. Only local `main` and
`origin/main` remain; the working tree was clean after the latest push. The
Obsidian mirror at `D:/notes/vault_1/Caissa-JEPA/` then contained 77 project
Markdown files. That count describes the prior sync only; the current
continuation refresh and final hash verification are tracked below.

**Next model-blind feasibility step (2026-09-30):** implemented a project-owned
depth-limited negamax/alpha-beta opponent over separate bitboard reference
rules, plus transition/terminal/legal-action differential checks against the
main adapter. Twelve seeded trajectories across Connect4-gravity-8x8,
Reversi8 and Connect-6x7 matched at every tested state; this is same-project
validation, not an external referee. The fingerprinted 32-game pilot is
`docs/validation/V27_SEARCH_OPPONENT_03.json` (two seeds, four policy pairings,
both seats, two games; 86.69 seconds). Search beat random and center/corner
sanity policies in 4/4 sampled games per family, but this sample is too small to
estimate strength. Reversi search-self-play remained seat-skewed (minus won
both unique trajectories; four rows include duplicate seat swaps) and hit its
per-move node cap 116 times. Preserve earlier revision
receipts 01 and 02. The targeted plus full regression passes **329 tests in
93.235 seconds**. No JEPA model, self-play dataset, training or checkpoint was
created. The opponent bank still fails the gate; investigate symmetry and
budget before training.

**Latest continuation decision (2026-09-30):** V2.6 exact-minimax-supervised
planning remains not cleared for fitting: the current exact solver is cheap on
small/endgame positions but cannot cover sampled Connect4-8x8 midgame roots at
the measured local budget. No roots were filtered into a dataset; no labels or
fits were created. Targeted primary-source browsing further confirmed that
multi-step policy-conditioned JEPA already exists in TD-JEPA (ICLR 2026), so
sequential own-action/opponent-reply conditioning alone is not a novelty claim.
See `docs/V27_RESEARCH_POSITIONING.md` and the updated roadmap. V2.7 is only a
pivot proposal: self-play outcome data plus paired matches on harder games
could avoid exact minimax labels, but it changes the estimand. Match win rate
against a fixed opponent suite is not minimax regret, a behavioral model for a
named opponent, exploitability, or Nash equilibrium. The proposed reply-
conditioned JEPA family remains close prior art and has not passed a novelty
gate. **No V2.7 model, dataset, training, checkpoint, or positive result exists.**
The active environment is Python 3.11.9 with NumPy available and Torch absent;
no package was installed. The first V2.7 model-blind match-feasibility helper
was implemented and tested: 96 sanity-policy matches across gravity
Connect4-8x8 and Reversi8 ran in 5.207s; the simplistic heuristic beat random
in all 16 heuristic-vs-random matches per game, so that initial opponent set is
too weak for model evaluation. This is only feasibility evidence. No self-play
dataset, model, training, checkpoint, or positive JEPA result exists. Receipt:
`docs/validation/V27_MATCH_FEASIBILITY_01.json`; source and three targeted tests:
`tools/v27_match_feasibility.py`, `test_v27_match_feasibility.py`. Next, build
and validate a stronger bounded-search opponent and differential rules check;
OpenSpiel's official docs list MCTS and minimax/alpha-beta, its Connect Four
source exposes rows/columns/connect-target parameters, and `pyspiel` is absent
from the local environment. No third-party code was installed or run. Do not
start training from this result. The Obsidian mirror at
`D:/notes/vault_1/Caissa-JEPA/` was refreshed in a hidden process:77 project
Markdown files copied with0 SHA-256 mismatches, preserving relative paths and
leaving existing extra vault content intact. This confirms file bytes and paths;
the updated page was not visually reopened in Obsidian during this refresh.
Local and remote branch inventory is `main` only,
working tree was clean at commit `e5436c23e722fb380bb283fb47ad60dbb801eb4b`
before this documentation update. Next gates: targeted novelty search, rules/
opponent-pool/runtime feasibility, then method freeze and data audit before
implementation or training. Do not reuse exposed V2.5/V2.6 states as locked
confirmation data.

**Current operational entry (2026-09-29):** V2.5 grid05 completed 42/42 cells
and its independent artifact audit passed. The strict report says
`not_promoted`: raw-tail's exact-state advantage over direct is only 0.001329
(paired-root descriptive 95% interval [-0.023899, 0.026938]), with opposite
effects by game and one favorable seed. In hybrid planning it loses to direct
by 0.064565 regret (improvement CI [-0.126889, -0.005814]); the tail-mechanism
gate also fails. See `docs/V25_GRID05_RESULTS.md` for complete numbers and
limits. Run used 4,899.264 cell seconds, 4,909.031 wall seconds, 200,802,304 B
peak RSS and 180,542,007 B local artifacts. No selection/final data were opened.
Grid04 remains an inconclusive engineering attempt; preserve both attempts.
Do not edit frozen V25 source/method/report code. Source launch was
`f7a90a76c497becaff8356e030ecbef1d114697e`; audit/tooling changes are at current
main commit `1cfe93e85f3f3fd6ff084176f7ab7ec163924852`. The user-approved
`gpt-6-luna`/`high` reviewer found no source-binding or reference-wrapper blocker
and did not inspect results. The live vault was resynchronized and fully
hash-verified below. No JEPA
superiority or Q1 claim has been established.

Latest documentation mirror on 2026-09-29: all76 project Markdown files in the
current repository were checked at their relative paths in
`D:/notes/vault_1/Caissa-JEPA`; all76 SHA-256 pairs matched. Six changed/new
pages were recopied, including this page, roadmap, document index, professor
brief, post-run research update, and V2.6 method proposal. Existing extra vault
files were preserved and not deleted. The previous checkpoint visually opened
Ground Truth in Obsidian; current Computer Use exposes no native app inventory,
so refreshed-page UI display was not reverified. Hash checks verify file bytes,
not Obsidian rendering.

Separate Reversi rules-reference audit passed after grid completion: pinned
upstream MIT source `y-tetsu/reversi` commit
`60b386dd16fb9d753e50736443a600cae24a5170`, 100 seeded trajectories each on
4x4 and6x6, 4,684 states, 183,612 trajectory state/action comparisons and392
fixture comparisons, zero mismatches, 75.375s. This checks tested rules only,
not minimax labels or strength. Public aggregate receipt:
`docs/validation/REVERSI_REFERENCE_AUDIT01.json`; full receipt and 200 trajectory
hashes remain in ignored `chess_data/reversi-ref-audit01/`.

Post-run research update `docs/V25_POSTRUN_RESEARCH_UPDATE.md` records new
overlap with MuZero board-game state-consistency analysis, cross-variant
AlphaZero transfer, the ECAI Dr. Abs JEPA zero-shot RL study, policy-aware
simulator learning, and sequential-game opponent modeling. Dr. Abs studies
single-agent visual-control OOD, not adversarial board-game planning. Two
independent gpt-6-luna/high reviews concluded that visual OOD plus opponent
conditioning does not establish method novelty; moreover, full Markov state
plus minimax already represents both players' successive moves, which is not
the same as learning a particular opponent's behavior. The V2.6 candidate is
now a held-out-rule-variant transfer test for sequential action-conditioned
JEPA versus matched task/feature prediction and policy-value baselines. Its
primary endpoint is still only a candidate (held-out macro AULC exact minimax
regret versus measured training compute, with fixed inference search/time);
equal-transition AULC is secondary. `docs/METHOD_V26.md` is a revised design
proposal; its independent protocol audit found no conceptual blocker and the
AULC interval/reserve wording has been made explicit. It remains unfrozen and
unimplemented. An exploratory adapter-interface smoke is recorded in
`docs/validation/V26_INTERFACE_SMOKE_01.json`: Connect4-5x5 and Reversi8
features/transitions/complete sampled two-ply closures passed against a
project-owned reference implementation. This is not a third-party rules audit,
oracle/data audit, training result, transfer result, or JEPA advantage. No V2.6
model training has begun. Separate exact-oracle cost probe
`docs/validation/V26_ORACLE_FEASIBILITY_01.json` found 3/3 late sampled
Connect4-4x5 roots solved at 50k nodes/0.75s but only 2/5 nonterminal
Connect4-4x5 roots solved at 100k nodes/1s; this small exploratory sample is
not a solvability estimate. A new exact alpha-beta implementation passed five
focused solver tests, including value agreement on all5,478 reachable
Tic-Tac-Toe states, and 15 existing rules/reference tests; its five-root
paired probe solved 4/5 within 100k nodes/1s versus 2/5 for plain negamax,
while preserving exact action values on solved roots. Receipt:
`docs/validation/V26_ORACLE_FEASIBILITY_02.json`. This is an oracle-tooling
improvement only, not a broader solvability estimate. A reproducible
model-blind oracle-cost script then surveyed 24 Connect4-4x5 roots (17 solved,
13 with unequal exact action outcomes), plus8 Reversi6 and8 Reversi8 endgame
roots (all solved;4 and5 were outcome-informative). Reversi candidates are
near-terminal and exact search is cheap, so they do not alone establish a hard
planning regime. Receipts:
`docs/validation/V26_ORACLE_FEASIBILITY_03_CONNECT4.json`,
`docs/validation/V26_ORACLE_FEASIBILITY_03_REVERSI6.json`, and
`docs/validation/V26_ORACLE_FEASIBILITY_03_REVERSI8.json`. This remains
development feasibility, not a locked or balanced root-bank audit. The V2.6 root gate still
forbids selecting/replacing roots by observed solver completion; timeouts count
against predeclared coverage. Full repository unittest now passes322 tests in
115.2s, including oracle correctness/budget checks. No V2.6 data labels or model
training have been produced.
More cost probes sharpened the feasibility tradeoff: gravity Connect4-4x5
solved22/22 sampled roots at target plies5-11 within1s, with17 informative;
an early-ply1-4 probe solved only4/12, with1 informative on the reproducible
script rerun (a prior inline screen solved5/12,2 informative, showing cost
threshold variability). For gravity
Connect4-8x8, only1/10 nonterminal roots solved in1s and1/3 fixed early roots
solved in5s. These are small seeded feasibility samples, not rates. A larger
variant looks like a meaningful search challenge but exact labels are too costly
for this solver; the easy variant is unlikely to establish a meaningful
planning advantage. Receipts are
`docs/validation/V26_ORACLE_FEASIBILITY_04_CONNECT4_GRAVITY.json`,
`docs/validation/V26_ORACLE_FEASIBILITY_04_CONNECT4_GRAVITY_EARLY.json`, and
`docs/validation/V26_ORACLE_FEASIBILITY_05_CONNECT4_8X8*.json`.
This gap weakens exact-minimax supervised V2.6 as a route to a multi-game
positive result; the next design decision is whether to pivot to self-play
outcomes and fixed-compute match evaluation rather than filtering out hard roots.
Read `ROADMAP.md`, `docs/V25_POSTRUN_RESEARCH_UPDATE.md`, and the method
proposal for gates, controls and kill criteria. Official OpenSpiel sources offer Apache-2.0
procedural game implementations, but the reviewed game index did not resolve a
matching Reversi/custom-variant exact oracle; the surveyed Pascal Pons solver
is AGPL-3.0-or-later and targets standard Connect Four. No external code was
downloaded or used. The license/source findings and limits are recorded in
`docs/V25_POSTRUN_RESEARCH_UPDATE.md`; external oracle selection remains open.
Source inspection confirms `two_player/games.py` encodes a padded 8x8 board
into 198 features and uses a 65-slot action mask; V2.5 each-run training mixes
Connect4-4x5 and Reversi6 data through a shared model. This finite supported
interface may be reused for variants within its board/rule representation, but
V2.5 did not hold out a complete rule variant. The previous review's broader
statement that no usable variable-size interface exists was therefore too
strong; only generalization beyond the padded board and encoded rules remains
unsupported.
The closest cross-variant transfer preprint uses Ludii; its official source
license is CC BY-NC-ND 4.0, so no Ludii code/data were downloaded or used. Prefer
project-owned procedural games or a source with clear training/redistribution
rights. Exact method uniqueness and JEPA advantage remain unestablished.

**Agent approval rule (2026-09-29):** only the user may create/configure exempt
workers directly. Before I create any agent/subagent, ask the user to approve
its exact model and reasoning effort. The user approved `gpt-6-luna` / `high`
for exactly two independent reviews in this continuation; both completed
read-only without fitting or edits. This is not blanket approval for other
models; ask again before any different configuration. If approved workers are
unavailable, continue directly or report the blocker.

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
At that survey stage no v2 model had been fitted/scored. Further root/target split analysis found only13
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
V2 grid01 COMPLETED36/36 at source commit
`325afc0502911314d585a659ce456bb150b6231e`, pushed and verified on sole branch
main. All36 cells remain frozen and preserved locally. No selection/final
predictions.29 integrated rules/data/model/
evaluator tests passed8.941s. Full regression then passed126 tests in72.353s;
runtime-specific10 tests passed0.324s. An earlier concurrent-source test run had
one expectation mismatch after the new invalid-cap guard; the fresh run passes.
Independent real-rule gradient audit:306 checks, maximum error6.69e-10. Runtime
repairs reviewed;6 report tests passed9.614s and its independent audit passed.
Local CPU: AMD Ryzen AI5 340,6cores/12logical processors,16,418,648,064bytes RAM.
Training is serial single-BLAS-thread; no cloud/GPU spending.37 Markdown files
were mirrored with matching SHA256 and Ground Truth reopened in Obsidian.
New `docs/V2_EXPERIMENT_LOG.md` records the full sequence and current run.

**V2 grid01 outcome: not promoted.** All15,048 learned decisions and836 fixed
controls completed without censor/error/collapse. Tuned rjepa exact equal-game
regret0.2491448293 versus value-dynamics0.2476635514: improvement-0.0014812779,
development bootstrap95% interval[-0.0494331,0.0487142]. Rjepa beats direct and
decoded pooled means but is worse on Connect4 than direct/value-dynamics.
No JEPA-superiority claim. Read `docs/V2_GRID01_RESULTS.md` and its aggregate
JSON in docs/validation. Independent reviewer recomputed all saved actions,
oracle regrets/tie-breaks, hashes and paired schedules without rerunning models.
Each run40epochs/2640steps/334080forkdraws; totaltraining513.287s, range11.691–18.316s;
process-lifetime peak RSS213,417,984bytes; local run artifacts36,905,709bytes.
Next: diagnostics-driven finite v2 development amendment, fair tuning of the
strong value-dynamics control. Do not touch selection/final or relabel this grid.

V2.1 amendment now frozen in `docs/METHOD_V21.md` before fitting: coherent legal
symmetry augmentation for every control, auxiliary weights0.1/1 for decoded/
rjepa/raw/no-response, two rates andthree seeds =60 cells. Same model/data/labels,
40epochs and promotion threshold. New package `two_player_v21/` keeps original
v2 source immutable. Grid02 COMPLETED60/60 at source
`086e839d5f9ed1559cce16a9f8ff9fdd6b843191`, pushed and verified on main.
Local artifacts: `chess_data/v21-grid-02/`; preserve both frozen packages/methods.
21 v2.1 augmentation/runtime/report tests passed10.858s; independent
review found no blocking fairness/identity/augmentation issue. Training-only
gradient/group probes and limits are recorded in `docs/V2_GRID01_DIAGNOSIS.md`.
They do not establish causality or novelty. V2.1 may still fail; all attempts stay.
Two later options are research proposals only, NOT frozen or implemented:
`docs/V22_MECHANISM_ANALYSIS.md` shows common sibling offsets can change minimax
actions; projected JEPA error alone does not bound value error. Reducing mean
residual weight weakens the worst-case bound. `docs/V22_LABEL_BUDGET_OPTION.md`
proposes a carefully masked label-efficiency study with strong EMA value controls.
These notes are proposals only; the subsequent selected design is METHOD_V22.

**Grid02 outcome: not promoted.** All25,080 learned decisions+836 controls
verified, all120 seed/epoch sampling AND augmentation schedules independently
replayed. No errors/censors/collapse. Raw JEPA(lr0.001,weight0.1) regret0.2074247144
versus strongest value-dynamics0.2122503207: improvement0.0048256063, descriptive
95% interval[-0.039003,0.044845], below0.05. Connect4 comparison with decoded
also fails. No-response exact0.201912 further limits action-conditioning claims;
raw JEPA Reversi hybrid0.496732 is worse than direct0.290850. No latent-planning
benefit established. Totaltraining916.427s; per-cell12.138–24.121s; peak RSS
215,351,296bytes; artifacts63,086,469bytes. See V21_GRID02_RESULTS and independent
review. Figures in docs/figures are rendered from verified aggregate JSON only.

**Next v2.2:** METHOD_V22 freezes a72-cell restricted-label study (25%/100%
training-root closure, six families including strong EMA-value and raw-no-response,
two rates, three seeds). Raw JEPA was chosen adaptively from grid02. The prefit design required at least50% genuinely unlabeled
nonterminal canonical training states in each scarce game before fitting. It required
redacted train AND separate development exports so the trainer never reads the
full parent artifact. Root IDs must not retain hidden-label-derived hashes.
No oracle-compute saving claim on this already solved/admitted bank. Selection/
final remain unscored. Original v2/v21 source stays unchanged.

V2.2 prefit implementation now passes186 full-regression tests in120.105s.
Independent masked-model/runtime/data reviews found no blocking issue. Fresh
standalone artifacts pass readiness: Connect4 has2620/3468(75.55%) and Reversi
4058/5444(74.54%) canonical nonterminal states unlabeled. Selected roots62/248
and66/261; all509 training roots and6750forks remain available to every family.
Scarce fingerprint dc81db9ab2d67d2905156fb328fe80369eb76bb4d5b140ebe041e68a578ebfab;
full73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18;
development bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617.
Paths are chess_data/v22-scarce-01, v22-full-01 and v22-development-01.
Aggregate audit: docs/validation/V22_LABEL_ACCESS_AUDIT.json. Grid03 COMPLETED all72declared cells at source
9e3d10bb3d01f4761db552ec6b2d7241957cf2e0, pushed/remote-verified on main.
Artifacts: chess_data/v22-grid-03. Do not edit frozen v2/v21/v22 packages or
method specifications: completed artifacts remain bound to their hashes. No final/selection predictions.
Keep all previous negative grids. The prefit review and later50 Markdown files
were mirrored to the discovered Obsidian vault; Ground Truth and the Vietnamese
professor brief were visibly opened and readable.

**Grid03 outcome: not promoted.** Scarce raw JEPA regret0.2933388309 versus direct
0.2839166819, improvement-0.0094221489, descriptive95% interval
[-0.0757303311,0.0479220115]. Allfour control intervals include0. The full-label
sensitivity reuses scarce-selected rates; it is not superiority against fully
retuned controls (the disclosed full direct0.001 cell mean0.196598 is better than
raw0.205867). Independent review verified72runs,30,096learned+836control decisions,
120sample/augmentation plans andall2880epoch label-count records. Allsix full-label
EMA/value-dynamics pairs have59bitwise-identical tensors andidentical decisions.
No failure/censor/collapse or selection/final prediction. Totaltraining1102.611s,
range11.930–23.861s; lifetime RSS251,486,208bytes; artifacts78,628,950bytes.
See docs/V22_GRID03_RESULTS.md and V22_INDEPENDENT_RESULTS_REVIEW.md.

Afterward, tools/diagnose_v21_value_alignment.py examined18selected Grid02 models
using only standalone full training/development exports in15.876s, with no new
optimization/search. It separates actual-encoded and recurrent-predicted value
errors, latent errors, weighting and strata. Raw Reversi H2 training encoded MSE
0.511297 is below a fitted constant0.663673, so absolute error alone does not
establish underfitting. Existing40epoch histories still improve. Before any new
architecture grid, freeze a finite training-only convergence/capacity diagnostic.
docs/V23_RESEARCH_OPTIONS.md is a conditional proposal, not an implemented model.
Recent primary research includes RePAIR, MuZero interpretation and action-factored
prediction; uniqueness remains unestablished. No further blind loss-weight search.

Next frozen protocol: docs/METHOD_V23_DIAGNOSTIC.md, independently reviewed before
implementation. It prescribes18 training-only runs (three unchanged families,
two total-model capacities, three seeds),160epochs with0/40/80/160 snapshots,
single learning rate0.001 and no development path or planner calls. Bound300s/cell,
5400cumulative seconds and3GB local output; measured overruns remain failures.
The9small-model epoch40 tensor references were independently checked against all
531saved tensor hashes from Grid03 FULL. Hash-only receipt:
docs/validation/V23_EPOCH40_REFERENCES.json. New runs initialize from seed, never
from those checkpoints. This diagnostic cannot nominate a JEPA model; it informs
a future separately frozen, fairly controlled development comparison.

V2.3 implementation is now separate in `two_player_v23_diagnostic/`; it accepts
only the frozen standalone FULL training artifact, saves four verified snapshots
per cell, and stops the grid on any failed/time-limited/collapsed cell. Independent
reviews covered training access, nonmutation, all59 checkpoint tensors, descriptive
report arithmetic and resource accounting. A final-ledger storage-limit gap was
fixed before fitting. Full regression passed210 tests in124.519s; subsequent final
targeted metrics/runtime/report checks passed27 tests in13.952s (including three
additional failure-path tests). These are engineering checks, not research results.
The source milestone must be committed/pushed before `chess_data/v23-fit-01`
is generated. No V2.3 fit has yet run at this prefit documentation update.

Subsequent V2.3 execution completed18/18 at source20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37.
All160epoch runs and72snapshots passed strict report and independent audit.
All6family/capacity groups still improve S80→S160 by median11.27–22.29%; larger
capacity helps every family/all3seeds (median20.75–26.03%). Direct meanS160
0.408437/0.305494 (small/large), rawJEPA0.436337/0.339782. This is training fit,
not a JEPA win or development evidence. No new development/selection/final
predictions. Actual cell work1627.083500s,62.842–127.134s/cell,137,879,552bytes
lifetime RSS,142,867,189bytes artifacts. Independent audit verified480 paired
plans,2880 histories,72snapshots/4248tensors,9 exact Grid03 replays and36,648root
metadata records against the standalone train payload and17 committed source
blobs. Read docs/V23_FIT_DIAGNOSTIC.md and V23_INDEPENDENT_RESULTS_REVIEW.md.

New mathematical critiques reject generic random minimum-probe fitting without
a concrete representation-reuse question (finite-probe and convex-hull
counterexamples). docs/V24_ADDITIVE_DYNAMICS_LIMIT.md derives an action-independent
coordinate-ordering restriction of the current additive transition. Its relevance
to actual target embeddings and planning remains unmeasured; gated/MLP mechanisms
have prior art and must strengthen non-JEPA controls too. Next budget/probe
decision must be frozen before measurement. No architecture is promoted.
External reference feasibility: OpenSpiel ConnectFour supports size parameters;
its inspected Othello is fixed8x8, so not an unmodified Reversi6 reference.
Only public source/docs were read; no external package/data acquired.

Next frozen decision is docs/METHOD_V24_ORDER_PROBE.md: common future128/64×160
budget for all controls, and one no-fit H1-only order probe over all18 final
V2.3 checkpoints. Deterministic disjoint state/action blocks are saved before
checkpoint loading; both online/EMA targets are measured, direct random
dynamics are never scored. Bounds are uniform-edge latent SSE, not planning
loss. A heuristic10% residual-floor/25% coverage screen is evaluated separately
by game/capacity, with nonterminal sensitivity and allnegative outcomes kept.
Independent spec reviews found denominator/perspective/tolerance/packing-order
ambiguities; these were clarified before implementation. No probe measurement
has yet been made. Runtime/tests/independent review and source push remain gates.

V2.4 implementation subsequently passed independent source review and the full
239-test regression (133.537s). Final output-hash rereading and failure-path
regressions were added before launch (11 runtime tests pass). Synthetic actual
core-to-report tests cover all18 configurations/72 rows without fitting. Direct
prediction metrics remain unavailable. Source commit/push and vault sync precede
the single fresh `chess_data/v24-order-01` probe; no result exists at this update.

Subsequent V2.4 probe completed18/18 at0a7edef6bf5a651c37ca4c23186dbbf472ea2b26
in12.875268s,103,759,872bytes lifetime RSS,1,875,856bytes excluding journal.
All72 contexts verified internally, no errors/mutations/protected predictions.
The prespecified obstruction screen failed allfour groups: median bound/full SSE
0.000326/0.000174 for Connect4 small/large and0.001933/0.002787 for Reversi,
with71.689%/68.136% H1 coverage. Nonterminal sensitivity also fails. The bound
does not establish a material bottleneck or prove adequacy; no JEPA advantage.
Read docs/V24_ORDER_RESULTS.md. Independent actual-artifact audit follows.

V2.4 independent audit subsequently PASSED:23 committed source files,22 outputs,
18checkpoints/1062tensors/72rows,2056 independently rebuilt H1edges and358packed
blocks. Source/schedule/hash/arithmetic all match. No new encodings or fits.
Read docs/V24_INDEPENDENT_RESULTS_REVIEW.md; allprimary/sensitivity screens fail.

Next frozen development protocol: docs/METHOD_V25.md, complete-reply half-mean/
half-max latent residual.42 cells,7 equally exposed families,2rates,3seeds,
128/64×160, shared standard MLP and recurrent policy/value supervision. Strong
scalar/decoded tail and scaled-uniform controls test whether latent allocation
adds anything. Exact-selected rates stay fixed for hybrid; both gates retained.
Independent method reviews resolved scalar-head lag, denominators, bound maxima
and tie-gradient issues before code. No uniqueness or positive outcome claim.
Additional primary search includes TD-JEPA/VaGraM/TEMPO/WAKER/MML; see
docs/V25_ROBUST_PREDICTION_RESEARCH.md and V25_PREFIT_REVIEW.md. Implementation
and source-validation gates remain before any V2.5 fit.

V2.5 implementation then passed independent source reviews and290 full regression
tests (106.256s), plus49 final targeted tests (10.385s). Allseven manual-gradient
objectives, legal complete-group sampler and strict artifact-only report are
implemented in two_player_v25; terminal-oracle and failed-budget journaling
findings were repaired before fitting. Existing source/checkpoints unchanged.
Next is commit/push, vault sync and one fresh bounded42-cell v25-grid04 attempt.
No V2.5 result exists at this prelaunch checkpoint. Data/checkpoints remain local.

Subsequent V2.5 grid04 at5102ea0588198f993874a495d18bfef1e868e2ec stopped
INCONCLUSIVE: three completed direct cells, fourth failed during diagnostics,
38 unstarted. Peak1,004,228,608 bytes exceeded1GB. Total cellcost496.259139s
includes136.737907 failed-cell seconds; wall503.946364s. The inherited Windows
monitor creates a new ctypes structure/pointer type every call; independent
monitor-only2000-call reproduction retained2000 cached types and15,859,712
additional bytes despite garbage collection. This is an engineering failure,
not a JEPA comparison. All old source/artifacts remain unchanged. Saved learned
decisions1254 undercount actual exposure: traceback proves another418 completed
but unsaved decisions, at least1672 total, plus836 controls. No partial outcome
scores were used for method selection; protected predictions remain0.
Read docs/V25_GRID04_FAILURE_AUDIT.md and prospective V25_RUNTIME_AMENDMENT.md.
Only the monitor/provenance bindings may change in a new two_player_v25r package;
all42 cells must restart fresh in grid05 after review/test/push/vault gates,
same scientific design and limits. No fit is active during this repair update.

Those repair gates subsequently passed and grid05 started once atf7a90a76.
Every scientific setting is unchanged. Four grid04 final optimizer states have
192 tensor hashes recorded prospectively for post-run numerical equivalence.
The new run is not complete and no comparative result has been inspected.


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

## Continuation update — 2026-09-30

The Reversi search helper now canonicalizes player-to-move to +1 and square
boards over D4, then maps the selected move back to the original frame. The
focused suite passes 5 tests, including all rotations, reflections, and
color/turn swaps on a seeded midgame. A second assertion verifies that the
symmetric initial position has four tied canonical maps, exercising that
selection path. These tests establish properties of this implementation; they
do not certify the strategy or external game rules. Receipt
`docs/validation/V27_SEARCH_OPPONENT_04.json` records 32 exploratory match rows,
two seeds, two game families, 51.19 seconds, 68 Reversi node-cap hits, and 4/4
sampled sanity-policy wins. The two Reversi self-play seeds each appear twice
through seat-swap rows, leaving two unique trajectories: plus/first won 2/2 in
receipt 04, while minus/second won both unique trajectories in receipt 03. This
unresolved reversal is evidence against interpreting the tiny pilot as bias
correction or strength evidence. No training data were generated.

Targeted source review found Deep Latent Competition (CoRL 2020/PMLR 2021), a
two-player racing system with joint latent dynamics conditioned on both
players' actions, opponent-view prediction, opponent action modeling, and
imagined self-play. Its visual racing setting differs from this project's
deterministic fully observable turn-based board-game class, but it rules out
novelty claims about competitive latent interaction or opponent-action
conditioning alone. MA-JEPA (Kaplowitz et al., arXiv preprint submitted
2026-09-27; not peer reviewed as of this update) further studies joint-action
conditioned JEPA prediction and imagined planning in cooperative decentralized
partially observable SMAC tasks. This difference in timing, observability,
team/reward structure, and solution concept does not itself establish novelty.
The retained reply-set/minimax-ordering objective remains a candidate only;
equivalent minimax/value-equivalence literature and exact teacher coverage
must be checked before implementation or training.

At the start of this continuation, HEAD and `origin/main` were both
`1f437db31e98e8b3905953a7cc222f9169f89d28`, branch inventory contained only
`main` locally and remotely, and no tags were reported. The continuation was
committed as `cc3cb127819ac8e9a24446f7a02fc748e6d4cb06`; normal fast-forward
push succeeded and `git ls-remote` returned the same SHA. The working tree was
clean afterward; local/remote branch listing contains only `main`.

Final Obsidian sync after the document corrections copied all **78 project
Markdown files** to `D:/notes/vault_1/Caissa-JEPA/`, preserving relative paths;
all 78 SHA-256 comparisons passed. This continuation did not reopen the page in
the Obsidian UI so the user's screen stays available; the prior session
visually opened and read this entry page.

Update this document and its vault copy after important decisions/deliverables and before ending a long session. Never substitute historical data/run claims for live verification.

Discovery correction: an initial 22-file copy was placed at D:/notes/Caissa-JEPA (the parent outside the vault). It is preserved as an intake snapshot, not the active mirror. No originals were moved or deleted.

### Prior-art update — 2026-09-30 (after Athénan audit)

The targeted review now includes Ishibashi, Abe & Iwasaki, “Approximate State
Abstraction for Markov Games” (AAAI 2025), which extends Q/minimax-value-based
aggregation to two-player zero-sum Markov games and reports a 760-state Markov
Soccer experiment; Soemers et al., “Transfer of Fully Convolutional
Policy-Value Networks Between Games and Game Variants” (TMLR 2023), with
zero-shot and fine-tuned game/variant transfer; Gao et al. (ICGA Journal 2018)
on transfer across Hex board sizes; and Banerjee & Stone (ICML 2007) on value
function transfer for general game playing. Sources and method-level comparison
are recorded in `docs/V27_PRIOR_ART_REAUDIT_20260930.md`. The methodological
novelty risk remains critical: compact minimax-sufficient abstraction and game
transfer are established, so neither latent compression nor held-out transfer
alone is a contribution. No V2.7 training, model, checkpoint, or JEPA advantage
exists. Next gate: define a measurable increment versus Athénan tree-value
learning, minimax-Q/approximate abstraction, direct policy-value transfer, and
task-prediction controls; then test label coverage and matched compute before
training. Two independent `gpt-6-luna/high` audits agree that this remains only
a candidate question: direct minimax-Q can learn the same action ordering from
the same successor labels, and Athénan already initializes all legal child
values at searched nodes then tree-bootstraps its partial tree. The JEPA claim
survives only if latent prediction adds planning-relevant information or a
measured fixed-compute decision advantage. The audits did not establish
novelty/superiority and ran no training. Details are in the re-audit note.
All 78 project Markdown files were copied to
`D:/notes/vault_1/Caissa-JEPA/` with their repository-relative paths and
independently compared by SHA-256; 0 files were missing or mismatched. Obsidian
UI was not opened during this sync to leave the desktop free.

The same source audit also found two required efficiency/consistency controls:
PCZero (ICML 2022), which reports efficient path-consistency-regularized
AlphaZero results in Hex/Othello/Gomoku, and Ota et al. (ICML 2026 accepted), a
model-free regularized policy-optimization study across Animal Shogi, Gardner
Chess, Go, Hex, and Othello. The latter's exact budgets and game-level tables
still need full-text review before quantitative use. These works further narrow
any generic efficiency or latent-consistency claim. Keep the experiment
exploratory; no candidate is frozen and no training gate has passed.

### KLENT full-text follow-up — 2026-09-30

The full accepted ICML 2026 paper by Ota et al. was reviewed at
`https://arxiv.org/html/2602.10894`. KLENT directly learns a policy and
action-value Q from regularized self-play, using reverse-KL, entropy and
lambda-returns without search during training. In its five-game evaluation it
uses a shared 6-block ResNet, three seeds, anchored pretrained Pgx opponents,
and simulator calls on the training axis. The paper reports reaching 50% mean
win rate at 75M simulator evaluations versus 300M for Gumbel AlphaZero. In a
separate protocol after 800M training evaluations, all methods use 800 test-time
MCTS rollouts and KLENT reports 77.2% mean win rate against its anchor. These
figures are the paper's, not ours, and do not directly measure minimax regret
or hardware compute. Full setup and restrictions are extracted in
`docs/V27_PRIOR_ART_REAUDIT_20260930.md`.

The authors' official code repository was inspected read-only at
`https://github.com/KazukiOhta/klent`. Its visible root/README has no LICENSE
file or declared code license; requirements pin JAX CUDA 12 and Pgx. We did not
clone, download or execute it. Treat upstream code as uncleared for reuse. A
clean-room implementation from the published equations is an option, requiring
an independent fidelity review.

Research decision: require a KLENT-style regularized direct policy/Q arm in V2
efficiency comparisons, separate from the direct minimax-Q worst-case control.
Simulator-call parity alone is inadequate; record environment calls, CPU time,
model/training cost and inference budget. No code, data, model, checkpoint, or
training run was created for this review. No claim of JEPA superiority has been
established. All 78 project Markdown files have now been copied to
`D:/notes/vault_1/Caissa-JEPA/` with repository-relative paths; independent
SHA-256 comparison found 0 missing files and 0 mismatches. The Obsidian UI was
left closed to keep the user's screen available.

### V2.8 experiment redesign proposal — 2026-09-30

Created `docs/V28_KLENT_JEPA_COMPARISON_DESIGN.md`: a proposal to test whether
adding one-/two-ply action-conditioned JEPA prediction to a KLENT-style direct
policy/Q learner improves decision performance under matched data, capacity,
training schedule, measured CPU compute and inference budget. It separates this
fixed-opponent behavior estimand from a minimax/planning estimand and defines
matched task-prediction controls, leakage/coverage/runtime gates, multiple
compute axes and explicit kill criteria. This is not frozen, code, trained
model, or evidence of superiority. The clean-room baseline specification is
K0.1, and `two_player/klent_baseline.py` implements its masked policy target
and player-perspective alternating lambda-return utilities.
`two_player/klent_model.py` implements a small shared encoder with separate
policy/Q heads, manually differentiated cross-entropy/MSE losses, Adam updates,
online self-play target collection and phase-based fitting. Sixteen focused
synthetic tests pass, including finite-difference gradient checks and an
eight-episode toy fit; two initial utility-test assertions were corrected
before the passing run. These are code-correctness checks, not policy
convergence, game results, or evidence of JEPA superiority. The complete
repository suite passed **346 tests in 125.103 seconds**, including the learner
additions; Qt emitted existing temporary-asset warnings during release/UI
smoke checks, but the suite exited successfully. Next is the source-hashed exact
alternating-toy convergence probe, followed by independent fidelity review and
the model-blind data/compute audit; JEPA training remains gated. Added
`docs/KLENT_CLEANROOM_BASELINE_SPEC.md` as K0.1: it specifies the masked KLENT
policy-improvement distribution, action-value loss, player-relative signs for
alternating lambda returns, and six synthetic fidelity checks. It is an
equation-level CAISSA adaptation, not a paper/code reproduction. `ROADMAP.md`
and `docs/DOCUMENT_INDEX.md` link both documents. All 80 project Markdown files were copied to
`D:/notes/vault_1/Caissa-JEPA/`; SHA-256 comparison found zero missing files and
zero mismatches. The Obsidian UI was not opened in this session to keep the
desktop available.

### Current K0.1 convergence evidence (2026-09-30)

The post-commit source-hashed Count Up probe ran on commit
`f9ac7f739fda1268515ef7e03652a9e9bc0bae47`, with seeds 17, 29 and 43. **Independent
review correction:** its policy TV/Brier values (TV 0.01995, 0.02027, 0.01609;
Q MAE 0.11375, 0.05894, 0.05667) compare the one-step improvement target
\(\pi'\) with the exact quantal-response fixed point, not the network policy
\(\pi_\theta\). They do not demonstrate learned-policy convergence. Q MAE is
from the learned Q head. The result concerns one seven-state synthetic game and
is not board-game strength, cross-game generalization, KLENT reproduction, or
JEPA-over-baseline evidence. The independent reviewer also found stale
on-policy target reuse when `epochs > 1` and missing replay/model/role provenance.
The implementation now rejects multi-epoch fit and attaches deterministic
trajectory identity, rules version, player sequence and behavior-model hash.
The corrected learned-policy probe passes; across seeds 17/29/43,
learned-policy TV is 0.020999/0.028382/0.019536, improvement-target TV is
0.019945/0.020272/0.016093, and Q MAE is 0.113751/0.058942/0.056669. Full
regression after the repair passes **346 tests in 134.030 seconds**; focused
tests pass 16/16. The raw per-state output remains excluded from Git.
Historical/corrected receipts and reports are
`docs/validation/V28_KLENT_COUNTUP_01.json`,
`docs/V28_KLENT_COUNTUP_01.md`, and
`docs/validation/V28_KLENT_COUNTUP_02.json` / `docs/V28_KLENT_COUNTUP_02.md`.
These are engineering checks only, not a JEPA or board-game result. Do not
start production board-game training until baseline review, model-blind rules,
runtime/power and data-split gates pass. The repository remains on `main`; its
current result docs need commit and remote verification. Obsidian
at `D:/notes/vault_1/Caissa-JEPA/` most recently contains all 90 project
Markdown files; the post-result verified copy pass found zero missing files and
zero SHA-256 mismatches. The PowerShell window was hidden and Obsidian UI stayed
closed to preserve the user's screen.

### V2.8 literature delta and model-blind rules gate (2026-09-30)

Targeted full-text primary-source review added H-JEPA (arXiv v1, 2026-09-27),
ActSWM (arXiv v2, 2026-08-15), Action-Conditioned Predictive Consistency
(2026-08-13), and TD-JEPA (ICLR 2026 proceedings) in
`docs/V28_PRIOR_ART_DELTA_20260930.md`. These establish prior art for
action-conditioned JEPA, action-sensitivity/readout, multi-step dynamics,
planning, and policy/task transfer. No direct two-player alternating
perfect-information zero-sum JEPA method was found in this targeted pass, which
does not certify novelty. The candidate must remain an explicit role-conditioned
alternating-action comparison against KLENT, task-prediction and minimax/tree
controls; if the measured fixed-budget decision benefit is absent, drop the
algorithm-novelty claim.

The project-owned Reversi4 adapter passed the exhaustive *rules-only* subgate
against a separate coordinate-ray oracle: all 62,789 reachable player-states
(including 6,168 terminal), 89,332 legal transitions, 8,988 forced-pass states
and 113,900 complete two-ply reply pairs were checked; maximum branching was 6.
The initial run took 8.73s wall / 8.59s CPU on local Python 3.11.9. No dataset
or training was created. The temporary source used commit
`c335c53ab273b92a1e533cb6bd7b98fb01b23ab6` plus a working-tree source hash; a
post-commit audit is required for the final receipt. This passes only rule,
transition and two-ply coverage for a 4x4 feasibility variant. Leakage/split,
opponent power, model compute parity, JEPA benefit and cross-game transfer all
remain unaudited. Full Reversi4 results must not be generalized to the stated
game class. Current gate source/test and literature note have passed the 348-test
full regression (127.285 seconds). The exhaustive pre-commit audit used
working-tree source; rerun after commit to pin the final source hash and resource
receipt. Then sync the new audit note to Obsidian and push/verify the documentation
milestone. Data split, opponent-power, model-compute and JEPA-superiority gates
remain open.

### Latest continuation checkpoint (2026-09-30)

The post-commit Reversi4 audit is pinned in
`docs/validation/V28_REVERSI4_RULES_GATE_01.json` and explained in
`docs/V28_REVERSI4_RULES_GATE_01.md`. It used source commit
`5abbd777261c34228888ecbddd9924686b159b63`, tool SHA-256
`d70752f756260ac29f79f4b7c15d17c974321130b05b6daed3fcbd6a606336fe`, adapter
SHA-256 `8acfc82a0a8ef9aecbe5f419bfb1c9d8433c4a3fa32c7c75418e17fa2ab477bf`,
and config SHA-256 `1e6156ed51cb7b805d5fd4872d616034dd0e7bc16485dedb8a7cdbeb145a8ad4`.
It exhaustively checked 62,789 reachable player-states (6,168 terminal),
89,332 legal transitions, 8,988 forced passes and 113,900 two-ply reply pairs;
complete enumeration was true. Runtime was 8.75 CPU / 8.77728 wall seconds,
peak working set 92,688,384 bytes. Raw receipt is ignored at
`chess_data/two-player-klent-toy/v28_reversi4_rules_dev02.json`, SHA-256
`faeb7a3af54ee8f5829a918edb71435caf94f2e3b840482e997b745f40d386ed`. This
passes rules/transition/two-ply coverage only. No data or training was created;
data splits/leakage, opponent power, compute parity, JEPA benefit and cross-game
transfer remain open. The existing full suite passed 348 tests in 127.285
seconds. The primary-source literature delta is in
`docs/V28_PRIOR_ART_DELTA_20260930.md`; targeted coverage narrows generic
action-conditioned JEPA novelty but does not establish novelty.

At this checkpoint `main` and `origin/main` were
`5abbd777261c34228888ecbddd9924686b159b63`; report/receipt/document updates need
Obsidian sync and commit/push. After updating Ground Truth, copy every project
Markdown file to the same relative path in `D:/notes/vault_1/Caissa-JEPA/` and
verify SHA-256 equality. Keep the Obsidian UI closed to leave the screen free.
Next, independently audit a frozen, model-blind situation-bank, grouping/split
and evaluation schedule. Training remains blocked until provenance, opponent-

### Independent V2.8 protocol review (2026-09-30)

`docs/V28_SPLIT_PROTOCOL_REVIEW_01.md` records a read-only independent audit.
It found the older trajectory splitter has useful hashing/canonical-overlap
checks but uses a narrow random-opponent mix and small minimum support; it is
not the V2.8 split/power protocol. The old endgame pilot (up to 24 roots/game)
is easy, tiny, and exposed; its zero-regret result is not confirmation. Existing
V2.7 match receipts do not calibrate opponent power (saturated simple pairings,
few search-game trajectories, unresolved Reversi seat effect). Reversi4 must be
kept as a rules/split-pipeline fixture only. Next: freeze whole-trajectory and
opponent-family grouping, raw plus role-/symmetry-normalized overlap checks for
all states and counterfactual branches, and paired-seat evaluation; independently
validate a harder game, then produce a model-blind bank/support/power receipt.
Initial proposed floors are 100 unique roots and 50 beyond-depth roots per game;
these are not a power result. Proposed paired power target is 80% for a justified
5-point effect at family-wise alpha .05, with roots, game, training seed, family
and seats kept in uncertainty estimates. No V2.8 training or confirmatory result
is supported yet.

The reviewer was assigned under the user's approved `gpt-6-luna` / `high`
configuration. The response did not independently report runtime model
metadata, so this is a record of configuration requested, not a runtime
attestation.

This review and the latest Reversi4 report/receipt are now part of the project
Markdown set. After the current Ground Truth update, mirror all current project
Markdown to `D:/notes/vault_1/Caissa-JEPA/` preserving relative paths; verify
SHA-256 before commit/push. The completed copy pass now includes 86 project
Markdown files, with 0 missing and 0 SHA-256 mismatches; the vault's Ground
Truth file opens as readable UTF-8 text. Latest completed code/test milestone remains
`5abbd777261c34228888ecbddd9924686b159b63`; docs-only receipt commit
`6c14cd40040ea5b48007e99f9d42f47a7b616419` is ahead of `origin/main` and still
needs push/hash verification. The prior vault sync copied 85 Markdown files
with zero missing files or hash mismatches; rerun after this review addition.

### Planner-estimand correction (2026-09-30)

An independent method review found the original V2.8 KLENT+JEPA proposal only
used JEPA as an auxiliary training loss while measuring fixed-opponent policy
score. A win there would not establish the stated planning hypothesis. The new
`docs/V28_PLANNER_DESIGN_AMENDMENT.md` makes use of the predicted latent branch
an explicit part of a two-ply max-min planner and sets exact regret on a frozen
root bank as primary; fixed-suite match score is secondary. Controls include
direct encoded-leaf minimax value, matched decoded/task dynamics, MuZero-style
latent planning, JEPA disabled at inference, and a separate no-search KLENT
learner. This is a proposal only: no prior-art certification, bank/power pass,
implementation, training, or JEPA advantage exists. Reversi4 is a pipeline
fixture, not a scientific strength game.

Two V2.8 documentation milestones have now been pushed normally to
`origin/main`: `6c14cd40040ea5b48007e99f9d42f47a7b616419` (rules receipt) and
`a7535f4b21c0bc885b262533a6e73657f67343a6` (split/power review). Remote
`refs/heads/main` matched `a7535f4b21c0bc885b262533a6e73657f67343a6`; local
branch inventory had only `main`; working tree was clean apart from temporary
command-output files subsequently removed. Next mirror all newly added/updated
Markdown to the active vault, verify path/hash equality, then commit and push
the planner-estimand correction. The Obsidian UI stays closed to keep the
 desktop free; the vault markdown is checked by direct UTF-8 read and hashes.

Final mirror pass after this correction copied 87 project Markdown files with
zero missing files and zero SHA-256 mismatches to
`D:/notes/vault_1/Caissa-JEPA/`; `GROUND_TRUTH.md` is readable UTF-8 there. The
new planner-estimand amendment is still uncommitted at this checkpoint and
requires commit/push and remote SHA verification. Do not begin model fitting;
the next evidence-bearing task is an independently reviewed, model-blind
harder-game rules/runtime plus data/split/support/power gate.

### Method candidate and game feasibility checkpoint (2026-09-30)

`docs/METHOD_V28_PLANNER_V01.md` now specifies a frozen development candidate:
shared game encoder; ordered own-action/opponent-reply two-ply predictor;
EMA-target latent loss with explicit anti-collapse diagnostics; exact legal
max-min closure; side-to-move value perspective; finite KLENT policy/Q targets;
matched direct encoded-leaf, decoded dynamics, task-value/MuZero-style and
JEPA-disabled planner controls; exact-root regret as the primary metric. This
is a candidate spec, not evidence of novelty or superiority. Earlier V28 docs
now clearly subordinate auxiliary-only fixed-suite policy comparisons to the
planner-level test.

The targeted primary-source refresh added LeJEPA/SIGReg in
`docs/V28_PRIOR_ART_DELTA_20260930.md`; its theory/experiments cover general SSL
representations but not alternating minimax planning, and no trajectory-game
guarantee is assumed. A bounded model-blind exact-oracle probe of no-gravity
Connect4 4x5 (source commit `609031e57cd1079ca326f105146a5bc61757a2f2`) solved
12/23 nonterminal roots within 100,000 nodes/1s; 11 timed out; 11/12 solved
roots had varying terminal labels. It is recorded in
`docs/V28_GAME_FEASIBILITY_01.md` and
`docs/validation/V28_GAME_FEASIBILITY_01.json`, with raw non-training output
ignored at `chess_data/two-player-klent-toy/v28_connect4_4x5_feas_dev01.json`
(SHA-256 `8cef23ba553943d4fc998aec9d9ccce449fab181f96475cc39fef215452c5234`).
This small probe defers that no-gravity variant from the primary exact-regret
bank under its current cap; it is not a solvability estimate. Previous model-
blind evidence favors gravity Connect4 4x5 and Reversi6, but those old banks
were used in earlier V2 development and cannot be V2.8 locked confirmation.
Next: fresh model-blind rule/runtime, exact-root support, split/leakage, opponent
calibration, power and compute audits for candidate games. No new dataset or
training was started.

The LeJEPA full text was reviewed at
`https://arxiv.org/html/2511.08544v3`; other updated sources and scope
boundaries are linked from the prior-art delta. The method and feasibility
documents, roadmap/index, and Ground Truth need vault sync, independent diff
check, commit and push. Training remains gated.

Latest full project Markdown copy to the active Obsidian vault preserved
repository-relative paths for 89 files; SHA-256 verification found zero missing
files and zero mismatches. Ground Truth was readable in UTF-8. This count
excludes `.git`, caches, environments, build output, generated data, checkpoints,
and logs. The Obsidian UI was not opened to preserve the user's desktop.

### V2.8 independent method review and first planner implementation (2026-09-30)

The independent V2.8 review found five protocol ambiguities: terminal outcomes
immediately after the root action; oracle-coverage bias from dropping hard roots;
the target-source contract across JEPA and non-JEPA arms; alternating-player Q
and return perspective; and incomplete sampling/behavior-policy identity. The
review also found no count mismatch in the existing 24-root feasibility receipt.
`docs/METHOD_V28_PLANNER_V02_AMENDMENT.md` freezes corrections for these items.
All scheduled nonterminal model-blind roots must stay in the denominator, and
every fixed development-gate root must have complete exact root-action values
before that game passes. A failed coverage gate requires a new version with a
uniformly changed budget, never solver-success filtering.

Implemented `two_player/planner.py` as a bounded-value depth-two max-min planner
using exact adapter legality/terminal rules and root-player score perspective;
immediate terminal root actions are scored directly without enumerating replies.
Ten focused unittest cases pass across planner contracts and model-blind gate
logic, including immediate wins, terminal reply outcomes, both player
perspectives, draw, forced pass, deterministic scheduling, action encoding, and
reference-rule transitions. This is implementation evidence only. No training
dataset or checkpoint was created; ignored raw gate receipts contain generated
root positions and exact labels.

### V2.8 early fixed-schedule gate attempt, superseded (2026-10-01)

`docs/V28_MODEL_BLIND_GATE_DEV03.md` and its raw receipts first recorded complete
root maps at 200,000 nodes and 1.0 second with 500,000 cache entries (the initial
tracked summary incorrectly said 200,000 cache entries). The 100-root gravity
Connect4 4x5 schedule had 72 variable exact labels and 53 beyond-depth roots;
Reversi6 had 150/150 maps, 54 variable exact labels, and 54 beyond-depth roots.
However, that gate implementation omitted the requested-root/support condition
from `gate_pass` and did not compare terminal outcomes after the first move.
DEV03 is historical and superseded, not the authoritative gate.

### V2.8 corrected model-blind gate DEV06 (2026-10-01)

`docs/V28_MODEL_BLIND_GATE_DEV06.md` and
`docs/validation/V28_MODEL_BLIND_GATE_DEV06.json` are the authoritative reviewed
record. Under a common cap of 200,000 nodes, 2 seconds, and 500,000 cache entries,
gravity Connect4 4x5 completed 100/100 exact root-action maps with 72 variable-
label and 53 beyond-depth roots; Reversi6 completed 150/150 with 54 variable-
label and 54 beyond-depth roots. Terminal-aware rule comparisons covered 2,509
and 2,651 legal transitions. Both passed unique-root quota, support floors, full
oracle coverage, and current differential terminal/rule checks.

Earlier failures are retained: at 100k nodes/0.5 seconds, Connect4 solved 99/100
and the 100-root Reversi6 schedule had only 40 beyond-depth roots. At 200k
nodes/1 second/200k cache, Connect4 solved 96/100 with 49 beyond-depth roots;
with 500k cache at 1 second it solved 98/100. Those runs failed and no roots were
removed. The corrected DEV06 run uniformly raised the time budget to two seconds.
Hashes/counts for all retained raw receipts are in the DEV06 summary.

These model-blind results do not audit training-trajectory split leakage,
opponent-family calibration, or statistical power. Root banks are exposed
development evidence and are ineligible for locked-final confirmation or reuse
as training roots. No model has been fitted, and no JEPA-vs-baseline result exists.
The v0.3 amendment clarifies planner counters, the `GameSpec.validate` contract,
terminal return indexing, and expanded unit-test coverage.

After the final DEV06 gate-predicate and terminal-differential fixes, the complete
repository suite passed: `python -B -m unittest discover -s . -p 'test_*.py' -q`
— 348 tests in 163.687 seconds. Existing Qt warnings concerned temporary
chess-piece assets and window sizing; the process exited with `OK`. All twelve
V2.8-focused tests also pass separately. These are regression checks, not a
V2.8 training run.

### Targeted adversarial JEPA prior-art update (2026-10-01)

Primary sources were checked for Deep Latent Competition (CoRL 2020/PMLR 155)
and the 2026-09-27 MA-JEPA preprint. Deep Latent Competition already combines
joint latent transitions, opponent-viewpoint prediction, and imagined self-play
in partially observed continuous racing; it is outside this project's finite
alternating perfect-information class, but rules out generic novelty claims for
joint-action latent prediction or imagined adversarial self-play. MA-JEPA uses
JEPA-based action-conditioned joint prediction and latent imagination for
cooperative, partially observed SMAC. Its paper reports task-dependent results:
it matches or exceeds the strongest reported comparator mean on four of eight
maps, and is behind DMAWM on other maps. These works make the general mechanism
novelty risk critical. The only candidate gap is reply-set JEPA for adversarial
minimax branch ranking under matched compute; that gap remains unverified. See
`docs/RELATED_WORK.md` and `docs/V27_RESEARCH_POSITIONING.md`; no novelty or
superiority claim is currently supported.

### Obsidian mirror verification (2026-10-01)

The project Markdown mirror was refreshed in the verified vault at
`D:\notes\vault_1\Caissa-JEPA\`. The latest sync copied 106 source Markdown
files, including this Ground Truth and the trainer review as project references. A SHA-256 pass
found zero missing files and zero content mismatches. It copied only and did
not delete vault notes. The Obsidian UI was verified in an earlier session;
this sync used hidden background file/hash verification and left the desktop
available.

### DEV10 exact-root feasibility and primary-endpoint redesign (2026-10-01)

Extended `tools/v28_modelblind_gate.py` to the admitted gravity Connect4 6x7
game and added adapter-action round-trip, seeded schedule and reference-rule
coverage tests. The focused gate suite passes 7 tests. The DEV10 exploratory
schedule requested five unique uniformly generated roots (seed 28094010,
trajectory seeds 29100000 onward, target ply 5–11); all five passed independent
two-ply rule comparisons. With 500,000 nodes, 500,000 cache entries and a two
second per-root budget, exact action-value coverage was 0/5 and the gate failed.
See `docs/validation/V28_ROOT_ORACLE_DEV10_PILOT.json`. This is a small
feasibility diagnostic, not a power estimate and not a learned result.

The exact minimax-regret primary endpoint is stopped for this two-game design.
Method V05 and data/power protocol V08 propose paired color-swapped complete
game score against the two strongest same-search no-JEPA controls, with fixed
secondary finite-opponent league results and exact regret only when a separately
frozen root set is fully solved. The proposed +0.05 practical match-score margin
and paired scenario power gate are pre-fit and require independent review. No
model training has begun or is authorized; implementation of the schedule and
power analysis remain outstanding. DEV09 remains only a prefit synthetic data
audit pass. No JEPA-over-baseline, broad transfer, exploitability, novelty, or
Q1 claim is supported.

The full post-DEV09 repository suite passed 381 tests in 128.652 seconds before
the match-analysis additions. The focused model-blind gate, power, and analysis
tests pass 17/17. The five-root DEV10 oracle run completed and produced the
failure receipt. The locked schedule contains 9,600 paired blocks and its
commitment is recorded without model outcomes. The screen remained free during
all command runs by launching PowerShell hidden in the background.

### Trainer hardening review cycle (2026-10-01)

The trainer review identified an API path that could update weights on arbitrary
caller-supplied records, insufficient semantic checks on resumed epoch history,
and the absence of a durable receipt. The fixes are implemented in the working
tree: the supported production fit entrypoint obtains records only through the
audited train-split loader, while low-level epoch/update primitives are private
and reserved for unit tests; checkpoint validation binds sequential epoch entries and update count to the
optimizer step; an atomic receipt hashes checkpoint, data, audit, code and run
identities and labels metrics as root-weighted pre-update minibatch training
metrics without held-out evaluation. A deterministic interruption test confirms
two epochs after resume produce the same parameters, EMA and Adam tensors as an
uninterrupted run. The public production trainer is the only documented fit
entrypoint; underscore-prefixed test primitives remain intentionally available
for unit tests. Independent review confirmed receipt/resume integrity and
runtime provenance. The run identity binds the research lockfile hash and
actual Python/NumPy/platform versions. All focused V2.8 suites pass 70 tests.
Review disposition is recorded in `docs/V28_TRAIN_RUNTIME_REVIEW_01.md`.
These are runtime-integrity checks, not model evidence.
DEV09 training approval remains false and no project-data fit or checkpoint has
been produced.

The trainer hardening was committed and pushed on `main` as
`f5f29af1054496943c43520bbdff5f0b253fd8c4`. The independent review note and
Obsidian mirror count correction were committed and pushed as
`1fa508c8d3ab2c9656891138571d42ccb160b4d9`; `origin/main` was verified at that
hash, and the working tree was clean. Only `main` remains locally and on the
remote. At that prior session boundary, the four-hour-capped model-blind proxy
run was still in progress; the later V02 interruption is recorded in the latest
session delta and `docs/V28_MODELBLIND_V02_INTERRUPTION_AUDIT_01.md`.

### V03 interruption and development-fit gate correction (2026-10-02)

The repository was rechecked at `main`, clean and matching `origin/main` at
`186f14a4f098c4e78ed2a50abaadaa5bad0a0cd3`; only `main` exists locally and
remotely. The V03 supervisor, runner and watcher processes were absent. The
temporary output contains 3,581 outcome rows plus a manifest for the planned
9,600-block schedule. A separate audit parsed and replayed all 3,581 rows,
matched their ordered schedule IDs and fields, found zero failures, and wrote
`%TEMP%\caissa_v03_prefix_audit.json`. Partial artifact size/hash are recorded
in `docs/V28_MODELBLIND_V03_INTERRUPTION_AUDIT_01.md`. No completion receipt
exists; supervisor status is stale `running`; termination cause is unknown.
The partial was not resumed or appended to and its outcome statistics were not
used for selection.

Review of the pilot objective found that its two seats use the same proxy
policy; its variance cannot power the learned JEPA-versus-control contrast.
Before viewing any learned result, `docs/V28_DEVELOPMENT_FIT_AMENDMENT_01.md`
retired that full proxy run as a development-training prerequisite and opened
a development-only fit gate on the already-passed DEV09 audit. The amendment
requires a separately fingerprinted authorization, train-split-only fitting,
development-scoped receipts/checkpoints, held-out diagnostics and the disjoint
development schedule. It preserves the false production-training flag and
keeps V08 locked. No development fit or model outcome has run yet.

The active user instructions continue: work toward a method that beats strong
matched non-JEPA controls; preserve negative evidence; make no Q1 promise;
run shell/PowerShell work in the background to leave the display available;
retain only `main`, commit verified milestones and push without force. The
Obsidian vault previously verified is `D:\notes\vault_1\Caissa-JEPA\`; these
new notes must be copied there with the existing relative structure and
verified before ending this research continuation.

### V2.10 gradient-alignment diagnostic completed (2026-10-02)

The V2.10 no-update diagnostic completed on audited DEV09 train roots using 20
hash-validated V2.9 reply-JEPA checkpoints, two games, 300 roots/game/seed, and
ten disjoint batches of 30. The complete result is
`docs/validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json`; the ignored working output
is `chess_data/v210_gradient_dev06/gradient_alignment.json`. It contains 400
seed/game/batch rows and 12,000 root observations, with zero invalid/skipped
roots, finite norms/cosines, reconciled branch counts, and maximum gradient-sum
relative error 5.1516e-18. The committed-copy artifact SHA-256 is
`f850feb6e867137429c888846d49b41aa56dd3d9148d18e273cd0d419d5c59e8`. No optimizer or EMA update occurred. Historical
training metrics/loss curves and locked-final data were not accessed.

The first full-compute attempt (`dev05`) calculated the batches but failed while
assembling its result because the gate aggregation treated Boolean criteria as
mappings; it wrote no artifact. A new unit test covers true and false criteria,
the reviewer approved the correction, and `dev06` reran to a fresh output root.

Independent review recomputed the frozen gate and found no P1/P2. Connect4's
median seed cosine was -0.029318, seed-cluster 95% CI [-0.048282, 0.155975],
with 13/20 seeds having conflicts in at least six of ten batches. Reversi6 was
-0.040235, CI [-0.065150, 0.106376], and 12/20 persistent-conflict seeds. Each
game failed all three predeclared criteria; conclusion:
`stop_gradient_conflict_candidate`. The diagnostic does not support a causal
claim about why V2.9 failed to beat task-value dynamics, and is not strength or
JEPA-superiority evidence. The code path is therefore not being extended with
gradient projection.

The independent audit is `docs/V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md`; the
frozen method and support amendment remain
`docs/METHOD_V210_GRADIENT_DIAGNOSTIC.md` and
`docs/V210_GRADIENT_DIAGNOSTIC_AMENDMENT_01.md`. Roadmap now proposes a new,
not-yet-frozen development candidate that weights reply-set JEPA prediction by
minimax decision relevance, with identical branch schedules for a matched
non-JEPA control. This is exploratory and has substantial prior-art risk from
MuZero, VQ planning, and generic hard-branch objectives. Do not claim novelty or
start a fit until a leakage-safe method and controls are frozen and reviewed.
The user's ongoing target remains a reproducible JEPA advantage over strong
matched baselines. All PowerShell commands continue to run hidden in the
background. Obsidian Markdown sync passed to
`D:\notes\vault_1\Caissa-JEPA\`: 116 Markdown files copied, 5 differing prior
files backed up under `_sync_history/20261002-160151-v28-hardening-preflight/`,
0 SHA-256 mismatches. The final Ground Truth refresh also copied all 116 files,
backed up one prior version under
`_sync_history/20261002-160240-v28-hardening-preflight/`, and had 0 mismatches.
The sync script copies Markdown only; the full JSON result is retained in the
repository validation artifact, and its summary is present in this note and
the professor brief.

### V2.11 pre-fit candidate frozen pending independent review (2026-10-02)

The gradient-conflict mechanism was stopped by its frozen V2.10 gate. A narrow
prospective calibration hypothesis is now recorded in
`docs/METHOD_V211_JEPA_WEIGHT_CALIBRATION.md` and
`docs/validation/V211_JEPA_WEIGHT_CALIBRATION_V01.json`: change only reply-set
JEPA loss coefficient from 1.0 to 8.0 while keeping the V2.9 architecture,
audited DEV09 train data, 20 initialization seeds, three epochs/87 updates,
and planner fixed. It compares the fresh λ=8 candidates against hash-verified
same-seed V2.9 λ=1 JEPA, task-value-dynamics, and direct-leaf controls on a
fresh hash-committed schedule of 240 paired blocks/480 color-swapped games.
Schedule SHA-256 is
`c6574b28767dc29e80c3bfd2ad158c58528561a8dc2c5393c86d54534f33bc2e`.

The V2.10 gradient diagnostic's median batchwise `||g_J||/||g_task||` is 0.04937
for Connect4 and 0.04550 for Reversi6. λ=8 implies approximate median ratios
0.395 and 0.364 if scaling is locally linear; this does not change direction
or prove strength. Loss weighting is standard calibration and is not asserted
as novel. V2.11 is a development/model-selection nomination experiment only,
requires independent review and a new grant before fitting, and does not open
loss histories, V08 outcomes, or locked-final data. No fit/match/code runner has
been started under V2.11. If its +0.05 per-game and macro margins and compute
caps fail, stop λ-only tuning and preserve the negative/mixed result.

This continuation began with a clean tree at `main` matching `origin/main` at
`702144179ed1a2c2d07ea472087532a935ffe268`; only `main` and `origin/main`
existed. The existing reviewer `/root/v28_dev_match_audit` was asked to review
the frozen V2.11 protocol only before implementation or training. No new agent
was created. PowerShell/command processes are to run hidden in the background
per the user's desktop-availability instruction. The previously verified
Obsidian location remains `D:\notes\vault_1\Caissa-JEPA`; sync the revised
Ground Truth, roadmap, and protocol after review/changes and verify SHA-256.

The independent protocol review is recorded in
`docs/V211_PROTOCOL_REVIEW_01.md`: no P1/P2, with the V2.11 schedule reproduced
at 240 paired blocks and matching SHA. The reviewer explicitly did not
authorize fitting. Its P3 condition was to implement and review the dedicated
V2.11 runner/checkpoint verifier, new train-only grant, dependency check, and
resource preflight before fitting. These are implemented in
`two_player/v211_development.py`, `tools/v211_run_development_panel.py`,
`tools/v211_development_panel_supervisor.py`, `tools/v211_model_match.py`, and
`tools/v211_development_match_analysis.py`. The matcher checks frozen V2.9
ledger/source/runtime/data/checkpoint identities and loads only online/EMA
weight arrays; it does not call `Model.load` for old controls. Its preflight
loaded all 60 controls across 20 seeds and 3 arms. Focused V2.11 unit tests pass
3/3; all V2.11 Python files compile; the spec/schedule validation and
`git diff --check` pass. The existing reviewer is now checking the complete
implementation. No V2.11 grant has been issued and no fit/match has started.

The Markdown sync to `D:\notes\vault_1\Caissa-JEPA\` most recently copied 118
files, backed up two changed prior versions under
`_sync_history/20261002-164148-v28-hardening-preflight/`, and reported zero
SHA-256 mismatches. The Computer Use app inventory in this session exposed no
native app windows, so the changed notes were hash-verified in the vault but
could not be reopened in the Obsidian UI during this session. The previously
verified vault location and UI read check remain recorded above.

### V2.11 final implementation review and pre-fit status (2026-10-02)

The first implementation review identified risks around embedded receipt
history parsing, a forgeable supervisor token, runtime parity, and the
imported resource-helper identity. Fixes bind receipts while parsing only
`effective_run` before history, require token plus Windows Job Object
membership, check runtime identity, and attest supervisor/helper/runner hashes
and resource status. Its follow-up found no P1/P2 and raised two P3 precision
issues: comparing working-set use against a commit limit, and checking runtime
parity only after fit. Both are corrected: working set is diagnostic only,
while Job Object enforces committed memory; a pre-fit gate now checks all 60
hash-bound V2.9 control receipts before train-data access. The final independent
review found no remaining P1/P2 or P3 blocker. Focused V2.11 tests pass 8/8,
Python compilation and `git diff --check` pass, all 60 controls load
weights-only, and runtime parity passes for all 60 controls. No V2.11 grant,
fit, or match exists yet. The next step is a background-only stable-memory
measurement; only after the requirement is met may the independently reviewed
train-only V2.11 grant and supervised exploratory panel proceed.

The code and protocol are still development/model-selection only. V2.11 tests
ordinary loss-weight calibration and cannot establish a novel JEPA method or
superiority until the frozen matches are actually run and their gates pass.

The first hidden stable-memory measurement did not pass the fit gate: four
samples 20 seconds apart reported 806,436,864; 909,082,624; 1,032,060,928; and
861,609,984 available physical bytes, with Windows memory load 93–95%. All were
below the required 2,000,000,000 bytes and the last was below the reactive
1,000,000,000-byte floor. No fit or match started. The reviewed supervisor is
designed to wait for four new stable samples for up to 30 minutes, then stop
without fitting if the threshold remains unmet. This initial result and the
continuation decision will be mirrored into Obsidian before that wait is
started.

The Markdown-only Obsidian sync copied 118 files, backed up four changed prior
notes to
`D:\notes\vault_1\Caissa-JEPA\_sync_history\20261002-171545-v28-hardening-preflight\`,
and reported zero hash mismatches. The follow-up resource-status sync also
copied 118 files, backed up the changed Ground Truth to
`D:\notes\vault_1\Caissa-JEPA\_sync_history\20261002-171805-v28-hardening-preflight\`,
and reported zero mismatches. Native Obsidian UI is unavailable in the current
Computer Use inventory, so the update was checked by file/hash rather than by
opening the app.

### V2.11 implementation review correction (2026-10-02)

The statement above that no V2.11 code runner had started is superseded: the
protocol implementation now exists, but no fit runner has executed. The first
implementation reviewer found two P2s: full fit-receipt JSON parsing could
expose embedded training history, and a caller could forge the supervisor
token. The matcher now SHA-256-checks receipt bytes against the panel ledger
without parsing receipt JSON; both old and new models are loaded from online
and EMA arrays only. The fit process also verifies Windows Job Object
membership. After a successful fit, the supervisor will attest its source,
status-file hash, limits, stable memory samples, and peak memory in the panel
ledger, and the matcher checks that attestation before accepting the panel.
These fixes are pending independent re-review. Focused tests pass 4/4, all
V2.11 modules compile, the frozen schedule/spec validate, and all 60 V2.9
control weights pass the weights-only identity preflight. No V2.11 approval
grant, training fit, or match has been created or run.

### V2.11 grant and gated supervisor continuation (2026-10-02)

The prior sentence is superseded: after the final independent implementation
review, the train-only V2.11 grant was created by replaying the audited DEV09
loader. It contains authorization metadata only, records 1,797 accepted train
records, is stored at ignored `chess_data/v211_data_dev09_approval.json`, and
has SHA-256
`9d7d876fcb94ea67eb90fddb391cd5516f30acda8e25e3041140051134bb0adc`. No
validation, selection, V08, or locked-final records were opened; no fit or
match has started. The reviewed supervisor may now be started in the
background to wait up to 30 minutes for the memory gate and start the frozen
fit panel only after four qualifying samples.

The first hidden supervisor invocation then exposed a CLI bootstrap defect:
direct execution from `tools/` did not include the repository root on
`sys.path`, so it exited before writing a status file or creating an output
panel. No fit started. The supervisor now adds its own repository root before
imports; its regression test runs only `--help`. The same independent reviewer
confirmed this fix, with no remaining concern. `py_compile`, `git diff --check`,
and the focused V2.11 suite pass; the suite is now 9/9. The initial 60-second
RAM sample failed, so the next action is to start the corrected background
supervisor and let its bounded 30-minute preflight either observe four stable
samples above 2.0 GB and launch, or stop without fitting.

### V2.11 resumed-session process audit (2026-10-02)

Current source of truth was re-read at session continuation: `GROUND_TRUTH.md`,
`ROADMAP.md`, `METHOD_SPEC.md`, the V2.11 method note and reviewer note. The
worktree is clean on `main` at commit
`dfe4b5495c4cf7e01ea09048124fa2b75663af24`, matching `origin/main`; local
branch inventory contains only `main`. Computer Use reports no native app
windows, so Obsidian cannot be opened in this session. Its previously verified
vault path is `D:\notes\vault_1\Caissa-JEPA` and the previous Markdown sync had
zero mismatches.

The corrected supervisor PID 104236 is no longer present. Its ignored status
artifact `chess_data/v211_fit_panel_dev01.supervisor.json` remains at
`waiting_for_stable_memory`, with zero consecutive passes, 1,127,247,872 bytes
available, no `fit_started`, and no return code. The corresponding output
directory and `panel.json` do not exist; captured supervisor stdout/stderr are
empty. Therefore the process ended without an authoritative terminal status;
this is not evidence of a completed timeout or a fit. Preserve this stale
status artifact and, after checking fresh machine memory, use a new output
path such as `chess_data/v211_fit_panel_dev02` if another bounded wait is
started. The V2.11 grant remains present at the hash recorded above; no fit or
match has been observed.

### V2.11 second supervisor attempt and stale-grant diagnosis (2026-10-02)

The second corrected supervisor ran with a live tool-session handle and passed
its four-sample memory gate: available physical RAM was 2,372,726,784;
2,304,016,384; 2,543,095,808; and 2,467,213,312 bytes (84-85% reported load).
The supervisor released child PID 70720 under the resource limits, then ended
85.58 seconds later with return code 1 / `runner_failed`; peak working set was
858,767,360 bytes. The traceback points to `load_train_split` rejecting the
grant as stale/different from frozen scope. That helper did not return records
to the fit loop; `chess_data/v211_fit_panel_dev02` and `panel.json` were never
created, so no training update, checkpoint, or match occurred. The supervisor
status artifact is terminal `failed`; preserve it, its stderr, and all grant
artifacts. The failure happened because the method-note status paragraph was
edited after grant creation, changing the method hash bound into the grant.

The method note is now being stabilized with no self-referential grant hash;
approval issuance status belongs here in Ground Truth. After this change is
committed, issue a distinct fresh grant (preserving the stale first grant at
`chess_data/v211_data_dev09_approval.json`) and use a new fit output root such
as `chess_data/v211_fit_panel_dev03`. Before invoking it, rerun the focused
protocol tests and verify the file-bound approval/method identities; never
reuse the failed `dev02` artifact path. The learning hypothesis and all fit,
match, resource, and nomination settings remain unchanged.

The updated Ground Truth, roadmap, and frozen method note were copied to the
verified vault in a Markdown-only sync: 118 files copied, three differing
prior notes backed up under
`D:\notes\vault_1\Caissa-JEPA\_sync_history\20261002-180054-v28-hardening-preflight\`,
zero SHA-256 mismatches. The app inventory still has no native Obsidian window;
the vault sync is verified by destination hashes.

### V2.11 fresh grant validation (2026-10-02)

The stable method-note text has been committed/pushed in `00aaeef` and no
longer embeds a particular grant hash. A second, distinct train-only grant was
created at ignored
`chess_data/v211_data_dev09_approval_v02.json`; SHA-256 is
`1f0e1ea3db751d3ab0d6462a99894ce672a4702d8d4d761c79aaec944b526b22`. The
train-only loader accepted it and returned exactly 1,797 records, all tagged
`train`, with DEV09 fingerprint
`cf1f408356058eae5224249010008c47a23a6d8f2a8c8530990388cc179b8c40`. This is
validation of the grant/data boundary, not model training. Grant v01 and the
failed dev02 supervisor artifacts remain preserved. The next attempt must use
the v02 grant and fresh ignored output root
`chess_data/v211_fit_panel_dev03`; no method or panel-spec changes are allowed
after grant validation.

The Ground Truth and roadmap grant update was mirrored in the verified Obsidian
vault: 118 Markdown files copied, two changed prior notes backed up under
`D:\notes\vault_1\Caissa-JEPA\_sync_history\20261002-180635-v28-hardening-preflight\`,
and zero hash mismatches. This hash check confirms destination file contents;
the current app inventory still exposes no Obsidian UI window.

### V2.11 dev03 fit complete; independent panel review pending (2026-10-02)

The third supervisor run used grant v02 at frozen commit `ae9c99c` and a fresh
ignored output root `chess_data/v211_fit_panel_dev03`. The resource gate passed
four 20-second samples (2,616,799,232; 2,612,367,360; 2,596,892,672; and
2,569,093,120 bytes available; all above 2.0 GB). The fit completed with status
`complete`, return code 0, elapsed time 582.14 seconds, peak working set
858,951,680 bytes, no termination reason, and panel ledger SHA-256
`729cbec5cc812dc4808df21e5f871f923298e51fd1b80e3757cd5a546e6d5aa0`. The
panel reports 20/20 runs completed with three epochs and 87 updates each,
train-only scope, and `locked_final_access=false`.

Before matching, local provenance verification accepted the supervisor status
attestation, V2.11 grant v02 hash, runtime identity, checkpoint/receipt hashes,
and every candidate receipt's `effective_run` without parsing its history. It
loaded all 20 candidate checkpoints and 60 V2.9 control checkpoints from
weights-only arrays. No training-loss history or V08/locked-final content was
read. Independent review of this fit panel has been requested from the
user-approved reviewer. No match has started and no JEPA strength result is
available. The next step is the already-frozen 240-block/480-game development
match only after panel review accepts these artifacts.

The independent panel review has now accepted `dev03` for the frozen
exploratory matcher with no P1/P2 findings. It verified grant/panel identity,
supervisor status and attestation, all 20 candidate rows, checkpoint/receipt
hashes, each receipt's `effective_run` before history, exact updates/epochs,
and candidate runtime equality against all 60 V2.9 control receipts. The
reviewer did not read histories/losses/game data and ran no match. Its runtime
was different from the panel runtime, so it correctly warned that its own
matcher would reject the panel. The local pre-match verification, using the
runtime that completed the panel, passed all candidate/control identities and
weights-only loads. The scheduled development match is therefore authorized
to proceed with that same local runtime. No outcomes have been observed yet.

### V2.11 reviewer disposition and next action (2026-10-02)

The accepted-review disposition above supersedes earlier statements that panel
review is pending. The approved reviewer found no P1/P2 blockers for the frozen
exploratory matcher. A pre-match check on the exact local Python runtime used
for fitting verified the supervisor attestation, train-only grant v02, all 20
candidate receipts/checkpoints and all 60 same-runtime V2.9 control checkpoints
using weights-only loading and receipt `effective_run` metadata only. It did
not inspect loss histories or locked-final data. No match outcome exists yet.
The next action is the frozen 240-block/480-game DEV09 development match, using
fresh output artifacts and that same runtime. This remains model selection;
even a pass nominates a later separately locked confirmation and does not
establish Q1 readiness or methodological novelty.

### V2.11 match completed and independently audited (2026-10-02)

The frozen local-runtime matcher completed 240/240 paired blocks (480 games),
with zero forfeits and zero censors. Match artifact SHA-256 is
`44d6db3cfcff1652fee62c75cb688b48fdc719ac9df77afbc71866cc9fc7dd23`; receipt
SHA-256 is `276d9ac96e631256890b6ef5047bd598969f708906297f2d9290b44201e5ed7c`.
The analysis is `docs/validation/V211_DEVELOPMENT_MATCH_ANALYSIS_DEV03.json`.
An approved independent reviewer replayed all 480 transcripts against pinned
rules, verified schedule/block order and color swaps, recalculated seed-cluster
effects and compute ratios, and matched the report exactly; no P1/P2/P3 issues
remain. They did not inspect training histories/loss metrics or V08/locked-final
data. λ=8 was not nominated: macro candidate-minus-control scores were −0.04375
against λ=1 JEPA, −0.0500 against task-value dynamics, and −0.0375 against
direct-leaf; Reversi was negative against all three, all intervals span zero,
and every compute screen passed. This is evidence against this calibration,
not JEPA generally. It supports no superiority, equilibrium, exploitability,
transfer, novelty, or Q1-readiness claim. The frozen rule stops λ-only tuning.
Full interpretation is in `docs/V211_DEVELOPMENT_RESULT_REVIEW_01.md`.

The match result reviewer was the user-approved `/root/v28_dev_match_audit`
agent on the user-approved `gpt-6-luna` high configuration. Their final audit
reported no P1/P2/P3 issues, replayed all 480 transcripts under pinned rules,
checked exact block order and color swaps, recomputed the seed-cluster and CPU
statistics, and matched the analysis exactly. This updates any older pending
reviewer status above.

The post-V2.11 research search found [One-Step Next-Latent Prediction Is Not a
World Model (Wang et al., 2026)](https://arxiv.org/abs/2609.36227), a very recent
paper arguing that one-step latent regression generally learns a conditional
mean rather than a roll-outable transition kernel. Also reviewed primary
sources for multistep JEPA-WM ablations, 2026 latent value alignment, policy-
aware minimax simulator learning, and model-based zero-sum games. They raise
novelty risk. The current candidate question is now recursive multi-step
alternating-player latent rollout prediction, motivated by horizon-dependent
planning failures; this remains unverified and is not a method novelty claim.
`docs/V212_RESEARCH_GATE.md` captures its falsifiable hypothesis, distinctions
between opponent behavior prediction and worst-case minimax planning, required
controls/evaluation, and kill criteria. No V2.12 code or training has started;
only a no-training feasibility/prior-art audit is allowed until an exact spec
and protocol have been frozen and independently reviewed.

The first no-training adapter audit passed on candidate held-out variants
Connect Four 8×8/k4 and Reversi 8×8: both use the existing 198-feature/65-action
shape; sampled legal transitions preserve side alternation; the initial legal
two-ply branch counts were 64 and 12; and sampled trajectories reached eight
plies. A separate 24-episode-per-variant random-play audit terminated every
episode legally and exercised eight Reversi forced-pass transitions. These are
rule/adapter smoke findings only; no trajectory split/audit, training,
planning-depth benchmark, or learned-performance claim follows. Ignored audit
scripts/logs are under `chess_data/v212_*`.

`METHOD_SPEC_V212.md` v01 is now drafted as the candidate method/protocol. It
defines recursive action-conditioned latent rollout at 1/2/4 plies, a
four-ply finite-horizon max-min planner with exact legal transitions, task and
anti-collapse losses, same-search controls, held-out-size evaluation, and a
positive-margin/uncertainty nomination gate. It remains unimplemented and
cannot be fit until independent review, multistep data-pipeline audit, and a
resource pilot pass. Its own preconditions explicitly state that multi-step
JEPA world models and minimax/value-aware model learning are prior art; any
incremental novelty claim remains unverified.

The user most recently requested that all commands/PowerShell run in the
background so the desktop remains available. Processes for the V2.11 match,
analysis and Obsidian synchronization were launched hidden; the match and
analysis finished successfully. Match output, receipts, checkpoints and
intermediate logs remain under ignored `chess_data/` and are excluded from Git
and Obsidian.

## V2.12 continuation: method review and compute gate (2026-10-02)

`METHOD_SPEC_V212.md` v02 supersedes v01. It clarifies absolute-winner versus
side-to-move utility, root-perspective max/min, exact masked task-loss
definitions, the six required matched arms, exploratory (non-power) status of
the development screen, and prohibits training while a compute cap is
unverified. A prior independent review identified the same key gaps; v02 is
being prepared for re-review. No V2.12 model code or training data exists.

A corrected no-training depth-four exhaustive tree pilot completed with
source/output consistency. Among 13 sampled Connect Four 8x8 roots, rule-only
wall p90 was 0.350s (max 4,681 nodes); among 16 Reversi8 roots, p90 was 6.037s
(max 28,009 nodes), exceeding the provisional 2s cap before learned-model
calls. The raw output, source SHA-256, and sampling limitations are in
`docs/validation/V212_NO_TRAIN_COMPUTE_AUDIT_01.md`; ignored artifacts are
under `chess_data/v212_unpruned_budget_audit.*`. A representative random-weight
model-call pilot is still required. The earlier constant-zero alpha-beta audit
is not compute evidence because equal leaf values caused atypical pruning. No
production training, resource grant, or match may start until the compute
protocol is revised using no-outcome measurements and independently reviewed.

All PowerShell/Python commands are now launched as hidden background
processes, per the user's latest instruction, to leave the desktop available.

### Draft v03 status (superseded by v04)

`METHOD_SPEC_V212.md` v03 was a draft awaiting independent re-review. It resolves
the v02 findings in the text by (a) defining the inference cap unit as entered
search-state visits and counting exact transition calls separately; (b) using
only the logged action sequence for 1/2/4-ply training targets; (c) explicitly
calling terminal-outcome value labels synthetic policy-mixture outcomes and
the planner a max/min backup heuristic rather than a minimax-value solver;
(d) specifying crossed-bootstrap simultaneous intervals plus Holm-adjusted
one-sided tests; and (e) deferring confirmatory episode generation/splitting
until after nomination. The head-to-head metric, opponent suite, shared
weights, architecture, and matched data/update/training-FLOP admission gate
are now specified. These edits do not establish feasibility or novelty.

Deep-search update: the official ICLR 2026 proceedings page for Regret-Guided
Search Control for Efficient Learning in AlphaZero reports regret-value and
ranking-guided state reuse across Go, Othello and Hex. This further raises
novelty risk for any regret-weighted or high-regret-state JEPA variant. It is
recorded in `docs/RELATED_WORK.md`; do not claim regret ranking or prioritized
hard-state sampling as new. The current v03 candidate remains a hypothesis,
and close overlap with multi-step JEPA-WM and policy-aware simulator learning
still makes novelty unverified.

The local `main` was at `bf48d5da61683bd949cd9b40b93b585b32d5191d` when this
checkpoint preparation began. Only documentation and validation report files
are intended for the next checkpoint; training code/data/checkpoints do not
exist for V2.12. The current corrected rule-only pilot fails the old 2-second
Reversi8 wall cap; no V2.12 training or matches are authorized.

### V2.12 v04 checkpoint update (2026-10-02)

Independent reviewer re-reviewed v03: no P1; P2 requested frozen game-balanced
window sampling/update schedule and corrected compute-audit terminology; P3
requested consistent positioning. `METHOD_SPEC_V212.md` v04 addresses these:
928 fixed, distinct train windows per game; 50:50 game-balanced batches; three
full epochs, 29 full minibatches each, 87 updates; same per-seed order across arms.
The compute audit now calls its cap 500,000 materialized search-node visits
(including root/terminal leaves) and explicitly notes transition calls were
not separately measured. Related-work positioning now describes a max/min
backup heuristic over synthetic mixture-outcome leaf values, not a minimax
value estimator or opponent-specific response model. Zero-variance or
incomplete/nonfinite inferential cells invalidate nomination. After §8 was
clarified, the independent reviewer confirmed no P1/P2 protocol blockers for
the narrowly scoped no-training instrumentation pilot only. It may measure
random-initialized inference on synthetic legal roots after review; it bars
labels, optimizer updates, trained checkpoints, game scores, or model
selection. Training, matches and objective/training code remain gated by
novelty, data/split audits, and separate pre-fit review. The prior 2-second
cap still fails, and the pilot has not begun. No V2.12 training code, training
data, checkpoint, or result exists.
The copy-only Obsidian sync was rerun after the v04 edits: 122 Markdown files
copied and zero content mismatches; differing prior vault files were preserved
in sync-history backups. Vault path:
`D:\notes\vault_1\Caissa-JEPA`. The desktop app inventory exposed no Obsidian
window during this session, so filesystem copy/hash verification passed but
opening the notes in the Obsidian UI could not be reverified.

Checkpoint publication: documentation-only commit
`ad345443be49b913355b58436efd5c7aff0845e7` was pushed normally to
`origin/main` and verified with `git ls-remote`. At verification, local and
remote branch inventories contained only `main` (plus remote HEAD alias), and
the working tree was clean. No V2.12 code, data, training, matches, or new
performance results were added. Documentation diff checks and independent
protocol review passed; no executable tests were rerun for this documentation-
only checkpoint.

### Pause request checkpoint (2026-10-02)

The active checkout was re-inspected from
`16aeae272bf040a97dc4784ec1e2368e23faebf0`: it is on `main`, with no V2.12
pilot code or outputs. The v04 method status wording and related-work pilot
status were aligned with the reviewer disposition: pilot instrumentation only
is cleared; no pilot has started; training and matches remain gated. The user
requested that these current statuses be pushed to GitHub and then the active
goal paused. This documentation-only status update contains no executable
changes or experiment results.

### V2.12 continuation: expanded compute checkpoint and literature refresh (2026-10-03)

This entry supersedes the earlier pause checkpoint above. The v02 random-weight,
no-training pilot completed 1,152/1,152 depth-four cells. Its independently
reviewed report and the separately reviewed 10,000-node/5-second candidate
budget are recorded in `docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md`
and `docs/V212_COMPUTE_BUDGET_AMENDMENT_05.md`; the budget is only a proposal.
No data labels, training, matches, or outcome inference were used. Focused tests
passed 9/9, source compilation passed, and an independent reviewer verified
both pilot receipts and recomputed summaries. Ignored raw receipts, summaries,
and `.venv` remain excluded from Git.

A targeted 2026-10-03 primary-source search added Alrasheed et al.,
`The Planning Limits of Latent World Models` (arXiv:2609.39235), and Ma et al.,
`ReWAM` (arXiv:2609.39245), to `docs/RELATED_WORK.md`. These are adjacent
robotics results, not evidence for or against CAISSA's finite zero-sum game
hypothesis. They reinforce the need for horizon-specific action-ranking/regret
tests and for a strict distinction between behavioral response prediction and
worst-case max/min search. Novelty remains unverified; training and matches
remain gated.

Commit `0db171df` contained the reviewed code/docs checkpoint; the configured
shell push lacked credentials. The authenticated GitHub integration published
the identical Git tree as commit `d3a668c99f3aa719c39836828795366e7ecc2771`
with parent `2cfb6947c7ba7f0261d4e4c53bd7e956731ef7e8`. Remote `main` was
verified at that commit and then fetched locally; local `main` now matches
`origin/main`. No generated pilot data, caches, or environment files were
published.

The read-only V2.12 trajectory/runtime audit is in
`docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md`. It confirms that the V2.8
generator can replay full legal episodes, but it only materializes H1/H2 and
its split overlap keys do not cover every V2.12 H0–H4 context/window state and
H1/H2/H4 target. No production V2.12 multi-step window materializer/generation
protocol exists, and the proposed request-time
budget is not wired through setup, search stop, and response handling. This is
an audit-coverage gap, not a finding that existing data leaks. No data or
outcome artifacts were opened or generated. A frozen synthetic-only protocol
and in-memory auditor are implemented in
`docs/V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md` and
`two_player/v212_trajectory_audit.py`; focused tests pass and independent review
accepted that software-contract scope. This does not authorize data generation.
Training, matches, and outcome access remain gated.

The follow-on design note `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md` and
`docs/METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md` propose train-only fit
episodes/windows on training sizes and standalone development roots on held-out
sizes. Independent review found the amendment explicit and consistent with the
held-out evaluation design as a draft. The companion
`docs/V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` proposes 48 roots per held-out
variant; it is suitable for further review but not frozen. Candidate yield,
occupancy bands, and canonical uniqueness rules remain unverified. These notes
authorize no data or root generation.


### V2.12 root-schedule reconciliation draft (2026-10-03)

The previous held-out root schedule proposal accepted the first 16 unique
canonical boards per occupancy band, while the later sampling amendment
proposes accepting the first 16 valid candidate slots regardless of repeated
boards. Added `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md` as a replacement design
draft that aligns the schedule with the amendment's success-conditional
first-passage slot estimand, fixed 64-slot yield bound, and stratified
bootstrap proposal. Design 01 remains as historical context. The change
resolves only the text-level conflict; independent review has not accepted the
conditional target, PRNG independence assumptions, equal band weights, or
inference procedure. No roots were generated and no method or data gate passed.


### V2.12 bounded symmetry property checks (2026-10-03)

Added `tests/test_v212_symmetry_properties.py` for the four current V2.12
variants. It checks every declared spatial map over deterministic in-memory
legal paths, and uses a hand-built Reversi forced-pass fixture to verify legal
set mapping, exact transition commutation, terminal-result preservation,
canonical-key invariance, role normalization, and fixed pass action 64. The
combined symmetry and synthetic trajectory-auditor tests passed 9/9. This is
bounded fixture coverage, not exhaustive state-space verification or a
leakage/support result. Canonical edge reporting, root generation, data
creation, matches, and training remain gated pending broader and independent
review.


### V2.12 expanded symmetry fixture coverage (2026-10-03)

Expanded the symmetry property test to enumerate every distinct exact-rule
state reachable through four legal plies for each of the four in-scope
variants, then supplement with three deterministic legal paths through
terminal states and the hand-built forced-pass fixture. Every declared mapping
is checked over every legal action at those states for bijection and transition
commutation, as well as terminal and canonical-key invariance. The symmetry
test passed 2/2 in 19.7 seconds; combined with the synthetic trajectory
auditor it passed 9/9 in 19.3 seconds. This remains shallow bounded software
coverage, not an exhaustive later-game proof or a data/leakage result.
Canonical edge reporting and all generation/training gates remain closed.


### V2.12 disposable cgroup containment probe (2026-10-03)

Using the authorized lattice session, a temporary user systemd scope with
`MemoryMax=1536M` reported `memory.max=1610612736` bytes; a child inherited the
same cgroup path; all initial `memory.events` counters were zero. A separate
64 MiB scope with swap disabled terminated a 128 MiB page-touch child and
reported `oom_kill=1`, while its parent survived to read the event. Both cgroup
directories were removed; the OOM-failed unit required `reset-failed` before
systemd reported it absent. Reservation-only and swap-enabled probes produced
memory.max events but no OOM kill and are not counted as passes. This verifies
the host cgroup mechanism only; the V2.12 pilot worker/request watchdog has not
been implemented or launched, so no pilot hard-memory claim is made. RSS
remains sampled telemetry. No project data, model, or pilot process was used.


### V2.12 request-adapter design v01 (2026-10-03)

Added `two_player/v212_request_adapter_v01.py` and
`tests/test_v212_request_adapter_v01.py`, leaving the frozen
`two_player/v212_pilot.py` and `two_player/v212_pilot_v02.py` unchanged (their
Git blob hashes still match the source recorded in prior receipts). The new
adapter starts its monotonic clock before validation/cgroup preflight/worker
spawn, passes an absolute 5-second planner deadline, and supervises a worker
with a 6-second response deadline. It kills a timed-out worker process group,
checks whether it was reaped, validates exact-root legal actions, preserves the
last completed depth, verifies parent/worker cgroup identity and 1.5 GiB
`memory.max`, and distinguishes OOM kills from response watchdog timeouts using
`memory.events`. It refuses cgroups unless `memory.oom.group=0`. The returned
action is transient; the adapter has no receipt writer or score output.

The focused request-adapter, symmetry, frozen V02 pilot, and trajectory-auditor
suite passed 19/19; compile and `git diff --check` passed. Tests compare request
search counters to the frozen search on synthetic in-memory roots and exercise
timeout/kill/reap and OOM classification. The cgroup preflight helper alone was
run inside a disposable 1.5 GiB systemd scope; it reported the expected limit
and `memory.oom.group=0`, and the scope was removed. No request worker ran in
that scope and no pilot batch, data generation, training, match, or outcome
inspection occurred. The adapter awaits independent review and has no integrated
pilot receipt; runtime headroom and cleanup remain unverified.


## V2.12 external OOM observer probe (2026-10-03)

A disposable 64-MiB, no-swap transient systemd service touched 128 MiB. Its
cgroup was distinct from the external caller's user-session service cgroup;
the worker's `memory.max` was 67,108,864 bytes. systemd killed the worker
(status 9) and surfaced `Result=oom-kill` through both `systemd-run --wait
--pipe --service-type=exec` output and the retained unit's
`systemctl --user show` properties; the recorded peak was 64 MiB. The caller
captured result/status/peak, ran `reset-failed`, and verified the unit was
`not-found/inactive`. The command's nonzero exit was specifically classified
as OOM. By the time status was queried, the cgroup path/event files were gone,
so this test did not capture post-exit `memory.events`.

This verifies one host-level external OOM-observation and cleanup path. It is
not V2.12 adapter integration, a request/inference pilot, or evidence of
response deadlines, watchdog handling, receipt persistence, repeated-job
cleanup, or universal supervisor survival. Preserve failed unit metadata until
a receipt is stored; do not collect the unit first. No data, model, training,
match, or outcome was used. The compute proposal remains unapproved pending
independent review.


## Research update: action-sensitive JEPA and counterfactual planning prior art (2026-10-03)

Primary-source review of two recent arXiv preprints materially narrows V2.12's
novelty scope. AD-WM (Qiu et al., arXiv:2609.30264v2) combines factual latent
transition prediction with action-recovery objectives and evaluates CEM
candidate selection using shared-sequence counterfactual diagnostics and elite
regret. ActSWM (Gan et al., arXiv:2607.26712v2) combines multi-step JEPA
rollouts with action-contrastive rollout separation and a frozen action
readout, and reports Minecraft planning plus offline gameplay action recovery.
Neither paper tests exact legal transitions and finite-horizon worst-case
max-min decisions in deterministic alternating two-player games; both are
preprints and their results were not independently reproduced in this audit.
The sources eliminate standalone novelty claims around multi-step JEPA,
action-aware dynamics, counterfactual planning, or cross-game action recovery.

The remaining candidate is an empirical, compute-matched question about
minimax decision regret in the narrowly declared board-game scope. V2.12-04
still trains only on recorded trajectory branches; its support-count proposal
does not prove action ranking over complete legal sets. Before any fit/model
scoring, a versioned independent review must decide on an action-sensitive
JEPA control and freeze legal-root action scoring plus bounded-reference
regret. Reviewed v04 remains unchanged; training, matches, and superiority or
novelty claims remain unauthorized. Source comparison is in
`docs/RELATED_WORK.md` and `docs/V212_RESEARCH_GATE.md`.


## Decision-regret metric design draft (2026-10-03)

Static source inspection found that the compute-only alpha-beta runner shares
the incumbent alpha between root actions, uses the temporary root score map
only for selection, and discards it. Later root-action values may be bounds;
the frozen random-weight pilot receipt does not record actions or values.
Therefore no retrospective decision-regret analysis can be derived from that
receipt. A new design proposal is in
docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md: it defines
root-perspective regret against one common exact or explicitly bounded
max-min reference, requires complete exact scores for every legal root action,
labels missing/bound cases rather than converting them to point estimates, and
keeps reference values out of training. This is a draft only; reference
heuristic/depth and evaluation allocation are unresolved and require
independent review. No scoring, code changes, or pilot were performed.


## Exact-regret oracle scope audit (2026-10-03)

The legacy two_player/evaluate.py plus two_player/games.py::exact_value path
provides a precedent for all-legal-root scoring and complete-case regret, but
only on tiny registered games (tic-tac-toe, connect3 4x4, reversi4, and held
out connect3 3x4). Its full-game solver is unbudgeted and warns callers to
restrict state-space size. V2.12's compute runner targets Connect Four 6x7/8x8
and Reversi6/8 and does not emit root scores. No pinned bounded-reference
nonterminal evaluator/config was found in the inspected V2.12 runner/game
path, despite the method spec requiring one for larger bounded references.
Keep exact solved and bounded-reference results separate; resolve the latter
before model scoring. No solver, dataset, model, or pilot was run.


## V2.12 data-generator compatibility finding (2026-10-03)

A static source audit documents in
docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md that V2.8's exact
Connect Four 6x7 and Reversi6 rules and full-episode replay may be reused as
implementation references, but its generator cannot produce V2.12-compliant
training data unchanged. V2.8 train policy assignment covers only the two
opposite uniform/tactical seat pairs, while V2.12 requires all 16 ordered
policy pairs; V2.8 applies its own split/phase/duplicate rules and materializes
H1/H2 records, not V2.12 H0-H4 windows with H1/H2/H4 targets. The synthetic
V2.12 auditor does not generate data. This proves incompatibility only; data
feasibility, leakage, and the 928-window quota remain untested. No corpus was
read or created, and all generation/training gates remain closed.


## Behavior-policy source audit (2026-10-03)

The V2.8 generator's four policy names now have a source-backed semantic
description in docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md.
Uniform samples legal actions; tactical filters immediate wins and one-ply
opponent wins; positional samples from a handcrafted board heuristic;
bounded-search is depth-four alpha-beta capped at 192 nodes and may stop before
scoring every legal action. These define the synthetic behavior distribution;
none is an expert label or the V2.12 bounded-reference oracle. V2.8 assigns
policy pairs from split/episode parity and uses one action RNG stream, while
V2.12 needs its own frozen 16-pair draw and RNG derivation. This is source
inspection only. No policies, data, models, or roots were generated.


## External exact-reference candidate audit (2026-10-03)

Read-only inspection pinned Markus Thill's MIT-licensed Connect-Four
framework to upstream commit `2a58844594ac022846385dd3ddc8bbbf0a26eae5`.
Its README claims exact game-theoretic position and state-action values.
Source inspection found `AlphaBetaAgent.getNextVTable`, which iterates legal
columns and evaluates each child through a fresh full-window `rootNode(true)`;
the default search depth is 100 for a 42-cell board, and passing a null
opening-book object disables book lookups. This is a plausible exact terminal
minimax candidate for valid reachable nonterminal Connect Four 6x7 roots.

The source hard-codes 7x6 and cannot cover Connect Four 8x8 or Reversi. This
finding is not independent correctness verification: no code or position was
run. Player-1 value orientation and win-distance scores require reviewed
root-perspective win/draw/loss normalization; legal-action completeness,
reachability, turn and terminal contracts, license provenance, and bounded
runtime remain unverified. Treat the source as a candidate only. It does not
close the overall exact-reference gap and does not authorize root/model
scoring, data generation, training, or matches. No local files were changed;
see the updated remote decision-regret design and research gate.

## Exact Connect Four reference-source audit (2026-10-03)

A primary-source pass found several standard-board exact references. The
MIT-licensed Rust `connect-four-ai` at pinned upstream commit
`28a112adaf3ff89ee23fb09411fa592b6597010e` exposes per-legal-column exact
scores, but assumes a valid nonterminal state, scores from side-to-move, and
encodes win/loss remoteness. Its no-book hard-opening benchmark averages
5.09 s by the author's report; this is not our measurement, and its API has no
call deadline. Pascal Pons's solver exposes exact per-column analysis under
AGPL-3.0-or-later. Böck (2025) reports a 89.6 GB strongly solved W/D/L table
built in 47 h using 128 GB RAM. The BDD repository had no license file in the
inspected tree. See `docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`
and `docs/RELATED_WORK.md`.

These sources narrow the candidate-oracle gap for Connect Four 6x7 only.
They do not cover 8x8 or Reversi and do not establish an integrated,
resource-bounded oracle. The 10,000 planner-node/5-second V2.12 proposal is
not comparable to third-party internal counters/timing. Exact regret still
needs reviewed root-player W/D/L normalization, a decision about whether
remoteness is secondary, complete legal-action results, and an independent
hard-deadline/resource contract. No solver was run, installed, or queried;
no scores, roots, data, models, or outcomes were produced. All generation,
scoring, and training gates remain closed.


### V2.12 focused request and symmetry regression check (2026-10-03)

The current `main` adapter already contains the corrected cgroup explanation: `memory.oom.group=0` avoids group OOM behavior but does not guarantee supervisor survival; its focused test asserts that wording. A focused run on the local working checkout passed all 7 request-adapter tests and both bounded symmetry tests (9 total). The adapter and test semantics match the verified remote versions for this check. The local checkout was not synchronized or edited during this continuation. This is software-contract regression evidence only: no cgroup OOM integration, request pilot, data generation, scoring, training, matches, or outcome inspection was performed. Independent review and integrated receipt validation remain open; all research gates remain closed.


### V2.12 Reversi8 weak-solution prior-art check (2026-10-03)

- Read Takizawa, *Othello is Solved*, arXiv:2310.19387v3. The result is a weak solution from the standard initial 8x8 position (draw plus a strategy guaranteeing at least a draw), not a strong solution for arbitrary reachable positions. The paper explicitly leaves all-position “semi-strong” solving as future work.
- The proof uses targeted subproblems and a modified Edax engine; the source repository carries GPL-3.0 and analysis outputs are hosted separately. Nothing was downloaded, installed, run, or queried.
- Static comparison with two_player/games.py suggests the Reversi8 opening, alternating turns, flips, forced passes, and terminal disc-count result align with standard Othello. This is not a verified adapter contract.
- This gives an opening-position theoretical anchor, but not complete values for every legal action at the benchmark's sampled roots. Exact/bounded regret, generation, scoring, and training gates remain unchanged. Source: [paper](https://arxiv.org/pdf/2310.19387), [pinned modified Edax source](https://github.com/eukaryo/edax-reversi-AVX-v446mod2/tree/fbec6a324775b55cafe4a6d9691d92b3fdde2ffc).


### V2.12 decision-metric JEPA prior-art update (2026-10-03)

- Reviewed Wang et al., *Decision-Metric Alignment in Latent World Models: Diagnostics and Action-Conditioned Objectives for MPC Planning*, arXiv:2608.18746v1 (submitted 2026-08-19). It introduces Plan-Real and CEM-stage Spearman and DA-LeWM, which adds inverse-action and demonstration-conditioned goal-action heads to an action-conditioned LeWM predictor.
- The overlap closes standalone novelty claims around action-conditioned JEPA planning, inverse/goal-action auxiliary objectives, and generic candidate-rank diagnostics. The study is single-agent Euclidean-goal CEM over four robotics tasks; it does not evaluate complete legal root actions under alternating two-player zero-sum max/min.
- The authors report near-zero/negative elite-stage CEM Spearman for all variants, including DA-LeWM, despite positive random-stage gains. They report one training run per configuration and three evaluation seeds. Treat as preprint evidence, not independent replication.
- A root-player decision-regret question under adversarial finite-horizon backup remains only a candidate distinction; novelty is unresolved. Before fitting, independent review must decide whether to add an inverse-action control and how to avoid treating logged policy goal-actions as optimal decisions.
- No local files, CAISSA code, data, outcomes, or gates changed. Source: [arXiv paper](https://arxiv.org/abs/2608.18746).


### V2.12 inverse-action control design checkpoint (2026-10-03)

- The v04 predictor already receives exact actions, and all arms already share a recorded-root-action policy loss. DA-LeWM's inverse head is therefore a distinct auxiliary-pressure control, not evidence that current v04 lacks action conditioning.
- Added docs/V212_INVERSE_ACTION_CONTROL_DESIGN_01_DRAFT.md on the remote branch. It proposes, for independent review only, a factorial crossing the six v04 arms with inverse-action loss on/off, using exact observed state transitions, legal masks, and action 64 for forced pass. It explicitly labels this as potentially redundant and gives no outcome or performance prediction.
- The draft rejects logged future-action sequences as optimal labels: they represent behavior-policy choices, may be non-unique for a state/goal pair, and do not encode minimax value. A future goal-action behavior-control would need a separate estimand.
- No current method, data, code, tests, root schedule, or gate changed. No training, scoring, match, or outcome access occurred. Independent review must decide the extra factorial's necessity, compute parity, loss scale, and multiplicity before any fitting.


### Inverse-action draft weighting clarification (2026-10-03)

Clarified that the proposed inverse-action loss is averaged over transition
slots in the frozen v04 windows. Overlapping windows may repeat a source
transition; the draft now requires counts for slots, transition IDs, repeat
frequency, and distinct state/action/successor content. Repeated slots are
training exposures, not independent observations, and are not silently
deduplicated. This only clarifies the unreviewed proposal; no data, method,
or gate changed.
