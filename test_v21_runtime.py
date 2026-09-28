"""V2.1 admission/pairing tests with fixtures; no research fitting or scoring."""
from collections import Counter
from contextlib import ExitStack
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from two_player_v2 import GAMES_V2
from two_player_v2 import runtime as old_runtime
from two_player_v21 import runtime


def forks_fixture():
    return [{'game': game, 'root_id': f'{game}-{root}', 'split': 'train'}
            for game, count in (('connect4-4x5', 2), ('reversi6', 3))
            for root in range(count) for _ in range(root + 1)]


def arrays_fixture(forks):
    n = len(forks)
    result = {'x': np.zeros((n, 3, 198)), 'valid': np.ones((n, 3), bool),
              'legal': np.zeros((n, 3, 65), bool), 'policy': np.zeros((n, 3, 65)),
              'value': np.zeros((n, 3, 1)), 'actions': np.zeros((n, 2, 65))}
    for i, fork in enumerate(forks):
        game = GAMES_V2[fork['game']]
        state = game.initial()
        for horizon in range(3):
            legal = game.legal_actions(state)
            result['x'][i, horizon] = game.features(state)
            result['legal'][i, horizon, list(legal)] = True
            result['policy'][i, horizon, list(legal)] = 1 / len(legal)
            if horizon < 2:
                result['actions'][i, horizon, legal[0]] = 1
                state = game.transition(state, legal[0])
    return result


class V21RuntimeTests(unittest.TestCase):
    def test_original_sampling_unchanged_and_transform_rng_separate(self):
        forks = forks_fixture()
        for seed in runtime.SEEDS:
            for epoch in (0, 7, 39):
                original, old_meta = old_runtime.epoch_indices(forks, seed, epoch)
                indices, metadata = runtime.epoch_indices(forks, seed, epoch)
                np.testing.assert_array_equal(indices, original)
                self.assertEqual(metadata, old_meta)
                transforms, plan = runtime.augmentation_plan(forks, indices, seed, epoch)
                rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2211]))
                expected = [rng.integers(len(GAMES_V2[forks[int(i)]['game']].transforms())) for i in indices]
                np.testing.assert_array_equal(transforms, expected)
                self.assertEqual(plan['index_sha256'], metadata['index_sha256'])
                self.assertEqual(sum(plan['transform_counts'].values()), len(indices))
                repeated, repeated_meta = runtime.augmentation_plan(forks, indices, seed, epoch)
                np.testing.assert_array_equal(transforms, repeated)
                self.assertEqual(plan, repeated_meta)

    def test_protected_forks_never_receive_a_training_or_augmentation_plan(self):
        for split in ('development', 'selection', 'final'):
            forks = forks_fixture()
            forks[0]['split'] = split
            with self.assertRaises(ValueError):
                runtime.epoch_indices(forks, 17, 0)
            with self.assertRaises(ValueError):
                runtime.augmentation_plan(forks, np.array([0]), 17, 0)

    def test_source_and_identity_pin_both_versions_and_weight(self):
        sources = runtime.runtime_source()
        for path in ('two_player_v2/model.py', 'two_player_v2/data.py', 'two_player_v2/evaluate.py',
                     'two_player_v21/runtime.py', 'two_player_v21/augmentation.py',
                     'docs/METHOD_V2.md', 'docs/METHOD_V21.md'):
            self.assertEqual(len(sources[path]), 64)
        manifest = {'dataset_fingerprint': 'fixture-data'}
        one = runtime.identity(runtime.Config(jepa_weight=1), manifest, sources)
        tenth = runtime.identity(runtime.Config(jepa_weight=.1), manifest, sources)
        self.assertNotEqual(one['config_sha256'], tenth['config_sha256'])
        self.assertNotEqual(one['method'], one['objective'])
        self.assertEqual(one['objective'], runtime.OBJECTIVE_VERSION)
        self.assertNotEqual(one, old_runtime.identity(runtime.Config(), manifest, sources))

    def test_train_loop_passes_same_epoch_augmentation_across_variants(self):
        forks = forks_fixture()
        train = {'forks': forks, 'manifest': {'dataset_fingerprint': 'fixture'}}
        batch = arrays_fixture(forks)
        original = {key: value.copy() for key, value in batch.items()}
        captured = []

        def no_optimizer(model, augmented):
            # Capture inputs at the optimizer boundary, without fitting a model.
            captured.append({key: value.copy() for key, value in augmented.items()})
            model.step += 1
            return {'samples': len(augmented['x'])}

        with TemporaryDirectory() as temporary, patch.object(runtime, 'EPOCHS', 2), \
             patch.object(runtime, 'DRAWS', 2), patch.object(runtime, 'runtime_source', return_value={'fixture': 'source'}), \
             patch.object(runtime.Model, 'update', no_optimizer):
            histories = []
            for variant in ('direct', 'rjepa'):
                path = Path(temporary) / variant
                config = runtime.Config(variant=variant, seed=17, jepa_weight=.1 if variant == 'rjepa' else 1.)
                runtime.train_run(config, train, batch, path, {'fixture': 'source'})
                histories.append(json.loads((path / 'history.json').read_text()))
        self.assertEqual(len(captured), 4)
        for epoch in range(2):
            for key in batch:
                np.testing.assert_array_equal(captured[epoch][key], captured[epoch + 2][key])
            self.assertEqual(histories[0][epoch]['augmentation'], histories[1][epoch]['augmentation'])
            self.assertEqual(histories[0][epoch]['schedule'], histories[1][epoch]['schedule'])
        for key in batch:
            np.testing.assert_array_equal(batch[key], original[key])

    def test_grid_inventory_uses_only_train_development_and_preserves_all_cells(self):
        roots = [{'game': 'connect4-4x5', 'root_id': 'fixture', 'trajectory': 'fixture', 'split': 'development'}]
        dataset = {'roots': roots, 'forks': forks_fixture()}
        configs = []

        def no_fit(config, train, batch, path, source):
            Path(path).mkdir()
            configs.append(config)
            return object(), {'seconds': 0., 'checkpoint_sha256': 'fixture-only'}

        def no_score(roots, model, tracks=('exact', 'hybrid')):
            return [{'status': 'complete', 'track': t} for t in tracks]

        with TemporaryDirectory() as temporary, ExitStack() as stack:
            stack.enter_context(patch.dict(runtime.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
            replacements = {'runtime_source': lambda: {'fixture': 'source'},
                            'verify_bytes': lambda _: ({'dataset_fingerprint': 'fixture'}, b''),
                            'batch_arrays': lambda *args: {'x': np.zeros((1, 3, 198))},
                            'train_run': no_fit, 'evaluate': no_score, 'diagnostics': lambda *args: {}}
            for name, replacement in replacements.items():
                stack.enter_context(patch.object(runtime, name, replacement))
            loader = stack.enter_context(patch.object(runtime, 'load_dataset', return_value=dataset))
            stack.enter_context(patch.object(runtime, 'augment', side_effect=AssertionError('Evaluation augmented')))
            stack.enter_context(patch('builtins.print'))
            ledger = runtime.run_grid('fixture-data', Path(temporary) / 'grid')
        self.assertEqual([call.args[1] for call in loader.call_args_list], ['train', 'development'])
        self.assertEqual(len(configs), 60)
        observed = {(c.variant, c.learning_rate, c.jepa_weight, c.seed) for c in configs}
        expected = {(v, rate, weight, seed) for v in runtime.VARIANTS for rate in runtime.RATES
                    for weight in ((1.,) if v in ('direct', 'value-dynamics') else (.1, 1.)) for seed in runtime.SEEDS}
        self.assertEqual(observed, expected)
        self.assertEqual(len({r['id'] for r in ledger['runs']}), 60)
        self.assertEqual(Counter(c.variant for c in configs),
                         {'direct': 6, 'value-dynamics': 6, 'decoded': 12, 'rjepa': 12, 'raw-jepa': 12, 'no-response': 12})
        self.assertEqual(ledger['status'], 'complete')
        self.assertEqual((ledger['selection_predictions'], ledger['final_predictions']), (0, 0))

    def test_interrupted_or_exhausted_attempt_cannot_gain_resume_budget(self):
        train = {'forks': forks_fixture(), 'manifest': {'dataset_fingerprint': 'fixture'}}
        config = runtime.Config()
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
