# V2.12 random-weight compute pilot V03

**Status: versioned implementation candidate; not independently reviewed and
not run.** V03 addresses the RSS guard/reporting gap found in V02 while keeping
the V02 source and receipt unchanged. This remains a no-training, no-outcome
compute instrument using synthetic reachable roots and random initialization.
It is not an evaluation pilot authorization or evidence of model performance.

## Frozen scope inherited from V02

V03 retains the V02 root schedule, four game/board-size variants, six named
arms, three initialization seeds, 500,000-node per-cell cap, 8-second
per-cell wall cap, and 1.5 GiB sampled-RSS stop threshold. It records only
compute counters and root fingerprints; it does not record selected actions,
action values, game scores, outcomes, or training state. A future method,
schedule, cap, or arm change needs a separate version and review.

## RSS stop and partial-run evidence

The cell runner samples RSS on entry before model work, every 256 entered
search nodes, and once at exit. An over-cap sample is converted into a returned
`rss_cap` cell row; after a crossing is known, the runner skips further samples
so a later sampler error cannot erase that row. The V03 runner immediately
persists that row and terminates the whole schedule; it does not continue with
later cells. If the process exits or is terminated before a cell returns, its
prior progress records remain available.

The progress journal is JSONL under the ignored `chess_data/` directory. It
records a source/schedule manifest first, then one redacted compute-only row per
completed cell, with each line flushed and fsynced, followed by a terminal
status when possible. A partial journal is explicitly incomplete and cannot
be treated as a completed pilot receipt. Only a full schedule can create the
final aggregate JSON receipt; it is schema-verified, written to a temporary
file, fsynced, linked without replacing an existing output, and followed by a
directory fsync. If any operation after linking fails, the runner reports
`publication_uncertain` and records that terminal state in the journal when
possible. The visible receipt is not treated as complete; its existence blocks
reruns until a reviewer reconciles it with the journal and filesystem
durability. If a process is killed mid-append, the final JSONL line may be
incomplete; readers must accept only newline-terminated, parseable records and
must classify an incomplete tail as interruption rather than success.

The final receipt binds this protocol, the V03 cell implementation and runner,
the V02 schedule implementation, shared model/rule sources, runtime, and root
schedule. V02 remains the source of the unchanged schedule and model classes;
its previous receipt is still verified by its original verifier.

## Limits and required review

RSS remains a sampled, cooperative check, not a hard memory ceiling. Entry and
final samples close the specific missing comparison/exception paths but cannot
prevent a rapid allocation between samples or an external OOM kill. A real
future pilot still requires the independently enforced worker memory limit,
supervisor survival, event/result attribution, durable receipt integration,
caller-observed deadlines, and independent review specified in
`docs/V212_EXTERNAL_SUPERVISION_DESIGN_01.md`. This V03 code remains a candidate
pending review of the latest revisions and must not be run as a substitute for
it.

Focused tests use one deterministic synthetic root, random initial weights,
mocked RSS sequences, and temporary files. They check search-counter parity
with V02, runner journaling on an RSS stop, and receipt publication failure
handling; they do not run the V03 schedule or create pilot outputs. No host
service, inference request, root-data file, score, training run, or model
update is part of the V03 implementation check.
