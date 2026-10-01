# V2.8 data/power protocol amendment v0.5

**Status: historical scope redesign; superseded for execution by V06 amendment.** Protocols v0.1–v0.4 and their raw diagnostics remain preserved.

## Why the prior split/quota line stopped

The largest evaluated candidate, DEV05, used the 4x5 Connect4 variant with 96 candidate episodes per split. Its pre-review manifest reported Connect4 train 9 trajectories/2 records, validation 4/20, and selection 9/26; Reversi6 had ample raw support. Connect4 failed the stated 8-trajectory/64-record/16-H2 floors. The independent reviewer also found that the implementation checked the support floor only for the last (empty locked-final) split. DEV05 therefore has **no valid pass status**; its recorded counts are diagnostic only, and no `records.jsonl` was emitted. The one mixed-family component and seat-coverage failures independently establish failure.

Repeatedly increasing the quota on this 4x5 game is stopped. The short, tactical trajectories provide too few post-phase roots, so this small state space is a poor development domain for the planned H1/H2 learning study.

## Frozen V06 scope and protocol

V06 replaces Connect4 gravity 4x5 with standard Connect4 gravity 6x7 and retains Reversi6. Both remain deterministic, alternating-turn, fully observable, two-player, zero-sum games with explicit legal actions and terminal rules. This is still only a two-game benchmark, not evidence of broad transfer. Exact minimax labels are not required for self-play outcome supervision; any exact-label analysis on 6x7 is a separately budgeted study.

DEV06 executed this scope with 48 candidate episodes per game/split and seed `28094004`; its support audit passed. A reviewer then found that the code did not enforce the exact split schedule even though the actual call used it. See V06 amendment: DEV06 records are not accepted for fitting, and one corrected rerun (DEV07) is required. Train/validation components are balanced toward a fixed 25% validation trajectory share. Components that mix held-out positional and train/validation families are quarantined whole.

The audit must verify deterministic regeneration from each row's source split, seed, episode, policy hashes, actions, terminal outcome and search-node metadata; exact `+1`/`-1` seat keys; family coverage in both seats; component-first assignment; complete cross-split key isolation; and per-game, per-split floors of 8 unique trajectories, 64 records and 16 H2 targets. Failed audits write diagnostic trajectories and manifest only. Even a passing pilot would be prefit feasibility only: power, independent method review, and a frozen training/selection/confirmatory plan still come first.

## Stop rule

If V06 fails any family, provenance, leakage or support gate, stop without fitting. Preserve the full receipt and decide whether to reduce the multi-game claim or redesign the benchmark under a new version. Do not relax support floors, phase threshold, overlap keys, or family holdouts after seeing the pilot.
