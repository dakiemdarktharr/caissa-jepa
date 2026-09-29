"""Complete legal-reply grouping and paired sampling; no artifact loaders."""
from collections import Counter, defaultdict
import hashlib
import json

import numpy as np

from two_player.games import State
from two_player_v2 import GAMES_V2
from two_player_v21.augmentation import augment

GROUP_VERSION = 'complete-legal-reply-groups-v25.0'
PLAN_VERSION = 'complete-group-plan-v25.0'
BASE_KEYS = {'x', 'valid', 'legal', 'policy', 'value', 'actions', 'value_labelled', 'policy_labelled'}
GROUPS_PER_ROOT = 4


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def state(node):
    return State(tuple(node['state']['board']), node['state']['player'])


def _inventory(groups):
    return {'roots': len({g['root_id'] for g in groups}), 'groups': len(groups),
            'fork_rows': sum(g['row_count'] for g in groups),
            'h1_terminal_groups': sum(g['h1_terminal'] for g in groups),
            'h1_nonterminal_groups': sum(not g['h1_terminal'] for g in groups),
            'h2_valid_rows': sum(g['h2_valid_rows'] for g in groups),
            'h2_missing_rows': sum(g['row_count']-g['h2_valid_rows'] for g in groups),
            'h2_terminal_rows': sum(g['h2_terminal_rows'] for g in groups),
            'h2_nonterminal_rows': sum(g['h2_nonterminal_rows'] for g in groups),
            'h2_eligible_groups': sum(g['h2_nonterminal_rows'] > 0 for g in groups)}


def build_groups(dataset):
    """Validate each legal H1/reply closure; preserve original base-array indices.

    Training/development loaders and immutable data identity verification are
    caller responsibilities. This function accepts a single already-loaded full
    split; it never opens a parent bank, file or protected split.
    """
    manifest = dataset['manifest']; split = manifest['split']
    roles = {'train': 'redacted-training', 'development': 'standalone-development'}
    require(split in roles and manifest['role'] == roles[split] and manifest['fraction'] == 1.,
            'Groups require standalone FULL train or development')
    roots = {r['root_id']: r for r in dataset['roots']}
    require(bool(roots) and len(roots) == len(dataset['roots']), 'Empty or duplicate roots')
    require(all(r['split'] == split and r['game'] in GAMES_V2 for r in roots.values()), 'Mixed or protected root split')
    nodes = dataset['nodes']
    for node in nodes.values():
        require(node['game'] in GAMES_V2, 'Unknown node game')
        game = GAMES_V2[node['game']]; s = state(node)
        game.validate(s); terminal = game.terminal(s)
        legal = game.legal_actions(s)
        require(type(node['terminal']) is bool and node['terminal'] == (terminal is not None)
                and tuple(node['legal']) == legal, 'Node rule metadata mismatch')
        require(node.get('value_labelled') is True and node.get('policy_labelled') is (terminal is None),
                'Every valid FULL node must have the permitted labels')
        require(type(node['value']) in (int, float) and node['value'] in (-1, 0, 1), 'Invalid oracle value')
        require(set(node['optimal']) <= set(legal) and len(set(node['optimal'])) == len(node['optimal'])
                and bool(node['optimal']) == (terminal is None), 'Invalid complete policy target')
        if terminal is not None:
            require(node['value'] == s.player*terminal, 'Terminal label has wrong successor perspective')
    grouped = defaultdict(list)
    seen_forks = set()
    for index, fork in enumerate(dataset['forks']):
        require(fork['split'] == split and fork['root_id'] in roots, 'Mixed/protected fork split or unknown root')
        root = roots[fork['root_id']]; game = GAMES_V2[root['game']]
        require(fork['game'] == root['game'] and len(fork['node_ids']) == 3 and len(fork['actions']) == 2,
                'Fork identity/shape mismatch')
        source_id, first_id, second_id = fork['node_ids']; own, reply = fork['actions']
        require(source_id in nodes and first_id in nodes, 'Missing source/H1 node')
        source, first = nodes[source_id], nodes[first_id]
        require(source['game'] == first['game'] == root['game'] and state(source) == state(root),
                'Fork source differs from root')
        require(game.terminal(state(source)) is None and tuple(root['actions']) == game.legal_actions(state(source)),
                'Root legal inventory or terminal state mismatch')
        require(type(own) is int and game.transition(state(source), own) == state(first), 'Illegal H1 transition')
        if first['terminal']:
            require(reply is None and second_id is None, 'Terminal H1 must have missing H2')
        else:
            require(second_id in nodes and type(reply) is int, 'Missing nonterminal reply transition')
            second = nodes[second_id]
            require(second['game'] == root['game'] and game.transition(state(first), reply) == state(second),
                    'Illegal reply transition')
        key = (root['game'], root['root_id'], own)
        signature = (*key, reply)
        require(signature not in seen_forks, 'Duplicate complete reply')
        seen_forks.add(signature)
        grouped[key].append((index, fork))
    expected = {(r['game'], rid, action) for rid, r in roots.items() for action in r['actions']}
    require(set(grouped) == expected, 'Missing own-action group')
    groups = []
    for (name, rid, own), members in sorted(grouped.items()):
        source_ids = {f['node_ids'][0] for _, f in members}
        first_ids = {f['node_ids'][1] for _, f in members}
        require(len(source_ids) == len(first_ids) == 1, 'Source/H1 target differs across replies')
        source_id, first_id = next(iter(source_ids)), next(iter(first_ids))
        first = nodes[first_id]; replies = [None] if first['terminal'] else list(GAMES_V2[name].legal_actions(state(first)))
        by_reply = {f['actions'][1]: (index, f) for index, f in members}
        require(set(by_reply) == set(replies) and len(members) == len(replies), 'Reply group is not complete')
        ordered = [by_reply[a] for a in replies]
        h2_ids = [f['node_ids'][2] for _, f in ordered]
        terminal_rows = sum(nid is not None and nodes[nid]['terminal'] for nid in h2_ids)
        valid_rows = sum(nid is not None for nid in h2_ids)
        groups.append({'game': name, 'root_id': rid, 'own_action': own,
                       'source_id': source_id, 'h1_id': first_id, 'h2_ids': h2_ids,
                       'fork_indices': [i for i, _ in ordered], 'reply_actions': replies,
                       'row_count': len(ordered), 'h1_terminal': first['terminal'],
                       'h2_valid_rows': valid_rows, 'h2_terminal_rows': terminal_rows,
                       'h2_nonterminal_rows': valid_rows-terminal_rows})
    inventory = _inventory(groups)
    inventory['games'] = {name: _inventory([g for g in groups if g['game'] == name])
                          for name in sorted({g['game'] for g in groups})}
    require(inventory['fork_rows'] == len(dataset['forks']), 'Ungrouped fork rows')
    receipt = {'version': GROUP_VERSION, 'split': split,
               'dataset_fingerprint': manifest.get('dataset_fingerprint'), 'groups': groups,
               'inventory': inventory}
    receipt['group_sha256'] = digest(receipt)
    return receipt


def _validate_receipt(receipt):
    require(receipt['version'] == GROUP_VERSION and receipt['split'] in ('train', 'development'), 'Unknown group receipt')
    require(receipt['group_sha256'] == digest({k: v for k, v in receipt.items() if k != 'group_sha256'}),
            'Group receipt changed')


def _array_sha(array):
    return hashlib.sha256(np.asarray(array, dtype='<i8').tobytes()).hexdigest()


def epoch_plan(group_receipt, seed, epoch):
    """One complete-group sampler and one independent group-symmetry RNG."""
    _validate_receipt(group_receipt)
    require(group_receipt['split'] == 'train', 'Only training groups may be sampled')
    require(type(seed) is int and seed >= 0 and type(epoch) is int and epoch >= 0,
            'Seed and epoch must be nonnegative integers')
    groups = group_receipt['groups']; by_game = defaultdict(lambda: defaultdict(list))
    for index, group in enumerate(groups):
        by_game[group['game']][group['root_id']].append(index)
    require(bool(by_game), 'Empty group inventory')
    maximum = max(len(roots) for roots in by_game.values())
    rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2501]))
    draws, games = [], {}
    for name in sorted(by_game):
        roots = sorted(by_game[name]); root_indices = rng.permutation(len(roots)).tolist()
        root_indices += rng.integers(len(roots), size=maximum-len(roots)).tolist()
        for i in root_indices:
            options = by_game[name][roots[i]]
            draws.extend(options[int(j)] for j in rng.integers(len(options), size=GROUPS_PER_ROOT))
        games[name] = {'unique_roots': len(roots), 'root_draws': maximum,
                       'repeated_root_draws': maximum-len(roots), 'group_draws': maximum*GROUPS_PER_ROOT}
    indices = np.asarray(draws, dtype=np.int64); rng.shuffle(indices)
    symmetry_rng = np.random.default_rng(np.random.SeedSequence([seed, epoch, 2511]))
    transforms = np.asarray([symmetry_rng.integers(len(GAMES_V2[groups[int(i)]['game']].transforms()))
                             for i in indices], dtype=np.int64)
    selected = [groups[int(i)] for i in indices]
    counters = _inventory(selected)
    for name in games:
        games[name].update({k: v for k, v in _inventory([g for g in selected if g['game'] == name]).items()
                            if k not in ('roots', 'groups')})
    counts = Counter(f"{g['game']}/{int(t)}" for g, t in zip(selected, transforms))
    receipt = {'version': PLAN_VERSION, 'seed': seed, 'epoch': epoch,
               'sampler_namespace': 2501, 'symmetry_namespace': 2511,
               'group_sha256': group_receipt['group_sha256'], 'groups_per_root': GROUPS_PER_ROOT,
               'group_draws': len(indices), 'unique_groups': len(set(indices.tolist())),
               'group_index_sha256': _array_sha(indices), 'transform_sha256': _array_sha(transforms),
               'transform_counts': dict(sorted(counts.items())), 'games': games,
               **{k: v for k, v in counters.items() if k not in ('roots', 'groups')}}
    receipt['plan_sha256'] = digest(receipt)
    return indices, transforms, receipt


def make_batch(basearrays, group_receipt, drawindices, transforms=None):
    """Copy complete groups; repeated selections receive distinct contiguous IDs.

    Callers verify the immutable group receipt once before batching (epoch_plan
    verifies it per epoch). Avoid rehashing its full contents in each minibatch.
    """
    require(group_receipt['version'] == GROUP_VERSION and group_receipt['split'] in ('train', 'development'),
            'Unknown group batch source')
    require(set(basearrays) == BASE_KEYS, 'Expected exactly eight base arrays')
    draws = np.asarray(drawindices)
    groups = group_receipt['groups']
    require(draws.ndim == 1 and draws.dtype.kind in 'iu' and len(draws) > 0
            and np.all(draws >= 0) and np.all(draws < len(groups)), 'Invalid drawn group indices')
    if transforms is not None:
        ts = np.asarray(transforms)
        require(ts.shape == draws.shape and ts.dtype.kind in 'iu', 'One integer transform per drawn group required')
    else:
        ts = None
    row_ids, instance_ids, names, row_transforms = [], [], [], []
    for instance, index in enumerate(draws):
        group = groups[int(index)]; fork_ids = group['fork_indices']
        require(len(fork_ids) == group['row_count'] and bool(fork_ids), 'Empty or corrupt group row count')
        row_ids.extend(fork_ids); instance_ids.extend([instance]*len(fork_ids))
        names.extend([group['game']]*len(fork_ids))
        if ts is not None:
            transform = int(ts[instance])
            require(0 <= transform < len(GAMES_V2[group['game']].transforms()), 'Illegal group symmetry')
            row_transforms.extend([transform]*len(fork_ids))
    indices = np.asarray(row_ids, dtype=np.int64)
    n = group_receipt['inventory']['fork_rows']
    require(np.all(indices >= 0) and np.all(indices < n), 'Fork index outside base arrays')
    require(all(isinstance(a, np.ndarray) and a.shape[0] == n for a in basearrays.values()), 'Base array inventory mismatch')
    batch = {k: a[indices].copy() for k, a in basearrays.items()}
    batch['group'] = np.asarray(instance_ids, dtype=np.int64)
    return augment(batch, names, np.asarray(row_transforms, dtype=np.int64)) if ts is not None else batch
