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
| Development root bank | Reachable root state under the frozen game/rules identity and declared symmetry-equivalence rule | Count only symmetry-distinct roots toward the independent-situation minimum. Use a predeclared deterministic candidate schedule; if it cannot supply the frozen minimum, fail before scoring and do not top up after outcomes. The proposed 48-root/64-slot schedule still lacks a verified yield audit. |
| Horizon target | Source-window id plus target horizon and exact terminal/mask status | Keep valid latent targets, terminal-exact targets, and unavailable tail targets in separate counts. These statuses do not change source-window identity or authorize substituting a missing target. |

The fit-bank content signature must transform state, action, and successor
together under one mapping. It may be used to report canonical duplicates or
cross-partition equivalence only after the adapter-wide legal-set and
transition-commutation checks in the counterfactual-support protocol pass.
Raw exact identities remain available as the primary audit record.

## Root-sampling and inference alignment

METHOD_SPEC_V212 §7 says to generate at least 40 independently generated
reachable situations per held-out variant and uses a crossed bootstrap that
resamples situation ids independently. The root-schedule draft instead accepts
the first 16 symmetry-unique roots from 64 candidate slots in each occupancy
band. If candidate slots are independent draws, the accepted set after
duplicate rejection is not an iid sample from the original policy-mixture
root distribution: acceptance depends on earlier accepted roots, and the
schedule itself notes that first-in-order acceptance changes the realized
policy-pair and prefix-length mix.

This is a possible mismatch between the sampling design and the resampling
assumption, not evidence that any result or interval is already invalid. The
schedule has not been run and the intended estimand has not been frozen. A
candidate resolution aligned with §7's independent-situation sample is to
define the target as an equal-weight, occupancy-stratified distribution of
first eligible nonterminal roots induced by the pinned policy mixture,
conditional on a candidate slot reaching its assigned band:

1. Preserve the 64 fixed, independently seeded candidate slots per band.
2. Accept the first 16 valid slots in schedule order, regardless of whether
   their canonical board states repeat. A slot id is the sampling unit; retain
   duplicate states as repeated draws and report their raw/canonical
   multiplicities rather than collapsing them.
3. Count terminal-before-band and other invalid slots before scoring; fail if
   fewer than 16 valid slots occur in any band. Do not top up the schedule.
4. Report the accepted policy-pair and prefix-length mix. Since validity can
   depend on policy and rollout, the target distribution is the induced
   success-conditional mixture, not the nominal uniform policy-pair mixture.

Under that proposal, independent candidate slots filtered only by their own
predeclared validity predicate yield independent accepted draws from the
success-conditional distribution. Duplicate board values do not make their
slot draws dependent. The current unique-root filter must be removed in a new
reviewed schedule version to obtain this estimand; this audit does not amend or
freeze that schedule.

The fixed allocation of 16 roots per occupancy band is a stratified design.
If the intended variant score gives the three bands equal weight, the crossed
bootstrap should resample situation-slot ids within each variant/band stratum
and combine band contrasts at fixed one-third weights, while retaining the
shared resampled model-seed multiset across variants. The current method text
resamples situation ids by variant without specifying the band strata. If a
different band weighting is intended, freeze those weights and a matching
resampling rule instead.

If the study instead targets a sample of unique reachable states, it needs an
estimator that respects the unique-state selection mechanism. If it targets a
fixed root bank, inference must be described as conditional on that bank and
root resampling must not imply generalization to a broader situation
population. In every option, the estimand, candidate-failure disposition, and
bootstrap unit must be resolved before scoring.

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
code, not an adapter-wide executable proof: `transforms()` does not assert
bijectivity, and the synthetic window test covers fixture paths rather than
every legal state/action. Keep canonical edge summaries disabled until
focused property tests check each transform's full legal-action bijection,
transition commutation, forced-pass invariance, and terminal-result
preservation on all in-scope variants. Those tests would verify code
properties only; they would not authorize canonical deduplication, data
generation, or training.

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
3. select evaluation roots only by the frozen pre-score candidate schedule and
   symmetry rule, failing closed if its minimum yield is not met; and
4. report valid, terminal-exact, and unavailable H1/H2/H4 targets separately
   without silently changing the 928-window count.

Before any executable generation work, independent review must resolve the
matrix above, including the meaning of independent development situations and
the root-schedule failure rule. The current synthetic tests establish none of
these production properties. No data feasibility, leakage-free corpus,
support, or training-readiness claim follows from this audit.
