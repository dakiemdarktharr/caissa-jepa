# V2.12 random-weight compute pilot v02

Status: completed compute-only pilot; independent review of this receipt and
report is the next gate. This run is an inference instrumentation result, not
an evaluation of playing strength, model quality, or research novelty. It does
not adopt a search budget or authorize training or match play.

## Result

All 1,152 root/arm/initialization cells completed four search plies without
reaching the per-cell safety ceilings of 500,000 nodes, 8 seconds, or 1.5 GiB
sampled RSS. The workload used four variants, 16 roots per variant (one
initial-state root and five each at plies 8, 16, and 24), six arms, and three
paired random initializations. The run used one Linux x86_64 host, Python
3.11.9, NumPy 2.4.6, and 12 reported CPUs.

| Measure | p50 nearest rank | p90 | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|
| Wall time | 0.1201 s | 0.7970 s | 1.2668 s | 2.0148 s | 3.7419 s |
| Search-node visits | 754 | 2,411 | 3,257 | 5,809 | 7,224 |
| Exact rules transitions | 750 | 2,407 | 3,253 | 5,805 | 7,220 |
| Model calls | 1,290 | 4,796 | 6,623 | 11,538 | 20,891 |
| Sampled RSS | 43.2 MiB | 47.5 MiB | 47.6 MiB | 47.8 MiB | 47.9 MiB |

Twelve of 1,152 cells exceeded 2 seconds; 46 exceeded 1.5 seconds. Those
cells still completed depth four under the 8-second pilot ceiling. A 2-second
cap therefore would not have completed the measured workload in every cell.
This count is a direct compute observation, not a selected model comparison.

| Variant | Cells | Wall p90 | Wall p99 | Wall max | Max nodes | Max model calls | Max sampled RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Connect Four 6x7 | 288 | 0.0864 s | 0.1158 s | 0.1386 s | 1,790 | 4,395 | 43.0 MiB |
| Connect Four 8x8 | 288 | 0.2183 s | 0.3329 s | 0.4098 s | 2,753 | 6,623 | 43.2 MiB |
| Reversi 6x6 | 288 | 0.2759 s | 0.3992 s | 0.5051 s | 1,435 | 3,784 | 45.2 MiB |
| Reversi 8x8 | 288 | 1.6718 s | 2.7413 s | 3.7419 s | 7,224 | 20,891 | 47.9 MiB |

| Inference arm | Cells | Wall p90 | Wall p99 | Wall max | Max nodes | Max model calls |
|---|---:|---:|---:|---:|---:|---:|
| Multi-step JEPA | 192 | 0.7355 s | 1.8633 s | 1.9599 s | 5,809 | 10,893 |
| Single-pair JEPA | 192 | 0.7190 s | 1.8427 s | 2.2222 s | 5,809 | 10,893 |
| Recursive raw-state dynamics | 192 | 1.0706 s | 2.7413 s | 3.7419 s | 7,224 | 20,891 |
| Value-only latent rollout | 192 | 0.6961 s | 1.8453 s | 2.2246 s | 5,809 | 10,893 |
| Direct-leaf value | 192 | 0.8573 s | 2.1979 s | 2.8462 s | 6,746 | 11,522 |
| Single-horizon JEPA | 192 | 0.6952 s | 1.8363 s | 1.8865 s | 5,809 | 10,893 |

The arm differences are compute observations under arbitrary random values;
alpha-beta pruning changes the visited tree. They do not rank model quality
or playing strength.

## Warm-up accounting

The 18 warm-ups (six arms × three initializations) are separate from the 1,152
measured cells. Their nearest-rank p50/p90/maximum wall time was
0.000076/0.000134/0.000252 seconds; model calls were 3/4/4 and rules
transitions were 1/1/1. Per-module counters and all raw warm-up records are in
the ignored receipt and verified summary.

## Limits and next gate

The expanded sample improves on v01's four roots per variant and one
initialization, but it still uses synthetic legal states and random weights on
one host. It does not establish the runtime of fitted models, universal
worst-case latency, or a common move budget. The Reversi8 maximum rose from
0.9901 seconds in v01 to 3.7419 seconds here as the root and initialization
sample expanded. The 8-second ceiling was not reached; no depth fallback was
exercised. Do not infer a cap from the no-stop result alone. Prepare a
separately versioned common-budget proposal using these no-outcome measurements
and submit it for independent review before any data-fitting work.

No training data or outcome labels were opened; no optimizer update or trained
checkpoint save occurred. No game scores, selected actions, or action values
were recorded; locked-final access was false. Raw receipt and aggregate stay
under ignored `chess_data/` and are excluded from Git.

## Reproducibility fingerprints

- Frozen protocol SHA-256: `8611fedb1610e4a574c4cbe8d21a023a0a3312fdd06a4c6956dcc95ad09fdc93`.
- Pilot module SHA-256: `c81a39abaa53dc38f5bdaaa8dc2e5babe389fcb043222b6d923af1955de4a9b1`.
- Runner SHA-256: `b71f4ef5442d0c4e3d80b61941d1ed102b63a8f156d06a490dcfba19d56d643a`.
- Shared v01 inference module SHA-256: `e08a7bdac8a027a0e48f601ba96b1d8d9fe2a39fbec6ac32b6e13ce517bd3796`.
- Rules module SHA-256: `fbdce0893f6dcc76d30b71d4391842abbcd7c15a0d1a9e20c40077457e273d3a`.
- Schedule SHA-256: `cce5bd7394b16f90f6d142e34d8c72928ff7c966bf40127cced0db3c27040450`.
- Raw receipt SHA-256: `f16cdb8f624e79b32bbef7499a2b772b7bdd3a64097a60cc3b9dbbe631f1df13`.
- Summary script SHA-256: `329dc9cd4bb119dc6e3f9767da47d9a14f0f16ad3e08fea3ef228161abb9cf59`.

The receipt verifier reconstructed the exact 64-root schedule and checked all
1,152 cells, call totals, caps, schemas, warm-ups, guardrails, and source
hashes. The focused test suite passed (9 tests); `py_compile` and
`git diff --check` passed. An independent reviewer must audit this no-outcome
report and receipt before a common-budget amendment is drafted.
