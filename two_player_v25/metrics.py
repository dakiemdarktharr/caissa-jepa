"""Read-only development diagnostics with complete legal reply groups."""
import numpy as np

from two_player_v2 import GAMES_V2
from two_player_v2.data import state_from
from two_player_v2.evaluate import representation, _geometry


def summary(values):
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Invalid diagnostic values')
    return {'count': len(x), 'mean': float(x.mean()) if len(x) else None,
            'max': float(x.max()) if len(x) else None,
            'quantiles_0_25_50_75_100': np.quantile(x, [0, .25, .5, .75, 1]).tolist() if len(x) else None}


def array(value, shape):
    x = np.asarray(value)
    if x.shape != shape or x.dtype != np.float64 or not np.isfinite(x).all():
        raise ValueError('Invalid float64 diagnostic model output')
    return x


def diagnostics(model, development, batch, grouping, guard):
    if development['manifest']['split'] != 'development' or grouping['split'] != 'development':
        raise ValueError('Diagnostics require standalone development inputs')
    guard()
    dim = model.config.latent
    direct = model.config.variant == 'direct'
    result = {'stage': 'development', 'weighting': 'Equal complete own-action groups within each game; distinct from occurrence metrics',
              'head_norm': float(np.linalg.norm(model.params['vw'])), 'games': {}, 'collapse': False}
    roots = {r['root_id']: r for r in development['roots']}
    groups = grouping['groups']
    occurrence = {}
    for game in sorted(GAMES_V2):
        guard()
        fork_indices = [i for i, f in enumerate(development['forks']) if f['game'] == game]
        occurrence[game] = representation(model, {k: v[fork_indices] for k, v in batch.items()})
        guard()
        nodes = [node for _, node in sorted(development['nodes'].items()) if node['game'] == game]
        z_parts = []
        for start in range(0, len(nodes), 128):
            guard()
            x = np.stack([GAMES_V2[game].features(state_from(n['state'])) for n in nodes[start:start+128]])
            z_parts.append(array(model.encode(x), (len(x), dim)))
        geometry = _geometry(np.concatenate(z_parts)); guard()
        collapse = geometry['effective_rank'] < 2 or geometry['median_std'] < .001
        result['collapse'] |= collapse
        # Compute each recorded fork only once per horizon; incomplete H2 is masked.
        by_horizon = {}
        for horizon in (1, 2):
            valid_ids = np.asarray([i for i in fork_indices if batch['valid'][i, horizon]], dtype=np.int64)
            targets, target_values, predictions, predicted_values = {}, {}, {}, {}
            for start in range(0, len(valid_ids), 128):
                guard(); ii = valid_ids[start:start+128]
                target = array(model.encode(batch['x'][ii, horizon], target=True), (len(ii), dim))
                value = array(model.value(target), (len(ii), 1)).ravel()
                if not direct:
                    z0 = array(model.encode(batch['x'][ii, 0]), (len(ii), dim))
                    pred = array(model.rollout(z0, batch['actions'][ii], horizon=horizon), (len(ii), dim))
                    pv = array(model.value(pred), (len(ii), 1)).ravel()
                for pos, index in enumerate(ii):
                    targets[int(index)] = target[pos]
                    target_values[int(index)] = float(value[pos])
                    if not direct:
                        predictions[int(index)] = pred[pos]
                        predicted_values[int(index)] = float(pv[pos])
            by_horizon[horizon] = (targets, target_values, predictions, predicted_values)
        rows = []
        for group in groups:
            if group['game'] != game: continue
            guard()
            ids = group['fork_indices']; first = ids[0]
            root = roots[group['root_id']]
            action_index = root['actions'].index(group['own_action'])
            oracle_action = float(root['oracle_values'][action_index])
            row = {'root_id': group['root_id'], 'own_action': group['own_action'],
                   'full_fork_rows': len(ids), 'oracle_action_value': oracle_action, 'horizons': {}}
            for horizon in (1, 2):
                target, tv, pred, pv = by_horizon[horizon]
                candidates = [first] if horizon == 1 else ids
                valid = [i for i in candidates if batch['valid'][i, horizon]]
                selected = [i for i in valid if batch['legal'][i, horizon].any()]
                target_errors = [tv[i]-float(batch['value'][i, horizon, 0]) for i in selected]
                ell = [float(np.mean((pred[i]-target[i])**2)) for i in selected] if not direct else []
                mean = float(np.mean(ell)) if ell else None
                maximum = max(ell) if ell else None
                row['horizons'][str(horizon)] = {
                    'valid_count': len(valid), 'missing_count': len(candidates)-len(valid),
                    'terminal_count': len(valid)-len(selected), 'nonterminal_count': len(selected),
                    'latent_mean': mean, 'latent_max': maximum,
                    'latent_mean_max': .5*(mean+maximum) if ell else None,
                    'target_value_oracle_mse': float(np.mean(np.square(target_errors))) if selected else None,
                    'target_oracle_max_absolute': max(map(abs, target_errors), default=0.),
                    'predicted_value_oracle_mse': float(np.mean([(pv[i]-float(batch['value'][i,horizon,0]))**2 for i in selected])) if selected and not direct else None}
            # Exact terminal values are shared by predicted and target backups.
            if not batch['valid'][first, 2]:
                target_min = -float(batch['value'][first, 1, 0])
                if target_min != oracle_action:
                    raise ValueError('Terminal H1 oracle perspective disagrees with root action')
                predicted_min = None if direct else target_min
                epsilon, bound = 0., None if direct else 0.
                false_pessimistic = False if not direct else None
            else:
                _, tv, _, pv = by_horizon[2]
                truths = np.array([float(batch['value'][i,2,0]) for i in ids])
                target_q = np.array([tv[i] if batch['legal'][i,2].any() else truths[j] for j,i in enumerate(ids)])
                target_min = float(target_q.min())
                epsilon = row['horizons']['2']['target_oracle_max_absolute']
                if direct:
                    predicted_min = bound = false_pessimistic = None
                else:
                    pred_q = np.array([pv[i] if batch['legal'][i,2].any() else truths[j] for j,i in enumerate(ids)])
                    predicted_min = float(pred_q.min())
                    j = row['horizons']['2']['latent_mean_max'] or 0.
                    bound = result['head_norm']*np.sqrt(2*dim*j)+epsilon
                    if abs(predicted_min-oracle_action) > bound+1e-9*max(1.,bound):
                        raise ValueError('Conditional oracle backup bound violated')
                    false_pessimistic = bool(any(q == predicted_min and truth > truths.min() and q < truth
                                                for q,truth in zip(pred_q,truths)))
                if float(truths.min()) != oracle_action:
                    raise ValueError('Oracle group minimum/perspective disagrees with root action')
            row.update(target_min=target_min, predicted_min=predicted_min,
                       target_min_oracle_bias=target_min-oracle_action,
                       predicted_min_oracle_bias=None if direct else predicted_min-oracle_action,
                       predicted_target_min_error=None if direct else predicted_min-target_min,
                       conditional_oracle_bound=None if direct else float(bound),
                       false_pessimistic_noncritical_reply=false_pessimistic)
            rows.append(row)
        metrics = {}
        for key in ('target_min_oracle_bias','predicted_min_oracle_bias','predicted_target_min_error','conditional_oracle_bound'):
            values = [r[key] for r in rows if r[key] is not None]
            metrics[key] = summary(values)
            if 'bias' in key or 'error' in key:
                metrics[key+'_squared'] = summary([v*v for v in values])
        for horizon in ('1', '2'):
            for key in ('latent_mean','latent_max','latent_mean_max','target_value_oracle_mse','target_oracle_max_absolute','predicted_value_oracle_mse'):
                metrics['h'+horizon+'_'+key] = summary([r['horizons'][horizon][key] for r in rows if r['horizons'][horizon][key] is not None])
        result['games'][game] = {'unique_node_geometry': geometry, 'collapse': bool(collapse),
                                'group_count': len(rows), 'groups': rows, 'summary': metrics,
                                'false_pessimistic_count': None if direct else sum(r['false_pessimistic_noncritical_reply'] for r in rows)}
        guard()
    result['collapse'] = bool(result['collapse'])
    return occurrence, result
