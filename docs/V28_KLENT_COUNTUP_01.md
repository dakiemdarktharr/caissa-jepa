# K0.1 baseline convergence check: Count Up

**Stage:** exploratory synthetic implementation validation, run against source
commit `f9ac7f739fda1268515ef7e03652a9e9bc0bae47`.

The clean-room KLENT-style policy/Q loop was trained on a seven-state,
deterministic, alternating zero-sum Count Up game. The reference target is the
exact backward-induction quantal-response fixed point at entropy temperature
\(\alpha=0.5\). Each of three seeds trained for 400 collection/fitting phases,
16 complete self-play episodes per phase, one fit epoch per phase and 800 Adam
updates per seed. The batch size was 64, latent dimension 8, and
\((\alpha,\beta,\lambda)=(0.5,1.0,e^{-1/8})\). The implementation used local
Python 3.11.9 and NumPy 2.4.6 CPU; no outside data or checkpoints were used.

| Seed | Episodes | Transitions | CPU seconds | Improvement-target TV | Improvement-target Brier | Q MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 17 | 6,400 | 31,318 | 2.500 | 0.01995 | 0.000448 | 0.11375 |
| 29 | 6,400 | 31,256 | 3.766 | 0.02027 | 0.000467 | 0.05894 |
| 43 | 6,400 | 31,170 | 3.766 | 0.01609 | 0.000331 | 0.05667 |

**Correction from independent review:** the reported policy metrics above were
computed from the one-step policy-improvement target \(\pi'\), not the learned
network policy \(\pi_\theta\). They are target-construction agreement with the
exact fixed point, not evidence that the network policy converged. The Q MAE is
from the learned Q head. A versioned follow-up probe now scores both
\(\pi_\theta\) and \(\pi'\) separately; the original receipt remains a
historical record.

This validates only target construction and the learned Q head on one
tractable synthetic game. It does not establish learned-policy convergence,
paper-scale fidelity, generalization, board-game strength, or any JEPA benefit.
The independent review also found multi-epoch reuse of stale on-policy targets
and missing replay metadata; these are being repaired before further fitting.
The full raw per-state receipt remains locally at
`chess_data/two-player-klent-toy/v28_countup_dev02.json` and is intentionally
excluded from Git. The compact reproducibility receipt, including source,
configuration and raw-file hashes, is
[`validation/V28_KLENT_COUNTUP_01.json`](validation/V28_KLENT_COUNTUP_01.json).

Next gate: rerun the corrected learned-policy diagnostic after metadata and
single-pass fitting fixes, then complete independent equation/perspective/replay
review and a model-blind coverage/runtime audit before board-game self-play or
fitting any JEPA arm.
