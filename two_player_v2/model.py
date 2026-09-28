"""Float64 recurrent JEPA controls from METHOD_V2; no dataset or GUI imports."""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np

FEATURE_SIZE = 198
ACTION_SIZE = 65
OBJECTIVE_VERSION = 'caissa-recurrent-reply-fork-v2.0'
VARIANTS = ('direct', 'value-dynamics', 'decoded', 'rjepa', 'raw-jepa', 'no-response')
ENCODER_KEYS = ('e1w', 'e1b', 'e2w', 'e2b')
PROJECTOR_KEYS = ('jw', 'jb')


@dataclass(frozen=True)
class Config:
    variant: str = 'rjepa'
    seed: int = 17
    hidden: int = 64
    latent: int = 32
    projection: int = 16
    learning_rate: float = .001
    jepa_weight: float = 1.
    ema: float = .99
    batch_size: int = 128

    def __post_init__(self):
        if self.variant not in VARIANTS:
            raise ValueError('Unknown v2 model variant')
        for name in ('seed', 'hidden', 'latent', 'projection', 'batch_size'):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == 'seed' else 2):
                raise ValueError('Invalid integer model configuration')
        if (not np.isfinite(self.learning_rate) or self.learning_rate <= 0
                or not np.isfinite(self.jepa_weight) or self.jepa_weight < 0
                or not np.isfinite(self.ema) or not 0 <= self.ema < 1):
            raise ValueError('Invalid optimizer, objective, or EMA configuration')


def _normalize(x):
    norm = np.sqrt(np.sum(x*x, axis=-1, keepdims=True) + 1e-6)
    return x / norm, norm


def _normalization_backward(x, norm, gradient):
    return gradient / norm - x * np.sum(gradient*x, axis=-1, keepdims=True) / norm**3


def _batch(batch):
    expected = {'x', 'valid', 'legal', 'policy', 'value', 'actions'}
    if set(batch) != expected:
        raise ValueError('Invalid batch field inventory')
    arrays = {key: np.asarray(value) for key, value in batch.items()}
    x = arrays['x']
    if x.ndim != 3 or x.shape[1:] != (3, FEATURE_SIZE) or len(x) == 0:
        raise ValueError('Invalid or empty feature batch')
    n = len(x)
    shapes = {'valid': (n, 3), 'legal': (n, 3, ACTION_SIZE),
              'policy': (n, 3, ACTION_SIZE), 'value': (n, 3, 1),
              'actions': (n, 2, ACTION_SIZE)}
    for key, shape in shapes.items():
        if arrays[key].shape != shape:
            raise ValueError('Invalid batch shape: ' + key)
    for key in ('valid', 'legal'):
        if arrays[key].dtype != np.bool_:
            raise ValueError('Batch masks must be boolean')
    for key in ('x', 'policy', 'value', 'actions'):
        if not np.issubdtype(arrays[key].dtype, np.number):
            raise ValueError('Non-numeric batch array')
        arrays[key] = arrays[key].astype(np.float64, copy=False)
        if not np.all(np.isfinite(arrays[key])):
            raise ValueError('Nonfinite batch array')
    valid, legal = arrays['valid'], arrays['legal']
    policy, actions = arrays['policy'], arrays['actions']
    if not np.all(valid[:, :2]):
        raise ValueError('Each fork requires a root and H1 successor')
    if (np.any(legal[~valid]) or np.any(arrays['x'][~valid])
            or np.any(arrays['value'][~valid]) or np.any(policy[~valid])):
        raise ValueError('Missing-state slots must be zero and masked')
    if (np.any(policy < 0) or np.any(policy[~legal])
            or not np.allclose(policy.sum(-1), legal.any(-1).astype(float), atol=1e-12, rtol=0)):
        raise ValueError('Invalid legal soft policy targets')
    if np.any(np.abs(arrays['value']) > 1):
        raise ValueError('Values must be in [-1, 1]')
    if np.any((actions != 0) & (actions != 1)):
        raise ValueError('Actions must be one-hot or missing')
    if (not np.all(actions[:, 0].sum(-1) == 1)
            or not np.all(actions[:, 1].sum(-1) == valid[:, 2])
            or np.any(actions[:, 0][~legal[:, 0]])
            or np.any(actions[:, 1][~legal[:, 1]])):
        raise ValueError('Illegal transition action or missing-horizon mask')
    if not np.array_equal(valid[:, 2], legal[:, 1].any(-1)):
        raise ValueError('H2 must exist exactly when H1 is nonterminal')
    return arrays


class Model:
    def __init__(self, config=Config()):
        self.config = config
        self.step = 0
        self.epoch = 0
        rng = np.random.default_rng(config.seed)
        h, d, q = config.hidden, config.latent, config.projection

        def weight(rows, cols):
            return rng.normal(0, np.sqrt(1 / rows), (rows, cols))

        self.params = {
            'e1w': weight(FEATURE_SIZE, h), 'e1b': np.zeros(h),
            'e2w': weight(h, d), 'e2b': np.zeros(d),
            'pw': weight(d, ACTION_SIZE), 'pb': np.zeros(ACTION_SIZE),
            'vw': weight(d, 1), 'vb': np.zeros(1),
            'gw': weight(d, d), 'aw': weight(ACTION_SIZE, d), 'gb': np.zeros(d),
            'dw': weight(d, FEATURE_SIZE), 'db': np.zeros(FEATURE_SIZE),
            'jw': weight(d, q), 'jb': np.zeros(q),
            'qw': weight(q, q), 'qb': np.zeros(q),
        }
        self.target = {key: self.params[key].copy() for key in ENCODER_KEYS + PROJECTOR_KEYS}
        self.m = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.v = {key: np.zeros_like(value) for key, value in self.params.items()}

    @property
    def horizons(self):
        return () if self.config.variant == 'direct' else (1, 2)

    def encode(self, x, target=False):
        p = self.target if target else self.params
        hidden = np.tanh(np.asarray(x) @ p['e1w'] + p['e1b'])
        return np.tanh(hidden @ p['e2w'] + p['e2b'])

    def project(self, z, target=False):
        p = self.target if target else self.params
        return z @ p['jw'] + p['jb']

    def value(self, z):
        return np.tanh(z @ self.params['vw'] + self.params['vb'])

    def policy_logits(self, z):
        return z @ self.params['pw'] + self.params['pb']

    def rollout(self, z, actions, horizon=2):
        if type(horizon) is not int or horizon not in (1, 2):
            raise ValueError('Rollout horizon must be one or two')
        z, actions = np.asarray(z), np.asarray(actions)
        if z.ndim != 2 or z.shape[1] != self.config.latent or actions.shape != (len(z), 2, ACTION_SIZE):
            raise ValueError('Invalid rollout shapes')
        p = self.params
        for index in range(horizon):
            action = np.zeros_like(actions[:, index]) if index == 1 and self.config.variant == 'no-response' else actions[:, index]
            z = np.tanh(z @ p['gw'] + action @ p['aw'] + p['gb'])
        return z

    def loss_grad(self, batch):
        b = _batch(batch)
        p, c = self.params, self.config
        valid = b['valid']
        n, count = len(valid), int(valid.sum())
        x = b['x'][valid]
        hidden = np.tanh(x @ p['e1w'] + p['e1b'])
        z = np.tanh(hidden @ p['e2w'] + p['e2b'])
        all_z = np.zeros((n, 3, c.latent))
        all_z[valid] = z
        dz = np.zeros_like(z)
        grad = {key: np.zeros_like(value) for key, value in p.items()}
        legal = b['legal'][valid]
        pol_mask = legal.any(-1)
        pol_count = int(pol_mask.sum())
        policy_loss = 0.
        if pol_count:
            pol_z, pol_legal = z[pol_mask], legal[pol_mask]
            logits = np.where(pol_legal, self.policy_logits(pol_z), -np.inf)
            shifted = logits - logits.max(-1, keepdims=True)
            lognorm = np.log(np.exp(shifted).sum(-1, keepdims=True))
            logprob = np.where(pol_legal, shifted - lognorm, 0.)
            targets = b['policy'][valid][pol_mask]
            policy_loss = float(-np.sum(targets * logprob) / pol_count)
            dl = (np.exp(shifted - lognorm) - targets) / pol_count
            grad['pw'] += pol_z.T @ dl
            grad['pb'] += dl.sum(0)
            dz[pol_mask] += dl @ p['pw'].T
        pred_v = self.value(z)
        delta = pred_v - b['value'][valid]
        value_loss = float(np.mean(delta**2))
        dv = 2 * delta / count * (1 - pred_v**2)
        grad['vw'] += z.T @ dv
        grad['vb'] += dv.sum(0)
        dz += dv @ p['vw'].T
        total = policy_loss + value_loss
        metrics = {'samples': n, 'encoded_count': count, 'policy_count': pol_count,
                   'terminal_count': count - pol_count, 'policy_nll': policy_loss,
                   'value_mse': value_loss}
        root_dz = np.zeros((n, c.latent))
        h2_mask = valid[:, 2]
        actions = b['actions'].copy()
        if c.variant == 'no-response':
            actions[:, 1] = 0
        predicted, predicted_grad = {}, {}
        if self.horizons:
            predicted[1] = np.tanh(all_z[:, 0] @ p['gw'] + actions[:, 0] @ p['aw'] + p['gb'])
            predicted[2] = np.tanh(predicted[1][h2_mask] @ p['gw'] + actions[h2_mask, 1] @ p['aw'] + p['gb'])
        for horizon in (1, 2):
            mask = np.ones(n, bool) if horizon == 1 else h2_mask
            eligible = int(mask.sum())
            enabled = horizon in self.horizons
            metrics.update({f'h{horizon}_eligible_count': eligible,
                            f'h{horizon}_count': eligible if enabled else 0,
                            f'h{horizon}_missing_count': n - eligible,
                            f'h{horizon}_loss': 0., f'h{horizon}_value_mse': 0.,
                            f'h{horizon}_value_loss': 0.})
            if not enabled:
                continue
            pred = predicted[horizon]
            dp = np.zeros_like(pred)
            predicted_grad[horizon] = dp
            if not eligible:
                continue
            target_x = b['x'][mask, horizon]
            latent_loss = 0.
            if c.variant == 'decoded':
                delta = pred @ p['dw'] + p['db'] - target_x
                latent_loss = float(np.mean(delta**2))
                dd = 2 * c.jepa_weight * delta / (eligible * FEATURE_SIZE)
                grad['dw'] += pred.T @ dd
                grad['db'] += dd.sum(0)
                dp += dd @ p['dw'].T
            elif c.variant == 'raw-jepa':
                delta = pred - self.encode(target_x, target=True)
                latent_loss = float(np.mean(delta**2))
                dp += 2 * c.jepa_weight * delta / (eligible * c.latent)
            elif c.variant in ('rjepa', 'no-response'):
                projected = self.project(pred)
                online = projected @ p['qw'] + p['qb']
                target = self.project(self.encode(target_x, target=True), target=True)
                online_n, norm = _normalize(online)
                target_n, _ = _normalize(target)
                delta = online_n - target_n
                latent_loss = float(np.mean(np.sum(delta**2, axis=-1)))
                do = _normalization_backward(online, norm, 2 * c.jepa_weight * delta / eligible)
                grad['qw'] += projected.T @ do
                grad['qb'] += do.sum(0)
                dj = do @ p['qw'].T
                grad['jw'] += pred.T @ dj
                grad['jb'] += dj.sum(0)
                dp += dj @ p['jw'].T
            pv = self.value(pred)
            delta = pv - b['value'][mask, horizon]
            mse = float(np.mean(delta**2))
            dv = .5 * delta / eligible * (1 - pv**2)
            grad['vw'] += pred.T @ dv
            grad['vb'] += dv.sum(0)
            dp += dv @ p['vw'].T
            total += c.jepa_weight * latent_loss + .25 * mse
            metrics[f'h{horizon}_loss'] = latent_loss
            metrics[f'h{horizon}_value_mse'] = mse
            metrics[f'h{horizon}_value_loss'] = .25 * mse
        if self.horizons:
            for horizon in (2, 1):
                mask = h2_mask if horizon == 2 else np.ones(n, bool)
                previous = predicted[1][mask] if horizon == 2 else all_z[:, 0]
                dg = predicted_grad[horizon] * (1 - predicted[horizon]**2)
                grad['gw'] += previous.T @ dg
                grad['aw'] += actions[mask, horizon-1].T @ dg
                grad['gb'] += dg.sum(0)
                backward = dg @ p['gw'].T
                if horizon == 2:
                    predicted_grad[1][mask] += backward
                else:
                    root_dz += backward
        centered = z - z.mean(0)
        std = np.sqrt(np.mean(centered**2, axis=0) + 1e-4)
        shortfall = np.maximum(0., .1 - std)
        coefficient = 0. if c.variant == 'direct' else .1
        variance = coefficient * float(np.mean(shortfall**2))
        dz += -2 * coefficient * shortfall * centered / (c.latent * count * std)
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
        metrics.update(loss=total, variance_loss=variance,
                       latent_std=float(np.std(z, axis=0).mean()))
        if not np.isfinite(total) or any(not np.all(np.isfinite(g)) for g in grad.values()):
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
            new_m[key] = .9 * self.m[key] + .1 * g
            new_v[key] = .999 * self.v[key] + .001 * g*g
            new_params[key] = parameter - self.config.learning_rate * (new_m[key] / (1-.9**step)) / (np.sqrt(new_v[key] / (1-.999**step)) + 1e-8)
        if any(not np.all(np.isfinite(a)) for group in (new_params, new_m, new_v) for a in group.values()):
            raise FloatingPointError('Nonfinite optimizer update')
        self.params, self.m, self.v, self.step = new_params, new_m, new_v, step
        for key in self.target:
            self.target[key] = self.config.ema * self.target[key] + (1-self.config.ema) * self.params[key]
        metrics.update(gradient_norm=norm, gradient_scale=scale)
        return metrics

    def parameter_counts(self):
        keys = list(ENCODER_KEYS) + ['pw', 'pb', 'vw', 'vb']
        if self.horizons:
            keys += ['gw', 'aw', 'gb']
        if self.config.variant == 'decoded' and self.config.jepa_weight:
            keys += ['dw', 'db']
        if self.config.variant in ('rjepa', 'no-response') and self.config.jepa_weight:
            keys += ['jw', 'jb', 'qw', 'qb']
        return {'allocated': sum(a.size for a in self.params.values()),
                'active': sum(self.params[key].size for key in keys),
                'ema': sum(a.size for a in self.target.values())}

    def save(self, path, identity):
        if not isinstance(identity, dict) or not identity:
            raise ValueError('A nonempty source/config/data identity is required')
        if type(self.step) is not int or type(self.epoch) is not int or min(self.step, self.epoch) < 0:
            raise ValueError('Invalid checkpoint counters')
        arrays = {prefix+key: value for prefix, group in
                  (('p_', self.params), ('t_', self.target), ('m_', self.m), ('v_', self.v))
                  for key, value in group.items()}
        if any(a.dtype != np.float64 or not np.all(np.isfinite(a)) for a in arrays.values()):
            raise ValueError('Invalid checkpoint tensor')
        metadata = {'method': OBJECTIVE_VERSION, 'config': asdict(self.config),
                    'identity': identity, 'step': self.step, 'epoch': self.epoch,
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
            if (metadata['method'] != OBJECTIVE_VERSION or metadata['config'] != asdict(config)
                    or metadata['identity'] != identity):
                raise ValueError('Checkpoint source/config/data/objective identity mismatch')
            model = cls(config)
            groups = (('p_', model.params), ('t_', model.target), ('m_', model.m), ('v_', model.v))
            expected = {prefix+key for prefix, group in groups for key in group}
            if set(file.files) != expected | {'metadata'} or set(metadata['array_hashes']) != expected:
                raise ValueError('Checkpoint tensor inventory mismatch')
            for prefix, group in groups:
                for key in group:
                    array = file[prefix+key]
                    if array.shape != group[key].shape or array.dtype != np.float64 or not np.all(np.isfinite(array)):
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
