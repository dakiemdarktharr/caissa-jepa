"""Artifact-verifier fixtures are engineering tests, not experiment results."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest.mock import patch

from two_player_v23_diagnostic import report as r


def metrics_fixture(config, scalar=.5):
    rows = []
    for game in r.GAMES:
        roots = r.ROOT_COUNTS[game]
        for i in range(roots):
            groups = {}
            for h in ('1', '2'):
                strata = {}
                for name in ('nonterminal', 'terminal'):
                    nroots, total = r.TARGET_COUNTS[game][h][name]
                    count = total//nroots+(i < total % nroots) if i < nroots else 0
                    strata[name] = {'count': count, **{k: (None if not count or
                        (config.variant == 'direct' and k != r.METRICS[0]) else scalar)
                        for k in r.METRICS}}
                count = sum(v['count'] for v in strata.values())
                strata['all'] = {'count': count, **{k: (None if config.variant == 'direct' and
                    k != r.METRICS[0] else scalar) for k in r.METRICS}}
                groups[h] = strata
            missing = int(game == r.GAMES[0] and i < 72)
            rows.append({'game': game, 'root_id': r.digest([game, i]), 'trajectory': r.digest(['trajectory', game, i]),
                         'fork_records': groups['2']['all']['count']+missing, 'missing_h2_forks': missing,
                         'horizons': groups, 'saved_planning': None})
    games, components, geometry = {}, {}, {}
    for game in r.GAMES:
        game_rows = [x for x in rows if x['game'] == game]
        horizons = {}
        components[game] = {}
        for h in ('1', '2'):
            horizons[h] = {}
            for s in ('all', 'nonterminal', 'terminal'):
                vals = [x['horizons'][h][s] for x in game_rows if x['horizons'][h][s]['count']]
                d = {k: (scalar if vals and (config.variant != 'direct' or k == r.METRICS[0]) else None) for k in r.METRICS}
                horizons[h][s] = {'root_count': len(game_rows), 'roots_with_targets': len(vals),
                                  'transition_targets': sum(x['count'] for x in vals),
                                  'equal_root': d.copy(), 'transition_weighted': d.copy()}
            v = horizons[h]['nonterminal']
            components[game][h] = {'encoded_oracle_mse': scalar, **{k: v[k] for k in ('root_count', 'roots_with_targets', 'transition_targets')}}
        games[game] = {'roots': len(game_rows), 'horizons': horizons,
                      'saved_planning_relationship': {'available': False, 'root_count': 0,
                          'pearson_h2_nonterminal_error_gap_vs_regret_gap': None}}
        n, t = (3792, 321) if game == r.GAMES[0] else (5445, 1)
        geometry[game] = {'samples': n, 'dimensions': config.latent, 'effective_rank': 4., 'mean_std': .2,
                          'median_std': .2, 'terminal_nodes': t, 'nonterminal_nodes': n-t,
                          'weighting': 'Every unique raw training node once; no canonical-orbit or fork weighting'}
    return {'fit': {'dynamics_metrics_available': config.variant != 'direct', 'games': games, 'per_root': rows},
            'geometry': geometry, 'collapse': [], 'S': scalar, 'S_components': components, 'S_component_count': 4,
            'counts': {'roots': 509, 'forks': 6750, 'unique_raw_nodes': 9237}}


def history_fixture(config):
    result = []
    for e in range(1, 161):
        counts = {'encoded_count': 25000, 'value_count': 25000, 'policy_count': 24700, 'terminal_count': 300,
                  'value_unlabelled_count': 0, 'policy_unlabelled_count': 0}
        for h, n in ((1, 8352), (2, 8296)):
            counts.update({f'h{h}_eligible_count': n, f'h{h}_missing_count': 8352-n,
                           f'h{h}_unlabelled_count': 0, f'h{h}_ema_value_count': 0,
                           f'h{h}_count': n if config.variant != 'direct' else 0,
                           f'h{h}_value_label_count': n if config.variant != 'direct' else 0,
                           f'h{h}_latent_count': n if config.variant == 'raw-jepa' else 0})
        ih = r.digest([config.seed, e, 'indices'])
        schedule = {'samples': 8352, 'unique_forks': 4500, 'index_sha256': ih,
                    'games': {g: {'unique_roots': n, 'root_draws': 261, 'repeated_root_draws': 261-n,
                                 'fork_draws': 4176} for g, n in r.ROOT_COUNTS.items()}}
        aug = {'version': 'legal-symmetries-v21', 'seed': config.seed, 'epoch': e-1, 'samples': 8352,
               'rng_namespace': 2211, 'index_sha256': ih, 'transform_sha256': r.digest([config.seed, e, 'aug']),
               'transform_counts': {g+'/0': 4176 for g in r.GAMES}}
        result.append({'epoch': e, 'step': e*66, 'steps': 66, 'seconds': .01, 'schedule': schedule,
                       'augmentation': aug, 'label_and_target_count_totals': counts,
                       'metrics_sample_weighted': {'gradient_scale': 1., 'gradient_norm': .5}})
    return result


class ReportUnits(unittest.TestCase):
    def test_reaggregate_and_reject_nonfinite_tampered_S_counts_and_collapse(self):
        c = r.Config(variant='raw-jepa')
        obj = metrics_fixture(c)
        self.assertEqual(r.validate_metrics(obj, c)[0], .5)
        for change in ('scalar', 'root_value', 'count', 'collapse', 'nonfinite', 'geometry'):
            altered = deepcopy(obj)
            if change == 'scalar': altered['S'] = .4
            if change == 'root_value': altered['fit']['per_root'][0]['horizons']['1']['nonterminal']['encoded_oracle_mse'] = .4
            if change == 'count': altered['fit']['per_root'][0]['horizons']['2']['all']['count'] += 1
            if change == 'collapse': altered['geometry'][r.GAMES[0]]['effective_rank'] = 1.
            if change == 'nonfinite': altered['geometry'][r.GAMES[0]]['mean_std'] = float('nan')
            if change == 'geometry': altered['geometry'][r.GAMES[0]]['samples'] += 1
            with self.subTest(change=change), self.assertRaises(ValueError): r.validate_metrics(altered, c)

    def test_direct_dynamics_absent_and_no_saved_planning(self):
        c = r.Config(variant='direct'); obj = metrics_fixture(c)
        r.validate_metrics(obj, c)
        obj['fit']['per_root'][0]['horizons']['1']['all']['predicted_oracle_mse'] = 0.
        with self.assertRaises(ValueError): r.validate_metrics(obj, c)
        obj = metrics_fixture(c); obj['fit']['per_root'][0]['saved_planning'] = {'regret': 0}
        with self.assertRaises(ValueError): r.validate_metrics(obj, c)

    def test_history_pairs_and_label_denominators(self):
        c = r.Config(variant='direct', seed=17); a = history_fixture(c)
        d = r.Config(variant='raw-jepa', seed=17); b = history_fixture(d)
        self.assertEqual(r.validate_history(a, c), r.validate_history(b, d))
        b[10]['label_and_target_count_totals']['h2_latent_count'] -= 1
        with self.assertRaises(ValueError): r.validate_history(b, d)
        a[0]['augmentation']['transform_counts'] = {r.GAMES[0]+'/7': 4176, r.GAMES[1]+'/0': 4176}
        with self.assertRaises(ValueError): r.validate_history(a, c)

    def test_descriptive_thresholds_seed_disagreement_and_harmed_game(self):
        rows = []
        for c in r.configurations():
            large = c.hidden == 128
            # Two good larger-model seeds, one harmed; expose a harmed game even when pooled response passes.
            s160 = (.4 if c.seed != 43 else .55) if large else .5
            components = {g: {h: s160 for h in ('1', '2')} for g in r.GAMES}
            if large and c.seed == 17: components[r.GAMES[1]]['1'] = .6
            rows.append({'config': asdict(c), 'snapshots': {'80': {'S': .51, 'components': {g: {h: .51 for h in ('1', '2')} for g in r.GAMES}},
                         '160': {'S': s160, 'components': components}}})
        result = r.decisions(rows)
        self.assertIsNone(result['candidate'])
        self.assertTrue(all(x['material_capacity_response'] for x in result['capacity']))
        self.assertEqual(result['capacity'][0]['favorable_seeds'], 2)
        self.assertLess(result['capacity'][0]['seeds'][0]['per_game_horizon'][r.GAMES[1]]['1'], 0)
        self.assertTrue(any(x['material_progress'] for x in result['progress']))


class ReportInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.base = Path(cls.tmp.name); cls.grid = cls.base/'grid'; cls.grid.mkdir()
        cls.source = {'frozen.py': 'a'*64}; cls.models = {r.run_id(c): r.Model(c) for c in r.configurations()}
        manifest = {'split': 'train', 'role': 'redacted-training', 'fraction': 1., 'label_seed': 271828,
                    'root_count': 509, 'node_count': 9237, 'fork_count': 6750, 'audit': {'status': 'PASSED', 'errors': []},
                    'selected_root_ids': {g: [r.digest([g, i]) for i in range(n)] for g, n in r.ROOT_COUNTS.items()}}
        cls.fp = r.digest(manifest); manifest['dataset_fingerprint'] = cls.fp
        refs = []
        ledger = {'version': 'v23-training-diagnostic01', 'method': r.METHOD_VERSION, 'stage': 'training-only diagnostic',
                  'source': cls.source, 'code_commit': 'b'*40, 'dataset_fingerprint': cls.fp, 'dataset_manifest': manifest,
                  'epochs': 160, 'snapshots': list(r.SNAPSHOTS), 'development_predictions': 0, 'selection_predictions': 0,
                  'final_predictions': 0, 'new_search_decisions': 0, 'status': 'complete', 'runs': [],
                  'failures': [], 'resource_limits': {'cell_seconds': 300., 'total_cell_seconds': 5400., 'artifact_bytes': 3_000_000_000},
                  'artifact_bytes_scope': 'All output files except ledger.json; cap includes ledger.json',
                  'total_cell_seconds': 180., 'preparation_seconds': .1, 'process_peak_rss_bytes': 1000000}
        for c in r.configurations():
            name = r.run_id(c); cell = cls.grid/name; cell.mkdir()
            identity = {'source': cls.source, 'data': cls.fp, 'config_sha256': r.digest(asdict(c)), 'method': r.METHOD_VERSION,
                        'objective': r.OBJECTIVE_VERSION, 'epochs': 160, 'draws': 16, 'python': 'fixture', 'numpy': 'fixture'}
            cls.write(cell/'history.json', history_fixture(c))
            cls.write(cell/'budget.json', {'status': 'complete', 'identity': identity, 'limit_seconds': 300., 'total_seconds': 10.})
            receipt = {'config': asdict(c), 'identity': identity, 'seconds': 10., 'parameters': cls.models[name].parameter_counts(),
                       'history_sha256': r.sha(cell/'history.json'), 'snapshots': []}
            for epoch in r.SNAPSHOTS:
                cp = f'checkpoint-e{epoch:03d}.npz'; mp = f'snapshot-e{epoch:03d}.json'
                (cell/cp).write_bytes(b'Engineering fixture: Model.load is mocked; not a checkpoint.')
                cls.write(cell/mp, metrics_fixture(c, .5))
                receipt['snapshots'].append({'epoch': epoch, 'step': epoch*66, 'checkpoint': cp, 'checkpoint_sha256': r.sha(cell/cp),
                    'metrics': mp, 'metrics_sha256': r.sha(cell/mp), 'S': .5, 'collapse': [],
                    'reference_match': 'verified' if c.hidden == 64 and epoch == 40 else 'not_applicable'})
            cls.write(cell/'receipt.json', receipt)
            ledger['runs'].append({'id': name, 'config': asdict(c), 'status': 'complete', 'seconds': 10., 'receipt_sha256': r.sha(cell/'receipt.json')})
            if c.hidden == 64:
                refs.append({'variant': c.variant, 'seed': c.seed, 'config': asdict(c), 'epoch': 40, 'step': 2640,
                             'array_hashes': r.tensor_hashes(cls.models[name])})
        cls.write(cls.base/'refs.json', {'dataset_fingerprint': cls.fp, 'rows': refs})
        ledger['artifact_bytes'] = sum(p.stat().st_size for p in cls.grid.rglob('*') if p.is_file())
        cls.write(cls.grid/'ledger.json', ledger)

    @staticmethod
    def write(path, obj): path.write_text(json.dumps(obj, separators=(',', ':'), allow_nan=False), encoding='utf-8')

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    @contextmanager
    def mocked(self):
        def load(path, config, identity):
            model = self.models[r.run_id(config)]
            model.epoch = int(Path(path).stem.split('-e')[1]); model.step = model.epoch*66
            return model
        with ExitStack() as stack:
            stack.enter_context(patch.object(r, 'runtime_source', return_value=self.source))
            stack.enter_context(patch.object(r, 'DATA_FINGERPRINT', self.fp))
            stack.enter_context(patch.object(r, 'ROOT', self.base))
            stack.enter_context(patch.object(r, 'REFERENCE_PATH', 'refs.json'))
            stack.enter_context(patch.object(r.Model, 'load', side_effect=load))
            yield

    def test_complete_inventory_is_diagnostic_not_promotion(self):
        with self.mocked(): report = r.summarize_grid(self.grid)
        self.assertEqual(report['verification_errors'], [])
        self.assertEqual(report['status'], 'verified_diagnostic')
        self.assertEqual(len(report['runs']), 18)
        self.assertIsNone(report['decisions']['candidate'])
        self.assertIn('No candidate promotion', r.markdown(report))

    def test_missing_cell_and_unprotected_prediction_fail_closed(self):
        path = self.grid/'ledger.json'; original = path.read_bytes()
        try:
            for change in ('missing', 'protected', 'source', 'budget'):
                ledger = json.loads(original)
                if change == 'missing': ledger['runs'].pop()
                if change == 'protected': ledger['development_predictions'] = 1
                if change == 'source': ledger['source'] = {}
                if change == 'budget': ledger['total_cell_seconds'] = 5401
                self.write(path, ledger)
                with self.mocked(): report = r.summarize_grid(self.grid)
                self.assertEqual(report['status'], 'inconclusive', change)
                self.assertIsNone(report['decisions'])
        finally: path.write_bytes(original)

    def test_active_journal_and_checkpoint_tampering_fail_closed(self):
        cell = self.grid/r.run_id(r.configurations()[0]); budget = cell/'budget.json'; original = budget.read_bytes()
        try:
            obj = json.loads(original); obj['status'] = 'active'; self.write(budget, obj)
            with self.mocked(): report = r.summarize_grid(self.grid)
            self.assertIn('budget', report['verification_errors'][0])
        finally: budget.write_bytes(original)
        path = cell/'checkpoint-e000.npz'; original = path.read_bytes()
        try:
            path.write_bytes(b'tampered')
            with self.mocked(): report = r.summarize_grid(self.grid)
            self.assertIn('checksum', report['verification_errors'][0])
        finally: path.write_bytes(original)

    def test_reference_tensors_not_just_reference_status(self):
        path = self.base/'refs.json'; original = path.read_bytes()
        try:
            obj = json.loads(original); obj['rows'][0]['array_hashes']['p_vw'] = 'f'*64; self.write(path, obj)
            with self.mocked(): report = r.summarize_grid(self.grid)
            self.assertIn('bitwise', report['verification_errors'][0])
        finally: path.write_bytes(original)


if __name__ == '__main__': unittest.main()
