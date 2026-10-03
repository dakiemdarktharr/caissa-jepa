# V2.12 random-weight compute pilot v01

Status: completed compute-only instrumentation; independent review is the next
gate. This report covers fresh random initialization only. It does not measure
playing strength, compare outcomes, establish research novelty, or authorize
training or match play.

## Result

The frozen pilot completed all 96 root-arm cells to four search plies without
reaching a safety ceiling. Across the cells, median wall time was 0.0662 s,
nearest-rank p90 was 0.2689 s, and maximum was 0.9901 s. Median search visits
were 685 (p90 1,398; maximum 3,210); median exact rules transitions were 681
(maximum 3,206); median model calls were 1,132 (maximum 9,272). Peak sampled
resident memory was 49,680,384 bytes (47.4 MiB).

| Variant | Cells | Wall p90 | Wall max | Max nodes | Max model calls | Peak sampled RSS |
|---|---:|---:|---:|---:|---:|---:|
| Connect Four 6x7 | 24 | 0.0866 s | 0.0877 s | 1,433 | 3,312 | 43.7 MiB |
| Connect Four 8x8 | 24 | 0.0972 s | 0.1926 s | 2,344 | 6,623 | 43.7 MiB |
| Reversi 6x6 | 24 | 0.1497 s | 0.2156 s | 1,398 | 2,627 | 45.1 MiB |
| Reversi 8x8 | 24 | 0.4505 s | 0.9901 s | 3,210 | 9,272 | 47.4 MiB |

| Inference arm | Cells | Wall p90 | Wall max | Max nodes | Max model calls |
|---|---:|---:|---:|---:|---:|
| Multi-step JEPA | 16 | 0.2690 s | 0.2758 s | 1,433 | 2,534 |
| Single-pair JEPA | 16 | 0.2686 s | 0.2755 s | 1,433 | 2,534 |
| Recursive raw-state dynamics | 16 | 0.4505 s | 0.9607 s | 3,210 | 9,272 |
| Value-only latent rollout | 16 | 0.2684 s | 0.2849 s | 1,433 | 2,534 |
| Direct-leaf value | 16 | 0.2285 s | 0.9901 s | 3,174 | 5,306 |
| Single-horizon JEPA | 16 | 0.2689 s | 0.2749 s | 1,433 | 2,534 |

Differences between arms in these measurements include alpha-beta pruning
effects from arbitrary random values. They are compute observations only and
must not be read as a ranking of model quality or playing strength.

## Scope and limitations

The run used four deterministic synthetic legal roots per variant, at plies
0, 8, 16, and 24, one paired random initialization, fixed legal-action order,
and iterative-deepening alpha-beta through four individual plies. The ceilings
were 500,000 entered nodes, 8 seconds, and 1.5 GiB sampled RSS per root-arm
cell. All cells completed depth four; no ceiling or fallback was exercised.
RSS was sampled before search and every 256 entered nodes, with a final sample.

This small single-machine pilot does not support a universal latency budget,
scaling estimate, or performance comparison. In particular, the fact that the
largest observed time was below one second does not establish that a tighter
common cap will work across later roots, machines, or fitted models. Keep all
arms on a shared budget in any future protocol. Do not revise the budget until
the independent review is complete and a larger no-outcome measurement plan is
versioned and reviewed.

No training data or outcome labels were opened; there were zero optimizer
updates and zero trained checkpoints saved. No game scores, selected actions,
or action values were recorded. The receipt marks locked-final access false.
Raw receipts and the detailed aggregate remain in ignored `chess_data/` and
are not included in Git.

## Reproducibility fingerprints

- Runtime: Python 3.11.9, NumPy 2.4.6, Linux x86_64, 12 reported CPUs.
- Protocol SHA-256: `ef28c734dc8c1352482e44183de6dafee80a0865153a71dbb207a64e8a71fd8e`.
- Pilot module SHA-256: `e08a7bdac8a027a0e48f601ba96b1d8d9fe2a39fbec6ac32b6e13ce517bd3796`.
- Runner SHA-256: `a72a83ee86af4859fda53419f52c31212f416c714f2da69414b433808e4c7710`.
- Rules module SHA-256: `fbdce0893f6dcc76d30b71d4391842abbcd7c15a0d1a9e20c40077457e273d3a`.
- Schedule SHA-256: `8a793e33854f5b53c2b13ce30a28afdac823958183f0ebc3e05d2e632675ba01`.
- Raw receipt SHA-256: `e2505c2d2ab055d586121864071f0177a14e932f352c2cb134348af67f115ff1`.

The receipt verifier passed, the deterministic root schedule was regenerated
and matched. The original v01 module and runner had one extra trailing blank
line; to keep `git diff --check` clean, those whitespace-only bytes were
removed and the summary verifier reconstructs that exact prior EOF byte before
comparing the recorded hashes. The protocol and rules hashes match directly.
No executable source content changed; the v02 implementation is separately
versioned.
The focused harness suite passed (5 tests). The independent `gpt-6-luna/high`
review found no blocker to the next no-training protocol-review step. It
confirmed there is no strength claim or unsupported tighter-cap recommendation.
Its nonblocking hardening suggestion was to make schedule regeneration and
source-hash authentication part of the reusable summary path. The summary
command now performs those checks, and a fresh verified aggregate was
generated. The reviewer accepted the expanded v02 no-training sampling
protocol for implementation; this is not budget adoption or training
authorization.
