# V2.8 model-blind pilot supervisor review 01

**Date:** 2026-10-01

**Scope:** hidden-run lifecycle, output collision handling, selected-schedule
and artifact provenance, Windows Job Object setup, heartbeat/terminal reporting.

**Reviewer:** independent `gpt-6-luna/high` review, requested and approved by the
user.

**Disposition:** no remaining P1/P2 in reviewed code/test scope after revisions.

## Findings and changes

The first review found four P2 issues:

1. Preflight omitted the runner receipt temporary and supervisor terminal
   fallback paths. Both are now checked before launch; existing outputs cause
   a fail-closed refusal.
2. `NaN` and infinity heartbeat intervals passed the CLI check and disabled
   progress writes. The CLI now requires a finite interval of at least one
   second.
3. A nested output path could fail while writing initial status because its
   parent did not exist. The supervisor creates the parent before starting its
   protected lifecycle and supports nested paths.
4. The supervisor recorded only a full default schedule hash and did not bind
   completion to the actual reduced schedule, receipt, source, and artifact.
   It now derives the selected schedule using the runner's sizing rules and
   requires schedule hash/count, entry-source hash, receipt schema, output
   path, byte count, and artifact SHA-256 to agree before reporting completion.

The second review identified that the supervisor itself and behavior modules
were not all represented in run identity. The final fingerprint includes
`tools/v28_modelblind_match_pilot.py`,
`tools/v28_modelblind_pilot_supervisor.py`, `two_player/v28_data.py`,
`two_player/games.py`, and `two_player/data.py`; it records a canonical digest
of that map and the Python/NumPy versions. Completion is rejected if any
fingerprinted source changes during the run.

## Verification

The focused `tests.test_v28_modelblind_pilot_supervisor` suite passes 5/5. The
combined supervisor/evaluator/analysis/power suite passes 24/24, and
`git diff --check` passes. A nested-path 8-block smoke run completed with all
records replay-verified and matching selected-schedule, source, artifact, and
receipt identities. This only validates the smoke run's lifecycle and replay;
it is not the 9,600-block runtime/power gate and contains no learned-model
comparison.

Static review found no concrete Windows Job Object structure/flag error, and
the Job Object accepted the smoke child on Windows. The four-hour CPU-time cap
and kill-on-close behavior were not separately stress-tested. Do not claim
those limits have empirical stress-test evidence.

## Remaining boundaries

The proxy runner contains no learned JEPA or learned baseline. Passing the
full proxy schedule would establish bounded runtime and paired-variance
feasibility only. It would not establish JEPA superiority, opponent modeling,
equilibrium quality, exploitability, transfer, novelty, or Q1 readiness.

The full repository discovery in the available bundled Python 3.12.14 runtime
ran 407 tests and ended with 20 errors because PySide6 was absent or incomplete
in that environment, affecting GUI and legacy trainer tests. The focused
V2.8 supervisor/evaluator/analysis/power suite passes as above; no package was
installed to repair the unrelated environment gap.
