# V2.2 independent prefit review

Reviewed 2026-09-29 against frozen [METHOD_V22](METHOD_V22.md), before research
fitting. **Data-readiness and implementation review passed.** This permits the
declared development experiment to proceed after source freeze; it is not a
result for JEPA, independent confirmation or external replication.

## Scope and artifact identities

The independent-audit agent read the masked model, runtime, redaction builder,
standalone loader and tests. A separate read-only calculation compared the real
redacted artifacts against the original parent **training split only**, then
checked the standalone development footprint and its existing frozen schedule.
No oracle solving, neural predictions, research fitting or protected-set scoring
was performed. No frozen implementation files were edited by this review.

Parent dataset fingerprint:
`3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.

| Standalone artifact | Dataset fingerprint | Data bytes SHA-256 |
| --- | --- | --- |
| chess_data/v22-scarce-01 | `dc81db9ab2d67d2905156fb328fe80369eb76bb4d5b140ebe041e68a578ebfab` | `86873ff7b85b0c26dd90011ffeb19244647b5dc2e5e0a2ffe54145209ce1052d` |
| chess_data/v22-full-01 | `73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18` | `674ac6003b0f02b7c550a32d01bb58354adcbd3a0695fb493af5f235ec7e4740` |
| chess_data/v22-development-01 | `bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617` | `d6ba8f69a67934b0b54eeeaed3aa56a6a2f33c00a305c87f9636ca84ddcda8b4` |

Scarce canonical label-mask hash:
`0c735117a0a8fac8ed20b894fb77c75cab75edfb3aad7e149f9f28602278b84f`.

Full canonical label-mask hash:
`037843d4eecc4eccb78cdbf8d0e8dd6c9d3a078c2faebc7b02d819ba862ac5cb`.

Pinned data implementation SHA-256:
`9483e5066e9b20ddb30b93650c30bd0eac6fda44a31be3614705e4c475122cf6`.

Pinned method SHA-256:
`322239a442fd75c5c96982dce4ac1e6e34652f425ad3e3eca552a0f265ed1028`.

All artifact byte/source/fingerprint checks passed. Each manifest retains the
same passed parent audit and fingerprint, preserving the original split-audit
binding. The inherited original oracle costs remain disclosed.

## Independent real-data findings

Both training arms contain exactly **509 roots, 9,237 node records and 6,750
complete legal forks**. The root and fork lists are identical across fractions,
including ordering. A one-to-one correspondence with parent training roots was
verified using game, trajectory and state. Every root identifier was independently
recomputed from those fields only. Replacing each parent root identifier with
its new identifier reproduces the complete fork list exactly.

Every known value/policy target was checked against its parent training target;
all match exactly. The full arm preserves every parent's value and optimal-action
list. Unknown nonterminal values are zero and policies are empty with false
availability masks. **5,437 hidden node records whose true parent value was
nonzero** were verified as actually redacted, so the check does not merely pass
on naturally drawn states. Root, node and fork field inventories match strict
allowlists. Serialized scarce training data contains no original label-derived
root identifiers, root oracle values, action-value arrays, beyond-depth flags,
or other audited label-derived root fields.

Root selection was independently recomputed by sorting the frozen
SHA256 JSON digest of [271828, game, trajectory, state], taking the declared
ceiling fraction per game. The review rebuilt the canonical closure of selected
roots, then checked availability at every state occurrence, including symmetry
and role aliases. Its independently reconstructed mask hash matches the manifest.

| Game | Selected / all roots | Known unique nonterminal value/policy states | Unknown unique nonterminal states | Free unique terminal states |
| --- | ---: | ---: | --- | ---: |
| connect4-4x5 | 62/248 | 848 | 2620/3468 (75.5479%) | 321 |
| reversi6 | 66/261 | 1386 | 4058/5444 (74.5408%) | 1 |

Both games exceed the required **50% unknown nonterminal-state** floor. These
are measured state counts, not an assumption that selecting 25% of roots gives
exactly 25% state-label availability. Terminal utility is available from the rules
and counted separately. The full arm has zero unknown nonterminal states.

Scarce-arm counts by horizon, before repeated epoch sampling:

| Game | Horizon | Valid occurrences | Known value occurrences | Known policy occurrences | Unique unknown nonterminal states | Unique free terminal states |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| connect4-4x5 | 0 | 2746 | 657 | 657 | 186 | 0 |
| connect4-4x5 | 1 | 2746 | 718 | 646 | 605 | 72 |
| connect4-4x5 | 2 | 2674 | 840 | 591 | 1832 | 249 |
| reversi6 | 0 | 4004 | 1011 | 1011 | 195 | 0 |
| reversi6 | 1 | 4004 | 1011 | 1011 | 871 | 0 |
| reversi6 | 2 | 4004 | 1012 | 1011 | 2992 | 1 |

Occurrence counts include repeated root/child positions across forks. Unique
horizon counts are not necessarily disjoint and must not be summed as if they
were independent observations.

All recorded fork transitions were independently replayed against the game
adapter. Missing H2 occurs only after a terminal H1. The standalone development
artifact contains **209 roots, 3,756 nodes and 2,735 forks**. Its ordered
game/root/trajectory inventory matches the previously frozen development-control
receipt. The canonical intersection of new training and standalone development
features is **zero**. Protected-split exclusions remain inherited from the
unchanged passed parent audit; this review did not reopen or score those splits.

## Model and runtime review

The model's encoded CE/value terms use available-label denominators; hidden
placeholders never become supervised targets. Per-horizon oracle-value losses
use that successor's label availability and mover perspective. Raw latent and
reconstruction targets remain available on all real successors. The EMA-value
control has its own detached EMA encoder and value head, using pseudo-values
only on genuinely unlabeled successors, with separate labeled/unlabeled mean
denominators as declared. No full-label teacher checkpoint is imported.

The model tests verify full-label EMA-value/value-dynamics online-update
equivalence, frozen-target gradients, recurrent H2 paths, zero-label behavior,
terminal masks, reply-only action ablation, checkpoint identity and atomicity.
The review found no blocking implementation defect. The combined model/runtime
suite passed **19 tests** (14 model, 5 independently authored runtime tests).

Runtime tests used mocked optimizer/scoring boundaries, not research fitting.
They verified the complete 72-cell grid, correct scarce/full batch routing,
identical observed transition exposure and augmentation plans across fractions,
unchanged label masks under augmentation, zero hidden targets at the optimizer
boundary, source/parent/fraction/seed/exposure mismatch rejection, cross-mask
checkpoint rejection, and interrupted/exhausted resume-budget rejection.
The runtime accepts scarce, full and standalone-development paths, with no
parent dataset argument.

Redaction tests passed **8 tests**, including standalone loads with the parent
loader forcibly disabled. An additional independent synthetic case selected
one of two symmetry-equivalent roots in each game: canonical closure revelation
made every nonterminal state known, and the audit correctly failed readiness
for both games. Thus the gate was checked on both passing and failing inputs.

The separate game/evaluation reviewer reported no blocking report defect. One
nonblocking hardening item remains: the report trusts ledger root counts and
the development fingerprint rather than embedding and reconstructing the full
development manifest. The actual 509/209 root inventories, development schedule
and artifact fingerprints were independently verified above for this grid;
that factual check must not be generalized to unreviewed future artifacts.
The coordinator additionally reported the complete regression suite passing
186 tests in 120.105 seconds before source freeze.

## Research limits retained before fitting

This is simulated label access on an already fully solved, oracle-admitted
bank. The trainer-facing redaction does not undo the cost or information used
to acquire that bank. No actual oracle-compute or data-acquisition saving can
be claimed. All methods share the observed transitions and augmentation, while
decoded and EMA-value provide strong controls for unlabeled transition learning.

The primary scarce-arm mask is fixed once; reported seed/root intervals will
condition on that single mask. The full arm is sensitivity analysis at learning
rates selected using the scarce arm, not an alternative primary result.
The 209 development roots have been exposed in earlier cycles, so any future
apparent gain remains adaptive until separately frozen replication and protected
evaluation. Passing readiness supplies no evidence that the JEPA hypothesis is
true and does not relax the frozen promotion margin or per-game requirements.
