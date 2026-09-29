"""Grouped float64 objectives frozen in METHOD_V25; no data/evaluator imports."""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np

FEATURE_SIZE = 198
ACTION_SIZE = 65
OBJECTIVE_VERSION = 'caissa-complete-reply-robust-consistency-v2.5'
VARIANTS = ('direct', 'recurrent-pv', 'decoded-tail', 'scalar-tail',
            'raw-mean', 'raw-tail', 'raw-scaled')
ENCODER_KEYS = ('e1w', 'e1b', 'e2w', 'e2b')
VALUE_KEYS = ('vw', 'vb')
TRANSITION_KEYS = ('g1w', 'g1b', 'g2w', 'g2b')


@dataclass(frozen=True)
class Config:
    variant: str = 'raw-tail'
    seed: int = 17
    hidden: int = 128
    latent: int = 64
    transition_hidden: int = 50
    learning_rate: float = .001
    aux_weight: float = .1
    ema: float = .99
    batch_groups: int = 32

    def __post_init__(self):
        if self.variant not in VARIANTS:
            raise ValueError('Unknown v2.5 variant')
        for name in ('seed', 'hidden', 'latent', 'transition_hidden', 'batch_groups'):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == 'seed' else 1):
                raise ValueError('Invalid integer configuration: ' + name)
        for name in ('learning_rate', 'aux_weight', 'ema'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                raise ValueError('Invalid numeric configuration: ' + name)
        if self.learning_rate <= 0 or self.aux_weight < 0 or not 0 <= self.ema < 1:
            raise ValueError('Invalid optimizer/auxiliary/EMA configuration')


def _batch(batch):
    expected = {'x', 'valid', 'legal', 'policy', 'value', 'actions',
                'value_labelled', 'policy_labelled', 'group'}
    if set(batch) != expected:
        raise ValueError('Invalid grouped batch field inventory')
    b = {key: np.asarray(value) for key, value in batch.items()}
    if b['x'].ndim != 3 or b['x'].shape[1:] != (3, FEATURE_SIZE) or not len(b['x']):
        raise ValueError('Invalid or empty feature batch')
    n = len(b['x'])
    shapes = {'valid': (n, 3), 'legal': (n, 3, ACTION_SIZE),
              'policy': (n, 3, ACTION_SIZE), 'value': (n, 3, 1),
              'actions': (n, 2, ACTION_SIZE), 'value_labelled': (n, 3),
              'policy_labelled': (n, 3), 'group': (n,)}
    for key, shape in shapes.items():
        if b[key].shape != shape:
            raise ValueError('Invalid batch shape: ' + key)
    for key in ('valid', 'legal', 'value_labelled', 'policy_labelled'):
        if b[key].dtype != np.bool_:
            raise ValueError('Batch masks must be boolean')
    for key in ('x', 'policy', 'value', 'actions'):
        if not np.issubdtype(b[key].dtype, np.number) or np.iscomplexobj(b[key]):
            raise ValueError('Batch arrays must be real numeric')
        b[key] = b[key].astype(np.float64, copy=False)
        if not np.isfinite(b[key]).all():
            raise ValueError('Nonfinite batch array')
    group = b['group']
    if (group.dtype != np.int64 or group[0] != 0
            or np.any((np.diff(group) != 0) & (np.diff(group) != 1))):
        raise ValueError('Groups must be contiguous int64 blocks numbered from zero')
    valid, legal = b['valid'], b['legal']
    if not np.all(valid[:, :2]):
        raise ValueError('Every row needs a root and H1')
    if (not np.array_equal(b['value_labelled'], valid)
            or not np.array_equal(b['policy_labelled'], valid & legal.any(-1))):
        raise ValueError('V2.5 requires full observed labels and no terminal policy')
    for key in ('x', 'value', 'policy', 'legal'):
        if np.any(b[key][~valid]):
            raise ValueError('Missing-state placeholders must be zero')
    policy, actions = b['policy'], b['actions']
    if (np.any(policy < 0) or np.any(policy[~legal])
            or not np.allclose(policy.sum(-1), b['policy_labelled'], atol=1e-12, rtol=0)):
        raise ValueError('Invalid legal soft policy targets')
    if np.any(np.abs(b['value']) > 1):
        raise ValueError('Values must be in [-1, 1]')
    if (np.any((actions != 0) & (actions != 1))
            or not np.all(actions[:, 0].sum(-1) == 1)
            or not np.all(actions[:, 1].sum(-1) == valid[:, 2])
            or np.any(actions[:, 0][~legal[:, 0]])
            or np.any(actions[:, 1][~legal[:, 1]])):
        raise ValueError('Illegal one-hot action or missing action mask')
    if not np.array_equal(valid[:, 2], legal[:, 1].any(-1)):
        raise ValueError('H2 must exist exactly when H1 is nonterminal')
    for g in range(int(group[-1]) + 1):
        rows = np.flatnonzero(group == g)
        first = rows[0]
        for key in ('x', 'valid', 'legal', 'policy', 'value', 'value_labelled', 'policy_labelled'):
            if not np.all(b[key][rows, :2] == b[key][first, :2]):
                raise ValueError('Group root/H1 occurrences disagree: ' + key)
        if not np.all(actions[rows, 0] == actions[first, 0]):
            raise ValueError('Group own actions disagree')
        if not np.array_equal(actions[rows, 1].sum(0), legal[first, 1].astype(float)):
            raise ValueError('Group must contain each legal reply exactly once')
        if not valid[first, 2] and len(rows) != 1:
            raise ValueError('Terminal H1 must have one missing-H2 row')
    return b


def _aggregate(errors, groups, mode, factors=None):
    """Equal eligible-group mean and d(loss)/d(per-row residual).

    Max ties use the uniform member of the subdifferential. Scaled factors are
    detached, including when this helper computes their base-point values.
    """
    errors, groups = np.asarray(errors), np.asarray(groups)
    if errors.ndim != 1 or groups.shape != errors.shape:
        raise ValueError('Invalid residual/group shapes')
    if mode not in ('mean', 'tail', 'scaled') or np.any(errors < 0) or not np.isfinite(errors).all():
        raise ValueError('Invalid aggregation mode or residuals')
    ids = np.unique(groups)
    weights = np.zeros_like(errors, dtype=np.float64)
    if not len(ids):
        return 0., weights
    loss = 0.
    for group in ids:
        rows = np.flatnonzero(groups == group)
        e = errors[rows]
        mean, maximum = float(e.mean()), float(e.max())
        if mode == 'mean':
            loss += mean
            weights[rows] = 1 / len(rows)
        elif mode == 'tail':
            ties = e == maximum
            loss += .5 * (mean + maximum)
            weights[rows] = .5 / len(rows) + .5 * ties / ties.sum()
        else:
            factor = (.5 * (mean + maximum) / mean if mean else 0.) if factors is None else float(factors[int(group)])
            if factor < 0 or not np.isfinite(factor):
                raise ValueError('Invalid detached factor')
            loss += factor * mean
            weights[rows] = factor / len(rows)
    return loss / len(ids), weights / len(ids)


class Model:
    def __init__(self, config=Config()):
        if not isinstance(config, Config):
            raise TypeError('Expected Config')
        self.config, self.step, self.epoch = config, 0, 0
        rng = np.random.default_rng(config.seed)
        h, d, t = config.hidden, config.latent, config.transition_hidden

        def weight(rows, columns):
            return rng.normal(0, np.sqrt(1 / rows), (rows, columns))

        self.params = {
            'e1w': weight(FEATURE_SIZE, h), 'e1b': np.zeros(h),
            'e2w': weight(h, d), 'e2b': np.zeros(d),
            'pw': weight(d, ACTION_SIZE), 'pb': np.zeros(ACTION_SIZE),
            'vw': weight(d, 1), 'vb': np.zeros(1),
            'g1w': weight(d + ACTION_SIZE, t), 'g1b': np.zeros(t),
            'g2w': weight(t, d), 'g2b': np.zeros(d),
            'dw': weight(d, FEATURE_SIZE), 'db': np.zeros(FEATURE_SIZE),
        }
        self.target = {key: self.params[key].copy() for key in ENCODER_KEYS + VALUE_KEYS}
        self.m = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.v = {key: np.zeros_like(value) for key, value in self.params.items()}

    @property
    def horizons(self):
        return () if self.config.variant == 'direct' else (1, 2)

    def encode(self, x, target=False):
        p = self.target if target else self.params
        hidden = np.tanh(np.asarray(x, dtype=np.float64) @ p['e1w'] + p['e1b'])
        return np.tanh(hidden @ p['e2w'] + p['e2b'])

    def value(self, z, target=False):
        p = self.target if target else self.params
        return np.tanh(z @ p['vw'] + p['vb'])

    def policy_logits(self, z):
        return z @ self.params['pw'] + self.params['pb']

    def _transition(self, z, action):
        cat = np.concatenate((z, action), axis=-1)
        hidden = np.tanh(cat @ self.params['g1w'] + self.params['g1b'])
        out = np.tanh(hidden @ self.params['g2w'] + self.params['g2b'])
        return out, (cat, hidden, out)

    def rollout(self, z, actions, horizon=2):
        z, actions = np.asarray(z, dtype=np.float64), np.asarray(actions, dtype=np.float64)
        if type(horizon) is not int or horizon not in (1, 2):
            raise ValueError('Rollout horizon must be one or two')
        if z.ndim != 2 or z.shape[1] != self.config.latent or actions.shape != (len(z), 2, ACTION_SIZE):
            raise ValueError('Invalid rollout shapes')
        if not np.isfinite(z).all() or not np.isfinite(actions).all():
            raise ValueError('Nonfinite rollout inputs')
        for index in range(horizon):
            z, _ = self._transition(z, actions[:, index])
        return z

    def detached_context(self, batch):
        """Base-point targets/factors for numerical differentiation only.

        Normal training derives these afresh. Numerical loss differences must
        hold the whole scalar target branch (including online head) and the
        raw-scaled allocation factor fixed, exactly as analytical gradients do.
        """
        b = _batch(batch)
        n, groups = len(b['group']), int(b['group'][-1]) + 1
        result = {'scalar_targets': None, 'scaled_factors': None}
        if self.config.variant == 'scalar-tail':
            targets = np.zeros((n, 3, 1))
            mask = b['valid']
            targets[mask] = self.value(self.encode(b['x'][mask], target=True))
            result['scalar_targets'] = targets
        if self.config.variant == 'raw-scaled':
            factors = np.zeros(groups)
            mask = b['valid'][:, 2] & b['legal'][:, 2].any(-1)
            if mask.any():
                pred = self.rollout(self.encode(b['x'][:, 0]), b['actions'], 2)[mask]
                delta = pred - self.encode(b['x'][mask, 2], target=True)
                errors = np.mean(delta**2, axis=-1)
                for group in np.unique(b['group'][mask]):
                    e = errors[b['group'][mask] == group]
                    mean = float(e.mean())
                    factors[group] = .5 * (mean + float(e.max())) / mean if mean else 0.
            result['scaled_factors'] = factors
        return result

    def loss_grad(self, batch, *, detached=None):
        b = _batch(batch)
        p, c = self.params, self.config
        valid, group = b['valid'], b['group']
        n, group_count = len(group), int(group[-1]) + 1
        sizes = np.bincount(group)
        row_weight = 1. / sizes[group]
        weights = np.broadcast_to(row_weight[:, None], valid.shape)[valid]
        first = np.r_[0, np.flatnonzero(np.diff(group)) + 1]
        x = b['x'][valid]
        hidden = np.tanh(x @ p['e1w'] + p['e1b'])
        z = np.tanh(hidden @ p['e2w'] + p['e2b'])
        all_z = np.zeros((n, 3, c.latent))
        all_z[valid] = z
        dz = np.zeros_like(z)
        grad = {key: np.zeros_like(value) for key, value in p.items()}
        if detached is not None:
            if set(detached) != {'scalar_targets', 'scaled_factors'}:
                raise ValueError('Invalid detached context inventory')
            for key, shape, needed in (
                    ('scalar_targets', (n, 3, 1), c.variant == 'scalar-tail'),
                    ('scaled_factors', (group_count,), c.variant == 'raw-scaled')):
                item = detached[key]
                if needed and (not isinstance(item, np.ndarray) or item.shape != shape or not np.isfinite(item).all()):
                    raise ValueError('Invalid detached context: ' + key)
                if not needed and item is not None:
                    raise ValueError('Unexpected detached context: ' + key)

        def value_loss(states, targets, w, coefficient):
            result = np.zeros_like(states)
            denominator = float(w.sum())
            if not denominator:
                return 0., result
            pred = self.value(states)
            delta = pred - targets
            loss = float(np.sum(w[:, None] * delta**2) / denominator)
            dv = 2 * coefficient * w[:, None] / denominator * delta * (1 - pred**2)
            grad['vw'] += states.T @ dv
            grad['vb'] += dv.sum(0)
            result += dv @ p['vw'].T
            return loss, result

        def policy_loss(states, targets, legal, w, coefficient):
            result = np.zeros_like(states)
            denominator = float(w.sum())
            if not denominator:
                return 0., result
            logits = np.where(legal, self.policy_logits(states), -np.inf)
            shifted = logits - logits.max(-1, keepdims=True)
            lognorm = np.log(np.exp(shifted).sum(-1, keepdims=True))
            logprob = np.where(legal, shifted - lognorm, 0.)
            loss = float(-np.sum(w[:, None] * targets * logprob) / denominator)
            dl = coefficient * w[:, None] / denominator * (np.exp(shifted - lognorm) - targets)
            grad['pw'] += states.T @ dl
            grad['pb'] += dl.sum(0)
            result += dl @ p['pw'].T
            return loss, result

        policy_mask = b['policy_labelled'][valid]
        value_mse, dv = value_loss(z, b['value'][valid], weights, 1.)
        dz += dv
        policy_nll, dp = policy_loss(z[policy_mask], b['policy'][valid][policy_mask],
                                     b['legal'][valid][policy_mask], weights[policy_mask], 1.)
        dz[policy_mask] += dp
        total = value_mse + policy_nll
        metrics = {
            'samples': n, 'group_count': group_count, 'encoded_count': int(valid.sum()),
            'value_count': int(valid.sum()), 'policy_count': int(policy_mask.sum()),
            'terminal_count': int((valid & ~b['legal'].any(-1)).sum()),
            'value_unlabelled_count': 0, 'policy_unlabelled_count': 0,
            'encoded_weight_sum': float(weights.sum()), 'value_weight_sum': float(weights.sum()),
            'policy_weight_sum': float(weights[policy_mask].sum()),
            'value_mse': value_mse, 'policy_nll': policy_nll,
            'h2_max_tie_group_count': 0, 'h2_max_tie_member_count': 0,
            'h2_scaled_factor_count': 0, 'h2_scaled_factor_nonzero_count': 0,
            'h2_scaled_factor_sum': 0., 'h2_scaled_factor_mean': 0.,
            'h2_scaled_factor_min': 0., 'h2_scaled_factor_max': 0.,
            'h2_scaled_factor_clip_count': 0,
        }
        predicted, caches, predicted_grad = {}, {}, {}
        h2_mask = valid[:, 2]
        if self.horizons:
            predicted[1], caches[1] = self._transition(all_z[:, 0], b['actions'][:, 0])
            predicted[2], caches[2] = self._transition(predicted[1][h2_mask], b['actions'][h2_mask, 1])
        for horizon in (1, 2):
            mask = valid[:, horizon]
            rows = np.flatnonzero(mask)
            nonterminal = mask & b['legal'][:, horizon].any(-1)
            aux_rows = first[nonterminal[first]] if horizon == 1 else np.flatnonzero(nonterminal)
            aux_groups = np.unique(group[aux_rows])
            enabled = horizon in self.horizons
            auxiliary = enabled and c.variant not in ('direct', 'recurrent-pv')
            pol = b['policy_labelled'][mask, horizon]
            metrics.update({
                f'h{horizon}_eligible_count': int(mask.sum()),
                f'h{horizon}_count': int(mask.sum()) if enabled else 0,
                f'h{horizon}_missing_count': n - int(mask.sum()),
                f'h{horizon}_terminal_count': int((mask & ~nonterminal).sum()),
                f'h{horizon}_value_label_count': int(mask.sum()) if enabled else 0,
                f'h{horizon}_policy_label_count': int(pol.sum()) if enabled else 0,
                f'h{horizon}_value_weight_sum': float(row_weight[mask].sum()) if enabled else 0.,
                f'h{horizon}_policy_weight_sum': float(row_weight[mask][pol].sum()) if enabled else 0.,
                f'h{horizon}_aux_eligible_group_count': len(aux_groups),
                f'h{horizon}_aux_eligible_row_count': int(nonterminal.sum()),
                f'h{horizon}_aux_group_count': len(aux_groups) if auxiliary else 0,
                f'h{horizon}_aux_row_count': len(aux_rows) if auxiliary else 0,
                f'h{horizon}_aux_excluded_group_count': group_count - len(aux_groups),
                f'h{horizon}_loss': 0., f'h{horizon}_aux_loss': 0.,
                f'h{horizon}_value_mse': 0., f'h{horizon}_value_loss': 0.,
                f'h{horizon}_policy_nll': 0., f'h{horizon}_policy_loss': 0.,
            })
            if not enabled:
                continue
            pred = predicted[horizon]
            dpred = np.zeros_like(pred)
            predicted_grad[horizon] = dpred
            mse, extra = value_loss(pred, b['value'][mask, horizon], row_weight[mask], .25)
            dpred += extra
            nll, extra = policy_loss(pred[pol], b['policy'][mask, horizon][pol],
                                     b['legal'][mask, horizon][pol], row_weight[mask][pol], .25)
            dpred[pol] += extra
            total += .25 * (mse + nll)
            metrics.update({f'h{horizon}_value_mse': mse, f'h{horizon}_value_loss': .25*mse,
                            f'h{horizon}_policy_nll': nll, f'h{horizon}_policy_loss': .25*nll})
            if not auxiliary or not len(aux_rows):
                continue
            local = np.searchsorted(rows, aux_rows)
            states = pred[local]
            if c.variant == 'decoded-tail':
                delta = states @ p['dw'] + p['db'] - b['x'][aux_rows, horizon]
            elif c.variant == 'scalar-tail':
                pv = self.value(states)
                target_v = (self.value(self.encode(b['x'][aux_rows, horizon], target=True))
                            if detached is None else detached['scalar_targets'][aux_rows, horizon])
                delta = pv - target_v
            else:
                delta = states - self.encode(b['x'][aux_rows, horizon], target=True)
            errors = np.mean(delta**2, axis=-1)
            mode = 'mean' if horizon == 1 or c.variant == 'raw-mean' else ('scaled' if c.variant == 'raw-scaled' else 'tail')
            factors = detached['scaled_factors'] if detached is not None and mode == 'scaled' else None
            if horizon == 2:
                used_factors = []
                for gid in aux_groups:
                    e = errors[group[aux_rows] == gid]
                    tied = int(np.count_nonzero(e == e.max()))
                    # Singleton maxima are not ties; member count covers tied groups only.
                    if tied > 1:
                        metrics['h2_max_tie_group_count'] += 1
                        metrics['h2_max_tie_member_count'] += tied
                    if mode == 'scaled':
                        mean = float(e.mean())
                        used_factors.append((.5*(mean+float(e.max()))/mean if mean else 0.)
                                            if factors is None else float(factors[gid]))
                if used_factors:
                    f = np.asarray(used_factors)
                    metrics.update(h2_scaled_factor_count=len(f),
                                   h2_scaled_factor_nonzero_count=int(np.count_nonzero(f)),
                                   h2_scaled_factor_sum=float(f.sum()),
                                   h2_scaled_factor_mean=float(f.mean()),
                                   h2_scaled_factor_min=float(f.min()),
                                   h2_scaled_factor_max=float(f.max()))
            loss, allocation = _aggregate(errors, group[aux_rows], mode, factors)
            derivative = 2 * c.aux_weight * allocation[:, None] * delta / delta.shape[1]
            if c.variant == 'decoded-tail':
                grad['dw'] += states.T @ derivative
                grad['db'] += derivative.sum(0)
                dpred[local] += derivative @ p['dw'].T
            elif c.variant == 'scalar-tail':
                derivative *= (1 - pv**2)
                grad['vw'] += states.T @ derivative
                grad['vb'] += derivative.sum(0)
                dpred[local] += derivative @ p['vw'].T
            else:
                dpred[local] += derivative
            total += c.aux_weight * loss
            metrics[f'h{horizon}_loss'] = loss
            metrics[f'h{horizon}_aux_loss'] = c.aux_weight * loss

        root_dz = np.zeros((n, c.latent))
        for horizon in reversed(self.horizons):
            cat, gh, out = caches[horizon]
            dout = predicted_grad[horizon] * (1 - out**2)
            grad['g2w'] += gh.T @ dout
            grad['g2b'] += dout.sum(0)
            dh = (dout @ p['g2w'].T) * (1 - gh**2)
            grad['g1w'] += cat.T @ dh
            grad['g1b'] += dh.sum(0)
            back = (dh @ p['g1w'].T)[:, :c.latent]
            if horizon == 2:
                predicted_grad[1][h2_mask] += back
            else:
                root_dz += back
        normalized = weights / weights.sum()
        centered = z - np.sum(normalized[:, None] * z, axis=0)
        population = np.sum(normalized[:, None] * centered**2, axis=0)
        std = np.sqrt(population + 1e-4)
        shortfall = np.maximum(0., .1 - std)
        coefficient = .1 if self.horizons else 0.
        variance = coefficient * float(np.mean(shortfall**2))
        dz += -2 * coefficient / c.latent * normalized[:, None] * centered * shortfall / std
        full_dz = np.zeros_like(all_z)
        full_dz[valid] = dz
        full_dz[:, 0] += root_dz
        de2 = full_dz[valid] * (1 - z**2)
        grad['e2w'] += hidden.T @ de2
        grad['e2b'] += de2.sum(0)
        de1 = (de2 @ p['e2w'].T) * (1 - hidden**2)
        grad['e1w'] += x.T @ de1
        grad['e1b'] += de1.sum(0)
        total += variance
        metrics.update(loss=total, variance_loss=variance, latent_std=float(np.sqrt(population).mean()))
        if not np.isfinite(total) or any(not np.isfinite(g).all() for g in grad.values()):
            raise FloatingPointError('Nonfinite loss or gradient')
        return metrics, grad

    def update(self, batch):
        metrics, grad = self.loss_grad(batch)
        norm = float(np.sqrt(sum(np.sum(g*g) for g in grad.values())))
        if not np.isfinite(norm):
            raise FloatingPointError('Nonfinite gradient norm')
        scale = min(1., 5 / max(norm, 1e-12))
        step = self.step + 1
        new_m, new_v, new_params = {}, {}, {}
        for key, parameter in self.params.items():
            g = grad[key] * scale
            new_m[key] = .9*self.m[key] + .1*g
            new_v[key] = .999*self.v[key] + .001*g*g
            new_params[key] = parameter - self.config.learning_rate * (new_m[key]/(1-.9**step)) / (np.sqrt(new_v[key]/(1-.999**step)) + 1e-8)
        new_target = {key: self.config.ema*target + (1-self.config.ema)*new_params[key]
                      for key, target in self.target.items()}
        if any(not np.isfinite(a).all() for group in (new_params, new_m, new_v, new_target) for a in group.values()):
            raise FloatingPointError('Nonfinite optimizer/EMA update')
        self.params, self.m, self.v, self.target, self.step = new_params, new_m, new_v, new_target, step
        metrics.update(gradient_norm=norm, gradient_scale=scale)
        return metrics

    def parameter_counts(self):
        keys = list(ENCODER_KEYS) + ['pw', 'pb', 'vw', 'vb']
        if self.horizons:
            keys += list(TRANSITION_KEYS)
        if self.config.variant == 'decoded-tail' and self.config.aux_weight:
            keys += ['dw', 'db']
        return {'allocated': sum(a.size for a in self.params.values()),
                'active': sum(self.params[key].size for key in keys),
                'ema': sum(a.size for a in self.target.values()),
                'transition': sum(self.params[key].size for key in TRANSITION_KEYS)}

    def save(self, path, identity):
        if not isinstance(identity, dict) or not identity:
            raise ValueError('A nonempty source/config/data identity is required')
        if type(self.step) is not int or type(self.epoch) is not int or min(self.step, self.epoch) < 0:
            raise ValueError('Invalid checkpoint counters')
        template = Model(self.config)
        arrays = {}
        for prefix, name in (('p_', 'params'), ('t_', 'target'), ('m_', 'm'), ('v_', 'v')):
            group, expected = getattr(self, name), getattr(template, name)
            if set(group) != set(expected):
                raise ValueError('Invalid checkpoint tensor inventory')
            for key, a in group.items():
                if a.shape != expected[key].shape or a.dtype != np.float64 or not np.isfinite(a).all():
                    raise ValueError('Invalid checkpoint tensor')
                if prefix == 'v_' and np.any(a < 0):
                    raise ValueError('Invalid Adam second moment')
                arrays[prefix+key] = a
        metadata = {'method': OBJECTIVE_VERSION, 'config': asdict(self.config), 'identity': identity,
                    'step': self.step, 'epoch': self.epoch,
                    'array_hashes': {key: hashlib.sha256(a.tobytes()).hexdigest() for key, a in arrays.items()}}
        arrays['metadata'] = np.array(json.dumps(metadata, sort_keys=True, allow_nan=False))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=path.name+'.', suffix='.tmp', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                np.savez_compressed(stream, **arrays)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path, config, identity):
        if not isinstance(identity, dict) or not identity:
            raise ValueError('A nonempty source/config/data identity is required')
        with np.load(path, allow_pickle=False) as file:
            metadata = json.loads(str(file['metadata']))
            if set(metadata) != {'method', 'config', 'identity', 'step', 'epoch', 'array_hashes'}:
                raise ValueError('Checkpoint metadata inventory mismatch')
            if metadata['method'] != OBJECTIVE_VERSION or metadata['config'] != asdict(config) or metadata['identity'] != identity:
                raise ValueError('Checkpoint source/config/data/objective identity mismatch')
            model = cls(config)
            groups = (('p_', model.params), ('t_', model.target), ('m_', model.m), ('v_', model.v))
            expected = {prefix+key for prefix, group in groups for key in group}
            if set(file.files) != expected | {'metadata'} or set(metadata['array_hashes']) != expected:
                raise ValueError('Checkpoint tensor inventory mismatch')
            for prefix, group in groups:
                for key in group:
                    array = file[prefix+key]
                    if array.shape != group[key].shape or array.dtype != np.float64 or not np.isfinite(array).all():
                        raise ValueError('Invalid checkpoint tensor')
                    if hashlib.sha256(array.tobytes()).hexdigest() != metadata['array_hashes'][prefix+key]:
                        raise ValueError('Checkpoint tensor checksum mismatch')
                    if prefix == 'v_' and np.any(array < 0):
                        raise ValueError('Invalid Adam second moment')
                    group[key] = array.copy()
            if type(metadata['step']) is not int or type(metadata['epoch']) is not int or min(metadata['step'], metadata['epoch']) < 0:
                raise ValueError('Invalid checkpoint counters')
            model.step, model.epoch = metadata['step'], metadata['epoch']
            return model
