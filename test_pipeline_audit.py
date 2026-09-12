import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import test_model_arena as fixtures
from tools.audit_pipeline_dataset import audit


class PipelineAuditTests(unittest.TestCase):
    def test_clean_fixture_is_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = fixtures.ModelArenaTests().build_dataset(Path(folder))
            before = {p: p.read_bytes() for p in dataset.rglob('*') if p.is_file()}
            with contextlib.redirect_stdout(io.StringIO()):
                result = audit(dataset)
            self.assertEqual(result['manifest_mismatches'], {})
            self.assertEqual(result['duplicate_rows'], 0)
            self.assertNotIn('None', result['result_counts'])
            self.assertEqual(before, {p: p.read_bytes() for p in dataset.rglob('*') if p.is_file()})

    def test_stale_counters_are_detected_when_writer_misses_them(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = fixtures.ModelArenaTests().build_dataset(Path(folder))
            path = dataset / 'dataset_manifest.json'
            manifest = json.loads(path.read_text())
            manifest['games'] += 1
            path.write_text(json.dumps(manifest), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                result = audit(dataset)
            self.assertIn('games', result['manifest_mismatches'])
            self.assertFalse(result['existing_writer_requests_reconciliation'])


if __name__ == '__main__':
    unittest.main()
