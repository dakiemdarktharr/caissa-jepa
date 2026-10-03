# V2.12 generation-protocol compatibility audit 01

**Status: static, no-training source audit.** No trajectories, labels, outcome
records, or checkpoints were read or generated. This audit checks whether the
current V2.8 episode/window pipeline can serve as the V2.12 generator without
a new versioned protocol.

## Source evidence

The audit inspected V2.8 source blob
[b252c703004f42af1574868e9d8c3fdd9a4b4f02](https://github.com/dakiemdarktharr/caissa-jepa/blob/main/two_player/v28_data.py),
the V2.12 in-memory auditor
[f90dd32ec34794826b702ca1c605b2de04faa685](https://github.com/dakiemdarktharr/caissa-jepa/blob/main/two_player/v212_trajectory_audit.py),
and METHOD_SPEC_V212-04.

| Pipeline property | Current V2.8 behavior | V2.12 requirement | Disposition |
| --- | --- | --- | --- |
| Exact game adapters | V28_GAMES instantiates Connect Four 6x7/k4 and Reversi6, the two V2.12 fit sizes. | Also needs held-out 8x8 adapters for roots, plus exact V2.12 source/rules fingerprints. | Reusable training-size rule code only after separate V2.12 binding; V2.8 protocol does not define held-out generation. |
| Episode/replay | generate_trajectory starts at game.initial(), runs to terminal, records actions/outcome, and replay regenerates the source-policy episode before checking it. | New immutable V2.12 manifest, policy-pair draw, IDs/seeds, exact fingerprints, and episode/window audit. | Exact-play/replay pattern is reusable; generated V2.8 episodes are not implicitly V2.12 data. |
| Policy assignment | _policy_pair assigns only uniform/tactical or tactical/uniform to train/validation by episode parity; selection uses positional/positional; locked-final uses bounded-search/bounded-search. | Each V2.12 episode independently draws both seats uniformly from four pinned policies, requiring all 16 ordered pairs in the declared mixture. | Incompatible distribution and split semantics. V2.8 train covers two of 16 pairs and cannot satisfy the V2.12 mixture. |
| Materialized records | _build_records_unchecked applies a phase cutoff, rejects duplicate symmetry/role trajectories, and emits one-step/two-step fields (next, reply, future2). | V2.12 requires full episode windows up to four plies, targets/masks at H1/H2/H4, explicit H0-H4 state keys, and reviewed duplicate disposition. | Not a V2.12 materializer. Reusing it would omit H4 and inherit an unreviewed sampling/duplicate rule. |
| Protocol identity | DATA_VERSION is v28-procedural-trajectories-v09; dev09-v1 is 48 episodes and has V2.8 split definitions. There is no V2.12 generation protocol ID in this module. | A separately reviewed, immutable V2.12 manifest and fail-closed audit before any generation. | No V2.12 corpus protocol is implemented. |

The V2.12 in-memory auditor can validate caller-supplied complete episodes
and construct H0-H4 windows for synthetic fixtures. Its module docstring
states that it is not a generator, performs no file I/O, and does not import
training code. It does not bridge the protocol mismatch above.

V2.8's bounded-search policy uses a 192-node/depth-four action search and its
handcrafted line score; this is part of that behavior policy's implementation,
not a V2.12 search reference or learned training target. The generation
protocol must hash and describe the exact V2.12 behavior-policy implementation
rather than infer equivalence from policy names. No claim is made that V2.8
source is invalid; it is valid for its own frozen protocol.

## Gate consequence

Do not run the V2.8 generator to fill V2.12 quotas, relabel V2.8 splits,
reinterpret its policy pairs, or reconstruct H4 data and call the result
protocol-compliant. The existing exact rules, replay pattern, and in-memory
auditor may inform a new V2.12 implementation after the allocation matrix,
policy distribution, source-window identity, H0-H4 overlap keys, duplicate
policy, window selection, and insufficient-support failure behavior are frozen
and independently reviewed.

This is a compatibility finding, not evidence of data leakage or an
insufficient 928-window corpus: no corpus was inspected. V2.12 data feasibility
remains unknown. No generation, training, scoring, match, or outcome access is
authorized by this audit.
