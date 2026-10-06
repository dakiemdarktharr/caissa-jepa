# V2.12 supervision failure matrix draft 01

Status: pre-implementation design. This matrix does not authorize request-
adapter integration, inference, a live service, training, a pilot, or OOM fault
injection. It applies to a future versioned request/runtime receipt contract;
the current synthetic collector remains unchanged.

## Acceptance invariant

The controller may return an action only after it has validated the exact
request/response binding, successful manager result, worker placement and
resource properties, complete worker-local counter evidence, exactly one
invocation-bound worker marker, the request deadline, and durable receipt
publication and required cleanup. Any failure before that point returns no
action and cannot create an accepted receipt. A failure after receipt
publication may leave a valid evidence receipt, but must still return no action
if the caller operation did not complete; it must report receipt certainty and
retain the remaining reconciliation handles.

Use these failure-state labels consistently:

- `not_attempted`: receipt publication did not begin.
- `uncertain`: publication began but durability/acknowledgment is unknown;
  inspect the exact destination before retrying.
- `persisted`: durable receipt was confirmed; never overwrite it during
  reconciliation.
- Unit and IPC state must separately say stopped/cleaned, retained, absent, or
  unknown. An error message must include the unit, invocation ID and worker
  cgroup when known, receipt path/state, and IPC directory/state. Do not include
  request bodies, actions, or token bytes.

## Required failure matrix

| ID | Injected condition | Required result | Receipt/action | Evidence retained | Minimum automated assertion |
| --- | --- | --- | --- | --- | --- |
| REQ-01 | Request bytes, nonce/digest, release token/FIFO message, source manifest, or runtime binding is malformed, altered, or mismatched | Fail before compute import/callback; never accept a worker response | No action or receipt | After dispatch, retain unit and IPC workspace plus known invocation/cgroup identifiers; report binding mismatch category | Inject each binding failure at its validation boundary; assert no compute callback/import, response read/acceptance, receipt, stop, or workspace cleanup |
| GATE-01 | Effective service property, caller/worker cgroup separation, worker `/proc` placement, or live cgroup memory file mismatches | Do not release compute; reject the active service as unverified | No action or receipt | Retain unit and IPC workspace, active unit snapshot, and identifiers needed for reconciliation | Inject each gate mismatch immediately before release; assert no release write, compute import/callback, response, receipt, stop, or workspace cleanup |
| MGR-01 | Manager query fails after dispatch or returns an incomplete snapshot | Fail closed; do not infer exit or success from worker response | No action; `not_attempted` unless publication already began | Unit name, invocation ID/cgroup if acquired, IPC path; unit state marked unknown | No response acceptance, receipt write, stop, or IPC cleanup; error carries reconciliation identifiers available at failure point |
| MGR-02 | Manager reports non-success result or nonzero main status | Treat as failed execution, even if response file exists | No action or accepted receipt | Exited manager snapshot, unit and IPC handles | Response is not read/accepted; no receipt/stop/cleanup |
| MGR-03 | Service never becomes active, or `not-found`/start race persists to caller deadline | Never release compute; distinguish dispatch/start timeout | No action; `not_attempted` | Unit identity and IPC workspace; unit state unknown until reconciled | No release write, response read, receipt, stop, or workspace removal after dispatch |
| RESP-01 | After successful manager exit, response is missing, malformed, oversized, truncated, non-canonical, or mismatches schema/nonce/request digest/byte length | Reject the result even if the process exited successfully | No action or accepted receipt; `not_attempted` | Preserve exited unit evidence, invocation/cgroup, response/IPC workspace and receipt destination for reconciliation | Hash exact bounded bytes before parsing; inject each framing/binding failure and assert no action, receipt, stop, or IPC cleanup |
| JRN-01 | Journal command/query fails, output is partial/oversized/malformed, or contains no worker marker | Required evidence unavailable | No action; `not_attempted` | Unit, invocation/cgroup, receipt destination, IPC workspace | No receipt/stop/cleanup; error identifies evidence failure and reconciliation handles |
| JRN-02 | More than one worker marker, duplicate marker, or marker unit/invocation/cgroup/boot/time mismatch | Reject ambiguous or foreign evidence; do not select one record heuristically | No action; `not_attempted` | Raw journal remains in system journal; local handles retained | Exact-one rule enforced; no receipt/action; include marker count or mismatch category without copying raw request data |
| CNT-01 | Either in-run `memory.events.local` sample disappears, cannot be read, or is malformed | Treat the pair as incomplete, not as zero events | No action; `not_attempted` | Unit, invocation/cgroup, IPC and receipt destination; capture whether the first or second sample failed | Missing either sample blocks amended-schema receipt; no coercion to zero, receipt, or cleanup |
| CNT-02 | Counter snapshot has wrong source/schema/cgroup/boot/window, incomplete keys, malformed/Boolean/negative/non-integer values, or counters move backward | Reject as unbound or inconsistent | No action; `not_attempted` | Same as CNT-01 | No receipt/action; counter source and failing identity dimension are reported |
| CLK-01 | Caller deadline expires during active wait, exit wait, evidence capture, or before durable receipt | Late worker output is never a valid action | No action; `not_attempted` or `uncertain` if publication began | Keep unit/workspace until state is reconciled; record receipt destination/state | Controlled clock covers each boundary; no late response acceptance, no unsafe cleanup |
| CLK-02 | Deadline expires after durable receipt but during stop/cleanup | The prior receipt stays immutable; operation still returns failure/no action | `persisted`, no action | Preserve receipt; report exact unit and IPC state, including `unknown` if the operation result is ambiguous | No receipt rewrite/delete; retries reconcile instead of replaying stop or receipt publication blindly |
| REC-01 | Kill/reap or stop command errors, or post-command unit query fails | Do not claim stopped/cleaned from command success alone | No action; receipt state reflects actual publication phase | Unit state `unknown` if not verified; IPC path retained unless verified cleaned | Error retains identifiers and recovery handle; no statement of cleanup success without postcondition |
| REC-02 | IPC cleanup detects path/device/inode substitution or fails partway | Stop processing; preserve evidence and identify path state | No action; `persisted` only if durable receipt was confirmed | Receipt plus substituted/remaining IPC path and unit state | No recursive delete of substituted path; no retry until inspected |
| RCP-01 | Receipt write/rename/fsync fails before publication or acknowledgment | Do not claim receipt absent if publication may have happened | No action; `not_attempted` or `uncertain` | Destination path, temporary/final identity where safe, unit and IPC handles | Failure injection distinguishes pre-publication from post-publication uncertainty; never overwrite on retry |
| RCP-02 | Receipt exists but embedded digest/schema/links do not validate | Treat the artifact as unaccepted/corrupt | No action; do not call it a valid receipt | Preserve the bytes for investigation and retain lifecycle handles | Independent recomputation fails closed; no automatic rewrite or cleanup |
| INT-01 | Ctrl-C before dispatch, while armed/releasing, after dispatch, or after receipt publication | Preserve phase-specific state; never turn interruption into success | No action; accurate `not_attempted`/`uncertain`/`persisted` label | Before dispatch, clean private workspace only if identity checks succeed; after dispatch preserve unit/workspace; after receipt preserve immutable receipt | Tests inject interruption at each boundary and assert phase-appropriate evidence and handles |

Every failure case must assert both (a) that no successful action/result escapes
and (b) that no required evidence is silently deleted. A success-path receipt
test is not a substitute for these paired assertions.

## Current implementation evidence and limits

The armed synthetic service and collector tests already exercise some rows:
non-success manager result, missing/duplicate/mismatched worker marker,
response deadline while active, start-state query/race, receipt publication and
durability uncertainty, stop/cleanup failure, and Ctrl-C at several phases.
At the current consumer seam, an empty journal-marker collection is also
injected and checked for no receipt attempt, unit stop, or workspace cleanup;
duplicate and foreign-invocation records are checked at the same seam.
The v01 smoke now checks the caller deadline immediately after journal capture;
a controlled expiry fixture proves receipt assembly, persistence, stop, and
workspace cleanup are skipped at that boundary.
It also checks immediately after the validated post-exit manager snapshot and
before reading response bytes; the corresponding controlled expiry fixture
proves response and journal reads plus receipt persistence and cleanup are
skipped.
The current suite injects failures at both first and second local counter
reads and removes a real temporary `memory.events.local` file between reader
calls to exercise disappearance during the mocked controller flow. It also
injects invalid counter records for source, schema, cgroup, boot,
time order/window, Boolean values, and rollback; all reject during receipt
assembly without persistence, stop, or workspace cleanup. It also injects a
stop-command timeout after durable receipt and Ctrl-C at stop after durable
receipt. The timeout is a mocked command result rather than a
controlled-clock test of the real stop command; none of these tests establish
live failure recovery. See the case-by-case map in
`docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`.

The v02 receipt assembler validates counter identity, order, required counter
keys, and nonnegative deltas when snapshots are supplied. It permits both
counter snapshots to be omitted. The isolated v03 draft boundary now requires
both samples, rejects counter rollback, Boolean, negative, non-integer, and
missing-key values, reports its own source digest and the delegated v02 source
digest, and leaves v02 behavior unchanged. This does not yet integrate an
accepted request/runtime path or prove the complete end-to-end contract; the
collector's capture of both samples is not itself acceptance evidence.

Before any request-adapter integration proposal, convert every row into a
versioned test case that names the exact injection seam, expected receipt
state, action disposition, and retained handles. Run those tests only in the
mocked harness until separate stage gates authorize later operations. OOM
fault injection remains separately gated and is deliberately absent from this
matrix. The proposed case-by-case injection and coverage mapping is tracked in
`docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`; that plan also remains
subject to independent review.
