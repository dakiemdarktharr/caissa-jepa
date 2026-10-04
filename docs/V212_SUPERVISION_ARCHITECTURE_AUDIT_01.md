# V2.12 supervision architecture audit 01

Updated: 2026-10-04. Audited source baseline: `ba390bff6e7dfb6393e03e66dd6ecbafbaa54979`.

## Decision

The armed synthetic harness supports one bounded normal-exit, no-inference
observation and a growing mocked failure suite. It does not satisfy the
request-adapter reproducibility contract. Keep request-adapter execution,
inference, training, and pilot use closed. The separately gated disposable OOM
stage also remains closed pending explicit authorization.

## Evidence by boundary

| Boundary | Verified evidence | Still unverified or incomplete |
| --- | --- | --- |
| Worker source loading | The bootstrap compares its command-line source digest, hashes three fixed helper files, then compiles those exact helper bytes from memory before invoking the synthetic callback (`two_player/v212_armed_service_smoke_v01.py:49-98`). One live normal exit passed this path. | The bundle omits Python executable/build, standard library, environment, and system dependencies. This is not the model/game/search runtime bundle required for adapter use. |
| Caller/evidence source | The harness hashes its own source plus live-evidence, collector, and receipt-assembler files and rechecks them before receipt assembly (`:37-42`, `:164-174`, `:382-405`). | These Python modules were imported before the file hashes are computed. The receipt proves current source-file stability, not that loaded code objects came from those exact bytes. It also lacks structured Python implementation/version/executable and systemd version fields. `-B` does not establish those identities. |
| Request binding | The controller identity-checks and hashes the request file before dispatch, rechecks it before receipt assembly, and records the digest (`:177-228`, `:269-275`, `:383-404`). The worker rejects duplicate keys and validates request schema/nonce. | The release-token field set contains the nonce and worker-source digest but no request digest (`two_player/v212_armed_protocol_v01.py:20-28`). The worker parses stdin without hashing the exact raw bytes (`armed_service_smoke_v01.py:54-64`). Therefore receipt-time file equality does not prove which exact bytes the worker parsed if a same-owner modification were made and reverted during the interval. Same-UID filesystem access is trusted by this smoke; request-byte/token binding is still a reproducibility gap for integration. |
| Service placement and manager state | Before release, the caller checks active state, invocation, effective memory/swap/runtime/restart/OOM properties, `MainPID` cgroup, separation from caller, and live cgroup limits (`:293-325`). After exit it normalizes manager state and accepts only success/status 0 before reading the response (`:353-374`). Mock tests cover query failure, not-found start wait, non-success result, and exit deadline. | Only the happy path has live evidence. Start-job failure, a running unit at deadline, and failed manager results have no live service characterization; failure paths intentionally retain the unit/workspace for reconciliation and do not automatically kill/reap a possibly active worker. |
| Journal evidence | The collector bounds journal output/record sizes, requires exactly one marker, and checks exact unit, invocation ID, and cgroup (`two_player/v212_supervision_collector_v01.py:191-224`). The assembler additionally binds boot ID and monotonic invocation window (`two_player/v212_supervision_receipt_v02.py:125-170`). One live marker was included in the normal-exit receipt. | No marker-missing/mismatch failure has been exercised on a live unit. OOM journal retrieval/classification was not attempted by this smoke. |
| Local memory counters | The adapter checks cgroup path containment, non-symlink regular file, byte limit, duplicate/required fields and numeric range (`two_player/v212_live_supervision_v01.py:119-188`). The assembler binds both samples to worker cgroup, boot ID and invocation window and rejects backward counters (`receipt_v02.py:255-335`). One live run produced two samples with zero delta. | No positive event transition, counter disappearance, or teardown race was tested live. The zero-delta normal-exit sample is not OOM evidence. |
| Receipt/cleanup/recovery | The receipt is persisted before stop; tests cover pre/post-publication uncertainty, stop failure, cleanup failure, deadline, not-found start race, and interruption. Post-dispatch diagnostics include known unit, invocation, cgroup and workspace identities. | Receipts are not produced when evidence is incomplete; recovery remains operator-driven. No live injected failure or OOM result has verified the end-to-end failure path. |

## Required work before request-adapter integration

1. Bind the exact request bytes to release: read a size-bounded raw stdin payload,
   hash it before parsing, include the digest in the release snapshot/token, and
   compare the worker's digest to the controller's value. Keep the private
   workspace ownership assumption explicit; do not describe same-UID isolation
   as protection from a hostile same-UID process.
2. Define a controller execution/runtime fingerprint that matches loaded code,
   not just files read after import. Record at least the interpreter real path,
   implementation/version/cache tag, executable digest, import origins and
   hashes for controller/evidence modules, systemd version, and relevant model
   dependency versions/builds when those are actually loaded. Choose and test an
   exact-byte loader or immutable artifact boundary; do not claim file hashes
   alone attest already-loaded bytecode.
3. Finish the manager/journal/counter failure matrix from
   `V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`, including duplicate or
   mismatched journal markers, counter disappearance, manager-state loss, and
   explicit reconciliation outcomes. The IPC helper already enforces bounded
   response bytes; verify that this existing limit remains enforced and
   fail-closed when wired at the adapter boundary. Keep live no-inference checks
   separate from the OOM fault stage.
4. Obtain independent review of the revised schema, exact-byte/runtime loader,
   failure map, and tests before any adapter integration. The OOM stage still
   requires its own separate explicit authorization.

## Scope statement

This audit adds no performance, strength, JEPA-superiority, or novelty result.
The current positive finding is limited to a synthetic normal-exit service
whose release gate, receipt ordering, and cleanup succeeded once. Negative and
ambiguous supervision observations elsewhere in Ground Truth remain in force.
