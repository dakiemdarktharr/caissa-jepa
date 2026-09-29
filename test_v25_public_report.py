"""Public-summary/plot regressions on synthetic aggregates only; no rendering.

No datasets, trained checkpoints, grid directories or actual scores are read.
The small fixture uses deterministic constant outcomes and expands only its
declared cohort counts to the frozen public schema; it is not research evidence.
"""
from copy import deepcopy
import hashlib
import json
import unittest
from unittest.mock import patch

from test_v25_report import fixture, set_good
from two_player_v25 import report as original
from tools import compact_v25_report as public
from tools import plot_v25_grid as plot


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _geometry(samples=100):
    return {'samples': samples, 'dimensions': 64, 'effective_rank': 8.,
            'mean_std': .1, 'median_std': .1, 'mean_norm': 1.}


def synthetic_report():
    cells, schedule = fixture((1, 1))
    # Raw-tail's higher rate wins HYBRID but loses EXACT. The public view must
    # carry the lower rate's worse hybrid outcome, never optimize the plot.
    for cell in cells:
        if cell['config']['variant'] == 'raw-tail':
            higher = cell['config']['learning_rate'] == .001
            set_good(cell, not higher, track='exact')
            set_good(cell, higher, track='hybrid')
    with patch.object(original, 'BOOTSTRAP_REPLICATES', 1):
        report = original.summarize(cells, schedule)
    if report['verification_errors']:
        raise AssertionError(report['verification_errors'])
    # Constant within-game/seed effects give identical intervals for every
    # number of draws. No expensive bootstrap is required for these fixtures.
    comparisons = [c for track in report['tracks'].values() for c in track['comparisons'].values()]
    for comparison in comparisons+list(report['mechanism']['ablations'].values()):
        comparison['bootstrap']['replicates'] = 10000
    for row in report['configurations']:
        for track in row['tracks'].values():
            track['roots_per_game_per_seed'] = dict(public.COUNTS)
    report.update(code_commit='a'*40, ledger_sha256='b'*64, source={'synthetic_source.py': 'c'*64},
                  development_truth_sha256='d'*64, development_schedule_sha256='e'*64,
                  train_group_sha256='f'*64, development_group_sha256='1'*64,
                  replayed_epoch_plans=480,
                  resources={'total_cell_seconds': 42., 'total_wall_seconds': 43.,
                             'process_peak_rss_bytes': 100000, 'memory_scope': 'Synthetic process lifetime',
                             'artifact_bytes': 10000, 'array_bytes': 1000},
                  decision_counts={'cells': 42, 'roots_per_cell': 209, 'tracks': 2,
                                   'complete': 17556, 'censored_or_error': 0}, artifacts=[])
    for split, root_count, node_count, fork_count in (('train', 509, 9237, 6750), ('development', 209, 3756, 2735)):
        report[split+'_manifest'] = {'version': 'synthetic-data', 'method': original.METHOD_VERSION,
                                    'role': 'redacted-training' if split == 'train' else 'standalone-development',
                                    'split': split, 'fraction': 1., 'label_seed': 271828,
                                    'dataset_fingerprint': _hash(split), 'parent_dataset_fingerprint': '2'*64,
                                    'root_count': root_count, 'node_count': node_count, 'fork_count': fork_count,
                                    'selected_root_ids': ['PRIVATE_ROOT_SENTINEL']}
    report['development_truth'] = {'roots': [{'root_id': 'PRIVATE_ROOT_SENTINEL', 'oracle_values': [1, -1]}]}
    summary_keys = {'target_min_oracle_bias', 'predicted_min_oracle_bias', 'predicted_target_min_error',
                    'target_min_oracle_bias_squared', 'predicted_min_oracle_bias_squared',
                    'predicted_target_min_error_squared', 'conditional_oracle_bound'}
    summary_keys |= {h+k for h in ('h1_', 'h2_') for k in ('latent_mean', 'latent_max', 'latent_mean_max',
                      'target_value_oracle_mse', 'target_oracle_max_absolute', 'predicted_value_oracle_mse')}
    for row in report['runs']:
        config = row['config']; variant = config['variant']
        cp_sha = _hash(config)
        row.update(seconds=1., checkpoint_sha256=cp_sha,
                   parameters={'allocated': 1, 'active': 1, 'ema': 1, 'transition': 1},
                   scores=[{'root_id': 'PRIVATE_ROOT_SENTINEL', 'action_estimates': [1, -1]}])
        for game in public.GAMES:
            for metric in row['metrics'][game].values():
                metric.update(scheduled=public.COUNTS[game], complete=public.COUNTS[game])
        row['representation'] = {game: {'forks': 3, 'samples': 9, 'missing_states': 0,
                                      'policy_samples': 9, 'terminal_samples': 0,
                                      'value_mse': .1, 'policy_nll': .5, 'policy_mrr': .5, 'policy_top1_optimal': .5,
                                      'unprojected': _geometry(9), 'projected': None,
                                      'horizons': {} if variant == 'direct' else
                                          {h: {'samples': 3, 'online_latent_mse': .1} for h in ('1', '2')}}
                                 for game in public.GAMES}
        row['diagnostics'] = {'stage': 'development', 'weighting': 'Synthetic complete groups', 'head_norm': 1.,
                              'collapse': False, 'games': {game: {
                                  'unique_node_geometry': _geometry(), 'collapse': False, 'group_count': 1,
                                  'false_pessimistic_count': None if variant == 'direct' else 0,
                                  'groups': [{'root_id': 'PRIVATE_ROOT_SENTINEL', 'oracle_values': [1, -1]}],
                                  'summary': {key: {'count': 0, 'mean': None, 'max': None,
                                                    'quantiles_0_25_50_75_100': None} for key in summary_keys}}
                              for game in public.GAMES}}
        rid = f"{variant}-lr{config['learning_rate']:g}-s{config['seed']}"
        report['artifacts'].append({'id': rid, 'checkpoint_sha256': cp_sha,
                                    **{k: _hash([rid, k]) for k in ('receipt_sha256', 'history_sha256', 'budget_sha256',
                                                                    'tensor_sha256', 'training_plan_sha256')}})
    report['baselines'] = {name: {g: {'exact': deepcopy(report['runs'][0]['metrics'][g]['exact'])} for g in public.GAMES}
                           for name in ('zero', 'untrained-17', 'untrained-29', 'untrained-43')}
    return report


class PublicReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = synthetic_report()

    def test_compact_preserves_42_cells_and_all_rates_without_mutation(self):
        source = deepcopy(self.original); before = deepcopy(source)
        result = public.compact(source, '3'*64)
        self.assertEqual(source, before)
        self.assertEqual(len(result['runs']), 42)
        self.assertEqual(len(result['configurations']), 14)
        self.assertEqual(len(result['artifacts']), 42)
        self.assertEqual(result['source_report_sha256'], '3'*64)
        self.assertEqual(result['status'], source['status'])
        self.assertEqual({(r['config']['variant'], r['config']['learning_rate'], r['config']['seed']) for r in result['runs']},
                         {(v, lr, seed) for v in public.FAMILIES for lr in public.RATES for seed in public.SEEDS})

    def test_raw_roots_groups_and_labels_are_absent_from_public_tree(self):
        result = public.compact(deepcopy(self.original), '3'*64)
        text = json.dumps(result)
        self.assertNotIn('PRIVATE_ROOT_SENTINEL', text)
        forbidden = {'root_id', 'trajectory', 'node_ids', 'roots', 'groups', 'scores', 'selected_root_ids',
                     'oracle_values', 'action_estimates', 'board', 'state', 'development_truth', 'train_manifest', 'development_manifest'}
        def walk(item):
            if isinstance(item, dict):
                self.assertFalse(set(item) & forbidden)
                for child in item.values(): walk(child)
            elif isinstance(item, list):
                for child in item: walk(child)
        walk(result)
        self.assertIn('development_truth_sha256', result)
        self.assertEqual(set(result['data_provenance']), {'train', 'development'})

    def test_unknown_nested_payloads_rejected_before_export(self):
        def bad_config(x): x['runs'][0]['config']['secret_array'] = [[1, 2]]
        def bad_parameter(x): x['runs'][0]['parameters']['weights'] = [1., 2.]
        def bad_selected(x): x['selected']['raw-tail']['tracks']['hybrid']['raw_values'] = [0., 1.]
        def bad_bootstrap(x): x['tracks']['exact']['comparisons']['direct']['bootstrap']['resampled_arrays'] = [[0.]]
        def bad_resource(x): x['resources']['raw_memory_samples'] = [10, 20]
        def bad_artifact(x): x['artifacts'][0]['checkpoint_arrays'] = [[0.]]
        def bad_geometry(x): x['runs'][0]['representation'][public.GAMES[0]]['unprojected']['latent_array'] = [[0.]]
        def bad_summary(x): x['runs'][0]['diagnostics']['games'][public.GAMES[0]]['summary']['extra_group_errors'] = [1., 2.]
        for edit in (bad_config, bad_parameter, bad_selected, bad_bootstrap, bad_resource, bad_artifact, bad_geometry, bad_summary):
            source = deepcopy(self.original); edit(source)
            with self.subTest(edit=edit.__name__), self.assertRaises(ValueError): public.compact(source, '3'*64)

    def test_arrays_in_scalar_fields_and_nonfinite_values_rejected(self):
        for key, value in (('head_norm', [1., 2.]), ('head_norm', float('nan'))):
            source = deepcopy(self.original); source['runs'][0]['diagnostics'][key] = value
            with self.subTest(value=value), self.assertRaises(ValueError): public.compact(source, '3'*64)
        source = deepcopy(self.original)
        source['tracks']['exact']['comparisons']['direct']['bootstrap']['aggregate_ci95'] = [[0.], [1.]]
        with self.assertRaises(ValueError): public.compact(source, '3'*64)

    def test_artifact_hash_bound_to_its_exact_run_identity(self):
        source = deepcopy(self.original)
        source['artifacts'][0]['checkpoint_sha256'], source['artifacts'][1]['checkpoint_sha256'] = (
            source['artifacts'][1]['checkpoint_sha256'], source['artifacts'][0]['checkpoint_sha256'])
        with self.assertRaisesRegex(ValueError, 'hashes disagree'): public.compact(source, '3'*64)

    def test_exact_600_second_boundary_rejected_below_boundary_accepted(self):
        source = deepcopy(self.original); source['runs'][0]['seconds'] = 600.
        with self.assertRaisesRegex(ValueError, 'time cap'): public.compact(source, '3'*64)
        source['runs'][0]['seconds'] = 599.999
        source['resources']['total_cell_seconds'] = 640.999
        source['resources']['total_wall_seconds'] = 642.
        self.assertEqual(public.compact(source, '3'*64)['runs'][0]['seconds'], 599.999)

    def test_exact_selected_rate_remains_for_hybrid_despite_better_other_rate(self):
        result = public.compact(deepcopy(self.original), '3'*64)
        chosen = result['selected']['raw-tail']
        self.assertEqual(chosen['learning_rate'], .0003)
        self.assertEqual(chosen['tracks']['exact']['mean_regret'], 0.)
        self.assertEqual(chosen['tracks']['hybrid']['mean_regret'], 2.)
        alternative = next(c for c in result['configurations'] if c['variant'] == 'raw-tail' and c['learning_rate'] == .001)
        self.assertEqual(alternative['tracks']['hybrid']['mean_regret'], 0.)
        tampered = deepcopy(self.original); tampered['selected']['raw-tail'] = deepcopy(alternative)
        with self.assertRaisesRegex(ValueError, 'EXACT-only'): public.compact(tampered, '3'*64)

    def test_missing_duplicate_failed_and_collapsed_cells_fail_closed(self):
        for issue in ('missing', 'duplicate', 'failed', 'collapse'):
            source = deepcopy(self.original)
            if issue == 'missing': source['runs'].pop()
            if issue == 'duplicate': source['runs'][-1] = deepcopy(source['runs'][0])
            if issue == 'failed': source['runs'][0]['status'] = 'failed'
            if issue == 'collapse': source['runs'][0]['collapse'] = [{'game': public.GAMES[0]}]
            with self.subTest(issue=issue), self.assertRaises(ValueError): public.compact(source, '3'*64)

    def test_plot_extract_uses_saved_values_and_intervals_only(self):
        source = public.compact(deepcopy(self.original), '3'*64); before = deepcopy(source)
        # Any accidental path/model/render access makes this pure extraction fail.
        with patch.object(plot, 'read', side_effect=AssertionError('No files')), \
             patch.object(plot, 'render', side_effect=AssertionError('No rendering')):
            result = plot.extract(source)
        self.assertEqual(source, before)
        self.assertEqual(result['selected']['raw-tail'], .0003)
        for track in public.TRACKS:
            chosen = next(x for x in result['tracks'][track]['families'] if x['family'] == 'raw-tail')
            self.assertEqual(chosen['rate'], .0003)
            self.assertEqual(chosen['mean'], source['selected']['raw-tail']['tracks'][track]['mean_regret'])
            self.assertEqual(len(result['full'][track]), 14)
            self.assertTrue(all(len(row) == 9 for row in result['full'][track]))
            for extracted in result['tracks'][track]['comparisons']:
                saved = source['tracks'][track]['comparisons'][extracted['control']]
                self.assertEqual(extracted['intervals'], [saved['bootstrap']['aggregate_ci95']]+
                                 [saved['bootstrap']['per_game_ci95'][g] for g in public.GAMES])
            for i, (variant, rate) in enumerate((v, lr) for v in public.FAMILIES for lr in public.RATES):
                for j, seed in enumerate(public.SEEDS):
                    row = next(x for x in source['runs'] if (x['config']['variant'], x['config']['learning_rate'], x['config']['seed']) == (variant, rate, seed))
                    per_game = [row['metrics'][g][track]['mean_regret'] for g in public.GAMES]
                    self.assertEqual(result['full'][track][i][j], sum(per_game)/2)
                    self.assertEqual(result['full'][track][i][j+3], per_game[0])
                    self.assertEqual(result['full'][track][i][j+6], per_game[1])


if __name__ == '__main__':
    unittest.main()
