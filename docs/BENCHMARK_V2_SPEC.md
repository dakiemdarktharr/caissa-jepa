# Development benchmark v2 — design freeze before new model scoring

Date: 2026-09-29. Trigger: the fixed v1.2 pilot is nondiscriminating and does not
show a JEPA advantage. User explicitly requested continued autonomous work toward
a credible professor-reviewable research v1. Preserve v1.2; do not reinterpret it.

## Question and scope

First determine whether tiny-game situation banks can meaningfully distinguish
two-ply learned planners from exact terminal rules. This is a **rule/oracle-only
feasibility survey**, not a learned-model experiment or final-test protocol.
No model predictions enter sampling, admission or design choices.

Survey gravity connect-3 4x4 and Reversi4, keeping tic-tac-toe as a correctness
fixture. The first bank uses new generator seed98371 and at most2,000 trajectories
per game, random/immediate-win behavior, with at most8 empty cells and at least5
for the main beyond-depth stratum. Retain whole source trajectory IDs and
symmetry-canonical state keys. At most500 admitted roots per game in this first
resource survey; do not train from an incomplete or failed audit.

## Independent rules and oracle

A separate reviewer implements contiguous-cell bitboard rules and bounded exact
negamax without importing the training adapter or NumPy. Differential tests cover
legal actions, child states, forced passes and terminal utility. Pin source hash,
configuration and version. This improves implementation independence but remains
same-project code, not an external authoritative engine. Third-party confirmation
is still a later gate and must not be claimed.

For a root s, solve each legal action exactly using the reference solver, then
verify adapter legal actions and depth2 leaves. Record solution nodes/cache hits,
wall time and unresolved/censored roots; do not silently label incomplete solves.
Stop a survey at120s per game or500,000 oracle cache states. Preserve failures and
counts. These are feasibility ceilings, not permission for paid compute.

Admission: nonterminal root, at least2 legal actions, at least1 nonterminal
depth2 leaf, and unequal exact action values. Also label a **beyond-depth** stratum
where all depth2 zero-leaf minimax estimates tie although exact action values
differ. Root choices and all exclusion reasons are based only on rules/oracle.
Require at least100 symmetry-unique admitted roots per game, at least50 in the
beyond-depth stratum, before declaring this bank scientifically useful. These
are support floors, not a confirmatory power calculation.

## Leakage and next-method gate

This survey may use previously seen rule states for counting only. Any later
learned evaluation must exclude all v1.2 training context/H1/H2 keys and label
the exposed pilot/transfer domains as development, not untouched final games.
If a new training bank is built, split by trajectory/connected root-target
components before learning and include every actual training/evaluation feature
state in the overlap audit. Counterfactual branches require their own exact
outcome/value provenance; a parent's outcome must not be reused as every
counterfactual child's target.

If the survey passes, freeze a separate method v2 before fitting: compare
trajectory-only predictive training against reply-fork supervision, include
direct policy/value, decoded dynamics, value-only dynamics, an untrained control
and a recurrent multi-step-trained consistency control. Match supervised examples
and report oracle-generation cost separately. No assumption of novel method or
positive gains. If support fails, expand game/board scope with a documented new
version instead of weakening the criterion after viewing learned results.

## Survey amendment 2 — before v2 model fitting

Survey01 is preserved at `chess_data/v2-survey-01/`: connect3 admitted500 roots
but only26 beyond-depth, so FAILED_SUPPORT; Reversi admitted355 roots with351
beyond-depth and passed. No learned model was scored or fitted. Source/reference
hashes and all rejection counts are in its receipt.

Survey02 replaces gravity connect3 4x4 with **gravity connect4 4x5**, keeping
Reversi4. Seed98372, otherwise identical admission rules, support floors,
2,000-trajectory/500-admitted/120-second/500,000-cache limits. This is a prospective
scope expansion motivated by rule-only support failure, not tuning on learned
performance. The new board still fits the common padded action/feature contract;
it is a development game and not a secretly reused transfer test.

## Survey amendment 3 — strict split-support failure, before v2 fitting

Survey02 passes difficulty support but its full root/child/grandchild footprint
ownership analysis leaves only13 Reversi4 validation roots after excluding old
training states. This is a benchmark-size failure, not a model result. Preserve
the bank and counts in `V2_SURVEY_RESULTS.md`.

Survey03 uses connect4 4x5 and **Reversi6x6**, seed98373. Keep the same5..8 empty
cell roots, admission predicates,2,000 trajectories,500 admitted roots and120s/game
limits. Reference version2 generalizes the independently tested bitboard center
initialization to even square boards;6x6 differential tests must pass first.

Cache semantics change prospectively: clear exact cached values between queries
when resident entries reach400,000, maintain the500,000 resident cap, and record
clear count/peak entries separately from cumulative expanded nodes and time.
This bounds memory without treating reused-cache capacity as a scientific sample
limit. No incomplete subtree value may be cached as exact. Timeouts are unresolved
and remain counted. The resulting task remains endgame local planning; increasing
board size does not justify whole-game or held-out-family generalization claims.
