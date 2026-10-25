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

Within each immutable snapshot, `snapshot.json` is authoritative;
`events.csv` is an event-oriented convenience table; `checksums.json` binds
both files. The directory suffix is the SHA-256 of the canonical checksum
mapping. Do not edit a published snapshot. Corrections need a new event and
export with an explanation, keeping the old evidence.

Use the [metrics and recovery contract](../../docs/COUNTERPLAY_METRICS_AND_RECOVERY_2026-10-25.md)
and [current state](../STATE.md) before creating or using new results.
