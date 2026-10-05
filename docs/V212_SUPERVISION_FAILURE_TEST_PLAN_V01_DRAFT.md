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
| CNT-01a | First or second in-run `memory.events.local` read fails, disappears, or is malformed | Pair is incomplete; do not substitute zero; no action/accepted receipt/cleanup | Mocked smoke now tests failures at both first and second reads; add disappearance/malformed variants and the amended integration boundary |
| CNT-01b | Both counter snapshots omitted from amended receipt assembly | Reject at the new accepted-receipt boundary; no action/receipt | Legacy assembler intentionally permits both omitted; preserve that API and enforce mandatory pair in a separately versioned schema |
| CNT-02 | Counter source/schema/cgroup/boot/time mismatch, incomplete keys, Boolean/negative/non-integer value, or counter rollback | Reject evidence; no receipt/action; identify failed dimension and retain handles | Legacy receipt tests already cover identity/schema/window/order, Boolean values and rollback. Carry those regressions into the amended-schema suite and add any missing malformed-value variants |
| CLK-01 | Deadline expires during active polling, exit polling, evidence capture, response validation, or before receipt publication | Never accept late output; `not_attempted`; preserve worker/IPC handles after dispatch | Existing controlled-clock tests cover active/exit waits; add evidence and response-boundary cases |
| CLK-02 | Deadline crosses while receipt write/fsync or after receipt durability during stop/cleanup | If publication began, inspect and classify `uncertain`/`persisted`; never return action on incomplete operation; never overwrite receipt | A mocked stop-command timeout after durable receipt now preserves the receipt and handles. This injects a timeout result; a controlled-clock crossing during real deadline-aware stop/evidence/receipt boundaries remains untested |
| REC-01 | Stop/kill command fails, reap cannot be confirmed, or post-command manager query fails | Unit state is unknown unless verified; no action; retain IPC as needed and report identifiers | Stop failure and cleanup failure are tested; kill/reap attribution and post-stop query failure need explicit cases |
| REC-02 | IPC path/device/inode changes or cleanup fails partway | Do not delete substituted path; preserve receipt if persisted and report IPC path state; no action | Current workspace primitive tests substitutions; test collector recovery with substitution after dispatch and after receipt |
| RCP-01 | Receipt temporary write, rename, file fsync, directory fsync, or durability acknowledgment fails | No action; accurately distinguish `not_attempted` from `uncertain`; preserve unit/workspace and inspect original destination before retry | Current orchestration tests cover before/after writer failure; enumerate each atomic-writer seam with injected filesystem operations |
| RCP-02 | Published receipt schema, embedded digest, linked hashes, or required evidence fail independent recomputation | Reject receipt; no action; preserve bytes and reconciliation state; no automatic rewrite | Receipt hash round-trip exists for current schema; add amended-schema independent verifier and corruption cases |
| INT-01a | Ctrl-C before dispatch, while waiting at the arm/release boundary, after release, while collecting evidence | No success/action; pre-dispatch cleanup only with identity checks; after dispatch retain handles and label receipt state | Armed service tests cover several interruption points; add evidence-capture and request-v02 boundaries |
| INT-01b | Ctrl-C after durable receipt during stop/cleanup | Preserve immutable receipt; no action if operation did not complete; accurately report unit/IPC state | Mocked Ctrl-C at stop after durable receipt now checks byte identity and retained unit/workspace; cleanup-phase interruption and live recovery remain untested |

## Existing-test traceability (2026-10-06)

This map records named tests present in the current repository. “Partial” means
the test covers a helper or mocked boundary but does not establish the complete
future request/runtime acceptance invariant. No mapped test authorizes a live
fault injection, adapter integration, or OOM operation.

| Case | Existing named tests | Status and remaining gap |
| --- | --- | --- |
| REQ-01a | `test_v212_request_schema_v02_proposal_audit.RequestSchemaProposalAuditTests.test_wire_decoder_rejects_duplicate_noncanonical_and_float_json`; `test_request_wire_size_cap_includes_cap_plus_one_rejection`; `test_deadline_and_digest_domains_are_enforced` | Partial: offline schema audit only; no raw worker-stream hashing, request digest in release token, source/runtime binding, or no-import-before-verify integration test |
| REQ-01b | `test_v212_release_token_v01.ReleaseTokenTests.test_rejects_request_unit_invocation_boot_and_cgroup_mismatches`; `test_worker_blocks_on_fifo_open_then_consumes_one_payload_to_eof`; `test_v212_armed_service_smoke_v01.ArmedServiceBootstrapTests.test_bootstrap_compiles_and_verifies_sources_before_project_imports` | Partial: token/FIFO/bootstrap helpers are tested separately; request-v02 digest and complete source/runtime manifest are not integrated |
| GATE-01a | `test_v212_armed_protocol_v01.ArmedProtocolTests.test_invalid_effective_properties_fail_before_fifo_open`; `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_invalid_service_profile_blocks_release_and_preserves_reconciliation_handles` | Partial: mocked property gates; actual request controller is not integrated |
| GATE-01b | `test_v212_armed_protocol_v01.ArmedProtocolTests.test_snapshot_and_live_cgroup_disagreement_never_releases`; `test_v212_live_supervision_v01.SystemdSnapshotTests.test_active_snapshot_rejects_wrong_unit_or_state`; `test_v212_live_supervision_v01.CgroupSnapshotTests.test_reads_typed_local_counters` | Partial: snapshot/live-file helper checks; no complete `/proc/<pid>/cgroup` mismatch matrix at the release boundary |
| MGR-01 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_active_snapshot_query_failure_during_start_retains_workspace`; `test_exit_poll_query_error_retains_reconciliation_handles`; `test_v212_supervision_receipt_v02.ReceiptAssemblyTests.test_manager_snapshot_must_match_invocation_and_be_post_exit` | Partial: selected start/exit failures and assembler binding; not table-driven over incomplete/foreign post-dispatch snapshots |
| MGR-02 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_non_success_manager_result_retains_unit_and_workspace`; `test_v212_supervision_collector_v01.CollectorOrchestrationTests.test_non_success_manager_result_never_persists_or_stops` | Partial: mocked manager-result rejection; complete invariant assertions across the future controller remain outstanding |
| MGR-03 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_not_found_during_start_poll_waits_to_deadline_without_release_or_cleanup`; `test_deadline_expiry_while_unit_remains_running_retains_handles` | Partial: start race and active deadline; no integrated post-release exit-timeout/reap contract |
| RESP-01a | `test_v212_worker_ipc.WorkerIPCTests.test_response_rejects_oversize_duplicate_keys_and_nonfinite_values`; `test_response_requires_valid_utf8_and_a_top_level_object`; `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_invalid_worker_response_retains_unit_and_workspace`; `test_v212_supervision_collector_v01.CollectorOrchestrationTests.test_bad_response_retains_unit_workspace_and_no_receipt` | Partial: bounded IPC parser and mocked malformed response; exact response digest/length is not in the integrated receipt path |
| RESP-01b | `test_v212_request_schema_v02_proposal_audit.ResponseSchemaProposalAuditTests.test_response_rejects_wrong_binding_or_open_schema`; `test_response_wire_cap_rejects_cap_plus_one`; `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_duplicate_response_key_is_rejected_without_receipt_or_cleanup` | Partial: proposal parser/size and legacy duplicate-key rejection; no amended worker/caller response boundary |
| JRN-01 | `test_v212_supervision_collector_v01.CollectorParsingTests.test_journal_query_fails_closed_on_missing_or_duplicate_marker`; `test_run_enforces_streaming_output_bound`; `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_missing_journal_marker_retains_unit_and_workspace` | Partial: missing marker/output bound; journal command failure and malformed/partial records are not all exercised at controller boundary |
| JRN-02 | `test_v212_supervision_collector_v01.CollectorParsingTests.test_journal_query_rejects_marker_with_mismatched_trusted_metadata`; `test_v212_supervision_receipt_v02.ReceiptAssemblyTests.test_missing_marker_conflict_and_duplicate_cursor_are_rejected` | Partial: parser/assembler mismatch cases; complete cardinality and foreign-marker cases at collection boundary still need a case map |
| CNT-01a | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_first_worker_counter_sample_failure_blocks_release_and_receipt`; `test_second_worker_counter_sample_failure_retains_dispatched_handles`; `test_v212_supervision_collector_v01.CollectorOrchestrationTests.test_missing_local_counter_or_journal_marker_blocks_receipt`; `test_v212_supervision_receipt_v02.ReceiptAssemblyTests.test_counter_snapshots_require_complete_pair_schema_and_monotonic_order` | Partial: mock covers first/second read exceptions; missing keys/disappearing cgroup and amended accepted-receipt integration remain open |
| CNT-01b | None at the amended accepted-receipt boundary | Missing: legacy assembler intentionally permits both snapshots omitted; new versioned boundary must reject that pair |
| CNT-02 | `test_v212_supervision_receipt_v02.ReceiptAssemblyTests.test_counter_snapshots_reject_wrong_cgroup_boot_schema_source_and_window`; `test_counter_regression_and_bool_counts_are_rejected`; `test_v212_live_supervision_v01.CgroupSnapshotTests.test_rejects_missing_counter_and_path_escape` | Partial: receipt/live helper validation; carry the regressions into the amended schema path |
| CLK-01 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_deadline_expiry_while_unit_remains_running_retains_handles`; `test_v212_supervision_collector_v01.CollectorParsingTests.test_run_kills_child_at_caller_deadline` | Partial: active-wait/child deadline; evidence, response-validation, and pre-publication deadline seams are not all covered |
| CLK-02 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_stop_deadline_after_durable_receipt_preserves_receipt_and_recovery_handles` | Partial: the fake stop command injects a timeout after durable publication; the production deadline-aware command and receipt/fsync crossing remain untested |
| REC-01 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_unit_stop_failure_keeps_persisted_receipt_and_ipc_workspace`; `test_v212_supervision_collector_v01.CollectorOrchestrationTests.test_stop_failure_keeps_durable_receipt_and_reconciliation_handles` | Partial: stop failure covered; kill/reap and post-stop query failure are not explicitly mapped |
| REC-02 | `test_v212_worker_ipc.WorkerIPCTests.test_cleanup_fails_closed_on_replaced_request_file`; `test_release_cleanup_rejects_fifo_substitution`; `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_ipc_cleanup_failure_keeps_receipt_and_reports_stopped_unit` | Partial: primitive substitution and cleanup failure; post-dispatch substitution recovery across the integrated controller remains open |
| RCP-01 | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_receipt_publication_failure_is_uncertain_and_retains_reconciliation_handles`; `test_receipt_durability_ack_failure_preserves_visible_receipt_and_handles`; `test_v212_supervision_receipt_v02.AtomicWriteTests.test_replace_and_directory_fsync_failures_are_visible` | Partial: selected write/ack/fsync failures; exhaustive atomic-writer seam coverage and amended-receipt integration remain open |
| RCP-02 | `test_v212_supervision_receipt_v02.AtomicWriteTests.test_nonfinite_and_oversize_receipts_do_not_replace_existing_file`; `test_assembler_source_hash_failure_prevents_receipt_creation` | Partial: creation guards; no independent amended-schema receipt verifier/corruption matrix |
| INT-01a | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_ctrl_c_before_dispatch_cleans_private_workspace`; `test_ctrl_c_during_release_preserves_active_service_and_workspace`; `test_ctrl_c_after_dispatch_preserves_service_workspace_identifiers`; `test_v212_supervision_collector_v01.CollectorParsingTests.test_keyboard_interrupt_preserves_recovery_handles_after_dispatch` | Partial: selected phases; evidence-capture and request-v02 boundaries remain unmapped |
| INT-01b | `test_v212_armed_service_smoke_v01.ArmedServiceOrchestrationTests.test_ctrl_c_during_stop_after_durable_receipt_preserves_receipt_and_handles` | Partial: the mocked stop boundary checks receipt byte identity and handle retention; cleanup interruption and live recovery remain open |

## Required completion evidence for this plan

Before any adapter-integration review, the implementation should provide a
versioned test module with one named test per case above (subtests are
acceptable for structurally identical input variants), a coverage report
mapping each case ID to that test, and an independent review of the resulting
controller/worker code and test harness. Passing the current synthetic suite
or the existing normal-exit smoke is not a substitute. Run no live service or
OOM test from this plan; later stage authorization and review remain separate.
