# CAISSA-JEPA research roadmap

Version 1 — 2026-09-29. Sizes are relative, not completion-date promises. Q1 is a quality target; acceptance and positive outcomes are unknown. See Ground Truth first and the source review in `docs/RELATED_WORK.md`.

| Milestone / size | Depends on | Deliverables and acceptance | Status |
| --- | --- | --- | --- |
| M0 memory and inventory / small | None | Preserve all branch commits/prompts; classify all Markdown; copy with SHA checks; open Ground Truth in existing Obsidian | PASS: 22 initial documents at `D:/notes/vault_1/Caissa-JEPA`; source baseline 70 tests pass |
| M1 repository consolidation / small | M0 | Main includes both branches; verified milestone commit/push; change default to main; delete only merged branches; remote/local verification | PASS; 135a690 pushed, default main, other branches integrated and deleted |
| M2 positioning and design / medium | M0 | Primary-source matrix including RePAIR/SPR/EfficientZero/AlphaZero/MuZero; data license register; frozen method v1; independent audit | Documents created; independent code audit received; method below is a specification, not results |
| M3 correctness and modular games / medium | M1,M2 | Repair reproduced leakage/ablation/terminal flaws; GameSpec supports legal transitions/terminal/role transforms; multiple game families; rule/oracle tests and negative tests | Implemented and tested; independent review repairs applied; independent rules for all games still deferred |
| M4 audited generated pilot data / medium | M3 | Versioned manifests, SHA/provenance, replay every trajectory, duplicate/symmetry checks, four nonempty splits per trained game; explicit quarantine counts and holdout | Whole-game audit FAILED; amended middle/late v1.2 PASSED; failed artifact retained |
| M5 representation/training runtime / medium | M4 | Shared weights across supported adapters; JEPA H1/H2, H1/no-response/no-regularizer controls, policy-value and decoded-dynamics; gradients, masks, seed/resume/atomic serialization, source/config/data fingerprints | Implemented seven variants including value-dynamics; gradients/resume/masks pass; pilot next |
| M6 bounded exploratory pilot / medium | M5 | At least 3 seeds, all-legal policy/value and collapse diagnostics; same-search comparisons; time/memory and per-game results; held-out variant zero-shot; negative results retained | Executed 21/21 runs at 66ff9f2; no demonstrated JEPA benefit, severe diagnostic ceiling; see pilot report |
| M7 development and model selection / large | M6 evidence | Fix weaknesses using development data; extend heterogeneous games/chess adapter; opponent pool/random/reference/self-play; independent rule validation; held-out whole game and few-shot comparison; matched wall-time and active compute tracks | PIVOT: benchmark redesign first; scaling current training is stopped by the benefit/coverage gates; selection remains unopened |
| M8 locked confirmatory study / large | M7 pass | Freeze independent referee/teacher identity, dataset/checkpoint/config/source hashes, primary metric, paired schedule/seeds/sample size/CI/multiplicity/censor/stopping rules; complete uncensored planned set | BLOCKED until readiness review; no fabricated protocol values chosen after outcomes |
| M9 paper and reproducibility release / large | M8 or documented negative pivot | Systematic review updated; method/ablations/negative findings/limitations/threats/license/reproduction statements; independent review; artifacts storage plan; no Q1 guarantee | Exploratory working paper and reproducibility report drafted; submission-quality study remains incomplete |

V2 M7 progress: preserved failed survey01/02, passed prospective survey03 on
Connect4 4x5/Reversi6; full fork audit passes509 training/209 development roots.
Frozen `docs/METHOD_V2.md` replaces v1 only for this new development cycle.
Six recurrent/direct objective families and a finite36-cell learning-rate/seed
grid are implemented for integration review. No selection/final predictions or
v2 superiority claim. Development promotion requires the declared0.05 margin,
both-game gains and paired-seed consistency against all tuned control families.
Further capacity/weight/compute studies and independent selection remain gates.
Grid01 then completed36/36 with no failures/censors/collapse, but rjepa0.249145
did not beat stronger value-dynamics0.247664. Preserve all results; next is a
diagnostics-driven finite amendment with equally strong controls. Selection/final
remain closed. This is continued M7 development, not a passed promotion gate.
V2.1 next finite cycle uses coherent legal-symmetry augmentation for all controls
and a small equally offered latent/reconstruction weight grid (60cells). Capacity,
labels and original v2 code remain unchanged. See METHOD_V21; group-relative
decision geometry remains a separately declared later hypothesis if warranted.

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

Evidence-driven decision after the fixed 21-run pilot: preserve all outputs and
do not increase epochs, replace the schedule, select a favorable seed or open
final predictions. Every learned exact-state variant hits zero regret, connect3
has only two roots with no neural leaves, and full hybrid JEPA does not improve
over direct/decoded controls. This fails the broad-benefit gate without disproving
JEPA generally. The next design must be separately versioned before fitting:

1. Generate a new development situation bank, independent of this exposed pilot;
   use rule-only admission criteria and predeclared strata beyond search depth.
2. Require at least100 independent root situations per scientific game, with
   at least50 having nonterminal depth2 leaves and unequal exact action values.
   These are proposed engineering floors, not a statistical power calculation.
   If a game cannot support them, retain it only as a correctness fixture.
3. Pin and differential-test an independent rules implementation for every game;
   record exact oracle/reference costs and source/license identities.
4. Add untrained and recurrent multi-step-trained consistency controls, balanced
   game sampling and separately matched step/compute tracks. Freeze new budgets
   after measuring oracle feasibility, before comparing learned objectives.
5. Only after that benchmark passes and new exploratory evidence is informative,
   resume M7 training, opponent/match studies, held-out-family/few-shot work and
   model selection. M8 needs a power-based final sample size and an independent
   readiness review. Do not relabel this pilot as confirmation.

Commit verified milestones on main, push without rewriting history, verify remote SHA, and mirror all Markdown to Obsidian. Record reviewer findings and repairs. Mark only deliverables actually executed as complete. Unfinished study stages must remain explicit, even when engineering tests pass.
