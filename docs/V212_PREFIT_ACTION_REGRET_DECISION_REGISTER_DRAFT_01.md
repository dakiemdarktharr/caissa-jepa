# V2.12 pre-fit action-sensitivity and regret decision register — draft 01

**Status: review aid only; no method choice or gate is accepted here.** This
register consolidates decisions that the action-sensitivity and regret drafts
share or leave open. It does not amend METHOD_SPEC v04, authorize root/branch
generation, scoring, inference, fitting, matches, or outcome access. Keep the
negative feasibility findings and all novelty limits in force.

## Candidate definitions retained for review

- The action-sensitivity draft is descriptive. Its exact-successor prediction
  error, retrieval diagnostic, and receipt-policy-pair-conditioned rollout are
  separate from strength and regret. Its horizon-2/4 branches do not replace
  v04's separate latent-error metrics at horizons 1/2/4/8.
- In the regret draft, “exact fixed-horizon” means an exact search value under
  a declared finite horizon and evaluator. It is not exact full-game minimax
  unless the game is solved to terminal. Scalar bounded-horizon regret and
  sound interval regret are different estimands; do not pool them.
- “Primary executed-action regret” refers only to the primary quantity within
  the regret design. METHOD_SPEC v04 keeps regret secondary to its paired
  head-to-head development score.
- Direct-leaf is not applicable to transition-prediction diagnostics. The
  random-weight pilot graph is not evidence of the eventual trainer/loss graph
  or learned support.

## Decisions and evidence required

| Decision | Current state | Evidence required before freeze | Responsible workstream |
| --- | --- | --- | --- |
| Development-root population, statistical unit, occupancy strata, repeated-state treatment, seat/band/variant weights, and yield/failure rule | Design 02 is a proposal: 48 slot draws per variant across three conditional bands; repeated states count as draws; the equal-band mixture and global six-band stop amend an ambiguous v04 minimum | Independent method disposition must say whether a slot event satisfies the ≥40 requirement, accept or replace the conditional populations and weights, and freeze yield/failure handling before schedule generation | Root-schedule method review |
| Six-arm transition eligibility and support | No V2.12 trainer exists; the pilot is random-weight proxy evidence. Raw-state wiring, target coordinates/masks, and terminal/horizon treatment are unadopted | Implement the planned trainer graph without fitting; independently inspect all six forward/loss graphs, value-only support path, raw-state target/mask/terminal contract, and train-only support ledger semantics | Trainer and raw-state wiring review |
| Action-sensitivity strata and summaries | Draft defines marginal action-index and exact state-action support classes and one-step collision/terminal accounting; no inferential threshold is proposed | Confirm support-key/count semantics against the frozen training objective masks; retain the fixed latent metric and descriptive-only scope; preserve the receipt-policy-pair conditioning in multi-step interpretation | Action-diagnostic protocol review |
| All-legal-action and branch work allocation | Feasibility is unmeasured; no common charged-work allocation or incomplete-cell limits are selected | Freeze complete-work accounting and per-root/per-cell transition, model-call, node, wall-time, and memory limits; assess feasibility under a separately approved no-outcome procedure before any model scoring | Compute/pilot protocol review |
| Regret reference and estimand | Scalar fixed-horizon, sound interval, exact-solved strata, and bounded strata remain alternatives; they are not interchangeable | Select the estimand/strata; pin evaluator and rules/adapter identity to executed bytes/config; specify terminal roots, ordering/ties, query plan, charged transition/node/time/memory limits, incomplete-cell/failure policy, and aggregation | Regret implementation and protocol review |
| Diagnostic priority and artifact contract | Action sensitivity is descriptive; regret is secondary under v04. Ranking/tie tolerance and result fingerprint/content contract remain open | State whether each quantity is descriptive or inferential, freeze any ranking/tie rule and result schema/fingerprints, and keep outcome/selection fields out unless separately reviewed | Evaluation protocol review |

No row is satisfied by document completeness alone. Each prerequisite must be
reviewed against the actual implementation and the applicable resource/gate
evidence. A proposed schedule or cap remains a proposal until that disposition
is recorded. If a required feasibility or training gate fails, preserve the
failure and version/review any redesign before fitting or scoring.

## Review disposition

An independent read-only review on 2026-10-07 found no hard mathematical
contradiction in the current one-step retrieval or horizon-denominator
definitions. It confirmed that the drafts are not decision-complete: root
population and weights, trainer/loss support, all-legal-action feasibility,
charged work, reference choice/provenance/resource limits, terminal handling,
and failure rules remain open. The reviewer accepted no method, arm, metric,
reference, threshold, schedule, or allocation. No roots, branches, outputs,
scores, outcomes, simulations, inference, or training were accessed or run.

## Current decision

Keep METHOD_SPEC v04 current and both diagnostic protocols gated. The next
reviewable milestone is implementation-level trainer/raw-state graph review
and a separately authorized, no-outcome feasibility assessment after the
root-schedule method decision. This register itself opens no gate and supports
no superiority, generalization, novelty, or Q1-readiness claim.
