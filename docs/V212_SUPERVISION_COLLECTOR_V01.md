# V2.12 no-inference supervision collector v01

Updated: 2026-10-04.

## Purpose

`two_player/v212_supervision_collector_v01.py` composes the file-backed worker IPC helper, live systemd/cgroup evidence adapter, and v02 receipt assembler for one synthetic normal-exit service. It validates that a response belongs to the request nonce, captures the effective service limits and two worker-local `memory.events.local` snapshots, binds one service-journal marker to the requested unit, invocation ID, and worker cgroup, and writes the receipt before stopping the transient unit.

The worker only sleeps briefly and writes a small JSON response. It does not load CAISSA-JEPA, run inference, access project data, or update parameters. The collector does not query the kernel OOM journal or trigger memory pressure. Its label `not_collected_no_oom_operation` means no kernel OOM collection was attempted; it is not evidence that the host had no unrelated OOM events.

## Bounds and failure handling

The transient unit requests `MemoryMax=128M`, `MemoryHigh=96M`, `MemorySwapMax=0`, `LimitFSIZE=65536`, `RuntimeMaxSec=8s`, `Restart=no`, and `OOMPolicy=kill`; the collector checks manager-reported values and worker cgroup files before accepting the run. Commands use a shared monotonic deadline and streaming output bounds. The function never returns a late success. Local atomic persistence and fsync cannot be safely interrupted, so they can delay reporting a deadline overrun.

The receipt destination is validated before dispatch and is create-only. Once dispatch may have started, failures leave the transient unit and IPC workspace for reconciliation and report the unit, receipt destination, and observed workspace-path state. If persistence was attempted but its durable publication status cannot be established, the error reports that uncertainty. Ctrl-C preserves the recovery handles while propagating the interruption. Cleanup verifies the original IPC directory and file identities and does not recursively remove unexpected content.

## Verification record

- Focused live-supervision, worker-IPC, receipt-assembler, and collector suites: 62/62 passed with Python 3.11.17. `git diff --check` passed. Independent read-only review found no remaining P1/P2 issue within this collector's scope.
- One live normal-exit smoke completed on 2026-10-04. The nonce/schema response validated; caller and worker cgroups differed; configured limits and both local counter samples matched; one marker bound to the same service invocation was included; the receipt was persisted before cleanup; and `systemctl show` reported `LoadState=not-found` after cleanup.
- Receipt: `/tmp/caissa-v212-smoke-receipt-00ywfuj4/receipt.json`, 2,683 bytes, mode `0600`, SHA-256 `79dabba0e715ba1fe03cca0d1390aba198620f1164e1ae300db453e7349ba03a`. Its embedded receipt digest matched. The receipt contains one invocation-bound service-journal marker and two local counter snapshots. Kernel OOM evidence was not collected.
- After the mocked lifecycle/receipt failure suite passed 92/92 and independent review found no remaining blocker to a trivial normal-exit smoke, a second bounded synthetic run completed under systemd 262. It again validated distinct caller/worker cgroups, limits, local counter pair, invocation marker, receipt-before-stop, embedded digest, and unit `LoadState=not-found` after cleanup. Unit: `caissa-v212-smoke-5f506842ca976f98.service`; invocation: `46fd79df69194b90af17ea900af4312d`.
- Second receipt: `/tmp/caissa-v212-smoke-183523/receipt.json`, 2,683 bytes, mode `0600`, SHA-256 `55937b10f67666b0f0ca3bdb2365cf22b28ac93a3e2e92ee901bbceef5d351f4`; embedded receipt digest matches. The two runs are separate normal-exit observations, not a repeatability study. No OOM journal was collected.
- The request-adapter test modules were attempted but could not import because NumPy is unavailable in the installed Python environments. The passing 62-test count covers only the four focused supervision/IPC/receipt suites.
- The current mocked orchestration regression suite covers lifecycle ordering and failure boundaries; collector/live-evidence/receipt/armed-protocol/release-token/IPC suites pass 92/92 with `unittest`. `pytest` is unavailable in this runtime. This is test evidence separate from the two live no-inference observations.

The later release-FIFO composition and its third live normal-exit observation
are documented separately in [`V212_ARMED_SERVICE_SMOKE_V01.md`](V212_ARMED_SERVICE_SMOKE_V01.md).
That harness reuses this collector's evidence/receipt components but adds the
pre-compute armed release gate; it does not replace or extend the two receipts
listed above.

## Limits and next gate

These two receipts document the earlier collector path; the armed-worker
composition is recorded separately. Neither record validates OOM attribution,
timeout behavior on a live service, interruption recovery against a live unit,
systematic repeatability, request-adapter integration, inference latency, or
pilot feasibility. They do not change the research method or open training,
pilot, or OOM gates. Any OOM fault test still requires separate explicit
authorization. Next, expand armed-service mocked recovery/failure coverage and
complete staged review before request-adapter use.
