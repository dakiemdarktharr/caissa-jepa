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

Snapshot `snapshot-dda8b75e012e4c8ac9724584a28b8e85b0b657a50e2b4f8086153e87c8f9b903/` retains 24 events across four workflow runs, adding
verified foundation publication and the independently reviewed horizon-support
correction. No corpus generation or scientific training ran before this snapshot.

Snapshot `snapshot-08da58b12f99c82fdf10c1440fd5994e0caf384584e2b42aaf8b828447b78c7f/` contains 29 events across 6 runs, now including
one development-data run and its preparation. It retains the failed first
reference-yield gate and reference-only diagnosis. No model was fitted. Raw
data are excluded; the compact per-game audit and reconstruction hashes are public.

Snapshot `snapshot-16d0db814953c45d5b9dd4fc4df4bd90fc5a5a31c7d6a1082ef0551073d585e8/` contains 32 events across 6 runs. It adds the
verified failed-batch publication, same-host fresh-clone recovery, and reviewed
final prospective screen amendment. No second batch ran before this export.

The amendment publication preflight found reviewer Markdown trailing hard-break
whitespace. Its failure and whitespace-only normalization are preserved in
`snapshot-99c0eb8a7253a461cc664ec05785b009802040e65faa991f0d0738d4fe66fd9f/` (34 events across six runs). No experiment ran during this correction.

Snapshot `snapshot-d3324954d19c278095d0f88ade020bffe478a49e2b976de521b3a6f29ea4e75b/` contains 41 events across 8 runs. It preserves
the final failed feasibility gate, exact episode equality, and the decision
to retire the two-game mechanism study and write a descriptive feasibility
report. Neither screen fitted a model; no third screen is planned.

Report-source snapshot `snapshot-c83a5ed3f639f329d81b2f5f66156e1e38cedc2db9a1f0d01e08c28f1fc6a743/` contains 45 events
across 10 runs, including two receipt-bound per-root exports (57 and 59
rows) and 50 passing scoped regression tests. The complete report is not yet
rendered or independently reviewed at this source checkpoint.
