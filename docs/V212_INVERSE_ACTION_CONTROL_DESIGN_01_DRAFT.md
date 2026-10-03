# V2.12 inverse-action control design 01 — draft

**Status: proposal for independent review only.** This note evaluates one
control suggested by recent decision-aligned JEPA work. It does not amend the
reviewed V2.12-04 specification, authorize data generation, fitting, model
scoring, matches, or outcome access. The six v04 arms, analysis plan, and
negative findings remain unchanged.

## Why consider an inverse-action control

V2.12's predictor already consumes the exact action and is trained to predict
latent consequences along logged one-, two-, and four-ply action sequences.
Every arm also has a masked policy loss that predicts a recorded root action
from the current latent. DA-LeWM adds a different auxiliary task: infer an
action from consecutive latents. This could alter what the shared latent
retains, even when the forward model is action-conditioned.

This is a potential confound/control, not a proposed fix or a prediction of
benefit. In these deterministic board rules, the transition pair
(state, successor) identifies the action: a placement changes its selected
cell, while Reversi pass is action 64 and occurs only when no placement is
legal. Thus an inverse-action target is reconstructable from the exact
transition. It tests whether auxiliary pressure to retain that transition
identity changes planning, rather than adding new environment information.
It may be redundant with the existing action-conditioned predictor and policy
head; that negative possibility must remain testable.

## Candidate auxiliary objective

For a training transition (s_t,p_t,a_t,s_(t+1)), compute the shared online
representations z_t=f_theta(x(s_t,p_t)) and
z_(t+1)=f_theta(x(s_(t+1),p_(t+1))). Add one shared categorical head

    q_psi(a_t | z_t, z_(t+1), p_t, game)

with a 65-action output and a legal-action mask from the exact adapter at
s_t. Use mean cross-entropy over observed transitions. The target is the
recorded action only; no terminal outcome, reference score, minimax label, or
unrecorded counterfactual action enters this loss. Include observed forced-pass
transitions with fixed action id 64. The head is training-only and discarded
for planning.

The draft proposes a factorial auxiliary switch lambda_ID in {0,1}: the same
head, initialization, forward/backward computation, and parameter count are
present for every arm; the loss coefficient is zero or one. This keeps compute
and architecture comparable while estimating the effect of inverse-action
supervision. The lambda=1 scale is an initial protocol candidate, not a tuned
or reviewed choice; independent review must either accept it as frozen or
replace it before any fitting. No coefficient sweep is allowed. Measure actual
FLOPs and retain the existing 5% parity gate.

## Comparison and interpretation

The candidate panel crosses the v04 six-arm factor with the inverse-action
factor, yielding twelve conditions. Keep data/windows, paired seeds, optimizer,
updates, and held-out roots identical. Report both:

- the JEPA-versus-non-JEPA contrasts with and without inverse-action
  supervision, preserving v04's existing primary head-to-head outcome gate;
- the inverse-action main effect and its interaction with model family on the
  predeclared action-regret/ranking diagnostics and primary outcome.

The added factor does not replace head-to-head outcomes with a representation
metric. If auxiliary supervision helps every model family equally, it does
not establish a JEPA-specific effect. If it helps only the JEPA arm, the
interaction remains an empirical result requiring the same multiplicity,
compute-parity, and held-out gates. Do not select the auxiliary weight or
action metric after seeing development outcomes.

Do not add a goal-conditioned future-action head to this control by default.
Those targets are actions chosen by the synthetic behavior-policy mixture,
not optimal actions. Given a current and distant board, several legal action
sequences can reach the same target state; squared or categorical imitation
can teach behavior frequency rather than minimax decision quality. Any such
head would require a separately named behavior-modeling estimand and review.

## Required pre-fit checks

Before any data generation or fitting under a future version, reviewers must
decide whether this factorial control is necessary and affordable; confirm
loss reduction, masks, role conditioning, target encoder/gradient flow,
terminal-transition treatment, and initialization pairing; and revise the
method, training-compute, and multiplicity plans together. A synthetic
in-memory contract test should verify the action mask and inverse label for
each legal transition in bounded deterministic paths across all four variants,
including wins, draws, and Reversi pass. These checks test implementation
contracts only and do not authorize corpus generation.

The design is not accepted by this note. The present data, split/leakage,
compute, novelty, independent-review, and outcome gates remain closed.
