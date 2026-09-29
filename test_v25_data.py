"""Grouped sampling on synthetic legal closures; no artifact loading/fitting."""
from copy import deepcopy
import json
import unittest

import numpy as np

from test_v22_data import fixture_parent
from two_player_v22.data import _prepare, batch_arrays
from two_player_v25 import data


def fixture(split='train', extra_root=False):
    parent = fixture_parent(split)
    dataset, _ = _prepare(parent, 1., 271828, split)
    dataset['manifest'] = {'split': split, 'fraction': 1., 'dataset_fingerprint': 'synthetic-only',
                           'role': 'redacted-training' if split == 'train' else 'standalone-development'}
    if extra_root:
        root = deepcopy(dataset['roots'][0]); previous = root['root_id']
        root['root_id'] = data.digest(['extra-fixture-root', previous])
        root['trajectory'] = 'extra-fixture-trajectory'
        dataset['roots'].append(root)
        dataset['forks'].extend([{**deepcopy(f), 'root_id': root['root_id']}
                                 for f in dataset['forks'] if f['root_id'] == previous])
    return dataset


class V25DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = fixture(extra_root=True)
        cls.receipt = data.build_groups(cls.dataset)
        cls.base = batch_arrays(cls.dataset, range(len(cls.dataset['forks'])))

    def test_complete_legal_reply_order_and_structural_receipt_privacy(self):
        ordered = [(g['game'], g['root_id'], g['own_action']) for g in self.receipt['groups']]
        self.assertEqual(ordered, sorted(ordered))
        seen = []
        for group in self.receipt['groups']:
            node = self.dataset['nodes'][group['h1_id']]
            game = data.GAMES_V2[group['game']]
            expected = [None] if node['terminal'] else list(game.legal_actions(data.state(node)))
            self.assertEqual(group['reply_actions'], expected)
            self.assertEqual([self.dataset['forks'][i]['actions'][1] for i in group['fork_indices']], expected)
            self.assertEqual(group['row_count'], len(expected))
            seen.extend(group['fork_indices'])
        self.assertEqual(sorted(seen), list(range(len(self.dataset['forks']))))
        self.assertTrue(any(g['h1_terminal'] for g in self.receipt['groups']))
        self.assertTrue(any(g['own_action'] == 64 or 64 in g['reply_actions'] for g in self.receipt['groups']))
        encoded = json.dumps(self.receipt)
        for hidden in ('oracle_values', 'action_values', 'beyond_depth', 'optimal', 'target_value'):
            self.assertNotIn(hidden, encoded)

    def test_json_roundtrip_root_node_order_and_fork_reply_order(self):
        copied = json.loads(json.dumps(self.dataset))
        copied['roots'].reverse(); copied['nodes'] = dict(reversed(list(copied['nodes'].items())))
        self.assertEqual(data.build_groups(copied), self.receipt)
        copied['forks'].reverse()
        result = data.build_groups(copied)
        for original, shuffled in zip(self.receipt['groups'], result['groups']):
            self.assertEqual({k: v for k, v in original.items() if k != 'fork_indices'},
                             {k: v for k, v in shuffled.items() if k != 'fork_indices'})
        newbase = batch_arrays(copied, range(len(copied['forks'])))
        indices = np.arange(len(result['groups']), dtype=np.int64)
        expected, actual = data.make_batch(self.base, self.receipt, indices), data.make_batch(newbase, result, indices)
        for key in expected:
            np.testing.assert_array_equal(expected[key], actual[key])

    def test_sampler_balances_games_covers_roots_and_pairs_serialization(self):
        ids, transforms, receipt = data.epoch_plan(self.receipt, 17, 4)
        repeat = data.epoch_plan(json.loads(json.dumps(self.receipt)), 17, 4)
        np.testing.assert_array_equal(ids, repeat[0]); np.testing.assert_array_equal(transforms, repeat[1])
        self.assertEqual(receipt, repeat[2])
        self.assertEqual(ids.dtype, np.int64); self.assertEqual(transforms.dtype, np.int64)
        self.assertEqual(receipt['group_draws'], 72)
        self.assertEqual(receipt['sampler_namespace'], 2501); self.assertEqual(receipt['symmetry_namespace'], 2511)
        selected = [self.receipt['groups'][i] for i in ids]
        self.assertEqual({g['root_id'] for g in selected}, {r['root_id'] for r in self.dataset['roots']})
        self.assertEqual([g['group_draws'] for g in receipt['games'].values()], [36, 36])
        self.assertEqual(receipt['fork_rows'], sum(g['row_count'] for g in selected))
        self.assertEqual(receipt['h2_valid_rows']+receipt['h2_missing_rows'], receipt['fork_rows'])
        self.assertEqual(receipt['h2_nonterminal_rows']+receipt['h2_terminal_rows'], receipt['h2_valid_rows'])
        rng = np.random.default_rng(np.random.SeedSequence([17, 4, 2511]))
        wanted = [rng.integers(len(data.GAMES_V2[g['game']].transforms())) for g in selected]
        np.testing.assert_array_equal(transforms, wanted)
        self.assertNotEqual(receipt['plan_sha256'], data.epoch_plan(self.receipt, 29, 4)[2]['plan_sha256'])
        self.assertNotEqual(receipt['plan_sha256'], data.epoch_plan(self.receipt, 17, 5)[2]['plan_sha256'])

    def test_repeated_group_and_last_eight_group_batch_no_padding_or_mutation(self):
        ids, transforms, _ = data.epoch_plan(self.receipt, 17, 0)
        before = {k: v.copy() for k, v in self.base.items()}
        batches = [data.make_batch(self.base, self.receipt, ids[i:i+32], transforms[i:i+32])
                   for i in range(0, len(ids), 32)]
        self.assertEqual([len(np.unique(b['group'])) for b in batches], [32, 32, 8])
        for batch in batches:
            self.assertEqual(set(batch), data.BASE_KEYS | {'group'})
            self.assertEqual(batch['group'].dtype, np.int64)
            self.assertTrue(np.all(np.diff(batch['group']) >= 0))
            np.testing.assert_array_equal(np.unique(batch['group']), np.arange(batch['group'][-1]+1))
        repeat = data.make_batch(self.base, self.receipt, np.array([0, 0]))
        k = self.receipt['groups'][0]['row_count']
        np.testing.assert_array_equal(repeat['group'], np.repeat([0, 1], k))
        for key in self.base:
            np.testing.assert_array_equal(self.base[key], before[key])
            np.testing.assert_array_equal(repeat[key][:k], repeat[key][k:])

    def test_all_legal_transforms_preserve_actual_forks_pass_and_missing_H2(self):
        chosen = set()
        for game in data.GAMES_V2:
            candidates = [i for i, g in enumerate(self.receipt['groups']) if g['game'] == game]
            chosen.add(candidates[0])
            chosen.update(i for i in candidates if self.receipt['groups'][i]['h1_terminal']
                          or self.receipt['groups'][i]['own_action'] == 64
                          or 64 in self.receipt['groups'][i]['reply_actions'])
        for index in chosen:
            group = self.receipt['groups'][index]; game = data.GAMES_V2[group['game']]
            for transform_id, mapping in enumerate(game.transforms()):
                batch = data.make_batch(self.base, self.receipt, np.array([index]), np.array([transform_id]))
                self.assertTrue(np.all(batch['group'] == 0))
                for row, fork_index in enumerate(group['fork_indices']):
                    fork = self.dataset['forks'][fork_index]
                    for h, nid in enumerate(fork['node_ids']):
                        if nid is None:
                            self.assertFalse(batch['valid'][row, h]); self.assertTrue(np.all(batch['x'][row, h] == 0)); continue
                        original = data.state(self.dataset['nodes'][nid])
                        transformed, _ = game.transform(original, 64, mapping)
                        np.testing.assert_array_equal(batch['x'][row, h], game.features(transformed))
                        np.testing.assert_array_equal(np.flatnonzero(batch['legal'][row, h]), sorted(game.legal_actions(transformed)))
                    for h, action in enumerate(fork['actions']):
                        if action is None:
                            self.assertTrue(np.all(batch['actions'][row, h] == 0)); continue
                        original = data.state(self.dataset['nodes'][fork['node_ids'][h]])
                        transformed, mapped_action = game.transform(original, action, mapping)
                        self.assertEqual(np.flatnonzero(batch['actions'][row, h]).tolist(), [mapped_action])
                        np.testing.assert_array_equal(batch['x'][row, h+1], game.features(game.transition(transformed, mapped_action)))

    def test_protected_splits_missing_replies_and_tamper_fail_closed(self):
        for defect in ('protected', 'hidden', 'missing', 'duplicate', 'illegal'):
            dataset = deepcopy(self.dataset)
            if defect == 'protected': dataset['manifest']['split'] = 'final'
            elif defect == 'hidden': next(iter(dataset['nodes'].values()))['value_labelled'] = False
            elif defect == 'missing': dataset['forks'].pop()
            elif defect == 'duplicate': dataset['forks'].append(deepcopy(dataset['forks'][0]))
            else: dataset['forks'][0]['actions'][0] = -1
            with self.subTest(defect=defect), self.assertRaises(ValueError): data.build_groups(dataset)
        altered = deepcopy(self.receipt); altered['groups'][0]['row_count'] += 1
        with self.assertRaisesRegex(ValueError, 'changed'): data.epoch_plan(altered, 17, 0)
        development = data.build_groups(fixture('development'))
        with self.assertRaisesRegex(ValueError, 'training'): data.epoch_plan(development, 17, 0)
        with self.assertRaises(ValueError): data.make_batch(self.base, self.receipt, np.array([], dtype=np.int64))
        with self.assertRaises(ValueError): data.make_batch(self.base, self.receipt, np.array([0]), np.array([99]))


if __name__ == '__main__':
    unittest.main()
