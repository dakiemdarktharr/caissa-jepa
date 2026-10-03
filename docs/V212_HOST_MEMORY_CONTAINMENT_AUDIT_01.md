# V2.12 process memory containment design note 01

**Status: primary-document design note; no workload was launched.** This
specifies what a future compute pilot would need to verify before describing
its memory budget as an operating-system-enforced bound. It does not test the
pilot runner, start a cgroup, or authorize a pilot, data generation, training,
or match.

## Resource-control interpretation

The kernel's cgroup-v2 documentation defines `memory.max` as the primary hard
memory limit, while noting that usage can temporarily exceed it in some
circumstances. It defines `memory.high` as a throttle/reclaim boundary that
does not invoke the OOM killer, so `memory.high` alone is not a hard cap. A
finite `memory.max` can still result in a cgroup OOM kill; a supervising
process must therefore distinguish normal completion, watchdog termination,
and memory-limit termination and preserve an auditable receipt. See the
[Linux kernel cgroup v2 memory interface](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory).

The presence of `systemd-run` does not by itself prove that a user manager can
create a scope with `MemoryMax=` or that its child receives a finite kernel
`memory.max`. Configuration and delegation depend on the host/session. Before
any future cap-stressed pilot, a no-op capability check would need to create a
disposable bounded unit, inspect its actual cgroup path and finite
`memory.max`, verify that the pilot and descendants remain in that cgroup, and
confirm that the temporary unit disappears. Do not change an ancestor cgroup
or desktop-session resource settings to make this pass. See the
[systemd resource-control reference](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)
and [systemd-run reference](https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html).

## Consequence for V2.12

1. Keep Python RSS sampling as diagnostic telemetry only; it cannot serve as
   the hard containment mechanism.
2. A future pilot version must verify a finite OS-enforced limit before work
   starts, fail closed if it cannot, and supervise the child process outside
   that limit so OOM or termination still yields a structured status.
3. Record cgroup path, `memory.max`, `memory.events` before/after, process exit
   status, watchdog status, and sampled process RSS in the receipt. State that
   `memory.max` is the containment boundary and that RSS is a separate measure.
4. Test entry-time RSS handling and periodic/final sample behavior in code, but
   do not deliberately exceed the OS limit on the desktop host just to test
   OOM behavior. Use a disposable isolated fixture or a reviewed small-limit
   subprocess test if such a test is later required.

This requirement does not invalidate V02: that completed pilot's maximum
sampled RSS was 50,212,864 bytes against its configured 1.5 GiB sampled cap,
with no reported over-cap event. The V02 implementation and hash-bound report
remain unchanged.


## Disposable cgroup verification on lattice (2026-10-03)

A temporary user systemd scope with `MemoryMax=1536M` exposed a finite kernel
`memory.max=1610612736` bytes. The scope's shell and a child shell reported the
same cgroup path. Its `memory.events` counters were all zero. The cgroup

directory was removed after exit, and systemd reported the transient unit
`LoadState=not-found`.

A separate 64 MiB disposable scope with `MemorySwapMax=0` ran a throwaway
process that touched 128 MiB of pages. The child was terminated; the surviving
shell observed `oom_kill=1` and `oom_group_kill=0` in `memory.events`. The
cgroup directory was removed. Systemd retained that failed transient unit
until `reset-failed`; after cleanup it reported `LoadState=not-found`. Earlier
reservation-only and swap-enabled probes hit memory.max events without an OOM
kill, so they do not count as enforcement evidence.

These probes verify the user-systemd/cgroup mechanism, descendant inheritance,
kernel kill accounting, and cleanup on the current lattice session. They did
not run the V2.12 pilot or its supervisor. A future pilot wrapper must still
place the actual worker and descendants in the verified bounded unit, record
its cgroup path and `memory.max`, distinguish OOM termination from request
watchdog termination, and verify its own receipt/cleanup behavior. Sampled RSS
remains telemetry, not the hard limit itself.
