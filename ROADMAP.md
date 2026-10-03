Warning: truncated output (original token count: 7406)
Total output lines: 253

# CAISSA-JEPA research roadmap

Updated: 2026-10-03. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

## V2.12 checkpoint (2026-10-03)

A hard memory bound for a future pilot remains unverified. Keep RSS as sampled
telemetry until a disposable bounded-unit check confirms a finite `memory.max`,
descendant containment, supervisor behavior, and cleanup. `memory.high` is not
a hard limit; see
`docs/V212_HOST_MEMORY_CONTAINMENT_AUDIT_01.md` and its primary references.

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
`docs/V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` propose train-only fit windows on
training sizes and 48 standalone development roots per held-out size.
Independent review accepted these as design drafts, not a frozen protocol. The
64-slot yield, occupancy bands, and symmetry uniqueness rule remain unverified
before implementation.

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

Falsifiable hypothesis: an EMA-target JEPA that predicts future latent states conditioned on both players' ordered actions can improve planning under a fixed compute budget over m…2406 tokens truncated…edistribution and derivative-output rights are documented. Each manifest must pin SHA-256, parser/rules version, counts, provenance, split, and trajectory/event grouping. Keep raw data, checkpoints, caches, and logs outside Git and the Obsidian mirror. No paid compute or service without explicit authorization.

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
