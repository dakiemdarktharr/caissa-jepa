"""Independent postrun artifact audit; no fitting, model predictions or search.

Accepts only a completed V2.3 grid and the standalone full-label TRAIN export.
Never opens a parent bank, development, selection or final artifact. Sampling,
augmentation and label-count replay are independently implemented below rather
than calling the training runner. Legal closure uses the audited game adapters;
this is internal reproducibility checking, not an external rules replication.
Saved metric arithmetic is checked by the frozen strict reporter; measurements
are not recomputed from model predictions. No training-only result establishes
generalization, JEPA superiority or a research candidate promotion.

Run only after fitting has stopped. Output must be a new JSON file outside the
input artifact directories. The 600-second audit deadline is cooperative.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
COMMIT = '20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37'
FINGERPRINT = '73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'
GAMES = ('connect4-4x5', 'reversi6')
SEEDS = (17, 29, 43)
FAMILIES = ('direct', 'value-dynamics', 'raw-jepa')
CAPACITIES = ((64, 32), (128, 64))
SNAPSHOTS = (0, 40, 80, 160)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deadline_guard(deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError('Independent audit deadline exceeded')


def git_source_inventory(ledger, deadline):
    require(ledger['code_commit'] == COMMIT, 'Grid commit differs from frozen launch commit')
    count = 0
    for name, expected in sorted(ledger['source'].items()):
        deadline_guard(deadline)
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and ':' not in name,
                'Invalid source inventory path')
        require((ROOT/relative).resolve().is_relative_to(ROOT), 'Source path escapes repository')
        blob = subprocess.run(['git', 'cat-file', 'blob', COMMIT+':'+name], cwd=ROOT,
                              check=True, capture_output=True, timeout=15).stdout
        normalized = hashlib.sha256(blob.replace(b'\r\n', b'\n')).hexdigest()
        current = hashlib.sha256((ROOT/relative).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        require(normalized == current == expected, 'Committed/current source mismatch: '+name)
        count += 1
    require(count > 0, 'Empty source inventory')
    require('tools/audit_v23_fit.py' not in ledger['source'], 'Audit unexpectedly changes frozen source inventory')
    return {'commit': COMMIT, 'files_checked': count, 'inventory_sha256': digest(ledger['source'])}


def structural_inventory(train, deadline):
    """Independently enumerate complete legal depth-two forks, without an oracle."""
    from two_player.games import State
    from two_player_v2 import GAMES_V2
    def state(obj):
        return State(tuple(obj['board']), obj['player'])
    def nid(game, position):
        return digest([game, asdict(position)])
    nodes, roots, forks = train['nodes'], train['roots'], train['forks']
    require((len(roots), len(nodes), len(forks)) == (509, 9237, 6750), 'Training inventory changed')
    root_by_id = {r['root_id']: r for r in roots}
    require(len(root_by_id) == len(roots), 'Duplicate training root')
    grouped = defaultdict(list)
    for f in forks:
        require(f['split'] == 'train' and f['root_id'] in root_by_id, 'Foreign fork root or split')
        grouped[f['root_id']].append(f)
    require(set(grouped) == set(root_by_id), 'Missing root forks')
    signature, reached = [], set()
    for root in roots:
        deadline_guard(deadline)
        name, rid = root['game'], root['root_id']
        require(name in GAMES and root['split'] == 'train', 'Foreign root game/split')
        require(rid == digest([name, root['trajectory'], root['state']]), 'State-only root identity mismatch')
        game = GAMES_V2[name]
        start = state(root['state'])
        expected, counts = set(), {h: dict.fromkeys(('all', 'nonterminal', 'terminal'), 0) for h in ('1', '2')}
        missing = 0
        for action in game.legal_actions(start):
            child = game.transition(start, action)
            terminal = game.terminal(child) is not None
            counts['1']['all'] += 1
            counts['1']['terminal' if terminal else 'nonterminal'] += 1
            replies = game.legal_actions(child)
            require(bool(replies) is not terminal, 'Terminal/action-list inconsistency')
            if not replies:
                expected.add(((action, None), (nid(name, start), nid(name, child), None)))
                missing += 1
            for reply in replies:
                leaf = game.transition(child, reply)
                expected.add(((action, reply), (nid(name, start), nid(name, child), nid(name, leaf))))
                counts['2']['all'] += 1
                counts['2']['terminal' if game.terminal(leaf) is not None else 'nonterminal'] += 1
        observed = {(tuple(f['actions']), tuple(f['node_ids'])) for f in grouped[rid]}
        require(observed == expected and len(observed) == len(grouped[rid]), 'Incomplete/duplicate/illegal root closure')
        require(all(f['game'] == name for f in grouped[rid]), 'Fork game mismatch')
        reached.update(n for _, ids in expected for n in ids if n is not None)
        signature.append([name, rid, root['trajectory'], len(expected), missing, counts])
    require(reached == set(nodes), 'Unused or missing closure nodes')
    geometry = {}
    for name in GAMES:
        selected = [n for n in nodes.values() if n['game'] == name]
        geometry[name] = {'samples': len(selected), 'terminal_nodes': sum(n['terminal'] for n in selected),
                          'nonterminal_nodes': sum(not n['terminal'] for n in selected)}
    for key, node in nodes.items():
        position = state(node['state']); game = GAMES_V2[node['game']]
        require(key == nid(node['game'], position), 'Node state identity mismatch')
        outcome = game.terminal(position)
        require(node['terminal'] is (outcome is not None), 'Node terminal flag mismatch')
        require(node['legal'] == list(game.legal_actions(position)), 'Node legal actions mismatch')
        require(node['value_labelled'] is True and node['policy_labelled'] is (outcome is None), 'Incomplete full labels')
        if outcome is not None:
            require(node['value'] == position.player*outcome, 'Terminal value perspective mismatch')
    return sorted(signature), geometry


def replay_plans(train, deadline):
    """Reconstruct 480 plans and counters without runtime/augmentation helpers."""
    import numpy as np
    forks, nodes = train['forks'], train['nodes']
    groups = defaultdict(lambda: defaultdict(list))
    valid = np.zeros((len(forks), 3), dtype=bool)
    terminal = np.zeros_like(valid)
    for i, f in enumerate(forks):
        groups[f['game']][f['root_id']].append(i)
        for h, node_id in enumerate(f['node_ids']):
            if node_id is not None:
                valid[i, h] = True
                terminal[i, h] = nodes[node_id]['terminal']
    require(set(groups) == set(GAMES) and {g: len(v) for g, v in groups.items()} ==
            dict(zip(GAMES, (248, 261))), 'Unexpected sampling root groups')
    plans = {}
    for seed in SEEDS:
        for epoch in range(160):
            deadline_guard(deadline)
            rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2201]))
            samples, exposure = [], {}
            maximum = max(map(len, groups.values()))
            for game in sorted(groups):
                ids = sorted(groups[game])
                order = list(rng.permutation(len(ids)))
                order.extend(rng.integers(len(ids), size=maximum-len(ids)).tolist())
                for root_index in order:
                    samples.extend(rng.choice(groups[game][ids[root_index]], size=16, replace=True).tolist())
                exposure[game] = {'unique_roots': len(ids), 'root_draws': maximum,
                                  'repeated_root_draws': maximum-len(ids), 'fork_draws': maximum*16}
            indices = np.asarray(samples, dtype=np.int64)
            rng.shuffle(indices)
            require(len(indices) == 8352, 'Wrong replay exposure')
            index_hash = hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest()
            schedule = {'games': exposure, 'samples': 8352, 'unique_forks': len(np.unique(indices)),
                        'index_sha256': index_hash}
            aug_rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2211]))
            transforms = np.asarray([int(aug_rng.integers(2 if forks[int(i)]['game'] == GAMES[0] else 8))
                                     for i in indices], dtype=np.int64)
            transform_counts = Counter(forks[int(i)]['game']+'/'+str(int(t)) for i, t in zip(indices, transforms))
            augmentation = {'version': 'legal-symmetries-v21', 'samples': 8352, 'seed': seed, 'epoch': epoch,
                            'rng_namespace': 2211, 'transform_counts': dict(sorted(transform_counts.items())),
                            'transform_sha256': hashlib.sha256(transforms.astype('<i8').tobytes()).hexdigest(),
                            'index_sha256': index_hash}
            selected, endings = valid[indices], terminal[indices]
            encoded = int(selected.sum()); terminals = int(endings.sum())
            counts = {'encoded_count': encoded, 'value_count': encoded, 'policy_count': encoded-terminals,
                      'terminal_count': terminals, 'value_unlabelled_count': 0, 'policy_unlabelled_count': 0}
            for h in (1, 2):
                eligible = int(selected[:, h].sum())
                counts.update({f'h{h}_eligible_count': eligible, f'h{h}_missing_count': 8352-eligible,
                               f'h{h}_unlabelled_count': 0, f'h{h}_ema_value_count': 0})
            plans[seed, epoch] = {'schedule': schedule, 'augmentation': augmentation, 'common_counts': counts}
    return plans


def metric_signature(metrics):
    rows = metrics['fit']['per_root']
    require(all(r['saved_planning'] is None for r in rows), 'Unexpected saved planning output')
    return sorted([[r['game'], r['root_id'], r['trajectory'], r['fork_records'], r['missing_h2_forks'],
                    {h: {s: r['horizons'][h][s]['count'] for s in ('all', 'nonterminal', 'terminal')}
                     for h in ('1', '2')}] for r in rows])


def audit(grid, training, deadline):
    import numpy as np
    from two_player_v22.data import load_dataset
    from two_player_v23_diagnostic.report import summarize_grid
    ledger = read(grid/'ledger.json')
    require(ledger['status'] == 'complete' and ledger['failures'] == [], 'Grid incomplete or failed; no audit replay permitted')
    original_ledger_hash = sha(grid/'ledger.json')
    require(ledger['dataset_fingerprint'] == FINGERPRINT, 'Wrong grid dataset fingerprint')
    source = git_source_inventory(ledger, deadline)
    # Manifest preflight precedes even the standalone payload loader.
    manifest = read(training/'manifest.json')
    require(manifest['dataset_fingerprint'] == FINGERPRINT and manifest['split'] == 'train'
            and manifest['role'] == 'redacted-training' and manifest['fraction'] == 1.
            and manifest['label_seed'] == 271828, 'Only frozen standalone full-label training is accepted')
    require(manifest == ledger['dataset_manifest'], 'Grid and supplied training manifests differ')
    train = load_dataset(training, 'train')
    signature, geometry = structural_inventory(train, deadline)
    plans = replay_plans(train, deadline)
    references = read(ROOT/'docs/validation/V23_EPOCH40_REFERENCES.json')
    refs = {(r['variant'], r['seed']): r for r in references['rows']}
    expected = {(v, h, z, s) for v in FAMILIES for h, z in CAPACITIES for s in SEEDS}
    require(len(ledger['runs']) == 18, 'Incomplete cell inventory')
    observed, allowed, epoch_receipts, snapshots, tensor_arrays, replay_count = set(), {'ledger.json'}, 0, 0, 0, 0
    cell_records = []
    for item in ledger['runs']:
        deadline_guard(deadline)
        config = item['config']; key = config['variant'], config['hidden'], config['latent'], config['seed']
        require(key in expected and key not in observed and item['status'] == 'complete', 'Duplicate/foreign/incomplete cell')
        observed.add(key)
        cell_name = f"{key[0]}-h{key[1]}-z{key[2]}-s{key[3]}"
        require(item['id'] == cell_name, 'Unexpected cell path')
        cell = grid/cell_name
        receipt = read(cell/'receipt.json'); history = read(cell/'history.json'); budget = read(cell/'budget.json')
        require(sha(cell/'receipt.json') == item['receipt_sha256'], 'Receipt bytes changed')
        require(sha(cell/'history.json') == receipt['history_sha256'], 'History bytes changed')
        require(receipt['config'] == config and budget['identity'] == receipt['identity'], 'Cell identity/config mismatch')
        require(budget['status'] == 'complete' and len(history) == 160, 'Incomplete journal/history')
        allowed.update(cell_name+'/'+name for name in ('receipt.json', 'history.json', 'budget.json'))
        for epoch, row in enumerate(history):
            plan = plans[config['seed'], epoch]
            require(row['epoch'] == epoch+1 and row['step'] == 66*(epoch+1) and row['steps'] == 66, 'History counters changed')
            require(row['schedule'] == plan['schedule'] and row['augmentation'] == plan['augmentation'], 'Independent sampling/augmentation replay mismatch')
            counts = dict(plan['common_counts'])
            for h in (1, 2):
                eligible = counts[f'h{h}_eligible_count']
                counts.update({f'h{h}_count': eligible if key[0] != 'direct' else 0,
                               f'h{h}_value_label_count': eligible if key[0] != 'direct' else 0,
                               f'h{h}_latent_count': eligible if key[0] == 'raw-jepa' else 0})
            require(row['label_and_target_count_totals'] == counts, 'Independent label/target counts differ')
            epoch_receipts += 1
        require([s['epoch'] for s in receipt['snapshots']] == list(SNAPSHOTS), 'Missing/extra snapshot')
        values = {}
        for snap in receipt['snapshots']:
            deadline_guard(deadline)
            epoch = snap['epoch']
            cp_name, mp_name = f'checkpoint-e{epoch:03d}.npz', f'snapshot-e{epoch:03d}.json'
            require(snap['checkpoint'] == cp_name and snap['metrics'] == mp_name, 'Noncanonical snapshot path')
            cp, mp = cell/cp_name, cell/mp_name
            require(sha(cp) == snap['checkpoint_sha256'] and sha(mp) == snap['metrics_sha256'], 'Snapshot bytes changed')
            allowed.update((cell_name+'/'+cp_name, cell_name+'/'+mp_name))
            with np.load(cp, allow_pickle=False) as saved:
                metadata = json.loads(str(saved['metadata']))
                names = set(saved.files)-{'metadata'}
                require(len(names) == 59 and names == set(metadata['array_hashes']), 'Checkpoint tensor inventory changed')
                require(metadata['config'] == config and metadata['identity'] == receipt['identity'], 'Checkpoint identity changed')
                require((metadata['epoch'], metadata['step'], snap['step']) == (epoch, epoch*66, epoch*66), 'Checkpoint counters changed')
                tensor_hashes = {}
                for name in sorted(names):
                    array = saved[name]
                    require(array.dtype == np.float64 and np.isfinite(array).all(), 'Invalid checkpoint tensor')
                    tensor_hashes[name] = hashlib.sha256(array.tobytes()).hexdigest()
                    tensor_arrays += 1
                require(tensor_hashes == metadata['array_hashes'], 'Checkpoint tensor checksum mismatch')
            small40 = key[1:3] == (64, 32) and epoch == 40
            require(snap['reference_match'] == ('verified' if small40 else 'not_applicable'), 'Replay status mismatch')
            if small40:
                ref = refs[key[0], key[3]]
                require(ref['config'] == config and ref['array_hashes'] == tensor_hashes and
                        (ref['epoch'], ref['step']) == (epoch, epoch*66), 'Independent historical replay mismatch')
                replay_count += 1
            metric = read(mp)
            require(metric_signature(metric) == signature, 'Snapshot root trajectory/fork/stratum metadata differs from legal train closure')
            for game in GAMES:
                require(all(metric['geometry'][game][k] == n for k, n in geometry[game].items()), 'Geometry raw-node counts differ from train payload')
            values[str(epoch)] = {'S': metric['S'], 'components': metric['S_components']}
            snapshots += 1
        cell_records.append({'id': cell_name, 'seconds': item['seconds'], 'snapshots': values})
    require(observed == expected and (epoch_receipts, snapshots, replay_count, tensor_arrays) == (2880, 72, 9, 4248), 'Postrun audit completeness mismatch')
    actual = {p.relative_to(grid).as_posix() for p in grid.rglob('*') if p.is_file()}
    require(actual == allowed, 'Unexpected/missing files, failure receipts or temporary artifacts in completed grid')
    deadline_guard(deadline)
    report = summarize_grid(grid)
    require(report['status'] == 'verified_diagnostic' and report['verification_errors'] == [],
            'Strict reporter failed: '+repr(report['verification_errors']))
    require(report['root_schedule_sha256'] == digest(signature), 'Strict report structural signature disagrees')
    require(report['decisions']['candidate'] is None, 'Unexpected model promotion')
    deadline_guard(deadline)
    require(sha(grid/'ledger.json') == original_ledger_hash, 'Grid changed during audit')
    require(sha(training/'data.json') == manifest['artifacts']['data.json']['sha256'], 'Training payload changed during audit')
    git_source_inventory(ledger, deadline)
    return {'status': 'verified', 'source_verification': source, 'ledger_sha256': original_ledger_hash,
            'training': {'dataset_fingerprint': FINGERPRINT, 'manifest_sha256': sha(training/'manifest.json'),
                         'payload_sha256': sha(training/'data.json'), 'roots': 509, 'nodes': 9237, 'forks': 6750,
                         'legal_root_signature_sha256': digest(signature), 'geometry_inventory': geometry},
            'counts': {'cells': 18, 'plans_replayed': 480, 'unique_replayed_fork_draws': 480*8352,
                       'epoch_receipts_checked': epoch_receipts, 'snapshots_checked': snapshots,
                       'tensor_arrays_checked': tensor_arrays, 'historical_replays': replay_count,
                       'snapshot_root_records_checked': 72*509},
            'plan_hashes_by_seed': {str(s): digest([plans[s, e] for e in range(160)]) for s in SEEDS},
            'strict_report_status': report['status'], 'strict_report_sha256': digest(report),
            'decisions': report['decisions'], 'cells': cell_records,
            'resource': {k: report[k] for k in ('total_cell_seconds', 'actual_artifact_bytes', 'process_peak_rss_bytes')},
            'new_predictions': 0, 'optimizer_updates': 0, 'protected_artifacts_opened': 0,
            'limitations': ['Internal independent replay using the same NumPy RNG and audited game adapters.',
                            'Checkpoint identity and saved metric arithmetic checked; no model predictions recomputed.',
                            'Training-only descriptive evidence; no generalization or JEPA superiority claim.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid', type=Path)
    parser.add_argument('full_training', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    require(os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1',
            'Set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 before Python')
    grid, train, output = args.grid.resolve(), args.full_training.resolve(), args.output.resolve()
    require(not output.exists() and output.suffix.lower() == '.json', 'Audit output must be a new JSON file')
    require(not output.is_relative_to(grid) and not output.is_relative_to(train), 'Audit output must be outside input artifacts')
    started = time.perf_counter()
    result = {'version': 'v23-independent-postrun-audit01', 'status': 'inconclusive',
              'script_sha256': sha(__file__), 'grid': str(grid), 'full_training': str(train), 'errors': []}
    try:
        result.update(audit(grid, train, started+600.))
    except (ValueError, KeyError, TypeError, IndexError, OSError, TimeoutError, subprocess.SubprocessError) as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    result['audit_seconds'] = time.perf_counter()-started
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'errors': result['errors'], 'output': str(output)}))
    return 0 if result['status'] == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
