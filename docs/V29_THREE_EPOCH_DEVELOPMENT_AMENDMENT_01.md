# V2.9 three-epoch development amendment 01

Date: 2026-10-02
Status: pre-outcome, bounded development-only probe.

## Question and controlled change

V2.8's 60 one-epoch fits completed only 29 optimizer updates per checkpoint.
The JEPA arm did not show an observed advantage over task-value-dynamics in
either game, while its macro estimate was negative. A limited alternative
explanation is insufficient optimization. This amendment tests that explanation
by changing **only the shared training duration from one to three epochs** for
all three arms and all 20 paired initialization seeds.

The method, architecture, losses, weights, data, train split, initialization
seeds, batch size, learning rate, optimizer, shuffle seed, planner, game rules,
per-move limits, and compared arms remain fixed. V2.8 checkpoints are not warm
starts; every arm is freshly initialized and fitted from the same seed-matched
recipe. The training set remains the same static self-play dataset, so the
additional epochs test optimization exposure, not new-data sample efficiency.

## Scope and authorization

This is development/model-selection only on the audited local DEV09 synthetic
self-play dataset. Read the `train` split only for fitting; validation and
selection remain diagnostic/model-selection splits. Do not inspect or load
locked-final records, V08 match outcomes, or training-loss histories for recipe
selection. Do not use a third-party dataset, paid compute, or external service.
Keep every fit, failure, and match record under a fresh ignored output root.

The frozen panel is `docs/validation/V29_DEV_FIT_PANEL_V01.json`. It contains
60 fits (20 seeds × three arms), each with three epochs and 87 optimizer
updates. The match schedule contains 160 paired blocks / 320 games, with two
seat-swapped games per checkpoint-seed/game/control cell, on Connect4-6x7 and
Reversi6. Its match seeds start at 35,000,000 and its schedule hash is pinned in
the panel specification. This schedule is disjoint from V2.8 development and
the locked V08 schedule. All arms use 2 seconds or 500,000 planner transitions
per move. Record both equal-cap outcomes and realized search/train compute.

## Frozen interpretation and selection rule

The estimand remains paired game score minus 0.5 for fixed checkpoints under
shared two-ply max-min search. The primary development comparator is
task-value-dynamics; direct-exact-leaf is a secondary control. Summarize each
game and an equal-weight two-game mean over the 20 checkpoint seeds. Report
unadjusted seed-cluster intervals conditional on the two scheduled match seeds;
these do not estimate broader situation or match-seed uncertainty. This sample
cannot establish superiority or support a confirmatory p-value.

The three-epoch recipe may be nominated for a separate model-selection study
only if all these development screens pass: (1) JEPA's V2.9 score difference
over task-value-dynamics is at least **+0.05** on each game and in the
equal-weight macro; (2) the V2.9 point estimate improves by at least **+0.05**
over the V2.8 one-epoch estimate on each game; (3) the sum of per-fit wall
seconds in the hash-bound panel ledger (measured around each fit and bound in
the match receipt) for JEPA is at most **3.5×** task-value-dynamics; and (4)
mean measured planner CPU time per game-seat for JEPA is at most **1.25×** task-value-dynamics in
each game. If any screen fails, stop duration-only tuning and preserve the
negative/mixed result. Direct-exact-leaf remains a reported secondary control;
any later confirmatory candidate must beat both primary non-JEPA controls at
the predeclared meaningful margin. These screens nominate a new experiment;
they do not prove superiority. Do not use training losses, validation loss, or
latent prediction error as substitutes for the paired decision metric.

## Stop conditions and next gate

Stop before any fit if the data replay/audit, fresh grant, frozen source hashes,
panel inventory, disjoint schedule, dependency lock, or local resource preflight
fails. Stop the panel on checkpoint/receipt mismatch, nonfinite values, memory
or runtime guard, or locked-final access attempt; preserve the partial root and
use a new one for any retry. Do not exceed local hardware capacity.

Even a positive development result remains exploratory. Before confirmatory
work, create a new preregistration with broader, balanced starting situations,
an independently audited game/rule adapter, meaningful effect margin, power,
multiplicity, stopping/censor policy, and compute-accounting plan; have an
independent reviewer inspect it before any locked evaluation. Do not open V08 in
this amendment.
