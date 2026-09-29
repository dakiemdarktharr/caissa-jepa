"""Synthetic grouped mathematical tests; no research artifacts or training runs."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from two_player_v25.model import Config, Model, VARIANTS, _aggregate, _batch


def fixture():
    rng = np.random.default_rng(2508)
    group = np.array([0, 0, 0, 1, 1, 2], dtype=np.int64)
    n = len(group)
    x = rng.normal(0, .035, (n, 3, 198))
    valid = np.ones((n, 3), dtype=bool)
    valid[-1, 2] = False
    x[~valid] = 0
    legal = np.zeros((n, 3, 65), dtype=bool)
    policy = np.zeros((n, 3, 65))
    value = np.zeros((n, 3, 1))
    actions = np.zeros((n, 2, 65))
    for g, replies in enumerate(([2, 3, 4], [6, 7], [])):
        rows = np.flatnonzero(group == g)
        x[rows, :2] = x[rows[0], :2]
        legal[rows, 0, 0] = True
        legal[rows, 0, 1] = True
        legal[rows, 0, 8] = True
        policy[rows, 0, 0] = .2
        policy[rows, 0, 1] = .3
        policy[rows, 0, 8] = .5
        actions[rows, 0, (8, 1, 0)[g]] = 1
        value[rows, 0, 0] = (.5, -1., .25)[g]
        value[rows, 1, 0] = (-.25, .5, -1.)[g]
        for action in replies:
            legal[rows, 1, action] = True
            policy[rows, 1, action] = (action + 1) / sum(a + 1 for a in replies)
        for row, action in zip(rows, replies):
            actions[row, 1, action] = 1
            value[row, 2, 0] = (-1., .3, 1., -1., 1.)[row]
    for row in (0, 1):
        legal[row, 2, [4, 5]] = True
        policy[row, 2, [4, 5]] = [.4, .6]
    return dict(x=x, valid=valid, legal=legal, policy=policy, value=value,
                actions=actions, value_labelled=valid.copy(),
                policy_labelled=legal.any(-1), group=group)


def terminal_fixture():
    b = fixture()
    b = {key: value[[5]].copy() for key, value in b.items()}
    b['group'][:] = 0
    return b


def config(variant='raw-tail'):
    return Config(variant=variant, seed=37, hidden=6, latent=4,
                  transition_hidden=5, learning_rate=.0003, aux_weight=.3, batch_groups=3)


def tensors(model):
    return {name: {key: a.copy() for key, a in getattr(model, name).items()}
            for name in ('params', 'target', 'm', 'v')}


class V25ModelTests(unittest.TestCase):
    def test_full_group_contract_and_rejection(self):
        b = fixture()
        _batch(b)
        for mutation in ('groupdtype', 'start', 'gap', 'interleave', 'duplicate-reply',
                         'incomplete', 'root', 'h1', 'own', 'policy', 'hidden',
                         'terminal-policy', 'missing', 'complex', 'nan'):
            c = {key: a.copy() for key, a in b.items()}
            if mutation == 'groupdtype':
                c['group'] = c['group'].astype(np.int32)
            elif mutation == 'start':
                c['group'] += 1
            elif mutation == 'gap':
                c['group'][c['group'] == 2] = 3
            elif mutation == 'interleave':
                c['group'][2:4] = [1, 0]
            elif mutation == 'duplicate-reply':
                c['actions'][1, 1] = c['actions'][0, 1]
            elif mutation == 'incomplete':
                c = {key: np.delete(a, 1, axis=0) for key, a in c.items()}
            elif mutation == 'root':
                c['x'][1, 0, 0] += .1
            elif mutation == 'h1':
                c['value'][1, 1, 0] = .7
            elif mutation == 'own':
                c['actions'][1, 0] = 0
                c['actions'][1, 0, 1] = 1
            elif mutation == 'policy':
                c['policy'][0, 2, 8] = .1
            elif mutation == 'hidden':
                c['value_labelled'][0, 2] = False
                c['value'][0, 2] = 0
            elif mutation == 'terminal-policy':
                c['policy_labelled'][5, 1] = True
            elif mutation == 'missing':
                c['x'][5, 2, 0] = .1
            elif mutation == 'complex':
                c['x'] = c['x'].astype(complex)
            else:
                c['value'][0, 2, 0] = np.nan
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _batch(c)
        c = {key: a[[5, 5]].copy() for key, a in b.items()}
        c['group'][:] = 0
        with self.assertRaises(ValueError):
            _batch(c)

    def test_weighted_supervision_and_variance_denominators(self):
        b, model = fixture(), Model(config())
        metrics, _ = model.loss_grad(b)
        sizes = np.bincount(b['group'])
        w = 1 / sizes[b['group']]
        valid = b['valid']
        weights = np.broadcast_to(w[:, None], valid.shape)[valid]
        z = model.encode(b['x'][valid])
        value_error = (model.value(z)-b['value'][valid])[:, 0]**2
        self.assertAlmostEqual(metrics['value_mse'], np.sum(weights*value_error)/weights.sum())
        self.assertEqual(metrics['encoded_count'], 17)
        self.assertEqual(metrics['policy_count'], 13)
        self.assertEqual(metrics['terminal_count'], 4)
        self.assertEqual(metrics['group_count'], 3)
        self.assertAlmostEqual(metrics['encoded_weight_sum'], 8.)
        self.assertAlmostEqual(metrics['policy_weight_sum'], 5+2/3)
        mean = np.sum(weights[:, None]*z, axis=0)/weights.sum()
        std = np.sqrt(np.sum(weights[:, None]*(z-mean)**2, axis=0)/weights.sum()+1e-4)
        self.assertAlmostEqual(metrics['variance_loss'], .1*np.mean(np.maximum(0, .1-std)**2))
        root = model.encode(b['x'][:, 0])
        for h in (1, 2):
            mask = valid[:, h]
            pred = model.rollout(root, b['actions'], h)[mask]
            error = (model.value(pred)-b['value'][mask, h])[:, 0]**2
            self.assertAlmostEqual(metrics[f'h{h}_value_mse'], np.sum(w[mask]*error)/w[mask].sum())
        self.assertEqual(metrics['h1_aux_group_count'], 2)
        self.assertEqual(metrics['h1_aux_row_count'], 2)
        self.assertEqual(metrics['h1_aux_eligible_row_count'], 5)
        self.assertEqual(metrics['h2_aux_group_count'], 1)
        self.assertEqual(metrics['h2_aux_row_count'], 2)
        self.assertEqual(metrics['h2_aux_excluded_group_count'], 2)
        self.assertAlmostEqual(metrics['h1_value_weight_sum'], 3)
        self.assertAlmostEqual(metrics['h2_value_weight_sum'], 2)
        self.assertAlmostEqual(metrics['h2_policy_weight_sum'], 2/3)

    def test_all_tensor_finite_differences_with_detached_branches(self):
        rng = np.random.default_rng(2509)
        for variant in VARIANTS:
            model, batch = Model(config(variant)), fixture()
            for key in ('e1w', 'e2b'):
                model.target[key] += .015
            before = tensors(model)
            detached = model.detached_context(batch)
            normal, gradients = model.loss_grad(batch)
            base, frozen_grad = model.loss_grad(batch, detached=detached)
            self.assertAlmostEqual(normal['loss'], base['loss'], delta=1e-13)
            for key, parameter in model.params.items():
                np.testing.assert_allclose(gradients[key], frozen_grad[key], atol=1e-13, rtol=1e-13)
                directions = [rng.normal(size=parameter.shape)]
                coordinate = np.zeros_like(parameter)
                coordinate.flat[np.argmax(np.abs(gradients[key]))] = 1
                directions.append(coordinate)
                for direction in directions:
                    direction /= np.linalg.norm(direction)
                    original = parameter.copy()
                    parameter[...] = original + 1e-6*direction
                    plus = model.loss_grad(batch, detached=detached)[0]['loss']
                    parameter[...] = original - 1e-6*direction
                    minus = model.loss_grad(batch, detached=detached)[0]['loss']
                    parameter[...] = original
                    numeric = (plus-minus)/2e-6
                    analytic = float(np.sum(gradients[key]*direction))
                    with self.subTest(variant=variant, tensor=key):
                        self.assertAlmostEqual(numeric, analytic, delta=3e-6*(1+abs(numeric)))
            for name, values in before.items():
                for key, expected in values.items():
                    np.testing.assert_array_equal(getattr(model, name)[key], expected)
            self.assertEqual(model.step, 0)

    def test_recurrent_soft_policy_gradient_has_its_own_weighted_denominators(self):
        b = fixture()
        w = 1 / np.bincount(b['group'])[b['group']]
        masks = b['policy_labelled']
        probability = b['legal'] / np.maximum(1, b['legal'].sum(-1, keepdims=True))
        residual = probability-b['policy']
        occurrence = np.broadcast_to(w[:, None], masks.shape)
        encoded = np.sum(occurrence[masks, None]*residual[masks], axis=0)/occurrence[masks].sum()
        recurrent = np.zeros(65)
        for h in (1, 2):
            mask = masks[:, h]
            recurrent += .25*np.sum(w[mask, None]*residual[mask, h], axis=0)/w[mask].sum()
        for variant in VARIANTS:
            model = Model(config(variant))
            model.params['pw'][:] = 0
            model.params['pb'][:] = 0
            _, grad = model.loss_grad(b)
            np.testing.assert_allclose(grad['pb'], encoded+(0 if variant == 'direct' else recurrent), atol=1e-14)

    def test_sampler_to_model_legal_synthetic_integration(self):
        from test_v25_data import fixture as legal_fixture
        from two_player_v22.data import batch_arrays
        from two_player_v25.data import build_groups, epoch_plan, make_batch
        dataset = legal_fixture(extra_root=True)
        receipt = build_groups(dataset)
        base = batch_arrays(dataset, range(len(dataset['forks'])))
        ids, transforms, _ = epoch_plan(receipt, 17, 0)
        for offset in (0, 64):
            batch = make_batch(base, receipt, ids[offset:offset+32], transforms[offset:offset+32])
            _batch(batch)
            for variant in VARIANTS:
                model = Model(config(variant))
                result = model.update(batch)
                self.assertEqual(result['group_count'], min(32, len(ids)-offset))
                self.assertTrue(np.isfinite(result['loss']))

    def test_tail_ties_scaled_forward_and_detached_allocation(self):
        errors = np.array([1., 1., 1., .1, .5])
        groups = np.array([0, 0, 0, 1, 1])
        tail, gradient = _aggregate(errors, groups, 'tail')
        self.assertAlmostEqual(tail, .7)
        np.testing.assert_allclose(gradient, [1/6, 1/6, 1/6, .125, .375])
        # Verify the convex subgradient inequality at a three-way exact tie.
        rng = np.random.default_rng(2510)
        for _ in range(30):
            alternative = rng.uniform(0, 2, 5)
            self.assertGreaterEqual(_aggregate(alternative, groups, 'tail')[0] + 1e-14,
                                    tail + gradient @ (alternative-errors))
        scaled, allocation = _aggregate(errors, groups, 'scaled')
        self.assertAlmostEqual(scaled, tail)
        np.testing.assert_allclose(allocation[:3], [1/6]*3)
        np.testing.assert_allclose(allocation[3:], [1/3]*2)
        self.assertFalse(np.allclose(allocation, gradient))
        loss, weight = _aggregate(np.zeros(3), np.zeros(3, dtype=int), 'scaled')
        self.assertEqual(loss, 0)
        np.testing.assert_array_equal(weight, np.zeros(3))
        for mode in ('mean', 'tail', 'scaled'):
            self.assertEqual(_aggregate(np.array([]), np.array([], int), mode)[0], 0)
        b = fixture()
        a, s = Model(config('raw-tail')), Model(config('raw-scaled'))
        ma, ga = a.loss_grad(b)
        ms, gs = s.loss_grad(b)
        self.assertAlmostEqual(ma['loss'], ms['loss'])
        self.assertAlmostEqual(ma['h1_loss'], ms['h1_loss'])
        self.assertAlmostEqual(ma['h2_loss'], ms['h2_loss'])
        self.assertGreater(np.linalg.norm(ga['g2w']-gs['g2w']), 1e-9)

    def test_scaled_factor_and_exact_tie_diagnostics(self):
        b, model = fixture(), Model(config('raw-scaled'))
        m, _ = model.loss_grad(b)
        factors = model.detached_context(b)['scaled_factors']
        self.assertEqual(m['h2_scaled_factor_count'], 1)
        self.assertEqual(m['h2_scaled_factor_nonzero_count'], 1)
        self.assertAlmostEqual(m['h2_scaled_factor_sum'], factors[0])
        self.assertAlmostEqual(m['h2_scaled_factor_mean'], factors[0])
        self.assertAlmostEqual(m['h2_scaled_factor_min'], factors[0])
        self.assertAlmostEqual(m['h2_scaled_factor_max'], factors[0])
        self.assertGreaterEqual(factors[0], 1.)
        self.assertLessEqual(factors[0], 1.5)
        self.assertEqual(m['h2_scaled_factor_clip_count'], 0)
        for key in ('e2w', 'e2b', 'g2w', 'g2b'):
            model.params[key][:] = 0
            if key in model.target:
                model.target[key][:] = 0
        m, _ = model.loss_grad(b)
        self.assertEqual(m['h2_max_tie_group_count'], 1)
        self.assertEqual(m['h2_max_tie_member_count'], 2)
        self.assertEqual(m['h2_scaled_factor_count'], 1)
        self.assertEqual(m['h2_scaled_factor_nonzero_count'], 0)
        for key in ('sum', 'mean', 'min', 'max'):
            self.assertEqual(m['h2_scaled_factor_'+key], 0.)
        absent = model.loss_grad(terminal_fixture())[0]
        self.assertEqual(absent['h2_scaled_factor_count'], 0)
        self.assertEqual(absent['h2_scaled_factor_min'], 0.)
        self.assertEqual(absent['h2_scaled_factor_max'], 0.)

    def test_same_online_scalar_head_target_is_wholly_detached(self):
        b, model = fixture(), Model(config('scalar-tail'))
        model.target['vw'][:] = 900
        model.target['vb'][:] = -900
        context = model.detached_context(b)
        expected = model.value(model.encode(b['x'][b['valid']], target=True))
        np.testing.assert_array_equal(context['scalar_targets'][b['valid']], expected)
        metrics, gradient = model.loss_grad(b)
        before = metrics.copy()
        model.target['vw'][:] = -100
        model.target['vb'][:] = 100
        self.assertEqual(before, model.loss_grad(b)[0])
        # Test the head direction specifically: numerical target remains frozen.
        for key in ('vw', 'vb'):
            initial = model.params[key].copy()
            direction = np.ones_like(initial)
            model.params[key][...] = initial + 1e-6*direction
            plus = model.loss_grad(b, detached=context)[0]['loss']
            model.params[key][...] = initial - 1e-6*direction
            minus = model.loss_grad(b, detached=context)[0]['loss']
            model.params[key][...] = initial
            self.assertAlmostEqual((plus-minus)/2e-6, float(np.sum(gradient[key])), delta=2e-6)

    def test_terminal_auxiliary_exclusion_missing_h2_and_soft_targets(self):
        b = terminal_fixture()
        for variant in VARIANTS:
            model = Model(config(variant))
            model.params['pw'][:] = 0
            model.params['pb'][:] = 0
            m, g = model.loss_grad(b)
            self.assertEqual(m['h2_count'], 0)
            self.assertEqual(m['h2_missing_count'], 1)
            self.assertEqual(m['h2_loss'], 0)
            self.assertEqual(m['h2_value_loss'], 0)
            self.assertEqual(m['h1_aux_group_count'], 0)
            self.assertEqual(m['h1_loss'], 0)
            self.assertEqual(m['h1_policy_loss'], 0)
            self.assertEqual(m['value_count'], 2)
            self.assertEqual(m['policy_count'], 1)
            self.assertAlmostEqual(m['policy_nll'], np.log(3))
            target = np.zeros(65)
            target[[0, 1, 8]] = 1/3-np.array([.2, .3, .5])
            np.testing.assert_allclose(g['pb'], target, atol=1e-14)
            if variant != 'direct':
                self.assertGreater(m['h1_value_loss'], 0)

    def test_direct_does_not_compute_recurrence_targets_or_decoder(self):
        model = Model(config('direct'))
        with mock.patch.object(model, '_transition', side_effect=AssertionError('recurrent call')):
            metrics, gradient = model.loss_grad(fixture())
        self.assertEqual(metrics['variance_loss'], 0)
        self.assertEqual(metrics['h1_count'], 0)
        self.assertEqual(metrics['h2_count'], 0)
        for key in ('g1w', 'g1b', 'g2w', 'g2b', 'dw', 'db'):
            np.testing.assert_array_equal(gradient[key], np.zeros_like(gradient[key]))

    def test_group_replication_and_member_order_invariance(self):
        b = fixture()
        permutation = [2, 0, 1, 4, 3, 5]
        shuffled = {key: a[permutation].copy() for key, a in b.items()}
        doubled = {key: np.concatenate((a, a), axis=0) for key, a in b.items()}
        doubled['group'][len(b['group']):] += 3
        for variant in VARIANTS:
            model = Model(config(variant))
            base, gradient = model.loss_grad(b)
            for other in (shuffled, doubled):
                m, g = model.loss_grad(other)
                self.assertAlmostEqual(base['loss'], m['loss'], delta=1e-13)
                for key in g:
                    np.testing.assert_allclose(gradient[key], g[key], atol=1e-13, rtol=1e-12)

    def test_two_layer_rollout_and_both_action_inputs(self):
        model, b = Model(config()), fixture()
        p = model.params
        z = model.encode(b['x'][:, 0])
        h1 = np.tanh(np.tanh(np.concatenate((z, b['actions'][:, 0]), axis=1) @ p['g1w'] + p['g1b']) @ p['g2w'] + p['g2b'])
        h2 = np.tanh(np.tanh(np.concatenate((h1, b['actions'][:, 1]), axis=1) @ p['g1w'] + p['g1b']) @ p['g2w'] + p['g2b'])
        np.testing.assert_array_equal(model.rollout(z, b['actions'], 1), h1)
        np.testing.assert_array_equal(model.rollout(z, b['actions'], 2), h2)
        for horizon in (0, 3, True):
            with self.assertRaises(ValueError):
                model.rollout(z, b['actions'], horizon)
        for slot in (0, 1):
            changed = b['actions'].copy()
            changed[:, slot] = np.roll(changed[:, slot], 1, axis=1)
            self.assertFalse(np.allclose(model.rollout(z, changed), h2))

    def test_initialization_counts_adam_ema_and_dormant_tensors(self):
        base = Model(config())
        self.assertFalse(hasattr(base, 'project'))
        self.assertEqual(Model().parameter_counts()['transition'], 9764)
        for variant in VARIANTS:
            model = Model(config(variant))
            for key, a in base.params.items():
                np.testing.assert_array_equal(model.params[key], a)
            counts = model.parameter_counts()
            if variant == 'decoded-tail':
                self.assertEqual(counts['active'], counts['allocated'])
            else:
                self.assertLess(counts['active'], counts['allocated'])
            before = tensors(model)
            metrics = model.update(fixture())
            self.assertEqual(model.step, 1)
            self.assertGreater(metrics['gradient_norm'], 0)
            for key in model.target:
                np.testing.assert_allclose(model.target[key], .99*before['target'][key]+.01*model.params[key], atol=2e-16)
            for key in ('dw', 'db'):
                if variant != 'decoded-tail':
                    np.testing.assert_array_equal(model.params[key], before['params'][key])
            if variant == 'direct':
                for key in ('g1w', 'g1b', 'g2w', 'g2b'):
                    np.testing.assert_array_equal(model.params[key], before['params'][key])

    def test_atomic_checkpoint_roundtrip_identity_and_tamper(self):
        identity = {'source': 'synthetic-source', 'data': 'synthetic-grouped', 'group': 'draw-fingerprint'}
        b = fixture()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'checkpoint.npz'
            for variant in VARIANTS:
                model = Model(config(variant))
                model.update(b)
                model.epoch = 1
                model.save(path, identity)
                restored = Model.load(path, model.config, identity)
                self.assertEqual(restored.step, 1)
                self.assertEqual(restored.epoch, 1)
                for name, group in tensors(model).items():
                    for key, a in group.items():
                        np.testing.assert_array_equal(getattr(restored, name)[key], a)
                # Runtime is fresh-only; this validates serialized Adam, not permission to resume grid cells.
                self.assertEqual(model.update(b), restored.update(b))
                for key in model.params:
                    np.testing.assert_array_equal(model.params[key], restored.params[key])
            with self.assertRaises(ValueError):
                Model.load(path, model.config, {**identity, 'group': 'different'})
            with self.assertRaises(ValueError):
                Model.load(path, replace(model.config, learning_rate=.002), identity)
            before = path.read_bytes()
            with mock.patch('two_player_v25.model.os.replace', side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):
                    model.save(path, identity)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list(Path(folder).iterdir())), 1)
            with np.load(path, allow_pickle=False) as file:
                original = {key: file[key].copy() for key in file.files}
            for attack in ('hash', 'negative-v', 'shape', 'dtype', 'inventory', 'method', 'counter'):
                arrays = {key: a.copy() for key, a in original.items()}
                meta = json.loads(str(arrays['metadata']))
                if attack == 'hash':
                    arrays['p_vb'][0] += .1
                elif attack == 'negative-v':
                    arrays['v_vb'][0] = -1
                    meta['array_hashes']['v_vb'] = hashlib.sha256(arrays['v_vb'].tobytes()).hexdigest()
                elif attack == 'shape':
                    arrays['p_vb'] = np.zeros(2)
                elif attack == 'dtype':
                    arrays['p_vb'] = arrays['p_vb'].astype(np.float32)
                elif attack == 'inventory':
                    arrays['extra'] = np.zeros(1)
                elif attack == 'method':
                    meta['method'] = 'old'
                else:
                    meta['step'] = True
                arrays['metadata'] = np.array(json.dumps(meta))
                np.savez_compressed(path, **arrays)
                with self.subTest(attack=attack), self.assertRaises(ValueError):
                    Model.load(path, model.config, identity)

    def test_config_and_nonfinite_updates_fail_before_mutation(self):
        for update in ({'variant': 'raw-jepa'}, {'latent': True}, {'seed': -1},
                       {'batch_groups': 0}, {'ema': 1.}, {'learning_rate': np.nan}, {'aux_weight': -1}):
            with self.assertRaises(ValueError):
                Config(**update)
        model = Model(config())
        before = tensors(model)
        metrics, gradient = model.loss_grad(fixture())
        gradient['vb'][0] = np.nan
        with mock.patch.object(model, 'loss_grad', return_value=(metrics, gradient)):
            with self.assertRaises(FloatingPointError):
                model.update(fixture())
        for name, group in before.items():
            for key, a in group.items():
                np.testing.assert_array_equal(getattr(model, name)[key], a)
        self.assertEqual(model.step, 0)


if __name__ == '__main__':
    unittest.main()
