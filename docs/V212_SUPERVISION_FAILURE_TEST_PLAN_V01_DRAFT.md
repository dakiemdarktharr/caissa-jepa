# V2.12 supervision failure test plan v01 draft

Status: design/test inventory only. No request-adapter integration, inference,
live-service fault injection, OOM operation, training, or outcome evaluation is
authorized by this plan. The plan targets a future versioned request/runtime
receipt boundary; current v01/v02 helpers retain their existing behavior.

## Shared test contract

Build tests around a controller/worker harness with fake systemd snapshots,
clock, cgroup files, journal records, IPC files, receipt filesystem and a
compute callback spy. Every injected failure must assert all applicable
invariants together:

1. No compute import/callback before request verification and the armed
   resource-release gate.
2. No worker action or successful result escapes any failure path.
3. No accepted receipt appears before all required evidence is validated and
   the receipt is durably published.
4. Receipt state is exactly `not_attempted`, `uncertain`, or `persisted`;
   ambiguous publication is reconciled by reading the original destination,
   never by overwriting it.
5. After dispatch, retain or accurately report the unit and IPC workspace
   states and all known invocation/cgroup/receipt identifiers. Cleanup failure
   must not erase evidence or be reported as success.

Use synthetic fixture data only. Fake clocks must exercise actual wait and
deadline branches. Assert event ordering where the contract depends on order,
such as `active checks < release < compute < exit snapshot < response read <
receipt durable < stop < IPC cleanup`. Never use a result/outcome fixture as a
training or scientific evaluation input.

## Case inventory

| Case | Injection seam and fixture | Required assertions | Existing coverage / remaining work |
| --- | --- | --- | --- |
| REQ-01a | Worker raw request reader: empty, oversized, truncated, invalid UTF-8, duplicate key, non-canonical JSON, wrong schema, or altered bytes | Hash exact bounded bytes before parse; reject; no release, compute import/callback, response, accepted receipt, stop, or post-dispatch cleanup | Worker-byte digest/token binding is proposed only; add versioned parser and boundary tests |
| REQ-01b | Release token/FIFO: absent, partial, replayed, malformed, stale nonce, digest/source/runtime mismatch | Fail before compute; preserve worker/unit/workspace handles after dispatch; no response or receipt | Current release helper tests token/FIFO semantics; integrate these with amended request schema and source/runtime binding |
| GATE-01a | Effective systemd properties disagree with required profile | Do not release or call compute; no response/receipt/stop/cleanup; retain reconciliation identifiers | Armed smoke covers profile rejection before release; retain as regression in integrated harness |
| GATE-01b | Caller and worker share cgroup, `/proc/<pid>/cgroup` disagrees, or live memory file disagrees with manager snapshot | Do not release; no compute/response/receipt; retain unit/workspace | Current collector tests placement/property success and selected failure paths; add a case for each mismatch at the actual pre-release seam |
| MGR-01 | `systemctl show` fails or returns incomplete/foreign unit, invocation, boot, state, or cgroup fields after dispatch | Do not infer exit from response; no accepted result/receipt/stop/cleanup; report unknown state and known handles | Receipt assembler checks snapshot binding; collector tests query failures. Add table-driven integrated post-dispatch cases |
| MGR-02 | Exited manager snapshot has non-success `Result` or nonzero `ExecMainStatus` while a response file exists | Reject manager outcome before response acceptance; no receipt/action/stop/cleanup | Armed smoke and collector tests cover non-success manager result; assert all invariant set in integrated harness |
| MGR-03 | Start race (`not-found`), failure to reach active, or failure to exit before caller deadline | Before release: no compute; after release: no late action; keep dispatched unit/workspace for reconciliation | Controlled-clock armed tests cover active/start and exit deadline branches; include the exact request/runtime controller |
| RESP-01a | Successful manager exit followed by missing, partial, truncated, or oversized response bytes | Bounded read, exact wire-byte hash before parse; no action/accepted receipt/stop/cleanup; preserve response workspace and unit evidence | Current smoke rejects malformed/duplicate-key response, but lacks the amended raw-byte response digest/size contract |
| RESP-01b | Canonical response has bad schema, nonce, request digest, byte length, action shape/type, or non-canonical encoding | Reject after manager success; no action or accepted receipt; preserve handles | New versioned response validation and wire-byte tests required |
| JRN-01 | Journal command failure, partial line, malformed/oversized record, or zero worker markers | Evidence unavailable; no receipt/action/stop/cleanup; retain handles | Collector tests cover missing marker and bounded parser cases; integrated controller case still required |
| JRN-02 | Two worker markers, duplicate marker, conflicting cursor, wrong unit/invocation/cgroup/boot/window | Fail closed; never select a convenient marker; no receipt/action; preserve handles | Current parser/assembler reject several cases; add exact cardinality and conflict cases at collection boundary |
| CNT-01a | First or second in-run `memory.events.local` read fails, disappears, or is malformed | Pair is incomplete; do not substitute zero; no action/accepted receipt/cleanup | Collector mock covers a later counter read failure; add both positions in amended integration test |
| CNT-01b | Both counter snapshots omitted from amended receipt assembly | Reject at the new accepted-receipt boundary; no action/receipt | Legacy assembler intentionally permits both omitted; preserve that API and enforce mandatory pair in a separately versioned schema |
| CNT-02 | Counter source/schema/cgroup/boot/time mismatch, incomplete keys, Boolean/negative/non-integer value, or counter rollback | Reject evidence; no receipt/action; identify failed dimension and retain handles | Legacy receipt tests already cover identity/schema/window/order, Boolean values and rollback. Carry those regressions into the amended-schema suite and add any missing malformed-value variants |
| CLK-01 | Deadline expires during active polling, exit polling, evidence capture, response validation, or before receipt publication | Never accept late output; `not_attempted`; preserve worker/IPC handles after dispatch | Existing controlled-clock tests cover active/exit waits; add evidence and response-boundary cases |
| CLK-02 | Deadline crosses while receipt write/fsync or after receipt durability during stop/cleanup | If publication began, inspect and classify `uncertain`/`persisted`; never return action on incomplete operation; never overwrite receipt | Existing tests simulate persistence acknowledgment uncertainty and cleanup failures; add deadline-specific cases at the durable boundary |
| REC-01 | Stop/kill command fails, reap cannot be confirmed, or post-command manager query fails | Unit state is unknown unless verified; no action; retain IPC as needed and report identifiers | Stop failure and cleanup failure are tested; kill/reap attribution and post-stop query failure need explicit cases |
| REC-02 | IPC path/device/inode changes or cleanup fails partway | Do not delete substituted path; preserve receipt if persisted and report IPC path state; no action | Current workspace primitive tests substitutions; test collector recovery with substitution after dispatch and after receipt |
| RCP-01 | Receipt temporary write, rename, file fsync, directory fsync, or durability acknowledgment fails | No action; accurately distinguish `not_attempted` from `uncertain`; preserve unit/workspace and inspect original destination before retry | Current orchestration tests cover before/after writer failure; enumerate each atomic-writer seam with injected filesystem operations |
| RCP-02 | Published receipt schema, embedded digest, linked hashes, or required evidence fail independent recomputation | Reject receipt; no action; preserve bytes and reconciliation state; no automatic rewrite | Receipt hash round-trip exists for current schema; add amended-schema independent verifier and corruption cases |
| INT-01a | Ctrl-C before dispatch, while waiting at the arm/release boundary, after release, while collecting evidence | No success/action; pre-dispatch cleanup only with identity checks; after dispatch retain handles and label receipt state | Armed service tests cover several interruption points; add evidence-capture and request-v02 boundaries |
| INT-01b | Ctrl-C after durable receipt during stop/cleanup | Preserve immutable receipt; no action if operation did not complete; accurately report unit/IPC state | Current suite exercises interruption after dispatch but not every post-receipt interruption boundary |

## Required completion evidence for this plan

Before any adapter-integration review, the implementation should provide a
versioned test module with one named test per case above (subtests are
acceptable for structurally identical input variants), a coverage report
mapping each case ID to that test, and an independent review of the resulting
controller/worker code and test harness. Passing the current synthetic suite
or the existing normal-exit smoke is not a substitute. Run no live service or
OOM test from this plan; later stage authorization and review remain separate.
