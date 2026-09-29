"""Independent completed-grid V2.5 audit; no optimizer or new model predictions.

Inputs are ONLY the completed grid and standalone FULL training/development
exports. Never open the parent bank, selection, or final files. Rebuild complete
legal groups using the separate bitboard reference; replay sampling/augmentation
without the runtime's sampler; bind embedded truth to the actual standalone.
Verify stored arrays, actions, counters and diagnostic arithmetic. Saved latent
errors/geometry are NOT remeasured and per-reply false-pessimism indicators cannot
be independently reconstructed from group summaries alone. The reference engine
is a same-project implementation, not a third-party referee. Reused development
roots and adaptive design do not support confirmatory or equilibrium claims.

Run only after the parent announces completion. New JSON output must be outside
all input directories. Audit errors are preserved, never repaired in artifacts.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORIGINAL_COMMIT = '5102ea0588198f993874a495d18bfef1e868e2ec'
REFERENCE_PATH = 'docs/validation/V25_GRID04_TENSOR_REFERENCES.json'
REFERENCE_SHA = 'e6d7a27624cc864fe6edcd8c0b21c9f93e7b239781729684bfc3bafe8a8b5b3c'
TRAIN_FP = '73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'
DEV_FP = 'bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617'
GAMES = ('connect4-4x5', 'reversi6')
SEEDS = (17, 29, 43)
RATES = (.001, .0003)
VARIANTS = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail', 'raw-mean', 'raw-tail', 'raw-scaled')
COUNTS = {'train': (509, 9237, 6750), 'development': (209, 3756, 2735)}


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value): return type(value) in (int, float) and math.isfinite(value)


def close(actual, expected, message):
    require(finite(actual) and finite(expected) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), message)


def guard(deadline):
    if time.perf_counter() >= deadline: raise TimeoutError('Independent audit exceeded 600-second cooperative deadline')


def source_check(ledger, deadline, expected_commit):
    from two_player_v25r.bindings import _ORIGINAL_SOURCE, runtime_source
    require(len(expected_commit) == 40 and all(c in '0123456789abcdef' for c in expected_commit)
            and ledger['code_commit'] == expected_commit and ledger['source'], 'Unexpected launch source provenance')
    original = _ORIGINAL_SOURCE()
    require(len(original) == 31 and ledger['source'] == runtime_source()
            and {k: ledger['source'][k] for k in original} == original, 'Original/augmented source inventory mismatch')
    require(len(ledger['source']) == 37, 'Expected original31 plus five repair modules and one amendment')
    sources = dict(ledger['source'])
    # Also bind the separately written rules used by this audit to launch code.
    name = 'benchmarks/reference_rules.py'
    sources.setdefault(name, hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest())
    for name, expected in sorted(sources.items()):
        guard(deadline)
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and ':' not in name
                and (ROOT/rel).resolve().is_relative_to(ROOT), 'Unsafe source path')
        blob = subprocess.run(['git', 'cat-file', 'blob', expected_commit+':'+name], cwd=ROOT,
                              check=True, capture_output=True, timeout=15).stdout
        require(hashlib.sha256(blob.replace(b'\r\n', b'\n')).hexdigest() == expected
                == hashlib.sha256((ROOT/rel).read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
                'Frozen/current Git blob mismatch: '+name)
        if name in original:
            historical = subprocess.run(['git', 'cat-file', 'blob', ORIGINAL_COMMIT+':'+name], cwd=ROOT,
                                        check=True, capture_output=True, timeout=15).stdout
            require(hashlib.sha256(historical.replace(b'\r\n', b'\n')).hexdigest() == expected,
                    'Repair changed original scientific source: '+name)
    require('tools/audit_v25_grid.py' not in sources, 'Audit unexpectedly in frozen runtime source')
    reference_blob = subprocess.run(['git', 'cat-file', 'blob', expected_commit+':'+REFERENCE_PATH], cwd=ROOT,
                                    check=True, capture_output=True, timeout=15).stdout
    require(hashlib.sha256(reference_blob.replace(b'\r\n', b'\n')).hexdigest() == REFERENCE_SHA,
            'Pre-retry tensor reference was not pinned in the repaired launch commit')
    return {'commit': expected_commit, 'original_commit': ORIGINAL_COMMIT, 'original_source_files_unchanged': len(original),
            'runtime_source_files': len(ledger['source']),
            'checked_source_files_including_reference': len(sources), 'source_inventory_sha256': digest(ledger['source'])}


def inventory(groups):
    return {'roots': len({g['root_id'] for g in groups}), 'groups': len(groups),
            'fork_rows': sum(g['row_count'] for g in groups),
            'h1_terminal_groups': sum(g['h1_terminal'] for g in groups),
            'h1_nonterminal_groups': sum(not g['h1_terminal'] for g in groups),
            'h2_valid_rows': sum(g['h2_valid_rows'] for g in groups),
            'h2_missing_rows': sum(g['row_count']-g['h2_valid_rows'] for g in groups),
            'h2_terminal_rows': sum(g['h2_terminal_rows'] for g in groups),
            'h2_nonterminal_rows': sum(g['h2_nonterminal_rows'] for g in groups),
            'h2_eligible_groups': sum(g['h2_nonterminal_rows'] > 0 for g in groups)}


def legal_closure(dataset, deadline):
    """Reconstruct nodes/forks/groups using the independent bitboard rules."""
    from benchmarks.reference_rules import ReferenceGame
    from two_player.games import State
    from two_player_v2 import GAMES_V2
    split = dataset['manifest']['split']
    require((len(dataset['roots']), len(dataset['nodes']), len(dataset['forks'])) == COUNTS[split], 'Standalone inventory mismatch')
    references = {'connect4-4x5': ReferenceGame(4, 5, 4, gravity=True), 'reversi6': ReferenceGame(6, 6, 0, reversi=True)}
    def action(ref, cell): return 64 if cell == -1 else cell//ref.cols*8+cell%ref.cols
    def legal(ref, state):
        cells = ref.legal_actions(state)
        return sorted(cells, key=lambda c: c % ref.cols) if ref.gravity else list(cells)
    def node_id(name, ref, state): return digest([name, {'board': list(ref.board(state)), 'player': state.player}])
    nodes, forks = dataset['nodes'], dataset['forks']
    counts = Counter(); canonical = set(); reached = set()
    for nid, node in nodes.items():
        guard(deadline)
        name = node['game']; ref = references[name]
        state = ref.from_board(node['state']['board'], node['state']['player'])
        outcome = ref.terminal(state)
        require(nid == node_id(name, ref, state) and node['terminal'] is (outcome is not None), 'Reference node identity/terminal mismatch')
        require(node['legal'] == [action(ref, c) for c in legal(ref, state)], 'Reference legal action order mismatch')
        require(node['value_labelled'] is True and node['policy_labelled'] is (outcome is None), 'Incomplete FULL labels')
        if outcome is not None: require(node['value'] == state.player*outcome, 'Reference terminal value sign mismatch')
        canonical.add((name, GAMES_V2[name].canonical_key(State(tuple(node['state']['board']), node['state']['player']))))
        counts['nodes'] += 1; counts['terminal_nodes'] += outcome is not None
        counts['forced_pass_nodes'] += ref.legal_actions(state) == (-1,)
    index = {}
    for i, fork in enumerate(forks):
        key = fork['game'], fork['root_id'], *fork['actions']
        require(key not in index and fork['split'] == split, 'Duplicate/foreign recorded fork')
        index[key] = i
    groups, root_trees = [], {}
    for root in dataset['roots']:
        guard(deadline)
        name, rid = root['game'], root['root_id']; ref = references[name]
        state = ref.from_board(root['state']['board'], root['state']['player'])
        require(root['split'] == split and ref.terminal(state) is None, 'Foreign/terminal root')
        if split == 'train': require(rid == digest([name, root['trajectory'], root['state']]), 'Training root rekey mismatch')
        own_cells = legal(ref, state)
        require(root['actions'] == [action(ref, a) for a in own_cells], 'Reference root action order mismatch')
        tree = {'nodes': 0, 'leafcount': 0, 'neural_leaf_candidates': 0, 'zero_estimates': [], 'terminal_branches': {}}
        for a in own_cells:
            child = ref.transition(state, a); own = action(ref, a)
            source_id, h1_id = node_id(name, ref, state), node_id(name, ref, child)
            terminal = ref.terminal(child) is not None
            replies = [None] if terminal else legal(ref, child)
            ids, h2ids, reply_actions, values, zeros = [], [], [], [], []
            tree['nodes'] += 1
            for reply in replies:
                reply_action = None if reply is None else action(ref, reply)
                key = name, rid, own, reply_action
                require(key in index, 'Missing legal reference fork')
                i = index.pop(key); fork = forks[i]
                if reply is None:
                    h2id = None; value = -nodes[h1_id]['value']; zero = state.player*ref.terminal(child)
                else:
                    leaf = ref.transition(child, reply); h2id = node_id(name, ref, leaf)
                    outcome = ref.terminal(leaf)
                    value = nodes[h2id]['value']; zero = 0. if outcome is None else state.player*outcome
                    tree['nodes'] += 1; tree['neural_leaf_candidates'] += outcome is None
                tree['leafcount'] += 1
                require(fork['node_ids'] == [source_id, h1_id, h2id], 'Reference transition differs from stored target')
                require(nodes[h1_id]['state']['player'] == -state.player, 'H1 player sign mismatch')
                if h2id is not None: require(nodes[h2id]['state']['player'] == state.player, 'H2 player sign mismatch')
                reached.update(nid for nid in fork['node_ids'] if nid is not None)
                ids.append(i); h2ids.append(h2id); reply_actions.append(reply_action); values.append(value); zeros.append(zero)
            valid = sum(i is not None for i in h2ids)
            terminal_rows = sum(i is not None and nodes[i]['terminal'] for i in h2ids)
            groups.append({'game': name, 'root_id': rid, 'own_action': own, 'source_id': source_id, 'h1_id': h1_id,
                           'h2_ids': h2ids, 'fork_indices': ids, 'reply_actions': reply_actions, 'row_count': len(ids),
                           'h1_terminal': terminal, 'h2_valid_rows': valid, 'h2_terminal_rows': terminal_rows,
                           'h2_nonterminal_rows': valid-terminal_rows})
            tree['zero_estimates'].append(min(zeros))
            if terminal or valid == terminal_rows: tree['terminal_branches'][own] = min(zeros)
            if split == 'development':
                require(min(values) == root['oracle_values'][root['actions'].index(own)], 'Stored own-action oracle disagrees with closure labels')
        root_trees[name, rid] = tree
    require(not index and reached == set(nodes), 'Extra forks or nodes outside complete legal closure')
    groups.sort(key=lambda g: (g['game'], g['root_id'], g['own_action']))
    totals = inventory(groups); totals['games'] = {g: inventory([a for a in groups if a['game'] == g]) for g in GAMES}
    receipt = {'version': 'complete-legal-reply-groups-v25.0', 'split': split,
               'dataset_fingerprint': dataset['manifest']['dataset_fingerprint'], 'groups': groups, 'inventory': totals}
    receipt['group_sha256'] = digest(receipt)
    return receipt, root_trees, canonical, dict(counts)


def replay(grouping, seed, epoch):
    """Independent namespace and complete-group/symmetry schedule reconstruction."""
    import numpy as np
    by_game = defaultdict(lambda: defaultdict(list)); groups = grouping['groups']
    for i, group in enumerate(groups): by_game[group['game']][group['root_id']].append(i)
    maximum = max(len(v) for v in by_game.values())
    rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2501])); draws = []; games = {}
    for game in sorted(by_game):
        roots = sorted(by_game[game]); root_indices = rng.permutation(len(roots)).tolist()
        root_indices += rng.integers(len(roots), size=maximum-len(roots)).tolist()
        for i in root_indices:
            choices = by_game[game][roots[i]]
            draws += [choices[int(j)] for j in rng.integers(len(choices), size=4)]
        games[game] = {'unique_roots': len(roots), 'root_draws': maximum,
                       'repeated_root_draws': maximum-len(roots), 'group_draws': 4*maximum}
    indices = np.asarray(draws, dtype=np.int64); rng.shuffle(indices)
    sym = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2511]))
    transforms = np.asarray([sym.integers(2 if groups[int(i)]['game'] == GAMES[0] else 8) for i in indices], dtype=np.int64)
    selected = [groups[int(i)] for i in indices]
    totals = inventory(selected)
    for game in games:
        games[game].update({k: v for k, v in inventory([g for g in selected if g['game'] == game]).items() if k not in ('roots', 'groups')})
    counts = Counter(f"{g['game']}/{int(t)}" for g, t in zip(selected, transforms))
    receipt = {'version': 'complete-group-plan-v25.0', 'seed': seed, 'epoch': epoch,
               'sampler_namespace': 2501, 'symmetry_namespace': 2511, 'group_sha256': grouping['group_sha256'],
               'groups_per_root': 4, 'group_draws': len(indices), 'unique_groups': len(set(indices.tolist())),
               'group_index_sha256': hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest(),
               'transform_sha256': hashlib.sha256(transforms.astype('<i8').tobytes()).hexdigest(),
               'transform_counts': dict(sorted(counts.items())), 'games': games,
               **{k: v for k, v in totals.items() if k not in ('roots', 'groups')}}
    receipt['plan_sha256'] = digest(receipt)
    return receipt


def checkpoint(path, config, receipt):
    import numpy as np
    shapes = {'e1w': (198, 128), 'e1b': (128,), 'e2w': (128, 64), 'e2b': (64,),
              'pw': (64, 65), 'pb': (65,), 'vw': (64, 1), 'vb': (1,),
              'g1w': (129, 50), 'g1b': (50,), 'g2w': (50, 64), 'g2b': (64,),
              'dw': (64, 198), 'db': (198,)}
    expected = {p+k: shape for p in ('p_', 'm_', 'v_') for k, shape in shapes.items()}
    expected.update({'t_'+k: shapes[k] for k in ('e1w', 'e1b', 'e2w', 'e2b', 'vw', 'vb')})
    hashes = {}
    with np.load(path, allow_pickle=False) as file:
        metadata = json.loads(str(file['metadata']))
        require(set(file.files) == set(expected) | {'metadata'} and len(expected) == 48, 'Checkpoint tensor inventory mismatch')
        require(metadata['config'] == config and metadata['identity'] == receipt['identity']
                and metadata['step'] == receipt['step'] == 10560 and metadata['epoch'] == receipt['epoch'] == 160,
                'Checkpoint source/config/data/counter mismatch')
        for name, shape in expected.items():
            value = file[name]
            require(value.shape == shape and value.dtype == np.float64 and np.isfinite(value).all(), 'Invalid tensor '+name)
            if name.startswith('v_'): require(np.all(value >= 0), 'Negative Adam second moment')
            hashes[name] = hashlib.sha256(value.tobytes()).hexdigest()
        head = float(np.linalg.norm(file['p_vw']))
        require(hashes == metadata['array_hashes'] and digest(hashes) == receipt['tensor_sha256'], 'Tensor hash inventory differs')
    return hashes, head


def decisions(rows, roots, trees, variant, tracks=('exact', 'hybrid'), zero=False):
    """Validate saved actions and independently enumerate reference tree counters."""
    import numpy as np
    require([(r['game'], r['root_id'], r['track']) for r in rows]
            == [(r['game'], r['root_id'], t) for r in roots for t in tracks], 'Decision schedule mismatch')
    mapping, totals = {}, Counter()
    for root in roots:
        key = root['game'], root['root_id']; tree = trees[key]
        for track in tracks:
            row = rows[len(mapping)]; mapping[*key, track] = row
            require(row['status'] == 'complete' and row['reason'] is None and row['split'] == 'development'
                    and row['trajectory'] == root['trajectory'] and row['beyond_depth'] == root['beyond_depth'], 'Incomplete/foreign decision')
            estimates = row['action_estimates']; truth = root['oracle_values']
            require(len(estimates) == len(root['actions']) and all(finite(v) and abs(v) <= 1+1e-12 for v in estimates), 'Invalid saved estimates')
            selected = int(np.argmax(estimates)); regret = max(truth)-truth[selected]
            require(row['action'] == root['actions'][selected] and row['regret'] == regret
                    and row['optimal'] is (regret == 0) and row['oracle_gap'] == max(truth)-min(truth), 'Saved action/regret/oracle mismatch')
            require(finite(row['seconds']) and 0 <= row['seconds'] < 1., 'Censored/invalid completed time')
            require(row['nodes'] == row['transitions'] == tree['nodes'] <= 4096
                    and row['leafcount'] == tree['leafcount'] and row['neural_leaf_candidates'] == tree['neural_leaf_candidates'],
                    'Saved tree counters differ from independent bitboard tree')
            for a, value in tree['terminal_branches'].items():
                close(estimates[root['actions'].index(a)], value, 'Terminal override changed')
            if zero: require(estimates == tree['zero_estimates'], 'Model-free baseline differs from reference tree')
            n = tree['neural_leaf_candidates']; recurrent = track == 'hybrid' and variant != 'direct'
            expected = dict.fromkeys(('encoder_calls', 'encoder_states', 'rollout_calls', 'predictor_steps', 'value_calls', 'value_states'), 0)
            if n and not zero:
                expected.update(encoder_calls=1, encoder_states=1 if recurrent else n,
                                rollout_calls=int(recurrent), predictor_steps=2*n if recurrent else 0,
                                value_calls=1, value_states=n)
            require(row['neural_leaves'] == (0 if zero else n) and row['neuralcounts'] == expected, 'Independent neural accounting mismatch')
            totals['decisions'] += 1; totals['transition_nodes'] += tree['nodes']; totals['neural_leaves'] += row['neural_leaves']
    return mapping, dict(totals)


def stats(values):
    import numpy as np
    x = np.asarray(values, dtype=np.float64)
    return {'count': len(x), 'mean': float(x.mean()) if len(x) else None,
            'max': float(x.max()) if len(x) else None,
            'quantiles_0_25_50_75_100': np.quantile(x, [0, .25, .5, .75, 1]).tolist() if len(x) else None}


def same_numeric(actual, expected, message):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), message+' keys')
        for key in expected: same_numeric(actual[key], expected[key], message+'/'+key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), message+' length')
        for i, value in enumerate(expected): same_numeric(actual[i], value, message+'/'+str(i))
    elif expected is None or isinstance(expected, bool): require(actual == expected, message)
    else: close(actual, expected, message)


def diagnostic_arithmetic(receipt, dev, grouping, mapping, head):
    direct = receipt['config']['variant'] == 'direct'; detail = receipt['diagnostics']; nodes = dev['nodes']
    require(detail['stage'] == 'development' and detail['collapse'] is False, 'Collapsed/foreign diagnostics')
    close(detail['head_norm'], head, 'Head norm differs from checkpoint')
    roots = {r['root_id']: r for r in dev['roots']}; checked = 0
    for game in GAMES:
        item = detail['games'][game]; groups = [g for g in grouping['groups'] if g['game'] == game]
        require(item['group_count'] == len(item['groups']) == len(groups), 'Diagnostic group inventory mismatch')
        geometry = item['unique_node_geometry']; actual_nodes = [n for n in nodes.values() if n['game'] == game]
        require(geometry['samples'] == len(actual_nodes) and geometry['dimensions'] == 64
                and geometry['effective_rank'] >= 2 and geometry['median_std'] >= .001
                and item['collapse'] is False, 'Invalid unique-node collapse inventory')
        occurrence = receipt['representation'][game]
        fork_ids = [i for i, f in enumerate(dev['forks']) if f['game'] == game]
        ids = [nid for i in fork_ids for nid in dev['forks'][i]['node_ids'] if nid is not None]
        nt = sum(not nodes[n]['terminal'] for n in ids)
        require(occurrence['forks'] == len(fork_ids) and occurrence['samples'] == len(ids)
                and occurrence['policy_samples'] == nt and occurrence['terminal_samples'] == len(ids)-nt
                and occurrence['missing_states'] == 3*len(fork_ids)-len(ids)
                and occurrence['unprojected']['samples'] == len(ids), 'Occurrence weighting/counts mismatch')
        expected_horizon_counts = {'1': len(fork_ids), '2': sum(dev['forks'][i]['node_ids'][2] is not None for i in fork_ids)}
        require(set(occurrence['horizons']) == (set() if direct else {'1', '2'}), 'Occurrence horizon inventory mismatch')
        for h, record in occurrence['horizons'].items():
            require(record['samples'] == expected_horizon_counts[h] and finite(record['online_latent_mse'])
                    and record['online_latent_mse'] >= 0, 'Occurrence horizon counts/MSE mismatch')
        for row, group in zip(item['groups'], groups):
            checked += 1; root = roots[group['root_id']]
            action_index = root['actions'].index(group['own_action']); oracle = root['oracle_values'][action_index]
            require((row['root_id'], row['own_action'], row['full_fork_rows'])
                    == (group['root_id'], group['own_action'], group['row_count']) and row['oracle_action_value'] == oracle,
                    'Diagnostic action/oracle binding mismatch')
            for h in (1, 2):
                report = row['horizons'][str(h)]
                candidates = [group['h1_id']] if h == 1 else group['h2_ids']
                valid = [nid for nid in candidates if nid is not None]; nonterminal = [nid for nid in valid if not nodes[nid]['terminal']]
                expected = {'valid_count': len(valid), 'missing_count': len(candidates)-len(valid),
                            'terminal_count': len(valid)-len(nonterminal), 'nonterminal_count': len(nonterminal)}
                require(all(report[k] == v for k, v in expected.items()), 'Diagnostic horizon mask/counter mismatch')
                epsilon = report['target_oracle_max_absolute']; n = len(nonterminal)
                require(finite(epsilon) and 0 <= epsilon <= 2, 'Invalid target/oracle maximum')
                target_mse = report['target_value_oracle_mse']
                if n:
                    require(finite(target_mse) and epsilon**2/n-1e-10 <= target_mse <= epsilon**2+1e-10,
                            'Target maximum/MSE inconsistency')
                else:
                    require(target_mse is None and epsilon == 0, 'Empty target mask metrics fabricated')
                keys = ('latent_mean', 'latent_max', 'latent_mean_max', 'predicted_value_oracle_mse')
                if not n or direct:
                    require(all(report[k] is None for k in keys), 'Missing/direct latent measurement fabricated')
                else:
                    mean, maximum, combined = (report[k] for k in keys[:3])
                    require(all(finite(v) for v in (mean, maximum, combined)) and 0 <= mean <= maximum+1e-10
                            and maximum/n-1e-10 <= mean and maximum <= 4+1e-10, 'Latent mean/max normalization mismatch')
                    close(combined, .5*(mean+maximum), 'Half mean/max arithmetic mismatch')
                    require(finite(report['predicted_value_oracle_mse']) and 0 <= report['predicted_value_oracle_mse'] <= 4+1e-10,
                            'Invalid predicted utility MSE')
            target, pred = row['target_min'], row['predicted_min']; h2 = row['horizons']['2']
            epsilon = h2['target_oracle_max_absolute']; j = h2['latent_mean_max'] or 0.
            require(finite(target) and abs(target) <= 1+1e-12, 'Invalid target minimum')
            close(row['target_min_oracle_bias'], target-oracle, 'Target minimum bias arithmetic')
            require(abs(target-oracle) <= epsilon+1e-9, 'Target minimum exceeds worst target/oracle error')
            if direct:
                require(all(row[k] is None for k in ('predicted_min', 'predicted_min_oracle_bias', 'predicted_target_min_error',
                                                     'conditional_oracle_bound', 'false_pessimistic_noncritical_reply')),
                        'Direct has fabricated recurrent diagnostic')
            else:
                require(finite(pred), 'Missing predicted minimum')
                close(pred, mapping[game, root['root_id'], 'hybrid']['action_estimates'][action_index],
                      'Diagnostic backed-up action differs from saved hybrid estimate')
                close(row['predicted_min_oracle_bias'], pred-oracle, 'Predicted minimum bias arithmetic')
                close(row['predicted_target_min_error'], pred-target, 'Predicted/target discrepancy arithmetic')
                bound = head*math.sqrt(128*j)+epsilon
                close(row['conditional_oracle_bound'], bound, 'Conditional bound normalization mismatch')
                require(abs(pred-oracle) <= bound+1e-9*max(1., bound), 'Conditional oracle bound violated')
                require(type(row['false_pessimistic_noncritical_reply']) is bool, 'Invalid false-pessimism flag')
            if group['h1_terminal']:
                close(target, -nodes[group['h1_id']]['value'], 'Terminal H1 target perspective mismatch')
        expected_summary = {}
        for key in ('target_min_oracle_bias', 'predicted_min_oracle_bias', 'predicted_target_min_error', 'conditional_oracle_bound'):
            values = [row[key] for row in item['groups'] if row[key] is not None]
            expected_summary[key] = stats(values)
            if 'bias' in key or 'error' in key: expected_summary[key+'_squared'] = stats([v*v for v in values])
        for h in ('1', '2'):
            for key in ('latent_mean', 'latent_max', 'latent_mean_max', 'target_value_oracle_mse', 'target_oracle_max_absolute', 'predicted_value_oracle_mse'):
                expected_summary['h'+h+'_'+key] = stats([row['horizons'][h][key] for row in item['groups'] if row['horizons'][h][key] is not None])
        same_numeric(item['summary'], expected_summary, 'Diagnostic summary')
        require(item['false_pessimistic_count'] == (None if direct else sum(row['false_pessimistic_noncritical_reply'] for row in item['groups'])),
                'False-pessimism aggregate count mismatch')
    return checked


def selected_analysis(cells, roots, report, deadline):
    """Independent saved-action aggregation, rate choice, bootstrap and gates."""
    import numpy as np
    rows = {(c['config']['variant'], c['config']['learning_rate'], c['config']['seed']):
            {(r['game'], r['root_id'], r['track']): r for r in c['scores']} for c in cells}
    values = {}
    for variant in VARIANTS:
        for rate in RATES:
            for track in ('exact', 'hybrid'):
                arrays, mse = {}, {}
                for game in GAMES:
                    subset = [r for r in roots if r['game'] == game]
                    arrays[game] = np.array([[rows[variant, rate, seed][game, root['root_id'], track]['regret'] for root in subset] for seed in SEEDS])
                    mse[game] = np.array([[np.mean((np.array(rows[variant, rate, seed][game, root['root_id'], track]['action_estimates'])
                                                  -root['oracle_values'])**2) for root in subset] for seed in SEEDS])
                values[variant, rate, track] = arrays, mse
    chosen = {}
    for variant in VARIANTS:
        means = {rate: float(np.mean([a.mean() for a in values[variant, rate, 'exact'][0].values()])) for rate in RATES}
        best = min(means.values()); chosen[variant] = min(rate for rate in RATES if abs(means[rate]-best) <= 1e-12)
        require(report['selected'][variant]['learning_rate'] == chosen[variant], 'Independent EXACT LR selection mismatch')
        for track in ('exact', 'hybrid'):
            arrays, mse = values[variant, chosen[variant], track]
            saved = report['selected'][variant]['tracks'][track]
            close(saved['mean_regret'], float(np.mean([a.mean() for a in arrays.values()])), 'Equal-game regret aggregation mismatch')
            close(saved['action_oracle_mse'], float(np.mean([a.mean() for a in mse.values()])), 'Root-action MSE aggregation mismatch')
    controls = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail'); passed = {}
    ablation_pass = False
    for ti, track in enumerate(('exact', 'hybrid')):
        guard(deadline)
        candidate = values['raw-tail', chosen['raw-tail'], track][0]
        # Root draws are shared across fixed seeds, and across all comparisons.
        rng = np.random.default_rng(np.random.SeedSequence([2505, ti]))
        draws = {g: np.empty((10000, candidate[g].shape[1]), dtype=np.int64) for g in GAMES}
        for i in range(10000):
            for game in GAMES: draws[game][i] = rng.integers(candidate[game].shape[1], size=candidate[game].shape[1])
        names = controls + (('raw-mean', 'raw-scaled') if track == 'hybrid' else ())
        independent = {}
        for name in names:
            delta = {g: values[name, chosen[name], track][0][g]-candidate[g] for g in GAMES}
            pergame = {g: float(d.mean()) for g, d in delta.items()}
            perseed = np.mean([d.mean(1) for d in delta.values()], axis=0)
            bootstrap = np.stack([delta[g].mean(0)[draws[g]].mean(1) for g in GAMES], axis=1)
            comparison = (report['tracks'][track]['comparisons'][name] if name in controls else report['mechanism']['ablations'][name])
            close(comparison['aggregate_improvement'], float(np.mean(list(pergame.values()))), 'Paired aggregate effect mismatch')
            same_numeric(comparison['per_game_improvement'], pergame, 'Per-game effect')
            same_numeric(comparison['per_seed_improvement'], dict(zip(map(str, SEEDS), perseed.tolist())), 'Paired-seed effect')
            same_numeric(comparison['bootstrap']['aggregate_ci95'], np.quantile(bootstrap.mean(1), [.025, .975]).tolist(), 'Independent paired-root CI')
            same_numeric(comparison['bootstrap']['per_game_ci95'],
                         {g: np.quantile(bootstrap[:, j], [.025, .975]).tolist() for j, g in enumerate(GAMES)}, 'Per-game paired-root CI')
            require(comparison['bootstrap']['replicates'] == 10000 and comparison['bootstrap']['seed_sequence'] == [2505, ti], 'Bootstrap namespace/draws changed')
            positive = all(v > 0 for v in pergame.values()) and int(np.sum(perseed > 0)) >= 2
            require(comparison['favorable_seeds'] == int(np.sum(perseed > 0)), 'Paired seed count differs')
            independent[name] = float(np.mean(list(pergame.values()))), positive
        strongest_margin = min(independent[name][0] for name in controls)
        passed[track] = strongest_margin >= .05 and all(independent[name][1] for name in controls)
        require(report['tracks'][track]['passed'] == passed[track], 'Independent primary comparator gate mismatch')
        if track == 'hybrid': ablation_pass = all(independent[v][1] for v in ('raw-mean', 'raw-scaled'))
    candidate_mse = float(np.mean([a.mean() for a in values['raw-tail', chosen['raw-tail'], 'hybrid'][1].values()]))
    mse_pass = True
    for name in controls[1:]:
        baseline_mse = float(np.mean([a.mean() for a in values[name, chosen[name], 'hybrid'][1].values()]))
        close(report['mechanism']['action_oracle_mse'][name]['improvement'], baseline_mse-candidate_mse, 'Mechanism MSE effect mismatch')
        mse_pass &= baseline_mse > candidate_mse
    mechanism = passed['hybrid'] and ablation_pass and mse_pass
    require(report['mechanism']['passed'] == mechanism, 'Independent mechanism gate mismatch')
    status = ('development_screen_passed' if passed['exact'] and mechanism else
              'exploratory_hybrid_only' if mechanism else 'not_promoted')
    require(report['status'] == status and report['candidate'] == 'raw-tail', 'Independent status/candidate mismatch')
    return {'rates': chosen, 'exact_gate': passed['exact'], 'hybrid_gate': passed['hybrid'],
            'mechanism_gate': mechanism, 'status': status, 'bootstrap_draws_per_track': 10000,
            'bootstrap_seeds_fixed': list(SEEDS)}


def audit(grid, training, development, deadline, expected_commit):
    import numpy as np
    from two_player_v22.data import load_dataset, verify_bytes
    from two_player_v25r.report import summarize_grid
    from two_player_v25.model import Model
    ledger = read(grid/'ledger.json'); initial_sha = sha(grid/'ledger.json')
    require(ledger['status'] == 'complete' and ledger['failures'] == [] and len(ledger['runs']) == 42,
            'Grid is not complete; do not inspect partial metrics')
    source = source_check(ledger, deadline, expected_commit)
    require(sha(ROOT/REFERENCE_PATH) == REFERENCE_SHA, 'Pre-retry numerical references changed')
    references = read(ROOT/REFERENCE_PATH)
    require(references['frozen_commit'] == ORIGINAL_COMMIT and references['training_dataset_fingerprint'] == TRAIN_FP
            and references['original_ledger_sha256'] == 'f60386efffe3a5de03ee22075b1af4418768944ddab98b4a2f864b05a6a2f0e5',
            'Prior failed-attempt reference provenance mismatch')
    reference_cells = {row['id']: row for row in references['records']}
    require(len(reference_cells) == len(references['records']) == 4, 'Incomplete four-cell neutral-repair reference inventory')
    matched_references = []
    # Fail loudly if future report/loader changes accidentally cross the audit
    # boundary. Model construction/checkpoint deserialization are allowed.
    def forbidden(*_args, **_kwargs): raise AssertionError('Audit forbids model inference, optimization and parent-bank loading')
    with ExitStack() as stack:
        for name in ('encode', 'rollout', 'value', 'policy_logits', 'update', 'loss_grad'):
            stack.enter_context(patch.object(Model, name, forbidden))
        stack.enter_context(patch('two_player_v22.data.parent_load', forbidden))
        stack.enter_context(patch('two_player_v2.data.load_dataset', forbidden))
        train, dev = load_dataset(training, 'train'), load_dataset(development, 'development')
        require(train['manifest'] == ledger['train_manifest'] and dev['manifest'] == ledger['development_manifest'], 'Standalone/ledger manifest mismatch')
        require(train['manifest']['dataset_fingerprint'] == TRAIN_FP and dev['manifest']['dataset_fingerprint'] == DEV_FP,
                'Unfrozen standalone inputs')
        rebuilt_train, _, train_keys, train_counts = legal_closure(train, deadline)
        rebuilt_dev, trees, dev_keys, dev_counts = legal_closure(dev, deadline)
        require(not train_keys.intersection(dev_keys), 'Train/development canonical closure state overlap')
        require(not {(r['game'], r['trajectory']) for r in train['roots']}.intersection((r['game'], r['trajectory']) for r in dev['roots']),
                'Train/development trajectory overlap')
        require(read(grid/'train-groups.json') == rebuilt_train and read(grid/'development-groups.json') == rebuilt_dev,
                'Independent reference complete-group reconstruction mismatch')
        truth = {'roots': [{k: root[k] for k in ('game', 'root_id', 'trajectory', 'actions', 'oracle_values', 'beyond_depth')} for root in dev['roots']],
                 'unique_node_counts': {g: sum(n['game'] == g for n in dev['nodes'].values()) for g in GAMES},
                 'development_fingerprint': DEV_FP}
        require(truth == ledger['development_truth'] and digest(truth) == ledger['development_truth_sha256'], 'Embedded truth differs from actual standalone')
        plans = {}
        for seed in SEEDS:
            for epoch in range(160):
                guard(deadline); plans[seed, epoch] = replay(rebuilt_train, seed, epoch)
        controls = read(grid/'controls.json'); control_count = 0
        _, counts = decisions(controls['zero'], dev['roots'], trees, 'direct', ('exact',), zero=True)
        control_count += counts['decisions']
        for seed in SEEDS:
            _, counts = decisions(controls['untrained'][str(seed)], dev['roots'], trees, 'direct', ('exact',))
            control_count += counts['decisions']
        cells, hashes, summaries = [], {}, []; epoch_count = array_count = diagnostic_count = decision_count = 0
        expected_cells = {(v, lr, s) for v in VARIANTS for lr in RATES for s in SEEDS}; seen = set()
        for item in ledger['runs']:
            guard(deadline); config = item['config']; key = config['variant'], config['learning_rate'], config['seed']
            require(key in expected_cells and key not in seen and item['status'] == 'complete', 'Unexpected/duplicate/incomplete cell')
            seen.add(key); directory = grid/item['id']; receipt = read(directory/'receipt.json')
            for name in ('checkpoint.npz', 'history.json', 'budget.json', 'receipt.json'):
                hashes[item['id']+'/'+name] = sha(directory/name)
            require(hashes[item['id']+'/receipt.json'] == item['receipt_sha256'] and
                    hashes[item['id']+'/checkpoint.npz'] == item['checkpoint_sha256'] == receipt['checkpoint_sha256'] and
                    hashes[item['id']+'/history.json'] == receipt['history_sha256'], 'Cell byte checksum mismatch')
            tensor_hashes, head = checkpoint(directory/'checkpoint.npz', config, receipt); array_count += len(tensor_hashes)
            if item['id'] in reference_cells:
                ref = reference_cells[item['id']]
                require(ref['config'] == config and (ref['epoch'], ref['step']) == (160, 10560)
                        and ref['array_hashes'] == tensor_hashes and ref['tensor_inventory_sha256'] == digest(tensor_hashes),
                        'Engineering repair changed numerical training result: '+item['id'])
                matched_references.append(item['id'])
            history = read(directory/'history.json'); require(len(history) == 160, 'Missing epoch history')
            for epoch, row in enumerate(history):
                require(row['epoch'] == epoch+1 and row['step'] == 66*(epoch+1) and row['steps'] == 66,
                        'History epoch/optimizer counter mismatch')
                require(row['schedule'] == plans[config['seed'], epoch], 'Independent sampling/augmentation replay differs')
                epoch_count += 1
            mapping, counts = decisions(receipt['scores'], dev['roots'], trees, config['variant'])
            decision_count += counts['decisions']
            diagnostic_count += diagnostic_arithmetic(receipt, dev, rebuilt_dev, mapping, head)
            cells.append(receipt)
            summaries.append({'id': item['id'], 'config': config, 'seconds': item['seconds'],
                              'checkpoint_sha256': item['checkpoint_sha256'], 'history_sha256': receipt['history_sha256'],
                              'head_norm': head, 'decision_counts': counts})
        require(seen == expected_cells and (array_count, epoch_count, decision_count, control_count) == (2016, 6720, 17556, 836),
                'Postrun audit completeness mismatch')
        require(set(matched_references) == set(reference_cells), 'A prior checkpoint configuration was not reproduced')
        guard(deadline); report = summarize_grid(grid); guard(deadline)
        require(report['verification_errors'] == [] and report['status'] != 'inconclusive', 'Strict reporter failed: '+repr(report['verification_errors']))
        selection = selected_analysis(cells, dev['roots'], report, deadline)
        for name in ('ledger.json', 'controls.json', 'train-groups.json', 'development-groups.json'): hashes[name] = sha(grid/name)
        actual_files = {p.relative_to(grid).as_posix() for p in grid.rglob('*') if p.is_file()}
        require(actual_files == set(hashes) and len(hashes) == 172, 'Unexpected/missing grid files')
        require(initial_sha == sha(grid/'ledger.json') and all(sha(grid/name) == value for name, value in hashes.items()), 'Artifacts changed during audit')
        require(verify_bytes(training)[0] == train['manifest'] and verify_bytes(development)[0] == dev['manifest'], 'Standalone bytes changed during audit')
        source_check(ledger, deadline, expected_commit)
    return {'status': 'verified', 'source': source, 'ledger_sha256': initial_sha,
            'artifact_inventory_sha256': digest(hashes), 'strict_report_sha256': digest(report),
            'data': {split: {'dataset_fingerprint': data['manifest']['dataset_fingerprint'],
                            'manifest_sha256': sha(path/'manifest.json'), 'payload_sha256': sha(path/'data.json'),
                            'parent_dataset_fingerprint': data['manifest']['parent_dataset_fingerprint'],
                            'group_sha256': groups['group_sha256'], 'reference_counts': counts}
                     for split, data, path, groups, counts in (('train', train, training, rebuilt_train, train_counts),
                                                              ('development', dev, development, rebuilt_dev, dev_counts))},
            'counts': {'cells': 42, 'checkpoints': 42, 'tensor_arrays': array_count, 'histories': epoch_count,
                       'plans_replayed': len(plans), 'group_draws_in_unique_plans': sum(p['group_draws'] for p in plans.values()),
                       'fork_rows_in_unique_plans': sum(p['fork_rows'] for p in plans.values()),
                       'learned_decisions': decision_count, 'control_decisions': control_count,
                       'diagnostic_groups': diagnostic_count, 'artifact_files': len(hashes),
                       'canonical_train_development_overlap': 0, 'trajectory_overlap': 0, 'failures': 0, 'censors': 0, 'collapse': 0},
            'sampling_hashes_by_seed': {str(s): digest([plans[s, e] for e in range(160)]) for s in SEEDS},
            'selection_verification': selection, 'selected': report['selected'], 'tracks': report['tracks'], 'mechanism': report['mechanism'],
            'neutral_repair_replay': {'reference_path': REFERENCE_PATH, 'reference_file_sha256': REFERENCE_SHA,
                                     'matched_cells': matched_references, 'matched_tensor_hashes': 192,
                                     'prior_failed_attempt_seconds': 496.25913929991657,
                                     'combined_attempt_cell_seconds': report['resources']['total_cell_seconds']+496.25913929991657},
            'resources': report['resources'], 'cells': summaries,
            'new_predictions': 0, 'optimizer_updates': 0, 'protected_artifacts_opened': 0,
            'limitations': ['Internal bitboard reference is independently implemented in this project, not a third-party referee.',
                            'Saved geometry/latent errors and per-reply false-pessimism flags are not remeasured; their counts and arithmetic are checked.',
                            'Prior exclusions beyond the two standalone exports are provenance-bound to previous audits, not reloaded here.',
                            'Adaptive reused development evidence; no confirmatory superiority, transfer, equilibrium or publication claim.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('grid', 'full_training', 'development', 'output'): parser.add_argument(name, type=Path)
    parser.add_argument('--expected-commit', required=True, help='Explicit 40-character repaired grid launch commit')
    args = parser.parse_args()
    require(os.environ.get('OPENBLAS_NUM_THREADS') == os.environ.get('OMP_NUM_THREADS') == '1', 'Set one BLAS/OMP thread before Python')
    grid, train, dev, output = (getattr(args, name).resolve() for name in ('grid', 'full_training', 'development', 'output'))
    require(not output.exists() and output.suffix.lower() == '.json', 'Output must be a new JSON file')
    require(all(not output.is_relative_to(path) for path in (grid, train, dev)), 'Output must be outside all input artifacts')
    started = time.perf_counter()
    result = {'version': 'v25-independent-postrun-audit01', 'status': 'inconclusive', 'script_sha256': sha(__file__),
              'grid': str(grid), 'full_training': str(train), 'development': str(dev),
              'expected_commit': args.expected_commit, 'errors': []}
    try:
        result.update(audit(grid, train, dev, started+600., args.expected_commit))
    except (ValueError, KeyError, TypeError, IndexError, AssertionError, OSError, TimeoutError, subprocess.SubprocessError) as exc:
        result['errors'].append(f'{type(exc).__name__}: {exc}')
    result['audit_seconds'] = time.perf_counter()-started
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'status': result['status'], 'errors': result['errors'], 'output': str(output)}))
    return 0 if result['status'] == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
