"""Synthetic report contract tests; these fixtures are not experiment evidence."""
from dataclasses import asdict
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from two_player_v22 import METHOD_VERSION
from two_player_v22.model import Config, Model, VARIANTS
from two_player_v22.report import (CONTROLS, GAMES, RATES, SEEDS, _digest, _sha,
                                 markdown, paired_bootstrap, promotion, summarize_grid, _counts)
from two_player_v22.runtime import identity, runtime_source, auxiliary_weight, FRACTIONS
from two_player_v22.data import DATA_VERSION, source_identity


def write(path, value):
    Path(path).write_text(json.dumps(value, allow_nan=False), encoding='utf-8')


def configurations():
    result = {}
    for fraction in FRACTIONS:
        for variant in VARIANTS:
            value = {'direct': .4, 'decoded': .45, 'value-dynamics': .5,
                     'ema-value': .35, 'raw-jepa': .1, 'raw-no-response': 0}[variant]
            for rate in RATES:
                arrays = {game: np.full((3, 4), value) for game in GAMES}
                result[fraction, variant, rate] = {'fraction': fraction, 'variant': variant,
                    'learning_rate': rate, 'jepa_weight': auxiliary_weight(variant), 'mean_regret': value,
                    'per_game_regret': {g: value for g in GAMES}, 'collapse': [], 'arrays': arrays}
    return result


def set_arrays(configs, fraction, variant, rate, arrays):
    row = configs[fraction, variant, rate]
    row.update(arrays=arrays, mean_regret=float(np.mean([a.mean() for a in arrays.values()])),
               per_game_regret={g: float(a.mean()) for g, a in arrays.items()})


def counts(variant, fraction):
    unknown = 288 if fraction == .25 else 0
    result = {'encoded_count': 384, 'policy_count': 384-unknown, 'value_count': 384-unknown,
              'value_unlabelled_count': unknown, 'policy_unlabelled_count': unknown, 'terminal_count': 0}
    for h in (1, 2):
        result.update({f'h{h}_eligible_count': 128, f'h{h}_missing_count': 0,
            f'h{h}_unlabelled_count': unknown//3,
            f'h{h}_count': 0 if variant == 'direct' else 128,
            f'h{h}_value_label_count': 0 if variant == 'direct' else 128-unknown//3,
            f'h{h}_latent_count': 128 if variant in ('decoded', 'raw-jepa', 'raw-no-response') else 0,
            f'h{h}_ema_value_count': unknown//3 if variant == 'ema-value' else 0})
    return result


def manifest(fraction):
    unknown = 75 if fraction == .25 else 0
    value = {'version': DATA_VERSION, 'method': METHOD_VERSION, 'fraction': fraction,
             'label_seed': 271828, 'split': 'train', 'role': 'redacted-training',
             'parent_dataset_fingerprint': 'parent-fixture', 'source_identity': source_identity(),
             'root_count': 8, 'parent_audit_status': 'PASSED', 'canonical_label_mask_sha256': 'a'*64,
             'audit': {'status': 'PASSED', 'errors': [], 'canonical_label_mask_sha256': 'a'*64,
                       'counts': {g: {'unique_nonterminal_states': 100,
                           'unlabelled_nonterminal_states': unknown,
                           'labelled_nonterminal_values': 100-unknown,
                           'labelled_nonterminal_policies': 100-unknown,
                           'unlabelled_nonterminal_fraction': unknown/100} for g in GAMES}}}
    value['dataset_fingerprint'] = _digest(value)
    return value


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
    ledger = {'version': 'v22-grid03', 'method': METHOD_VERSION, 'stage': 'development', 'source': source,
              'code_commit': 'fixture-only', 'train_roots': 8,
              'dataset_fingerprints': {str(f): manifest(f)['dataset_fingerprint'] for f in FRACTIONS},
              'label_manifests': {str(f): manifest(f) for f in FRACTIONS},
              'development_fingerprint': 'dev-fixture', 'parent_dataset_fingerprint': 'parent-fixture',
              'epochs': 40, 'draws': 16, 'development_roots': len(schedule),
              'selection_predictions': 0, 'final_predictions': 0,
              'controls_sha256': _sha(directory/'controls.json'),
              'development_schedule_sha256': _digest(schedule), 'status': 'complete',
              'failures': [], 'runs': []}
    ledger['control_status_counts'] = {'complete': 4*len(schedule), 'censored': 0, 'error': 0}
    for fraction in FRACTIONS:
        for variant in VARIANTS:
            for rate in RATES:
                for seed in SEEDS:
                    config = Config(variant=variant, learning_rate=rate, jepa_weight=auxiliary_weight(variant), seed=seed)
                    run_id = f'f{fraction:g}-{variant}-lr{rate:g}-w{config.jepa_weight:g}-s{seed}'
                    path = directory/run_id
                    path.mkdir()
                    expected = identity(config, ledger['label_manifests'][str(fraction)], source)
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
                                'label_and_target_count_totals': counts(variant, fraction),
                                'seconds': .01} for epoch in range(1, 41)]
                    write(path/'history.json', history)
                    geometry = {'samples': 128, 'effective_rank': 4., 'median_std': .1}
                    receipt = {'fraction': fraction, 'identity': expected, 'config': asdict(config), 'seconds': 1.,
                               'prior_attempt_seconds': 0.,
                               'epoch': 40, 'steps': 40, 'checkpoint_sha256': checkpoint_sha,
                               'parameters': model.parameter_counts(), 'scores': decisions(('exact', 'hybrid')),
                               'representation': {g: {'unprojected': geometry, 'projected': geometry} for g in GAMES}}
                    write(path/'receipt.json', receipt)
                    write(path/'budget.json', {'status': 'complete', 'identity': expected, 'total_seconds': 1., 'limit_seconds': 180.})
                    ledger['runs'].append({'id': run_id, 'fraction': fraction, 'config': asdict(config), 'status': 'complete',
                                           'decision_status_counts': {'complete': 2*len(schedule), 'censored': 0, 'error': 0},
                                           'checkpoint_sha256': checkpoint_sha,
                                           'receipt_sha256': _sha(path/'receipt.json')})
    write(directory/'ledger.json', ledger)
    return ledger


class V22ReportTests(unittest.TestCase):
    def test_scarce_selection_reuses_rates_full_and_raw_only(self):
        configs = configurations()
        set_arrays(configs, .25, 'raw-jepa', .001, {g: np.full((3, 4), .05) for g in GAMES})
        # The full arm would prefer the other rate; it cannot retune.
        set_arrays(configs, 1., 'raw-jepa', .001, {g: np.full((3, 4), .9) for g in GAMES})
        result = promotion(configs)
        self.assertEqual(result['status'], 'development_screen_passed')
        self.assertEqual(result['candidate']['variant'], 'raw-jepa')
        self.assertEqual(result['candidate']['learning_rate'], .001)
        self.assertEqual(result['strongest_control'], 'ema-value')
        self.assertEqual(set(result['comparisons']), set(CONTROLS))
        full = result['full_label_sensitivity']['selected']['raw-jepa']
        self.assertEqual(full['learning_rate'], .001)
        self.assertAlmostEqual(full['mean_regret'], .9)
        self.assertEqual(result['selected']['raw-no-response']['mean_regret'], 0)
        self.assertEqual(result['selected']['direct']['learning_rate'], .0003)

    def test_collapse_and_per_game_seed_gates(self):
        configs = configurations()
        configs[.25, 'raw-jepa', .0003]['collapse'] = [{'game': GAMES[0], 'seed': 17}]
        self.assertIsNone(promotion(configs)['candidate'])
        configs[.25, 'ema-value', .0003]['collapse'] = [{'game': GAMES[0], 'seed': 17}]
        self.assertEqual(promotion(configs)['status'], 'inconclusive')
        configs = configurations()
        for rate in RATES:
            set_arrays(configs, .25, 'raw-jepa', rate,
                       {g: np.tile(np.array([.4, .4, 0])[:, None], (1, 4)) for g in GAMES})
        result = promotion(configs)
        self.assertGreater(result['strongest_control_margin'], .05)
        self.assertEqual(result['comparisons']['ema-value']['favorable_seeds'], 1)
        self.assertEqual(result['status'], 'not_promoted')
        for rate in RATES:
            set_arrays(configs, .25, 'raw-jepa', rate,
                       {GAMES[0]: np.zeros((3, 4)), GAMES[1]: np.full((3, 4), .35)})
        self.assertTrue(any('game improvement' in r for r in promotion(configs)['reasons']))

    def test_count_contract_oracle_and_pseudo_denominators(self):
        for fraction in FRACTIONS:
            for variant in VARIANTS:
                row = {'schedule': {'samples': 128}, 'label_and_target_count_totals': counts(variant, fraction)}
                _counts(row, Config(variant=variant), fraction)
                broken = deepcopy(row)
                broken['label_and_target_count_totals']['h1_ema_value_count'] += 1
                with self.assertRaisesRegex(ValueError, 'denominator'):
                    _counts(broken, Config(variant=variant), fraction)

    def test_full_grid_verification_and_cross_fraction_pairing(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            ledger = grid_fixture(directory)
            report = summarize_grid(directory)
            self.assertEqual(report['verification_errors'], [])
            self.assertEqual(report['status'], 'not_promoted')
            self.assertEqual(len(report['runs']), 72)
            self.assertEqual(len(report['training_schedule_sha256_by_seed']), 3)
            self.assertEqual(len(report['label_count_schedule_sha256_by_fraction_seed']), 6)
            self.assertIn('verified', report['full_label_ema_value_equivalence'])
            self.assertIn('f0.25-direct-lr0.001-w1-s17', markdown(report))
            item = next(r for r in ledger['runs'] if r['fraction'] == 1.)
            path = directory/item['id']/'history.json'
            original = path.read_bytes()
            history = json.loads(original)
            history[0]['augmentation']['transform_sha256'] = 'b'*64
            write(path, history)
            result = summarize_grid(directory)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertTrue(any('Augmentation plans' in e for e in result['verification_errors']))
            path.write_bytes(original)
            # Different oracle counts remain structurally consistent but violate pairing.
            item = ledger['runs'][3]
            path = directory/item['id']/'history.json'
            history = json.loads(path.read_text())
            count = history[0]['label_and_target_count_totals']
            count['value_count'] += 1
            count['policy_count'] += 1
            count['value_unlabelled_count'] -= 1
            count['policy_unlabelled_count'] -= 1
            write(path, history)
            self.assertTrue(any('Oracle label-count' in e for e in summarize_grid(directory)['verification_errors']))

    def test_censor_budget_identity_and_manifest_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            ledger = grid_fixture(directory)
            item = ledger['runs'][0]
            receipt_path = directory/item['id']/'receipt.json'
            original = receipt_path.read_bytes()
            receipt = json.loads(original)
            receipt['scores'][0].update(status='censored', regret=None, optimal=None)
            write(receipt_path, receipt)
            item['receipt_sha256'] = _sha(receipt_path)
            write(directory/'ledger.json', ledger)
            report = summarize_grid(directory)
            self.assertEqual(len(report['runs']), 72)
            self.assertEqual(report['status'], 'inconclusive')
            self.assertEqual(report['runs'][0]['decision_status_counts']['censored'], 1)
            receipt_path.write_bytes(original)
            item['receipt_sha256'] = _sha(receipt_path)
            write(directory/'ledger.json', ledger)
            budget_path = directory/item['id']/'budget.json'
            budget = json.loads(budget_path.read_text())
            budget['total_seconds'] = 2.
            write(budget_path, budget)
            self.assertTrue(any('Attempt budget' in e for e in summarize_grid(directory)['verification_errors']))
            budget['total_seconds'] = 1.
            write(budget_path, budget)
            receipt = json.loads(original)
            receipt['identity']['data'] = ledger['dataset_fingerprints']['1.0']
            write(receipt_path, receipt)
            item['receipt_sha256'] = _sha(receipt_path)
            write(directory/'ledger.json', ledger)
            self.assertTrue(any('Run identity' in e for e in summarize_grid(directory)['verification_errors']))
            ledger['label_manifests']['0.25']['label_seed'] = 1
            write(directory/'ledger.json', ledger)
            self.assertTrue(any('manifest fingerprint' in e for e in summarize_grid(directory)['verification_errors']))
            ledger['runs'].pop()
            # Inventory preserved even when the independent manifest check fails first.
            write(directory/'ledger.json', ledger)
            self.assertEqual(len(summarize_grid(directory)['runs']), 71)

    def test_full_label_tensor_equivalence_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            ledger = grid_fixture(directory)
            item = next(r for r in ledger['runs'] if r['fraction'] == 1. and r['config']['variant'] == 'ema-value')
            path = directory/item['id']
            receipt = json.loads((path/'receipt.json').read_text())
            config = Config(**item['config'])
            model = Model.load(path/'checkpoint.npz', config, receipt['identity'])
            model.target['vw'][0, 0] += .1
            model.save(path/'checkpoint.npz', receipt['identity'])
            receipt['checkpoint_sha256'] = item['checkpoint_sha256'] = _sha(path/'checkpoint.npz')
            write(path/'receipt.json', receipt)
            item['receipt_sha256'] = _sha(path/'receipt.json')
            write(directory/'ledger.json', ledger)
            report = summarize_grid(directory)
            self.assertTrue(any('Full-label EMA-value/value-dynamics tensor mismatch' in e for e in report['verification_errors']))
            self.assertEqual(report['status'], 'inconclusive')


if __name__ == '__main__':
    unittest.main()
