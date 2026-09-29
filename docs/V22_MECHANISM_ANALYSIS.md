# Sibling residual weighting: prospective mechanism audit

Date: 2026-09-29. **Proposal only; not frozen, implemented or evaluated.**
Written while v2.1 Grid02 is running. This note uses Grid01 diagnostics and
algebra only; it does not inspect new Grid02 scores, fit a model or access
selection/final data. The current experiment remains unchanged. All bounds and
counterexamples below are elementary derivations for this proposal, not new
theorems claimed from the cited papers.

## Main conclusion

Downweighting the common error of legal sibling replies is a plausible capacity
allocation experiment, but **the common error is decision relevant**. It shifts
an own action's worst-case value relative to other own actions. A large measured
common-error fraction does not mean that fraction is nuisance information.
The proposed loss weakens a worst-case guarantee unless value anchoring or
better fitting compensates. That compensation must be measured.

There is a second important limitation: the frozen primary evaluator re-encodes
exact successor states and does not use the recurrent predictor. An improvement
in its primary regret would support useful representation regularization, not
directly demonstrate more accurate learned-transition planning. The hybrid
track uses the recurrent predictor and is necessary for the latter mechanism.

## Notation and error decomposition

At one fixed root s, own action a leads to K_a legal opponent replies b.
Let q_ab be the exact continuation value in the root player's perspective.
Terminal branches use exact known utilities. The true depth-two backup is

`m_a = min_b q_ab`, and `a* in argmax_a m_a`.

Let t_ab be a detached successor target representation, u_ab the recurrent
prediction, and e_ab=u_ab-t_ab. Within an own-action group define

`mu_a = mean_b e_ab`, `d_ab = e_ab-mu_a`,

`C_a = mean_b ||d_ab||^2`, `M_a = ||mu_a||^2`.

Ordinary pointwise matching is exactly `J_1,a=C_a+M_a`. A candidate is
`J_lambda,a=C_a+lambda*M_a`, with proposed lambda=0.25 for K_a>=2. K_a=1
would retain ordinary pointwise loss; there is no sibling contrast to emphasize.
H1 matching and existing absolute policy/value supervision would remain.

The complete-pair identity is

`sum_(b<c) ||e_ab-e_ac||^2 = K_a * sum_b ||d_ab||^2`.

Thus uniform displacement matching supplies no extra targets beyond centered
residual MSE. The prediction-space gradient of J_lambda for a fixed target is

`dJ/du_ab = (2/K_a) * [d_ab + lambda*mu_a]`.

The intervention specifically scales the common residual gradient. For
normalized/projected embeddings, the same residual identity holds, but this
gradient must then be propagated through the normalization and projection
Jacobians. It is not a free translation in raw latent coordinates.

## Local minimax error and margin bounds

Assume temporarily that u and t lie in the space actually read by a value head
V, and V is L-Lipschitz in Euclidean norm. Define target value error
`eta_a = max_b |V(t_ab)-q_ab|`. By the triangle inequality,

`max_b |V(u_ab)-q_ab| <= eta_a + L*max_b ||e_ab||`.

Since the centered residuals sum to zero, for K_a>=2,

`max_b ||d_ab|| <= sqrt((K_a-1)*C_a)`.

Proof: fixing one d, the other K_a-1 vectors sum to -d, so Cauchy-Schwarz
implies their summed squared norms are at least ||d||^2/(K_a-1).
Consequently,

`epsilon_a = eta_a + L*[sqrt(M_a)+sqrt((K_a-1)*C_a)]`

bounds every modeled reply's value error in the group. For lambda>0 a convenient
looser bound is

`epsilon_a <= eta_a + L*sqrt((K_a-1+1/lambda)*J_lambda,a)`.

This follows by weighted Cauchy-Schwarz. For the same numerical loss level,
lambda=1 gives coefficient sqrt(K_a); lambda=0.25 gives sqrt(K_a+3).
At lambda=0 there is no finite bound on the common residual from this loss.
These statements compare guarantees, not attainable optima or observed errors;
a smaller lambda might still improve fitting of other errors in finite capacity.

The minimum operator is 1-Lipschitz in the sup norm. Therefore
`|mhat_a-m_a| <= epsilon_a`, where `mhat_a=min_b V(u_ab)` with exact terminal
overrides. If ahat maximizes mhat, then

`m_(a*)-m_ahat <= epsilon_(a*)+epsilon_ahat <= 2*max_a epsilon_a`.

An optimal action stays preferred over a suboptimal a whenever
`m_(a*)-m_a > epsilon_(a*)+epsilon_a`. A uniform sufficient condition is
that the smallest positive root action gap exceeds 2*max_a epsilon_a.
For multiple optimal actions this guarantees membership of the optimal set,
not preservation of a particular tie-break. The same nonexpansiveness holds
for a fixed deeper min/max tree with uniformly bounded leaf errors; no
stochastic expectation or behavioral-opponent calibration is involved.

These are **per-root, per-group sup-error bounds**. A global mean training loss
does not certify them. Rare bad roots, branch-count differences and target value
approximation remain material. Average MSE can conceal the one overestimated
or underestimated reply that changes a minimax backup.

## A concrete common-offset failure

Consider two own actions A and B, each with two replies. Suppose all successors
after A have true minimax value0, and all successors after B have value-1.
Use the actual head form V(z)=tanh(z) in one latent coordinate. Let target
latents be t_A1=t_A2=0 and t_B1=t_B2=-2. Encoded values are0 and about-0.964;
the target's value approximation error for B is about0.036.

Set predicted latents u_A1=u_A2=-1 and u_B1=u_B2=1. Both groups have C_a=0:
all sibling residual differences match perfectly. Predicted minima are about
-0.762 for A and+0.762 for B. The planner selects B and incurs regret1.
Relative-only loss is zero despite the incorrect decision. The example can be
embedded in a larger noncollapsed representation, so a global effective-rank
gate does not eliminate this failure.

Even if each group preserves the correct ordering of its replies exactly,
group-specific value offsets c_a yield `mhat_a=m_a+c_a`, which can reverse the
root action ranking. A common scalar offset shared across every root action
would cancel from ranking; different offsets for each `(s,a)` do not. This is
why grouping only by own-action siblings is a stronger invariance than minimax
decisions permit. Terminal overrides prevent this particular error on already
terminal leaves; the example concerns nonterminal leaves with known eventual
oracle outcomes, which are precisely where a learned value estimate is used.

## Projected JEPA has no automatic value bound

The actual projected-JEPA loss compares normalized projected predictions to
normalized EMA target projections. The planner's V reads **unprojected** z.
A small error in the former does not imply a small error in the latter.

For example, a linear projection can ignore a coordinate used by V: changing
only that coordinate leaves projected matching unchanged while changing value.
The present32-to16 projection has a nontrivial linear null space, and
normalization additionally discards scale. The online prediction head and EMA
target map are also different mappings. No inverse-Lipschitz or value-sufficiency
condition for these maps has been established.

For the actual tanh linear value head, an unprojected bound can use
`L=||w_value||_2`, because tanh is1-Lipschitz. It still needs raw predicted-to-target
latent errors and an EMA-target value approximation term eta. Alternatively,
directly measure the two observable terms

`|V(u)-q| <= |V(u)-V(encode_online(successor))|`
`             + |V(encode_online(successor))-q|`.

The first is rollout-induced value discrepancy; the second is encoded value
error. Neither requires pretending that projected error controls value.
EMA-target drift can be measured separately. A learned decoder from projected
space to value could provide a different conditional guarantee, but adding it
would change the method and introduce another controlled head/objective.

## What the existing predicted-value anchor can and cannot do

Every recurrent non-direct variant already applies absolute future-value MSE
with the frozen coefficient0.25 per supported horizon. This directly penalizes
the counterexample and constrains the value-relevant direction even when a
projector discards it. For a group with direct value MSE E_a,

`max_b |V(u_ab)-q_ab| <= sqrt(K_a*E_a)`.

Thus one can also use `epsilon_a=sqrt(K_a*E_a)` in the minimax bound above.
This is an empirical per-group bound at the measured states, not a generalization
guarantee. A fixed loss coefficient0.25 does not imply any fixed bound on E_a.
Sampling may rarely expose decisive replies; optimization and model capacity
can still leave them inaccurate. Saturated tanh heads can also have small
gradients despite large latent offsets.

The fair question is consequently whether reweighting the latent auxiliary
improves decision-relevant errors **beyond the same predicted-value anchor
alone**. Strong value-dynamics controls are essential. The anchor cannot be
advertised as new JEPA information, and adding stronger value ranking only to
the candidate would confound the experiment.

## A finite falsifiable experiment, if later authorized by evidence

First finish and report Grid02. Any further implementation requires a separately
frozen amendment. The narrow candidate would keep projected recurrent JEPA,
H1 loss and existing value anchor, while replacing only H2 residual loss with
`C+0.25M` on complete legal sibling groups. This is groupwise residual weighting,
not a new class of relational representation learning.

Complete-group training changes exposure relative to uniform fork draws.
Therefore every comparator must use the same new group/branch schedule,
augmentation, all existing labels, state weights and update budget. Define
root/own-action/reply weighting explicitly before fitting; do not accidentally
give own actions with more replies larger root supervision weight. Report
unique/repeated state exposures and actual compute. Old Grid01/02 results are
historical references, not the primary controls for a changed sampler.

| Prospective control | Required inference |
| --- | --- |
| Pointwise JEPA J_1 on identical complete groups | Does changing relative/common weighting add anything beyond grouping/exposure? |
| Uniformly scaled pointwise0.5*J_1, with a prespecified finite weight opportunity | Is any gain merely a smaller auxiliary? The fixed0.5 scale roughly brackets the aggregate reduction suggested by Grid01, but is not an exactly matched gradient norm. Do not choose it using future outcomes. |
| Random group residual weighting, same game/size and same branch examples | Does legally meaningful sibling membership matter? Only the centering groups change; correct transition targets and actions must remain paired. Any additional phase matching must use predeclared state metadata. |
| Value dynamics, decoded dynamics and direct policy/value, all with the identical grouped schedule | Does the candidate beat strong non-JEPA supervision and reconstruction controls? Give auxiliary-bearing controls the same declared tuning opportunity. |
| Centered-MSE implementation versus explicit all-pair reference on fixtures | Loss/gradient equality is a correctness test, not independent empirical evidence or another scientific baseline. |

For random groups, permit a deterministic within-game permutation of the same
prediction-target residual rows into the exact sibling-group size multiset.
Preserve eligibility masks and original supervised weights. Randomization must
not accidentally swap targets, grant extra examples or change the value loss.
If groups contain repeated training examples, count those explicitly in all
arms. Group-size-one fallback must be identical. Root-level or minibatch-level
grouping would be a separate hypothesis, not a post-hoc substitution.

Any shared reply-value difference/ranking term is a later factorial intervention:
add it to both JEPA and value-dynamics controls with identical labels/weights.
Do not put the added supervised signal only in the candidate. Avoid a large
combined architecture/grouping/ranking search before this narrow test resolves.

## Mechanism diagnostics and prospective rejection rules

Retain the frozen development promotion gates and every attempted cell. Declare
additional mechanism endpoints before fitting: per-root worst-reply value error;
error in each own-action minimum; group-mean value bias; within-group centered
value error; root action gap and backup ranking mistakes; exact/hybrid regret
and their paired difference. Measure C and M separately, unprojected rollout
value discrepancy, encoded value error, EMA drift, rank and variance. Use exact
oracle labels already available to all methods; report ties, branch counts,
terminal overrides and samples rather than a tie-ambiguous single worst reply.

The legal-sibling mechanism fails if any of these occur:

- It lowers centered latent error while worsening own-action minimum errors,
  false optimistic backups or regret; that is the counterexample's failure mode.
- It cannot beat the strongest matched non-JEPA baseline under the declared
  development gates, regardless of attractive auxiliary diagnostics.
- Uniformly scaled pointwise matching explains the gain; narrow the explanation
  to auxiliary strength rather than sibling geometry.
- Random groups perform comparably and no sufficiently precise paired contrast
  supports a legal-group advantage; the legal-sibling claim remains unsupported.
- Gains arise only after changed branch exposure, stronger supervised anchors,
  extra tuning or active compute unavailable to controls.
- Improvement appears only on exact-state evaluation with no favorable rollout
  discrepancy/hybrid evidence; limit the mechanism claim to representation
  regularization, not learned-transition planning.

An underpowered difference between controls is inconclusive, not evidence of
equivalence. Thresholds for auxiliary diagnostic contrasts and any compute-matched
replication must be specified in the future protocol, not after seeing scores.
Even a successful development screen nominates a candidate for independent
selection/replication; it does not establish JEPA superiority or Q1 readiness.

## Prior-art boundary

This note adds no new web search. It relies on the inspected-source review and
read-depth labels in `V2_PREDICTIVE_RESEARCH.md` and
`V2_FORK_GEOMETRY_NOVELTY.md`:

- [Relational Knowledge Distillation, CVPR2019](https://openaccess.thecvf.com/content_CVPR_2019/papers/Park_Relational_Knowledge_Distillation_CVPR_2019_paper.pdf)
  is prior art for teacher/student relational geometry.
- [SPR, ICLR2021](https://arxiv.org/pdf/2007.05929) and
  [EfficientZero, NeurIPS2021](https://arxiv.org/html/2111.00210v2) are direct
  prior art for recurrent projected predictive consistency in control/planning.
- [The Value Equivalence Principle, NeurIPS2020](https://arxiv.org/abs/2011.03506)
  and [Approximate Value Equivalence, NeurIPS2022](https://papers.neurips.cc/paper_files/paper/2022/file/d53538ba21c05fa361d2b21704172753-Paper-Conference.pdf)
  already emphasize planning-relevant model approximation. Their MDP results
  are not being asserted as minimax theorems for this implementation.
- [PhyLatent, August2026 preprint](https://arxiv.org/html/2608.05720) is close
  counterfactual branch-separation prior art; exact legal successor supervision
  is a potential experimental distinction, not established novelty.

No search-absence or algebraic-repackaging argument establishes a unique method.
The useful contribution would have to be a reproducible, carefully controlled
effect in the declared adversarial-game setting.
