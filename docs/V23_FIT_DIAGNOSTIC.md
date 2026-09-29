# V2.3 training-only diagnostic

Status: **verified_diagnostic**.

No candidate promotion or generalization claim is permitted.

Executed 2026-09-29 at source commit
`20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37`, on the same single-thread CPU
environment. This implements [the frozen diagnostic](METHOD_V23_DIAGNOSTIC.md).
All18 fresh runs completed160 epochs/10,560 updates, with72 saved snapshots.
No development, model-selection or final evaluation was performed.

The main finding is a common budget/capacity effect, not a JEPA win. All six
family/capacity groups still improve training fit from80 to160 epochs. Larger
capacity helps all three families in all three seeds. Direct's mean final S is
0.408437 (small) and0.305494 (large), versus raw JEPA0.436337 and0.339782.
This comparison concerns training value fit, not generalization or policy convergence.
Reversi remains harder to fit: for large raw JEPA, mean H1/H2 encoded-value MSE
is0.561221/0.463107, versus Connect4's0.149358/0.185441. Do not attribute these
differences causally to dynamics from aggregate MSE alone.

![Training fit by game, family and capacity](figures/v23-fit.png)

[Vector PDF](figures/v23-fit.pdf). Thin lines are seeds; bold lines are their
mean. No confidence bands are implied. The report's S gives equal weight to
games and horizons after averaging nonterminal targets within each root.

Artifacts: local `chess_data/v23-fit-01/` and `chess_data/v23-fit-01-report/`.
Public aggregate receipt: [validation/V23_FIT_DIAGNOSTIC.json](validation/V23_FIT_DIAGNOSTIC.json),
SHA-256 `0650c859f4ea35e6c8123a4a873e1fd32ed947a9978c37df8759dad47f662e49`.
Independent review is [V23_INDEPENDENT_RESULTS_REVIEW.md](V23_INDEPENDENT_RESULTS_REVIEW.md).

Total cell work1627.083500s, range62.842–127.134s, lifetime process RSS137,879,552
bytes, outputs142,867,189bytes. Preparation and audit are separate; this is not
a FLOP-matched efficiency comparison. All9 small epoch40 checkpoints exactly
match the frozen historical59-tensor references. Independent audit reconstructed
480 sampling/augmentation plans and verified all2880 epoch records,72 snapshots,
4248 tensor hashes and36,648 per-root metadata records. No errors or collapse;
minimum effective rank12.827917 and minimum median standard deviation0.151240.

The three earlier negative development grids remain negative. A new common
budget decision and frozen controlled experiment are required before further
development scoring. Generic minimum-probe losses are deferred after explicit
counterexamples; the additive-transition ordering restriction is a separate
training-only diagnostic proposal, not evidence of a better replacement.

| Cell | S0 | S40 | S80 | S160 | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct-h64-z32-s17 | 0.798577 | 0.530430 | 0.469161 | 0.399694 | 66.274 |
| direct-h64-z32-s29 | 0.746266 | 0.517151 | 0.472786 | 0.416752 | 62.842 |
| direct-h64-z32-s43 | 0.757147 | 0.519069 | 0.472583 | 0.408863 | 77.883 |
| value-dynamics-h64-z32-s17 | 0.798577 | 0.555571 | 0.486456 | 0.427148 | 71.793 |
| value-dynamics-h64-z32-s29 | 0.746266 | 0.542922 | 0.506717 | 0.430488 | 62.992 |
| value-dynamics-h64-z32-s43 | 0.757147 | 0.531659 | 0.480169 | 0.419613 | 63.965 |
| raw-jepa-h64-z32-s17 | 0.798577 | 0.559466 | 0.486970 | 0.441244 | 66.864 |
| raw-jepa-h64-z32-s29 | 0.746266 | 0.548668 | 0.498363 | 0.434107 | 74.373 |
| raw-jepa-h64-z32-s43 | 0.757147 | 0.538324 | 0.488724 | 0.433660 | 89.180 |
| direct-h128-z64-s17 | 0.776752 | 0.479956 | 0.400695 | 0.311373 | 107.214 |
| direct-h128-z64-s29 | 0.697380 | 0.480856 | 0.386646 | 0.308281 | 109.987 |
| direct-h128-z64-s43 | 0.846760 | 0.477132 | 0.397987 | 0.296828 | 91.934 |
| value-dynamics-h128-z64-s17 | 0.776752 | 0.498434 | 0.417805 | 0.324909 | 108.406 |
| value-dynamics-h128-z64-s29 | 0.697380 | 0.486161 | 0.422267 | 0.343509 | 113.982 |
| value-dynamics-h128-z64-s43 | 0.846760 | 0.496070 | 0.424126 | 0.317997 | 103.501 |
| raw-jepa-h128-z64-s17 | 0.776752 | 0.513139 | 0.431745 | 0.349678 | 127.134 |
| raw-jepa-h128-z64-s29 | 0.697380 | 0.495888 | 0.423947 | 0.346762 | 119.947 |
| raw-jepa-h128-z64-s43 | 0.846760 | 0.496255 | 0.421153 | 0.322905 | 108.814 |

| Family / capacity | Median relative improvement 80→160 | Interpretation |
| --- | ---: | --- |
| direct 64/32 | 0.134833 | still making material fit progress |
| direct 128/64 | 0.222919 | still making material fit progress |
| value-dynamics 64/32 | 0.126114 | still making material fit progress |
| value-dynamics 128/64 | 0.222343 | still making material fit progress |
| raw-jepa 64/32 | 0.112669 | still making material fit progress |
| raw-jepa 128/64 | 0.190082 | still making material fit progress |

| Family | Median relative capacity improvement | Favorable seeds | Material response |
| --- | ---: | ---: | --- |
| direct | 0.260277 | 3/3 | True |
| value-dynamics | 0.239354 | 3/3 | True |
| raw-jepa | 0.207518 | 3/3 | True |

Budget may be limiting; separately freeze a budget decision before another development grid.

All per-seed and per-game/horizon effects are retained in report.json.

- Training fit does not establish generalization, playing strength or JEPA superiority.
- No candidate is promoted; no development, selection or final data is read.
- Capacity changes several components and compute; this is not an isolated encoder intervention.
- A threshold flag is not proof of convergence. No inferential bootstrap is computed.
- Saved diagnostics are checked for integrity and arithmetic, not recomputed model predictions.
