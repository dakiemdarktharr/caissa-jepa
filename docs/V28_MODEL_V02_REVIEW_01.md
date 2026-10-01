# V2.8 supervised V02 implementation review

Date: 2026-10-01

Reviewer: independent read-only method/code review using the user-approved
`gpt-6-luna` / `high` configuration.
Scope: `two_player/v28_model.py`, `tests/test_v28_model.py`, and
`docs/METHOD_V28_SUPERVISED_V02_AMENDMENT.md`.

## Finding

The reviewer found no remaining P1 issue in the repaired V02 implementation or
its objective description. The objective documented for V02 matches the code:
legal behavior-action cross-entropy, root side-to-move terminal-outcome MSE,
observed nonterminal H2 outcome MSE, collapse regularization, and a root-balanced
EMA-target reply-set latent loss only for `reply-jepa`. `task-value-dynamics`
retains the predictor and observed H2 value path without latent matching;
`direct-leaf` trains/evaluates exact encoded leaves. V02 is explicitly separate
from frozen V01 and does not claim KLENT policy improvement, lambda returns,
behavioral opponent modelling, minimax guarantees, equilibrium, novelty, or
general JEPA superiority.

The review verified these changes against earlier P1 findings:

- Terminal H2 outcomes are masked from learned H2 value loss and take exact
  utility in the planner. Generated Reversi terminal-H2 examples are tested.
- Observed H1/H2 states and replies are checked against exact transitions.
- Exact terminal scores use `root.player * absolute_terminal_outcome` for
  immediate and H2 terminal branches. Reversi final states exercise win, loss,
  draw, and color-swapped roles. Nonterminal learned branch scores are also
  tested invariant to color/role swap.
- A real forced Reversi pass is tested in both the root-action and opponent
  reply positions of the ordered action pair.
- Finite differences cover every weight and bias tensor across all three model
  arms at nonunit JEPA weight; separate checks cover zero/nonunit JEPA weights,
  shared-loss invariance, and immutability of EMA target arrays during loss
  evaluation.
- Checkpoints require dataset and audit SHA-256 plus train split, and validate
  method/config/code identity, tensor inventory, and tensor checksums.

The reviewer saw one nonblocking P2 gap before the final addition: learned
nonterminal score perspective lacked a color/role-swap assertion. The test
`test_nonterminal_branch_values_are_invariant_to_color_role_swap` now covers
this case. Local verification after the addition passed all 63 V2.8 tests,
including the focused model/evaluator tests. This is engineering and review
evidence only; it is not model training or a strength result.

## Remaining gates

This review signs off only on the implementation/objective consistency listed
above. It does not approve fitting or confirmatory evaluation. Before fitting,
the independent V08 nonlearned complete-game runtime/replay/variance/power gate
must finish within its local CPU cap and the final V02 artifact set must be
frozen. The current full proxy schedule is exploratory and was launched from a
prior runner source snapshot; it is not a JEPA result. Data manifest
`training_approved` remains false. No checkpoint or learned outcome exists.
