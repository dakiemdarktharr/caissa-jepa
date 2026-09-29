# An elementary limitation of additive action conditioning

Date: 2026-09-29. **Mathematical audit and proposed diagnostic only.** No V23
partial metrics, datasets or new fits were inspected. This is not a frozen
experiment, a novel theorem claim, or evidence that a replacement improves
playing strength. The analysis concerns the present recurrent map with a
fixed encoder/target snapshot; the scope of learned encoders is discussed below.

## Coordinate ordering cannot reverse with the action

For coordinate j, the current transition has the form

`g_j(z,a) = tanh(w_j^T z + beta_aj)`.

Here beta_aj includes the action embedding and bias. For any two fixed input
latents z1,z2 and any action a, strict monotonicity of tanh gives

`sign(g_j(z1,a)-g_j(z2,a)) = sign(w_j^T(z1-z2))`.

The right side does not depend on a. Actions can change the size of the gap
through saturation, but not its sign. Equality holds for every action if the
linear gap is zero. In finite precision saturation can create extra ties, but
it does not restore a strict reversal. This restriction holds for any input
dimension and learned matrix W; it is not a claim that the nonlinear model has
no state/action interactions.

Consequently, if two states admit two common legal actions a,b and the target
coordinate has gaps

`t_1a - t_2a = alpha > 0`,
`t_1b - t_2b = -beta < 0`,

the transition cannot match all four targets exactly. Both comparisons must
use the same input state pair and coordinate, the same action identities,
and one frozen target encoder. Mixing games or incompatible player perspectives
would not constitute this test. At the second recurrent step the same fact
applies to two fixed intermediate latents and common legal reply actions.

## A quantitative squared-error lower bound

Suppose two target scalars x>y have gap d, while predictions u<=v have the
opposite weak order. Then

`(u-x)^2 + (v-y)^2 >= d^2/2`.

The constrained unconstrained-range minimum is at u=v=(x+y)/2. Restricting
predictions further cannot reduce this bound. Therefore one of the two action
pairs above must incur its wrong-order cost, giving

`sum_(i in {1,2}, action in {a,b}) (g_j(z_i,action)-t_i,action)^2`
`    >= min(alpha^2,beta^2)/2`.

The four-observation **mean** squared error is at least
`min(alpha^2,beta^2)/8`. If a reported latent MSE additionally averages over d
coordinates, this coordinate contributes at least `min(alpha^2,beta^2)/(8d)`.
Summing these bounds over contradictory coordinates is valid for this same
four-observation block. The bound can be loose: the shared preactivation gap
imposes more constraints than mere ordering. No attainability assertion is
made for the original additive map.

For positive observation weights lambda1,lambda2, the violated-pair cost is

`[lambda1*lambda2/(lambda1+lambda2)] * d^2`.

For one state pair and several common actions, sum those costs separately over
positive and negative target gaps. Their minimum is a lower bound on weighted
SSE, because the predicted coordinate must choose one ordering for all actions.
Zero target gaps impose no such penalty. Divide by the declared total weight
and coordinate normalization to compare with an actual loss.

**Do not sum bounds over overlapping blocks without accounting for reuse.**
The same prediction residual can occur in many state/action pairs. A disjoint
block packing gives a valid summed bound. Alternatively, a bound that sums
over all blocks must divide by a proven maximum residual participation count;
otherwise it exaggerates irreducible loss. Uniform-fork and uniform-own-action
weightings are different and require their own explicit lambda values.

## Minimal example and a stronger swap pattern

Let z(s1)=+c, z(s2)=-c with 0<c<1. Two common legal actions, identity and swap,
have targets:

| Input | Identity | Swap |
| --- | ---: | ---: |
| s1 | +c | -c |
| s2 | -c | +c |

Here alpha=beta=2c. Every additive one-coordinate predictor has four-target
SSE at least 2c^2, or mean error at least c^2/2. Taking c=1/2 gives SSE>=1/2
and mean>=1/8. These are algebraic bounds, not fitted numerical results.

The target pattern need not arise from arbitrary coordinate choices. Consider
the exact transition diamond

`T(s1,a)=u, T(s2,a)=v, T(s1,b)=v, T(s2,b)=u`.

For any fixed target embeddings t_u,t_v, each nonzero coordinate difference
reverses under the two actions. Summing the coordinate bounds yields

`four-target vector SSE >= ||t_u-t_v||_2^2 / 2`,
`mean squared error over four observations and d coordinates`
`    >= ||t_u-t_v||_2^2 / (8d)`.

This statement permits arbitrary learned input embeddings of s1 and s2. A
learned target encoder can evade exact contradiction only by making t_u=t_v
for that diamond, or by departing from the specified coordinatewise additive
transition/pointwise target objective. The toy graph can be embedded in a
deterministic alternating game with s1,s2 at one player's turn and u,v at the
other player's turn; distinct continuation utilities can occur later. This
is an existence construction, not a claim that the current board datasets
contain exact diamonds, or that a terminal override must incur model error.

In fact, the **literal raw-state swap diamond with two distinct common legal
cell actions is excluded by the current placement adapters**. Reading
`two_player/games.py` shows that a legal placement fills its own previously
empty cell; Reversi flips only already occupied cells. If a and b are distinct
and legal in both states, cell a is empty in both inputs. After a it is filled;
after b it stays empty. Hence `T(s1,a)` cannot equal `T(s2,b)` as a raw board.
Forced pass is offered only when there are no legal placements, so it cannot
supply a second common alternative. This argument covers the present Connect4
and Reversi cell-action encoding; it is not a theorem about every possible game
or canonicalized state equivalence. The abstract swap construction motivates
the general expressivity issue, while **frozen latent-coordinate reversals**
are the relevant empirical question in these adapters.

If the same L-Lipschitz scalar head reads target embeddings and approximates
the two root-perspective continuation values within eta, a true utility gap
Delta gives `||t_u-t_v|| >= max(Delta-2eta,0)/L` for L>0. The vector SSE bound
then becomes `max(Delta-2eta,0)^2/(2L^2)`. This is conditional on measured target
accuracy and a bounded head norm, not an unconditional planning lower bound.

## Two architectures can express the toy reversal

A rank-one multiplicative state/action gate represents the scalar example
exactly. Encode identity/swap by u_a=+1/-1 and use

`g(z,a) = tanh((atanh(c)/c) * z * u_a)`.

For z=+c or -c, its outputs are precisely the four targets. This can be embedded
in a residual factored transition with its additive terms set to zero.

A two-layer nonlinear MLP can also represent the example with only two hidden
units; gating is not the only remedy. For any k>0, let

`s=z/c+u_a`,
`h1=tanh(k*(s-1)), h2=tanh(k*(-s-1))`,
`A=tanh(k)-tanh(3k), B=-2*tanh(k)`,
`gamma=2*atanh(c)/(A-B), delta=-atanh(c)-gamma*B`.

Then `g=tanh(gamma*(h1+h2)+delta)` is +c for s=+2 or -2 and -c for s=0.
The denominator is strictly positive: writing t=tanh(k),
`A-B=3t-tanh(3k)=8t^3/(1+3t^2)>0`. Thus all parameters are finite.
Since u_a is a linear function of a two-action one-hot vector, this is an
ordinary MLP on concatenated state/action input.

These constructions establish expressivity on four points, not favorable
optimization, generalization or compute. Any later comparison must give
additive, gated and nonlinear-MLP transitions the same task supervision and
every relevant JEPA/non-JEPA objective, with credible parameter and measured
compute accounting. Factored action-dependent transformations already appear
in [Oh et al., Action-Conditional Video Prediction, NIPS 2015](https://proceedings.neurips.cc/paper/2015/file/6ba3af5d7b2790e73f0de32e5c8c1798-Paper.pdf).
Replacing the present map with this known mechanism is not a novelty claim.

## What this does not prove

- General reversals of chosen latent coordinates depend on the learned basis.
  Unlike the exact swap diamond, a pattern seen at one frozen encoder might
  disappear when the encoder co-adapts. Target/online EMA differences matter.
- Latent distances can shrink while the value head grows. Global variance or
  effective-rank gates do not ensure separation of the particular states u,v.
  An L-dependent bound must report L; normalization introduces its own geometry.
- Latent inconsistency does not necessarily imply wrong scalar values. With
  multiple latent coordinates, a value head can combine coordinate differences
  of opposite signs, whose magnitudes vary by action, and reverse scalar value
  order even though no individual coordinate reverses. A value-equivalent
  model may therefore plan well while refusing to reconstruct target latents.
- A pointwise JEPA objective may be harder for this architecture than value-only
  training. That is a concrete objective/architecture mismatch hypothesis, not
  proof that resolving it makes JEPA outperform equally strengthened controls.
- Finite training time, sampling and optimization can dominate the bound. The
  complete V23 outcome must be interpreted first. This memo does not bypass it.

## A bounded probe worth considering after the complete diagnostic

The restriction warrants a **targeted training-only feasibility probe**, not
an immediate architecture grid. Freeze its source, selection and resource cap
before measuring checkpoints. Use only transitions already present in the
audited training artifact; generate no oracle labels or development queries.

Choose within-game, same-player state pairs admitting at least two common
recorded legal actions. Select state/action blocks by a deterministic hash of
state/action identities before inspecting embeddings or errors. Keep all
selected blocks, including those with no reversal. Do not search the current
placement data for literal raw-state diamonds already excluded by the rule
argument above. Probe the broader frozen-coordinate ordering restriction; its
presence and magnitude are not established by the abstract counterexample.

For every included family/seed/capacity, freeze the checkpoint and separately
test its online and actual EMA target encoders. Report common-action coverage,
coordinate gap distributions, strict and tolerance-qualified reversal counts,
and conservative weighted lower bounds with a documented disjoint packing or
reuse correction. Normalize consistently with the training loss; distinguish
raw squared distances from dimension-scaled or standard-deviation diagnostics.
Count exact/near ties explicitly and preserve the denominator of all eligible
blocks. If group weighting differs from the sampler, do not call the result a
lower bound on its training objective without the proper weights.

Report target-value separation/accuracy and value-head norm, plus observed
pointwise and value errors on these same predefined blocks. An appreciable
latent lower bound accompanied by almost no decision/value discrepancy would
support an overly restrictive latent target objective, not automatically a
need for stronger dynamics. A negligible bound, little common-action coverage,
or discrepancies confined to tiny latent gaps would weaken this rationale for
an architecture change. No search decisions or performance claim follow from
this diagnostic alone.

Only if the completed budget diagnosis and this finite probe justify the
mechanism should a separate development protocol compare the additive map,
one fixed gated map and one matched nonlinear MLP. Keep the strongest controls,
common recurrent task supervision and existing promotion requirements. Do not
add new architectures until a preferred result appears.
