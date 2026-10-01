# V2.8 data/power protocol amendment v0.6

**Status: historical amendment; DEV07 did not produce a receipt.** V0.1–v0.5 definitions and receipts remain historical records. See active v0.7 for the corrected software rerun.

## DEV06 audit and review

DEV06 used the V0.5 scope: Connect4 gravity 6x7 plus Reversi6, 48 candidates per game/split, seed `28094004`, one-third phase threshold, and the required train/validation/selection schedule in actual invocation. The audit reported PASSED with zero errors. Support was Connect4: train 72 trajectories/342 records/298 H2; validation 24/200/182; selection 47/72/64. Reversi6: train 72/1,474/1,402; validation 24/495/471; selection 48/968/920. It wrote `records.jsonl` and `trajectories.jsonl`; neither is committed, and training was not approved.

Independent static review then found the generator accepted duplicate, omitted, or reordered split sequences under the same protocol ID. The actual DEV06 call used the intended default sequence, so its observed support remains descriptive, but the code did not enforce the frozen protocol. The current source hash differs, and the current loader rejects that DEV06 manifest. Do not use DEV06 records for fitting.

## Frozen DEV07 rerun

DEV07 was launched with the intended scope/quota/seed/split schedule but stopped on a valid Reversi trajectory because the pass-aware finite action bound was wrong. It created no output directory, manifest, or data. Static review later also found a caller-overridable phase threshold, which is corrected in the active v0.7 amendment.

DEV07 is not a pass/fail observation. Do not infer anything from the stopped run. The next accepted data-feasibility run is defined by v0.7.
