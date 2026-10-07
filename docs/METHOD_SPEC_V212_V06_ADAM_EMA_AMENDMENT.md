# METHOD SPEC V2.12-06 Adam/EMA update semantics amendment

**Status: adopted after independent method review on 2026-10-07.** This narrow
amendment applies to the current `METHOD_SPEC_V212.md` v06. It retains v05's
six arms, objective/losses, trainable parameter sets, paired seeds, batch and
window schedule, and evaluation protocol. It resolves optimizer details that
v05 did not uniquely specify. It does not authorize data access, profile,
inference, fitting, or locked evaluation; no gate is opened by this amendment.

## 1. Stateful training update

For each arm and seed, initialize each online trainable parameter's Adam first
moment `m` and second moment `v` to zero. The optimizer timestep starts at zero
and increments exactly once for every scheduled update, from `t=1` through
`t=87`; updates are not skipped. There is no weight decay or other optimizer
state.

Let `g` be the gradient of the combined arm loss over all online trainable
parameters, including arm-specific predictor and decoder tensors. Exclude the
non-gradient EMA target encoder. Compute one global L2 norm across all gradient
coordinates and clip once:

```text
norm = sqrt(sum over every online trainable gradient coordinate of g_i^2)
c = 1                 if norm <= 5
c = 5 / norm          if norm > 5
g_clip = c * g
```

Thus a zero norm uses `c=1` and never divides by zero. Record `norm` before
clipping. Then apply Adam using the updated moments and one-based timestep:

```text
m = 0.9 * m + 0.1 * g_clip
v = 0.999 * v + 0.001 * (g_clip * g_clip)
m_hat = m / (1 - 0.9**t)
v_hat = v / (1 - 0.999**t)
theta = theta - 0.001 * m_hat / (sqrt(v_hat) + 1e-8)
```

The epsilon is deliberately placed outside the square root. This resolves a
choice that the v05 hyperparameter list left ambiguous; it is an explicit v06
method decision. Implementations must not substitute another Adam convention
or per-tensor clipping.

## 2. EMA update

For the multi-step JEPA, single-pair JEPA, and single-horizon JEPA arms,
initialize target-encoder weights and biases equal to the online encoder at
step zero. After each Adam update, update target-encoder weights and biases as
follows:

```text
target = 0.99 * target + 0.01 * updated_online
```

The target encoder has no gradients. The recursive raw-state, value-only
latent-rollout, and direct-leaf-value arms have no EMA target and perform no
EMA update.

## 3. No-fitting profile interpretation

An independently authorized no-fitting operation-trace profile follows
`docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md`. It must not carry
parameters, moments, or EMA state between scheduled batches. For scheduled
update `u`, it may start from the frozen seed initialization with zero scratch
moments, the online-initialized scratch target, and `t=u`, execute the same
shape-level update operations, then discard every result. This is an
operation-trace count, not a training trajectory and not a prediction of
training values. The profile must count step-dependent powers/bias correction
for every scheduled update and retain the protocol's full-schedule bounds on all
value-dependent branches.

Before any profile or fit, freeze the counter implementation/version/coverage,
source and runtime fingerprints, scalar powers and bias-correction treatment,
comparisons, zero-norm path, indexing/integer work, and unsupported operators.
Report non-FLOP operations separately or under a disclosed frozen conversion as
required by the preregistered compute protocol. A pass clears no gate beyond
the compute condition it measures; this amendment opens none.
