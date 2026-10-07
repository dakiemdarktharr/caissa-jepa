# CAISSA-JEPA research roadmap

Updated: 2026-10-07. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

### 2026-10-07 reference DSYEVD driver-site bound

`tools/v212_dsyevd_driver_source_bound.py` isolates the reference LAPACK 3.12.1
N=32 eigenvalues-only driver's direct arithmetic plus its reference DSCAL
rescale loop: 2–4 divisions, 0–32 multiplications, and two separately
reported square-root calls. Conditional DLASCL and DSCAL helper work, DLAMCH,
DLANSY, DSYTRD/DSTERF internals, and actual NumPy-linked LAPACK dispatch
remain unresolved. This small source-site interval is not a full eigensolver
bound and does not clear counter or parity gates. An approved read-only review
accepted the arithmetic within this boundary and confirmed helper divisions
remain excluded. Continue static accounting of the remaining helpers and
loaded runtime; keep profile and training closed.

### 2026-10-07 static DNRM2 binary candidate

Static inspection of five architecture-specific DNRM2 kernels in the observed
Linux `scipy-openblas` binary yields a conditional N=32 upper candidate of
2,030 add/multiply FLOPs and 58 square-root calls for at most two DNRM2 calls
per DLARFG reflector, plus two length-one wrapper fast paths. The report is
SHA-256 bound to that wheel and does not attest the runtime-selected function
pointer, Windows target, execution bytes, or helper internals. It is separate
from the reference-source subtotal. An approved read-only review accepted the
arithmetic under the assumptions, but did not inspect the binary trace or
verify its hash. The reproducible `--audit-binary` mode now validates the exact
wheel hash, all five discovered kernel symbols, and identical static opcode
totals (18 `fmul`, 21 `faddp`, one `fsqrt`) with GNU Binutils 2.47. It does not
attest runtime dispatch or dynamic loop execution. A read-only code review
caught and a focused regression corrected the inventory check to reject both
missing and unexpected symbols. This does not close eigensolver coverage or
clear any gate. Next admissible work is the remaining static LAPACK/runtime
accounting; do not run service, eigensolver,
profile, inference, simulation, or training until the relevant gates pass.

### 2026-10-07 DSYTRD reference path and partial helper accounting

`tools/v212_dsytd2_rank_update_bound.py` now reports 47,165 reference-BLAS
rank-update operations plus a 11,745 direct DLARFG/DSCAL candidate subtotal,
for 58,910 candidate operations excluding DNRM2, DLAMCH, and DLAPY2 helper
internals. The latter subtotal is a source calculation, not independently
reviewed. Primary-source inspection also establishes that reference
ILAENV(v3.12.1) returns NB=32 for DSYTRD at N=32; tagged DSYTRD consequently
falls back to DSYTD2 and omits DLATRD/DSYR2K in that reference path. Actual
linked ILAENV and kernel dispatch remain unverified, so this is not a complete
eigensolver or runtime bound. The approved reviewer confirmed only the
47,165 rank-update formulas/subtotal and emphasized the DNRM2/runtime caveats.
The focused DSYTD2/DSTERF suite passes 7/7; targeted compile and whitespace
checks pass. No eigensolver or model ran; no gate changed.

### 2026-10-07 DSTERF source-bound correction

Added a reviewed, deliberately partial source-operation bound for the
OpenBLAS v0.3.31 reference DSTERF N=32 path: 428,497 add/subtract/multiply/
divide operations per call, plus 48 separately reported power sites (or
428,545 if each is treated as one multiply). Independent review caught that
an earlier 428,466 draft omitted non-shift convergence scans; the corrected
value includes them and tightens the disjoint initial split scan. DSYEVD,
DSYTRD, scaling/helper internals, and the actual future linked binary remain
unbounded, so this does not clear counter coverage or parity. Four focused
tests and static checks pass; no model/runtime profile ran.

### 2026-10-07 exact-version runtime observation

CPython 3.11.9 and NumPy 2.4.6 are now available together in a temporary
Linux environment. A read-only runtime observation identified the NumPy wheel's
`scipy-openblas` 0.3.31.188.0 build and matched file-backed executable mappings
to their backing files at read time. `execution_bytes_verified` remains false;
the declared lock describes a Windows environment, and no D03 profile process
was run. This corrects the earlier package-availability note without resolving
the final runtime identity, LAPACK operation bound, full counter, or six-arm
parity gate. The temporary environment and receipt were excluded from Git.

### 2026-10-07 partial-ledger parity sensitivity

`tools/v212_parity_shared_work_sensitivity.py` applies D03's 5% range rule to
the all-valid source-covered intervals under the explicit assumption that all
omitted FP work is identical across arms and the same per-update fixture
repeats. The raw-state upper and direct-leaf lower endpoints imply a
hypothetical common omitted term of 446,264,889 FLOPs/invocation, or
776,500,906,860 over 1,740 updates, to dilute the partial subtotal endpoints
to 5%. This is a sensitivity calculation; omitted work need not be common,
and actual masks/runtime/LAPACK remain unmeasured. Three tests pass; full
counter, parity, profile and fit eligibility remain false. No gate changed.

### 2026-10-07 source-operation ownership crosswalk

Added a source-hash-bound candidate crosswalk covering all 964 AST sites in
the current model and scratch optimizer. Its v02 report digest also includes
the two analyzer source hashes and the hashes of all referenced owner files
(all present). Current digest is `a78afac2369f200a792bfdeb09a96cdc1db7e4c1814b00ac89d55072061fe7e9`.
It records 107 candidate-owner, 32
partial-owner, one runtime-unverified-owner, six separately reported, ten
separately/partially bounded non-FP, one blocking unresolved eigensolver, 186
unresolved, 452 unresolved non-FP, and 169 context-owned/unresolved sites.
These are syntax-site dispositions, not operation counts. Candidate ownership
does not validate expression context, branch work, component overlap, runtime
behavior, or complete accounting. Read-only review caught and corrected the
`_finite_array` finite-check mapping and the input-dependent `np.asarray`
conversion classification; the report digest does not attest implementation.
The 80-test accounting/source suite passes under Python 3.14.7 with NumPy
2.5.3; the eight standard-library inventory/crosswalk tests also pass under
Python 3.11.17. Targeted compile and whitespace checks pass. The
crosswalk explicitly denies full-counter, graph-freeze, and parity eligibility.
After fetching current `origin/main`, the strict v03 schedule/replay-receipt/
adapter/model synthetic regression group passes 46/46 under Python 3.14.7 /
NumPy 2.5.3; production data, trainer, and profile gates remain closed.

Next research step remains static closure of semantic ownership and the
eigensolver/runtime bounds, then independent review and integrated trainer /
schedule evidence. No profile or gate was opened; the ≤5% six-arm gate remains
**untested and unpassed**.

### 2026-10-07 owner-reconciled partial FLOP ledger

Added `tools/v212_partial_flop_ledger.py` to combine source-covered candidate
FP arithmetic using the unique owner fields from the counter audit. It excludes
known square/activation/reduction overlaps and reports effective-rank and
optimizer branch intervals. Four focused accounting tests, targeted compile,
and whitespace validation pass; the combined ledger/subcounter suite passes
55/55 under Python 3.14.7 / NumPy 2.5.3 (not the locked runtime). Independent
static review found no overlap defect and confirmed the masked-fixture
coverage follow-up. A subsequent review confirmed the native call-versus-output
element labels for log and square-root counts.

For illustrative all-valid masks, the source-covered per-invocation intervals
are 9,540,294–9,540,390 (multi-step JEPA), 7,885,496–7,885,592 (single-pair),
27,130,644–27,130,740 (raw-state), 7,038,991–7,039,087 (value-only),
4,588,091–4,588,187 (direct-leaf), and 7,885,496–7,885,592 (single-horizon).
Raw-state therefore carries a substantial known-work parity risk. These counts
exclude linked LAPACK/runtime operations, several non-FP and unsupported
categories, and replay-derived 20×87 masks; they are not total FLOPs, a parity
result, or authorization to fit. Graph freeze remains **NO** and ≤5% remains
**untested and unpassed**.

The ledger also reports the non-FP/unconverted counts already supplied by the
subcounters in their native units, distinguishing call counts from output
elements, without converting them into FLOPs. Preflight, indexing, copies,
control flow, loaded-runtime dispatch, and unsupported operators remain
incomplete.

### 2026-10-07 raw-state and six-arm freeze review

An approved read-only `gpt-6-luna/high` review found the adopted v05/v06
raw-state `F→D→E` method and current objective source internally consistent.
The full six-arm graph is not ready to freeze: an integrated trainer/trace,
selected-window roster and exact-rule replay receipt, and the frozen 20-seed ×
87-update batch/mask schedule are absent; data/preflight authorization is also
still closed. The model entry points permit arbitrary batch sizes, and the
64-window adapter does not establish 32 windows per game.

The full counter still lacks a reviewed owner-reconciled aggregate, the actual
NumPy reduction/runtime and linked-LAPACK paths, complete per-update non-FP and
unsupported-operation inventories, and conservative full-schedule bounds for
value-dependent branches. Corrected D03 wording now separates the accepted
candidate source-level square convention from unresolved loaded-kernel and
counter coverage. Graph freeze remains **NO** and ≤5% remains **untested and
unpassed**. Review was read-only; no tests, data, roots, profile, simulations,
inference, scoring, or training ran.

### 2026-10-07 reduction counter owner fields

The reduction-shape report now tags each addition row with its owner and
provides ordinary-reduction versus effective-rank entropy totals, plus a
non-overlapping root-`std` component breakdown. A source regression now links
the assumed `(64, 32)` diagnostic shape to the fixed 64-window adapter,
32-wide encoder config, `z0` construction, and `std` call. The legacy candidate
totals are unchanged; schema is v04. The six focused reduction tests passed
under a temporary in-process Boolean-mask shim because NumPy is absent from
available local Python environments (the lock specifies NumPy 2.4.6/Python
3.11.9); five effective-rank tests, targeted compileall, and `git diff --check`
also pass.
The shim does not validate NumPy or the locked runtime. No data or model
operation ran. This does not assemble the complete counter:
linked LAPACK, all non-FP branches, the replay-derived 20×87 masks, runtime
identity, and trainer trace remain open. Freeze remains **NO** and ≤5% remains
**untested and unpassed**.
The approved read-only follow-up found no current owner/double-counting defect;
the source regression now binds parameter initialization to latent width. An
integrated route from the 64-window adapter to `loss_grad` is still not proven;
no trainer exists to provide that evidence.

### 2026-10-07 candidate counter-owner reconciliation

Added a draft field-level owner partition for the existing V2.12 arithmetic
subcounters, including explicit exclusions for the square/residual/activation/
reduction/effective-rank overlaps. It emits no combined count and has not been
independently reviewed or frozen for D03. The reduction export still needs
owner-filtered rows; linked LAPACK remains unbounded; non-FP/unsupported work,
replay-derived 20×87 masks, runtime/backend identity, and integrated
trainer/update trace remain open. This was documentation-only: no data, model,
profile, roots, inference, outcomes, simulation, or training ran. Graph freeze
remains **NO** and the ≤5% gate remains **untested and unpassed**.

### 2026-10-07 source-wide arithmetic ownership review

An approved read-only `gpt-6-luna/high` sweep found plausible source-level
owners for explicit FP arithmetic in the encoder/value heads, regularizer,
`loss_grad`, and scratch Adam/EMA code; it confirmed the corrected scalar
subtotal **46 / 30 / 46 / 22 / 3 / 30**. It did not accept a complete counter.
The linked-LAPACK eigensolver, exact loaded reduction/runtime behavior,
complete per-update non-FP bookkeeping, and integrated trainer/update trace
remain open. Several shape reports overlap intentionally and need a single
reconciled ledger before summation. No code/model/data/profile/outcome work ran;
graph freeze stays **NO** and the ≤5% gate remains **untested and unpassed**.

### 2026-10-07 objective scalar counter correction

The source AST audit found the scalar root-value gradient coefficient
`2.0 / batch_size` and the pooled target-loss normalization `/ d` or
`/ FEATURE_SIZE` absent from the first scalar inventory. Both are now counted
once at their source sites. Independent read-only review confirmed corrected
all-valid six-arm subtotals of **46 / 30 / 46 / 22 / 3 / 30** operations per
invocation, with no overlap across the inspected counters. The combined
objective/gradient/activation/residual/square suite passes 26/26; compile and
whitespace checks pass. These remain partial analytical counts, not full
compute or parity evidence. No model/data/profile or outcome work ran. Graph
freeze remains **NO** and the ≤5% gate remains **untested and unpassed**.

### 2026-10-07 pooled target-gradient multiplier subcounter

Added a mask-parameterized count for the per-coordinate scalar-coefficient
multiply on enabled latent and raw-feature target gradients. All-valid
illustrative counts in six-arm order are 6,144 / 2,048 / 38,016 / 0 / 0 /
2,048. An approved read-only reviewer confirmed the target dimensions and
horizon masks match the source and found no overlap with activation,
residual/square, or matmul inventories. The combined focused suite passes
21/21; compile and whitespace checks pass. This is a small source-shape
subcounter, not full coverage or parity evidence. No model/data/profile or
outcome work ran; graph freeze stays **NO** and the ≤5% gate remains **untested
and unpassed**.

### 2026-10-07 gradient-accumulation inventory and independent correction

Added a mask-parameterized inventory of candidate array additions at
loss-gradient state and parameter-buffer accumulation sites. An approved
read-only reviewer caught an omitted predictor `fw/fb` gradient-buffer update
in the first raw-state formula; corrected the raw-state full-valid subtotal by
13,440 additions (3,360 per active step). The corrected illustrative six-arm
subtotals are 48,709 / 44,613 / 182,877 / 42,565 / 19,043 / 44,613. This is a
narrow source-shape addition inventory, not total FLOPs or a parity verdict.
The new subcounter and related objective/elementwise suites pass 16/16, with
compile and whitespace checks passing. No model/data/profile or outcome work
ran. Graph freeze remains **NO**, and the ≤5% gate remains **untested and
unpassed**.

### 2026-10-07 pooled objective scalar subcounter

Added a mask-parameterized candidate inventory of horizon-denominator
weighting, per-horizon scalar scales, pooled-loss accumulation, and scalar
gradient coefficients. The corrected all-valid subtotals are 46 operations per
invocation for multi-step JEPA and recursive raw-state, 30 for single-pair and
single-horizon JEPA, 22 for value-only rollout, and 3 for direct-leaf value.
This is a deliberately narrow scalar-only subcounter; it does not count array
operations or reductions and does not establish total arm compute. Direct-leaf
accounting enforces the existing nonempty-H4 schedule condition. The new
subcounter plus regularizer/policy accounting tests pass 11/11, with compile and
whitespace checks passing. No model/data/profile or outcome work ran. Graph
freeze remains **NO**; the ≤5% gate remains **untested and unpassed**.

### 2026-10-07 elementwise objective subcounters

Added candidate source-shape subcounters for the fixed 64×65 policy softmax/NLL
path (including its gradient batch normalization) and the root regularizer's
elementwise arithmetic/scalar weighting. Reduction, square, matmul, and
eigensolver components stay separately owned to avoid double counting. Their
source-AST/shape tests pass 6/6. These additions reduce objective-coverage gaps
but do not establish loaded NumPy work, complete FLOPs, or parity. Graph freeze
remains **NO**; the ≤5% gate is **untested and unpassed**.

### 2026-10-07 schedule mask-integrity schema v03

Schema v03 (with draft 02 preserved) requires the three mutually exclusive
clean-window categories to cover all 64 rows at every horizon and rejects any
declared invalid-transition count. This matches D03's stop-on-invalid rule and
the adapter's exact local-transition check. Schedule, replay-receipt, adapter,
and trajectory tests pass 29/29. This catches inconsistent declarations; the
actual replay-derived 20×87 schedule and source provenance remain absent.
Graph freeze is **NO** and ≤5% parity is **untested and unpassed**. No gate
advanced.

### 2026-10-07 clipping branch source correction

The scratch optimizer always materializes `grads[key] * clip_scale` for all
parameter coordinates, including when `clip_scale` is 1. The branch-specific
operation is only the scalar division on the norm>5 path. The analytical
six-arm report now exposes both counts and its test ties them to the source AST;
optimizer-accounting tests pass 4/4. This corrects source coverage, not total
compute: objective/LAPACK coverage, frozen masks, and runtime identity remain
open. Graph freeze is **NO** and the ≤5% gate remains **untested and unpassed**.
No gate advanced.

### 2026-10-07 raw-state and six-arm parity review

An approved read-only `gpt-6-luna/high` review found that the method defines
raw-state targets but current adapters and synthetic fixtures do not prove
selected-window provenance, full-episode replay, split/duplicate identity, or
the 32-window-per-game cross-arm roster. The illustrative fully valid dense
forward inventory is 72,544 MAC/window for raw-state versus 40,864 for
multi-step JEPA (+77.53%); this is a risk signal, not a complete graph or parity
verdict. Integrated forward/backward/objective counts, actual masks, linked
runtime/LAPACK identity, and branch bounds remain open. Graph freeze is still
**NO** and the ≤5% gate is **untested and unpassed**. No gate advanced.

### 2026-10-07 V2.12 effective-rank branch interval

Added `tools/v212_effective_rank_branch_accounting.py` to bound the selected-
spectrum normalization/log/entropy branch after eigensolver and spectrum sum.
For each arm across the 20×87 update slots, inactive work has a zero lower
bound; active K=1..32 has upper bounds of 53,940 candidate reduction additions,
55,680 multiplications/divisions/log calls, and 1,740 exp calls. Comparison and
unary-negation counts are separate. A zero-selected-count input is now rejected
when the active branch is declared. Branch/reduction validation passes 10/10.
The bound excludes the eigensolver and does not attest actual branches. Runtime,
linked-LAPACK count, frozen masks, complete FLOP coverage, and branch bounds
remain open; no gate advanced.

### 2026-10-07 V2.12 square-site counter inventory

An approved read-only `gpt-6-luna/high` review accepts the semantic convention
of one candidate multiplication per element for every fixed-shape array
`x ** 2`; this is not a claim about NumPy's loaded power kernel. The same review
accepts ordinary-reduction `I-O` additions and mean `O` divisions only as
analytical shape-level candidates. Added
`tools/v212_model_square_flop_accounting.py` to map all 20 current square AST
sites, including regularization, loss residuals, tanh derivatives and returned
gradient-norm coordinates. Its fully valid illustrative six-arm counts are
38,242 / 30,050 / 116,712 / 25,954 / 16,002 / 30,050. Existing activation,
residual and root-`std` square counts overlap and must not be summed twice.
The square/reduction/residual/activation focused suite passes 17/17. This is a
subcounter only; the actual locked NumPy runtime/reduction kernel, linked
LAPACK path, frozen per-update masks and full branch bounds remain unresolved.
No profile, data, or model was run and no gate advanced.

### 2026-10-07 V2.12 replay-receipt-bound schedule preflight

Added a no-update seam that indexes receipts from a whole supplied train
episode collection and binds a manifest update to ordered replayed window
payloads, the paired model seed, and actual adapter-derived masks before the
six-arm call. The receipt index is built once, not by replaying the whole
collection per update. A separate builder validates a detached 20×87 manifest
snapshot once and freezes its nested rows; scheduled calls reuse that object
without rescanning the full manifest. The synthetic schedule test verifies
detachment and immutability. The snapshot type's public constructor now accepts
only a raw manifest and performs complete validation itself, preventing
caller-supplied digests/mutable rows from masquerading as validated. Five
receipt-bound tests cover the other components; the high-level coordination
fixture uses a structurally valid synthetic 20×87 schedule but mocks
row-to-receipt binding, mask extraction, and the paired-call helper, so it does
not prove an end-to-end data batch. A pre-model callback checks masks on the
one read-only materialized batch and rejects before any arm call; a new
scheduled-call test checks that failure behavior. This removes duplicate
adapter materialization,
while the callback adds one preflight and each arm still repeats its own.
The seam still allows direct `loss_grad` bypass. The focused episode/trajectory/
schedule/adapter/model suite passes 44/44 under Python 3.14.7/temporary NumPy
2.5.3, not the locked runtime; compile and whitespace checks pass. No research
data or compute was used. Next: independent review of the seam, then build a
true exclusive trainer boundary only after manifest/replay and compute
prerequisites are resolved. No gate advances.

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
expansion; current totals are 36,376–186,745 and 132–137.
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
audit tools. A material scope limitation remains: pair-only validity does not
model root-quality, state/prefix, or within-pair score-yield associations, so
the proposal is an abstract success-conditional structural proxy rather than
the actual first-passage root-state/score joint law. Reviewers must accept this
limited scope or request added dependence stresses before simulation. The
estimand, root schedule, yield contract, calibration requirement, tolerances,
and failure response remain open; v04 is current and no gate advanced. No
simulation, root, score, outcome, inference, or training occurred. See
`docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-07 root-quality/yield calibration stress addendum

Drafted a separate unapproved addendum that isolates within-policy-pair
root-quality selection using a slot-level shared latent factor, keeps marginal
validity at 0.40, and calibrates score means under the success-conditional
selected-root law. Four proposed P2 cells cover global null and +0.05
boundary alternatives under both signs of the quality/yield association. A
read-only review requested explicit independence assumptions and exact
assurance-helper arguments; both were added and the follow-up confirmed those
findings were resolved. The reviewer found the variance split, target law,
scenario counts, endpoints, workload and helper structure internally
consistent under the stated assumptions, without accepting the proposal.
For 63 endpoints, deterministic assurance is 0.794741 at R=18,000 and
0.805948 at R=18,200; 18,200 is only a candidate pending review of the 0.80
target and endpoint family. The pair-yield × root-quality interaction,
stress adequacy, and local feasibility remain open. No roots, data, scores,
outcomes, simulations, inference, or training were accessed/generated; v04
remains current and all gates stay closed. See the addendum and
`docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-07 deterministic root-quality proposal audit

Added a no-RNG audit for the proposed Simpson integration, validity
intercepts, selected-root ordinal targets, P2 covariance split, 120-row
manifest, and revised assurance family. Its seven focused fixture tests pass;
temporary outputs are under `/tmp`. The current runtime was Python 3.14.7,
unlike the Python 3.11.9 Windows runtime in the research lock; this is
recorded, not selected for calibration. Read-only source review found no
major math/scope issue and requested a dedicated intercept width tolerance.
The fix is applied and read-only follow-up confirmed it resolves the finding.
No simulation or roots were generated and no gate advanced.

### 2026-10-07 independent pre-fit action-sensitivity/regret review

An approved read-only review found the descriptive action-sensitivity and
executed-action regret definitions mostly coherent under their stated
assumptions, but did not freeze or adopt either protocol. Blocking items include
the absent trained six-arm graph/support implementation and unresolved
raw-state target contract; the accepted-root population, occupancy/seat
weighting, and yield/failure estimand; realistic all-legal-action expansion and
charged-work allocation; and the choice and identity of the exact or bounded
reference (including scalar versus interval regret). Terminal branch
denominators and operational occupancy strata also need definition. Preserve
the rollout's receipt-assigned policy-pair conditioning in interpretation.
No roots, outputs, scores, outcomes, simulations, inference, or training were
accessed or run. No gate advanced. See the two protocol drafts.

### 2026-10-07 action/regret aggregation crosswalk candidate

Added a conditional consistency proposal to both drafts: if development-root
schedule design 02 is accepted unchanged, use its three occupancy bands,
repeated slot IDs, equal within-band root weights, equal band and variant
weights, and global six-band under-yield stop; for regret, also average v04's
two seat assignments within each slot/model-seed cell. The action-sensitivity
ledger now separates planned branch cells, expected-terminal masks,
target-eligible cells, and completed predictions. A follow-up review found an
incomplete-prefix classification ambiguity; the draft now counts a pre-horizon
interruption without an observed terminal as target-eligible but incomplete,
and labels horizon error as conditional on exact nonterminal branches. These
clarifications do not accept the root schedule or resolve its independence/
yield assumptions, trainer graph, reference estimand, resource allocation, or
branch feasibility. No roots or model outputs were generated. No gate advanced.
An additional read-only follow-up confirmed this ledger and the conditional
crosswalk against schedule design 02 and METHOD_SPEC v04 by inspection. It
reaffirmed that schedule population/independence/yield choices, six-arm and
raw-state support, all-legal-action feasibility, and regret reference/budget/
evaluator/failure policy remain unresolved. No acceptance or freeze is
appropriate; no roots, scores, outcomes, simulations, inference, or training
were accessed or run.

### 2026-10-07 bounded-reference provenance/resource audit

Static source inspection found the bounded-reference helper validates the
shape of caller-supplied evaluator hashes but does not bind them to the
callable/configuration actually executed. Its hard cap counts transitions;
node count is telemetry and there is no internal wall/RSS bound. The rules
adapter implementation is not included in the current root fingerprint. A
protocol-level provenance/resource contract is recorded in the regret design
draft. An approved static review confirmed the source findings and the
proposed pre-freeze requirements. No evaluator, horizon, budget, or
terminal-root policy is selected. No roots or outputs were read or generated;
scoring and all downstream gates remain closed.
See `docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md` and
`two_player/v212_bounded_reference_v01.py`.

### 2026-10-07 action-sensitivity diagnostic protocol draft

Prepared a non-operative candidate protocol for one-step exact-successor
prediction error/action retrieval and multi-step open-loop latent prediction.
It separates transition-bearing arms from not-applicable arms, defines
per-arm action exposure and exact state-action support, excludes only
exact-tuple duplicate-successor pairs from retrieval, and distinguishes
expected terminal masks from missing outputs. Multi-step branches intervene
on each legal first action and reuse the root receipt's policy pair. The
approved static review found the support, collision, terminal-mask, and
intervention logic mostly coherent, while identifying remaining freeze
conditions. The current revision specifies separate marginal support strata,
paired eligible-row denominators, and branch-identity serialization; actual
six-arm graph and raw-state target/mask checks remain open. The all-legal
first-action expansion may still be infeasible; no cap, threshold, root
schedule, or estimator is selected. Independent graph/mask disposition and an
accepted root schedule are prerequisites for freeze; no roots, branches,
model outputs, or outcomes were generated, and no gate advanced.
See `docs/V212_ACTION_SENSITIVITY_DIAGNOSTIC_PROTOCOL_DRAFT_01.md`.

### 2026-10-07 pre-fit action-sensitivity and regret review

An approved independent reviewer reconsidered the six-arm v04 scope against
UWM-JEPA, ActSWM, and AD-WM and found retaining it defensible for the narrow
fixed contrast family, without adding an arm or certifying novelty. The
action-sensitivity diagnostic and reference-regret protocol remain unfrozen.
Resolve support buckets, latent metric/horizons, terminal/pass handling,
reference strata and identity, charged work/resource budgets, ties/order,
incomplete-cell behavior, and realistic feasibility before any fit. The
scalar and interval regret candidates are not interchangeable. No method,
arm, threshold, or solver was selected; no gate advanced. See
`docs/V212_ACTION_SENSITIVITY_CONTROL_DISPOSITION_DRAFT_01.md` and
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-07 root-sampling calibration-prerequisite review

An approved independent static review found the v05 first-valid-slot IID
argument coherent only under its stated slot assumptions and found the
seed × slot bootstrap structurally aligned with its estimand. Finite-sample
coverage/FWER are not established. The reviewer recommends design-matched
synthetic calibration before nomination, without treating that as a gate
decision. Freeze the estimand, situation-count interpretation, weights, RNG
and validity contract, global yield/pass-probability rule, calibration grid,
tolerances, outer/inner replication and uncertainty reporting, and failure
response before any simulation. No method version or gate changed; v04 remains
current and calibration/root generation remain unauthorized. See
`docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-07 synthetic calibration protocol proposal (draft 01; superseded)

Initial protocol draft 01 proposed design-matched synthetic calibration of
the v05 crossed bootstrap with ten atomic and five algebraically derived macro
contrasts, a 29-cell null/alternative and yield-stress grid, and
outer/inner-replication proposals. Its abstract contrast-level generator did
not enforce shared-arm/seat-swap dependence, as the approved reviewer noted.
The final draft-01 text added a dependence-robust union bound and reported a
5.22-billion-replicate workload, 53 endpoints, and 0.8439 boundary assurance.
Draft 01 is retained as superseded history, not the current calibration
proposal. Draft 02 replaces it with shared-arm ordinal outcomes, 31 cells, 57
endpoints, 5.58 billion inner replicates, and 0.8322 assurance; those numbers
are the current proposal and remain unapproved. No simulations, roots, scores,
or outcomes were accessed or generated. v04 remains current; calibration,
root generation, and downstream gates remain closed. See
`docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_01.md`,
`docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_02.md`, and
`docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-07 shared-arm calibration DGP proposal

Protocol draft 02 replaces contrast-level copula outcomes with a shared-arm
ordinal match-score generator. Candidate and control arm effects are reused
across their related contrasts; seat advantage changes sign across the two
assignments; wins/draws/losses yield the discrete paired-score support; and
macro contrasts are computed from the atomic contrasts. A scalar normal-CDF
equation calibrates declared matchup means while preserving the partial-null
scenario grid. This remains an unapproved synthetic model, not a game
simulator or evidence of performance. The DGP covariance, seat-pair law,
calibration equation, exact marginal target, and the 18,000 × 10,000 workload
need read-only statistical review before any run. v04 remains current; all
root, simulation, and downstream gates remain closed. See
`docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_02.md`.

### 2026-10-07 calibration profile coverage revision

After the approved static review identified missing seed-dominant,
slot-dominant, and heteroskedastic stress coverage, protocol draft 02 now has
five profiles: seed-dominant, slot-dominant, balanced, seed×slot-interaction
dominant, and combined band/arm heteroskedastic. The five global-null cells
cover each profile; the remaining principal IDs use a frozen round-robin map,
and the two yield cells explicitly inherit P5 and P1. `A-HETERO` adds
low/middle/high occupancy-band mean offsets. The grid now contains 25 null and
four alternative principal cells plus two yield stresses (31 total), with 57
Monte Carlo acceptance endpoints. At R=18,000 the analytic union-bound
assurance is 0.8322 and workload is 5.58 billion inner bootstrap replicates
(up to 83.7 billion contrast evaluations). These are design calculations,
not simulation results; an independent reviewer is checking the revision.
No simulation, root, score, or outcome was generated/accessed; v04 remains
current and all research gates remain closed.

### 2026-10-07 shared-seed and alternative-coverage correction

The reviewer found that P5's band-varying seed variance needed an explicit
shared-seed construction and that P5 did not yet appear under an alternative.
Draft 02 now transforms one standardized latent seed per seed through
band-specific covariance factors and specifies the induced cross-band
covariance; `A-HETERO` maps to P5. P4 is explicitly limited to null-pattern
coverage in this finite grid. The K=57 binomial-tail calculation was
rechecked at alpha `0.05/57`; unrounded union-bound assurance at R=18,000 is
0.8321582599. The second read-only review confirmed these fixes and found no
remaining inconsistency in the edits, but did not accept the overall protocol
or independently recompute the binomial tails. Calibration and all downstream
gates remain closed.

### 2026-10-07 calibration assurance arithmetic reproduction

Added `tools/v212_calibration_assurance.py` to reproduce the proposed K=57
Bonferroni Clopper–Pearson assurance with downward recurrence, log-PMF
summation, and 60-digit Decimal tails. It only computes binomial probabilities;
no synthetic dataset is generated. It confirms cutoff 981 at R=18,000,
individual boundary pass assurance 0.9970554080891540, and dependence-robust
union lower bound 0.8321582610817799. At R=6,000, cutoff 303 gives individual
assurance 0.5854327569152956 and no useful joint bound. This corrects about
1e-11 numerical drift in the earlier double-only values. The calibration
protocol remains unapproved; the calculation opens no gate.

The analytic-audit tree was published as remote commit
`d59c4d8d0c46318d230da3bd29f55502e1d6f571` from expected parent
`dd68156365a66ee84b75c5b52efff92b3ddb40ee` using a non-force API ref update;
GitHub compare verified `main` advanced by one commit and the remote tree
matched local. SSH/HTTPS Git transport was unavailable, so the local
`origin/main` tracking ref is still stale pending a later fetch. No generated
simulation artifacts were published.

### 2026-10-07 schema proposal bounded stream reader

Added an audit-only fd reader to the unreviewed response/request schema
proposal helper. The focused suite passes 17/17; pipe fixtures exercise empty,
exact 811/747-byte caps, cap-plus-one rejection, short reads, and invalid
bounds. The helper retains at most `cap+1` bytes. It has no caller deadline and
is not wired to the worker bootstrap, request controller, or receipt publisher.
RESP-01b and schema review remain partial; no gate advanced. See the schema
proposal and failure-test traceability.

### 2026-10-07 raw-state control wiring proposal

Converted the architecture audit into a reviewable clarification proposal:
reuse the shared 104-to-32 action-conditioned latent predictor in the
raw-state control, decode its latent output to 198 exact-state features, and
re-encode for recurrence. The decoder output is linear because exact feature
targets include 0/1 channels under MSE; the random-weight pilot's `tanh`
decoder is not an equivalent training path. The proposal fixes wiring at
18,440 online parameters while retaining the required 5% training-FLOP gate.
It was later adopted narrowly in v05; it does not resolve compute feasibility.
V04 is preserved unchanged, and no trainer or model operation was run. See
the amendment and architecture reconciliation.

### 2026-10-07 v04 arm architecture and compute reconciliation

A static comparison found that the raw-state control description leaves its
predictor/decoder wiring ambiguous. The random-weight pilot implements a
direct 104-to-198 feature decoder and allocates an unused latent predictor;
the spec can also be read as a 104-to-32 latent predictor followed by a
32-to-198 decoder. These imply 29,336 versus 18,440 online parameters under
the specified widths. The trainer is absent, so the required all-arm 5% FLOP
parity has not been demonstrated. Freeze the intended wiring in a reviewed
method amendment before using the pilot as an arm-level compute proxy or
implementing the trainer. This does not establish the panel is unfair or
infeasible; no model operation ran and no method/gate changed. See the arm
reconciliation draft.

### 2026-10-07 root-schedule yield sensitivity

Added an exact Binomial-tail sensitivity for the proposed six-stratum schedule
(64 slots, at least 16 valid per stratum). Under equal assumed slot-yield and
independence, the all-six schedule passes with probability 36.1% at `p=0.30`,
82.1% at `p=0.35`, and 97.6% at `p=0.40`; illustrative 90/95/99% schedule
targets imply equal per-slot yields of about 0.366/0.383/0.418. This is
analytic sensitivity, not an estimate of any game-policy stratum's yield.
No reliability threshold was selected. The root schedule, yield model,
bootstrap calibration, and method amendment remain unapproved; no roots or
scores were generated. See the sensitivity note and root-sampling review.

### 2026-10-07 request/response schema proposal parser audit

Reviewed the unintegrated, unreviewed v02 closed-schema validator against its
proposal and ran its focused standard-library suite: 17/17 pass. The fixtures
cover canonical encoding, duplicate keys, invalid encodings, field bounds,
request binding, exact 811/747-byte witnesses, and isolated stream caps. No concrete validator
defect was found in this bounded offline audit. This does not independently
approve the schema or byte caps: worker/caller integration of stream boundaries,
request-controller and receipt integration, resource-profile reconciliation,
runtime attestation, and independent design review remain open. No service,
inference, OOM, training, generation, scoring, or match ran; no gate advanced.
See the schema proposal and RESP-01b in the failure test plan.

### 2026-10-07 request watchdog boundary checks

Five isolated request-adapter tests pass using the existing NumPy 2.5.3
package under `/tmp` without changing project dependencies. An AST audit
resolved all 52 fully qualified references in the failure plan. The tests cover
temporary cgroup-bound parsing, mocked startup-deadline fallback, local child
kill/reap, mocked cgroup-inheritance preflight, and mocked post-worker audit
delay. The random-weight search path was not run. These checks verify helper
behavior only; systemd integration, cgroup-attributed kill/reap, runtime
attestation, and operational headroom remain open. See Ground Truth and the
failure plan.

### 2026-10-07 post-stop manager-query failure coverage

Added a mocked armed-smoke controller case where the stop command succeeds
but the post-stop manager query fails. It preserves the already-durable
receipt and IPC workspace and reports unit state as retained/unknown with the
known invocation and worker-cgroup identifiers. The focused armed-service-
smoke module passes 40/40. This covers one REC-01 seam only; kill/reap
attribution, live recovery, and v02 integration remain open. No live service
or model operation ran. See the failure matrix and test plan.

### 2026-10-07 request-failure traceability update

Reconciled the failure-test plan's REQ-01a/REQ-01b rows with the existing
v02 raw-stdin and exact-request release-digest tests. A read-only AST audit
resolved all 49 fully qualified test references; none were missing. The
disposition remains partial because these helper tests do not establish
controller/runtime integration or complete failure behavior. No tests or
runtime work were needed for this documentation change, and no gate advanced.
See `docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md` and Ground Truth.

### 2026-10-07 v02 worker-helper regression

Re-ran the bounded v02 raw-stdin bootstrap, armed protocol/release-binding,
and worker IPC suites: 49/49 pass under `unittest` on the current checkout.
This verifies the isolated synthetic helpers only; systemd/controller
integration, executed-runtime attestation, and service gates remain open. No
data, inference, OOM, training, score, or match operation ran. See Ground
Truth and the request-adapter integration design.

### 2026-10-07 independent V03 and generation-protocol review

An independent read-only static review found no basis for a safe offline
production-code change. V03 remains a candidate and is not cleared for runtime:
sampled RSS is cooperative, while hard worker memory enforcement,
caller-observed deadlines, runtime attestation, and integrated
supervision/receipt evidence remain prerequisites. Do not implement the
production generator until a reviewed protocol freezes split matrix/quotas,
RNG and policy-stream semantics, the 928-window/minibatch contract,
lineage/overlap identities, and atomic artifact/receipt behavior. The
held-out-root yield rule and finite-sample calibration remain unresolved, so
v04 stays current. No tests or runtime/research operations ran; no code changed
and no gate advanced. See Ground Truth and the V03, generation-protocol, and
root-sampling review documents.

### 2026-10-07 post-exit boot identity revalidation

The v01 armed-smoke controller rereads the host boot ID after a successful
post-exit manager snapshot and before reading the worker response. If the
source is unavailable or the ID differs from the pre-dispatch value, it fails
closed without response/journal/receipt/stop and retains the dispatched
workspace. A two-case mocked regression passes. This is MGR-01 controller-seam
coverage, not live manager/reboot evidence; the v02 controller and full manager
failure map remain open. No service or model operation ran. See the failure
plan and matrix.

### 2026-10-07 post-dispatch request mutation rejection

The mocked v01 controller now changes the request at its final caller-side
identity/hash check, once with same-length byte mutation and once with a
request-path symlink substitution. Both cases reject before receipt
publication or unit stop and retain the IPC workspace. This adds controller-
flow evidence to REC-02; post-receipt recovery and v02 integration remain open.
No service or model operation ran. See the failure plan and matrix.

### 2026-10-07 isolated Python startup in armed-worker candidates

The v01 service-smoke worker command and the offline v02 raw-stdin bootstrap
candidate now require `-I -S -B -c`, and each bootstrap checks the exact option
sequence before accepting its self-hash at the adjusted `/proc/self/cmdline`
position. Synthetic/mock bootstrap and orchestration tests pass 54/54. This
removes environment and `site` startup hooks for these candidate invocations;
it does not attest the Python executable, loader, native libraries, or mapped
runtime bytes. No service/systemd smoke was run. The authenticated immutable
runtime contract, independent review, and adapter integration remain open; no
gate advanced. See `docs/V212_EXECUTED_RUNTIME_ATTESTATION_RESEARCH_01.md`.

### 2026-10-07 pre-release cgroup gate failure cases

The armed-smoke orchestration test now injects three GATE-01b failures at the
pre-release seam: worker `/proc/<pid>/cgroup` mismatch, caller/worker cgroup
sharing, and live `memory.max` disagreement. Each prevents counter reads and
release, leaves the receipt absent, and retains the dispatched unit/workspace.
The focused armed-smoke/collector/live-evidence/receipt group passes 97/97;
compileall and `git diff --check` pass. The failure-test AST audit resolves all
46 fully qualified references. These are mocked identities/limits,
not host-service evidence; the v02 controller and live placement remain open.
No service, inference, OOM, training, score, or match ran. See GATE-01b.

### 2026-10-07 failure-test traceability reconciliation

The JRN-01/JRN-02 coverage map now names the armed-smoke empty, duplicate, and
foreign-invocation marker injection test. An AST audit resolved all 45
fully-qualified test references in the plan to existing test methods; none
were missing. This validates reference integrity only, not assertion coverage,
live behavior, or an open gate. No code/test behavior, service, inference,
OOM, training, score, or match changed. See the test plan's traceability
section.

### 2026-10-07 counter-file disappearance between controller samples

The armed-smoke test now drives the actual bounded `memory.events.local`
reader against a temporary cgroup-shaped tree, removes the file after the first
sample, and verifies the second read fails closed through the mocked controller.
No receipt is written, the unit is not stopped, and the IPC workspace remains.
The focused armed-smoke/collector/live-evidence/receipt group passes 96/96;
compileall and `git diff --check` pass. This does not establish live cgroup or
service behavior; amended v03 receipt integration remains open. No inference,
OOM, training, score, or match ran. See CNT-01a.

### 2026-10-07 counter evidence rejection at the armed-smoke receipt boundary

The armed-smoke mock can now mutate worker-local counter snapshots at the
collector seam. A table-driven case injects wrong source/schema/cgroup/boot,
out-of-window and unordered timestamps, a Boolean count, and counter rollback.
Each case reaches receipt assembly, rejects before persistence or unit stop,
and retains the IPC workspace. The focused armed-smoke/collector/live-evidence/
receipt group passes 95/95; compileall and `git diff --check` pass. This remains
mock evidence: live filesystem disappearance between samples, the amended
v03 receipt controller, and service behavior are not covered. No inference,
OOM, training, score, or match ran. See CNT-02 in the failure plan and matrix.

### 2026-10-07 deadline check after post-exit manager snapshot

The v01 armed-smoke controller now checks the caller deadline after validating
the post-exit unit/invocation/boot/cgroup snapshot and before reading response
bytes. A controlled mock expiry at this seam blocks response and journal reads,
receipt persistence, unit stop, and workspace cleanup while retaining the
workspace. The focused armed-smoke/collector/live-evidence/receipt group passes
94/94. This is mock evidence for one additional CLK-01 boundary; remaining
evidence crossings and v02 integration remain open. No service, inference, OOM,
training, score, or match ran; no gate changed. See CLK-01 in the failure test
plan.

### 2026-10-06 deadline check after journal capture

The v01 armed-smoke controller now checks the caller deadline immediately
after the journal query and before receipt assembly. A controlled mock expiry
at that seam proves receipt assembly/publication, unit stop, and workspace
cleanup are skipped while the workspace is retained. The focused
armed-smoke/collector/live-evidence/receipt group passes 93/93. This adds one
mocked evidence boundary; other evidence operations and the v02 controller
remain open. No service, inference, OOM, training, score, or match ran; no gate
changed. See CLK-01 in the failure test plan.

### 2026-10-06 empty journal collection at the consumer boundary

Extended the mocked armed-smoke marker injection to include an empty record
collection alongside the duplicate and foreign-invocation cases. All three
fail before receipt persistence or unit stop and retain the workspace. The
focused armed-smoke/collector/live-evidence/receipt group passes 92/92. This
does not replace collector parser coverage or establish live journal behavior;
amended-controller receipt mapping remains open. No service, inference, OOM,
training, score, or match ran; no gate changed. See JRN-01/JRN-02 in the
supervision failure plan and matrix.

### 2026-10-06 duplicate and foreign journal-marker orchestration cases

The armed-smoke mock now injects duplicate marker records and a marker whose
message names a different invocation. Both cases reject at the controller
consumer boundary before receipt persistence or unit stop, and retain the IPC
workspace. The focused armed-smoke/collector/live-evidence/receipt group passes
92/92. These remain synthetic mock cases: they do not verify live journal
behavior or the amended controller/receipt path. No service, inference, OOM,
training, score, or match ran; no gate changed. See JRN-02 in the supervision
failure test plan.

### 2026-10-06 deadline checks after response and counter evidence

The v01 no-inference smoke checks the caller deadline after bounded response
read/parse and after each local counter snapshot. Controlled expiry after the
response blocks journal collection; after the first counter it blocks release;
after the second it blocks exit polling. All retain the workspace and skip
receipt publication/unit stop. The focused armed-smoke/collector/live-evidence/
receipt group passes 91/91. Other evidence-operation boundaries and the v02
controller remain open. No live service, inference, OOM, training, score, or
match ran; no gate changed. See CLK-01 in the supervision failure plan.

### 2026-10-06 raw response validation in the schema proposal audit

The offline v02 proposal auditor now validates a bounded canonical response
buffer, checks the closed schema and request-bound fields, and returns the
validated object with schema, SHA-256, and byte-length metadata derived from
that exact buffer. Maximum-size success, metadata values, non-canonical bytes,
and cap-plus-one failure are covered. The focused IPC/schema/smoke/receipt/
bootstrap group passes 139/139. This helper does not publish receipts or
integrate a worker/controller response boundary; independent review and full
failure mapping remain ahead of integration. No gate changed. See the
request-adapter design and RESP-01b traceability.

### 2026-10-06 exact bounded response-byte reader

The IPC helper now returns the exact bounded response bytes after its existing
path/inode/owner/race checks. A separate parser accepts that same byte buffer,
and the legacy object-returning helper composes the two without changing its
API. Tests show that the digest of received wire bytes differs from the digest
of parsed-and-reserialized JSON when whitespace is present, while size limits
remain enforced. The focused IPC/schema/smoke/receipt/bootstrap group passes
137/137. This does not yet validate the v02 response schema or bind exact
response digest and length into a receipt. No runtime or research gate changed.
See the request-adapter integration design and failure plan.

### 2026-10-06 post-exit manager identity before response read

The existing v01 no-inference smoke now binds the post-exit manager snapshot
back to the active unit, invocation, boot, and any retained cgroup path before
reading response bytes. Table-driven mocked cases reject foreign invocation
or cgroup identity and missing/malformed invocation, `Result`, or
`ExecMainStatus`; they preserve the workspace and skip response acceptance,
receipt publication, and unit stop. The focused armed-smoke/collector/live-
evidence/receipt group passes 89/89. This does not test live failures, boot-
source loss, or the v02 controller and does not complete the failure matrix.
Runtime attestation and independent review remain open. No service, inference,
OOM, training, score, or match ran; no gate changed. See the request-adapter
integration design and supervision failure plan.

### 2026-10-06 canonical request bytes at the v02 bootstrap boundary

The separate v02 bootstrap re-encodes the parsed bounded stdin request using
the pinned sorted-key/compact UTF-8 JSON form and byte-compares it before
opening project helper files. Offline subprocess fixtures reject trailing
whitespace, a leading newline, reordered keys, and a non-canonical request at
the exact byte cap; canonical source-verified release-to-response still
passes. The focused bootstrap/protocol/release-token/IPC/service-smoke/receipt
group passes 139/139. This does not wire v02 into systemd or the adapter and
does not establish caller deadlines, executed runtime identity, complete
failure mapping, or independent review. No live service, request, inference,
OOM, training, score, or match ran; no gate changed. See the integration design
and supervision failure plan.

### 2026-10-06 strict journal evidence parsing

The collector now rejects duplicate JSON keys at every nesting level and
non-standard JSON constants in journal records. Its fixtures cover partial
final records, malformed JSON, invalid UTF-8, non-object records, duplicate
keys, and `NaN`; the existing exact-one-marker and trusted unit/invocation/
cgroup checks remain in place. The collector plus receipt-assembler suites
pass 48/48; logs are under
`/tmp/caissa-v212-journal-strict-tests-20261006.{log,pid}`. These are parser,
assembler, and mocked no-inference checks only. Live journal failure evidence
and the integrated request-controller action/receipt/handle matrix remain
open. No service, request, inference, OOM, training, score, or match ran; no
gate changed. See `docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`.

### 2026-10-06 nonblocking cgroup-counter evidence reads

The live-evidence reader now opens `memory.events.local` with `O_NONBLOCK` and
`O_NOCTTY` before checking that the descriptor is a regular file. This closes
a FIFO-substitution hang between the path check and post-open type check.
Regression fixtures cover that FIFO case plus malformed/duplicate rows,
non-ASCII bytes, negative and overflowing counts, and oversized input. The
focused live-evidence and mocked collector suites pass 32/32; run evidence is
under `/tmp/caissa-v212-counter-failure-tests-20261006.{log,pid}`. This does not
prove the counter path cannot disappear between real service samples or
integrate mandatory counter pairs into an accepted request receipt. No live
service, cgroup, OOM operation, request, inference, training, score, or match
ran, and no gate changed. See the failure test plan.

### 2026-10-06 counterfactual-action JEPA literature refresh

A targeted primary-source refresh examined UWM-JEPA and Flow-JEPA. UWM-JEPA
reports a controlled hidden-velocity result where teacher-forced targets permit
an action-insensitive predictor, while simulator-generated counterfactual
targets restore action-perturbation sensitivity. This does not establish that
V2.12 is insensitive: the paper uses partial observations and a different
latent geometry, and does not demonstrate competitive adversarial planning.
It does make action use an empirical question even when an action is an
explicit predictor input. Flow-JEPA independently establishes conditional
flow-matching over multi-step latent trajectories in continuous control, not
exact-rule board-game search. Both results are author-reported and were not
reproduced. The current v04 trains along recorded policy-mixture branches;
counterfactual-target training would be a new data intervention and method
version, not a silent edit to one arm. The prior conditional six-arm review
does not cite UWM-JEPA, so its scope exclusion needs explicit reviewer
reconsideration before fit. No code/data was downloaded, no arm or gate
changed, and no root, model, score or outcome was run. See
`docs/RELATED_WORK.md` and
`docs/V212_ACTION_SENSITIVITY_CONTROL_DISPOSITION_DRAFT_01.md`.

### 2026-10-06 compute/resource profile reconciliation

A static source audit corrected the request-schema bound audit: the unintegrated
`v212_request_adapter_v02` defaults to 10,000 nodes, a 5-second planner
deadline, a 6-second response deadline, and 1.5 GiB RSS/expected cgroup memory;
the separate `v212_pilot` defaults to 500,000 nodes, 8 seconds, and 1.5 GiB
RSS. The armed synthetic supervision fixture specifies 128 MiB `MemoryMax`,
96 MiB `MemoryHigh`, zero swap, and an 8-second `RuntimeMaxUSec`. These
profiles do not compose as written: the adapter expects 12 times the smoke
fixture's memory limit, and its node cap is 50 times below the provisional v04
method cap. The adapter's response deadline is caller-observed and is not
replaced by the service runtime limit. The previously measured rule-only
Reversi8 p90 of 6.037 seconds against the v04 2-second target remains a failed
negative result. No profile or cap was selected, and no request, root, model,
service, inference, training, score, or match ran. No gate changed. A future
versioned protocol must reconcile the estimand, common root schedule, all-arm
resource limits, and separate setup/search/response/receipt costs before
service or pilot work. See
`docs/V212_REQUEST_SCHEMA_BOUND_AUDIT_DRAFT_01.md`.

### 2026-10-06 armed-bootstrap release and manifest boundary tests

Added offline subprocess fixtures for a valid exact-byte release-to-response
round trip and rejection of an altered request against the original token.
Additional negative cases reject wrong schema, extra request fields,
non-finite JSON, unexpected helper paths, a bad manifest digest, changed helper
bytes, and a symlink escape. Source loading now opens the fixed project/package
directories without following symlinks, reads each helper through its pinned
descriptor with nonblocking file opens, and enforces a 256 KiB per-file cap.
Tests cover exact-limit helper acceptance, an oversized helper, a substituted
FIFO without blocking, and source changes after manifest creation. The test uses temporary
cgroup and source-tree fixtures and suppresses the journal marker; it does not
create a systemd unit. The focused bootstrap suite passes 16/16, and the
combined protocol/IPC/supervision regression group passes 121/121. Canonical
request encoding enforcement, controller and receipt integration, actual
runtime identity, full failure mapping, and independent review remain open. No
live service, inference, OOM, training, score, or match ran; no gate changed.
Next, resolve the runtime fingerprint contract and obtain the required
architecture review before connecting the candidate to systemd or the adapter.
See
`docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md` and the failure test plan.

### 2026-10-06 incremental single-PV bound-allocation follow-up

Added a second synthetic interval-search schedule with cached frontier counts
and ancestor-only bound backups after the first principal-variation attempt
showed high control overhead. Across six single-run comparisons at 4,096,
16,384, and 65,536 transitions on the same two opening states, no root/action
interval narrowed. The schedule improved wall time over DFS for these
Connect Four openings but was substantially slower on Reversi6 (18.735 s vs
4.861 s at 65,536). This remains a custom, unselected allocation policy; the
result neither validates nor refutes published FSSS-Minimax, and does not
justify cap changes. Sixteen tiny/oracle-focused tests pass. Details and raw
receipt hash: `docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-06 bound-critical interval-search probe

An isolated principal-variation schedule alternated lower/upper critical paths
for root value and executed-action regret. Tiny-game exhaustive checks pass,
including forced Reversi pass accounting and every integer budget prefix on a
small Tic-Tac-Toe state. A source-hashed, same-cap comparison on one opening
state per game found no interval narrowing at 4,096 transitions for this
schedule, transition-DFS, or root-balanced DFS. Single-run PV times were 4.038 s
for Connect Four 6x7 and 7.142 s for Reversi6, several times slower than either
DFS candidate. A one-off Connect Four 16,384-transition PV run took 80.348 s
with no narrowing and was stopped before larger-cap or second-game measurements.
This schedule is not adopted and does not refute published FSSS-Minimax; no
model cap, root schedule, or gate changed. See the bound-critical probe in
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-04 interval-valued minimax reference option

Deep search identified a possible alternative to choosing an arbitrary scalar
leaf evaluator: give unexpanded nonterminal leaves the valid W/D/L interval
[-1,+1] and propagate lower/upper values by MAX/MIN. For every legal root
action this yields a sound interval containing the full-game minimax value;
combining the root-optimum and executed-action intervals yields a conservative
decision-regret interval. A zero-width interval identifies a point value;
otherwise the width must remain visible. This avoids direct reuse of the
synthetic-data heuristic but may be too wide under practical compute limits.
Independent review found no blocker in the derivation under a full-successor
accounting invariant: enumerate every legal child or retain omitted actions
as unresolved intervals; forced passes count as transitions. The general
algorithm precedent does not establish CAISSA correctness or feasibility. An
isolated deterministic-DFS candidate and focused tiny-game tests now validate
containment across every expansion-budget prefix for one late Tic-Tac-Toe
fixture, plus forced-pass handling and unresolved root actions. Independent
code review confirmed the recurrence and prompted stricter action-ID validation.
Follow-up hard-transition-cap variants enforce complete root enumeration and
atomic successor expansion. On one standard opening state per intended game,
root-balanced DFS still left all root/action intervals at full width 2 through
65,536 transitions (single-run 11.345 s Connect Four 6x7; 4.107 s Reversi6).
This negative result argues against adopting the naive DFS orders but is not
representative cap evidence. The interval option remains a candidate, not an
accepted or frozen method; no benchmark roots, models, scores, or gates changed.
See `docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-04 decision-regret source-code audit

The legacy V2.8 line heuristic is used to generate positional policy choices
and as the bounded-search policy's leaf evaluator, so reusing it as the
decision-regret reference could favor trajectories from those policies.
Separately, primary executed-action regret can be calculated from a complete
bounded-reference root maximum and independent full-window reference values
for each arm's executed action; exact values for every legal action are needed
only for an optional action-ranking table. This could reduce redundant oracle
work without reducing the root schedule or weakening the selected-action
value check. The reviewer found no blocker in the draft amendment. It remains
unfrozen: choose an evaluator/depth and query budget and verify alpha-beta
exactness and adapter semantics against tiny exhaustive fixtures before
scoring. No root, model, score, or outcome was accessed; no gate changed. See
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-04 Reversi6 exact-reference source lead

A primary-source search found Takizawa's 6x6 Othello semi-strong solution
artifact. It supports exact values only on certified regions `R_P`; it is not
a strong oracle for all policy-mixture roots. For roots verified in the same
orientation-specific region where the side to move is the free player, the
definition covers every legal successor and could support complete action-
level W/D/L values. Union-only `R` membership is insufficient; every child
query must also be verified. The paper's score-margin value
maps to CAISSA winner/draw utility by monotone sign, a derivation that still
needs adapter verification. The Zenodo release is 138.4 GB and has no license
value in the inspected rights metadata, so it was not downloaded. This is a
potential exact stratum only; bounded references remain unresolved for other
variants and uncertified roots. No roots/models/scores were inspected and no
gate changed. Independent static review confirmed the scope and orientation
conditions; the artifact remains unadopted. See the source analysis in
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-04 action-sensitivity control disposition draft

Primary-source comparison confirms a real v04 risk: action input does not
guarantee useful action sensitivity, and recorded-branch latent targets do
not cover every legal counterfactual branch. ActSWM and AD-WM establish
relevant action-sensitive objectives and candidate-selection diagnostics, but
do not provide a ready-made matched control for deterministic alternating
zero-sum board search. Draft 01 recommends preserving the six frozen v04 arms
only for their narrow contrast family; the independent reviewer accepted this
conditional scope exclusion with no P1/P2 blocker. A broader method comparison
needs its own versioned benchmark. It also proposes full legal-root action
scoring and decision-regret measurement, with latent separation alone
insufficient. This does not amend v04 or open fit: the regret protocol is
unfrozen and the Reversi8 2-second p90 gate remains failed. No code, roots,
data, models, inference, or outcomes were run. See
`docs/V212_ACTION_SENSITIVITY_CONTROL_DISPOSITION_DRAFT_01.md`.

### 2026-10-04 D-JEPA control-scope assessment

A static comparison of v04’s six arms with D-JEPA/ARC-Bench recommends keeping the frozen panel unchanged for its prespecified candidate-versus-control contrast family around the multi-step JEPA candidate, inside the specified exact-rule max/min planner. Adding one outcome-supervised candidate ranker would not change those existing contrasts, but would add a distinct, unmatched benchmark comparison, compute, and multiplicity; adding it across all arms would be a new factorial study. This recommendation is not independent review approval. Before any corpus generation or fit, an independent reviewer must accept the scope rationale and resolve the still-draft support/regret protocol; the failed Reversi8 2-second p90 compute gate also remains open. Do not claim general decision-alignment superiority. See `docs/V212_DECISION_ALIGNMENT_CONTROL_REVIEW_DRAFT_01.md`.

### 2026-10-04 decision-alignment prior-art refresh

A targeted primary-source pass found ARC-Bench (fixed-candidate JEPA rankability with regret/ranking metrics) and D-JEPA (outcome-supervised relational selection among shared predicted-future candidates). These preprints make generic candidate-ranking diagnostics and JEPA-informed decision alignment poor novelty claims. Their reported domains are navigation/manipulation/robotics, not exact-rule alternating zero-sum board search; no CAISSA result follows. Before any corpus generation or fit, review whether the frozen six-arm v04 panel needs an outcome-supervised candidate-set control to isolate the recursive JEPA transition term, or record why the estimand excludes it. Do not add a loss/arm to v04 silently. The D-JEPA code repo states Apache-2.0, but its checkpoint card leaves upstream redistribution/license checks open and its linked dataset card was empty/unlicensed in this snapshot; no artifacts were downloaded or reused. No gate changed. See the targeted section in `docs/RELATED_WORK.md`; the full search snapshot remains in `docs/V212_RELATED_WORK_POSITIONING_AUDIT_01.md`.

### 2026-10-04 request/runtime binding and related-work audit

Published the supervision architecture audit and drafted a new versioned request/runtime-binding contract: hash the exact bounded request bytes the worker reads, bind that digest into release/response/receipt, and attest project code from verified bytes or immutable artifacts while recording interpreter, systemd, and native runtime identities. Independent review found no P1/P2 issue; canonical JSON rules and a mapped-native-binary check were added, with host support for `/proc/map_files` still open. A sourced first-pass related-work audit found strong overlap with V-JEPA 2-AC, JEPA-WM/physical-planning studies, value/plan-aware objectives, action-conditioned JEPA theory, and multi-step action-sensitive JEPA work. ConnectX and LAMIR establish learned latent game planning and two-player zero-sum look-ahead; JEPA Arcade describes a non-peer-reviewed two-player Atari pipeline. Broad “first JEPA game planner/agent” claims are unsupported. The key design gap is that v04 trains on recorded actions but plans over alternative legal branches; decide before fitting whether to add an action-sensitive control and diagnostics that score every legal root action against a bounded exact-search reference. Keep novelty clearance, adapter, inference, training, pilot, and OOM gates closed. Next: finish source/citation chasing and exact-method comparison, decide any method-spec changes under independent review, and complete the manager/journal/counter failure matrix. See `docs/V212_REQUEST_RUNTIME_BINDING_AMENDMENT_DRAFT_01.md`, `docs/V212_RELATED_WORK_POSITIONING_AUDIT_01.md`, `docs/V212_SUPERVISION_ARCHITECTURE_AUDIT_01.md`, and the detailed `docs/RELATED_WORK.md` ledger.

### 2026-10-04 request/runtime amendment review follow-up

The focused reviewer confirmed four added requirements: Python interpreter
executed-byte identity must remain unverified absent an immutable/equivalent
execution proof; canonical JSON must reject non-string keys recursively;
response receipts must bind the exact bounded bytes read, byte length, and
schema; and amended-schema tests must integrate manager/journal/counter failure
and reconciliation cases. The reviewer also identified ambiguity in whether
request canonicalization rules apply to responses. The draft now explicitly
applies the same encoding, allowed value types, int64 bounds, key and
duplicate-key checks, and canonical re-encoding to response bytes, with a
versioned response schema and explicit size limit. The reviewer confirmed this
closes the ambiguity. This remains documentation only; no implementation,
adapter, inference, pilot, training, or OOM operation ran. See
`docs/V212_REQUEST_RUNTIME_BINDING_AMENDMENT_DRAFT_01.md`.

### 2026-10-04 supervision failure matrix and counter requirement

Read the armed collector and receipt assembler against the outstanding
manager/journal/counter failure map and drafted
`docs/V212_SUPERVISION_FAILURE_MATRIX_DRAFT_01.md`. It pairs each failure with
the required action disposition, receipt certainty, retained lifecycle handles
and minimum test assertion. The code review surfaced a concrete schema gap:
the legacy receipt assembler permits both worker-local counter snapshots to be
omitted, although the collector currently captures both. An amended accepted-
receipt path must require the pair; do not silently change the legacy helper.
The reviewer requested explicit pre-release rows for request/release binding
and the resource/placement gate, corrected the counter sampling wording to
reflect two in-run worker samples, and added a separate post-exit response
validation row for malformed or mismatched bytes. The reviewer confirmed the
revised matrix. It remains a design inventory, not evidence of live recovery
or adapter readiness. No service, adapter, inference, OOM operation, training,
or outcome ran. Next: version an integrated regression plan and resolve
immutable runtime identity and bounded IPC details. A case-by-case draft now
exists in `docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`; it maps each
matrix row to a fault seam, fail-closed assertions and current coverage, and
has independent design review. The reviewer confirmed Boolean/rollback
counter tests already exist in the legacy suite; the amended schema must carry
them forward. No live service, adapter, inference or OOM operation is in scope. See
`docs/V212_SUPERVISION_FAILURE_MATRIX_DRAFT_01.md` and
`docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.


### 2026-10-06 bounded raw-stdin helper for request-byte v02

Added an isolated helper that reads worker stdin through EOF while retaining no
more than the existing 65,536-byte IPC cap plus one probe byte, then forwards
the exact bytes into the v02 request digest/parser/release path. Focused tests
cover short EOF, exact and over-cap streams, invalid bounds, and invalid
UTF-8 and truncated-JSON rejection before release or callback; all ten v02
protocol tests pass.
This does not integrate a bootstrap, set the proposed 811-byte schema cap, or
close runtime identity, receipt, failure-map, or independent-review gaps. A
non-terminating stream still depends on the outer caller deadline. No service,
request adapter, inference, OOM, training, score, or match ran; all related
gates remain closed. See `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.


### 2026-10-06 v03 counter-validation regressions

The isolated v03 receipt boundary now has fixture regressions for counter
rollback, Boolean, negative, non-integer, and missing-key values, carried
forward from v02 while both snapshots are mandatory. The combined v02/v03
receipt suites pass 31/31. This does not establish a live counter capture path
or the controller-level no-action/no-receipt/retained-handle invariants; those
integration cases and independent review remain open. No service, OOM test,
request, inference, training, score, or match ran, and no gate changed. See
`tests/test_v212_supervision_receipt_v03.py` and
`docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`.


### 2026-10-06 request-byte v02 worker bootstrap candidate

A separate source builder now generates a no-inference worker bootstrap that
reads raw stdin under the existing IPC hard limit before opening project
files, validates JSON framing/duplicate keys, checks its bootstrap and five
helper hashes, compiles the verified helper bytes in dependency order, and
passes the exact original request bytes to the v02 release verifier. Seven
static/subprocess tests cover ordering, manifest membership, empty and
one-byte input, exact-cap and cap-plus-one boundaries, and UTF-8/duplicate-key
rejection. The combined relevant regression group passes 112/112; py_compile
and `git diff --check` pass.

The candidate is not connected to the v01 systemd smoke or request adapter,
and it has not completed a valid release/response cycle. Runtime identity,
receipt integration, canonical application-schema limits, full failure-map
coverage, independent review, and external supervision gates remain open. No
service, inference, OOM, training, score, or match ran. See
`docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.

### 2026-10-05 executed-runtime attestation research

Primary-source review found that descriptor-based `fexecve` avoids pathname
replacement but does not stop file-content changes between hashing and exec.
Linux fs-verity is the stronger per-file candidate: it makes verity files
read-only and verifies reads/mmap, while still requiring the measured digest to
be authenticated against a trusted manifest. Python's documented
source-to-code path can execute exact already-read source bytes inside explicit
module namespaces. Proposed chain: a trusted minimal launcher verifies
fs-verity digests for the interpreter, dynamic loader and mandatory native
libraries, descriptor-executes that interpreter, then a minimal Python
bootstrap verifies and compiles allowlisted project sources from the exact
bytes. Startup and loader state are also in scope: isolate CPython (`-I -S`),
attest its pre-bootstrap import inputs, sanitize loader environment variables,
and bind RPATH/RUNPATH, preload/cache configuration and later `dlopen`
dependencies to the verified image. None of this is implemented or
host-validated.

Read-only shell probes found the project checkout on an ext4 RW bind mount and
Python/runtime files under an ext4 RO root. A short no-inference systemd user
service under the reviewed 128/96 MiB, swap-zero, 8-second profile instead
saw both `/` and the project path on one ext4 RW mount. Its unit had no
`RootDirectory`, `RootImage`, `ProtectSystem`, private mounts, or read-only
binds. Python's main executable, ELF loader, libc/libm/libpython and two
extensions appeared in `/proc/self/maps`, but were not bound to a trusted
manifest. CPython `-I -S` was effective. The process reported
`Seccomp: 0`; nevertheless `FS_IOC_MEASURE_VERITY` returned errno 95 for the
same seven runtime files. Linux documents this `EOPNOTSUPP` result as kernel
fs-verity support missing or the filesystem superblock lacking its `verity`
feature. The running kernel and ext4 driver advertise fs-verity support, so a
missing superblock feature is likely, but a read-only superblock query was
denied and did not confirm it. The kernel config also includes modular
dm-verity/loop support and signed-root-hash verification; modules were not
loaded/exposed during inspection. `/proc/1/ns/mnt` was inaccessible. The unit
completed without inference and was stopped/unloaded.

Independent review found no contract blocker, confirmed the systemd v262
image/signature description, and prompted the explicit errno interpretation
added to the note. Official systemd v262 documents `RootImage=`, dm-verity
`RootHash=`/`RootVerity=`, and optional `RootHashSignature=` verification with
a key in the kernel keyring. The host has unprivileged user namespaces
enabled, and the running kernel has modular dm-verity/loop support plus signed
root-hash verification. However, `systemd-mountfsd.service` and its socket now
report `LoadState=not-found`; `systemd-nsresourced.service` was inactive in the
earlier inspection. User-service
RootImage requires mountfsd and private user namespaces; no image mount or
trust configuration was attempted. mountfsd accepts images in designated
trusted system directories by location, or signed Verity images with a
trusted key. `/etc/verity.d` is absent and a read-only user-level keyring query
did not establish available trusted keys, so no image trust anchor has been
demonstrated. A read-only bind or `ProtectSystem=strict` alone would not prove
backing-file bytes immutable against changes outside the service namespace.
The response IPC path has a 65,536-byte hard bound and file-identity checks but
does not return exact wire-byte digest/length or enforce canonical re-encoding;
request v02 lacks a finalized schema-derived cap. Full findings and source
links: `docs/V212_EXECUTED_RUNTIME_ATTESTATION_RESEARCH_01.md`.

Follow-up read-only `keyctl`/`/proc/keys` checks did not expose the kernel
trusted keyring: `.builtin_trusted_keys` is not resolvable in the current user
key context, and the visible session/user rings contain no trusted-keyring
name. This cannot prove the kernel ring is empty. Both mountfsd service and
socket currently report `LoadState=not-found`, so no no-configuration-change
signed-image route is demonstrated. Preserve this runtime option as
unavailable; do not attempt a mount unless an existing authorized trust anchor
and mountfsd route can be inspected. The request/response schemas and candidate
byte caps are now drafted and mechanically audited; obtain independent design
review and add actual stream-boundary tests before adapter integration. Do not
open inference, training, pilot or OOM gates from this research note.

### 2026-10-05 signed-image trust-store feasibility follow-up

Read-only host inspection found no conventional systemd userspace Verity
certificate directories at `/etc/verity.d`, `/usr/lib/verity.d`,
`/run/verity.d`, or `/lib/verity.d`. Installed systemd v262 documentation says
userspace signature verification defaults on and may use those locations or
built-in kernel certificates; the existing user-level keyring query did not
establish whether a suitable built-in key is available. mountfsd's relaxed
policy for designated image directories is location trust and does not by
itself establish an authenticated root hash for a project image. No key,
certificate, image, unit, or system trust setting was created or changed, and
no RootImage/mountfsd probe ran. A trust anchor and safe no-configuration
route remain unproven; keep runtime attestation and adapter integration
blocked pending that evidence. See
`docs/V212_EXECUTED_RUNTIME_ATTESTATION_RESEARCH_01.md`.

### 2026-10-05 request/response byte-bound source audit

Read-only inspection of the adapter and IPC source confirms the 65,536-byte
limit is only a generic transport ceiling. The candidate v02 adapter payload
has float monotonic deadlines, unbounded/overridable numeric values and a
cgroup path without a protocol length bound; its worker reads stdin without a
byte limit. Its response has a floating-point duration, no closed schema, and
an unbounded error-name field. Existing enum/board/action domains are useful
but insufficient to derive a worst-case encoding. No smaller cap or schema
was guessed. Next: version and review exact field/range bounds, choose integer
time units consistent with the canonical encoding, and only then derive
separate request/response byte caps. No request, worker, model, service, game
state, score, or outcome was run/read; no gate changed. See
`docs/V212_REQUEST_SCHEMA_BOUND_AUDIT_DRAFT_01.md`.

### 2026-10-05 candidate v02 request/response schema bounds

Drafted an unreviewed closed-schema proposal that replaces float timestamps
with bounded integer nanoseconds, uses fixed enums/hashes instead of free-form
strings, and defines success-only response fields. A reproducible local
calculation with the proposed canonical encoder gives candidate maxima of 811
request bytes and 747 response bytes. These are proposal figures, not selected
caps: the cgroup-path digest and interface ranges need design review; the embedded
byte witness passes but a checked schema/range validator is still required, and
the candidate adapter's 1.5 GiB memory default has not been reconciled with the
observed 128/96 MiB service
profile. No code or gate changed. Keep adapter integration, inference, pilot,
training and OOM operations closed. See
`docs/V212_REQUEST_RESPONSE_SCHEMA_V02_PROPOSAL_DRAFT_01.md`.

### 2026-10-06 failure-test traceability audit

Added a case-by-case map from the supervision failure plan's 22 cases to named
tests in the current synthetic/helper suites. An AST-based static check resolved
40 fully qualified references and confirmed all 54 distinct referenced test
method names exist. This verifies names only; it does not establish that those
tests jointly prove the acceptance invariant. At that point, the map marked
the amended-counter-pair, both counter-read positions, deadlines after receipt
durability, post-receipt Ctrl-C, and request-v02 integration as gaps. The mock
additions below partially cover both counter-read positions and stop-boundary
timeout/interruption. No tests or live services were run during traceability
mapping, and no supervision, inference, pilot, training, or OOM gate changed. Details:
`docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md`.

The mock armed-smoke suite now injects first- and second-counter-read failures,
a stop-command timeout after receipt durability, and Ctrl-C at that same stop
boundary. The four focused regressions pass; the whole smoke module passes
28/28. Both counter failures prevent receipt publication, and timeout/Ctrl-C
preserve the exact durable receipt bytes and unit/workspace reconciliation
handles. These are mocked lifecycle checks: the timeout is an injected command
result, not live deadline or recovery evidence. Mandatory amended-counter-pair
validation and the real request/runtime path remain open. No gate changed. See
`docs/V212_SUPERVISION_FAILURE_TEST_PLAN_V01_DRAFT.md` and
`docs/V212_ARMED_SERVICE_SMOKE_V01.md`.

### 2026-10-06 versioned mandatory-counter receipt boundary

Added an isolated v03 receipt boundary that rejects both omitted counter
snapshots and either one-sided omission, while leaving the v02 helper's
compatibility behavior unchanged. A complete pair is delegated to the existing
v02 evidence validator/classifier; the emitted v03 receipt records both the
wrapper source digest and delegated v02 source digest. The four focused v02/v03
tests pass 30/30. This closes the isolated CNT-01b assembler case only; no
request/runtime integration or end-to-end action/receipt gate is established.
No service, inference, OOM, training, pilot, or outcome evaluation ran. See
`two_player/v212_supervision_receipt_v03.py` and the updated failure test plan.

### 2026-10-05 proposal-only schema-bound audit

Added `two_player/v212_request_schema_v02_proposal_audit.py` and focused
standard-library tests without connecting them to either request adapter. The
audit exposed a malformed extremal witness in the draft: a 64-cell board was
paired with Connect Four 6x7. Rechecking each allowed variant with its exact
board length confirms the worst canonical request is still 811 bytes (Connect
Four 8x8); the response witness remains 747 bytes. Eleven tests pass, covering
the field/range domains, canonical encoding, duplicate keys, request/response
nonce/digest and cgroup/profile binding, and exact/cap-plus-one byte
boundaries. This proves only the proposal's structural schema and arithmetic.
It does not prove root reachability/state-hash consistency,
bounded stream reads, worker/caller integration, or the approved resource
profile. Independent design review and those integration checks remain open;
no research gate changes.

### 2026-10-04 supervision architecture audit

Read-only audit of the armed synthetic smoke confirmed exact in-memory execution for its three worker helper files, active manager/cgroup/property checks, one invocation-bound journal marker, two invocation-bound local counter snapshots, and receipt-before-stop behavior. It also identified integration blockers: caller source hashes are taken after imports and cannot attest loaded code objects; no structured Python/systemd runtime fingerprint is included; and the request digest is recorded in the envelope but is not bound into the release token or computed by the worker from raw stdin bytes. Failure-path behavior remains mock-only; the single normal-exit receipt is not invalidated by these gaps. Added `docs/V212_SUPERVISION_ARCHITECTURE_AUDIT_01.md`. Next: obtain independent review of a versioned request-digest/token amendment and an exact runtime/source-loading contract, then close manager/journal/counter failure mapping. Keep request-adapter, inference, training and pilot gates closed; OOM still requires separate explicit authorization.

### 2026-10-04 armed no-inference service smoke

Implemented `two_player/v212_armed_service_smoke_v01.py` and its mocked lifecycle/failure tests. After independent review and three receipt-boundary fixes, one bounded systemd v262 synthetic worker passed the pre-compute release gate and normal exit. The caller persisted a mode-0600 receipt before cleanup; its embedded digest matched, the local counter delta was zero, and the service ended `not-found`. Receipt: `/tmp/caissa-v212-armed-smoke-a_a4wly0/receipt.json`, SHA-256 `ee1d679c27f5a2c2b009045582a5d18eb8668f396fa33fb82e7203185a26a3a0`. The focused smoke/collector/live-evidence/receipt/protocol/token/IPC suites pass 116/116. Mocked recovery covers bad/duplicate-key responses, missing markers, receipt publication/durability failures, unit-stop and IPC-cleanup failures, active-state query error and not-found start-race, non-success manager result, deadline expiry while active, and Ctrl-C before dispatch, during release, and after dispatch. Post-dispatch errors carry the validated invocation and worker-cgroup identifiers for reconciliation. Independent review confirmed the controlled clocks, interruption handlers, and diagnostics. This is one normal-exit no-inference observation only; it does not validate OOM, live timeout/interruption recovery, repeatability, request-adapter behavior, inference feasibility, or the pilot. No model, adapter, project data, score, or outcome ran. Next: audit source/runtime fingerprinting and the remaining manager/journal/counter failure map before staged request-adapter integration; OOM remains separately authorization-gated. See `docs/V212_ARMED_SERVICE_SMOKE_V01.md` and `GROUND_TRUTH.md`.

### 2026-10-04 reviewed no-inference normal-exit smoke

After the mocked lifecycle suite and independent architecture review, ran one bounded synthetic transient user service through normal exit. systemd v262 accepted the unit; the worker and caller were in distinct cgroups; the invocation-bound receipt was persisted before stop; embedded receipt digest matched; and the collector verified `LoadState=not-found` after cleanup. Receipt: `/tmp/caissa-v212-smoke-183523/receipt.json`, mode 0600, SHA-256 `55937b10f67666b0f0ca3bdb2365cf22b28ac93a3e2e92ee901bbceef5d351f4`. This is a second no-inference normal-exit observation, not OOM/timeout validation or request-adapter integration. No inference, project data, score, or outcome ran. Next: close remaining armed-worker integration and failure-contract gaps before any request adapter use; OOM remains separately authorization-gated. See `docs/V212_SUPERVISION_COLLECTOR_V01.md` and `GROUND_TRUTH.md`.

### 2026-10-04 mocked supervision lifecycle and receipt-failure coverage

Extended `tests/test_v212_supervision_collector_v01.py` with nine fully mocked orchestration cases for success, invalid response, dispatch failure, non-success manager result, local-counter/journal evidence failure, receipt persistence failure, post-publication durability uncertainty, unit-stop failure, and IPC-cleanup failure. Follow-up review found and prompted two fixture fixes: response publication now follows the exited manager snapshot, and evidence-capture failures assert no stop/cleanup with the workspace retained. Success asserts response read follows worker exit and durable receipt completion precedes unit stop and cleanup; ambiguous publication retains the receipt/workspace and avoids stopping the service. The reviewer found no remaining issue in the revised changes. The focused collector/live-evidence/receipt/armed-protocol/release-token/IPC suite passes 92/92 using `unittest`; `pytest` is unavailable in this runtime. This is mocked boundary coverage only. No adapter, inference, OOM, data, score, or outcome ran. The reviewed no-inference live normal-exit smoke is recorded above. Next: close remaining armed-worker integration and failure-contract gaps before any request adapter use; OOM still requires separate explicit authorization. See `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.

### 2026-10-04 mocked armed controller/worker release protocol

Added `two_player/v212_armed_protocol_v01.py`: the caller validates an exact bounded v01 service profile and live memory values, waits for the worker's blocking FIFO barrier, then sends a nonce/source/invocation/cgroup-bound token carrying the absolute monotonic deadline. The worker checks the deadline immediately before the synthetic callback. Deadline, resource-profile, live-memory mismatch and worker-context tests establish callback suppression on failure. Combined IPC/token/protocol tests pass 36/36; independent static review found no blocker in this mock scope. This is not systemd snapshot provenance, worker termination/reap, journal/counter receipt capture, or live service evidence. No service, adapter, inference, OOM, data, score, or outcome ran. Next: mock supervisor lifecycle/receipt/cleanup failure boundaries, then review before live normal-exit service smoke. See `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.

### 2026-10-04 synthetic worker release-token verifier

Added `two_player/v212_release_token_v01.py`: the worker blocks on the verified release FIFO, reads one bounded token through EOF, validates canonical sorted JSON and its digest, binds nonce/unit/invocation/boot/cgroup/source-manifest identity, and compares the live cgroup memory limit files. Fixture tests cover mismatch, malformed/duplicate/oversized input, FIFO substitution, empty EOF and blocking readiness. Combined IPC/token tests pass 30/30; independent static review found no remaining blocker. This is helper-level no-inference verification only: there is no controller/service integration or internal FIFO-read timeout, and the future caller deadline/service runtime must bound that wait. No service, adapter, inference, OOM, training, data, score, or outcome ran. Next: mocked service/controller failure-path protocol; review before any live service smoke. See `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.

### 2026-10-04 release-FIFO IPC primitive

Added an optional private mode-0600 release FIFO to `two_player/v212_worker_ipc.py`, with device/inode/type/owner/mode checks around the caller's nonblocking writer open, a one-shot 4096-byte bounded write contract, and substitution-safe cleanup. Its readiness test exercises a blocking reader open; the 21-case focused IPC suite passes, including concurrent duplicate-open rejection. This is transport groundwork only: no worker token verification, service launch, cgroup/property gate, receipt integration, or failure-path service protocol exists yet. No inference, OOM, training, data, score, or outcome ran. Next: implement a synthetic no-inference armed worker and mocked failure-path tests; obtain independent review before any live service. See `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`.

### 2026-10-04 request-adapter integration design review

Static comparison found that the existing v02 request adapter still uses a same-cgroup pipe worker and caller-side hierarchical counters, so the new transient-service collector cannot be substituted as a command-only change. Added and independently reviewed `docs/V212_REQUEST_ADAPTER_INTEGRATION_DESIGN_01.md`: it requires a no-compute armed worker, a nonce/invocation/cgroup/effective-limit-bound release FIFO handshake, fail-closed response/receipt handling, and exact verified source bytes. Review findings on start ordering, release snapshot contents, token replay, and source TOCTOU were resolved in the design. No adapter code or inference ran, and no gate changed. Next safe implementation step: synthetic no-inference armed/release service plus failure-path tests. OOM stage 3 still needs separate explicit authorization; no-outcome request integration remains behind the staged design gates.

### 2026-10-04 invocation-bound normal-exit receipt collector

Implemented `two_player/v212_supervision_collector_v01.py`, completed independent static review, and ran one no-inference transient-service smoke. The smoke validated file-backed nonce/schema IPC, distinct caller/worker cgroups, configured manager and cgroup limits, two worker-local counter snapshots, one unit/invocation/cgroup-bound service-journal marker, receipt persistence before cleanup, and final `LoadState=not-found`. The private receipt and SHA are recorded in `GROUND_TRUTH.md` and `docs/V212_SUPERVISION_COLLECTOR_V01.md`. The focused suites pass 62/62; adapter suites remain unverified because NumPy is unavailable. This is one normal-exit instrumentation observation only. No kernel OOM journal was collected, and no OOM, inference, training, data, score, or outcome was run. Research, pilot, training, and OOM gates remain closed. Next: review whether the current evidence contract is sufficient for a separate request-adapter integration design; do not run OOM or inference without their distinct gates and authorization.

### 2026-10-04 file-backed transient-service IPC design

Official systemd v262 source confirms `systemd-run` rejects `--wait`/`--pipe` when combined with `--remain-after-exit`, and unit GC drops manager results. Added and independently reviewed a file-only bounded IPC helper; its 13 synthetic cases plus the 26 receipt-assembler cases pass 39/39. A trivial no-inference transient service then verified file-backed stdin/stdout, retained success state, worker/caller separation, effective cgroup/resource limits, and cleanup. It did not persist a same-invocation receipt or test timeout/race/OOM behavior; one worker-side cgroup-file lookup failure remains unexplained and is preserved in Ground Truth. Next: implement a caller-owned manager/journal/cgroup collector that persists the no-inference receipt before cleanup, then independently review it. Do not run an OOM test without separate explicit authorization. No inference, training, project data, or pilot ran. See `docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`.

### 2026-10-04 live evidence adapter primitives

Added `two_player/v212_live_supervision_v01.py` with bounded systemd-property parsing, invocation-bound active/post-exit snapshot normalization, fail-closed `memory.events.local` reads under the supplied cgroup root, and private one-shot receipt persistence. Receipt destinations are reserved exclusively before the existing fsync-and-rename writer is used; failed writes retain a claim for reconciliation. Ten focused tests plus the previous IPC and receipt suites pass 49/49; independent review found no remaining P1/P2 blocker after fixes for retained-success mapping, writable ancestors, and timestamp order. This is adapter groundwork, not operational supervision evidence. No service, inference, OOM, training, project data, or outcomes were run/read. Next: integrate bounded manager and journal capture around the no-inference worker lifecycle, then independently review and perform only a normal-exit smoke. OOM remains separately authorization-gated. See `docs/V212_LIVE_EVIDENCE_ADAPTER_01.md`.

### 2026-10-04 systemd worker IPC/lifecycle constraint

The installed systemd 262 CLI rejects combining `--wait` with `--remain-after-exit` and `--pipe` with `--remain-after-exit`; `--collect` unloads the unit, and garbage collection drops manager execution results. Thus the service adapter cannot rely on a single `systemd-run` command for both request/response streaming and retained manager evidence. This earlier pinned-D-Bus direction is superseded by the tentative file-backed IPC candidate above; neither is implemented or runtime-verified. No service, inference, OOM test, or pilot ran; supervision and pilot gates stay closed. See `docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`.

### 2026-10-04 V03 compute-pilot RSS guard candidate

Added a versioned no-training V03 implementation candidate while preserving the executed V02 sources/receipt: RSS is checked at entry, every 256 visited nodes, and exit; a known crossing returns a diagnostic row without another sampler call. The runner writes an fsynced per-cell progress journal and only emits a complete aggregate receipt after full schedule verification. Any failure after receipt linking is marked `publication_uncertain` in the journal/CLI, and its existing path blocks reruns pending reconciliation. Eleven V03 tests, including V02 counter parity, RSS-stop runner journaling, and post-link publication failures, and the combined V02/V03 suite pass 17/17. The latest code revisions passed independent static review. RSS is still cooperative, V03 has not been run, and external supervision gates remain closed. See `docs/V212_COMPUTE_PILOT_V03.md`.

### 2026-10-04 JEPA Arcade two-player prior art

Added the JEPA Arcade author model card as artifact-level prior art for action-conditioned JEPA representations in two-player Atari games. Its reported state-probe metrics and hand-written controller do not establish strategic strength or search benefit. This closes broad “JEPA in two-player games” novelty language while leaving only the narrower exact-rule adversarial decision-quality comparison open. The GitHub code link was not independently inspectable in this pass, and the card's claims remain author-reported. No method/gate changed; see `docs/RELATED_WORK.md` and the V2.12 novelty crosswalk.

### 2026-10-04 root-schedule yield sensitivity

Added a closed-form sensitivity for the proposed six-stratum schedule requiring at least 16 valid roots among 64 candidates per stratum. Under hypothetical equal, independent per-slot validity, a common validity rate near 0.3834 implies about 95% whole-schedule yield; this is not an observed rate, accepted target, or feasibility result. The analysis highlights why reviewer disposition must specify whether a schedule-pass probability is required and how stratum heterogeneity/dependence is handled. No roots, data, outcomes, or inferential calibration were generated. See `docs/V212_ROOT_SCHEDULE_YIELD_SENSITIVITY_01.md`.

### 2026-10-04 LAMIR prior-art crosswalk

Added the already full-text-reviewed LAMIR study to the V2.12 novelty crosswalk. It establishes learned latent look-ahead and equilibrium-oriented reasoning in two-player zero-sum games; its formalism also represents sequential games using fictitious non-acting-player actions. This removes broad novelty claims around latent reasoning in alternating games. The remaining CAISSA question is limited to its specific EMA-target JEPA objective and decision-rank/regret effect in deterministic, fully observed exact-rule games against matched controls. This is a testable research question, not a novelty finding. No method or gate changed; no data, model, roots, score, match, or outcome was generated or accessed. See `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md` and `docs/RELATED_WORK.md`.

### 2026-10-04 root-sampling draft consistency reconciliation

A fresh independent read-only review found stale references to the superseded Design01 schedule, canonical-window deduplication wording that conflicted with split amendment v05, and root-sampling text that still required symmetry-unique states. The split amendment, generation design, duplicate/overlap audit, v05 root-sampling draft, and review record now agree editorially that source-window IDs define fit-bank distinctness, canonical content is diagnostic, and repeated development-root slot states remain separate observations under Design02. The global six-stratum under-yield stop is proposed in both v05 and Design02, but remains unaccepted and has no chosen schedule-pass-probability threshold. This does not validate the changed estimand or inference. No roots, simulation, data, model, scoring, or outcomes were run/read; no gate changed. See `docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-04 MetaOthello multi-world representation prior art

Full-text review of the ICML 2026 camera-ready MetaOthello study found shared board-state representations and causal cross-variant probe transfer across Othello-like games with changed rules or token mappings. Reported next-move-distribution α-scores exceed 0.98, but each model was trained only once at seed 42. The paper's world-model usage is latent state representation from move histories, not an explicit JEPA transition planner. This closes broad multi-rule shared-representation claims; it does not evaluate adversarial decisions, legal-action values, board-size transfer, or decision regret. No code/data or CAISSA outcomes were accessed. No method or gate changed. See `docs/RELATED_WORK.md` and `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.

### 2026-10-04 static request-adapter capacity audit

Added `docs/V212_ADAPTER_CAPACITY_AUDIT_01.md` with model-array and model-call upper bounds derived from the random-weight request harness. They show only that the pilot-shaped parameter arrays are small; they do not estimate Python/cgroup peak memory, latency, or fitted-model capacity. Static call-graph review also found that the v02 request wrapper dispatches actual workers through the v01 module, so both source blobs must be version-bound. The worker still shares its caller cgroup and the external supervision/receipt correction remains a draft. No request, data, score, outcome, or fit was run/read; no gate changed. Next: obtain independent review of versioned external supervision and receipt integration, then perform only separately authorized no-outcome checks. OOM fault injection remains separately authorized.

### 2026-10-04 RePAIR chess representation prior art

Full-text review of Koller et al.'s RePAIR paper found self-supervised latent gap repair over chess-state sequences. The paper's chosen later-experiment objective omits the optional JEPA term; its 93.71% ± 0.05% result is square-element reconstruction with 80% sequence masking and a 50% always-empty baseline, not move selection or planning. This closes broad claims to self-supervised latent sequence reconstruction in chess but does not establish action-conditioned transition planning or adversarial max/min. No source code/data was downloaded or run; repository reuse licensing was not visible. This only narrows the prior-art positioning; no method or gate changed. See `docs/RELATED_WORK.md` and `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.

### 2026-10-04 root-sampling and inference review

Independent static review found the design-02 first-valid-slot argument coherent under its explicit IID/slot-local assumptions, but the proposal materially changes v04 §7's target, sampling unit, occupancy-band weights, and bootstrap. It is not compatible with current v04 and its max-|T|/centered-bootstrap/Holm procedure is not finite-sample calibrated by cited sources for 20 seeds × 16 slots per band. Added a replacement §7 v05 draft and review record; v04 remains current. A follow-up review required carrying forward v04's fresh/disjoint locked-confirmation schedule and no-replacement/no-censoring forfeit rules, and called out v05's global two-variant under-yield stop as an unresolved choice relative to design 02. Before any roots or scores, independent method/statistical review must accept or reject the changed estimand and slot/RNG/yield/seat/bootstrap/failure contract, and decide whether a design-matched calibration is required. If required, freeze scenarios, numerical tolerances, and failure disposition before simulation. No simulation, roots, outcomes, or training occurred. See `docs/V212_ROOT_SAMPLING_REVIEW_01.md` and `docs/METHOD_SPEC_V212_V05_ROOT_SAMPLING_DRAFT.md`.

### 2026-10-04 root-inference methods literature check

Primary methods sources show that two-way/crossed resampling has asymptotic results under explicit assumptions, while few-cluster and multiway procedures can behave differently in finite samples; none directly calibrates the proposed bounded paired-score statistic, conditional yield mechanism, 20-seed × 16-slot strata, or 15-contrast max-|T| gate. An independent static review supported the recommendation to calibrate as a precaution and required preserving macro-contrast algebra, paired-seat/shared-arm dependence, variance heterogeneity, and the distinction between schedule yield and conditional inferential error rates. The note now uses direct Romano–Wolf step-down citations and states that calibration cannot establish general validity beyond its frozen scenarios. A qualified statistical reviewer must still accept, revise, or reject the recommendation and freeze scenarios, tolerances, Monte Carlo precision, and failure consequences before any simulation. v04 remains current; no simulation, roots, scores, training, or outcomes were generated or accessed.

### 2026-10-04 production generator readiness review

Independent static review found the current protocol drafts insufficient for production-generator implementation. Before code, freeze/review the split-matrix amendment and numeric episode quotas/resource basis; pair/action/policy RNG streams and support disposition; the 928-window source-ID, no-replacement, terminal-only and nonempty-target minibatch contract; H0–H4 key versus lineage and overlap rules; and atomic manifest/receipt/partial-failure semantics. Recorded as explicit prerequisites in `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`. The synthetic auditor remains fixture-only; no policy, episode, data, or generator was run, and no gate advanced.

### 2026-10-04 static episode quota lower bound

Rule-source arithmetic under Draft v05 eligibility gives at most 42 action-start windows per complete Connect Four 6×7 episode and 64 per Reversi6 episode, so 928 source windows imply optimistic minima of 23 and 15 episodes. Passes are bounded by placements because a nonterminal Reversi pass is legal only when the opponent can place next. These are structural lower bounds only, not resource-based quotas or proof of feasibility; actual episodes can contribute fewer windows. No games or data were generated. See `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`.

### 2026-10-04 synthetic receipt-assembler contract

Added a versioned, fail-closed receipt assembler and 26 synthetic tests binding systemd unit/invocation/ControlGroup/boot snapshots, worker-local event counters, and normalized kernel OOM evidence. Static independent review found no remaining blocking attribution issue after strict post-active time windows and input validation. This is not a live collector or adapter integration: the current request adapter still lacks caller isolation and worker-specific OOM evidence. No service, OOM fault test, inference, data, or outcome run occurred. Keep the supervision and pilot gates closed; any new OOM injection still needs separate explicit authorization. See `docs/V212_RECEIPT_ASSEMBLER_DESIGN_01.md`.

### 2026-10-04 multimodal JEPA videogame prior-art update

A primary-source search added Campese and Moschitti's ICML 2026 workshop study of multimodal JEPA pretraining on Pokémon Red, with a frozen representation used by PPO. Its abstract reports held-out starting-state results and an offline trajectory-diversity finding. This broadens the established JEPA-in-games context, but it is not evidence for action-conditioned exact-rule minimax planning in a two-player zero-sum game. Full-text access was blocked in this source pass, so details beyond the official abstract/first page remain unverified. No method or gate changed. See `docs/RELATED_WORK.md`.

### 2026-10-04 EB-JEPA action-conditioned planning prior-art update

A primary-source review of Terver et al.'s EB-JEPA paper and official repository found AC-video-JEPA: action-conditioned multi-step latent prediction with goal-conditioned MPPI/CEM planning in Two Rooms. The authors report 97±2% success on randomized-wall navigation and 1±1% when removing inverse-dynamics supervision, alongside substantial variance/covariance and temporal-similarity ablation effects. This removes standalone novelty claims for action-conditioned JEPA planning and inverse-action auxiliary losses. Its continuous 2D goal-navigation results do not establish anything about deterministic adversarial board games or V2.12 performance. It informs reviewer disposition of the existing inverse-action factorial only; no method or gate changed. See `docs/RELATED_WORK.md` and `docs/V212_INVERSE_ACTION_CONTROL_DESIGN_01_DRAFT.md`.

### 2026-10-04 composite no-inference journal/receipt rehearsal

The no-inference composite rehearsal validated a pre-armed journal follower, 12 live cgroup samples, worker invocation/unit/cgroup binding, separate replay of the retained historical OOM record, and a file+directory-fsynced atomic receipt before cleanup. Independent review accepted this composition prerequisite. It did not exercise live same-invocation OOM capture, positive counter changes, or failure handling; the broader supervision/pilot gate stays closed. See docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md.


### 2026-10-04 kernel-attributed bounded worker-cgroup OOM trial

One 64 MiB no-inference transient-service worker was killed during a bounded 256 MiB touch attempt. The external caller survived, the worker did not complete, and the kernel journal positively attributes the kill to CONSTRAINT_MEMCG with oom_memcg/task_memcg matching the worker unit and group-kill policy. The event-file monitor missed a positive local counter; the journal excerpt was copied only after teardown. This establishes one bounded worker-cgroup OOM/caller-survival observation, while pre-teardown receipt integration, counter capture, repeatability, ancestor headroom, request timing, inference, and the wider supervision gate remain open. No pilot/outcome gate changed. See docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md.


### 2026-10-04 no-inference event/result capture-path check

The no-inference 128 MiB transient-service check captured 14 local event samples while live, then captured the normal-exit systemd result after the cgroup disappeared; receipt persistence and unit cleanup passed. Independent review accepted this as the stage-2 capture-order prerequisite. No event changed, so OOM attribution remains unverified and stage 3 remains open. Log: /tmp/caissa_v212_capture_preflight_v2.log.


### 2026-10-04 bounded transient-service OOM probe (ambiguous)

A bounded no-inference transient-service worker passed the finite 64 MiB/swap-zero/OOM-group preflight, attempted a 256 MiB allocation, and was recorded by systemd as Result=oom-kill; the external controller survived and the worker did not complete. However, the last worker-local memory.events.local sample had max=3 and zero oom, oom_kill, and oom_group_kill. Independent review found the source ambiguous, so this does not demonstrate local OOM containment and stage 3 remains closed. Verify and review event/result capture under no-inference stage 2, including attribution before cgroup teardown, before repeating fault injection. No inference, training, data, or outcome gate changed. See docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md.



## No-inference external-service placement completed (2026-10-04)

After design review, two short transient-service probes confirmed worker placement in a separate cgroup and a finite effective 128 MiB memory/96 MiB high limit. A third `--collect` lifecycle probe confirmed the unit and cgroup evidence disappear after completion; the retained-unit probe kept manager result fields but not the cgroup files. These results verify only no-inference placement and successful-exit evidence lifecycle. The OOM classification path, caller survival, external counter capture, receipt persistence, request timing, and inference remain unverified. All temporary units were cleaned. The next gate is independent review of the updated evidence, then an explicitly authorized OOM fault test; no OOM or pilot is authorized by this observation. Keep training and outcomes closed.

## Supervision design review revision (2026-10-04)

Independent review requested an explicit test of transient unit/cgroup evidence lifetime. The revised design requires measuring when `memory.events.local` disappears, verifying manager OOM/result fields through unit release, and proving the selected receipt path before cleanup; it specifies an external monitor fallback and fail-closed behavior if evidence is unavailable. The design awaits re-review. No unit or worker has been started. Keep OOM injection, inference, and pilot closed until each stated gate is met.

## External supervision preflight (2026-10-04)

Read-only lattice checks confirm systemd 262, an active delegated user manager, and the cgroup-v2 memory controller enabled in its subtree. The user manager reports `degraded`. Its inherited effective memory ceiling is about 15 GiB; direct user-service/app-slice memory limits are unlimited. This advances only the capability/ancestry survey. The finite worker-service limit, live headroom, caller survival under worker-local OOM, receipt capture, and cleanup remain unverified. No unit or worker was started; no OOM test or inference ran. Next: resolve the manager health observation if relevant, then obtain independent review before a no-inference transient-service placement check. Keep the pilot closed.

## External supervision research update (2026-10-04)

Added [V2.12 external worker supervision design 01](docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md), a primary-source-backed proposal to test a transient systemd service as a worker-local cgroup boundary with the caller outside that unit. Linux cgroup semantics do not guarantee supervisor survival under ancestor or host-wide OOM, and systemd service runtime does not cover all request startup latency. The proposal requires capability/ancestry preflight, no-inference placement verification, a separately authorized disposable OOM fault test, caller-observed no-outcome integration, receipt validation, and independent review. No experiment ran and no runtime, pilot, training, or data gate passed. Keep the pilot closed.

## V2.12 checkpoint (2026-10-03)

A versioned request-adapter v02 candidate now remeasures elapsed time after
all supervisor-side request processing and converts late results to forfeits.
Its exact remote focused suite passes 8/8, including a mocked post-worker delay.
This remains software-only evidence: no cgroup-contained request or inference
was measured. External OOM supervision, independent review, receipt integration,
and caller-observed deadline enforcement are still required; the pilot gate
remains closed. See the [runtime audit](docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md).

The mocked-clock deadline finding applied to adapter v01: it sampled
elapsed time before post-worker cgroup validation and reply checks. Adapter v02
now remeasures after full function processing and converts a late return to a
forfeit; its new post-worker-delay regression test passes. This is a source
contract correction only, not a hard real-time guarantee or measured request.
Keep v02 unapproved until independent review, external OOM supervision, receipt
integration, and caller-observed no-outcome deadline tests pass. See the
[trajectory/runtime audit](docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md).

The 2026-10-04 primary-source refresh adds JEPA-TTT (persistent online
predictor adaptation under dynamics shifts) and point-cloud adaptations of
LeWM/Delta-JEPA to Related Work and the draft crosswalk. They reinforce that
action-conditioned JEPA planning and action-sensitive objectives are established
outside this exact game setting. Neither evaluates deterministic two-player
exact-rule max/min or isolates the proposed V2.12 loss. This is positioning
evidence only; the method and gates remain unchanged, and no training or pilot
is authorized. See [Related Work](docs/RELATED_WORK.md) and the
[prior-art crosswalk](docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md).

A precision clarification in the review-only outer-simulation audit separates
marginal operating-characteristic rates from paired method differences. For
methods evaluated on the same generated outer datasets, estimate the replicate-
level paired difference and its Monte Carlo error directly; do not infer it by
subtracting marginal intervals. Pairing does not guarantee lower Monte Carlo
error: its variance effect depends on the covariance of paired method outcomes.
Common datasets pair methods within replicate, while independent outer streams
separate replicates. The required R and
decision/uncertainty criteria remain for independent review to freeze before
any simulation. No simulation or gate change follows from this note.

The related-work scan added Chess-World-Model (2026), a 10M-game benchmark
for exact chess-state reconstruction from move sequences, including a
uniformly random legal-play split. This narrows broad claims to board-game
state tracking; the paper does not evaluate JEPA or planning/decision quality.
An apparent separate JEPA-Chess result remained aggregator-only and its
reported metrics were excluded without a primary-source record. A primary
ESANN 2025 paper also establishes one-step action-conditioned JEPA
representation learning with PPO on CartPole; it does not evaluate adversarial
board-game planning. This narrows the novelty question to the incremental
effect of recursive latent matching on exact-rule max/min decision quality.
No method or gate changed; see the updated crosswalk and Related Work.

A no-training source audit of the in-memory trajectory helper found it does
not enforce that a supplied episode begins at the game's initial state or
preserve a parent-episode/original-ply offset for a trajectory suffix. A
deterministic suffix fixture was accepted as a new episode with start ply zero;
the focused seven-test suite passed. This does not show existing data leakage,
but a production materializer must bind full-game origin, seed, policy pair,
and source hashes—or use typed segments with parent lineage—before data
generation. No method/gate change or corpus authorization follows.

The lattice session verified cgroup enforcement in disposable user
scopes: a 1.5 GiB `memory.max` was finite and inherited by a child; a separate
64 MiB no-swap scope killed an over-limit child and recorded `oom_kill=1`;
both cgroups were removed after cleanup. A new fail-closed request adapter,
`two_player/v212_request_adapter_v01.py`, checks the exact cgroup limit and
`memory.oom.group=0`, verifies that its worker inherits the same path, applies
absolute 5-second planner and 6-second response deadlines, kills a timed-out
worker group, and distinguishes OOM events from watchdog timeouts. The focused
suite passes 20/20. The exact remote adapter and test blobs also passed their
seven-test subset in a scratch overlay (7/7); this is mocked/in-memory
validation, not a cgroup-contained request measurement. A no-inference
subprocess preflight inside the real 1.5 GiB
scope verified that the worker inherited the parent's exact cgroup path,
`memory.max=1610612736`, and `memory.oom.group=0`; the disposable scope was
removed. No request/inference worker or multi-cell pilot ran. The adapter has no
report/receipt writer and awaits independent review. Keep RSS as sampled
telemetry and the budget as a proposal until an integrated no-outcome run and
receipt review pass. `memory.high` is not a hard limit; see
`docs/V212_HOST_MEMORY_CONTAINMENT_AUDIT_01.md`.

A source audit also found that V2.12-04 calls for counterfactual coverage but
does not define its branch population, denominator, or missing-support
handling. V2.8 reply closure is used for overlap checks, while its model-facing
targets remain observed actions; the V2.12 synthetic helper likewise only
forms observed-path windows. This is a protocol-definition gap, not a result
about model quality or leakage. Before data generation, define behavior
support and complete legal-branch evaluation, distinguish held-out-size
structural absence from ordinary missing actions, and get the versioned
protocol independently reviewed. See
`docs/V212_COUNTERFACTUAL_SUPPORT_AUDIT_DESIGN_01.md`; V2.12-04 remains
unchanged.

The follow-on `docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md` proposes
separate denominators for fitting-data action support, full root decision sets,
and visited-node expansion; it explicitly treats held-out-size exact support
as not comparable. A self-audit removed the pooled legal-edge ratio as a
headline because repeated states and game branching factor can dominate it;
the draft instead reports per-state coverage and state/episode frequency.
It now separates encoder-state exposure from exact transition edges used in
valid nonterminal target unrolls; the eventual trainer's masks must verify that
derivation before corpus generation. A source cross-check found that the
existing trajectory auditor jointly maps state/action paths only for duplicate
window detection; it does not provide a canonical edge-support ledger. The
draft now requires joint `(state, action, successor)` transforms and explicit
legal-set bijection/transition-commutation checks before any canonical edge
summary is reported.
The follow-on `docs/V212_DUPLICATE_AND_OVERLAP_POLICY_AUDIT_01.md` records a
separate source conflict: the frozen synthetic fixture rejects all canonical
duplicate windows, while split amendment v05 proposes retaining repeated fit
content as a diagnostic. A production materializer must not reuse that fixture
unchanged. Source-id uniqueness, prohibited cross-partition overlap, fit-bank
content diagnostics, and symmetry-distinct development roots now have separate
proposed dispositions; all remain subject to independent protocol review.
The source inventory in that audit records the declared in-scope maps (two
gravity-preserving maps for each Connect Four variant; D4 for Reversi), but
`canonical_key` does not return its minimizing map. A bounded
`tests/test_v212_symmetry_properties.py` suite now checks each declared map's
legal-action bijection and transition commutation on deterministic in-memory
fixtures for all four in-scope variants: it exhausts states through four
legal plies, then checks three deterministic paths to terminal plus a
forced-pass Reversi fixture. This remains shallow bounded coverage, not
exhaustive verification of later states; canonical edge metrics remain
disabled pending broader/adversarial code-property review and independent
protocol review.
The earlier design-01 root schedule kept only the first 16
symmetry-unique roots from 64 candidate slots per band, which changes the
accepted distribution. The conflict now has a candidate written resolution
in `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md`: retain repeated states as
separate valid slot draws, define the success-conditional first-passage
estimand, and stratify the crossed bootstrap by occupancy band. Design 02
aligns with the root-sampling amendment but is not frozen; independent
statistical/protocol review must accept the target, RNG assumptions, yield
rule, and inference procedure before generation or scoring.
The candidate resolution is now specified for review in
`docs/METHOD_SPEC_V212_ROOT_SAMPLING_AMENDMENT_DRAFT_01.md`: it defines the
success-conditional first-passage distribution, treats slot IDs as sampling
units, and proposes fixed one-third weighting with within-band bootstrap.
This is a design proposal only; v04 and the existing root schedule remain
unchanged pending independent review. A new conditional-IID argument states
the assumptions needed for the first 16 valid slots to represent IID draws
from the success-conditional law, conditional on the fixed yield gate passing;
it also flags deterministic PRNG streams as an operational approximation and
duplicate/outcome-based rejection as invalidating that argument. The draft
cites crossed and stratified-bootstrap method analogues and small-cluster
cautions with explicit limits; none validates the proposed small-sample
max-T/Holm procedure. The 10,000 replicates improve resampling precision, not
the number of independent seeds or root slots.
This remains a review draft, with no thresholds, data generation, method
amendment, or training authorization. Resolve it alongside the split matrix,
development-root schedule, and compute cap before producing any corpus.

The follow-on source review found that the V02 RSS guard is sampled/cooperative,
not a hard ceiling: the initial sample is not compared to the cap, periodic
checks happen every 256 nodes, and an over-cap final check can escape the
per-depth handler before the runner writes a receipt. Existing pilot tests do
not exercise RSS-cap paths. V02's completed cells remain valid as measured
compute evidence (max sampled RSS 50,212,864 bytes versus a 1.5 GiB cap), but no
future cap-stressed run should rely on this path as hard containment. A
versioned pilot update, RSS branch tests, and an OS/process memory bound are
required before describing RSS as a hard cap. See
`docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md`; no V02 rerun or training is
authorized by this finding.

The v04-authorized random-weight, no-training compute pilot v02 completed
1,152/1,152 cells to four plies; p90 wall time was 0.7970 s, p99 was 2.0148 s,
and maximum was 3.7419 s. Twelve cells exceeded 2 seconds. The 16 roots per
variant and three initializations broaden v01's four-root/one-initialization
sample, but both remain synthetic, random-weight measurements from one host.
The amended protocol and runner passed independent `gpt-6-luna/high` review.
The v02 compute-only report also passed review. The 10,000-node/5-second
planner cap proposal in `docs/V212_COMPUTE_BUDGET_AMENDMENT_05.md` passed
independent review as a proposal only; it is not an operational budget until
request-to-search headroom and the implementation pass pre-fit verification.
No training or match is authorized. See `GROUND_TRUTH.md`, the [v01 pilot report](docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_01.md), and the [v02 pilot report](docs/validation/V212_RANDOM_WEIGHT_COMPUTE_PILOT_02.md).

A 2026-10-03 targeted primary-source refresh added the September preprints
`The Planning Limits of Latent World Models` and `ReWAM` to
`docs/RELATED_WORK.md`. They reinforce two existing requirements: measure
decision ranking/regret at each imagined horizon, and distinguish learned
behavioral response models from exact-rule worst-case max/min search. They do
not change the research gate or authorize fitting. The next permitted internal
work is the no-training audit of the candidate multistep trajectory generator,
prior-art distinctions, and request-to-search resource headroom, followed by a
frozen method/protocol review before any fit. A static source audit found a
no-I/O synthetic V2.12 helper that constructs H0–H4 windows from caller-supplied
episodes for fixture assertions, but no production/corpus generator or V2.12
generation protocol. The current V2.8 leak-key audit covers H1/H2 plus two-ply
reply closure, not every V2.12 H0–H4 context/window state and H1/H2/H4 target.
The synthetic helper rejects canonical duplicate windows, while draft v05 calls
for reporting equivalent content diagnostically; production reuse requires an
explicit reviewed policy. A source-level runtime pass also confirmed V02's
per-search clock starts after input validation/model reset, while schedule/model
construction and warmup occur before the call; RSS is sampled every 256 nodes,
and no end-to-end action-response watchdog exists. These are expected pilot
instrumentation boundaries, not evidence the proposed request-anchored cap is
operational.
See `docs/V212_TRAJECTORY_AND_RUNTIME_AUDIT_01.md` and the frozen
`docs/V212_TRAJECTORY_AUDIT_PROTOCOL_V01.md`. The in-memory synthetic
fail-closed auditor is implemented, its focused tests pass, and independent
review accepted it for the synthetic-only contract. No data bank or trained
model is authorized by this software-contract step.
The follow-on design note `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`,
`docs/METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md`, and
`docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md` propose train-only fit windows on
training sizes and 48 held-out development root slots per variant. Design 02
supersedes the earlier unique-root proposal by retaining the first 16 valid
slots per occupancy band, including repeated board states, to align with the
success-conditional slot estimand in Amendment Draft 01. This resolves the
written design conflict only; independent review still must accept the target,
slot-independence assumptions, yield gate, band weights, and bootstrap before
any root generation or scoring.

A second targeted literature pass added Semigroup-JEPA and Action-Conditioned
Predictive Consistency to `docs/RELATED_WORK.md`. Recursive rollout JEPA is
direct prior art, so V2.12 can only support a game-specific empirical
increment after matched JEPA and decision-aware baselines. A JEPA-Chess title
appeared only in an aggregator record; no primary Zenodo/DOI source was found,
so its claimed results are excluded as unverified. These findings do not
authorize fitting or root generation and do not change the current gate.

A further primary-source check found PiJEPA (arXiv:2603.25981v1), which trains
an autoregressive multi-step JEPA world model and plans over action sequences
with policy-guided MPPI. Its single-agent continuous-robot task differs from
V2.12's exact legal branches and max/min backup, but confirms that multi-step
JEPA plus planning is established. The bounded comparison is recorded in
`docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`; it narrows the defensible claim to
an empirical incremental effect of latent matching over matched controls.
This is not a novelty finding and does not change the no-fit gate.

The expanded 2026-10-03 source pass added Value-Guided JEPA Planning, H-JEPA,
Delta-JEPA, WA-JEPA, and the game-domain ActSWM. These cover value-structured
planning, action-sensitive latent geometry, joint world/action prediction, and
multi-step JEPA planning in Minecraft. ActSWM is single-agent open-world control,
not zero-sum board play, but removes any claim that action-sensitive JEPA
planning in a game is new. The present candidate lacks those specialized
mechanisms; more critically, none makes its simple multi-step JEPA loss novel.
The V2.12 claim should remain an empirical test of policy-mixture outcome
targets with exact legal max/min, and must beat matched value/state controls to
support even that narrow claim. Before method freeze, a versioned design review
could assess a diagnostic comparing same-root legal alternatives only when
their exact-rule consequences differ, and pairing latent separation with
exact-state, value, and ranking differences. Distinct legal actions need not
map to distinct latents; latent distance alone is not evidence of useful
sensitivity. See the updated [prior-art crosswalk](docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md).

The latest primary-source pass found the author-released 2026
[WorldModel-ConnectX](https://github.com/alextitonis/WorldModel-ConnectX) and
the 2025 [SOLIS chess study](https://arxiv.org/abs/2506.04892). ConnectX
directly overlaps the adversarial board-game setting with a learned latent
model and search, but its deployed minimax uses exact board rules and learned
value leaves; its latent beam is a separate baseline, and training folds one
fixed opponent response into each action transition. It has no EMA-target
JEPA loss. SOLIS is value-aligned latent chess planning without learned
transition dynamics. These results remove setting-level novelty claims and
raise the remaining bar to a matched empirical effect of the specific V2.12
objective. The sources and their limitations are recorded in
`docs/RELATED_WORK.md`; no spec, data, compute, or training gate changes.

## Research objective

Falsifiable hypothesis: an EMA-target JEPA that predicts future latent states conditioned on both players' ordered actions can improve planning under a fixed compute budget over matched non-JEPA baselines, with the benefit retained across a declared family of deterministic, alternating-turn, fully observed, finite-action, zero-sum games. Current evidence does not support this hypothesis. The immediate aim is to determine whether there is a defensible mechanism worth testing, not to tune until a development win appears.

Keep distinct: (a) behavioral prediction for a particular opponent, (b) worst-case optimal-reply modeling, (c) minimax/equilibrium search, and (d) expectation under an uncalibrated policy distribution. Current V2.8/V2.9 is (b)+(c), a depth-two max-min cutoff with a learned leaf evaluator. It is not (a), a full equilibrium solver, or exploitability evaluation.

## Workstreams and gates

| Order | Workstream and deliverable | Acceptance criteria | Relative effort / dependency |
| --- | --- | --- | --- |
| 0 | Provenance and durable memory: `GROUND_TRUTH.md`, Obsidian mirror, Git inventory | Ground Truth states repo/data/results truth; Markdown mirror hash-verified; only `main`; no unknown files overwritten | Small; continuous |
| 1 | Research positioning: `docs/RELATED_WORK.md`, primary-source search log | Cover JEPA/world models, game planning, board-game transfer, objective/gradient routing; describe search limits; make no unsupported novelty claim | Medium; ongoing |
| 2 | Method diagnosis V2.10: frozen gradient-alignment diagnostic spec and implementation | Decomposed loss gradients sum numerically to the existing total; diagnostics report cosine/norm/interference by shared encoder, game and seed on train-only batches; no optimizer update and no locked data access | Medium; depends on V2.9 negative result and new code review |
| 3 | Mechanism decision gate | Proceed only if negative JEPA-vs-task gradient alignment is stable across seeds/batches and is concentrated in shared parameters; otherwise reject gradient-conflict explanation and choose a different hypothesis | Small; depends on workstream 2 |
| 4 | Bounded development experiment, only if gate 3 passes | Compare raw reply-JEPA, predeclared encoder-only conflict-projected JEPA, task-value dynamics and direct leaf; same data, initialization, updates, compute/search, held-out development situations, seeds and rules; independent pre-fit review | Large; new grant, protocol, power/compute check and run artifacts required |
| 5 | Model selection and locked confirmatory evaluation | Separate untouched data/situations, independent schedule, predeclared primary regret/strength metric, practical margin, power, multiplicity, censoring and stop rule; no reuse for tuning | Large; only after development nomination and review |
| 6 | Generalization and paper package | Test held-out variants and multiple admitted games, strength/search costs, representation diagnostics, robustness, negative results, data/license statements, reproducibility and threat-to-validity | Large; after method survives confirmation |

## V2.9 disposition

The frozen three-epoch recipe failed its nomination screen. Under the shared two-ply max-min planner, the JEPA-minus-task-value mean paired score was -0.1375 on Connect4-6x7, +0.0125 on Reversi6, and -0.0625 macro over 20 checkpoint-seed clusters. The artifact has 160 complete paired blocks/320 games, no forfeits/censors, balanced JEPA seat swaps, and schedule-order/replay integrity checks. The outcome starts from fixed standard initial states; uncertainty intervals are exploratory and conditional on scheduled seeds. The JEPA/task-value planner CPU ratios were 1.025 and 1.005. Thus greater search CPU does not explain the result. This is evidence against the tested recipe, not proof against JEPA generally. Stop duration-only tuning.

The machine-readable analysis is `docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json`; raw fit/match/checkpoint artifacts remain ignored. The result is development evidence, not confirmatory inference.

## V2.10 candidate: diagnose before intervening

Candidate mechanism: the model's shared encoder receives gradients from legal-policy/value targets and from reply-set latent prediction. If the latter repeatedly conflicts with decision-task gradients, it may impair minimax-relevant value features despite good latent prediction. First compute gradients independently on the exact same train-only batches, decomposed into policy, root-value, observed-leaf-value, reply-JEPA, and latent-regularizer terms. Do not read historical `train_metrics`/loss curves or locked V08 records. This diagnostic makes no optimizer update and selects no model.

If and only if that predeclared diagnostic gate passes, a subsequent version may apply conflict projection only to the JEPA gradient on shared online-encoder parameters, leaving its predictor-specific gradient intact. The update rule, thresholds, hyperparameters, sample, seeds, and controls must be frozen before any fit. Compare at least raw JEPA, routed JEPA, task-value-dynamics, and direct leaf, on a fresh development schedule and with equal measured training/search budgets. This family is not claimed novel: PCGrad/CAGrad and gradient routing in JEPA Policy are prior art. Any defensible contribution would have to be a demonstrated, reproducible incremental benefit in the explicitly zero-sum reply-set setting and survive strong matched controls.

The diagnostic validated decomposition against the existing summed gradient (real-batch maximum relative error 5.15e-18), used frozen train-only inputs and model/panel hashes, and sampled all 20 seeds × two games × ten disjoint batches of 30 roots. All 400 cells were present with zero invalid/skipped roots and finite values. The frozen gate required, in both games, a seed-level median cosine below -0.05, a 95% seed-cluster interval wholly below zero, and at least 15/20 seeds with conflicts in at least six of ten batches. It failed every criterion: Connect4 median -0.0293, CI [-0.0483, 0.1560], 13/20 persistent-conflict seeds; Reversi6 median -0.0402, CI [-0.0651, 0.1064], 12/20. The correct decision is `stop_gradient_conflict_candidate`; do not fit a projected variant or search for post-hoc subgroups. Full outputs are in [the diagnostic artifact](docs/validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json), independently audited in [the review note](docs/V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md).

The next low-cost model-selection test is frozen in `docs/METHOD_V211_JEPA_WEIGHT_CALIBRATION.md` and `docs/validation/V211_JEPA_WEIGHT_CALIBRATION_V01.json`. It raises only reply-JEPA coefficient from 1.0 to 8.0. At coefficient 1.0, the diagnostic's median encoder-gradient norm ratios `||g_JEPA|| / ||g_task||` were 0.04937 in Connect4 and 0.04550 in Reversi6; the angle screen found no persistent conflict. Scaling by eight is a calibration hypothesis, not evidence of improved play. V2.11 precommits 20 same-seed fits and 240 fresh paired blocks/480 games, comparing the candidate to same-seed λ=1 JEPA, task-value-dynamics, and direct-leaf V2.9 controls. It preserves the +0.05 per-game and macro development nomination margin and V2.9 compute caps. Independent review accepted the protocol/schedule (no P1/P2; implementation requirements P3) and verified the schedule hash `c6574b28767dc29e80c3bfd2ad158c58528561a8dc2c5393c86d54534f33bc2e`. The implementation review found two P2s: whole-receipt JSON parsing and a forgeable supervisor token. Both are corrected by hash-only receipt verification without parsing history, a Job Object membership check, and a hash-bound supervisor status attestation. Four focused tests and a 60-control weights-only validation pass after the changes; the independent final re-review is pending. No V2.11 fit or match has started.

This coefficient adjustment is ordinary objective-weight calibration, not a unique method contribution. Minimax-critical reply weighting remains an alternative only after more review: opponent-conditioned latent planning already appears in two-player MuZero and [Vector Quantized Models for Planning](https://proceedings.mlr.press/v139/ozair21a.html); value-sensitive model fitting and latent value alignment are established in [VaGraM](https://openreview.net/forum?id=4-D6CZkRXxI), [Value-Aligned World Models](https://proceedings.mlr.press/v306/jiang26ai.html), and policy-aware simulator learning. Any later variant must beat equally decision-aware non-JEPA controls and establish its specific incremental difference. No current method is certified novel.

## Kill criteria

- Stop active-superiority claims if a predeclared development candidate does not beat both task-value and direct-leaf at the chosen practical margin in every primary game, or if the effect depends on one seed, one game, extra compute, or post-hoc exclusions.
- Stop gradient-routing work if the diagnosis fails its frozen gate, or if projection does not improve the primary decision metric at equal compute.
- Narrow to a benchmark/methodological negative-result paper if no JEPA-specific mechanism survives matched controls and independent replication.
- Stop/pivot if exact search dominates under the relevant budget, legal/rule/data audit fails, held-out evaluation leaks, or a data license is unclear.
- Do not claim generic two-player coverage: hidden information, simultaneous actions, chance, general-sum utility, behavioral opponent forecasting, and equilibrium/exploitability guarantees need separate methods and evaluations.

## Data, compute, and reproducibility gates

Only locally generated, audited development data with clear provenance is currently used. Do not use third-party data until primary-source license/terms, training rights, redistribution and derivative-output rights are documented. Each manifest must pin SHA-256, parser/rules version, counts, provenance, split, and trajectory/event grouping. Keep raw data, checkpoints, caches, and logs outside Git and the Obsidian mirror. No paid compute or service without explicit authorization.

Before a training panel, freeze the objective, config, data fingerprint, exact split, seed schedule, schedule hash, compute caps, failure/censor policy and source commit; run the locked environment tests and independent review. A development result can nominate a model-selection study only. Confirmatory data stays unopened until all choices are frozen.

## Current status and professor-facing claim

The implementation and evaluation harness can test a narrow JEPA hypothesis, but current measured results do not show JEPA superiority. V2.9 is a negative/mixed development result; V2.10 rejects the gradient-conflict explanation for the tested checkpoints and train-root distribution. The V2.11 λ=8 calibration protocol, fit runner, matcher, and analysis are independently reviewed with no remaining P1/P2/P3 blockers. The first supervisor process disappeared without terminal status and is preserved; dev02 then failed before the fit loop because grant v01 no longer matched the method-note hash. Grant v02 is separately issued and loader-validated on all 1,797 DEV09 train records. Under grant v02, the dev03 fit panel completed all 20 seeds (3 epochs/87 updates) in 582.14 seconds with an attested resource gate and peak working set 859 MB. The 20 candidates and 60 V2.9 controls pass local hash/runtime/weights-only verification; independent panel review is pending. The frozen 480-game development match has not started, so there is still no JEPA strength result. The 9/9 protocol suite, compile, control preflight, and pre-fit runtime checks pass. Loss-weight calibration is not a novelty claim. No cross-game transfer, equilibrium, exploitability, or Q1-readiness claim is established.

## V2.11 execution status update (2026-10-02)

The dev03 panel is complete and independently accepted for the frozen exploratory matcher (no P1/P2 findings). Local verification on the exact fit runtime passed the grant v02, supervisor attestation, all 20 JEPA candidates, and all 60 V2.9 controls without reading training histories or locked-final data. Next: run the predeclared 240-block/480-game DEV09 development match with that runtime, then independently audit transcript integrity and evaluate nomination gates. A pass only nominates later locked confirmation; a failure remains a reportable negative result. No outcome or superiority claim is available yet.

## V2.11 result and V2.12 research gate (2026-10-02)

V2.11 dev03 is complete and independently audited. The frozen λ=8 candidate failed nomination: its equal-weight macro score differences were −0.04375 vs λ=1 reply-JEPA, −0.0500 vs task-value dynamics, and −0.0375 vs direct-leaf. Reversi was negative against every control; all 95% seed-cluster intervals span zero. All compute screens passed, with 240/240 paired blocks, 480 games, no forfeits/censors, and transcript/rule replay plus analysis recomputation independently verified. This is evidence against the calibration recipe only. **Stop λ-only tuning.** See `docs/V211_DEVELOPMENT_RESULT_REVIEW_01.md` and `docs/validation/V211_DEVELOPMENT_MATCH_ANALYSIS_DEV03.json`.

The candidate direction is now multi-step alternating-player latent rollout JEPA: test whether recursive action-conditioned prediction improves horizon-dependent minimax decision quality over the current single-pair predictor, matched task-value dynamics, and direct-leaf controls. The 2026 preprint *One-Step Next-Latent Prediction Is Not a World Model* strengthens the motivation to measure open-loop rollout stability, while established JEPA-WM, MuZero, value-alignment, and policy-aware minimax methods create high novelty risk. This is a research hypothesis only. Do not start coding/training until the V2.12 research gate identifies a precise difference, feasible fixed-compute protocol, and valid train-only trajectory targets. First perform a no-training feasibility and prior-art audit; then freeze the method and independent pre-fit review. See `docs/V212_RESEARCH_GATE.md` and `docs/RELATED_WORK.md`.

| Next gate | Deliverable | Acceptance / kill criterion | Effort |
| --- | --- | --- | --- |
| 1 | Complete V2.12 related-work and adapter/data feasibility audit | Cover closest multistep JEPA-WM, MuZero, value-aligned/policy-aware learning; demonstrate legal variable-horizon target construction and resource feasibility without training | Small/medium |
| 2 | Freeze `METHOD_SPEC_V212.md` and exact panel protocol, conditional on gate 1 | Define role-aware recursive transition, masked multistep loss, candidate and matched controls, runtime/data fingerprints, held-out variant and locked split; independent review accepts before fitting | Medium |
| 3 | Train/match bounded development panel | Equal seeds, examples, training compute and planner budget; complete transcripts; report open-loop latent error, minimax rank/regret, strength by game/opponent, inference cost; no locked data | Large |
| 4 | Nomination and independent result audit | Continue only if candidate passes all-control per-game/macro margin, compute, uncertainty and held-out-variant gates; otherwise preserve negative result and kill this objective | Medium/large |
| 5 | Locked confirmation and multi-game transfer, conditional on nomination | Predeclare primary metric/power/multiplicity/censoring/stopping; independent data/situations; no tuning after unlock | Large |

V2.12 progress: the no-training adapter audit passed for 8×8 Connect Four and Reversi (feature/action dimensions, legal transitions, role alternation, 8-ply samples, and 24 full random episodes each; Reversi forced passes included). `METHOD_SPEC_V212.md` v01 now defines the candidate recursive action-conditioned 1/2/4-ply latent objective and four-ply max-min planner. Independent method/protocol review is the current gate. Passing this review will permit implementation work only; trajectory audit, resource pilot, and a separate pre-fit review are still required before training. No training, outcome data, or V2.12 performance result exists.

Current evidence remains insufficient for a Q1-ready performance claim. The best professor-facing description is a rigorously audited negative development result for two JEPA training recipes (V2.9 and the V2.11 λ increase), plus a tested reproducible benchmark harness; the latter still needs broader games and independent replication before it is a paper contribution.

## V2.12 current gate (2026-10-02)

`METHOD_SPEC_V212.md` v02 is a candidate protocol, not an implementation or fit authorization. It closes reviewer questions about utility perspective, baseline definitions, objective weights, and development-versus-confirmatory claims. The corrected no-training depth-four pilot exceeds the provisional 2-second Reversi8 move cap (rule-only p90 6.037s over 16 roots, before model calls); Connect Four 8x8 p90 is 0.350s over 13 roots. The limited sample diagnoses a compute mismatch but does not estimate worst-case or all-root feasibility. A representative random-weight model-call pilot is still required. Do not fit while the fixed common compute budget is unverified. Revise only from no-outcome measurements, then obtain independent review.

| Gate | Deliverable | Acceptance / kill criterion | Effort |
| --- | --- | --- | --- |
| 1 | Reproducible limited unpruned depth-four rules pilot, all variants | Source hash matches output; disclose sampled-root schedule, wall time and node cap; treat as diagnostic only; no outcome data | Small |
| 2 | Revise compute cap from no-outcome evidence, then random-weight all-arm inference pilot | Freeze an incomplete-depth fallback and common node cap; pilot every game/variant/arm with full call/node/memory/wall accounting; no outcome-based cap changes | Medium |
| 3 | Independent review of v04 method/compute/sampling manifest | No unresolved P1/P2 protocol blockers; review is not fit authorization until fresh data/split audits pass | Medium |
| 4 | Adapter/data audit and reproducible trajectory pipeline | Replay, role/action, terminal-mask, deduplication, grouped split and leakage checks pass before any fit | Medium/large |
| 5 | Separate pre-fit grant and bounded development experiment | Exact method/source/config/data/runtime/schedule hashes, reviewed resources, model-selection only; all controls pass or objective is killed | Large |

The development sample count (20 model seeds and at least 40 paired situations
per held-out variant) is an exploratory nomination screen, not a power claim.
V2.12 method draft v03 adds a precise interpretation of policy-mixture outcome
values, sequential trajectory targets, crossed-bootstrap familywise intervals,
Holm tests, and measured training-FLOP gates. It awaits independent review and
is not a training grant. V2.12 keeps high novelty risk: multi-step JEPA-WM,
value-aligned world models, policy-aware simulator learning, regret-guided
board-game search control, and learned planning across board games are
established prior art. The incremental effect of latent matching remains
untested. See `docs/RELATED_WORK.md`, including the ICLR 2026 RGSC update.

Checkpoint update: v04 freezes the balanced two-game window bank (928 per
game), shared per-seed minibatch schedule (87 updates across three epochs), and
correct search-node-visit terminology in the rule-only audit. Related-work
positioning is aligned with the outcome-mixture max/min heuristic. The
2.0-second Reversi8 cap remains failed; do not train or match. After independent
acceptance of v04, the narrowly specified no-training, random-weight
instrumentation pilot may begin; objective/training code and fitted experiments
remain gated by novelty, data/split audits, and separate pre-fit review.


### 2026-10-03 targeted related-work update

The ICML 2026 paper [Causal-JEPA](https://proceedings.mlr.press/v306/nam26c.html)
uses object-level latent masking to create counterfactual-like prediction
queries and reports results on reasoning and agent-control tasks. This is
adjacent prior art for structured prediction queries, but it does not establish
coverage of every legal action or exact counterfactual transition in a
zero-sum board game. The current V2.12 counterfactual-support protocol gap
therefore remains open; no method, data, or training gate changes.


### 2026-10-03 root-score semantics audit

A source-level review of the compute-only alpha-beta runner found that it
carries the incumbent root alpha between legal root actions and discards the
per-action score map after selecting a move. Under pruning, some non-selected
root entries can be bounds rather than exact depth-limited values. The
counterfactual-support draft now requires score-status/bound provenance and
prohibits interpreting bounds as point-valued rankings or regret. Exact
all-action ranking would need a separately specified diagnostic and budget.
This is a measurement-contract clarification only: frozen pilot receipts
contain compute counters, not these scores, and no pilot result changes. See
`docs/V212_COUNTERFACTUAL_SUPPORT_PROTOCOL_DRAFT_01.md`; the draft remains
unreviewed and authorizes no model scoring or data generation.


### 2026-10-03 support-count independence clarification

The counterfactual-support draft now defines episode support as distinct
source episode IDs, not statistically independent samples. It requires
separate declared-seed and policy-pair/seat diversity plus duplicate
trajectory/prefix diagnostics, replacing “multiple independent episodes” with
multiple distinct episode IDs. This avoids inflating the evidential meaning of
support counts when policy behavior is deterministic or episode content repeats.
The summaries remain descriptive, with no sufficiency threshold or gate change.


### 2026-10-03 memory-policy correction draft

A consistency check found that compute-budget amendment v05 describes sampled
RSS as a hard process safety stop, while source and host audits show RSS is
sampled/cooperative and the hard-limit mechanism is cgroup `memory.max`.
It also found that `memory.oom.group=0` does not guarantee a same-cgroup
request supervisor survives OOM victim selection. Added
`docs/V212_COMPUTE_BUDGET_AMENDMENT_06_DRAFT.md` to correct these semantics
without changing the proposed numerical caps. It is not independently reviewed
or operational; no pilot or fit is authorized.


### 2026-10-03 cgroup peak interface check

A no-inference probe in a disposable 1.5-GiB lattice scope confirmed
`memory.peak` is exposed, with `memory.max=1610612736`, and the transient
scope was removed. Its 5.5-MB metadata-only reading is not an inference
working-set estimate. v06 still needs independent review, OOM supervision, and
integrated receipt/timing tests before any pilot.


### V2.12 external OOM-observer feasibility probe (2026-10-03)

A fresh 64-MiB no-swap transient systemd **service** touched 128 MiB and was
OOM-killed while its caller remained in the distinct
`flatpak-session-helper.service` cgroup. The service reported
`memory.max=67108864`; `systemd-run --wait --pipe --service-type=exec` returned
nonzero with `Result=oom-kill`, status 9, and 64-MiB peak. The caller captured
the same `Result`, `ExecMainStatus`, and `MemoryPeak` with
`systemctl --user show`, then used `reset-failed`; the unit was removed.
Post-exit cgroup event files were unavailable, so the verified external signal
is systemd unit metadata, not `memory.events`. This is a disposable mechanism
test only; it does not integrate the V2.12 adapter or validate deadlines,
watchdogs, durable receipts, or all OOM cases. Before any pilot, the adapter
still needs a reviewed bounded-service launcher, retained result capture,
receipt persistence, cleanup checks, and separate watchdog/OOM tests. No pilot,
training, data, matches, or outcome evaluation occurred. Amendment v06 and the
1.5-GiB resource proposal remain drafts pending independent review.


### 2026-10-03 action-sensitive world-model prior-art update

A targeted primary-source search added two close arXiv preprints to
`docs/RELATED_WORK.md`: AD-WM (action-recovery regularization plus CEM-facing
counterfactual/elite-regret diagnostics) and ActSWM (multi-step JEPA rollouts,
recorded-versus-zero action contrast, frozen action readout, Minecraft planning,
and offline gameplay action recovery). Both are author-reported preprints and
were not independently reproduced. They do not instantiate exact-rule,
alternating-player, zero-sum max-min board games, but they remove standalone
novelty claims for multi-step JEPA, action sensitivity, counterfactual planning
comparison, or cross-game action recovery.

The research gate now narrows the remaining question to empirical decision
quality for finite-horizon exact-rule max-min search at matched compute. The
v04 training objective only supervises recorded branches; support summaries do
not establish legal-action ranking. Before any fit, a newly versioned and
independently reviewed protocol must decide on an action-sensitive JEPA control
and specify full legal-root scores and bounded-reference decision regret. The
reviewed v04 method is unchanged. No training, match, or gate authorization
follows from this search.


### 2026-10-03 bounded-reference decision-regret design draft

A source audit of two_player/v212_pilot.py confirms the current compute-only
runner carries a root alpha between root actions, discards its temporary score
map after move selection, and does not write action values to receipts. Later
root values can be bounds, and the frozen v02 receipt cannot be reused for
regret. Added docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md
to propose complete per-legal-action full-window scores, bounded-reference
regret, exact/bounded strata, and explicit missing/bound treatment. It also
specifies reference-value leakage limits and synthetic-only implementation
checks. The draft is not frozen or reviewed; reference depth/heuristic, compute
allocation, seat/root weighting, ranking measure, and primary-vs-secondary
status remain open. No code, data, outcomes, or pilot artifacts were changed.


### 2026-10-03 exact-regret oracle source audit

The decision-regret design audit located an existing full-game exact-regret
precedent in two_player/evaluate.py backed by two_player/games.py::exact_value.
That path covers only tiny registered games, uses a two-ply max-min planner,
and reports regret only for a complete decision. The oracle is unbudgeted and
explicitly documented for tiny state spaces. V2.12 instead targets Connect
Four 6x7/8x8 and Reversi6/8; its random-weight runner exposes no root-action
scores, and the inspected runner/game path has no pinned nonterminal bounded
reference heuristic. Exact solved roots and bounded-reference roots must be
kept as distinct strata. Do not run the legacy exact solver over the larger
variants or replace the frozen game scope. Reference configuration and
independent review remain open; this was a static source audit only.


### 2026-10-03 V2.8-to-V2.12 generation compatibility audit

The source audit in docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md
shows that V2.8 provides reusable exact training-size rules and a replayable
full-episode pattern, but cannot directly produce V2.12-compliant data. Its
train policy schedule covers only uniform/tactical opposite-seat pairs, its
selection and locked policies are split-specific, and its materializer emits
H1/H2 after a V2.8 phase cutoff under V2.8 duplicate rules. V2.12 requires a
uniform draw over all 16 ordered policy pairs and H0-H4 windows with H1/H2/H4
targets. The V2.12 auditor remains in-memory only. This is protocol/code
incompatibility, not evidence of insufficient data or leakage; no data was
generated or inspected. A separate reviewed V2.12 generator is required.


### 2026-10-03 behavior-policy semantics and RNG audit

A source-level policy audit was added to
docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md. It records the exact
uniform, tactical, positional, and bounded-search behavior, including the
192-node/depth-four search cap and handcrafted leaf score. These are synthetic
data-generation policies, not expert targets or the V2.12 evaluation oracle.
V2.8's policy-pair mapping is split/episode parity and its action RNG is one
SeedSequence stream; V2.12 requires a separately frozen draw across all 16
ordered seat-policy pairs and an explicit seed contract. No episodes or policy
actions were generated; exact source/config hashes and edge-case tests remain
pre-generation requirements.

A read-only audit found a pinned MIT-licensed Connect Four engine as a
candidate full-game reference for the standard 7x6 training variant only:
[Markus Thill/Connect-Four at commit 2a588445](https://github.com/MarkusThill/Connect-Four/tree/2a58844594ac022846385dd3ddc8bbbf0a26eae5).
Its `getNextVTable` source enumerates legal columns and independently calls a
full-window minimax root after each candidate move; the 100-ply default
exceeds the 42-cell board and opening books can be disabled with a null book.
This is static source evidence only, not an independently checked oracle or
measured runtime. It does not support 8x8 Connect Four or Reversi. Value-sign
normalization, reachability/turn/terminal contracts, correctness, licensing
provenance, and bounded-runtime checks remain open before any use. It does
not authorize scoring or change the research gate; see
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

An exact-oracle literature/source check narrowed, but did not close, the
Connect Four 6x7 reference gap. The MIT-licensed Rust
[connect-four-ai](https://github.com/benjaminrall/connect-four-ai) at pinned
commit `28a112adaf3ff89ee23fb09411fa592b6597010e` provides exact all-playable-
column scores, but they are side-to-move remoteness values and the API has no
call deadline. Its published author benchmark averages 5.09 s on a difficult
opening-position set; that is not a CAISSA measurement. Pascal Pons's
all-action solver is AGPL-3.0-or-later, while a 2025 BDD strong solution
reports 89.6 GB table size, 47 h and 128 GB RAM. No external engine/artifact
was installed, run, or downloaded.

The 10,000 V2.12 planner-node / 5-second request proposal cannot be transferred
to a solver's separate internal node counter or seconds-scale worst-case
search. Exact-root scoring therefore needs its own predeclared value semantics
(root-player W/D/L, with remoteness secondary unless reviewed), compute
allocation, hard worker deadline, and full-action completeness contract. This
is software-source evidence for Connect Four 6x7 only; 8x8 and both Reversi
variants remain without a pinned exact oracle. It changes no method or gate.


### 2026-10-03 Reversi8 weak-solution scope update

Takizawa's 2023 primary-source result weakly solves standard 8x8 Othello
from its initial position as a draw, with a strategy guaranteeing at least a
draw. It does not solve arbitrary reachable positions or provide complete
per-action values for the V2.12 sampled-root schedule. This removes any
assumption that standard Reversi8's opening value is unknown, but does not
close the all-actions regret-reference gate. The modified Edax source is
GPL-3.0 and was not downloaded, run, or integrated. Our Reversi8 rules appear
compatible by static inspection; formal adapter equivalence remains open. No
evaluation or training gate changes. See docs/RELATED_WORK.md and
docs/V212_RESEARCH_GATE.md.


### 2026-10-03 decision-metric JEPA prior-art update

Wang et al. (arXiv:2608.18746v1) introduce Plan-Real/CEM-stage rank
diagnostics and DA-LeWM with inverse-action and demonstration-conditioned
goal-action heads. These results remove standalone novelty claims for
action-conditioned JEPA planning, these auxiliary losses, and generic
candidate-rank metrics. Their single-agent Euclidean-goal CEM robotics tasks
do not test CAISSA's proposed complete legal-action, root-player max/min
regret question; that distinction remains a hypothesis, not established
novelty. A negative result in the paper is also relevant: elite-stage rank
agreement remains near zero or negative for all variants, including DA-LeWM,
despite random-stage gains. The paper is a preprint with one training run per
configuration. Before any fit, independently review whether to add an
inverse-action control and whether logged goal-actions would only encode
behavior imitation. No method/data/training gate changes. See
docs/RELATED_WORK.md, docs/V212_RESEARCH_GATE.md, and the decision-regret
design draft.


### 2026-10-03 candidate inverse-action control design

Added docs/V212_INVERSE_ACTION_CONTROL_DESIGN_01_DRAFT.md for independent
review. V2.12 v04 already conditions its predictor on actions and predicts
recorded root actions; the draft asks whether DA-LeWM-style inference of the
action from adjacent latents adds useful auxiliary pressure. It proposes a
matched factorial across all six existing arms and explicitly treats the
objective as potentially redundant. Logged future actions are not minimax
labels, so a goal-action imitation head is excluded unless separately
justified as behavior modeling. No method amendment, data generation, fitting,
scoring, or gate change is authorized.


### 2026-10-03 LAMIR prior-art update

LAMIR (Kubíček & Lisý, ICLR 2026) learns latent game dynamics and uses
depth-limited CFR+ reasoning in two-player zero-sum imperfect-information
games. Because its formalism can represent sequential games via fictitious
non-acting-player actions, alternating/zero-sum game scope and learned-model
look-ahead cannot stand alone as novelty. CAISSA's possible distinction is
narrower: JEPA-style latent targets in fully observed deterministic games
with known exact rules, tested on legal-action decision regret against
compute-matched controls. This remains unverified and must not be represented
as a new method or JEPA advantage. LAMIR's paper-reported exploitability and
head-to-head results were not reproduced. The v04 scope, method, and all
research gates are unchanged. See docs/RELATED_WORK.md and
docs/V212_RESEARCH_GATE.md.


### 2026-10-03 executable game-model prior art

Code World Models for General Game Playing (ICLR 2026) synthesizes executable
Python game models from rules and sample trajectories and plans with MCTS or
ISMCTS; its 10-game study includes Connect Four. This means broad game-model
plus search and general game-playing scope are established. Its LLM-generated
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

### 2026-10-07 repeated model-preflight scan inventory

Added a bounded source-level inventory of numeric finite-check element
cardinalities and action-validation scan sizes for the repeated
`preflight_batch` call inside one `loss_grad` invocation. In the illustrative
64-row shape this covers 80,640 numeric finite-check inputs and a 16,640-entry
action nonzero scan; comparison-element counts are reported separately. It
does not estimate runtime or FLOPs, cover all validation/indexing/control-flow
work, include the one-time dataset preflight, or aggregate the frozen 20×87
schedule. The source-counter suite passes 58/58; targeted compile and
whitespace checks pass. An approved read-only review confirmed the counts and
requested explicit qualification that malformed inputs can short-circuit the
predicate path. No data or model run occurred; graph freeze remains **NO** and
≤5% compute parity remains **untested and unpassed**.

Local commit `c2d20667824a33b1615662be56ce2a28aa5211f4` records this milestone.
The normal push did not connect: system SSH configuration ownership blocked
the default client, and a read-only `/dev/null` config retry could not resolve
`github.com`. Remote `main` therefore remains unverified and publication is
pending restored network/SSH access; no force push or alternate write path was
used.

### 2026-10-07 V2.12 runtime observation utility

Added a read-only utility that can record the Python/NumPy build and version,
host/platform fields, thread-control environment values, and hashes of
file-backed executable mappings after checking device/inode identity. It
explicitly labels these as observations rather than executed-byte attestation;
active BLAS threadpool state and loaded-page identity remain unproven. It now
removes map-order-dependent digest fields and compares mappings before and
after file hashing using normalized segment ranges, permissions, offsets and
backing identities. This detects observed changes but is not an atomic
snapshot. Three focused tests pass. An in-memory run on Python 3.14.7 / NumPy
2.5.3 observed 36 mapped executable files whose backing-file path/device/inode
hashes matched at read time with matching normalized segment inventories
before/after hashing; its digest recomputed, while its locked-version check was
false. No receipt was persisted. No D03 runtime gate or profile was advanced.

### 2026-10-07 V2.12 static source-operation inventory

Added a deterministic AST inventory for the current model and scratch
optimizer source. It enumerates arithmetic/unary syntax, calls, indexing,
comparisons, and control flow, and binds each report to the source hashes.
There are 829 listed syntax sites in the model, including 37 augmented
assignments, and 135 in the optimizer. Read-only review identified the initial
omission of `AugAssign`, then the missing `Return` and `Raise` control-flow
nodes; the collector and regression now include them. Every site remains
semantically unresolved. A read-only follow-up found no other currently used
arithmetic, indexing, or explicit control-flow syntax class omitted from the
inventory. This remains a review map, not a counter or execution trace. Its
three standard-library tests pass under Python 3.11.17 and 3.14.7.
The locked 3.11.9 / NumPy 2.4.6 runtime is unavailable in the local
interpreters, so the locked NumPy reduction path was not verified. No compute,
data, or fit gate advanced.

Publication: code milestone `c1b503a` is local only. `origin/main` was last
read at `86eb81b` before the ordinary push attempt. The push and a later
read-only verification both stopped because SSH rejected ownership of
`/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf`. No force push or alternate
write path was used; retry normal publication after SSH access is restored.
