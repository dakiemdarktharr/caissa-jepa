# Independent review and disposition

Reviewer: separate `independent_audit` agent, read-only inspection and independent
in-memory numerical checks. Date: 2026-09-29. This is independent agent review,
not external peer review or a certificate of correctness.

## Repaired before the exploratory pilot

| Finding | Consequence | Disposition |
| --- | --- | --- |
| Equivalent FEN text such as split empty runs had different identity keys | Cross-split state leakage | Canonical parse/serialize before hashing; regression fixture |
| Legacy no-response H4 masked the next own action | Confounded ablation | Preserve own action, mask replies only; incompatible old weights rejected |
| Pinned UCI telemetry described as independent adjudication | Unsupported confirmation claim | Protocol v3 unconditionally blocks pending independent full-history rules replay |
| Mate on the final allowed ply could be truncated | Incorrect censored outcome | Check terminal immediately after applying each move |
| Root neural scoring lacked deadline propagation | Unaccounted search overrun | Forward supported deadline; cooperative limits disclosed |
| Three splits conflicted with selection/final separation | Model-selection leakage risk | Four-stage audit v3, stale plans rejected |
| Git HEAD included in dataset fingerprint | Unrelated doc commit invalidated data | Commit remains provenance, relevant code/data hashes define identity |
| Tiny planner counted neural work as another node at exact cap | Unequal censoring of identical search trees | Transition-only node checks; both baselines complete the 81-node boundary test |
| Pilot cached evaluation data but reloaded training independently | Cross-run version mixing | Freeze expected data/source identity, check each run and final receipt |
| Metrics JSON could tear during resume | Valid checkpoint became unusable | Atomic history write; corrupt/missing history explicitly marked incomplete |
| Timeout only checked at epoch boundary | Long epoch could exceed limit | Cooperative batch checks; partial epoch does not replace committed checkpoint |
| Resume reported only latest runtime as total | Invalid compute comparison | Label attempt-only and resumed status; no resumed compute equivalence |
| H1 hybrid rollout unspecified | Unclear ablation semantics | Declare recurrent two-step H1 inference before fitting |
| Collapse alert did not prevent planning | Violated readiness gate | Preserve representation output and block planning |

Reviewer independently reproduced all-seven-variant directional derivatives over
every parameter tensor with maximum absolute error 5.18e-11, including missing
H2 targets and frozen EMA. Parent tests also check atomic serialization, exact
epoch resume, identity/corruption rejection, masking, search budgets and complete
tic-tac-toe reachable-state agreement with a separate bitboard rules fixture.

## Unresolved scientific limitations

- Exact oracle and adapters share rule code except the independent tic-tac-toe
  fixture. No all-game independent rules implementation or pinned engine teacher.
- Pilot schedule has only two connect3 states and many terminal-resolved branches.
  This diagnostic cannot support a general planning-advantage conclusion.
- Three seeds, tiny games and one held-out size combination do not establish
  family generalization, playing strength, exploitability or opponent robustness.
- `full` and `no-var` may be nearly identical because the variance penalty is
  barely active. Equal results do not prove the regularizer unnecessary.
- Joint training is sample-weighted (183 tic-tac-toe, 300 connect3, 646 Reversi
  records), not balanced per game. Active tensor counts include masked rows and
  are not measured FLOPs. Initial timing overlaps tests and includes tracemalloc.
- Missing controls include a recurrent predictor trained through multiple steps,
  stronger consistency objectives, calibrated opponent models and independent
  engine/reference match evaluation. No claim of faithful SPR/MuZero reproduction.
- Selection/final predictions remain unopened; confirmation and paper-submission
  readiness remain blocked. These are visible roadmap items, not waived findings.

## V2 pre-fit review (supersedes corresponding engineering limitations only)

Separate same-project bitboard rules now cover both v2 games; they are not an
external engine. Complete counterfactual fork labels use each successor's exact
mover-perspective value. All six split intersections were independently rebuilt
with both canonical keys and raw encoded features: zero overlaps. Data tests
cover legal enumeration, terminal masking, unrelated exact-recursion labels,
held-out-first quarantine, tampering and protected split access.

Model reviewer ran11 tests plus306 independent finite-difference checks on17
real TicTacToe forks, maximum absolute error6.69e-10. H2 BPTT, normalization,
EMA stop-gradient, terminal masks and own-action retention were checked.
Evaluator review found no minimax/perspective/pass/node-cap defect; median_std
was added to implement the frozen collapse gate.

Runtime review found missing serialization time on resume, failure rows reported
as completed, and an after-write storage-cap gap. Repairs add an active-attempt
budget journal (unknown interrupted time fails closed), explicit decision/control
status counts and post-write cap checks. Frozen schedule and controls get hashes.
Objective weights remain fixed in the first grid; this is not optimal tuning of
all baseline families. Exact-state gains would support representation utility;
learned latent-planning claims require the separate hybrid evidence. No final
predictions, external publication or positive outcome follow from these tests.
