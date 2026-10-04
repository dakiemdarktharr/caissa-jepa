# V2.12 decision-alignment control review — draft 01

**Status: study-design analysis for independent review.** This memo reads the
frozen V2.12-04 specification against the ARC-Bench and D-JEPA primary
sources. It is not an independent review disposition, a method amendment, or
permission to generate roots/data, fit models, score models, or open outcomes.

## Decision under review

The question is whether the newly added D-JEPA prior art requires an
outcome-supervised candidate-set arm in V2.12-04 before its first fit.

V2.12-04's treatment is the recursive multi-step EMA-target latent-prediction
loss. Its five controls vary prediction target/horizon or remove the transition
predictor while holding the trajectory windows, policy/root-value and rollout-
value losses, initialization pairing, update schedule, rules, and evaluation
schedule fixed. The main candidate is tested against all five controls under a
matched compute gate. The study is designed to estimate the incremental effect
of that latent-matching component inside one fixed four-ply exact-rule max/min
planner, not to rank every available action-selection architecture.

D-JEPA asks a different question. It learns a permutation-equivariant relation
among predicted candidate futures using candidate-level execution outcomes,
then selects among that shared candidate set. ARC-Bench separately audits
whether latent costs rank fixed candidates consistently with their executed
terminal costs. These papers establish candidate-set decision alignment and
its direct measurement as neighboring methods; they do not evaluate
alternating zero-sum board search or the mixture-outcome leaf values used by
V2.12.

## Why a seventh arm is not a matched control

Adding one relational decision head to the existing six-arm panel would
change its estimand. The new head would receive candidate-set structure and
candidate-level outcome supervision that the other arms do not receive. It
would add a different architecture, data interface, loss, and inference path.
A win or loss against that single added arm would not isolate the effect of the
JEPA transition loss, and the existing equal-window, compatible-head, and
within-5%-FLOP requirements would need a new design. Adding the head to all six
arms would instead create a new factorial study with additional interactions,
compute, labels, and multiplicity; it is not an editorial update to v04.

The semantic targets also differ. D-JEPA's reported tasks select goal-reaching
candidates from task costs/success labels. V2.12's action sequence comes from
a fixed synthetic policy mixture, its rollout-value labels describe that
mixture, and its planner applies worst-case max/min backup at internal nodes.
An outcome-supervised board-game candidate control would need a frozen
candidate-set construction, per-candidate rollout policy/opponent treatment,
root-player utility definition, data/split rules, and compute budget. Feeding
exact minimax or bounded-reference scores into its training loss would further
change the estimand and compromise the current evaluation-only boundary for
those references.

## Recommendation

For the narrow v04 hypothesis, retain all six arms unchanged and treat
D-JEPA-style candidate-set alignment as adjacent prior art rather than adding
it as a seventh matched control. Define the result narrowly as the incremental
effect of the specified multi-step JEPA loss against the five frozen controls
inside the specified planner and task scope. The paper must not claim a new
general method for action ranking, superiority to decision-aligned world
models, or state-of-the-art performance from those contrasts.

This recommendation does **not** establish that the six-arm panel is
sufficient for a broader competitive-algorithm claim. A later benchmark that
asks which decision architecture is stronger should compare a separately
versioned, outcome-supervised candidate-set control on the same board states,
legal-action sets, utility, data budget, compute, and held-out schedule. Such a
track needs its own method and evaluation review; it must not be backfilled
into v04 after outcomes are observed.

## Preconditions still open

An independent pre-fit reviewer must explicitly accept or reject this scope
rationale against the complete v04 panel and the current prior-art ledger. The
review must separately dispose of action-discriminative multi-step JEPA prior
art such as ActSWM/AD-WM: either require a new matched control/version or
accept that their continuous-action planner mechanisms are outside this fixed
latent-loss estimand. D-JEPA outcome-set alignment and action-sensitive
predictor training are related but distinct design questions.
The counterfactual-support and decision-regret drafts also remain unfrozen:
root-action score bounds, reference depth/evaluator, exact-versus-bounded
strata, root schedule, missingness, and diagnostic compute need disposition.
Separately, v04's 2.0-second search gate has already failed the Reversi8 rule-
only p90 audit and requires a no-outcome compute-protocol revision and review.
No trajectory generation, model fit, scoring, match, or confirmatory evaluation
is authorized until all applicable review and compute gates pass.

## Source quality and limits

ARC-Bench and D-JEPA are arXiv preprints at this snapshot, and their reported
results are author-reported rather than independently reproduced here. ARC-
Bench's fixed-candidate ranking metrics transfer as evaluation concepts, not
as a board-game result. D-JEPA's author repository states Apache-2.0, while
its checkpoint card says publication licensing and upstream-weight
redistribution checks remain open; its linked dataset card was empty and
unlicensed in this snapshot. No external code, model, or data was downloaded
or reused. See the targeted source descriptions and citations in
[`RELATED_WORK.md`](RELATED_WORK.md).
