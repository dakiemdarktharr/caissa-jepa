"""Small synthetic/source tests only: never executes the 200-trajectory audit."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import reversi_reference as ref


class SourceTests(unittest.TestCase):
    def test_git_blob_and_fresh_output(self):
        self.assertEqual(ref.blob_sha(b'test content\n'), 'd670460b4b4aece5915caf5c68d12f560a9fe3e4')
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'one.json'
            ref.write_new(file, {'test': 1})
            with self.assertRaises(FileExistsError):
                ref.write_new(file, {'test': 2})
            with self.assertRaises(ValueError), patch.object(ref, 'LIMIT_BYTES', 1):
                ref.write_new(Path(directory)/'two.json', {})
            with self.assertRaises(ValueError), patch.object(ref, 'fetch') as fetch:
                ref.acquire(directory)
            fetch.assert_not_called()

    def test_loader_requires_subprocess(self):
        if not sys.flags.isolated:
            with self.assertRaisesRegex(ValueError, 'isolated'):
                with ref.reference_namespace('missing'):
                    pass

    def test_wrapper_validation_without_loading(self):
        r = ref.Reference(None, 4)
        for state in (ref.ReferenceState((0,)*16, True), ref.ReferenceState((0,)*15),
                      ref.ReferenceState((False,)+(0,)*15), ref.ReferenceState((2,)+(0,)*15),
                      ref.ReferenceState([0]*16)):
            with self.assertRaises(ValueError):
                r.validate(state)
        with self.assertRaises(ValueError):
            ref.Reference(None, 8)
        with self.assertRaises(ValueError):
            r.transition(ref.ReferenceState((0,)*16), True)

    def test_acquisition_rejects_wrong_commit_before_raw_download(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'new'
            with patch.object(ref, 'fetch', return_value=b'{"sha":"wrong","tree":{"sha":"wrong"}}') as fetch:
                with self.assertRaises(ValueError):
                    ref.acquire(path)
                self.assertEqual(fetch.call_count, 1)
            self.assertFalse(path.exists())

    @unittest.skipUnless(ref.DEFAULT_SOURCE.exists(), 'Pinned originals not acquired; source-dependent smoke unavailable')
    def test_exact_source_and_manifest_tamper(self):
        manifest = ref.verify_source(ref.DEFAULT_SOURCE)
        self.assertEqual(len(manifest['files']), 5)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'original'
            shutil.copytree(ref.DEFAULT_SOURCE, target)
            board = target/'reversi/board.py'
            raw = board.read_bytes()
            board.write_bytes(raw+b'\n')
            with self.assertRaises(ValueError):
                ref.verify_source(target)
            board.write_bytes(raw)
            original = (target/'manifest.json').read_bytes()
            changed = copy.deepcopy(manifest)
            changed['files'][0]['path'] = '../LICENSE'
            (target/'manifest.json').write_text(json.dumps(changed), encoding='utf-8')
            with self.assertRaises(ValueError):
                ref.verify_source(target)
            (target/'manifest.json').write_bytes(original)
            (target/'reversi/__init__.py').write_text('raise RuntimeError("must not run")')
            with self.assertRaises(ValueError):
                ref.verify_source(target)

    @unittest.skipUnless(ref.DEFAULT_SOURCE.exists(), 'Pinned originals unavailable')
    def test_real_isolated_loader_smoke_no_trajectories(self):
        result = ref.isolated(ref.DEFAULT_SOURCE)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['status'], 'smoke_only')
        self.assertFalse(payload['trajectory_audit_executed'])
        self.assertEqual(payload['sizes']['6']['initial_actions'], [10, 17, 28, 35])
        self.assertFalse(any(name.startswith('reversi') for name in sys.modules))

    @unittest.skipUnless(ref.DEFAULT_SOURCE.exists(), 'Pinned originals unavailable')
    def test_fixture_comparator_and_sentinel_failure(self):
        # Only two initial synthetic states and explicit wrapper fixtures; no trajectories.
        code = '''
import sys
sys.path.insert(0, sys.argv[1])
from tools import reversi_reference as r
from two_player.games import BoardGame
with r.reference_namespace(sys.argv[2]) as cls:
    for n in (4,6):
        reference=r.Reference(cls,n)
        counts=r.counters()
        r.compare_state(reference,BoardGame('test',n,n,k=0,reversi=True),reference.initial(),counts,lambda:None)
        assert counts['player_states']==2 and counts['legal_branches']==8
        rows=dict(r.fixtures(reference))
        assert len(rows)==14
        passed, flips=reference.transition(rows['forced_pass'],64)
        assert passed.board==rows['forced_pass'].board and passed.player==1 and flips==()
        assert reference.inspect(rows['forced_pass_role_swap'])[0]==(64,)
        for name in ('full_black','full_white','full_draw','terminal_empty'):
            assert reference.inspect(rows[name])[0]==()
        before=cls.put_disc
        calls=[]
        def fail(*a,**kw):
            calls.append(1)
            raise AssertionError('illegal original mutation')
        cls.put_disc=fail
        try:
            try: reference.transition(rows['initial'],0)
            except ValueError: pass
            else: raise AssertionError('illegal action accepted')
            assert not calls
        finally: cls.put_disc=before
try:
    with r.reference_namespace(sys.argv[2]):
        sys.modules['reversi.BitBoardMethods'].unexpected()
except RuntimeError: pass
else: raise AssertionError('sentinel access did not fail')
assert not any(k=='reversi' or k.startswith('reversi.') for k in sys.modules)
'''
        result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(ref.ROOT), str(ref.DEFAULT_SOURCE)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(ref.DEFAULT_SOURCE.exists(), 'Pinned originals unavailable')
    def test_watchdog_and_worker_crash_preserve_failure(self):
        for failure in ('timeout', 'crash'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)/'audit'
                with patch.object(ref.subprocess, 'run') as run:
                    if failure == 'timeout':
                        run.side_effect = subprocess.TimeoutExpired('synthetic', 120)
                        with self.assertRaises(subprocess.TimeoutExpired):
                            ref.isolated(ref.DEFAULT_SOURCE, output)
                    else:
                        run.return_value = subprocess.CompletedProcess([], 3, '', 'synthetic worker failure')
                        result = ref.isolated(ref.DEFAULT_SOURCE, output)
                        self.assertEqual(result.returncode, 3)
                receipt = json.loads((output/'receipt.json').read_text())
                self.assertEqual(receipt['status'], 'failed')
                run_receipt = json.loads((output/'run.json').read_text())
                self.assertEqual(run_receipt['status'], 'failed')
                self.assertEqual(run_receipt['receipt_sha256'], ref.sha((output/'receipt.json').read_bytes()))
                with patch.object(ref.subprocess, 'run') as run:
                    with self.assertRaises(FileExistsError):
                        ref.isolated(ref.DEFAULT_SOURCE, output)
                    run.assert_not_called()

    @unittest.skipUnless(ref.DEFAULT_SOURCE.exists(), 'Pinned originals unavailable')
    def test_parent_does_not_accept_early_success_followed_by_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'audit'
            def crash_after_write(*args, **kwargs):
                ref.write_new(output/'receipt.json', {'status': 'passed'})
                return subprocess.CompletedProcess([], 3, '', 'synthetic crash after receipt')
            with patch.object(ref.subprocess, 'run', side_effect=crash_after_write):
                result = ref.isolated(ref.DEFAULT_SOURCE, output)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads((output/'run.json').read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
