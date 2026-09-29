# Data provenance and license register

Reviewed 2026-09-29 from official hosts. No external dataset downloaded in this milestone; counts below are source descriptions, not locally audited counts. Public access alone does not authorize training/redistribution. Dataset, engine source, binary and weights can have different licenses.

| Source / owner / original URL | Rights and attribution | Format, scope, quality and decision |
| --- | --- | --- |
| [Lichess open database](https://database.lichess.org/), Lichess contributors | Official page explicitly releases exports CC0 and permits modification/redistribution/research. Cite Lichess and export date despite no attribution condition | PGN games, puzzle CSV and evaluation JSONL. Game exports can supply trajectories/outcomes; evaluation FENs omit clocks/history and mix Stockfish versions/depths. Puzzle first move belongs to the opponent. Record exact chosen archive SHA, month, variant, time control, player/event/game IDs and source policy. Not yet acquired; no assumed sample count |
| [Connect-4](https://archive.ics.uci.edu/dataset/26/connect%2B4), John Tromp / UCI, DOI 10.24432/C59P43 | Official page states CC BY 4.0; retain creator/DOI/license and modification notice on derived shares | 67,557 positions, 42 categorical board features; eight-ply nonterminal positions with game-theoretic labels. Not complete trajectories and not human behavior data. Useful independent value/solver checks, not direct H1/H2 training without regenerated transitions. Not acquired |
| [Tic-Tac-Toe Endgame](https://archive.ics.uci.edu/dataset/101/tic%2Btac%2Btoe%2Bendgame), David Aha / UCI, DOI 10.24432/C5688J | Official page CC BY 4.0; cite creator/DOI/license and changes | 958 terminal boards, nine features, binary X-win label. Does not provide nonterminal actions or balanced WDL labels. Do not mistake negative class for draw. Candidate rules verification, not trajectory learning. Not acquired |
| [OpenSpiel source](https://github.com/google-deepmind/open_spiel/blob/master/LICENSE), Google DeepMind and contributors | Apache-2.0 code license; preserve LICENSE/NOTICE/modified-source notices when applicable. Outputs require their own provenance; code license does not automatically certify third-party data | Candidate independent rules/solver implementation for multiple games. No binary/package downloaded. Pin revision and game parameters before use |
| [TWIC](https://theweekinchess.com/), publisher Mark Crowther | Not cleared in this review: no training/redistribution license verification completed | Historical repo crawler support is not authorization. Do not acquire/train/republish through it until rights are clear |
| Project-owned procedural self-play, source tree in this repo | User authorized creating research code and data. No external dataset/engine code copied for new tiny-game generator. Private/local generated outputs only; public artifact license must be set by owner before distribution | Record generator source SHA, commit, rule version, seed, policy mixture, initial state, ordered actions, outcome and exact counts. Label as synthetic policy/self-play, never human games. First CPU pilot uses this path to avoid external data/credential dependencies |

## Required immutable manifest

Schema/objective/parser/rules versions; source owner/URL/license/attribution/review status; code SHA and commit (provenance distinct from data identity); source SHA-256 and sizes; generated policy/seed/config; raw and retained games/positions; duplicate/illegal/unfinished counts and reasons; ordered trajectory identity; symmetry-canonical context and target identities; four split assignments; holdout game/variant; derived-content hashes. Hash identity excludes timestamps and unrelated documentation commits.

Audit reconstructs every transition and outcome using exact rules, validates action legality and targets, verifies counts/hashes, and quarantines exact or symmetry-equivalent duplicate trajectories. Assign trajectories/groups before extracting records. Keep train/validation/model-selection/locked-final-test separate. All H1/H2 targets participate in cross-split overlap checks. Common initial states are not silently exempt: omit conflicting records with explicit counts or use a separately declared shared-start evaluation protocol. A small game may lose most data under strict disjointness; this is a feasibility result, not a reason to disable the audit.

No production training until audit passes. Training never consumes selection/final rows. Development may inspect validation; model-selection is a separately recorded stage. Locked final predictions remain unopened until method/budget/sample-size freeze. Dataset audit may inspect identity/legality without using final performance for selection.

Generated data, caches, checkpoints and detailed logs stay under ignored `chess_data/` or `build/`; do not add binary artifacts to Git or Obsidian. Publish only source, configurations, small aggregate receipts, hashes and reproducibility instructions until a separate storage/license plan exists.

## Executed V2 data lineage

The later V2 studies use project-owned procedural Connect4 4x5 and Reversi6
positions with complete legal two-ply forks, not human trajectories. A separate
same-project bitboard implementation supplies exact minimax labels; this is not
a third-party engine. `V2_SURVEY_RESULTS.md` and `validation/V2_FORK_AUDIT.json`
record generation, exclusions, oracle costs and source hashes. The immutable
bank has 984 roots: 509 training, 209 development, 131 selection and 135 final.
No selection/final predictions have been made.

V2.2 derives standalone training exports with identical 509 roots, 9,237 raw
nodes and 6,750 forks at two label-access levels, plus a separate development
export with 209 roots, 3,756 nodes and 2,735 forks. The scarce export selects
62/248 Connect4 and 66/261 Reversi root closures. Canonical nonterminal labels
are retained for 848/3,468 and 1,386/5,444 states respectively; terminal utility
is free from the rules. Hidden nonterminal values/policies are removed before
the trainer receives the artifact. See `V22_PREFIT_REVIEW.md` and
`validation/V22_LABEL_ACCESS_AUDIT.json` for byte, mask and parent fingerprints.

These exports inherit the same locally authorized procedural provenance and
unassigned public artifact license. Restricting access to previously computed
labels does not save their original computation cost. No external corpus,
licensed engine package or checkpoint was acquired for these studies. None of
the generated datasets/checkpoints is included in Git or the Obsidian mirror.
