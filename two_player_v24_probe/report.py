"""Pure arithmetic/report validation for the frozen training-only H1 probe."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
import statistics

from two_player_v22.model import Config

GAMES = ('connect4-4x5', 'reversi6')
FAMILIES = ('direct', 'value-dynamics', 'raw-jepa')
CAPACITIES = ((64, 32), (128, 64))
SEEDS = (17, 29, 43)
SPACES = ('online', 'ema')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label, nonnegative=True):
    require(type(value) in (int, float) and math.isfinite(value), 'Invalid '+label)
    require(not nonnegative or value >= 0, 'Negative '+label)
    return value


def count(value, label):
    require(type(value) is int and value >= 0, 'Invalid '+label+' count')
    return value


def close(a, b):
    return math.isclose(number(a, 'ratio'), number(b, 'ratio'), rel_tol=1e-10, abs_tol=1e-12)


def ratio(value, numerator, denominator, label):
    if numerator is None or denominator == 0:
        require(value is None, label+' must be unavailable')
    else:
        require(close(value, numerator/denominator), label+' normalization mismatch')


def quantiles(value, supported, label):
    if not supported:
        require(value is None, label+' must be unavailable without blocks')
        return
    require(isinstance(value, list) and len(value) == 5, label+' needs five quantiles')
    require(all(number(v, label) >= 0 for v in value) and value == sorted(value), 'Invalid '+label)


def validate_schedule(schedule):
    require(schedule['version'] == 'v24-order-schedule01'
            and schedule['edge_order'] == ['s1a', 's2a', 's1b', 's2b']
            and set(schedule['games']) == set(GAMES), 'Schedule identity mismatch')
    require(schedule['schedule_sha256'] == digest({k: v for k, v in schedule.items() if k != 'schedule_sha256'}),
            'Schedule checksum mismatch')
    result = {}
    for game in GAMES:
        group = schedule['games'][game]
        edges, blocks, declared = group['edges'], group['blocks'], group['counts']
        require(group['edge_sha256'] == digest(edges) and group['block_sha256'] == digest(blocks),
                'Edge/block checksum mismatch')
        require(len({(e['root_id'], e['action']) for e in edges}) == len(edges), 'Repeated H1 edge')
        roots = {}
        for edge in edges:
            require(type(edge['player']) is int and edge['player'] in (-1, 1)
                    and edge['target_player'] == -edge['player']
                    and type(edge['action']) is int and 0 <= edge['action'] <= 64
                    and type(edge['target_terminal']) is bool, 'Invalid edge perspective/action/terminal')
            require(number(edge['target_value'], 'target value', nonnegative=False) in (-1, 0, 1), 'Invalid oracle value')
            root = edge['root_id']
            state = (edge['player'], edge['source_id'])
            require(root not in roots or roots[root] == state, 'Root identity differs between actions')
            roots[root] = state
        used, histogram = set(), {str(n): 0 for n in range(5)}
        for block in blocks:
            ids = block['edges']
            require(isinstance(ids, list) and len(ids) == 4 and len(set(ids)) == 4
                    and all(type(i) is int and 0 <= i < len(edges) for i in ids), 'Invalid four-edge block')
            require(not used.intersection(ids), 'Blocks overlap H1 edges')
            used.update(ids)
            a, b, c, d = [edges[i] for i in ids]
            require(a['root_id'] == c['root_id'] < b['root_id'] == d['root_id']
                    and a['action'] == b['action'] < c['action'] == d['action']
                    and len({e['player'] for e in (a, b, c, d)}) == 1,
                    'Block is not the declared state-pair across two common actions')
            identity = [2401, game, a['root_id'], b['root_id'], a['action'], c['action']]
            require(block['identity'] == identity and block['sha256'] == digest(identity), 'Block identity/hash mismatch')
            terminals = sum(e['target_terminal'] for e in (a, b, c, d))
            require(block['terminal_count'] == terminals, 'Block terminal stratum changed')
            histogram[str(terminals)] += 1
        nt_edges = sum(not e['target_terminal'] for e in edges)
        require(declared['roots'] == len(roots) and declared['selected_blocks'] == len(blocks)
                and declared['total_h1_edges'] == len(edges) and declared['used_edges'] == len(used)
                and declared['terminal_block_counts'] == histogram
                and declared['nonterminal_blocks'] == histogram['0']
                and declared['all_nonterminal_edges'] == nt_edges
                and declared['used_nonterminal_edges'] == 4*histogram['0'], 'Packing count inventory mismatch')
        ratio(declared['used_fraction'], len(used), len(edges), 'Coverage')
        ratio(declared['nonterminal_used_fraction'], 4*histogram['0'], nt_edges, 'Nonterminal coverage')
        require(count(declared['candidate_blocks'], 'candidate blocks') >= len(blocks)
                and count(declared['eligible_root_pairs'], 'eligible root pairs') <= len(roots)*(len(roots)-1)//2,
                'Invalid candidate inventory')
        result[game] = {'edges': len(edges), 'blocks': len(blocks), 'nonterminal_edges': nt_edges,
                        'nonterminal_blocks': histogram['0'], 'used_edges': len(used),
                        'terminal_block_counts': histogram, 'edge_sha256': group['edge_sha256'],
                        'block_sha256': group['block_sha256']}
    return result


def value_geometry(group, n, dim, direct):
    for metric in ('target_value_oracle_mse', 'predicted_value_oracle_mse', 'predicted_target_value_mse'):
        value = group[metric]
        if not n or (direct and metric != 'target_value_oracle_mse'):
            require(value is None, 'Absent/direct value measurement must be unavailable')
        else:
            require(number(value, metric) <= 4+1e-9, 'Value MSE exceeds bounded-head range')
    geo = group['target_geometry']
    if not n:
        require(geo is None, 'Empty target geometry must be unavailable')
    else:
        require(geo['samples'] == n and geo['dimensions'] == dim
                and geo['weighting'] == 'Uniform H1 edge targets; repeated successor states retain edge multiplicity',
                'Target geometry weighting/count mismatch')
        require(number(geo['effective_rank'], 'effective rank') <= min(dim, n)+1e-9
                and number(geo['mean_std'], 'mean std') <= 1+1e-9
                and number(geo['median_std'], 'median std') <= 1+1e-9, 'Invalid target geometry')


def validate_row(row, counts):
    config = Config(**row['config'])
    expected = Config(variant=config.variant, hidden=config.hidden, latent=config.latent,
                      seed=config.seed, jepa_weight=.1 if config.variant == 'raw-jepa' else 1.)
    require(asdict(config) == asdict(expected), 'Unfrozen checkpoint configuration')
    require(row['latent_dim'] == config.latent and row['direct'] is (config.variant == 'direct'),
            'Row dimension/direct identity mismatch')
    direct, dim = row['direct'], config.latent
    require(row['predicted_order_violations'] is None if direct else row['predicted_order_violations'] == 0,
            'Predicted ordering violation or direct dynamics measured')
    for key, n in (('all_h1', counts['edges']), ('all_nonterminal', counts['nonterminal_edges'])):
        group = row[key]
        require(count(group['edge_count'], key) == n, 'Full edge inventory mismatch')
        sse = group['latent_sse']
        if direct:
            require(sse is None and group['latent_mse'] is None, 'Direct unused dynamics were scored')
        else:
            number(sse, key+' SSE')
            ratio(group['latent_mse'], sse, n*dim, key+' MSE')
        value_geometry(group, n, dim, direct)
    if not direct:
        require(row['all_nonterminal']['latent_sse'] <= row['all_h1']['latent_sse']+1e-10,
                'Nonterminal SSE exceeds full SSE')
    for key, nblocks, full in (('packed', counts['blocks'], row['all_h1']),
                              ('packed_nonterminal', counts['nonterminal_blocks'], row['all_nonterminal'])):
        group = row[key]
        require(count(group['block_count'], key) == nblocks and count(group['edge_count'], key) == 4*nblocks,
                'Packed inventory mismatch')
        value_geometry(group, 4*nblocks, dim, direct)
        bound = number(group['bound_sse'], 'bound SSE')
        if not nblocks:
            require(bound == 0, 'Empty packing has nonzero bound')
        ratio(group['bound_mse'], bound, 4*nblocks*dim, key+' bound MSE')
        ratio(group['full_bound_mse'], bound, full['edge_count']*dim, key+' full bound MSE')
        number(group['head_norm'], 'head norm')
        comparisons = count(group['coordinate_comparisons'], 'coordinate comparisons')
        require(comparisons == nblocks*dim, 'Coordinate denominator mismatch')
        strict = count(group['reversals_strict'], 'strict reversal')
        large = count(group['reversals_1e6'], 'tolerance reversal')
        ties = count(group['near_ties_1e6'], 'near tie')
        require(large <= strict <= comparisons and ties <= comparisons
                and large+ties <= comparisons and strict <= large+ties,
                'Inconsistent overlapping reversal/near-tie counts')
        for name in ('absolute_gap_quantiles', 'min_absolute_gap_quantiles', 'target_value_gap_quantiles'):
            quantiles(group[name], bool(nblocks), name)
        observed = group['latent_sse']
        if direct:
            require(observed is None and group['latent_mse'] is None
                    and group['bound_packed_sse_ratio'] is None and group['bound_full_sse_ratio'] is None,
                    'Direct prediction error/ratios must be unavailable')
        else:
            number(observed, 'packed SSE')
            require(nblocks > 0 or observed == 0, 'Empty packing has nonzero observed SSE')
            tolerance = 1e-10*max(1, observed, bound)
            require(bound <= observed+tolerance, 'Conditional bound exceeds observed packed SSE')
            require(observed <= full['latent_sse']+1e-10*max(1, full['latent_sse']),
                    'Packed SSE exceeds matching full SSE')
            ratio(group['latent_mse'], observed, 4*nblocks*dim, key+' observed MSE')
            ratio(group['bound_packed_sse_ratio'], bound if nblocks else None, observed, key+' packed ratio')
            ratio(group['bound_full_sse_ratio'], bound if nblocks else None, full['latent_sse'], key+' full ratio')
    require(row['packed_nonterminal']['bound_sse'] <= row['packed']['bound_sse']+1e-10,
            'Nonterminal bound exceeds total bound')
    require(close(row['packed']['head_norm'], row['packed_nonterminal']['head_norm']), 'Head norm differs across strata')


def screen(rows, coverage, packed_key):
    values = [r[packed_key]['bound_full_sse_ratio'] for r in rows]
    available = all(v is not None for v in values)
    median = statistics.median(values) if available else None
    favorable = sum(v is not None and v >= .1 for v in values)
    passed = bool(coverage >= .25 and available and median >= .1 and favorable >= 2)
    return {'coverage': coverage, 'ratios_by_seed': dict(zip(map(str, SEEDS), values)),
            'median_bound_full_sse_ratio': median, 'seeds_at_least_0_10': favorable,
            'material_obstruction': passed,
            'interpretation': 'material conditional obstruction under the heuristic screen' if passed
            else 'not established by this conservative screen; additive adequacy is not proved'}


def summarize(rows, schedule):
    """Validate all 72 contextual rows and summarize the frozen primary screen.

    Source/checkpoint/data/resource verification belongs to the runtime. This
    pure function never loads artifacts, fits, encodes or scores a planner.
    """
    result = {'version': 'v24-order-probe-report01', 'stage': 'training-only architecture probe',
              'status': 'inconclusive', 'verification_errors': [], 'rows': deepcopy(rows),
              'screens': [], 'candidate': None,
              'limitations': [
                  'Valid only with a complete runtime journal and matching report hash.',
                  'Frozen H1 target coordinates only; no irreducible joint encoder/model or H2 claim.',
                  'Uniform unique root/action edges, not the fork-sampled training objective or equal-root value error.',
                  'A low conservative bound or coverage does not establish additive adequacy.',
                  'Heuristic thresholds are not statistical significance or proof of planning failure.',
                  'Terminal errors may be overridden in planning; nonterminal sensitivity never replaces the primary screen.',
                  'No candidate promotion, new fitting, development/protected scoring or game-strength claim.']}
    try:
        counts = validate_schedule(schedule)
        expected = {(v, h, d, s, g, t) for v in FAMILIES for h, d in CAPACITIES
                    for s in SEEDS for g in GAMES for t in SPACES}
        observed, lookup = [], {}
        for row in rows:
            c = row['config']
            key = (c['variant'], c['hidden'], c['latent'], c['seed'], row['game'], row['target_space'])
            observed.append(key); lookup[key] = row
        require(len(observed) == 72 and set(observed) == expected, 'Expected exactly 72 distinct frozen context rows')
        for row in rows:
            validate_row(row, counts[row['game']])
        for game in GAMES:
            n = counts[game]
            coverage = 4*n['blocks']/n['edges'] if n['edges'] else 0.
            nt_coverage = 4*n['nonterminal_blocks']/n['nonterminal_edges'] if n['nonterminal_edges'] else 0.
            for h, d in CAPACITIES:
                primary = [lookup['raw-jepa', h, d, seed, game, 'ema'] for seed in SEEDS]
                main = screen(primary, coverage, 'packed')
                sensitivity = screen(primary, nt_coverage, 'packed_nonterminal')
                relevance = ('nonterminal sensitivity also meets its screen' if sensitivity['material_obstruction']
                             else 'terminal-sensitive or unsupported for nonterminal planning') if main['material_obstruction'] else 'primary obstruction not established'
                result['screens'].append({'game': game, 'hidden': h, 'latent': d,
                    'family': 'raw-jepa', 'target_space': 'ema', 'primary': main,
                    'nonterminal_sensitivity': sensitivity, 'planning_relevance_limit': relevance})
        result.update(status='verified_probe', schedule_counts=counts)
    except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        result['verification_errors'].append(str(exc))
        result['screens'] = []
    return result


def markdown(result):
    lines = ['# V2.4 fixed-target additive-order probe', '', 'Status: **'+result['status']+'**.', '',
             'Training-only H1 architecture diagnostic. No candidate is promoted.', '',
             '**Valid only with a complete runtime journal and matching report hash.**', '']
    if result['verification_errors']:
        lines += ['- '+error for error in result['verification_errors']] + ['']
    if result['screens']:
        lines += ['Primary: raw JEPA, actual EMA targets. Ratios use all H1 edge SSE.', '',
                  '| Game / capacity | Coverage | Seed ratios 17 / 29 / 43 | Median | Screen | Nonterminal interpretation |',
                  '| --- | ---: | --- | ---: | --- | --- |']
        def fmt(v): return 'N/A' if v is None else f'{v:.6f}'
        for row in result['screens']:
            p = row['primary']
            lines.append(f"| {row['game']} {row['hidden']}/{row['latent']} | {p['coverage']:.3%} | "+
                         ' / '.join(fmt(v) for v in p['ratios_by_seed'].values())+
                         f" | {fmt(p['median_bound_full_sse_ratio'])} | {p['material_obstruction']} | {row['planning_relevance_limit']} |")
        lines += ['', 'Fixed all-four-nonterminal sensitivity; no repacking. Ratios use all nonterminal H1 edge SSE.', '',
                  '| Game / capacity | NT coverage | Seed ratios 17 / 29 / 43 | Median | Sensitivity screen |',
                  '| --- | ---: | --- | ---: | --- |']
        for row in result['screens']:
            p = row['nonterminal_sensitivity']
            lines.append(f"| {row['game']} {row['hidden']}/{row['latent']} | {p['coverage']:.3%} | "+
                         ' / '.join(fmt(v) for v in p['ratios_by_seed'].values())+
                         f" | {fmt(p['median_bound_full_sse_ratio'])} | {p['material_obstruction']} |")
        lines += ['', 'All 72 contextual rows, online/EMA spaces, direct target diagnostics, gap quantiles and distinct packed/full denominators remain in the JSON.',
                  'Strict reversals and near ties can overlap; they are not disjoint categories.', '']
    lines += ['- '+text for text in result['limitations']]
    return '\n'.join(lines)+'\n'
