import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from tools.v212_runtime_observation import (
    _file_observation,
    _canonical_sha256,
    parse_proc_maps,
)


class RuntimeObservationTests(unittest.TestCase):
    def test_parse_maps_groups_executable_file_objects_and_keeps_spaced_paths(self):
        maps = "\n".join((
            "7f0000000000-7f0000001000 r-xp 00000000 08:01 42 /usr/lib/lib example.so",
            "7f0000001000-7f0000002000 r-xp 00001000 08:01 42 /usr/lib/lib example.so",
            "7f0000002000-7f0000003000 rw-p 00002000 08:01 43 /usr/lib/not-executable.so",
            "7f0000003000-7f0000004000 r-xp 00000000 00:00 0 [vdso]",
            "7f0000004000-7f0000005000 r-xp 00000000 08:01 44 /tmp/gone.so (deleted)",
        ))
        rows = parse_proc_maps(maps)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["path_as_mapped"], "/usr/lib/lib example.so")
        self.assertEqual(rows[0]["executable_mapping_count"], 2)
        self.assertEqual(rows[1]["lookup_path"], "/tmp/gone.so")
        self.assertTrue(rows[1]["deleted_suffix"])
        self.assertEqual(parse_proc_maps("\n".join(reversed(maps.splitlines()))), rows)
        self.assertEqual(_canonical_sha256(rows), _canonical_sha256(
            parse_proc_maps("\n".join(reversed(maps.splitlines())))))
        shifted = maps.replace("7f0000000000-7f0000001000", "7f0000000100-7f0000001100")
        shifted_rows = parse_proc_maps(shifted)
        self.assertNotEqual(shifted_rows, rows)
        self.assertNotEqual(_canonical_sha256(shifted_rows), _canonical_sha256(rows))

    def test_hashes_file_only_when_mapped_device_inode_matches(self):
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(b"runtime-object-bytes")
            stream.flush()
            info = os.stat(stream.name)
            report = _file_observation(
                stream.name,
                expected_device=(os.major(info.st_dev), os.minor(info.st_dev)),
                expected_inode=info.st_ino,
            )
            self.assertEqual(report["status"], "mapped_identity_hash_match")
            self.assertEqual(report["sha256"], hashlib.sha256(b"runtime-object-bytes").hexdigest())

            mismatch = _file_observation(
                stream.name,
                expected_device=(os.major(info.st_dev), os.minor(info.st_dev)),
                expected_inode=info.st_ino + 1,
            )
            self.assertEqual(mismatch["status"], "mapped_identity_mismatch")
            self.assertIsNone(mismatch["sha256"])

    def test_execution_bytes_are_explicitly_not_attested_by_contract(self):
        source = (Path(__file__).parents[1] / "tools/v212_runtime_observation.py").read_text(
            encoding="utf-8")
        self.assertIn('"identity_status": "observational_only"', source)
        self.assertIn('"execution_bytes_verified": False', source)
        self.assertIn("do not prove the bytes already executed", source)


if __name__ == "__main__":
    unittest.main()
