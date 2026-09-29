# V2.5 grid05 verified development result

Date: 2026-09-29. This is an adaptive development result on the fixed 209-root
development set. It is not a confirmatory estimate, a held-out transfer result,
or evidence of Q1 readiness by itself.

## Decision

**Not promoted.** The prespecified `raw-tail` candidate failed both the exact
project gate and the hybrid mechanism gate. Do not replace it with an ablation
or describe the grid as demonstrating JEPA superiority.

In the exact-state track, `raw-tail` regret was 0.202446 versus 0.203775 for the
strongest control (`direct`), a descriptive improvement of 0.001329. The
paired-root 95% bootstrap interval was [-0.023899, 0.026938]. It improved
Connect4 4x5 by 0.012461 but regressed Reversi6 by 0.009804; only one of three
seed comparisons favored it. The protocol required at least 0.05 improvement,
positive effects in both games against every control, and at least two favorable
seeds.

In the hybrid latent-planning track, `raw-tail` regret was 0.268340 versus
0.203775 for `direct`, a loss of 0.064565; its paired-root 95% interval for
improvement was [-0.126889, -0.005814]. It also lost to the tuned recurrent
policy/value control (0.250596 regret). The hybrid primary comparator gate
failed.

The mechanism gate failed as well. The `raw-tail` candidate did not improve in
both games and at least two seeds over either `raw-mean` or `raw-scaled`; it
also did not reduce backed-up oracle MSE below the scalar-consistency control
(candidate 0.545679, scalar-tail 0.529363). The modest exact-track point
difference is therefore not a JEPA-tail mechanism result.

## Audit and scope

The strict report and independent audit both returned `not_promoted` and
`verified`, respectively. The audit checked 42/42 cells and checkpoints,
2,016 tensor arrays, 480 replayed plans, 17,556 learned decisions, 836 fixed
control decisions, all 1,002,240 unique-plan group draws and 3,218,558 fork
rows; it found zero failures, censors, collapse events, train/development
overlap or trajectory overlap. The independent audit also verified all 37
runtime sources against launch commit
`f7a90a76c497becaff8356e030ecbef1d114697e`, the source/data/artifact hashes,
and all 192 tensor references from the failed grid04 attempt.

A separate third-party rules audit also passed: 100 seeded trajectories for
each Reversi size4 and6, 4,684 trajectory states and 183,612 state/action
comparisons, plus 392 fixture comparisons; there were zero mismatches. It uses
the upstream MIT implementation at pinned commit
`60b386dd16fb9d753e50736443a600cae24a5170`. This establishes compatibility on
the tested states only. It does not validate minimax labels or playing strength.
See `docs/validation/REVERSI_REFERENCE_AUDIT01.json` and
`docs/THIRD_PARTY_RULES_REFERENCE_PLAN.md`.

Total cell time was 4,899.264 s, wall time 4,909.031 s, process-lifetime peak
RSS 200,802,304 bytes, and local artifacts 180,542,007 bytes. These figures
describe this run, not a comparative compute advantage. The inference protocol
used exact legal trees and terminal overrides, near-terminal full-oracle
endgame positions, two trained games, three fixed seeds, and reused roots.
Its intervals condition on the seeds and do not account for adaptive reuse.
There is no held-out-game, full-game strength, exploitability, or Q1 claim.

## Reproduction and artifacts

Frozen method: `docs/METHOD_V25.md`; runtime repair: `docs/V25_RUNTIME_AMENDMENT.md`.
Strict aggregate report: `chess_data/v25-grid05-report/report.json`.
Independent audit receipt: `chess_data/v25-grid05-independent-audit.json`.
The audit script is `tools/audit_v25_grid.py`. The public aggregate-only report
and figures are derived from the strict report; raw data, checkpoints, caches,
and detailed logs remain local and excluded from Git.

Reproduce from project root with the pinned Python 3.11 environment and one
BLAS/OMP thread:

```powershell
python -B -m two_player_v25r.report chess_data/v25-grid05 chess_data/v25-grid05-report
python -B tools/audit_v25_grid.py chess_data/v25-grid05 chess_data/v22-full-01 chess_data/v22-development-01 chess_data/v25-grid05-independent-audit.json --expected-commit f7a90a76c497becaff8356e030ecbef1d114697e
python -B tools/compact_v25_report.py chess_data/v25-grid05-report/report.json chess_data/v25-grid05-report-public.json
python -B tools/plot_v25_grid.py chess_data/v25-grid05-report-public.json docs/figures/v25-grid05
```

## Decision for follow-up

Close V2.5 as a valid negative development screen, preserving both failed
grid04 and complete grid05 artifacts. Any new method must be a new version with
a frozen specification, a prospective development set or explicitly declared
adaptive reuse, and equally tuned strong non-JEPA controls. The result points
away from treating lower latent error or worst-reply weighting as sufficient:
exact-state encodings matched or slightly outperformed the candidate, while
using the learned latent transition in the planner degraded regret. Before
another broad training grid, identify a testable representation-reuse benefit
that a rule-aware or value-aware control cannot obtain more cheaply. No
selection or locked-final artifact was opened by this evaluation.
