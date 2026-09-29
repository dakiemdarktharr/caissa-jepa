"""Synthetic arithmetic/inventory checks; no datasets, models or fits."""
from copy import deepcopy
from dataclasses import asdict
import unittest

from two_player_v24_probe import report as r


def schedule_fixture():
    schedule = {'version': 'v24-order-schedule01', 'edge_order': ['s1a', 's2a', 's1b', 's2b'], 'games': {}}
    for game in r.GAMES:
        edges = [{'root_id': f'r{root}', 'player': 1, 'action': action, 'source_id': f's{root}',
                  'target_id': f't{root}-{action}', 'target_player': -1, 'target_value': 0,
                  'target_terminal': root == 3 and action == 1}
                 for root in range(8) for action in range(2)]
        blocks = []
        for root in (0, 2):
            identity = [2401, game, f'r{root}', f'r{root+1}', 0, 1]
            ids = [2*root, 2*(root+1), 2*root+1, 2*(root+1)+1]
            blocks.append({'identity': identity, 'sha256': r.digest(identity), 'edges': ids,
                           'terminal_count': sum(edges[i]['target_terminal'] for i in ids)})
        counts = {'roots': 8, 'eligible_root_pairs': 28, 'candidate_blocks': 28,
                  'selected_blocks': 2, 'total_h1_edges': 16, 'used_edges': 8, 'used_fraction': .5,
                  'terminal_block_counts': {'0': 1, '1': 1, '2': 0, '3': 0, '4': 0},
                  'nonterminal_blocks': 1, 'all_nonterminal_edges': 15, 'used_nonterminal_edges': 4,
                  'nonterminal_used_fraction': 4/15}
        schedule['games'][game] = {'edges': edges, 'blocks': blocks, 'counts': counts,
                                  'edge_sha256': r.digest(edges), 'block_sha256': r.digest(blocks)}
    schedule['schedule_sha256'] = r.digest(schedule)
    return schedule


def rows_fixture():
    rows = []
    for family in r.FAMILIES:
        for hidden, dim in r.CAPACITIES:
            for seed in r.SEEDS:
                config = asdict(r.Config(variant=family, hidden=hidden, latent=dim, seed=seed,
                                         jepa_weight=.1 if family == 'raw-jepa' else 1.))
                direct = family == 'direct'
                def summary(n, sse):
                    return {'edge_count': n, 'latent_sse': None if direct else sse,
                            'latent_mse': None if direct or not n else sse/(n*dim),
                            'target_value_oracle_mse': .2 if n else None,
                            'predicted_value_oracle_mse': None if direct or not n else .3,
                            'predicted_target_value_mse': None if direct or not n else .1,
                            'target_geometry': {'samples': n, 'dimensions': dim, 'effective_rank': 3.,
                                'mean_std': .2, 'median_std': .2,
                                'weighting': 'Uniform H1 edge targets; repeated successor states retain edge multiplicity'} if n else None}
                for game in r.GAMES:
                    for space in r.SPACES:
                        full, nt = summary(16, 10.), summary(15, 8.)
                        def packed(blocks, sse, bound, all_summary):
                            p = summary(4*blocks, sse)
                            p.update(block_count=blocks, bound_sse=bound,
                                bound_mse=bound/(4*blocks*dim),
                                full_bound_mse=bound/(all_summary['edge_count']*dim),
                                bound_packed_sse_ratio=None if direct else bound/sse,
                                bound_full_sse_ratio=None if direct else bound/all_summary['latent_sse'],
                                reversals_strict=2, reversals_1e6=1, near_ties_1e6=1,
                                coordinate_comparisons=blocks*dim,
                                absolute_gap_quantiles=[0., .1, .2, .3, .4],
                                min_absolute_gap_quantiles=[0., .05, .1, .2, .3],
                                target_value_gap_quantiles=[0., .1, .2, .3, .4], head_norm=1.)
                            return p
                        rows.append({'config': config, 'game': game, 'target_space': space, 'latent_dim': dim,
                                     'direct': direct, 'all_h1': full, 'all_nonterminal': nt,
                                     'packed': packed(2, 8., 2., full), 'packed_nonterminal': packed(1, 4., .4, nt),
                                     'predicted_order_violations': None if direct else 0})
    return rows


def change_bound(row, group, bound, full):
    p, f, dim = row[group], row[full], row['latent_dim']
    p['bound_sse'] = bound
    p['bound_mse'] = bound/(p['edge_count']*dim)
    p['full_bound_mse'] = bound/(f['edge_count']*dim)
    p['bound_packed_sse_ratio'] = bound/p['latent_sse']
    p['bound_full_sse_ratio'] = bound/f['latent_sse']


class V24ReportTests(unittest.TestCase):
    def test_real_core_to_report_schema_all_initial_configs_no_training(self):
        from test_v24_core import fixture
        from two_player_v24_probe import core
        from two_player_v22.model import Model
        train = fixture()
        schedule = core.build_schedule(train, lambda: None)
        rows = []
        for family in r.FAMILIES:
            for hidden, latent in r.CAPACITIES:
                for seed in r.SEEDS:
                    config = r.Config(variant=family, hidden=hidden, latent=latent, seed=seed,
                                      jepa_weight=.1 if family == 'raw-jepa' else 1.)
                    measured = core.measure(Model(config), train, schedule, lambda: None)
                    rows.extend({**row, 'config': asdict(config)} for row in measured['rows'])
        result = r.summarize(rows, schedule)
        self.assertEqual(result['verification_errors'], [])
        self.assertEqual(result['status'], 'verified_probe')
        self.assertEqual(len(result['rows']), 72)
        self.assertTrue(all(row['predicted_order_violations'] is None
                            for row in result['rows'] if row['direct']))

    def test_complete_context_retained_and_terminal_sensitivity_not_hidden(self):
        rows, schedule = rows_fixture(), schedule_fixture()
        before = deepcopy(rows), deepcopy(schedule)
        report = r.summarize(rows, schedule)
        self.assertEqual(report['verification_errors'], [])
        self.assertEqual(report['status'], 'verified_probe')
        self.assertEqual(len(report['rows']), 72)
        self.assertIsNone(report['candidate'])
        self.assertEqual(len(report['screens']), 4)
        for screen in report['screens']:
            self.assertTrue(screen['primary']['material_obstruction'])
            self.assertFalse(screen['nonterminal_sensitivity']['material_obstruction'])
            self.assertIn('terminal-sensitive', screen['planning_relevance_limit'])
        self.assertIn('complete runtime journal and matching report hash', r.markdown(report))
        self.assertEqual((rows, schedule), before)

    def test_full_denominator_primary_cannot_be_replaced_by_packed_or_NT(self):
        rows = rows_fixture()
        for row in rows:
            if row['config']['variant'] == 'raw-jepa' and row['target_space'] == 'ema':
                change_bound(row, 'packed', .9, 'all_h1')
                change_bound(row, 'packed_nonterminal', .8, 'all_nonterminal')
        report = r.summarize(rows, schedule_fixture())
        self.assertEqual(report['verification_errors'], [])
        for screen in report['screens']:
            self.assertFalse(screen['primary']['material_obstruction'])
            self.assertTrue(screen['nonterminal_sensitivity']['material_obstruction'])
        # These primary packed ratios exceed10%, but full ratios are9%.
        self.assertGreater(next(x for x in rows if x['config']['variant'] == 'raw-jepa')['packed']['bound_packed_sse_ratio'], .1)

    def test_thresholds_are_inclusive_and_all_seed_ratios_required(self):
        rows = [{'packed': {'bound_full_sse_ratio': v}} for v in (.1, .1, .01)]
        self.assertTrue(r.screen(rows, .25, 'packed')['material_obstruction'])
        self.assertFalse(r.screen(rows, .249, 'packed')['material_obstruction'])
        rows[2]['packed']['bound_full_sse_ratio'] = None
        self.assertFalse(r.screen(rows, .9, 'packed')['material_obstruction'])
        self.assertIsNone(r.screen(rows, .9, 'packed')['median_bound_full_sse_ratio'])

    def test_inventory_direct_and_nonfinite_rejected_without_partial_screen(self):
        for defect in ('missing', 'duplicate', 'direct', 'nan', 'space', 'predicted_order'):
            rows = rows_fixture()
            if defect == 'missing': rows.pop()
            elif defect == 'duplicate': rows[-1] = deepcopy(rows[0])
            elif defect == 'direct': rows[0]['packed']['latent_sse'] = 1.
            elif defect == 'nan': rows[-1]['packed']['absolute_gap_quantiles'][0] = float('nan')
            elif defect == 'space': rows[-1]['target_space'] = 'projected'
            else: rows[-1]['predicted_order_violations'] = 1
            result = r.summarize(rows, schedule_fixture())
            self.assertEqual(result['status'], 'inconclusive', defect)
            self.assertEqual(result['screens'], [])

    def test_bound_normalization_and_geometry_are_validated(self):
        for field in ('bound_mse', 'full_bound_mse', 'bound_full_sse_ratio', 'head_norm', 'target_geometry'):
            rows = rows_fixture(); group = rows[-1]['packed']
            if field == 'target_geometry': group[field]['samples'] += 1
            elif field == 'head_norm': group[field] = float('inf')
            else: group[field] += .01
            self.assertEqual(r.summarize(rows, schedule_fixture())['status'], 'inconclusive', field)
        rows = rows_fixture()
        change_bound(rows[-1], 'packed', 9., 'all_h1')
        self.assertIn('bound exceeds', r.summarize(rows, schedule_fixture())['verification_errors'][0])

    def test_schedule_overlap_and_hash_changes_fail_closed(self):
        schedule = schedule_fixture()
        schedule['games'][r.GAMES[0]]['counts']['used_fraction'] = .75
        self.assertIn('checksum', r.summarize(rows_fixture(), schedule)['verification_errors'][0])
        schedule = schedule_fixture(); group = schedule['games'][r.GAMES[0]]
        group['blocks'][1] = deepcopy(group['blocks'][0])
        group['block_sha256'] = r.digest(group['blocks'])
        schedule['schedule_sha256'] = r.digest({k: v for k, v in schedule.items() if k != 'schedule_sha256'})
        self.assertIn('overlap', r.summarize(rows_fixture(), schedule)['verification_errors'][0])

    def test_empty_packing_is_unsupported_not_zero_error_pass(self):
        schedule, rows = schedule_fixture(), rows_fixture()
        for group in schedule['games'].values():
            group['blocks'] = []; group['block_sha256'] = r.digest([])
            group['counts'].update(selected_blocks=0, used_edges=0, used_fraction=0.,
                                   terminal_block_counts={str(i): 0 for i in range(5)},
                                   nonterminal_blocks=0, used_nonterminal_edges=0, nonterminal_used_fraction=0.)
        schedule['schedule_sha256'] = r.digest({k: v for k, v in schedule.items() if k != 'schedule_sha256'})
        for row in rows:
            for key in ('packed', 'packed_nonterminal'):
                row[key].update(block_count=0, edge_count=0, bound_sse=0., bound_mse=None,
                                full_bound_mse=0., latent_sse=None if row['direct'] else 0., latent_mse=None,
                                bound_packed_sse_ratio=None, bound_full_sse_ratio=None,
                                coordinate_comparisons=0, reversals_strict=0, reversals_1e6=0, near_ties_1e6=0,
                                absolute_gap_quantiles=None, min_absolute_gap_quantiles=None,
                                target_value_gap_quantiles=None, target_geometry=None,
                                target_value_oracle_mse=None, predicted_value_oracle_mse=None,
                                predicted_target_value_mse=None)
        result = r.summarize(rows, schedule)
        self.assertEqual(result['verification_errors'], [])
        self.assertTrue(all(not s['primary']['material_obstruction'] for s in result['screens']))
        self.assertTrue(all(s['primary']['median_bound_full_sse_ratio'] is None for s in result['screens']))

    def test_zero_observed_sse_does_not_pass_as_ratio_zero_or_infinity(self):
        rows = rows_fixture()
        for row in rows:
            if row['direct']: continue
            for key in ('all_h1', 'all_nonterminal', 'packed', 'packed_nonterminal'):
                row[key].update(latent_sse=0., latent_mse=0., predicted_target_value_mse=0.)
            for key in ('packed', 'packed_nonterminal'):
                row[key].update(bound_sse=0., bound_mse=0., full_bound_mse=0.,
                                bound_packed_sse_ratio=None, bound_full_sse_ratio=None,
                                reversals_strict=0, reversals_1e6=0)
        result = r.summarize(rows, schedule_fixture())
        self.assertEqual(result['verification_errors'], [])
        self.assertTrue(all(not s['primary']['material_obstruction'] for s in result['screens']))


if __name__ == '__main__':
    unittest.main()
