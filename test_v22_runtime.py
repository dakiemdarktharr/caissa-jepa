"""Restricted-label runtime checks with synthetic artifacts and no research fit."""
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from test_v21_runtime import arrays_fixture, forks_fixture
from two_player_v22 import runtime


def artifacts():
    roots = [{'game': 'connect4-4x5', 'root_id': 'fixture', 'trajectory': 'fixture', 'split': 'train'}]
    result = {}
    for path, fraction, split in (('scarce', .25, 'train'), ('full', 1., 'train'), ('dev', 1., 'development')):
        result[path] = {'roots': [dict(r, split=split) for r in roots], 'forks': forks_fixture(),
                        'manifest': {'fraction': fraction, 'label_seed': 271828,
                                     'parent_dataset_fingerprint': 'parent-fixture',
                                     'dataset_fingerprint': path + '-fixture'}}
    return result


class V22RuntimeTests(unittest.TestCase):
    def test_complete_grid_routes_only_correct_redacted_fraction_and_separate_dev(self):
        banks = artifacts()
        fitted = []

        def no_fit(config, train, batch, path, source):
            fraction = train['manifest']['fraction']
            self.assertEqual(batch['value_labelled'][0, 0], fraction == 1.)
            fitted.append((fraction, config))
            Path(path).mkdir()
            return object(), {'seconds': 0., 'checkpoint_sha256': 'fixture-only'}

        def batches(dataset, indices):
            known = dataset['manifest']['fraction'] == 1.
            return {'x': np.zeros((1, 3, 198)), 'value_labelled': np.full((1, 3), known)}

        with TemporaryDirectory() as temporary, ExitStack() as stack:
            stack.enter_context(patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
            loader = stack.enter_context(patch.object(runtime, 'load_dataset', side_effect=lambda path, split: banks[path]))
            for name, replacement in {
                'runtime_source': lambda: {'fixture': 'source'},
                'verify_bytes': lambda path: (banks[path]['manifest'], b''),
                'batch_arrays': batches, 'train_run': no_fit,
                'evaluate': lambda roots, model, tracks=('exact', 'hybrid'): [{'status': 'complete'} for _ in tracks],
                'diagnostics': lambda *args: {},
            }.items():
                stack.enter_context(patch.object(runtime, name, replacement))
            stack.enter_context(patch('two_player_v22.data.parent_load', side_effect=AssertionError('Runtime opened parent labels')))
            stack.enter_context(patch('builtins.print'))
            ledger = runtime.run_grid('scarce', 'full', 'dev', Path(temporary) / 'grid')
        self.assertEqual([call.args for call in loader.call_args_list], [('scarce', 'train'), ('full', 'train'), ('dev', 'development')])
        expected = {(f, v, lr, seed) for f in (.25, 1.) for v in runtime.VARIANTS for lr in runtime.RATES for seed in runtime.SEEDS}
        self.assertEqual({(f, c.variant, c.learning_rate, c.seed) for f, c in fitted}, expected)
        self.assertEqual(len(fitted), 72)
        self.assertEqual(Counter(f for f, _ in fitted), {.25: 36, 1.: 36})
        for _, config in fitted:
            self.assertEqual(config.jepa_weight, .1 if config.variant in ('decoded', 'raw-jepa', 'raw-no-response') else 1.)
        self.assertEqual(len({r['id'] for r in ledger['runs']}), 72)
        self.assertEqual(ledger['status'], 'complete')
        self.assertEqual((ledger['selection_predictions'], ledger['final_predictions']), (0, 0))

    def test_regime_parent_and_exposure_mismatch_fail_before_fitting(self):
        for defect in ('fraction', 'label-seed', 'parent', 'root-exposure', 'fork-exposure'):
            banks = artifacts()
            if defect == 'fraction': banks['scarce']['manifest']['fraction'] = 1.
            elif defect == 'label-seed': banks['scarce']['manifest']['label_seed'] = 123
            elif defect == 'parent': banks['full']['manifest']['parent_dataset_fingerprint'] = 'other'
            elif defect == 'root-exposure': banks['full']['roots'][0]['trajectory'] = 'other'
            else: banks['full']['forks'].pop()
            with self.subTest(defect=defect), TemporaryDirectory() as temporary, \
                 patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}), \
                 patch.object(runtime, 'runtime_source', return_value={'fixture': 'source'}), \
                 patch.object(runtime, 'load_dataset', side_effect=lambda path, split: banks[path]), \
                 patch.object(runtime, 'train_run') as fit:
                with self.assertRaises(ValueError):
                    runtime.run_grid('scarce', 'full', 'dev', Path(temporary) / 'grid')
                fit.assert_not_called()

    def test_optimizer_boundary_preserves_mask_and_zero_targets_through_augmentation(self):
        forks = forks_fixture()
        full = arrays_fixture(forks)
        full['value_labelled'] = full['valid'].copy()
        full['policy_labelled'] = full['legal'].any(-1)
        scarce = deepcopy(full)
        scarce['value_labelled'][::2] = False
        scarce['policy_labelled'][::2] = False
        scarce['value'][::2] = 0
        scarce['policy'][::2] = 0
        observed = []

        def no_optimizer(model, batch):
            observed.append(deepcopy(batch))
            self.assertFalse(batch['value'][~batch['value_labelled']].any())
            self.assertFalse(batch['policy'][~batch['policy_labelled']].any())
            model.step += 1
            return {'value_count': int(batch['value_labelled'].sum()),
                    'policy_count': int(batch['policy_labelled'].sum())}

        with TemporaryDirectory() as temporary, patch.object(runtime, 'EPOCHS', 1), \
             patch.object(runtime, 'DRAWS', 2), patch.object(runtime, 'runtime_source', return_value={'fixture': 'source'}), \
             patch.object(runtime.Model, 'update', no_optimizer):
            histories = []
            for name, batch in (('scarce', scarce), ('full', full)):
                train = {'forks': forks, 'manifest': {'dataset_fingerprint': name}}
                path = Path(temporary) / name
                runtime.train_run(runtime.Config(seed=17), train, batch, path, {'fixture': 'source'})
                histories.append(json.loads((path / 'history.json').read_text())[0])
            indices, _ = runtime.epoch_indices(forks, 17, 0)
        self.assertEqual(len(observed), 2)
        for key in ('x', 'valid', 'legal', 'actions'):
            np.testing.assert_array_equal(observed[0][key], observed[1][key])
        self.assertLess(observed[0]['value_labelled'].sum(), observed[1]['value_labelled'].sum())
        for index, batch in enumerate((scarce, full)):
            for mask in ('value_labelled', 'policy_labelled'):
                np.testing.assert_array_equal(observed[index][mask], batch[mask][indices])
        for i, history in enumerate(histories):
            self.assertEqual(history['label_and_target_count_totals']['value_count'], int(observed[i]['value_labelled'].sum()))
            self.assertEqual(history['label_and_target_count_totals']['policy_count'], int(observed[i]['policy_labelled'].sum()))
        self.assertEqual(histories[0]['augmentation'], histories[1]['augmentation'])
        self.assertEqual(histories[0]['schedule'], histories[1]['schedule'])

    def test_masked_dataset_identity_prevents_cross_regime_resume(self):
        source = runtime.runtime_source()
        for name in ('two_player_v22/data.py', 'two_player_v22/model.py', 'two_player_v22/runtime.py', 'docs/METHOD_V22.md'):
            self.assertEqual(len(source[name]), 64)
        config = runtime.Config()
        scarce = runtime.identity(config, {'dataset_fingerprint': 'scarce-mask'}, source)
        full = runtime.identity(config, {'dataset_fingerprint': 'full-mask'}, source)
        self.assertNotEqual(scarce, full)
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / 'model.npz'
            runtime.Model(config).save(path, scarce)
            with self.assertRaisesRegex(ValueError, 'identity'):
                runtime.Model.load(path, config, full)

    def test_interrupted_or_exhausted_resume_cannot_reset_budget(self):
        config = runtime.Config()
        train = {'forks': forks_fixture(), 'manifest': {'dataset_fingerprint': 'fixture'}}
        source = {'fixture': 'source'}
        identity = runtime.identity(config, train['manifest'], source)
        for status in ('active', 'complete'):
            with self.subTest(status=status), TemporaryDirectory() as temporary:
                path = Path(temporary)
                runtime.Model(config).save(path / 'checkpoint.npz', identity)
                runtime.atomic_json(path / 'history.json', [])
                runtime.atomic_json(path / 'budget.json', {'status': status, 'identity': identity,
                                                         'total_seconds': 180., 'limit_seconds': 180.})
                with patch.object(runtime, 'runtime_source', return_value=source), patch.object(runtime.Model, 'update') as update:
                    with self.assertRaises((ValueError, TimeoutError)):
                        runtime.train_run(config, train, {}, path, source, resume=True)
                    update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
