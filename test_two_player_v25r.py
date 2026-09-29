"""Engineering-only regressions; no datasets, checkpoints or research fits."""
import ctypes
from dataclasses import asdict
import gc
import os
from pathlib import Path
from threading import Thread
import unittest
from unittest.mock import patch

from two_player_v25 import runtime as frozen
from two_player_v25 import report as frozen_report
from two_player_v25r import bindings, monitor, runtime, report


class BindingsTests(unittest.TestCase):
    def assert_original(self):
        self.assertIs(frozen.process_peak_rss, bindings._ORIGINAL_MONITOR)
        self.assertIs(frozen.runtime_source, bindings._ORIGINAL_SOURCE)

    def test_only_two_globals_changed_and_originals_restored(self):
        before = dict(vars(frozen))
        configs = [asdict(c) for c in frozen.configurations()]
        with bindings.repaired_bindings():
            self.assertEqual(set(vars(frozen)), set(before))
            changed = {k for k in before if getattr(frozen, k) is not before[k]}
            self.assertEqual(changed, {'runtime_source', 'process_peak_rss'})
            self.assertIs(frozen.process_peak_rss, monitor.process_peak_rss)
            self.assertEqual([asdict(c) for c in frozen.configurations()], configs)
            self.assertEqual((frozen.CELL_LIMIT, frozen.TOTAL_LIMIT, frozen.BYTE_LIMIT, frozen.RSS_LIMIT),
                             (600., 25200., 3_000_000_000, 1_000_000_000))
        self.assert_original()
        self.assertTrue(all(getattr(frozen, k) is value for k, value in before.items()))

    def test_restoration_on_exception_and_baseexception(self):
        for kind in (ValueError, KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind), self.assertRaises(kind):
                with bindings.repaired_bindings():
                    raise kind('Synthetic interruption')
            self.assert_original()
        # The lock must also have been released, not merely the globals reset.
        with bindings.repaired_bindings():
            self.assertIs(frozen.process_peak_rss, monitor.process_peak_rss)
        self.assert_original()

    def test_nested_and_overlapping_contexts_rejected_without_disturbing_outer(self):
        failures = []
        def overlap():
            try:
                with bindings.repaired_bindings():
                    failures.append('incorrectly entered')
            except RuntimeError as exc:
                failures.append(str(exc))
        with bindings.repaired_bindings():
            with self.assertRaisesRegex(RuntimeError, 'non-reentrant'):
                with bindings.repaired_bindings(): pass
            thread = Thread(target=overlap)
            thread.start(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(failures), 1)
            self.assertIn('non-reentrant', failures[0])
            self.assertIs(frozen.process_peak_rss, monitor.process_peak_rss)
            self.assertIs(frozen.runtime_source, bindings.runtime_source)
        self.assert_original()

    def test_unexpected_existing_binding_not_overwritten(self):
        foreign = lambda: 123
        with patch.object(frozen, 'process_peak_rss', foreign):
            with self.assertRaisesRegex(RuntimeError, 'unexpected'):
                with bindings.repaired_bindings(): pass
            self.assertIs(frozen.process_peak_rss, foreign)
            self.assertIs(frozen.runtime_source, bindings._ORIGINAL_SOURCE)
        with bindings.repaired_bindings(): pass
        self.assert_original()

    def test_source_is_strict_superset_and_repair_changes_are_detected(self):
        old = bindings._ORIGINAL_SOURCE()
        augmented = bindings.runtime_source()
        self.assertEqual({k: augmented[k] for k in old}, old)
        wanted = {p.relative_to(bindings.ROOT).as_posix() for p in Path(bindings.__file__).parent.rglob('*.py')}
        wanted.add('docs/V25_RUNTIME_AMENDMENT.md')
        self.assertEqual(set(augmented)-set(old), wanted)
        self.assertTrue(all(len(h) == 64 for h in augmented.values()))
        target = Path(monitor.__file__).resolve()
        original_read = Path.read_bytes
        def changed(path):
            value = original_read(path)
            return value+b'\n# synthetic source mutation\n' if path.resolve() == target else value
        with patch.object(Path, 'read_bytes', changed):
            modified = bindings.runtime_source()
        differences = {k for k in augmented if augmented[k] != modified[k]}
        self.assertEqual(differences, {'two_player_v25r/monitor.py'})
        config = frozen.configurations()[0]
        a = frozen.identity(config, {'dataset_fingerprint': 'synthetic'}, 'groups', old)
        b = frozen.identity(config, {'dataset_fingerprint': 'synthetic'}, 'groups', augmented)
        self.assertEqual({k: v for k, v in a.items() if k != 'source'},
                         {k: v for k, v in b.items() if k != 'source'})

    def test_runtime_and_report_delegate_with_identical_bindings_and_restore(self):
        observed = []
        def run(*args):
            observed.append(('run', args, frozen.runtime_source(), frozen.process_peak_rss))
            return {'status': 'synthetic'}
        def verify(*args):
            observed.append(('report', args, frozen.runtime_source(), frozen.process_peak_rss))
            return {'status': 'synthetic'}
        arguments = (object(), object(), object())
        with patch.object(frozen, 'run_grid', run), patch.object(frozen_report, 'summarize_grid', verify):
            self.assertEqual(runtime.run_grid(*arguments), {'status': 'synthetic'})
            self.assert_original()
            self.assertEqual(report.summarize_grid(arguments[2]), {'status': 'synthetic'})
            self.assert_original()
        self.assertEqual(observed[0][1], arguments)
        self.assertEqual(observed[1][1], (arguments[2],))
        self.assertEqual(observed[0][2], observed[1][2])
        self.assertIs(observed[0][3], monitor.process_peak_rss)
        self.assertIs(observed[1][3], monitor.process_peak_rss)
        self.assertIs(report.markdown, frozen_report.markdown)
        for wrapper, module, name, args in ((runtime.run_grid, frozen, 'run_grid', arguments),
                                          (report.summarize_grid, frozen_report, 'summarize_grid', arguments[2:])):
            with patch.object(module, name, side_effect=KeyboardInterrupt('Synthetic delegated failure')):
                with self.assertRaises(KeyboardInterrupt): wrapper(*args)
            self.assert_original()


@unittest.skipUnless(os.name == 'nt', 'Windows PROCESS_MEMORY_COUNTERS contract')
class MonitorTests(unittest.TestCase):
    def test_structure_layout_and_real_bound_function_signatures(self):
        size = ctypes.sizeof(ctypes.c_size_t)
        self.assertEqual(ctypes.sizeof(monitor.Counters), 8+8*size)
        self.assertEqual(monitor.Counters.cb.offset, 0)
        self.assertEqual(monitor.Counters.PageFaultCount.offset, 4)
        names = ['PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
                 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage']
        for i, name in enumerate(names):
            self.assertEqual(getattr(monitor.Counters, name).offset, 8+i*size)
        self.assertIs(monitor.COUNTERS_POINTER, ctypes.POINTER(monitor.Counters))
        self.assertEqual(monitor._current_process.argtypes, [])
        self.assertEqual(monitor._memory_info.argtypes,
                         [ctypes.wintypes.HANDLE, monitor.COUNTERS_POINTER, ctypes.wintypes.DWORD])
        self.assertIs(monitor._memory_info.restype, ctypes.wintypes.BOOL)

    def test_ten_thousand_measurements_do_not_retain_new_types_or_reset_peak(self):
        previous = monitor.process_peak_rss()
        self.assertIs(type(previous), int)
        self.assertGreater(previous, 0)
        before = len(ctypes._pointer_type_cache)
        pointer = monitor.COUNTERS_POINTER
        function = monitor._memory_info
        for _ in range(10000):
            current = monitor.process_peak_rss()
            self.assertIs(type(current), int)
            self.assertGreaterEqual(current, previous)
            previous = current
        gc.collect()
        self.assertEqual(len(ctypes._pointer_type_cache), before)
        self.assertIs(monitor.COUNTERS_POINTER, pointer)
        self.assertIs(monitor._memory_info, function)

    def test_peak_field_not_current_working_set_and_api_failure_propagates(self):
        def fake(handle, memory, size):
            self.assertEqual(handle, 19)
            self.assertEqual(memory._obj.cb, ctypes.sizeof(monitor.Counters))
            self.assertEqual(size, ctypes.sizeof(monitor.Counters))
            memory._obj.PeakWorkingSetSize = 12345678
            memory._obj.WorkingSetSize = 5
            return True
        with patch.object(monitor, '_current_process', return_value=19), patch.object(monitor, '_memory_info', fake):
            self.assertEqual(monitor.process_peak_rss(), 12345678)
        with patch.object(monitor, '_memory_info', return_value=False), patch.object(ctypes, 'get_last_error', return_value=5):
            with self.assertRaisesRegex(OSError, 'GetProcessMemoryInfo failed'):
                monitor.process_peak_rss()


if __name__ == '__main__': unittest.main()
