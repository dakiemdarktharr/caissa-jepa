"""Verify frozen training-only artifacts; never fit, predict or select a model."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import statistics

from . import METHOD_VERSION
from .runtime import (runtime_source, configurations, run_id, tensor_hashes,
                      ROOT, REFERENCE_PATH, DATA_FINGERPRINT, SNAPSHOTS,
                      FAMILIES, CAPACITIES, SEEDS)
from two_player_v22.model import Model, Config, OBJECTIVE_VERSION

GAMES = ('connect4-4x5', 'reversi6')
ROOT_COUNTS = dict(zip(GAMES, (248, 261)))
TARGET_COUNTS = {
    'connect4-4x5': {'1': {'all': (248, 876), 'nonterminal': (248, 804), 'terminal': (71, 72)},
                    '2': {'all': (248, 2674), 'nonterminal': (248, 2425), 'terminal': (111, 249)}},
    'reversi6': {'1': {'all': (261, 1180), 'nonterminal': (261, 1180), 'terminal': (0, 0)},
                '2': {'all': (261, 4004), 'nonterminal': (261, 4003), 'terminal': (1, 1)}}}
METRICS = ('encoded_oracle_mse', 'predicted_oracle_mse',
           'predicted_encoded_value_mse', 'raw_online_latent_mse')
COMMON_COUNTS = ('encoded_count', 'policy_count', 'value_count',
                 'value_unlabelled_count', 'policy_unlabelled_count', 'terminal_count',
                 'h1_eligible_count', 'h2_eligible_count', 'h1_missing_count',
                 'h2_missing_count', 'h1_unlabelled_count', 'h2_unlabelled_count')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def finite(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Nonfinite/nonnumeric measurement')
    return value


def close(a, b):
    return math.isclose(finite(a), finite(b), rel_tol=1e-10, abs_tol=1e-12)


def hash_string(value):
    require(isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdef' for c in value), 'Malformed SHA-256')


def local_path(root, name):
    require(isinstance(name, str) and Path(name).name == name, 'Artifact path must be a local basename')
    result = (root/name).resolve()
    require(result.parent == root.resolve(), 'Artifact path escapes cell')
    return result


def validate_history(history, config):
    require(len(history) == 160, 'Expected 160 epoch receipts')
    paired = []
    for epoch, row in enumerate(history, 1):
        require((row['epoch'], row['step'], row['steps']) == (epoch, 66*epoch, 66), 'Epoch/update counters mismatch')
        require(0 <= finite(row['seconds']) <= 300, 'Invalid epoch duration')
        schedule, aug, counts = row['schedule'], row['augmentation'], row['label_and_target_count_totals']
        require(schedule['samples'] == 8352 and 0 < schedule['unique_forks'] <= 6750
                and set(schedule['games']) == set(GAMES), 'Sampling counts differ from protocol')
        for g in GAMES:
            require(schedule['games'][g] == {'unique_roots': ROOT_COUNTS[g], 'root_draws': 261,
                    'repeated_root_draws': 261-ROOT_COUNTS[g], 'fork_draws': 4176}, 'Unbalanced root schedule')
        hash_string(schedule['index_sha256'])
        require(aug['version'] == 'legal-symmetries-v21' and aug['seed'] == config.seed
                and aug['epoch'] == epoch-1 and aug['rng_namespace'] == 2211
                and aug['samples'] == 8352 and aug['index_sha256'] == schedule['index_sha256'], 'Augmentation identity mismatch')
        hash_string(aug['transform_sha256'])
        totals = dict.fromkeys(GAMES, 0)
        for key, n in aug['transform_counts'].items():
            g, t = key.rsplit('/', 1)
            require(g in GAMES and t.isdigit() and str(int(t)) == t
                    and int(t) < (2 if g == GAMES[0] else 8)
                    and type(n) is int and n > 0, 'Illegal augmentation transform count')
            totals[g] += n
        require(all(n == 4176 for n in totals.values()), 'Augmentation game exposure mismatch')
        require(all(type(n) is int and n >= 0 for n in counts.values()), 'Invalid label counts')
        require(counts['h1_eligible_count'] == 8352 and counts['h1_missing_count'] == 0
                and counts['h2_eligible_count']+counts['h2_missing_count'] == 8352
                and counts['encoded_count'] == 16704+counts['h2_eligible_count'], 'Horizon counts mismatch')
        require(counts['value_count'] == counts['encoded_count']
                and counts['policy_count']+counts['terminal_count'] == counts['encoded_count']
                and counts['value_unlabelled_count'] == counts['policy_unlabelled_count'] == 0,
                'Full training label counts mismatch')
        active = config.variant != 'direct'
        for h in (1, 2):
            n = counts[f'h{h}_eligible_count']
            require(counts[f'h{h}_unlabelled_count'] == counts[f'h{h}_ema_value_count'] == 0
                    and counts[f'h{h}_count'] == counts[f'h{h}_value_label_count'] == (n if active else 0)
                    and counts[f'h{h}_latent_count'] == (n if config.variant == 'raw-jepa' else 0),
                    'Objective denominator mismatch')
        for value in row['metrics_sample_weighted'].values():
            finite(value)
        require(0 < row['metrics_sample_weighted']['gradient_scale'] <= 1
                and row['metrics_sample_weighted']['gradient_norm'] >= 0, 'Invalid gradient diagnostics')
        paired.append(digest([schedule, aug, {k: counts[k] for k in COMMON_COUNTS}]))
    return paired


def validate_metrics(obj, config):
    """Recompute summaries from saved root rows without invoking the model."""
    require(obj['counts'] == {'roots': 509, 'forks': 6750, 'unique_raw_nodes': 9237}, 'Diagnostic dataset counts mismatch')
    fit = obj['fit']
    direct = config.variant == 'direct'
    require(fit['dynamics_metrics_available'] is (not direct), 'Untrained direct dynamics were scored')
    require(set(fit['games']) == set(obj['geometry']) == set(obj['S_components']) == set(GAMES), 'Diagnostic game inventory mismatch')
    rows = fit['per_root']
    require(len(rows) == 509 and len({r['root_id'] for r in rows}) == 509, 'Root inventory incomplete/duplicated')
    signature, components, collapsed = [], {}, []
    for row in rows:
        require(row['game'] in GAMES and row['saved_planning'] is None, 'Nontraining planning result in snapshot')
        hash_string(row['root_id'])
        require(type(row['fork_records']) is int and row['fork_records'] > 0
                and type(row['missing_h2_forks']) is int and 0 <= row['missing_h2_forks'] <= row['fork_records'], 'Invalid root fork counts')
        signature.append([row['game'], row['root_id'], row['trajectory'], row['fork_records'], row['missing_h2_forks'],
                          {h: {s: row['horizons'][h][s]['count'] for s in ('all', 'nonterminal', 'terminal')} for h in ('1', '2')}])
        for h in ('1', '2'):
            groups = row['horizons'][h]
            require(groups['all']['count'] == groups['nonterminal']['count']+groups['terminal']['count'], 'Stratum counts do not sum')
            for s, entry in groups.items():
                n = entry['count']
                require(s in ('all', 'nonterminal', 'terminal') and type(n) is int and n >= 0, 'Invalid root stratum')
                for key in METRICS:
                    val = entry[key]
                    if n == 0 or (direct and key != METRICS[0]):
                        require(val is None, 'Absent metric must remain null')
                    else:
                        require(finite(val) >= 0, 'Negative MSE')
                if n:
                    for key in METRICS:
                        if entry[key] is not None:
                            parts = [groups[t] for t in ('nonterminal', 'terminal') if groups[t]['count']]
                            if s == 'all':
                                require(close(entry[key], sum(v[key]*v['count'] for v in parts)/n), 'Root strata do not reconstruct all metric')
            if h == '2':
                require(groups['all']['count']+row['missing_h2_forks'] == row['fork_records'], 'Missing H2 count mismatch')
    require(sum(r['fork_records'] for r in rows) == 6750, 'Fork total mismatch')
    for g in GAMES:
        gr = [r for r in rows if r['game'] == g]
        require(len(gr) == ROOT_COUNTS[g] == fit['games'][g]['roots'], 'Per-game root count mismatch')
        relation = fit['games'][g]['saved_planning_relationship']
        require(relation['available'] is False and relation['root_count'] == 0
                and relation['pearson_h2_nonterminal_error_gap_vs_regret_gap'] is None, 'Planning relationship forbidden')
        components[g] = {}
        for h in ('1', '2'):
            for s in ('all', 'nonterminal', 'terminal'):
                vals = [r['horizons'][h][s] for r in gr if r['horizons'][h][s]['count']]
                count = sum(v['count'] for v in vals)
                summary = fit['games'][g]['horizons'][h][s]
                require((summary['root_count'], summary['roots_with_targets'], summary['transition_targets']) ==
                        (len(gr), len(vals), count), 'Summary target counts mismatch')
                require((len(vals), count) == TARGET_COUNTS[g][h][s], 'Frozen training stratum counts changed')
                for key in METRICS:
                    expected = bool(vals) and not (direct and key != METRICS[0])
                    er, tw = summary['equal_root'][key], summary['transition_weighted'][key]
                    if expected:
                        require(close(er, statistics.mean(v[key] for v in vals))
                                and close(tw, sum(v[key]*v['count'] for v in vals)/count), 'Root and summary metrics disagree')
                    else:
                        require(er is None and tw is None, 'Absent summary metric must remain null')
            ss = fit['games'][g]['horizons'][h]['nonterminal']
            require(ss['transition_targets'] > 0, 'Unsupported S component')
            component = {'encoded_oracle_mse': ss['equal_root'][METRICS[0]],
                         **{k: ss[k] for k in ('root_count', 'roots_with_targets', 'transition_targets')}}
            require(component == obj['S_components'][g][h], 'S component differs from saved fit')
            components[g][h] = component['encoded_oracle_mse']
        geo = obj['geometry'][g]
        require((geo['samples'], geo['terminal_nodes'], geo['nonterminal_nodes']) ==
                ((3792, 321, 3471) if g == GAMES[0] else (5445, 1, 5444)), 'Raw-node geometry inventory changed')
        require(type(geo['samples']) is int and geo['samples'] > 0
                and geo['dimensions'] == config.latent and geo['samples'] == geo['terminal_nodes']+geo['nonterminal_nodes']
                and geo['terminal_nodes'] >= 0 and geo['nonterminal_nodes'] > 0, 'Invalid geometry counts')
        require(0 <= finite(geo['effective_rank']) <= config.latent+1e-9
                and 0 <= finite(geo['median_std']) <= 1+1e-9 and 0 <= finite(geo['mean_std']) <= 1+1e-9,
                'Invalid latent geometry')
        require(geo['weighting'] == 'Every unique raw training node once; no canonical-orbit or fork weighting', 'Geometry weighting mismatch')
        if geo['effective_rank'] < 2 or geo['median_std'] < .001:
            collapsed.append({'game': g, 'space': 'unprojected', 'samples': geo['samples'],
                              'effective_rank': geo['effective_rank'], 'median_std': geo['median_std']})
    require(sum(v['samples'] for v in obj['geometry'].values()) == 9237, 'Geometry node inventory mismatch')
    require(obj['collapse'] == collapsed, 'Collapse flag does not match geometry')
    scalar = statistics.mean(components[g][h] for g in GAMES for h in ('1', '2'))
    require(obj['S_component_count'] == 4 and close(obj['S'], scalar), 'S scalar mismatch')
    require(not collapsed, 'A snapshot collapsed; interpretation is inconclusive')
    return scalar, components, digest(sorted(signature))


def decisions(runs):
    lookup = {(r['config']['variant'], r['config']['hidden'], r['config']['latent'], r['config']['seed']): r for r in runs}
    progress, capacity = [], []
    for family in FAMILIES:
        for hidden, latent in CAPACITIES:
            values = []
            details = []
            for seed in SEEDS:
                row = lookup[family, hidden, latent, seed]
                a, b = row['snapshots']['80'], row['snapshots']['160']
                value = (a['S']-b['S'])/max(a['S'], 1e-12)
                values.append(value)
                details.append({'seed': seed, 'r': value, 'per_game_horizon': {
                    g: {h: (a['components'][g][h]-b['components'][g][h])/max(a['components'][g][h], 1e-12)
                        for h in ('1', '2')} for g in GAMES}})
            median = statistics.median(values)
            progress.append({'family': family, 'hidden': hidden, 'latent': latent, 'seeds': details,
                             'median_r': median, 'material_progress': median > .05,
                             'interpretation': 'still making material fit progress' if median > .05 else 'no material improvement under this threshold'})
        details = []
        for seed in SEEDS:
            a = lookup[family, *CAPACITIES[0], seed]['snapshots']['160']
            b = lookup[family, *CAPACITIES[1], seed]['snapshots']['160']
            details.append({'seed': seed, 'c': (a['S']-b['S'])/max(a['S'], 1e-12), 'per_game_horizon': {
                g: {h: (a['components'][g][h]-b['components'][g][h])/max(a['components'][g][h], 1e-12)
                    for h in ('1', '2')} for g in GAMES}})
        median = statistics.median(d['c'] for d in details)
        favorable = sum(d['c'] > 0 for d in details)
        capacity.append({'family': family, 'seeds': details, 'median_c': median, 'favorable_seeds': favorable,
                         'material_capacity_response': median > .05 and favorable >= 2})
    if any(p['material_progress'] for p in progress):
        branch = 'Budget may be limiting; separately freeze a budget decision before another development grid.'
    elif any(c['material_capacity_response'] for c in capacity):
        branch = 'Consider a common larger-capacity comparison with equally strengthened baselines.'
    else:
        branch = 'Examine objectives/state representation rather than automatically extending epochs.'
    return {'progress': progress, 'capacity': capacity, 'branch': branch, 'candidate': None}


def summarize_grid(path):
    root = Path(path).resolve()
    report = {'version': 'v23-training-diagnostic-report01', 'stage': 'training-only diagnostic',
              'input_directory': str(root), 'status': 'inconclusive', 'verification_errors': [],
              'runs': [], 'decisions': None, 'limitations': [
                  'Training fit does not establish generalization, playing strength or JEPA superiority.',
                  'No candidate is promoted; no development, selection or final data is read.',
                  'Capacity changes several components and compute; this is not an isolated encoder intervention.',
                  'A threshold flag is not proof of convergence. No inferential bootstrap is computed.',
                  'Saved diagnostics are checked for integrity and arithmetic, not recomputed model predictions.']}
    try:
        ledger = read(root/'ledger.json')
        report['ledger_sha256'] = sha(root/'ledger.json')
        report['runs'] = [{'id': r.get('id'), 'config': r.get('config'), 'status': r.get('status')} for r in ledger.get('runs', [])]
        require(ledger['version'] == 'v23-training-diagnostic01' and ledger['method'] == METHOD_VERSION
                and ledger['stage'] == report['stage'] and ledger['status'] == 'complete', 'Incomplete or wrong diagnostic ledger')
        require(ledger['failures'] == [] and ledger['resource_limits'] ==
                {'cell_seconds': 300., 'total_cell_seconds': 5400., 'artifact_bytes': 3_000_000_000}
                and ledger['artifact_bytes_scope'] == 'All output files except ledger.json; cap includes ledger.json',
                'Recorded failure or resource accounting protocol mismatch')
        require(ledger['source'] == runtime_source(), 'Frozen source inventory changed')
        require(ledger['epochs'] == 160 and ledger['snapshots'] == list(SNAPSHOTS), 'Unfrozen training schedule')
        for k in ('development_predictions', 'selection_predictions', 'final_predictions', 'new_search_decisions'):
            require(ledger[k] == 0, 'Protected evaluation or planning detected')
        require(ledger['dataset_fingerprint'] == DATA_FINGERPRINT, 'Unfrozen dataset')
        manifest = ledger['dataset_manifest']
        require(digest({k: v for k, v in manifest.items() if k not in ('code_commit', 'dataset_fingerprint')}) == DATA_FINGERPRINT
                and manifest['dataset_fingerprint'] == DATA_FINGERPRINT
                and manifest['split'] == 'train' and manifest['role'] == 'redacted-training'
                and manifest['fraction'] == 1 and manifest['label_seed'] == 271828
                and (manifest['root_count'], manifest['node_count'], manifest['fork_count']) == (509, 9237, 6750)
                and manifest['audit']['status'] == 'PASSED' and not manifest['audit']['errors'], 'Training manifest mismatch')
        require(isinstance(ledger['code_commit'], str) and len(ledger['code_commit']) == 40, 'Missing code commit')
        reference = read(ROOT/REFERENCE_PATH)
        require(reference['dataset_fingerprint'] == DATA_FINGERPRINT and len(reference['rows']) == 9, 'Reference inventory mismatch')
        refs = {(r['variant'], r['seed']): r for r in reference['rows']}
        require(set(refs) == {(v, s) for v in FAMILIES for s in SEEDS}, 'Reference cells missing/duplicated')
        expected = {run_id(c): c for c in configurations()}
        require(len(ledger['runs']) == 18 and {r['id'] for r in ledger['runs']} == set(expected), 'Expected exactly 18 distinct cells')
        rows, pairs, inventory, environments = [], {}, None, set()
        seconds = 0.
        for item in ledger['runs']:
            config = expected[item['id']]
            require(item['config'] == asdict(config) and item['status'] == 'complete', 'Cell configuration/status mismatch')
            cell = root/item['id']
            receipt = read(cell/'receipt.json')
            require(sha(cell/'receipt.json') == item['receipt_sha256'] and receipt['config'] == item['config'], 'Receipt checksum/config mismatch')
            identity = receipt['identity']
            require(identity['source'] == ledger['source'] and identity['data'] == DATA_FINGERPRINT
                    and identity['config_sha256'] == digest(asdict(config)) and identity['method'] == METHOD_VERSION
                    and identity['objective'] == OBJECTIVE_VERSION and identity['epochs'] == 160 and identity['draws'] == 16,
                    'Cell identity mismatch')
            environments.add((identity['python'], identity['numpy']))
            budget = read(cell/'budget.json')
            duration = finite(receipt['seconds'])
            outer_duration = finite(item['seconds'])
            require(0 < duration <= outer_duration <= 300
                    and budget['status'] == 'complete' and budget['identity'] == identity
                    and budget['limit_seconds'] == 300 and close(budget['total_seconds'], duration), 'Active/failed/overrun or inconsistent cell budget')
            seconds += outer_duration
            require(sha(cell/'history.json') == receipt['history_sha256'], 'History checksum mismatch')
            history = read(cell/'history.json')
            pairing = validate_history(history, config)
            require(sum(h['seconds'] for h in history) <= duration+1e-6, 'Epoch times exceed cell work')
            if config.seed in pairs:
                require(pairing == pairs[config.seed], 'Unpaired sampler/augmentation/common labels')
            pairs[config.seed] = pairing
            require([s['epoch'] for s in receipt['snapshots']] == list(SNAPSHOTS), 'Snapshot inventory/order mismatch')
            snapshots = {}
            for snap in receipt['snapshots']:
                epoch = snap['epoch']
                require(snap['step'] == epoch*66 and snap['checkpoint'] == f'checkpoint-e{epoch:03d}.npz'
                        and snap['metrics'] == f'snapshot-e{epoch:03d}.json', 'Snapshot path/counter mismatch')
                checkpoint, metrics_path = local_path(cell, snap['checkpoint']), local_path(cell, snap['metrics'])
                require(sha(checkpoint) == snap['checkpoint_sha256'] and sha(metrics_path) == snap['metrics_sha256'], 'Snapshot checksum mismatch')
                model = Model.load(checkpoint, config, identity)
                require((model.epoch, model.step) == (epoch, epoch*66)
                        and model.parameter_counts() == receipt['parameters'], 'Checkpoint counters/parameters mismatch')
                if epoch == 0:
                    require(tensor_hashes(model) == tensor_hashes(Model(config)), 'Initialization differs from seed')
                small40 = (config.hidden, config.latent) == CAPACITIES[0] and epoch == 40
                require(snap['reference_match'] == ('verified' if small40 else 'not_applicable'), 'Incorrect replay-reference status')
                if small40:
                    ref = refs[config.variant, config.seed]
                    require(ref['config'] == asdict(config) and (ref['epoch'], ref['step']) == (40, 2640)
                            and ref['array_hashes'] == tensor_hashes(model), 'Epoch40 does not bitwise replay Grid03 FULL')
                metrics = read(metrics_path)
                for g in GAMES:
                    require({r['root_id'] for r in metrics['fit']['per_root'] if r['game'] == g}
                            == set(manifest['selected_root_ids'][g]), 'Snapshot roots differ from full training manifest')
                scalar, components, sig = validate_metrics(metrics, config)
                require(close(snap['S'], scalar) and snap['collapse'] == metrics['collapse'], 'Snapshot S/collapse receipt mismatch')
                if inventory is not None:
                    require(sig == inventory, 'Snapshot root/target schedule changed')
                inventory = sig
                snapshots[str(epoch)] = {'S': scalar, 'components': components, 'geometry': metrics['geometry'],
                    'checkpoint_sha256': snap['checkpoint_sha256'], 'metrics_sha256': snap['metrics_sha256'],
                    'reference_match': snap['reference_match']}
            rows.append({'id': item['id'], 'config': asdict(config), 'status': 'complete', 'seconds': outer_duration,
                         'receipt_seconds': duration,
                         'receipt_sha256': item['receipt_sha256'], 'snapshots': snapshots})
        require(len(environments) == 1, 'Mixed training environments')
        require(close(seconds, ledger['total_cell_seconds']) and seconds <= 5400, 'Cumulative budget mismatch/overrun')
        actual_bytes = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
        require(type(ledger['artifact_bytes']) is int and 0 <= ledger['artifact_bytes'] <= 3_000_000_000
                and ledger['artifact_bytes'] == actual_bytes-(root/'ledger.json').stat().st_size
                and actual_bytes <= 3_000_000_000, 'Artifact storage accounting mismatch/cap exceeded')
        require(0 <= finite(ledger['preparation_seconds']), 'Invalid preparation duration')
        report.update(status='verified_diagnostic', runs=rows, decisions=decisions(rows),
                      total_cell_seconds=seconds, actual_artifact_bytes=actual_bytes,
                      ledger_artifact_bytes=ledger['artifact_bytes'], code_commit=ledger['code_commit'],
                      dataset_fingerprint=DATA_FINGERPRINT, source=ledger['source'], root_schedule_sha256=inventory,
                      process_peak_rss_bytes=ledger.get('process_peak_rss_bytes'))
    except (ValueError, KeyError, TypeError, OSError, IndexError, ZeroDivisionError) as error:
        report['verification_errors'].append(str(error))
    return report


def markdown(report):
    lines = ['# V2.3 training-only diagnostic', '', f'Status: **{report["status"]}**.', '',
             'No candidate promotion or generalization claim is permitted.', '']
    if report['verification_errors']:
        lines += ['Verification errors:', '', *['- '+s for s in report['verification_errors']], '']
    if report['decisions']:
        lines += ['| Cell | S0 | S40 | S80 | S160 | Seconds |', '| --- | ---: | ---: | ---: | ---: | ---: |']
        for row in report['runs']:
            lines.append('| '+row['id']+' | '+' | '.join(f'{row["snapshots"][str(e)]["S"]:.6f}' for e in SNAPSHOTS)+f' | {row["seconds"]:.3f} |')
        lines += ['', '| Family / capacity | Median relative improvement 80→160 | Interpretation |', '| --- | ---: | --- |']
        for row in report['decisions']['progress']:
            lines.append(f'| {row["family"]} {row["hidden"]}/{row["latent"]} | {row["median_r"]:.6f} | {row["interpretation"]} |')
        lines += ['', '| Family | Median relative capacity improvement | Favorable seeds | Material response |', '| --- | ---: | ---: | --- |']
        for row in report['decisions']['capacity']:
            lines.append(f'| {row["family"]} | {row["median_c"]:.6f} | {row["favorable_seeds"]}/3 | {row["material_capacity_response"]} |')
        lines += ['', report['decisions']['branch'], '', 'All per-seed and per-game/horizon effects are retained in report.json.', '']
    lines += ['- '+s for s in report['limitations']]
    return '\n'.join(lines)+'\n'


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), 'Report output must be a new directory')
    require(not args.output.resolve().is_relative_to(args.grid.resolve()), 'Report output must be outside grid artifacts')
    result = summarize_grid(args.grid)
    args.output.mkdir(parents=True)
    (args.output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    (args.output/'report.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'output': str(args.output.resolve()), 'errors': result['verification_errors']}))


if __name__ == '__main__':
    main()
