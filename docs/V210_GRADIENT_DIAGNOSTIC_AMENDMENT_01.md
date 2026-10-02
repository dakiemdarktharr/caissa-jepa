# V2.10 gradient diagnostic amendment 01

Date: 2026-10-02
Status: pre-gradient amendment; independent review required before run.
Supersedes: root/batch-count clauses only in `METHOD_V210_GRADIENT_DIAGNOSTIC.md`.

## Why this amendment exists

The support-feasibility attempt `v210_gradient_diagnostic_dev02` used the frozen requirement of ten batches × 64 roots = 640 roots per game. Its hash-validated DEV09 loader reported 307 Connect4 train roots and 1,490 Reversi6 train roots, so the runner stopped before loading any model checkpoint or computing any gradient. The failed run produced no diagnostic artifact or result. Its stderr log is ignored under `chess_data/v210_gradient_diagnostic_dev02.stderr.log`; no metric was inspected.

This is a support-feasibility correction made before any gradient outcome was computed. It does not change the games, model/checkpoint seeds, root-selection hash, batch count, gate thresholds, gradient definitions, or decision logic.

## Frozen corrected sample

Per game, take the first 300 eligible train records after sorting by the existing SHA-256 key `sha256("caissa-v210-roots-v01:" + digest(record))`. Partition into ten disjoint batches of 30 roots; use the identical selected record set for each of the 20 checkpoint seeds. This covers 300/307 Connect4 train roots and 300/1,490 Reversi6 train roots. No record is repeated within a seed/game. The remaining roots are omitted by the frozen hash order, not by outcomes or model scores.

Retain the original gate exactly: (1) median across 20 per-seed median encoder cosines below -0.05 in each game; (2) unadjusted two-sided 95% t interval for the mean per-seed median below zero in each game; and (3) at least 15/20 seeds with negative cosine in at least 6/10 batches in each game. The smaller batch size may make the gradient estimate noisier; that limitation must be reported. If the gate fails, stop this gradient-conflict candidate without subgroup or sample-size tuning.

## Failed feasibility attempt ledger

`v210_gradient_diagnostic_dev01` exited on the initial import error before data access; no dataset, checkpoint, or gradient was loaded. `dev02` exited at root-sample feasibility validation with `Connect4 ... 307 train roots; 640 required`. It used the train-only audit loader but did not load V2.9 checkpoint contents or compute gradients. `dev03` passed the support check but stopped because the runner expected the data-audit source hash in the individual receipt; the frozen panel ledger, not the per-fit receipt, carries that field. It verified panel-bound checkpoint and receipt hashes, but did not load parameter arrays or compute gradients. `dev04` verified support, panel-bound artifact hashes and receipt identity, but stopped because the runner requested the frozen model config from the fit-result panel instead of its hash-bound input spec. It did not load checkpoint parameter arrays or compute gradients. These are pre-gradient implementation/provenance feasibility failures, not negative gradient results. The corrected run uses a fresh output root (`v210_gradient_diagnostic_dev05`).

Acceptance before execution: source/tests pass; checkpoint receipts/hashes are bound to the pinned panel ledger; the no-metadata weights-only loader is verified; an independent reviewer confirms this amendment changes only support counts and that the boundary remains train-only/no-update. No fitting or confirmatory access is authorized.
