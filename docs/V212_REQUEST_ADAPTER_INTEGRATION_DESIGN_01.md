# V2.12 request-adapter integration design 01

## Implementation progress: armed no-inference service smoke (2026-10-04)

Added `two_player/v212_armed_service_smoke_v01.py`, a separate synthetic
controller/worker composition around the release-FIFO protocol. The worker
hashes the exact bootstrap and three helper files before compiling those
verified bytes in memory, waits until the caller verifies active systemd
properties and worker/caller cgroup placement, validates the one-shot release
token and deadline, then emits only a tiny synthetic response and
invocation-bound journal marker. The caller starts its deadline before
receipt-destination validation and source/request preflight, rechecks worker
and host evidence source manifests, hashes the request with directory-relative
no-follow opens and identity checks, and persists the assembled receipt before
stopping the unit and removing the private IPC workspace. Pre-dispatch cleanup
failures and post-dispatch failures retain/report reconciliation state.

Independent review found and the follow-up resolved three receipt-boundary
gaps: deadline start now precedes destination validation; the harness itself
and evidence dependencies are in a captured/rechecked host-source manifest;
request hashing checks the original directory/file identities and revalidates
the bytes before receipt assembly. Follow-up tests now cover invalid worker
response, missing marker, receipt publication and durability-acknowledgement
failures, unit-stop failure, IPC-cleanup failure, active-state query failure,
non-success manager result, caller deadline expiry while the service stays
active, duplicate-key response bytes, and Ctrl-C before dispatch/during
release/after dispatch; all preserve the appropriate receipt uncertainty and
reconciliation handles. The focused orchestration and supervision suites pass
116/116 with `unittest`; the whitespace check and AST parsing pass.
Independent review confirmed the controlled clocks exercise the actual
active-wait and exit-wait deadline branches, including a start-race snapshot
reporting `LoadState=not-found`, and found no remaining P1/P2 issue.
Post-dispatch error text now carries validated invocation/cgroup identifiers
alongside the unit and IPC path for reconciliation; review confirmed it does
not expose request or release-token contents.
One bounded live normal-exit systemd v262 run then verified armed release,
receipt-before-cleanup, matching embedded receipt digest, mode `0600`, and
`LoadState=not-found` after cleanup. Receipt SHA-256:
`ee1d679c27f5a2c2b009045582a5d18eb8668f396fa33fb82e7203185a26a3a0`.

This validates one synthetic normal-exit path only. Mock coverage and this
single live run do not establish timeout/interruption recovery, OOM attribution,
repeatability, or real request-adapter behavior. The manifest records source
file stability; it does not independently attest host bytecode already loaded
before the run and is not the complete model/runtime fingerprint required for
adapter integration. No adapter, inference, OOM operation, training, project
data, score, or outcome ran. The current request adapter remains same-cgroup
and is not wired to this harness. Next: review remaining manager-result,
service-start race, and deadline/interruption recovery contracts; keep staged
external-supervision and separate OOM authorization gates closed.

The next research task is an architecture audit of source/runtime fingerprint
coverage and the remaining manager/journal/counter failure map before
request-adapter integration. The live normal-exit smoke does not
substitute for those failures, and the separately gated OOM stage remains
closed pending explicit authorization.

## Request-byte release binding candidate v02 (2026-10-06)

Added versioned `two_player/v212_release_token_v02.py` and
`two_player/v212_armed_protocol_v02.py` without changing the v01 modules. The
v02 worker API takes the exact bounded request byte string, rejects malformed,
duplicate-key, non-object, non-finite, and oversized JSON, and computes its
SHA-256 before waiting on the release FIFO. The v02 release token includes
that digest and verifies it against the worker's bytes before the callback
can run. A same-nonce request changed only by appended whitespace is rejected,
so the binding covers bytes rather than parsed-object equivalence.

Five focused protocol tests pass, including matching-byte release,
same-nonce/different-byte rejection before callback, tampered release digest,
and malformed/oversized request rejection before the FIFO wait. The separate
v02 bootstrap now reads bounded raw stdin, enforces canonical request bytes,
and passes the exact bytes to that API. This remains a synthetic candidate:
the v01 systemd smoke and current request adapter do not call v02, and no live
service or request was run. It does not close the runtime fingerprint or
remaining manager/journal/counter failure map, receive independent review, or
open adapter/pilot/OOM gates.

### Canonical raw-request bootstrap enforcement (2026-10-06)

The separate v02 bootstrap now re-encodes the parsed request using the pinned
sorted-key, compact, UTF-8 JSON encoding and compares those bytes with bounded
stdin before opening project helper files. Subprocess fixtures reject trailing
whitespace, a leading newline, reordered keys, and an exact-cap non-canonical
request; the exact canonical source-verified release-to-response fixture still
passes. The focused bootstrap/protocol/release-token/IPC/service-smoke/receipt
regression group passes 139/139. This remains offline candidate evidence: v02
is not wired into the current systemd smoke or adapter, and caller deadline,
executed runtime identity, integrated failure mapping, independent review, and
all live-service gates remain open. No service, request, inference, OOM,
training, score, or match ran.

### Post-exit manager identity gate before response read (2026-10-06)

The existing v01 no-inference smoke now compares the post-exit manager
snapshot's unit, invocation ID, boot ID, and any still-present cgroup path
against the active worker snapshot before it reads the response file. A
table-driven mocked orchestration regression injects foreign invocation and
cgroup values plus missing/malformed invocation, `Result`, and
`ExecMainStatus`; each path rejects before response read or receipt publication
and retains the service workspace without stopping the unit. The focused
armed-smoke/collector/live-evidence/receipt group passes 89/89. This closes
only those v01 mocked pre-response cases: the candidate v02 controller is not
integrated, live manager failures and boot-source loss remain unverified, and
the full failure matrix, runtime attestation, independent review, and all
service/pilot gates remain open. No live service or model work ran.

### Exact bounded response-byte reader (2026-10-06)

The IPC layer now exposes `read_response_bytes`, which performs the existing
private-directory, inode, owner, link-count, race, and byte-cap checks before
returning the exact bytes read. `parse_response_bytes` applies the legacy
strict UTF-8/object/duplicate-key/non-finite parser to that same in-memory
buffer; `read_response` delegates through these APIs and retains its existing
return shape. A regression demonstrates that hashing original whitespace-
formatted wire bytes differs from hashing a re-serialized object. The focused
IPC/schema/smoke/receipt/bootstrap regression group passes 137/137. This only
enables an exact-byte caller path: no v02 response schema validation or
response digest/length receipt binding is implemented, v02 remains unwired,
and no service/request/model operation ran.

## Implementation progress: mocked collector lifecycle boundaries (2026-10-04)

Added nine orchestration tests in `tests/test_v212_supervision_collector_v01.py`
with the systemd command/snapshot, cgroup, journal, clock, IPC lifecycle, and
failure boundaries mocked. They cover successful receipt-before-stop/cleanup
ordering; invalid worker response; service dispatch failure; non-success
manager result; missing worker-local counter or journal marker; receipt write
failure; an ambiguous post-publication durability acknowledgement; unit-stop
failure; and IPC cleanup failure. The post-publication case invokes the real
atomic receipt writer before raising a simulated acknowledgement error, and
verifies the visible receipt and workspace remain while the service is not
stopped. A successful run separately verifies receipt persistence completion
precedes the stop command, which precedes workspace cleanup.

The configured independent reviewer found no remaining fixture issue. The
focused collector, live-evidence, receipt, armed-protocol, release-token, and
IPC suites pass 92/92 under `unittest`. The environment has no `pytest`
installation. This is mocked orchestration coverage only; it provides no new
evidence about live systemd, cgroup teardown, journal timing, or receipt
durability on the host. No service, adapter, inference, OOM, data, score, or
outcome ran. The next step is independent review of the complete architecture
and remaining failure contracts before any live service step. OOM still needs
separate explicit authorization.

A broader architecture review identified that the response fixture was
available before the worker's exited snapshot and that missing-counter/journal
tests did not prove reconciliation handles were retained. The fixture now
publishes the staged response only with the exited snapshot and asserts the
response is read afterward; evidence-capture failures assert no stop/cleanup
and a retained workspace. Follow-up review found no remaining issue in these
changes. This closes those mock-coverage gaps only and does not add live service
evidence.

After this review, one second no-inference normal-exit run of the existing
collector completed on systemd 262. It verified the invocation-bound receipt
before cleanup and left the transient unit `not-found`; details and the
receipt digest are in `docs/V212_SUPERVISION_COLLECTOR_V01.md`. This does not
exercise the armed-release protocol in a live service or connect the request
adapter. OOM, inference, and request-adapter gates remain closed. Next, finish
the armed-worker service integration and its failure contract before any
request-adapter use; separate authorization remains required for OOM testing.

## Implementation progress: private release-FIFO primitive (2026-10-04)

`two_player/v212_worker_ipc.py` now optionally creates a mode-0600 release FIFO
inside the existing mode-0700 workspace. It records and checks the FIFO's
device/inode/owner/type/mode/link identity during nonblocking writer open,
checks the opened descriptor before a single-use bounded write (maximum 4096
bytes), closes/consumes the writer once a one-shot send is accepted (including
later payload/write failure), and refuses cleanup if the path was substituted.
Calls rejected before consuming the one-shot state leave descriptor ownership
with the caller. The readiness regression uses a blocking
`O_RDONLY` FIFO open and confirms its subsequent read blocks until release. The
default workspace path remains unchanged when the FIFO option is off. The
focused IPC suite passes 21/21 tests, including sequential and concurrent
duplicate-open rejection and duplicate-write rejection.

## Implementation progress: synthetic worker release verifier (2026-10-04)

Added `two_player/v212_release_token_v01.py`. Its worker-side read blocks on the
identity-checked FIFO barrier, consumes a single bounded payload through EOF,
and rejects empty, oversized, substituted, or malformed input. The strict
sorted-JSON schema rejects duplicate/extra fields and verifies the SHA-256
digest, request nonce, service unit, invocation ID, boot ID, exact cgroup path,
expected source-manifest digest, and live `memory.max`, `memory.high`, and
`memory.swap.max` values before returning. Fixture-backed tests cover binding
mismatches, digest/limit mismatch, path traversal, missing cgroup evidence,
blocking-open/read-to-EOF behavior, empty EOF, FIFO substitution, and the
4097-byte boundary. The combined IPC/token suites pass 30/30 tests.

This helper has no internal timeout: a live controller must enforce the
service/caller deadline and terminate a worker whose release FIFO stays open
without progress. The helper is not wired to model imports or a service. No
systemd property verifier, receipt binding, service launch, failure-path service
harness, adapter call, inference, or OOM behavior has been implemented or
tested. These synthetic helpers are not supervision or pilot evidence. Next is
the mocked no-inference service/controller failure protocol, followed by
independent review before any live service smoke.

## Implementation progress: mocked armed controller/worker protocol (2026-10-04)

Added `two_player/v212_armed_protocol_v01.py`. The controller rejects any
snapshot whose effective properties do not exactly match the v01 profile
(128/96 MiB memory, swap 0, 64 KiB file limit, 8-second runtime, no restart,
`OOMPolicy=kill`, retained exit result) or whose manager memory values disagree
with the live cgroup files. It sends one canonical token only after the worker
reaches the FIFO read barrier and before the absolute monotonic deadline. That
deadline is now bound into the token; after validating token, invocation,
cgroup, source fingerprint, and live limits, the worker checks it again
immediately before the synthetic callback. Tests prove invalid policy, stale
nonce, pre-release timeout, and expiry between release and callback never invoke
the callback. The combined IPC, release-token, and armed-protocol suites pass
36/36; independent static review found no remaining issue in this mock scope.

This is not the complete supervision failure protocol: systemd snapshot
provenance, actual service termination/kill/reap on deadline, journal/counter
capture, receipt durability, and cleanup/recovery remain unimplemented here.
No service, adapter, inference, OOM, or project outcome was run. Next, extend
the mocked supervisor boundaries for lifecycle and receipt failure paths, then
obtain review of the complete architecture before any live normal-exit service
smoke.

Updated: 2026-10-04. **Status: design plus partial, synthetic IPC/token helper implementation; no service integration and no authorization to run inference/OOM.**

## Decision

The current normal-exit collector is a useful evidence component, but it is not sufficient to wrap the existing request adapter by changing only the `systemd-run` command. The adapter's current request path still supervises a same-cgroup subprocess and measures the caller cgroup. Reuse of that path inside a transient service would either keep the worker in the caller's resource boundary or cause the caller to inspect the wrong cgroup. The request path needs an explicit caller/worker split before no-outcome integration.

This note defines that split and the evidence contract for a future implementation. It does not change V2.12 or its gates. Per the external-supervision sequence, no-outcome request integration remains downstream of a separately authorized and reviewed OOM stage; this design does not grant that authorization.

## Current code paths and mismatch

`two_player/v212_request_adapter_v02.py` currently runs `_run_move_request_body`, reads the current process cgroup, and launches `two_player.v212_request_adapter_v01 --worker` through `_run_worker_process`. That helper sends JSON through a pipe and kills/reaps a process group on timeout. The child inherits the caller's cgroup. The caller samples its own hierarchical `memory.events` before and after the child. This path does not use the new file-backed IPC, transient service, service invocation ID, worker-specific `memory.events.local`, journal marker, or pre-cleanup receipt.

The existing module also contains a worker entry point, but the caller payload is assembled around the same-cgroup path: it carries the caller cgroup's expected memory limit/path and the deadlines are based on an already-started request. Simply invoking that worker in the current collector would therefore fail closed or leave the evidence bound to the wrong cgroup. The current root worker response is plain JSON without request schema/version or nonce binding. These are interface gaps, not evidence of a JEPA method issue.

## Proposed separation

Keep a caller-side request controller separate from a service-side compute worker. The controller owns systemd, deadlines, IPC files, journal/cgroup capture, receipt persistence, and cleanup. The service worker owns only parsing one versioned request, constructing the specified synthetic root and random-initialized model, running the existing bounded search core, and writing one bounded versioned response. The worker never writes receipts, accesses training/outcome labels, updates parameters, or persists scores.

The controller should pass one strict request object through `StandardInput=file:<request>` and receive one strict response through `StandardOutput=truncate:<response>`. Both objects need a schema/version and unpredictable request nonce. The response must echo the nonce and identify the worker protocol; the caller must validate duplicate keys, sizes, finite values, required fields, request binding, action legality against the caller's original root, and counter types before returning an action. The action remains transient and is excluded from any pilot receipt. No arbitrary paths or commands should be accepted from the payload.

The caller can validate the requested unit configuration before launch, but effective properties and the actual `ControlGroup` only exist after systemd creates the service. Therefore the worker must start in a **no-compute armed state**. The concrete candidate is a private, identity-checked release FIFO in the IPC workspace: the worker parses the bounded request, opens the FIFO for reading, then blocks before model initialization/search. The caller retries a nonblocking FIFO writer open under the shared deadline; a connected reader confirms the reviewed worker reached the barrier. Both sides check FIFO type, owner, mode, and device/inode immediately around their opens. EOF before any release bytes, partial/invalid JSON, oversized input, or failed digest is an integrity failure with no computation. The caller then verifies the active unit's effective `MemoryMax`, `MemoryHigh`, swap, runtime, restart, OOM policy, exact `ControlGroup`, and `/proc/<MainPID>/cgroup` placement, plus the live cgroup memory files. Only after every check passes may the caller send a bounded release message and close the FIFO. The FIFO coordinates trusted same-UID processes; it is not an adversarial security boundary. Linux FIFO open behavior is documented in [`fifo(7)`](https://man7.org/linux/man-pages/man7/fifo.7.html) and [`open(2)`](https://man7.org/linux/man-pages/man2/open.2.html). The synthetic armed service harness now exercises this ordering; the production request adapter does not yet use it.

The release payload must bind the request nonce, exact service unit, active invocation ID, boot ID, exact `ControlGroup`, the captured effective unit properties and live `memory.max`, `memory.high`, and `memory.swap.max` values, source-manifest digest, and capture time. Define a canonical sorted JSON encoding of these fields and include its SHA-256 digest. Before model initialization, the worker consumes the message once, recomputes the digest, compares the nonce with the request, invocation ID with its systemd-provided `INVOCATION_ID`, cgroup with `/proc/self/cgroup`, and each memory value with its live cgroup files. A second, stale, foreign-invocation, digest-mismatched, or limit-mismatched message fails closed. If this handshake cannot be implemented and tested without races, the request must fail before computation; a post-hoc property check alone is insufficient to establish the pre-compute resource gate. The earlier collector had no armed/release handshake; the separate synthetic harness now verifies it, but this does not satisfy the request-adapter integration requirement.

The worker must verify its actual cgroup path and memory limit against the controller's captured service snapshot; it must not infer them from caller-side constants. The caller and worker must be in distinct cgroups. Capture `memory.events.local` from the worker cgroup while it exists, not from the caller's cgroup. Bind the service journal marker to exact unit, invocation ID, worker cgroup, boot ID, and monotonic window. Capture manager exit/result fields, response validation, and counter samples into one receipt before stop/unload and IPC cleanup.

## Request clock and outcomes

Start the caller-observed monotonic clock before request construction. It covers preflight, payload encoding, transient-service dispatch/start, worker import/model initialization, search, worker exit, response read/validation, evidence assembly, receipt durability, and cleanup. Keep planner and service runtime caps distinct from the caller response deadline. A late result is never returned as a move. Atomic file/directory fsync cannot be safely interrupted, so timeout reporting may be delayed if the filesystem blocks; the call must still report deadline failure and preserve enough evidence to reconcile a late receipt or cleanup state.

Keep these outcomes distinct: unsupported/missing systemd property; start-job failure; caller deadline; service runtime expiry; worker OOM; successful exit with missing/malformed/late/illegal response; receipt publication/durability uncertainty; missing worker counters; unit/journal invocation mismatch; and cleanup failure. No fallback action may hide timeout, OOM, invalid response, or missing evidence. A fallback allowed by the frozen planner is only a bounded-search fallback returned by a successfully validated worker response.

## Required implementation tests and gates

Before connecting this controller to the real adapter, add tests that exercise the target service-worker protocol with fixture roots and mocked process/service boundaries. Cover no-duplicate/versioned schema parsing, nonce mismatch, oversized/partial/duplicate-key JSON, short response writes and the `LimitFSIZE` boundary, illegal actions, incorrect cgroup identity/limits, start-job races, manager result retention, missing/duplicate/mismatched journal markers, counter disappearance, deadline/kill/reap outcomes, restart prevention, receipt write/rename/fsync failures, cleanup substitution, and Ctrl-C recovery handles. Tests must prove that no failure can return an action as a successful response or silently delete ambiguous evidence.

Use `docs/V212_SUPERVISION_FAILURE_MATRIX_DRAFT_01.md` to make these tests
phase-aware and assert receipt certainty, action disposition, and retained
reconciliation handles together. In the amended request/runtime receipt
schema, both worker-local counter samples are mandatory: the legacy receipt
assembler currently allows both to be omitted, so an integration wrapper must
reject that state until a separately reviewed schema version enforces it.

Then obtain independent review of the complete architecture, service properties, source fingerprints, response contract, failure mapping, tests, and no-outcome evidence. The next live step remains governed by `docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`: stage 3 is a disposable OOM fault test requiring separate explicit user authorization; stage 4 request integration follows only after earlier stages and reviews pass. Until then, do not call the request adapter, run inference, generate game outcomes, or claim the pilot gate is open.

## Reproducibility contract

Before live integration, freeze hashes for the controller, worker bootstrap/entrypoint, search/model implementation, games/rules, IPC, evidence adapter, receipt assembler, Python runtime, and NumPy/runtime versions. The bootstrap must compare its expected source manifest before importing model/search modules; include that manifest in the readiness/release exchange and final response. The controller rechecks the source bundle after worker exit and binds the manifest, request/config hash, systemd version, effective resource properties, and receipt schema into the receipt. Any mismatch before release blocks computation; any post-run mismatch invalidates the response and receipt. The worker must execute the exact bytes that were verified: use a genuinely immutable content-addressed artifact for the run or a loader that compiles/imports the verified in-memory bytes. A read-only bind mount alone is not sufficient if another host path can still mutate the same backing files; systemd documents `BindReadOnlyPaths=` as a read-only bind mount in the unit's filesystem view ([systemd.exec v262](https://github.com/systemd/systemd/blob/v262/man/systemd.exec.xml)). Test that a mutation between preflight and import cannot change executed code or produce an accepted response. The current collector receipt hashes the collector and assembler but is not yet the complete request-adapter execution fingerprint.

## Evidence reviewed

- `two_player/v212_request_adapter_v02.py` and `two_player/v212_request_adapter_v01.py`: current same-cgroup pipe worker and caller-side event sampling.
- `two_player/v212_worker_ipc.py`: bounded file-backed request/response primitive.
- `two_player/v212_supervision_collector_v01.py`: one synthetic normal-exit service with invocation-bound receipt-before-cleanup.
- `docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`: staged validation, required failure cases, and separate OOM authorization.
- `docs/V212_RECEIPT_ASSEMBLER_DESIGN_01.md`: normalized evidence/receipt contract and limits.
- Official systemd v262 documentation linked from `docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`: transient-service and file-backed stdio constraints.
- Official systemd v262 `systemd.exec`: `BindReadOnlyPaths=` creates a unit-specific read-only bind view; that setting does not by itself freeze the host-side source bytes.

No request-adapter code, inference, training, project data, game score, or outcome was run or accessed for this design review. The request-adapter test modules remain unverified in the installed Python runtimes because NumPy is unavailable.

## Request-byte v02 raw-stdin helper (2026-10-06)

`two_player/v212_armed_protocol_v02.py` now provides
`read_bounded_request_bytes(fd=0)`, which reads until EOF while retaining at
most the existing 65,536-byte IPC bound plus one probe byte. The companion
`run_synthetic_armed_worker_from_stdin` passes that exact byte string to the
v02 digest/parser/release helper. Tests cover short EOF, a configured exact
limit, limit-plus-one, invalid reader bounds, and invalid UTF-8 rejection
before waiting on the release FIFO or invoking a callback. A truncated JSON
stream ending at EOF is also rejected before release. The focused v02 suite
passes 10/10; compileall and `git diff --check` pass.

This is still an isolated helper, not a worker entrypoint, source-verified
bootstrap, systemd smoke, or request adapter. It does not select the proposed
811-byte request-schema cap; it uses the existing IPC hard limit until a
versioned request schema is accepted. A stream that never reaches EOF relies
on the outer caller deadline, which this helper does not enforce. Duplicate
keys and other parse errors are rejected by the existing v02 parser, but a
complete stream-to-controller failure matrix and executed-runtime fingerprint
remain open. No service, request, inference, OOM operation, training, result,
or game outcome ran, and no gate changed.

## Candidate v02 raw-stdin worker bootstrap (2026-10-06)

Added `two_player/v212_armed_worker_bootstrap_v02.py` as a separate bootstrap
source builder, preserving the v01 smoke implementation. Its generated worker
reads stdin with a 65,536-byte cap plus one probe byte, rejects malformed
UTF-8/JSON and duplicate keys before opening the project source tree, verifies
the exact bootstrap and five helper-file hashes, compiles those verified
helper bytes in dependency order, then passes the unchanged raw request bytes
to `v212_armed_protocol_v02.run_synthetic_armed_worker` before its synthetic
no-inference callback. The request envelope is separately versioned as a
bootstrap fixture; it does not freeze the proposed application request schema
or its 811-byte limit.

Sixteen subprocess/static tests verify source compilation/order, manifest
coverage, rejection of empty/one-byte/truncated input, acceptance of the exact
hard cap up to the bootstrap fingerprint gate, and early rejection of
cap-plus-one, invalid UTF-8, duplicate keys, wrong schema, extra request
fields, and non-finite JSON values. Manifest negatives cover unexpected
helper paths, a bad manifest digest, changed helper bytes, oversized helper
files, and a symlink outside the project root. A helper exactly at the 256 KiB
source bound reaches post-compilation workspace setup; cap-plus-one is rejected.
Helper source is opened via
root/package directory descriptors with `O_NOFOLLOW`; helper files open
nonblocking, must be regular, and are read through the opened descriptor under
a 256 KiB per-file bound before digest validation. An
offline subprocess fixture also completed a
valid source-verified bootstrap, released it with a request-byte-bound token
through the real FIFO helpers, and received the no-inference response; an
altered raw request was rejected before response. The fixture supplied fake
cgroup files and suppressed the system journal marker; it did not create a
systemd unit. The combined bootstrap, armed-protocol, release-token, IPC,
service-smoke mock, and receipt regression suites now pass 121/121; Python
bytecode compilation and `git diff --check` pass. This does not provide
canonical request enforcement, controller/runtime-receipt integration, an
actual runtime fingerprint, or independent review. The candidate is not wired
to systemd or the request adapter. It supplies no service, inference, OOM,
training, score, match, or gate evidence.
