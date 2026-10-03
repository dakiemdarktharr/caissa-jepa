# V2.12 compute-budget amendment v06 — draft

**Status: correction draft for independent review.** This version corrects the
memory-enforcement and OOM-supervisor language in amendment v05. It preserves
the proposed 10,000-node, 5-second planner, 6-second response, and 1.5-GiB
resource values; none becomes operational from this draft. It does not
authorize data access, model fitting, match play, or outcome evaluation.

## Why a versioned correction is needed

Amendment v05 calls “1.5 GiB sampled RSS” a hard process safety stop. That
description is not supported by the implementation: the request adapter
samples its own process RSS at setup, every 256 search nodes, and at exit.
Sampling can miss transient peaks, excludes the supervising parent, and is
cooperative. It is telemetry and a sampled stop condition, not a hard memory
limit.

The kernel documents `memory.max` as the cgroup memory hard-limit mechanism;
when the limit cannot be met, the cgroup OOM killer may be invoked, and usage
can temporarily exceed the limit. `memory.high` is a reclaim/throttling
boundary, not the hard limit. The lattice disposable-scope probe verified a
configured `memory.max=1610612736` and observed an over-limit child OOM kill.
See the [Linux cgroup v2 memory controller documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)
and `docs/V212_HOST_MEMORY_CONTAINMENT_AUDIT_01.md`.

A second wording issue affects `memory.oom.group=0`. Zero avoids treating the
cgroup as one indivisible workload for a group OOM kill; it does **not** protect
the request supervisor from being selected as an individual OOM victim. The
lattice probe where a shell survived its child is one observed case, not a
guarantee. In the current adapter, the request supervisor and inference worker
share a cgroup, so the supervisor may not survive to inspect `memory.events`
or return an OOM classification.

## Proposed memory policy

1. Apply the 1.5-GiB kernel hard-limit mechanism through a verified
   `memory.max` on the bounded workload cgroup. Verify the exact value,
   hierarchy, and worker placement at runtime. Describe this as a cgroup
   hard-limit/OOM boundary, not an instantaneous RSS ceiling.
2. Keep sampled worker RSS as per-process telemetry and an optional cooperative
   stop. Label its scope and sampling cadence. Do not call it a process-tree
   or cgroup memory peak.
3. Record cgroup `memory.peak` when the lattice kernel exposes it, alongside
   the request's before/after `memory.events` counters. If the high-water file
   is unavailable, report the limit and observed event counters; any
   `memory.current` polling must include its sampling interval and must not be
   described as a peak.
4. Arrange an external supervisor outside the bounded workload cgroup, or an
   equivalently reviewed control plane, so it can observe worker termination,
   cgroup OOM events, missing response, and cleanup even if the request parent
   is killed. A missing response remains a forfeit/failure; it is never replaced
   with a successful fallback after the deadline.
5. Treat `memory.oom.group=0` as a group-kill policy choice, not a parent
   survivability guarantee. Independent review must decide whether this value
   and the supervisor placement preserve the required failure accounting.

## Evidence and remaining verification

The existing 64-MiB no-swap probe killed a 128-MiB page-touch child and the
parent observed `oom_kill=1`, with `oom_group_kill=0`. The separate 1.5-GiB
scope and the adapter's no-inference parent/worker inheritance preflight also
passed and were cleaned up. These tests verify the host mechanism and one
child-kill path. They do not verify that an adapter supervisor survives every
OOM-victim selection, that request timing fits, or that a pilot receipt is
complete.

Before any no-outcome integrated pilot, version and test the external
supervision/receipt path, verify the meaning and capture/reset procedure for
cgroup peak and event counters during a worker run, exercise worker OOM and
watchdog termination separately, and verify no process or scope remains after
each case. Independent review must accept this corrected
memory policy and implementation before any pre-fit grant. V2.12 novelty,
trajectory generation/replay, split/leakage, and separate pre-fit gates remain
unchanged and closed.


## Lattice memory.peak interface probe (2026-10-03)

A short no-inference process in a disposable user systemd scope with
`MemoryMax=1536M` reported `memory.max=1610612736`,
`memory.peak` present, `memory.oom.group=0`, and a 5,529,600-byte
`memory.peak`/current reading. Systemd reported the scope `LoadState=not-found`
and `ActiveState=inactive` after exit. This verifies that the interface is
exposed in a 1.5-GiB scope on lattice and that cleanup completed. The tiny
metadata probe is not a model working-set or headroom measurement, and it did
not verify peak reset semantics or OOM-supervisor survival.
