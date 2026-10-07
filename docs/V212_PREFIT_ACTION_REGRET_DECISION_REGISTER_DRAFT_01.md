# V2.12 pre-fit action-sensitivity and regret decision register — draft 01

**Status: review aid only; no root/regret/diagnostic choice or gate is
accepted here.** The narrow raw-state contract is retained in METHOD_SPEC
v06, which also fixes Adam/EMA semantics; this register consolidates decisions
that the action-sensitivity and regret drafts share or leave open. It does not
change the v06 method or authorize root/branch generation, scoring, inference,
fitting, matches, or outcome access. Keep the
negative feasibility findings and all novelty limits in force.

## Candidate definitions retained for review

- The action-sensitivity draft is descriptive. Its exact-successor prediction
  error, retrieval diagnostic, and receipt-policy-pair-conditioned rollout are
  separate from strength and regret. Its horizon-2/4 branches do not replace
  current v06 method's separate latent-error metrics at horizons 1/2/4/8.
- In the regret draft, “exact fixed-horizon” means an exact search value under
  a declared finite horizon and evaluator. It is not exact full-game minimax
  unless the game is solved to terminal. Scalar bounded-horizon regret and
  sound interval regret are different estimands; do not pool them.
- “Primary executed-action regret” refers only to the primary quantity within
  the regret design. Current METHOD_SPEC v06 keeps regret secondary to its
  paired head-to-head development score.
- Direct-leaf is not applicable to transition-prediction diagnostics. The
  random-weight pilot graph is not evidence of the eventual trainer/loss graph
  or learned support.

## Decisions and evidence required

| Decision | Current state | Evidence required before freeze | Responsible workstream |
| --- | --- | --- | --- |
| Development-root population, statistical unit, occupancy strata, repeated-state treatment, seat/band/variant weights, and yield/failure rule | Design 02 is a proposal: 48 slot draws per variant across three conditional bands; repeated states count as draws; the equal-band mixture and global six-band stop amend an ambiguous v04 minimum | Independent method disposition must say whether a slot event satisfies the ≥40 requirement, accept or replace the conditional populations and weights, and freeze yield/failure handling before schedule generation | Root-schedule method review |
| Six-arm transition eligibility and support | No V2.12 trainer exists; the pilot is random-weight proxy evidence. The narrow raw-state contract is retained in v06 after read-only method disposition; no trainer implementation graph or target-support ledger exists | Implement the trainer graph without fitting and inspect all six forward/loss graphs, value-only support path, raw-state masks/gradient/terminal contract, and train-only support ledger semantics; then measure the full six-arm FLOP gate before any fit | Trainer and raw-state wiring review |
| Action-sensitivity strata and summaries | Draft defines marginal action-index and exact state-action support classes and one-step collision/terminal accounting; no inferential threshold is proposed | Confirm support-key/count semantics against the frozen training objective masks; retain the fixed latent metric and descriptive-only scope; preserve the receipt-policy-pair conditioning in multi-step interpretation | Action-diagnostic protocol review |
| Cross-arm latent-error comparison and protocol version anchors | The drafts now identify current METHOD_SPEC v06 and bar cross-arm raw latent-MSE ranking; scale calibration and protocol adoption remain open | Keep raw MSE descriptive within an arm unless train-only scale calibration and a cross-arm estimand are preregistered; preserve v06 optimizer semantics and adopted raw-state contract | Action-diagnostic and regret protocol revision/review |
| All-legal-action and branch work allocation | Feasibility is unmeasured; no common charged-work allocation or incomplete-cell limits are selected | Freeze complete-work accounting and per-root/per-cell transition, model-call, node, wall-time, and memory limits; assess feasibility under a separately approved no-outcome procedure before any model scoring | Compute/pilot protocol review |
| Six-arm training-FLOP parity | Static dense-forward inventory shows raw-state 72,544 versus multi-step JEPA 40,864 MAC/window (+77.53%); it is not a total-FLOP measurement or a gate verdict | After all six graphs and masks are implemented and independently reviewed, profile forward/backward work per update on identical dry-run batches and masks; require the current v06 ≤5% total-training-FLOP parity or version/re-review a method change before fitting | Trainer implementation and compute review |
| Regret reference and estimand | Scalar fixed-horizon, sound interval, exact-solved strata, and bounded strata remain alternatives; they are not interchangeable | Select the estimand/strata; pin evaluator and rules/adapter identity to executed bytes/config; specify terminal roots, ordering/ties, query plan, charged transition/node/time/memory limits, incomplete-cell/failure policy, and aggregation | Regret implementation and protocol review |
| Diagnostic priority and artifact contract | Action sensitivity is descriptive; regret is secondary under v06. Ranking/tie tolerance and result fingerprint/content contract remain open | State whether each quantity is descriptive or inferential, freeze any ranking/tie rule and result schema/fingerprints, and keep outcome/selection fields out unless separately reviewed | Evaluation protocol review |

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

An additional approved read-only review on 2026-10-07 found the action-
sensitivity and executed-action regret drafts' core estimands coherent as
separate estimands, but not preregistration-complete. It requires explicit root and
failure rules, reference/evaluator/compute choices, implementation binding,
per-cell limits, result fingerprints, and a choice between descriptive and
inferential claims. Raw latent MSE magnitudes should not be ranked across arms
with potentially different latent scales absent train-only calibration and a
preregistered estimand. The reviewer found the action-sensitivity/regret
drafts' v04/v05 anchors stale relative to current v06. The drafts have since
been editorially rebased; a follow-up review confirmed the v06 anchors and
scale/overlap/query-plan caveats. Protocol adoption remains open. Before model
scoring, a split audit should cover episode, state, augmentation, and symmetry
overlap, not only exact absolute-board support keys. Caller-supplied evaluator
hashes in the bounded reference solver are labels rather than proof of loaded
implementation; tiny-
oracle equivalence and actual all-action feasibility remain open. No design
was adopted and no roots, scores, outcomes, or simulations were accessed.

Separate approved read-only reviews found V03 runtime fingerprints descriptive
and its pilot without hard containment/operational receipt evidence; the
generation protocol and v05 root/calibration proposals remain
non-frozen/non-authorizing; and the current raw-state partial accounting has
no raw-state-specific omission within its stated scope. These reviews did not
clear runtime, generation, calibration, graph-freeze, or compute-parity gates.

## Current decision

Keep METHOD_SPEC v06 current; its §7 root schedule still follows the v04
method until a versioned amendment is independently accepted. The diagnostic
drafts now name v06 but remain gated pending full preregistration and
implementation evidence. The next reviewable milestone is
implementation-level trainer/six-arm graph review, after any required method
dispositions for root scheduling. This register itself opens no gate and
supports no superiority, generalization, novelty, or Q1-readiness claim.
