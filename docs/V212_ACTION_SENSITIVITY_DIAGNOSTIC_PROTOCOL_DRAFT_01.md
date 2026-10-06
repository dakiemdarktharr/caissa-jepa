# V2.12 action-sensitivity diagnostic protocol — draft 01

**Status: proposal for independent review only.** This draft does not amend
METHOD_SPEC v04, change any arm, select checkpoints, authorize root or branch
generation, model scoring, training, inference, matches, or outcomes. The
root-sampling schedule and decision-regret reference remain separate,
unapproved designs. No threshold or gate changes here.

## Question and scope

Measure whether an arm's supplied legal action changes its predicted
transition in a way that matches exact rule consequences. This tests a
mechanism; it is not a strength metric, action optimality claim, full-game
model, or evidence that JEPA improves decisions. Keep the diagnostic distinct
from the primary head-to-head score, bounded-reference regret, and model-score
ranking. Reference values and game outcomes are not inputs.

The diagnostic applies only to arms with an explicit action-conditioned
transition output. For latent-transition arms, compare predicted latents with
the frozen inference encoder's latent for the exact successor. This is a
within-arm evaluation target, not a claim that all arms train against the same
target; JEPA's EMA target remains its training target. The value-only arm
qualifies only if final graph inspection confirms it has the explicit
action-conditioned recursive transition output described by METHOD_SPEC v04.
For the recursive raw-state arm, compare its decoded exact-state feature
prediction with the rule-generated successor features using that arm's
independently reviewed target and validity mask. Do not introduce a new mask
or compare raw-feature MSE numerically with latent MSE. Mark arms without the
relevant transition output as not applicable, not as zero error. The six-arm
graph and raw-state target/mask contract must be independently verified before
freeze; this draft does not infer that contract.

## Sampling and support records

Use only a separately reviewed, prehashed development-root schedule after its
own method review. No root may be generated under this draft. The root-slot is
the reporting unit; retain repeated states as separate scheduled draws if and
only if the accepted root protocol does so. Freeze game/rules, adapter,
encoder and predictor hashes, target-encoder rule, action order, root receipt,
policy configuration, branch RNG derivation, and software versions before
diagnostic computation.

Before evaluating predictions, derive support labels per arm from its frozen
training-window manifest and objective masks, without using model outputs. An
eligible occurrence is a unique source transition `(episode_id, ply_index)`
whose action is supplied to that arm's predictor along a loss path with a
valid target. Count the source transition once even if overlapping windows,
horizons, or epochs reuse it. A logged action that never enters a valid
predictor target path is not predictor support. Define and hash this per-arm
eligible train-only source-transition ledger.

1. **Action-index support:** in the namespace `(game_family, action_id)`,
   whether that global 8×8 placement ID (0–63), or reserved forced-pass ID
   64, occurred in an eligible train-only transition in the same game family,
   with per-arm source-transition count. This is coarse exposure, not evidence
   that a state-action transition was learned.
2. **Exact state-action support:** whether the exact tuple `(variant/rules
   fingerprint, absolute board, player to move, supplied action_id)` occurred
   in that arm's eligible source-transition ledger, with per-arm
   source-transition count. The actor is already `player to move`; there is no
   additional seat/role key. Do not symmetry-canonicalize this key. Preserve
   the held-out-size designation even when exact support is absent.

Report every candidate-slot disposition and all accepted-root/action cells,
plus support-label counts. Rejected candidate slots remain in the schedule
ledger and have no model-metric denominator; a failed root-yield gate fails
the diagnostic without replacement. Support categories are descriptive
strata only; they must not determine root acceptance, alter the model, select
checkpoints, or change evaluation weights. For one-step action-error and
action-retrieval summaries, run two separate marginal stratifications: one by
action-index support (present/absent) and one by exact state-action support
(present/absent). Do not combine them into a four-cell joint class. Within
each marginal class, retain held-out-size as a separate variant stratum.
Within each root and class, average applicable action rows; then average those
root summaries equally within the accepted variant × occupancy stratum.
Report the number of roots and rows contributing to each class. Multi-step
rollout error is not support-stratified because its horizon target results
from several intervened and policy-selected actions; instead report both
support labels and counts for each action occurrence along each branch,
without attributing horizon error to one occurrence. Do not reweight classes
or treat action rows as independent roots.

## One-step all-legal-action probe

For each scheduled nonterminal root `s` with legal set `A(s)`, encode the root
once and, for every `a` in `A(s)`, construct the exact successor
`s_a = T(s,a)`. For nonterminal `s_a`, obtain target `z_eval(s_a)` using the
arm's frozen inference encoder and prediction
`zhat(s,a) = F(z(s),a,p_s,g)`. Record the
per-coordinate mean-squared error `e(s,a) = MSE(zhat(s,a), z_eval(s_a))`; do
not normalize by test-set variance or tune a latent metric after looking at
results. Keep terminal successors in a separate exact-terminal count because
the method bypasses learned latent value/prediction at terminal states.

To measure action discrimination for latent-transition arms, let `A_nt(s)` be
the root actions whose exact successors are nonterminal, and form the full
within-root matrix for `a,b` in `A_nt(s)`:

```text
d_s(a,b) = MSE(F(z(s), b, p_s, g), z_eval(T(s,a)))
```

For each target action `a`, compare against candidate set `B_s(a)`, consisting
of `a` and all nonterminal actions whose exact successor tuple differs from
the successor for `a`. Report whether the diagonal prediction is strictly
nearer than every eligible off-diagonal prediction, and its tie-fraction
credit: `1 / |argmin_{b in B_s(a)} d_s(a,b)|` when `a` is in that argmin set,
otherwise zero. For
eligible target rows, average off-diagonal error within row first, then
average rows equally within root. Diagonal error and paired root contrast use
exactly this same eligible target-row set; the contrast is mean eligible
off-diagonal error minus diagonal error. A root with zero eligible target
rows is excluded from retrieval, diagonal-error, and paired-contrast
aggregates and is reported as `not_estimable` for those quantities.
Preserve all
legal actions, including forced pass 64. A singleton legal set has a
transition error but no action-discrimination comparison. If two actions
yield identical exact successor tuples (variant/rules, absolute board,
player to move), report that exact-tuple collision and exclude that pair from
discrimination while retaining its transition-error record. Do not equate
symmetry-canonical states for this purpose. If a target row has no distinct-
successor competitor, mark retrieval and off-diagonal contrast not_estimable
for that row. If a root has no estimable target rows, mark its retrieval
diagnostic not_estimable; retain its transition-error rows. Report row and
competitor counts.

Terminal-successor actions are excluded from both the matrix rows and columns
and remain in the separate terminal count. The exact-successor MSE is the
primary diagnostic quantity; raw distance
between predicted latents for different actions is not treated as success.
This probe tests one-step transition discrimination only. No action-recovery
accuracy threshold is proposed.

## Multi-step open-loop probe

For each root and each legal first action, generate one exact counterfactual
continuation branch to horizons 2 and 4 plies using the ordered policy pair
and absolute-seat assignment recorded in that root's accepted receipt. The
first action is fixed to the enumerated legal action; subsequent actions use
the frozen policy assigned to the acting seat and a deterministic
branch-specific RNG stream. Map the first and second policy in the receipt to
absolute players `+1` and `-1` before freezing the schedule. Use the same
policy pair for every first-action intervention from that root. Never
continue after terminal. A forced pass counts as one legal ply. Record
terminal reach and pass counts by ply. Do not generate final outcomes or use
them as labels.

The horizon-2 state/prediction is the exact prefix of the same counterfactual
branch used for horizon 4. Build a canonical JSON identity with exactly the
fields `namespace`, `root_schedule_seed_id`, `root_slot_id`, `first_action_id`,
and `ordered_policy_pair_id`. Set `namespace` to the literal
`caissa-jepa-v212-action-sensitivity-branch-v1`. Encode
`root_schedule_seed_id` as `sha256:` plus 64 lowercase hex digits of the
SHA-256 digest of the root schedule's unsigned 64-bit seed encoded as exactly
8 little-endian bytes; `root_slot_id` as `slot-` plus a 1-based, zero-padded
8-digit ordinal in that frozen schedule; `first_action_id` as an integer from
0 through 64, where 64 is the reserved forced-pass ID and must be legal at
that root; and `ordered_policy_pair_id` as `sha256:` plus 64 lowercase hex
digits of SHA-256 over canonical JSON with the sole top-level field `policies`,
whose value is an ordered two-element list of objects with exactly `policy_id`
and `config_sha256` fields. `policy_id` is the UTF-8 registry identifier;
`config_sha256` is `sha256:` plus 64 lowercase hex digits for that policy's
frozen configuration bytes. Use UTF-8, sorted keys, compact separators,
`ensure_ascii=False`, and
`allow_nan=False`. Hash those bytes with SHA-256;
interpret the digest as eight little-endian 32-bit words for
`numpy.random.SeedSequence`; then use `numpy.random.PCG64` through the
`Generator` API. Pin the exact NumPy version and record the stream-identity
digest before branch generation. The policy API must consume this stream for
every stochastic draw; policy tie-breaking and fallback behavior must also be
specified as follows: an exact score tie selects the lowest action ID, and
there is no fallback to another policy or action if a policy returns an
illegal/unavailable action; record that branch as incomplete. Enumerate each
legal first action once, with equal planned weight within its accepted root,
then follow its receipt-assigned policies. The sampled root marginal remains
the reviewed success-conditional distribution, but the intervened first-action
target is not the behavior-policy first-action distribution.

For each nonterminal horizon state, recursively apply the arm's predictor to
the exact branch action sequence and compare the resulting latent with the
arm's frozen inference-encoder encoding of the exact branch state by
per-coordinate MSE. For the raw-state arm, report exact-feature error
separately at the same horizons only after its independently reviewed decoder
target and horizon-validity contract specifies target coordinates, masking,
and terminal-successor handling. Pair arms by root, legal first
action, policy pair, and branch-stream ID; retain missing or interrupted
cells without replacement. The first-action branch outcomes do not become
game-score observations.

The branch-allocation rule must be frozen before any branch generation. This
draft proposes one continuation per root × legal first action, reusing the
root's recorded ordered policy pair rather than redrawing or enumerating all
16 pairs. This retains the success-conditional root marginal and conditions
continuations on the receipt's policy pair. It does not preserve the
behavior-policy distribution over first actions or estimate uniform legal
continuations. The action expansion cost and feasibility remain unknown.

## Aggregation, missingness, and reporting

For horizon `h`, an expected-terminal mask applies when the branch reaches a
terminal state at or before `h`; no predicted state error is defined at or
after that event. Report the mask ply and terminal count separately at each
horizon. It is not a missing or failed prediction. For a nonterminal state at
`h`, the prediction/target row is required; interruption, nonfinite output,
or unavailable nonterminal target is incomplete and invalidates its
predeclared aggregate. Denominators are the nonterminal accepted-root ×
first-action branch cells at that horizon; report numerator, denominator, and
terminal masks.

First average applicable action rows within root, then roots within the
accepted variant × occupancy stratum, then use only weights explicitly
accepted in the root/method protocol. For support-stratified metrics, average
rows within each root × support class before averaging contributing roots.
Report each seed and arm separately before any macro summary. Do not pool
action rows as independent roots. Report counts and fractions for terminal
masks, forced passes, support strata, exact-tuple duplicate successors, and
missing/incomplete rows beside each metric.

Keep every candidate disposition and every accepted-root/action/policy row in
the denominator ledger. A failed root schedule, missing model output,
nonfinite value, or incomplete horizon invalidates the corresponding
predeclared aggregate; do not drop, replace, or reweight the affected row.
Preserve diagnostic failures as failures, not as zero loss. Store no game
outcome, reference label, or selected action in the protocol's result artifact
unless a separate reviewed receipt explicitly requires it.

This draft specifies descriptive diagnostics only. It supplies no null
hypothesis, acceptance threshold, multiplicity procedure, confidence
interval, or checkpoint-selection rule. If inferential comparisons or
selection are wanted, freeze their estimand, error control, uncertainty
method, and sample-size rationale in a new reviewed version before any model
output is examined.

## Decisions required before freeze

Independent review must check the metric against the actual six-arm forward
graphs; verify whether the value-only arm has the qualifying recursive
action-conditioned output; resolve the raw-state target/validity/horizon mask
and terminal-successor mechanics from its actual graph; approve support-key
and source-transition count semantics; validate role/terminal/pass behavior,
expected-terminal masks, and exact-tuple duplicate handling; accept or revise
the policy-mixture branch allocation and PRNG contract; reconcile the proposed
root schedule, fixed per-root compute cost, and missingness rules; and specify
result-artifact fingerprints and privacy/content boundaries.
The all-legal first-action expansion may be infeasible under available compute
and must not be assumed practical without measurement. Any revised allocation
requires a new draft and independent review. The 2.0-second Reversi8 p90
failure and all other pre-fit gates remain unchanged.
