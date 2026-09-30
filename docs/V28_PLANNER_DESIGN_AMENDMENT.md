# V2.8 planner-level amendment

Date: 2026-09-30. Status: proposed design correction, not frozen or implemented.

## Why the proposal changes

The earlier `docs/V28_KLENT_JEPA_COMPARISON_DESIGN.md` primary endpoint was fixed-opponent policy/Q score with JEPA used only as an auxiliary training loss. That can test whether an auxiliary predictive representation changes policy learning, but it does not establish the user's main hypothesis that predicted latent futures improve planning. An independent methods review identified this estimand mismatch. The earlier fixed-opponent learner question remains a secondary mechanism study.

## Planner-level estimand

For a deterministic, alternating, fully observed, two-player zero-sum game, let `s` be a root where player `i` acts, `A(s)` its legal actions, `s_a=T(s,a)`, `B(s_a)` the opponent's legal replies, and `s_{ab}=T(s_a,b)`. The proposed two-ply minimax decision score is

\[
\hat Q_i(s,a)=\min_{b\in B(s_a)} \hat V_i(s_{ab}),\qquad
\hat a=\arg\max_{a\in A(s)} \hat Q_i(s,a).
\]

Terminal branch values use the exact game outcome in player-`i` perspective. For nonterminal `s_{ab}`, the planner uses a learned leaf representation/value. The primary candidate encodes only `s`, predicts the target-encoder latent of each legal two-action branch from `(z(s), a, b, game_id, player_role, horizon=2)`, then scores that predicted latent with the shared value head. The opponent is modeled as a worst-case legal reply in this planner; this is not an opponent behavior model or a policy-mixture expectation. Search is a max-min planner, not an equilibrium solver beyond the declared depth and cutoff.

The primary outcome is exact root minimax regret on a model-blind bank with exact complete action values, reported per root and clustered by trajectory/game/training seed. Win rate against a frozen calibrated opponent suite is secondary and has a distinct fixed-suite interpretation. Root action values, regret, and confidence intervals must remain separate from response prediction and minimax/exploitability claims.

## Fair arms and compute

Every arm receives the same legal rules, root set, own-action/reply closure, terminal labels, seed schedule, cutoff value targets, training examples, optimizer opportunity and planner. Include:

1. Shared KLENT-style direct policy/Q with no learned transition (separate no-search learner diagnostic).
2. Direct encoded-leaf minimax-Q/value, scoring the exact `s_{ab}` representation without predicting a future latent.
3. EMA-target JEPA latent prediction used by the two-ply max-min planner (primary candidate).
4. Matched decoded board/rule-feature dynamics plus the same value head and planner.
5. A recurrent latent dynamics/value/policy control trained with MuZero-style task/value objectives and used by the same planner.
6. JEPA auxiliary trained but disabled at inference, to identify whether any change comes from representation training or actual predictive planning.

All arms must receive equal counterfactual root/reply exposure; extra branches cannot be hidden as free JEPA labels. Report equal-update and measured-compute comparisons, with wall/CPU time, parameter count, transition enumeration, encoder/predictor/value calls, peak memory, and censored roots. Compare under both equal measured inference cost and a predeclared hard budget; count all target generation and training cost on learning-curve axes. If direct baseline or exact rule search is faster and lower-regret, report that result without a JEPA claim.

## Data, model-blind gates, and kill criteria

Use only independently rule-validated game variants and synthetic project-generated trajectories. Split whole trajectories and opponent families before sample expansion. Keep all role swaps, symmetries, raw states, target-latent source states, and every counterfactual branch in a single ownership group; require zero cross-split overlap under both raw and role-/symmetry-normalized hashes. Keep all timeouts in the predeclared quota. The 100 unique-root and 50 beyond-depth counts are only support floors; a paired, clustered model-blind power simulation must select a final schedule before any learned outcomes are viewed.

Reversi4 is only an adapter/splitter fixture because of its small state space and ceiling risk. A harder game must pass an independent rules/runtime audit and support/power gate before it becomes a scientific game. Stop or narrow the claim if exact labels do not cover the frozen diverse root strata, reference matchups saturate, seat effects persist, or the required effect is underpowered. Do not claim JEPA planning superiority unless it improves the predeclared exact-regret endpoint over **both** direct encoded-leaf value and matched non-JEPA latent/task dynamics at the same measured budget. No result from one game or one opponent suite establishes cross-game or worst-case generalization.

## Method identity and prior-art risk

This is a concrete, falsifiable method family, not a novelty certification. Action-conditioned latent dynamics, MuZero planning, minimax value learning, and competitive latent prediction are established. The unresolved increment is whether EMA-target JEPA prediction, trained on complete own-action/opponent-reply counterfactual sets, improves fixed-budget max-min decision regret beyond direct minimax-value and matched task-dynamics controls in the stated game class. The prior-art matrix and independent method review do not yet verify that gap. The method must be frozen only after a new prior-art audit and a model-blind bank/power pre-fit review.
