"""Verify saved V2.5 development decisions, without fitting or new predictions.

The sole candidate is raw-tail. All rates/cells remain visible, including failed
ones. Rate selection uses EXACT only; the same rate carries into every hybrid
and mechanism comparison. Bootstrap intervals describe adaptive development.
"""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from two_player_v2.report import _digest, _read, _sha, _finite, _require, _score_map, _metrics
from two_player_v2 import GAMES_V2
from . import METHOD_VERSION

GAMES = tuple(sorted(GAMES_V2))
SEEDS = (17, 29, 43)
RATES = (.001, .0003)
VARIANTS = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail', 'raw-mean', 'raw-tail', 'raw-scaled')
CONTROLS = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail')
TRACKS = ('exact', 'hybrid')
CANDIDATE = 'raw-tail'
BOOTSTRAP_REPLICATES = 10000
DEVELOPMENT_FINGERPRINT = 'bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617'
TRAIN_FINGERPRINT = '73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'


def _schedule(schedule):
    roots = schedule['roots']
    _require(isinstance(roots, list) and bool(roots), 'Missing truth schedule')
    seen, trajectories = set(), set()
    for root in roots:
        game, rid, trajectory = root['game'], root['root_id'], root['trajectory']
        _require(game in GAMES and isinstance(rid, str) and bool(rid), 'Invalid root identity')
        _require((game, rid) not in seen and (game, trajectory) not in trajectories,
                 'Duplicate root or multiple roots per trajectory require a new cluster protocol')
        seen.add((game, rid)); trajectories.add((game, trajectory))
        _require(root.get('split', 'development') == 'development', 'Non-development truth schedule')
        actions, truth = root['actions'], root['oracle_values']
        _require(isinstance(actions, list) and len(actions) >= 1 and len(set(actions)) == len(actions)
                 and all(type(a) is int and 0 <= a < 65 for a in actions), 'Invalid root legal actions')
        _require(isinstance(truth, list) and len(truth) == len(actions)
                 and all(_finite(v) and v in (-1, 0, 1) for v in truth), 'Invalid root oracle values')
        _require(type(root['beyond_depth']) is bool, 'Invalid beyond-depth stratum')
    _require({r['game'] for r in roots} == set(GAMES), 'Missing development game')
    counts = schedule['unique_node_counts']
    _require(set(counts) == set(GAMES) and all(type(n) is int and n >= 2 for n in counts.values()),
             'Invalid unique-node inventory')
    _require(schedule['development_fingerprint'] == DEVELOPMENT_FINGERPRINT, 'Unrecognized development dataset')
    return [(r['game'], r['root_id'], r['trajectory']) for r in roots]


def validate_scores(scores, roots, variant, tracks=TRACKS, zero=False):
    """Recompute every decision from its saved legal action estimates and truth."""
    mapping = _score_map(scores, [(r['game'], r['root_id'], r['trajectory']) for r in roots], tracks)
    mse = {}
    counter_keys = {'encoder_calls', 'encoder_states', 'rollout_calls', 'predictor_steps', 'value_calls', 'value_states'}
    for root in roots:
        for track in tracks:
            key = root['game'], root['root_id'], track
            row = mapping[key]
            estimates = row['action_estimates']
            _require(isinstance(estimates, list) and len(estimates) == len(root['actions'])
                     and all(_finite(v) and abs(v) <= 1+1e-12 for v in estimates), 'Invalid saved action estimates')
            index = int(np.argmax(estimates)); truth = root['oracle_values']
            regret = max(truth)-truth[index]
            _require(type(row['action']) is int and row['action'] == root['actions'][index], 'Chosen action violates saved argmax or legal tie order')
            _require(row['regret'] == regret and row['optimal'] == (regret == 0), 'Saved regret disagrees with original oracle')
            _require(row['oracle_gap'] == max(truth)-min(truth) and row['beyond_depth'] == root['beyond_depth'], 'Decision stratum/oracle gap mismatch')
            _require(row['reason'] is None and row['seconds'] < 1, 'Completed decision exceeded time budget or has error reason')
            for name in ('nodes', 'transitions', 'leafcount', 'neural_leaves', 'neural_leaf_candidates'):
                _require(type(row[name]) is int and row[name] >= 0, 'Invalid decision resource count: '+name)
            _require(row['nodes'] == row['transitions'] and 0 < row['nodes'] <= 4096,
                     'Transition budget/count mismatch')
            n = row['neural_leaf_candidates']
            _require(n <= row['leafcount'] <= row['nodes'] and row['neural_leaves'] == (0 if zero else n),
                     'Leaf counter mismatch')
            expected = {k: 0 for k in counter_keys}
            if n and not zero:
                recurrent = track == 'hybrid' and variant != 'direct'
                expected.update(encoder_calls=1, encoder_states=1 if recurrent else n,
                                rollout_calls=int(recurrent), predictor_steps=2*n if recurrent else 0,
                                value_calls=1, value_states=n)
            _require(row['neuralcounts'] == expected and all(type(v) is int for v in row['neuralcounts'].values()),
                     'Neural accounting disagrees with evaluator semantics')
            mse[key] = float(np.mean((np.asarray(estimates)-np.asarray(truth))**2))
    if variant == 'direct' and tuple(tracks) == TRACKS:
        for root in roots:
            a = mapping[root['game'], root['root_id'], 'exact']
            b = mapping[root['game'], root['root_id'], 'hybrid']
            _require(all(a[k] == b[k] for k in ('action', 'action_estimates', 'regret', 'nodes', 'leafcount', 'neuralcounts')),
                     'Direct exact and hybrid decisions differ')
    return mapping, mse


def _geometry(cell, schedule):
    diagnostics = cell['diagnostics']
    _require(diagnostics.get('stage') == 'development' and set(diagnostics['games']) == set(GAMES),
             'Diagnostic game/stage mismatch')
    _require(set(cell['representation']) == set(GAMES), 'Occurrence representation game inventory mismatch')
    collapse = []
    for game in GAMES:
        g = diagnostics['games'][game]['unique_node_geometry']
        rank, std = g['effective_rank'], g['median_std']
        _require(type(g['samples']) is int and g['samples'] == schedule['unique_node_counts'][game]
                 and g['dimensions'] == 64, 'Unique-node geometry sample/dimension mismatch')
        _require(_finite(rank) and _finite(std) and 0 <= rank <= min(64, g['samples'])+1e-9
                 and std >= 0, 'Invalid unique-node geometry')
        bad = rank < 2 or std < .001
        _require(type(diagnostics['games'][game]['collapse']) is bool
                 and diagnostics['games'][game]['collapse'] == bad, 'Per-game collapse flag contradicts geometry')
        if bad:
            collapse.append({'game': game, 'effective_rank': rank, 'median_std': std})
    _require(type(diagnostics['collapse']) is bool and diagnostics['collapse'] == bool(collapse),
             'Aggregate collapse flag contradicts geometry')
    return collapse


def _plans(root_counts, track_index, replicates):
    """Stratified paired-root bootstrap, keeping the three training seeds fixed."""
    rng = np.random.default_rng(np.random.SeedSequence([2505, track_index]))
    plans = {g: np.empty((replicates, root_counts[g]), dtype=np.int64) for g in GAMES}
    for i in range(replicates):
        for game in GAMES:
            plans[game][i] = rng.integers(root_counts[game], size=root_counts[game])
    return plans


def _comparison(candidate, baseline, plans, track_index):
    differences = {g: baseline[g]-candidate[g] for g in GAMES}
    per_game = {g: float(a.mean()) for g, a in differences.items()}
    per_seed = np.mean([a.mean(axis=1) for a in differences.values()], axis=0)
    # Averaging the fixed cohort first is exactly the shared-root draw across
    # all three paired seeds, not 3N independent root observations.
    draws = np.stack([differences[g].mean(axis=0)[plans[g]].mean(axis=1) for g in GAMES], axis=1)
    return {'aggregate_improvement': float(np.mean(list(per_game.values()))),
            'per_game_improvement': per_game, 'per_seed_improvement': dict(zip(map(str, SEEDS), per_seed.tolist())),
            'favorable_seeds': int(np.sum(per_seed > 0)),
            'bootstrap': {'replicates': len(draws), 'seed_sequence': [2505, track_index],
                          'resampling': 'Roots stratified by game; same root draw across fixed three paired seeds and compared models',
                          'aggregate_ci95': np.quantile(draws.mean(axis=1), [.025, .975]).tolist(),
                          'per_game_ci95': {g: np.quantile(draws[:, i], [.025, .975]).tolist() for i, g in enumerate(GAMES)},
                          'scope': 'Descriptive adaptive development; no confirmation or selection correction'}}


def _positive(comparison):
    return (comparison['aggregate_improvement'] > 0 and
            all(v > 0 for v in comparison['per_game_improvement'].values()) and comparison['favorable_seeds'] >= 2)


def summarize(cells, schedule):
    """Pure saved-record report. Invalid inventories fail closed, preserving cells.

    schedule contains roots with legal actions/oracle_values, unique_node_counts,
    and development_fingerprint. Strict summarize_grid additionally binds this
    metadata to immutable manifests, source, history and checkpoint files.
    """
    result = {'version': 'v25-development-report01', 'method': METHOD_VERSION, 'stage': 'development',
              'status': 'inconclusive', 'verification_errors': [], 'runs': [], 'configurations': [],
              'selected': {}, 'candidate': CANDIDATE, 'tracks': {}, 'mechanism': None,
              'limitations': ['Adaptive development on reused roots; no confirmatory significance or Q1/transfer claim.',
                              'Only raw-tail is eligible; controls and ablations cannot replace a failed candidate.',
                              'One exact-selected global rate per family carries into all hybrid comparisons.',
                              'Same legal tree and updates do not match active compute or wall time.',
                              'Saved decisions are verified; this report makes no model predictions.']}
    errors = result['verification_errors']
    result['runs'] = [{'config': c.get('config'), 'status': c.get('status'), 'checkpoint_sha256': c.get('checkpoint_sha256')}
                      for c in cells]
    try:
        _schedule(schedule)
        _digest(schedule); _digest(cells)  # reject all NaN/Infinity, including unused diagnostics
        expected = {(v, r, s) for v in VARIANTS for r in RATES for s in SEEDS}
        keys = [(c['config']['variant'], c['config']['learning_rate'], c['config']['seed']) for c in cells]
        _require(len(keys) == 42 and len(set(keys)) == 42 and set(keys) == expected,
                 'Grid must contain all 42 frozen cells exactly once')
        roots = schedule['roots']; by_key = {}
        for cell, public, key in zip(cells, result['runs'], keys):
            from .model import Config
            _require(cell['config'] == asdict(Config(variant=key[0], learning_rate=key[1], seed=key[2])),
                     'Nonfrozen model configuration')
            _require(cell['status'] == 'complete', 'Incomplete/failed cell '+str(key))
            mapping, mse = validate_scores(cell['scores'], roots, key[0])
            collapse = _geometry(cell, schedule)
            public.update(metrics=_metrics(cell['scores']), collapse=collapse,
                          seconds=cell.get('seconds'), parameters=cell.get('parameters'),
                          representation=cell['representation'], diagnostics=cell['diagnostics'])
            _require(not collapse, 'Collapsed cell makes the entire grid inconclusive: '+str(key))
            by_key[key] = mapping, mse
        configs = {}
        for variant in VARIANTS:
            for rate in RATES:
                tracks, arrays = {}, {}
                for track in TRACKS:
                    aa, mm = {}, {}
                    for game in GAMES:
                        rids = [r['root_id'] for r in roots if r['game'] == game]
                        aa[game] = np.array([[by_key[variant, rate, seed][0][game, rid, track]['regret'] for rid in rids] for seed in SEEDS])
                        mm[game] = np.array([[by_key[variant, rate, seed][1][game, rid, track] for rid in rids] for seed in SEEDS])
                    arrays[track] = aa, mm
                    tracks[track] = {'mean_regret': float(np.mean([a.mean() for a in aa.values()])),
                                     'per_game_regret': {g: float(a.mean()) for g, a in aa.items()},
                                     'per_seed_regret': dict(zip(map(str, SEEDS), np.mean([a.mean(axis=1) for a in aa.values()], axis=0).tolist())),
                                     'action_oracle_mse': float(np.mean([a.mean() for a in mm.values()])),
                                     'per_game_action_oracle_mse': {g: float(a.mean()) for g, a in mm.items()},
                                     'roots_per_game_per_seed': {g: a.shape[1] for g, a in aa.items()}}
                row = {'variant': variant, 'learning_rate': rate, 'tracks': tracks}
                result['configurations'].append(row)
                configs[variant, rate] = row, arrays
        selected = {}
        for variant in VARIANTS:
            choices = [configs[variant, r] for r in RATES]
            best = min(x[0]['tracks']['exact']['mean_regret'] for x in choices)
            selected[variant] = min((x for x in choices if abs(x[0]['tracks']['exact']['mean_regret']-best) <= 1e-12),
                                    key=lambda x: x[0]['learning_rate'])
        result['selected'] = {v: x[0] for v, x in selected.items()}
        root_counts = {g: sum(r['game'] == g for r in roots) for g in GAMES}
        for ti, track in enumerate(TRACKS):
            plans = _plans(root_counts, ti, BOOTSTRAP_REPLICATES)
            comparisons = {v: _comparison(selected[CANDIDATE][1][track][0], selected[v][1][track][0], plans, ti) for v in CONTROLS}
            strongest = min(CONTROLS, key=lambda v: selected[v][0]['tracks'][track]['mean_regret'])
            margin = comparisons[strongest]['aggregate_improvement']
            reasons = []
            if margin < .05: reasons.append('Strongest-control improvement below 0.05')
            for name, comparison in comparisons.items():
                if not _positive(comparison): reasons.append('Nonpositive game effect or fewer than two favorable seeds versus '+name)
            result['tracks'][track] = {'passed': not reasons, 'strongest_control': strongest,
                                      'strongest_control_margin': margin, 'comparisons': comparisons, 'reasons': reasons}
            if track == 'hybrid':
                ablations = {v: _comparison(selected[CANDIDATE][1][track][0], selected[v][1][track][0], plans, ti)
                             for v in ('raw-mean', 'raw-scaled')}
                candidate_mse = selected[CANDIDATE][0]['tracks'][track]['action_oracle_mse']
                mse_comparisons = {v: {'candidate_mse': candidate_mse,
                                      'control_mse': selected[v][0]['tracks'][track]['action_oracle_mse'],
                                      'improvement': selected[v][0]['tracks'][track]['action_oracle_mse']-candidate_mse}
                                   for v in CONTROLS if v != 'direct'}
                mechanism_reasons = [v+' ablation did not improve in both games and two seeds' for v, c in ablations.items() if not _positive(c)]
                mechanism_reasons += [v+' own-action oracle MSE not reduced' for v, c in mse_comparisons.items() if c['improvement'] <= 0]
                if reasons: mechanism_reasons.append('Hybrid primary comparator gate failed')
                result['mechanism'] = {'passed': not mechanism_reasons, 'ablations': ablations,
                                       'action_oracle_mse': mse_comparisons, 'reasons': mechanism_reasons}
        result['status'] = ('development_screen_passed' if result['tracks']['exact']['passed'] and result['mechanism']['passed']
                            else 'exploratory_hybrid_only' if result['mechanism']['passed'] else 'not_promoted')
        result['decision_counts'] = {'cells': len(cells), 'roots_per_cell': len(roots), 'tracks': 2,
                                     'complete': len(cells)*len(roots)*2, 'censored_or_error': 0}
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        errors.append(type(exc).__name__+': '+str(exc))
    return result


def _count_totals(plan, variant):
    rows, groups = plan['fork_rows'], plan['group_draws']
    t1, t2, n2 = plan['h1_terminal_groups'], plan['h2_terminal_rows'], plan['h2_nonterminal_rows']
    v2 = plan['h2_valid_rows']
    recurrent = variant != 'direct'
    auxiliary = variant not in ('direct', 'recurrent-pv')
    result = {'group_count': groups, 'encoded_count': 2*rows+v2, 'value_count': 2*rows+v2,
              'policy_count': 2*rows-t1+n2, 'terminal_count': t1+t2,
              'value_unlabelled_count': 0, 'policy_unlabelled_count': 0}
    for h, valid, terminal, eligible_groups, eligible_rows in (
            (1, rows, t1, groups-t1, rows-t1),
            (2, v2, t2, plan['h2_eligible_groups'], n2)):
        prefix = f'h{h}_'
        result.update({prefix+'eligible_count': valid, prefix+'count': valid if recurrent else 0,
                       prefix+'missing_count': rows-valid, prefix+'terminal_count': terminal,
                       prefix+'value_label_count': valid if recurrent else 0,
                       prefix+'policy_label_count': valid-terminal if recurrent else 0,
                       prefix+'aux_eligible_group_count': eligible_groups,
                       prefix+'aux_eligible_row_count': eligible_rows,
                       prefix+'aux_group_count': eligible_groups if auxiliary else 0,
                       prefix+'aux_row_count': (eligible_groups if h == 1 else eligible_rows) if auxiliary else 0,
                       prefix+'aux_excluded_group_count': groups-eligible_groups})
    return result


def _weight_sums(grouping, indices):
    groups = [grouping['groups'][int(i)] for i in indices]
    total = len(groups); terminal = sum(g['h1_terminal'] for g in groups)
    q = sum(g['h2_nonterminal_rows']/g['row_count'] for g in groups)
    return {'encoded_weight_sum': 3*total-terminal, 'value_weight_sum': 3*total-terminal,
            'policy_weight_sum': 2*total-terminal+q,
            'h1_value_weight_sum': total, 'h1_policy_weight_sum': total-terminal,
            'h2_value_weight_sum': total-terminal, 'h2_policy_weight_sum': q}


def _history(history, config, grouping, replayed):
    from .data import epoch_plan
    _require(isinstance(history, list) and len(history) == 160, 'Incomplete epoch history')
    for epoch, row in enumerate(history):
        _require(row['epoch'] == epoch+1 and row['step'] == 66*(epoch+1) and row['steps'] == 66,
                 'History step/epoch counters mismatch')
        key = config.seed, epoch
        if key not in replayed:
            indices, _, plan = epoch_plan(grouping, config.seed, epoch)
            replayed[key] = plan, _weight_sums(grouping, indices)
        plan, expected_sums = replayed[key]
        _require(row['schedule'] == plan, 'Sampling/augmentation replay mismatch')
        _require(row['fork_rows'] == plan['fork_rows'] and row['group_draws'] == plan['group_draws'] == 2088,
                 'History exposure counters mismatch')
        _require(_finite(row['seconds']) and row['seconds'] >= 0, 'Invalid epoch time')
        expected = _count_totals(plan, config.variant)
        counts = row['count_totals']
        dynamic = {'h2_max_tie_group_count', 'h2_max_tie_member_count', 'h2_scaled_factor_count',
                   'h2_scaled_factor_nonzero_count', 'h2_scaled_factor_clip_count'}
        _require(set(counts) == set(expected) | dynamic and all(counts[k] == v for k, v in expected.items()),
                 'History label/target counters mismatch')
        _require(all(type(v) is int and v >= 0 for v in counts.values()), 'Noninteger history counts')
        ties, members = counts['h2_max_tie_group_count'], counts['h2_max_tie_member_count']
        _require(ties <= expected['h2_aux_group_count'] and 2*ties <= members <= expected['h2_aux_row_count']
                 and (ties > 0 or members == 0), 'Invalid exact-max tie counts')
        scaled = config.variant == 'raw-scaled'
        n, nonzero = counts['h2_scaled_factor_count'], counts['h2_scaled_factor_nonzero_count']
        _require(n == (plan['h2_eligible_groups'] if scaled else 0) and nonzero <= n
                 and counts['h2_scaled_factor_clip_count'] == 0, 'Scaled-factor count/clipping mismatch')
        sums, factors = row['sum_totals'], row['scaled_factors']
        _require(set(sums) == set(expected_sums) | {'h2_scaled_factor_sum'}, 'Additive metric inventory mismatch')
        for name, value in expected_sums.items():
            if config.variant == 'direct' and name.startswith(('h1_', 'h2_')): value = 0.
            _require(_finite(sums[name]) and math.isclose(sums[name], value, rel_tol=1e-12, abs_tol=1e-8),
                     'Group-weighted label denominator mismatch: '+name)
        _require(all(_finite(v) and v >= 0 for v in sums.values()) and factors['count'] == n,
                 'Invalid additive metrics/factor counts')
        factor_sum = sums['h2_scaled_factor_sum']
        if n:
            lo, hi, mean = factors['min'], factors['max'], factors['mean']
            maximum_k = max((g['h2_nonterminal_rows'] for g in grouping.get('groups', [])), default=65)
            upper = (1+maximum_k)/2
            _require(all(_finite(v) for v in (lo, hi, mean)) and 0 <= lo <= mean <= hi <= upper+1e-10
                     and (lo == 0 if nonzero < n else lo >= 1-1e-10)
                     and nonzero-1e-9 <= factor_sum <= nonzero*upper+1e-8
                     and math.isclose(mean, factor_sum/n, abs_tol=1e-12, rel_tol=1e-12),
                     'Scaled-factor extrema/mean/bounds mismatch')
        else:
            _require(factor_sum == 0 and factors == {'count': 0, 'min': None, 'max': None, 'mean': None},
                     'Inactive scaled-factor metrics must be empty')
        _require(isinstance(row['metrics_group_weighted_batch_mean'], dict)
                 and bool(row['metrics_group_weighted_batch_mean'])
                 and all(_finite(v) for v in row['metrics_group_weighted_batch_mean'].values()), 'Invalid epoch metrics')
    return _digest([r['schedule'] for r in history])


def _group_file(directory, ledger, split):
    from .data import GROUP_VERSION, _inventory
    file = directory/(split+'-groups.json')
    _require(_sha(file) == ledger[split+'_groups_file_sha256'], 'Group file checksum mismatch')
    data = _read(file)
    _require(data['version'] == GROUP_VERSION and data['split'] == split, 'Group version/split mismatch')
    _require(data['group_sha256'] == ledger[split+'_group_sha256']
             == _digest({k: v for k, v in data.items() if k != 'group_sha256'}), 'Group metadata hash mismatch')
    _require(data['dataset_fingerprint'] == ledger[split+'_manifest']['dataset_fingerprint'], 'Group data identity mismatch')
    groups = data['groups']
    keys = [(g['game'], g['root_id'], g['own_action']) for g in groups]
    _require(keys == sorted(keys) and len(keys) == len(set(keys)), 'Duplicate/reordered groups')
    for g in groups:
        _require(g['game'] in GAMES and type(g['row_count']) is int and g['row_count'] > 0,
                 'Invalid group row inventory')
        k = g['row_count']
        _require(len(g['fork_indices']) == len(g['reply_actions']) == len(g['h2_ids']) == k
                 and len(set(g['fork_indices'])) == len(set(g['reply_actions'])) == k,
                 'Incomplete/duplicated reply group')
        _require(type(g['h1_terminal']) is bool, 'Invalid terminal group flag')
        if g['h1_terminal']:
            _require(k == 1 and g['reply_actions'] == [None] and g['h2_ids'] == [None]
                     and g['h2_valid_rows'] == g['h2_terminal_rows'] == g['h2_nonterminal_rows'] == 0,
                     'Terminal H1 must have singleton missing H2')
        else:
            _require(all(type(a) is int and 0 <= a < 65 for a in g['reply_actions'])
                     and all(isinstance(n, str) and n for n in g['h2_ids'])
                     and g['h2_valid_rows'] == k and 0 <= g['h2_terminal_rows'] <= k
                     and g['h2_nonterminal_rows'] == k-g['h2_terminal_rows'], 'Nonterminal reply group counters mismatch')
    inventory = _inventory(groups)
    inventory['games'] = {g: _inventory([a for a in groups if a['game'] == g]) for g in GAMES}
    _require(data['inventory'] == inventory, 'Group aggregate inventory mismatch')
    indices = [i for g in groups for i in g['fork_indices']]
    _require(sorted(indices) == list(range(inventory['fork_rows'])), 'Fork rows missing/duplicated across groups')
    return data


def summarize_grid(directory):
    """Strict local artifact audit; only saved records/checkpoints are inspected.

    Original data bytes and legal closure are checked by the runtime and the
    independent post-run audit. This report verifies the embedded manifest and
    truth schedule, but cannot derive original truth from its checksum alone.
    """
    from . import runtime as rt
    from .model import Config, Model
    directory = Path(directory).resolve()
    failed = {'version': 'v25-development-report01', 'method': METHOD_VERSION, 'stage': 'development',
              'status': 'inconclusive', 'input_directory': str(directory), 'verification_errors': [], 'runs': []}
    errors = failed['verification_errors']
    try:
        ledger = _read(directory/'ledger.json')
        failed['runs'] = [{'id': r.get('id'), 'config': r.get('config'), 'status': r.get('status')} for r in ledger.get('runs', [])]
        _require(ledger['version'] == 'v25-grid04' and ledger['method'] == METHOD_VERSION
                 and ledger['stage'] == 'development' and ledger['epochs'] == 160, 'Unknown grid/method/stage')
        _require(ledger['status'] == 'complete' and ledger['failures'] == [], 'Grid failed or incomplete')
        _require(ledger['selection_predictions'] == ledger['final_predictions'] == 0, 'Protected predictions present')
        _require(ledger['limits'] == {'cell_seconds': 600., 'total_cell_seconds': 25200., 'bytes': 3000000000, 'rss': 1000000000},
                 'Frozen resource limits changed')
        _require(ledger['source'] == rt.runtime_source() and bool(ledger['source']), 'Current source/inventory mismatch')
        _require(isinstance(ledger['code_commit'], str) and len(ledger['code_commit']) == 40
                 and all(c in '0123456789abcdef' for c in ledger['code_commit']), 'Missing commit provenance')
        expected_configs = [asdict(c) for c in rt.configurations()]
        _require([r['config'] for r in ledger['runs']] == expected_configs and len(expected_configs) == 42,
                 'Missing/reordered/extra grid configurations')
        for row, config in zip(ledger['runs'], rt.configurations()):
            _require(row['id'] == rt.run_id(config) and row['status'] == 'complete', 'Noncomplete or substituted run ID')
        expected_files = {'ledger.json', 'controls.json', 'train-groups.json', 'development-groups.json'}
        expected_files |= {item['id']+'/'+name for item in ledger['runs']
                           for name in ('checkpoint.npz', 'history.json', 'budget.json', 'receipt.json')}
        _require({p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} == expected_files,
                 'Unexpected or missing grid artifact files (failed work may not be hidden)')
        tm, dm = ledger['train_manifest'], ledger['development_manifest']
        for manifest, split, fp, role in ((tm, 'train', TRAIN_FINGERPRINT, 'redacted-training'),
                                         (dm, 'development', DEVELOPMENT_FINGERPRINT, 'standalone-development')):
            _require(manifest['dataset_fingerprint'] == fp and manifest['split'] == split
                     and manifest['fraction'] == 1 and manifest['role'] == role
                     and manifest['audit']['status'] == manifest['parent_audit_status'] == 'PASSED', 'Unverified data manifest')
        _require(tm['parent_dataset_fingerprint'] == dm['parent_dataset_fingerprint'], 'Cross-split parent provenance mismatch')
        truth = ledger['development_truth']; schedule = _schedule(truth)
        _require(_digest(truth) == ledger['development_truth_sha256'] and _digest(schedule) == ledger['development_schedule_sha256']
                 and [list(a) for a in schedule] == ledger['development_schedule'], 'Development truth/schedule identity mismatch')
        _require({g: sum(r['game'] == g for r in truth['roots']) for g in GAMES}
                 == {'connect4-4x5': 107, 'reversi6': 102} and sum(truth['unique_node_counts'].values()) == 3756,
                 'Development root/node inventory mismatch')
        grouping = _group_file(directory, ledger, 'train')
        dev_groups = _group_file(directory, ledger, 'development')
        _require(grouping['inventory']['roots'] == 509 and grouping['inventory']['groups'] == 2056
                 and grouping['inventory']['fork_rows'] == 6750 and dev_groups['inventory']['fork_rows'] == 2735,
                 'Frozen group/row/root inventory mismatch')
        _require({(g['game'], g['root_id'], g['own_action']) for g in dev_groups['groups']}
                 == {(r['game'], r['root_id'], a) for r in truth['roots'] for a in r['actions']},
                 'Development truth legal actions differ from complete group inventory')
        _require(_sha(directory/'controls.json') == ledger['controls_sha256'], 'Control file checksum mismatch')
        controls = _read(directory/'controls.json')
        _require(set(controls) == {'zero', 'untrained'} and set(controls['untrained']) == set(map(str, SEEDS)), 'Control inventory mismatch')
        validate_scores(controls['zero'], truth['roots'], 'direct', ('exact',), zero=True)
        baselines = {'zero': _metrics(controls['zero'])}
        for seed in SEEDS:
            validate_scores(controls['untrained'][str(seed)], truth['roots'], 'direct', ('exact',))
            baselines['untrained-'+str(seed)] = _metrics(controls['untrained'][str(seed)])
        _require(ledger['control_decisions'] == 836 and ledger['development_decisions'] == 17556, 'Grid decision counters mismatch')
        cells, artifacts, replayed, environments = [], [], {}, set()
        for item in ledger['runs']:
            path = directory/item['id']; config = Config(**item['config'])
            _require(_sha(path/'receipt.json') == item['receipt_sha256'], 'Receipt checksum mismatch: '+item['id'])
            receipt = _read(path/'receipt.json')
            _require(receipt['config'] == item['config'] and receipt['status'] == 'complete', 'Cell receipt identity/status mismatch')
            identity = rt.identity(config, tm, grouping['group_sha256'], ledger['source'])
            # Preserve historical environment in expected identity; reading on a
            # later compatible interpreter does not rewrite the training cohort.
            for key in ('python', 'numpy'): identity[key] = receipt['identity'][key]
            environments.add((identity['python'], identity['numpy']))
            _require(receipt['identity'] == identity, 'Checkpoint objective/source/config/data identity mismatch')
            checkpoint_sha = _sha(path/'checkpoint.npz')
            _require(checkpoint_sha == receipt['checkpoint_sha256'] == item['checkpoint_sha256'], 'Checkpoint checksum mismatch')
            model = Model.load(path/'checkpoint.npz', config, identity)
            _require(model.step == receipt['step'] == 10560 and model.epoch == receipt['epoch'] == 160,
                     'Checkpoint/receipt step or epoch mismatch')
            _require(receipt['tensor_sha256'] == _digest(rt.tensor_hashes(model)) and receipt['parameters'] == model.parameter_counts(),
                     'Checkpoint tensor/parameter inventory mismatch')
            _require(_sha(path/'history.json') == receipt['history_sha256'], 'History checksum mismatch')
            history = _read(path/'history.json')
            plan_sha = _history(history, config, grouping, replayed)
            budget = _read(path/'budget.json')
            _require(budget['status'] == 'complete' and budget['identity'] == identity and budget['limit_seconds'] == 600.,
                     'Budget journal status/identity/limit mismatch')
            times = [receipt['seconds'], budget['total_seconds'], item['seconds']]
            _require(all(_finite(x) and 0 <= x < 600 for x in times) and times == sorted(times), 'Invalid/unaccounted cell runtime')
            _require(sum(r['seconds'] for r in history) <= receipt['seconds']+1e-9, 'History work exceeds receipt time')
            cells.append(receipt)
            artifacts.append({'id': item['id'], 'receipt_sha256': item['receipt_sha256'], 'checkpoint_sha256': checkpoint_sha,
                              'history_sha256': receipt['history_sha256'], 'budget_sha256': _sha(path/'budget.json'),
                              'tensor_sha256': receipt['tensor_sha256'], 'training_plan_sha256': plan_sha})
        _require(len(environments) == 1, 'Mixed training environments')
        total = sum(item['seconds'] for item in ledger['runs'])
        _require(_finite(ledger['total_cell_seconds']) and 0 <= ledger['total_cell_seconds'] < 25200
                 and math.isclose(total, ledger['total_cell_seconds'], abs_tol=1e-8, rel_tol=1e-12), 'Cumulative cost mismatch/overrun')
        _require(_finite(ledger['preparation_seconds']) and ledger['preparation_seconds'] >= 0
                 and _finite(ledger['total_wall_seconds']) and ledger['total_wall_seconds'] >= total+ledger['preparation_seconds']-1e-8,
                 'Invalid total wall/preparation accounting')
        rss = ledger['process_peak_rss_bytes']
        _require(type(rss) is int and 0 < rss < 1000000000, 'Peak process RSS missing or exceeds cap')
        size = rt.artifact_bytes(directory)
        _require(size < 3000000000, 'Output byte cap exceeded')
        report = summarize(cells, truth)
        report.update(input_directory=str(directory), ledger_sha256=_sha(directory/'ledger.json'), source=ledger['source'],
                      code_commit=ledger['code_commit'], train_manifest=tm, development_manifest=dm,
                      development_truth_sha256=ledger['development_truth_sha256'],
                      development_schedule_sha256=ledger['development_schedule_sha256'],
                      train_group_sha256=grouping['group_sha256'], development_group_sha256=dev_groups['group_sha256'],
                      baselines=baselines, artifacts=artifacts, replayed_epoch_plans=len(replayed),
                      resources={'total_cell_seconds': total, 'total_wall_seconds': ledger['total_wall_seconds'],
                                 'process_peak_rss_bytes': rss, 'memory_scope': 'Process lifetime including inputs and all previous cells',
                                 'artifact_bytes': size, 'array_bytes': ledger['array_bytes']})
        return report
    except (ValueError, KeyError, TypeError, OSError, IndexError, OverflowError) as exc:
        errors.append(type(exc).__name__+': '+str(exc))
        return failed


def markdown(report):
    lines = ['# V2.5 complete-reply development report', '', '**Status: '+report['status']+'**', '',
             'Adaptive development; only raw-tail is the prespecified candidate. No confirmatory or publication claim.', '']
    lines += ['- Verification failure: '+error for error in report['verification_errors']]
    if report.get('selected'):
        lines += ['', '| Family | Exact-selected LR | Exact regret | Hybrid regret | Hybrid action MSE |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for variant, row in report['selected'].items():
            a, b = row['tracks']['exact'], row['tracks']['hybrid']
            lines.append(f"| {variant} | {row['learning_rate']:g} | {a['mean_regret']:.6f} | {b['mean_regret']:.6f} | {b['action_oracle_mse']:.6f} |")
        for track, result in report['tracks'].items():
            lines += ['', f"{track.capitalize()} gate: {'passed' if result['passed'] else 'failed'}.", '',
                      '| Control | Improvement | Root bootstrap 95% interval | Favorable seeds |', '| --- | ---: | --- | ---: |']
            for variant, comparison in result['comparisons'].items():
                low, high = comparison['bootstrap']['aggregate_ci95']
                lines.append(f"| {variant} | {comparison['aggregate_improvement']:.6f} | [{low:.6f}, {high:.6f}] | {comparison['favorable_seeds']}/3 |")
        lines += ['', 'Mechanism gate: '+('passed' if report['mechanism']['passed'] else 'failed')+'.']
        lines += ['- '+reason for reason in report['mechanism']['reasons']]
    lines += ['', 'Every cell and both learning rates remain in the JSON, with per-game results and artifact provenance.', '']
    lines += ['- '+item for item in report.get('limitations', [])]
    return '\n'.join(lines)+'\n'


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid'); parser.add_argument('output')
    args = parser.parse_args()
    result = summarize_grid(args.grid)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=False)
    (output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    (output/'report.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'errors': len(result['verification_errors']), 'output': str(output.resolve())}))
    return 1 if result['verification_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
