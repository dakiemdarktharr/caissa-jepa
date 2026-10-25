# V2.12 arm architecture and compute reconciliation — draft 01

**Status: static implementation/spec audit only.** This note does not change
METHOD_SPEC_V212-04, select the raw-state control architecture, authorize a
trainer, data generation, fitting, model scoring, or open a gate. No training
or inference was run for this audit.

## Finding

The v04 architecture section defines a latent predictor

```text
F: concat(z[32], onehot(action)[65], role[1], game[6]) -> z_next[32]
```

and §4 describes the recursive raw-state control as a “shared
encoder/predictor trunk and a decoder” that predicts 198-dimensional exact
state features and re-encodes each predicted feature vector. This wording
leaves open whether the raw-state arm is:

1. **latent-then-decode:** apply `F` to obtain `z_next`, decode `z_next` to
   198 features, then re-encode; or
2. **direct action-conditioned decode:** map the concatenated current latent,
   action, role, and game descriptor directly to 198 features, then re-encode,
   with no learned 32-dimensional `F` on that path.

The no-training random-weight compute pilot implements the second path in
`two_player/v212_pilot.py::RandomInferenceModel.advance`: its raw-state arm
uses `decoder_w` with input width 104 and output width 198, applies `tanh`,
then calls the encoder. It allocates `predictor_w` for every arm, but the
raw-state branch does not use that matrix. The exact feature adapter emits
binary channels and descriptor values in `[0,1]`; the pilot's `tanh` output
therefore is not the linear-MSE decoder proposed in the follow-up amendment.
This is an instrumentation proxy, not evidence that the v04 raw-state
training arm has a frozen architecture. No V2.12 trainer or optimizer
implementation is present under `two_player/` in the current checkout.

## Parameter-count consequences

Using the dimensions in METHOD_SPEC_V212-04 and counting matrix weights plus
biases (online trainable parameters only):

| Module | Calculation | Parameters |
| --- | ---: | ---: |
| Encoder | `198*32 + 32` | 6,368 |
| Policy head | `32*65 + 65` | 2,145 |
| Value head | `32*1 + 1` | 33 |
| Shared encoder and task heads | sum above | 8,546 |
| Latent predictor `F` | `104*32 + 32` | 3,360 |
| Direct action-conditioned feature decoder | `104*198 + 198` | 20,790 |
| Latent-state decoder | `32*198 + 198` | 6,534 |

Therefore the second raw-state interpretation has 29,336 online parameters
(shared 8,546 plus direct decoder 20,790). If interpretation 1 includes both
`F` and a latent-state decoder, it has 18,440 (shared 8,546 plus 3,360 plus
6,534). The two readings differ by 10,896 parameters, about 59% of the
latent-then-decode count. These are architecture arithmetic, not measured
training parameters, FLOPs, optimizer memory, or runtime results. EMA target
encoder state is excluded because the raw-arm target path is not specified
consistently enough here to count it by arm.

The pilot's allocated-but-unused raw-arm `predictor_w` adds 3,360 stored
parameters to its Python object but not to the raw-arm executed computation or
effective trainable capacity. A parameter report derived only from that object
would therefore be misleading.

## Fair-comparison implications

The method already requires recording parameter counts and profiling forward
and backward FLOPs on identical dry-run batches, with total training FLOPs
within 5% across all six arms. It has no trainer yet, so this parity condition
has not been demonstrated. Resolve the raw-state wiring before implementing
the trainer or interpreting pilot counters as a faithful arm-level compute
estimate. The implementation contract should also state whether an unused
predictor is absent from the raw arm, merely allocated for shared code, or
part of its computational path; unused allocation must not be reported as
effective capacity or FLOPs.

This finding alone does not prove the six-arm comparisons unfair or
infeasible: the latent predictor, direct leaf, and raw-feature decoder encode
different hypotheses. It identifies an unresolved architectural degree of
freedom that changes capacity and compute, so it must be fixed before the
existing 5% gate can be evaluated. Keep the current objective, arms, and
negative results unchanged until an independently reviewed method amendment
disposes the ambiguity.

## Scope and reproduction

The source reading was limited to the v04 architecture and arm definitions,
the random-weight inference model and its `advance` method, and the tracked
`two_player/` file inventory. Counts above are integer arithmetic from the
stated dimensions; no model was instantiated and no inference, fit, dataset,
root, score, outcome, match, or service was accessed or run. This audit is
not independent review, a FLOP profile, or approval to train.

## Follow-up proposal

`V212_RAW_STATE_ARM_WIRING_AMENDMENT_DRAFT_01.md` now proposes the
latent-then-decode interpretation: use the shared 104-to-32 action-conditioned
predictor, decode its output through a 32-to-198 feature head, and re-encode
predicted features for recurrence. It specifies masks and initialization
pairing, gives the resulting 18,440 online-parameter count, and preserves the
existing 5% FLOP-parity gate. That proposal has not been independently
reviewed or adopted; v04 remains unchanged. It specifies a linear feature
decoder because exact adapter features include 0/1 targets; the pilot's
bounded `tanh` output is not treated as an equivalent training objective.

## Follow-up static dense-forward MAC inventory (2026-10-07)

Added `tools/v212_arm_dense_forward_macs_audit.py` to count only dense
matrix multiply-accumulates implied by v04 and the unadopted latent-then-decode
proposal, per fully valid nonterminal four-ply window with 1/2/4 targets. The
first published inventory undercounted recursion by omitting transition 3,
which is needed to construct horizon 4. After independent review, the audit
and regression expectations now count four predictor calls and, for the
proposed raw-state graph, four 32-to-198 decoder calls plus four online
198-to-32 re-encodes. Corrected counts are 40,864 MACs for multi-step JEPA;
72,544 for recursive raw-state (+77.53%); 21,856 for value-only latent
rollout; 28,192 for single-pair and single-horizon JEPA; and 14,816 for
direct-leaf value. The former counts (37,536, 56,544, 18,528, and 24,864)
are superseded. The JEPA count includes three EMA target encodes. Equal
windows, batches, and update counts therefore do not imply close dense forward
work.

This is a static operation inventory, not a complete FLOP count, not a
forward/backward dry-run, and not a verdict that the v04 5% gate fails. It
omits activations, bias additions, loss/reduction work, masks, backward,
optimizer, EMA updates, and data movement; actual valid-target masks may also
change executed calls. The raw-state architecture remains a proposal. Before
any trainer or fit, independently resolve the arm graphs and run the required
same-batch forward/backward FLOP profile; if the measured panel exceeds 5%,
version and review a method change rather than adding filler work.

Three standard-library tests verify the shape arithmetic and corrected graph
call counts: four recursive predictor transitions, three rollout-value calls
at horizons 1/2/4, and four raw-state decode/re-encode transitions. EMA target
encodes are arm-specific: three for multi-step JEPA and one for each
single-target JEPA arm.
The deterministic JSON is at `/tmp/caissa-v212-arm-dense-forward-macs-audit.json`;
the output is not a dataset or performance result. No model was instantiated
and no roots, outcomes, inference, training, or matches were run/accessed.

## Method disposition (2026-10-07)

The latent-then-decode raw-state graph and its target/loss, terminal, gradient,
and preflight contract were later adopted narrowly in
`METHOD_SPEC_V212.md` v05 after read-only method disposition. This resolves
the architecture ambiguity identified above; it does not change or validate
the old random-weight pilot path. The actual six-arm trainer implementation
and same-batch forward/backward FLOP profile still do not exist. The ≤5%
training-FLOP gate remains untested and unpassed; the MAC inventory above is
still a risk signal only.

### Current-source provenance correction (2026-10-07)

The static inventory's original contemporaneous description above records its
2026-10-07 proposal status. The latent-then-decode graph was subsequently
adopted in v05 and remains current in v06. The executable inventory now names
`METHOD_SPEC_V212.md` v06 as its graph source; the MAC totals are unchanged.
An approved read-only six-arm review confirmed the adopted raw-state recurrence
and the reported dense-forward figures, while retaining **NO** graph freeze
and an **untested/unpassed** ≤5% compute gate. The six-arm mask schedule,
trainer, complete source/runtime counter, and forward/backward parity profile
remain absent.
