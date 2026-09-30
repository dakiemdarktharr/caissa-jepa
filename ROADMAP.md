# CAISSA-JEPA research roadmap

Version 1 — 2026-09-29; V2.7 positioning amended 2026-09-30. Sizes are relative, not completion-date promises. Q1 is a quality target; acceptance and positive outcomes are unknown. See Ground Truth first and the source review in `docs/RELATED_WORK.md`.

Latest positioning gate: primary-source review now includes Athénan
(JMLR 2026) and its AAMAS 2023 comparison with Polygames, plus AAAI 2025
approximate state abstraction for two-player zero-sum Markov games, TMLR 2023
cross-game/variant transfer of policy-value networks, and board-size transfer
in Hex. Generic joint-action JEPA, opponent-conditioned imagination,
tree-supervised value learning, minimax search, minimax-sufficient state
abstraction, and game transfer are not novelty claims. The retained candidate
combines complete legal-reply-set prediction with a separately ablated minimax
action-order objective, but methodological distinctness remains unverified and
V2.6 teacher coverage failed at prior budgets. This combination must be
distinguished experimentally from Athénan-style tree-value learning,
minimax-Q/approximate abstraction, direct policy-value transfer, and ordinary
task/feature prediction before any training. Require model-blind target
coverage and a fair measured-compute comparison. If that design is infeasible or
adds no decision quality at matched compute, pivot to a benchmark or
negative-results paper rather than relaxing gates. The broader audit also found
path-consistency AlphaZero (PCZero, ICML 2022) and regularized model-free
two-player game learning (ICML 2026 accepted). The candidate must be
distinguished from these compute-efficient controls; no training yet.

Latest M7 evidence: V2.5 grid05 completed all42 cells and independently passed
its artifact/source/data/schedule audit. It was **not promoted**: raw-tail's
exact-state improvement over direct was only0.001329 (paired-root descriptive
95% interval[-0.023899,0.026938]); it regressed Reversi6, favored only one seed,
and failed the required0.05 margin. Hybrid raw-tail lost to direct by0.064565
regret (improvement interval[-0.126889,-0.005814]); its mechanism gate also
failed against uniform/scaled latent and scalar-tail controls. Close this recipe
as a valid negative development screen. Keep grid04 as an inconclusive runtime
failure and preserve both attempts. See `docs/V25_GRID05_RESULTS.md`.

V2.5 is closed as a valid negative development screen; its external Reversi
rules audit is complete and limited to tested rules compatibility. The next
milestone is V2.6 **research/design feasibility**, not another loss sweep. New
primary-source review and two independent gpt-6-luna/high reviews found that
game-variant transfer, predictive board-game consistency, JEPA visual OOD, and
adversarial simulator learning all have relevant prior art. In a fully observed
Markov game, predicting the sequential moves of both players is not itself
opponent-behavior modeling: minimax already searches both actions. Keep those
research questions separate.

V2.6 candidate: test whether a shared action-conditioned JEPA representation
improves sample efficiency of minimax decision quality on complete held-out
deterministic rule variants. This is an unverified hypothesis, not a novelty
claim. A bounded first step uses project-owned procedural rules and local data
to validate split hygiene, hard-root coverage and oracle cost, reusing the
existing padded 198-feature/65-action interface only within its 8x8 board and
known-rule limits. No fitting until the gate passes. Cross-game claims require
at least two distinct held-out rule families; a board-size-only split supports
only within-family variant transfer.

Before freezing `METHOD_V26`: independently verify source-level novelty scope;
include an equal-update/equal-data track to isolate objective effects and a
separate equal-measured-compute track for bounded planning; include direct
and recurrent policy/value, MuZero-style task-prediction/recurrent, explicit
feature-transition, JEPA, and a separate exact-rule system baseline. The
candidate primary metric is held-out equal-variant macro AULC of exact minimax
regret versus measured training compute with fixed matched inference search/time;
equal-transition AULC is secondary for sample efficiency.
Opponent policy behavior, when studied, gets a separate opponent model and
metric, never a minimax label. Freeze practical margin/sample size using
development variance before selection. If no fair, feasible test distinguishes
JEPA from the controls, pivot to a benchmark/negative-results paper instead of
reusing exposed roots. User approved gpt-6-luna/high for the current independent
reviews; ask again for any other self-created agent configuration.

V2.6 source-novelty and protocol reviews are complete for this draft. The
protocol reviewer found no conceptual blocker and required an explicit AULC
terminal interval and frozen update-plus-checkpoint/log reserve; both are now
specified in `docs/METHOD_V26.md`. The bounded interface smoke passed on one
Connect4-5x5 and one Reversi8 sample set against the project-owned reference
rules, with receipt `docs/validation/V26_INTERFACE_SMOKE_01.json`. This only
supports feasibility of the current encoded adapter and sampled two-ply
closure. Next gates remain: a reproducible source-level novelty disposition,
independent/admissible rule and oracle cost review for candidate variants, and a
frozen split/data/selection/compute protocol. No V2.6 labels or training have
been produced; the method is still a proposal and cannot yet support a JEPA-win
or Q1-readiness claim.
The exploratory exact-oracle probe in `docs/validation/V26_ORACLE_FEASIBILITY_01.json`
solved only2/5 nonterminal Connect4-4x5 roots within 100k nodes/1s. This small
sample is a warning about variable label cost, not a population estimate. Root
admission cannot depend on oracle completion: predeclared solver timeouts count
against coverage, and failing that gate forces a narrower domain or a new
method version before labels/training.
An exact alpha-beta/transposition solver was then implemented against the
project-owned reference rules. It matches plain exact labels across sampled
small-game states and two solved Connect4-4x5 roots; its five focused tests
include all5,478 reachable Tic-Tac-Toe states, and 15 rules/reference tests
pass. On the same five nonterminal roots it solved4/5
versus2/5 within1s. This supports further feasibility only; one root still
times out, and the sample cannot establish coverage. See
`docs/validation/V26_ORACLE_FEASIBILITY_02.json`.
The full repository suite passes322 tests (115.2s) after the solver addition.
The pinned-seed model-blind probe then solved17/24 Connect4-4x5 candidates,
13 of which had unequal exact action outcomes. It solved all eight Reversi6 and
Reversi8 roots chosen at eight or fewer empty cells, but these late-game states
are mostly cheap for exact search. This suggests Reversi endgames are a weak
primary planning challenge, while Connect4 midgame still has costly roots.
Full per-root cost receipts are under `docs/validation/V26_ORACLE_FEASIBILITY_03_*`;
none of these exploratory roots may be reused as locked confirmation data.
The gravity variant sharpens the tradeoff: Connect4-4x5 solved22/22 roots at
plies5-11 within1s (17 informative), but only4/12 early-ply1-4 roots (1
informative) on the reproducible script rerun; a prior inline probe solved5/12,
showing threshold variability. On Connect4-gravity-8x8 only1/10 sampled nonterminal roots solved
within1s, and only1/3 fixed roots within5s. The larger domain is more search-
challenging but this exact-label pipeline is too costly at current limits; the
small domain is cheap enough for exact search to dominate. V2.6 exact-supervised
work must either find a model-independent oracle/compute protocol between those
extremes or pivot to outcome/self-play evaluation with paired fixed-budget
matches. Do not filter hard roots post hoc. See
`docs/validation/V26_ORACLE_FEASIBILITY_04_*` and
`docs/validation/V26_ORACLE_FEASIBILITY_05_CONNECT4_8X8*.json`.

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

V2.5 closure criteria: all42 planned cells complete; strict result is
`not_promoted`; independent audit is `verified`; all192 prior-attempt tensor
references pass; no selection/final inputs opened; public aggregate/plots derived
from strict report; results and limits recorded in Ground Truth, this roadmap,
professor dossier and Obsidian. The third-party Reversi4/6 differential audit
now also passes (100 seeded trajectories/size; 183,612 trajectory comparisons;
zero mismatches), within its explicitly limited rules-compatibility claim.
Closure work passed: result, reviewer limits and vault sync are recorded;
targeted tests passed; milestone is committed and remote-verified. The built-in
LaTeX compiler remains unavailable on this platform, and current Computer Use
cannot reopen Obsidian for a new visual check; neither limitation changes the
hash-verified file-copy evidence.

| V2.6 gate / relative size | Deliverables and acceptance | Stop condition | Status |
| --- | --- | --- | --- |
| Related-work and hypothesis audit / small | Primary-source matrix; distinguish task-prediction, JEPA state prediction, minimax, and opponent behavior; state only a testable incremental claim | Same sequential objective/evaluation already established, or no defensible difference | Primary-source matrix and two reviews complete; method proposal revised and undergoing final read-only audit |
| Procedural benchmark feasibility / medium | Reuse/test padded <=8x8 state/action interface on held-out project-owned deterministic variants; independent rule checks; oracle-cost and hard-root coverage; grouped splits before labels | Oracle cheaper at target quality, insufficient hard roots, or any split/label leakage | Not started; design gate must pass before training |
| Matched development comparison / large | Frozen method/config and finite runs; shared capacity/data/schedules; direct+recurrent PV, MuZero-style task prediction, feature transition, JEPA; exact solver separately; paired seeds and full resource curves | JEPA fails predeclared per-family AULC margin/replication or fails compute comparison | Not started |
| Locked confirmation / large | Untouched variants; power/multiplicity/censor protocol; independent artifact audit | Development gate fails or test access/compute integrity fails | Not started |

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
Grid02 completed60/60 but failed promotion: +0.004826 against strongest control,
interval includes0 and one per-game gate fails. M7 now tests the explicitly
narrower label-access hypothesis in METHOD_V22;72cells after redaction/mask audits.
This does not erase the full-label negative findings or establish any superiority.

Grid03 completed all 72 cells and also failed: scarce raw JEPA regret 0.293339
versus direct 0.283917, improvement -0.009422 with descriptive 95% interval
[-0.075730, 0.047922]. All 30,096 learned decisions and 836 controls passed
verification. Do not continue blind weight searches on the same affine recipe.
Next dependency is the train/development value-alignment diagnosis and a finite
training-only convergence/capacity check, before selecting an architecture
amendment. `docs/V23_RESEARCH_OPTIONS.md` is a proposal, not an executed method.
Final/selection remain closed; none of these grids is a promoted candidate.

V2.3 training-only diagnosis completed18/18 with72 verified snapshots. Both
additional epochs and larger total capacity improve training fit across all
families; direct remains better than rawJEPA on final mean training S. There is
no demonstrated plateau or superiority. Before another M7 development grid,
freeze a finite common training-budget decision and strengthen all relevant
controls equally. An optional bounded additive-order feasibility probe can test
whether the current transition conflicts with fixed EMA targets; mathematical
restrictions alone do not establish a planning bottleneck. Generic random
minimum-probe fitting is deferred after counterexamples, not scheduled for a
blind grid. See V23_FIT_DIAGNOSTIC and the conditional V24 critique notes.

## Experiment stages and budgets

## V2.7 pivot proposal (2026-09-29; not frozen)

V2.6 exact-minimax-supervised work did not pass the oracle-feasibility gate:
small roots are too easy for the intended bounded-search question and sampled
Connect4-8x8 midgame roots mostly time out. Do not cherry-pick solved roots or
fit on the exposed feasibility samples. A separate proposal,
`docs/V27_RESEARCH_POSITIONING.md`, explores locally generated self-play outcome
trajectories and paired match evaluation on harder variants. This avoids exact
minimax training labels but changes the estimand to performance against a fixed
opponent suite. It cannot support a worst-case, exploitability, or equilibrium
claim without a separate validated estimator.

| Workstream / size | Dependency | Deliverable and acceptance | Current status / kill gate |
| --- | --- | --- | --- |
| V2.7 positioning / small | V2.6 gate failure | Focused primary-source review across competitive JEPA, minimax learning, Markov-game abstraction, and board-game transfer; define and test one incremental question | Search found Deep Latent Competition, MA-JEPA, Athénan, approximate Markov-game state abstraction (AAAI 2025), and direct policy-value transfer across games/variants (TMLR 2023). Novelty risk remains **critical**. Complete legal reply-set prediction plus minimax action-order preservation is only a candidate; it is not frozen or established as distinct. Next: finish source-level candidate audit and identify measurable separation versus Athénan, minimax-Q/abstraction, direct policy-value transfer, and task-prediction controls. No training until that test and model-blind coverage gate pass. |
| Rules and opponent feasibility / medium | Positioning | Project-owned rules for at least two game families; independently check transitions/terminal/role/symmetry; test opponent diversity, non-saturated match schedule, game length and CPU runtime | Depth-3/500-node search agrees with the adapter on 12 seeded trajectories. After Reversi D4/color-role canonicalization, its capped pilot beats random/center controls in 4/4 samples per pairing/family, with 68 cap hits (down from 116 in the preceding two-seed run). Same-policy self-play favors plus/first on both unique seeds (four receipt rows include duplicate seat-swap records); the preceding version favored minus/second on both unique seeds. Seat/RNG effects are unresolved. An independent review found no blocker. Full regression passes 330 tests; receipt source hashes match. Do not generate research data yet; increase seed diversity and independently audit rules. OpenSpiel reference remains uninstalled. |
| Data audit / medium | Rules pilot passes | Local self-play manifest with seeds, policy/opponent provenance, outcomes, hashes, trajectory-grouped splits and replay/duplicate/seat-balance audits | Not started; production data/training forbidden before pass. No third-party corpus or service needed. |
| Method freeze and matched pilot / large | Positioning, feasibility, data audit | Freeze two-ply JEPA plus direct PV, task-prediction, decoded-feature and JEPA-ablation controls; identical trajectory labels, model budget, optimizer schedule and inference planner; at least three seeds; all censors retained | Not started. A match-score result is limited to the declared opponent suite; keep expected-opponent and minimax planners as separate studies. |
| Development and selection / large | Pilot informative | Append-only adaptive development ledger; freeze finite shortlist before distinct opponent/variant selection; paired seats/color, clustered uncertainty and multiplicity/censor rules | Not started. A development improvement nominates a candidate only; no reuse of exposed opponents as confirmation. |
| Locked confirmation and paper / large | Selection and independent review pass | Fresh trajectories/opponents/variants, preregistered primary metric and sample size; independent artifact/rule audit; negative results, novelty limits, license and reproducibility statement | Not started. No Q1 readiness or acceptance claim until evidence and independent review support it. |

Relative effort: positioning (small), rule/runtime feasibility (medium), data
and method implementation (medium-to-large), matched development (large),
confirmation/paper (large). No calendar-duration estimate is asserted.

V2.7 stop rules: stop/narrow if two game families cannot support non-saturated
paired evaluation; if direct or non-JEPA predictive controls match the JEPA
candidate; if benefits vanish against held-out opponents; if effects reverse
by game or seat; if JEPA needs extra transitions/search/parameters; if any
trajectory/symmetry leakage or opponent identity leaks across splits; or if
related work contains the claimed mechanism. A negative controlled comparison
may remain useful science, but does not satisfy the user’s JEPA-superiority
target. All thresholds and sample sizes still need a model-blind pilot before
method freeze; no post-result threshold adjustment is allowed.

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
