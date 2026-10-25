# Reproduce the scoped CP-01 feasibility report

The learned-model study stopped at its frozen eligibility gate. These commands
reconstruct evidence and the report; they do not approve further scientific
screens, fitting, locked evaluation, or paid compute. Both observed screens use
the same 164 original episodes and must not be pooled as independent samples.

## Published evidence and minimal reproduction

Clone the configured GitHub repository and read `research/STATE.md`,
`research/feasibility_analysis.json`, `research/runs.csv`, the two attempt
receipts, final disposition and `paper/claims.csv`. The exact source tree used
for the delivered PDF is in `paper/artifact-manifest.json`. This manifest also
binds every generated file and the small analysis inputs by SHA-256.

The report needs no raw boards, checkpoint weights, GPU or historical archive.
Use a separate renderer environment; it does not change the NumPy research
runtime. The tested renderer is Python 3.12.15 with exact packages in
`paper/requirements-render.txt`.

```bash
uv venv /tmp/cp01-report-reproduce --python 3.12
uv pip install --python /tmp/cp01-report-reproduce/bin/python -r paper/requirements-render.txt
MPLCONFIGDIR=/tmp/cp01-reproduce-mpl /tmp/cp01-report-reproduce/bin/python -B -m tools.counterplay_render_report --run-id cp01-report-reproduce-unique-attempt
```

Run from a clean checkout. The command verifies per-root CSV counts against
receipts, generates the table data, Markdown tables, PNG/SVG figure, complete
Markdown manuscript, PDF and artifact manifest, and records a workflow event.
The PDF is at `output/pdf/counterplay-feasibility.pdf`. A run creates local
untracked/changed outputs; use a fresh checkout or preserve these outputs before
another attempt. Do not discard human changes just to satisfy the clean-source
guard. The fresh-clone artifact verification distinguishes exact recovered
bytes from any newly regenerated PDF. Full byte-identical rendering across
different platforms/fonts/library versions is not claimed.

Core mathematical/data tests used Python 3.11.9 and NumPy 2.4.6. Install NumPy
alone for this scoped core path; Qt is unnecessary. From that environment:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B -m unittest tests.test_counterplay_gradient tests.test_counterplay_data tests.test_counterplay_data_producer tests.test_research_ledger tests.test_research_checkpoint
```

The older full repository suite has known unavailable-artifact and Windows
limitations. A scoped pass is not a claim that the full suite passed.

## Optional raw recovery, not another scientific screen

Raw datasets remain ignored/local under the GitHub-only storage choice.
Recovery must use separate clean checkouts at the producing revisions:

| Artifact | Producing source | Expected data SHA-256 |
| --- | --- | --- |
| First screen | `09f18a5cf5e9a827ce526997714a035d4b07175e` | `442e97c0d685494df753a5723a0bb3389ad4e960ad6ac3c52e416256217b650b` |
| Final screen | `c0503beeee856a51a781c9c2ea29b0434475f490` | `222331ca7a9bc3a20fd8be084debd975db5580b76aa46dd52911642060fc11e0` |

At each exact revision, the recipe and command are in that revision's
`research/data_contract.json`, `research/STATE.md` and `tools/counterplay_data.py`.
The module command takes a fresh ignored destination, a fresh compact receipt
and unique run ID. Use the original seed and recipe, one BLAS/OMP thread,
100,000 solver nodes/two seconds per root and an external 330-second wall
deadline. Both original invocations returned exit code 2 because feasibility
gates failed; that is the expected scientific disposition, not permission to
retry until success. The final revision binds the published first receipt and
charges its 15.391540855 builder CPU seconds against 300 cumulative seconds.

An actual disaster-recovery regeneration must be labeled a new recovery
attempt, retain costs/failures and compare exact data hashes. It is not a third
scientific screen, independent corpus, or extension of the retired design.
Exact recovery of local-only artifacts is not guaranteed if environment or
source dependencies cannot be recreated. Hashes identify bytes, not restore
them. No raw corpus or trained checkpoint was recovered from GitHub in this
session.

## Per-root analysis units and publication

`research/results/cp01-attempt1-roots.csv` has 57 rows and the second file has
59. They preserve source commit, game, episode group, root identity, source
ply, reference status/count/cost, pairability and necessary signed support;
they contain no board corpus. The rows were exported from clean source
`2b10bef418d4b909f19b1e506d13ebbbadd73618` using the receipt-bound
`tools.counterplay_feasibility_units` module. `paper/artifact-manifest.json`
and the claim map bind the analysis outputs used by the manuscript.

Every new project commit needs a refreshed README status section and explicit
small-file checkpoint selection. PDF/PNG/SVG artifacts retain the same 2 MB
per-file and 10 MB aggregate caps as other curated evidence. The checkpoint
tool rejects ignored datasets, weights, environments, raw logs, pre-staged
user work and non-fast-forward publication. No force-push, background service,
storage purchase, paper submission or external message is part of this report.
