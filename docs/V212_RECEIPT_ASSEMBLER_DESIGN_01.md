# V2.12 invocation-bound supervision receipt assembler v02

**Status: synthetic evidence assembler only.** This module does not launch a
systemd service, sample a live cgroup, follow the journal, call the request
adapter, or certify supervision readiness. Its 26 tests use synthetic records
and temporary files only. No OOM fault test or inference request was run.

## Evidence contract

`two_player/v212_supervision_receipt_v02.py` consumes a caller request start
and boot ID, an active systemd snapshot, a post-exit manager snapshot, a
bounded batch of journal JSON records, and optionally two typed
`memory.events.local` samples. Both systemd snapshots carry a schema ID, exact
unit name, invocation ID, boot ID, and monotonic capture time. The active
snapshot supplies the exact `ControlGroup`; its final path component must be
the requested unit. The manager snapshot must bind to the same unit,
invocation, and boot and show an inactive exited/failed service.

Kernel OOM evidence is attributable only when the record has kernel transport,
`CONSTRAINT_MEMCG`, matching `oom_memcg` and `task_memcg`, the same boot ID,
and a monotonic timestamp strictly after the active snapshot and no later than
the manager snapshot. Unit markers and counter samples use that same interval.
Counter samples must declare the `memory.events.local` source/schema, exact
worker cgroup, matching boot, complete nonnegative OOM counters, and strictly
increasing capture times. A positive `max` delta alone never counts as an OOM
kill. Missing counters remain missing; malformed, stale, foreign-cgroup, or
backwards evidence fails closed.

The receipt stores bounded normalized kernel fields, cursor, timestamp, boot,
and a digest of the raw message, while excluding raw journal text. The cursor
must remain retrievable if a later reviewer needs to verify how fields were
parsed. The receipt records the assembler version and source SHA-256. JSON is
written to a mode-0600 temporary file, fsynced, atomically replaced, and the
parent directory is fsynced.

## Verification and limits

The synthetic suite covers unit/invocation/ControlGroup binding, request boot
binding, active-to-exit time windows, kernel event normalization, counter
source/schema/cgroup/time provenance, fail-closed classifications, bounded
input, and durable-write failures. A static independent review found no
remaining blocking attribution or malformed-input issue after adding strict
post-active evidence windows and typed journal fields.

This contract does not verify that a collector queried the stated unit,
captured counters while the cgroup existed, retained journal cursors, or
persisted the receipt before cleanup. It does not yet integrate with
`v212_request_adapter_v02.py`, whose current same-cgroup worker path does not
provide caller isolation or worker-specific OOM counters. Do not use the
assembler to claim a live same-invocation OOM result. External transient
service integration and its failure paths require separate implementation and
review. Any new OOM fault injection still requires separate explicit user
authorization under the project supervision gate.
