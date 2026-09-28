"""Reproductions of independent-review findings, not research results."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from main import pgnparser, vitriengine, text_thanh_move
from research_dataset import canonical_fen, game_identity, position_keys, SPLITS
from adversarial_jepa import AdversarialJEPA, ACTION_SIZE, snapshot_from_engine
from research_search import terminal_result, search_move, play_pair
from confirmatory_protocol import protocol_manifest, protocol_errors
import test_model_arena as fixtures
from adversarial_jepa import iter_dataset_games, sample_from_dataset_position


class ReviewRegressions(unittest.TestCase):
    def test_equivalent_fen_cannot_evade_identity_and_overlap(self):
        a='7k/8/8/8/8/8/P7/K7 w - - 0 1'
        b=a.replace('/8/','/44/',1)
        self.assertEqual(canonical_fen(a),canonical_fen(b))
        self.assertEqual(position_keys({'fen':a}),position_keys({'fen':b}))
        ga={'positions':[{'fen':a,'action_uci':'a2a3'}]}
        gb={'positions':[{'fen':b,'action_uci':'a2a3'}]}
        self.assertEqual(game_identity(ga),game_identity(gb))
        self.assertEqual(SPLITS,('train','validation','selection','test'))

    def test_no_response_preserves_own_action_at_h4(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=fixtures.ModelArenaTests().build_dataset(root)
            samples=[sample_from_dataset_position(p,np.random.default_rng(1)) for p in next(iter_dataset_games(data))['positions'][:3]]
            model=AdversarialJEPA(root/'m.npz',latent_size=4,variant='no-response')
            captured=[]
            original=model._predict
            def predict(z,actions,horizon):
                if horizon==4: captured.append(actions)
                return original(z,actions,horizon)
            # Evaluation invokes _predict; training has an explicit concat path.
            with patch.object(model,'_predict',side_effect=predict): model.evaluate_batch(samples)
            if captured:
                actions=captured[0]
                self.assertFalse(np.any(actions[1]))
                self.assertTrue(np.any(actions[2]))
                self.assertFalse(np.any(actions[3]))
            before=model.predictor_w4.copy()
            model.train_batch(samples)
            own_slice=slice(model.latent_size+2*ACTION_SIZE,model.latent_size+3*ACTION_SIZE)
            self.assertGreater(np.abs(model.predictor_w4[own_slice]-before[own_slice]).sum(),0)
            model.save()
            AdversarialJEPA(root/'m.npz',variant='no-response')
            with np.load(root/'m.npz',allow_pickle=False) as file:
                payload={k:file[k] for k in file.files if k!='response_mask_version'}
            np.savez(root/'old.npz',**payload)
            with self.assertRaisesRegex(ValueError,'own action'): AdversarialJEPA(root/'old.npz',variant='no-response')

    def test_deadline_forwarded_and_confirmation_blocked(self):
        class Model:
            seen=None
            def score_legal_moves(self,snapshot,legal,deadline=None):
                self.seen=deadline
                return [],[1/len(legal)]*len(legal),0
            def danh_gia_snapshot(self,snapshot): return 0
        model=Model()
        search_move(model,pgnparser().tao_snapshot_ban_dau(),{'nodes':1,'move_seconds':1})
        self.assertIsNotNone(model.seen)
        self.assertTrue(any('Independent rule' in e for e in protocol_errors(protocol_manifest(),False)))

    def test_mate_on_last_ply_is_result_not_truncation(self):
        engine=vitriengine(pgnparser().tao_snapshot_ban_dau(),.01)
        for uci in 'f2f3 e7e5 g2g4'.split(): engine.thuc_hien_nuoc_di(text_thanh_move(uci,engine.turn))
        self.assertIsNone(terminal_result(engine))
        protocol=protocol_manifest()
        protocol['openings']=[{'uci':'f2f3 e7e5 g2g4'}]
        protocol['search'].update(max_plies=1,nodes=10,move_seconds=1)
        protocol['dataset_fingerprint']='fixture'
        protocol['referee']={'sha256':'fixture'}
        protocol['models']=[{'registry_id':'h1','seed_checkpoints':{'17':{'path':'fixture','sha256':'fixture'}}}]*2
        model=MagicMock(seed=17,dataset_fingerprint='fixture',trained_steps=1)
        context=MagicMock()
        with patch('dataset_integrity.sha256_file',return_value='fixture'), patch('research_search.create_model',return_value=model), patch('confirmatory_protocol.pinned_referee',return_value=context), patch('research_search.search_move',return_value=(text_thanh_move('d8h4','black'),{'nodes':1,'timeout':False})):
            records=play_pair(protocol,0,17)
        self.assertTrue(all(r['result']=='0-1' and r['reason']=='CHECKMATE' for r in records))
        context.__enter__.return_value.evaluate.assert_not_called()


if __name__=='__main__': unittest.main()
