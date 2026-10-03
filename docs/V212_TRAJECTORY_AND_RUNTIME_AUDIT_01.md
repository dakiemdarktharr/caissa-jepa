# V2.12 trajectory and runtime audit 01

**Status: static, no-training source audit; candidate data feasibility is not yet passed.**
This audit read the V2.12 method, the existing V2.8 trajectory generator/auditor,
its active protocol amendment, and the V2.12 compute-budget proposal. It did not
open generated data, inspect training/outcome artifacts, generate or save
trajectories, run an optimizer, or start a match. This is an implementation-gap
assessment, not evidence of leakage or a method failure.

## Finding

The repository has reusable exact-rule and full-episode replay code, but no
V2.12 multi-step window materializer or V2.12 generation protocol. The existing
V2.8 audit cannot certify a V2.12 four-ply window bank: it materializes H1/H2
records, and its overlap-key construction checks observed targets through two
plies plus a two-ply legal-reply closure. Consequently it does not test whether
H3 intermediate context states or H4 target states overlap across split
components. This is a coverage gap in the audit, not proof that the existing
dataset leaks.

## Source audit

| Area | Existing support | V2.12 gap |
| --- | --- | --- |
| Exact trajectory replay | `two_player/v28_data.py::replay` regenerates a declared policy/seed episode, replays each action through exact rules, and checks the terminal label. | V2.12 must bind its own game/rules/code version, policy mixture, seed schedule, and episode identity; dev09's manifest cannot be reused as an implicit V2.12 grant. |
| Model-facing targets | `_build_records_unchecked` validates H1/H2 and emits `next`/`future2`. | V2.12 requires materialized sequence windows through four plies, target horizons 1/2/4, explicit actor roles, and counts for valid/terminal-masked targets at each horizon. |
| Split/leakage checks | The existing pipeline hashes full trajectories and groups several raw/canonical states and legal two-ply branches before assigning components. | Audit identities must cover all V2.12 H0–H4 context/window states and target horizons H1/H2/H4, role/symmetry transform, and episode lineage before window extraction. The current path-target keys stop at H2; the reply closure stops at depth two. |
| Protocol coverage | `GENERATION_PROTOCOLS` contains `unit-diagnostic` and `dev09-v1`; dev09 uses 48 episodes per game/split and splits train/validation/selection. | There is no V2.12 protocol ID or locked-final assignment, no frozen realized policy-by-seat schedule bound to episode IDs/seeds, and no evidence that 928 eligible windows per training game remain after component quarantine. V2.12 evaluation includes held-out board sizes absent from the V2.8 generator; its training sizes match. |
| Fail-closed behavior | Existing manifests keep `training_approved` false and the loader refuses data unless it is explicitly true. | Preserve this guard. A future V2.12 audit pass must not set training approval; only a separate reviewed grant can do that. |
| Runtime budget | V02 measures search-call instrumentation. `two_player/v212_pilot.py::run_root_arm` implements search-local node/deadline stops and retains the last completed iteration, with a first-legal fallback state. | V02 observed no cap stops, and its timing starts inside `run_root_arm`, excluding setup/dispatch. No move-serving adapter verifies the amendment's request-anchored 5-second planner and 6-second response deadlines, pre-search setup/dispatch, returned legal action, or process-forfeit behavior. The proposal is not operational. |

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
6. verifies policy/source/code/rules/config fingerprints and fails closed on a
   mismatch; and
7. verifies the existing search-local stops/fallbacks, then separately measures
   request-to-search setup and fallback/response handling with the same
   request-anchored clock and common caps, using random weights and synthetic
   roots only.

The implemented software-contract check uses a tiny in-memory synthetic fixture
with known legal paths, a forced-pass case, terminal boundaries, deliberate
duplicate windows, and deliberate H4-only cross-split overlap. Each fault is
rejected before model-facing windows are returned. No old labels or locked-final
artifacts were read. Any future corpus feasibility work requires a separate
reviewed generation protocol.

## Decision

V2.12 trajectory generation, four-ply split-leakage validation, and operational
request-to-response timing remain **not audited**. The frozen protocol and
in-memory synthetic auditor pass their focused software-contract tests and were
independently accepted for that synthetic-only scope. This cannot certify corpus
splits or operational timing. Data generation, training, matches, and outcome
access remain gated. The 10,000-node/5-second/6-second limits remain a reviewed
proposal until the full pre-fit gates pass.
