"""Independent V2.3 runtime checks; synthetic fixtures, no research fitting."""
from contextlib import ExitStack
from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from test_v21_runtime import arrays_fixture, forks_fixture
from two_player_v22 import runtime as historical
from two_player_v23_diagnostic import runtime


class V23RuntimeTests(unittest.TestCase):
    def tiny_cell(self, stack, epochs=1):
        """Keep actual save/load and 66-step counters; mock every optimizer call."""
        forks = forks_fixture()
        batch = arrays_fixture(forks)
        batch['value_labelled'] = batch['valid'].copy()
        batch['policy_labelled'] = batch['legal'].any(-1)
        train = {'forks': forks, 'manifest': {'dataset_fingerprint': 'fixture'}}
        source = {'fixture': 'source'}
        config = runtime.Config(variant='direct', seed=17, jepa_weight=1.)
        indices = np.resize(np.arange(len(forks)), 8352)
        def no_fit(model, selected):
            model.step += 1
            return {'value_count': int(selected['value_labelled'].sum()), 'loss': 1.}
        for name, replacement in {
            'check_train': lambda train: None,
            'runtime_source': lambda: source,
            'epoch_indices': lambda *args: (indices, {'samples': 8352, 'index_sha256': 'fixture'}),
            'augmentation_plan': lambda *args: (np.zeros(8352, dtype=int), {'fixture': True}),
            'augment': lambda batch, *args: batch,
            'snapshot_metrics': lambda *args: {'S': 1., 'collapse': []},
        }.items():
            stack.enter_context(patch.object(runtime, name, replacement))
        stack.enter_context(patch.object(runtime, 'EPOCHS', epochs))
        stack.enter_context(patch.object(runtime, 'SNAPSHOTS', (0, epochs)))
        stack.enter_context(patch.object(runtime.Model, 'update', no_fit))
        return config, train, batch, source

    def test_frozen_grid_complete_with_equal_baseline_capacity_and_no_rate_search(self):
        configs = runtime.configurations()
        observed = {(c.variant, c.hidden, c.latent, c.seed) for c in configs}
        expected = {(v, h, z, s) for v in ('direct', 'value-dynamics', 'raw-jepa')
                    for h, z in ((64, 32), (128, 64)) for s in (17, 29, 43)}
        self.assertEqual(observed, expected)
        self.assertEqual(len(configs), 18)
        self.assertEqual(len({runtime.run_id(c) for c in configs}), 18)
        for c in configs:
            self.assertEqual((c.learning_rate, c.batch_size, c.projection, c.ema), (.001, 128, 16, .99))
            self.assertEqual(c.jepa_weight, .1 if c.variant == 'raw-jepa' else 1.)
        self.assertEqual(runtime.SNAPSHOTS, (0, 40, 80, 160))

    def test_sampling_exactly_replays_historical_addressed_schedule_and_rejects_other_split(self):
        forks = forks_fixture()
        for seed in (17, 29, 43):
            for epoch in (0, 39, 79, 159):
                current, receipt = runtime.epoch_indices(forks, seed, epoch)
                previous, original = historical.epoch_indices(forks, seed, epoch)
                np.testing.assert_array_equal(current, previous)
                self.assertEqual(receipt, original)
        invalid = [dict(f) for f in forks]
        invalid[0]['split'] = 'development'
        with self.assertRaises(ValueError):
            runtime.epoch_indices(invalid, 17, 0)

    def test_source_inventory_binds_helper_reference_and_method(self):
        source = runtime.runtime_source()
        for name in ('tools/diagnose_v21_value_alignment.py', 'docs/METHOD_V23_DIAGNOSTIC.md',
                     'docs/validation/V23_EPOCH40_REFERENCES.json', 'two_player_v22/model.py',
                     'two_player_v23_diagnostic/runtime.py', 'two_player_v23_diagnostic/metrics.py'):
            self.assertEqual(len(source[name]), 64)

    def test_tensor_receipt_covers_online_ema_and_both_adam_moments(self):
        model = runtime.Model(runtime.Config())
        before = runtime.tensor_hashes(model)
        self.assertEqual(len(before), 59)
        for prefix, group in (('p_', model.params), ('t_', model.target), ('m_', model.m), ('v_', model.v)):
            key = next(iter(group))
            group[key].flat[0] += .1
            changed = runtime.tensor_hashes(model)
            self.assertEqual({k for k in before if before[k] != changed[k]}, {prefix+key})
            before = changed

    def test_atomic_receipt_failure_preserves_prior_valid_bytes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/'receipt.json'
            runtime.atomic_json(path, {'status': 'active', 'elapsed': 12.})
            old = path.read_bytes()
            with self.assertRaises(ValueError):
                runtime.atomic_json(path, {'elapsed': float('nan')})
            self.assertEqual(path.read_bytes(), old)
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_separate_snapshots_verified_all_tensors_and_fresh_only(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            config, train, batch, source = self.tiny_cell(stack)
            path = Path(directory)/'cell'
            receipt = runtime.train_run(config, train, batch, path, source, {}, directory)
            self.assertEqual([(r['epoch'], r['step']) for r in receipt['snapshots']], [(0, 0), (1, 66)])
            for row in receipt['snapshots']:
                self.assertEqual(runtime.sha(path/row['checkpoint']), row['checkpoint_sha256'])
                restored = runtime.Model.load(path/row['checkpoint'], config, receipt['identity'])
                self.assertEqual(len(runtime.tensor_hashes(restored)), 59)
                self.assertEqual((restored.epoch, restored.step), (row['epoch'], row['step']))
            self.assertEqual(json.loads((path/'budget.json').read_text())['status'], 'complete')
            with self.assertRaises(FileExistsError):
                runtime.train_run(config, train, batch, path, source, {}, directory)

    def test_checkpoint_verification_rejects_altered_ema_before_metrics_or_updates(self):
        real_load = runtime.Model.load
        def altered(*args, **kwargs):
            restored = real_load(*args, **kwargs)
            restored.target['vw'].flat[0] += 1.
            return restored
        with TemporaryDirectory() as directory, ExitStack() as stack:
            config, train, batch, source = self.tiny_cell(stack)
            stack.enter_context(patch.object(runtime.Model, 'load', side_effect=altered))
            metric = stack.enter_context(patch.object(runtime, 'snapshot_metrics'))
            path = Path(directory)/'cell'
            with self.assertRaisesRegex(ValueError, 'Saved online/EMA/Adam'):
                runtime.train_run(config, train, batch, path, source, {}, directory)
            metric.assert_not_called()
            self.assertEqual(json.loads((path/'budget.json').read_text())['status'], 'failed')

    def test_diagnostic_mutation_is_detected_and_failed_work_journaled(self):
        def bad_metric(model, *args):
            model.m['vw'].flat[0] = 1.
            return {'S': 1., 'collapse': []}
        with TemporaryDirectory() as directory, ExitStack() as stack:
            config, train, batch, source = self.tiny_cell(stack)
            stack.enter_context(patch.object(runtime, 'snapshot_metrics', bad_metric))
            path = Path(directory)/'cell'
            with self.assertRaisesRegex(ValueError, 'mutated model'):
                runtime.train_run(config, train, batch, path, source, {}, directory)
            journal = json.loads((path/'budget.json').read_text())
            self.assertEqual(journal['status'], 'failed')
            self.assertGreater(journal['total_seconds'], 0.)

    def test_epoch40_replay_mismatch_stops_before_snapshot_interpretation(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            config, train, batch, source = self.tiny_cell(stack, epochs=40)
            reference = {(config.variant, config.seed): {'config': asdict(config), 'epoch': 40,
                         'step': 2640, 'array_hashes': runtime.tensor_hashes(runtime.Model(config))}}
            reference[(config.variant, config.seed)]['array_hashes']['t_vw'] = 'tampered'
            metric = stack.enter_context(patch.object(runtime, 'snapshot_metrics', return_value={'S': 1., 'collapse': []}))
            path = Path(directory)/'cell'
            with self.assertRaisesRegex(ValueError, 'epoch40 replay differs'):
                runtime.train_run(config, train, batch, path, source, reference, directory)
            self.assertEqual(metric.call_count, 1)  # epoch0 only
            history = json.loads((path/'history.json').read_text())
            self.assertEqual((history[-1]['epoch'], history[-1]['step']), (40, 2640))
            self.assertEqual(json.loads((path/'budget.json').read_text())['status'], 'failed')

    def test_overrun_during_diagnostics_and_artifact_cap_fail_closed(self):
        for mode in ('time', 'bytes'):
            with self.subTest(mode=mode), TemporaryDirectory() as directory, ExitStack() as stack:
                config, train, batch, source = self.tiny_cell(stack)
                clock = [100.]
                stack.enter_context(patch.object(runtime.time, 'perf_counter', side_effect=lambda: clock[0]))
                if mode == 'time':
                    def overrun(*args):
                        clock[0] += runtime.CELL_LIMIT+1
                        return {'S': 1., 'collapse': []}
                    stack.enter_context(patch.object(runtime, 'snapshot_metrics', overrun))
                else:
                    stack.enter_context(patch.object(runtime, 'artifact_bytes', return_value=runtime.BYTE_LIMIT))
                path = Path(directory)/'cell'
                with self.assertRaises((TimeoutError, RuntimeError)):
                    runtime.train_run(config, train, batch, path, source, {}, directory)
                journal = json.loads((path/'budget.json').read_text())
                self.assertEqual(journal['status'], 'failed')
                if mode == 'time': self.assertEqual(journal['total_seconds'], runtime.CELL_LIMIT+1)

    def test_grid_accepts_only_train_loader_and_counts_failed_cell_before_stopping(self):
        source = {'fixture': 'source'}
        train = {'manifest': {'dataset_fingerprint': runtime.DATA_FINGERPRINT, 'split': 'train'},
                 'forks': forks_fixture()}
        clock = [0.]
        def failed(*args):
            clock[0] += 7.5
            raise TimeoutError('synthetic failure after work')
        with TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
            loader = stack.enter_context(patch.object(runtime, 'load_dataset', return_value=train))
            stack.enter_context(patch('two_player_v22.data.parent_load', side_effect=AssertionError('parent access')))
            for name, replacement in {
                'runtime_source': lambda: source, 'references': lambda: {}, 'check_train': lambda data: None,
                'verify_bytes': lambda path: (train['manifest'], b''),
                'batch_arrays': lambda *args: {'x': np.zeros((1, 3, 198))},
                'train_run': failed, 'process_peak_rss': lambda: None,
            }.items(): stack.enter_context(patch.object(runtime, name, replacement))
            stack.enter_context(patch.object(runtime.time, 'perf_counter', side_effect=lambda: clock[0]))
            stack.enter_context(patch('builtins.print'))
            output = Path(directory)/'grid'
            ledger = runtime.run_grid('standalone-full-only', output)
            loader.assert_called_once_with('standalone-full-only', 'train')
            self.assertEqual(ledger['status'], 'inconclusive')
            self.assertEqual(ledger['total_cell_seconds'], 7.5)
            self.assertEqual(ledger['runs'][0]['status'], 'failed')
            self.assertTrue(all(r['status'] == 'planned' for r in ledger['runs'][1:]))
            self.assertEqual([ledger[k] for k in ('development_predictions', 'selection_predictions',
                                                'final_predictions', 'new_search_decisions')], [0]*4)
            self.assertEqual(json.loads((output/'ledger.json').read_text()), ledger)

    def test_wrong_artifact_identity_rejected_before_loading_labels_or_allocating_model(self):
        for bad in ({'dataset_fingerprint': 'protected-or-other', 'split': 'train'},
                    {'dataset_fingerprint': runtime.DATA_FINGERPRINT, 'split': 'development'}):
            with self.subTest(manifest=bad), TemporaryDirectory() as directory, ExitStack() as stack:
                stack.enter_context(patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
                stack.enter_context(patch.object(runtime, 'runtime_source', return_value={'fixture': 'source'}))
                stack.enter_context(patch.object(runtime, 'references', return_value={}))
                stack.enter_context(patch.object(runtime, 'verify_bytes', return_value=(bad, b'')))
                loader = stack.enter_context(patch.object(runtime, 'load_dataset'))
                model = stack.enter_context(patch.object(runtime, 'Model'))
                with self.assertRaisesRegex(ValueError, 'Only the frozen standalone training'):
                    runtime.run_grid('untrusted-path', Path(directory)/'grid')
                loader.assert_not_called()
                model.assert_not_called()

    def test_epoch40_replay_accepts_all_matching_tensors_with_new_checkpoint_identity(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            config, train, batch, source = self.tiny_cell(stack, epochs=40)
            hashes = runtime.tensor_hashes(runtime.Model(config))
            reference = {(config.variant, config.seed): {'config': asdict(config), 'epoch': 40,
                         'step': 2640, 'array_hashes': hashes, 'checkpoint_sha256': 'historical-file-hash'}}
            receipt = runtime.train_run(config, train, batch, Path(directory)/'cell', source, reference, directory)
            self.assertEqual(receipt['snapshots'][-1]['reference_match'], 'verified')
            self.assertNotEqual(receipt['snapshots'][-1]['checkpoint_sha256'], 'historical-file-hash')

    def test_final_ledger_growth_cannot_publish_complete_above_byte_cap(self):
        train = {'manifest': {'dataset_fingerprint': runtime.DATA_FINGERPRINT, 'split': 'train'},
                 'forks': forks_fixture()}
        config = runtime.configurations()[0]
        def no_fit(config, train, batch, path, *args):
            Path(path).mkdir()
            return {'seconds': 0., 'fixture_only': True}
        def bytes_after_complete(path, exclude_ledger=False):
            ledger = Path(path)/'ledger.json'
            if not exclude_ledger and ledger.exists() and json.loads(ledger.read_text())['status'] == 'complete':
                return runtime.BYTE_LIMIT
            return 0
        with TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
            for name, replacement in {
                'runtime_source': lambda: {'fixture': 'source'}, 'references': lambda: {},
                'configurations': lambda: [config], 'check_train': lambda data: None,
                'verify_bytes': lambda path: (train['manifest'], b''), 'load_dataset': lambda *args: train,
                'batch_arrays': lambda *args: {'x': np.zeros((1, 3, 198))},
                'train_run': no_fit, 'process_peak_rss': lambda: None, 'artifact_bytes': bytes_after_complete,
            }.items(): stack.enter_context(patch.object(runtime, name, replacement))
            stack.enter_context(patch('builtins.print'))
            output = Path(directory)/'grid'
            result = runtime.run_grid('full-only', output)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertIn('final ledger exceeded aggregate artifact limit', result['failures'])
            self.assertEqual(json.loads((output/'ledger.json').read_text())['status'], 'inconclusive')


if __name__ == '__main__':
    unittest.main()
