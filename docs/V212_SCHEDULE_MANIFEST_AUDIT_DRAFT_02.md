# V2.12 schedule manifest payload binding — draft 02

**Status: structural identity contract only.** This updates the unaccepted
validator schema from draft 01 to
`caissa.v212.training-schedule.v02`; draft 01 remains as history. It does not
amend the accepted method or D03 preregistration, read or generate research
data, validate a selected-window manifest, or authorize profiling/fitting.

## Payload-bound window records

Every ordered schedule row stores a window record:

```json
{
  "id": ["connect4-gravity-6x7", "episode-id", 12],
  "payload_sha256": "<64 lowercase hexadecimal characters>"
}
```

The digest is computed over canonical JSON for the `Window` fields (adapter
identity and rules version, game, episode id, split, absolute episode outcome,
start ply, ordered exact states/players, actions, valid horizons, and terminal
targets). The paired scheduled-batch helper computes these digests after its
adapter has rechecked local transitions and target masks. Its batch payload
digest binds the seed ordinal, update index, ordered IDs, and per-window
payload digests. Each update stores that batch digest and the validator
recomputes it from the update identity and ordered window records. It requires
each ID to keep the same payload digest every time it appears across all three
epochs; the canonical schedule digest includes both batch and window payload
digests.

## Limits

The per-window digest covers only the materialized window object. It does not
prove who generated the episode, validate the full episode outside the window,
bind the audited outcome to the exact terminal state, identify the source data
file, prove train-split provenance, or hash the executing adapter/rules source.
The scheduled helper's local-edge replay and digest are not a signed replay
receipt. A future materializer must bind window hashes to source-episode and
exact-rule replay receipts, and the trainer must bind the complete manifest
digest to every scheduled update. Direct `loss_grad` calls remain possible.

The focused tests use synthetic windows, IDs, and declared masks. They prove
canonical identity changes when the payload changes and that schedule records
reject malformed or inconsistent digests; they establish no data provenance,
schedule execution, runtime identity, compute parity, or empirical result.
The ≤5% gate remains untested and unpassed.
