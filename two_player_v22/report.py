"""Verify a complete frozen label-access grid; never fit or score models."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from . import METHOD_VERSION
from .model import Config, Model, OBJECTIVE_VERSION, VARIANTS
from .runtime import auxiliary_weight, FRACTIONS
from .data import DATA_VERSION, source_identity
from two_player_v2.report import (SEEDS, RATES, GAMES, _digest, _read, _sha,
                                 _finite, _require, _score_map, _metrics,
                                 _collapse, paired_bootstrap)
from two_player_v21.report import _augmentation

CONTROLS = ('direct', 'value-dynamics', 'decoded', 'ema-value')
COMMON_COUNTS = ('encoded_count', 'policy_count', 'value_count', 'value_unlabelled_count',
                 'policy_unlabelled_count', 'terminal_count',
                 'h1_eligible_count', 'h2_eligible_count', 'h1_missing_count',
                 'h2_missing_count', 'h1_unlabelled_count', 'h2_unlabelled_count')


def _trained_sha(model):
    return _digest({prefix+key: hashlib.sha256(value.tobytes()).hexdigest()
                    for prefix, group in (('p_', model.params), ('t_', model.target),
                                          ('m_', model.m), ('v_', model.v))
                    for key, value in group.items()})


def _manifests(ledger):
    names = {str(f) for f in FRACTIONS}
    _require(set(ledger['dataset_fingerprints']) == set(ledger['label_manifests']) == names,
             'Label regime manifest inventory mismatch')
    _require(len(set(ledger['dataset_fingerprints'].values())) == 2, 'Label regimes share an identity')
    for fraction in FRACTIONS:
        manifest = ledger['label_manifests'][str(fraction)]
        fingerprint = _digest({k: v for k, v in manifest.items() if k not in ('code_commit', 'dataset_fingerprint')})
        _require(fingerprint == manifest['dataset_fingerprint'] == ledger['dataset_fingerprints'][str(fraction)],
                 'Label manifest fingerprint mismatch')
        _require(manifest['version'] == DATA_VERSION and manifest['method'] == METHOD_VERSION
                 and manifest['fraction'] == fraction and manifest['label_seed'] == 271828
                 and manifest['split'] == 'train' and manifest['role'] == 'redacted-training'
                 and manifest['parent_dataset_fingerprint'] == ledger['parent_dataset_fingerprint']
                 and manifest['source_identity'] == source_identity()
                 and manifest['root_count'] == ledger['train_roots'], 'Label manifest protocol mismatch')
        audit = manifest['audit']
        _require(manifest['parent_audit_status'] == audit['status'] == 'PASSED' and not audit['errors']
                 and audit['canonical_label_mask_sha256'] == manifest['canonical_label_mask_sha256'],
                 'Label mask audit failed or changed')
        _require(set(audit['counts']) == set(GAMES), 'Label audit game inventory mismatch')
        for game in GAMES:
            counts = audit['counts'][game]
            total = counts['unique_nonterminal_states']
            unknown = counts['unlabelled_nonterminal_states']
            labelled = counts['labelled_nonterminal_values']
            _require(type(total) is int and total > 0 and type(unknown) is int and 0 <= unknown <= total
                     and type(labelled) is int and labelled+unknown == total
                     and counts['labelled_nonterminal_policies'] == labelled
                     and math.isclose(counts['unlabelled_nonterminal_fraction'], unknown/total, rel_tol=0, abs_tol=1e-12),
                     'Inconsistent canonical label counts')
            _require((unknown/total >= .5 if fraction == .25 else unknown == 0),
                     'Label access readiness gate failed')


def _counts(row, config, fraction):
    counts = row['label_and_target_count_totals']
    _require(isinstance(counts, dict) and all(type(value) is int and value >= 0 for value in counts.values()),
             'Invalid label/target count totals')
    n = row['schedule']['samples']
    _require(counts['h1_eligible_count'] == n and counts['h1_missing_count'] == 0
             and counts['h2_eligible_count']+counts['h2_missing_count'] == n
             and counts['encoded_count'] == 2*n+counts['h2_eligible_count'], 'Invalid horizon exposure counts')
    _require(counts['value_count']+counts['value_unlabelled_count'] == counts['encoded_count']
             and counts['policy_count']+counts['policy_unlabelled_count']+counts['terminal_count'] == counts['encoded_count']
             and counts['policy_count']+counts['terminal_count'] == counts['value_count'],
             'Invalid oracle label counts')
    if fraction == 1.:
        _require(counts['value_unlabelled_count'] == counts['policy_unlabelled_count'] == 0,
                 'Full-label schedule contains hidden labels')
    for h in (1, 2):
        eligible = counts[f'h{h}_eligible_count']
        unknown = counts[f'h{h}_unlabelled_count']
        active = config.variant != 'direct'
        _require(unknown <= eligible and (fraction != 1. or unknown == 0)
                 and counts[f'h{h}_count'] == (eligible if active else 0)
                 and counts[f'h{h}_value_label_count'] == (eligible-unknown if active else 0)
                 and counts[f'h{h}_ema_value_count'] == (unknown if config.variant == 'ema-value' else 0)
                 and counts[f'h{h}_latent_count'] == (eligible if config.variant in ('decoded', 'raw-jepa', 'raw-no-response') else 0),
                 'Incorrect per-horizon oracle/pseudo/latent denominator')


def _public(row):
    return {key: value for key, value in row.items() if key != 'arrays'}


def _compare(candidate, control):
    per_game = {g: float(np.mean(control['arrays'][g]-candidate['arrays'][g])) for g in GAMES}
    per_seed = np.mean(np.stack([np.mean(control['arrays'][g]-candidate['arrays'][g], axis=1) for g in GAMES]), axis=0)
    interval = paired_bootstrap(candidate['arrays'], control['arrays'])
    interval['label_mask_scope'] = 'One fixed label mask; no resampling of label-selection seeds'
    return {'aggregate_improvement': control['mean_regret']-candidate['mean_regret'],
            'per_game_improvement': per_game, 'per_seed_improvement': dict(zip(map(str, SEEDS), per_seed.tolist())),
            'favorable_seeds': int(np.sum(per_seed > 0)), 'bootstrap': interval}


def promotion(configurations):
    selected = {}
    for family in VARIANTS:
        options = [configurations[.25, family, rate] for rate in RATES]
        best = min(row['mean_regret'] for row in options)
        selected[family] = min((row for row in options if abs(row['mean_regret']-best) <= 1e-12),
                               key=lambda row: row['learning_rate'])
    full = {family: configurations[1., family, row['learning_rate']] for family, row in selected.items()}
    full_result = {'fraction': 1., 'rate_selection': 'reuse scarce-selected rate for each family',
                   'selected': {family: _public(row) for family, row in full.items()},
                   'comparisons': {}, 'status': 'descriptive_only'}
    if any(full[name]['collapse'] for name in (*CONTROLS, 'raw-jepa')):
        full_result['status'] = 'inconclusive_due_to_selected_collapse'
    else:
        full_result['comparisons'] = {name: _compare(full['raw-jepa'], full[name]) for name in CONTROLS}
    result = {'primary_fraction': .25, 'selected': {family: _public(row) for family, row in selected.items()},
              'candidate': None, 'comparisons': {}, 'status': 'not_promoted', 'reasons': [],
              'full_label_sensitivity': full_result}
    if any(selected[name]['collapse'] for name in CONTROLS):
        result.update(status='inconclusive', reasons=['A scarce-selected control collapsed; it cannot be bypassed'])
        return result
    chosen = selected['raw-jepa']
    if chosen['collapse']:
        result['reasons'] = ['The globally tuned raw-JEPA candidate is ineligible due to collapse']
        return result
    result['candidate'] = _public(chosen)
    strongest = min(CONTROLS, key=lambda name: selected[name]['mean_regret'])
    margin = selected[strongest]['mean_regret']-chosen['mean_regret']
    if margin < .05:
        result['reasons'].append('Aggregate improvement against the strongest tuned control is below 0.05')
    for name in CONTROLS:
        comparison = _compare(chosen, selected[name])
        result['comparisons'][name] = comparison
        if any(value <= 0 for value in comparison['per_game_improvement'].values()):
            result['reasons'].append('Nonpositive game improvement versus '+name)
        if comparison['favorable_seeds'] < 2:
            result['reasons'].append('Fewer than two favorable paired seeds versus '+name)
    result.update(strongest_control=strongest, strongest_control_margin=margin)
    if not result['reasons']:
        result['status'] = 'development_screen_passed'
    return result


def summarize_grid(directory):
    directory = Path(directory).resolve()
    report = {'version': 'v22-development-report03', 'stage': 'development',
              'input_directory': str(directory), 'status': 'inconclusive', 'verification_errors': [],
              'runs': [], 'baselines': {}, 'promotion': None,
              'limitations': ['Grid03 reuses exposed development roots; tuning is adaptive and not confirmatory.',
                              'Intervals condition on one fixed label mask; optimizer seeds do not measure label-selection uncertainty.',
                              'Scarce-arm selected rates are reused unchanged for the full-label sensitivity arm.',
                              'This simulates label access on an already solved bank; no oracle-compute saving is demonstrated.',
                              'Primary comparisons use augmented tuned controls; shared augmentation gains are not JEPA-specific.',
                              'No uniqueness or publication-readiness claim follows from passing this development screen.',
                              'Intervals condition on two fixed games and three training seeds.',
                              'Equal-update/data comparison is not equal active compute; process-lifetime peak RSS is not a per-model peak.',
                              'No new model fitting, decision scoring, selection-set or final-set access occurs here.']}
    errors = report['verification_errors']
    try:
        ledger = _read(directory/'ledger.json')
        report['runs'] = [{'id': row.get('id'), 'fraction': row.get('fraction'), 'config': row.get('config'), 'status': row.get('status')}
                          for row in ledger.get('runs', [])]
        report['ledger_sha256'] = _sha(directory/'ledger.json')
        report['source'] = ledger['source']
        report['dataset_fingerprints'] = ledger['dataset_fingerprints']
        report['development_fingerprint'] = ledger['development_fingerprint']
        report['parent_dataset_fingerprint'] = ledger['parent_dataset_fingerprint']
        report['label_manifests'] = ledger['label_manifests']
        _manifests(ledger)
        report['code_commit'] = ledger.get('code_commit')
        report['resources'] = {key: ledger.get(key) for key in ('array_bytes', 'memory_scope', 'process_peak_rss_bytes')}
        _require(ledger['version'] == 'v22-grid03' and ledger['method'] == METHOD_VERSION and ledger['stage'] == 'development', 'Unknown grid/stage')
        _require(ledger['epochs'] == 40 and ledger['draws'] == 16, 'Frozen schedule configuration mismatch')
        _require(ledger['selection_predictions'] == ledger['final_predictions'] == 0, 'Selection/final predictions are present')
        expected = {(fraction, v, rate, auxiliary_weight(v), seed) for fraction in FRACTIONS for v in VARIANTS for rate in RATES for seed in SEEDS}
        observed = [(r['fraction'], r['config']['variant'], r['config']['learning_rate'], r['config']['jepa_weight'], r['config']['seed']) for r in ledger['runs']]
        _require(len(observed) == 72 and set(observed) == expected, 'The grid must contain exactly the 72 frozen cells')
        _require(len({r['id'] for r in ledger['runs']}) == 72, 'Duplicate run identifiers')
        for row in ledger['runs']:
            config = Config(**row['config'])
            _require(asdict(config) == asdict(Config(variant=config.variant, seed=config.seed, learning_rate=config.learning_rate, jepa_weight=auxiliary_weight(config.variant))), 'Nonfrozen model configuration')
            _require(row['id'] == f"f{row['fraction']:g}-{config.variant}-lr{config.learning_rate:g}-w{config.jepa_weight:g}-s{config.seed}", 'Unexpected run path identifier')
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
    paired_schedules, paired_augmentations, paired_labels, verified, cohort = {}, {}, {}, {}, None
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
            fraction = item['fraction']
            _require(receipt['fraction'] == fraction, 'Receipt label fraction mismatch')
            _require(receipt['config'] == item['config'], 'Receipt config mismatch')
            _require(_finite(receipt['seconds']) and receipt['seconds'] >= 0
                     and _finite(receipt['prior_attempt_seconds']) and receipt['prior_attempt_seconds'] >= 0
                     and receipt['prior_attempt_seconds'] + receipt['seconds'] < 180,
                     'Run runtime violates the frozen cap')
            expected_identity = {'source': ledger['source'], 'data': ledger['dataset_fingerprints'][str(float(fraction))],
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
                _counts(row, config, fraction)
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
            label_sha = _digest([{k: row['label_and_target_count_totals'][k] for k in COMMON_COUNTS} for row in history])
            label_key = f'{fraction:g}/{config.seed}'
            if label_key not in paired_labels:
                paired_labels[label_key] = label_sha
            _require(paired_labels[label_key] == label_sha, 'Oracle label-count schedules differ across paired models')
            _score_map(receipt['scores'], schedule, ('exact', 'hybrid'))
            _require(item['decision_status_counts'] == summary['decision_status_counts'],
                     'Ledger decision status counts mismatch')
            collapse = _collapse(receipt['representation'], config.variant)
            summary.update(metrics=_metrics(receipt['scores']), representation=receipt['representation'],
                           collapse=collapse, seconds=receipt['seconds'], prior_attempt_seconds=receipt['prior_attempt_seconds'],
                           total_training_seconds=budget['total_seconds'], budget_sha256=_sha(path/'budget.json'), parameters=receipt['parameters'],
                           checkpoint_sha256=sha, receipt_sha256=item['receipt_sha256'],
                           history_sha256=_sha(path/'history.json'), training_schedule_sha256=schedule_sha,
                           augmentation_schedule_sha256=augmentation_sha, label_count_schedule_sha256=label_sha,
                           label_and_target_count_totals={k: sum(r['label_and_target_count_totals'][k] for r in history)
                                                          for k in history[0]['label_and_target_count_totals']},
                           trained_tensor_sha256=_trained_sha(model),
                           receipt_path=str(path/'receipt.json'), checkpoint_path=str(path/'checkpoint.npz'))
            verified[fraction, config.variant, config.learning_rate, config.seed] = receipt, summary
        except (ValueError, KeyError, TypeError, OSError) as exc:
            summary['verification_error'] = f'{type(exc).__name__}: {exc}'
            errors.append(item['id'] + ': ' + summary['verification_error'])
    if ledger.get('status') != 'complete' or ledger.get('failures'):
        errors.append('Ledger records an incomplete grid or failures')
    report['training_schedule_sha256_by_seed'] = paired_schedules
    report['augmentation_schedule_sha256_by_seed'] = paired_augmentations
    report['label_count_schedule_sha256_by_fraction_seed'] = paired_labels
    if errors:
        return report
    for rate in RATES:
        for seed in SEEDS:
            a = verified[1., 'value-dynamics', rate, seed][1]['trained_tensor_sha256']
            b = verified[1., 'ema-value', rate, seed][1]['trained_tensor_sha256']
            if a != b:
                errors.append(f'Full-label EMA-value/value-dynamics tensor mismatch at rate {rate:g}, seed {seed}')
    if errors:
        return report
    report['full_label_ema_value_equivalence'] = 'verified online, EMA and Adam tensors for all six rate/seed pairs'
    configurations = {}
    for fraction in FRACTIONS:
        for variant in VARIANTS:
            for rate in RATES:
                arrays = {}
                for game in GAMES:
                    roots = [r for g, r, t in schedule if g == game]
                    values = []
                    for seed in SEEDS:
                        scores = verified[fraction, variant, rate, seed][0]['scores']
                        mapping = {(r['game'], r['root_id'], r['track']): r['regret'] for r in scores}
                        values.append([mapping[game, r, 'exact'] for r in roots])
                    arrays[game] = np.asarray(values)
                configurations[fraction, variant, rate] = {
                    'fraction': fraction, 'variant': variant, 'learning_rate': rate,
                    'jepa_weight': auxiliary_weight(variant), 'arrays': arrays,
                    'mean_regret': float(np.mean([a.mean() for a in arrays.values()])),
                    'per_game_regret': {g: float(a.mean()) for g, a in arrays.items()},
                    'collapse': [{'seed': seed, **finding} for seed in SEEDS
                                 for finding in verified[fraction, variant, rate, seed][1]['collapse']],
                }
    report['promotion'] = promotion(configurations)
    report['status'] = report['promotion']['status']
    return report


def markdown(report):
    lines = ['# V2.2 restricted-label development grid report', '', '**Status: '+report['status']+'**', '',
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
        lines += ['', 'Primary scarce arm (25% selected roots; actual state-label counts are in JSON).', '', '| Comparison | Improvement | Development bootstrap 95% interval | Favorable seeds |', '| --- | ---: | --- | ---: |']
        for name, row in promotion_result['comparisons'].items():
            low, high = row['bootstrap']['aggregate_ci95']
            lines.append(f"| Candidate versus {name} | {row['aggregate_improvement']:.6f} | [{low:.6f}, {high:.6f}] | {row['favorable_seeds']}/3 |")
        lines += ['', 'Full-label sensitivity uses exactly the scarce-selected rate for each family.', '',
                  '| Family | Reused rate | Full-label exact regret | Collapse findings |',
                  '| --- | ---: | ---: | ---: |']
        for family, row in promotion_result['full_label_sensitivity']['selected'].items():
            lines.append(f"| {family} | {row['learning_rate']:g} | {row['mean_regret']:.6f} | {len(row['collapse'])} |")
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
