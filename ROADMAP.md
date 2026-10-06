Warning: truncated output (original token count: 40773)
Total output lines: 2019

# CAISSA-JEPA research roadmap

Updated: 2026-10-07. This is an adaptive research plan, not a promise of a positive result or Q1 acceptance. `GROUND_TRUTH.md` is the session-entry record.

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

### 2026-10-07 synthetic calibration protocol proposal

Prepared `docs/V212_ROOT_SAMPLING_CALIBRATION_PROTOCOL_DRAFT_01.md` as a
reviewable, unapproved proposal for design-matched synthetic calibration of
the v05 crossed bootstrap. It specifies the ten atomic and five algebraically
derived macro contrasts, a 29-cell null/alternative and yield-stress grid,
outer/inner replication proposals, Monte Carlo uncertainty, candidate
acceptance limits, and stop conditions. The synthetic generator is an
abstract discrete dependence stress model; whether it adequately preserves
the intended shared-arm structure remains under independent review. The
proposed workload is 5.22 billion inner bootstrap replicates at R=18,000, so
feasibility is unproven. The approved static reviewer found the scenario
arithmetic coherent but did not accept the protocol: the contrast-level
copula does not enforce shared-arm/seat-swap dependence. The draft now uses a
dependence-robust union bound for within-scenario FWER/coverage endpoints; an
analytic boundary-rate calculation gives a joint assurance lower limit of
0.8439 across 53 endpoints. Reviewer acceptance of that calculation/target,
adequacy of the abstract generator, and local feasibility remain open. No
simulations, roots, scores, or outcomes were accessed or generated. v04
remains current; calibration, root generation, and downstream gates remain
closed. See the draft protocol and `docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

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
decoder is not an equivalent training path. This fixes the proposed wiring at 18,440 online
parameters while retaining the required 5% training-FLOP gate. It does not
resolve whether that gate is feasible, and independent review has not adopted
the proposal; v04 remains current. No trainer or model operation was run. See
the new wiring amendment and architecture reconciliation drafts.

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
gate changed. Independent static review confirmed the scope …20773 tokens truncated…s, no forfeits/censors, and transcript/rule replay plus analysis recomputation independently verified. This is evidence against the calibration recipe only. **Stop λ-only tuning.** See `docs/V211_DEVELOPMENT_RESULT_REVIEW_01.md` and `docs/validation/V211_DEVELOPMENT_MATCH_ANALYSIS_DEV03.json`.

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
