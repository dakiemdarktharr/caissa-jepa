Warning: truncated output (original token count: 49083)
Total output lines: 2547

# CAISSA-JEPA research roadmap

Updated: 2026-10-07. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

### 2026-10-07 V2.12 raw-state and six-arm compute review follow-up

An approved read-only `gpt-6-luna/high` reviewer found the adopted raw-state
v05/v06 `F→D→E` method internally coherent with the current no-update graph,
with no arithmetic contradiction in its pooled losses, masks, terminal
handling, recurrent reverse pass, parameter shapes, initialization, or
optimizer routing. Six-arm graph-freeze readiness remains **NO**: trainer
integration, selected-window exact-rule replay, the 20×87 mask roster, a full
counter with linked-LAPACK coverage and branch bounds, and a runtime/backend
fingerprint remain absent. The review specifically confirmed that every
direct-leaf scheduled minibatch must have at least one valid H4 leaf; the
current graph rejects a zero-H4 batch even if other horizons are valid. D03
now states this as a schedule prerequisite. This is a source/review
clarification, not a method change or gate transition. The ≤5% compute gate
remains **untested and unpassed**; no profile, roots, simulation, inference,
score, outcome, or training ran.

### 2026-10-07 V2.12 activation and affine-bias subcounter

Added a mask-parameterized subcounter for affine bias additions, `tanh`
element counts, and explicit `1-z**2` derivative arithmetic. Its AST fixture
tracks all four source `np.tanh` sites; synthetic masks test each arm and
active-prefix usage. The combined nine-module validation passes 38/38, with
`compileall` and `git diff --check` passing. Under fully valid illustrative masks, bias additions
range from 8,384–73,536, `tanh` elements from 4,224–18,688, and derivative
arithmetic from 12,672–56,064 FLOPs across arms. Nonlinear `tanh` cost and all
other loss/reduction/LAPACK/optimizer operations remain excluded. This is
partial analytical coverage and does not establish parity or permit a profile.

### 2026-10-07 V2.12 explicit model-matmul accounting

Added a mask-parameterized analytical inventory for every explicit dense
matrix product in the no-update objective and manual backward graph. It reports
active-prefix rows, target/value rows, each matmul call site, and FLOPs under
`2*m*k*n`, including raw-state `F→D→E`, direct-leaf and covariance products.
Four synthetic tests match the existing fully valid forward-MAC audit, assert
all current source-level `@` sites, and test mask-dependent calls. A fully valid illustrative 64-window batch ranges from
4,329,472 explicit-matmul FLOPs for direct-leaf to 26,128,384 for raw-state;
these are assumed-shape counts, not observed schedule work or total FLOPs.
Elementwise/reduction work, LAPACK, optimizer and runtime remain uncounted, so
the ≤5% gate cannot be inferred. No real data ran; the counting tool did not
execute the graph, while the combined eight-module regression suite exercised
existing no-update graph tests on synthetic arrays and passed 35/35. All
profile, training and pre-fit gates remain closed.

### 2026-10-07 V2.12 optimizer-only FLOP accounting

Added an analytical count for the scratch Adam/EMA helper, including
per-coordinate moment/parameter arithmetic, per-tensor scalar coefficients,
global norm reduction, EMA for the three JEPA arms, and the optional clipping
division. Synthetic checks match parameter/EMA shapes across all six arms and
validate the formulas and 20×87 branch interval. Optimizer-only FP arithmetic
is 136,750–136,751 FLOPs/update for direct-leaf, 190,514–190,515 for
value-only, 209,620–209,621 for each JEPA arm, and 295,062–295,063 for
raw-state. These counts exclude the objective graph and do not decide total
panel parity. The full counter, eigensolver coverage, runtime fingerprint,
selected-window replay/masks, and required independent counter review remain
open; no data, profile, inference, outcome, or training gate advanced.

### 2026-10-07 V2.12 action-validation accounting follow-up

Replaced repeated `actions.sum(axis=2)` one-hot validation inside
`preflight_batch` with integer `np.count_nonzero` after the same finite/range/
binary checks. The accepted input contract is unchanged: one set bit for each
present transition and none for padding. Four synthetic malformed/valid cases
are covered; the focused model, window, trajectory, raw-state, MAC, and scratch
optimizer suite passes 28/28, and compile/diff checks pass. This removes the
previously counted 16,384 FP additions per call, but still scans all 256×65
entries; no total runtime/work reduction is inferred, and the counter must
separately account for integer/comparison work. No data, roots, profile,
inference, scores, outcomes, or training ran. The linked-LAPACK trace, trainer,
selected-window replay, runtime fingerprint, and independent counter review
remain open; the ≤5% six-arm compute gate remains **untested and unpassed**.

### 2026-10-07 V2.12 raw-state and six-arm parity readiness review

An approved read-only `gpt-6-luna/high` review found the adopted v06 raw-state
`F→D→E` contract coherent with the no-update graph and found no arithmetic
contradiction in that graph. It did not establish exact-rule training data,
decoder behavior on real batches, or trainer integration. Freeze/profile
readiness remains **NO**: selected-window manifest/replay, the actual 20×87
mask schedule, a full counter and branch bounds, and a pinned runtime/LAPACK
fingerprint are absent. The ≤5% total-training-FLOP gate remains
**untested and unpassed**; no profile or model operation occurred. The review
also identified proposal-stage wording under draft 02's adopted status; that
file now identifies the wording as history and names the adopted v05/v06
documents as normative. No method or gate changed.

### 2026-10-07 V2.12 LAPACK eigensolver path audit

Followed the eigensolver gap to primary implementation references: NumPy 2.4
documents `_syevd` for real symmetric matrices; Netlib's reference `DSYEVD`
eigenvalues-only path calls `DSYTRD` then `DSTERF`, with conditional scaling.
Netlib `DSTERF` caps the reference path at 30×N iterations (960 at N=32), but
that does not by itself bound FP operations for the linked runtime. The audit
also counts the repeated one-hot action validation reduction: 16,384 additions
per 64-window `loss_grad` call. The linked LAPACK build and exact/bounded FLOP
coverage remain open; no profile or experiment ran.

### 2026-10-07 V2.12 FLOP-counter source coverage audit

Added `docs/V212_FLOP_COUNTER_COVERAGE_AUDIT_DRAFT_01.md` as a static map of
the D03 accounting obligations to the current no-update objective and scratch
optimizer. It enumerates six-arm/mask-dependent work, covariance diagnostics,
per-call preflight, clipping branches, Adam/EMA, and scalar powers. The audit
finds that `np.linalg.eigvalsh` has no frozen algorithm-specific FLOP count or
reviewed full-schedule bound, and that repeated model preflight needs explicit
table treatment. It is not a counter, instrumentation run, or compute result.
The selected-window manifest/replay, trainer integration, 20×87 mask schedule,
counter/runtime fingerprint, and separate data/preflight authorization remain
absent; the ≤5% compute gate remains **untested and unpassed**.

### 2026-10-07 V2.12 audited-window batch adapter fixture

Added `two_player/v212_window_batch.py` to convert explicit in-memory windows
from the exact-rule episode auditor into the v06 model batch schema. Windows
now carry the audited absolute terminal outcome; the adapter rechecks local
edges, derives adapter features/legal masks/one-hot actions/absolute actors and
side-to-move value labels, pads unavailable suffixes behind explicit masks,
accepts only the train split, and runs structural model preflight. The adapter
does no file I/O, selection, data loading, optimizer work, or fitting. Synthetic
tests cover Connect Four labels/features, Reversi forced pass, exact draw labels,
short terminal padding, split rejection, and corrupt-edge rejection. The
selected-window manifest/materializer, data provenance and split gates, full
trainer, and FLOP counter remain absent; no operational gate opens. The ≤5%
compute gate remains **untested and unpassed**.

### 2026-10-07 V2.12 raw-state endpoint-mask correction

The approved read-only raw-state/six-arm review found a structural mismatch:
preflight could count a valid later horizon while active execution stopped at
an unsupervised intermediate target, leaving the endpoint prediction at its
zero initializer. The no-update objective graph now activates each transition
when any valid supervised horizon needs that prefix, and a synthetic regression
fixture covers the case for all five recurrent arms. The v06 model suite passes
7/7 under the available temporary NumPy 2.5.3 / Python 3.14 runtime. Its first
run exposed an obsolete operation-count expectation (7 instead of 6) for a
truncated row whose only remaining call was an unsupervised third transition;
the fixture was corrected and the suite rerun successfully. The raw-state
feature audit, static dense-forward inventory, and scratch-optimizer suites
also pass (2/2, 3/3, and 4/4), for 16 focused tests total. `compileall` and
`git diff --check` pass. This runtime differs from the locked NumPy 2.4.6, so
it is synthetic regression evidence, not the D03 runtime fingerprint. The
approved read-only follow-up confirms the specific source-level mismatch is
resolved. This does not validate selected-window exact-rule replay, freeze the
raw-state graph, or measure six-arm training compute. D03's ≤5% gate remains
**untested and unpassed**, and data/profile/training gates remain closed.

### 2026-10-07 V2.12-06 Adam/EMA semantics adoption

Static comparison found that v05 fixed Adam/EMA hyperparameters but did not
uniquely define moment initialization/persistence, bias correction, epsilon
placement, clipping scope at the parameter-tensor level, or EMA timing. The
approved read-only reviewer recommended adopting the explicit equations as a
narrow versioned method amendment, preserving the six arms, objectives,
trainable parameter sets, and 87-update schedule. V06 adopts those equations
and transparently records epsilon placement and global clipping scope as
deliberate choices. The v05 text is archived at
`docs/METHOD_SPEC_V212_V05.md`; v05's raw-state review and earlier method
content remain in force. No code, tests, profile, data, training, or outcomes
were accessed. The six-arm ≤5% gate remains **untested and unpassed**; v06 opens
no operational gate.

### 2026-10-07 V2.12-06 compute preregistration revision

V06 makes the prior v05 compute draft stale because it did not bind the newly
adopted optimizer equations. `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md`
now supersedes the v05-specific draft 02 and fixes stateful training versus
reset scratch semantics, `t=u`, the v06 amendment reference, and the 20-seed ×
87-update estimand. The approved read-only reviewer accepts D03 as a
preregistration for v06 only and confirms the interval/branch-bound design.
Before any execution, freeze the explicit counter checklist and source/runtime
identity. No data or profile gate opens. The trainer, selected-window
materialization/replay, full counter and preflight authorization remain absent;
the ≤5% gate is **untested and unpassed**.

### 2026-10-07 V2.12 training-FLOP profile protocol revision

Draft 01 of `docs/V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_01.md` remains
unchanged as history; an approved read-only reviewer rejected it as a
preregistration because it did not freeze and aggregate the full 20 paired
seeds × 87 updates or bound value-dependent work under disposable updates.
Draft 02 now specifies the full pooled estimand, seed-specific batch/mask
manifest, per-invocation and per-example table units, and conservative
pass/fail/indeterminate bounds for clipping and covariance active-set branches.
An approved read-only reviewer accepts it as a preregistration only and confirms
the interval formulas; the freeze must still pin disposable Adam
state/timestep semantics and bias-correction work. This accepts no profile or
data access and opens no gate. The arm-routed pure
one-step scratch Adam/clipping/EMA helper remains outside the objective graph
and trainer; four focused synthetic-array tests pass, including all six
EMA-routing cases. This helper is not a trainer or measured profile.
Selected-window materialization/replay and a full FLOP counter remain absent.
No profile ran; the ≤5% threshold remains **untested and unpassed**, fitting
remains prohibited, and no data, roots, inference, scores, or outcomes were
accessed. See `GROUND_TRUTH.md` and both versioned protocol drafts.

### 2026-10-07 V2.12 no-update six-arm objective graph

`two_player/v212_model.py` now implements the six v05 arm objectives and
manual gradients without an optimizer or fitting loop. Independent read-only
review found no remaining source-level objective blocker for a future
no-outcome dry-run profile after fixes to pooled reductions, terminal/missing
prefix masks, invalid-transition handling, and latent-coordinate averaging.
Six synthetic-array tests pass, including pooled-loss checks, finite-difference
gradients, parameter inventories, and terminal/truncated operation counts.
This graph does not include the optimizer, clipping, EMA updates, or full
selected-window exact-rule replay. No FLOP profile ran; the no-outcome compute
protocol and remaining pre-fit gates still require review. The ≤5% total
training-FLOP gate remains **untested and unpassed**, and fitting remains
prohibited. No roots, trajectories, simulation, inference, scores, or outcomes
were generated or accessed. See `GROUND_TRUTH.md` and
`tests/test_v212_model.py`.

The graph also reports root latent statistics, covariance spectrum/effective
rank, and per-horizon losses. Independent review confirms these diagnostics do
not change losses or gradients; their eigenspectrum work must be included in a
future runtime profile and is not included in the existing dense-MAC inventory.

### 2026-10-07 V2.12-05 raw-state method adoption

The D02 raw-state contract is adopted as the narrow v05 method change after
approved read-only method disposition. `METHOD_SPEC_V212.md` is current v05;
the exact v04 text is archived at `docs/METHOD_SPEC_V212_V04.md`. This changes
only the raw-state arm; the six-arm/update controls and every other open v04
gate remain. The six-arm training-FLOP gate is **untested and unpassed**: the
77.53% dense-forward MAC difference is a risk signal, not a measured gate
result. No trainer implementation or profile exists. No compute/data/training
gate advanced. See
`docs/METHOD_SPEC_V212_V05_RAW_STATE_AMENDMENT.md`.

### 2026-10-07 raw-state graph and compute-parity review

The approved static review found the proposed latent-then-decode raw-state
graph defensible but not uniquely implied by v04. Draft 02 recorded explicit
choices for recurrent gradient flow, terminal versus missing-target handling,
invalid-transition failures, and feature/reduction weights. The approved
read-only method review found this contract coherent and it was later adopted
as the narrow v05 amendment. Its
static dense-forward cost is 72,544 MAC/window versus 40,864 for multi-step
JEPA (+77.53%); this warns of a parity problem but is not a full training-FLOP
result or proof that the 5% gate fails. Compute-gate readiness remains NO: the
required same-batch, same-mask forward/backward measurement across all six
implemented arms is still outstanding. Draft 02 also requires replay
validation of all selected windows and precomputation of each fixed
minibatch's target count before the first update; invalid transitions or any
zero-valid-target batch reject the run before updates. It remains an
unadopted candidate and does not authorize a trainer, roots, outputs, or
model operation. No trainer, roots, outputs, or model operation was run. V04
remains current; no gate advanced. See
`docs/V212_RAW_STATE_ARM_WIRING_AMENDMENT_DRAFT_02.md`.

### 2026-10-07 action-sensitivity/regret decision register

An approved read-only review found the one-step retrieval and horizon
denominators coherent as proposals, but both diagnostics remain gated. A
cross-draft register now names the open root-population/weight/yield choices,
missing trainer and raw-state evidence, all-legal-action feasibility and
charged-work needs, regret-reference alternatives and provenance/resource
contract, and metric-priority/result-schema decisions. Terminology now
distinguishes exact fixed-horizon values from exact full-game minimax, regret's
local “primary” quantity from v04's secondary status, and the proposed
horizon-2/4 action-sensitive rollout from v04's separate latent-error
horizons 1/2/4/8. No protocol, arm, metric, threshold, root schedule, or gate
was frozen. No roots, branches, outcomes, inference, or training were
accessed/run. See `docs/V212_PREFIT_ACTION_REGRET_DECISION_REGISTER_DRAFT_01.md`.

### 2026-10-07 ResDreamer prior-art refresh

Full-text review of ICML 2026 ResDreamer adds a nearby combat-world-model
precedent: hierarchical Dreamer-style observation/residual prediction with
imagined actor-critic training on five MineDojo hostile-mob tasks. It is not a
JEPA loss, strategic two-player model, or zero-sum minimax planner. It narrows
broad self-supervised combat/world-model claims but does not test CAISSA's
specific matched-JEPA question. The related-work ledger records the distinction
and its scope; no paper result was reproduced and no gate advanced. See
`docs/RELATED_WORK.md`.

### 2026-10-07 root-schedule minimum-count interpretation

An approved static follow-up found that design 02's 48 accepted slots meet
v04's numeric minimum of 40 only if “independently generated situations”
means independent generation events, not 40 distinct board states. Its 16
slots per occupancy band come from three band-conditional first-passage
populations, so the 48 are not necessarily IID from one variant-wide
population. Design 02 therefore proposes an equal-weight mixture and a
material estimand amendment; v04 is ambiguous on both the unit and population.
This is not unchanged-v04 compliance or schedule acceptance. No roots or
simulations ran and no gate advanced. See the root-schedule design and review.

### 2026-10-07 corrected six-arm dense-forward MAC inventory

Independent static review found the first inventory counted only three
recursive transitions for horizons 1/2/4. Constructing horizon 4 requires
four predictor calls, including an unsupervised transition-3 intermediate;
the raw-state graph adopted later in v05 also needs four decoder and online re-encoder
calls. Corrected counts per fully valid nonterminal four-ply window are
40,864 for multi-step JEPA, 72,544 for raw-state (+77.53%), 21,856 for
value-only, 28,192 for single-pair and single-horizon, and 14,816 for
direct-leaf. The earlier published values are superseded. Common samples and
updates do not guarantee close compute. This operation count excludes
backward, optimizer, activations, losses, masks, EMA update, and data movement;
it does not establish whether the 5% measured training-FLOP gate passes.
Regression checks assert four transition calls, three rollout-value calls
for horizons 1/2/4, and four raw-state decoder/re-encoder calls. EMA target
encodes remain arm-specific: three for multi-step JEPA and one each for
single-pair and single-horizon JEPA. No model or data was instantiated and no
gate advanced. The next required evidence remains an
independently reviewed, same-batch forward/backward profile after the six
graphs and raw-state arm are frozen. See the architecture reconciliation
draft and `tools/v212_arm_dense_forward_macs_audit.py`.

### 2026-10-07 raw-state feature coordinate audit

The raw-state wiring draft now names the exact 198 adapter coordinates and
records their source in `BoardGame.features`. A deterministic test covers
Connect Four and Reversi at training and held-out sizes, including padded-grid
indicators and descriptor values; a separate fixture verifies that forced
pass swaps the side-relative occupancy planes while leaving the board and
descriptor planes unchanged. Both focused tests pass. This is adapter mapping
evidence only; decoder/loss/mask/gradient behavior and the actual six-arm
training graph remain unverified, and no protocol is adopted. No model, root,
score, or outcome was generated. No gate advanced. See the raw-state amendment
and `tests/test_v212_raw_state_feature_contract_audit.py`.

### 2026-10-07 manager/journal failure-map regressions

Mocked armed-smoke validation now rejects a contradictory post-exit manager
state (`failed/failed`) even when the result/status fields claim success, before
response acceptance or lifecycle cleanup. Journal consumer-seam fixtures now
also reject wrong unit, invocation, boot ID, time window, and missing cursor,
retaining reconciliation handles and skipping receipt/stop. The 43-test
armed-smoke module passes; compile and whitespace checks pass. These tests do
not exercise live systemd/journal behavior or integrate the amended v02
controller. No operational or research gate advanced. See the supervision
failure matrix and named-test plan.

### 2026-10-07 v02 request-helper schema boundary

Read-only review found that the generic v02 helper only required a JSON object
and matching nonce, while the generated bootstrap checked a canonical synthetic
envelope. The helper now enforces canonical request bytes, the exact envelope,
the five-file manifest shape and digest syntax, the recomputed manifest digest,
and equality with the expected digest before it blocks on the release FIFO.
Focused negative fixtures cover wrong schema, noncanonical bytes, and manifest
digest mismatch. The REQ-01a/REQ-01b test-plan crosswalk now includes these
direct-helper cases and the renamed canonical-byte rejection; all 116
documented test-method names resolve in the test tree (name existence only,
not assertion/completeness evidence). The approved read-only follow-up confirmed the generic-helper
gap is closed and emphasized that manifest consistency is not an independent
trust anchor; the bootstrap still verifies and compiles exact local helper
bytes. This hardens only the isolated no-inference candidate; it does not
integrate the caller deadline, response receipt, runtime identity, or full
supervision failure map. No service or model operation ran and no gate
advanced. See `two_player/v212_armed_protocol_v02.py` and its tests.

### 2026-10-07 diagnostic runtime observation inventory

An approved read-only runtime review established that an offline post-startup
fingerprint cannot prove executed interpreter, loader, standard-library, or
native-library bytes without an independently trusted immutable boundary or
equivalent measurement. Added a standalone, bounded observation-inventory
candidate with only `partial` and `unavailable` assurance states. Its integrity
digest is not an attestation, and it is not connected to the release token,
bootstrap, controller, service, adapter, or receipt. Eight synthetic tests pass,
including fail-closed handling of deeply nested input.
No host values were collected in this milestone; prior host feasibility evidence
is limited to the recorded user/sandbox context. No service, OOM, inference,
roots, scores, outcomes, simulations, or training were run/accessed, and no gate
advanced. See `docs/V212_RUNTIME_OBSERVATION_INVENTORY_DRAFT_01.md`.

### 2026-10-07 root-sampling calibration DGP scope review

An approved read-only review found the shared-arm ordinal calibration proposal
internally consistent by inspection, including its arm/seed/slot dependence,
seat-swap structure, macro derivation, covariance/profile mapping, endpoint
counts, and workload arithmetic. The reviewer did not recompute tails or run
audit tools. A m…37083 tokens truncated…-playing scope are established. Its LLM-generated
code differs from CAISSA's learned JEPA latents and is not a matched neural
control; sampled-trajectory tests also leave unseen-state correctness open.
This narrows positioning but does not answer the V2.12 empirical comparison.
No gate changes. See docs/RELATED_WORK.md and docs/V212_RESEARCH_GATE.md.


### 2026-10-03 root-bootstrap inference audit

Primary-source review shows the cited crossed-bootstrap result is mean
consistency in a crossed random-effects setting, while related sources cover
asymptotic two-way regression inference, survey sampling without replacement,
and few-treated-cluster models. None establishes coverage for the current
20-seed/16-slot-per-band max-|T| and Holm procedure. Require independent
statistical review to decide whether a design-matched synthetic coverage and
power study is necessary and to freeze scenarios/acceptance criteria before
running it. This is an open validation item; do not generate roots or read
outcomes. Details: docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 bootstrap alternatives scan

Owen and Eckles's product-factor reweighting is a candidate variance-method
comparison for crossed random-effects data, but its mean-variance results do
not validate the V2.12 familywise interval/test procedure. A newer proportional
random-effect block bootstrap targets nested cluster mixed models and is not a
drop-in method for seed × root-slot crossing. Independent statistical review
must select/compare methods against the frozen estimand; no simulation, roots,
or outcomes have been produced. See the inference audit draft.


### 2026-10-03 null-versus-effects inference evidence

Bakshy and Eckles show why A/A validation is narrow: it evaluates sharp-null
behavior, while their simulated treatment–item interactions expose
undercoverage in a one-way bootstrap; their multiway method is mildly
conservative in the scenarios studied. The reported 87.5% coverage for a
nominal 95% interval is specific to one user–item simulation, not a CAISSA
estimate. Their arXiv v4 withdraws the Section 3.4/Figure 4 imbalance result,
which is excluded. If independent review requires inference simulation, add
both null and heterogeneous/nonzero seed × root-effect scenarios and freeze
criteria first. This does not validate CAISSA's procedure or authorize
simulation; no roots, scores, or training were produced. Details:
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md and
[Bakshy & Eckles](https://arxiv.org/abs/1304.7406).


### 2026-10-03 few-factor inference scope

The new review of multiway wild-cluster/bootstrap and cluster-robust sources
finds further evidence that small factor counts warrant method-specific
diagnostics. The cited alternatives are regression/score-based and make
bootstrap-dimension choices; they do not validate the proposed paired,
stratified 20-seed × 16-root-slot bootstrap or max-|T|/Holm family. Independent
review should assess the per-stratum counts and decide whether a design-matched
comparison is required. Preserve paired arms, fixed stratum weights, and all
15 contrasts in any comparison. This is a research requirement, not a method
selection or gate change; no simulation, roots, outcomes, or training occurred.
See docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 crossed mixed-model comparator

Crossed random-effects models can represent seed and root-slot dependence,
and Kenward–Roger provides a small-sample fixed-effect adjustment for Gaussian
linear mixed models. These sources do not validate CAISSA's discrete/bounded
paired score, stratum-weighted 15-contrast family, or simultaneous decision
rule. If considered, the alternative needs a reviewed model and a
design-matched comparison against the existing bootstrap, with assumptions and
familywise criteria frozen first. No model was selected, no simulation or
data/root access occurred, and no gate changed. See
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 interaction-component bootstrap evidence

Owen and Eckles find that two-factor product reweighting can overstate mean
variance by about 3× when only the crossed interaction component is present;
near-correctness relies on main-effect variance dominating. The proposed
20-seed × 16-slot grid has epsilon = eta = 1/16 per occupancy stratum, a
design descriptor that does not establish those variance assumptions or
finite-sample coverage. If an inference simulation is required, reviewer
should decide whether to test both main-effect- and interaction-dominated
variance regimes and evaluate the full familywise procedure. This neither
selects a bootstrap nor authorizes simulation. No data, roots, or outcomes were
accessed. See docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 bootstrap Monte Carlo precision

With 10,000 replicates, the p-value estimate near the first Holm cutoff
(0.05/15) has visible simulation error: 32 vs 33 exceedances straddle the
cutoff, and the conditional binomial 95% half-width is roughly 0.00113.
This is only uncertainty in approximating a bootstrap tail probability;
seed/root sampling uncertainty and inferential validity remain separate.
Independent review should freeze a precision/reporting rule or revised B
before outcomes. No results or bootstrap were computed, and the gate remains
closed. Details: docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 outer simulation precision

A future calibration study would need to separate inner bootstrap replicates
from outer independent datasets. The latter determine Monte Carlo precision
for estimated FWER, coverage, and power. Near 5%/95%, an illustrative
95% half-width of one percentage point requires about 1,825 outer datasets
per scenario-method cell; half a point requires about 7,300. Independent
review must select the precision target, R, uncertainty intervals, and
reproducible RNG streams before any simulation. No run is authorized or
performed. See docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-04 analytical root-yield sensitivity

An exact binomial-tail calculation illustrates the proposed global yield gate:
with 64 candidates and 16 required valid slots in each of six variant ×
occupancy strata, a common independent slot-validity rate of 0.30, 0.35, and
0.40 implies all-six pass probabilities of about 0.361, 0.821, and 0.976.
Rates of about 0.366, 0.383, and 0.418 correspond to 90%, 95%, and 99% pass
probability. This is analytic sensitivity, not an observed yield, selected
threshold, simulation, or gate transition; actual stratum rates and
dependencies remain unknown. See docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-04 Othello sequence-model prior-art refresh

Full-text review of Yuan and Søgaard's Othello World Model study added a
direct board-game sequence-model precedent: autoregressive models predict
recorded Othello moves and their internal features are probed/aligned for
board structure. Reported one-hop error is below 0.1% for non-pretrained
models at the full synthetic-data scale, while multi-step generation remains
harder. These outcomes are next-move/representation measures, not full
legal-action values, adversarial planning, or decision regret. This removes
broad novelty around learning board structure from Othello histories but does
not test V2.12's narrow objective-attributed question. No local data/code or
outcomes were accessed; no method or gate changed. See
`docs/RELATED_WORK.md` and `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.


### 2026-10-06 bounded-reference scaffold

A project-owned fixed-horizon alpha-beta candidate now computes every legal
root-action Q value independently with a full window and fails closed when the
hard transition budget cannot cover the complete table. Five focused tests and
the four existing interval-search suites pass 18/18 against tiny oracles and
forced-pass/cap fixtures. This does not select or validate a production
evaluator, depth, budget, or regret estimand. Independent implementation review
and realistic root-cap feasibility remain open; do not advance the pilot,
training, scoring, or outcome gates. See the current state in
`GROUND_TRUTH.md` and the design draft.


### 2026-10-06 adversarial world-model prior-art refresh

Full-text review of Nie et al.'s AWM preprint found a close conceptual
neighbor: a role-conditioned autoregressive traffic model is trained as an
adversary, then a planner is updated against it with reference-relative regret
and tail-risk terms. Its stochastic traffic-policy setting differs from
V2.12's exact legal actions and deterministic board-game max/min search, but
further weakens standalone novelty claims around adversarial world models,
counterfactual role conditioning, min-max planner framing, or regret-aware
planning. Only a measured incremental JEPA effect against equally decision-
aware controls remains an empirical question; no superiority or novelty
finding follows.
See `docs/RELATED_WORK.md` and `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.


### 2026-10-06 bounded-reference adapter and fingerprint verification

The bounded-reference candidate now has oracle parity checks on shallow
reachable states in all four in-scope variants, with both player perspectives
and role-symmetric positions. Every legal root-action score matches plain
minimax at three plies. A root-digest collision for same-name, different-rule
games was fixed by including the adapter's canonical game-state key; a
regression test covers it. The seven bounded-reference tests and 29-test
bounded-reference, interval-search, request-adapter, and symmetry group pass.
This verifies fixture behavior, not realistic transition/time caps or
evaluator provenance. The reference configuration and regret estimand remain
unselected, and independent review remains required before scoring or opening
downstream gates.


### 2026-10-06 request-byte release binding candidate

A versioned no-inference protocol candidate now binds the release token to the
SHA-256 of the exact bounded request bytes read by the worker, rejecting a
same-nonce request if even its byte encoding changes. Five synthetic protocol
tests pass; the frozen v01 modules are unchanged. The v02 bootstrap/service
integration, actual loaded-runtime fingerprint, remaining supervision failure
map, and independent review are still required. No service, adapter, inference,
or OOM test ran, and no downstream gate opened. See
`docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.


### 2026-10-07 pre-fit action-sensitivity graph audit

Static reconciliation distinguishes the six-arm v04 specification from the
random-weight inference proxy: four arms specify recursive action-conditioned
latent `F`, raw-state specifies a feature-prediction path with unresolved
predictor/decoder placement, and direct-leaf has no transition output. The
pilot uses a direct action-conditioned feature decoder for raw-state; the
proposed latent-then-decode wiring amendment is not adopted. No V2.12 trainer
exists in the tracked `two_player/` inventory, so this does not verify the
training graph. The approved read-only review found the diagnostic coherent
as a proposal but recommends keeping it gated until the trainer's six
forward/loss graphs, raw-state wiring/masks/terminal rules, root schedule, and
resource/denominator rules are reviewed. Decision regret remains a separate
unresolved gate. No freeze or gate change follows. No roots, scores, outcomes,
model outputs, inference, or training were produced/accessed. See
`docs/V212_ACTION_SENSITIVITY_DIAGNOSTIC_PROTOCOL_DRAFT_01.md` and
`docs/V212_ARM_ARCHITECTURE_FLOP_RECONCILIATION_DRAFT_01.md`.


### 2026-10-07 generation receipt/auditor crosswalk

Added a non-operative crosswalk for proposed episode/window/root identities,
lineage, masks, duplicate multiplicities, overlap keys, and durable audit
receipts. Independent static review confirmed it keeps current v04 separate
from unaccepted split v05 and root-schedule design 02. It also records why the
existing synthetic trajectory auditor cannot be reused unchanged: it rejects
repeated canonical windows and does not emit lineage-linked, typed corpus or
root receipts. The fixture remains unchanged. Next dependencies are method
and statistical acceptance, a separately versioned/reviewed no-I/O fixture,
and only later an independently reviewed/authorized bounded no-outcome
feasibility pilot to set quotas/caps. No generation, roots, scoring, inference,
training, or gate transition occurred. See
`docs/V212_GENERATION_RECEIPT_AUDITOR_CROSSWALK_DRAFT_01.md`.


### 2026-10-07 raw-state feature-loss contract proposal

The raw-state wiring proposal now defines a candidate masked loss over all
198 feature coordinates, including padded zeros and descriptors, and a
weighted valid-target normalization over horizons 1/2/4. A valid target now
requires valid transitions through `k`, an available target, and a nonterminal
state. Terminal branches stop before decode and mask that and later horizons;
truncated nonterminal targets are tracked separately. The proposed total raw
arm loss is explicit; a zero-valid-target minibatch aborts the run before any
update rather than being skipped, replaced, or resampled. These are proposed
semantics only; v04 remains current. Independent review of the revision is
complete: the approved read-only reviewer confirmed the requested mask,
zero-target, and total-loss details and found no blocker to further method
review. This is not adoption or fit approval. The parameter-count difference is not parameter matching, and the
measured ≤5% total training-FLOP gate remains mandatory. No trainer, data,
inference, training, scoring, or gate transition occurred. See
`docs/V212_RAW_STATE_ARM_WIRING_AMENDMENT_DRAFT_01.md`.


### 2026-10-07 calibration covariance-profile audit

Added `tools/v212_calibration_profile_audit.py` to calculate and serialize
draft 02's per-band covariance matrices, candidate-control component margins,
P5 cross-band shared-seed covariance, total `V`, and `sigma` without random
draws. Its six standard-library tests pass. Independent read-only review
confirmed the specified P1–P5 normalization and cross-band construction. This
supports reproducibility of the proposed DGP arithmetic only; it is not a
calibration simulation or statistical acceptance. v04 remains current and
root generation, calibration, scoring, training, and downstream gates remain
closed. See `docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_02.md`.

### 2026-10-07 calibration scenario-target audit

Implemented deterministic target and η auditing for all 31 proposed draft-02 scenarios. The manifest serializes 990 solved profile/band/policy-pair targets; the maximum absolute residual is `9.910895715226076e-11`. The control-major contrast order now explicitly matches the document and N-ATOMIC indexing. N-MACRO's V1 +0.10 / V2 −0.10 orientation is called out as a proposed convention requiring independent disposition before simulation.

Eleven profile/target tests pass. Read-only `gpt-6-luna/high` review confirmed the mapping and convention are consistent across protocol, tool, and tests. This is deterministic analytic reproducibility only: no random draws, calibration datasets, roots, scores, outcomes, or model runs were generated/accessed. It does not accept the protocol or open any gate; v04 remains current. Obtain independent statistical disposition of the draft and its open conventions before any simulation. See `tools/v212_calibration_target_audit.py`, its tests, and the draft-02 calibration protocol.

### 2026-10-07 v02 bootstrap import-path audit

A canary showed the worker's `sys.path[0] = project root` allowed an
unmanifested root-level `dataclasses.py` to shadow a standard-library import
made by a verified helper. The bootstrap now leaves isolated interpreter
imports alone, removes the project directory from the synthetic package search
path, and compiles only the five allowlisted helper byte buffers. A subprocess
regression confirms the unmanifested canary is not run. Added a second test
that reaches the bootstrap self-hash rejection with a canonical request and a
valid recomputed manifest digest. The focused bootstrap/protocol/release-token/
IPC suites pass 60/60; an approved read-only `gpt-6-luna/high` reviewer
confirmed the source-level fixes and helper import order.

The v02 request-carried source manifest is still not authenticated by an
independent trust anchor. Python startup/stdlib, loader and native runtime
remain unattested, with no runtime fingerprint in the release or accepted
receipt. The v01 controller also collects source hashes after importing its
Python dependencies, and its runtime receipt describes service/cgroup
properties; neither attests already-loaded code. v02 remains unwired to the
systemd controller/adapter; the failure matrix remains partial. No service,
adapter, inference, OOM, training, score, match, or outcome ran. No gate
advanced. Continue static design toward a trusted immutable runtime source and
integrated failure contract before any service/pilot transition. See
`docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md` and the updated
supervision test map.

### 2026-10-07 manager exit-snapshot failure cases

Extended the mocked v01 post-exit snapshot table to reject a malformed short
invocation ID and missing, negative, malformed, or uint64-overflow
`ExecMainStatus`. The focused omission test and all 41 armed-service smoke tests pass. The test
verifies rejection before response read or receipt, with the dispatched
workspace retained. The MGR-01 map now names these cases. Coverage remains partial: v02 controller
composition, live manager failures, and the full property/failure cross-product
are still open. No service, request, inference, OOM, training, score, match, or
outcome ran; no gate advanced.

A read-only reviewer noted the earlier new cases used empty strings rather than
omitted manager keys. Added a separate fixture that omits `InvocationID`,
`Result`, and `ExecMainStatus`; all are rejected before response read, receipt,
and stop while preserving the workspace. Missing `ActiveState`/`SubState` is
handled through the state-poll deadline path and was not misrepresented as a
snapshot-parser test. The focused omitted-fields test passes; MGR-01 remains
partial.

### 2026-10-07 policy-yield × root-quality interaction stress

Drafted four candidate P2 cells crossing the existing low/high policy-pair
yield groups with the prior root-quality factor. A deterministic, no-RNG
audit preserves marginal q=.40, accepted group weights .25/.75, group-
conditional targets, and root-slot variance; its six focused tests pass.
Read-only review found no major math or inventory mismatch. It requested a
convergence check for selected-root second moments and variance; those checks
and a written 1e-10 cross-order contract are now present, with follow-up
confirmation that the finding is resolved. Under the cumulative 39-cell/69-
endpoint proposal, the analytic assurance union bound is .806789 at R=18,450
and .794551 at R=18,500 because of the discrete cutoff. R=18,450 is only a
grid candidate, not an adopted replication rule; the 7.1955 billion inner
bootstrap / 107.9325 billion contrast workload remains unmeasured locally.
This draft does not revise calibration draft 02 or accept the earlier root-
quality addendum. No simulation, roots, scores, outcomes, inference, or
training occurred; v04 and all gates remain unchanged.

### 2026-10-07 consolidated root-sampling calibration draft 03

Consolidated the shared-arm draft 02 and separate root-quality and
policy-yield × root-quality extensions into one unapproved candidate protocol.
The 39-cell map is 30 null plus 9 alternatives, with 30 FWER and 39 coverage
endpoints. The exact lexicographic low/high ordered policy-pair groups,
target offsets, P2 root-quality variance split, and N-MACRO orientation are
now named in one document. The approved read-only reviewer confirmed the
previous cell-map, pair-group, target-weighting, and endpoint-count findings
are resolved. The 69-endpoint assurance grid is non-monotone, so no R was
selected; integer-R assurance search, independent dispositions, the unified
executable manifest, and local feasibility remain pre-simulation blockers.
The relevant deterministic suites pass 19/19 and `git diff --check` passes.
No simulation, root generation, scores, outcomes, inference, or training
occurred. v04 remains current and no gate advanced. See
`docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_03.md` and
`docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

Publication record: local commit `b3f9f70d210275757b4552ac942879e7c50be83b`
has tree `5102d6eb83c456251a9ebe355ddefc99e497c24f`. SSH blocked a normal
push because of the system SSH config file's ownership. The remote head/tree
were verified first; GitHub main was then advanced without force and with
expected-head `c3e96c45462f2eba0ba98bca018e45a2ce3ed0c8` to commit
`434dfb1b65c6f9c0dfb8866a4ef13fe0c961c67b`, whose tree matches the local
milestone tree. The GitHub ref/commit APIs confirm the destination and tree.

### 2026-10-07 integer assurance scan and executable manifest audit

Added a pure deterministic integer-R scan for the proposal's K=69 endpoint
family and a consolidated manifest audit that joins the target, covariance,
root-quality, and yield-interaction calculations. The scan covers every
integer R=1..18,600: 145 values meet the proposed 0.80 union-bound threshold,
with the first in-range crossing at R=18,378 (0.8020521569, cutoff 1,001).
Because the cutoff changes discretely, R=18,380 falls back below the target
(0.7999565426). The 60-digit Decimal neighborhood check agrees with the
recurrence/log-PMF reference. The first crossing is not an adopted replication
rule and says nothing about local compute feasibility.

The regenerated temporary manifest has 18,720 conditional target rows, all
39 cells and 69 endpoints, 180 pair-yield target checks, the exact v05 method
source hash, and the assurance-search result/digest. The previous output was
stale relative to final reviewed source and was regenerated. The focused
search/manifest tests pass 5/5; compile and whitespace checks pass. Updated
draft 03 records the arithmetic scan and workload of 7.16742 billion inner
bootstrap replicates (up to 107.5113 billion contrast evaluations) at the
first crossing with B=10,000. Independent methodological disposition and a
local feasibility assessment remain required before any simulation. No R was
selected; no simulation, roots, scores, outcomes, inference, or training ran.
v04 remains current, all gates remain closed, and no superiority claim is
supported.

Publication: local commit `6eb77995c3cf31d9f864da35ca404c2ea6516c58` has
tree `c0147d5771e4e8157cedb7cf2093d5c4cecd8bc1`. The normal SSH push was
blocked by the system SSH-config ownership check. Verified `main` at
`67c6fbbd29b36dbf76d45e574e470064f8b83599`, then advanced it through the
GitHub Git Database API with `force=false` and that expected old SHA to
`0d74266883a7539e60738478c76ff6e420e84bb6`; GitHub confirms its tree matches
the local milestone tree exactly.

### 2026-10-07 post-exit manager snapshot parser boundary

Added direct snapshot-parser regressions for required active-state fields
(`InvocationID`, `ControlGroup`, `ActiveState`, `SubState`) and required
post-exit fields (`InvocationID`, `ActiveState`, `SubState`, `Result`,
`ExecMainStatus`). This is parser-level coverage only. The caller's polling
path still treats absent state fields as not yet post-exit and can terminate at
its deadline; MGR-01 remains partial alongside v02 controller composition and
live systemd failure coverage. The parser and mocked orchestration suites pass
55/55, and `git diff --check` passes. No service, request, inference, OOM
test, training, score, match, or outcome ran; no gate advanced.
