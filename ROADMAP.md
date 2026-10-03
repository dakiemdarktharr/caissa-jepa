# CAISSA-JEPA research roadmap

Updated: 2026-10-03. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

## V2.12 checkpoint (2026-10-03)

The lattice session verified cgroup enforcement in disposable user
scopes: a 1.5 GiB `memory.max` was finite and inherited by a child; a separate
64 MiB no-swap scope killed an over-limit child and recorded `oom_kill=1`;
both cgroups were removed after cleanup. A new fail-closed request adapter,
`two_player/v212_request_adapter_v01.py`, checks the exact cgroup limit and
`memory.oom.group=0`, verifies that its worker inherits the same path, applies
absolute 5-second planner and 6-second response deadlines, kills a timed-out
worker group, and distinguishes OOM events from watchdog timeouts. The focused
suite passes 20/20. A no-inference subprocess preflight inside the real 1.5 GiB
scope verified that the worker inherited the parent's exact cgroup path,
`memory.max=1610612736`, and `memory.oom.group=0`; the disposable scope was
removed. No request/inference worker or multi-cell pilot ran. The adapter has no
report/receipt writer and awaits independent review. Keep RSS as sampled
telemetry and the budget as a proposal until an integrated no-outcome run and
receipt review pass. `memory.high` is not a hard limit; see
`docs/V212_HOST_MEMORY_CONTAINMENT_AUDIT_01.md`.

A source audit also found that V2.12-04 calls for counterfactual coverage but
does not define its branch population, denominator, or missing-support
handling. V2.8 reply closure is used for overlap checks, while its model-facing
targets remain observed actions; the V2.12 synthetic helper likewise only
forms observed-path windows. This is a protocol-definition gap, not a result
about model quality or leakage. Before data generation, define behavior
support and complete legal-branch evaluation, distinguish held-out-size
structural absence from ordinary missing actions, and get the versioned
protocol independently reviewed. See
`docs/V212_COUNTERFACTUAL_SUPPORT_AUDIT_DESIGN_01.md`; V2.12-04 remains
unchanged.

The follow-on `docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md` proposes
separate denominators for fitting-data action support, full root decision sets,
and visited-node expansion; it explicitly treats held-out-size exact support
as not comparable. A self-audit removed the pooled legal-edge ratio as a
headline because repeated states and game branching factor can dominate it;
the draft instead reports per-state coverage and state/episode frequency.
It now separates encoder-state exposure from exact transition edges used in
valid nonterminal target unrolls; the eventual trainer's masks must verify that
derivation before corpus generation. A source cross-check found that the
existing trajectory auditor jointly maps state/action paths only for duplicate
window detection; it does not provide a canonical edge-support ledger. The
draft now requires joint `(state, action, successor)` transforms and explicit
legal-set bijection/transition-commutation checks before any canonical edge
summary is reported.
The follow-on `docs/V212_DUPLICATE_AND_OVERLAP_POLICY_AUDIT_01.md` records a
separate source conflict: the frozen synthetic fixture rejects all canonical
duplicate windows, while split amendment v05 proposes retaining repeated fit
content as a diagnostic. A production materializer must not reuse that fixture
unchanged. Source-id uniqueness, prohibited cross-partition overlap, fit-bank
content diagnostics, and symmetry-distinct development roots now have separate
proposed dispositions; all remain subject to independent protocol review.
The source inventory in that audit records the declared in-scope maps (two
gravity-preserving maps for each Connect Four variant; D4 for Reversi), but
`canonical_key` does not return its minimizing map. A bounded
`tests/test_v212_symmetry_properties.py` suite now checks each declared map's
legal-action bijection and transition commutation on deterministic in-memory
fixtures for all four in-scope variants: it exhausts states through four
legal plies, then checks three deterministic paths to terminal plus a
forced-pass Reversi fixture. This remains shallow bounded coverage, not
exhaustive verification of later states; canonical edge metrics remain
disabled pending broader/adversarial code-property review and independent
protocol review.
The earlier design-01 root schedule kept only the first 16
symmetry-unique roots from 64 candidate slots per band, which changes the
accepted distribution. The conflict now has a candidate written resolution
in `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md`: retain repeated states as
separate valid slot draws, define the success-conditional first-passage
estimand, and stratify the crossed bootstrap by occupancy band. Design 02
aligns with the root-sampling amendment but is not frozen; independent
statistical/protocol review must accept the target, RNG assumptions, yield
rule, and inference procedure before generation or scoring.
The candidate resolution is now specified for review in
`docs/METHOD_SPEC_V212_ROOT_SAMPLING_AMENDMENT_DRAFT_01.md`: it defines the
success-conditional first-passage distribution, treats slot IDs as sampling
units, and proposes fixed one-third weighting with within-band bootstrap.
This is a design proposal only; v04 and the existing root schedule remain
unchanged pending independent review. A new conditional-IID argument states
the assumptions needed for the first 16 valid slots to represent IID draws
from the success-conditional law, conditional on the fixed yield gate passing;
it also flags deterministic PRNG streams as an operational approximation and
duplicate/outcome-based rejection as invalidating that argument. The draft
cites crossed and stratified-bootstrap method analogues and small-cluster
cautions with explicit limits; none validates the proposed small-sample
max-T/Holm procedure. The 10,000 replicates improve resampling precision, not
the number of independent seeds or root slots.
This remains a review draft, with no thresholds, data generation, method
amendment, or training authorization. Resolve it alongside the split matrix,
development-root schedule, and compute cap before producing any corpus.

The follow-on source review found that the V02 RSS guard is sampled/cooperative,
not a hard ceiling: the initial sample is not compared to the cap, periodic
checks happen every 256 nodes, and an over-cap final check can escape the
per-depth handler before the runner writes a receipt. Existing pilot tests do
not exercise RSS-cap paths. V02's completed cells remain valid as measured
compute evidence (max sampled RSS 50,212,864 bytes versus a 1.5 GiB cap), but no
future cap-stressed run should rely on this path as hard containment. A
versioned pilot update, RSS branch tests, and an OS/process memory bound are
required before describing RSS as a hard cap. See
`docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md`; no V02 rerun or training is
authorized by this finding.

The v04-authorized random-weight, no-training compute pilot v02 completed
1,152/1,152 cells to four plies; p90 wall time was 0.7970 s, p99 was 2.0148 s,
and maximum was 3.7419 s. Twelve cells exceeded 2 seconds. The 16 roots per
variant and three initializations broaden v01's four-root/one-initialization
sample, but both remain synthetic, random-weight measurements from one host.
The amended protocol and runner passed independent `gpt-6-luna/high` review.
The v02 compute-only report also passed review. The 10,000-node/5-second
planner cap proposal in `docs/V212_COMPUTE_BUDGET_AMENDMENT_05.md` passed
independent review as a proposal only; it is not an operational budget until
request-to-search headroom and the implementation pass pre-fit verification.
No training or match is authorized. See `GROUND_TRUTH.md`, the [v01 pilot report](docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_01.md), and the [v02 pilot report](docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md).

A 2026-10-03 targeted primary-source refresh added the September preprints
`The Planning Limits of Latent World Models` and `ReWAM` to
`docs/RELATED_WORK.md`. They reinforce two existing requirements: measure
decision ranking/regret at each imagined horizon, and distinguish learned
behavioral response models from exact-rule worst-case max/min search. They do
not change the research gate or authorize fitting. The next permitted internal
work is the no-training audit of the candidate multistep trajectory generator,
prior-art distinctions, and request-to-search resource headroom, followed by a
frozen method/protocol review before any fit. A static source audit found a
no-I/O synthetic V2.12 helper that constructs H0–H4 windows from caller-supplied
episodes for fixture assertions, but no production/corpus generator or V2.12
generation protocol. The current V2.8 leak-key audit covers H1/H2 plus two-ply
reply closure, not every V2.12 H0–H4 context/window state and H1/H2/H4 target.
The synthetic helper rejects canonical duplicate windows, while draft v05 calls
for reporting equivalent content diagnostically; production reuse requires an
explicit reviewed policy. A source-level runtime pass also confirmed V02's
per-search clock starts after input validation/model reset, while schedule/model
construction and warmup occur before the call; RSS is sampled every 256 nodes,
and no end-to-end action-response watchdog exists. These are expected pilot
instrumentation boundaries, not evidence the proposed request-anchored cap is
operational.
See `docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md` and the frozen
`docs/V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md`. The in-memory synthetic
fail-closed auditor is implemented, its focused tests pass, and independent
review accepted it for the synthetic-only contract. No data bank or trained
model is authorized by this software-contract step.
The follow-on design note `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`,
`docs/METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md`, and
`docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md` propose train-only fit windows on
training sizes and 48 held-out development root slots per variant. Design 02
supersedes the earlier unique-root proposal by retaining the first 16 valid
slots per occupancy band, including repeated board states, to align with the
success-conditional slot estimand in Amendment Draft 01. This resolves the
written design conflict only; independent review still must accept the target,
slot-independence assumptions, yield gate, band weights, and bootstrap before
any root generation or scoring.

A second targeted literature pass added Semigroup-JEPA and Action-Conditioned
Predictive Consistency to `docs/RELATED_WORK.md`. Recursive rollout JEPA is
direct prior art, so V2.12 can only support a game-specific empirical
increment after matched JEPA and decision-aware baselines. A JEPA-Chess title
appeared only in an aggregator record; no primary Zenodo/DOI source was found,
so its claimed results are excluded as unverified. These findings do not
authorize fitting or root generation and do not change the current gate.

A further primary-source check found PiJEPA (arXiv:2603.25981v1), which trains
an autoregressive multi-step JEPA world model and plans over action sequences
with policy-guided MPPI. Its single-agent continuous-robot task differs from
V2.12's exact legal branches and max/min backup, but confirms that multi-step
JEPA plus planning is established. The bounded comparison is recorded in
`docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`; it narrows the defensible claim to
an empirical incremental effect of latent matching over matched controls.
This is not a novelty finding and does not change the no-fit gate.

The expanded 2026-10-03 source pass added Value-Guided JEPA Planning, H-JEPA,
Delta-JEPA, WA-JEPA, and the game-domain ActSWM. These cover value-structured
planning, action-sensitive latent geometry, joint world/action prediction, and
multi-step JEPA planning in Minecraft. ActSWM is single-agent open-world control,
not zero-sum board play, but removes any claim that action-sensitive JEPA
planning in a game is new. The present candidate lacks those specialized
mechanisms; more critically, none makes its simple multi-step JEPA loss novel.
The V2.12 claim should remain an empirical test of policy-mixture outcome
targets with exact legal max/min, and must beat matched value/state controls to
support even that narrow claim. Before method freeze, a versioned design review
could assess a diagnostic comparing same-root legal alternatives only when
their exact-rule consequences differ, and pairing latent separation with
exact-state, value, and ranking differences. Distinct legal actions need not
map to distinct latents; latent distance alone is not evidence of useful
sensitivity. See the updated [prior-art crosswalk](docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md).

The latest primary-source pass found the author-released 2026
[WorldModel-ConnectX](https://github.com/alextitonis/WorldModel-ConnectX) and
the 2025 [SOLIS chess study](https://arxiv.org/abs/2506.04892). ConnectX
directly overlaps the adversarial board-game setting with a learned latent
model and search, but its deployed minimax uses exact board rules and learned
value leaves; its latent beam is a separate baseline, and training folds one
fixed opponent response into each action transition. It has no EMA-target
JEPA loss. SOLIS is value-aligned latent chess planning without learned
transition dynamics. These results remove setting-level novelty claims and
raise the remaining bar to a matched empirical effect of the specific V2.12
objective. The sources and their limitations are recorded in
`docs/RELATED_WORK.md`; no spec, data, compute, or training gate changes.

## Research objective

Falsifiable hypothesis: an EMA-target JEPA that predicts future latent states conditioned on both players' ordered actions can improve planning under a fixed compute budget over matched non-JEPA baselines, with the benefit retained across a declared family of deterministic, alternating-turn, fully observed, finite-action, zero-sum games. Current evidence does not support this hypothesis. The immediate aim is to determine whether there is a defensible mechanism worth testing, not to tune until a development win appears.

Keep distinct: (a) behavioral prediction for a particular opponent, (b) worst-case optimal-reply modeling, (c) minimax/equilibrium search, and (d) expectation under an uncalibrated policy distribution. Current V2.8/V2.9 is (b)+(c), a depth-two max-min cutoff with a learned leaf evaluator. It is not (a), a full equilibrium solver, or exploitability evaluation.

## Workstreams and gates

| Order | Workstream and deliverable | Acceptance criteria | Relative effort / dependency |
| --- | --- | --- | --- |
| 0 | Provenance and durable memory: `GROUND_TRUTH.md`, Obsidian mirror, Git inventory | Ground Truth states repo/data/results truth; Markdown mirror hash-verified; only `main`; no unknown files overwritten | Small; continuous |
| 1 | Research positioning: `docs/RELATED_WORK.md`, primary-source search log | Cover JEPA/world models, game planning, board-game transfer, objective/gradient routing; describe search limits; make no unsupported novelty claim | Medium; ongoing |
| 2 | Method diagnosis V2.10: frozen gradient-alignment diagnostic spec and implementation | Decomposed loss gradients sum numerically to the existing total; diagnostics report cosine/norm/interference by shared encoder, game and seed on train-only batches; no optimizer update and no locked data access | Medium; depends on V2.9 negative result and new code review |
| 3 | Mechanism decision gate | Proceed only if negative JEPA-vs-task gradient alignment is stable across seeds/batches and is concentrated in shared parameters; otherwise reject gradient-conflict explanation and choose a different hypothesis | Small; depends on workstream 2 |
| 4 | Bounded development experiment, only if gate 3 passes | Compare raw reply-JEPA, predeclared encoder-only conflict-projected JEPA, task-value dynamics and direct leaf; same data, initialization, updates, compute/search, held-out development situations, seeds and rules; independent pre-fit review | Large; new grant, protocol, power/compute check and run artifacts required |
| 5 | Model selection and locked confirmatory evaluation | Separate untouched data/situations, independent schedule, predeclared primary regret/strength metric, practical margin, power, multiplicity, censoring and stop rule; no reuse for tuning | Large; only after development nomination and review |
| 6 | Generalization and paper package | Test held-out variants and multiple admitted games, strength/search costs, representation diagnostics, robustness, negative results, data/license statements, reproducibility and threat-to-validity | Large; after method survives confirmation |

## V2.9 disposition

The frozen three-epoch recipe failed its nomination screen. Under the shared two-ply max-min planner, the JEPA-minus-task-value mean paired score was -0.1375 on Connect4-6x7, +0.0125 on Reversi6, and -0.0625 macro over 20 checkpoint-seed clusters. The artifact has 160 complete paired blocks/320 games, no forfeits/censors, balanced JEPA seat swaps, and schedule-order/replay integrity checks. The outcome starts from fixed standard initial states; uncertainty intervals are exploratory and conditional on scheduled seeds. The JEPA/task-value planner CPU ratios were 1.025 and 1.005. Thus greater search CPU does not explain the result. This is evidence against the tested recipe, not proof against JEPA generally. Stop duration-only tuning.

The machine-readable analysis is `docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json`; raw fit/match/checkpoint artifacts remain ignored. The result is development evidence, not confirmatory inference.

## V2.10 candidate: diagnose before intervening

Candidate mechanism: the model's shared encoder receives gradients from legal-policy/value targets and from reply-set latent prediction. If the latter repeatedly conflicts with decision-task gradients, it may impair minimax-relevant value features despite good latent prediction. First compute gradients independently on the exact same train-only batches, decomposed into policy, root-value, observed-leaf-value, reply-JEPA, and latent-regularizer terms. Do not read historical `train_metrics`/loss curves or locked V08 records. This diagnostic makes no optimizer update and selects no model.

If and only if that predeclared diagnostic gate passes, a subsequent version may apply conflict projection only to the JEPA gradient on shared online-encoder parameters, leaving its predictor-specific gradient intact. The update rule, thresholds, hyperparameters, sample, seeds, and controls must be frozen before any fit. Compare at least raw JEPA, routed JEPA, task-value-dynamics, and direct leaf, on a fresh development schedule and with equal measured training/search budgets. This family is not claimed novel: PCGrad/CAGrad and gradient routing in JEPA Policy are prior art. Any defensible contribution would have to be a demonstrated, reproducible incremental benefit in the explicitly zero-sum reply-set setting and survive strong matched controls.

The diagnostic validated decomposition against the existing summed gradient (real-batch maximum relative error 5.15e-18), used frozen train-only inputs and model/panel hashes, and sampled all 20 seeds × two games × ten disjoint batches of 30 roots. All 400 cells were present with zero invalid/skipped roots and finite values. The frozen gate required, in both games, a seed-level median cosine below -0.05, a 95% seed-cluster interval wholly below zero, and at least 15/20 seeds with conflicts in at least six of ten batches. It failed every criterion: Connect4 median -0.0293, CI [-0.0483, 0.1560], 13/20 persistent-conflict seeds; Reversi6 median -0.0402, CI [-0.0651, 0.1064], 12/20. The correct decision is `stop_gradient_conflict_candidate`; do not fit a projected variant or search for post-hoc subgroups. Full outputs are in [the diagnostic artifact](docs/validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json), independently audited in [the review note](docs/V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md).

The next low-cost model-selection test is frozen in `docs/METHOD_V211_JEPA_WEIGHT_CALIBRATION.md` and `docs/validation/V211_JEPA_WEIGHT_CALIBRATION_V01.json`. It raises only reply-JEPA coefficient from 1.0 to 8.0. At coefficient 1.0, the diagnostic's median encoder-gradient norm ratios `||g_JEPA|| / ||g_task||` were 0.04937 in Connect4 and 0.04550 in Reversi6; the angle screen found no persistent conflict. Scaling by eight is a calibration hypothesis, not evidence of improved play. V2.11 precommits 20 same-seed fits and 240 fresh paired blocks/480 games, comparing the candidate to same-seed λ=1 JEPA, task-value-dynamics, and direct-leaf V2.9 controls. It preserves the +0.05 per-game and macro development nomination margin and V2.9 compute caps. Independent review accepted the protocol/schedule (no P1/P2; implementation requirements P3) and verified the schedule hash `c6574b28767dc29e80c3bfd2ad158c58528561a8dc2c5393c86d54534f33bc2e`. The implementation review found two P2s: whole-receipt JSON parsing and a forgeable supervisor token. Both are corrected by hash-only receipt verification without parsing history, a Job Object membership check, and a hash-bound supervisor status attestation. Four focused tests and a 60-control weights-only validation pass after the changes; the independent final re-review is pending. No V2.11 fit or match has started.

This coefficient adjustment is ordinary objective-weight calibration, not a unique method contribution. Minimax-critical reply weighting remains an alternative only after more review: opponent-conditioned latent planning already appears in two-player MuZero and [Vector Quantized Models for Planning](https://proceedings.mlr.press/v139/ozair21a.html); value-sensitive model fitting and latent value alignment are established in [VaGraM](https://openreview.net/forum?id=4-D6CZkRXxI), [Value-Aligned World Models](https://proceedings.mlr.press/v306/jiang26ai.html), and policy-aware simulator learning. Any later variant must beat equally decision-aware non-JEPA controls and establish its specific incremental difference. No current method is certified novel.

## Kill criteria

- Stop active-superiority claims if a predeclared development candidate does not beat both task-value and direct-leaf at the chosen practical margin in every primary game, or if the effect depends on one seed, one game, extra compute, or post-hoc exclusions.
- Stop gradient-routing work if the diagnosis fails its frozen gate, or if projection does not improve the primary decision metric at equal compute.
- Narrow to a benchmark/methodological negative-result paper if no JEPA-specific mechanism survives matched controls and independent replication.
- Stop/pivot if exact search dominates under the relevant budget, legal/rule/data audit fails, held-out evaluation leaks, or a data license is unclear.
- Do not claim generic two-player coverage: hidden information, simultaneous actions, chance, general-sum utility, behavioral opponent forecasting, and equilibrium/exploitability guarantees need separate methods and evaluations.

## Data, compute, and reproducibility gates

Only locally generated, audited development data with clear provenance is currently used. Do not use third-party data until primary-source license/terms, training rights, redistribution and derivative-output rights are documented. Each manifest must pin SHA-256, parser/rules version, counts, provenance, split, and trajectory/event grouping. Keep raw data, checkpoints, caches, and logs outside Git and the Obsidian mirror. No paid compute or service without explicit authorization.

Before a training panel, freeze the objective, config, data fingerprint, exact split, seed schedule, schedule hash, compute caps, failure/censor policy and source commit; run the locked environment tests and independent review. A development result can nominate a model-selection study only. Confirmatory data stays unopened until all choices are frozen.

## Current status and professor-facing claim

The implementation and evaluation harness can test a narrow JEPA hypothesis, but current measured results do not show JEPA superiority. V2.9 is a negative/mixed development result; V2.10 rejects the gradient-conflict explanation for the tested checkpoints and train-root distribution. The V2.11 λ=8 calibration protocol, fit runner, matcher, and analysis are independently reviewed with no remaining P1/P2/P3 blockers. The first supervisor process disappeared without terminal status and is preserved; dev02 then failed before the fit loop because grant v01 no longer matched the method-note hash. Grant v02 is separately issued and loader-validated on all 1,797 DEV09 train records. Under grant v02, the dev03 fit panel completed all 20 seeds (3 epochs/87 updates) in 582.14 seconds with an attested resource gate and peak working set 859 MB. The 20 candidates and 60 V2.9 controls pass local hash/runtime/weights-only verification; independent panel review is pending. The frozen 480-game development match has not started, so there is still no JEPA strength result. The 9/9 protocol suite, compile, control preflight, and pre-fit runtime checks pass. Loss-weight calibration is not a novelty claim. No cross-game transfer, equilibrium, exploitability, or Q1-readiness claim is established.

## V2.11 execution status update (2026-10-02)

The dev03 panel is complete and independently accepted for the frozen exploratory matcher (no P1/P2 findings). Local verification on the exact fit runtime passed the grant v02, supervisor attestation, all 20 JEPA candidates, and all 60 V2.9 controls without reading training histories or locked-final data. Next: run the predeclared 240-block/480-game DEV09 development match with that runtime, then independently audit transcript integrity and evaluate nomination gates. A pass only nominates later locked confirmation; a failure remains a reportable negative result. No outcome or superiority claim is available yet.

## V2.11 result and V2.12 research gate (2026-10-02)

V2.11 dev03 is complete and independently audited. The frozen λ=8 candidate failed nomination: its equal-weight macro score differences were −0.04375 vs λ=1 reply-JEPA, −0.0500 vs task-value dynamics, and −0.0375 vs direct-leaf. Reversi was negative against every control; all 95% seed-cluster intervals span zero. All compute screens passed, with 240/240 paired blocks, 480 games, no forfeits/censors, and transcript/rule replay plus analysis recomputation independently verified. This is evidence against the calibration recipe only. **Stop λ-only tuning.** See `docs/V211_DEVELOPMENT_RESULT_REVIEW_01.md` and `docs/validation/V211_DEVELOPMENT_MATCH_ANALYSIS_DEV03.json`.

The candidate direction is now multi-step alternating-player latent rollout JEPA: test whether recursive action-conditioned prediction improves horizon-dependent minimax decision quality over the current single-pair predictor, matched task-value dynamics, and direct-leaf controls. The 2026 preprint *One-Step Next-Latent Prediction Is Not a World Model* strengthens the motivation to measure open-loop rollout stability, while established JEPA-WM, MuZero, value-alignment, and policy-aware minimax methods create high novelty risk. This is a research hypothesis only. Do not start coding/training until the V2.12 research gate identifies a precise difference, feasible fixed-compute protocol, and valid train-only trajectory targets. First perform a no-training feasibility and prior-art audit; then freeze the method and independent pre-fit review. See `docs/V212_RESEARCH_GATE.md` and `docs/RELATED_WORK.md`.

| Next gate | Deliverable | Acceptance / kill criterion | Effort |
| --- | --- | --- | --- |
| 1 | Complete V2.12 related-work and adapter/data feasibility audit | Cover closest multistep JEPA-WM, MuZero, value-aligned/policy-aware learning; demonstrate legal variable-horizon target construction and resource feasibility without training | Small/medium |
| 2 | Freeze `METHOD_SPEC_V212.md` and exact panel protocol, conditional on gate 1 | Define role-aware recursive transition, masked multistep loss, candidate and matched controls, runtime/data fingerprints, held-out variant and locked split; independent review accepts before fitting | Medium |
| 3 | Train/match bounded development panel | Equal seeds, examples, training compute and planner budget; complete transcripts; report open-loop latent error, minimax rank/regret, strength by game/opponent, inference cost; no locked data | Large |
| 4 | Nomination and independent result audit | Continue only if candidate passes all-control per-game/macro margin, compute, uncertainty and held-out-variant gates; otherwise preserve negative result and kill this objective | Medium/large |
| 5 | Locked confirmation and multi-game transfer, conditional on nomination | Predeclare primary metric/power/multiplicity/censoring/stopping; independent data/situations; no tuning after unlock | Large |

V2.12 progress: the no-training adapter audit passed for 8×8 Connect Four and Reversi (feature/action dimensions, legal transitions, role alternation, 8-ply samples, and 24 full random episodes each; Reversi forced passes included). `METHOD_SPEC_V212.md` v01 now defines the candidate recursive action-conditioned 1/2/4-ply latent objective and four-ply max-min planner. Independent method/protocol review is the current gate. Passing this review will permit implementation work only; trajectory audit, resource pilot, and a separate pre-fit review are still required before training. No training, outcome data, or V2.12 performance result exists.

Current evidence remains insufficient for a Q1-ready performance claim. The best professor-facing description is a rigorously audited negative development result for two JEPA training recipes (V2.9 and the V2.11 λ increase), plus a tested reproducible benchmark harness; the latter still needs broader games and independent replication before it is a paper contribution.

## V2.12 current gate (2026-10-02)

`METHOD_SPEC_V212.md` v02 is a candidate protocol, not an implementation or fit authorization. It closes reviewer questions about utility perspective, baseline definitions, objective weights, and development-versus-confirmatory claims. The corrected no-training depth-four pilot exceeds the provisional 2-second Reversi8 move cap (rule-only p90 6.037s over 16 roots, before model calls); Connect Four 8x8 p90 is 0.350s over 13 roots. The limited sample diagnoses a compute mismatch but does not estimate worst-case or all-root feasibility. A representative random-weight model-call pilot is still required. Do not fit while the fixed common compute budget is unverified. Revise only from no-outcome measurements, then obtain independent review.

| Gate | Deliverable | Acceptance / kill criterion | Effort |
| --- | --- | --- | --- |
| 1 | Reproducible limited unpruned depth-four rules pilot, all variants | Source hash matches output; disclose sampled-root schedule, wall time and node cap; treat as diagnostic only; no outcome data | Small |
| 2 | Revise compute cap from no-outcome evidence, then random-weight all-arm inference pilot | Freeze an incomplete-depth fallback and common node cap; pilot every game/variant/arm with full call/node/memory/wall accounting; no outcome-based cap changes | Medium |
| 3 | Independent review of v04 method/compute/sampling manifest | No unresolved P1/P2 protocol blockers; review is not fit authorization until fresh data/split audits pass | Medium |
| 4 | Adapter/data audit and reproducible trajectory pipeline | Replay, role/action, terminal-mask, deduplication, grouped split and leakage checks pass before any fit | Medium/large |
| 5 | Separate pre-fit grant and bounded development experiment | Exact method/source/config/data/runtime/schedule hashes, reviewed resources, model-selection only; all controls pass or objective is killed | Large |

The development sample count (20 model seeds and at least 40 paired situations
per held-out variant) is an exploratory nomination screen, not a power claim.
V2.12 method draft v03 adds a precise interpretation of policy-mixture outcome
values, sequential trajectory targets, crossed-bootstrap familywise intervals,
Holm tests, and measured training-FLOP gates. It awaits independent review and
is not a training grant. V2.12 keeps high novelty risk: multi-step JEPA-WM,
value-aligned world models, policy-aware simulator learning, regret-guided
board-game search control, and learned planning across board games are
established prior art. The incremental effect of latent matching remains
untested. See `docs/RELATED_WORK.md`, including the ICLR 2026 RGSC update.

Checkpoint update: v04 freezes the balanced two-game window bank (928 per
game), shared per-seed minibatch schedule (87 updates across three epochs), and
correct search-node-visit terminology in the rule-only audit. Related-work
positioning is aligned with the outcome-mixture max/min heuristic. The
2.0-second Reversi8 cap remains failed; do not train or match. After independent
acceptance of v04, the narrowly specified no-training, random-weight
instrumentation pilot may begin; objective/training code and fitted experiments
remain gated by novelty, data/split audits, and separate pre-fit review.


### 2026-10-03 targeted related-work update

The ICML 2026 paper [Causal-JEPA](https://proceedings.mlr.press/v306/nam26c.html)
uses object-level latent masking to create counterfactual-like prediction
queries and reports results on reasoning and agent-control tasks. This is
adjacent prior art for structured prediction queries, but it does not establish
coverage of every legal action or exact counterfactual transition in a
zero-sum board game. The current V2.12 counterfactual-support protocol gap
therefore remains open; no method, data, or training gate changes.


### 2026-10-03 root-score semantics audit

A source-level review of the compute-only alpha-beta runner found that it
carries the incumbent root alpha between legal root actions and discards the
per-action score map after selecting a move. Under pruning, some non-selected
root entries can be bounds rather than exact depth-limited values. The
counterfactual-support draft now requires score-status/bound provenance and
prohibits interpreting bounds as point-valued rankings or regret. Exact
all-action ranking would need a separately specified diagnostic and budget.
This is a measurement-contract clarification only: frozen pilot receipts
contain compute counters, not these scores, and no pilot result changes. See
`docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md`; the draft remains
unreviewed and authorizes no model scoring or data generation.


### 2026-10-03 support-count independence clarification

The counterfactual-support draft now defines episode support as distinct
source episode IDs, not statistically independent samples. It requires
separate declared-seed and policy-pair/seat diversity plus duplicate
trajectory/prefix diagnostics, replacing “multiple independent episodes” with
multiple distinct episode IDs. This avoids inflating the evidential meaning of
support counts when policy behavior is deterministic or episode content repeats.
The summaries remain descriptive, with no sufficiency threshold or gate change.


### 2026-10-03 memory-policy correction draft

A consistency check found that compute-budget amendment v05 describes sampled
RSS as a hard process safety stop, while source and host audits show RSS is
sampled/cooperative and the hard-limit mechanism is cgroup `memory.max`.
It also found that `memory.oom.group=0` does not guarantee a same-cgroup
request supervisor survives OOM victim selection. Added
`docs/V212_COMPUTE_BUDGET_AMENDMENT_06_DRAFT.md` to correct these semantics
without changing the proposed numerical caps. It is not independently reviewed
or operational; no pilot or fit is authorized.


### 2026-10-03 cgroup peak interface check

A no-inference probe in a disposable 1.5-GiB lattice scope confirmed
`memory.peak` is exposed, with `memory.max=1610612736`, and the transient
scope was removed. Its 5.5-MB metadata-only reading is not an inference
working-set estimate. v06 still needs independent review, OOM supervision, and
integrated receipt/timing tests before any pilot.


### V2.12 external OOM-observer feasibility probe (2026-10-03)

A fresh 64-MiB no-swap transient systemd **service** touched 128 MiB and was
OOM-killed while its caller remained in the distinct
`flatpak-session-helper.service` cgroup. The service reported
`memory.max=67108864`; `systemd-run --wait --pipe --service-type=exec` returned
nonzero with `Result=oom-kill`, status 9, and 64-MiB peak. The caller captured
the same `Result`, `ExecMainStatus`, and `MemoryPeak` with
`systemctl --user show`, then used `reset-failed`; the unit was removed.
Post-exit cgroup event files were unavailable, so the verified external signal
is systemd unit metadata, not `memory.events`. This is a disposable mechanism
test only; it does not integrate the V2.12 adapter or validate deadlines,
watchdogs, durable receipts, or all OOM cases. Before any pilot, the adapter
still needs a reviewed bounded-service launcher, retained result capture,
receipt persistence, cleanup checks, and separate watchdog/OOM tests. No pilot,
training, data, matches, or outcome evaluation occurred. Amendment v06 and the
1.5-GiB resource proposal remain drafts pending independent review.


### 2026-10-03 action-sensitive world-model prior-art update

A targeted primary-source search added two close arXiv preprints to
`docs/RELATED_WORK.md`: AD-WM (action-recovery regularization plus CEM-facing
counterfactual/elite-regret diagnostics) and ActSWM (multi-step JEPA rollouts,
recorded-versus-zero action contrast, frozen action readout, Minecraft planning,
and offline gameplay action recovery). Both are author-reported preprints and
were not independently reproduced. They do not instantiate exact-rule,
alternating-player, zero-sum max-min board games, but they remove standalone
novelty claims for multi-step JEPA, action sensitivity, counterfactual planning
comparison, or cross-game action recovery.

The research gate now narrows the remaining question to empirical decision
quality for finite-horizon exact-rule max-min search at matched compute. The
v04 training objective only supervises recorded branches; support summaries do
not establish legal-action ranking. Before any fit, a newly versioned and
independently reviewed protocol must decide on an action-sensitive JEPA control
and specify full legal-root scores and bounded-reference decision regret. The
reviewed v04 method is unchanged. No training, match, or gate authorization
follows from this search.


### 2026-10-03 bounded-reference decision-regret design draft

A source audit of two_player/v212_pilot.py confirms the current compute-only
runner carries a root alpha between root actions, discards its temporary score
map after move selection, and does not write action values to receipts. Later
root values can be bounds, and the frozen v02 receipt cannot be reused for
regret. Added docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md
to propose complete per-legal-action full-window scores, bounded-reference
regret, exact/bounded strata, and explicit missing/bound treatment. It also
specifies reference-value leakage limits and synthetic-only implementation
checks. The draft is not frozen or reviewed; reference depth/heuristic, compute
allocation, seat/root weighting, ranking measure, and primary-vs-secondary
status remain open. No code, data, outcomes, or pilot artifacts were changed.


### 2026-10-03 exact-regret oracle source audit

The decision-regret design audit located an existing full-game exact-regret
precedent in two_player/evaluate.py backed by two_player/games.py::exact_value.
That path covers only tiny registered games, uses a two-ply max-min planner,
and reports regret only for a complete decision. The oracle is unbudgeted and
explicitly documented for tiny state spaces. V2.12 instead targets Connect
Four 6x7/8x8 and Reversi6/8; its random-weight runner exposes no root-action
scores, and the inspected runner/game path has no pinned nonterminal bounded
reference heuristic. Exact solved roots and bounded-reference roots must be
kept as distinct strata. Do not run the legacy exact solver over the larger
variants or replace the frozen game scope. Reference configuration and
independent review remain open; this was a static source audit only.


### 2026-10-03 V2.8-to-V2.12 generation compatibility audit

The source audit in docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md
shows that V2.8 provides reusable exact training-size rules and a replayable
full-episode pattern, but cannot directly produce V2.12-compliant data. Its
train policy schedule covers only uniform/tactical opposite-seat pairs, its
selection and locked policies are split-specific, and its materializer emits
H1/H2 after a V2.8 phase cutoff under V2.8 duplicate rules. V2.12 requires a
uniform draw over all 16 ordered policy pairs and H0-H4 windows with H1/H2/H4
targets. The V2.12 auditor remains in-memory only. This is protocol/code
incompatibility, not evidence of insufficient data or leakage; no data was
generated or inspected. A separate reviewed V2.12 generator is required.


### 2026-10-03 behavior-policy semantics and RNG audit

A source-level policy audit was added to
docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md. It records the exact
uniform, tactical, positional, and bounded-search behavior, including the
192-node/depth-four search cap and handcrafted leaf score. These are synthetic
data-generation policies, not expert targets or the V2.12 evaluation oracle.
V2.8's policy-pair mapping is split/episode parity and its action RNG is one
SeedSequence stream; V2.12 requires a separately frozen draw across all 16
ordered seat-policy pairs and an explicit seed contract. No episodes or policy
actions were generated; exact source/config hashes and edge-case tests remain
pre-generation requirements.

A read-only audit found a pinned MIT-licensed Connect Four engine as a
candidate full-game reference for the standard 7x6 training variant only:
[Markus Thill/Connect-Four at commit 2a588445](https://github.com/MarkusThill/Connect-Four/tree/2a58844594ac022846385dd3ddc8bbbf0a26eae5).
Its `getNextVTable` source enumerates legal columns and independently calls a
full-window minimax root after each candidate move; the 100-ply default
exceeds the 42-cell board and opening books can be disabled with a null book.
This is static source evidence only, not an independently checked oracle or
measured runtime. It does not support 8x8 Connect Four or Reversi. Value-sign
normalization, reachability/turn/terminal contracts, correctness, licensing
provenance, and bounded-runtime checks remain open before any use. It does
not authorize scoring or change the research gate; see
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

An exact-oracle literature/source check narrowed, but did not close, the
Connect Four 6x7 reference gap. The MIT-licensed Rust
[connect-four-ai](https://github.com/benjaminrall/connect-four-ai) at pinned
commit `28a112adaf3ff89ee23fb09411fa592b6597010e` provides exact all-playable-
column scores, but they are side-to-move remoteness values and the API has no
call deadline. Its published author benchmark averages 5.09 s on a difficult
opening-position set; that is not a CAISSA measurement. Pascal Pons's
all-action solver is AGPL-3.0-or-later, while a 2025 BDD strong solution
reports 89.6 GB table size, 47 h and 128 GB RAM. No external engine/artifact
was installed, run, or downloaded.

The 10,000 V2.12 planner-node / 5-second request proposal cannot be transferred
to a solver's separate internal node counter or seconds-scale worst-case
search. Exact-root scoring therefore needs its own predeclared value semantics
(root-player W/D/L, with remoteness secondary unless reviewed), compute
allocation, hard worker deadline, and full-action completeness contract. This
is software-source evidence for Connect Four 6x7 only; 8x8 and both Reversi
variants remain without a pinned exact oracle. It changes no method or gate.
