Warning: truncated output (original token count: 51469)
Total output lines: 2703

# CAISSA-JEPA research roadmap

Updated: 2026-10-07. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

### 2026-10-07 V2.12 episode replay receipt candidate and six-arm review

Added a strict-schema in-memory receipt builder that exact-rule replays a full
episode, hashes its canonical state/action/outcome content with adapter/rules
identity, and binds all derived window payload hashes. Three synthetic receipt
tests plus the existing trajectory audit pass 10/10 under Python 3.14.7 with
temporary NumPy 2.5.3, not the locked research runtime. It does not bind source
file bytes, provenance, loaded implementation identity, or schedule/trainer
use. No real or research corpus, root, profile, inference, score, outcome, or
training was used.

An approved read-only `gpt-6-luna/high` review finds the adopted raw-state
`F→D→E` graph source-consistent but not ready to freeze. It identifies missing
trainer exclusivity, replay-derived selected-window masks, schedule-to-receipt
binding, full FLOP counter/branch bounds, and pinned runtime/backend/source
identity. The ≤5% compute gate remains **untested and unpassed**. Next: design
and review a receipt-bound scheduled-call boundary with actual mask checks and
bypass prevention; keep profiling and fitting closed.

### 2026-10-07 V2.12 schedule window-payload digests

Schedule schema v02 adds canonical per-window payload hashes and a batch
payload digest bound to seed/update identity and ordered rows; the validator
recomputes each batch digest and requires stable payload hashes whenever an ID
repeats across epochs. Thirteen payload/schedule tests and the adapter/model
regressions pass 26/26, with compile and whitespace checks. Digests cover only
materialized windows and adapter identity; they do not prove episode provenance, exact full-episode
replay, source/code fingerprints, or trainer use. No data or compute gate
opened. Next: produce source-bound replay receipts and integrate the frozen
manifest into an exclusive trainer boundary before any profile work.

### 2026-10-07 V2.12 schedule-manifest structural validator

Added a pure validator for the frozen 20×87 schedule shape: ordered update
indices and epoch/batch mapping, 64 IDs split 32/32 across the two training
games, 928 distinct windows/game reused as the same bank across three epochs,
per-arm horizon masks, and per-update direct-leaf H4 validity. Six synthetic
manifest tests pass; combined focused V2.12 boundary/adapter/model tests pass
23/23. This checks declarations only, not source payloads, selection,
train-split provenance, exact-rule replay, actual masks, or trainer use; D03
was left unchanged and no data/profile/fit gate opened. Next: bind schedule IDs
to payload/replay receipts and integrate exclusive trainer routing before any
profile work.

### 2026-10-07 V2.12 paired scheduled-batch boundary helper

Added a no-update six-arm call boundary that takes audited windows, enforces
the exact two training adapters and 32/32 game composition, checks the
20-seed/87-update index ranges and common paired model seed, and supplies one
read-only adapter batch to every arm. Its digest covers ordered window IDs
only. It is not an integrated trainer, manifest verifier, replay receipt,
profile, or parity result; `loss_grad` remains directly callable. The focused
scheduled-boundary, adapter, and model suites pass 17/17 with compile and
whitespace checks under Python 3.14.7 / NumPy 2.5.3, not the locked research
runtime. Next: specify/freeze the manifest identity and implement
trainer routing plus cross-update roster checks before attempting any profile
prerequisite.

### 2026-10-07 V2.12 raw-state/six-arm readiness recheck

An approved read-only review reconfirmed that the adopted raw-state `F→D→E`
recurrence, masks, pooled losses, terminal handling, backward path, common
initialization, and JEPA-only EMA routing match the current no-update graph at
source level. Six-arm graph freeze remains **NO** and the ≤5% gate remains
**untested and unpassed**. D03 already captures the direct-call bypass of the
64-row adapter guard, the required 32-per-game composition, shared batch/mask
identity, and direct-leaf valid-H4 condition. A narrow scheduled-call wrapper
is the next code-only boundary step once its accepted input/identity contract
is explicit; it cannot substitute for the trainer, replay/mask manifest, full
counter/branch bounds, or pinned runtime/LAPACK fingerprint. No gate opens.

### 2026-10-07 V2.12 latent-standard-deviation subcounter

Using NumPy's v2.4.6 source, expanded the root `z0.std(axis=0)` shape path
for a 64×32 float64 latent batch. The candidate per-call count is 8,192
add/subtract/multiply/divide operations under one-multiply-per-square
accounting, plus 32 square roots. All five focused reduction/source tests pass;
`compileall` and `git diff --check` pass. The reduction-shape tool and tests
include the internal mean and variance sum. This remains a source-based
subcounter: loaded runtime/reduction-kernel identity, independent count
acceptance, LAPACK, and the full compute gate remain open; no model/data ran.

### 2026-10-07 V2.12 raw-state and compute-freeze review

An approved read-only review found the adopted `F→D→E` raw-state method and
current no-update graph internally consistent, but did not establish data
replay, trainer behavior, or six-arm compute parity. It found one additional
freeze prerequisite: at review time, `windows_to_model_batch` accepted
nonempty batches of any size although D03 and the shape counters assume 64.
The subsequent fixed-size adapter guard is recorded below; the trainer must
preserve it and the manifest/replay evidence must attest matching batch
boundaries. Six-arm graph-freeze readiness remains
**NO** because the trainer, selected-window replay/masks, full counter and
branch bounds, and pinned runtime/LAPACK fingerprint are still absent. The
≤5% gate remains **untested and unpassed**; no tests or model operations were
run by the reviewer.

### 2026-10-07 V2.12 fixed-batch adapter guard

`windows_to_model_batch` now fails closed unless given exactly 64 windows, and
the synthetic adapter fixtures cover valid fixed-size conversion plus empty,
63-row, and 65-row rejection. This implements the v06 batch-size invariant at
the adapter seam. It does not enforce 32 windows per game, freeze selected
window order, or establish cross-arm schedule identity; the trainer, exact-rule
replay manifest, full counter, branch bounds, and pinned runtime remain absent.
An approved read-only reviewer accepts the adapter's narrow 64-window guard,
but notes the model graph can still be called directly with other sizes. The
trainer must prevent that bypass for scheduled updates. No profile or fit is
authorized.

### 2026-10-07 V2.12 reduction-shape inventory

Added a mask-parameterized inventory of objective `mean`/`sum` call shapes,
including both separate softmax denominator sums, value/target reductions,
bias-gradient sums, and per-tensor gradient-norm sums. Effective-rank entropy
uses explicit branch/activity and selected-spectrum inputs. The root latent
`np.std` path is now expanded from NumPy 2.4.6 source. Five synthetic/source
tests passed in the earlier inventory; the current focused suite also passes
5/5. The combined five-module model,
activation, matmul, residual, and reduction suite passes 25/25. For a fully
valid illustrative batch with 32 active spectrum entries, the earlier inventory
reported additions 32,343–182,712 and mean divisions 100–105 before latent-std
expansion; current totals are 36,375–186,744 and 132–137.
These candidate counts require independent acceptance and do not pin the actual
loaded reduction kernel. The `std` estimate is source-expanded only, while
LAPACK and other work remain omitted, so the figures are not total FLOPs or a
parity result. No gate opens.

### 2026-10-07 V2.12 loss-residual and square inventory

Added a mask-parameterized source subcounter for residual subtractions and
squared-error array elements across root, direct-leaf, outcome, latent-roll,
and raw-state losses. It records repeated square expressions used separately
by per-horizon means and pooled sums. Four synthetic/source tests pass; the
four-module model/activation/matmul/residual suite passes 20/20, and compile
and whitespace checks pass. Under fully valid illustrative masks, residual
subtractions range 128–38,272 and square elements 128–76,480. Counting each
square as a multiply gives only a candidate partial subtotal: D03's square
convention remains unaccepted, and reductions, gradients, scalar weighting,
regularizer/LAPACK, and other graph operations remain outside. No gate opens.

### 2026-10-07 V2.12 value-gradient scaling inventory correction

Source reinspection found that the value-head gradient expressions multiply
the loss-scaled delta by `(1-z²)`. The activation subcounter already counted
the derivative's square, subtraction, and derivative multiplication, but did
not separately count the preceding array-scale multiply. It now reports those
operations by value-head call site and provides a combined activation-gradient
array subtotal. Under fully valid illustrative masks, the added count is 256
operations per recurrent arm and 128 for direct-leaf. Scalar coefficient
construction and other elementwise/reduction/LAPACK operations remain outside
the subcounter. This correction affects no model objective and is not a total
compute or parity result; all profile/training gates remain closed.
The focused model/optimizer/matmul/activation regression set passes 20/20,
with `compileall` and `git diff --check` passing.

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
content…41469 tokens truncated…NCE_AUDIT_01_DRAFT.md.


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
