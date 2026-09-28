# V2 rule-only benchmark feasibility

No model checkpoints or predictions are used in these surveys. The frozen
admission rules and successive prospective changes are in `BENCHMARK_V2_SPEC.md`.

| Survey | Game | Admitted roots | Beyond-depth | Seconds | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 01, seed98371 | Connect3 4x4 | 500 | 26 | 1.385 | Failed beyond-depth support |
| 01, seed98371 | Reversi4 | 355 | 351 | 3.039 | Passed difficulty support |
| 02, seed98372 | Connect4 4x5 | 500 | 191 | 2.940 | Passed difficulty support |
| 02, seed98372 | Reversi4 | 356 | 352 | 2.967 | Passed difficulty support |

Support is not split validity. Prospective state/target ownership analysis of
survey02 hashes trajectories70/10/10/10, includes every root/child/grandchild
feature state, and gives final/selection/validation precedence over training.
All validation/selection/final closures overlapping v1.2 training feature states
are excluded. This uses identity and oracle structural data only; no model scores.

| Game | Train | Validation | Selection | Final | Cross-split root exclusions | Old-training root exclusions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Connect4 4x5 | 328 | 69 | 40 | 48 | 15 | 0 |
| Reversi4 | 117 | 13 | 16 | 22 | 118 | 70 |

Therefore Reversi4 is too small for the intended independent comparison despite
passing the first difficulty survey. Do not train and call13 validation roots a
credible second-family study. Expand Reversi to6x6 prospectively, retain exact
reference validation and bound oracle memory/time before freezing method v2.
Connect4 remains unchanged. Root/target audits and teacher cost will be repeated.

Local receipts and immutable root banks: `chess_data/v2-survey-01/` and
`chess_data/v2-survey-02/`. Their manifests contain exact solver/config/source
hashes, exclusions, cache/transition counts and root-bank SHA-256. No artifacts
are uploaded; raw benchmark states remain generated data under existing exclusions.
