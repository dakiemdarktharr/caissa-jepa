# V2.12-05 raw-state arm amendment

**Status: adopted in METHOD_SPEC_V212 v05 on 2026-10-07 after independent
read-only method disposition.** This amendment changes only the raw-state
arm's graph, target/loss, terminal, gradient, and preflight contract. The
unchanged v04 specification is preserved at
`docs/METHOD_SPEC_V212_V04.md`. This adoption does not authorize a trainer,
data or root generation, inference, fitting, scoring, matches, or open any
remaining gate. All non-raw-state procedures, prior negative results, and
scope limits remain in force.

## 1. Decision covered by this amendment

V04 §4 names a raw-state arm with a shared encoder/predictor trunk and a
decoder, but does not uniquely define whether the action-conditioned predictor
feeds a latent decoder or whether the concatenated action input feeds a direct
feature decoder. This amendment adopts the latent-then-decode graph in v05. It
also makes the target, loss, gradient, terminal,
and failure semantics explicit. The choice is narrow: it does not add or
remove an arm or change the hypothesis, games, data, schedule, metrics,
planner, or acceptance criteria.

The independent static review of raw-state draft 02 found this contract
coherent with v04's stated controls and suitable for narrow v05 method-level
adoption. That review does not accept unrelated v04 sections, training compute
parity, or any research gate. See
`V212_RAW_STATE_ARM_WIRING_AMENDMENT_DRAFT_02.md` for the review trail and
static arithmetic.

## 2. Candidate recursive graph

For root state features `x_0`, initialize `z_hat_0 = E_theta(x_0)`. For each
supplied legal transition `k`, use the same predictor dimensions and action,
absolute-role, and game-descriptor semantics as the other predictive arms:

```text
z_pred_k = tanh(F_phi(concat(z_hat_(k-1), onehot(a_(k-1)), p_(k-1), g)))
x_pred_k = D_psi(z_pred_k)       # affine 32 -> 198; linear output
z_hat_k  = tanh(E_theta(x_pred_k))
```

The re-encoded prediction is the only recurrent state after the root. Do not
replace it with an exact intermediate state or encoding. Construct four
transitions when horizon 4 is required, including transition 3 even though
only horizons 1, 2, and 4 carry prediction losses. The feature vector uses the
existing 198-coordinate adapter contract: current-player and opponent
occupancy planes, in-board indicator plane, then six game descriptors. Do not
clip decoder outputs before re-encoding; predicted features are not legal
board states.

The raw-state arm has no EMA target encoder or EMA-target dynamics loss: its
prediction target is the exact adapter feature vector. The EMA target encoder
and loss paths for the three JEPA arms remain unchanged. The decoder is
initialized independently with the existing fan-in rule; the initial `F` is
paired by seed with the other predictive arms. Record hashes for `F` and `D`
separately.

## 3. Raw-state target and loss candidate

For batch example `b` and horizon `k ∈ {1,2,4}`, define the coordinate-mean
squared error and the valid-target mask as:

```text
e_(b,k) = (1 / 198) * sum_(j=0..197) (x_pred[b,k,j] - x_exact[b,k,j])^2
m_(b,k) = 1 iff all transitions through k are valid and the exact target
          exists and is nonterminal; otherwise 0
L_raw   = sum_(b,k) alpha_k * m_(b,k) * e_(b,k)
          / sum_(b,k) alpha_k * m_(b,k)
```

Use `alpha_1=1`, `alpha_2=0.5`, `alpha_4=0.25`. Weight all 198 coordinates
uniformly, including zero-valued padding and descriptor/in-board coordinates.
Do not apply coordinate-, channel-, game-, or variant-specific rescaling.
Normalize over pooled valid weighted targets, not by first computing and
equally averaging separate horizon means.

The candidate total raw-state arm loss is:

```text
L_raw_arm = L_policy + L_root_value + 1.0*L_outcome_roll + 1.0*L_raw
            + 0.1*L_variance + 0.01*L_covariance
```

`L_outcome_roll` uses the same predicted/re-encoded states, outcome labels,
horizon weights, valid-transition masks, and valid-target normalization as
the other predictive arms. Root regularizers retain their exact v04
definitions and coefficients. This arm replaces latent `L_roll` with
`L_raw`; it does not receive both targets.

## 4. Terminal, gradient, and failure semantics

- **Terminal targets:** do not decode or predict a terminal state or any later
  state on that branch. Exclude terminal and later horizons from both `L_raw`
  and predicted `L_outcome_roll`. Use exact terminal utility through the
  exact-rule planner/bypass path only; it is not a learned terminal training
  target in this candidate. This explicitly resolves the wording tension
  between v04's statement that terminal states receive exact utility and its
  nonterminal rollout-loss definition. Any alternate terminal training target
  requires a further versioned review.
- **Gradient flow:** backpropagate through every active online `F -> D -> E`
  operation and recurrent connection, including the root online encoder. Do
  not detach predicted features or intermediate re-encodings. Exact adapter
  features and recorded outcome labels are constants. Apply the v04 global
  gradient-norm clip of 5 after loss combination.
- **Accounting and preflight:** record valid nonterminal, terminal-masked,
  missing/truncated, and invalid-source-transition counts separately for each
  arm, batch, and horizon. A terminal masks that horizon and all later ones;
  truncation is not reported as terminal. Before the first optimizer update,
  replay every selected training window and required transition, and
  precompute each fixed minibatch's valid-target count. Any invalid transition
  or any raw-state minibatch with zero valid targets rejects the whole run
  before updates. Do not skip, replace, or resample a fixed batch.

These rules preserve the common v04 window order, minibatch boundaries, and
87-update schedule. For a fixed batch with no valid targets for another
predictive arm, retain the v04 fail-closed zero-target behavior; do not alter
that arm's schedule independently.

## 5. Capacity and compute gate

The candidate raw-state arm has 18,440 online trainable parameters under the
v04 dimensions (shared encoder/heads 8,546, predictor 3,360, decoder 6,534).
The three JEPA arms retain their separate 6,368-parameter non-gradient EMA
encoder state. Parameter totals are not compute measurements.

The static dense-forward inventory is 72,544 MAC per fully valid four-ply
raw-state window versus 40,864 for multi-step JEPA (+77.53%). It omits
backward, optimizer, EMA updates, activations, loss/reduction work, masks, and
data movement. This is a parity risk signal, not proof that the v04 ≤5%
total-training-FLOP gate passes or fails. The ≤5% training-FLOP gate remains
**untested and unpassed**. Before any fit, independently review
the actual six forward/loss graphs and measure parameter counts and total
forward/backward training FLOPs per update on identical dry-run batches and
masks. The existing ≤5% panel-wide threshold remains mandatory. Do not add
filler computation or change update counts to manufacture parity. If measured
parity fails, fitting remains prohibited until a new controls/config version
is independently reviewed.

## 6. Gate status and inheritance

All v04 prerequisites remain in force: primary-source novelty disposition,
trajectory-generator transition/split audits, accepted development-root
method and schedule, reviewed no-outcome compute protocol, actual graph and
runtime review, data/provenance audit, and separate pre-fit review. The
Reversi8 2-second rule-only p90 failure remains a recorded negative result;
this amendment does not waive it or authorize choosing a new cap. The root
sampling, action-sensitivity, regret, and service/supervision drafts remain
independent gated workstreams.

No trainer implementation graph, training batch, FLOP profile, dataset, model,
root schedule, score, outcome, simulation, inference, service, or match was
run or created for this amendment. V05 is the current accepted specification,
with independent review scoped to its raw-state amendment only. No
superiority, novelty, transfer, or Q1-readiness claim follows from this method
decision.
