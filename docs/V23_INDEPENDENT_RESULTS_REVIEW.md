# Independent review of the completed V2.3 training diagnostic

Reviewed 2026-09-29. **Independent artifact audit: verified, errors `[]`.**
All 18 cells completed the frozen training-only protocol. These results support
continued training-value-fit improvement and a capacity response under this
optimizer. They do not establish generalization, playing strength, JEPA
superiority or a promoted research candidate.

## Audit procedure and completeness

The audit ran after fitting stopped, using
`tools/audit_v23_fit.py chess_data/v23-fit-01 chess_data/v22-full-01
chess_data/v23-fit-01-independent-audit.json` with explicit CPython and one
BLAS/OMP thread. It completed in **26.103252 seconds**. It performed no optimizer
updates, model predictions, planning, new oracle queries or protected-artifact
access. The existing artifacts were not edited.

The independent reviewer checked:

- **18 cells**, all three families, both capacities and seeds 17/29/43.
- **17 source files**, matching both current normalized file bytes and Git blobs
  at the frozen launch commit. The audit script is outside that frozen inventory.
- **480 independently reconstructed sampling and augmentation plans**, covering
  4,008,960 replayed fork draws, against all **2,880 epoch receipts**. This includes
  exact label/terminal/horizon counts, not just matching hashes across families.
- **72 checkpoints**, their counters, configurations and identities, and all
  **4,248 tensor arrays**. The nine small-model epoch-40 snapshots exactly match
  the historical Grid03 FULL online/EMA/Adam reference tensors.
- **36,648 saved root records** across snapshots. Trajectories, fork counts,
  missing H2 and terminal/nonterminal strata match a separately enumerated legal
  depth-two closure of the actual standalone training payload. This closes the
  report's limitation of comparing root metadata only between snapshots.
- Complete artifact inventory: no unexpected failure receipts, temporary files,
  missing snapshots or extra cell files. The frozen strict report independently
  returned **`verified_diagnostic`**, verification errors `[]`, candidate `null`.

Each run completed 160 epochs, 10,560 optimizer steps and 1,336,320 fork draws.
Across 18 runs this is **190,080 updates and 24,053,760 training fork draws**.
These are exposure counts, not independent observations.

The training export contains **509 roots, 9,237 unique raw nodes and 6,750
complete forks**. Geometry uses 3,792 Connect4 nodes (321 terminal) and 5,445
Reversi6 nodes (one terminal). The audit opens only this full-label train export;
it does not parse the original combined parent bank.

## Prespecified descriptive findings

S is encoded-value MSE averaged equally over roots with nonterminal targets,
then equally over the two games and H1/H2. The table gives mean S160 across
three seeds and the prespecified median relative improvement from epoch 80 to
160. Lower S is better; larger positive improvement means further training fit.

| Family | Hidden/latent | Mean S160 | Median improvement 80→160 | Frozen progress flag |
| --- | ---: | ---: | ---: | --- |
| Direct | 64/32 | 0.408437 | 13.4833% | Material progress |
| Direct | 128/64 | 0.305494 | 22.2919% | Material progress |
| Value-dynamics | 64/32 | 0.425750 | 12.6114% | Material progress |
| Value-dynamics | 128/64 | 0.328805 | 22.2343% | Material progress |
| Raw-JEPA | 64/32 | 0.436337 | 11.2669% | Material progress |
| Raw-JEPA | 128/64 | 0.339782 | 19.0082% | Material progress |

All six family/capacity groups exceed the frozen 5% median-progress threshold;
all 18 individual seeds also exceed it. At epoch 160, the median relative
small-to-large capacity improvement is **26.0277% for direct**, **23.9354% for
value-dynamics**, and **20.7518% for raw-JEPA**. Each family has three favorable
seeds. All 36 individual game/horizon capacity comparisons are favorable.

The frozen decision branch is therefore: **the training budget may be limiting;
freeze a separate budget decision before another development grid**. The
capacity response also supports comparing any future design with equally
strengthened larger baselines. It does not justify changing promotion gates or
extending training indefinitely.

Training progress is uneven. Reversi6 H2 worsens slightly from epoch 80 to 160
for direct 64/32 seed43, direct 128/64 seed17, value-dynamics 64/32 seed29 and
raw-JEPA 64/32 seed43. These four adverse components remain in the saved report;
pooled progress is not universal component-wise convergence.

Direct has lower mean S160 than raw-JEPA at both capacities. This diagnostic
does not provide a JEPA value-fit win. It also cannot establish that direct has
better planning or generalization: it measures fitting the available training
values, and the objectives include different auxiliary terms.

## Failure and resource accounting

- Failed cells, overrun/censored cells and collapse flags: **zero**.
- Minimum effective rank over all snapshot/game geometry records: **12.827917**.
  Minimum median dimension standard deviation: **0.151240**. Both are above
  their prespecified thresholds, including at initialization.
- Total measured cell work: **1,627.083500 seconds**; individual cells:
  **62.841865–127.133560 seconds**, within the 300-second acceptance limit.
- Aggregate grid artifacts: **142,867,189 bytes**, within 3 GB.
- Reported process peak RSS: **137,879,552 bytes**. This is the training
  process-lifetime Windows peak, not a per-cell allocation or isolated hardware
  benchmark. Training arrays and preparation have different accounting scopes.
- Development, selection and final predictions and new search decisions: **zero**.

The audit itself required no repairs and passed on its first run. A supplementary
arithmetic cross-check initially used exact Python-float equality between saved
S and the report's reaggregated S; that assertion was too strict. Rechecking all
nine median rules with a 1e-12 tolerance passed; the largest discrepancy was
**1.387779e-16**. This is reduction-order rounding, not a changed decision or
artifact. No stored data, checkpoint, metric or audit result was rewritten.

## Reproducibility identities

| Item | Identity |
| --- | --- |
| Frozen code commit | `20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37` |
| Normalized source-inventory digest | `e648907051ae10e5ca379dc891ff2bbe3237cf72106c3171c02bf1617ed62940` |
| Grid ledger SHA-256 | `77f0dd686e820715f4e608176449ad32852d1c2604d0ce556b7edcf2c190a63c` |
| Training dataset fingerprint | `73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18` |
| Training manifest SHA-256 | `a93187a6c66978e0f0a2f1108bc9a50ccdc974c7900ed9cb78cf7e383718c5b5` |
| Training payload SHA-256 | `674ac6003b0f02b7c550a32d01bb58354adcbd3a0695fb493af5f235ec7e4740` |
| Rebuilt root/target signature digest | `4fcea396118f6c123dca377f3b4f1d79209b2f1a072f347995fde84c591170b2` |
| Audit script SHA-256 | `3f93d16e2c9444167813b92d025e63e8d68be799440f3b6dff94e2c548c15b2f` |
| Audit JSON file SHA-256 | `e5f7d6df255699ea0f5684f215546f72dd48368f70e6c4c2ad1c478199ce8ced` |
| Strict report canonical-JSON digest | `1eaa5dfbf020c87f82c60a79792a225950c8c48a362148cfe9eab9f20c356fa2` |

All individual checkpoint/metric hashes, root rows and epoch histories remain in
the ignored local grid. The compact audit JSON retains per-cell snapshot S and
components, replay digests and descriptive decisions. These local artifacts
must remain available for later reproduction; their presence is not implied by
publishing the source repository alone.

This is an independent internal reviewer implementation. It shares the NumPy
RNG and previously audited game adapters; it is not an external rules engine or
external replication. The audit verifies checkpoint integrity and saved-metric
arithmetic, not newly recomputed model predictions. The three earlier negative
development grids remain negative; protected evaluation remains untouched.
