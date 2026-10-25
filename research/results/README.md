# Reviewed research evidence

Only small, reviewed, phase-labelled analysis exports belong here. Raw data,
weights, the full local event database and logs remain excluded from Git.

The first `snapshot-30f1f437285953b9d39dbe464b5444bfc61a254cca8dea361a98aec92b987e7b/`
contains five **workflow** events from 25 October 2026: search inventory
counts, infrastructure tests, GitHub recovery tests, verified source
publication, and usage availability. There are no scientific training results.

The later `snapshot-318cd4ed7adf998ec6050b955569347196edcc45dd91abd40ce6ccff5b774fdd/`
contains all seven events, adding the CSV publication failure and the passing
15-test regression verification. These are cumulative snapshots of the same
run: deduplicate by run ID and event key; never count both as separate samples.

The setup `snapshot-7d9d08c983796b8815aeb1e773f8641592a0945e8595f81e72676f4d26b51a68/`
has 10 unique events across two workflow runs. It adds the approved startup
configuration, a failed test-fixture attempt and the passing 17-test README
publication-gate verification. No subagents or scientific experiments were
launched. This snapshot also includes the previous seven events unchanged.

Within each immutable snapshot, `snapshot.json` is authoritative;
`events.csv` is an event-oriented convenience table; `checksums.json` binds
both files. The directory suffix is the SHA-256 of the canonical checksum
mapping. Do not edit a published snapshot. Corrections need a new event and
export with an explanation, keeping the old evidence.

Use the [metrics and recovery contract](../../docs/COUNTERPLAY_METRICS_AND_RECOVERY_2026-10-25.md)
and [current state](../STATE.md) before creating or using new results.

The CP-01 Review 1 milestone snapshot
`snapshot-455f0ea8227860b722846c568fc523803a5db4eb546bf473b39faa1323bd44d9/`
contains 13 unique events across three workflow runs. It adds the current
17-test bootstrap verification, explicit unavailable usage/attestation, and
the accepted targeted Review 1 closure. No scientific experiment ran.

Publication preflight stopped before committing because the reviewer used a
Markdown trailing hard break. The [receipt](../../docs/validation/CP01_PUBLICATION_PREFLIGHT_2026-10-25.json) preserves that failure
and a one-line whitespace-only normalization. Snapshot `snapshot-93f01ce1daaf4409e6d4dffd1981a707158947d59832b98226d02d5b1cb7d75d/` contains
15 events across three workflow runs and retains the original 13 events.

The foundation snapshot `snapshot-aac52d91312e03b6911f8d2f4151d7c102c1a62fad3414476764e1f94e19a3c4/`
contains 22 events across 4 workflow runs. It adds the covariance-gradient
failing baseline/repair, data-source and producer-fixture failures, corrected
synthetic verification and the prior verified GitHub publication. No actual
corpus generation, training or matches ran in this milestone.
