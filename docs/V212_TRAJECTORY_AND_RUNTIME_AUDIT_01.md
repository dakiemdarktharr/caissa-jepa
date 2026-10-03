# V2.12 trajectory and runtime audit 01

**Status: static, no-training source audit; candidate data feasibility is not yet passed.**
This audit read the V2.12 method, the existing V2.8 trajectory generator/auditor,
its active protocol amendment, and the V2.12 compute-budget proposal. It did not
open generated data, inspect training/outcome artifacts, generate or save
trajectories, run an optimizer, or start a match. This is an implementation-gap
assessment, not evidence of leakage or a method failure.

## Finding

The repository has reusable exact-rule and full-episode replay code, plus a
no-I/O synthetic V2.12 window auditor. Given caller-supplied complete episode
fixtures, `two_player/v212_trajectory_audit.py::audit_trajectories` constructs
H0–H4 windows and terminal masks in memory for software-contract assertions.
This helper is not a seed/policy-bound episode generator, corpus pipeline, or
production materializer; no V2.12 generation protocol exists. The existing V2.8
audit cannot certify a V2.12 four-ply window bank: it materializes H1/H2
records, and its overlap-key construction checks observed targets through two
plies plus a two-ply legal-reply closure. Consequently it does not test whether
H3 intermediate context states or H4 target states overlap across split
components. This is a coverage gap in the audit, not proof that the existing
dataset leaks.

## Source audit

| Area | Existing support | V2.12 gap |
| --- | --- | --- |
| Exact trajectory replay | `two_player/v28_data.py::replay` regenerates a declared policy/seed episode, replays each action through exact rules, and checks the terminal label. | V2.12 must bind its own game/rules/code version, policy mixture, seed schedule, and episode identity; dev09's manifest cannot be reused as an implicit V2.12 grant. |
| Model-facing targets | `_build_records_unchecked` validates H1/H2 and emits `next`/`future2`. The synthetic V2.12 helper constructs H0–H4 windows and terminal masks from supplied episodes. | A production V2.12 pipeline must bind source episodes and materialized sequence windows through four plies, target horizons 1/2/4, explicit actor roles, and valid/terminal-masked counts at each horizon. |
| Split/leakage checks | The existing pipeline hashes full trajectories and groups several raw/canonical states and legal two-ply branches before assigning components. The synthetic helper checks fixture H0–H4 state/window overlap. | A production audit must cover raw, role-normalized, and symmetry-normalized H0–H4 context/window states and H1/H2/H4 targets, plus episode lineage, before extraction. Current V2.8 path-target keys stop at H2; reply closure stops at depth two. |
| Protocol coverage | `GENERATION_PROTOCOLS` contains `unit-diagnostic` and `dev09-v1`; dev09 uses 48 episodes per game/split and splits train/validation/selection. | There is no V2.12 protocol ID or locked-final assignment, no frozen realized policy-by-seat schedule bound to episode IDs/seeds, and no evidence that 928 eligible windows per training game remain after component quarantine. V2.12 evaluation includes held-out board sizes absent from the V2.8 generator; its training sizes match. |
| Fail-closed behavior | Existing manifests keep `training_approved` false and the loader refuses data unless it is explicitly true. | Preserve this guard. A future V2.12 audit pass must not set training approval; only a separate reviewed grant can do that. |
| Runtime budget | V02 measures search-call instrumentation. `two_player/v212_pilot.py::run_root_arm` implements cooperative search-local node/deadline stops and retains the last completed iteration, with a first-legal fallback state. | Its timer starts only after root/cap validation and `model.reset_calls()`. The runner builds the schedule and models and performs warmup before the timed call. RSS is sampled at timer start, every 256 entered nodes, and at return; there is no independent process watchdog. The function returns counters, not a move response. No adapter verifies the amendment's request-anchored 5-second planner or 6-second response deadline, setup/dispatch, returned legal action, or process-forfeit behavior. The proposal is not operational. |

### Runtime timing boundary from source

The V02 runner calls `build_root_schedule_v02()`, instantiates all random
models, performs per-model warmup, and hashes its sources before entering the
cell loop. Inside `run_root_arm`, game/root/cap validation and model counter
reset occur before `time.perf_counter()` starts. Root feature extraction,
encoding, legal-action enumeration, and the search itself are inside that
timer. The deadline is checked cooperatively at search-node entry; RSS is
sampled at timer start, every 256 nodes, and on return. A long single
expansion or a process that stops responding is not independently interrupted
by this function.
After search it returns a diagnostic dictionary; the pilot appends it to the
receipt and writes the file after the full loop. No action is returned through
a serving protocol, and no 6-second request-to-response monitor is present.

These boundaries are appropriate for the reviewed compute-only pilot, but the
measured per-cell `wall_seconds` cannot verify the proposed request-anchored
planner or response deadlines. A future pre-fit adapter audit must start the
clock at request receipt, include dispatch/setup, pass remaining time into
search, enforce a separate response watchdog, validate the emitted legal
action, and account for controlled fallbacks separately from timeouts and
forfeits. It must also state whether RSS overshoot is bounded or sampled-only.

### Follow-on RSS guard-path review (2026-10-03)

A read-only review of `run_root_arm`, the V02 runner, and their focused tests
found an additional reporting/safety gap in the existing pilot code path:

- The initial RSS sample is recorded as `peak_sampled_rss_bytes` but is not
  compared with `rss_cap_bytes`. Later checks occur every 256 entered nodes.
- A periodic over-cap sample raises `PilotBudgetStop` inside the iterative-
  depth `try` and can set `stop_reason="rss_cap"`. After leaving that handler,
  `run_root_arm` unconditionally calls `sample_memory()` again outside the
  handler. If the cap is still exceeded, the exception escapes rather than
  returning the diagnostic row. The V02 runner does not catch it around
  `run_root_arm`, so it exits before writing the aggregate receipt.
- The existing focused pilot tests cover node-cap stopping, but contain no
  RSS-cap entry, periodic, or final-sample cases. There is no process-level
  memory watchdog in this path.

This is a code-path finding, not evidence that the completed V02 cells crossed
the cap: the reviewed receipt reports a maximum sampled RSS of 50,212,864 bytes
against the 1.5 GiB cap. It does mean the Python check is sampled/cooperative,
not a hard memory ceiling, and an actual over-cap run may terminate without an
auditable per-cell stop receipt. Do not edit the hash-bound V02 implementation
in place or rerun its frozen report. A future pilot version needs entry-time
cap handling, a single structured over-cap result or an explicitly fail-stop
receipt, tests for each RSS path, and a separately verified OS/process memory
bound if the cap is to be described as hard. The end-to-end request watchdog
remains a separate requirement.

## Required next no-training work

Before fitting, freeze a V2.12 generation/audit protocol that:

1. assigns whole replay-verified episodes and all connected overlap components
   to splits before deriving any windows;
2. records the ordered state/action/actor sequence and exact transition hashes
   for every materialized four-ply window;
3. checks raw, role-normalized, and symmetry-normalized overlap for every
   H0–H4 context/window state and H1/H2/H4 target across train, development,
   selection, and any separately approved locked split;
4. proves terminal and Reversi forced-pass semantics, and reports per-horizon
   valid/masked counts without replacing missing targets with zeros;
5. reports candidate, duplicate, illegal, terminal-short, quarantined, and
   retained episode/window counts by game, split, policy family, seat, and ply;
6. reports canonical-equivalent within-split window content as a diagnostic
   under draft v05; do not reuse the synthetic auditor's unconditional
   duplicate-window rejection as a production policy without an explicit,
   reviewed reconciliation;
7. verifies policy/source/code/rules/config fingerprints and fails closed on a
   mismatch; and
8. verifies the existing search-local stops/fallbacks, then separately measures
   request-to-search setup and fallback/response handling with the same
   request-anchored clock and common caps, using random weights and synthetic
   roots only; verify watchdog behavior and explicitly bound (or label as
   sampled-only) RSS enforcement.

The implemented software-contract check uses a tiny in-memory synthetic fixture
with known legal paths, a forced-pass case, terminal boundaries, deliberate
duplicate windows, and deliberate H4-only cross-split overlap. These returned
windows exist only for synthetic fixture assertions. The fixture deliberately
rejects duplicate windows; draft v05 instead calls for reporting canonical
equivalent content diagnostically. No old labels or locked-final artifacts were
read. Any future corpus feasibility work requires a separate reviewed
generation protocol and an explicit duplicate-policy reconciliation.

## Request adapter implementation follow-up (2026-10-03)

Added `two_player/v212_request_adapter_v01.py` as a new design-v01 feasibility
adapter; the frozen `v212_pilot.py` and `v212_pilot_v02.py` implementations
were not edited. The adapter starts a monotonic request clock before request
validation and cgroup preflight, passes an absolute request+5-second planner
deadline to a separate worker, and enforces a request+6-second response
deadline in the supervising parent. On timeout it SIGKILLs the worker process
group and records whether the process was reaped. It validates the returned
action against the exact root's legal-action set and returns the last completed
iterative-deepening action, or the first legal action if depth one did not
finish. OOM termination is separated from watchdog timeout using the cgroup
`memory.events` delta.

The public request function has no unbounded-scope override. Parent and worker
both require the exact 1.5 GiB finite `memory.max`, `memory.oom.group=0`, and
matching cgroup paths; they fail closed on mismatch. The response carries the
cgroup path, limit, event delta, request/search timing, and counters. The move
action is transient and excluded from the counters. This adapter has no receipt
writer, score, dataset, optimizer, or training checkpoint.

`tests/test_v212_request_adapter_v01.py` covers cgroup path/limit/group checks,
deadline/fallback logic, response-action validation, worker timeout/kill/reap,
OOM event classification, and counter equivalence with the frozen search.
Together with the symmetry, frozen V02 pilot, and synthetic trajectory-auditor
tests, the focused suite passed 20/20. A no-inference subprocess scope preflight
ran in a real disposable 1.5 GiB scope and verified the spawned preflight worker
had the same cgroup path as its parent, `memory.max=1610612736`, and
`memory.oom.group=0`; the scope was removed afterward. No request/inference
worker ran there. Request orchestration unit tests use a mocked cgroup boundary,
while search equivalence tests use in-memory synthetic roots. This is software
verification only, not an end-to-end runtime measurement.

The adapter has not received independent review and has not been launched as a
pilot. Its per-request fresh model construction, worker startup, actual
six-second wall response, worker behavior under inference load, and receipt/report
integration remain unmeasured. The no-inference subprocess preflight verifies
only cgroup inheritance and does not measure request execution or headroom. No training-data or outcome
artifact was read or created. Do not use the adapter for evaluation until
independent review and a separate no-outcome integration run are accepted.

## Decision

V2.12 trajectory generation and four-ply split-leakage validation remain **not audited**. Request-adapter code and unit tests now exist, but end-to-end request timing remains **not empirically audited**: no worker request was run inside the verified cgroup, and no multi-cell pilot or receipt was produced. Source review and mocked orchestration tests cannot substitute for an integrated no-outcome run. The frozen
protocol and in-memory synthetic auditor pass their focused software-contract
tests and were independently accepted for that synthetic-only scope. This
cannot certify corpus splits or operational timing. Data generation, training,
matches, and outcome access remain gated. The 10,000-node/5-second/6-second
limits remain a reviewed proposal until the full pre-fit gates pass. The
follow-on RSS source check adds a versioned pilot guard/reporting fix and
specific RSS tests to the open work before any future cap-stressed pilot; it
does not invalidate the completed V02 measurements, which stayed well below
the sampled RSS cap.


## Episode origin and full-game provenance audit

The remote helper at `two_player/v212_trajectory_audit.py` validates that
each supplied state has the adapter's shape, replays each supplied action
legally from the preceding supplied state, checks role alternation, and
matches the terminal result. It rejects a terminal first state, but does not
require the first state to equal `game.initial()`; its state validator checks
shape, values, and player sign, not reachability from the standard opening.
The helper therefore proves consistency of the supplied segment, not that it
is a complete game episode with verified seed/policy provenance.

A deterministic in-memory probe used the suffix of an existing five-ply
Connect Four fixture beginning after its first move. The suffix was accepted
as an episode and emitted four windows with `start_ply=0`, although its first
state was not the game's initial state. The focused seven-test
`test_v212_trajectory_audit.py` suite also passed. The probe used only a tiny
rule fixture; no generated corpus, model, training label bank, or match
outcome was accessed.

This is not evidence of a defect in the pure in-memory helper's stated
segment-level contract, and it does not show that any current dataset is
contaminated. It is an integration requirement: before corpus generation,
the production materializer must either enforce the initial-state/full-game
invariant and bind the original episode ID, seed, ordered policy pair, and
source hashes, or use a separately typed segment format with an original-ply
offset and parent-episode provenance. Otherwise a suffix can be renumbered
from ply zero and the whole-episode split/manifest assumptions cannot be
verified by this helper alone. No method or gate is amended by this audit.
