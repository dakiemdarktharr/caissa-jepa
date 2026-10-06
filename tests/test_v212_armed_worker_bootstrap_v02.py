import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from two_player import v212_armed_protocol_v02 as armed
from two_player import v212_armed_worker_bootstrap_v02 as bootstrap
from two_player import v212_release_token_v02 as release
from two_player import v212_worker_ipc as ipc


class ArmedWorkerBootstrapV02Tests(unittest.TestCase):
    def test_bootstrap_compiles_and_reads_before_project_source_access(self):
        source = bootstrap.worker_source()
        compile(source, "<armed-worker-bootstrap-v02>", "exec")
        self.assertLess(source.index("request_raw=read_raw_request()"),
                        source.index("root=Path(sys.argv[3])"))
        self.assertLess(source.index("root=Path(sys.argv[3])"),
                        source.index("exec(compile(verified[relative]"))
        self.assertIn("request_bytes=request_raw", source)
        self.assertIn("v212_armed_protocol_v02.py", source)
        self.assertNotIn("v212_request_adapter", source)
        self.assertNotIn("import torch", source.lower())

    def test_source_manifest_binds_bootstrap_and_all_v02_worker_helpers(self):
        root = Path(bootstrap.__file__).resolve().parents[1]
        source = bootstrap.worker_source()
        manifest, digest = bootstrap.source_manifest(root, source)
        self.assertEqual(set(manifest), {"bootstrap_sha256", "files"})
        self.assertEqual(set(manifest["files"]), set(bootstrap.WORKER_MODULES))
        self.assertEqual(len(digest), 64)
        self.assertEqual(
            manifest["bootstrap_sha256"],
            hashlib.sha256(source.encode("utf-8")).hexdigest())
        request = bootstrap.request_bytes("a" * 32, manifest, digest)
        self.assertIn(b'"schema":"caissa.synthetic.armed-bootstrap-request.v02"',
                      request)

    def _run_bootstrap(self, raw: bytes,
                       project_root: str = "/missing/project-root"
                       ) -> subprocess.CompletedProcess:
        source = bootstrap.worker_source()
        return subprocess.run(
            [sys.executable, "-B", "-c", source, "/missing/ipc",
             "caissa-test.service", project_root],
            input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=5)

    def test_empty_and_one_byte_requests_are_rejected_before_project_access(self):
        for raw in (b"", b"{"):
            with self.subTest(byte_count=len(raw)):
                result = self._run_bootstrap(raw)
                self.assertEqual(result.returncode, 31)
                self.assertEqual(result.stdout, b"")

    def test_invalid_utf8_is_rejected_before_project_source_access(self):
        result = self._run_bootstrap(b"\xff")
        self.assertEqual(result.returncode, 31)
        self.assertEqual(result.stdout, b"")

    def test_duplicate_request_key_is_rejected_before_project_source_access(self):
        result = self._run_bootstrap(
            b'{"schema":"x","schema":"y","nonce":"' + b"a" * 32 + b'"}')
        self.assertEqual(result.returncode, 31)
        self.assertEqual(result.stdout, b"")

    def test_cap_plus_one_is_rejected_before_project_source_access(self):
        with tempfile.TemporaryFile() as stream:
            stream.write(b" " * (bootstrap.MAX_REQUEST_BYTES + 1))
            stream.seek(0)
            source = bootstrap.worker_source()
            result = subprocess.run(
                [sys.executable, "-B", "-c", source, "/missing/ipc",
                 "caissa-test.service", "/missing/project-root"],
                stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=False, timeout=5)
        self.assertEqual(result.returncode, 30)
        self.assertEqual(result.stdout, b"")

    def test_exact_hard_cap_reaches_bootstrap_fingerprint_gate(self):
        root = Path(bootstrap.__file__).resolve().parents[1]
        source = bootstrap.worker_source()
        manifest, _ = bootstrap.source_manifest(root, source)
        manifest["bootstrap_sha256"] = "0" * 64
        encoded_manifest = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode("utf-8")
        digest = hashlib.sha256(encoded_manifest).hexdigest()
        raw = bootstrap.request_bytes("a" * 32, manifest, digest)
        self.assertLess(len(raw), bootstrap.MAX_REQUEST_BYTES)
        raw += b" " * (bootstrap.MAX_REQUEST_BYTES - len(raw))
        self.assertEqual(len(raw), bootstrap.MAX_REQUEST_BYTES)
        result = self._run_bootstrap(raw, str(root))
        self.assertEqual(result.returncode, 36)
        self.assertEqual(result.stdout, b"")

    def test_verified_bootstrap_releases_on_exact_stdin_and_returns_response(self):
        root = Path(bootstrap.__file__).resolve().parents[1]
        # Route cgroup checks to fixture files and suppress the synthetic
        # journal marker so this offline test has no host-journal side effect.
        worker_source = bootstrap.worker_source().replace(
            "expected_source_manifest_sha256=request[\"source_manifest_sha256\"],",
            "expected_source_manifest_sha256=request[\"source_manifest_sha256\"],\n"
            "    cgroup_root=Path(sys.argv[4]),")
        source = ("import syslog; syslog.syslog=lambda *args,**kwargs:None\n"
                  + worker_source)
        manifest, manifest_digest = bootstrap.source_manifest(root, source)
        nonce = "a" * 32
        request_object = {
            "schema": bootstrap.REQUEST_SCHEMA,
            "nonce": nonce,
            "source_manifest": manifest,
            "source_manifest_sha256": manifest_digest,
        }
        raw_request = bootstrap.request_bytes(nonce, manifest, manifest_digest)
        self.assertEqual(
            raw_request,
            json.dumps(request_object, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8"))
        nonce_invocation = "b" * 32
        unit = "caissa-bootstrap-fixture.service"
        cgroup = next(
            line[3:] for line in Path("/proc/self/cgroup").read_text(
                encoding="ascii").splitlines() if line.startswith("0::"))
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(
            encoding="ascii").strip().replace("-", "").lower()

        with tempfile.TemporaryDirectory(prefix="caissa-bootstrap-v02-") as td:
            temp_root = Path(td)
            cgroup_root = temp_root / "cgroup"
            worker_group = cgroup_root / cgroup.lstrip("/")
            worker_group.mkdir(parents=True)
            for name, value in (("memory.max", "134217728"),
                                ("memory.high", "100663296"),
                                ("memory.swap.max", "0")):
                (worker_group / name).write_text(value, encoding="ascii")

            workspace = ipc.create_workspace(
                request_object, parent=temp_root, with_release_fifo=True)
            process = None
            try:
                env = dict(os.environ, INVOCATION_ID=nonce_invocation)
                process = subprocess.Popen(
                    [sys.executable, "-B", "-c", source,
                     str(workspace.directory), unit, str(root), str(cgroup_root)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, env=env)
                process.stdin.write(raw_request)
                process.stdin.close()
                process.stdin = None

                snapshot = {
                    "schema": release.SCHEMA,
                    "request_nonce": nonce,
                    "request_sha256": hashlib.sha256(raw_request).hexdigest(),
                    "service_unit": unit,
                    "invocation_id": nonce_invocation,
                    "boot_id": boot_id,
                    "control_group": cgroup,
                    "effective_properties": dict(
                        armed.EXPECTED_EFFECTIVE_PROPERTIES),
                    "live_cgroup": {"memory.max": "134217728",
                                    "memory.high": "100663296",
                                    "memory.swap.max": "0"},
                    "source_manifest_sha256": manifest_digest,
                    "captured_monotonic_ns": time.monotonic_ns(),
                }
                armed.release_when_ready(
                    workspace, snapshot, deadline=time.monotonic() + 5)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stderr.decode(errors="replace"))
                response = json.loads(stdout.decode("utf-8"))
                self.assertEqual(response, {
                    "schema": "caissa.v212.armed-no-inference-response.v02",
                    "nonce": nonce,
                    "request_sha256": hashlib.sha256(raw_request).hexdigest(),
                    "status": "released_no_inference",
                })

                # A semantically equivalent JSON byte stream must not inherit
                # the release token bound to the original wire bytes.
                altered_workspace = ipc.create_workspace(
                    request_object, parent=temp_root, with_release_fifo=True)
                altered_process = None
                try:
                    altered_process = subprocess.Popen(
                        [sys.executable, "-B", "-c", source,
                         str(altered_workspace.directory), unit, str(root),
                         str(cgroup_root)],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, env=env)
                    altered_process.stdin.write(raw_request + b" ")
                    altered_process.stdin.close()
                    altered_process.stdin = None
                    armed.release_when_ready(
                        altered_workspace, snapshot,
                        deadline=time.monotonic() + 5)
                    altered_stdout, _ = altered_process.communicate(timeout=5)
                    self.assertNotEqual(altered_process.returncode, 0)
                    self.assertEqual(altered_stdout, b"")
                finally:
                    if (altered_process is not None
                            and altered_process.poll() is None):
                        altered_process.kill()
                        altered_process.communicate(timeout=2)
                    ipc.cleanup_workspace(altered_workspace)
            finally:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.communicate(timeout=2)
                ipc.cleanup_workspace(workspace)


if __name__ == "__main__":
    unittest.main()
