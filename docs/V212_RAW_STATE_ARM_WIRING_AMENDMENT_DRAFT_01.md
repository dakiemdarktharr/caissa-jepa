# V2.12 raw-state control wiring amendment — draft 01

**Status: proposed clarification for independent method review only.** This
draft does not amend METHOD_SPEC_V212-04, authorize a trainer, data generation,
fitting, model scoring, or open any gate. The six-arm panel and negative
results remain unchanged unless a reviewed version explicitly adopts a
clarification.

## Proposed resolution

Interpret the §4 raw-state control's “shared encoder/predictor trunk and a
decoder” literally. Use the same action-conditioned latent predictor `F` in
the raw-state arm as in the other predictive arms, then decode its latent
output to exact-state features:

```text
input_k = concat(z_hat_(k-1), onehot(a_(k-1)), p_(k-1), g)  # width 104
z_pred_k = tanh(F_phi(input_k))                              # 104 -> 32
x_pred_k = D_psi(z_pred_k)                                    # linear 32 -> 198
z_hat_k = tanh(E_theta(x_pred_k))                            # 198 -> 32
```

Initialize `z_hat_0` from the exact root encoder. At each nonterminal step,
feed `z_hat_k` (the re-encoded prediction) into the next call of `F`; do not
feed an exact intermediate state or its encoding. Compare each valid `x_pred`
at horizons 1, 2, and 4 against the exact rule-generated 198-dimensional
feature target with the raw-state arm's masked feature MSE. Use the already
specified terminal masks and identical policy/root/rollout-value losses.
Terminal nodes keep exact game utility and are never decoded as value leaves.

The decoder is one affine `32 -> 198` layer with a linear output. The exact
feature adapter emits binary occupancy/side channels and game-descriptor
values in `[0,1]`; a `tanh` decoder cannot attain target value 1 at finite
weights and can saturate under the specified MSE objective. Do not clip
predictions before re-encoding: the predicted vector is a model feature, not a
legal board state. Pair the initial `F_phi` with the other predictive arms by
initialization seed; initialize `D_psi` independently with the existing
fan-in rule. The EMA target encoder is used only by arms with latent JEPA
targets; the raw-state arm's dynamics target is exact state features and has
no EMA-latent loss. Record the decoder and predictor hashes separately in
each run manifest.

This choice matches the spec's stated shared predictor trunk and preserves
the role of the raw-state control: its transition target is raw exact-state
features, while it shares the recursive action-conditioned latent transition
interface. It is preferred here as a review proposal, not a settled scientific
decision.

## Parameter accounting under this proposal

With matrix weights and biases included, and counting online trainable
parameters only:

| Arm | Online parameter calculation | Online parameters |
| --- | --- | ---: |
| Multi-step JEPA | shared encoder/heads `8,546` + `F` `3,360` | 11,906 |
| Single-pair JEPA | shared encoder/heads `8,546` + `F` `3,360` | 11,906 |
| Recursive raw-state dynamics | shared encoder/heads `8,546` + `F` `3,360` + `D` `6,534` | 18,440 |
| Value-only latent rollout | shared encoder/heads `8,546` + `F` `3,360` | 11,906 |
| Direct-leaf value | shared encoder/heads `8,546` | 8,546 |
| Single-horizon JEPA | shared encoder/heads `8,546` + `F` `3,360` | 11,906 |

The three JEPA arms additionally keep a non-gradient EMA target encoder of
6,368 parameters; report that target state separately from online trainable
counts. The raw-state arm is 1.55× the online parameter count of the candidate,
and direct-leaf is 0.72×. These structural differences do not by themselves
make the controls unfair: the raw-state, direct-leaf, and latent-rollout arms
test different hypotheses. They must be reported and interpreted alongside
the frozen compute-parity requirement.

## Required implementation and parity checks

Before any fit grant, an independently reviewed implementation must verify:

1. `F` is actually used on every raw-arm transition and receives the same
   action, absolute actor role, and game descriptor semantics as the JEPA
   arms; `D` consumes only `z_pred`, and recurrence uses `E(x_pred)`.
2. Exact features, linear decoder outputs, target masks, terminal handling,
   forced pass 64, gradient flow through `D` and the re-encoding step, and
   stop-gradient on any EMA target match the versioned contract.
3. The no-training random-weight pilot's raw arm either gets updated to this
   path under a separately reviewed compute-pilot change or is clearly
   labelled a different proxy. Existing pilot receipts and historical
   measurements are not rewritten.
4. Parameter census and forward/backward FLOPs are measured for every arm on
   the same fixed dry-run batches and masks. The spec's total training-FLOP
   parity threshold remains 5%. Parameter-count differences alone do not
   waive that threshold; if parity fails, revise a new method/config version
   and review it before fitting. Do not add filler computation or alter update
   counts only to make the profiler totals appear equal.

The expected 18,440 count is an architecture calculation, not an empirical
FLOP, memory, or fit result. If reviewers prefer the direct action-conditioned
104-to-198 decoder, it should be frozen explicitly instead; the compute pilot
path and count would then need a new reconciliation. The current random
compute pilot applies `tanh` to that direct decoder, so it also differs in
output activation from this proposed training arm. No implementation, training
profile, or performance result follows from this proposal.
