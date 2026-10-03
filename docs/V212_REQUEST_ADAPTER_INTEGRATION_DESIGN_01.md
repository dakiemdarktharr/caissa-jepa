# V2.12 request-adapter integration design 01

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

The caller can validate the requested unit configuration before launch, but effective properties and the actual `ControlGroup` only exist after systemd creates the service. Therefore the worker must start in a **no-compute armed state**. The concrete candidate is a private, identity-checked release FIFO in the IPC workspace: the worker parses the bounded request, opens the FIFO for reading, then blocks before model initialization/search. The caller retries a nonblocking FIFO writer open under the shared deadline; a connected reader confirms the reviewed worker reached the barrier. Both sides check FIFO type, owner, mode, and device/inode immediately around their opens. EOF before any release bytes, partial/invalid JSON, oversized input, or failed digest is an integrity failure with no computation. The caller then verifies the active unit's effective `MemoryMax`, `MemoryHigh`, swap, runtime, restart, OOM policy, exact `ControlGroup`, and `/proc/<MainPID>/cgroup` placement, plus the live cgroup memory files. Only after every check passes may the caller send a bounded release message and close the FIFO. The FIFO coordinates trusted same-UID processes; it is not an adversarial security boundary. Linux FIFO open behavior is documented in [`fifo(7)`](https://man7.org/linux/man-pages/man7/fifo.7.html) and [`open(2)`](https://man7.org/linux/man-pages/man2/open.2.html).

The release payload must bind the request nonce, exact service unit, active invocation ID, boot ID, exact `ControlGroup`, the captured effective unit properties and live `memory.max`, `memory.high`, and `memory.swap.max` values, source-manifest digest, and capture time. Define a canonical sorted JSON encoding of these fields and include its SHA-256 digest. Before model initialization, the worker consumes the message once, recomputes the digest, compares the nonce with the request, invocation ID with its systemd-provided `INVOCATION_ID`, cgroup with `/proc/self/cgroup`, and each memory value with its live cgroup files. A second, stale, foreign-invocation, digest-mismatched, or limit-mismatched message fails closed. If this handshake cannot be implemented and tested without races, the request must fail before computation; a post-hoc property check alone is insufficient to establish the pre-compute resource gate. The current collector has no armed/release handshake and does not satisfy it.

The worker must verify its actual cgroup path and memory limit against the controller's captured service snapshot; it must not infer them from caller-side constants. The caller and worker must be in distinct cgroups. Capture `memory.events.local` from the worker cgroup while it exists, not from the caller's cgroup. Bind the service journal marker to exact unit, invocation ID, worker cgroup, boot ID, and monotonic window. Capture manager exit/result fields, response validation, and counter samples into one receipt before stop/unload and IPC cleanup.

## Request clock and outcomes

Start the caller-observed monotonic clock before request construction. It covers preflight, payload encoding, transient-service dispatch/start, worker import/model initialization, search, worker exit, response read/validation, evidence assembly, receipt durability, and cleanup. Keep planner and service runtime caps distinct from the caller response deadline. A late result is never returned as a move. Atomic file/directory fsync cannot be safely interrupted, so timeout reporting may be delayed if the filesystem blocks; the call must still report deadline failure and preserve enough evidence to reconcile a late receipt or cleanup state.

Keep these outcomes distinct: unsupported/missing systemd property; start-job failure; caller deadline; service runtime expiry; worker OOM; successful exit with missing/malformed/late/illegal response; receipt publication/durability uncertainty; missing worker counters; unit/journal invocation mismatch; and cleanup failure. No fallback action may hide timeout, OOM, invalid response, or missing evidence. A fallback allowed by the frozen planner is only a bounded-search fallback returned by a successfully validated worker response.

## Required implementation tests and gates

Before connecting this controller to the real adapter, add tests that exercise the target service-worker protocol with fixture roots and mocked process/service boundaries. Cover no-duplicate/versioned schema parsing, nonce mismatch, oversized/partial/duplicate-key JSON, short response writes and the `LimitFSIZE` boundary, illegal actions, incorrect cgroup identity/limits, start-job races, manager result retention, missing/duplicate/mismatched journal markers, counter disappearance, deadline/kill/reap outcomes, restart prevention, receipt write/rename/fsync failures, cleanup substitution, and Ctrl-C recovery handles. Tests must prove that no failure can return an action as a successful response or silently delete ambiguous evidence.

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
