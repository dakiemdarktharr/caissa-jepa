"""Synthetic legal diagnostics: no research checkpoint or experimental fitting."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import numpy as np

from test_v25_data import fixture
from two_player_v22.data import batch_arrays
from two_player_v25.data import build_groups
from two_player_v25.model import Model, Config
from two_player_v25.metrics import diagnostics


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev=fixture('development')
        cls.groups=build_groups(cls.dev)
        cls.base=batch_arrays(cls.dev,range(len(cls.dev['forks'])))
        # Fixture labels are synthetic, not solved. Make their root action
        # labels exactly consistent with the fixture's declared leaf labels.
        roots={r['root_id']:r for r in cls.dev['roots']}
        for group in cls.groups['groups']:
            ids=group['fork_indices']; first=ids[0]
            value=(-float(cls.base['value'][first,1,0]) if not cls.base['valid'][first,2]
                   else min(float(cls.base['value'][i,2,0]) for i in ids))
            root=roots[group['root_id']]
            root['oracle_values'][root['actions'].index(group['own_action'])]=value

    def test_actual_complete_groups_and_conditional_bounds_all_variants(self):
        for name in ('direct','recurrent-pv','decoded-tail','scalar-tail','raw-mean','raw-tail','raw-scaled'):
            model=Model(Config(variant=name))
            before={k:v.copy() for k,v in model.params.items()}
            occurrence,result=diagnostics(model,self.dev,self.base,self.groups,lambda:None)
            self.assertEqual(set(occurrence),{'connect4-4x5','reversi6'})
            self.assertEqual(result['stage'],'development')
            self.assertAlmostEqual(result['head_norm'],np.linalg.norm(model.params['vw']))
            for game,item in result['games'].items():
                expected=[g for g in self.groups['groups'] if g['game']==game]
                self.assertEqual(item['group_count'],len(expected))
                self.assertEqual(item['unique_node_geometry']['samples'],sum(n['game']==game for n in self.dev['nodes'].values()))
                for row,group in zip(item['groups'],expected):
                    self.assertEqual(row['full_fork_rows'],len(group['fork_indices']))
                    if name=='direct':
                        self.assertIsNone(row['predicted_min'])
                        self.assertIsNone(row['conditional_oracle_bound'])
                    else:
                        self.assertLessEqual(abs(row['predicted_min_oracle_bias']),row['conditional_oracle_bound']+1e-9)
            for key in before: np.testing.assert_array_equal(model.params[key],before[key])

    def test_direct_unused_transition_and_failure_contracts(self):
        model=Model(Config(variant='direct'))
        with patch.object(model,'rollout',side_effect=AssertionError('Direct rollout forbidden')):
            diagnostics(model,self.dev,self.base,self.groups,lambda:None)
        corrupt=deepcopy(self.dev); corrupt['manifest']['split']='final'
        with self.assertRaises(ValueError): diagnostics(model,corrupt,self.base,self.groups,lambda:None)
        with self.assertRaises(TimeoutError):
            diagnostics(model,self.dev,self.base,self.groups,lambda:(_ for _ in ()).throw(TimeoutError()))
        model.params['vw'][0,0]=np.nan
        with self.assertRaises(ValueError): diagnostics(model,self.dev,self.base,self.groups,lambda:None)

    def test_zero_head_target_max_error_not_mse_and_unique_node_collapse(self):
        model=Model(Config(variant='raw-tail'))
        model.params['vw'][:]=0.; model.params['vb'][:]=0.
        _,report=diagnostics(model,self.dev,self.base,self.groups,lambda:None)
        self.assertEqual(report['head_norm'],0.)
        for item in report['games'].values():
            for row in item['groups']:
                self.assertAlmostEqual(row['conditional_oracle_bound'],row['horizons']['2']['target_oracle_max_absolute'])
        model.params['e2w'][:]=0.; model.params['e2b'][:]=0.
        _,collapsed=diagnostics(model,self.dev,self.base,self.groups,lambda:None)
        self.assertTrue(collapsed['collapse'])

    def test_terminal_h1_oracle_mismatch_rejected_for_direct_and_recurrent(self):
        corrupt=deepcopy(self.dev)
        group=next(g for g in self.groups['groups'] if g['h1_terminal'])
        root=next(r for r in corrupt['roots'] if r['root_id']==group['root_id'])
        index=root['actions'].index(group['own_action'])
        root['oracle_values'][index]=0 if root['oracle_values'][index] else 1
        for variant in ('direct','raw-tail'):
            with self.assertRaisesRegex(ValueError,'Terminal H1 oracle'):
                diagnostics(Model(Config(variant=variant)),corrupt,self.base,self.groups,lambda:None)


if __name__=='__main__': unittest.main()
