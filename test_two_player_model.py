import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from two_player.data import generate, audit
from two_player.games import GAMES, State
from two_player.model import Model, Config, VARIANTS, batch_arrays
from two_player.train import train_epoch, train
from two_player.evaluate import plan, schedule, representation, evaluate


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,_=audit(generate(8,39),'middle-late')
        cls.records=cls.records[:24]

    def test_all_variant_gradients_and_stop_gradient(self):
        batch=batch_arrays(self.records)
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                model=Model(Config(variant=variant,latent=4)); rng=np.random.default_rng(2)
                targets={k:v.copy() for k,v in model.target.items()}
                _,grad=model.loss_grad(batch)
                for key,param in model.params.items():
                    direction=rng.normal(size=param.shape); direction/=np.linalg.norm(direction)
                    old=param.copy(); eps=1e-5
                    param[:]=old+eps*direction; high=model.loss_grad(batch)[0]['loss']
                    param[:]=old-eps*direction; low=model.loss_grad(batch)[0]['loss']
                    param[:]=old
                    self.assertAlmostEqual((high-low)/(2*eps),float(np.sum(grad[key]*direction)),places=7,msg=key)
                for key in targets: np.testing.assert_array_equal(targets[key],model.target[key])

    def test_missing_horizon_and_response_mask(self):
        terminal=[r for r in self.records if r['future2'] is None]
        self.assertTrue(terminal)
        model=Model(); metrics,grad=model.loss_grad(batch_arrays(terminal))
        self.assertEqual(metrics['h2_count'],0)
        batch=batch_arrays(self.records)
        model=Model(Config(variant='no-response',latent=4))
        _,grad=model.loss_grad(batch)
        np.testing.assert_array_equal(grad['gw'][4+65:4+130],0)
        self.assertGreater(np.linalg.norm(grad['gw'][4:4+65]),0)
        broken=dict(self.records[0]); broken['value']=float('nan')
        with self.assertRaises(ValueError): batch_arrays([broken])

    def test_atomic_serialization_resume_and_identity(self):
        config=Config(latent=4,batch_size=8); identity={'data':'fixture','source':'test'}
        uninterrupted=Model(config); train_epoch(uninterrupted,self.records)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'model.npz'; uninterrupted.save(path,identity)
            resumed=Model.load(path,config,identity)
            for group in ('params','target','m','v'):
                for k,v in getattr(resumed,group).items(): np.testing.assert_array_equal(v,getattr(uninterrupted,group)[k])
            train_epoch(uninterrupted,self.records); train_epoch(resumed,self.records)
            self.assertEqual(uninterrupted.step,resumed.step)
            for k,v in resumed.params.items(): np.testing.assert_array_equal(v,uninterrupted.params[k])
            with self.assertRaises(ValueError): Model.load(path,config,{'data':'other'})
            with self.assertRaises(ValueError): Model.load(path,Config(variant='direct',latent=4,batch_size=8),identity)
            with np.load(path,allow_pickle=False) as archive: payload={k:archive[k] for k in archive.files}
            payload['p_ew'][0,0]+=.1; np.savez(path,**payload)
            with self.assertRaisesRegex(ValueError,'checksum'): Model.load(path,config,identity)
            self.assertEqual(list(Path(tmp).glob('*.tmp')),[])

    def test_search_terminal_perspective_budget_and_zero_baseline(self):
        game=GAMES['tic-tac-toe']; state=State((1,1,0,-1,-1,0,0,0,0),1)
        for variant in VARIANTS:
            for track in ('exact','hybrid'):
                result=plan(game,state,Model(Config(variant=variant)),track)
                self.assertEqual(result['status'],'complete'); self.assertEqual(result['action'],2)
        swapped=State(tuple(-x for x in state.board),-1)
        self.assertEqual(plan(game,swapped)['action'],2)
        self.assertEqual(plan(game,state,node_limit=1)['status'],'censored_budget')
        for model in (None,Model(Config(variant='direct'))):
            result=plan(game,game.initial(),model,node_limit=81,time_limit=10.)
            self.assertEqual(result['status'],'complete'); self.assertEqual(result['nodes'],81)

    def test_schedule_and_metrics_are_finite(self):
        positions=schedule(self.records)
        self.assertEqual(positions,schedule(list(reversed(self.records))))
        result=representation(Model(),self.records)
        json.dumps(result,allow_nan=False)
        self.assertGreater(result['effective_rank'],0)

    def test_identity_change_deadline_and_collapsed_planning_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('two_player.train.load_dataset',return_value=(self.records,'changed')):
                with self.assertRaisesRegex(ValueError,'schedule freeze'):
                    train('fixture',Path(tmp)/'run',Config(),expected_identity={'dataset_fingerprint':'frozen','source_sha256':'frozen'})
        model=Model()
        with self.assertRaises(TimeoutError): train_epoch(model,self.records,deadline=0)
        self.assertEqual(model.step,0)
        model.params['ew'][:]=0; model.params['eb'][:]=0
        result=evaluate(model,self.records,schedule(self.records))
        self.assertEqual(result['planning_status'],'blocked_collapse')
        self.assertEqual(result['decisions'],[])


if __name__=='__main__': unittest.main()
