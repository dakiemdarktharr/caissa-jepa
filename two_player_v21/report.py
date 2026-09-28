"""Verify the frozen v2.1 development grid; never fit or score models."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from two_player_v2.model import Config, Model, OBJECTIVE_VERSION, VARIANTS
from two_player_v2.report import (SEEDS, RATES, GAMES, CONTROLS, _digest, _read,
                                 _sha, _finite, _require, _score_map, _metrics,
                                 _collapse, paired_bootstrap)
from . import METHOD_VERSION


def weights(variant):
    return (1.,) if variant in ('direct', 'value-dynamics') else (.1, 1.)


def _augmentation(row, config, epoch):
    plan, schedule = row['augmentation'], row['schedule']
    _require(plan['version'] == 'legal-symmetries-v21'
             and plan['rng_namespace'] == 2211 and plan['seed'] == config.seed
             and plan['epoch'] == epoch-1 and plan['samples'] == schedule['samples']
             and plan['index_sha256'] == schedule['index_sha256'],
             'Augmentation protocol, indices or epoch mismatch')
    counts = plan['transform_counts']
    _require(isinstance(counts, dict) and bool(counts), 'Missing augmentation counts')
    totals = {game: 0 for game in GAMES}
    for key, count in counts.items():
        game, transform = key.rsplit('/', 1)
        maximum = 2 if game == 'connect4-4x5' else 8
        _require(game in GAMES and transform.isdigit() and str(int(transform)) == transform
                 and 0 <= int(transform) < maximum and type(count) is int and count > 0,
                 'Invalid augmentation transform count')
        totals[game] += count
    _require(sum(totals.values()) == schedule['samples'], 'Augmentation count mismatch')
    _require(set(schedule['games']) == set(GAMES)
             and all(totals[game] == schedule['games'][game]['fork_draws'] for game in GAMES),
             'Augmentation game counts differ from sampling schedule')
    for key in ('transform_sha256', 'index_sha256'):
        value = plan[key]
        _require(isinstance(value, str) and len(value) == 64
                 and all(c in '0123456789abcdef' for c in value), 'Malformed augmentation hash')


def promotion(configurations):
    """Select global rates/weights and apply the frozen development screen to all models."""
    selected = {}
    for family in VARIANTS:
        options = [configurations[family, rate, weight] for rate in RATES for weight in weights(family)]
        best = min(item['mean_regret'] for item in options)
        ties = [item for item in options if abs(item['mean_regret']-best) <= 1e-12]
        selected[family] = min(ties, key=lambda item: (item['learning_rate'], item['jepa_weight']))
    public = {family: {k: v for k, v in row.items() if k != 'arrays'} for family, row in selected.items()}
    result = {'selected': public, 'candidate': None, 'comparisons': {}, 'status': 'not_promoted', 'reasons': []}
    if any(selected[c]['collapse'] for c in CONTROLS):
        result.update(status='inconclusive', reasons=['A selected control configuration collapsed; it cannot be bypassed'])
        return result
    candidates = [selected[v] for v in ('rjepa', 'raw-jepa') if not selected[v]['collapse']]
    if not candidates:
        result['reasons'] = ['Both globally tuned JEPA candidate configurations are ineligible due to collapse']
        return result
    chosen = min(candidates, key=lambda row: (row['mean_regret'], row['variant'] != 'rjepa'))
    result['candidate'] = {k: v for k, v in chosen.items() if k != 'arrays'}
    strongest = min(CONTROLS, key=lambda name: selected[name]['mean_regret'])
    margin = selected[strongest]['mean_regret'] - chosen['mean_regret']
    if margin < .05:
        result['reasons'].append('Aggregate improvement against the strongest tuned control is below 0.05')
    for name in CONTROLS:
        baseline = selected[name]
        per_game = {g: float(np.mean(baseline['arrays'][g]-chosen['arrays'][g])) for g in GAMES}
        per_seed = np.mean(np.stack([np.mean(baseline['arrays'][g]-chosen['arrays'][g], axis=1) for g in GAMES]), axis=0)
        comparison = {'aggregate_improvement': baseline['mean_regret']-chosen['mean_regret'],
                      'per_game_improvement': per_game,
                      'per_seed_improvement': dict(zip(map(str, SEEDS), per_seed.tolist())),
                      'favorable_seeds': int(np.sum(per_seed > 0)),
                      'bootstrap': paired_bootstrap(chosen['arrays'], baseline['arrays'])}
        result['comparisons'][name] = comparison
        if any(value <= 0 for value in per_game.values()):
            result['reasons'].append('Nonpositive game improvement versus ' + name)
        if comparison['favorable_seeds'] < 2:
            result['reasons'].append('Fewer than two favorable paired seeds versus ' + name)
    result.update(strongest_control=strongest, strongest_control_margin=margin)
    if not result['reasons']:
        result['status'] = 'development_screen_passed'
    return result


def summarize_grid(directory):
    directory = Path(directory).resolve()
    report = {'version': 'v21-development-report02', 'stage': 'development',
              'input_directory': str(directory), 'status': 'inconclusive', 'verification_errors': [],
              'runs': [], 'baselines': {}, 'promotion': None,
              'limitations': ['Grid02 reuses exposed Grid01 development roots; tuning is adaptive and not confirmatory.',
                              'Primary comparisons use augmented tuned controls; shared augmentation gains are not JEPA-specific.',
                              'No uniqueness or publication-readiness claim follows from passing this development screen.',
                              'Intervals condition on two fixed games and three training seeds.',
                              'Equal-update/data comparison is not equal active compute; process-lifetime peak RSS is not a per-model peak.',
                              'No new model fitting, decision scoring, selection-set or final-set access occurs here.']}
    errors = report['verification_errors']
    try:
        ledger = _read(directory/'ledger.json')
        report['runs'] = [{'id': row.get('id'), 'config': row.get('config'), 'status': row.get('status')}
                          for row in ledger.get('runs', [])]
        report['ledger_sha256'] = _sha(directory/'ledger.json')
        report['source'] = ledger['source']
        report['dataset_fingerprint'] = ledger['dataset_fingerprint']
        report['code_commit'] = ledger.get('code_commit')
        report['resources'] = {key: ledger.get(key) for key in ('array_bytes', 'memory_scope', 'process_peak_rss_bytes')}
        _require(ledger['version'] == 'v21-grid02' and ledger['method'] == METHOD_VERSION and ledger['stage'] == 'development', 'Unknown grid/stage')
        _require(ledger['epochs'] == 40 and ledger['draws'] == 16, 'Frozen schedule configuration mismatch')
        _require(ledger['selection_predictions'] == ledger['final_predictions'] == 0, 'Selection/final predictions are present')
        expected = {(v, rate, weight, seed) for v in VARIANTS for rate in RATES for weight in weights(v) for seed in SEEDS}
        observed = [(r['config']['variant'], r['config']['learning_rate'], r['config']['jepa_weight'], r['config']['seed']) for r in ledger['runs']]
        _require(len(observed) == 60 and set(observed) == expected, 'The grid must contain exactly the 60 frozen cells')
        _require(len({r['id'] for r in ledger['runs']}) == 60, 'Duplicate run identifiers')
        for row in ledger['runs']:
            config = Config(**row['config'])
            _require(asdict(config) == asdict(Config(variant=config.variant, seed=config.seed, learning_rate=config.learning_rate, jepa_weight=config.jepa_weight)), 'Nonfrozen model configuration')
            _require(row['id'] == f'{config.variant}-lr{config.learning_rate:g}-w{config.jepa_weight:g}-s{config.seed}', 'Unexpected run path identifier')
        root = Path(__file__).resolve().parents[1]
        _require(isinstance(ledger['source'], dict) and bool(ledger['source']), 'Missing source identity')
        from .runtime import runtime_source
        _require(set(ledger['source']) == set(runtime_source()), 'Source file inventory mismatch')
        for filename, sha in ledger['source'].items():
            path = (root/filename).resolve()
            _require(path.is_relative_to(root), 'Source identity escapes repository')
            _require(hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == sha, 'Current source mismatch: ' + filename)
        _require(_sha(directory/'controls.json') == ledger['controls_sha256'], 'Control receipt checksum mismatch')
        controls = _read(directory/'controls.json')
        schedule = [(r['game'], r['root_id'], r['trajectory']) for r in controls['zero']]
        _require(len(schedule) == ledger['development_roots'] and len(set((g, r) for g, r, t in schedule)) == len(schedule), 'Invalid development root inventory')
        _require(set(g for g, r, t in schedule) == set(GAMES), 'Development game inventory mismatch')
        _require(len(set((g, t) for g, r, t in schedule)) == len(schedule), 'Multiple roots per trajectory require a cluster-aware protocol amendment')
        _require(_digest(schedule) == ledger['development_schedule_sha256'], 'Development schedule fingerprint mismatch')
        report['development_schedule_sha256'] = ledger['development_schedule_sha256']
        _score_map(controls['zero'], schedule, ('exact',))
        report['baselines']['zero'] = _metrics(controls['zero'])
        _require(set(controls['untrained']) == set(map(str, SEEDS)), 'Untrained baseline seed inventory mismatch')
        for seed in SEEDS:
            rows = controls['untrained'][str(seed)]
            _score_map(rows, schedule, ('exact',))
            report['baselines']['untrained-'+str(seed)] = _metrics(rows)
        _require(ledger['control_status_counts'] == {'complete': 4*len(schedule), 'censored': 0, 'error': 0},
                 'Ledger control status counts mismatch')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(f'Grid verification: {type(exc).__name__}: {exc}')
        return report
    paired_schedules, paired_augmentations, verified, cohort = {}, {}, {}, None
    for item, summary in zip(ledger['runs'], report['runs']):
        try:
            _require(item['status'] == 'complete', 'Declared cell did not complete: ' + str(item.get('error', item['status'])))
            path = directory/item['id']
            _require(_sha(path/'receipt.json') == item['receipt_sha256'], 'Receipt checksum mismatch')
            receipt = _read(path/'receipt.json')
            summary['receipt_path'] = str(path/'receipt.json')
            summary['decision_status_counts'] = {status: sum(row['status'] == status for row in receipt['scores'])
                                                 for status in ('complete', 'censored', 'error')}
            config = Config(**item['config'])
            _require(receipt['config'] == item['config'], 'Receipt config mismatch')
            _require(_finite(receipt['seconds']) and receipt['seconds'] >= 0
                     and _finite(receipt['prior_attempt_seconds']) and receipt['prior_attempt_seconds'] >= 0
                     and receipt['prior_attempt_seconds'] + receipt['seconds'] < 180,
                     'Run runtime violates the frozen cap')
            expected_identity = {'source': ledger['source'], 'data': ledger['dataset_fingerprint'],
                                 'config_sha256': _digest(asdict(config)), 'method': METHOD_VERSION, 'objective': OBJECTIVE_VERSION,
                                 'epochs': 40, 'draws': 16, 'python': receipt['identity']['python'],
                                 'numpy': receipt['identity']['numpy']}
            _require(receipt['identity'] == expected_identity, 'Run identity mismatch')
            budget = _read(path/'budget.json')
            _require(budget['status'] == 'complete' and budget['identity'] == expected_identity
                     and budget['limit_seconds'] == 180 and _finite(budget['total_seconds'])
                     and 0 <= budget['total_seconds'] < 180
                     and math.isclose(budget['total_seconds'], receipt['seconds'] + receipt['prior_attempt_seconds'], rel_tol=0, abs_tol=1e-9),
                     'Attempt budget status, identity, cap or total differs from receipt')
            environment = (expected_identity['python'], expected_identity['numpy'])
            if cohort is None:
                cohort = environment
            _require(cohort == environment, 'Mixed runtime environments')
            sha = _sha(path/'checkpoint.npz')
            _require(sha == item['checkpoint_sha256'] == receipt['checkpoint_sha256'], 'Checkpoint checksum mismatch')
            model = Model.load(path/'checkpoint.npz', config, expected_identity)
            _require(model.epoch == receipt['epoch'] == 40 and model.step == receipt['steps'], 'Final checkpoint counters mismatch')
            _require(receipt['parameters'] == model.parameter_counts(), 'Parameter count mismatch')
            history = _read(path/'history.json')
            _require(len(history) == 40, 'Incomplete training history')
            cumulative = 0
            for epoch, row in enumerate(history, 1):
                _require(row['epoch'] == epoch, 'History epoch mismatch')
                _augmentation(row, config, epoch)
                steps = math.ceil(row['schedule']['samples']/config.batch_size)
                _require(steps > 0 and row['steps'] == steps, 'History batch-step mismatch')
                cumulative += steps
                _require(row['step'] == cumulative, 'History cumulative-step mismatch')
            _require(cumulative == model.step, 'History/checkpoint step mismatch')
            schedule_sha = _digest([r['schedule'] for r in history])
            if config.seed not in paired_schedules:
                paired_schedules[config.seed] = schedule_sha
            _require(paired_schedules[config.seed] == schedule_sha, 'Training sampling schedules differ across paired configurations')
            augmentation_sha = _digest([r['augmentation'] for r in history])
            if config.seed not in paired_augmentations:
                paired_augmentations[config.seed] = augmentation_sha
            _require(paired_augmentations[config.seed] == augmentation_sha, 'Augmentation plans differ across paired configurations')
            _score_map(receipt['scores'], schedule, ('exact', 'hybrid'))
            _require(item['decision_status_counts'] == summary['decision_status_counts'],
                     'Ledger decision status counts mismatch')
            collapse = _collapse(receipt['representation'], config.variant)
            summary.update(metrics=_metrics(receipt['scores']), representation=receipt['representation'],
                           collapse=collapse, seconds=receipt['seconds'], prior_attempt_seconds=receipt['prior_attempt_seconds'],
                           total_training_seconds=budget['total_seconds'], budget_sha256=_sha(path/'budget.json'), parameters=receipt['parameters'],
                           checkpoint_sha256=sha, receipt_sha256=item['receipt_sha256'],
                           history_sha256=_sha(path/'history.json'), training_schedule_sha256=schedule_sha,
                           augmentation_schedule_sha256=augmentation_sha,
                           receipt_path=str(path/'receipt.json'), checkpoint_path=str(path/'checkpoint.npz'))
            verified[config.variant, config.learning_rate, config.jepa_weight, config.seed] = receipt, summary
        except (ValueError, KeyError, TypeError, OSError) as exc:
            summary['verification_error'] = f'{type(exc).__name__}: {exc}'
            errors.append(item['id'] + ': ' + summary['verification_error'])
    if ledger.get('status') != 'complete' or ledger.get('failures'):
        errors.append('Ledger records an incomplete grid or failures')
    report['training_schedule_sha256_by_seed'] = paired_schedules
    report['augmentation_schedule_sha256_by_seed'] = paired_augmentations
    if errors:
        return report
    configurations = {}
    for variant in VARIANTS:
        for rate in RATES:
            for weight in weights(variant):
                arrays = {}
                for game in GAMES:
                    roots = [r for g, r, t in schedule if g == game]
                    values = []
                    for seed in SEEDS:
                        scores = verified[variant, rate, weight, seed][0]['scores']
                        mapping = {(r['game'], r['root_id'], r['track']): r['regret'] for r in scores}
                        values.append([mapping[game, r, 'exact'] for r in roots])
                    arrays[game] = np.asarray(values)
                configurations[variant, rate, weight] = {
                    'variant': variant, 'learning_rate': rate, 'jepa_weight': weight, 'arrays': arrays,
                    'mean_regret': float(np.mean([a.mean() for a in arrays.values()])),
                    'per_game_regret': {g: float(a.mean()) for g, a in arrays.items()},
                    'collapse': [{'seed': seed, **finding} for seed in SEEDS for finding in verified[variant, rate, weight, seed][1]['collapse']],
                }
    report['promotion'] = promotion(configurations)
    report['status'] = report['promotion']['status']
    return report


def markdown(report):
    lines = ['# V2.1 development grid report', '', '**Status: '+report['status']+'**', '',
             'This is adaptive development evidence, not confirmation or a publication guarantee.', '',
             'Input artifacts: `'+report['input_directory']+'`.', '']
    for error in report['verification_errors']:
        lines.append('- Verification failure: '+error)
    if report['promotion']:
        promotion_result = report['promotion']
        candidate = promotion_result['candidate']
        lines += ['', 'Candidate: '+(f"{candidate['variant']} at learning rate {candidate['learning_rate']:g}, auxiliary weight {candidate['jepa_weight']:g}" if candidate else 'none eligible')+'.', '']
        for reason in promotion_result['reasons']:
            lines.append('- '+reason)
        lines += ['', '| Tuned family | Global learning rate | Auxiliary weight | Equal-game exact regret |', '| --- | ---: | ---: | ---: |']
        for family, row in promotion_result['selected'].items():
            lines.append(f"| {family} | {row['learning_rate']:g} | {row['jepa_weight']:g} | {row['mean_regret']:.6f} |")
        lines += ['', '| Comparison | Improvement | Development bootstrap 95% interval | Favorable seeds |', '| --- | ---: | --- | ---: |']
        for name, row in promotion_result['comparisons'].items():
            low, high = row['bootstrap']['aggregate_ci95']
            lines.append(f"| Candidate versus {name} | {row['aggregate_improvement']:.6f} | [{low:.6f}, {high:.6f}] | {row['favorable_seeds']}/3 |")
    lines += ['', '| Run | Status | Connect4 exact / hybrid regret | Reversi exact / hybrid regret |', '| --- | --- | --- | --- |']
    for row in report['runs']:
        values = []
        for game in GAMES:
            group = row.get('metrics', {}).get(game, {})
            values.append(' / '.join(f"{group[t]['mean_regret']:.6f}" if group.get(t, {}).get('mean_regret') is not None else 'unavailable' for t in ('exact', 'hybrid')))
        lines.append(f"| {row['id']} | {row['status']} | {values[0]} | {values[1]} |")
    lines += ['', '| Fixed baseline | Connect4 exact regret | Reversi exact regret |', '| --- | ---: | ---: |']
    for name, metrics in report['baselines'].items():
        lines.append(f"| {name} | {metrics[GAMES[0]]['exact']['mean_regret']:.6f} | {metrics[GAMES[1]]['exact']['mean_regret']:.6f} |")
    lines += ['', '## Interpretation limits', ''] + ['- '+text for text in report['limitations']]
    lines += ['', 'JSON retains hashes, source identity, all per-game metrics and paired-seed effects. No failed cell or censored root is deleted.', '']
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid', help='Existing grid output directory')
    parser.add_argument('output', help='New report directory, containing report.json and report.md')
    args = parser.parse_args()
    report = summarize_grid(args.grid)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    (output/'report.md').write_text(markdown(report), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'errors': len(report['verification_errors']), 'output': str(output.resolve())}))


if __name__ == '__main__':
    main()
