# K0.1 independent implementation review

Date: 2026-09-30. Scope: read-only review of `two_player/klent_baseline.py`,
`two_player/klent_model.py`, the Count Up probe/receipt, and the V2.8 comparison
design. The audit checked published KLENT equations at
https://arxiv.org/html/2602.10894 (Eqs. 2–4, Algorithm 1, Appendices D/F),
adaptation fidelity, perspective/signs, masks, data provenance, and claim
limits. It did not run training or inspect board-game data. The follow-up was
assigned with the user's approved `gpt-6-luna/high` configuration; the returned
review did not independently restate its model metadata.

## Findings

1. **Blocking for interpreting the first Count Up result:** the probe compared
   the one-step improvement target \(\pi'\) against the exact quantal-response
   policy instead of scoring the learned network policy \(\pi_\theta\). The
   old TV/Brier values were target-construction agreement, not learned-policy
   convergence. The learned Q-head MAE was scored correctly. Keep the original
   receipt as historical evidence and use a versioned correction that reports
   both policy quantities separately.
2. **Blocking before multi-epoch use:** `fit_selfplay_batch` reused fixed
   on-policy targets after updating the policy/Q parameters, without an
   off-policy contract. K0.1 now requires exactly one pass through a freshly
   collected batch; a multi-epoch variant would require its own method version.
3. **Blocking before split/persistent dataset audits:** collected trajectories
   lacked stable replay identity, acting-role sequence, rules version and
   behavior-model identity. Collection now records these fields and hashes the
   replay plus model/config provenance.

## Correctness and limitations confirmed

The masked regularized policy-improvement formula, legal-only normalization,
sampled legal-action Q loss, and alternating signed return recurrence are
consistent with the declared zero-sum player-to-move adaptation. The local
affine-tanh network is far smaller than the paper's ResNet and is correctly
described as a KLENT-style clean-room adaptation rather than a KLENT
reproduction. The original exact target is the correct backward-induction
quantal-response fixed point for Count Up. None of this establishes board-game
strength, transfer, a JEPA benefit, or paper-scale efficiency.

## Repair verification state

- One-pass fitting is enforced, with a regression test that rejects `epochs=2`.
- Trajectory records include game/rules, player sequence, parameter/config
  hash, and deterministic replay-derived identity; tests check format, roles,
  and repeatability.
- `tools/v28_klent_countup_probe_v2.py` evaluates learned policy and improvement
  target separately on committed source `79b09e34dff35f0a76757bd4dd898ed0c7acbd96`.
  Its three-seed run found learned-policy TV 0.0195–0.0284, target TV
  0.0161–0.0203, and Q MAE 0.0567–0.1138. The compact receipt is
  `docs/validation/V28_KLENT_COUNTUP_02.json`; the raw state-level receipt is
  excluded under `chess_data/` and hashed there.
- Focused tests pass (16 tests, 0.135 s); the full repository regression passes
  346 tests in 134.030 s after the repairs.
- The model-blind board-game rule/data/runtime/power audit and every JEPA versus
  matched-control comparison remain open.
