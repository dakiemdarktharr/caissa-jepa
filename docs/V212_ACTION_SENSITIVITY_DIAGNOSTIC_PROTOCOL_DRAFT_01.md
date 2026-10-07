# V2.12 action-sensitivity diagnostic protocol — draft 01

**Status: proposal for independent review only.** This draft does not amend
METHOD_SPEC v05, change any arm, select checkpoints, authorize root or branch
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
action-conditioned recursive transition output described by METHOD_SPEC v05.
For the recursive raw-state arm, compare its decoded exact-state feature
prediction with the rule-generated successor features using that arm's
v05-defined target and validity mask. Do not introduce a new mask
or compare raw-feature MSE numerically with latent MSE. Mark arms without the
relevant transition output as not applicable, not as zero error. The raw-state
target/mask contract is fixed by v05, but the six-arm implementation graph
and its support ledger must still be verified before this diagnostic is
frozen; this draft does not infer implementation behavior.

## Sampling and support records

Use only a separately reviewed, prehashed development-root schedule after its
own method review. No root may be generated under this draft. The root-slot is
the reporting unit; retain repeated states as separate scheduled draws if and
only if the accepted root protocol does so. Freeze game/rules, adapter,
encoder and predictor hashes, target-encoder rule, action order, root receipt,
policy configuration, branch RNG derivation, and software versions before
diagnostic computation.

**Conditional alignment candidate, not an accepted schedule:** if
`V212_DEV_ROOT_SCHEDULE_DESIGN_02.md` is accepted unchanged, use its three
root-occupancy bands `[0,1/3)`, `[1/3,2/3)`, and `[2/3,1)`, where occupancy is
occupied cells divided by board area (the four initial Reversi discs count;
forced passes advance ply but do not change occupancy). Keep each accepted
slot as a root draw, including repeated boards; average root-slot summaries
equally within each variant × band, weight the three bands equally within a
variant, and weight the two variants equally for a macro summary. The proposed
schedule's first-16-valid-of-64-per-band rule and global failure if any of the
six bands under-yields also govern only if that schedule is independently
accepted. Until then, root population, weights, and failure/yield treatment
remain open; this paragraph does not authorize generation or choose a
schedule.

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
horizon. It is not a missing or failed prediction. For operational accounting,
report (i) planned branch cells, one per accepted root-slot × legal first
action; (ii) expected-terminal cells, whose exact branch is observed to reach
terminal at or before `h`; and (iii) target-eligible cells, which are every
planned cell without an observed expected-terminal event. Thus a branch
interrupted before reaching `h`, without a terminal already observed, is
target-eligible but incomplete, not terminal-masked. The error denominator is
the target-eligible count, not the planned count; terminal cells remain in the
planned ledger and are reported separately. Every target-eligible cell must
have an exact state at `h`, its required prediction, and target. Interruption,
nonfinite output, or unavailable nonterminal target is an incomplete cell,
not an expected mask, and invalidates its predeclared aggregate. For each
variant × occupancy stratum and horizon, report schedule-level `N_planned`,
`N_terminal`, and `N_target_eligible = N_planned - N_terminal`. Report
`N_complete` separately per arm and model seed; a valid error aggregate
requires `N_complete = N_target_eligible`. Report incomplete counts and
reasons when they differ. The reported horizon error is conditional on exact
branches that remain nonterminal at `h`; it is not an unconditional average
over all planned branches.

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

The proposed open-loop subdiagnostic reports horizons 2 and 4 on its
intervened, receipt-policy-pair-conditioned branches. It does not replace or
reduce METHOD_SPEC v04's separate latent-error reporting at horizons 1, 2, 4,
and 8, and it does not estimate the behavior-policy first-action or uniform
legal-continuation distribution.

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

## Static spec/pilot graph reconciliation (2026-10-07)

This reconciliation reads METHOD_SPEC_V212-04, the random-weight pilot model
and its v02/v03 wrappers, plus the raw-state wiring proposal. It does not
establish a trained or optimizer graph: no V2.12 trainer is present in the
tracked `two_player/` inventory. The pilot uses fixed random weights and is a
compute/inference proxy only.

| Arm | v04-specified transition path | Random-weight pilot path | Diagnostic status |
| --- | --- | --- | --- |
| Multi-step JEPA candidate | Recursive action-conditioned latent `F`; JEPA targets at 1/2/4 plies | `advance` uses the shared 104-to-32 latent predictor | Latent probe is structurally applicable to the proxy; trained graph and support ledger are absent |
| Single-pair JEPA | Same recursive `F`; latent target only at the 2-ply point | Same latent-predictor path as other non-raw predictive arms | Latent probe is structurally applicable to the proxy; target-path training support is unverified |
| Recursive raw-state dynamics | “Shared encoder/predictor trunk and a decoder”; exact placement of `F` is unresolved in v04 | Direct 104-to-198 action-conditioned decoder with `tanh`, then re-encode; allocated 104-to-32 `predictor_w` is unused on this branch | Do not score as the v04 raw-state arm. The latent-then-decode wiring proposal is not adopted; feature target, masks, and terminal/horizon contract remain unresolved |
| Value-only latent rollout | Recursive action-conditioned `F`; outcome targets at predicted 1/2/4-ply states; no latent/raw-state transition target | Same 104-to-32 latent-predictor path | Structurally qualifies at spec and proxy level, but an actual trained graph/support path is unavailable |
| Direct-leaf value | No learned transition predictor | No `advance`; values exact encoded leaves | Transition diagnostic is not applicable, not zero error |
| Single-horizon JEPA | Recursive action-conditioned `F`; JEPA target at one ply | Same 104-to-32 latent-predictor path | Latent probe is structurally applicable to the proxy; trained graph and support ledger are absent |

The pilot class allocates a predictor matrix for every arm, including the
raw-state arm, but allocation is not execution or effective capacity. Its
v02/v03 runners reuse this model path; their wrapper changes do not provide a
trainer or resolve the raw-state graph. Consequently, this audit narrows the
static applicability decision but does not satisfy the independent graph
verification required for protocol freeze. Keep raw-state metrics not
estimable/not applicable pending a reviewed wiring contract; do not substitute
the pilot decoder or compare its feature error numerically with latent MSE.

No raw-state target masks were inferred from the diagnostic wording, and no
arm was removed or changed. Value-only qualification here means only that the
v04 and proxy paths expose a recursive action-conditioned latent transition;
it does not validate its outcome-label support or establish a trained
implementation. The protocol remains a review draft with no thresholds,
checkpoint selection, root generation, scoring, inference, training, or
outcome access authorized.

The separately versioned raw-state wiring amendment now proposes a specific
198-coordinate feature MSE and horizon mask for independent review. This is a
candidate clarification only; the diagnostic still does not adopt it, and v04
remains unchanged. See
`docs/V212_RAW_STATE_ARM_WIRING_AMENDMENT_DRAFT_01.md`.

**Independent read-only pre-fit review (2026-10-07): keep gated; no freeze
approval.** The reviewer confirmed that v04 specifies latent `F` paths for
the candidate, single-pair, value-only, and single-horizon arms; the raw-state
arm is a distinct feature-prediction path whose predictor/decoder placement
and target contract are unresolved; and direct-leaf has no transition output.
The pilot verifies only its random-weight proxy graph, not a future training
graph or value-only loss/support implementation. The diagnostic's evaluation
target distinction, N/A treatment, and stated one-step terminal/collision
rules were considered coherent as a proposal. Before freeze, review the
eventual trainer's six forward/loss graphs, adopt and specify raw-state wiring,
feature masks and terminal handling, and separately resolve the accepted root
schedule and resource/denominator rules. The decision-regret protocol remains
a separate unresolved gate. No roots, outputs, simulations, inference, or
training were accessed or run.

**Independent read-only action-sensitivity/regret review (2026-10-07): no
freeze approval.** The reviewer found the descriptive one-step support,
terminal, collision, and denominator concepts mostly coherent, but identified
three blockers shared with the regret design: actual per-arm trainer/loss
graphs and raw-state target/mask behavior are unavailable; the accepted-root
population, occupancy strata, repeated-state weighting, and failure/yield
estimand are not frozen; and all-legal-action branch expansion has no measured
feasibility or predeclared charged-work allocation. Before freeze, operationally
define occupancy strata and how terminal branch cells enter horizon
denominators/failure summaries. Preserve the explicit conditioning of the
multi-step diagnostic on the receipt-assigned policy pair; it does not estimate
behavior-policy first-action or uniform-legal-continuation performance. The
review adopted no arm, metric, root schedule, threshold, or allocation. No
roots, branches, model outputs, simulations, inference, or training were
accessed or run.

**Aggregation crosswalk (2026-10-07):** the root-population and terminal-cell
accounting are now stated as a conditional alignment candidate above. It
reuses design 02's three occupancy bands, repeated-slot sampling unit,
equal-band/equal-variant weights, and global under-yield stop only if an
independent method review accepts that schedule unchanged. It also distinguishes
planned, terminal-masked, target-eligible, and completed horizon cells. This
resolves wording ambiguity but does not resolve the underlying root-schedule
acceptance, sample-size rationale, trainer graph, or branch feasibility; no
protocol or gate is frozen.
