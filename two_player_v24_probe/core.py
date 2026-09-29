"""Outcome-blind H1 packing and frozen-model additive-order measurements."""
from collections import Counter
from dataclasses import asdict
import hashlib
from itertools import combinations
import json

import numpy as np

from two_player_v2 import GAMES_V2
from two_player_v2.data import state_from

BATCH_SIZE = 128
QUANTILES = (0., .25, .5, .75, 1.)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _training(train):
    m = train['manifest']
    require(m['split'] == 'train' and m['role'] == 'redacted-training' and m['fraction'] == 1.,
            'Probe requires full standalone training data')
    require(train['roots'] and train['forks'], 'Empty training artifact')
    require(all(r['split'] == 'train' for r in train['roots'])
            and all(f['split'] == 'train' for f in train['forks']), 'Nontraining records')
    require(all(n['value_labelled'] is True for n in train['nodes'].values()), 'Hidden value label in probe')


def build_schedule(train, guard):
    """Select disjoint quadruples using identities only, before model loading."""
    guard(); _training(train)
    roots = {r['root_id']: r for r in train['roots']}
    require(len(roots) == len(train['roots']), 'Duplicate root identity')
    grouped = {}
    for i, fork in enumerate(train['forks']):
        if i % BATCH_SIZE == 0: guard()
        rid = fork['root_id']; root = roots[rid]; game = root['game']
        require(game in GAMES_V2 and fork['game'] == game, 'Fork game mismatch')
        source_id, target_id = fork['node_ids'][:2]
        require(source_id is not None and target_id is not None, 'Missing H1 edge')
        source, target = train['nodes'][source_id], train['nodes'][target_id]
        action = fork['actions'][0]
        require(type(action) is int and 0 <= action < 65 and source['game'] == target['game'] == game
                and source['state'] == root['state'], 'Inconsistent H1 source/action identity')
        value = target['value']
        require(type(value) in (int, float) and np.isfinite(value) and abs(value) <= 1
                and type(target['terminal']) is bool, 'Invalid successor value/terminal metadata')
        edge = {'root_id': rid, 'player': source['state']['player'], 'action': action,
                'source_id': source_id, 'target_id': target_id, 'target_player': target['state']['player'],
                'target_value': value, 'target_terminal': target['terminal']}
        key = (rid, action)
        old = grouped.setdefault(game, {}).get(key)
        if old is not None:
            require(old == edge, 'Repeated H1 target disagrees across replies')
            continue
        adapter = GAMES_V2[game]; state = state_from(source['state'])
        require(set(root['actions']) == set(source['legal']) == set(adapter.legal_actions(state)), 'Incomplete legal H1 action list')
        actual = adapter.transition(state, action)
        require(actual == state_from(target['state']) and target['terminal'] == (adapter.terminal(actual) is not None)
                and edge['target_player'] == -edge['player'], 'Recorded H1 transition/turn/terminal is invalid')
        if target['terminal']:
            require(value == adapter.terminal(actual)*actual.player, 'Terminal value perspective mismatch')
        grouped[game][key] = edge
    result = {'version': 'v24-order-schedule01', 'edge_order': ['s1a', 's2a', 's1b', 's2b'], 'games': {}}
    for game in sorted(grouped):
        guard(); edges = [v for _, v in sorted(grouped[game].items())]
        index = {(e['root_id'], e['action']): i for i, e in enumerate(edges)}
        actions = {rid: sorted(a for r, a in index if r == rid) for rid in sorted(roots) if roots[rid]['game'] == game}
        require(all(set(aa) == set(roots[r]['actions']) for r, aa in actions.items()), 'Missing recorded legal H1 edge')
        candidates, eligible = [], 0
        for n, (r1, r2) in enumerate(combinations(sorted(actions), 2)):
            if n % BATCH_SIZE == 0: guard()
            if roots[r1]['state']['player'] != roots[r2]['state']['player']: continue
            common = sorted(set(actions[r1]) & set(actions[r2]))
            if len(common) < 2: continue
            eligible += 1
            for a, b in combinations(common, 2):
                identity = [2401, game, r1, r2, a, b]
                candidates.append((digest(identity), tuple(identity)))
                if len(candidates) % BATCH_SIZE == 0: guard()
        guard(); candidates.sort(); guard()
        used, blocks = set(), []
        terminal_counts = {str(i): 0 for i in range(5)}
        for n, (checksum, identity) in enumerate(candidates):
            if n % BATCH_SIZE == 0: guard()
            _, _, r1, r2, a, b = identity
            ids = [index[r1, a], index[r2, a], index[r1, b], index[r2, b]]
            if any(i in used for i in ids): continue
            used.update(ids)
            terminals = sum(edges[i]['target_terminal'] for i in ids)
            terminal_counts[str(terminals)] += 1
            blocks.append({'identity': list(identity), 'sha256': checksum, 'edges': ids, 'terminal_count': terminals})
        nt_edges = sum(not e['target_terminal'] for e in edges)
        nt_blocks = terminal_counts['0']
        counts = {'roots': len(actions), 'eligible_root_pairs': eligible, 'candidate_blocks': len(candidates),
                  'selected_blocks': len(blocks), 'total_h1_edges': len(edges), 'used_edges': len(used),
                  'used_fraction': len(used)/len(edges), 'terminal_block_counts': terminal_counts,
                  'nonterminal_blocks': nt_blocks, 'all_nonterminal_edges': nt_edges,
                  'used_nonterminal_edges': 4*nt_blocks,
                  'nonterminal_used_fraction': 4*nt_blocks/nt_edges if nt_edges else None}
        result['games'][game] = {'edges': edges, 'blocks': blocks, 'counts': counts,
                                 'edge_sha256': digest(edges), 'block_sha256': digest(blocks)}
        guard()
    require(set(result['games']) == {r['game'] for r in roots.values()}, 'Root game missing H1 records')
    result['schedule_sha256'] = digest(result)
    guard()
    return result


def _tensor_identity(model):
    arrays = {prefix+name: {'shape': array.shape, 'dtype': str(array.dtype),
                          'sha256': hashlib.sha256(array.tobytes()).hexdigest()}
              for prefix, group in (('p_', model.params), ('t_', model.target), ('m_', model.m), ('v_', model.v))
              for name, array in group.items()}
    return digest({'arrays': arrays, 'epoch': model.epoch, 'step': model.step, 'config': asdict(model.config)})


def _array(value, shape):
    out = np.asarray(value)
    require(out.shape == shape and out.dtype == np.float64 and np.isfinite(out).all(), 'Invalid/nonfinite float64 model output')
    return out


def _quantiles(values):
    return np.quantile(values, QUANTILES, method='linear').tolist() if values.size else None


def _geometry(z):
    if not len(z): return None
    spectrum = np.linalg.svd(z-z.mean(axis=0), compute_uv=False)**2
    spectrum = spectrum[spectrum > 0]
    p = spectrum/spectrum.sum() if len(spectrum) else np.array([])
    std = z.std(axis=0)
    return {'samples': len(z), 'dimensions': z.shape[1],
            'effective_rank': float(np.exp(-np.sum(p*np.log(p)))) if len(p) else 0.,
            'mean_std': float(std.mean()), 'median_std': float(np.median(std)),
            'weighting': 'Uniform H1 edge targets; repeated successor states retain edge multiplicity'}


def _summary(indices, target, pred, tv, pv, oracle):
    idx = np.asarray(indices, dtype=np.int64)
    n, d = len(idx), target.shape[1]
    sse = None if pred is None else float(np.sum((pred[idx]-target[idx])**2))
    return {'edge_count': n, 'latent_sse': sse, 'latent_mse': sse/(n*d) if n and sse is not None else None,
            'target_value_oracle_mse': float(np.mean((tv[idx]-oracle[idx])**2)) if n else None,
            'predicted_value_oracle_mse': float(np.mean((pv[idx]-oracle[idx])**2)) if n and pv is not None else None,
            'predicted_target_value_mse': float(np.mean((pv[idx]-tv[idx])**2)) if n and pv is not None else None,
            'target_geometry': _geometry(target[idx])}


def _packed(blocks, target, pred, tv, pv, oracle, full, head_norm):
    d = target.shape[1]
    ids = np.asarray([b['edges'] for b in blocks], dtype=np.int64).reshape(-1, 4)
    n = len(ids)
    da = target[ids[:, 0]]-target[ids[:, 1]]
    db = target[ids[:, 2]]-target[ids[:, 3]]
    opposite = ((da > 0) & (db < 0)) | ((da < 0) & (db > 0))
    bounds = np.where(opposite, np.minimum(da*da, db*db)/2, 0.)
    bound = float(bounds.sum())
    result = _summary(ids.ravel(), target, pred, tv, pv, oracle)
    observed = result['latent_sse']
    if observed is not None:
        require(bound <= observed+1e-10*max(1., observed, bound), 'Conditional bound exceeds observed packed SSE')
    value_gaps = np.concatenate((np.abs(tv[ids[:, 0]]-tv[ids[:, 1]]),
                                 np.abs(tv[ids[:, 2]]-tv[ids[:, 3]]))).ravel()
    result.update(block_count=n, bound_sse=bound, bound_mse=bound/(4*n*d) if n else None,
                  full_bound_mse=bound/(full['edge_count']*d) if full['edge_count'] else None,
                  bound_packed_sse_ratio=bound/observed if observed is not None and observed > 0 and n else None,
                  bound_full_sse_ratio=bound/full['latent_sse'] if full['latent_sse'] is not None and full['latent_sse'] > 0 and n else None,
                  reversals_strict=int(opposite.sum()),
                  reversals_1e6=int((opposite & (np.abs(da) > 1e-6) & (np.abs(db) > 1e-6)).sum()),
                  near_ties_1e6=int(((np.abs(da) <= 1e-6) | (np.abs(db) <= 1e-6)).sum()),
                  coordinate_comparisons=n*d,
                  absolute_gap_quantiles=_quantiles(np.concatenate((np.abs(da).ravel(), np.abs(db).ravel()))),
                  min_absolute_gap_quantiles=_quantiles(np.minimum(np.abs(da), np.abs(db)).ravel()),
                  target_value_gap_quantiles=_quantiles(value_gaps), head_norm=head_norm)
    return result


def measure(model, train, schedule, guard):
    """Measure frozen online/EMA targets; direct's unused dynamics are never called."""
    guard(); _training(train)
    before = _tensor_identity(model)
    require(schedule['version'] == 'v24-order-schedule01'
            and schedule['edge_order'] == ['s1a', 's2a', 's1b', 's2b']
            and schedule['schedule_sha256'] == digest({k: v for k, v in schedule.items() if k != 'schedule_sha256'}),
            'Packing identity changed')
    direct = model.config.variant == 'direct'
    head_norm = float(np.linalg.norm(model.params['vw']))
    require(np.isfinite(head_norm), 'Nonfinite online value-head norm')
    rows = []
    for game, group in sorted(schedule['games'].items()):
        guard(); edges, blocks = group['edges'], group['blocks']
        require(digest(edges) == group['edge_sha256'] and digest(blocks) == group['block_sha256'], 'Edge/block checksum mismatch')
        flat = [i for b in blocks for i in b['edges']]
        require(len(flat) == len(set(flat)) and all(type(i) is int and 0 <= i < len(edges) for i in flat), 'Overlapping or invalid packed edges')
        for b in blocks:
            identity = b['identity']
            require(b['sha256'] == digest(identity) and len(identity) == 6 and identity[0:2] == [2401, game], 'Block identity mismatch')
            _, _, r1, r2, a, bb = identity
            require(r1 < r2 and a < bb and [(edges[i]['root_id'], edges[i]['action']) for i in b['edges']] ==
                    [(r1, a), (r2, a), (r1, bb), (r2, bb)]
                    and len({edges[i]['player'] for i in b['edges']}) == 1
                    and b['terminal_count'] == sum(edges[i]['target_terminal'] for i in b['edges']), 'Wrong state-pair ordering or terminal subset')
        n, d = len(edges), model.config.latent
        require(n > 0, 'Empty H1 edge table')
        target_parts = {'online': [], 'ema': []}; pred_parts = []
        for start in range(0, n, BATCH_SIZE):
            guard(); es = edges[start:start+BATCH_SIZE]
            for e in es:
                node = train['nodes'][e['target_id']]; source = train['nodes'][e['source_id']]
                require(node['game'] == source['game'] == game and node['value'] == e['target_value']
                        and node['terminal'] == e['target_terminal'] and node['state']['player'] == e['target_player']
                        and source['state']['player'] == e['player'], 'Edge metadata changed after packing')
            x = np.stack([GAMES_V2[game].features(state_from(train['nodes'][e['target_id']]['state'])) for e in es])
            for space in target_parts:
                z = _array(model.encode(x, target=(space == 'ema')), (len(es), d))
                require(np.all(np.abs(z) <= 1+1e-12), 'Encoded target outside tanh range')
                target_parts[space].append(z)
                guard()
            if not direct:
                x0 = np.stack([GAMES_V2[game].features(state_from(train['nodes'][e['source_id']]['state'])) for e in es])
                z0 = _array(model.encode(x0), (len(es), d))
                # Model22 retains its two-slot API even for a one-step rollout.
                actions = np.zeros((len(es), 2, 65), dtype=np.float64)
                actions[np.arange(len(es)), 0, [e['action'] for e in es]] = 1.
                pred = _array(model.rollout(z0, actions, horizon=1), (len(es), d))
                require(np.all(np.abs(pred) <= 1+1e-12), 'Prediction outside tanh range')
                pred_parts.append(pred)
            guard()
        pred = np.concatenate(pred_parts) if pred_parts else None
        def values(z):
            if z is None: return None
            parts = []
            for start in range(0, len(z), BATCH_SIZE):
                guard(); group_z = z[start:start+BATCH_SIZE]
                parts.append(_array(model.value(group_z), (len(group_z), 1)).ravel())
            return np.concatenate(parts)
        pv = values(pred)
        if pred is not None:
            ids = np.asarray([b['edges'] for b in blocks], dtype=np.int64).reshape(-1, 4)
            da, db = pred[ids[:, 0]]-pred[ids[:, 1]], pred[ids[:, 2]]-pred[ids[:, 3]]
            violations = int((((da > 0) & (db < 0) | (da < 0) & (db > 0))
                             & (np.abs(da) > 1e-12) & (np.abs(db) > 1e-12)).sum())
            require(violations == 0, 'Predicted coordinates violate additive ordering')
        else:
            violations = None
        oracle = np.array([e['target_value'] for e in edges], dtype=np.float64)
        nt = [i for i, e in enumerate(edges) if not e['target_terminal']]
        nt_blocks = [b for b in blocks if b['terminal_count'] == 0]
        for space, parts in target_parts.items():
            guard(); target = np.concatenate(parts); tv = values(target)
            full = _summary(range(n), target, pred, tv, pv, oracle); guard()
            nonterminal = _summary(nt, target, pred, tv, pv, oracle); guard()
            packed = _packed(blocks, target, pred, tv, pv, oracle, full, head_norm); guard()
            packed_nt = _packed(nt_blocks, target, pred, tv, pv, oracle, nonterminal, head_norm); guard()
            rows.append({'config': asdict(model.config), 'game': game, 'target_space': space, 'latent_dim': d, 'direct': direct,
                         'all_h1': full, 'all_nonterminal': nonterminal, 'packed': packed,
                         'packed_nonterminal': packed_nt, 'predicted_order_violations': violations})
    guard()
    require(_tensor_identity(model) == before, 'Probe mutated model tensors/config/counters')
    result = {'rows': rows, 'head_norm': head_norm}
    json.dumps(result, allow_nan=False)
    guard()
    return result
