# CAISSA-JEPA research roadmap

Version 1 — 2026-09-29. Sizes are relative, not completion-date promises. Q1 is a quality target; acceptance and positive outcomes are unknown. See Ground Truth first and the source review in `docs/RELATED_WORK.md`.

| Milestone / size | Depends on | Deliverables and acceptance | Status |
| --- | --- | --- | --- |
| M0 memory and inventory / small | None | Preserve all branch commits/prompts; classify all Markdown; copy with SHA checks; open Ground Truth in existing Obsidian | PASS: 22 initial documents at `D:/notes/vault_1/Caissa-JEPA`; source baseline 70 tests pass |
| M1 repository consolidation / small | M0 | Main includes both branches; verified milestone commit/push; change default to main; delete only merged branches; remote/local verification | In progress, main created from f8588e8; no branch deleted yet |
| M2 positioning and design / medium | M0 | Primary-source matrix including RePAIR/SPR/EfficientZero/AlphaZero/MuZero; data license register; frozen method v1; independent audit | Documents created; independent code audit received; method below is a specification, not results |
| M3 correctness and modular games / medium | M1,M2 | Repair reproduced leakage/ablation/terminal flaws; GameSpec supports legal transitions/terminal/role transforms; multiple game families; rule/oracle tests and negative tests | Pending |
| M4 audited generated pilot data / medium | M3 | Versioned manifests, SHA/provenance, replay every trajectory, duplicate/symmetry checks, four nonempty splits per trained game; explicit quarantine counts and holdout | Pending; audit failure blocks training |
| M5 representation/training runtime / medium | M4 | Shared weights across supported adapters; JEPA H1/H2, H1/no-response/no-regularizer controls, policy-value and decoded-dynamics; gradients, masks, seed/resume/atomic serialization, source/config/data fingerprints | Pending |
| M6 bounded exploratory pilot / medium | M5 | At least 3 seeds, all-legal policy/value and collapse diagnostics; same-search comparisons; time/memory and per-game results; held-out variant zero-shot; negative results retained | Pending; small CPU scope only |
| M7 development and model selection / large | M6 pass | Fix weaknesses using development data; extend heterogeneous games/chess adapter; opponent pool/random/reference/self-play; independent rule validation; held-out whole game and few-shot comparison; matched wall-time and active compute tracks | Pending; do not silently extrapolate pilot |
| M8 locked confirmatory study / large | M7 pass | Freeze independent referee/teacher identity, dataset/checkpoint/config/source hashes, primary metric, paired schedule/seeds/sample size/CI/multiplicity/censor/stopping rules; complete uncensored planned set | BLOCKED until readiness review; no fabricated protocol values chosen after outcomes |
| M9 paper and reproducibility release / large | M8 or documented negative pivot | Systematic review updated; method/ablations/negative findings/limitations/threats/license/reproduction statements; independent review; artifacts storage plan; no Q1 guarantee | Pending |

## Experiment stages and budgets

Exploratory pilot: generated tiny games and fixed small configurations, single CPU BLAS thread, no paid/GPU resources. Record time, peak memory where measurable, sample exclusions, per-seed metrics. These data can diagnose implementation/feasibility and inform development; they cannot become confirmatory by relabeling. Start with a bounded run (minutes, small tens of MB model/data target), measure actual resource cost, and stop on numerical/audit failure. Increase only if the measured pilot supports a useful question within local resources.

Development: train and validation are available for debugging/hyperparameters. Model-selection: freeze a finite candidate/budget list first, compare using a distinct split, log every attempt and selection. Locked-final-test: no performance inspection until separate confirmatory manifest is complete. A dataset being marked locked is not technical access control; evaluator stage gates and an immutable run ledger are required.

Tiny-game exact minimax regret and exploitable-policy best response support correctness diagnostics; match score alone is not exploitability. Representation losses and behavior-label ranking do not measure optimal play. End-to-end systems with different search belong in a separate table from same-search architecture comparisons.

## Risks and kill criteria

- **Novelty:** JEPA, SPR/EfficientZero consistency, board-game latent planning and size transfer already exist. If the method adds no controlled benefit, narrow to negative/benchmark evidence or pivot; never claim novelty from a name.
- **Data:** strict context/target/symmetry isolation can destroy small-game coverage. If any training/validation/selection/final split becomes empty, stop that training design; redesign collection/scope with a new version before reading final performance. No leakage exemption added after seeing results.
- **Learning:** any nonfinite loss/gradient/checkpoint, wrong perspective, missing-mask leakage, failed numerical gradients or collapsed rank blocks progression. Effective rank below 2 or median dimension std below 1e-3 on diverse validation states is an immediate collapse alert, not a universal theorem.
- **Scientific benefit:** if JEPA fails to improve over policy/value and decoded-dynamics under same-search and resource reporting across at least two game families, no broad planning-improvement claim. A pilot with inconclusive seed variation warrants development, not significance claims. If no-response matches/full beats only at extra cost, drop opponent-specific or efficiency claims.
- **Transfer:** separately trained per-game models do not prove a shared model. Held-out variants are weaker evidence than held-out families; report exactly which. If benefit only exists after game-specific retraining, narrow to per-game regularization.
- **Fairness/compute:** exact rules expose information unavailable to a fully latent world model. Disclose the hybrid planner. Equal nodes/parameters do not imply equal FLOPs/time. Stop comparisons with uncontrolled timeouts, ignored errors or mismatched teachers.
- **Rules/referee:** external UCI evaluation is not independent terminal adjudication. Confirmatory chess remains blocked until independent full-history replay agrees.
- **License/storage:** uncertain rights block that source only. Local project-owned procedural data is the fallback. No cloud spending, external restricted uploads or large Git blobs.

## Update rule

Commit verified milestones on main, push without rewriting history, verify remote SHA, and mirror all Markdown to Obsidian. Record reviewer findings and repairs. Mark only deliverables actually executed as complete. Unfinished study stages must remain explicit, even when engineering tests pass.
