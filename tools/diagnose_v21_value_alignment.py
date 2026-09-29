"""Read-only checkpoint diagnostics for every globally selected grid02 family.

Only standalone v2.2 FULL training and development exports are accepted; the
parent dataset file is never opened. No fitting, search, new oracle queries, or
selection/final loading occurs. Train
metrics describe fit; development metrics reuse an adaptively exposed split.
H1 deduplicates the same root/action repeated across replies; H2 counts complete
fork paths. Equal-root and transition-weighted summaries are both descriptive:
forks, shared model seeds, and state occurrences are not independent replicates.
No inferential confidence interval is computed. Raw latent scales are not
comparable across models. Root-level error/regret correlations are observational,
not causal evidence that representation error produced a planning mistake.
Terminal overrides mean terminal latent/value errors do not enter saved search
decisions. All/terminal/nonterminal strata are specified here for every model.

Run only after active training finishes. Set OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1
before starting Python. Output is a new JSON artifact; all inputs remain intact.
"""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VERSION = 'grid02-value-alignment-v1'
METRICS = ('encoded_oracle_mse', 'predicted_oracle_mse',
           'predicted_encoded_value_mse', 'raw_online_latent_mse')
SEEDS = (17, 29, 43)
GAMES = ('connect4-4x5', 'reversi6')
FAMILIES = ('direct', 'value-dynamics', 'decoded', 'rjepa', 'raw-jepa', 'no-response')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def empty():
    return {'count': 0, 'sums': {}}


def add(accumulator, values):
    accumulator['count'] += 1
    for key, value in values.items():
        accumulator['sums'][key] = accumulator['sums'].get(key, 0.) + float(value)


def finish(accumulator):
    count = accumulator['count']
    return {'count': count, **{k: accumulator['sums'][k] / count
                              if count and k in accumulator['sums'] else None for k in METRICS}}


def load_inventory(grid, report_path, dataset_fingerprint):
    """Recompute global tuning from all frozen receipts, before loading models."""
    from two_player.data import digest
    from two_player_v2.model import Config
    ledger, report = read(grid / 'ledger.json'), read(report_path)
    require(ledger.get('status') == 'complete' and not ledger['failures'], 'Grid is incomplete')
    require(report['verification_errors'] == [], 'Input report failed verification')
    require(report['ledger_sha256'] == sha(grid / 'ledger.json'), 'Report ledger hash mismatch')
    require(ledger['dataset_fingerprint'] == dataset_fingerprint == report['dataset_fingerprint'], 'Dataset mismatch')
    require(ledger['selection_predictions'] == ledger['final_predictions'] == 0, 'Protected predictions present')
    for name, expected in ledger['source'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), 'Source path escapes repository')
        require(hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected, 'Frozen source changed: ' + name)
    expected_cells = {(v, lr, weight, seed) for v in FAMILIES for lr in (.001, .0003)
                      for weight in ((1.,) if v in ('direct', 'value-dynamics') else (.1, 1.)) for seed in SEEDS}
    receipts, groups, cells = {}, defaultdict(list), set()
    for item in ledger['runs']:
        c = item['config']
        key = (c['variant'], c['learning_rate'], c['jepa_weight'], c['seed'])
        require(key not in cells and item['status'] == 'complete', 'Missing/duplicate cell')
        cells.add(key)
        require(item['id'] == f'{key[0]}-lr{key[1]:g}-w{key[2]:g}-s{key[3]}', 'Unexpected run identifier')
        path = grid / item['id']
        require(sha(path / 'receipt.json') == item['receipt_sha256'], 'Receipt checksum changed')
        receipt = read(path / 'receipt.json')
        require(receipt['config'] == c, 'Receipt config mismatch')
        config = Config(**c)
        require(asdict(config) == asdict(Config(variant=key[0], learning_rate=key[1], jepa_weight=key[2], seed=key[3])), 'Unfrozen model configuration')
        require(receipt['identity']['source'] == ledger['source'] and receipt['identity']['data'] == dataset_fingerprint
                and receipt['identity']['config_sha256'] == digest(c), 'Checkpoint identity mismatch')
        require(sha(path / 'checkpoint.npz') == item['checkpoint_sha256'] == receipt['checkpoint_sha256'], 'Checkpoint checksum changed')
        require(all(row['status'] == 'complete' and row['split'] == 'development' for row in receipt['scores']), 'Incomplete/nondevelopment decisions')
        per_game = []
        for game in GAMES:
            rows = [r for r in receipt['scores'] if r['game'] == game and r['track'] == 'exact']
            require(bool(rows), 'Missing game decisions')
            per_game.append(sum(r['regret'] for r in rows) / len(rows))
        groups[key[:3]].append(sum(per_game) / len(GAMES))
        receipts[key] = (item, receipt)
    require(cells == expected_cells and len(ledger['runs']) == 60, 'Expected exactly 60 frozen cells')
    selected = {}
    for family in FAMILIES:
        options = [(sum(values) / 3, key) for key, values in groups.items() if key[0] == family]
        require(all(len(values) == 3 for key, values in groups.items() if key[0] == family), 'Incomplete seed cohort')
        best = min(value for value, _ in options)
        chosen = min((key for value, key in options if abs(value - best) <= 1e-12), key=lambda k: (k[1], k[2]))
        declared = report['promotion']['selected'][family]
        require(chosen[1:] == (declared['learning_rate'], declared['jepa_weight']), 'Global tuning differs from frozen report')
        selected[family] = chosen
    return ledger, receipts, selected


def diagnostic(model, dataset, saved, batch_size, deadline):
    import numpy as np
    from two_player_v2.data import batch_arrays
    roots = {r['root_id']: r for r in dataset['roots']}
    raw_counts = defaultdict(lambda: {'fork_records': 0, 'missing_h2_forks': 0})
    for fork in dataset['forks']:
        raw_counts[fork['root_id']]['fork_records'] += 1
        raw_counts[fork['root_id']]['missing_h2_forks'] += fork['node_ids'][2] is None
    accumulators = {rid: {str(h): {s: empty() for s in ('all', 'nonterminal', 'terminal')}
                         for h in (1, 2)} for rid in roots}
    direct = model.config.variant == 'direct'
    for horizon in (1, 2):
        seen, indices = set(), []
        for i, fork in enumerate(dataset['forks']):
            key = (fork['root_id'], *fork['actions'][:horizon])
            if fork['node_ids'][horizon] is not None and key not in seen:
                seen.add(key)
                indices.append(i)
        for begin in range(0, len(indices), batch_size):
            if time.perf_counter() >= deadline:
                raise TimeoutError('Diagnostic time budget exceeded')
            chosen = indices[begin:begin + batch_size]
            batch = batch_arrays(dataset, chosen)
            actual_z = model.encode(batch['x'][:, horizon])
            actual_value = model.value(actual_z)
            target = batch['value'][:, horizon]
            measurements = {'encoded_oracle_mse': ((actual_value - target)**2).ravel()}
            if not direct:
                predicted_z = model.rollout(model.encode(batch['x'][:, 0]), batch['actions'], horizon=horizon)
                predicted_value = model.value(predicted_z)
                measurements.update(predicted_oracle_mse=((predicted_value - target)**2).ravel(),
                                    predicted_encoded_value_mse=((predicted_value - actual_value)**2).ravel(),
                                    raw_online_latent_mse=np.mean((predicted_z - actual_z)**2, axis=1))
            require(all(np.isfinite(v).all() for v in measurements.values()), 'Nonfinite diagnostic value')
            for j, index in enumerate(chosen):
                fork = dataset['forks'][index]
                node = dataset['nodes'][fork['node_ids'][horizon]]
                values = {key: value[j] for key, value in measurements.items()}
                group = accumulators[fork['root_id']][str(horizon)]
                add(group['all'], values)
                add(group['terminal' if node['terminal'] else 'nonterminal'], values)
    rows = []
    for rid, root in roots.items():
        decision = saved.get((root['game'], rid)) if saved is not None else None
        rows.append({'game': root['game'], 'root_id': rid, 'trajectory': root['trajectory'],
                     **raw_counts[rid], 'horizons': {h: {s: finish(a) for s, a in strata.items()}
                                                   for h, strata in accumulators[rid].items()},
                     'saved_planning': decision})
    summaries = {}
    for game in GAMES:
        game_rows = [r for r in rows if r['game'] == game]
        groups = {}
        for horizon in ('1', '2'):
            groups[horizon] = {}
            for stratum in ('all', 'nonterminal', 'terminal'):
                values = [r['horizons'][horizon][stratum] for r in game_rows]
                nonempty = [v for v in values if v['count']]
                counts = sum(v['count'] for v in values)
                weighted, root_mean = {}, {}
                for key in METRICS:
                    measured = [v for v in nonempty if v[key] is not None]
                    weighted[key] = sum(v[key]*v['count'] for v in measured)/sum(v['count'] for v in measured) if measured else None
                    root_mean[key] = sum(v[key] for v in measured)/len(measured) if measured else None
                groups[horizon][stratum] = {'root_count': len(game_rows), 'roots_with_targets': len(nonempty),
                                           'transition_targets': counts, 'transition_weighted': weighted, 'equal_root': root_mean}
        relationship = {'available': saved is not None, 'reason': 'Saved development decisions only; train search was not rerun',
                        'root_count': 0, 'pearson_h2_nonterminal_error_gap_vs_regret_gap': None}
        if saved is not None and not direct:
            pairs = [(r['horizons']['2']['nonterminal']['predicted_oracle_mse'] - r['horizons']['2']['nonterminal']['encoded_oracle_mse'],
                      r['saved_planning']['hybrid_minus_exact_regret']) for r in game_rows
                     if r['horizons']['2']['nonterminal']['count']]
            relationship['root_count'] = len(pairs)
            array = np.asarray(pairs)
            if len(pairs) > 1 and np.std(array[:, 0]) > 0 and np.std(array[:, 1]) > 0:
                relationship['pearson_h2_nonterminal_error_gap_vs_regret_gap'] = float(np.corrcoef(array.T)[0, 1])
        summaries[game] = {'roots': len(game_rows), 'horizons': groups, 'saved_planning_relationship': relationship}
    return {'dynamics_metrics_available': not direct,
            'dynamics_limitation': 'Direct has no trained predictor; unused random dynamics are not scored' if direct else None,
            'games': summaries, 'per_root': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid', type=Path)
    parser.add_argument('full_training', type=Path, help='Standalone v2.2 full-label training artifact')
    parser.add_argument('development', type=Path, help='Standalone v2.2 development artifact')
    parser.add_argument('verified_report', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--max-seconds', type=float, default=300.)
    args = parser.parse_args()
    require(os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1', 'Set BLAS/OMP threads to 1 before Python startup')
    require(args.batch_size > 0 and 0 < args.max_seconds <= 600, 'Invalid bounded diagnostic configuration')
    require(not args.output.exists(), 'Output already exists; preserve previous diagnostics')
    import numpy as np
    from two_player.data import digest
    from two_player_v22.data import load_dataset
    from two_player_v2.model import Model, Config
    started = time.perf_counter()
    directories = {'train': args.full_training, 'development': args.development}
    datasets = {split: load_dataset(directory, split) for split, directory in directories.items()}
    fingerprint = datasets['train']['manifest']['parent_dataset_fingerprint']
    for split, dataset in datasets.items():
        manifest = dataset['manifest']
        require(manifest['fraction'] == 1. and manifest['parent_dataset_fingerprint'] == fingerprint,
                'Expected full-label standalone artifacts from the same historical parent')
        require(all(node['value_labelled'] and node['policy_labelled'] == (not node['terminal'])
                    for node in dataset['nodes'].values()), 'Diagnostic targets must be fully labelled')
    ledger, receipts, selected = load_inventory(args.grid, args.verified_report, fingerprint)
    development = datasets['development']['roots']
    schedule = [(r['game'], r['root_id'], r['trajectory']) for r in development]
    require(digest(schedule) == ledger['development_schedule_sha256'], 'Development schedule changed')
    result = {'version': VERSION, 'stage': 'post-hoc development diagnostic',
              'script_sha256': sha(__file__), 'source': ledger['source'], 'source_commit': ledger['code_commit'],
              'ledger_sha256': sha(args.grid / 'ledger.json'), 'verified_report_sha256': sha(args.verified_report),
              'historical_parent_dataset_fingerprint': fingerprint,
              'standalone_datasets': {split: {'directory': str(directory.resolve()),
                  'dataset_fingerprint': datasets[split]['manifest']['dataset_fingerprint'],
                  'parent_dataset_fingerprint': datasets[split]['manifest']['parent_dataset_fingerprint'],
                  'manifest_sha256': sha(directory / 'manifest.json'), 'payload_sha256': sha(directory / 'data.json'),
                  'source_identity': datasets[split]['manifest']['source_identity']}
                  for split, directory in directories.items()},
              'global_configurations': selected, 'batch_size': args.batch_size,
              'selection_predictions': 0, 'final_predictions': 0, 'new_search_decisions': 0,
              'limitations': __doc__, 'runs': []}
    for family in FAMILIES:
        for seed in SEEDS:
            item, receipt = receipts[(*selected[family], seed)]
            expected = [(g, rid, trajectory, track) for g, rid, trajectory in schedule for track in ('exact', 'hybrid')]
            require([(r['game'], r['root_id'], r['trajectory'], r['track']) for r in receipt['scores']] == expected, 'Saved root/track schedule differs')
            by_key = {(r['game'], r['root_id'], r['track']): r for r in receipt['scores']}
            saved = {}
            for root in development:
                pair = {track: by_key[root['game'], root['root_id'], track] for track in ('exact', 'hybrid')}
                for row in pair.values():
                    require(row['action'] in root['actions'], 'Saved illegal action')
                    regret = max(root['oracle_values']) - root['oracle_values'][root['actions'].index(row['action'])]
                    require(regret == row['regret'] and row['nodes'] <= 4096 and row['seconds'] < 1., 'Saved utility or budget mismatch')
                saved[root['game'], root['root_id']] = {**{t + '_regret': pair[t]['regret'] for t in pair},
                    'hybrid_minus_exact_regret': pair['hybrid']['regret'] - pair['exact']['regret']}
            config = Config(**receipt['config'])
            model = Model.load(args.grid / item['id'] / 'checkpoint.npz', config, receipt['identity'])
            row = {'run_id': item['id'], 'config': receipt['config'], 'seed': seed,
                   'checkpoint_sha256': receipt['checkpoint_sha256'], 'receipt_sha256': item['receipt_sha256'],
                   'identity': receipt['identity'], 'splits': {}}
            for split, dataset in datasets.items():
                row['splits'][split] = diagnostic(model, dataset, saved if split == 'development' else None,
                                                 args.batch_size, started + args.max_seconds)
            result['runs'].append(row)
    result['seconds'] = time.perf_counter() - started
    require(np.isfinite(result['seconds']) and result['seconds'] < args.max_seconds, 'Diagnostic exceeded budget')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({'output': str(args.output.resolve()), 'runs': len(result['runs']), 'seconds': result['seconds']}))


if __name__ == '__main__':
    main()
