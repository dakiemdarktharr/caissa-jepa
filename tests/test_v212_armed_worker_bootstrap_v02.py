import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from two_player import v212_armed_worker_bootstrap_v02 as bootstrap


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


if __name__ == "__main__":
    unittest.main()
