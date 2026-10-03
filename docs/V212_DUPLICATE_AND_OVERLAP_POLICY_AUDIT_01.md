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
