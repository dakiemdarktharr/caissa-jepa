# V2.12 prior-art crosswalk — draft 01

**Status: bounded primary-source comparison for design review only.** This is
not a systematic literature review, a novelty finding, a frozen method
specification, or authorization to generate data or fit a model. It compares
the reviewed V2.12-04 candidate and split/schedule draft v05 with selected
closest prior art.

An earlier independent source/code fact-check of the original comparison
found no concrete correction; that check is not design approval or a novelty
determination. The subsequent ConnectX check adds a first-party board-game
prior and an internal README/method wording discrepancy documented below.

## Candidate under review

V2.12 trains a small shared state encoder, EMA target encoder, and action/role-
conditioned latent predictor on recorded Connect Four and Reversi episodes. It
recursively predicts the latent sequence at plies 1, 2, and 4. Its proposed
planner traverses exact legal branches with a fixed four-ply alpha-beta max/min
backup; nonterminal leaves use a value head supervised from the fixed synthetic
policy-mixture outcomes. It is neither a learned opponent-response model nor a
minimax-value or equilibrium estimator. The method remains draft v04 and the
data/split design remains unapproved draft v05; see [the method spec](../METHOD_SPEC_V212.md)
and [the split amendment](METHOD_SPEC_V212_SPLIT_AMENDMENT_DRAFT_V05.md).

## Closest-feature comparison

| Feature | Closest prior art and source evidence | Difference in the V2.12 proposal | Novelty consequence |
| --- | --- | --- | --- |
| Action-conditioned JEPA planning | [V-JEPA 2-AC](https://arxiv.org/abs/2506.09985) post-trains a latent action-conditioned model and plans in a visual robot MPC loop. [PiJEPA](https://arxiv.org/abs/2603.25981) uses an autoregressive multi-step latent MSE objective and policy-guided MPPI over a JEPA model; its full method sections 3.1–3.4 were inspected. | Small symbolic state/action spaces, learned online encoder with EMA target, exact legal transitions and alternating-player max/min rather than image goals, robot actions, or an Octo proposal prior. | JEPA rollouts, action conditioning, and using a planner over predicted latents are established. The domain/planner difference supports a scoped application question, not algorithmic novelty by itself. |
| Recursive multi-step JEPA loss | [Semigroup-JEPA](https://arxiv.org/abs/2609.10464) trains encoder and predictor through recursive discounted latent rollout; [PiJEPA](https://arxiv.org/html/2603.25981v1) explicitly uses autoregressive multi-step latent MSE. | V2.12 uses recorded two-player action sequences, horizons 1/2/4, stop-gradient EMA targets, terminal masks, and shared outcome/policy task losses. | Recursion and multi-step latent matching are not new. The incremental question is whether EMA-target latent matching contributes beyond matched task/value and state-prediction controls in this game setting. |
| Value-aware JEPA planning | [Value-Guided Action Planning with JEPA World Models](https://arxiv.org/abs/2601.00844) shapes embedding distance to approximate a goal-conditioned value and uses MPC. | V2.12's values are rollout-policy terminal-outcome labels and its search uses alternating max/min; they are neither goal-conditioned reaching values nor minimax targets. | Value-structured JEPA planning is established. Preserve the target/solution-concept distinction and do not claim decision-aware representation learning generally as novel. |
| Action-sensitive/control-state JEPA | [H-JEPA](https://arxiv.org/abs/2609.33497) introduces a planner-facing control state and port-inverse consistency; [Delta-JEPA](https://arxiv.org/abs/2606.31232) predicts actions from latent displacement; [WA-JEPA](https://arxiv.org/abs/2608.20974) jointly predicts future scene and action trajectories. | V2.12 uses a small affine predictor conditioned on exact supplied actions and role; it does not use a structured control state, displacement decoder, flow matching, or joint future-action generation. Search enumerates exact legal actions. | These methods establish that JEPA planning designs increasingly target action sensitivity and world/action coupling. V2.12's simpler architecture is not a method contribution by itself; a structured/action-decoding addition needs a new spec and controls. |
| Action-sensitive game JEPA | [ActSWM](https://arxiv.org/abs/2607.26712v2) combines a frozen action readout from latent transitions with rollout-level separation between recorded-action and all-zero-action predictions; it evaluates open-world Minecraft planning and CEM action recovery. | V2.12 also acts in a game, but its games are deterministic, turn-based, two-player, zero-sum board variants with exact legal actions and an alternating max/min planner. It does not specify either ActSWM objective. | ActSWM is the nearest game-domain JEPA prior found so far, though its game is single-agent open-world control. It rules out claims that action-sensitive multi-step JEPA planning in games is new. A diagnostic should compare same-root legal alternatives only when exact-rule consequences differ, and pair latent separation with exact-state, value, and ranking differences. Distinct legal actions need not map to distinct latents; latent distance alone is insufficient. Any method change requires a new spec and review. |
| Learned latent models with adversarial board search | [WorldModel-ConnectX](https://github.com/alextitonis/WorldModel-ConnectX) is an author-released Connect Four system with latent transition/value models and an adversarial search implementation; its actual deployed search uses exact board rules and learned value leaves, while latent beam search is a separate baseline. [SOLIS](https://arxiv.org/abs/2506.04892) uses supervised contrastive, Stockfish-value-aligned embeddings for six-ply latent-guided chess search. | V2.12 uses an EMA target, predicts along separately ordered actions from both players, supervises a policy-mixture terminal outcome, and backs up exact legal branches. ConnectX instead trains transitions with a fixed opponent bundled into each environment step, has no EMA JEPA target, and uses its latent model as a leaf evaluator in deployed exact search; SOLIS learns no transition model. Both are single-board/game studies. | Learned latent models plus adversarial board search and latent-guided board-game planning are no longer defensible as novel settings. Neither source tests V2.12's specific JEPA loss against matched non-JEPA and exact-state controls. Treat only that narrow incremental question as open, with high prior-art risk and no positive outcome evidence. ConnectX's README/result claims are author-reported and were not independently reproduced. |
| Search over opponent actions | [MuZero](https://arxiv.org/html/1911.08265v2) learns action-conditioned latent dynamics and reward/policy/value predictions for tree search; [Vector Quantized Models for Planning](https://proceedings.mlr.press/v139/ozair21a.html) studies chess with opponent response included in a stochastic latent planning formulation. | V2.12 enumerates exact rules-admissible discrete branches and applies finite-horizon alternating max/min; it does not learn transition legality or a stochastic opponent distribution. | Two-player latent planning and planning across board games are strong prior art. Exact-rule minimax with a JEPA loss is a difference in setup, not proof that the JEPA objective is the source of any gain. |
| Decision alignment | [Value-Aligned World Models](https://proceedings.mlr.press/v306/jiang26ai.html), [VaGraM](https://arxiv.org/abs/2204.01464), and [policy-aware simulator learning](https://arxiv.org/abs/2605.29032) establish value-/policy-sensitive dynamics learning outside this exact symbolic-game setting. | Current v04 does not propose regret-weighted or worst-case-weighted JEPA loss; its objective uses fixed horizon weights and its leaf value follows rollout-policy outcomes. | Do not describe fixed horizon weights, policy-mixture values, or max/min search as a new decision-aware JEPA objective. A future reweighting variant needs a new method version and direct decision-aware non-JEPA controls. |

## Defensible empirical question and limits

The narrow falsifiable question is whether latent matching at multiple horizons
improves the frozen paired game-score primary metric, with horizon-wise regret
and ranking as secondary measures, over the specified controls when training
windows, labels, model capacity, updates, exact search, and measured compute are
held constant. The control panel addresses parts of this question,
but no fit or outcome result exists for V2.12, and the operational 5/6-second
budget, production trajectory generator, split/leak audit, 64-slot held-out-root
yield, and all pre-fit reviews remain open.

The remaining differentiating question is **objective and evaluation**, not
the setting or a standalone JEPA mechanism: a Connect Four latent model with
exact-rule adversarial search already exists, while V2.12 proposes EMA-target
matching along separately ordered actions from both players, policy-mixture
outcome labels, a second game, and held-out board sizes. These distinctions
remain untested and are not a novelty finding. A positive result would still
require matched controls and independent review to attribute any gain to
latent matching. If task/value dynamics match
the candidate, or if fixed-compute decision metrics fail their frozen gates,
stop the superiority claim and preserve the negative result. Do not claim first,
novel, general game transfer, equilibrium, exploitability, or Q1 readiness.

## Search coverage

This crosswalk uses selected primary papers and source checks. It includes
full-text or method-section reviews for PiJEPA, Value-Guided Action Planning
with JEPA World Models, H-JEPA, Delta-JEPA, WA-JEPA, ActSWM, Semigroup-JEPA,
and MuZero; source-code review for ConnectX; and the camera-ready SOLIS paper.
It is not a venue-complete search,
forward/backward citation census, or proof that no closer work exists. Re-run a
systematic citation and database search before any submission-level novelty
statement. The current V2.12 gate remains unchanged.
