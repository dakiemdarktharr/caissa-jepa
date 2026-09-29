"""Publish aggregate-only V2.5 results from a completed strict report.

Usage: python tools/compact_v25_report.py FINAL_REPORT.json NEW_OUTPUT.json
This does not inspect grid directories, datasets, checkpoints or model outputs.
Run the strict artifact verifier and independent audit before using this helper.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

VERSION = 'v25-public-summary01'
SOURCE_VERSION = 'v25-development-report01'
FAMILIES = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail', 'raw-mean', 'raw-tail', 'raw-scaled')
CONTROLS = FAMILIES[:4]
GAMES = ('connect4-4x5', 'reversi6')
TRACKS = ('exact', 'hybrid')
RATES = (.001, .0003)
SEEDS = (17, 29, 43)
COUNTS = {'connect4-4x5': 107, 'reversi6': 102}
STATUSES = ('not_promoted', 'exploratory_hybrid_only', 'development_screen_passed')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, low=0., high=float('inf')):
    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
            'Invalid finite aggregate number')
    return value


def close(a, b):
    require(math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12), 'Saved aggregate arithmetic disagrees')


def sha(value, length=64):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{'+str(length)+'}', value), 'Missing/invalid provenance hash')
    return value


def keys(obj, expected):
    require(isinstance(obj, dict) and set(obj) == set(expected), 'Unknown or missing aggregate fields')


def strings(values):
    require(isinstance(values, list) and all(isinstance(v, str) for v in values), 'Expected text-only aggregate notes')


def aggregate_inventory(report):
    """Reject unknown fields in every nested structure copied without filtering."""
    config_fields = ('variant', 'seed', 'hidden', 'latent', 'transition_hidden', 'learning_rate', 'aux_weight', 'ema', 'batch_groups')
    for row in report['runs']:
        keys(row['config'], config_fields)
        keys(row['parameters'], ('allocated', 'active', 'ema', 'transition'))
        for value in row['parameters'].values():
            require(type(value) is int and value >= 0, 'Invalid parameter count')
    for row in [*report['configurations'], *report['selected'].values()]:
        keys(row, ('variant', 'learning_rate', 'tracks'))
        keys(row['tracks'], TRACKS)
        for value in row['tracks'].values():
            keys(value, ('mean_regret', 'per_game_regret', 'per_seed_regret', 'action_oracle_mse',
                         'per_game_action_oracle_mse', 'roots_per_game_per_seed'))
            keys(value['per_game_regret'], GAMES); keys(value['per_game_action_oracle_mse'], GAMES)
            keys(value['roots_per_game_per_seed'], GAMES); keys(value['per_seed_regret'], map(str, SEEDS))
    for gate in report['tracks'].values():
        keys(gate, ('passed', 'strongest_control', 'strongest_control_margin', 'comparisons', 'reasons'))
        strings(gate['reasons'])
    mechanism = report['mechanism']
    keys(mechanism, ('passed', 'ablations', 'action_oracle_mse', 'reasons'))
    strings(mechanism['reasons'])
    for value in mechanism['action_oracle_mse'].values():
        keys(value, ('candidate_mse', 'control_mse', 'improvement'))
    comparisons = [c for t in report['tracks'].values() for c in t['comparisons'].values()]
    for comparison in [*comparisons, *mechanism['ablations'].values()]:
        keys(comparison, ('aggregate_improvement', 'per_game_improvement', 'per_seed_improvement', 'favorable_seeds', 'bootstrap'))
        keys(comparison['per_game_improvement'], GAMES); keys(comparison['per_seed_improvement'], map(str, SEEDS))
        b = comparison['bootstrap']
        keys(b, ('replicates', 'seed_sequence', 'resampling', 'aggregate_ci95', 'per_game_ci95', 'scope'))
        keys(b['per_game_ci95'], GAMES)
        require(isinstance(b['resampling'], str) and isinstance(b['scope'], str), 'Invalid bootstrap scope')
    keys(report['resources'], ('total_cell_seconds', 'total_wall_seconds', 'process_peak_rss_bytes',
                               'memory_scope', 'artifact_bytes', 'array_bytes'))
    require(isinstance(report['resources']['memory_scope'], str), 'Invalid resource scope')
    for artifact in report['artifacts']:
        keys(artifact, ('id', 'receipt_sha256', 'checkpoint_sha256', 'history_sha256', 'budget_sha256',
                        'tensor_sha256', 'training_plan_sha256'))
    strings(report['limitations'])


def read(path):
    raw = Path(path).read_bytes()
    result = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    return result, hashlib.sha256(raw).hexdigest()


def validate(report):
    """Validate saved aggregates, not the underlying scientific artifacts."""
    require(report.get('version') in (VERSION, SOURCE_VERSION), 'Unsupported report version')
    require(report.get('stage') == 'development' and report.get('verification_errors') == [], 'Unverified report')
    require(report.get('status') in STATUSES and report.get('candidate') == 'raw-tail', 'Incomplete/inconclusive candidate report')
    sha(report.get('code_commit'), 40); sha(report.get('ledger_sha256'))
    require(isinstance(report.get('method'), str), 'Invalid method name')
    for key in ('development_truth_sha256', 'development_schedule_sha256', 'train_group_sha256', 'development_group_sha256'):
        sha(report.get(key))
    require(type(report.get('replayed_epoch_plans')) is int and report['replayed_epoch_plans'] >= 0,
            'Invalid replayed-plan count')
    if report['version'] == VERSION:
        require(report.get('source_report_version') == SOURCE_VERSION, 'Missing original report schema')
        sha(report.get('source_report_sha256'))
    require(isinstance(report.get('source'), dict) and bool(report['source']), 'Missing source inventory')
    for value in report['source'].values(): sha(value)
    require(report.get('decision_counts') == {'cells': 42, 'roots_per_cell': 209, 'tracks': 2,
                                            'complete': 17556, 'censored_or_error': 0}, 'Incomplete decision inventory')
    aggregate_inventory(report)
    runs = report.get('runs', [])
    expected = {(v, lr, seed) for v in FAMILIES for lr in RATES for seed in SEEDS}
    keys = [(r['config']['variant'], r['config']['learning_rate'], r['config']['seed']) for r in runs]
    require(len(keys) == 42 and len(set(keys)) == 42 and set(keys) == expected, 'Missing/duplicate cell')
    cells = dict(zip(keys, runs))
    for row in runs:
        require(row['status'] == 'complete' and row['collapse'] == [], 'Failed/collapsed cell cannot be omitted')
        c = row['config']
        require((c['hidden'], c['latent'], c['transition_hidden'], c['batch_groups'], c['aux_weight'], c['ema'])
                == (128, 64, 50, 32, .1, .99), 'Unfrozen model configuration')
        sha(row['checkpoint_sha256']); number(row['seconds'], 0, 600)
        require(row['seconds'] < 600, 'Cell reached frozen time cap')
        require(set(row['metrics']) == set(GAMES), 'Missing per-game results')
        for game in GAMES:
            require(set(row['metrics'][game]) == set(TRACKS), 'Missing evaluation track')
            for track in TRACKS:
                m = row['metrics'][game][track]
                require(m['scheduled'] == m['complete'] == COUNTS[game] and m['censored_or_error'] == 0,
                        'Cell has missing/censored decisions')
                number(m['mean_regret'], 0, 2)
    config_rows = report.get('configurations', [])
    require(len(config_rows) == 14 and {(r['variant'], r['learning_rate']) for r in config_rows}
            == {(v, lr) for v in FAMILIES for lr in RATES}, 'Missing full rate comparison')
    configurations = {(r['variant'], r['learning_rate']): r for r in config_rows}
    for (variant, rate), row in configurations.items():
        require(set(row['tracks']) == set(TRACKS), 'Missing configuration track')
        for track in TRACKS:
            m = row['tracks'][track]
            require(m['roots_per_game_per_seed'] == COUNTS and set(m['per_game_regret']) == set(GAMES)
                    and set(m['per_seed_regret']) == set(map(str, SEEDS)), 'Unpaired aggregate cohort')
            for game in GAMES:
                close(number(m['per_game_regret'][game], 0, 2),
                      sum(cells[variant, rate, s]['metrics'][game][track]['mean_regret'] for s in SEEDS)/3)
            close(number(m['mean_regret'], 0, 2), sum(m['per_game_regret'].values())/2)
            for seed in SEEDS:
                close(number(m['per_seed_regret'][str(seed)], 0, 2),
                      sum(cells[variant, rate, seed]['metrics'][g][track]['mean_regret'] for g in GAMES)/2)
            number(m['action_oracle_mse'], 0, 4)
            require(set(m['per_game_action_oracle_mse']) == set(GAMES), 'Missing action-error game aggregate')
            close(m['action_oracle_mse'], sum(number(v, 0, 4) for v in m['per_game_action_oracle_mse'].values())/2)
    selected = report.get('selected', {})
    require(set(selected) == set(FAMILIES), 'Missing exact-selected family')
    for variant in FAMILIES:
        choices = [configurations[variant, r] for r in RATES]
        best = min(x['tracks']['exact']['mean_regret'] for x in choices)
        chosen = min((x for x in choices if abs(x['tracks']['exact']['mean_regret']-best) <= 1e-12),
                     key=lambda x: x['learning_rate'])
        require(selected[variant] == chosen, 'Selected rate does not follow EXACT-only selection')
    require(set(report['tracks']) == set(TRACKS), 'Missing gate track')
    for ti, track in enumerate(TRACKS):
        gate = report['tracks'][track]
        require(type(gate['passed']) is bool and set(gate['comparisons']) == set(CONTROLS), 'Missing comparator gate')
        for control, comparison in gate['comparisons'].items():
            validate_comparison(comparison, selected, control, track, ti)
        strongest = min(CONTROLS, key=lambda v: selected[v]['tracks'][track]['mean_regret'])
        require(gate['strongest_control'] == strongest, 'Wrong strongest control')
        margin = gate['comparisons'][strongest]['aggregate_improvement']
        close(gate['strongest_control_margin'], margin)
        require(gate['passed'] == (margin >= .05 and all(positive(c) for c in gate['comparisons'].values())),
                'Track gate contradicts frozen effect rules')
    mechanism = report['mechanism']
    require(type(mechanism['passed']) is bool and set(mechanism['ablations']) == {'raw-mean', 'raw-scaled'}, 'Missing mechanism gate')
    for control, comparison in mechanism['ablations'].items():
        validate_comparison(comparison, selected, control, 'hybrid', 1)
    mse = mechanism['action_oracle_mse']
    require(set(mse) == set(CONTROLS)-{'direct'}, 'Missing recurrent action-error controls')
    for control, comparison in mse.items():
        expected_candidate = selected['raw-tail']['tracks']['hybrid']['action_oracle_mse']
        expected_control = selected[control]['tracks']['hybrid']['action_oracle_mse']
        close(number(comparison['candidate_mse'], 0, 4), expected_candidate)
        close(number(comparison['control_mse'], 0, 4), expected_control)
        close(number(comparison['improvement'], -4, 4), expected_control-expected_candidate)
    require(mechanism['passed'] == (report['tracks']['hybrid']['passed']
            and all(positive(c) for c in mechanism['ablations'].values())
            and all(c['improvement'] > 0 for c in mse.values())), 'Mechanism gate contradicts frozen rules')
    status = ('development_screen_passed' if report['tracks']['exact']['passed'] and mechanism['passed']
              else 'exploratory_hybrid_only' if mechanism['passed'] else 'not_promoted')
    require(report['status'] == status, 'Status contradicts declared gates')
    require(isinstance(report.get('resources'), dict), 'Missing strict report resources')
    for key in ('total_cell_seconds', 'total_wall_seconds', 'process_peak_rss_bytes', 'artifact_bytes', 'array_bytes'):
        number(report['resources'][key])
    require(report['resources']['total_cell_seconds'] < 25200
            and report['resources']['process_peak_rss_bytes'] < 1_000_000_000
            and report['resources']['artifact_bytes'] < 3_000_000_000, 'Report exceeds frozen resource caps')
    artifacts = report.get('artifacts', [])
    expected_ids = {f'{v}-lr{lr:g}-s{s}' for v, lr, s in expected}
    require(len(artifacts) == 42 and {a['id'] for a in artifacts} == expected_ids, 'Missing artifact receipts')
    for row in artifacts:
        for key in ('receipt_sha256', 'checkpoint_sha256', 'history_sha256', 'budget_sha256', 'tensor_sha256', 'training_plan_sha256'):
            sha(row[key])
    artifact_by_id = {row['id']: row for row in artifacts}
    for (variant, rate, seed), run in cells.items():
        require(artifact_by_id[f'{variant}-lr{rate:g}-s{seed}']['checkpoint_sha256'] == run['checkpoint_sha256'],
                'Run/checkpoint artifact hashes disagree')
    return report


def positive(comparison):
    return (comparison['aggregate_improvement'] > 0
            and all(x > 0 for x in comparison['per_game_improvement'].values())
            and comparison['favorable_seeds'] >= 2)


def validate_comparison(row, selected, control, track, index):
    candidate, baseline = selected['raw-tail']['tracks'][track], selected[control]['tracks'][track]
    close(number(row['aggregate_improvement'], -2, 2), baseline['mean_regret']-candidate['mean_regret'])
    require(set(row['per_game_improvement']) == set(GAMES) and set(row['per_seed_improvement']) == set(map(str, SEEDS)),
            'Missing paired effects')
    for game in GAMES:
        close(number(row['per_game_improvement'][game], -2, 2), baseline['per_game_regret'][game]-candidate['per_game_regret'][game])
    for seed in map(str, SEEDS):
        close(number(row['per_seed_improvement'][seed], -2, 2), baseline['per_seed_regret'][seed]-candidate['per_seed_regret'][seed])
    require(row['favorable_seeds'] == sum(x > 0 for x in row['per_seed_improvement'].values()), 'Seed direction counts disagree')
    boot = row['bootstrap']
    require(boot['replicates'] == 10000 and boot['seed_sequence'] == [2505, index]
            and set(boot['per_game_ci95']) == set(GAMES), 'Unrecognized bootstrap protocol')
    for bounds in [boot['aggregate_ci95'], *boot['per_game_ci95'].values()]:
        require(isinstance(bounds, list) and len(bounds) == 2, 'Missing saved confidence interval')
        require(number(bounds[0], -2, 2) <= number(bounds[1], -2, 2), 'Reversed confidence interval')


def keep(obj, keys):
    return {k: deepcopy(obj[k]) for k in keys if k in obj}


def geometry(obj):
    if obj is None:
        return None
    fields = ('samples', 'dimensions', 'effective_rank', 'mean_std', 'median_std', 'mean_norm')
    keys(obj, fields)
    for key in ('samples', 'dimensions'):
        require(type(obj[key]) is int and obj[key] >= 0, 'Invalid geometry count')
    for key in fields[2:]:
        if obj[key] is not None: number(obj[key])
    return keep(obj, fields)


def occurrence(obj):
    allowed = ('forks', 'samples', 'missing_states', 'policy_samples', 'terminal_samples',
               'value_mse', 'policy_nll', 'policy_mrr', 'policy_top1_optimal', 'unprojected', 'projected', 'horizons')
    keys(obj, allowed)
    row = keep(obj, ('forks', 'samples', 'missing_states', 'policy_samples', 'terminal_samples',
                     'value_mse', 'policy_nll', 'policy_mrr', 'policy_top1_optimal'))
    for key, value in row.items():
        if key.endswith('samples') or key == 'forks':
            require(type(value) is int and value >= 0, 'Invalid occurrence count')
        elif value is not None: number(value)
    row.update(unprojected=geometry(obj.get('unprojected')), projected=geometry(obj.get('projected')))
    require(set(obj['horizons']) <= {'1', '2'}, 'Unknown horizon')
    for value in obj['horizons'].values():
        keys(value, ('samples', 'online_latent_mse'))
        require(type(value['samples']) is int and value['samples'] >= 0, 'Invalid horizon count')
        if value['online_latent_mse'] is not None: number(value['online_latent_mse'])
    row['horizons'] = {h: keep(x, ('samples', 'online_latent_mse')) for h, x in obj.get('horizons', {}).items()}
    return row


def diagnostic_summary(obj):
    biases = ('target_min_oracle_bias', 'predicted_min_oracle_bias', 'predicted_target_min_error')
    expected = {*biases, *(b+'_squared' for b in biases), 'conditional_oracle_bound'}
    expected |= {h+key for h in ('h1_', 'h2_') for key in ('latent_mean', 'latent_max', 'latent_mean_max',
                 'target_value_oracle_mse', 'target_oracle_max_absolute', 'predicted_value_oracle_mse')}
    keys(obj, expected)
    result = {}
    for key, value in obj.items():
        keys(value, ('count', 'mean', 'max', 'quantiles_0_25_50_75_100'))
        require(type(value['count']) is int and value['count'] >= 0, 'Invalid diagnostic count')
        if value['count']:
            number(value['mean'], -float('inf')); number(value['max'], -float('inf'))
            quantiles = value['quantiles_0_25_50_75_100']
            require(isinstance(quantiles, list) and len(quantiles) == 5, 'Invalid diagnostic quantiles')
            for q in quantiles: number(q, -float('inf'))
        else:
            require(all(value[k] is None for k in ('mean', 'max', 'quantiles_0_25_50_75_100')), 'Empty diagnostic has values')
        result[key] = deepcopy(value)
    return result


def compact(report, report_sha256):
    """Allowlist aggregates; never copy manifests, root/group rows or truth."""
    validate(report); sha(report_sha256)
    require(report['version'] == SOURCE_VERSION, 'Compact from the original strict report, not an existing summary')
    result = keep(report, ('method', 'stage', 'status', 'verification_errors', 'candidate', 'decision_counts',
                          'configurations', 'selected', 'tracks', 'mechanism', 'limitations', 'code_commit',
                          'ledger_sha256', 'source', 'development_truth_sha256', 'development_schedule_sha256',
                          'train_group_sha256', 'development_group_sha256', 'replayed_epoch_plans', 'resources', 'artifacts'))
    result.update(version=VERSION, source_report_version=SOURCE_VERSION, source_report_sha256=report_sha256,
                  public_scope='Aggregate-only derivative of strict report; no dataset, checkpoint, raw root/group records or labels.',
                  validation_scope='Schema/arithmetic checks here do not replace the original strict artifact and independent audits.')
    result['data_provenance'] = {name: keep(report[name+'_manifest'],
        ('version', 'method', 'role', 'split', 'fraction', 'label_seed', 'dataset_fingerprint',
         'parent_dataset_fingerprint', 'root_count', 'node_count', 'fork_count')) for name in ('train', 'development')}
    for manifest in result['data_provenance'].values():
        for key, value in manifest.items():
            if key.endswith('fingerprint'): sha(value)
            elif key in ('fraction', 'label_seed', 'root_count', 'node_count', 'fork_count'): number(value)
            else: require(isinstance(value, str), 'Invalid public data provenance')
    metric_keys = ('scheduled', 'complete', 'censored_or_error', 'mean_regret', 'optimal_rate',
                   'median_seconds', 'p95_seconds', 'transitions', 'neural_leaves')
    def metrics(obj):
        require(set(obj) == set(GAMES), 'Missing aggregate games')
        result = {}
        for game, tracks in obj.items():
            require(bool(tracks) and set(tracks) <= set(TRACKS), 'Unknown aggregate tracks')
            result[game] = {}
            for track, value in tracks.items():
                keys(value, metric_keys)
                for key, item in value.items():
                    number(item)
                    if key in ('scheduled', 'complete', 'censored_or_error', 'transitions', 'neural_leaves'):
                        require(type(item) is int, 'Invalid aggregate count')
                result[game][track] = keep(value, metric_keys)
        return result
    require(set(report['baselines']) == {'zero', 'untrained-17', 'untrained-29', 'untrained-43'}, 'Missing control aggregates')
    result['baselines'] = {name: metrics(rows) for name, rows in report['baselines'].items()}
    result['runs'] = []
    for source in report['runs']:
        row = keep(source, ('config', 'status', 'checkpoint_sha256', 'collapse', 'seconds', 'parameters'))
        row['metrics'] = metrics(source['metrics'])
        row['representation'] = {g: occurrence(source['representation'][g]) for g in GAMES}
        original = source['diagnostics']
        keys(original, ('stage', 'weighting', 'head_norm', 'collapse', 'games'))
        require(original['stage'] == 'development' and isinstance(original['weighting'], str)
                and original['collapse'] is False, 'Invalid diagnostic scope')
        number(original['head_norm'])
        row['diagnostics'] = keep(original, ('stage', 'weighting', 'head_norm', 'collapse'))
        row['diagnostics']['games'] = {}
        for game in GAMES:
            value = original['games'][game]
            keys(value, ('unique_node_geometry', 'collapse', 'group_count', 'false_pessimistic_count', 'groups', 'summary'))
            require(value['collapse'] is False and type(value['group_count']) is int and value['group_count'] > 0,
                    'Invalid diagnostic group inventory')
            require(value['false_pessimistic_count'] is None or type(value['false_pessimistic_count']) is int
                    and 0 <= value['false_pessimistic_count'] <= value['group_count'], 'Invalid false-pessimistic count')
            summaries = diagnostic_summary(value['summary'])
            row['diagnostics']['games'][game] = {
                'unique_node_geometry': geometry(value['unique_node_geometry']),
                **keep(value, ('collapse', 'group_count', 'false_pessimistic_count')), 'summary': summaries}
        result['runs'].append(row)
    # Fail if a future schema accidentally reintroduces record-level contents.
    forbidden = {'root_id', 'trajectory', 'node_ids', 'source_id', 'h1_id', 'h2_ids', 'fork_indices',
                 'oracle_values', 'action_estimates', 'board', 'state', 'roots', 'groups', 'scores', 'selected_root_ids'}
    def check(value):
        if isinstance(value, dict):
            require(not (set(value) & forbidden), 'Record-level fields found in public derivative')
            for child in value.values(): check(child)
        elif isinstance(value, list):
            for child in value: check(child)
    check(result)
    validate(result)
    json.dumps(result, allow_nan=False)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report'); parser.add_argument('output')
    args = parser.parse_args()
    report, report_sha = read(args.report)
    result = compact(report, report_sha)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output': str(output.resolve()), 'status': result['status'], 'cells': len(result['runs']),
                      'source_report_sha256': report_sha}))


if __name__ == '__main__': main()
