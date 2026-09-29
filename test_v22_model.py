"""Numerical and runtime contract checks, not research performance evidence."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from two_player_v22.model import Config, Model, VARIANTS, _batch


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
    return dict(x=x, valid=valid, legal=legal, policy=policy, value=value, actions=actions,
                value_labelled=valid.copy(), policy_labelled=legal.any(-1))


def mixed_fixture():
    batch = fixture()
    for row, horizon in ((0, 0), (0, 1), (2, 2), (3, 1)):
        batch['value_labelled'][row, horizon] = False
        batch['policy_labelled'][row, horizon] = False
        batch['value'][row, horizon] = 0
        batch['policy'][row, horizon] = 0
    return batch


def unlabelled_fixture():
    # Row0 has three real nonterminal states; no rules-known terminal labels.
    batch = {key: value[[0, 0, 0, 0]].copy() for key, value in fixture().items()}
    batch['x'] += np.random.default_rng(823).normal(0, .02, batch['x'].shape)
    for key in ('value_labelled', 'policy_labelled', 'value', 'policy'):
        batch[key][...] = 0
    return batch


def small_config(variant='raw-jepa'):
    return Config(variant=variant, seed=11, hidden=6, latent=4, projection=3,
                  learning_rate=.0003, jepa_weight=.7, batch_size=4)


class V22ModelTests(unittest.TestCase):
    def test_full_labels_make_ema_value_identical_to_value_dynamics(self):
        batch = fixture()
        a = Model(small_config('value-dynamics'))
        b = Model(small_config('ema-value'))
        for _ in range(3):
            ma, ga = a.loss_grad(batch)
            mb, gb = b.loss_grad(batch)
            self.assertEqual(ma, mb)
            self.assertEqual(mb['h1_ema_value_count'], 0)
            self.assertEqual(mb['h2_ema_value_count'], 0)
            for key in ga:
                np.testing.assert_array_equal(ga[key], gb[key])
            self.assertEqual(a.update(batch), b.update(batch))
            for group in ('params', 'target', 'm', 'v'):
                for key in getattr(a, group):
                    np.testing.assert_array_equal(getattr(a, group)[key], getattr(b, group)[key])

    def test_ema_value_target_and_separate_denominators(self):
        batch = mixed_fixture()
        model = Model(small_config('ema-value'))
        model.target['vw'] *= -2
        model.target['vb'][:] = .23
        before = {key: value.copy() for key, value in model.target.items()}
        metrics, gradients = model.loss_grad(batch)
        root_z = model.encode(batch['x'][:, 0])
        for h in (1, 2):
            valid = batch['valid'][:, h]
            labeled = batch['value_labelled'][valid, h]
            pred = model.rollout(root_z, batch['actions'], h)[valid]
            target = model.value(model.encode(batch['x'][valid, h][~labeled], target=True), target=True)
            ema_mse = np.mean((model.value(pred[~labeled])-target)**2)
            oracle_mse = np.mean((model.value(pred[labeled])-batch['value'][valid, h][labeled])**2)
            self.assertEqual(metrics[f'h{h}_ema_value_count'], int((~labeled).sum()))
            self.assertEqual(metrics[f'h{h}_value_label_count'], int(labeled.sum()))
            self.assertAlmostEqual(metrics[f'h{h}_ema_value_loss'], .25*ema_mse)
            self.assertAlmostEqual(metrics[f'h{h}_value_loss'], .25*oracle_mse)
        for key in before:
            np.testing.assert_array_equal(model.target[key], before[key])
        # Targets are frozen as online value-head weights are perturbed.
        for key in ('vw', 'vb', 'gw', 'e1w'):
            direction = gradients[key]/np.linalg.norm(gradients[key])
            original = model.params[key].copy()
            values = []
            for sign in (1, -1):
                model.params[key][...] = original+sign*1e-6*direction
                values.append(model.loss_grad(batch)[0]['loss'])
            model.params[key][...] = original
            self.assertAlmostEqual((values[0]-values[1])/2e-6,
                                   float(np.sum(gradients[key]*direction)), delta=2e-6)

    def test_no_labels_zero_supervision_but_predictive_support_remains(self):
        batch = unlabelled_fixture()
        for variant in VARIANTS:
            model = Model(small_config(variant))
            metrics, gradients = model.loss_grad(batch)
            for key in ('value_count', 'policy_count', 'value_mse', 'policy_nll',
                        'h1_value_label_count', 'h2_value_label_count', 'h1_value_loss', 'h2_value_loss'):
                self.assertEqual(metrics[key], 0)
            if variant == 'direct':
                self.assertEqual(metrics['loss'], 0)
                for gradient in gradients.values():
                    np.testing.assert_array_equal(gradient, np.zeros_like(gradient))
            if variant in ('raw-jepa', 'raw-no-response', 'decoded'):
                self.assertEqual(metrics['h1_latent_count'], 4)
                self.assertEqual(metrics['h2_latent_count'], 4)
                self.assertGreater(metrics['h1_loss'], 0)
                self.assertGreater(metrics['h2_loss'], 0)
            if variant == 'ema-value':
                self.assertEqual(metrics['h1_ema_value_count'], 4)
                self.assertEqual(metrics['h2_ema_value_count'], 4)
                self.assertGreater(metrics['h1_ema_value_loss'], 0)
            # No policy target is fabricated by any unsupervised auxiliary.
            np.testing.assert_array_equal(gradients['pw'], np.zeros_like(gradients['pw']))
            np.testing.assert_array_equal(gradients['pb'], np.zeros_like(gradients['pb']))

    def test_mask_validation_and_hidden_target_rejection(self):
        mutations = ('value-hidden', 'policy-hidden', 'terminal-policy', 'missing-slot-label',
                     'terminal-hidden', 'integer-mask', 'missing-mask')
        for mutation in mutations:
            batch = mixed_fixture()
            if mutation == 'value-hidden':
                batch['value'][0, 0] = .5
            elif mutation == 'policy-hidden':
                batch['policy'][0, 0, 0] = 1
            elif mutation == 'terminal-policy':
                batch['policy_labelled'][1, 1] = True
            elif mutation == 'missing-slot-label':
                batch['value_labelled'][1, 2] = True
            elif mutation == 'terminal-hidden':
                batch['value_labelled'][1, 1] = False
                batch['value'][1, 1] = 0
            elif mutation == 'integer-mask':
                batch['value_labelled'] = batch['value_labelled'].astype(int)
            else:
                del batch['policy_labelled']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _batch(batch)

    def test_all_parameter_gradients_with_frozen_ema(self):
        rng = np.random.default_rng(782)
        for regime, batch in (('mixed', mixed_fixture()), ('full', fixture()), ('none', unlabelled_fixture())):
            for variant in VARIANTS:
                model = Model(small_config(variant))
                target_before = {key: a.copy() for key, a in model.target.items()}
                metrics, gradients = model.loss_grad(batch)
                self.assertEqual(metrics['encoded_count'], int(batch['valid'].sum()))
                self.assertEqual(metrics['policy_count'], int(batch['policy_labelled'].sum()))
                self.assertEqual(metrics['terminal_count'], int((batch['valid'] & ~batch['legal'].any(-1)).sum()))
                self.assertEqual(metrics['value_count'], int(batch['value_labelled'].sum()))
                self.assertEqual(metrics['value_unlabelled_count'], int((batch['valid'] & ~batch['value_labelled']).sum()))
                if variant != 'direct':
                    self.assertGreater(metrics['variance_loss'], 0)
                    self.assertEqual(metrics['h1_count'], 4)
                    self.assertEqual(metrics['h2_count'], int(batch['valid'][:, 2].sum()))
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
                        with self.subTest(regime=regime, variant=variant, tensor=key):
                            self.assertAlmostEqual(numeric, analytic, delta=2e-6 * (1+abs(numeric)))
                for key in target_before:
                    np.testing.assert_array_equal(model.target[key], target_before[key])

    def test_reply_mask_preserves_own_action_and_recurrence(self):
        batch = fixture()
        model = Model(small_config('raw-no-response'))
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
        ordinary = Model(small_config('raw-jepa'))
        self.assertFalse(np.allclose(ordinary.rollout(z, batch['actions']), ordinary.rollout(z, changed_reply['actions'])))

    def test_missing_horizon_and_terminal_soft_policy(self):
        batch = fixture()
        batch['valid'][:, 2] = False
        batch['x'][:, 2] = 0
        batch['value'][:, 2] = 0
        batch['policy'][:, 1:] = 0
        batch['legal'][:, 1:] = False
        batch['actions'][:, 1] = 0
        batch['value_labelled'] = batch['valid'].copy()
        batch['policy_labelled'] = batch['legal'].any(-1)
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
        for variant in ('raw-jepa', 'decoded'):
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
        config = small_config('ema-value')
        identity = {'source': 'fixture-source', 'dataset': 'fixture-data', 'objective': 'fixture-v22', 'mask_sha256': 'fixed-sparse-mask'}
        batch = mixed_fixture()
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
                Model.load(path, config, dict(identity, mask_sha256='different-mask'))
            with np.load(path, allow_pickle=False) as source:
                arrays = {key: source[key].copy() for key in source.files}
            arrays['t_vw'][0, 0] += .1
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
            with mock.patch('two_player_v22.model.os.replace', side_effect=OSError('injected rename failure')):
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
