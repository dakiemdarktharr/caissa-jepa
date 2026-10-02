# V2.12 no-training depth-four compute pilot 01

Date: 2026-10-02. Branch/commit: `main` at
`bf48d5da61683bd949cd9b40b93b585b32d5191d`. Runtime: Python 3.14.3, local
Windows host. This audit makes no optimizer update, loads no checkpoint, reads
no training histories, and accesses no locked-final data.

## Protocol and reproducibility

The ignored script `chess_data/v212_unpruned_budget_audit.py` has SHA-256
`7e6855f0bc70d7107eb97be7e0175a4302efe22d22631a2eb9e0ec95d2dfc067`. It
builds exact 8x8 Connect Four/k4 and Reversi8 adapters, creates random legal
episodes from seeds 66271 through 66274, and measures exhaustive unpruned
four-ply traversal at plies 0, 8, 16 and 24 (when reached). At most 16 roots
per game are sampled. Each root stops at 500,000 materialized search-node
visits, counting the root and terminal leaves. The script does not separately
measure exact transition calls. Reported
p90 uses sorted index `floor(0.9*(n-1))`. Results are in the ignored raw file
`chess_data/v212_unpruned_budget_audit.out`; stderr was empty.

| Variant | Roots | Node min / median / p90 / max | Roots capped | Rule-only wall p90 |
| --- | ---: | ---: | ---: | ---: |
| Connect Four 8x8/k4 | 13 | 2,513 / 4,625 / 4,681 / 4,681 | 0 | 0.350 s |
| Reversi8 | 16 | 317 / 7,463 / 20,465 / 28,009 | 0 | 6.037 s |

The 2-second provisional wall cap is not feasible for this Reversi8
exhaustive-search pilot, even before learned-model calls. This is a small
random-position diagnostic, not a performance benchmark: it has few roots,
no JEPA/control model inference, no trained weights, no alpha-beta pruning,
and no hardware-normalized claim. It only establishes that the current
unpruned procedure cannot support the recorded 2-second gate. The previous
pilot output is invalid as evidence because it did not match the saved source
and the source had a cross-game sampling bug; it is superseded by this run.

## Decision

Do not grant training or run a match. The method and evaluation budget need a
versioned no-outcome revision. A next pilot may use a lower, fixed search-node-visit
budget with a specified incomplete-depth fallback such as iterative deepening
that returns the last fully completed root iteration. It must compare all
arms on common roots, include random-weight model inference and exact node /
model-call / memory / wall accounting, and be independently reviewed before
any fit. The compute cap may change only from these no-outcome measurements.

The existing V2.11 protocol suite still passes 9/9 tests under the same local
Python; this validates that legacy test suite only and is not evidence of
V2.12 feasibility or performance.
