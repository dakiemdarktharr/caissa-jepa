# V2.12 duplicate and overlap policy audit 01

**Status: review proposal only.** This is a no-training source audit. It does
not authorize trajectory or root generation, fitting, match play, or outcome
access, and it does not amend the frozen synthetic-auditor contract or
`METHOD_SPEC_V212.md`.

## Source-level conflict

The frozen `V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md` asks its synthetic fixture
to reject a duplicate window, including a role- or symmetry-canonical
equivalent. The implementation follows that contract: `_window_signature`
canonicalizes an ordered state/action path, and `audit_trajectories` raises on
any repeated signature. It emits all in-memory windows and does not implement
the 928-window selection or a production corpus policy.

The later `METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md` proposes a different
fit-bank estimand: source windows are distinct by
`(game/rules fingerprint, episode id, start ply)`; canonical-equivalent content
is reported diagnostically, not silently dropped or upweighted. Its open
review question explicitly asks how production handling should replace or
scope the fixture's unconditional duplicate rejection. Reusing the fixture as
a production filter unchanged would therefore contradict the later proposal.

## Proposed identity and disposition matrix

| Scope | Identity | Proposed disposition |
| --- | --- | --- |
| Fit-bank source row | `(game/rules fingerprint, episode id, start ply)` | Require uniqueness; a repeated source id is an integrity failure. |
| Fit-bank content | Exact and role/spatial-canonical ordered state/action window signatures, with game/rules/dimensions included | Count and report collisions by signature and source lineage; retain selected rows and do not reweight. This is a data-quality diagnostic, not a split leak by itself. |
| Cross-partition state/content | Raw and role/spatial-canonical state keys and ordered-window keys under the same game/rules identity | Any prohibited train/evaluation collision fails the data gate. Preserve exact keys and owner metadata so the collision can be explained. Fit and current held-out-size roots are structurally separate by dimensions; that does not validate a future same-size split. |
| Development root bank | Candidate-slot ID plus reachable root receipt under the frozen game/rules identity | The current Design02 proposal accepts 48 slot observations per variant, 16 per occupancy band from 64 candidates per band. Slot ID is the sampling unit; repeated raw/canonical states remain separate draws and are reported by multiplicity. The proposed global stop if any of the six strata yields fewer than 16 remains unaccepted; no minimum schedule-pass probability is set. |
| Horizon target | Source-window id plus target horizon and exact terminal/mask status | Keep valid latent targets, terminal-exact targets, and unavailable tail targets in separate counts. These statuses do not change source-window identity or authorize substituting a missing target. |

The fit-bank content signature must transform state, action, and successor
together under one mapping. It may be used to report canonical duplicates or
cross-partition equivalence only after the adapter-wide legal-set and
transition-commutation checks in the counterfactual-support protocol pass.
Raw exact identities remain available as the primary audit record.

## Root-sampling and inference alignment

The earlier Design01 proposal accepted symmetry-unique roots from candidate
slots. This section's original warning applied to that superseded unique-root
filter. Current Design02 replaces it with first-valid slot acceptance and
keeps repeated board states as separate observations. Under its stated IID
within-variant/band and slot-local eligibility assumptions, accepting the
first 16 valid slots does not condition on board identity or previous slots;
repeated states are chance repetitions in the sampled distribution, not
rejections. Design02's success-conditional first-passage target and slot-ID
unit remain proposals and have not been observed or independently accepted.

Design02 and root-sampling amendment v05 now propose a fixed equal-weight
mixture across the three occupancy bands, a shared model-seed resample, and
slot-ID resampling with replacement within each variant × band stratum. This
resolves the earlier editorial mismatch with v04's unspecified root strata,
but it does not validate the finite-sample crossed bootstrap, max-|T|
intervals, centered tests, or Holm family. The analytic six-stratum yield
sensitivity in `V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md` is illustrative
only; neither an acceptable probability of schedule completion nor the
global under-yield disposition is accepted.

Unique-state sampling and fixed-bank-conditional inference were earlier design
alternatives, not the current v05/Design02 proposal. Adopting either would
require another versioned estimand and matching inference review. Before
scoring, independent reviewers still must accept the meaning of v04's 40-
situation minimum under the 48 slot-observation proposal, the all-six yield
rule, stratum weights and resampling implementation, and whether design-matched
calibration is required. No statistical validity or operating characteristics
are inferred from this editorial reconciliation.

## Adapter symmetry inventory from source

| In-scope adapter | Spatial mappings declared by `BoardGame.transforms()` | Action mapping and rule argument |
| --- | --- | --- |
| Connect Four 6x7/k4 | Identity and horizontal reflection | Gravity keeps the bottommost empty cell in each column mapped to the corresponding reflected column; the four line directions are preserved as a set. |
| Connect Four 8x8/k4 | Identity and horizontal reflection | Same gravity/line argument as 6x7; square shape does not enable rotations because the adapter has gravity. |
| Reversi6 and Reversi8 | The eight square D4 rotations/reflections | The eight neighbor rays and flips are permuted; legal placements map bijectively, and the forced-pass action id `64` stays fixed. |

The shared action vocabulary stores board cells with stride 8, even when the
board is smaller. `BoardGame.transform` maps a cell action through the same
cell permutation used for the board, then returns it in that padded action
vocabulary; it handles `64` separately as a fixed pass. `BoardGame.canonical_key`
normalizes pieces relative to the side to move and minimizes over spatial
mappings, but returns only a hash, not the mapping that attained the minimum.
It therefore cannot by itself supply a consistent canonical action key. A
future edge ledger must enumerate each declared mapping, transform source,
action, and successor together, normalize role only as a joint color/player
relabeling, and then select a joint key.

This inventory is a structural reading of the in-scope rules and transform
code, not an exhaustive adapter-wide proof. `transforms()` does not assert
bijectivity. The new bounded suite exhausts distinct states reachable through
four legal plies, supplements them with three deterministic legal paths to
terminal, and checks a hand-built Reversi pass fixture. For every declared
mapping it checks permutation validity, complete legal-action-set bijection
at each fixture state, transition commutation for every legal action,
terminal-result preservation, and canonical-key invariance. It cannot
establish these properties over all later reachable states. Keep canonical
edge summaries disabled pending broader/adversarial state coverage and
independent protocol review. These code checks do not authorize canonical
deduplication, data generation, or training.

## Focused symmetry software-contract test

Added `tests/test_v212_symmetry_properties.py`. It exhausts all distinct
states reachable through four legal plies for the four V2.12 variants, then
adds three deterministic in-memory legal paths through terminal states and a
hand-built Reversi forced-pass fixture. For each declared mapping it checks
permutation validity, the complete legal-action set at every fixture state,
transition commutation for every legal action, terminal-result preservation,
and canonical-key invariance under spatial and side-to-move role transforms.
The Reversi fixture also verifies that pass action 64 remains fixed under all
D4 mappings.

After the four-ply expansion, the suite passed 2/2 in 19.7 seconds; combined
with `tests.test_v212_trajectory_audit`, 9/9 passed in 19.3 seconds. Coverage
is exhaustive only through the shallow four-ply frontier; later game states
are represented by three deterministic paths, not exhaustive enumeration.
This is not evidence that a generated corpus is leakage-free. It does not
enable canonical edge summaries, root generation, fitting, or match play.
Independent review and broader adversarial state coverage remain open.

## Implementation boundary and required review

Keep the current synthetic fixture unchanged for its frozen positive/fault
contract. Do not route a production candidate bank through its unconditional
duplicate rejection. After the method amendment, development-root schedule,
and generation protocol are independently accepted, a separate production
materializer/auditor should:

1. fail on repeated source-window ids, invalid replay, or prohibited
   cross-partition raw/canonical overlap;
2. retain all selected fit source windows while reporting exact and canonical
   repeated-content counts by game, policy pair, seat, and phase;
3. select evaluation root slot observations only by the frozen pre-score
   candidate schedule, retaining repeated board identities as specified by
   the accepted estimand and failing closed if its minimum yield is not met; and
4. report valid, terminal-exact, and unavailable H1/H2/H4 targets separately
   without silently changing the 928-window count.

Before any executable generation work, independent review must resolve the
matrix above, including the meaning of independent development situations,
the global six-stratum yield rule, and the minimum acceptable probability that
the fixed schedule can pass. The current synthetic tests establish none of
these production properties. No data feasibility, leakage-free corpus,
support, or training-readiness claim follows from this audit.
