"""Synthetic report contract tests; these fixtures are not experiment evidence."""
from dataclasses import asdict
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from two_player_v21 import METHOD_VERSION
from two_player_v2.model import Config, Model, VARIANTS
from two_player_v21.report import (CONTROLS, GAMES, RATES, SEEDS, _digest, _sha,
                                 markdown, paired_bootstrap, promotion, summarize_grid, weights, _augmentation)
from two_player_v21.runtime import identity, runtime_source


def write(path, value):
    Path(path).write_text(json.dumps(value, allow_nan=False), encoding='utf-8')


def configurations():
    result = {}
    for variant in VARIANTS:
        value = {'direct': .4, 'decoded': .45, 'value-dynamics': .5,
                 'rjepa': .1, 'raw-jepa': .2, 'no-response': 0}[variant]
        for rate in RATES:
            for weight in weights(variant):
                arrays = {game: np.full((3, 4), value) for game in GAMES}
                result[variant, rate, weight] = {'variant': variant, 'learning_rate': rate,
                    'jepa_weight': weight, 'mean_regret': value,
                    'per_game_regret': {g: value for g in GAMES}, 'collapse': [], 'arrays': arrays}
    return result


def set_arrays(configs, variant, arrays):
    for rate in RATES:
        for weight in weights(variant):
            row = configs[variant, rate, weight]
            row['arrays'] = arrays
            row['mean_regret'] = float(np.mean([a.mean() for a in arrays.values()]))
            row['per_game_regret'] = {g: float(a.mean()) for g, a in arrays.items()}


def grid_fixture(directory):
    source = runtime_source()
    schedule = [(game, game+'-root'+str(i), game+'-trajectory'+str(i)) for game in GAMES for i in range(2)]

    def decisions(tracks):
        return [{'game': game, 'root_id': root, 'trajectory': trajectory, 'split': 'development',
                 'track': track, 'status': 'complete', 'regret': i % 2, 'optimal': i % 2 == 0,
                 'seconds': .0001, 'transitions': 12, 'neural_leaves': 3}
                for i, (game, root, trajectory) in enumerate(schedule) for track in tracks]

    controls = {'zero': decisions(('exact',)),
                'untrained': {str(seed): decisions(('exact',)) for seed in SEEDS}}
    write(directory/'controls.json', controls)
    ledger = {'version': 'v21-grid02', 'method': METHOD_VERSION, 'stage': 'development', 'source': source,
              'code_commit': 'fixture-only', 'dataset_fingerprint': 'fixture-dataset',
              'epochs': 40, 'draws': 16, 'development_roots': len(schedule),
              'selection_predictions': 0, 'final_predictions': 0,
              'controls_sha256': _sha(directory/'controls.json'),
              'development_schedule_sha256': _digest(schedule), 'status': 'complete',
              'failures': [], 'runs': []}
    ledger['control_status_counts'] = {'complete': 4*len(schedule), 'censored': 0, 'error': 0}
    for variant in VARIANTS:
        for rate in RATES:
            for weight in weights(variant):
                for seed in SEEDS:
                    config = Config(variant=variant, learning_rate=rate, jepa_weight=weight, seed=seed)
                    run_id = f'{variant}-lr{rate:g}-w{weight:g}-s{seed}'
                    path = directory/run_id
                    path.mkdir()
                    expected = identity(config, ledger, source)
                    model = Model(config)
                    model.epoch, model.step = 40, 40
                    model.save(path/'checkpoint.npz', expected)
                    checkpoint_sha = _sha(path/'checkpoint.npz')
                    history = [{'epoch': epoch, 'step': epoch, 'steps': 1,
                                'schedule': {'samples': 128, 'index_sha256': _digest([seed, epoch]),
                                             'games': {g: {'fork_draws': 64} for g in GAMES}},
                                'augmentation': {'version': 'legal-symmetries-v21', 'samples': 128,
                                    'seed': seed, 'epoch': epoch-1, 'rng_namespace': 2211,
                                    'transform_counts': {g+'/0': 64 for g in GAMES},
                                    'transform_sha256': _digest([seed, epoch, 'transform']),
                                    'index_sha256': _digest([seed, epoch])},
                                'seconds': .01} for epoch in range(1, 41)]
                    write(path/'history.json', history)
                    geometry = {'samples': 128, 'effective_rank': 4., 'median_std': .1}
                    receipt = {'identity': expected, 'config': asdict(config), 'seconds': 1.,
                               'prior_attempt_seconds': 0.,
                               'epoch': 40, 'steps': 40, 'checkpoint_sha256': checkpoint_sha,
                               'parameters': model.parameter_counts(), 'scores': decisions(('exact', 'hybrid')),
                               'representation': {g: {'unprojected': geometry, 'projected': geometry} for g in GAMES}}
                    write(path/'receipt.json', receipt)
                    write(path/'budget.json', {'status': 'complete', 'identity': expected, 'total_seconds': 1., 'limit_seconds': 180.})
                    ledger['runs'].append({'id': run_id, 'config': asdict(config), 'status': 'complete',
                                           'decision_status_counts': {'complete': 2*len(schedule), 'censored': 0, 'error': 0},
                                           'checkpoint_sha256': checkpoint_sha,
                                           'receipt_sha256': _sha(path/'receipt.json')})
    write(directory/'ledger.json', ledger)
    return ledger


class V21ReportTests(unittest.TestCase):
    def test_global_tuning_ties_and_candidate_attribution(self):
        configs = configurations()
        result = promotion(configs)
        self.assertEqual(result['status'], 'development_screen_passed')
        self.assertEqual(result['candidate']['variant'], 'rjepa')
        self.assertTrue(all(row['learning_rate'] == .0003 for row in result['selected'].values()))
        self.assertTrue(all(row['jepa_weight'] == min(weights(family)) for family, row in result['selected'].items()))
        self.assertEqual(result['strongest_control'], 'direct')
        # No-response has the lowest regret but cannot become a candidate.
        self.assertEqual(result['selected']['no-response']['mean_regret'], 0)
        # Exact family tie selects rjepa; one global rate is selected for all seeds.
        set_arrays(configs, 'raw-jepa', {g: np.full((3, 4), .1) for g in GAMES})
        self.assertEqual(promotion(configs)['candidate']['variant'], 'rjepa')

    def test_global_weight_selection_and_lexicographic_tie(self):
        configs = configurations()
        row = configs['rjepa', .001, 1.]
        row.update(mean_regret=.05, arrays={g: np.full((3, 4), .05) for g in GAMES},
                   per_game_regret={g: .05 for g in GAMES})
        selected = promotion(configs)['selected']['rjepa']
        self.assertEqual((selected['learning_rate'], selected['jepa_weight']), (.001, 1.))
        # A tie within tolerance uses rate first, even if that selects a larger weight.
        row = configs['rjepa', .0003, 1.]
        row.update(mean_regret=.05+5e-13, arrays={g: np.full((3, 4), .05+5e-13) for g in GAMES},
                   per_game_regret={g: .05+5e-13 for g in GAMES})
        selected = promotion(configs)['selected']['rjepa']
        self.assertEqual((selected['learning_rate'], selected['jepa_weight']), (.0003, 1.))

    def test_augmentation_protocol_checks(self):
        row = {'schedule': {'samples': 128, 'index_sha256': 'a'*64,
                            'games': {g: {'fork_draws': 64} for g in GAMES}},
               'augmentation': {'version': 'legal-symmetries-v21', 'samples': 128,
                                'seed': 17, 'epoch': 0, 'rng_namespace': 2211,
                                'transform_counts': {g+'/0': 64 for g in GAMES},
                                'index_sha256': 'a'*64, 'transform_sha256': 'b'*64}}
        _augmentation(row, Config(seed=17), 1)
        for key, value in [('seed', 29), ('epoch', 1), ('rng_namespace', 2201),
                           ('index_sha256', 'c'*64), ('samples', 129), ('transform_sha256', 'bad'),
                           ('transform_counts', {GAMES[0]+'/2': 64, GAMES[1]+'/0': 64}),
                           ('transform_counts', {GAMES[0]+'/0': 63, GAMES[1]+'/0': 65})]:
            with self.subTest(key=key, value=value):
                broken = deepcopy(row)
                broken['augmentation'][key] = value
                with self.assertRaises(ValueError):
                    _augmentation(broken, Config(seed=17), 1)

    def test_per_game_and_paired_seed_gates(self):
        configs = configurations()
        set_arrays(configs, 'rjepa', {GAMES[0]: np.zeros((3, 4)), GAMES[1]: np.full((3, 4), .5)})
        set_arrays(configs, 'raw-jepa', {g: np.full((3, 4), .8) for g in GAMES})
        result = promotion(configs)
        self.assertEqual(result['status'], 'not_promoted')
        self.assertTrue(any('game improvement' in reason for reason in result['reasons']))
        configs = configurations()
        set_arrays(configs, 'rjepa', {g: np.tile(np.array([.5, .5, 0])[:, None], (1, 4)) for g in GAMES})
        set_arrays(configs, 'raw-jepa', {g: np.full((3, 4), .8) for g in GAMES})
        result = promotion(configs)
        self.assertGreater(result['strongest_control_margin'], .05)
        self.assertEqual(result['comparisons']['direct']['favorable_seeds'], 1)
        self.assertEqual(result['status'], 'not_promoted')

    def test_collapse_eligibility_and_failed_control(self):
        configs = configurations()
        configs['rjepa', .0003, .1]['collapse'] = [{'seed': 17, 'game': GAMES[0], 'space': 'projected'}]
        self.assertEqual(promotion(configs)['candidate']['variant'], 'raw-jepa')
        configs['direct', .0003, 1.]['collapse'] = [{'seed': 17, 'game': GAMES[1]}]
        self.assertEqual(promotion(configs)['status'], 'inconclusive')

    def test_bootstrap_reuses_paired_roots_across_seeds(self):
        candidate = {g: np.zeros((3, 3)) for g in GAMES}
        control = {g: np.array([[0., 1., 2.], [.1, .4, .8], [.2, .6, 1.2]]) for g in GAMES}
        result = paired_bootstrap(candidate, control, replicates=2000, seed=901)
        rng = np.random.default_rng(901)
        expected = []
        for _ in range(2000):
            seeds = rng.integers(3, size=3)
            means = []
            for game in GAMES:
                roots = rng.integers(3, size=3)
                means.append(control[game][seeds][:, roots].mean())
            expected.append(np.mean(means))
        np.testing.assert_array_equal(result['aggregate_ci95'], np.quantile(expected, [.025, .975]))
        identical = paired_bootstrap(control, control)
        self.assertEqual(identical['aggregate_ci95'], [0., 0.])

    def test_full_receipts_hashes_schedules_and_censors(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            ledger = grid_fixture(directory)
            report = summarize_grid(directory)
            self.assertEqual(report['verification_errors'], [])
            self.assertEqual(report['status'], 'not_promoted')
            self.assertEqual(len(report['runs']), 60)
            self.assertEqual(len(report['baselines']), 4)
            self.assertIn('direct-lr0.001-w1-s17', markdown(report))
            item = ledger['runs'][0]
            path = directory/item['id']/'receipt.json'
            original = path.read_bytes()
            receipt = json.loads(original)
            receipt['scores'][0].update(status='censored', regret=None, optimal=None)
            write(path, receipt)
            item['receipt_sha256'] = _sha(path)
            write(directory/'ledger.json', ledger)
            censored = summarize_grid(directory)
            self.assertEqual(censored['status'], 'inconclusive')
            self.assertEqual(len(censored['runs']), 60)
            self.assertEqual(censored['runs'][0]['decision_status_counts']['censored'], 1)
            self.assertTrue(any('Censored' in e for e in censored['verification_errors']))
            path.write_bytes(original)
            item['receipt_sha256'] = _sha(path)
            write(directory/'ledger.json', ledger)
            budget_path = directory/item['id']/'budget.json'
            budget = json.loads(budget_path.read_text())
            budget['total_seconds'] = 2.
            write(budget_path, budget)
            inconsistent = summarize_grid(directory)
            self.assertTrue(any('Attempt budget' in e for e in inconsistent['verification_errors']))
            resumed_receipt = json.loads(original)
            resumed_receipt['prior_attempt_seconds'] = 1.
            write(path, resumed_receipt)
            item['receipt_sha256'] = _sha(path)
            write(directory/'ledger.json', ledger)
            resumed = summarize_grid(directory)
            self.assertEqual(resumed['verification_errors'], [])
            self.assertEqual(resumed['runs'][0]['total_training_seconds'], 2.)
            budget['status'] = 'active'
            write(budget_path, budget)
            self.assertTrue(any('Attempt budget' in e for e in summarize_grid(directory)['verification_errors']))
            budget['status'] = 'complete'
            write(budget_path, budget)
            history_path = directory/ledger['runs'][3]['id']/'history.json'
            history = json.loads(history_path.read_text())
            history[0]['augmentation']['transform_sha256'] = 'a'*64
            write(history_path, history)
            changed = summarize_grid(directory)
            self.assertEqual(changed['status'], 'inconclusive')
            self.assertTrue(any('Augmentation plans' in e for e in changed['verification_errors']))

    def test_missing_cell_or_baseline_tamper_preserves_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            ledger = grid_fixture(directory)
            ledger['runs'][0]['status'] = 'failed'
            ledger['failures'] = [ledger['runs'][0]['id']]
            write(directory/'ledger.json', ledger)
            report = summarize_grid(directory)
            self.assertEqual(report['status'], 'inconclusive')
            self.assertEqual(len(report['runs']), 60)
            self.assertEqual(report['runs'][0]['status'], 'failed')
            (directory/'controls.json').write_text('{}')
            report = summarize_grid(directory)
            self.assertTrue(any('Control receipt checksum' in e for e in report['verification_errors']))
            self.assertEqual(len(report['runs']), 60)
            ledger['runs'].pop()
            write(directory/'ledger.json', ledger)
            report = summarize_grid(directory)
            self.assertTrue(any('60 frozen cells' in e for e in report['verification_errors']))


if __name__ == '__main__':
    unittest.main()
