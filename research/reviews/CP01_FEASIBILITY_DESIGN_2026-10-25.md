# CP-01 feasibility design review

**Date:** 2026-10-25
**Disposition:** The current matched signed-repair primary is structurally unavailable for the observed Connect Four reference pairs and has narrow potential common support in Reversi. One final, prospective C4 root-window screen widening the empties limit from 8 to 12 is justified before trainer implementation. Keep signed matching. If that bounded screen misses the gates below, stop the two-game mechanism study and report feasibility; do not keep widening or select roots by outcome.

## Inspected evidence and hashes

Checkout commit: `09f18a5cf5e9a827ce526997714a035d4b07175e`. I read the current CP-01 v2 protocol, data contract, attempt 1 receipt, diagnosis receipt, and checked the value head implementation. The attempt was development-data feasibility only: 50 episodes per game, all evaluated references solved, 0 fits and 0 matches; the reference-yield gate failed while the 256 training / 64 development window count and selected-window isolation checks passed. For C4, 43 of 50 episodes had no candidate under the 8-empty limit; the other 7 references were complete but 0 were reference-pairable, and the sole root-decision-critical action had a terminal critical child. Reversi had 50 complete roots, 11 reference-pairable roots and 4 with potential nonzero same-sign support. The diagnosis reports reference-value pairs `critical=-1/control=+1` (12) and `critical=0/control=+1` (6). No model score or locked outcome is present.

| File | SHA-256 |
| --- | --- |
| `research/protocol.yaml` | `7c15ea31d090eec96e439812657559e205ec89e4f4d2de67dc5afe32fb1a1adc` |
| `research/data_contract.json` | `4c84250c3737a9a75bd63ab61e91f40d851b9a0136b465931f6897d8b16ac0bd` |
| `docs/validation/CP01_DATA_ATTEMPT1_2026-10-25.json` | `a2c35335b2c1829d73eb789c6b6517314558df6abc4cda032efabd4c75d52a90` |
| `docs/validation/CP01_DATA_DIAGNOSIS_2026-10-25.json` | `a5db7fac3c0780fafe58587b5caa4c2966bd0ac04d49cf8c98231919c8cf9e0a` |
| `two_player/v212_model.py` | `93cc56127aebf2934670ecf7c18d2204565b9c85e4ef660394b98df7282eb7bf` |

## Structural check and implications

The value head is `tanh(z @ vw + vb)` (`two_player/v212_model.py:188`), hence `q_hat ∈ [-1,1]`. For a reference critical branch with `q_ref=-1`, residual `e_c=q_hat−q_ref=q_hat+1∈[0,2]`. For a control with `q_ref=+1`, `e_u=q_hat−q_ref=q_hat−1∈[-2,0]`. Same-sign matching permits only `e_c=e_u=0`; both repairs then have zero magnitude and cannot change regret. The 12 observed `(-1,+1)` pairs are therefore structurally excluded from the nonzero primary, independent of training. For `(q_ref,c,q_ref,u)=(0,+1)`, nonzero same-sign matching is possible only when both residuals are negative, so the observed potential support is specifically underestimation of both values. This is a narrow conditional estimand, not general coverage of critical replies.

C4's first batch does not fail because the solver could not finish: all seven unique roots were solved, but none met reference-pairability, and the sole decision-critical action had a terminal child that the contract correctly excludes from repair. Reversi has some structurally possible common support, but four roots out of 50 is only a feasibility signal. No trainer result can be inferred from it.

## Recommended bounded next action and stop rule

Make one versioned, outcome-blind C4 sampling revision: change only `connect4-6x7` max empty cells from 8 to 12, keep the same 50 episodes and corpus seed, one SHA-256-selected candidate root per episode before solving, preserve duplicate/no-candidate counts, keep Reversi at 6, and retain the 100,000-node / 2-second per-root limits. The cumulative reference batch must remain within 300 CPU seconds. Preserve attempt 1 and all failures; do not replace roots or select by criticality, value, matchability, or model score. This is a bounded test of whether slightly earlier C4 positions contain nonterminal decisive replies, not a study result.

Before running it, freeze the revised contract/config hash and apply the existing reference gate: at least 5 pairable roots per game and at least 90% complete references. Also require C4 to have at least 2 roots and at least 20% of its reference-pairable roots with nonzero reference-value/sign configurations that can satisfy the signed rule. This is a necessary structural feasibility floor aligned with the existing pilot engineering floors, not power. Reversi's current potential support clears those simple floors (4 of 11), but actual model-based matching remains unknown. The existing development match floor must still be met after a future model evaluation, before interpreting a pilot diagnostic.

If the widened C4 screen still fails reference pairability or nonzero common-support yield, stop the two-game matched mechanism design before trainer construction. Preserve a feasibility report; any Reversi-only mechanism study requires a new prospective protocol and enough fresh roots/common support to justify its estimator. Do not remove signed matching, use zero corrections as evidence, or broaden root selection again to manufacture yield. This review approves no trainer, fit, or Review 2 pilot.

No new data were generated for this review, no model was fit, and no locked data were accessed. The protocol was inspected as JSON-compatible YAML; exact bounded checks above are mathematical implications of the declared value range and the receipt's reported reference-value pairs.

## Implementation amendment review — CP-01 v3 feasibility screen

**Disposition:** Conditional pass for the clean source checkpoint and the single final model-blind feasibility screen only. No trainer implementation, model scoring, pilot, or locked evaluation is authorized by this review. The source changes currently appear in a working tree based on `d2d12f29761f0e745d9c32a2b8df434cb6d1a84a`; the screen should run only after the declared source checkpoint is clean and pinned.

| Inspected file | SHA-256 |
| --- | --- |
| `research/protocol.yaml` (v3) | `b6dcc6d38601982d9f92d4eb030ae9919982631bdaa7371873d2f508fbb82670` |
| `research/data_contract.json` (v2) | `d7ba9dccc3fe6ff9da3e3f71630cea08634ef571acc07ce5e8d4f711a9791e9f` |
| `counterplay/data.py` | `7ae09153a6fd57f9b9d97c8eacb944f2ed5c6c2c43fde00d2a875f7f3da611c3` |
| `tools/counterplay_data.py` | `ba68e721850dec54d5a78e17345d0b4793e6b455df60019e2b8278abe750c09f` |
| `tests/test_counterplay_data.py` | `54ff6b24ba493017418c97d7aa5b487f42b85ddaacbd6fed1a5e029bc3338a66` |
| `tests/test_counterplay_data_producer.py` | `c32d863bd769e99922403a12d2076d95c66ea02262dc8ded19f6c69117bfacd2` |
| `research/protocols/cp01-v2-before-feasibility-amendment.yaml` | `7c15ea31d090eec96e439812657559e205ec89e4f4d2de67dc5afe32fb1a1adc` |
| Prior attempt 1 receipt | `a2c35335b2c1829d73eb789c6b6517314558df6abc4cda032efabd4c75d52a90` |

Protocol and contract IDs and both C4/Reversi empties thresholds agree. The revised root chooser changes only the C4 empty limit and preserves the 50-episode seed namespace and pre-solve hash selection. `critical_pair` enforces nonterminal critical/control branches before the lexicographic choice. `potential_nonzero_signed_support` implements the exact necessary condition for nonzero same-sign residual support: because the reference gap is positive, a shared residual sign exists iff the control-reference gap is below 2. This correctly rejects `(-1,+1)` and accepts a possible `(0,+1)` case without claiming model matchability. The two-root / 20% support gate in code agrees with the protocol and is explicitly necessary, not sufficient.

The wrapper binds the prior receipt by its exact hash and reads its recorded `cpu_seconds` (`15.391540855`), leaving `284.608459145` seconds of the declared 300-second `build()` CPU allowance. It passes that remainder to `build` and records prior, current, and cumulative builder CPU. This matches the first receipt's CPU accounting unit; wall time is reported separately. The 10/10 test result stated in the handoff was not rerun during this review.

One enforcement caveat remains nonblocking for this single authorized invocation: the tool always subtracts the pinned first receipt, but does not detect a completed v3 screen or charge a later v3 receipt. Therefore “no further screen” is currently a protocol/operator constraint, not a program-enforced one-shot lock. Run this amendment once only; preserve its receipt whether it passes or fails, and do not retry. If the tool is ever reused for another screen, add a one-shot receipt/ledger guard and cumulative accounting first. The current protocol's explicit stop rule is sufficient for this one bounded action under the present handoff.

No new screen or scientific data generation occurred during review. The v3 protocol parses as JSON-compatible YAML. This disposition permits only a source checkpoint followed by the single prescribed model-blind screen; its result must meet the reference-yield and nonzero-sign-support gates before any separate Review 2/pilot decision.
