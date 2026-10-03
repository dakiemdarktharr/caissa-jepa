import json
import os
import stat
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from two_player import v212_worker_ipc as ipc
from two_player.v212_worker_ipc import (
    MAX_IPC_BYTES,
    WorkerIPCError,
    create_workspace,
    read_response,
)


class WorkerIPCTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.parent = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _workspace(self, *, max_bytes=MAX_IPC_BYTES):
        return create_workspace({"request_schema": "test.v1", "root": 3},
                                parent=self.parent, max_bytes=max_bytes)

    def _write_response(self, workspace, payload: bytes):
        workspace.response_path.write_bytes(payload)

    def test_creates_private_directory_and_exclusive_private_files(self):
        workspace = self._workspace()
        self.assertEqual(stat.S_IMODE(workspace.directory.stat().st_mode), 0o700)
        for path in (workspace.request_path, workspace.response_path):
            info = path.stat()
            self.assertTrue(stat.S_ISREG(info.st_mode))
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
            self.assertEqual(info.st_nlink, 1)
            self.assertEqual(info.st_uid, os.getuid())
        self.assertEqual(json.loads(workspace.request_path.read_text()),
                         {"request_schema": "test.v1", "root": 3})
        self.assertEqual(workspace.response_path.stat().st_size, 0)

    def test_cleanup_removes_only_the_original_private_workspace(self):
        workspace = self._workspace()
        directory = workspace.directory
        ipc.cleanup_workspace(workspace)
        self.assertFalse(directory.exists())

    def test_cleanup_fails_closed_on_replaced_request_file(self):
        workspace = self._workspace()
        original = workspace.request_path.read_bytes()
        workspace.request_path.unlink()
        workspace.request_path.write_bytes(original)
        with self.assertRaises(WorkerIPCError):
            ipc.cleanup_workspace(workspace)
        self.assertTrue(workspace.directory.exists())
        self.assertTrue(workspace.response_path.exists())

    def test_optional_release_fifo_is_private_and_removed_during_cleanup(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        self.assertEqual(workspace.release_path,
                         workspace.directory / ipc.RELEASE_NAME)
        info = os.lstat(workspace.release_path)
        self.assertTrue(stat.S_ISFIFO(info.st_mode))
        self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
        self.assertEqual(info.st_uid, os.getuid())
        self.assertEqual(info.st_nlink, 1)
        ipc.cleanup_workspace(workspace)
        self.assertFalse(workspace.directory.exists())

    def test_release_writer_returns_none_until_worker_opens_fifo(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        opening = threading.Event()
        opened = threading.Event()
        received = []
        failures = []

        def worker_barrier():
            try:
                opening.set()
                reader = os.open(workspace.release_path, os.O_RDONLY)
                opened.set()
                received.append(os.read(reader, ipc.MAX_RELEASE_BYTES))
                os.close(reader)
            except BaseException as exc:
                failures.append(exc)

        worker = threading.Thread(target=worker_barrier, daemon=True)
        worker.start()
        self.assertTrue(opening.wait(1))
        writer = None
        try:
            deadline = time.monotonic() + 1
            while writer is None and time.monotonic() < deadline:
                writer = ipc.open_release_writer(workspace)
                if writer is None:
                    time.sleep(0.001)
            self.assertIsNotNone(writer)
            self.assertTrue(opened.wait(1))
            payload = b'{"release_schema":"test.v1"}'
            ipc.write_release(workspace, writer, payload)
            worker.join(timeout=1)
            self.assertFalse(worker.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(received, [payload])
            with self.assertRaisesRegex(WorkerIPCError, "one-shot"):
                ipc.open_release_writer(workspace)
            with self.assertRaisesRegex(WorkerIPCError, "one-shot"):
                ipc.write_release(workspace, writer, payload)
        finally:
            if writer is not None and workspace.release_writer_state is not None \
                    and not workspace.release_writer_state.consumed:
                os.close(writer)
            worker.join(timeout=1)

    def test_release_open_rejects_fifo_substitution(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        workspace.release_path.unlink()
        os.mkfifo(workspace.release_path, 0o600)
        with self.assertRaisesRegex(WorkerIPCError, "identity changed"):
            ipc.open_release_writer(workspace)

    def test_concurrent_release_writer_opens_are_one_shot(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        reader = os.open(workspace.release_path,
                         os.O_RDONLY | os.O_NONBLOCK)
        start = threading.Barrier(3)
        opened = []
        rejected = []

        def try_open():
            start.wait()
            try:
                opened.append(ipc.open_release_writer(workspace))
            except WorkerIPCError as exc:
                rejected.append(str(exc))

        threads = [threading.Thread(target=try_open) for _ in range(2)]
        for thread in threads:
            thread.start()
        start.wait()
        for thread in threads:
            thread.join(timeout=1)
        try:
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(len(opened), 1)
            self.assertEqual(len(rejected), 1)
            self.assertIn("one-shot", rejected[0])
        finally:
            for fd in opened:
                os.close(fd)
            os.close(reader)

    def test_release_cleanup_rejects_fifo_substitution(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        workspace.release_path.unlink()
        os.mkfifo(workspace.release_path, 0o600)
        with self.assertRaisesRegex(WorkerIPCError, "identity changed"):
            ipc.cleanup_workspace(workspace)
        self.assertTrue(workspace.request_path.exists())
        self.assertTrue(workspace.response_path.exists())

    def test_release_writer_rejects_oversize_and_partial_write(self):
        workspace = create_workspace({"request_schema": "test.v1"},
                                     parent=self.parent,
                                     with_release_fifo=True)
        reader = os.open(workspace.release_path,
                         os.O_RDONLY | os.O_NONBLOCK)
        writer = ipc.open_release_writer(workspace)
        try:
            with self.assertRaisesRegex(WorkerIPCError, "1..4096"):
                ipc.write_release(workspace, writer, b"x" * 4097)
        finally:
            os.close(reader)

        other = create_workspace({"request_schema": "test.v1"},
                                 parent=self.parent,
                                 with_release_fifo=True)
        other_reader = os.open(other.release_path, os.O_RDONLY | os.O_NONBLOCK)
        other_writer = ipc.open_release_writer(other)
        try:
            with patch.object(ipc.os, "write", return_value=1), \
                    self.assertRaisesRegex(WorkerIPCError, "partial"):
                ipc.write_release(other, other_writer, b"{}")
            with self.assertRaisesRegex(WorkerIPCError, "one-shot"):
                ipc.write_release(other, other_writer, b"{}")
        finally:
            os.close(other_reader)

    def test_request_writer_retries_short_writes_and_rejects_zero_progress(self):
        writes = []

        def short_write(_fd, payload):
            writes.append(payload)
            return min(2, len(payload))

        with patch.object(ipc.os, "write", side_effect=short_write):
            ipc._write_all(123, b"abcdef")
        self.assertEqual(writes, [b"abcdef", b"cdef", b"ef"])
        with patch.object(ipc.os, "write", return_value=0), \
                self.assertRaisesRegex(WorkerIPCError, "short IPC file write"):
            ipc._write_all(123, b"x")

    def test_reads_one_bounded_json_object(self):
        workspace = self._workspace()
        payload = b'{"response_schema":"worker.v1","action":3}'
        self._write_response(workspace, payload)
        self.assertEqual(read_response(workspace),
                         {"response_schema": "worker.v1", "action": 3})

    def test_request_rejects_nonfinite_and_oversized_json(self):
        with self.assertRaisesRegex(WorkerIPCError, "finite JSON"):
            create_workspace({"number": float("nan")}, parent=self.parent)
        with self.assertRaisesRegex(WorkerIPCError, "request exceeds"):
            create_workspace({"value": "x" * 64}, parent=self.parent,
                             max_bytes=16)
        with self.assertRaises(ValueError):
            create_workspace({}, parent=self.parent, max_bytes=MAX_IPC_BYTES + 1)

    def test_creation_rejects_a_nonprivate_nontsticky_parent(self):
        self.parent.chmod(0o777)
        try:
            with self.assertRaisesRegex(WorkerIPCError, "IPC parent"):
                self._workspace()
            self.assertEqual(list(self.parent.glob("caissa-v212-*")), [])
        finally:
            self.parent.chmod(0o700)

    def test_creation_rejects_an_unsafe_parent_ancestor(self):
        child = self.parent / "private-child"
        child.mkdir(mode=0o700)
        self.parent.chmod(0o777)
        try:
            with self.assertRaisesRegex(WorkerIPCError, "ancestors"):
                create_workspace({"request_schema": "test.v1"}, parent=child)
            self.assertEqual(list(child.iterdir()), [])
        finally:
            self.parent.chmod(0o700)

    def test_creation_cleans_partial_files_on_interrupt(self):
        with patch.object(ipc, "_write_all", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self._workspace()
        self.assertEqual(list(self.parent.glob("caissa-v212-*")), [])

    def test_creation_reports_cleanup_failure_without_masking_primary_error(self):
        original_create = ipc._create_file
        calls = 0

        def fail_second_create(directory, name, payload=b""):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("response setup failed")
            return original_create(directory, name, payload)

        original_unlink = Path.unlink

        def fail_request_cleanup(path, *args, **kwargs):
            if path.name == ipc.REQUEST_NAME:
                raise OSError("cleanup failed")
            return original_unlink(path, *args, **kwargs)

        with patch.object(ipc, "_create_file", side_effect=fail_second_create), \
                patch.object(Path, "unlink", fail_request_cleanup):
            with self.assertRaisesRegex(WorkerIPCError, "cleanup incomplete") as caught:
                self._workspace()
        self.assertIsInstance(caught.exception.__cause__, OSError)
        leftovers = list(self.parent.glob("caissa-v212-*"))
        self.assertEqual(len(leftovers), 1)
        original_unlink(leftovers[0] / ipc.REQUEST_NAME)
        leftovers[0].rmdir()

    def test_response_rejects_oversize_duplicate_keys_and_nonfinite_values(self):
        workspace = self._workspace()
        with self.subTest("oversize"):
            self._write_response(workspace, b" " * (MAX_IPC_BYTES + 1))
            with self.assertRaisesRegex(WorkerIPCError, "exceeds"):
                read_response(workspace)
        with self.subTest("duplicate"):
            self._write_response(workspace, b'{"a":1,"nested":{"b":2,"b":3}}')
            with self.assertRaisesRegex(WorkerIPCError, "duplicate JSON key"):
                read_response(workspace)
        for label, payload, message in (
            ("nonfinite-token", b'{"value":NaN}', "non-finite"),
            ("float-overflow", b'{"value":1e9999}', "overflows"),
        ):
            with self.subTest(label):
                self._write_response(workspace, payload)
                with self.assertRaisesRegex(WorkerIPCError, message):
                    read_response(workspace)

    def test_response_requires_valid_utf8_and_a_top_level_object(self):
        workspace = self._workspace()
        for payload in (b"\xff", b"[]", b"{} trailing", b""):
            with self.subTest(payload=payload):
                self._write_response(workspace, payload)
                with self.assertRaises(WorkerIPCError):
                    read_response(workspace)

    def test_response_rejects_symlink_or_replaced_inode(self):
        workspace = self._workspace()
        target = workspace.directory / "elsewhere"
        target.write_text('{"action":3}', encoding="utf-8")
        workspace.response_path.unlink()
        workspace.response_path.symlink_to(target)
        with self.assertRaisesRegex(WorkerIPCError, "regular file"):
            read_response(workspace)

        workspace.response_path.unlink()
        workspace.response_path.write_text('{"action":3}', encoding="utf-8")
        workspace.response_path.chmod(0o600)
        with self.assertRaisesRegex(WorkerIPCError, "identity changed"):
            read_response(workspace)

    def test_response_rejects_hard_link_and_private_directory_replacement(self):
        workspace = self._workspace()
        other = workspace.directory / "other"
        os.link(workspace.response_path, other)
        with self.assertRaisesRegex(WorkerIPCError, "exactly one link"):
            read_response(workspace)

        other.unlink()
        old = workspace.directory.with_name(workspace.directory.name + "-old")
        workspace.directory.rename(old)
        workspace.directory.mkdir(mode=0o700)
        with self.assertRaisesRegex(WorkerIPCError, "directory identity changed"):
            read_response(workspace)

    def test_response_enforces_caller_parse_limit_below_global_limit(self):
        workspace = self._workspace()
        self._write_response(workspace, b'{"action":"' + b"x" * 32 + b'"}')
        with self.assertRaisesRegex(WorkerIPCError, "exceeds"):
            read_response(workspace, max_bytes=16)


if __name__ == "__main__":
    unittest.main()
