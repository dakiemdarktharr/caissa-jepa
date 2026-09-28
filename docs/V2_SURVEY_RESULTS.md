# V2 rule-only benchmark feasibility

No model checkpoints or predictions are used in these surveys. The frozen
admission rules and successive prospective changes are in `BENCHMARK_V2_SPEC.md`.

| Survey | Game | Admitted roots | Beyond-depth | Seconds | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 01, seed98371 | Connect3 4x4 | 500 | 26 | 1.385 | Failed beyond-depth support |
| 01, seed98371 | Reversi4 | 355 | 351 | 3.039 | Passed difficulty support |
| 02, seed98372 | Connect4 4x5 | 500 | 191 | 2.940 | Passed difficulty support |
| 02, seed98372 | Reversi4 | 356 | 352 | 2.967 | Passed difficulty support |
| 03, seed98373 | Connect4 4x5 | 500 | 195 | 3.308 | Passed difficulty support |
| 03, seed98373 | Reversi6 | 500 | 499 | 15.152 | Passed difficulty support |

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

## Survey03 and immutable fork audit

The prospective50/20/15/15 split in METHOD_V2 passes all support gates:

| Game | Train | Development | Selection | Final |
| --- | ---: | ---: | ---: | ---: |
| Connect4 4x5 | 248 | 107 | 59 | 70 |
| Reversi6 | 261 | 102 | 72 | 65 |

Sixteen Connect4 roots were quarantined for cross-split closure overlap. All six
split pairs have zero canonical and raw encoded-feature intersections. All held-out
closures exclude old v1 training. Development contains39 Connect4 and102 Reversi
beyond-depth roots. Selection/final labels are generated for identity/audit only;
no predictions are made on them.

`chess_data/v2-forks-01` contains984 roots,17,612 unique raw state nodes and12,833
complete legal forks. Dataset fingerprint:
`3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
Raw artifact9,889,235 bytes; SHA256
`f09d55886284692b325d6b6109b9116561fa792cfa739b42312f2f24a5f31813`.
Generation took30.981s. Independent exact teacher counted82,614/368,376 expanded
nodes and130,128/427,433 transitions for Connect4/Reversi. This is project-owned
procedural counterfactual data, not human play; public artifact license remains
unassigned and raw data stays excluded from Git/vault.

Bitboard reference is a separate same-project implementation, not third party.
V2 rules passed exhaustive TTT plus generated rectangular/Reversi checks, including
20,268 Reversi6 transitions and51 forced-pass visits. Code source SHA:
`916a08f68cb2be60529b8d134cdea448f2d53aeb24d6ad5bc775699e9918ce9e`.
