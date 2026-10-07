# V2.12 Adam and EMA update semantics amendment — draft 01

**Status: independently accepted as a method-clarification proposal only; not
adopted; no trainer, profile, or fitting is authorized.** The independent review
found the equations coherent and aligned with the existing scratch helper, but
not uniquely implied by v05 where clipping scope and epsilon placement were
unspecified. This candidate only makes optimizer/update semantics explicit for
the already frozen six arms. It does not alter losses, parameters, data, seeds,
update count, evaluation, or the ≤5% compute gate.

## 1. Ambiguity in the accepted specification

`METHOD_SPEC_V212.md` fixes learning rate `0.001`, batch size `64`, Adam
`beta1=0.9`, `beta2=0.999`, epsilon `1e-8`, global gradient-norm clip `5`,
EMA decay `0.99`, and exactly 87 scheduled updates per seed. It does not
explicitly define moment initialization/persistence, bias correction, epsilon
placement, zero-gradient clipping behavior, or when EMA is updated. The current
pure helper in `two_player/v212_scratch_optimizer.py` implements choices for
these details, but that helper is not itself the adopted method specification
or trainer. Resolve this proposal before implementing a trainer or freezing a
compute profile.

## 2. Proposed per-seed training equations

For every arm and paired seed, initialize every trainable parameter's first and
second moments to zero. Set optimizer step `t=0`. At each of the 87 scheduled
updates, increment `t` once; scheduled updates are never skipped. Let `g` be
the gradient over all trainable online parameters, including arm-specific
predictor/decoder parameters and excluding non-gradient EMA target parameters.
Compute the global L2 norm over all gradient coordinates and set

```text
c = 1                         if ||g||2 <= 5
c = 5 / ||g||2               if ||g||2 > 5
g_clip = c * g
m = 0.9 * m + 0.1 * g_clip
v = 0.999 * v + 0.001 * (g_clip * g_clip)
m_hat = m / (1 - 0.9**t)
v_hat = v / (1 - 0.999**t)
theta = theta - 0.001 * m_hat / (sqrt(v_hat) + 1e-8)
```

The epsilon is outside the square root. No weight decay or additional optimizer
state is used. If the norm is zero, `c=1`; implementations must not divide by
zero. Record the norm before clipping. The clip applies once to the concatenated
gradient over all online trainable parameters, not independently per tensor.

For each of the three JEPA arms only, initialize EMA target-encoder weights and
biases equal to the corresponding online encoder at step zero. After the Adam
online-parameter update at every scheduled update, apply

```text
target = 0.99 * target + 0.01 * online
```

to the encoder weight and bias. The EMA target is not gradient-updated. The
three non-JEPA arms have no EMA target or EMA update.

## 3. Disposable compute-profile interpretation

This method clarification describes persistent state in actual training. A
separately authorized no-fitting FLOP profile must not carry parameter, Adam,
or EMA state between scheduled batches. For update index `u=1..87`, it may
execute the same operation trace on disposable arrays reset from the frozen
seed initialization (zero moments, online-initialized target, and bias
correction using `t=u`), then discard all scratch results. It must count
step-dependent scalar/bias-correction work for every update. This does not
produce a training trajectory and does not replace the full-schedule bounds on
value-dependent branches in
`docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_02.md`.

## 4. Independent review disposition and adoption boundary

The approved read-only reviewer accepted these equations as a clarification
proposal, confirmed global norm scope over all online trainable gradients,
one-based Adam bias correction, epsilon outside the square root, zero norm
scale 1, and post-Adam EMA for the three JEPA arms. The reviewer also accepted
the disposable reset/timestep interpretation as an operation trace only,
conditional on retaining D02's branch bounds. Epsilon placement and clipping
scope were explicitly under-specified by v05, so these are deliberate proposed
choices rather than facts uniquely implied by the current method.

This review is not method adoption. A future adoption must be recorded in a
new versioned method-spec amendment; until then, v05 remains current and its
underspecified implementation choices must not be treated as resolved for a
trainer or profile. Counter treatment of scalar powers and comparisons follows
D02's separate-operation reporting rule. This proposal grants no data access,
profile, inference, training, root generation, scoring, or outcome evaluation.
The ≤5% gate remains **untested and unpassed**; existing negative results and
novelty risks remain in force.
