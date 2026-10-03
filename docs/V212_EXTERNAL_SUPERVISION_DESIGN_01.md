# V2.12 external worker supervision design 01

**Status: stages 1–2 placement/lifecycle checks passed for no-inference workers; the bounded OOM probe produced an ambiguous manager-classified OOM/SIGKILL result with zero local oom/oom_kill counters. Local OOM containment remains unvalidated.** This note translates the open external-OOM-supervision gate into a testable design. It does not authorize inference, an OOM stress test, a pilot, training, or a change to the V2.12 method or budget.

## Candidate architecture

Run each inference worker as a uniquely named transient **service** managed by systemd, with a finite per-unit memory limit and a runtime limit. Keep the request-owning caller outside that service unit. Prefer service semantics over `systemd-run --scope`: systemd documents that a transient service runs in a detached environment with the service manager as parent, while a scope runs with `systemd-run` itself as the command's parent. The systemd-run interface supports `--service-type=exec`, `--pipe`, and `--wait`; these are candidate mechanics, not a verified command line for this host.

The kernel documents that an OOM event invoked in a cgroup does not kill tasks outside that cgroup. That supports the isolation hypothesis for a worker-local cgroup OOM. It does not establish protection from OOM at an ancestor cgroup, host-wide OOM, or a systemd-oomd action targeting a larger ancestor. The caller's cgroup ancestry, effective limits, and available headroom therefore remain part of the safety proof. `MemoryMax=` maps to `memory.max`; systemd describes it as the final memory defense and recommends `MemoryHigh=` as the normal pressure control.

A worker service may use `MemoryMax=` and a finite `RuntimeMaxSec=` after checking that the installed manager accepts and enforces those properties. The outer caller must retain its own monotonic request clock and enforce the existing absolute request/response deadline; a service runtime limit starts only after the unit becomes active and cannot account for all dispatch/startup latency. No timeout value is frozen by this design note.

## Response and evidence contract

The caller should treat each service invocation as one request and accept exactly one bounded, schema-validated response. Keep worker stdout reserved for the response, stderr for bounded diagnostics, and reject missing, duplicate, malformed, late, illegal-action, or non-finite responses as no-action/forfeit according to the reviewed protocol. Never replace an OOM or timeout with a fallback that could be mistaken for a completed search.

Before cleanup or unit release, capture the unique unit name and invocation ID, unit result, main-process exit code/status, effective memory properties, control-group path, caller/worker cgroup paths, elapsed request time, and local cgroup memory event counters where available. In particular, compare `memory.events.local` (or a verified manager result such as the unit's OOM result and exit fields); hierarchical `memory.events` may include descendant events. A transient unit and its execution statistics may be garbage-collected after it stops and is no longer referenced, while the kernel cgroup files may disappear when the cgroup is removed. The caller must pin/query the unit result or use a verified external monitor to capture counters before they vanish, and then persist the evidence in the versioned receipt before bounded cleanup. If neither manager result nor counters can be captured and verified, fail closed.

## Required staged validation

1. **Read-only capability preflight:** record systemd version and user-manager availability; confirm unified cgroup v2, memory-controller delegation, relevant transient-service properties, and effective limits. Inspect the worker unit and caller ancestry. Fail closed if the manager cannot enforce the requested finite limit, if the caller shares the worker's unit cgroup, or if an ancestor limit can exhaust the supervisor's headroom.
2. **No-inference placement check:** run a trivial process only after review of this design. Verify from the manager and `/proc`/cgroup that the worker is inside the expected transient service and the caller remains outside it. Verify effective `MemoryMax`, unit runtime control, stdio behavior, and caller-observed deadline accounting. After the process exits, record when the cgroup directory and `memory.events.local` disappear, whether the unit result/exit fields remain queryable while referenced and after release, and whether `--collect` changes either lifecycle. Exercise the planned capture order and bounded cleanup without an OOM event. If counters vanish before capture, define and test an external monitor/capture path or rely on manager result fields that were independently verified to distinguish OOM from timeout; unavailable evidence is an integrity failure. This is not an inference or OOM run.
3. **Disposable OOM fault test:** only after independent review and a separate explicit test authorization, run a tiny controlled allocator in a disposable transient service with a low memory cap and no project model/data. Require the worker to be terminated while the external caller remains alive, the outcome to be classified as OOM (not timeout or success), and the selected evidence path (manager result or externally captured local event counters) to be durably recorded before unit/cgroup teardown. Verify there is no automatic restart/retry that could be mistaken for the same request. Stop on any host-wide or ancestor pressure, ambiguous event, leaked unit, or evidence loss.
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

## No-inference placement and lifecycle check (2026-10-04)

After independent review, two short transient user services ran only a Python process that reported its cgroup files and slept briefly. No project code/data, model, inference, memory-pressure allocator, OOM event, or outcome was involved. The services used `MemoryMax=128M`, `MemoryHigh=96M`, `MemorySwapMax=0`, `RuntimeMaxSec=10s`, `Restart=no`, and `OOMPolicy=kill`. While active, systemd reported `EffectiveMemoryMax=134217728` and `EffectiveMemoryHigh=100663296`; the worker read matching `memory.max`, `memory.high`, and `memory.swap.max`. Its unit cgroup was `app.slice/caissa-v212-placement-*.service`; the caller was in sibling `app.slice/flatpak-session-helper.service`. All three temporary units used across the placement/lifecycle checks were later `LoadState=not-found`, with no running unit left.

The retained-unit case used `RemainAfterExit=yes`. After the worker exited successfully, `Result=success` and `ExecMainStatus=0` remained queryable while the unit was retained, but `ControlGroup=` was empty and the cgroup directory plus `memory.events.local` had already disappeared. The `--collect` case was observed active with the same finite limit; after completion, `LoadState=not-found` and the unit/cgroup files were gone. A synthetic `Result=success` returned alongside `LoadState=not-found` is not treated as stored execution evidence.

This verifies placement, effective resource properties, caller/worker cgroup separation, and the successful-exit evidence lifecycle for trivial processes. It does not verify OOM result classification, caller survival under worker OOM, headroom under ancestor pressure, atomic receipt persistence, service startup contribution to a real request, or inference behavior. An OOM-stage design must capture the manager result while pinned or prove an external counter monitor works before cgroup teardown. At the time of this stage-2 check, no OOM, inference, or pilot had run; the later bounded probe is recorded below.

Primary references:

- [Linux kernel cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html): cgroup-local OOM boundaries, `memory.oom.group`, `memory.events`, and `memory.events.local`.
- [systemd-run manual](https://github.com/systemd/systemd/blob/main/man/systemd-run.xml): transient service versus scope, `--service-type=exec`, `--pipe`, `--wait`, and collection behavior.
- [systemd resource-control manual](https://github.com/systemd/systemd/blob/main/man/systemd.resource-control.xml): `MemoryMax=`, effective limits, and `MemoryHigh=`.
- [systemd service manual](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml): `RuntimeMaxSec=` starts after activation and does not apply to oneshot units; OOM result/exit status and restart behavior.
- [systemd unit manual](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml): transient unit garbage collection and loss of unloaded execution-result state.
## Bounded transient-service OOM probe (2026-10-04; ambiguous)

A gated Python worker passed pre-release checks for a sibling cgroup, effective MemoryMax=64M, MemorySwapMax=0, memory.oom.group=1, Restart=no, OOMPolicy=kill, and readable memory.events.local. It attempted to touch 256 MiB. systemd reported Result=oom-kill with ExecMainStatus=9; the external controller remained alive and the worker did not create its completion marker. The unit was verified LoadState=not-found after cleanup.

The last sampled worker-local memory.events.local had max=3, but oom=0, oom_kill=0, and oom_group_kill=0. Per the kernel cgroup-v2 documentation, these counters distinguish approaching the max boundary from OOM/allocation-failure and killed-process events. systemd documents OOMPolicy=kill for processes terminated by the kernel OOM killer or systemd-oomd. Thus the manager result is an OOM-classified observation, but the available evidence does not identify the worker's memory.max as the cause; local containment is not demonstrated, and stage 3 is not passed. Independent review reached the same disposition.

Before repeating fault injection, validate the event/result capture path during a no-inference stage-2 run: observe local counters and manager properties while the cgroup exists, persist the event deltas and result before teardown, and demonstrate attribution to the worker cgroup. Investigate kernel-local versus ancestor/global and systemd-oomd causes. Obtain independent review of the capture-path evidence before another OOM test. No inference, training, project data, or outcomes were used. Probe log: /tmp/caissa_v212_oom_probe.log.

Primary references:

- [Linux kernel cgroup v2 event definitions](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [systemd service OOMPolicy](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml)
- [systemd process result meanings](https://github.com/systemd/systemd/blob/main/man/systemd.exec.xml)


### No-inference event/result capture-path check (2026-10-04)

A gated normal-exit transient service repeated the sibling-cgroup and finite-limit preflight (128 MiB effective max, swap 0, memory.oom.group=1, Restart=no, OOMPolicy=kill). The external controller captured 14 samples of the worker's memory.events.local while the cgroup existed. After normal worker exit, the controller captured SubState=exited, Result=success, ExecMainStatus=0, and empty ControlGroup; the cgroup event file was absent. It wrote the receipt before cleanup and verified the transient unit was not-found afterward. No allocation stress or OOM event occurred. Log: /tmp/caissa_v212_capture_preflight_v2.log.

Independent review accepts this as the stage-2 placement/lifecycle/capture-order prerequisite. It validates ordinary sampling and result capture only; all event counters stayed zero, so it does not validate nonzero-event detection or OOM attribution. Stage 3 must explicitly test whether a local OOM counter can be captured before teardown. If only the manager result is observed, classify it as a manager-classified OOM with local source uncorroborated.
