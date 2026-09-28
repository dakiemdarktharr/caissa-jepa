"""Independent small-fixture checks; never score selection or final data."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.reference_rules import ReferenceGame, ReferenceSolver
from two_player.games import BoardGame, State
from two_player_v2 import data


class ForkDataTests(unittest.TestCase):
    def setUp(self):
        self.game = BoardGame('fixture', 3, 3, 3)
        self.state = State((1, 1, 0, -1, -1, 0, 0, 0, 0), 1)

    def fixture(self):
        with patch.dict(data.GAMES_V2, {'fixture': self.game}, clear=True):
            states, branches, keys = data.closure('fixture', self.state)
            ref = ReferenceGame(3, 3, 3)
            solver = ReferenceSolver(ref)
            nodes = {nid: data.label_node('fixture', state, ref, solver)
                     for nid, state in states.items()}
        forks = [{'root_id': 'fixture-root', 'game': 'fixture', 'split': 'train',
                  'node_ids': ids, 'actions': actions} for ids, actions in branches]
        return {'roots': [], 'nodes': nodes, 'forks': forks}, states, keys

    def test_complete_forks_terminal_masks_and_perspective(self):
        dataset, states, keys = self.fixture()
        expected = []
        for action in self.game.legal_actions(self.state):
            child = self.game.transition(self.state, action)
            replies = self.game.legal_actions(child)
            expected.extend((action, reply) for reply in replies)
            if not replies:
                expected.append((action, None))
        self.assertEqual([tuple(f['actions']) for f in dataset['forks']], expected)
        self.assertEqual(keys, {self.game.canonical_key(s) for s in states.values()})
        with patch.dict(data.GAMES_V2, {'fixture': self.game}, clear=True):
            batch = data.batch_arrays(dataset, range(len(expected)))
        for index, fork in enumerate(dataset['forks']):
            a, b = fork['actions']
            self.assertTrue(batch['valid'][index, :2].all())
            self.assertEqual(batch['actions'][index, 0, a], 1)
            child = dataset['nodes'][fork['node_ids'][1]]
            if a == 2:  # +1 completes the top row, then the mover becomes -1.
                self.assertTrue(child['terminal'])
                self.assertEqual(child['value'], -1)
                self.assertEqual(b, None)
                self.assertFalse(batch['valid'][index, 2])
                self.assertFalse(batch['x'][index, 2].any())
                self.assertFalse(batch['actions'][index, 1].any())
            for h, nid in enumerate(fork['node_ids']):
                if nid is None:
                    continue
                node = dataset['nodes'][nid]
                self.assertEqual(batch['value'][index, h, 0], node['value'])
                self.assertEqual(batch['policy'][index, h].sum(), 0 if node['terminal'] else 1)
                self.assertFalse(batch['policy'][index, h, ~batch['legal'][index, h]].any())

    def test_exact_labels_against_independent_plain_recursion(self):
        dataset, _, _ = self.fixture()

        def solve(state):
            outcome = self.game.terminal(state)
            if outcome is not None:
                return state.player * outcome
            return max(-solve(self.game.transition(state, a)) for a in self.game.legal_actions(state))

        for node in dataset['nodes'].values():
            state = data.state_from(node['state'])
            self.assertEqual(node['value'], solve(state))
            if not node['terminal']:
                values = [-solve(self.game.transition(state, a)) for a in node['legal']]
                self.assertEqual(node['action_values'], values)
                self.assertEqual(node['optimal'], [a for a, v in zip(node['legal'], values) if v == max(values)])

    def test_split_quarantine_uses_entire_fork_closure(self):
        game = data.GAMES_V2['connect4-4x5']
        ancestor = game.initial()
        for action in (24, 25, 16, 17):
            ancestor = game.transition(ancestor, action)
        descendant = game.transition(game.transition(ancestor, 26), 27)

        def root(state, bucket):
            return {'game': game.name, 'state': {'board': list(state.board), 'player': state.player},
                    'canonical_key': game.canonical_key(state), 'actions': list(game.legal_actions(state)),
                    'trajectory': f'{bucket:016x}' + '1' * 48}

        roots = [root(ancestor, 0), root(descendant, 95)]
        kept, audit = data.assign_roots(roots, set())
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0][0]['split'], 'final')
        self.assertEqual(audit['excluded_roots'][0]['reason'], 'cross_split_fork_closure_overlap')
        self.assertEqual(audit['status'], 'FAILED')  # Tiny fixtures never pass support gates.
        kept, audit = data.assign_roots([roots[1]], {game.canonical_key(descendant)})
        self.assertEqual(kept, [])
        self.assertEqual(audit['excluded_roots'][0]['reason'], 'old_v1_training_overlap')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            data.assign_roots([roots[0], copy.deepcopy(roots[0])], set())

    def test_artifact_manifest_and_source_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            raw = b'{"roots":[],"forks":[],"nodes":{}}'
            manifest = {'version': data.DATA_VERSION, 'source_identity': data.source_identity(),
                        'audit': {'status': 'PASSED'},
                        'artifacts': {'forks.json': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}}}
            manifest['dataset_fingerprint'] = data.digest(manifest)
            path = directory / 'manifest.json'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            (directory / 'forks.json').write_bytes(raw)
            self.assertEqual(data.verify_bytes(directory)[1], raw)
            for split in ('selection', 'final'):
                with self.assertRaisesRegex(ValueError, 'separate frozen protocol'):
                    data.load_dataset(directory, split)
            (directory / 'forks.json').write_bytes(raw + b' ')
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                data.verify_bytes(directory)
            (directory / 'forks.json').write_bytes(raw)
            manifest['audit']['extra'] = 'mutated'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
                data.verify_bytes(directory)
            manifest['source_identity'] = {}
            path.write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'source/audit mismatch'):
                data.verify_bytes(directory)


if __name__ == '__main__':
    unittest.main()
