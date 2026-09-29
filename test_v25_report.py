"""Synthetic report arithmetic and fail-closed checks; no research predictions."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from two_player_v25 import report as r
from two_player_v25.model import Config


def fixture(counts=(3, 5)):
    roots = [{'game': game, 'root_id': game+str(i), 'trajectory': game+'t'+str(i),
              'actions': [0, 1], 'oracle_values': [1, -1], 'beyond_depth': bool(i % 2)}
             for game, n in zip(r.GAMES, counts) for i in range(n)]
    schedule = {'roots': roots, 'unique_node_counts': {g: 100 for g in r.GAMES},
                'development_fingerprint': r.DEVELOPMENT_FINGERPRINT}
    cells = []
    for variant in r.VARIANTS:
        for rate in r.RATES:
            for seed in r.SEEDS:
                rows = []
                for root in roots:
                    for track in r.TRACKS:
                        good = variant == 'raw-tail'
                        recurrent = variant != 'direct' and track == 'hybrid'
                        rows.append({'game': root['game'], 'root_id': root['root_id'], 'trajectory': root['trajectory'],
                                     'split': 'development', 'track': track, 'beyond_depth': root['beyond_depth'],
                                     'status': 'complete', 'reason': None, 'seconds': .01,
                                     'action': 0 if good else 1, 'regret': 0 if good else 2, 'optimal': good,
                                     'action_estimates': [1., -1.] if good else [-1., 1.], 'oracle_gap': 2.,
                                     'nodes': 4, 'transitions': 4, 'leafcount': 2, 'neural_leaves': 2, 'neural_leaf_candidates': 2,
                                     'neuralcounts': {'encoder_calls': 1, 'encoder_states': 1 if recurrent else 2,
                                                      'rollout_calls': int(recurrent), 'predictor_steps': 4 if recurrent else 0,
                                                      'value_calls': 1, 'value_states': 2}})
                cells.append({'config': asdict(Config(variant=variant, learning_rate=rate, seed=seed)), 'status': 'complete',
                              'scores': rows, 'representation': {g: {'samples': 200} for g in r.GAMES},
                              'diagnostics': {'stage': 'development', 'collapse': False,
                                              'games': {g: {'unique_node_geometry': {'samples': 100, 'dimensions': 64,
                                                                                    'effective_rank': 8., 'median_std': .1},
                                                            'collapse': False} for g in r.GAMES}}})
    return cells, schedule


def set_good(cell, good, track=None, game=None, index=None, estimates=None):
    for i, row in enumerate(cell['scores']):
        if track is not None and row['track'] != track: continue
        if game is not None and row['game'] != game: continue
        if index is not None and i != index: continue
        values = estimates if estimates is not None else ([1., -1.] if good else [-1., 1.])
        choice = int(np.argmax(values))
        row.update(action=choice, action_estimates=values, regret=2*choice, optimal=choice == 0)


class V25ReportTests(unittest.TestCase):
    def report(self, cells, schedule):
        with patch.object(r, 'BOOTSTRAP_REPLICATES', 64):
            return r.summarize(cells, schedule)

    def test_all_cells_and_rates_preserved_and_only_candidate_promoted(self):
        cells, schedule = fixture()
        before = deepcopy((cells, schedule))
        result = self.report(cells, schedule)
        self.assertEqual(result['verification_errors'], [])
        self.assertEqual(result['status'], 'development_screen_passed')
        self.assertEqual(len(result['runs']), 42)
        self.assertEqual(len(result['configurations']), 14)
        self.assertEqual(result['candidate'], 'raw-tail')
        self.assertTrue(all(row['learning_rate'] == .0003 for row in result['selected'].values()))
        self.assertEqual((cells, schedule), before)

    def test_exact_global_rate_carries_to_hybrid(self):
        cells, schedule = fixture()
        for cell in cells:
            if cell['config']['variant'] == 'raw-tail':
                high_rate = cell['config']['learning_rate'] == .001
                set_good(cell, not high_rate, track='exact')
                set_good(cell, high_rate, track='hybrid')
        result = self.report(cells, schedule)
        self.assertEqual(result['selected']['raw-tail']['learning_rate'], .0003)
        self.assertEqual(result['selected']['raw-tail']['tracks']['hybrid']['mean_regret'], 2)
        self.assertEqual(result['status'], 'not_promoted')
        self.assertTrue(result['tracks']['exact']['passed'])

    def test_hybrid_only_is_narrow_result(self):
        cells, schedule = fixture()
        for cell in cells:
            if cell['config']['variant'] == 'raw-tail': set_good(cell, False, track='exact')
        result = self.report(cells, schedule)
        self.assertEqual(result['status'], 'exploratory_hybrid_only')
        self.assertFalse(result['tracks']['exact']['passed'])
        self.assertTrue(result['mechanism']['passed'])

    def test_better_ablation_never_replaces_candidate(self):
        cells, schedule = fixture()
        for cell in cells:
            if cell['config']['variant'] == 'raw-tail': set_good(cell, False)
            if cell['config']['variant'] == 'raw-mean': set_good(cell, True)
        result = self.report(cells, schedule)
        self.assertEqual(result['candidate'], 'raw-tail')
        self.assertEqual(result['status'], 'not_promoted')

    def test_ablation_or_scalar_mse_can_veto_primary_gains(self):
        for reason in ('ablation', 'mse'):
            with self.subTest(reason=reason):
                cells, schedule = fixture()
                for cell in cells:
                    if reason == 'ablation' and cell['config']['variant'] == 'raw-scaled': set_good(cell, True)
                    if reason == 'mse':
                        if cell['config']['variant'] == 'raw-tail': set_good(cell, True, estimates=[.01, 0.])
                        if cell['config']['variant'] == 'scalar-tail': set_good(cell, False, estimates=[0., .01])
                if reason == 'mse':
                    # Correct decisions may still have greater action-value MSE.
                    for cell in cells:
                        if cell['config']['variant'] == 'raw-tail': set_good(cell, True, estimates=[1., .99])
                result = self.report(cells, schedule)
                self.assertEqual(result['verification_errors'], [])
                self.assertTrue(result['tracks']['hybrid']['passed'])
                self.assertFalse(result['mechanism']['passed'])
                self.assertEqual(result['status'], 'not_promoted')

    def test_equal_game_weighting_not_pooled_root_weighting(self):
        cells, schedule = fixture((1, 9))
        for cell in cells:
            if cell['config']['variant'] == 'direct': set_good(cell, True, game=r.GAMES[1])
        result = self.report(cells, schedule)
        self.assertEqual(result['selected']['direct']['tracks']['exact']['mean_regret'], 1.)
        self.assertEqual(result['selected']['direct']['tracks']['hybrid']['action_oracle_mse'], 2.)
        self.assertFalse(result['tracks']['hybrid']['passed'])  # one game ties

    def test_two_paired_seeds_required_even_with_positive_mean(self):
        cells, schedule = fixture()
        for cell in cells:
            if cell['config']['variant'] == 'raw-tail' and cell['config']['seed'] != 17: set_good(cell, False)
        result = self.report(cells, schedule)
        comparison = result['tracks']['exact']['comparisons']['direct']
        self.assertGreater(comparison['aggregate_improvement'], .05)
        self.assertEqual(comparison['favorable_seeds'], 1)
        self.assertFalse(result['tracks']['exact']['passed'])

    def test_any_unselected_collapse_is_inconclusive(self):
        cells, schedule = fixture()
        c = cells[0]  # high rate that loses the exact tie
        d = c['diagnostics']; d['collapse'] = True
        d['games'][r.GAMES[0]]['collapse'] = True
        d['games'][r.GAMES[0]]['unique_node_geometry']['effective_rank'] = 1.
        result = self.report(cells, schedule)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertIn('Collapsed', result['verification_errors'][0])
        self.assertEqual(len(result['runs']), 42)

    def test_failed_missing_duplicate_and_nonfrozen_cells(self):
        for issue in ('failed', 'missing', 'duplicate', 'config'):
            cells, schedule = fixture()
            if issue == 'failed': cells[20]['status'] = 'failed'
            if issue == 'missing': cells.pop()
            if issue == 'duplicate': cells[-1] = deepcopy(cells[0])
            if issue == 'config': cells[0]['config']['latent'] = 32
            with self.subTest(issue=issue):
                result = self.report(cells, schedule)
                self.assertEqual(result['status'], 'inconclusive')
                self.assertTrue(result['verification_errors'])
                self.assertEqual(len(result['runs']), len(cells))

    def test_saved_decision_tampering_censor_and_resources_fail_closed(self):
        edits = ({'action': 0}, {'regret': 0., 'optimal': True}, {'seconds': 1.}, {'status': 'censored'},
                 {'transitions': 7}, {'nodes': 4097, 'transitions': 4097}, {'action_estimates': [float('nan'), 0.]},
                 {'action_estimates': [0., 0.]}, {'beyond_depth': True}, {'split': 'final'})
        for edit in edits:
            cells, schedule = fixture(); cells[0]['scores'][0].update(edit)
            with self.subTest(edit=edit):
                result = self.report(cells, schedule)
                self.assertEqual(result['status'], 'inconclusive')
                self.assertTrue(result['verification_errors'])

    def test_schedule_pairing_and_unique_geometry_counts(self):
        for issue in ('order', 'duplicate_trajectory', 'geometry', 'neural'):
            cells, schedule = fixture()
            if issue == 'order': cells[0]['scores'].reverse()
            if issue == 'duplicate_trajectory': schedule['roots'][1]['trajectory'] = schedule['roots'][0]['trajectory']
            if issue == 'geometry': cells[0]['diagnostics']['games'][r.GAMES[0]]['unique_node_geometry']['samples'] = 200
            if issue == 'neural': cells[0]['scores'][0]['neuralcounts']['predictor_steps'] = 4
            result = self.report(cells, schedule)
            self.assertEqual(result['status'], 'inconclusive', issue)
            self.assertTrue(result['verification_errors'], issue)

    def test_bootstrap_fixed_seeds_and_shared_root_not_pseudoreplication(self):
        a = {g: np.zeros((3, 2)) for g in r.GAMES}
        b = {g: np.array([[0., 2.], [2., 0.], [1., 1.]]) for g in r.GAMES}
        plans = r._plans({g: 2 for g in r.GAMES}, 0, 100)
        result = r._comparison(a, b, plans, 0)
        # Across the fixed seed cohort every root has difference exactly one;
        # independent resampling of seed/root occurrences would create variance.
        self.assertEqual(result['bootstrap']['aggregate_ci95'], [1., 1.])
        self.assertEqual(result['bootstrap']['seed_sequence'], [2505, 0])
        self.assertTrue(any(not np.array_equal(plans[g], r._plans({x: 2 for x in r.GAMES}, 1, 100)[g]) for g in r.GAMES))
        reverse = r._comparison(b, a, plans, 0)
        self.assertEqual(reverse['bootstrap']['aggregate_ci95'], [-1., -1.])

    def test_history_counts_mask_and_variant_semantics(self):
        p = {'fork_rows': 10, 'group_draws': 4, 'h1_terminal_groups': 1,
             'h2_terminal_rows': 2, 'h2_nonterminal_rows': 7, 'h2_valid_rows': 9, 'h2_eligible_groups': 2}
        direct, recurrent, raw = (r._count_totals(p, v) for v in ('direct', 'recurrent-pv', 'raw-tail'))
        self.assertEqual(raw['encoded_count'], 29)
        self.assertEqual(raw['policy_count'], 26)
        self.assertEqual(raw['terminal_count'], 3)
        self.assertEqual(raw['h1_aux_row_count'], 3)  # unique H1 per drawn group
        self.assertEqual(raw['h2_aux_row_count'], 7)
        self.assertEqual(recurrent['h2_count'], 9)
        self.assertEqual(recurrent['h2_aux_group_count'], 0)
        self.assertEqual(direct['h2_value_label_count'], 0)
        self.assertEqual(direct['encoded_count'], raw['encoded_count'])

    def test_history_requires_160_exact_replayed_plans_and_all_counts(self):
        config = Config()
        grouping = {'groups': [{'h1_terminal': True, 'row_count': 1, 'h2_nonterminal_rows': 0},
                               {'h1_terminal': False, 'row_count': 3, 'h2_nonterminal_rows': 2}]}
        indices = [0, 0]+[1]*2086
        def plan(_group, seed, epoch):
            return indices, None, {'seed': seed, 'epoch': epoch, 'fork_rows': 5000, 'group_draws': 2088,
                                'h1_terminal_groups': 2, 'h2_terminal_rows': 20, 'h2_nonterminal_rows': 4978,
                                'h2_valid_rows': 4998, 'h2_eligible_groups': 2080}
        history = []
        for epoch in range(160):
            p = plan(None, 17, epoch)[2]
            history.append({'epoch': epoch+1, 'step': 66*(epoch+1), 'steps': 66, 'schedule': p,
                            'fork_rows': 5000, 'group_draws': 2088, 'seconds': .01,
                            'count_totals': r._count_totals(p, 'raw-tail'), 'metrics_group_weighted_batch_mean': {'loss': 1.}})
            history[-1]['count_totals'].update(h2_max_tie_group_count=0, h2_max_tie_member_count=0,
                                             h2_scaled_factor_count=0, h2_scaled_factor_nonzero_count=0,
                                             h2_scaled_factor_clip_count=0)
            history[-1].update(sum_totals={**r._weight_sums(grouping, indices), 'h2_scaled_factor_sum': 0.},
                               scaled_factors={'count': 0, 'min': None, 'max': None, 'mean': None})
        with patch('two_player_v25.data.epoch_plan', side_effect=plan):
            cache = {}; r._history(history, config, grouping, cache)
            self.assertEqual(len(cache), 160)
            for issue in ('step', 'count', 'plan', 'short', 'ties', 'clipped', 'inactive_factor', 'weight'):
                bad = deepcopy(history)
                if issue == 'step': bad[-1]['step'] -= 1
                if issue == 'count': bad[0]['count_totals']['h2_aux_row_count'] -= 1
                if issue == 'plan': bad[2]['schedule']['epoch'] = 7
                if issue == 'short': bad.pop()
                if issue == 'ties': bad[0]['count_totals']['h2_max_tie_member_count'] = 1
                if issue == 'clipped': bad[0]['count_totals']['h2_scaled_factor_clip_count'] = 1
                if issue == 'inactive_factor': bad[0]['sum_totals']['h2_scaled_factor_sum'] = 1.
                if issue == 'weight': bad[0]['sum_totals']['h2_policy_weight_sum'] += 1.
                with self.subTest(issue=issue), self.assertRaises(ValueError): r._history(bad, config, grouping, cache)

    def test_actual_synthetic_model_metrics_match_report_structural_denominators(self):
        from test_v25_data import fixture as legal_fixture
        from two_player_v25.data import build_groups, epoch_plan, make_batch
        from two_player_v22.data import batch_arrays
        from two_player_v25.model import Model
        data = legal_fixture('train'); grouping = build_groups(data)
        indices, transforms, plan = epoch_plan(grouping, 17, 0)
        batch = make_batch(batch_arrays(data, range(len(data['forks']))), grouping, indices, transforms)
        for variant in r.VARIANTS:
            metrics, _ = Model(Config(variant=variant)).loss_grad(batch)
            for key, value in r._count_totals(plan, variant).items():
                self.assertEqual(metrics[key], value, (variant, key))
            for key, value in r._weight_sums(grouping, indices).items():
                if variant == 'direct' and key.startswith(('h1_', 'h2_')): value = 0.
                self.assertAlmostEqual(metrics[key], value, places=10, msg=(variant, key))

    def test_strict_missing_failure_source_and_no_prediction_access(self):
        from two_player_v25 import runtime
        with tempfile.TemporaryDirectory() as directory, patch('two_player_v25.model.Model.encode', side_effect=AssertionError('no predictions')):
            result = r.summarize_grid(directory)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertTrue(result['verification_errors'])
            ledger = {'version': 'v25-grid04', 'method': r.METHOD_VERSION, 'stage': 'development',
                      'epochs': 160, 'status': 'inconclusive', 'failures': ['retained'], 'runs': []}
            path = Path(directory)/'ledger.json'; path.write_text(json.dumps(ledger), encoding='utf-8')
            result = r.summarize_grid(directory)
            self.assertIn('failed or incomplete', result['verification_errors'][0])
            ledger.update(status='complete', failures=[], selection_predictions=0, final_predictions=0,
                          limits={'cell_seconds': 600., 'total_cell_seconds': 25200., 'bytes': 3000000000, 'rss': 1000000000},
                          source={'fabricated': '0'*64})
            path.write_text(json.dumps(ledger), encoding='utf-8')
            result = r.summarize_grid(directory)
            self.assertIn('source/inventory', result['verification_errors'][0])


if __name__ == '__main__':
    unittest.main()
