"""Independent tiny-rule oracle and adversarial audit regressions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from two_player.games import GAMES, State, exact_value, FEATURE_SIZE
from two_player.data import audit, generate, load_dataset, replay, write_dataset, digest


class TinyRulesTests(unittest.TestCase):
    def test_tictactoe_all_reachable_states_against_bitboard_rules(self):
        game=GAMES['tic-tac-toe']
        masks=(7,56,448,73,146,292,273,84)
        visited=set()
        def visit(state):
            if state in visited:
                return
            visited.add(state)
            plus=sum(1<<i for i,v in enumerate(state.board) if v==1)
            minus=sum(1<<i for i,v in enumerate(state.board) if v==-1)
            winner=next((p for p,bits in ((1,plus),(-1,minus)) if any(bits&m==m for m in masks)),None)
            terminal=winner if winner is not None else 0 if plus|minus==511 else None
            self.assertEqual(game.terminal(state),terminal)
            legal=tuple((i//3)*8+i%3 for i in range(9) if not ((plus|minus)&(1<<i))) if terminal is None else ()
            self.assertEqual(game.legal_actions(state),legal)
            for action in legal:
                child=game.transition(state,action)
                self.assertEqual(child.player,-state.player)
                visit(child)
        visit(game.initial())
        self.assertEqual(len(visited),5478)
        self.assertEqual(exact_value(game,game.initial()),0)

    def test_gravity_win_and_illegal_actions(self):
        game=GAMES['connect3']
        state=game.initial()
        self.assertEqual(game.legal_actions(state),(24,25,26,27))
        with self.assertRaises(ValueError): game.transition(state,0)
        for action in (24,25,16,17,8):
            state=game.transition(state,action)
        self.assertEqual(game.terminal(state),1)
        with self.assertRaises(ValueError): game.transition(state,26)

    def test_reversi_pass_and_terminal_without_two_pass_counter(self):
        game=GAMES['reversi4']
        self.assertEqual(len(game.legal_actions(game.initial())),4)
        # One empty cell: +1 must pass; -1 can bracket the +1 at index 1.
        state=State((0,1,-1,-1)+(-1,)*12,1)
        self.assertIsNone(game.terminal(state))
        self.assertEqual(game.legal_actions(state),(64,))
        next_state=game.transition(state,64)
        self.assertEqual(next_state.board,state.board)
        self.assertEqual(game.legal_actions(next_state),(0,))
        end=game.transition(next_state,0)
        self.assertEqual(game.terminal(end),-1)
        self.assertEqual(game.legal_actions(end),())
        with self.assertRaises(ValueError): game.transition(end,64)

    def test_symmetry_role_swap_and_feature_contract(self):
        rng=np.random.default_rng(71)
        for game in GAMES.values():
            for _ in range(10):
                state=game.initial()
                while game.terminal(state) is None:
                    action=int(rng.choice(game.legal_actions(state)))
                    child=game.transition(state,action)
                    swapped=State(tuple(-v for v in state.board),-state.player)
                    np.testing.assert_array_equal(game.features(state),game.features(swapped))
                    self.assertEqual(game.features(state).shape,(FEATURE_SIZE,))
                    self.assertEqual(game.canonical_key(state),game.canonical_key(swapped))
                    for mapping in game.transforms():
                        transformed,transformed_action=game.transform(state,action,mapping)
                        expected,_=game.transform(child,64,mapping)
                        self.assertEqual(game.transition(transformed,transformed_action),expected)
                        self.assertEqual(game.canonical_key(state),game.canonical_key(transformed))
                    state=child


class ProceduralDataTests(unittest.TestCase):
    def test_generation_replay_dedup_and_no_cross_split_targets(self):
        rows=generate(30,17)
        self.assertEqual(rows,generate(30,17))
        rows.append(copy.deepcopy(rows[0]))
        records,receipt=audit(rows)
        self.assertGreater(receipt['exclusion_counts']['duplicate_symmetry_trajectory'],0)
        self.assertEqual(receipt['raw_trajectories'],121)
        owners={}
        for record in records:
            game=GAMES[record['game']]
            for field in ('state','next','future2'):
                if record[field] is None:
                    continue
                data=record[field]
                key=game.canonical_key(State(tuple(data['board']),data['player']))
                self.assertIn(owners.get(key), (None,record['split']))
                owners[key]=record['split']
            if record['game']=='connect3-heldout': self.assertEqual(record['split'],'transfer')
        self.assertEqual(receipt['cross_split_overlap'],0)

    def test_invalid_outcomes_illegal_moves_and_missing_h2(self):
        rows=generate(1,17)
        for row in rows:
            replay(row)
        changed=copy.deepcopy(rows)
        changed[0]['actions'][1]=changed[0]['actions'][0]
        _,receipt=audit(changed)
        self.assertEqual(receipt['status'],'FAILED')
        self.assertEqual(receipt['exclusion_counts']['illegal_or_malformed_trajectory'],1)
        records,_=audit(rows)
        last=[r for r in records if r['future2'] is None]
        self.assertTrue(last)
        self.assertTrue(all(r['reply'] is None for r in last))

    def test_failed_support_cannot_train_and_tampered_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'data'
            manifest=write_dataset(directory,2,17)
            self.assertFalse(manifest['production_training_allowed'])
            with self.assertRaisesRegex(ValueError,'audit failed'): load_dataset(directory,'train')
            with self.assertRaisesRegex(ValueError,'excludes'): load_dataset(directory,'test')
            path=directory/'records.jsonl'
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'bytes changed'): load_dataset(directory,'train')
            with self.assertRaises(FileExistsError): write_dataset(directory,2,17)


if __name__=='__main__':
    unittest.main()
