# V2.8 independent split and evaluation review

Date: 2026-09-30. Read-only review of the current executable pipeline and V2.8 proposal. The review is a design audit, not an experiment or evidence of JEPA benefit.

## Findings

The comparison and locked evaluation remain proposals. `docs/V28_KLENT_JEPA_COMPARISON_DESIGN.md` is explicitly not frozen; its model-blind data/compute gate has not started. The exhaustive Reversi4 receipt covers rules, legal transitions, and two-ply closure only.

The legacy `two_player/data.py` path is not the V2.8 dataset protocol. It makes random and random-immediate-win trajectories, hashes whole trajectories into splits, and removes canonical context/target overlap. Those are useful protections, but it does not record a diverse opponent source/family bank, and minimum split counts of 16 trajectories/records and 8 two-ply records do not establish power. The old pilot schedule selects up to 24 endgame positions per game (at most four empties); it is too small and easy to distinguish learned policies, and the transfer data used there are exposed. Its zero-regret result cannot become future confirmation. The MARS-JEPA chess confirmatory runner is unrelated to V2.8 and currently reports a missing independent full-history rules validation.

The V2.7 match receipts are feasibility-only. Simple opponents saturate, while the bounded-search pilot has too few unique trajectories and a Reversi seat reversal. These do not calibrate a V2.8 opponent bank.

## Required pre-fit gate

Freeze the trajectory/situation generator, rules/version hashes, opponent policy versions, root predicates, split algorithm, seats, and metric schedule before generating model-facing examples. Split complete trajectories first. Keep role swaps, symmetry transforms, context/target states, and every action/reply counterfactual grouped. Verify **zero** overlap among train, development, model-selection, and locked-final groups using both raw-state and role-/symmetry-normalized keys. If opponent generalization is claimed, also require zero opponent-family overlap between training and the held-out evaluation banks. Count censored/incomplete oracle roots against their declared strata; never drop them after seeing model outcomes.

Use at least 100 symmetry-unique admitted roots per scientific game and at least 50 roots beyond the predeclared search-depth threshold as initial support floors, following `docs/BENCHMARK_V2_SPEC.md`. These are support floors only, not power guarantees. Before fitting, simulate the paired evaluation schedule using frozen, non-learned references and choose the sample size for at least 80% power at family-wise alpha .05 against a predeclared five-percentage-point score difference; this margin is provisional and must be justified as the smallest practically meaningful effect in the paper protocol. Keep training seed, game, root, opponent family, and seat pairing as clusters in uncertainty estimates. If support or power fails, narrow the intended claim or redesign the model-blind schedule before training.

Calibrate random, tactical, frozen-policy, and independent-search strata separately with both player assignments. Reject a suite as nondiscriminating if reference scores saturate or the seat effect is material. Report fixed-suite score/win rate for these matchups; this protocol does not estimate exploitability, equilibrium quality, or response to a named opponent unless those are directly evaluated.

## Decision and next sequence

No V2.8 production data, training, or confirmation are justified yet. Use the already-audited Reversi4 only to test splitter/provenance machinery; its small 4x4 game cannot be a scientific strength result. Then select a less trivial deterministic game variant, pass its independent rules and runtime gate, and produce a model-blind bank/split/power receipt. Only after independent review of that receipt should the frozen KLENT/JEPA/task-prediction/minimax comparison be implemented and fitted. If the complete-set JEPA arm cannot beat both direct policy/Q and matched task prediction at the same measured budget, do not promote a JEPA-superiority claim.

The review was commissioned with the user's approved `gpt-6-luna` / `high` agent configuration. The returned review did not independently report runtime model metadata; this document records the requested configuration, not an external attestation of it.
