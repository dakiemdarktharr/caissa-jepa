# V2.12 armed no-inference service smoke v01

Updated: 2026-10-04.

## Scope

`two_player/v212_armed_service_smoke_v01.py` composes the release-FIFO worker
barrier with a bounded transient user service and the existing local evidence
and receipt helpers. It is a synthetic lifecycle smoke, not the request adapter
and not a compute pilot.

The worker validates the bounded request and its nonce, hashes the exact
bootstrap command source and three fixed helper files before loading them,
then compiles the verified helper bytes from memory. It waits at the release
FIFO until the caller has checked the active systemd invocation, effective
resource properties, worker/caller cgroup separation, and live worker cgroup
memory files. The release token binds the request nonce, unit, invocation,
boot, cgroup, resource snapshot, source manifest, and shared monotonic deadline.
After token verification, the callback only writes an invocation marker and
returns a tiny synthetic JSON response.

The caller deadline and request-start timestamp begin before receipt-path
validation, source preflight, and request construction. It verifies request
bytes through directory-relative no-follow file descriptors against the
original directory and file identities, and repeats that verification before
receipt assembly. The caller also fingerprints and rechecks the harness and
its live-evidence/collector/receipt dependencies. The receipt is made durable
before service stop and IPC cleanup. A pre-dispatch cleanup failure reports
the remaining reconciliation path; a post-dispatch failure retains the unit
and workspace identifiers.

## Verification record

- Independent static review requested fixes for deadline coverage, host-source
  fingerprint completeness, and request-path identity. All were corrected and
  re-reviewed; no remaining P1/P2 blocker was found for one bounded
  normal-exit synthetic run. The reviewer noted that source-file hashes do not
  independently attest host bytecode already loaded before execution.
- The focused armed-smoke, collector, live-evidence, receipt, armed-protocol,
  release-token, and IPC suites pass 116/116 using `unittest`; the whitespace
  check and AST parsing of the new module/tests pass.
- Mocked composition failures cover a nonmatching response, missing journal
  evidence, receipt publication failure before a visible file, durability
  acknowledgement failure after a visible file, unit-stop failure, and IPC
  cleanup failure. These assert no premature stop/cleanup and preserve receipt
  uncertainty plus unit/workspace reconciliation identifiers as applicable.
- Further composition cases cover active-state query failure, a non-success
  manager result, deadline expiry while repeated snapshots still report the
  worker active, and Ctrl-C after release. The deadline test advances a
  controlled monotonic clock through the real polling-loop condition and
  verifies no receipt, response read, or stop occurs while the workspace stays
  available. Independent review confirmed this exercises the deadline branch.
- A separate start-race fixture reports `LoadState=not-found` before the active
  snapshot. The controlled clock advances beyond the active-wait deadline, and
  the test confirms the worker is never released, no receipt is published, no
  stop is attempted, and the IPC workspace remains available for reconciliation.
- Duplicate-key response JSON is rejected before receipt publication. Ctrl-C
  before dispatch cleans the private IPC workspace without creating a unit;
  Ctrl-C at the release call retains the active-unit/workspace reconciliation
  handles. Independent review confirmed all three branches and fixture teardown.
- Post-dispatch errors include the validated systemd invocation ID and worker
  cgroup alongside the unit and IPC path when an active snapshot is available;
  they omit request/token contents. Independent review found no diagnostic
  leakage or recovery-path issue.
- Mocked lifecycle coverage now injects failure on the first and second
  `memory.events.local` sample separately. The first prevents release; the
  second retains the dispatched worker/IPC handles. Two additional cases
  inject a stop-command timeout and Ctrl-C at the stop boundary after the
  receipt is durable; both preserve exact receipt bytes and keep reconciliation
  handles. The focused module passes 28/28. These remain fake-service tests;
  the stop timeout is an injected command result, not live deadline or recovery
  evidence.
- One live smoke completed under systemd v262 with a normal exit. It verified
  distinct caller and worker cgroups, the 128 MiB max / 96 MiB high memory
  profile, swap 0, 64 KiB file limit, no restart, `OOMPolicy=kill`, successful
  manager result, one invocation-bound journal marker, and a zero local
  `memory.events.local` delta. The receipt was persisted before cleanup, its
  embedded digest matched, and the unit was `not-found` afterward.
- Unit: `caissa-v212-armed-smoke-dadf9f51bd059f0f.service`. Receipt:
  `/tmp/caissa-v212-armed-smoke-a_a4wly0/receipt.json`, 3,731 bytes, mode
  `0600`, SHA-256
  `ee1d679c27f5a2c2b009045582a5d18eb8668f396fa33fb82e7203185a26a3a0`.
  It records hashes for three worker helper files and four host evidence
  files, plus the request digest.

## Limits and next gate

This is one normal-exit no-inference observation. The mocked suite does not
establish live timeout, interruption, start-race, manager-result or cleanup
recovery behavior, and one run does not establish repeatability. It only
exercises response corruption at the composition boundary, not arbitrary
worker process corruption. The source manifest captures file stability but
is not the complete execution
fingerprint required for a real model/runtime worker. No model/search module,
request adapter, project data, inference, OOM operation, training, score, or
outcome ran or was accessed. The run does not validate OOM attribution or
caller survival under resource failure, and it does not open the pilot gate.

Next: audit source/runtime fingerprinting and the remaining manager/journal/
counter failure map before staged request-adapter integration. The
external-supervision OOM stage still requires separate explicit authorization.
Request-adapter integration remains behind the supervision stages and
independent review.
