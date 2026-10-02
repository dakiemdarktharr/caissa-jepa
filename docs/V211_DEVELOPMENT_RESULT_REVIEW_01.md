# V2.11 DEV03 Development Match: Result and Independent Audit

Date: 2026-10-02  
Protocol: `V211_JEPA_WEIGHT_CALIBRATION_V01`  
Candidate: reply-set JEPA with prediction coefficient λ=8  
Frozen fit commit: `ae9c99c8b60b128f994d91f904c3a3505ca1a32d`

## Result

The λ=8 candidate was evaluated in 240 paired blocks (480 color-swapped games),
20 initialization-seed clusters, two games, and three same-seed controls. It
did not meet its frozen nomination rule and was not nominated for a separate
confirmatory study.

| Control | Connect Four 6×7 | Reversi 6×6 | Equal-weight macro |
| --- | ---: | ---: | ---: |
| Reply JEPA λ=1 | +0.0500 | −0.1375 | −0.04375 |
| Task-value dynamics | +0.0250 | −0.1250 | −0.0500 |
| Direct-leaf value | +0.0375 | −0.1125 | −0.0375 |

Each value is the candidate-minus-control paired score, with 0 representing a
tie and +1/−1 a win/loss under the score coding. Every reported unadjusted
95% interval over the 20 checkpoint-initialization seeds spans zero. The
Connect Four effect is positive against each control but below the +0.05
per-game gate for two controls; Reversi is negative against every control.
The equal-weight macro is negative against every control.

All three planner CPU caps passed. Candidate/control planner CPU ratios were
1.118 versus λ=1 on Connect Four and 1.006 on Reversi; 1.117 versus task-value
on Connect Four and 0.978 on Reversi; and 0.952 versus direct-leaf on Connect
Four and 0.995 on Reversi. Candidate fit time was 490.71 seconds versus
432.05 seconds for task-value dynamics (ratio 1.136, below the 3.5 cap). There
were 240/240 complete blocks, 480 games, zero forfeits and zero censored games.

## Independent audit

The approved independent reviewer replayed all 480 game transcripts against
the pinned game rules, checked the exact block schedule/order and color-swapped
score reconstruction, recalculated the seed-cluster summaries and compute
ratios, and verified the match artifact against its receipt hash. All values
matched the saved analysis exactly. No P1, P2, or P3 findings remain. The
reviewer did not inspect training histories/loss metrics or V08/locked-final
data, did not rerun the match, and made no artifact changes.

## Interpretation and claim boundary

This is a complete exploratory/model-selection result for the frozen two-game
schedule. It is evidence against this λ=8 calibration recipe. It does not show
that JEPA in general is inferior, nor that JEPA is superior. The development
analysis supports no causal, confirmatory, equilibrium, exploitability,
cross-game transfer, methodological novelty, or Q1-readiness claim. The
predeclared rule stops λ-only tuning; the result must remain unchanged in
future summaries.

## Provenance

- Match: `chess_data/v211_fit_match_dev03.jsonl`
- Match receipt: `chess_data/v211_fit_match_dev03.jsonl.receipt.json`
- Candidate fit panel: `chess_data/v211_fit_panel_dev03/panel.json`
- Train-only grant: `chess_data/v211_data_dev09_approval_v02.json`
- Machine analysis: `docs/validation/V211_DEVELOPMENT_MATCH_ANALYSIS_DEV03.json`
- Frozen method: `docs/METHOD_V211_JEPA_WEIGHT_CALIBRATION.md`
- Independent panel review: `docs/V211_PROTOCOL_REVIEW_01.md`
- Match/protocol audit: reviewer result recorded in Ground Truth and this note

Raw match, checkpoint, and run artifacts remain under ignored `chess_data/`;
none are copied to GitHub or the Obsidian mirror.
