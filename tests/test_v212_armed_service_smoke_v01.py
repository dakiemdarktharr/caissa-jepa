import json
from contextlib import ExitStack
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from two_player import v212_armed_protocol_v01 as armed
from two_player import v212_armed_service_smoke_v01 as service
from two_player import v212_live_supervision_v01 as live
from two_player import v212_supervision_collector_v01 as collector
from two_player import v212_worker_ipc as ipc


class ArmedServiceBootstrapTests(unittest.TestCase):
    def test_bootstrap_compiles_and_verifies_sources_before_project_imports(self):
        source = service._worker_source()
        compile(source, "<armed-worker-bootstrap>", "exec")
        self.assertLess(source.index("hashlib.sha256(argv[3])"),
                        source.index("exec(compile(verified[relative]"))
        self.assertIn("armed.run_synthetic_armed_worker", source)
        self.assertNotIn("v212_request_adapter", source)
        self.assertNotIn("import torch", source.lower())
        self.assertNotIn("model", source.lower())

    def test_source_manifest_is_bound_to_bootstrap_and_exact_helper_files(self):
        root = Path(service.__file__).resolve().parents[1]
        source = service._worker_source()
        manifest, digest = service._source_manifest(root, source)
        self.assertEqual(set(manifest), {"bootstrap_sha256", "files"})
        self.assertEqual(set(manifest["files"]), set(service.WORKER_MODULES))
        self.assertEqual(len(digest), 64)
        service._assert_source_manifest(root, manifest, source)
        host_sources = service._host_evidence_manifest(root)
        self.assertEqual(set(host_sources), set(service.HOST_EVIDENCE_MODULES))
        self.assertIn("two_player/v212_armed_service_smoke_v01.py", host_sources)
        service._assert_host_evidence_manifest(root, host_sources)

    def test_source_manifest_rejects_helper_hash_mismatch(self):
        root = Path(service.__file__).resolve().parents[1]
        source = service._worker_source()
        manifest, _ = service._source_manifest(root, source)
        manifest["files"][service.WORKER_MODULES[0]] = "0" * 64
        with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                    "worker source changed"):
            service._assert_source_manifest(root, manifest, source)

    def test_host_manifest_rejects_evidence_dependency_hash_mismatch(self):
        root = Path(service.__file__).resolve().parents[1]
        manifest = service._host_evidence_manifest(root)
        manifest[service.HOST_EVIDENCE_MODULES[0]] = "0" * 64
        with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                    "host evidence source changed"):
            service._assert_host_evidence_manifest(root, manifest)


class ArmedServiceOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ipc_parent = self.root / "ipc"
        self.ipc_parent.mkdir(mode=0o700)
        self.receipt = self.root / "receipt.json"
        self.workspaces = []

    def tearDown(self):
        for workspace in self.workspaces:
            if workspace.directory.exists():
                try:
                    ipc.cleanup_workspace(workspace)
                except ipc.WorkerIPCError:
                    pass
        self.temp.cleanup()

    def test_request_hash_rejects_path_substitution_and_detects_byte_changes(self):
        workspace = ipc.create_workspace({"schema": "test"}, parent=self.ipc_parent,
                                         with_release_fifo=True)
        self.workspaces.append(workspace)
        original_digest = service._hash_verified_request(workspace)
        with workspace.request_path.open("wb") as stream:
            stream.write(b'{"schema":"xxxx"}')
        self.assertNotEqual(service._hash_verified_request(workspace), original_digest)
        workspace.request_path.unlink()
        workspace.request_path.symlink_to(self.receipt)
        with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                    "verified request file could not be hashed"):
            service._hash_verified_request(workspace)

    def _mock_host(self, stack, *, fail_release=False, fail_profile=False,
                   response_status="released_no_inference", fail_journal=False,
                   fail_persist=None, fail_stop=False, fail_cleanup=False,
                   fail_first_show=False, exited_result="success",
                   exited_status="0", fail_exited_show=False,
                   interrupt_exited_show=False, keep_running_at_exit=False,
                   first_show_load_state="loaded", raw_response=None,
                   interrupt_release=False, timeout_stop=False,
                   interrupt_stop=False, fail_event_sample=None,
                   exited_overrides=None):
        state = {"workspace": None, "show": 0, "sequence": [],
                 "event_samples": 0, "persist_durable": False}
        original_create = ipc.create_workspace
        original_read = ipc.read_response
        original_persist = live.persist_receipt_once

        def create(request, **kwargs):
            ws = original_create(request, parent=self.ipc_parent, **kwargs)
            state["workspace"] = ws
            self.workspaces.append(ws)
            return ws

        def run(argv, **kwargs):
            if argv[0] == "systemd-run":
                state["sequence"].append("systemd-run")
                self.assertIn("--remain-after-exit", argv)
                self.assertIn("--property=Restart=no", argv)
                self.assertIn("--property=OOMPolicy=kill", argv)
                self.assertIn("--property=StandardInput=file:" +
                              str(state["workspace"].request_path), argv)
                return b""
            if tuple(argv[:4]) == ("systemctl", "--user", "stop", state["unit"]):
                state["sequence"].append("stop")
                if timeout_stop:
                    self.assertIsNotNone(kwargs.get("deadline"))
                    raise collector.CollectorError(
                        "mock stop command timed out at caller deadline")
                if interrupt_stop:
                    raise KeyboardInterrupt()
                if fail_stop:
                    raise collector.CollectorError("mock unit stop failure")
                return b""
            raise AssertionError(f"unexpected command: {argv[0]}")

        unit_props = {
            "LoadState": "loaded", "InvocationID": "a" * 32,
            "ControlGroup": "/user.slice/" + state.get("unit", "pending"),
            "MainPID": "4242",
            "EffectiveMemoryMax": str(collector.MEMORY_MAX),
            "EffectiveMemoryHigh": str(collector.MEMORY_HIGH),
            "MemorySwapMax": "0", "LimitFSIZE": str(collector.FILE_SIZE_LIMIT),
            "RuntimeMaxUSec": "8s", "Restart": "no", "OOMPolicy": "kill",
            "RemainAfterExit": "yes",
        }

        def show(unit, **kwargs):
            state["unit"] = unit
            unit_props["ControlGroup"] = "/user.slice/" + unit
            state["show"] += 1
            if state["show"] == 1:
                state["sequence"].append("active_snapshot")
                if fail_first_show:
                    raise collector.CollectorError("mock active-state query failed")
                if first_show_load_state != "loaded":
                    return {"LoadState": first_show_load_state,
                            "ActiveState": "inactive", "SubState": "dead"}
                return dict(unit_props, ActiveState="active", SubState="running")
            if state["show"] == 2:
                state["sequence"].append("exited_snapshot")
                if fail_exited_show:
                    raise collector.CollectorError("caller-observed response deadline expired")
                if interrupt_exited_show:
                    raise KeyboardInterrupt()
                if keep_running_at_exit:
                    return dict(unit_props, ActiveState="active", SubState="running")
                if raw_response is None:
                    state["workspace"].response_path.write_text(json.dumps({
                        "schema": service.RESPONSE_SCHEMA,
                        "nonce": json.loads(state["workspace"].request_path.read_text())["nonce"],
                        "status": response_status,
                    }, separators=(",", ":")), encoding="utf-8")
                else:
                    state["workspace"].response_path.write_bytes(raw_response)
                exited = dict(unit_props, ControlGroup="", ActiveState="inactive",
                              SubState="exited", Result=exited_result,
                              ExecMainStatus=exited_status)
                if exited_overrides:
                    exited.update(exited_overrides)
                return exited
            return {"LoadState": "not-found"}

        def release_when_ready(workspace, snapshot, **kwargs):
            state["sequence"].append("release")
            self.assertIsNotNone(workspace.release_identity)
            self.assertEqual(snapshot["service_unit"], state["unit"])
            self.assertEqual(snapshot["request_nonce"],
                             json.loads(workspace.request_path.read_text())["nonce"])
            if fail_release:
                raise armed.ArmedProtocolError("mock release rejection")
            if interrupt_release:
                raise KeyboardInterrupt()
            return b"synthetic-token"

        def verify_properties(properties):
            if fail_profile:
                raise collector.CollectorError("mock resource policy mismatch")

        def read_response(workspace):
            state["sequence"].append("response_read")
            return original_read(workspace)

        def persist(path, envelope):
            state["sequence"].append("persist_attempt")
            if fail_persist == "before":
                raise live.LiveEvidenceError("mock receipt publication failure")
            result = original_persist(path, envelope)
            state["persist_durable"] = True
            state["receipt_bytes_after_persist"] = Path(path).read_bytes()
            if fail_persist == "after":
                raise live.LiveEvidenceError("mock receipt durability acknowledgement failure")
            state["sequence"].append("persist_complete")
            return result

        def journal(unit, *, invocation_id, worker_cgroup, deadline):
            if fail_journal:
                raise collector.CollectorError("mock journal marker missing")
            return [{
                "__CURSOR": "mock", "_BOOT_ID": "b" * 32,
                "__MONOTONIC_TIMESTAMP": "16000",
                "_SYSTEMD_USER_UNIT": unit,
                "_SYSTEMD_INVOCATION_ID": invocation_id,
                "_SYSTEMD_CGROUP": worker_cgroup,
                "MESSAGE": collector.MARKER_PREFIX + invocation_id,
            }]

        event_samples = 0

        def read_events(**kwargs):
            nonlocal event_samples
            event_samples += 1
            state["event_samples"] = event_samples
            if fail_event_sample == event_samples:
                raise live.LiveEvidenceError("mock local counter read failure")
            return {
                "schema": "cgroup-v2.memory.events.local.v1",
                "source": "memory.events.local",
                "cgroup": "/user.slice/" + state["unit"],
                "boot_id": "b" * 32,
                "captured_monotonic_us": 13000 if event_samples == 1 else 18000,
                "counters": {"low": 0, "high": 0, "max": 0, "oom": 0,
                             "oom_kill": 0, "oom_group_kill": 0},
            }

        stack.enter_context(patch.object(collector, "_boot_id", return_value="b" * 32))
        stack.enter_context(patch.object(collector, "_proc_cgroup",
                                         side_effect=lambda pid=None:
                                         "/user.slice/caller" if pid is None
                                         else state["sequence"] and
                                         "/user.slice/" + state["unit"] or "/user.slice/pending"))
        stack.enter_context(patch.object(collector, "_monotonic_us",
                                         side_effect=[10000, 12000, 13000, 18000, 20000]))
        stack.enter_context(patch.object(collector, "_run", side_effect=run))
        stack.enter_context(patch.object(collector, "_show", side_effect=show))
        stack.enter_context(patch.object(collector, "_verify_effective_properties",
                                         side_effect=verify_properties))
        stack.enter_context(patch.object(collector, "_cgroup_scalar",
                                         side_effect=[str(collector.MEMORY_MAX),
                                                      str(collector.MEMORY_HIGH), "0"]))
        stack.enter_context(patch.object(collector, "_journal_markers", side_effect=journal))
        stack.enter_context(patch.object(collector.time, "sleep", return_value=None))
        stack.enter_context(patch.object(live, "read_memory_events_local",
                                         side_effect=read_events))
        stack.enter_context(patch.object(ipc, "create_workspace", side_effect=create))
        stack.enter_context(patch.object(ipc, "read_response", side_effect=read_response))
        stack.enter_context(patch.object(live, "persist_receipt_once", side_effect=persist))
        if fail_cleanup:
            stack.enter_context(patch.object(
                ipc, "cleanup_workspace",
                side_effect=ipc.WorkerIPCError("mock post-stop cleanup failure")))
        stack.enter_context(patch.object(armed, "release_when_ready",
                                         side_effect=release_when_ready))
        return state

    def test_mocked_success_releases_after_active_gate_and_persists_before_cleanup(self):
        with ExitStack() as stack:
            state = self._mock_host(stack)
            result = service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        envelope = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertTrue(result["armed_release_verified"])
        self.assertTrue(envelope["no_inference"])
        self.assertEqual(envelope["receipt"]["classification"], "normal_exit")
        self.assertLess(state["sequence"].index("active_snapshot"),
                        state["sequence"].index("release"))
        self.assertLess(state["sequence"].index("release"),
                        state["sequence"].index("exited_snapshot"))
        self.assertLess(state["sequence"].index("exited_snapshot"),
                        state["sequence"].index("response_read"))
        self.assertLess(state["sequence"].index("persist_complete"),
                        state["sequence"].index("stop"))
        self.assertFalse(self.workspaces[0].directory.exists())

    def test_release_failure_preserves_unit_workspace_and_skips_receipt(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_release=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_not_attempted.*unit_retained_or_state_unknown"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_invalid_service_profile_blocks_release_and_preserves_reconciliation_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_profile=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_not_attempted.*unit_retained_or_state_unknown"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertNotIn("release", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_pre_dispatch_cleanup_failure_reports_reconciliation_path(self):
        failure = ipc.WorkerIPCError("mock cleanup failure")
        with ExitStack() as stack:
            original_create = ipc.create_workspace

            def create(request, **kwargs):
                workspace = original_create(request, parent=self.ipc_parent,
                                            with_release_fifo=True)
                self.workspaces.append(workspace)
                return workspace

            stack.enter_context(patch.object(ipc, "create_workspace", side_effect=create))
            stack.enter_context(patch.object(collector, "_check_deadline",
                                             side_effect=RuntimeError("pre-dispatch rejected")))
            stack.enter_context(patch.object(ipc, "cleanup_workspace", side_effect=failure))
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "service_not_dispatched.*ipc_directory=.*pre_dispatch_cleanup_failed"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_invalid_worker_response_retains_unit_and_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, response_status="unexpected")
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "response did not match its release.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_missing_journal_marker_retains_unit_and_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_journal=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "journal marker missing.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_receipt_publication_failure_is_uncertain_and_retains_reconciliation_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_persist="before")
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_publication_or_durability_uncertain"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertIn("persist_attempt", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_receipt_durability_ack_failure_preserves_visible_receipt_and_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_persist="after")
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_publication_or_durability_uncertain"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertTrue(self.receipt.exists())
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_unit_stop_failure_keeps_persisted_receipt_and_ipc_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_stop=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_persisted.*unit_retained_or_state_unknown"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertTrue(self.receipt.exists())
        self.assertIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_ipc_cleanup_failure_keeps_receipt_and_reports_stopped_unit(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_cleanup=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "receipt_persisted.*unit_stopped.*original_directory_present"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertTrue(self.receipt.exists())
        self.assertIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_first_worker_counter_sample_failure_blocks_release_and_receipt(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_event_sample=1)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "local counter read failure.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertEqual(state["event_samples"], 1)
        self.assertNotIn("release", state["sequence"])
        self.assertNotIn("persist_attempt", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_second_worker_counter_sample_failure_retains_dispatched_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_event_sample=2)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "local counter read failure.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertEqual(state["event_samples"], 2)
        self.assertIn("release", state["sequence"])
        self.assertNotIn("persist_attempt", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_stop_deadline_after_durable_receipt_preserves_receipt_and_recovery_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, timeout_stop=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "stop command timed out.*receipt_persisted") as caught:
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        message = str(caught.exception)
        self.assertIn("receipt_persisted", message)
        self.assertIn("unit_retained_or_state_unknown", message)
        self.assertIn("invocation_id=" + "a" * 32, message)
        self.assertIn("worker_cgroup=/user.slice/" + state["unit"], message)
        self.assertEqual(state["sequence"].count("persist_complete"), 1)
        self.assertIn("stop", state["sequence"])
        self.assertTrue(self.receipt.exists())
        self.assertEqual(self.receipt.read_bytes(), state["receipt_bytes_after_persist"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_ctrl_c_during_stop_after_durable_receipt_preserves_receipt_and_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, interrupt_stop=True)
            with self.assertRaises(KeyboardInterrupt) as caught:
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        message = str(caught.exception)
        self.assertIn("receipt_persisted", message)
        self.assertIn("unit_retained_or_state_unknown", message)
        self.assertIn("invocation_id=" + "a" * 32, message)
        self.assertIn("worker_cgroup=/user.slice/" + state["unit"], message)
        self.assertEqual(state["sequence"].count("persist_complete"), 1)
        self.assertIn("stop", state["sequence"])
        self.assertNotIn("persist_attempt", state["sequence"][state["sequence"].index("stop") + 1:])
        self.assertEqual(self.receipt.read_bytes(), state["receipt_bytes_after_persist"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_active_snapshot_query_failure_during_start_retains_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_first_show=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "active-state query failed.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertIn("systemd-run", state["sequence"])
        self.assertNotIn("release", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_not_found_during_start_poll_waits_to_deadline_without_release_or_cleanup(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, first_show_load_state="not-found")
            clock = iter((0.0, 0.1, 2.1))
            stack.enter_context(patch.object(service.time, "monotonic",
                                             side_effect=lambda: next(clock)))
            stack.enter_context(patch.object(collector, "_check_deadline"))
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "did not reach active state before deadline.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt,
                                                     timeout_seconds=2)
        self.assertEqual(state["sequence"].count("active_snapshot"), 1)
        self.assertNotIn("release", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_duplicate_response_key_is_rejected_without_receipt_or_cleanup(self):
        duplicate = (b'{"schema":"' + service.RESPONSE_SCHEMA.encode()
                     + b'","schema":"' + service.RESPONSE_SCHEMA.encode()
                     + b'","nonce":"' + (b"a" * 32)
                     + b'","status":"released_no_inference"}')
        with ExitStack() as stack:
            state = self._mock_host(stack, raw_response=duplicate)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "duplicate JSON key.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_ctrl_c_before_dispatch_cleans_private_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack)
            stack.enter_context(patch.object(collector, "_check_deadline",
                                             side_effect=KeyboardInterrupt()))
            with self.assertRaisesRegex(KeyboardInterrupt,
                                        "service_not_dispatched; ipc_workspace_cleaned"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertNotIn("systemd-run", state["sequence"])
        self.assertFalse(self.workspaces[0].directory.exists())

    def test_ctrl_c_during_release_preserves_active_service_and_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, interrupt_release=True)
            with self.assertRaises(KeyboardInterrupt) as caught:
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertIn("receipt_not_attempted", str(caught.exception))
        self.assertIn("unit_retained_or_state_unknown", str(caught.exception))
        self.assertIn("release", state["sequence"])
        self.assertIn("invocation_id=" + "a" * 32, str(caught.exception))
        self.assertIn("worker_cgroup=/user.slice/" + state["unit"],
                      str(caught.exception))
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_non_success_manager_result_retains_unit_and_workspace(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, exited_result="exit-code", exited_status="1")
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "did not exit successfully.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertFalse(self.receipt.exists())
        self.assertIn("exited_snapshot", state["sequence"])
        self.assertNotIn("response_read", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_exit_snapshot_identity_and_required_fields_fail_before_response_read(self):
        cases = (
            ({"InvocationID": "c" * 32}, "identity did not match active worker"),
            ({"ControlGroup": "/user.slice/foreign.service"},
             "identity did not match active worker"),
            ({"InvocationID": ""}, "systemd property InvocationID is missing"),
            ({"Result": ""}, "systemd property Result is missing"),
            ({"ExecMainStatus": "invalid"},
             "systemd property ExecMainStatus is malformed"),
        )
        for overrides, expected_error in cases:
            with self.subTest(overrides=overrides), ExitStack() as stack:
                state = self._mock_host(stack, exited_overrides=overrides)
                with self.assertRaisesRegex(
                        service.ArmedServiceSmokeError, expected_error):
                    service.run_no_inference_armed_smoke(receipt_path=self.receipt)
                self.assertFalse(self.receipt.exists())
                self.assertNotIn("response_read", state["sequence"])
                self.assertNotIn("persist_attempt", state["sequence"])
                self.assertNotIn("stop", state["sequence"])
                self.assertTrue(self.workspaces[-1].directory.exists())

    def test_exit_poll_query_error_retains_reconciliation_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, fail_exited_show=True)
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "response deadline expired.*receipt_not_attempted.*unit_retained_or_state_unknown"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertIn("release", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_deadline_expiry_while_unit_remains_running_retains_handles(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, keep_running_at_exit=True)
            clock = iter((0.0, 0.1, 0.2, 2.1))
            stack.enter_context(patch.object(service.time, "monotonic",
                                             side_effect=lambda: next(clock)))
            stack.enter_context(patch.object(collector, "_check_deadline"))
            with self.assertRaisesRegex(service.ArmedServiceSmokeError,
                                        "did not exit before caller deadline.*receipt_not_attempted"):
                service.run_no_inference_armed_smoke(receipt_path=self.receipt,
                                                     timeout_seconds=2)
        self.assertIn("release", state["sequence"])
        self.assertEqual(state["sequence"].count("exited_snapshot"), 1)
        self.assertNotIn("response_read", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertFalse(self.receipt.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_ctrl_c_after_dispatch_preserves_service_workspace_identifiers(self):
        with ExitStack() as stack:
            state = self._mock_host(stack, interrupt_exited_show=True)
            with self.assertRaises(KeyboardInterrupt) as caught:
                service.run_no_inference_armed_smoke(receipt_path=self.receipt)
        self.assertIn("receipt_not_attempted", str(caught.exception))
        self.assertIn("unit_retained_or_state_unknown", str(caught.exception))
        self.assertIn(str(self.workspaces[0].directory), str(caught.exception))
        self.assertIn("release", state["sequence"])
        self.assertNotIn("stop", state["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())


if __name__ == "__main__":
    unittest.main()
