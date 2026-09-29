# V2.4 order-probe specification review

2026-09-29. **Specification-only independent review: PASS, no blocking
mathematical finding.** Reviewed [the frozen protocol](METHOD_V24_ORDER_PROBE.md)
and [the additive-dynamics derivation](V24_ADDITIVE_DYNAMICS_LIMIT.md).
No implementation, dataset, checkpoint or partial experiment output was read;
no fitting or measurements were performed. This is not an implementation pass.

## Bound and comparison direction

The specified comparisons are **the same pair of states under two actions**:
`d_a=t(s1,a)-t(s2,a)` and `d_b=t(s1,b)-t(s2,b)` in one coordinate. They are not
the alternative comparison between two actions within each state.

For the present map, the predicted state-pair preactivation gap is
`w_j^T(z1-z2)` for every action. Monotone tanh preserves its weak ordering,
including ties. If target state-pair gaps have opposite signs, at least one
target pair must be approximated with the wrong weak ordering. Projecting two
scalar targets separated by d onto a reversed-order constraint has minimum
SSE `d^2/2`, attained at their midpoint in the relaxed prediction class.
Therefore the four-edge SSE is at least `min(d_a^2,d_b^2)/2`. Additional model
constraints can raise this minimum, not invalidate the lower bound. This is
an elementary conservative bound; attainability by the actual model is not
claimed. The online input and EMA target spaces need not be identical for
this fixed-target ordering argument.

Summing over coordinates and blocks is valid because each `(root,action)`
residual occurs in at most one retained block. Shared model parameters or
repeated target node states do not invalidate the sum: its observational unit
is the unique root/action edge, not a deduplicated successor state.

For B blocks, latent width d and N total unique H1 edges:

- Packed MSE bound is `summed_bound_SSE / (4*B*d)`.
- Full-H1 MSE bound is `summed_bound_SSE / (N*d)`; unselected-edge errors are
  nonnegative.
- Bound/full observed SSE must use the same uniform-edge latent residuals and
  target space. Neither fork frequency nor equal-root value weighting belongs
  in this ratio.

The all-four-nonterminal sensitivity correctly restricts the already fixed
packing and uses its own denominator. Repacking would change the intervention.
Zero supported blocks or zero denominator are unavailable, not zero-error
successes. Direct's unused transition correctly remains unscored.

## Decision rules and scientific limits

The 25% coverage and 10% bound/full-SSE thresholds are explicitly heuristic,
separate for each game/capacity. Three finite seed ratios with median at least
10% necessarily contain at least two ratios at least 10%; keeping both stated
checks is harmless but does not add independent evidence. No pooled pass should
hide a failed game/capacity. Report the complete decision map and sensitivity.

Strict reversals, tolerance-qualified reversals and near ties can overlap in
the declared summaries: a strict sign reversal with tiny gaps remains a near
tie. They must not be presented as disjoint categories. The exact sign-based
bound and separately reported numerical tolerance are appropriate. A bound
above observed packed error outside tolerance must fail the whole probe.

The protocol correctly limits the inference to the frozen representation,
H1 additive map and uniform-edge diagnostic. The target encoder can co-adapt,
coordinate bases can change, value directions can cancel latent errors, and
terminal predictions are overridden in planning. Consequently, a material
latent obstruction does not establish irreducible joint training error,
opponent-response deficiency, wrong decisions or JEPA superiority. A low bound
does not establish additive adequacy. The common 128/64, 160-epoch operating
point is explicitly bounded and not described as convergence.

## Implementation checks to preserve this pass

1. Build and save deterministic block receipts before loading any model.
   The V2.3 strict report verifier itself loads checkpoints: schedule that
   verification after packing is saved, while completing it before probe
   encodings. Early verification of ledger/data identities can remain read-only.
2. Confirm the actual H1 implementation has the stated affine-plus-action,
   coordinatewise monotone form; do not silently measure a projected predictor,
   H2 unroll or the alternative action-gap bound.
3. Test the four-edge inequality, a zero/reversed-gap case, disjoint packing,
   both normalizations, terminal subset without repacking, direct exclusions
   and zero-support/ratio handling. Report signed and absolute gap quantiles
   with explicit names so “gap quantiles” cannot conceal their convention.
4. Preserve all 18 checkpoints, both target spaces, source/tensor hashes,
   resource acceptance checks and failure receipts. A separately reviewed
   implementation and frozen source are still required before execution.
# Post-review clarifications

Before implementation, the specification was amended to make both nonterminal
denominators/coverage explicit, retain terminal-sensitive interpretation, fix
successor-player value perspective, define absolute-gap quantiles and ordering
tolerance, save packing before checkpoint-loading verification, bind the exact
independent-audit hash, and include enumeration/sorting in resource checks.
These clarify the prospective measurement; no checkpoint was measured during
review. The second independent reviewer supplied these implementation boundaries.

## Implementation review before launch

The separate `two_player_v24_probe` implementation received independent source
review and synthetic legal-fixture integration tests. Review found and repaired
three issues before any research measurement: a report-verification failure could
otherwise be marked complete; a late resource failure could leave a provisional
positive report; and direct-model ordering diagnostics used incompatible null/zero
conventions across modules. Final saved schedule and all measurement hashes are
also reread before completion, with tamper regressions. No blocking source finding
remained at launch review. Artifact audit remains necessary after execution.

Full regression passed239 tests in133.537s before the final output-hash guard;
the final runtime suite passed11 tests in4.852s after that guard. Tests use small
synthetic fixtures or mocked cells, not the research checkpoints, and are not
evidence for JEPA. All frozen legacy source remains unchanged.
