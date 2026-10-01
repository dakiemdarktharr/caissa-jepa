# V2.8 trainer runtime independent review 01

**Reviewed:** 2026-10-01  
**Scope:** `two_player/v28_train.py`, checkpoint/resume logic in
`two_player/v28_model.py`, and their focused tests. This is a software and
provenance review, not approval of a scientific result or project-data fit.

## Findings and disposition

The first review pass found that a public epoch helper and optimizer update
could accept caller-created train-labeled records without consulting the
audited manifest. It also found incomplete resume-history invariants and no
durable receipt. The follow-up found that an initially proposed permit issuer
could itself be called without approval and was not bound to audited records.

The final implementation narrows the supported production fit entrypoint to
`train_dataset()`. It gets the train split through `load_split`, which checks
explicit training approval, audit status, source and artifact hashes, and
replay/audit identity. Optimizer and epoch primitives are underscore-prefixed
private test helpers; Python callers can still deliberately call them, so the
claim is limited to the supported production API rather than a security
boundary.

Checkpoint validation requires history length to equal completed epochs,
ordered epoch indices, positive update counts, metric semantics, and the sum
of epoch updates to equal the optimizer step. Checkpoints include parameters,
EMA target and Adam moments with tensor inventory, shape, dtype, finite-value,
and SHA-256 validation. An interrupted run resumed from a committed epoch
matches uninterrupted parameters, EMA, Adam state and step exactly.

Each epoch checkpoint is accompanied by an atomic JSON receipt that binds the
checkpoint digest, dataset and audit fingerprints, code and run identities,
and epoch history. Metrics are explicitly root-weighted pre-update minibatch
training metrics; the receipt states that no held-out evaluation occurred.
The run identity includes a normalized SHA-256 of
`requirements-research-lock.txt` and actual Python, Python implementation,
NumPy, and platform versions, so changes invalidate resume identity and remain
visible in the receipt. Versions are recorded rather than enforced against the
lockfile.

## Verification and limits

The final focused V2.8 suite passed **70 tests**, including six trainer tests
and 15 model tests. The earlier full repository suite is not current evidence;
the available runtime lacks PySide6 for GUI tests. No project-data fit ran, no
checkpoint was created from DEV09, and the manifest's `training_approved`
flag remains false. The reviewer found no remaining P1/P2 blocker in this
runtime scope. Remaining release gates are V08 model-blind schedule/replay,
runtime and paired-variance/power checks, V02 artifact freeze, and their
independent review. These findings support trainer engineering readiness only;
they do not support JEPA superiority, novelty, transfer, exploitability, or Q1
readiness.

Implementation milestone: `f5f29af1054496943c43520bbdff5f0b253fd8c4`.
