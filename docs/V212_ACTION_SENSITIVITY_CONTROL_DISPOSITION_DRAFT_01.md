# V2.12 action-sensitivity control disposition — draft 01

**Status: pre-fit study-design recommendation for independent review.** This
draft does not amend `METHOD_SPEC_V212.md`, add an arm, freeze a diagnostic,
authorize data generation, fit, inference, scoring, matches, or advance any
research gate. The six-arm panel and all open compute, data, supervision, and
review gates remain unchanged.

**Independent review (2026-10-04): conditionally accepts retaining the six
arms for the narrow v04 contrast family; no P1/P2 blocker.** The reviewer
confirmed the estimand limitation, source summaries, and decision-facing
diagnostics. A nonblocking AD-WM wording correction distinguishing elite-regret
from Cube success evidence was incorporated. This review accepts the scope
exclusion only; it does not freeze the regret protocol or open any fit gate.

**Literature follow-up (2026-10-06):** the targeted source refresh identified
UWM-JEPA's counterfactual-target action-binding result, which is not cited in
the 2026-10-04 disposition.

**Independent pre-fit reconsideration (2026-10-07):** a read-only reviewer
explicitly considered UWM-JEPA together with ActSWM and AD-WM. The reviewer
found exclusion of these methods from v04's fixed six-arm contrast family
defensible: they establish action-sensitivity and related mechanisms, but do
not provide matched controls for the current deterministic board-game/minimax
estimand. No v04 arm needs to be retrofitted or added on that basis. This is
scope review only, not novelty certification or fit-gate approval. Claims
remain limited to the six named arms; they cannot establish superiority over
action-sensitive JEPA or broader latent-planning methods.

## Decision to review

Does the frozen V2.12-04 six-arm panel need an action-sensitive JEPA control
before fitting, given that its candidate conditions a recursive predictor on
actions but trains its latent targets only along recorded trajectory branches?

This is a distinct question from whether a D-JEPA-style candidate-set ranker is
needed. The six v04 contrasts vary latent-target horizon, prediction target,
and architecture. They are a prespecified contrast set, not one pooled
component-effect estimate and not a comparison against every action-selection
architecture.

## What the closest prior art establishes

Radha and Goktas' UWM-JEPA trains an action-conditioned unitary JEPA on
partially observed trajectories. In its hidden-velocity task, the authors
report that an observed-future teacher-forced target lets the action term
become nearly inert, while independently sampled simulator counterfactual
targets restore action-perturbation sensitivity. Their result is a controlled
mechanism finding, not evidence about deterministic board games or
competitive planning. It makes one point directly relevant to v04: passing an
action into the predictor does not establish that the learned predictor uses
it. Because exact board rules can generate alternate legal successors,
counterfactual-target training is technically available here, but it would be
a new data intervention and requires a new method/control version if adopted.
The UWM-JEPA preprint and its author code were inspected in the 2026-10-06
refresh; no code or data was downloaded or used.

Gan et al.'s ActSWM combines multi-step JEPA prediction with two action-
sensitivity constraints: a rollout-level contrast between recorded actions
and an all-zero future-action sequence, and a frozen action readout applied to
encoded and predicted latent transitions. It reports step-drift diagnostics,
closed-loop CEM planning in Minecraft, and action recovery from offline
gameplay videos ([arXiv v2](https://arxiv.org/abs/2607.26712), [full text](https://arxiv.org/html/2607.26712)).
The paper's reported evidence is author-reported preprint evidence and was not
reproduced for this audit. Its all-zero contrast is not directly portable:
zero can be illegal or carry a special meaning in a finite board game's legal
action space.

Qiu et al.'s AD-WM uses residual latent prediction plus predictor-level
inverse-action and normalized action-recovery objectives on model-generated
transitions. Its auxiliary heads are discarded at inference, while CEM uses
the latent dynamics unchanged. It also evaluates predicted-versus-realized
costs on shared candidate banks, including ranking and elite-regret measures
([arXiv v2](https://arxiv.org/abs/2609.30264), [full text](https://arxiv.org/html/2609.30264v2)).
The reported experiments are also preprint results, not independent
replication. The paper itself reports that the inverse-only increment is
unresolved for its Cube elite-regret diagnostic. In the Cube success ablation,
the inverse objective has a smaller, weight-dependent effect; the authors
identify residual prediction and normalized recovery as the largest
contributors.

These works make action sensitivity, transition action recovery, and
planner-facing candidate regret established design ideas. Their experiments
do not cover finite legal root-action sets in deterministic alternating
two-player zero-sum games, role-conditioned opponent moves, exact game rules,
or worst-case max/min search. They therefore establish a material mechanism
and evaluation risk for v04, but do not supply a ready-made matched board-game
control or imply any CAISSA result.

## Recommended disposition for the current v04 question

Retain the six v04 arms only for their narrow, fixed-planner contrast family,
conditional on an independent pre-fit reviewer accepting this scope exclusion.
Do not add an action-recovery loss to only the candidate: that would change
the treatment recipe and confound the current contrasts. Do not add a seventh
arm and call it a matched control. A separately declared seventh arm could be
a useful method benchmark without changing the existing five candidate-versus-
control contrasts, but it would require its own comparison, compute allocation,
and multiplicity disposition. Adding action-sensitivity objectives to the
existing arms would be a new factorial design with interactions and a new
protocol version.

If the reviewer accepts the narrow scope, any eventual six-arm result must be
described only as the observed v04 candidate-versus-five-control contrasts
inside the declared exact-rule planner and game/variant scope. It cannot
support superiority over action-sensitive JEPA, broad latent-planning
architectures, or state of the art. It also cannot attribute an outcome to
action-sensitive representations without a separately designed mechanism
test. If the intended claim is comparative algorithm performance against
action-sensitive JEPA, the current panel is insufficient; version and review a
separate benchmark arm before fitting.

The 2026-10-04 disposition conditionally addressed the narrow v04 contrast
family against the sources then listed. The 2026-10-07 reconsideration now
explicitly includes UWM-JEPA and confirms that the current narrow scope can be
retained without a new arm. This does not establish action sensitivity or
permit broader comparative claims. The decision-facing diagnostic remains
unfrozen, and fitting remains blocked by its protocol, the legal-root regret
protocol, and the other open gates.

## Required decision-facing measurement, still unfrozen

Regardless of whether a new training arm is added, action conditioning must not
be treated as evidence that the predictor responds usefully to actions. Before
fit, independently review a versioned evaluation protocol that:

1. Uses prehashed, held-out reachable roots and enumerates each root's full
   legal action set. It must distinguish actions present in training support
   from counterfactual legal actions absent from the recorded windows.
2. For legal alternatives from the same root, compares predicted transitions
   and multi-ply rollouts with exact rule-generated consequences under a
   fixed, declared latent metric. It must stratify cases where exact successor
   states or relevant outcomes differ; raw latent separation alone is not a
   success criterion.
3. Records a score or explicit missing/bound status for every legal root
   action under the same node/deadline policy, then reports minimax
   action-ranking agreement and regret against a pinned exact or bounded
   reference. Exact and bounded-reference cases remain separate strata.
4. Keeps reference labels evaluation-only. They may not enter v04 training,
   model selection, or a learned action-sensitivity loss unless a new method
   version and leakage review explicitly authorize that change.

This is a design requirement, not a frozen protocol. Root sampling, reference
depth/evaluator, budget, incomplete-cell policy, multiplicity, and thresholds
remain unresolved in
`V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`. The prior draft and
this memo do not advance that gate. The failed Reversi8 2.0-second p90 gate
also remains open. A candidate descriptive transition-sensitivity protocol is
recorded in `V212_ACTION_SENSITIVITY_DIAGNOSTIC_PROTOCOL_DRAFT_01.md`. Static
review found its initial support, collision, terminal-mask, and intervention
logic mostly coherent but left graph/mask and other pre-freeze conditions
open; a revised draft and final read-only review do not resolve the regret
reference, amend v04, or authorize roots or model output.

## Source and claim limits

The source claims above were checked against the ActSWM and AD-WM arXiv v2
full texts. The 2026-10-06 refresh additionally checked the UWM-JEPA arXiv
full text and author repository. The 2026-10-07 reviewer reconsidered these
sources for scope, but did not reproduce them or certify novelty. They are
preprints in this source snapshot; reported results are author-reported. This
targeted comparison is not a systematic literature review, reproduction, or
novelty certification. No external code, model, dataset, game state, score,
or outcome was used in this analysis.
