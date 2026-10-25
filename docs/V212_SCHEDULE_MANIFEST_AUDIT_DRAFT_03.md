# V2.12 schedule manifest mask-integrity amendment — draft 03

**Status: structural validator contract only.** This draft versions the
schedule validator as `caissa.v212.training-schedule.v03`; v02 remains
unchanged history. It does not amend the accepted method or D03
preregistration, validate research data, create a schedule, or authorize a
profile or fit.

## Fail-closed mask counts

For each of horizons 1, 2, and 4, every update and arm declares four D03 mask
counts. The schedule validator now requires:

- `valid_nonterminal + terminal_masked + missing_or_truncated == 64`;
- `invalid_transition == 0`; and
- at least one valid nonterminal H4 leaf for the direct-leaf-value arm.

The first three categories partition the 64 selected windows for a well-formed
replay-audited batch. Invalid-transition count is separate because it measures
invalid transition positions within each horizon prefix; any positive value
means the batch violates D03's stop-on-invalid condition. The fixed mask-count
fields remain the same as v02, while the strengthened acceptance rules receive
a new schema version so a v02 digest cannot silently stand for this contract.

## Limits

These checks validate declarations only. They do not prove that the counts
match materialized adapter masks, that selected windows came from a
train-split episode collection, or that those episodes passed full exact-rule
replay. `validate_actual_mask_roster` on the replay-bound batch path remains
necessary; source-data provenance and trainer exclusivity remain open. The
20×87 shape and shared six-arm roster are still structural declarations, not a
frozen schedule or compute result. The ≤5% gate remains untested and unpassed.

Focused schedule, receipt-bound, adapter, and trajectory tests use synthetic
fixtures only. One exact-rule synthetic adapter batch also checks the category
partition directly against `preflight_batch` counts. These tests provide
regression evidence for this validator contract, not data, profile, training,
or superiority evidence.
