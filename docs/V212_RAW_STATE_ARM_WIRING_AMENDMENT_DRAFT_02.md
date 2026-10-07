# V2.12 raw-state control wiring amendment — draft 02

**Status: adopted as the narrow raw-state amendment in METHOD_SPEC_V212-05;
the archived v04 text remains unchanged.** Draft 02 supersedes draft 01 as the
raw-state contract record; draft 01 remains unchanged history. The adoption
does not authorize a trainer, data generation, fitting, model scoring, or
open any gate. The six-arm panel and negative results remain unchanged.

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
feature target. This draft proposes the following literal-coordinate
interpretation of “masked feature MSE” for independent review; it does not
claim v04 uniquely specifies it:

The proposed coordinates follow the existing `BoardGame.features` adapter:
`x[0:64]` is the current player's occupancy on the shared 8×8 grid,
`x[64:128]` is the opponent's occupancy, `x[128:192]` is the in-board
indicator, and `x[192:198]` is `(rows/8, cols/8, k/8, placement_flag,
reversi_flag, gravity_flag)`. Grid indices are `row*8+column`; cells outside
the board are zero in the first three planes. Occupancy planes are relative to
the side to move, including after a forced Reversi pass; the six descriptor
coordinates are unchanged by the pass. `tests/test_v212_raw_state_feature_contract_audit.py`
checks this existing adapter mapping on both training and held-out sizes and
checks the forced-pass role switch. This is evidence about feature encoding
only, not decoder outputs, the proposed loss/masks, or a trained arm.

```text
e_(b,k) = (1 / 198) * sum_(j=0..197) (x_pred[b,k,j] - x_exact[b,k,j])^2
L_raw   = sum_(b,k) alpha_k * m_(b,k) * e_(b,k)
          / sum_(b,k) alpha_k * m_(b,k)
```

Here `k ∈ {1,2,4}`, `alpha_1=1`, `alpha_2=0.5`, `alpha_4=0.25`, and
`m_(b,k)=1` only when every transition through horizon `k` is valid, the
exact target at that horizon exists, and that target is nonterminal. The
fixed denominator inside `e` includes all 198 coordinates:
both occupancy/side planes, the in-board indicator plane, zero-valued padded
cells, and all six game-descriptor coordinates. There is no coordinate-level
mask or variant-dependent denominator. The outer weighted denominator
normalizes over valid nonterminal targets, matching the valid-example
normalization used for the v04 rollout losses. This is a proposed contract,
not an adopted change to v04.

At the first terminal state on a branch, do not decode/predict that state or
any later state; use exact game utility for terminal handling. Its feature
target and every later horizon on that branch have `m=0`. A truncated
trajectory with a missing nonterminal target also has `m=0` for that horizon,
but must be counted separately from terminal masks. If a minibatch has no
valid nonterminal raw-state target, its loss is undefined and the
implementation must abort the run before any optimizer update. Do not skip,
replace, or resample that batch: v04 fixes common minibatches and 87 updates
across arms. No prediction or value leaf is required at or past terminal.
Keep identical policy/root/rollout-value losses, with the v04 terminal
utility rule.

For this arm, the candidate total loss is:

```text
L_raw_arm = L_policy + L_root_value + 1.0*L_outcome_roll + 1.0*L_raw
            + 0.1*L_variance + 0.01*L_covariance
```

`L_outcome_roll` uses the same predicted/re-encoded states, labels, horizon
weights, valid-transition masks, and valid-target normalization as the other
predictive arms. The variance and covariance terms are the frozen v04 root
online-latent regularizers with unchanged definitions and coefficients. This
arm has no EMA-latent `L_roll`; `L_raw` occupies that objective slot and
compares decoder output to exact features. The formula is a proposed
instantiation of §4's “same policy/root/rollout-value losses” plus raw-state
dynamics loss, pending method review.

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

## Draft 02 explicit gradient, terminal, and failure proposals

These clauses make previously implicit implementation choices reviewable;
they are not adopted method decisions.

- **Gradient flow:** use ordinary end-to-end backpropagation through every
  active online `F -> D -> E` operation and through the recurrent path from a
  later prediction into each earlier predicted/re-encoded state, including
  the exact root's online encoding. Do not detach predicted features or
  intermediate re-encodings. Exact adapter feature targets and outcome labels
  are constants. This raw-state arm has no EMA target or EMA loss. Existing
  root regularizers retain their v04 definitions; global gradient-norm clipping
  remains 5 after loss combination.
- **Terminal handling:** for this candidate, terminal transitions and later
  horizons are excluded from both `L_raw` and predicted rollout-value loss;
  exact terminal utility is used only by the exact-rule planner/bypass path and
  is not a learned terminal training target. This interpretation follows
  v04's nonterminal rollout-loss wording but needs explicit disposition because
  §3 also says terminal states “receive exact terminal utility.” Any different
  terminal training target requires a new reviewed amendment.
- **Mask and failure accounting:** for each arm, batch, and horizon, record
  counts for valid nonterminal targets, terminal-masked targets, missing or
  truncated targets, and invalid source transitions separately. A terminal
  at or before the horizon masks that and later horizons. A trajectory ending
  before a nonterminal target is available masks that horizon and is counted
  as missing/truncated; it is never counted as terminal. Any invalid
  rule-transition in a selected training window is a data-integrity failure
  that aborts the run before the first optimizer update; it must not be
  converted into an ordinary mask. Preflight-replay every selected window
  and its required transitions before training begins, so invalidity cannot
  be discovered only after earlier batches updated. Precompute the raw-state
  valid-target count for every fixed minibatch before the first update; if any
  minibatch has zero valid raw-state targets, reject the run before any update,
  with no replacement or resampling.
- **Feature weighting and reduction:** retain uniform weight across all 198
  coordinates, including descriptor and in-board coordinates; no per-channel,
  per-game, or per-variant rescaling is applied. Retain the draft's pooled
  valid-target normalization `sum_(b,k) alpha_k*m_(b,k)*e_(b,k) /
  sum_(b,k) alpha_k*m_(b,k)` for `L_raw`. This means examples at a horizon
  contribute in proportion to their valid weighted count, rather than first
  giving each horizon an equal-size mean. The coordinate weights and pooled
  reduction remain explicit review choices, not a claim that v04 uniquely
  determines them.

## Dense-forward compute implication

The reviewed static inventory is 72,544 dense forward MACs per fully valid
four-ply raw-state window versus 40,864 for multi-step JEPA: 31,680 more, or
77.53%. In this graph, the raw arm adds four decoder/online-re-encoder pairs
(50,688 MACs), while the multi-step JEPA arm instead includes three EMA target
encodes (19,008 MACs). This is a substantive parity risk, not a measured FLOP
result or proof that v04's 5% total-training-FLOP gate fails. The inventory
omits backward, optimizer, EMA update, activations, reductions, data movement,
and mask-dependent execution. Only a same-batch, same-mask forward/backward
profile of all six implemented arms can decide the gate. If measured total
training FLOPs exceed 5%, version and independently review a method/config
change before fitting; do not add filler computation.

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

**Independent read-only follow-up (2026-10-07):** at this stage, before the
method-level disposition below, the approved reviewer
confirmed the transition-validity mask, fail-run behavior for a
zero-valid-target minibatch, complete raw-arm loss and regularizer terms, and
the proposal-only/gated status. They found no remaining inconsistency that
blocks further independent method review. This is not method adoption or fit
approval. The exact-coordinate MSE and pooled horizon normalization remain
reviewable method choices. The 5% total training-FLOP check and all other v04
gates remain mandatory and closed.

**Independent read-only review of draft 01 and the static MAC inventory
(2026-10-07):** the latent-then-decode graph is a defensible reading of v04,
but v04 does not uniquely require it. The reviewer found no arithmetic
contradiction in the proposed loss and masks, while identifying open choices
for gradients through `F -> D -> E`, terminal training targets, separate
terminal/missing/invalid-transition counts, and uniform coordinate weighting
with pooled horizon normalization. The reviewer confirmed that the 77.53%
dense-forward MAC difference warns of parity risk but cannot establish the
5% total-training-FLOP gate. Draft 02 records these choices for disposition;
at that point, before the draft-02 disposition below, no graph had yet been
frozen even as a candidate. No implementation/profile was authorized and no
gate advanced. No model, root, simulation, inference, or training was run.

**Independent read-only method disposition of draft 02 (2026-10-07):** the
reviewer found the candidate internally coherent with v04's stated controls,
including end-to-end `F -> D -> E` gradients, the stated nonterminal target
mask/terminal interpretation, separate mask/failure accounting, and the
preflight needed to preserve fixed minibatches and 87 updates. Uniform
coordinate weighting and pooled valid-target normalization were accepted as
explicit candidate choices where v04 was underspecified. This disposition
supported adoption of the narrow raw-state amendment in v05, without changing
archived v04 or authorizing implementation, pilot, or fitting. Compute-gate
readiness is **NO**: the ≤5% total training-FLOP requirement remains
unmeasured and mandatory. If it fails, any
method/config change requires a new version and review before fitting. No
profile, model operation, or gate advancement occurred.
