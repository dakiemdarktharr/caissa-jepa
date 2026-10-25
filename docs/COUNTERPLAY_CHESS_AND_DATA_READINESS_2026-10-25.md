---
title: Counterplay — Chess, Elo, and data readiness
date: 2026-10-25
tags:
  - counterplay
  - chess
  - research-plan
  - data-readiness
status: Proposed extension; data not ready for the new study
---

**Decision in brief:** chess is a feasible extension of the proposed Counterplay
study. Relative Elo would make playing strength easier to communicate. The
current project does **not** have an accepted train/validation/test package for
V2.12, the proposed Counterplay study, or its chess extension. Historical
small-game datasets are recoverable from a local archive, which changes the
recovery picture but does not satisfy the new study's data contract.

Prepared on **25 October 2026, Asia/Saigon**. Budget: **US$50/month**, with no
fixed deadline or venue. This note records the discussion and a read-only data
inventory; it does not adopt a new experimental protocol or start training.

**1. Scope and naming**

Recommended project/framework name: **Counterplay: Counterfactual Audits of
Latent Planning in Adversarial Games**. Suggested future repository name:
`counterplay-lab`. The chess experiment can be called **Counterplay-Chess**.
The existing implementation identifier `multi-step-jepa` should remain until a
distinct model warrants a new identifier. No repository or package was renamed.

The paper asks which opponent-reply distinctions predictive representations
must preserve for planning decisions to remain sound. It can report useful
mechanisms, limitations, and negative results even if JEPA has lower playing
strength. Adding chess or an Elo display alone does not establish novelty.

| Track | Purpose | Main measurements |
| --- | --- | --- |
| Connect Four / Reversi | Controlled, inexpensive study of adversarial planning errors | Decision regret, preservation of critical replies, effects of targeted representation repairs |
| Chess positions | Check whether the findings extend to chess | Tactical decisions, critical-reply preservation, disagreement with a pinned reference |
| Chess matches | Assess practical strength of complete agents | Win/draw/loss score, relative Elo and confidence intervals, runtime and failures |

Recommendation: complete the first small-game training pilot, then add chess as
a bounded extension. Chess should not delay the shared gradient, data, and
trainer fixes. Ordinary Stockfish search evaluations are reference estimates;
exactly solved endgame results, if used, belong in a separately identified
stratum. A fixed-horizon reference is also distinct from a solved full game.

**2. How Elo helps, and how to measure it**

Elo also works for agents playing Connect Four or Reversi. Each game and
opponent pool has its own relative scale; ratings should not be compared across
these games or presented as FIDE/Lichess ratings.

For a two-agent match, the existing arena uses score
`p = (wins + 0.5 * draws) / games` and the conventional descriptive difference
`delta_elo = 400 * log10(p / (1 - p))`. A 55% score corresponds to approximately
+35 Elo under that model. Scores of zero or one do not yield finite estimates;
the current implementation returns no Elo estimate at those endpoints.

A credible chess evaluation needs:

- Diverse held-out openings, each played with colors reversed.
- Pinned checkpoint identities, opponent versions/options, rules, search
  implementation, hardware, and time/node/thread budgets.
- Several training seeds, with uncertainty accounting for repeated openings
  and repeated use of the same checkpoints.
- A fixed evaluation schedule and declared handling of illegal moves,
  timeouts, infrastructure failures, truncations, and incomplete pairs.
- Opponents close enough in strength to avoid almost-all-win or almost-all-loss
  results; a small fixed pool can reveal matchup effects hidden by one rating.
- Win/draw/loss counts and paired score intervals alongside any Elo summary.
  Match sample size must follow a development precision/cost pilot; a small
  smoke tournament does not establish a precise rating.

The existing `arena_research.py::matchup_statistics` already calculates a
relative Elo estimate, but returns `ranking_ready: False`. Legacy confirmation
is explicitly blocked in `confirmatory_protocol.py` because independent
full-history rule replay/outcome validation is not implemented. A pinned UCI
evaluation engine does not fill that rules-validation gap.

The primary scientific measurements remain planning decisions and controlled
interventions. Elo is an interpretable strength endpoint alongside those
measurements. Stockfish's official documentation explains both the
[dependence of ratings on match conditions](https://official-stockfish.github.io/docs/stockfish-wiki/Stockfish-FAQ.html#the-elo-rating-of-stockfish)
and its [paired engine-match statistical framework](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html).

**3. Data actually available on this machine**

The active checkout is `/home/koi/src/caissa-jepa`. Its ignored `chess_data/`
contains **12 files, 1,702,737 bytes**: V2.12 random-weight compute-pilot JSON
files and summaries. These are runtime evidence, not an accepted model-training
corpus. The expected `fen_dataset/`, `downloads/`, and `build/` directories are
absent. The historical V2.9 panel path is absent from the active checkout.

This follow-up located a separate archive at:

`/home/koi/archive/windows-project-handoff-2026-10-03/caissa-jepa/chess_data`

It contains **1,694 files, 932,981,707 bytes** (about 933 MB), including data,
receipts, logs, and **449 NPZ experiment artifacts**. That is not 449 training
datasets. Historical V2.9 and V2.11 panel paths exist in this archive. They were
not restored or loaded for new evaluation.

The archived DEV09 `records.jsonl` and `trajectories.jsonl`, and the V2
`forks.json`, match the byte sizes and SHA-256 values in the repository's
historical validation receipts. This establishes selected artifact identity,
not a new full rules audit, complete archive validation, or suitability for
the revised method. No final prediction records were parsed or scored.

**Archived V2.8 DEV09 counts:** the manifest records 284 trajectories and 3,531
retained records. These support counts also match the curated historical
receipt; they were not recomputed by replaying every trajectory in this task.

| Game | Training records (episodes) | Validation records (episodes) | Selection records (episodes) | Locked-final records |
| --- | ---: | ---: | ---: | ---: |
| Connect Four 6×7 | 307 (72) | 128 (24) | 139 (44) | 0 |
| Reversi6 | 1,490 (72) | 491 (24) | 976 (48) | 0 |
| Total | 1,797 (144) | 619 (48) | 1,115 (92) | 0 |

DEV09 training/validation use uniform and tactical policy families; selection
uses positional policies. Its H2-oriented records and policy mixture differ
from the current four-policy, 16 ordered-pair, up-to-H4 contract.
`METHOD_SPEC_V212.md`, section 6, explicitly says DEV09 is not reusable for
that study. Its 307 Connect Four training records also do not directly supply
the specified 928 eligible training windows for that game. These are different
record contracts, so raw record counts must not be equated with H4 windows.

An earlier **V2 fork bank** is also present: 984 roots, split into 509 training,
209 development, 131 selection, and 135 final roots. It uses Connect Four 4×5
and Reversi6, with two-ply forks. Its final split is a historical holdout, not
an accepted final benchmark for the new study. Its presence does not authorize
opening protected outcomes or treating it as fresh after study redesign.

No current audited **chess** corpus was located in the active checkout or the
identified project archive. Old documentation describes a much larger Windows
FEN/game database and subsequent removal of production chess data. Those old
counts are historical evidence, not data verified available now. The legacy
120 opening fixtures are testing infrastructure from six synthetic families;
they are not a training dataset or an independently reviewed final opening set.

**4. Is there sufficient training, validation, and test data?**

**No, for the current/new study.** The answer differs by intended use:

| Intended use | Readiness | Remaining requirement |
| --- | --- | --- |
| Synthetic software checks | Existing fixtures available | They establish code behavior, not model-learning or paper validity |
| Revisit historical small-game experiments | Selected source data located and hash-verified | Restore deliberately, check original environment/configuration and all needed artifact identities |
| Train the adopted V2.12 recipe | Not ready | New accepted episode/window corpus, four-policy provenance, H1/H2/H4 masks, split audit and schedule |
| Train the proposed Counterplay study | Not ready | Prospective protocol and accepted train/validation/selection corpora plus locked evaluation design |
| Train and evaluate Counterplay-Chess | Not ready | Chess representation/action adapter, audited trajectories, rules/history validation, position benchmark and match openings |
| Make a final paper claim | Not ready | Fresh frozen evaluation, measured uncertainty, reproducibility and complete reporting |

Sufficiency has three parts: enough valid training support to fit the intended
model; clean group separation and trustworthy targets; and enough independent
evaluation units for useful uncertainty. More windows from the same few games
do not automatically provide more independent evidence. A fixed percentage
split such as 80/10/10 alone cannot establish sufficiency.

**5. Data plan and acceptance criteria**

For the proposed Counterplay protocol, specify four roles before materializing
records: training for gradient updates, validation for declared development
choices, selection for the bounded comparison/nomination stage, and a locked
final evaluation. If the new protocol merges validation and selection, record
that choice prospectively and still keep final evaluation independent. The
historical V2.12 development protocol intentionally has no final corpus yet;
its lack of one should not be misreported as a corrupted split.

Assign complete games/episodes and related groups before extracting windows.
Bind context and all future targets to the same split. Define exact,
symmetry-equivalent, and transposition-overlap rules. Shared chess openings
need an explicit exclusion/shared-start policy; do not silently exempt them
or insist on impossible whole-board disjointness without measuring retention.

Acceptance requires:

- Every retained action and target replays legally, with explicit terminal,
  missing-target, truncation, and invalid-record handling.
- Complete source/provenance, generator/parser/rules identities, file hashes,
  split assignments, retained counts, and exclusion reasons.
- Zero prohibited cross-split overlap under the prospectively declared rule;
  report any permitted shared-start overlap separately.
- Nonempty splits and adequate coverage of both games, policy pairs, plies,
  terminal/nonterminal conditions, and eligible H1/H2/H4 targets.
- Training loaders cannot access validation/selection/final records as
  gradient data. Training scaling/calibration uses training data only.
- Frozen reference construction and complete reference coverage for retained
  evaluation roots, with unresolved roots reported rather than cherry-picked.
- Sample sizes fixed from development cost/variance measurements before
  inspecting locked performance. Report dependence between roots and seeds.

The earlier proposal's **4,096 training windows per game/corpus**, **200 fresh
evaluation roots per game**, and **50-root H4 subset** are planning estimates,
not available data, guarantees of statistical power, or an adopted protocol.
Evaluate training learning curves on development data and revise the proposed
budget once before final freeze. The suggested regret interval half-width of
0.05 is a planning target; feasibility must be measured. Chess needs a separate
throughput/precision pilot before choosing its game and opening counts.

**6. Next steps until training**

1. **Write the prospective Counterplay protocol.** Freeze scope, objectives,
   comparison arms, reference definitions, split policy, primary metrics,
   cost limits, and outcome-independent paper deliverables. Preserve V2.12 as
   historical work rather than silently changing its gates.
2. **Fix objective correctness.** Resolve the confirmed covariance-gradient
   weighting defect and check encoder gradients against finite differences
   across all affected arms.
3. **Complete the dataset contract and generator.** Resolve duplicate/shared-
   state rules, manifest identity, deterministic windows, target masks, and
   retention failures before generating the accepted corpus.
4. **Materialize and audit a small development corpus.** Use fresh procedural
   small-game episodes. Keep historical recovery separate from new evidence.
5. **Integrate and verify the trainer.** Check one update, optimizer/EMA state,
   deterministic scheduling, resume equivalence, finite gradients, and a tiny
   learning sanity check. Those checks are development training, not paper
   experiments.
6. **Measure resources and run the first small-game pilot.** Record throughput,
   memory, learning curves, model/reference costs, and failures. Freeze the
   bounded full experiment only after the pilot supports its cost and design.
7. **Add the chess adapter.** Represent piece types, side to move, castling,
   en passant, promotion actions, and an explicit clock/history policy. The
   current 198-feature/65-action adapter cannot be reused unchanged.
8. **Prepare chess data and evaluation.** Audit full trajectories and source
   rights; validate special moves and terminal/draw rules independently;
   create held-out position and opening sets; adapt the comparison arms to a
   common search implementation. Then run the first small chess training
   pilot and a separate match-throughput pilot.

The $50/month budget favors bounded offline training and measured evaluation.
The current small-model implementation is CPU NumPy; renting a GPU will not
accelerate it without an appropriate implementation change. No paid compute,
dataset download, corpus generation, training, or matches were launched for
this note. Generated data, checkpoints, environments, and logs remain excluded
from Git and Obsidian.

**7. Evidence and storage**

Repository sources checked: `arena_research.py`, `confirmatory_protocol.py`,
`two_player/games.py`, `V7_RESEARCH_PROTOCOL.md`, `METHOD_SPEC_V212.md`,
`docs/DATA_SOURCES.md`, `docs/PROJECT_REVIEW_2026-10-25.md`, and the historical
receipts `docs/validation/V28_DATA_SPLIT_DEV09.json` and
`docs/validation/V2_FORK_AUDIT.json`.

The fresh inventory/hash-check receipt is
`docs/validation/DATA_READINESS_2026-10-25.json`. Only selected data identities
were checked; the full 933 MB archive was neither revalidated nor copied.

Versioned note:
`/home/koi/src/caissa-jepa/docs/COUNTERPLAY_CHESS_AND_DATA_READINESS_2026-10-25.md`.
Local Obsidian destination:
`/home/koi/Documents/Obsidian Vault/Caissa-JEPA/COUNTERPLAY_CHESS_AND_DATA_READINESS_2026-10-25.md`.
The old Windows destination `D:/notes/vault_1/Caissa-JEPA` is not mounted here.
Native Obsidian rendering has not been verified; the copy is checked by file
content and SHA-256.
