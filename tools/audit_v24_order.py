"""Independent saved-artifact/packing audit; never encode, predict, fit or search.

Rebuilds H1 edges and deterministic outcome-blind packing from the standalone
full-label training payload. Reads checkpoint arrays only for integrity checks.
Reported lower bounds/SSEs are checked arithmetically, not remeasured; this is an
internal reproducibility audit sharing the audited game rules, not an external
rules or model replication. Accepts no development/selection/final input.
"""
import argparse
from dataclasses import asdict
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
COMMIT = '0a7edef6bf5a651c37ca4c23186dbbf472ea2b26'
GRID_COMMIT = '20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37'
FP = '73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'
AUDIT_SHA = 'e5f7d6df255699ea0f5684f215546f72dd48368f70e6c4c2ad1c478199ce8ced'
GAMES = ('connect4-4x5', 'reversi6')
SEEDS = (17, 29, 43)
CAPACITIES = ((64, 32), (128, 64))
FAMILIES = ('direct', 'value-dynamics', 'raw-jepa')


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rebuild_packing(train, guard):
    """Enumerate real legal own-action transitions, then pack identity hashes.

    Candidate priority and edge-disjoint selection depend only on game, root IDs,
    player and actions. Labels and terminal flags are carried only as metadata.
    Neither the production packing function nor a model is called.
    """
    from two_player.games import State
    from two_player_v2 import GAMES_V2
    roots = {r['root_id']: r for r in train['roots']}
    require(len(roots) == 509 and len(train['nodes']) == 9237 and len(train['forks']) == 6750, 'Wrong train inventory')
    actual_forks = {}
    for fork in train['forks']:
        require(fork['split'] == 'train', 'Foreign fork split')
        key = fork['root_id'], fork['actions'][0]
        pair = tuple(fork['node_ids'][:2])
        require(key not in actual_forks or actual_forks[key] == pair, 'H1 target differs between replies')
        actual_forks[key] = pair
    observed_keys = set()
    rebuilt = {'version': 'v24-order-schedule01', 'edge_order': ['s1a', 's2a', 's1b', 's2b'], 'games': {}}
    for name in GAMES:
        game = GAMES_V2[name]
        edges, actions, players = [], {}, {}
        for rid, root in sorted(roots.items()):
            if root['game'] != name: continue
            guard()
            require(root['split'] == 'train' and rid == digest([name, root['trajectory'], root['state']]), 'Foreign/rekeyed root identity')
            state = State(tuple(root['state']['board']), root['state']['player'])
            sid = digest([name, asdict(state)])
            legal = list(game.legal_actions(state))
            require(legal == root['actions'], 'Root legal actions changed')
            actions[rid], players[rid] = legal, state.player
            for action in legal:
                target = game.transition(state, action); tid = digest([name, asdict(target)])
                node = train['nodes'][tid]; outcome = game.terminal(target)
                require(actual_forks[rid, action] == (sid, tid), 'Actual legal edge differs from recorded H1')
                require(node['terminal'] is (outcome is not None) and target.player == -state.player, 'Terminal/turn mismatch')
                if outcome is not None: require(node['value'] == outcome*target.player, 'Terminal perspective mismatch')
                observed_keys.add((rid, action))
                edges.append({'root_id': rid, 'player': state.player, 'action': action, 'source_id': sid,
                              'target_id': tid, 'target_player': target.player, 'target_value': node['value'],
                              'target_terminal': outcome is not None})
        edges.sort(key=lambda e: (e['root_id'], e['action']))
        index = {(e['root_id'], e['action']): n for n, e in enumerate(edges)}
        candidates, eligible = [], 0
        for r1, r2 in combinations(sorted(actions), 2):
            if players[r1] != players[r2]: continue
            common = sorted(set(actions[r1]).intersection(actions[r2]))
            if len(common) < 2: continue
            eligible += 1
            for a, b in combinations(common, 2):
                identity = [2401, name, r1, r2, a, b]
                candidates.append((digest(identity), tuple(identity)))
            if eligible % 128 == 0: guard()
        guard(); candidates.sort(); guard()
        used, blocks = set(), []
        histogram = {str(i): 0 for i in range(5)}
        for checksum, identity in candidates:
            _, _, r1, r2, a, b = identity
            ids = [index[r1, a], index[r2, a], index[r1, b], index[r2, b]]
            if not used.isdisjoint(ids): continue
            used.update(ids)
            terminals = sum(edges[i]['target_terminal'] for i in ids)
            histogram[str(terminals)] += 1
            blocks.append({'identity': list(identity), 'sha256': checksum, 'edges': ids, 'terminal_count': terminals})
        nt = sum(not e['target_terminal'] for e in edges)
        counts = {'roots': len(actions), 'eligible_root_pairs': eligible, 'candidate_blocks': len(candidates),
                  'selected_blocks': len(blocks), 'total_h1_edges': len(edges), 'used_edges': len(used),
                  'used_fraction': len(used)/len(edges), 'terminal_block_counts': histogram,
                  'nonterminal_blocks': histogram['0'], 'all_nonterminal_edges': nt,
                  'used_nonterminal_edges': 4*histogram['0'],
                  'nonterminal_used_fraction': 4*histogram['0']/nt if nt else None}
        rebuilt['games'][name] = {'edges': edges, 'blocks': blocks, 'counts': counts,
                                  'edge_sha256': digest(edges), 'block_sha256': digest(blocks)}
    require(observed_keys == set(actual_forks), 'Unused or missing H1 edge')
    rebuilt['schedule_sha256'] = digest(rebuilt)
    guard()
    return rebuilt


def independent_screens(rows, schedule):
    result = []
    for game in GAMES:
        counts = schedule['games'][game]['counts']
        for hidden, latent in CAPACITIES:
            selected = {row['config']['seed']: row for row in rows if row['game'] == game
                        and row['target_space'] == 'ema' and row['config']['variant'] == 'raw-jepa'
                        and (row['config']['hidden'], row['config']['latent']) == (hidden, latent)}
            require(set(selected) == set(SEEDS), 'Missing primary seed')
            item = {'game': game, 'hidden': hidden, 'latent': latent}
            for label, packed, full, n_edges, n_used in (
                    ('primary', 'packed', 'all_h1', counts['total_h1_edges'], counts['used_edges']),
                    ('nonterminal', 'packed_nonterminal', 'all_nonterminal',
                     counts['all_nonterminal_edges'], counts['used_nonterminal_edges'])):
                values = []
                for seed in SEEDS:
                    row = selected[seed]; denominator = row[full]['latent_sse']; numerator = row[packed]['bound_sse']
                    value = numerator/denominator if denominator and row[packed]['block_count'] else None
                    saved = row[packed]['bound_full_sse_ratio']
                    require((value is None and saved is None) or (value is not None and saved is not None
                            and math.isclose(value, saved, rel_tol=1e-12, abs_tol=1e-12)), 'Independent ratio normalization mismatch')
                    values.append(value)
                coverage = n_used/n_edges if n_edges else 0.
                median = statistics.median(values) if all(v is not None for v in values) else None
                favorable = sum(v is not None and v >= .1 for v in values)
                item[label] = {'coverage': coverage, 'ratios_by_seed': dict(zip(map(str, SEEDS), values)),
                               'median': median, 'favorable_seeds': favorable,
                               'passed': coverage >= .25 and median is not None and median >= .1 and favorable >= 2}
            result.append(item)
    return result


def audit(probe, grid, training, guard):
    import numpy as np
    from two_player_v22.data import load_dataset
    from two_player_v24_probe.report import summarize, markdown
    journal = read(probe/'journal.json'); journal_hash = sha(probe/'journal.json')
    require(journal['status'] == 'complete' and journal['errors'] == [], 'Probe incomplete or failed')
    require(journal['code_commit'] == COMMIT, 'Wrong probe launch commit')
    require(journal['limits'] == {'seconds': 600., 'output_bytes': 200000000, 'process_peak_rss_bytes': 1000000000}, 'Changed resource caps')
    require(0 <= journal['seconds'] < 600. and 0 < journal['process_peak_rss_bytes'] < 1000000000, 'Resource acceptance failed')
    for key in ('optimizer_updates', 'development_predictions', 'selection_predictions', 'final_predictions', 'new_search_decisions'):
        require(journal[key] == 0, 'Forbidden fitting/evaluation counter')
    for name, expected in journal['source'].items():
        guard(); path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and ':' not in name, 'Unsafe source path')
        blob = subprocess.run(['git', 'cat-file', 'blob', COMMIT+':'+name], cwd=ROOT,
                              check=True, capture_output=True, timeout=15).stdout
        require(hashlib.sha256(blob.replace(b'\r\n', b'\n')).hexdigest() == expected ==
                hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n', b'\n')).hexdigest(), 'Committed source mismatch: '+name)
    prerequisite_path = ROOT/'docs/validation/V23_INDEPENDENT_AUDIT.json'
    require(sha(prerequisite_path) == journal['prerequisite_audit_sha256'] == AUDIT_SHA, 'Prerequisite audit changed')
    prerequisite = read(prerequisite_path)
    require(prerequisite['status'] == 'verified' and prerequisite['errors'] == [], 'Invalid prerequisite')
    ledger = read(grid/'ledger.json')
    require(sha(grid/'ledger.json') == journal['grid_ledger_sha256'] == prerequisite['ledger_sha256'], 'Input grid ledger changed')
    require(ledger['status'] == 'complete' and ledger['failures'] == [] and ledger['code_commit'] == GRID_COMMIT, 'Invalid source grid')
    manifest = read(training/'manifest.json')
    require(manifest['dataset_fingerprint'] == journal['dataset_fingerprint'] == FP and manifest['split'] == 'train'
            and manifest['role'] == 'redacted-training' and manifest['fraction'] == 1., 'Only full standalone training permitted')
    require(manifest == ledger['dataset_manifest'] and sha(training/'manifest.json') == prerequisite['training']['manifest_sha256']
            and sha(training/'data.json') == prerequisite['training']['payload_sha256'], 'Training identity mismatch')
    train = load_dataset(training, 'train'); guard()
    schedule = read(probe/'schedule.json')
    require(sha(probe/'schedule.json') == journal['schedule_sha256'], 'Saved schedule bytes changed')
    rebuilt = rebuild_packing(train, guard)
    require(rebuilt == schedule, 'Independent complete H1/packing reconstruction differs')
    expected_cells = {(v, h, d, s) for v in FAMILIES for h, d in CAPACITIES for s in SEEDS}
    seen, rows, tensors = set(), [], 0
    source_cells = {r['id']: r for r in ledger['runs']}
    allowed = {'journal.json', 'schedule.json', 'report.json', 'report.md'}
    require(len(journal['completed_cells']) == 18, 'Missing/extra completed cells')
    for cell in journal['completed_cells']:
        guard(); config = cell['config']; key = config['variant'], config['hidden'], config['latent'], config['seed']
        require(key in expected_cells and key not in seen, 'Repeated/unfrozen measurement cell')
        seen.add(key)
        name = f'{key[0]}-h{key[1]}-z{key[2]}-s{key[3]}'
        require(cell['id'] == name and cell['measurement_file'] == name+'.json', 'Invalid measurement path')
        allowed.add(cell['measurement_file'])
        require(sha(probe/cell['measurement_file']) == cell['measurement_sha256'], 'Measurement file hash changed')
        measurement = read(probe/cell['measurement_file']); old = source_cells[name]
        require(old['config'] == measurement['config'] == config and old['status'] == 'complete', 'Cell configuration changed')
        receipt_path = grid/name/'receipt.json'; receipt = read(receipt_path)
        require(sha(receipt_path) == old['receipt_sha256'], 'Original checkpoint receipt changed')
        reference = [r for r in receipt['snapshots'] if r['epoch'] == 160]
        require(len(reference) == 1 and reference[0]['checkpoint'] == 'checkpoint-e160.npz', 'Wrong final snapshot')
        checkpoint = grid/name/'checkpoint-e160.npz'
        require(sha(checkpoint) == cell['checkpoint_sha256'] == measurement['checkpoint_sha256'] == reference[0]['checkpoint_sha256'], 'Checkpoint bytes changed')
        with np.load(checkpoint, allow_pickle=False) as saved:
            metadata = json.loads(str(saved['metadata']))
            require(metadata['config'] == config and metadata['identity'] == receipt['identity']
                    and (metadata['epoch'], metadata['step']) == (160, 10560), 'Checkpoint identity/counters changed')
            names = set(saved.files)-{'metadata'}
            require(len(names) == 59 and names == set(metadata['array_hashes']), 'Checkpoint tensor inventory changed')
            hashes = {}
            for tensor in sorted(names):
                array = saved[tensor]
                require(array.dtype == np.float64 and np.isfinite(array).all(), 'Invalid checkpoint tensor')
                hashes[tensor] = hashlib.sha256(array.tobytes()).hexdigest(); tensors += 1
            require(hashes == metadata['array_hashes'] and digest(hashes) == measurement['checkpoint_tensor_sha256'], 'Measured tensor identity differs')
        require(len(measurement['rows']) == 4 and all(row['config'] == config for row in measurement['rows']), 'Measurement row identity mismatch')
        rows.extend(measurement['rows'])
    require(seen == expected_cells and len(rows) == 72 and tensors == 1062, 'Incomplete audit inventory')
    require({p.relative_to(probe).as_posix() for p in probe.rglob('*') if p.is_file()} == allowed, 'Unexpected/missing output file')
    report = read(probe/'report.json')
    require(sha(probe/'report.json') == journal['report_sha256'] and sha(probe/'report.md') == journal['markdown_sha256'], 'Report bytes changed')
    recomputed = summarize(rows, schedule)
    require(recomputed['status'] == 'verified_probe' and recomputed['verification_errors'] == [], 'Frozen arithmetic verifier failed')
    require(all(report[k] == value for k, value in recomputed.items()), 'Saved report differs from recomputed arithmetic')
    require(report['measurements'] == journal['completed_cells'] and report['source'] == journal['source']
            and report['code_commit'] == COMMIT and report['dataset_fingerprint'] == FP
            and report['grid_ledger_sha256'] == journal['grid_ledger_sha256']
            and report['schedule_file_sha256'] == journal['schedule_sha256']
            and report['prerequisite_audit_sha256'] == AUDIT_SHA, 'Report provenance mismatch')
    require((probe/'report.md').read_text(encoding='utf-8') == markdown(report), 'Markdown report differs from JSON rendering')
    screens = independent_screens(rows, schedule)
    for screen in screens:
        saved = next(r for r in report['screens'] if (r['game'], r['hidden'], r['latent']) ==
                     (screen['game'], screen['hidden'], screen['latent']))
        for ours, theirs in (('primary', 'primary'), ('nonterminal', 'nonterminal_sensitivity')):
            a, b = screen[ours], saved[theirs]
            require(a['coverage'] == b['coverage'] and a['ratios_by_seed'] == b['ratios_by_seed']
                    and a['median'] == b['median_bound_full_sse_ratio'] and a['passed'] == b['material_obstruction']
                    and a['favorable_seeds'] == b['seeds_at_least_0_10'], 'Independent heuristic-screen disagreement')
    actual_bytes = sum(p.stat().st_size for p in probe.rglob('*') if p.is_file())
    require(actual_bytes < 200000000 and actual_bytes-(probe/'journal.json').stat().st_size == journal['artifact_bytes_excluding_journal'], 'Output size accounting mismatch')
    require(sha(probe/'journal.json') == journal_hash, 'Probe changed during audit')
    guard()
    return {'status': 'verified', 'probe_commit': COMMIT, 'source_files_verified': len(journal['source']),
            'source_inventory_digest': digest(journal['source']), 'journal_sha256': journal_hash,
            'report_sha256': journal['report_sha256'], 'schedule_file_sha256': journal['schedule_sha256'],
            'schedule_canonical_digest': schedule['schedule_sha256'], 'prerequisite_audit_sha256': AUDIT_SHA,
            'dataset_fingerprint': FP, 'training_payload_sha256': sha(training/'data.json'),
            'grid_ledger_sha256': journal['grid_ledger_sha256'],
            'counts': {'cells': 18, 'rows': 72, 'checkpoints': 18, 'checkpoint_tensor_arrays': tensors,
                       'primary_screens': 4, 'nonterminal_screens': 4,
                       'h1_edges': sum(len(g['edges']) for g in schedule['games'].values()),
                       'packed_blocks': sum(len(g['blocks']) for g in schedule['games'].values())},
            'packing': {g: v['counts'] for g, v in schedule['games'].items()}, 'screens': screens,
            'resource': {'probe_seconds': journal['seconds'], 'process_peak_rss_bytes': journal['process_peak_rss_bytes'],
                         'actual_artifact_bytes': actual_bytes},
            'optimizer_updates': 0, 'new_model_encodings': 0, 'new_model_predictions': 0,
            'protected_artifacts_opened': 0,
            'limitations': ['Internal independent packing implementation shares audited game adapters.',
                            'Saved bounds, reversal counts and SSEs not remeasured; arithmetic/provenance checked without encoding.',
                            'Conservative fixed-target H1 diagnostic; no generalization, additive adequacy or JEPA superiority claim.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe', type=Path); parser.add_argument('grid', type=Path)
    parser.add_argument('full_training', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    require(os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1', 'Set BLAS/OMP threads to1')
    paths = [args.probe.resolve(), args.grid.resolve(), args.full_training.resolve()]; output = args.output.resolve()
    require(not output.exists() and output.suffix == '.json' and not any(output.is_relative_to(p) for p in paths), 'New audit JSON must be outside input directories')
    started = time.perf_counter()
    def guard():
        if time.perf_counter()-started >= 600.: raise TimeoutError('Independent audit deadline exceeded')
    result = {'version': 'v24-independent-order-audit01', 'status': 'inconclusive', 'script_sha256': sha(__file__), 'errors': []}
    try:
        result.update(audit(*paths, guard))
    except (ValueError, KeyError, TypeError, IndexError, OSError, TimeoutError, subprocess.SubprocessError) as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    result['audit_seconds'] = time.perf_counter()-started
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'status': result['status'], 'errors': result['errors'], 'output': str(output)}))
    return 0 if result['status'] == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
