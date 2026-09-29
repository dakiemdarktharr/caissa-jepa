# Conditional critique: targets that preserve legal-reply backups

2026-09-29. **Proposal only; not frozen, implemented or evaluated.** Written
while the source-pinned V2.3 diagnostic runs. No V2.3 results, new data, model
predictions or protected splits were inspected. This note does not change its
protocol or authorize a further fit.

**Decision after mathematical critique: defer the generic random-probe grid.**
For the present single value head, it has no demonstrated task-relevant target
beyond the stronger scalar backup controls. The finite matrix below is retained
as a conditional proposal, not a recommendation to spend another 18 fits.

## Is there a meaningful hypothesis?

Yes, but “game-aware action-conditioned latent targets” is too broad to be a
contribution. Action-conditioned recurrence is already central to
[MuZero](https://arxiv.org/abs/1911.08265), and multi-step EMA representation
prediction to [SPR](https://arxiv.org/abs/2007.05929) and
[EfficientZero](https://arxiv.org/html/2111.00210v2). Legal counterfactual
successors change the experimental setting, not that priority boundary.

A narrower falsifiable hypothesis is: **preserving action-indexed worst-reply
function values across several fixed latent probes improves bounded learned
rollouts beyond equally supervised scalar backup learning and pointwise latent
matching.** This changes what the auxiliary asks the model to preserve. It does
not assume a superior encoder or that every differing action deserves latent
separation. Test it only if V2.3 leaves a credible recurrent-model problem after
resolving the common training-budget/capacity decision.

This is a failure-capable hypothesis, not yet a well-motivated intervention.
The null-space argument below makes its missing connection to the actual
decision function explicit. “Several functions” alone does not imply better
preservation of the one function the planner uses.

## Finite-probe counterexample and the actual value-head identity

Stack the eight linear probes in `P in R^(8 x 32)`. Then
`dim ker(P) = 32 - rank(P) >= 24`. Unless the current value direction `w`
lies in `rowspan(P)`, there is an `n in ker(P)` with `w^T n != 0`; rescale n
so `w^T n = 1`. Probe agreement therefore gives no bound on the current
value-relevant displacement. If w happens to lie in that span, this particular
counterexample does not apply, but unrestricted training does not preserve
that coincidence.

Moreover, being in the span is not sufficient for **minimum-probe** matching:
`min_b sum_j alpha_j p_j^T z_b` is generally not determined by the individual
probe minima. For probes e1 and e2, the sets `{(0,0.5),(0.5,0)}` and
`{(0,0),(0.5,0.5)}` have identical coordinate minima, but minima along
`w=e1+e2` are 0.5 and 0 respectively. Adding the actual w as a probe matters;
merely spanning w with other probes does not repair this aggregation loss.

Use the actual head form `V(z)=tanh(w^T z + b)`, and let `z0=-b*n`. Consider two
own-action groups, each containing one or more identical nonterminal replies:

| Group | Detached actual target | Recurrent prediction | Target / predicted head value |
| --- | --- | --- | --- |
| A | `z0` | `z0-c*n` | `0` / `-tanh(c)` |
| B | `z0-c*n` | `z0+c*n` | `-tanh(c)` / `+tanh(c)` |

For every `c>0`, all probe values are zero, so every action-indexed operator
target matches exactly. Yet target-backed planning chooses A and predicted
planning chooses B. If actual oracle values are A=0 and B=-1, target-value
approximation error is only `1-tanh(c)` on B, but the prediction incurs regret
1. This construction concerns arbitrary latent vectors: it shows that the
probe loss alone implies no value guarantee. Bounded tanh encoder outputs limit
attainable c for fixed w, but not the existence of small value-changing
null-space perturbations or the need for an additional bound. A noncollapsed
background population can coexist with this local error.

The candidate's retained pointwise and scalar losses would penalize this
example. That is precisely the concern: any protection comes from those
anchors, not from the eight random operator targets. Low probe loss cannot be
interpreted as independent evidence of minimax sufficiency.

For a fixed finite set of nonterminal replies, monotonicity gives the exact
identity

`min_b tanh(w^T z_ab + b0) = tanh(min_b w^T z_ab + b0)`.

Thus matching the minimum along **this single actual head direction** for each
own action preserves its modeled backup exactly. No other latent directions
are needed for that local fixed-head statement. With terminal overrides, the
backup is the minimum of these nonterminal modeled values and the exact
terminal utilities; those utilities must remain separate. This identity does
not establish accuracy relative to the oracle, future-head reuse, or deeper
action-conditioned recurrence.

Adding `stopgrad(w/||w||)` as a probe (when `||w||>0`) repairs the missing
direction for the current head, but changes the interpretation to **value-aware
backup consistency**. With the same fixed w and b0 on predicted and encoded
branches, equality of the preactivation minima is equivalent to equality of
their tanh-backed values. Squared preactivation error and squared value error
are not numerically the same objective: tanh saturation changes their scale
and gradients. That distinction warrants an explicit scalar preactivation
backup control, not a claim of a new latent sufficiency principle. If the
target uses the EMA value head instead, teacher/head drift makes the equality
conditions different and calls for the matching EMA-value backup control.

An operator scalar control is also stronger than merely assuming the existing
pointwise EMA-value loss realizes the same weighting: pointwise consistency
penalizes every reply, whereas backup consistency emphasizes extrema. Both
should be named accurately. None requires random latent probes to encode the
known current task direction. A zero w makes all current nonterminal values
constant; random probes do not by themselves establish a useful value head.

The distinction from the rejected sibling idea matters. As derived in
[the mechanism audit](V22_MECHANISM_ANALYSIS.md), uniform pairwise latent
displacement loss is centered residual MSE. It discards group offsets that can
reverse own-action rankings. Retaining that recipe under a new name would not
address the failure. Matching backup operators instead has a different loss,
though no automatic sufficiency guarantee.

## One candidate, with explicit failure modes

For a nonterminal own action `a` at root `s`, enumerate **all** legal replies `b`.
Let `u_ab` be its recurrent H2 prediction and `t_ab` the detached EMA encoding
of the real H2 successor. Fix eight unit linear probes `p_j` before fitting,
drawn independently of labels/development with one published seed. Keep raw
latent dimension fixed across this candidate study. Define

`U_aj = min_b <p_j, u_ab>`; `T_aj = stopgrad(min_b <p_j, t_ab>)`;

`L_operator = mean_roots mean_own_actions mean_probes (U_aj - T_aj)^2`.

Both actions remain inputs to the recurrent predictor. The target is a vector
of **operator evaluations indexed by own action**, not an embedding of a
physically realizable successor. Matching only `max_a U_aj` would allow action
permutations and is inadequate. Retain ordinary pointwise H1/H2 matching and
the existing noncollapse diagnostics; this term replaces neither action
correspondence nor absolute value supervision. Proposed auxiliary coefficient
is one fixed 0.1, with no adaptive probe/weight search; this is a design choice
for a future freeze, not an established optimum.

Keep root-player value perspective explicit. At depth two the player returns
to the root role. Immediate terminal own actions are excluded from this H2
auxiliary and counted; their scalar backup uses exact utility. For terminal
reply branches, use the same detached actual terminal representation on both
sides of the probe comparison, consistent with exact terminal overrides.
This does not teach legality: branch membership comes from shared exact rules.

The limitation is fundamental: even all linear minimum probes identify only
the convex hull of successor latents. They cannot identify interior points,
multiplicities or reply-to-state correspondence. Eight probes are weaker still.
A model can match these targets yet fail deeper continuation or the nonlinear
learned value head. Gradients concentrate on extremal branches, EMA targets can
be strategically poor, and collapsed representations match every probe. Keep
these as refutable risks, not reasons to assert game-theoretic equivalence.

## A finite fair comparison, conditional on V2.3

**Do not execute this matrix without a concrete representation-reuse rationale.**
A testable rationale could be that one frozen representation must support a
predeclared family of distinct continuation-value heads, including heads/tasks
held out from auxiliary fitting, with identical head-training data for every
method. Success must mean measured reuse beyond the current-head scalar
control. Arbitrary random directions are not such tasks. The existing two-game,
single-head endgame bank does not establish this use case. Defining different
opponent-policy expectations would also change the target semantics; it cannot
be relabeled as the current minimax objective. A reuse study would require its
own prospective task/split design and source positioning before this matrix
could be a sensible investment.

If that rationale becomes concrete, first fix a common budget/capacity using
the training-only diagnostic rules.
Do not bundle action gating or a spatial encoder into this experiment. Use one
shared recurrent architecture and shared encoded/predicted policy/value losses;
any added recurrent policy supervision must go to every recurrent arm. Give
every arm a **scalar oracle backup loss** on the same complete legal groups,
with a proposed shared coefficient 0.25: square the difference between each predicted
own-action minimum and its oracle minimum, including exact terminal utilities.
These labels already exist in the fully labeled bank; they are not JEPA-only
supervision. Count and normalize roots/actions explicitly in every arm.

One bounded proposal is six arms × three seeds = **18 cells**, one common
learning rate 0.001, one final checkpoint, no unplanned expansion:

| Arm | Purpose beyond common supervision and scalar backup |
| --- | --- |
| Strong recurrent non-JEPA | Direct matched test of whether scalar decision supervision suffices. |
| Pointwise raw JEPA | Does the proposed operator improve ordinary latent matching? |
| Pointwise raw JEPA + operator probes | Candidate. |
| Decoded dynamics | Does observed-feature prediction explain the gain? |
| Pointwise raw JEPA + pointwise probe matching | Same fixed probes and coefficient, without taking legal-group minima; controls directional weighting and extra auxiliary strength. |
| Candidate with shuffled residual-row groups | Preserves correct prediction/target/action pairs, eligibility and group-size multiset within game; tests legal grouping rather than generic grouping. |

For the last arm, only probe-auxiliary aggregation membership changes; scalar
backups and all supervised terms keep the genuine legal groups. Never shuffle a target
away from its own prediction. Terminal rows must retain their override and
eligibility strata. With a complete orthonormal probe basis, pointwise probe
matching is merely rescaled latent MSE; a finite bank weights a subspace. Neither
is a new objective family. All arms share full groups, labels, exposure and
tuning opportunity. Record active compute; equal updates do not establish
compute fairness. A surviving candidate needs a separately specified comparison
that lets cheaper controls use a matched compute allowance productively.

## Kill criteria and claims boundary

Reject the generic random-probe justification for the present fixed-head task
unless it specifies and tests such a reuse benefit. Do not start if V2.3 indicates
an unresolved common fit-budget limitation.
Otherwise freeze downstream endpoints before any new development scoring.
This mechanism specifically requires favorable **hybrid** evidence, own-action
minimum errors and false-optimistic-backup counts; exact-state improvement alone
can only support encoder regularization. Retain the existing practical margin
and per-game/paired-seed requirements, separately declaring their application
to any new primary endpoint before outcomes are known.

Reject the operator-specific explanation if it fails the strongest scalar or
decoded control, if pointwise probes explain the gain, or if legal grouping has
no supported advantage over shuffled grouping. Imprecise contrasts are
inconclusive, not equivalence. Reject a latent-planning claim if only probe loss
improves, common-offset/value errors grow, or the hybrid gap persists. Never
select a probe seed, favorable game, checkpoint or label fraction post hoc.
Preserve all negative arms and require independent replication and protected
confirmation after any developmental success.

[Value equivalence](https://arxiv.org/abs/2011.03506),
[value-aware model losses](https://arxiv.org/pdf/1806.01265), and
[game refinement metrics](https://arxiv.org/html/0806.4956) already motivate
function/operator-based sufficiency. The full prior-art boundaries and the
convex-hull limitation are recorded in [V23 research options](V23_RESEARCH_OPTIONS.md).
This proposal establishes no new theorem, bisimulation metric or unique JEPA
architecture. The most plausible contribution would be a reproducible controlled
effect of legal adversarial grouping; the audited benchmark/workflow is a
separate reproducibility contribution. Either requires evidence beyond a new
name and a positive development point estimate. No new source search was needed
for this critique; citations reuse the previously inspected primary sources.
