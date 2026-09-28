"""Numerical and runtime contract checks, not research performance evidence."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from two_player_v2.model import Config, Model, VARIANTS, _normalize, _normalization_backward


def fixture():
    rng = np.random.default_rng(816)
    x = rng.normal(0, .04, (4, 3, 198))
    valid = np.ones((4, 3), dtype=bool)
    valid[1, 2] = False
    x[~valid] = 0
    legal = np.zeros((4, 3, 65), dtype=bool)
    policy = np.zeros_like(legal, dtype=float)
    for row in range(4):
        legal[row, 0, [0, 1, 8]] = True
        policy[row, 0, [0, 1, 8]] = [.2, .3, .5]
        if row != 1:
            legal[row, 1, [2, 3]] = True
            policy[row, 1, [2, 3]] = [.7, .3]
        if row not in (1, 3):
            legal[row, 2, [4, 5]] = True
            policy[row, 2, [4, 5]] = [.4, .6]
    value = np.array([[-1, 1, -1], [0, -1, 0], [1, 0, 1], [1, -1, 1]], dtype=float)[..., None]
    actions = np.zeros((4, 2, 65))
    for row, action in enumerate((8, 1, 0, 8)):
        actions[row, 0, action] = 1
        if row != 1:
            actions[row, 1, 3 if row == 2 else 2] = 1
    return dict(x=x, valid=valid, legal=legal, policy=policy, value=value, actions=actions)


def small_config(variant='rjepa'):
    return Config(variant=variant, seed=11, hidden=6, latent=4, projection=3,
                  learning_rate=.0003, jepa_weight=.7, batch_size=4)


class V2ModelTests(unittest.TestCase):
    def test_all_parameter_gradients_with_frozen_ema(self):
        batch = fixture()
        rng = np.random.default_rng(782)
        for variant in VARIANTS:
            model = Model(small_config(variant))
            target_before = {key: a.copy() for key, a in model.target.items()}
            metrics, gradients = model.loss_grad(batch)
            self.assertEqual(metrics['encoded_count'], 11)
            self.assertEqual(metrics['policy_count'], 9)
            self.assertEqual(metrics['terminal_count'], 2)
            if variant != 'direct':
                self.assertGreater(metrics['variance_loss'], 0)
                self.assertEqual(metrics['h1_count'], 4)
                self.assertEqual(metrics['h2_count'], 3)
            for key, parameter in model.params.items():
                directions = [rng.normal(size=parameter.shape)]
                coordinate = np.zeros_like(parameter)
                coordinate.flat[np.argmax(np.abs(gradients[key]))] = 1
                directions.append(coordinate)
                for direction in directions:
                    direction /= np.linalg.norm(direction)
                    original = parameter.copy()
                    epsilon = 1e-6
                    parameter[...] = original + epsilon * direction
                    plus = model.loss_grad(batch)[0]['loss']
                    parameter[...] = original - epsilon * direction
                    minus = model.loss_grad(batch)[0]['loss']
                    parameter[...] = original
                    numeric = (plus-minus)/(2*epsilon)
                    analytic = float(np.sum(gradients[key]*direction))
                    with self.subTest(variant=variant, tensor=key):
                        self.assertAlmostEqual(numeric, analytic, delta=2e-6 * (1+abs(numeric)))
            for key in target_before:
                np.testing.assert_array_equal(model.target[key], target_before[key])

    def test_normalization_gradient_near_zero(self):
        x = np.array([[0., 1e-5, -2e-5], [.1, -.2, .4]])
        weights = np.array([[.2, .4, -.1], [-.5, .1, .3]])
        _, norm = _normalize(x)
        analytic = _normalization_backward(x, norm, weights)
        for index in np.ndindex(x.shape):
            old = x[index]
            epsilon = 1e-8
            x[index] = old+epsilon
            plus = float(np.sum(_normalize(x)[0]*weights))
            x[index] = old-epsilon
            minus = float(np.sum(_normalize(x)[0]*weights))
            x[index] = old
            self.assertAlmostEqual((plus-minus)/(2*epsilon), analytic[index], delta=1e-5)

    def test_reply_mask_preserves_own_action_and_recurrence(self):
        batch = fixture()
        model = Model(small_config('no-response'))
        z = model.encode(batch['x'][:, 0])
        expected_h1 = np.tanh(z @ model.params['gw'] + batch['actions'][:, 0] @ model.params['aw'] + model.params['gb'])
        expected_h2 = np.tanh(expected_h1 @ model.params['gw'] + model.params['gb'])
        np.testing.assert_array_equal(model.rollout(z, batch['actions'], 1), expected_h1)
        np.testing.assert_array_equal(model.rollout(z, batch['actions'], 2), expected_h2)
        changed_reply = {key: a.copy() for key, a in batch.items()}
        changed_reply['actions'][:, 1] = 0
        for row in (0, 2, 3):
            changed_reply['actions'][row, 1, 2 if row == 2 else 3] = 1
        metrics, gradient = model.loss_grad(batch)
        altered_metrics, altered_gradient = model.loss_grad(changed_reply)
        self.assertEqual(metrics, altered_metrics)
        for key in gradient:
            np.testing.assert_array_equal(gradient[key], altered_gradient[key])
        changed_own = batch['actions'].copy()
        changed_own[:, 0] = 0
        changed_own[:, 0, 1] = 1
        self.assertFalse(np.allclose(model.rollout(z, changed_own), expected_h2))
        ordinary = Model(small_config('rjepa'))
        self.assertFalse(np.allclose(ordinary.rollout(z, batch['actions']), ordinary.rollout(z, changed_reply['actions'])))

    def test_missing_horizon_and_terminal_soft_policy(self):
        batch = fixture()
        batch['valid'][:, 2] = False
        batch['x'][:, 2] = 0
        batch['value'][:, 2] = 0
        batch['policy'][:, 1:] = 0
        batch['legal'][:, 1:] = False
        batch['actions'][:, 1] = 0
        for variant in VARIANTS:
            model = Model(small_config(variant))
            model.params['pw'][:] = 0
            model.params['pb'][:] = 0
            metrics, grad = model.loss_grad(batch)
            self.assertEqual(metrics['h2_count'], 0)
            self.assertEqual(metrics['h2_loss'], 0)
            self.assertEqual(metrics['h2_value_loss'], 0)
            self.assertEqual(metrics['h2_missing_count'], 4)
            self.assertEqual(metrics['policy_count'], 4)
            self.assertEqual(metrics['terminal_count'], 4)
            self.assertAlmostEqual(metrics['policy_nll'], np.log(3))
            target = np.zeros(65)
            target[[0, 1, 8]] = np.array([1/3, 1/3, 1/3]) - [.2, .3, .5]
            np.testing.assert_allclose(grad['pb'], target, atol=1e-14)

    def test_encoded_coverage_and_successor_value_independence(self):
        model = Model(small_config('value-dynamics'))
        batch = fixture()
        metrics, _ = model.loss_grad(batch)
        z = model.encode(batch['x'][:, 0])
        h1 = model.rollout(z, batch['actions'], 1)
        h2 = model.rollout(z, batch['actions'], 2)
        self.assertAlmostEqual(metrics['h1_value_mse'], np.mean((model.value(h1)-batch['value'][:, 1])**2))
        mask = batch['valid'][:, 2]
        self.assertAlmostEqual(metrics['h2_value_mse'], np.mean((model.value(h2[mask])-batch['value'][mask, 2])**2))
        self.assertAlmostEqual(metrics['value_mse'], np.mean((model.value(model.encode(batch['x'][batch['valid']]))-batch['value'][batch['valid']])**2))
        changed = {key: a.copy() for key, a in batch.items()}
        changed['value'][:, 0] *= -1
        changed_metrics, _ = model.loss_grad(changed)
        self.assertEqual(metrics['h1_value_mse'], changed_metrics['h1_value_mse'])
        self.assertEqual(metrics['h2_value_mse'], changed_metrics['h2_value_mse'])

    def test_seed_pairing_active_parameters_and_ema_update(self):
        base = Model(small_config())
        for variant in VARIANTS:
            model = Model(small_config(variant))
            for key in base.params:
                np.testing.assert_array_equal(base.params[key], model.params[key])
            counts = model.parameter_counts()
            self.assertLess(counts['active'], counts['allocated'])
        old = {key: a.copy() for key, a in base.target.items()}
        base.update(fixture())
        self.assertEqual(base.step, 1)
        for key in old:
            np.testing.assert_allclose(base.target[key], .99*old[key]+.01*base.params[key], rtol=2e-15, atol=1e-18)

    def test_zero_auxiliary_weight_matches_value_dynamics(self):
        batch = fixture()
        control = Model(small_config('value-dynamics'))
        control_metrics, control_grad = control.loss_grad(batch)
        for variant in ('rjepa', 'raw-jepa', 'decoded'):
            candidate = Model(replace(small_config(variant), jepa_weight=0.))
            metrics, grad = candidate.loss_grad(batch)
            self.assertEqual(metrics['loss'], control_metrics['loss'])
            self.assertEqual(candidate.parameter_counts()['active'], control.parameter_counts()['active'])
            for key in grad:
                np.testing.assert_array_equal(grad[key], control_grad[key])

    def test_h2_recurrent_gradient_cannot_be_detached(self):
        # Difference-of-differences removes encoded supervision, H1 and variance:
        # only changing H2 labels remains in the recurrent auxiliary gradient.
        batch = fixture()
        altered = {key: a.copy() for key, a in batch.items()}
        altered['value'][altered['valid'][:, 2], 2] *= -1
        model = Model(small_config('value-dynamics'))
        direct = Model(small_config('direct'))
        ga = model.loss_grad(batch)[1]
        gb = model.loss_grad(altered)[1]
        da = direct.loss_grad(batch)[1]
        db = direct.loss_grad(altered)[1]
        mask = batch['valid'][:, 2]
        for key in ('e1w', 'gw', 'aw'):
            gradient = gb[key]-ga[key]-(db[key]-da[key])
            self.assertGreater(np.linalg.norm(gradient), 1e-8)
            direction = gradient / np.linalg.norm(gradient)
            original = model.params[key].copy()
            values = []
            for sign in (1, -1):
                model.params[key][...] = original + sign*1e-6*direction
                future = model.rollout(model.encode(batch['x'][:, 0]), batch['actions'])[mask]
                value = model.value(future)
                values.append(.25*np.mean((value-altered['value'][mask, 2])**2-(value-batch['value'][mask, 2])**2))
            model.params[key][...] = original
            self.assertAlmostEqual((values[0]-values[1])/2e-6, float(np.sum(gradient*direction)), delta=2e-6)

    def test_exact_resume_and_reject_tampering(self):
        config = small_config()
        identity = {'source': 'fixture-source', 'dataset': 'fixture-data', 'objective': 'fixture-v2'}
        batch = fixture()
        model = Model(config)
        for _ in range(3):
            model.update(batch)
        model.epoch = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'checkpoint.npz'
            model.save(path, identity)
            resumed = Model.load(path, config, identity)
            self.assertEqual((resumed.step, resumed.epoch), (3, 2))
            self.assertEqual(model.update(batch), resumed.update(batch))
            for group in ('params', 'target', 'm', 'v'):
                for key, tensor in getattr(model, group).items():
                    np.testing.assert_array_equal(tensor, getattr(resumed, group)[key])
            with self.assertRaisesRegex(ValueError, 'identity'):
                Model.load(path, replace(config, jepa_weight=.8), identity)
            with self.assertRaisesRegex(ValueError, 'identity'):
                Model.load(path, config, dict(identity, dataset='other'))
            with np.load(path, allow_pickle=False) as source:
                arrays = {key: source[key].copy() for key in source.files}
            arrays['p_gw'][0, 0] += .1
            np.savez_compressed(path, **arrays)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                Model.load(path, config, identity)
            model.save(path, identity)
            with np.load(path, allow_pickle=False) as source:
                arrays = {key: source[key].copy() for key in source.files}
            metadata = json.loads(str(arrays['metadata']))
            metadata['epoch'] = True
            arrays['metadata'] = np.array(json.dumps(metadata))
            np.savez_compressed(path, **arrays)
            with self.assertRaisesRegex(ValueError, 'counters'):
                Model.load(path, config, identity)

    def test_atomic_save_failure_preserves_previous_checkpoint(self):
        model = Model(small_config())
        identity = {'source': 'fixture'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'checkpoint.npz'
            model.save(path, identity)
            original = path.read_bytes()
            model.update(fixture())
            with mock.patch('two_player_v2.model.os.replace', side_effect=OSError('injected rename failure')):
                with self.assertRaises(OSError):
                    model.save(path, identity)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['checkpoint.npz'])

    def test_input_contract_rejects_corruption(self):
        for mutation in ('nan', 'illegal-policy', 'bad-soft-policy', 'missing-action', 'terminal-reply', 'padding', 'mask-dtype'):
            batch = fixture()
            if mutation == 'nan':
                batch['x'][0, 0, 0] = np.nan
            elif mutation == 'illegal-policy':
                batch['policy'][0, 0, 40] = .1
            elif mutation == 'bad-soft-policy':
                batch['policy'][0, 0, 0] = .1
            elif mutation == 'missing-action':
                batch['actions'][0, 0] = 0
            elif mutation == 'terminal-reply':
                batch['actions'][1, 1, 2] = 1
            elif mutation == 'padding':
                batch['x'][1, 2, 0] = 1
            elif mutation == 'mask-dtype':
                batch['valid'] = batch['valid'].astype(int)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                Model(small_config()).loss_grad(batch)
        for kwargs in ({'latent': True}, {'seed': -1}, {'learning_rate': np.nan}, {'ema': 1.}, {'jepa_weight': -.1}):
            with self.assertRaises(ValueError):
                Config(**kwargs)


if __name__ == '__main__':
    unittest.main()
