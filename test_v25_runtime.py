"""Independent bounded runtime regressions; synthetic data and mocked updates only."""
from contextlib import ExitStack, redirect_stdout
import inspect
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from test_v25_data import fixture
from two_player_v22.data import batch_arrays
from two_player_v25.data import build_groups
from two_player_v25 import runtime


class DummyModel:
    """No prediction or optimizer implementation: orchestration only."""
    def __init__(self, config):
        self.config = config
        self.params = {'w': np.zeros(1)}
        self.target = {'w': np.zeros(1)}
        self.m = {'w': np.zeros(1)}
        self.v = {'w': np.zeros(1)}
        self.epoch, self.step = 160, 10560


class GridHarness:
    def __init__(self, stack, directory, mode=None):
        self.directory = Path(directory)
        self.training, self.development = self.directory/'train', self.directory/'development'
        self.output = self.directory/'output'
        self.clock = 100.
        self.fits, self.loads, self.verified, self.evaluations = [], [], [], []
        self.source = {'synthetic.py': '0'*64}
        self.mode = mode
        self.late_cap = False
        self.completed = 0
        self.post_complete_rss_checks = 0
        self.tm = {'dataset_fingerprint': runtime.TRAIN_FP, 'parent_dataset_fingerprint': 'parent',
                   'split': 'train', 'role': 'redacted-training', 'fraction': 1.,
                   'audit': {'status': 'PASSED'}, 'parent_audit_status': 'PASSED'}
        self.dm = {**self.tm, 'dataset_fingerprint': runtime.DEV_FP,
                   'split': 'development', 'role': 'standalone-development'}
        self.train = {'manifest': self.tm, 'forks': [{'split': 'train'}]}
        roots = [{'game': 'connect4-4x5' if i < 107 else 'reversi6', 'root_id': f'r{i}',
                  'trajectory': f't{i}', 'split': 'development', 'actions': [0],
                  'oracle_values': [0], 'beyond_depth': True} for i in range(209)]
        self.dev = {'manifest': self.dm, 'roots': roots, 'forks': [{'split': 'development'}],
                    'nodes': {'c': {'game': 'connect4-4x5'}, 'r': {'game': 'reversi6'}}}
        real_atomic = runtime.atomic_json

        def atomic(path, obj):
            real_atomic(path, obj)
            if Path(path).name == 'ledger.json':
                self.completed = sum(r['status'] == 'complete' for r in obj['runs'])
                if mode == 'final_cap' and obj['status'] == 'complete': self.late_cap = True
            if mode == 'receipt_cap' and Path(path).name == 'receipt.json' and obj['status'] == 'complete':
                self.late_cap = True

        replacements = {
            'runtime_source': lambda: {'changed': '1'} if mode == 'source' and self.fits else self.source,
            'code_commit': lambda: 'synthetic-commit',
            'verify_bytes': self.verify,
            'load_dataset': self.load,
            'check_train': lambda value: self._check_train(value),
            'build_groups': lambda value: {'groups': [None]*2056 if value is self.train else [None],
                                            'group_sha256': 'train-groups' if value is self.train else 'dev-groups'},
            'batch_arrays': lambda *args: {'x': np.zeros((1, 1))},
            'Model': DummyModel,
            'fit_model': self.fit,
            'evaluate': self.evaluate,
            'diagnostics': self.diagnostics,
            'atomic_json': atomic,
            'artifact_bytes': lambda path: runtime.BYTE_LIMIT if self.late_cap else 100,
            'process_peak_rss': self.rss,
        }
        for name, value in replacements.items(): stack.enter_context(patch.object(runtime, name, value))
        stack.enter_context(patch.object(runtime.time, 'perf_counter', side_effect=lambda: self.clock))
        stack.enter_context(patch.dict(runtime.os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1'))
        stack.enter_context(redirect_stdout(io.StringIO()))

    def _check_train(self, value):
        if value is not self.train: raise AssertionError('Optimizer received foreign data')

    def rss(self):
        if self.mode == 'between_cells' and self.completed == 1:
            self.post_complete_rss_checks += 1
            # Let the just-completed cell's last guard pass; fail the next
            # iteration's preflight before its clock or active item is set.
            if self.post_complete_rss_checks >= 2: return runtime.RSS_LIMIT
        return 100

    def verify(self, path):
        path = Path(path); self.verified.append(path)
        if path == self.training: return self.tm, b'synthetic'
        if path == self.development: return self.dm, b'synthetic'
        raise AssertionError('Unexpected data access: '+str(path))

    def load(self, path, split):
        self.loads.append((Path(path), split))
        if (Path(path), split) == (self.training, 'train'): return self.train
        if (Path(path), split) == (self.development, 'development'): return self.dev
        raise AssertionError('Protected/parent access')

    def fit(self, config, train, base, grouping, path, source, guard):
        self._check_train(train)
        self.assert_readonly = all(not a.flags.writeable for a in base.values())
        self.fits.append(config); self.clock += 1.
        if self.mode == 'fit_error': raise RuntimeError('Synthetic fit failure')
        if self.mode == 'cell_time': self.clock += runtime.CELL_LIMIT
        if self.mode == 'total_time': self.clock += runtime.TOTAL_LIMIT
        guard()
        (path/'checkpoint.npz').write_bytes(runtime.run_id(config).encode())
        (path/'history.json').write_text('[]', encoding='utf-8')
        model = DummyModel(config)
        return model, {'checkpoint_sha256': runtime.sha(path/'checkpoint.npz')}

    def evaluate(self, roots, model=None, *, tracks=('exact', 'hybrid')):
        if roots is not self.dev['roots']: raise AssertionError('Different evaluation schedule')
        self.evaluations.append((None if model is None else model.config, tuple(tracks)))
        self.clock += .01
        return [{'status': 'complete', 'root_id': r['root_id'], 'track': track}
                for r in roots for track in tracks]

    def diagnostics(self, model, dev, base, groups, guard):
        if dev is not self.dev: raise AssertionError('Wrong development object')
        if self.mode == 'mutation': model.m['w'][0] = 1.
        if self.mode == 'counter_mutation': model.step += 1
        return {}, {'collapse': self.mode == 'collapse'}

    def run(self):
        return runtime.run_grid(self.training, self.development, self.output)


class RuntimeTests(unittest.TestCase):
    def test_frozen_42_cells_and_optimizer_boundary(self):
        configs = runtime.configurations()
        self.assertEqual(len(configs), 42)
        self.assertEqual(len({runtime.run_id(c) for c in configs}), 42)
        self.assertEqual({(c.variant, c.learning_rate, c.seed) for c in configs},
                         {(v, lr, s) for v in runtime.FAMILIES for lr in (.001, .0003) for s in (17, 29, 43)})
        for c in configs:
            self.assertEqual((c.hidden, c.latent, c.transition_hidden, c.batch_groups), (128, 64, 50, 32))
        self.assertEqual(runtime.EPOCHS, 160)
        self.assertEqual(list(inspect.signature(runtime.fit_model).parameters),
                         ['config', 'train', 'base', 'grouping', 'path', 'source', 'guard'])
        sources = runtime.runtime_source()
        for path in ('two_player_v25/data.py', 'two_player_v25/model.py', 'two_player_v25/runtime.py',
                     'two_player_v25/metrics.py', 'docs/METHOD_V25.md', 'two_player_v21/augmentation.py'):
            self.assertEqual(len(sources[path]), 64)

    def test_all_42_cells_complete_same_schedule_and_fresh_only(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            h = GridHarness(stack, directory)
            result = h.run()
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(h.fits, runtime.configurations())
            self.assertTrue(h.assert_readonly)
            self.assertEqual(result['development_decisions'], 42*418)
            self.assertEqual(result['control_decisions'], 836)
            self.assertEqual((result['selection_predictions'], result['final_predictions']), (0, 0))
            self.assertEqual(h.loads, [(h.training, 'train'), (h.development, 'development')])
            self.assertEqual(set(h.verified), {h.training, h.development})
            self.assertEqual([c for c, tracks in h.evaluations[4:]], runtime.configurations())
            self.assertTrue(all(tracks == ('exact', 'hybrid') for _, tracks in h.evaluations[4:]))
            self.assertAlmostEqual(result['total_cell_seconds'], sum(r['seconds'] for r in result['runs']))
            prior = (h.output/'ledger.json').read_bytes()
            with self.assertRaises(FileExistsError): h.run()
            self.assertEqual((h.output/'ledger.json').read_bytes(), prior)

    def test_wrong_standalone_fingerprint_rejected_before_loading_or_optimizer(self):
        for target in ('tm', 'dm'):
            with self.subTest(target=target), TemporaryDirectory() as directory, ExitStack() as stack:
                h = GridHarness(stack, directory)
                getattr(h, target)['dataset_fingerprint'] = 'foreign'
                result = h.run()
                self.assertEqual(result['status'], 'inconclusive')
                self.assertEqual(h.loads, []); self.assertEqual(h.fits, [])
                self.assertEqual(h.evaluations, [])

    def test_failure_limits_collapse_and_state_changes_stop_all_later_cells(self):
        for mode in ('fit_error', 'cell_time', 'total_time', 'mutation', 'counter_mutation', 'source', 'collapse', 'receipt_cap'):
            with self.subTest(mode=mode), TemporaryDirectory() as directory, ExitStack() as stack:
                h = GridHarness(stack, directory, mode)
                result = h.run()
                self.assertEqual(result['status'], 'inconclusive')
                self.assertEqual(len(h.fits), 1)
                self.assertEqual([r['status'] for r in result['runs']], ['failed']+['planned']*41)
                first = result['runs'][0]
                self.assertGreater(first['seconds'], 0.)
                self.assertEqual(result['total_cell_seconds'], first['seconds'])
                budget = runtime.read(h.output/first['id']/'budget.json')
                self.assertEqual(budget['status'], 'failed')
                self.assertEqual(budget['total_seconds'], first['seconds'])
                if mode == 'receipt_cap':
                    self.assertEqual(runtime.read(h.output/first['id']/'receipt.json')['status'], 'failed')

    def test_late_final_cap_revokes_complete_ledger(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            h = GridHarness(stack, directory, 'final_cap')
            result = h.run()
            self.assertEqual(len(h.fits), 42)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertEqual(runtime.read(h.output/'ledger.json')['status'], 'inconclusive')
            self.assertEqual(result['failures'], ['preparation_or_completion'])

    def test_between_cells_resource_failure_is_journaled_without_unstarted_clock(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            h = GridHarness(stack, directory, 'between_cells')
            result = h.run()
            self.assertEqual(result['status'], 'inconclusive')
            self.assertEqual(len(h.fits), 1)
            self.assertNotIn('NoneType', result['error'])
            self.assertEqual(sum(r['status'] == 'planned' for r in result['runs']), 41)
            self.assertEqual(result['runs'][0]['status'], 'complete')
            self.assertEqual(result['failures'], ['preparation_or_completion'])

    def test_one_mocked_epoch_retains_2088_group_instances_and_final_eight(self):
        # Real legal arrays, group expansion, augmentation and checkpoint I/O;
        # update itself is replaced, so no fitting or research result is produced.
        dataset = fixture(); groups = build_groups(dataset)
        base = batch_arrays(dataset, range(len(dataset['forks'])))
        indices = np.resize(np.arange(len(groups['groups']), dtype=np.int64), 2088)
        transforms = np.zeros(2088, dtype=np.int64)
        rows = sum(groups['groups'][i]['row_count'] for i in indices)
        plan = {'group_draws': 2088, 'fork_rows': rows}
        seen = []
        def update(model, batch):
            seen.append(len(np.unique(batch['group'])))
            model.step += 1
            return {'value_count': int(batch['valid'].sum()), 'loss': 1.,
                    'h2_scaled_factor_count': 0, 'h2_scaled_factor_sum': 0.,
                    'h2_scaled_factor_min': 0., 'h2_scaled_factor_max': 0.}
        source = {'synthetic': 'source'}
        with TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.object(runtime, 'EPOCHS', 1))
            stack.enter_context(patch.object(runtime, 'check_train', lambda value: None))
            stack.enter_context(patch.object(runtime, 'runtime_source', lambda: source))
            stack.enter_context(patch.object(runtime, 'epoch_plan', return_value=(indices, transforms, plan)))
            stack.enter_context(patch.object(runtime.Model, 'update', update))
            config = runtime.configurations()[0]
            model, receipt = runtime.fit_model(config, dataset, base, groups, Path(directory), source, lambda **kw: None)
            self.assertEqual(seen, [32]*65+[8])
            self.assertEqual((model.epoch, model.step), (1, 66))
            history = runtime.read(Path(directory)/'history.json')
            self.assertEqual(history[0]['fork_rows'], rows)
            self.assertEqual(history[0]['group_draws'], 2088)
            self.assertEqual(receipt['checkpoint_sha256'], runtime.sha(Path(directory)/'checkpoint.npz'))
            restored = runtime.Model.load(Path(directory)/'checkpoint.npz', config, receipt['identity'])
            self.assertEqual(runtime.tensor_hashes(restored), runtime.tensor_hashes(model))

    def test_invalid_training_and_changed_source_rejected_before_model_creation(self):
        with TemporaryDirectory() as directory, patch.object(runtime, 'Model') as constructor:
            with self.assertRaises(ValueError):
                runtime.fit_model(runtime.configurations()[0], fixture('development'), {}, {},
                                  Path(directory), {}, lambda **kw: None)
            constructor.assert_not_called()
        with TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.object(runtime, 'check_train', lambda value: None))
            stack.enter_context(patch.object(runtime, 'runtime_source', return_value={'changed': '1'}))
            constructor = stack.enter_context(patch.object(runtime, 'Model'))
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                runtime.fit_model(runtime.configurations()[0], {'manifest': {'dataset_fingerprint': 'fixture'}},
                                  {}, {'group_sha256': 'fixture'}, Path(directory), {}, lambda **kw: None)
            constructor.assert_not_called()


if __name__ == '__main__': unittest.main()
