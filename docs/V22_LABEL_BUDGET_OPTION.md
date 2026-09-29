# Label-budget alternative for a later development cycle

Date: 2026-09-29. **Proposal, not frozen, implemented or evaluated.** Prepared
while Grid02 runs, using its design and earlier literature review, without
reading new Grid02 scores, fitting models or accessing selection/final data.
This is an alternative to `V22_MECHANISM_ANALYSIS.md`, not an instruction to run
both proposals or to change the current experiment.

## Scientific question and decision

The current dataset supplies exact policy/value targets for every supported
training fork state. A recurrent value-dynamics model already receives explicit
supervision about the quantity used by minimax. Dense latent matching may add
little useful information, or spend capacity on distinctions unnecessary for
that value function. This is a possible explanation, not a diagnosis proved by
Grid01's near tie.

A cleaner next question is: **with a fixed limited set of exact training labels
and the same additional unlabeled legal transitions for every method, does
predictive latent supervision improve held-out bounded minimax planning more
than reconstruction or scalar value consistency?**

This is more directly motivated by the auxiliary-learning rationale in SPR and
EfficientZero than assuming common sibling offsets are irrelevant. It does not
have the specific weakened minimax guarantee of dropping common residual
weight. It still offers no guarantee of an advantage: low-label regimes can
also favor reconstruction, self-training or simple regularization. Value
equivalence makes scalar consistency a particularly strong alternative.

A positive result would support **label efficiency under a defined supervision
budget**, not unconditional superiority over fully supervised baselines. Keep
the full-label regime visible. Do not manufacture a favorable regime by trying
many label fractions and reporting only the fraction where JEPA wins. Existing
exact labels were already computed: this would initially simulate restricted
training access, not demonstrate savings in actual oracle acquisition cost.

## Required separation of information types

Unlabeled examples may reveal board features, player to move, legal actions,
the exact transition, game identity, terminal status and terminal utility from
the game rules. These are already available to every planner and adapter.
They may not expose nonterminal oracle value, optimal-action policy, action
oracle values, solved-outcome tags, outcome-derived difficulty strata, or labels
embedded in metadata, cache names, sampling probabilities or diagnostics used
to update parameters.

Terminal utility is free under the declared rules and should remain available
to all methods. Count it separately from queried nonterminal labels. Terminal
policy targets remain absent. Predicted-value supervision for terminal successor
slots can use this common free label; that fact reduces the effective scarcity
and must be reported. Do not call all successor targets unlabeled when a large
fraction are terminal or coincide with already labeled states.

The current dataset's earlier oracle-informed construction/filtering is also
fixed background information. A restricted-label experiment on it does not
establish a fully oracle-free acquisition pipeline. This limitation belongs in
the paper, not only in internal notes.

## Freeze label selection using training roots only

Before any new fitting or development scoring, choose one sparse fraction such
as25% and a full-label100% control. For each game, order eligible training root
IDs by a documented seeded hash of `(label_seed, game, trajectory_id, root_id)`;
take the declared count using a fixed rounding rule. Do not select by labels,
baseline error, JEPA error or development outcomes. If multiple roots share a
trajectory, select the entire trajectory group. Report resulting counts when
the fraction cannot be exact. The same mask is used across every model, rate,
weight and optimizer seed. Training-root selection randomness is independent
of optimizer and augmentation randomness.

The selected roots expose their predefined state/transition closure, not an
adaptively chosen subset of favorable replies. Define a global labeled set
using canonical `(game, state)` keys, with the same symmetry and perspective
rules as the existing overlap audit. A canonical state exposed through any
selected root has the same label-availability mask at every occurrence,
including occurrences in an otherwise unselected root. This prevents falsely
counting duplicate hidden labels as novel unsupervised information.

Root fraction is **not** unique-state label fraction. All legal forks of25% of
roots may cover much more than25% of unique states. Before freezing the training
experiment, audit counts of selected roots/trajectories, unique nonterminal
value labels, unique policy labels and their label-component sizes, free
terminal labels, and remaining genuinely unlabeled states, separately by game
and horizon. If overlap leaves little unlabeled support, the proposed regime
has failed its data-readiness test; declare a different acquisition unit or
dataset prospectively instead of presenting it as25% labeling.

If a precise oracle-query budget is eventually claimed, allocate/query unique
canonical states explicitly and report solving effort/node counts, not just
root fraction. Cached labels in this initial study cannot provide an honest
measurement of acquisition runtime saved.

## Missing-label masks and artifact audit

The existing `valid` mask indicates that a transition state exists. It must
continue to control encoding and predictive targets; it is **not** a label mask.
A missing nonterminal label must not erase a real future latent target.
Introduce separate boolean `value_labelled[N,3]` and
`policy_labelled[N,3]` masks, with the latter false on terminal states. Masks
are protocol metadata, not encoder input features.

Every supervised term must use its correct mask:

- Encoded value MSE uses valid-and-value-labeled states.
- Encoded legal soft policy CE uses valid, nonterminal, policy-labeled states.
- Recurrent H1/H2 predicted-value MSE uses the corresponding valid future slot
  and its value-label mask, preserving the correct player perspective.
- Latent matching, reconstruction and permitted self-consistency use supported
  transitions regardless of nonterminal label availability.
- Variance diagnostics/regularization retain the same declared valid-state
  support for every appropriate family.

For completely unlabeled minibatches, supervised losses and gradients are
exactly zero without division by zero. Missing targets use explicit masks plus
sanitized stored values; zero alone is ambiguous because it is a legitimate
draw label. Policy mass can be zero only when the policy label is absent or the
state is terminal. Legal action masks remain genuine rules-derived masks.

Specify normalization before fitting. Dividing supervised sums by the number
of available labels avoids simply shrinking their coefficient when labels are
scarce, but minibatch label-count variability changes the estimator and must be
made common across models. Prefer a declared paired sampling scheme or fixed
epoch-level normalizers, with actual effective supervised weights recorded.
Do not silently oversample labeled examples only for JEPA or give one family
more labeled optimizer steps.

Build redacted training arrays/artifacts so hidden nonterminal labels cannot
be read by the trainer, auxiliary target computation, sampler or metric hooks.
Keep any full-label analysis in a separate read-only post-training process;
it must not select masks, epochs or update steps. Every cache/checkpoint identity
must include label-mask/manifest SHA-256, redaction/parser version, label-seed,
canonical closure version, objective/mask version and normalization policy.
Resuming across fractions or masks must fail closed even with the same raw
dataset fingerprint.

Required audits include labels hidden in root `oracle_values`, fork metadata,
soft policies or cached arrays; state duplicates within/across subsets; closure
overlap across training/development/selection/final; symmetry transformation of
masks and policy labels; terminal and missing-H2 cases; and action/perspective
consistency. Existing split boundaries remain fixed. No selection/final access
is needed to choose a training mask beyond existing immutable audit manifests.

## Strong controls on the same unlabeled transitions

All methods receive the same canonical training pool, same labeled subset,
same additional unlabeled forks, shared supervised losses, augmentation and
group/trajectory schedule. Keep ordinary uniform-fork sampling for this study
so label scarcity is not confounded with sibling grouping.

| Family | How it can use the common unlabeled data |
| --- | --- |
| Direct policy/value | Same labeled encoder supervision and permitted common consistency/augmentation protocol. No transition auxiliary by definition; report that its active training compute is smaller. |
| Recurrent value dynamics | Same labeled encoded/predicted value and policy supervision; establishes the incremental effect beyond supervised transition training. |
| Decoded recurrent dynamics | Predict observed successor features on the same labeled and unlabeled transitions, with the same state support as JEPA. |
| Recurrent JEPA | Predict detached EMA successor embeddings; no hidden teacher labels enter the target. |
| Recurrent EMA value consistency | On every supported transition, match predicted future value to a detached EMA encoder/value-head estimate of the actual successor, plus identical available-label supervision. |

The fifth control directly tests whether task-relevant scalar bootstrapping
explains an apparent JEPA advantage. Its target is
`stop_gradient(V_EMA(encode_EMA(actual_successor)))`; compare this with
`V_online(recurrent_prediction)`, aligned to the successor player's perspective.
Use the same EMA timescale, recurrence, horizons, target update order and
terminal rules as the candidate. An EMA **value head** is required; the current
EMA encoder/projector alone does not provide this target. Version and serialize
that extra state. The candidate must not gain access to a superior teacher
trained using withheld labels. This control can collapse/self-confirm wrong
values, so keep common labeled anchors and report value calibration/error.

A stronger joint policy/value self-distillation control may be warranted in a
follow-up, especially if JEPA only beats scalar consistency. That is a separate
declared expansion; it must not be hidden behind the label “value dynamics.”
Changing direct supervision/consistency should be offered transparently to
the corresponding baselines. Architectural parameter counts and actual active
compute will differ; an equal-update comparison is not compute matching.

## A bounded prospective study

Before implementing, choose the scarce fraction and mask seed once using only
training inventory. A possible first development matrix has two fractions
(25%,100%), five families above, two learning rates and three optimizer seeds:
**60 cells**, with one prospectively fixed auxiliary coefficient per family.
The fixed coefficients should come from an explicit justified scale convention
or the completed earlier protocol, not from scores in this new grid. One fixed
coefficient limits conclusions about optimally tuned families; report that.

If two auxiliary weights are necessary for fair comparison, declare the larger
matrix explicitly: direct/value-dynamics have canonical weight, the three
auxiliary families each have two weights, giving **96 cells** over the two
fractions, two rates and three seeds. Do not run60 then selectively expand only
JEPA. Choose either matrix and a local resource cap before fitting; preserve
every failed/timed-out cell and do not start it merely because the previous
negative grid invites another attempt.

Select each family's rate/weight globally across the same games and optimizer
seeds within the prespecified primary scarce regime; never per game or per seed.
Keep the full-label arm visible as a planned interaction/sensitivity analysis.
Declare whether it shares scarce-selected hyperparameters or receives its own
equal-opportunity tuning before fitting. Do not select the best label fraction
after observing regret. A single fixed mask tests one subset: three optimizer
seeds do not measure uncertainty over label acquisition. Any promoted result
needs independent label-mask replication before a broad label-efficiency claim.

Use the existing exact/hybrid development schedule and strong-baseline
promotion thresholds unless a prospective new protocol explicitly explains a
different scientific endpoint. Comparators are the newly trained matched
controls at the **same** label budget. Also show the best full-label baseline
as a reference ceiling. A low-budget win does not erase a full-budget loss.

Additional endpoints: performance versus actual unique label count; encoded
and recurrent value errors; policy NLL/ranking with legal-action support;
calibration; effective rank/covariance; projected/unprojected prediction errors;
terminal fraction; runtime and unlabeled exposure. Every interval must state
its seed/root/mask scope and adaptive-development limitation. A direct claim
about learned rollout requires hybrid evidence beyond an exact-state encoder
regularization gain.

## Stop and interpretation criteria

Stop or narrow the hypothesis if unlabeled support is negligible after canonical
closure, if a mask/audit leak is found, or if gains disappear against decoded or
EMA value consistency. If all auxiliaries improve similarly, the conclusion is
benefit from unlabeled transition learning rather than a JEPA-specific effect.
If only a chosen label mask works, retain it as a negative replication finding.
If benefit exists only under restricted labels, state that regime explicitly.
Do not lower promotion margins, switch fractions or remove failed controls to
obtain a positive result.

This regime is methodologically motivated, but label-efficient predictive
representation learning is established prior art. Neither masking labels nor
combining JEPA with deterministic game forks establishes a unique workflow.
The eventual contribution would need reproducible controlled gains, independent
mask/seed replication and a defensible adversarial-planning distinction.

## Existing primary-source basis

No additional web search was needed for this option. Read-depth and coverage
limitations remain those in `V2_PREDICTIVE_RESEARCH.md`:

- [SPR, ICLR2021](https://arxiv.org/pdf/2007.05929) studies action-conditioned
  predictive representation auxiliaries for data-efficient visual RL.
- [EfficientZero, NeurIPS2021](https://arxiv.org/html/2111.00210v2) combines
  projected consistency with learned planning under limited data.
- [DeepMDP, ICML2019](https://proceedings.mlr.press/v97/gelada19a.html) is prior
  art for latent dynamics and reward-informed representation learning; only
  abstract/metadata were inspected in the earlier review.
- [The Value Equivalence Principle, NeurIPS2020](https://arxiv.org/abs/2011.03506)
  motivates a task-relevant scalar model control. Its MDP equivalence statements
  do not automatically prove sufficiency for this adversarial game setting.

These sources motivate a test; they neither predict a positive outcome on the
current symbolic games nor establish novelty of the proposed label regime.
