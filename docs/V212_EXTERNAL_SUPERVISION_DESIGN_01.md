# V2.12 external worker supervision design 01

**Status: research proposal only; partial read-only host capability preflight completed; not independently reviewed or operationally validated.** This note translates the open external-OOM-supervision gate into a testable design. It does not authorize inference, an OOM stress test, a pilot, training, or a change to the V2.12 method or budget.

## Candidate architecture

Run each inference worker as a uniquely named transient **service** managed by systemd, with a finite per-unit memory limit and a runtime limit. Keep the request-owning caller outside that service unit. Prefer service semantics over `systemd-run --scope`: systemd documents that a transient service runs in a detached environment with the service manager as parent, while a scope runs with `systemd-run` itself as the command's parent. The systemd-run interface supports `--service-type=exec`, `--pipe`, and `--wait`; these are candidate mechanics, not a verified command line for this host.

The kernel documents that an OOM event invoked in a cgroup does not kill tasks outside that cgroup. That supports the isolation hypothesis for a worker-local cgroup OOM. It does not establish protection from OOM at an ancestor cgroup, host-wide OOM, or a systemd-oomd action targeting a larger ancestor. The caller's cgroup ancestry, effective limits, and available headroom therefore remain part of the safety proof. `MemoryMax=` maps to `memory.max`; systemd describes it as the final memory defense and recommends `MemoryHigh=` as the normal pressure control.

A worker service may use `MemoryMax=` and a finite `RuntimeMaxSec=` after checking that the installed manager accepts and enforces those properties. The outer caller must retain its own monotonic request clock and enforce the existing absolute request/response deadline; a service runtime limit starts only after the unit becomes active and cannot account for all dispatch/startup latency. No timeout value is frozen by this design note.

## Response and evidence contract

The caller should treat each service invocation as one request and accept exactly one bounded, schema-validated response. Keep worker stdout reserved for the response, stderr for bounded diagnostics, and reject missing, duplicate, malformed, late, illegal-action, or non-finite responses as no-action/forfeit according to the reviewed protocol. Never replace an OOM or timeout with a fallback that could be mistaken for a completed search.

Before cleanup, capture the unique unit name and invocation ID, unit result, main-process exit code/status, effective memory properties, control-group path, caller/worker cgroup paths, elapsed request time, and local cgroup memory event counters where available. In particular, compare `memory.events.local` (or a verified unit result) before/after; hierarchical `memory.events` may include descendant events. Preserve this evidence in the versioned receipt. Cleanup must be bounded and must not delete evidence before the receipt is durable. Test what `--collect` does to the opportunity to read final unit/cgroup properties; do not assume those properties remain available after collection.

## Required staged validation

1. **Read-only capability preflight:** record systemd version and user-manager availability; confirm unified cgroup v2, memory-controller delegation, relevant transient-service properties, and effective limits. Inspect the worker unit and caller ancestry. Fail closed if the manager cannot enforce the requested finite limit, if the caller shares the worker's unit cgroup, or if an ancestor limit can exhaust the supervisor's headroom.
2. **No-inference placement check:** run a trivial process only after review of this design. Verify from the manager and `/proc`/cgroup that the worker is inside the expected transient service and the caller remains outside it. Verify effective `MemoryMax`, unit runtime control, stdio behavior, unit-result capture, and cleanup. This is not a request/inference run.
3. **Disposable OOM fault test:** only after independent review and a separate explicit test authorization, run a tiny controlled allocator in a disposable transient service with a low memory cap and no project model/data. Require the worker to be terminated while the external caller remains alive, the outcome to be classified as OOM (not timeout or success), local event/unit evidence to be recorded, and the unit/cgroup to be removed. Stop on any host-wide or ancestor pressure, ambiguous event, leaked unit, or evidence loss.
4. **No-outcome integration:** only after stages 1–3 pass review, exercise synthetic legal roots and random initialization under the existing proposed request deadlines. Verify setup + dispatch + search + validation + receipt within caller-observed bounds; separately account for service-start time, search time, response time, and every no-outcome/forfeit. Do not generate episodes, fit weights, or record game scores.
5. **Independent review:** review the architecture, unit configuration, failure mapping, receipt schema, tests, and observed no-outcome evidence before the pilot gate can be reconsidered.

## Failure cases that must stay distinct

- Manager unavailable, unsupported property, permission/delegation failure, or wrong effective limit: fail closed before dispatch.
- Worker memory OOM: no move; retain unit/cgroup evidence and classify as OOM.
- Caller-observed deadline or service runtime expiry: no move; classify as timeout, with OOM counters checked to avoid conflation.
- Worker exits successfully without one valid response, emits malformed output, or returns an illegal action: invalid response/forfeit.
- Parent or manager failure, lost unit state, missing counters, or incomplete receipt: supervision-integrity failure; no move and no pilot evidence accepted.
- Ancestor/host pressure: abort the run; a worker-local memory limit is not evidence that the external caller is safe under a broader OOM event.

## Evidence and scope limits

The existing disposable-scope tests established cgroup-v2 memory enforcement and worker inheritance for a scope. They did not exercise transient-service semantics, a service-local OOM, caller survival, or receipt capture. The request-adapter tests are mocked and do not close those gaps. No claim of operational OOM supervision follows until the staged checks pass.

## Partial read-only host capability preflight (2026-10-04)

A read-only lattice check observed systemd 262. The user manager responds to queries and reports version 262; `user@1000.service` is active with `Delegate=yes` and memory accounting enabled. The manager state query reports `degraded`, which was not diagnosed. The unified cgroup memory controller is available and enabled in the user-manager subtree. systemd reports an effective memory maximum/high of 16,092,520,448 bytes (about 15 GiB) for the user manager and its app slice; their direct `MemoryMax`/`MemoryHigh` properties are `infinity`. The caller currently runs in a child cgroup under that app slice.

This indicates that the host has a functioning delegated cgroup-v2 user manager and a finite inherited effective memory ceiling. It does **not** show that a transient inference service can be started with the requested finite limit, that the worker's effective limit will be below the ancestor ceiling, or that sufficient live headroom exists. It also does not show worker-local OOM containment, caller survival, reliable unit-result/event capture, or cleanup. No transient unit was created, and no inference or OOM test ran. Continue to fail closed until a reviewed no-inference placement check verifies those properties.

Primary references:

- [Linux kernel cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html): cgroup-local OOM boundaries, `memory.oom.group`, `memory.events`, and `memory.events.local`.
- [systemd-run manual](https://github.com/systemd/systemd/blob/main/man/systemd-run.xml): transient service versus scope, `--service-type=exec`, `--pipe`, `--wait`, and collection behavior.
- [systemd resource-control manual](https://github.com/systemd/systemd/blob/main/man/systemd.resource-control.xml): `MemoryMax=`, effective limits, and `MemoryHigh=`.
- [systemd service manual](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml): `RuntimeMaxSec=` starts after activation and does not apply to oneshot units.
