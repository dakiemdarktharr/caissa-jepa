# Corrected K0.1 diagnostic: learned policy on Count Up

**Stage:** exploratory synthetic engineering diagnostic on committed source
`79b09e34dff35f0a76757bd4dd898ed0c7acbd96`; three seeds, no external data,
local CPU only.

This version corrects the original metric: it scores the learned network policy
\(\pi_\theta\) returned by `model.predict` separately from its one-step policy
improvement target \(\pi'\). Both are compared with the exact
backward-induction quantal-response policy. Q MAE is from the learned Q head.
Each seed used 400 phases, 16 online self-play episodes per phase, 800 updates,
batch size 64, latent dimension 8, and \((\alpha,\beta,\lambda)=(0.5,1,e^{-1/8})\).

| Seed | Transitions | CPU s | Learned-policy TV | Learned-policy Brier | Improvement-target TV | Q MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 17 | 31,318 | 2.922 | 0.020999 | 0.000487 | 0.019945 | 0.113751 |
| 29 | 31,256 | 4.484 | 0.028382 | 0.000953 | 0.020272 | 0.058942 |
| 43 | 31,170 | 4.828 | 0.019536 | 0.000592 | 0.016093 | 0.056669 |

The network's learned policy is slightly farther from the exact policy than the
improvement target on all three seeds, which is consistent with incomplete
fitting of \(\pi'\). These errors are small in this seven-state game but do not
estimate playing strength, sample efficiency, transfer, or a JEPA contribution.
They are not a KLENT reproduction: the local affine-tanh learner and tiny
synthetic task differ substantially from the published ResNet and five-game
experiments. No JEPA arm or comparator was trained in this diagnostic.

The full raw, state-level receipt is excluded at
`chess_data/two-player-klent-toy/v28_countup_dev04.json`; SHA-256
`9a942fb98b8dc2c627b27260f70d38ddc0b149bb62e40759acdab314ad538cf8`. The
compact version-controlled receipt is
[`validation/V28_KLENT_COUNTUP_02.json`](validation/V28_KLENT_COUNTUP_02.json).
Source and config hashes are recorded there. The focused 16-test suite and the
full 346-test suite pass after the fitting/provenance repairs. Independent
review is documented in [`KLENT_K0_1_INDEPENDENT_REVIEW.md`](KLENT_K0_1_INDEPENDENT_REVIEW.md).

Next: a model-blind board-game rules/data/runtime/power audit, then a frozen
matched JEPA-versus-direct-policy/Q development protocol. There is still no
evidence that JEPA beats the baseline.
