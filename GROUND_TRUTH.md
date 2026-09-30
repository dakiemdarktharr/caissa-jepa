# CAISSA-JEPA — Ground Truth

Updated: 2026-09-30. Read this page first when resuming. Statements below distinguish inspected facts, historical receipts, proposed work, and research evidence.

**Current continuation state:** canonicalization, exploratory pilot receipt,
and initial novelty re-audit were committed on `main` as
`cc3cb127819ac8e9a24446f7a02fc748e6d4cb06`; publication status was recorded in
`8796a8f5fe9d027db06a339fc6e9563aeead7b91`. Both were pushed fast-forward and
the latter matched the remote SHA at verification. Current working-tree changes
extend the prior-art audit with Athénan, *Minimax Strikes Back*, AAAI-25
Markov-game abstraction, board-game transfer, PCZero and ICML-26 regularized
game learning, and revise the candidate's model-blind gate. This documentation
milestone was committed as `cfb709fd00612d02c3459252c508f5b7ea71ef52`, pushed
normally to `origin/main`, and verified against the remote SHA. The latest
documentation copy was synced to Obsidian. The focused search suite passes 5 tests; full
regression passed **330 tests in 150.012 seconds**.
An independent review using the user-approved gpt-6-luna/high configuration
found no blocking finding. The previous Obsidian sync contained 78 Markdown
files with matching hashes; it needs refresh after these latest edits.
The latest pilot is exploratory only: 32
receipt rows over two seeds took 51.19 seconds; shallow search beat each sanity
opponent 4/4 in sampled pairings. Identical-policy Reversi self-play has only
two unique trajectories (the seat-swap rows duplicate each game): V2 had
minus-seat wins 2/2, and the canonicalized version plus-seat wins 2/2. Seat
effects remain unresolved. Reversi node-cap hits fell from 116 to 68, but
match trajectories and search calls changed, so this is not an efficiency
claim. No JEPA model has been trained and no JEPA-over-baseline result exists.

Independent review found (a) duplicated identical-policy self-play rows being
too easily read as four independent games and (b) no explicit assertion for the
four tied canonical maps on the symmetric initial Reversi board. Documentation
now reports two unique seeds/trajectories, and the focused test asserts the
four-map case. Reviewer found no canonicalization defect, receipt hash mismatch,
or commit-blocking fairness issue. The updated focused suite passes 5 tests in
0.621 seconds; full suite passed 330 tests in 150.012 seconds immediately before
that assertion-only test edit.

The 2026-09-30 prior-art re-audit adds Deep Latent Competition, the recent
MA-JEPA preprint, AAR/AI's learned ranking/value/search combination, and
Athénan (JMLR 2026), a direct two-player perfect-information zero-sum game
method using tree-bootstrapped value learning with minimax. Athénan reports
strong results across Go, Hex, Othello, Arimaa and other games, so it is a key
non-JEPA baseline. Its AAMAS 2023 follow-up *Minimax Strikes Back* compares
Athénan with Polygames/AlphaZero and reports much lower state-data generation
cost in its setup. Generic opponent-action-conditioned latent prediction or
tree-state supervision is not a novelty claim. The only retained candidate is
complete legal-reply-set prediction plus a separately evaluated minimax
action-order objective; distinctness is unverified, oracle feasibility is not
passed, and training is not yet justified by evidence. Approximate zero-sum
Markov-game abstraction and direct game/variant policy-value transfer are also
prior art, so neither latent compression nor transfer alone is a contribution.
Before coding or fitting, the next gate is a source-level design and measurable
comparison that distinguishes this candidate from Athénan-style tree-value
learning, minimax-Q/abstraction, direct policy-value transfer, and task/feature
prediction at matched compute. If no fair incremental claim survives, stop or
pivot to a benchmark paper. Any future method comparison must include these
controls. See
`docs/V27_PRIOR_ART_REAUDIT_20260930.md` and
`docs/V27_RESEARCH_POSITIONING.md`.

The preceding committed V2.7 positioning milestone passed 325
tests in 128.753 seconds on Python 3.11.9. The targeted primary-source review
now also records the distinction between learned opponent-behavior models
(He et al., ICML 2016), game-theoretic robust MBRL (Rajeswaran et al., ICML
2020), fixed-suite match estimation, and worst-case/equilibrium planning. See
`docs/V27_RESEARCH_POSITIONING.md`. This milestone still contains no trained
JEPA or superiority evidence.

The V2.7 positioning and bounded-search feasibility milestones are commits
`c71d97a85d3218569f25e39cadfc7ccc410d9631` and
`59b7698093809f0e90934c4934975876842158dc`, respectively, both pushed to
`origin/main` and verified against remote SHAs. Only local `main` and
`origin/main` remain; the working tree was clean after the latest push. The
Obsidian mirror at `D:/notes/vault_1/Caissa-JEPA/` then contained 77 project
Markdown files. That count describes the prior sync only; the current
continuation refresh and final hash verification are tracked below.

**Next model-blind feasibility step (2026-09-30):** implemented a project-owned
depth-limited negamax/alpha-beta opponent over separate bitboard reference
rules, plus transition/terminal/legal-action differential checks against the
main adapter. Twelve seeded trajectories across Connect4-gravity-8x8,
Reversi8 and Connect-6x7 matched at every tested state; this is same-project
validation, not an external referee. The fingerprinted 32-game pilot is
`docs/validation/V27_SEARCH_OPPONENT_03.json` (two seeds, four policy pairings,
both seats, two games; 86.69 seconds). Search beat random and center/corner
sanity policies in 4/4 sampled games per family, but this sample is too small to
estimate strength. Reversi search-self-play remained seat-skewed (minus won
both unique trajectories; four rows include duplicate seat swaps) and hit its
per-move node cap 116 times. Preserve earlier revision
receipts 01 and 02. The targeted plus full regression passes **329 tests in
93.235 seconds**. No JEPA model, self-play dataset, training or checkpoint was
created. The opponent bank still fails the gate; investigate symmetry and
budget before training.

**Latest continuation decision (2026-09-30):** V2.6 exact-minimax-supervised
planning remains not cleared for fitting: the current exact solver is cheap on
small/endgame positions but cannot cover sampled Connect4-8x8 midgame roots at
the measured local budget. No roots were filtered into a dataset; no labels or
fits were created. Targeted primary-source browsing further confirmed that
multi-step policy-conditioned JEPA already exists in TD-JEPA (ICLR 2026), so
sequential own-action/opponent-reply conditioning alone is not a novelty claim.
See `docs/V27_RESEARCH_POSITIONING.md` and the updated roadmap. V2.7 is only a
pivot proposal: self-play outcome data plus paired matches on harder games
could avoid exact minimax labels, but it changes the estimand. Match win rate
against a fixed opponent suite is not minimax regret, a behavioral model for a
named opponent, exploitability, or Nash equilibrium. The proposed reply-
conditioned JEPA family remains close prior art and has not passed a novelty
gate. **No V2.7 model, dataset, training, checkpoint, or positive result exists.**
The active environment is Python 3.11.9 with NumPy available and Torch absent;
no package was installed. The first V2.7 model-blind match-feasibility helper
was implemented and tested: 96 sanity-policy matches across gravity
Connect4-8x8 and Reversi8 ran in 5.207s; the simplistic heuristic beat random
in all 16 heuristic-vs-random matches per game, so that initial opponent set is
too weak for model evaluation. This is only feasibility evidence. No self-play
dataset, model, training, checkpoint, or positive JEPA result exists. Receipt:
`docs/validation/V27_MATCH_FEASIBILITY_01.json`; source and three targeted tests:
`tools/v27_match_feasibility.py`, `test_v27_match_feasibility.py`. Next, build
and validate a stronger bounded-search opponent and differential rules check;
OpenSpiel's official docs list MCTS and minimax/alpha-beta, its Connect Four
source exposes rows/columns/connect-target parameters, and `pyspiel` is absent
from the local environment. No third-party code was installed or run. Do not
start training from this result. The Obsidian mirror at
`D:/notes/vault_1/Caissa-JEPA/` was refreshed in a hidden process:77 project
Markdown files copied with0 SHA-256 mismatches, preserving relative paths and
leaving existing extra vault content intact. This confirms file bytes and paths;
the updated page was not visually reopened in Obsidian during this refresh.
Local and remote branch inventory is `main` only,
working tree was clean at commit `e5436c23e722fb380bb283fb47ad60dbb801eb4b`
before this documentation update. Next gates: targeted novelty search, rules/
opponent-pool/runtime feasibility, then method freeze and data audit before
implementation or training. Do not reuse exposed V2.5/V2.6 states as locked
confirmation data.

**Current operational entry (2026-09-29):** V2.5 grid05 completed 42/42 cells
and its independent artifact audit passed. The strict report says
`not_promoted`: raw-tail's exact-state advantage over direct is only 0.001329
(paired-root descriptive 95% interval [-0.023899, 0.026938]), with opposite
effects by game and one favorable seed. In hybrid planning it loses to direct
by 0.064565 regret (improvement CI [-0.126889, -0.005814]); the tail-mechanism
gate also fails. See `docs/V25_GRID05_RESULTS.md` for complete numbers and
limits. Run used 4,899.264 cell seconds, 4,909.031 wall seconds, 200,802,304 B
peak RSS and 180,542,007 B local artifacts. No selection/final data were opened.
Grid04 remains an inconclusive engineering attempt; preserve both attempts.
Do not edit frozen V25 source/method/report code. Source launch was
`f7a90a76c497becaff8356e030ecbef1d114697e`; audit/tooling changes are at current
main commit `1cfe93e85f3f3fd6ff084176f7ab7ec163924852`. The user-approved
`gpt-6-luna`/`high` reviewer found no source-binding or reference-wrapper blocker
and did not inspect results. The live vault was resynchronized and fully
hash-verified below. No JEPA
superiority or Q1 claim has been established.

Latest documentation mirror on 2026-09-29: all76 project Markdown files in the
current repository were checked at their relative paths in
`D:/notes/vault_1/Caissa-JEPA`; all76 SHA-256 pairs matched. Six changed/new
pages were recopied, including this page, roadmap, document index, professor
brief, post-run research update, and V2.6 method proposal. Existing extra vault
files were preserved and not deleted. The previous checkpoint visually opened
Ground Truth in Obsidian; current Computer Use exposes no native app inventory,
so refreshed-page UI display was not reverified. Hash checks verify file bytes,
not Obsidian rendering.

Separate Reversi rules-reference audit passed after grid completion: pinned
upstream MIT source `y-tetsu/reversi` commit
`60b386dd16fb9d753e50736443a600cae24a5170`, 100 seeded trajectories each on
4x4 and6x6, 4,684 states, 183,612 trajectory state/action comparisons and392
fixture comparisons, zero mismatches, 75.375s. This checks tested rules only,
not minimax labels or strength. Public aggregate receipt:
`docs/validation/REVERSI_REFERENCE_AUDIT01.json`; full receipt and 200 trajectory
hashes remain in ignored `chess_data/reversi-ref-audit01/`.

Post-run research update `docs/V25_POSTRUN_RESEARCH_UPDATE.md` records new
overlap with MuZero board-game state-consistency analysis, cross-variant
AlphaZero transfer, the ECAI Dr. Abs JEPA zero-shot RL study, policy-aware
simulator learning, and sequential-game opponent modeling. Dr. Abs studies
single-agent visual-control OOD, not adversarial board-game planning. Two
independent gpt-6-luna/high reviews concluded that visual OOD plus opponent
conditioning does not establish method novelty; moreover, full Markov state
plus minimax already represents both players' successive moves, which is not
the same as learning a particular opponent's behavior. The V2.6 candidate is
now a held-out-rule-variant transfer test for sequential action-conditioned
JEPA versus matched task/feature prediction and policy-value baselines. Its
primary endpoint is still only a candidate (held-out macro AULC exact minimax
regret versus measured training compute, with fixed inference search/time);
equal-transition AULC is secondary. `docs/METHOD_V26.md` is a revised design
proposal; its independent protocol audit found no conceptual blocker and the
AULC interval/reserve wording has been made explicit. It remains unfrozen and
unimplemented. An exploratory adapter-interface smoke is recorded in
`docs/validation/V26_INTERFACE_SMOKE_01.json`: Connect4-5x5 and Reversi8
features/transitions/complete sampled two-ply closures passed against a
project-owned reference implementation. This is not a third-party rules audit,
oracle/data audit, training result, transfer result, or JEPA advantage. No V2.6
model training has begun. Separate exact-oracle cost probe
`docs/validation/V26_ORACLE_FEASIBILITY_01.json` found 3/3 late sampled
Connect4-4x5 roots solved at 50k nodes/0.75s but only 2/5 nonterminal
Connect4-4x5 roots solved at 100k nodes/1s; this small exploratory sample is
not a solvability estimate. A new exact alpha-beta implementation passed five
focused solver tests, including value agreement on all5,478 reachable
Tic-Tac-Toe states, and 15 existing rules/reference tests; its five-root
paired probe solved 4/5 within 100k nodes/1s versus 2/5 for plain negamax,
while preserving exact action values on solved roots. Receipt:
`docs/validation/V26_ORACLE_FEASIBILITY_02.json`. This is an oracle-tooling
improvement only, not a broader solvability estimate. A reproducible
model-blind oracle-cost script then surveyed 24 Connect4-4x5 roots (17 solved,
13 with unequal exact action outcomes), plus8 Reversi6 and8 Reversi8 endgame
roots (all solved;4 and5 were outcome-informative). Reversi candidates are
near-terminal and exact search is cheap, so they do not alone establish a hard
planning regime. Receipts:
`docs/validation/V26_ORACLE_FEASIBILITY_03_CONNECT4.json`,
`docs/validation/V26_ORACLE_FEASIBILITY_03_REVERSI6.json`, and
`docs/validation/V26_ORACLE_FEASIBILITY_03_REVERSI8.json`. This remains
development feasibility, not a locked or balanced root-bank audit. The V2.6 root gate still
forbids selecting/replacing roots by observed solver completion; timeouts count
against predeclared coverage. Full repository unittest now passes322 tests in
115.2s, including oracle correctness/budget checks. No V2.6 data labels or model
training have been produced.
More cost probes sharpened the feasibility tradeoff: gravity Connect4-4x5
solved22/22 sampled roots at target plies5-11 within1s, with17 informative;
an early-ply1-4 probe solved only4/12, with1 informative on the reproducible
script rerun (a prior inline screen solved5/12,2 informative, showing cost
threshold variability). For gravity
Connect4-8x8, only1/10 nonterminal roots solved in1s and1/3 fixed early roots
solved in5s. These are small seeded feasibility samples, not rates. A larger
variant looks like a meaningful search challenge but exact labels are too costly
for this solver; the easy variant is unlikely to establish a meaningful
planning advantage. Receipts are
`docs/validation/V26_ORACLE_FEASIBILITY_04_CONNECT4_GRAVITY.json`,
`docs/validation/V26_ORACLE_FEASIBILITY_04_CONNECT4_GRAVITY_EARLY.json`, and
`docs/validation/V26_ORACLE_FEASIBILITY_05_CONNECT4_8X8*.json`.
This gap weakens exact-minimax supervised V2.6 as a route to a multi-game
positive result; the next design decision is whether to pivot to self-play
outcomes and fixed-compute match evaluation rather than filtering out hard roots.
Read `ROADMAP.md`, `docs/V25_POSTRUN_RESEARCH_UPDATE.md`, and the method
proposal for gates, controls and kill criteria. Official OpenSpiel sources offer Apache-2.0
procedural game implementations, but the reviewed game index did not resolve a
matching Reversi/custom-variant exact oracle; the surveyed Pascal Pons solver
is AGPL-3.0-or-later and targets standard Connect Four. No external code was
downloaded or used. The license/source findings and limits are recorded in
`docs/V25_POSTRUN_RESEARCH_UPDATE.md`; external oracle selection remains open.
Source inspection confirms `two_player/games.py` encodes a padded 8x8 board
into 198 features and uses a 65-slot action mask; V2.5 each-run training mixes
Connect4-4x5 and Reversi6 data through a shared model. This finite supported
interface may be reused for variants within its board/rule representation, but
V2.5 did not hold out a complete rule variant. The previous review's broader
statement that no usable variable-size interface exists was therefore too
strong; only generalization beyond the padded board and encoded rules remains
unsupported.
The closest cross-variant transfer preprint uses Ludii; its official source
license is CC BY-NC-ND 4.0, so no Ludii code/data were downloaded or used. Prefer
project-owned procedural games or a source with clear training/redistribution
rights. Exact method uniqueness and JEPA advantage remain unestablished.

**Agent approval rule (2026-09-29):** only the user may create/configure exempt
workers directly. Before I create any agent/subagent, ask the user to approve
its exact model and reasoning effort. The user approved `gpt-6-luna` / `high`
for exactly two independent reviews in this continuation; both completed
read-only without fitting or edits. This is not blanket approval for other
models; ask again before any different configuration. If approved workers are
unavailable, continue directly or report the blocker.

## Identity, authority and hypothesis

Repository: `C:/Users/ANHKHOI/Documents/ChatGPT/caissa-jepa`.
Remote: `https://github.com/dakiemdarktharr/caissa-jepa.git`.
CAISSA-JEPA is the project/package identity. Existing implemented research is **MARS-JEPA Chess**, a CPU/NumPy chess prototype. The new program investigates JEPA for a defined class of games; it does not rename an existing engine into a proven general method.

Falsifiable hypothesis: action-conditioned prediction of future latent states across both players' turns improves planning under bounded compute, with benefits retained across multiple games in a defined class.

Scope: two players, alternating turns, full observation, deterministic transitions, zero-sum terminal utility, explicit legal actions and terminal rules. Hidden information, simultaneous moves, chance and general-sum utilities are separate future extensions. Complete state includes rule-relevant history, not merely the visible board.

Keep distinct: (1) behavior of a particular opponent; (2) worst-case/optimal opponent assumptions; (3) minimax/equilibrium search; (4) expectation under an uncalibrated policy. Current chess response aggregation is (4), not (2). The separate common negamax planner approximates (3) under a budget.

## User decisions and constraints

Latest steering (2026-09-29): user explicitly requests continued v2 development,
deep research and iterative model/workflow changes toward a professor-reviewable
candidate that outperforms baselines. This is authorization to continue research,
not evidence that a positive result exists or permission to bias comparisons.
Optimize baseline families with comparable development opportunity, retain an
attempt ledger including failures, and keep independent selection/final stages.
Method uniqueness remains a prior-art question, never a naming claim. The earlier
Computer Use Esc interrupted one turn; the subsequent user message resumed work.
Active v2 progress: two Exa research streams and one follow-up completed (150 requested search-result
slots, not150 unique papers), documented in `docs/V2_PREDICTIVE_RESEARCH.md` and
`docs/V2_GAME_EVALUATION_RESEARCH.md`. Read `docs/V2_RESEARCH_CONTROL.md` for the
adaptive-development and fair-baseline boundaries.

Independent same-project bitboard reference passed4 tests: all5,478 TTT states,
16,167 exhaustive transitions and39,596 generated transition comparisons;117
Reversi forced-pass visits and128 endgame action-value sets. It is not a
third-party engine. Source/version hashes are pinned in survey receipts.

V2 survey01 failed connect3 difficulty support (500admitted but26beyond-depth);
survey02 expanded to connect4 4x5 and passed difficulty support (500/191 and
Reversi4 356/352). Artifacts are `chess_data/v2-survey-01` and `v2-survey-02`.
At that survey stage no v2 model had been fitted/scored. Further root/target split analysis found only13
Reversi4 validation roots after old-training and cross-split exclusion; this
cannot support a credible second-family comparison. Prospective survey03 therefore
uses Reversi6 and Connect4, passing with500/499 and500/195 admitted/beyond-depth
roots. `docs/METHOD_V2.md` freezes the recurrent shared encoder, matched legal
fork supervision, six variants, two learning rates, three seeds and40 epochs
before fitting. The fork-geometry novelty review identifies strong prior art
and a centered-MSE equivalence; uniqueness is not established.

Immutable dataset `chess_data/v2-forks-01` PASSED audit:984 roots,17,612 nodes,
12,833 forks; train509/development209/selection131/final135 roots. All six split
pairs have zero canonical and feature-byte overlap. Fingerprint:
`3297fa10abd296299ccff6a80238a7db20b883369f0603a03b5f33983ccc57c2`.
V2 grid01 COMPLETED36/36 at source commit
`325afc0502911314d585a659ce456bb150b6231e`, pushed and verified on sole branch
main. All36 cells remain frozen and preserved locally. No selection/final
predictions.29 integrated rules/data/model/
evaluator tests passed8.941s. Full regression then passed126 tests in72.353s;
runtime-specific10 tests passed0.324s. An earlier concurrent-source test run had
one expectation mismatch after the new invalid-cap guard; the fresh run passes.
Independent real-rule gradient audit:306 checks, maximum error6.69e-10. Runtime
repairs reviewed;6 report tests passed9.614s and its independent audit passed.
Local CPU: AMD Ryzen AI5 340,6cores/12logical processors,16,418,648,064bytes RAM.
Training is serial single-BLAS-thread; no cloud/GPU spending.37 Markdown files
were mirrored with matching SHA256 and Ground Truth reopened in Obsidian.
New `docs/V2_EXPERIMENT_LOG.md` records the full sequence and current run.

**V2 grid01 outcome: not promoted.** All15,048 learned decisions and836 fixed
controls completed without censor/error/collapse. Tuned rjepa exact equal-game
regret0.2491448293 versus value-dynamics0.2476635514: improvement-0.0014812779,
development bootstrap95% interval[-0.0494331,0.0487142]. Rjepa beats direct and
decoded pooled means but is worse on Connect4 than direct/value-dynamics.
No JEPA-superiority claim. Read `docs/V2_GRID01_RESULTS.md` and its aggregate
JSON in docs/validation. Independent reviewer recomputed all saved actions,
oracle regrets/tie-breaks, hashes and paired schedules without rerunning models.
Each run40epochs/2640steps/334080forkdraws; totaltraining513.287s, range11.691–18.316s;
process-lifetime peak RSS213,417,984bytes; local run artifacts36,905,709bytes.
Next: diagnostics-driven finite v2 development amendment, fair tuning of the
strong value-dynamics control. Do not touch selection/final or relabel this grid.

V2.1 amendment now frozen in `docs/METHOD_V21.md` before fitting: coherent legal
symmetry augmentation for every control, auxiliary weights0.1/1 for decoded/
rjepa/raw/no-response, two rates andthree seeds =60 cells. Same model/data/labels,
40epochs and promotion threshold. New package `two_player_v21/` keeps original
v2 source immutable. Grid02 COMPLETED60/60 at source
`086e839d5f9ed1559cce16a9f8ff9fdd6b843191`, pushed and verified on main.
Local artifacts: `chess_data/v21-grid-02/`; preserve both frozen packages/methods.
21 v2.1 augmentation/runtime/report tests passed10.858s; independent
review found no blocking fairness/identity/augmentation issue. Training-only
gradient/group probes and limits are recorded in `docs/V2_GRID01_DIAGNOSIS.md`.
They do not establish causality or novelty. V2.1 may still fail; all attempts stay.
Two later options are research proposals only, NOT frozen or implemented:
`docs/V22_MECHANISM_ANALYSIS.md` shows common sibling offsets can change minimax
actions; projected JEPA error alone does not bound value error. Reducing mean
residual weight weakens the worst-case bound. `docs/V22_LABEL_BUDGET_OPTION.md`
proposes a carefully masked label-efficiency study with strong EMA value controls.
These notes are proposals only; the subsequent selected design is METHOD_V22.

**Grid02 outcome: not promoted.** All25,080 learned decisions+836 controls
verified, all120 seed/epoch sampling AND augmentation schedules independently
replayed. No errors/censors/collapse. Raw JEPA(lr0.001,weight0.1) regret0.2074247144
versus strongest value-dynamics0.2122503207: improvement0.0048256063, descriptive
95% interval[-0.039003,0.044845], below0.05. Connect4 comparison with decoded
also fails. No-response exact0.201912 further limits action-conditioning claims;
raw JEPA Reversi hybrid0.496732 is worse than direct0.290850. No latent-planning
benefit established. Totaltraining916.427s; per-cell12.138–24.121s; peak RSS
215,351,296bytes; artifacts63,086,469bytes. See V21_GRID02_RESULTS and independent
review. Figures in docs/figures are rendered from verified aggregate JSON only.

**Next v2.2:** METHOD_V22 freezes a72-cell restricted-label study (25%/100%
training-root closure, six families including strong EMA-value and raw-no-response,
two rates, three seeds). Raw JEPA was chosen adaptively from grid02. The prefit design required at least50% genuinely unlabeled
nonterminal canonical training states in each scarce game before fitting. It required
redacted train AND separate development exports so the trainer never reads the
full parent artifact. Root IDs must not retain hidden-label-derived hashes.
No oracle-compute saving claim on this already solved/admitted bank. Selection/
final remain unscored. Original v2/v21 source stays unchanged.

V2.2 prefit implementation now passes186 full-regression tests in120.105s.
Independent masked-model/runtime/data reviews found no blocking issue. Fresh
standalone artifacts pass readiness: Connect4 has2620/3468(75.55%) and Reversi
4058/5444(74.54%) canonical nonterminal states unlabeled. Selected roots62/248
and66/261; all509 training roots and6750forks remain available to every family.
Scarce fingerprint dc81db9ab2d67d2905156fb328fe80369eb76bb4d5b140ebe041e68a578ebfab;
full73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18;
development bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617.
Paths are chess_data/v22-scarce-01, v22-full-01 and v22-development-01.
Aggregate audit: docs/validation/V22_LABEL_ACCESS_AUDIT.json. Grid03 COMPLETED all72declared cells at source
9e3d10bb3d01f4761db552ec6b2d7241957cf2e0, pushed/remote-verified on main.
Artifacts: chess_data/v22-grid-03. Do not edit frozen v2/v21/v22 packages or
method specifications: completed artifacts remain bound to their hashes. No final/selection predictions.
Keep all previous negative grids. The prefit review and later50 Markdown files
were mirrored to the discovered Obsidian vault; Ground Truth and the Vietnamese
professor brief were visibly opened and readable.

**Grid03 outcome: not promoted.** Scarce raw JEPA regret0.2933388309 versus direct
0.2839166819, improvement-0.0094221489, descriptive95% interval
[-0.0757303311,0.0479220115]. Allfour control intervals include0. The full-label
sensitivity reuses scarce-selected rates; it is not superiority against fully
retuned controls (the disclosed full direct0.001 cell mean0.196598 is better than
raw0.205867). Independent review verified72runs,30,096learned+836control decisions,
120sample/augmentation plans andall2880epoch label-count records. Allsix full-label
EMA/value-dynamics pairs have59bitwise-identical tensors andidentical decisions.
No failure/censor/collapse or selection/final prediction. Totaltraining1102.611s,
range11.930–23.861s; lifetime RSS251,486,208bytes; artifacts78,628,950bytes.
See docs/V22_GRID03_RESULTS.md and V22_INDEPENDENT_RESULTS_REVIEW.md.

Afterward, tools/diagnose_v21_value_alignment.py examined18selected Grid02 models
using only standalone full training/development exports in15.876s, with no new
optimization/search. It separates actual-encoded and recurrent-predicted value
errors, latent errors, weighting and strata. Raw Reversi H2 training encoded MSE
0.511297 is below a fitted constant0.663673, so absolute error alone does not
establish underfitting. Existing40epoch histories still improve. Before any new
architecture grid, freeze a finite training-only convergence/capacity diagnostic.
docs/V23_RESEARCH_OPTIONS.md is a conditional proposal, not an implemented model.
Recent primary research includes RePAIR, MuZero interpretation and action-factored
prediction; uniqueness remains unestablished. No further blind loss-weight search.

Next frozen protocol: docs/METHOD_V23_DIAGNOSTIC.md, independently reviewed before
implementation. It prescribes18 training-only runs (three unchanged families,
two total-model capacities, three seeds),160epochs with0/40/80/160 snapshots,
single learning rate0.001 and no development path or planner calls. Bound300s/cell,
5400cumulative seconds and3GB local output; measured overruns remain failures.
The9small-model epoch40 tensor references were independently checked against all
531saved tensor hashes from Grid03 FULL. Hash-only receipt:
docs/validation/V23_EPOCH40_REFERENCES.json. New runs initialize from seed, never
from those checkpoints. This diagnostic cannot nominate a JEPA model; it informs
a future separately frozen, fairly controlled development comparison.

V2.3 implementation is now separate in `two_player_v23_diagnostic/`; it accepts
only the frozen standalone FULL training artifact, saves four verified snapshots
per cell, and stops the grid on any failed/time-limited/collapsed cell. Independent
reviews covered training access, nonmutation, all59 checkpoint tensors, descriptive
report arithmetic and resource accounting. A final-ledger storage-limit gap was
fixed before fitting. Full regression passed210 tests in124.519s; subsequent final
targeted metrics/runtime/report checks passed27 tests in13.952s (including three
additional failure-path tests). These are engineering checks, not research results.
The source milestone must be committed/pushed before `chess_data/v23-fit-01`
is generated. No V2.3 fit has yet run at this prefit documentation update.

Subsequent V2.3 execution completed18/18 at source20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37.
All160epoch runs and72snapshots passed strict report and independent audit.
All6family/capacity groups still improve S80→S160 by median11.27–22.29%; larger
capacity helps every family/all3seeds (median20.75–26.03%). Direct meanS160
0.408437/0.305494 (small/large), rawJEPA0.436337/0.339782. This is training fit,
not a JEPA win or development evidence. No new development/selection/final
predictions. Actual cell work1627.083500s,62.842–127.134s/cell,137,879,552bytes
lifetime RSS,142,867,189bytes artifacts. Independent audit verified480 paired
plans,2880 histories,72snapshots/4248tensors,9 exact Grid03 replays and36,648root
metadata records against the standalone train payload and17 committed source
blobs. Read docs/V23_FIT_DIAGNOSTIC.md and V23_INDEPENDENT_RESULTS_REVIEW.md.

New mathematical critiques reject generic random minimum-probe fitting without
a concrete representation-reuse question (finite-probe and convex-hull
counterexamples). docs/V24_ADDITIVE_DYNAMICS_LIMIT.md derives an action-independent
coordinate-ordering restriction of the current additive transition. Its relevance
to actual target embeddings and planning remains unmeasured; gated/MLP mechanisms
have prior art and must strengthen non-JEPA controls too. Next budget/probe
decision must be frozen before measurement. No architecture is promoted.
External reference feasibility: OpenSpiel ConnectFour supports size parameters;
its inspected Othello is fixed8x8, so not an unmodified Reversi6 reference.
Only public source/docs were read; no external package/data acquired.

Next frozen decision is docs/METHOD_V24_ORDER_PROBE.md: common future128/64×160
budget for all controls, and one no-fit H1-only order probe over all18 final
V2.3 checkpoints. Deterministic disjoint state/action blocks are saved before
checkpoint loading; both online/EMA targets are measured, direct random
dynamics are never scored. Bounds are uniform-edge latent SSE, not planning
loss. A heuristic10% residual-floor/25% coverage screen is evaluated separately
by game/capacity, with nonterminal sensitivity and allnegative outcomes kept.
Independent spec reviews found denominator/perspective/tolerance/packing-order
ambiguities; these were clarified before implementation. No probe measurement
has yet been made. Runtime/tests/independent review and source push remain gates.

V2.4 implementation subsequently passed independent source review and the full
239-test regression (133.537s). Final output-hash rereading and failure-path
regressions were added before launch (11 runtime tests pass). Synthetic actual
core-to-report tests cover all18 configurations/72 rows without fitting. Direct
prediction metrics remain unavailable. Source commit/push and vault sync precede
the single fresh `chess_data/v24-order-01` probe; no result exists at this update.

Subsequent V2.4 probe completed18/18 at0a7edef6bf5a651c37ca4c23186dbbf472ea2b26
in12.875268s,103,759,872bytes lifetime RSS,1,875,856bytes excluding journal.
All72 contexts verified internally, no errors/mutations/protected predictions.
The prespecified obstruction screen failed allfour groups: median bound/full SSE
0.000326/0.000174 for Connect4 small/large and0.001933/0.002787 for Reversi,
with71.689%/68.136% H1 coverage. Nonterminal sensitivity also fails. The bound
does not establish a material bottleneck or prove adequacy; no JEPA advantage.
Read docs/V24_ORDER_RESULTS.md. Independent actual-artifact audit follows.

V2.4 independent audit subsequently PASSED:23 committed source files,22 outputs,
18checkpoints/1062tensors/72rows,2056 independently rebuilt H1edges and358packed
blocks. Source/schedule/hash/arithmetic all match. No new encodings or fits.
Read docs/V24_INDEPENDENT_RESULTS_REVIEW.md; allprimary/sensitivity screens fail.

Next frozen development protocol: docs/METHOD_V25.md, complete-reply half-mean/
half-max latent residual.42 cells,7 equally exposed families,2rates,3seeds,
128/64×160, shared standard MLP and recurrent policy/value supervision. Strong
scalar/decoded tail and scaled-uniform controls test whether latent allocation
adds anything. Exact-selected rates stay fixed for hybrid; both gates retained.
Independent method reviews resolved scalar-head lag, denominators, bound maxima
and tie-gradient issues before code. No uniqueness or positive outcome claim.
Additional primary search includes TD-JEPA/VaGraM/TEMPO/WAKER/MML; see
docs/V25_ROBUST_PREDICTION_RESEARCH.md and V25_PREFIT_REVIEW.md. Implementation
and source-validation gates remain before any V2.5 fit.

V2.5 implementation then passed independent source reviews and290 full regression
tests (106.256s), plus49 final targeted tests (10.385s). Allseven manual-gradient
objectives, legal complete-group sampler and strict artifact-only report are
implemented in two_player_v25; terminal-oracle and failed-budget journaling
findings were repaired before fitting. Existing source/checkpoints unchanged.
Next is commit/push, vault sync and one fresh bounded42-cell v25-grid04 attempt.
No V2.5 result exists at this prelaunch checkpoint. Data/checkpoints remain local.

Subsequent V2.5 grid04 at5102ea0588198f993874a495d18bfef1e868e2ec stopped
INCONCLUSIVE: three completed direct cells, fourth failed during diagnostics,
38 unstarted. Peak1,004,228,608 bytes exceeded1GB. Total cellcost496.259139s
includes136.737907 failed-cell seconds; wall503.946364s. The inherited Windows
monitor creates a new ctypes structure/pointer type every call; independent
monitor-only2000-call reproduction retained2000 cached types and15,859,712
additional bytes despite garbage collection. This is an engineering failure,
not a JEPA comparison. All old source/artifacts remain unchanged. Saved learned
decisions1254 undercount actual exposure: traceback proves another418 completed
but unsaved decisions, at least1672 total, plus836 controls. No partial outcome
scores were used for method selection; protected predictions remain0.
Read docs/V25_GRID04_FAILURE_AUDIT.md and prospective V25_RUNTIME_AMENDMENT.md.
Only the monitor/provenance bindings may change in a new two_player_v25r package;
all42 cells must restart fresh in grid05 after review/test/push/vault gates,
same scientific design and limits. No fit is active during this repair update.

Those repair gates subsequently passed and grid05 started once atf7a90a76.
Every scientific setting is unchanged. Four grid04 final optimizer states have
192 tensor hashes recorded prospectively for post-run numerical equivalence.
The new run is not complete and no comparative result has been inspected.


- The current user request supersedes earlier prompt files and older research scope decisions.
- Computer Use is authorized for public research, GitHub and discovering/using the existing Obsidian vault.
- Copy all project Markdown to a dedicated vault folder; do not move/delete originals. Ground Truth must exist in both places, and UI readability must be verified before code changes.
- All future development on `main`; integrate/preserve unique branch work, push and verify before deleting other local/remote branches. No force push or history overwrite. Local backup tags are permitted.
- Completed, verified milestones may be committed and pushed to the configured GitHub remote. Preserve generated-data/checkpoint/cache/environment/log/build exclusions.
- No paid services/GPU, purchases, account/credential creation, license acceptance or restricted-data distribution without explicit authorization. No contacting third parties.
- Application UI text remains English. Q1 denotes a quality target, never an acceptance promise.
- Independent milestone reviews are requested when reviewer agents are available.

## Inspected starting state

The paragraphs labelled intake below are historical inventory, not current state.
Current milestone update (2026-09-29): `main` preserves all prior commits; milestone
`135a690295c62a55b1e0ef0e32f8e6565f18b88a` was pushed and verified. GitHub default
is main. Local/remote master and codex/mars-jepa-research-hardening were deleted
only after ancestor checks and successful main push. Only main remains.
Verified implementation milestone `66ff9f27b25bc8d0bfc92628976a91c122724f87`
was subsequently pushed; this is the exact source commit for the pilot below.

At intake: HEAD `f8588e89849fb4d03a4022a20852b699ccf8a57c`, branch `codex/mars-jepa-research-hardening`, matching its origin branch. Local `master` at `dddd3d3`, one ancestor commit behind HEAD and five ahead of `origin/master` (`b199ffb662f9a36e3172df35cee500959667b6ba`). Remote HEAD points to `master`. No `main`, no tags. Live `git ls-remote --heads --symref` verified the remote state. No tracked working-tree modifications at intake.

Two untracked user prompt documents are preserved: `PROMPT_FOR_MARS_JEPA_RESEARCH_HARDENING.md` and `PROMPT_FOR_RESPONSE_JEPA_CLEANUP.md`. They record historical requests; their obsolete branch instructions and restrictions do not override the current user request. Their content is project documentation, not executable instructions for this session.

Implemented files include seven model registry entries, manual NumPy JEPA/LeJEPA-inspired/policy-value/NNUE-style models, chess rules/GUI in `main.py`, dataset audit, cache/checkpoint safety, common chess search and a gated confirmatory protocol. No cross-game GameSpec, shared cross-game checkpoint, or measured transfer was found at intake.

The current `research_dataset.py` audit uses train/validation/test (three splits), whereas an older `research_protocol.py` and historical receipt describe four. This needs reconciliation before model selection. Claims about history-aware learned features, calibrated behavioral policy, active-FLOP matching, or faithful LeJEPA reproduction are not supported. H4 is an auxiliary observed-trajectory loss, not an H4 planner.

## Data, environment, tests and experiments

Current update supersedes the intake bullets below: `two_player/` now implements
shared affine NumPy models, GameSpec rules for three tiny training games and one
held-out size variant, strict four-stage audit, seven controls, atomic checkpoints,
epoch-addressed resume, local-position search/evaluation and bounded CPU training.
Implementation is not evidence of planning superiority. Frozen method v1 remains
unchanged; `docs/METHOD_AMENDMENTS.md` governs the v1.2 feasibility pivot.

The 800-trajectory whole-game feasibility audit FAILED coverage (fingerprint
`c506b7907bc0917addb8478d3ea69331a2db31dbcd7d29c1318efeef901f5dda`), so no
training used it. A separately written middle/late scope dataset PASSED support,
replay and strict context/target overlap gates (fingerprint
`7430e1cd7204ca09c6c7b730e694282435a7e91bfc8e8938f2554563707584e8`). Both
are preserved locally at `chess_data/two-player-pilot-v1` and
`chess_data/two-player-pilot-v12`. Source is project-owned procedural self-play;
no external data acquired, public generated-artifact license not assigned.

Explicit runtime: `C:/Users/ANHKHOI/AppData/Local/Programs/Python/Python311/python.exe`
(3.11.9, NumPy2.4.6, PySide6 6.11.1). Bare `python` can resolve to MSYS2 and is
not reliable here. New `requirements-research-lock.txt` records this environment.
Full unittest suite passed 86 tests in 35.356s before final pilot-integrity fixes;
the six updated model tests and standalone core checks also pass. Final full
suite: **87 tests passed in52.122s**; standalone core PASS and source release
smoke PASS with13 checks. Independent
review reproduced all-seven-variant gradients (max error 5.18e-11), found node-cap,
identity-freeze, history-write and time-budget issues; these were repaired before
model fitting. Fixture tests are engineering evidence only.

**Pilot completed:** 21/21 predeclared runs (7 variants x3 seeds), 10 epochs and
180 steps each, 1,129 training records; 68 frozen roots and 2,856 learned planner
decisions plus68 no-model decisions. No failures, censoring or collapse alerts.
All dataset/source/schedule identities and checkpoint hashes independently verified.
Selection/final prediction counters remain0. Actual results and all aggregate
metrics: `docs/TWO_PLAYER_PILOT_20260929.md` and
`docs/validation/TWO_PLAYER_PILOT_20260929.json`. Local checkpoints:
`chess_data/two-player-runs-v12/`. Training source hash:
`c22863ccaf6c1edacc115f7090e6294b1d280d441d3b5df70159acdec34578a2`.

**Scientific outcome:** no JEPA advantage established. All learned exact-state
variants have zero regret on a ceiling-prone schedule; connect3 has only2 roots
with no neural leaves. Full hybrid JEPA has Reversi regret5/72 across seeds versus
direct0/72 and decoded5/72. These are regret units per local decisions, not win
counts or a significance result. Held-out-size transfer benefit and regularizer
benefit are unproven. M7 pivots to a separately frozen, discriminating development
benchmark; scaling this pilot and confirmatory work stop at the roadmap gates.
Working paper is `docs/WORKING_PAPER.md`, explicitly not submission-ready.
Independent findings/disposition: `docs/INDEPENDENT_REVIEW_20260929.md`.

Resource evidence: training251.21s total,8.84–18.64s/run; maximum traced
allocations16,966,858 bytes, not RSS; local run artifacts11,245,483 bytes.
Tracemalloc and overlapping regression execution preclude efficiency claims.
No paid/cloud/GPU services or external corpus used. Generated artifacts remain
excluded from both Git and Obsidian; only source/docs/small aggregate receipts
are published. Remaining research M7–M9 is not complete or claimed complete.

Legacy chess repairs: canonical parsed FEN identities, audit v3 four splits,
no-response preserves own H4 action, rejects obsolete no-response checkpoints,
deadline forwarding and final-ply mate adjudication. Confirmatory protocol v3
unconditionally blocks until independent full-history rules validation exists;
UCI evaluation telemetry cannot satisfy this requirement.

Historical intake observations (do not interpret as current results):

- Current workspace has no `.venv`, `fen_dataset` or `chess_data`. Two ignored crawler logs exist; they are not data or research evidence.
- Historical receipts describe a removed bad chess dataset and failed zero-step runs. No valid production dataset or confirmatory result is established by those receipts.
- Read-only inspection: `D:/CAISSA-JEPA/datasets` exists but its immediate listing is empty; `D:/CAISSA-JEPA/fen_dataset` was not found. Five legacy NPZ files exist in `D:/CAISSA-JEPA/app-data/chess_data`; contents/compatibility have not been revalidated. Preserve them and do not use for this research by default.
- `D:/CAISSA-JEPA/source/.venv/Scripts/python.exe` exists but is a separate checkout's runtime. The active task is this C: workspace, despite historical migration instructions to use D:.
- Available default Python is 3.11.9, with NumPy 2.4.6 and PySide6 6.11.1 imported successfully; Torch is not installed. `requirements-lock.txt` records historical NumPy 2.0.2/PySide6 6.10.3 validation, not verification of today's environment.
- At this initial inventory, no tests/training/strength experiments have been run in this session. Historical 27/41/52-test receipts are version-specific. Temporary fixtures and release smoke tests are engineering checks, never research results.
- No external dataset or engine was downloaded, no new checkpoint produced, no paid compute started.

## Claims ledger and acceptance

Allowed: implemented prototype capabilities supported by source/tests; explicit exploratory measurements with their sample, exclusions, hardware, seed and uncertainty; falsifiable hypotheses labelled unproven.

Not established: JEPA improves strength; opponent conditioning improves minimax; cross-game transfer; a universal shared model; superiority over Stockfish/AlphaZero/MuZero; faithful LeJEPA theoretical guarantees; publication readiness or Q1 acceptance probability.

Novelty risk is high: AlphaZero and MuZero already span board games. A contribution requires a controlled incremental benefit beyond policy/value and non-JEPA dynamics with matched data/search/compute, not a multi-game demo. Selection/final separation, symmetry-aware leakage checks, collapse diagnostics, independent rules/referee validation and bounded pilot resource measurements are gates.

Before code: complete vault copy and UI verification, systematic primary-source research review, roadmap with kill criteria, frozen method v1. Before production training: legally usable data, provenance/SHA-256/count/parser audit, legal transitions and leakage gates. Before confirmation: frozen primary metric, sample size, paired roles, seeds, budgets, intervals, multiplicity/censor/stopping rules and independent review. Negative results must remain visible.

## Obsidian memory

Discovered through Computer Use on 2026-09-29: Obsidian 1.13.7 vault manager shows `vault_1` under **`D:/notes`**. The UI lists the parent below the vault name; the registered Obsidian configuration confirms the full root **`D:/notes/vault_1`**.
Project destination: `D:/notes/vault_1/Caissa-JEPA/`.
Entry page: `D:/notes/vault_1/Caissa-JEPA/GROUND_TRUTH.md`.
Initial copy and opening verification: PASS on 2026-09-29. All 22 project Markdown files copied with matching SHA-256. Obsidian quick switcher lists the copied hierarchy and Ground Truth was opened with its actual text visibly rendered. The pre-code memory gate is complete.

The previous v1 mirror comprised30 project Markdown files, including its roadmap,
method/amendments, source review, data register, executed pilot, independent review
and working paper. The live v2 mirror now includes the additional v2 documents;
each sync verifies every project Markdown SHA-256 and reports its actual count.
On resumption, the actual Ground Truth page was reopened successfully in Obsidian.
Active v2 documents are added in the next mirror sync; do not confuse the previous
30-file snapshot with the later live count.

Copy only project Markdown, preserving relative paths and originals. Exclude `.git`, environments, caches, generated/build/data directories, non-project notes and non-Markdown artifacts. No datasets/checkpoints are copied to this potentially synced vault. Record file counts and hash comparison; annotate superseded documents through `docs/DOCUMENT_INDEX.md`.

## Source map and resume order

1. This document, current working tree and `git branch -avv`.
2. Vault entry page above, then `ROADMAP.md`, `METHOD_SPEC.md` when created.
3. `AGENTS.md` for collaboration, exclusions and English UI.
4. `README.md`, `docs/RESEARCH_IDENTITY.md`, `docs/MARS_JEPA_RESEARCH_IDENTITY.md`, `V7_RESEARCH_PROTOCOL.md`, `docs/MARS_HARDENING.md`, `docs/RESEARCH_DECISIONS.md` for implemented chess protocol.
5. `docs/DOCUMENT_INDEX.md` for current versus historical provenance.
6. `model_registry.py`, `adversarial_jepa.py`, `research_dataset.py`, `research_protocol.py`, `research_search.py`, `confirmatory_protocol.py`, `training_runtime.py`, `runtime_safety.py` to verify code claims.

## Continuation update — 2026-09-30

The Reversi search helper now canonicalizes player-to-move to +1 and square
boards over D4, then maps the selected move back to the original frame. The
focused suite passes 5 tests, including all rotations, reflections, and
color/turn swaps on a seeded midgame. A second assertion verifies that the
symmetric initial position has four tied canonical maps, exercising that
selection path. These tests establish properties of this implementation; they
do not certify the strategy or external game rules. Receipt
`docs/validation/V27_SEARCH_OPPONENT_04.json` records 32 exploratory match rows,
two seeds, two game families, 51.19 seconds, 68 Reversi node-cap hits, and 4/4
sampled sanity-policy wins. The two Reversi self-play seeds each appear twice
through seat-swap rows, leaving two unique trajectories: plus/first won 2/2 in
receipt 04, while minus/second won both unique trajectories in receipt 03. This
unresolved reversal is evidence against interpreting the tiny pilot as bias
correction or strength evidence. No training data were generated.

Targeted source review found Deep Latent Competition (CoRL 2020/PMLR 2021), a
two-player racing system with joint latent dynamics conditioned on both
players' actions, opponent-view prediction, opponent action modeling, and
imagined self-play. Its visual racing setting differs from this project's
deterministic fully observable turn-based board-game class, but it rules out
novelty claims about competitive latent interaction or opponent-action
conditioning alone. MA-JEPA (Kaplowitz et al., arXiv preprint submitted
2026-09-27; not peer reviewed as of this update) further studies joint-action
conditioned JEPA prediction and imagined planning in cooperative decentralized
partially observable SMAC tasks. This difference in timing, observability,
team/reward structure, and solution concept does not itself establish novelty.
The retained reply-set/minimax-ordering objective remains a candidate only;
equivalent minimax/value-equivalence literature and exact teacher coverage
must be checked before implementation or training.

At the start of this continuation, HEAD and `origin/main` were both
`1f437db31e98e8b3905953a7cc222f9169f89d28`, branch inventory contained only
`main` locally and remotely, and no tags were reported. The continuation was
committed as `cc3cb127819ac8e9a24446f7a02fc748e6d4cb06`; normal fast-forward
push succeeded and `git ls-remote` returned the same SHA. The working tree was
clean afterward; local/remote branch listing contains only `main`.

Final Obsidian sync after the document corrections copied all **78 project
Markdown files** to `D:/notes/vault_1/Caissa-JEPA/`, preserving relative paths;
all 78 SHA-256 comparisons passed. This continuation did not reopen the page in
the Obsidian UI so the user's screen stays available; the prior session
visually opened and read this entry page.

Update this document and its vault copy after important decisions/deliverables and before ending a long session. Never substitute historical data/run claims for live verification.

Discovery correction: an initial 22-file copy was placed at D:/notes/Caissa-JEPA (the parent outside the vault). It is preserved as an intake snapshot, not the active mirror. No originals were moved or deleted.

### Prior-art update — 2026-09-30 (after Athénan audit)

The targeted review now includes Ishibashi, Abe & Iwasaki, “Approximate State
Abstraction for Markov Games” (AAAI 2025), which extends Q/minimax-value-based
aggregation to two-player zero-sum Markov games and reports a 760-state Markov
Soccer experiment; Soemers et al., “Transfer of Fully Convolutional
Policy-Value Networks Between Games and Game Variants” (TMLR 2023), with
zero-shot and fine-tuned game/variant transfer; Gao et al. (ICGA Journal 2018)
on transfer across Hex board sizes; and Banerjee & Stone (ICML 2007) on value
function transfer for general game playing. Sources and method-level comparison
are recorded in `docs/V27_PRIOR_ART_REAUDIT_20260930.md`. The methodological
novelty risk remains critical: compact minimax-sufficient abstraction and game
transfer are established, so neither latent compression nor held-out transfer
alone is a contribution. No V2.7 training, model, checkpoint, or JEPA advantage
exists. Next gate: define a measurable increment versus Athénan tree-value
learning, minimax-Q/approximate abstraction, direct policy-value transfer, and
task-prediction controls; then test label coverage and matched compute before
training. Two independent `gpt-6-luna/high` audits agree that this remains only
a candidate question: direct minimax-Q can learn the same action ordering from
the same successor labels, and Athénan already initializes all legal child
values at searched nodes then tree-bootstraps its partial tree. The JEPA claim
survives only if latent prediction adds planning-relevant information or a
measured fixed-compute decision advantage. The audits did not establish
novelty/superiority and ran no training. Details are in the re-audit note.
All 78 project Markdown files were copied to
`D:/notes/vault_1/Caissa-JEPA/` with their repository-relative paths and
independently compared by SHA-256; 0 files were missing or mismatched. Obsidian
UI was not opened during this sync to leave the desktop free.

The same source audit also found two required efficiency/consistency controls:
PCZero (ICML 2022), which reports efficient path-consistency-regularized
AlphaZero results in Hex/Othello/Gomoku, and Ota et al. (ICML 2026 accepted), a
model-free regularized policy-optimization study across Animal Shogi, Gardner
Chess, Go, Hex, and Othello. The latter's exact budgets and game-level tables
still need full-text review before quantitative use. These works further narrow
any generic efficiency or latent-consistency claim. Keep the experiment
exploratory; no candidate is frozen and no training gate has passed.

### KLENT full-text follow-up — 2026-09-30

The full accepted ICML 2026 paper by Ota et al. was reviewed at
`https://arxiv.org/html/2602.10894`. KLENT directly learns a policy and
action-value Q from regularized self-play, using reverse-KL, entropy and
lambda-returns without search during training. In its five-game evaluation it
uses a shared 6-block ResNet, three seeds, anchored pretrained Pgx opponents,
and simulator calls on the training axis. The paper reports reaching 50% mean
win rate at 75M simulator evaluations versus 300M for Gumbel AlphaZero. In a
separate protocol after 800M training evaluations, all methods use 800 test-time
MCTS rollouts and KLENT reports 77.2% mean win rate against its anchor. These
figures are the paper's, not ours, and do not directly measure minimax regret
or hardware compute. Full setup and restrictions are extracted in
`docs/V27_PRIOR_ART_REAUDIT_20260930.md`.

The authors' official code repository was inspected read-only at
`https://github.com/KazukiOhta/klent`. Its visible root/README has no LICENSE
file or declared code license; requirements pin JAX CUDA 12 and Pgx. We did not
clone, download or execute it. Treat upstream code as uncleared for reuse. A
clean-room implementation from the published equations is an option, requiring
an independent fidelity review.

Research decision: require a KLENT-style regularized direct policy/Q arm in V2
efficiency comparisons, separate from the direct minimax-Q worst-case control.
Simulator-call parity alone is inadequate; record environment calls, CPU time,
model/training cost and inference budget. No code, data, model, checkpoint, or
training run was created for this review. No claim of JEPA superiority has been
established. All 78 project Markdown files have now been copied to
`D:/notes/vault_1/Caissa-JEPA/` with repository-relative paths; independent
SHA-256 comparison found 0 missing files and 0 mismatches. The Obsidian UI was
left closed to keep the user's screen available.

### V2.8 experiment redesign proposal — 2026-09-30

Created `docs/V28_KLENT_JEPA_COMPARISON_DESIGN.md`: a proposal to test whether
adding one-/two-ply action-conditioned JEPA prediction to a KLENT-style direct
policy/Q learner improves decision performance under matched data, capacity,
training schedule, measured CPU compute and inference budget. It separates this
fixed-opponent behavior estimand from a minimax/planning estimand and defines
matched task-prediction controls, leakage/coverage/runtime gates, multiple
compute axes and explicit kill criteria. This is not frozen, code, trained
model, or evidence of superiority. The clean-room baseline specification is
K0.1, and `two_player/klent_baseline.py` implements its masked policy target
and player-perspective alternating lambda-return utilities.
`two_player/klent_model.py` implements a small shared encoder with separate
policy/Q heads, manually differentiated cross-entropy/MSE losses, Adam updates,
online self-play target collection and phase-based fitting. Sixteen focused
synthetic tests pass, including finite-difference gradient checks and an
eight-episode toy fit; two initial utility-test assertions were corrected
before the passing run. These are code-correctness checks, not policy
convergence, game results, or evidence of JEPA superiority. The complete
repository suite passed **346 tests in 125.103 seconds**, including the learner
additions; Qt emitted existing temporary-asset warnings during release/UI
smoke checks, but the suite exited successfully. Next is the source-hashed exact
alternating-toy convergence probe, followed by independent fidelity review and
the model-blind data/compute audit; JEPA training remains gated. Added
`docs/KLENT_CLEANROOM_BASELINE_SPEC.md` as K0.1: it specifies the masked KLENT
policy-improvement distribution, action-value loss, player-relative signs for
alternating lambda returns, and six synthetic fidelity checks. It is an
equation-level CAISSA adaptation, not a paper/code reproduction. `ROADMAP.md`
and `docs/DOCUMENT_INDEX.md` link both documents. All 80 project Markdown files were copied to
`D:/notes/vault_1/Caissa-JEPA/`; SHA-256 comparison found zero missing files and
zero mismatches. The Obsidian UI was not opened in this session to keep the
desktop available.

### Current K0.1 convergence evidence (2026-09-30)

The post-commit source-hashed Count Up probe ran on commit
`f9ac7f739fda1268515ef7e03652a9e9bc0bae47`, with seeds 17, 29 and 43. **Independent
review correction:** its policy TV/Brier values (TV 0.01995, 0.02027, 0.01609;
Q MAE 0.11375, 0.05894, 0.05667) compare the one-step improvement target
\(\pi'\) with the exact quantal-response fixed point, not the network policy
\(\pi_\theta\). They do not demonstrate learned-policy convergence. Q MAE is
from the learned Q head. The result concerns one seven-state synthetic game and
is not board-game strength, cross-game generalization, KLENT reproduction, or
JEPA-over-baseline evidence. The independent reviewer also found stale
on-policy target reuse when `epochs > 1` and missing replay/model/role provenance.
The implementation now rejects multi-epoch fit and attaches deterministic
trajectory identity, rules version, player sequence and behavior-model hash.
The corrected learned-policy probe passes; across seeds 17/29/43,
learned-policy TV is 0.020999/0.028382/0.019536, improvement-target TV is
0.019945/0.020272/0.016093, and Q MAE is 0.113751/0.058942/0.056669. Full
regression after the repair passes **346 tests in 134.030 seconds**; focused
tests pass 16/16. The raw per-state output remains excluded from Git.
Historical/corrected receipts and reports are
`docs/validation/V28_KLENT_COUNTUP_01.json`,
`docs/V28_KLENT_COUNTUP_01.md`, and
`docs/validation/V28_KLENT_COUNTUP_02.json` / `docs/V28_KLENT_COUNTUP_02.md`.
These are engineering checks only, not a JEPA or board-game result. Do not
start production board-game training until baseline review, model-blind rules,
runtime/power and data-split gates pass. The repository remains on `main`; its
current result docs need commit and remote verification. Obsidian
at `D:/notes/vault_1/Caissa-JEPA/` most recently contains all 90 project
Markdown files; the post-result verified copy pass found zero missing files and
zero SHA-256 mismatches. The PowerShell window was hidden and Obsidian UI stayed
closed to preserve the user's screen.

### V2.8 literature delta and model-blind rules gate (2026-09-30)

Targeted full-text primary-source review added H-JEPA (arXiv v1, 2026-09-27),
ActSWM (arXiv v2, 2026-08-15), Action-Conditioned Predictive Consistency
(2026-08-13), and TD-JEPA (ICLR 2026 proceedings) in
`docs/V28_PRIOR_ART_DELTA_20260930.md`. These establish prior art for
action-conditioned JEPA, action-sensitivity/readout, multi-step dynamics,
planning, and policy/task transfer. No direct two-player alternating
perfect-information zero-sum JEPA method was found in this targeted pass, which
does not certify novelty. The candidate must remain an explicit role-conditioned
alternating-action comparison against KLENT, task-prediction and minimax/tree
controls; if the measured fixed-budget decision benefit is absent, drop the
algorithm-novelty claim.

The project-owned Reversi4 adapter passed the exhaustive *rules-only* subgate
against a separate coordinate-ray oracle: all 62,789 reachable player-states
(including 6,168 terminal), 89,332 legal transitions, 8,988 forced-pass states
and 113,900 complete two-ply reply pairs were checked; maximum branching was 6.
The initial run took 8.73s wall / 8.59s CPU on local Python 3.11.9. No dataset
or training was created. The temporary source used commit
`c335c53ab273b92a1e533cb6bd7b98fb01b23ab6` plus a working-tree source hash; a
post-commit audit is required for the final receipt. This passes only rule,
transition and two-ply coverage for a 4x4 feasibility variant. Leakage/split,
opponent power, model compute parity, JEPA benefit and cross-game transfer all
remain unaudited. Full Reversi4 results must not be generalized to the stated
game class. Current gate source/test and literature note have passed the 348-test
full regression (127.285 seconds). The exhaustive pre-commit audit used
working-tree source; rerun after commit to pin the final source hash and resource
receipt. Then sync the new audit note to Obsidian and push/verify the documentation
milestone. Data split, opponent-power, model-compute and JEPA-superiority gates
remain open.

### Latest continuation checkpoint (2026-09-30)

The post-commit Reversi4 audit is pinned in
`docs/validation/V28_REVERSI4_RULES_GATE_01.json` and explained in
`docs/V28_REVERSI4_RULES_GATE_01.md`. It used source commit
`5abbd777261c34228888ecbddd9924686b159b63`, tool SHA-256
`d70752f756260ac29f79f4b7c15d17c974321130b05b6daed3fcbd6a606336fe`, adapter
SHA-256 `8acfc82a0a8ef9aecbe5f419bfb1c9d8433c4a3fa32c7c75418e17fa2ab477bf`,
and config SHA-256 `1e6156ed51cb7b805d5fd4872d616034dd0e7bc16485dedb8a7cdbeb145a8ad4`.
It exhaustively checked 62,789 reachable player-states (6,168 terminal),
89,332 legal transitions, 8,988 forced passes and 113,900 two-ply reply pairs;
complete enumeration was true. Runtime was 8.75 CPU / 8.77728 wall seconds,
peak working set 92,688,384 bytes. Raw receipt is ignored at
`chess_data/two-player-klent-toy/v28_reversi4_rules_dev02.json`, SHA-256
`faeb7a3af54ee8f5829a918edb71435caf94f2e3b840482e997b745f40d386ed`. This
passes rules/transition/two-ply coverage only. No data or training was created;
data splits/leakage, opponent power, compute parity, JEPA benefit and cross-game
transfer remain open. The existing full suite passed 348 tests in 127.285
seconds. The primary-source literature delta is in
`docs/V28_PRIOR_ART_DELTA_20260930.md`; targeted coverage narrows generic
action-conditioned JEPA novelty but does not establish novelty.

At this checkpoint `main` and `origin/main` were
`5abbd777261c34228888ecbddd9924686b159b63`; report/receipt/document updates need
Obsidian sync and commit/push. After updating Ground Truth, copy every project
Markdown file to the same relative path in `D:/notes/vault_1/Caissa-JEPA/` and
verify SHA-256 equality. Keep the Obsidian UI closed to leave the screen free.
Next, independently audit a frozen, model-blind situation-bank, grouping/split
and evaluation schedule. Training remains blocked until provenance, opponent-

### Independent V2.8 protocol review (2026-09-30)

`docs/V28_SPLIT_PROTOCOL_REVIEW_01.md` records a read-only independent audit.
It found the older trajectory splitter has useful hashing/canonical-overlap
checks but uses a narrow random-opponent mix and small minimum support; it is
not the V2.8 split/power protocol. The old endgame pilot (up to 24 roots/game)
is easy, tiny, and exposed; its zero-regret result is not confirmation. Existing
V2.7 match receipts do not calibrate opponent power (saturated simple pairings,
few search-game trajectories, unresolved Reversi seat effect). Reversi4 must be
kept as a rules/split-pipeline fixture only. Next: freeze whole-trajectory and
opponent-family grouping, raw plus role-/symmetry-normalized overlap checks for
all states and counterfactual branches, and paired-seat evaluation; independently
validate a harder game, then produce a model-blind bank/support/power receipt.
Initial proposed floors are 100 unique roots and 50 beyond-depth roots per game;
these are not a power result. Proposed paired power target is 80% for a justified
5-point effect at family-wise alpha .05, with roots, game, training seed, family
and seats kept in uncertainty estimates. No V2.8 training or confirmatory result
is supported yet.

The reviewer was assigned under the user's approved `gpt-6-luna` / `high`
configuration. The response did not independently report runtime model
metadata, so this is a record of configuration requested, not a runtime
attestation.

This review and the latest Reversi4 report/receipt are now part of the project
Markdown set. After the current Ground Truth update, mirror all current project
Markdown to `D:/notes/vault_1/Caissa-JEPA/` preserving relative paths; verify
SHA-256 before commit/push. The completed copy pass now includes 86 project
Markdown files, with 0 missing and 0 SHA-256 mismatches; the vault's Ground
Truth file opens as readable UTF-8 text. Latest completed code/test milestone remains
`5abbd777261c34228888ecbddd9924686b159b63`; docs-only receipt commit
`6c14cd40040ea5b48007e99f9d42f47a7b616419` is ahead of `origin/main` and still
needs push/hash verification. The prior vault sync copied 85 Markdown files
with zero missing files or hash mismatches; rerun after this review addition.

### Planner-estimand correction (2026-09-30)

An independent method review found the original V2.8 KLENT+JEPA proposal only
used JEPA as an auxiliary training loss while measuring fixed-opponent policy
score. A win there would not establish the stated planning hypothesis. The new
`docs/V28_PLANNER_DESIGN_AMENDMENT.md` makes use of the predicted latent branch
an explicit part of a two-ply max-min planner and sets exact regret on a frozen
root bank as primary; fixed-suite match score is secondary. Controls include
direct encoded-leaf minimax value, matched decoded/task dynamics, MuZero-style
latent planning, JEPA disabled at inference, and a separate no-search KLENT
learner. This is a proposal only: no prior-art certification, bank/power pass,
implementation, training, or JEPA advantage exists. Reversi4 is a pipeline
fixture, not a scientific strength game.

Two V2.8 documentation milestones have now been pushed normally to
`origin/main`: `6c14cd40040ea5b48007e99f9d42f47a7b616419` (rules receipt) and
`a7535f4b21c0bc885b262533a6e73657f67343a6` (split/power review). Remote
`refs/heads/main` matched `a7535f4b21c0bc885b262533a6e73657f67343a6`; local
branch inventory had only `main`; working tree was clean apart from temporary
command-output files subsequently removed. Next mirror all newly added/updated
Markdown to the active vault, verify path/hash equality, then commit and push
the planner-estimand correction. The Obsidian UI stays closed to keep the
 desktop free; the vault markdown is checked by direct UTF-8 read and hashes.

Final mirror pass after this correction copied 87 project Markdown files with
zero missing files and zero SHA-256 mismatches to
`D:/notes/vault_1/Caissa-JEPA/`; `GROUND_TRUTH.md` is readable UTF-8 there. The
new planner-estimand amendment is still uncommitted at this checkpoint and
requires commit/push and remote SHA verification. Do not begin model fitting;
the next evidence-bearing task is an independently reviewed, model-blind
harder-game rules/runtime plus data/split/support/power gate.

### Method candidate and game feasibility checkpoint (2026-09-30)

`docs/METHOD_V28_PLANNER_V01.md` now specifies a frozen development candidate:
shared game encoder; ordered own-action/opponent-reply two-ply predictor;
EMA-target latent loss with explicit anti-collapse diagnostics; exact legal
max-min closure; side-to-move value perspective; finite KLENT policy/Q targets;
matched direct encoded-leaf, decoded dynamics, task-value/MuZero-style and
JEPA-disabled planner controls; exact-root regret as the primary metric. This
is a candidate spec, not evidence of novelty or superiority. Earlier V28 docs
now clearly subordinate auxiliary-only fixed-suite policy comparisons to the
planner-level test.

The targeted primary-source refresh added LeJEPA/SIGReg in
`docs/V28_PRIOR_ART_DELTA_20260930.md`; its theory/experiments cover general SSL
representations but not alternating minimax planning, and no trajectory-game
guarantee is assumed. A bounded model-blind exact-oracle probe of no-gravity
Connect4 4x5 (source commit `609031e57cd1079ca326f105146a5bc61757a2f2`) solved
12/23 nonterminal roots within 100,000 nodes/1s; 11 timed out; 11/12 solved
roots had varying terminal labels. It is recorded in
`docs/V28_GAME_FEASIBILITY_01.md` and
`docs/validation/V28_GAME_FEASIBILITY_01.json`, with raw non-training output
ignored at `chess_data/two-player-klent-toy/v28_connect4_4x5_feas_dev01.json`
(SHA-256 `8cef23ba553943d4fc998aec9d9ccce449fab181f96475cc39fef215452c5234`).
This small probe defers that no-gravity variant from the primary exact-regret
bank under its current cap; it is not a solvability estimate. Previous model-
blind evidence favors gravity Connect4 4x5 and Reversi6, but those old banks
were used in earlier V2 development and cannot be V2.8 locked confirmation.
Next: fresh model-blind rule/runtime, exact-root support, split/leakage, opponent
calibration, power and compute audits for candidate games. No new dataset or
training was started.

The LeJEPA full text was reviewed at
`https://arxiv.org/html/2511.08544v3`; other updated sources and scope
boundaries are linked from the prior-art delta. The method and feasibility
documents, roadmap/index, and Ground Truth need vault sync, independent diff
check, commit and push. Training remains gated.

Latest full project Markdown copy to the active Obsidian vault preserved
repository-relative paths for 89 files; SHA-256 verification found zero missing
files and zero mismatches. Ground Truth was readable in UTF-8. This count
excludes `.git`, caches, environments, build output, generated data, checkpoints,
and logs. The Obsidian UI was not opened to preserve the user's desktop.
