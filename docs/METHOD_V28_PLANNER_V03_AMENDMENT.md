# Method V2.8-P v0.3 amendment: counter semantics and return indexing

**Status: frozen implementation-contract amendment; no learned model or result.** Read with `METHOD_V28_PLANNER_V01.md` and `METHOD_V28_PLANNER_V02_AMENDMENT.md`. This resolves the independent implementation review before any counter is used to claim compute fairness.

## Planner contract and branch counters

The `GameSpec` interface includes `validate(state)`; the planner rejects terminal roots and relies on the adapter for legal actions, transitions, and absolute-player terminal utility. Nonterminal states with no legal actions are invalid unless the adapter represents a forced pass as a legal action.

`PlanResult` reports `root_actions_evaluated` as the number of legal root actions; `immediate_terminal_actions` is the subset that ends the game after the root action. `reply_branches_evaluated` counts all enumerated legal replies under nonterminal root-action successors. It is partitioned into `terminal_reply_branches` and `nonterminal_leaf_evaluations`, so these two counts sum to reply branches. `nonterminal_leaf_evaluations` is also exactly the number of learned scorer calls. Report the fields separately; never add subset counters to their totals.

## Exact terminal indexing for training returns

For nonterminal state `s_t` with player `p_t`, let transition reward be zero on every nonterminal move. If action `a_t` reaches terminal state `s_{t+1}`, define `G_t = p_t * u(s_{t+1})` directly; there is no terminal value prediction or fitted successor action. Otherwise the successor is a nonterminal state with `p_{t+1}=-p_t`, and the side-to-move return recursion is

```text
G_t^(lambda) = -(1-lambda) * V(s_{t+1}) - lambda * G_{t+1}^(lambda)
```

where `V(s_{t+1})` and `G_{t+1}` are both in the successor side-to-move perspective. The Q target for the observed action is `Q_target(s_t,a_t)=G_t^(lambda)`; equivalently, for a nonterminal successor it is `-[(1-lambda)V(s_{t+1})+lambda G_{t+1}]`, while for an immediate terminal successor it is `p_t*u(s_{t+1})`. Terminal labels use absolute `+1` utility. These equations assume zero intermediate rewards and gamma one; if a game has nonzero intermediate reward, it is outside the current spec until separately defined.

## Verification scope

The focused planner tests cover immediate terminal root actions, terminal reply win/loss, both player perspectives, a draw, forced Reversi pass, bounded latent values, and the counter partition. The model-blind gate tests cover deterministic scheduling, padded-vs-contiguous action IDs, depth-two immediate wins, and differential legality/transitions against the independent project reference. These are engineering contract tests, not evidence of game strength, dataset validity, or JEPA superiority. The prior v0.1 sentence claiming forced-pass unit coverage is only satisfied after this amendment and its current test suite.
