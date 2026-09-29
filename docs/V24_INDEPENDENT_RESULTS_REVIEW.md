# Independent V2.4 order-probe results review

2026-09-29. **Audit verified on its first run, errors `[]`.** The frozen
material-obstruction screen fails for both games and both capacities; its
nonterminal sensitivity also fails. This probe does not establish the proposed
material fixed-target additive-order obstruction. A small conservative **lower**
bound does not upper-bound the architecture's actual limitation or prove
additive adequacy.

## Independent verification

`tools/audit_v24_order.py` inspected `chess_data/v24-order-01`, the original
`chess_data/v23-fit-01` checkpoints and the standalone `chess_data/v22-full-01`
training export. It completed in **7.400646 seconds**, without optimizer updates,
new model encodings/predictions, search, labels or protected-artifact access.
All original artifacts and frozen probe source remain unchanged.

The audit verified **23 normalized source files** against both current bytes
and Git blobs at the frozen probe commit, the pinned prerequisite audit, the
training manifest/payload and source grid ledger. All **22 probe output files**
are present and checksum-consistent, with no unexpected temporary/failure files.
All **18 final checkpoints**, **1,062 tensor arrays** and **72 contextual rows**
match their configurations, checkpoint identities and counters (160 epochs,
10,560 updates). These historical training counters are not new probe updates.

An independent implementation reconstructed all legal H1 transitions directly
from training roots, checked their recorded successor identities and terminal
perspective, then enumerated candidate state/action blocks and applied the
prespecified hash ordering and greedy edge-disjoint packing. The entire rebuilt
schedule equals the saved schedule. Selection uses game/root/player/action
identities; neither target values nor checkpoint measurements set its priority.
Terminal metadata only defines the prespecified sensitivity subset.

The frozen pure report validator reproduced all saved report fields and
Markdown. A separate arithmetic implementation recomputed every raw-JEPA/EMA
ratio, median and threshold decision from the saved SSE/bound values. Direct
prediction metrics remain unavailable. All 48 dynamics rows retain zero
predicted-order violations, and both packed bound inequalities per row pass.

## Packing and prespecified screens

| Game | Roots | H1 edges | Eligible root pairs | Candidate blocks | Selected blocks | Edge coverage | All-NT blocks / NT coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Connect4 4×5 | 248 | 876 | 2,825 | 4,001 | 157 | 71.6895% | 111 / 55.2239% |
| Reversi6 | 261 | 1,180 | 2,988 | 4,480 | 201 | 68.1356% | 201 / 68.1356% |

There are **2,056 unique H1 edges and 358 disjoint blocks**. Connect4 blocks
contain respectively 0/1/2/3/4 terminal targets in counts **111/39/7/0/0**;
all 201 Reversi blocks are nonterminal. The nonterminal sensitivity uses the
fixed subset, without repacking. Both coverage thresholds exceed 25%.

The following are ratios, not percentages. The prespecified materiality
threshold is **0.10**. Primary denominators use observed SSE over *all* H1 edges;
nonterminal denominators use *all* nonterminal H1 edges.

| Game / hidden-latent | Primary seed ratios 17 / 29 / 43 | Primary median | NT median | Seeds ≥0.10 | Primary / NT screen |
| --- | --- | ---: | ---: | ---: | --- |
| Connect4 64/32 | 0.000299415 / 0.000325689 / 0.000350797 | 0.000325689 | 0.000243206 | 0/3 | Fail / Fail |
| Connect4 128/64 | 0.000174104 / 0.000142827 / 0.000189833 | 0.000174104 | 0.000119234 | 0/3 | Fail / Fail |
| Reversi6 64/32 | 0.002310940 / 0.001932624 / 0.001771799 | 0.001932624 | 0.001932624 | 0/3 | Fail / Fail |
| Reversi6 128/64 | 0.002786618 / 0.002984068 / 0.002307854 | 0.002786618 | 0.002786618 | 0/3 | Fail / Fail |

All 12 primary seed ratios and all 12 sensitivity ratios are below the
threshold. The negative outcome must remain unchanged: it does not trigger
the proposed architecture comparison through this screen. Any further design
requires a separate rationale and prospective protocol with equally strong
controls. It cannot be justified by calling a conservative lower bound an
estimate of total irreducible error.

## Resources and identities

The completed probe used **12.875268 seconds**, **103,759,872 bytes** of Windows
process-lifetime peak RSS, and **1,889,925 bytes** of output including its journal.
These satisfy the frozen 600-second, 1-GB RSS and 200-MB output limits. Journal
errors, optimizer updates, development/selection/final predictions and new
search decisions are all zero. The RSS measurement is not a per-checkpoint
allocation or an isolated hardware-efficiency result.

| Item | Identity |
| --- | --- |
| Probe commit | `0a7edef6bf5a651c37ca4c23186dbbf472ea2b26` |
| Checkpoint source commit | `20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37` |
| Probe source-inventory digest | `c5fd637a9f9d351d0c0ce3068aea52e603f5d2449ad2e17bc4824ed9bd5b47d1` |
| Journal file SHA-256 | `528c66f0137af1a5eade8694e408ddd6e215fb6dbfae048a9b4871eda3a41e08` |
| Report file SHA-256 | `19523d039427fb4521e69dfe9c65103d24caa29e633515e28ff424820cc4ada4` |
| Schedule file SHA-256 | `c47a5f8ee2a8d95ab435ae0a3575c009a038de5bfc0a1d1022e98249abf5d658` |
| Rebuilt canonical schedule digest | `07bf87c7e9d6e95c399fb5b11a1cc6a4c025ec27ad6ccc5b05596563976ed09a` |
| Training fingerprint | `73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18` |
| Independent audit file SHA-256 | `f6eea8c85ddcabb0c66168c63d0c932f045c82ce92a56afac75f1ca64e552691` |
| Independent audit script SHA-256 | `31dd0f76cc6231ecea1dcf14678484b342595f3d5193a2de9f84c60ef6a8a2a3` |

The compact local receipt is
`chess_data/v24-order-01-independent-audit.json`. This is an independent internal
packing implementation sharing the audited game adapters, not an external
replication. Saved latent SSEs, gap/reversal measurements and bound numerators
were not remeasured by encoding checkpoints; this audit verifies their saved
arithmetic, identities and protocol consistency. The result concerns frozen H1
target coordinates only. It establishes neither H2 behavior, game strength,
generalization nor a JEPA advantage.
