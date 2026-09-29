"""Small legal transition fixtures with synthetic nonterminal labels; no research data."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import numpy as np

from two_player_v22.model import Model, Config
from two_player_v24_probe import core


def fixture(games=('connect4-4x5', 'reversi6')):
    train = {'manifest': {'split': 'train', 'role': 'redacted-training', 'fraction': 1.},
             'roots': [], 'nodes': {}, 'forks': []}
    for name in games:
        game = core.GAMES_V2[name]
        initial = game.initial()
        states = [initial]
        if name == 'connect4-4x5':
            s = initial
            for i, action in enumerate((24, 16, 25, 17, 26, 18)):
                s = game.transition(s, action)
                if i in (1, 5): states.append(s)
        else:
            for a in game.legal_actions(initial):
                child = game.transition(initial, a)
                for b in game.legal_actions(child):
                    state = game.transition(child, b)
                    if state not in states: states.append(state)
        def node(state):
            obj = {'board': list(state.board), 'player': state.player}
            nid = core.digest([name, obj])
            terminal = game.terminal(state)
            train['nodes'][nid] = {'game': name, 'state': obj, 'terminal': terminal is not None,
                'legal': list(game.legal_actions(state)), 'value': terminal*state.player if terminal is not None else 0,
                'value_labelled': True, 'policy_labelled': terminal is None}
            return nid
        for state in states:
            source = node(state); rid = core.digest(['root', name, source])
            train['roots'].append({'game': name, 'root_id': rid, 'split': 'train',
                                   'state': train['nodes'][source]['state'], 'actions': list(game.legal_actions(state))})
            for action in game.legal_actions(state):
                after = game.transition(state, action); target = node(after)
                replies = list(game.legal_actions(after))[:2] or [None]
                for reply in replies:
                    end = node(game.transition(after, reply)) if reply is not None else None
                    train['forks'].append({'game': name, 'root_id': rid, 'split': 'train',
                        'node_ids': [source, target, end], 'actions': [action, reply]})
    return train


class PackingTests(unittest.TestCase):
    def test_legal_edges_disjoint_deterministic_outcome_blind(self):
        train = fixture(); calls = []
        schedule = core.build_schedule(train, lambda: calls.append(1))
        self.assertGreater(len(calls), 5)
        changed = deepcopy(train)
        changed['roots'].reverse(); changed['forks'].reverse()
        again = core.build_schedule(changed, lambda: None)
        self.assertEqual(schedule, again)
        for node in changed['nodes'].values():
            if not node['terminal']: node['value'] = 1
        altered = core.build_schedule(changed, lambda: None)
        for game, group in schedule['games'].items():
            ids = [i for b in group['blocks'] for i in b['edges']]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertGreater(len(group['blocks']), 0)
            self.assertEqual(group['blocks'], altered['games'][game]['blocks'])
            self.assertEqual(group['counts']['used_edges'], 4*len(group['blocks']))
            self.assertEqual(len(group['edges']), sum(len(r['actions']) for r in train['roots'] if r['game'] == game))
            for block in group['blocks']:
                _, _, r1, r2, a, b = block['identity']
                self.assertEqual([(group['edges'][i]['root_id'], group['edges'][i]['action']) for i in block['edges']],
                                 [(r1, a), (r2, a), (r1, b), (r2, b)])

    def test_bad_duplicate_edge_illegal_transition_and_guard(self):
        train = fixture(('connect4-4x5',))
        corrupt = deepcopy(train)
        row = deepcopy(corrupt['forks'][0]); row['node_ids'][1] = row['node_ids'][0]
        corrupt['forks'].append(row)
        with self.assertRaisesRegex(ValueError, 'Repeated H1'): core.build_schedule(corrupt, lambda: None)
        corrupt = deepcopy(train); corrupt['forks'][0]['actions'][0] = 0
        with self.assertRaises(ValueError): core.build_schedule(corrupt, lambda: None)
        def stop(): raise TimeoutError('bounded')
        with self.assertRaises(TimeoutError): core.build_schedule(train, stop)

    def test_terminal_value_is_successor_perspective(self):
        train = fixture(('connect4-4x5',)); schedule = core.build_schedule(train, lambda: None)
        terminals = [e for e in schedule['games']['connect4-4x5']['edges'] if e['target_terminal']]
        self.assertTrue(terminals)
        self.assertTrue(all(e['target_value'] == -1 for e in terminals))
        corrupt = deepcopy(train); corrupt['nodes'][terminals[0]['target_id']]['value'] = 1
        with self.assertRaisesRegex(ValueError, 'perspective'): core.build_schedule(corrupt, lambda: None)


class MeasurementTests(unittest.TestCase):
    def test_exact_statepair_bound_normalization_and_overlapping_categories(self):
        target = np.array([[.8, 0., .5e-7], [.3, 0., -.5e-7], [-.2, 1e-7, -.5e-7], [.7, -1e-7, .5e-7]], dtype=np.float64)
        pred = np.zeros_like(target); oracle = np.zeros(4); tv = target[:, 0]; pv = np.zeros(4)
        full = core._summary(range(4), target, pred, tv, pv, oracle)
        packed = core._packed([{'edges': [0, 1, 2, 3]}], target, pred, tv, pv, oracle, full, 2.)
        expected = .5**2/2+(1e-7)**2/2
        self.assertAlmostEqual(packed['bound_sse'], expected, places=14)
        self.assertAlmostEqual(packed['bound_mse'], expected/12)
        self.assertEqual(packed['reversals_strict'], 2)
        self.assertEqual(packed['reversals_1e6'], 1)
        self.assertEqual(packed['near_ties_1e6'], 2)
        da, db = target[0]-target[1], target[2]-target[3]
        np.testing.assert_array_equal(packed['absolute_gap_quantiles'], np.quantile(np.abs(np.r_[da, db]), core.QUANTILES))
        with self.assertRaisesRegex(ValueError, 'bound exceeds'):
            core._packed([{'edges': [0, 1, 2, 3]}], target, target.copy(), tv, tv, oracle, full, 2.)

    def test_all_families_online_ema_and_read_only(self):
        train = fixture(); schedule = core.build_schedule(train, lambda: None)
        for variant in ('direct', 'value-dynamics', 'raw-jepa'):
            model = Model(Config(variant=variant, hidden=6, latent=4, projection=3))
            model.target['e2b'] += .2
            before = core._tensor_identity(model)
            if variant == 'direct':
                with patch.object(model, 'rollout', side_effect=AssertionError('Direct rollout forbidden')):
                    result = core.measure(model, train, schedule, lambda: None)
            else:
                result = core.measure(model, train, schedule, lambda: None)
            self.assertEqual(core._tensor_identity(model), before)
            self.assertEqual(len(result['rows']), 4)
            self.assertEqual({r['target_space'] for r in result['rows']}, {'online', 'ema'})
            self.assertNotEqual(result['rows'][0]['all_h1']['target_value_oracle_mse'], result['rows'][1]['all_h1']['target_value_oracle_mse'])
            for row in result['rows']:
                packed = row['packed']; group = schedule['games'][row['game']]
                self.assertEqual(packed['edge_count'], group['counts']['used_edges'])
                self.assertEqual(row['packed_nonterminal']['edge_count'], group['counts']['used_nonterminal_edges'])
                if variant == 'direct':
                    self.assertIsNone(row['all_h1']['latent_sse'])
                    self.assertIsNone(packed['bound_full_sse_ratio'])
                    self.assertIsNone(row['predicted_order_violations'])
                else:
                    self.assertEqual(row['predicted_order_violations'], 0)
                    self.assertLessEqual(packed['bound_sse'], packed['latent_sse']+1e-10)

    def test_no_blocks_explicitly_unsupported_and_direct_nulls(self):
        train = fixture(('connect4-4x5',)); rid = train['roots'][0]['root_id']
        train['roots'] = train['roots'][:1]; train['forks'] = [f for f in train['forks'] if f['root_id'] == rid]
        schedule = core.build_schedule(train, lambda: None)
        self.assertEqual(schedule['games']['connect4-4x5']['counts']['selected_blocks'], 0)
        for v in ('direct', 'raw-jepa'):
            result = core.measure(Model(Config(variant=v, hidden=6, latent=4, projection=3)), train, schedule, lambda: None)
            for row in result['rows']:
                p = row['packed']
                self.assertEqual(p['bound_sse'], 0.)
                self.assertEqual(p['full_bound_mse'], 0.)
                self.assertIsNone(p['bound_mse']); self.assertIsNone(p['bound_full_sse_ratio'])
                self.assertIsNone(p['absolute_gap_quantiles'])
                self.assertEqual(p['latent_sse'], None if v == 'direct' else 0.)

    def test_report_integration_all_frozen_configurations_on_legal_fixture(self):
        from two_player_v24_probe.report import summarize
        train = fixture(); schedule = core.build_schedule(train, lambda: None); rows = []
        for hidden, latent in ((64, 32), (128, 64)):
            for variant in ('direct', 'value-dynamics', 'raw-jepa'):
                for seed in (17, 29, 43):
                    model = Model(Config(variant=variant, hidden=hidden, latent=latent, seed=seed,
                                         jepa_weight=.1 if variant == 'raw-jepa' else 1.))
                    rows.extend(core.measure(model, train, schedule, lambda: None)['rows'])
        report = summarize(rows, schedule)
        self.assertEqual(report['verification_errors'], [])
        self.assertEqual(report['status'], 'verified_probe')
        self.assertIsNone(report['candidate'])

    def test_order_violation_mutation_and_schedule_tamper_fail(self):
        train = fixture(('connect4-4x5',)); schedule = core.build_schedule(train, lambda: None)
        model = Model(Config(hidden=6, latent=4, projection=3))
        group = schedule['games']['connect4-4x5']; pred = np.zeros((len(group['edges']), 4))
        ids = group['blocks'][0]['edges']; pred[ids, 0] = [.5, -.5, -.5, .5]
        with patch.object(model, 'rollout', return_value=pred), self.assertRaisesRegex(ValueError, 'additive ordering'):
            core.measure(model, train, schedule, lambda: None)
        original = model.encode
        def mutate(*args, **kwargs):
            model.params['dw'][0, 0] += .01
            return original(*args, **kwargs)
        with patch.object(model, 'encode', side_effect=mutate), self.assertRaisesRegex(ValueError, 'mutated'):
            core.measure(model, train, schedule, lambda: None)
        changed = deepcopy(schedule); changed['games']['connect4-4x5']['blocks'][0]['edges'].reverse()
        with self.assertRaisesRegex(ValueError, 'Packing identity'):
            core.measure(model, train, changed, lambda: None)


if __name__ == '__main__': unittest.main()
