# V2.12 replay-receipt-bound schedule seam — draft 01

**Status: no-update in-memory preflight candidate.** The helper binds a
validated schedule row to a caller-supplied train replay receipt index and
actual batch masks before invoking the existing six-arm no-update helper. It
does not amend the accepted method or D03 profile preregistration, create a
trainer, read files, generate/select a corpus, or authorize profile, inference,
or training. Six-arm graph freeze remains **NO** and ≤5% parity remains
**untested and unpassed**.

## Boundary behavior

`build_train_replay_receipt_index` first passes the complete supplied in-memory
train episode collection through the existing exact-rule trajectory auditor.
It then reuses those audited windows to build canonical episode receipts and
an immutable episode/window digest index. This avoids replaying the entire
collection again for every scheduled update. The index represents only the
records supplied to this call: it does not prove source-file bytes, generator
lineage, completeness of the declared train corpus, or separation from
development/locked splits.

`validate_and_freeze_schedule_manifest` deep-copies and validates the complete
structural 20×87 declaration once, then returns immutable nested seed/update
records with its canonical digest. The snapshot type's only public constructor
also accepts a raw manifest and performs this complete validation; it cannot
be instantiated from a caller-supplied digest and mutable rows.
`compute_receipt_bound_panel_batch` accepts
that frozen value, selects one seed/update row without rewalking the whole
schedule, and checks that the 64 supplied windows match its exact ordered IDs
and payload hashes and appear in the replay receipt index. It checks the six
model identities and paired initialization seed, materializes the fixed-size
model batch once, compares actual adapter-derived horizon masks with all six
declarations in the pre-model callback, then invokes the paired six-arm
no-update helper and compares its batch digest with the row. The result
carries the schedule digest and unique episode-receipt digests used by that
update. The one-time structural validation/snapshot cost must be reported
separately under D03; no production schedule is currently loaded.

This is a callable preflight seam, not an exclusive trainer. `loss_grad` and
the existing no-update helper remain directly callable; a future trainer must
route every scheduled update through this boundary and prevent bypass. The
paired-call helper exposes a pre-model callback so this seam checks masks on
the same read-only batch that reaches all six arms. A callback error stops
before any model call. This removes duplicate adapter materialization, while
the callback runs one extra structural `preflight_batch`; each arm's own
`loss_grad` also repeats preflight. Those paths must be represented in any
future counter/profile.

## Validation and limits

Five new synthetic tests cover full-train receipt indexing, ordered payload
binding, mask-roster rejection, train-only input, and high-level call
coordination. The paired-call suite also tests that the callback receives the
shared read-only batch and blocks all arm calls when it rejects. The manifest
suite checks that a full synthetic 20×87 schedule becomes a detached immutable
snapshot and rejects direct construction with a forged digest/row tuple. The
high-level coordination fixture uses a structurally valid synthetic 20×87
schedule and exercises the real paired-call boundary with six test-double
models, asserting ordered dispatch and a shared read-only batch. Replay-to-row
binding, materialization, and mask extraction remain mocked; this is not an
end-to-end adapter or actual research-data batch. The prior focused subset
passed 44/44 under Python 3.14.7 with temporary NumPy 2.5.3. After the
integration fixture change, the episode/trajectory, manifest, scheduled-call,
adapter, model, and receipt-bound suites pass 46/46 under the locked Python
3.11.9 / NumPy 2.4.6 environment; `compileall` and `git diff --check` pass.

No research corpus, selected schedule, roots, scores/outcomes, profile,
inference, or training was loaded or run. Before any profile this seam needs
independent implementation review, an immutable source/data manifest and
selected-window replay receipts, a true exclusive trainer path, a valid actual
mask roster, complete counter/branch bounds, and pinned runtime/backend/source
identity. No gate advances from these fixtures; keep all prior negative
results and novelty risks.
