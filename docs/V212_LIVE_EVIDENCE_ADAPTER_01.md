# V2.12 live evidence adapter primitives v01

**Status: synthetic adapter groundwork only.** This module normalizes a few
live evidence sources and protects receipt persistence. It is not an
operational collector or transient-service runner.

## Implemented contract

`two_player/v212_live_supervision_v01.py` parses bounded `systemctl show`
property text and rejects duplicate or malformed fields. It normalizes active
and post-exit snapshots into the invocation-bound schema consumed by
`v212_supervision_receipt_v02.py`. The raw systemd `ActiveState=failed` is
preserved separately because the existing assembler represents completed
failure as `active_state=inactive` plus `sub_state=failed` and the manager
result. Retained successful units may report `ActiveState=active,
SubState=exited`; that raw state is preserved while normalizing the completed
lifecycle for the receipt schema.

The cgroup reader accepts only an absolute non-symlink cgroup root and a
canonical control-group path below that root. It bounds `memory.events.local`
input, rejects symlinked files, duplicate/malformed counters and values above
uint64, and returns the source/schema/cgroup/boot/time binding expected by the
receipt assembler.

Receipt persistence requires an existing private caller-owned directory. It
creates an exclusive claim and an exclusive destination placeholder, fsyncs
the directory, then calls the assembler's bounded fsync-and-rename writer. It
removes and fsyncs the claim only after success. Failures leave the claim and
reserved destination in place so a retry cannot silently replace ambiguous or
partial evidence. A caller must reconcile those files before retrying.

## Validation and limits

Ten focused synthetic tests cover manager property parsing, active/failed and
retained-success snapshot mapping, local-counter reading and path checks, and
private no-overwrite receipt persistence including writable-ancestor checks.
Together with the 26 receipt-assembler and 13 file-backed IPC tests, the
focused suite passes 49/49. `git diff --check` passes. Independent static
review found no remaining P1/P2 blocker after the implementation and test fixes.

The module does not invoke `systemctl` or `journalctl`, establish a journal
follower, collect invocation markers, schedule repeated counter reads, assemble
the receipt, coordinate cleanup, or launch a worker. No live receipt or
pre-cleanup ordering claim follows from these tests. Next work is to integrate
bounded manager/journal collection around a no-inference normal-exit worker,
persist the receipt before cleanup, and obtain independent review. OOM fault
injection remains separately gated and is not part of that step.
