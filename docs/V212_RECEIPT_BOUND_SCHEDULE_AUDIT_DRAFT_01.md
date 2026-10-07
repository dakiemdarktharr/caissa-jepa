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

`compute_receipt_bound_panel_batch` validates the complete structural
20×87 manifest, selects one seed/update row, and checks that the 64 supplied
windows match the row's exact ordered IDs and payload hashes and appear in the
replay receipt index. It checks the six model identities and their paired
initialization seed, materializes the fixed-size model batch, compares actual
adapter-derived horizon masks with all six declarations, then calls the
existing paired six-arm no-update helper and compares its batch digest with
the declared row. The returned result carries the schedule digest and unique
episode-receipt digests used by that update.

This is a callable preflight seam, not an exclusive trainer. `loss_grad` and
the existing no-update helper remain directly callable; a future trainer must
route every scheduled update through this boundary and prevent bypass. The
helper currently materializes the batch once to inspect actual masks and the
existing call helper materializes it again before arm calls. That repeated
adapter work is visible implementation overhead, not measured runtime; any
profile must count it or a separately reviewed refactor must remove it.

## Validation and limits

Five new synthetic tests cover full-train receipt indexing, ordered payload
binding, mask-roster rejection, train-only input, and high-level call
coordination. The high-level coordination fixture mocks the whole-schedule
validator, materializer and paired-call helper; it deliberately does not
constitute a valid 20×87 replayed schedule or an end-to-end model batch. With
the episode/trajectory, manifest, scheduled-call, adapter and model suites,
focused validation passes 41/41 under Python 3.14.7 with temporary NumPy
2.5.3, not the locked Python 3.11.9 / NumPy 2.4.6 runtime. `compileall` and
`git diff --check` pass.

No research corpus, selected schedule, roots, scores/outcomes, profile,
inference, or training was loaded or run. Before any profile this seam needs
independent implementation review, an immutable source/data manifest and
selected-window replay receipts, a true exclusive trainer path, a valid actual
mask roster, complete counter/branch bounds, and pinned runtime/backend/source
identity. No gate advances from these fixtures; keep all prior negative
results and novelty risks.
