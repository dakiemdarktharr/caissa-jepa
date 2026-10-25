# CP-01 data foundation review — 2026-10-25

## Decision

**CONDITIONAL PASS for one bounded, model-blind development-data feasibility batch only:** 100 development episodes (50 per game, each considered for one preselected reference root) plus 64 training episodes. This is not corpus acceptance, Review 2 pilot approval, or authorization to fit a model. The current checkout is dirty, and `tools/counterplay_data.py::prepare` correctly refuses to run from it. The lead must first publish a clean pinned checkpoint containing the reviewed files, then run the exact frozen recipe and retain its receipt. No corpus or scientific result was generated in this review.

## Reviewed identity

Base commit: `5378c0ce3c51fb1a04723a2b2b30d4a573d953a0`.

| File | SHA-256 |
|---|---|
| `research/protocol.yaml` | `7c15ea31d090eec96e439812657559e205ec89e4f4d2de67dc5afe32fb1a1adc` |
| `research/data_contract.json` | `4c84250c3737a9a75bd63ab61e91f40d851b9a0136b465931f6897d8b16ac0bd` |
| `counterplay/data.py` | `190c90ae97e4fcd0c81bf42ad4a7c8aabe0def780c5262c030c72474b83c5081` |
| `tools/counterplay_data.py` | `36a645feccb9dc6754b0ffba6be2dee290aa4fe4e535dfdc4b3eb718a197c922` |
| `tests/test_counterplay_data.py` | `45dde74ef7ad3964db3591178afefaca97bf5dda1841d97108f2580653df096b` |
| `tests/test_counterplay_data_producer.py` | `f4fa5eb80b0e6bb61e487a7ce6884c3dae76dc4b54e22102624b2a754a99da43` |
| `benchmarks/reference_rules.py` | `916a08f68cb2be60529b8d134cdea448f2d53aeb24d6ad5bc775699e9918ce9e` |
| `two_player/games.py` | `fbdce0893f6dcc76d30b71d4391842abbcd7c15a0d1a9e20c40077457e273d3a` |
| `two_player/v28_data.py` | `555ec047fcc06a1d4a71f02b4744181afcd68b237173288191b8d790e78904dd` |
| `two_player/v212_trajectory_audit.py` | `06b97d3beb952b8fd41a3a3d58a1961d37cbf4ca26d064ef549c90812bb32664` |
| `two_player/v212_window_batch.py` | `3d4f697fe4057f9c035979bd92fcfda8ef17af5c12241ace45fd88e5c596c3dd` |
| `two_player/v212_model.py` | `93cc56127aebf2934670ecf7c18d2204565b9c85e4ef660394b98df7282eb7bf` |
| `research_ledger.py` | `30a21b787ba5072dbf60424fcb21489630e55e45e97c57d97e82f25640e29d0d` |
| `.gitignore` | `7f5f66ef12d0528a342debde6d330e0e31bf1f639a22f6d8dca9c96dcb84be25` |

These are working-tree hashes, not a claim that the files are in the base commit. A later source change requires a fresh review of the changed identity.

## Findings

- The implementation matches the CP-01 v2 reference semantics in the reviewed paths. `solved_fork` enumerates every legal first action and every legal opponent reply, uses exact terminal utility from the original root player's perspective, keeps terminal first moves as exact one-entry branches, and raises instead of returning partial tables. The critical-pair rule selects a nonterminal unique worst reply only when the same action has a qualifying noncritical nonterminal control and the reference gap reaches 0.5. Candidate roots are hash-selected before solving, duplicates are counted without replacement, and failed references remain represented in raw root rows.
- Episode generation is role-seeded and deterministic; each episode is replayed against both project rule implementations, including legal-action and transition comparisons at every retained state. Window extraction requires four transitions and a nonterminal fifth state, removes all selected evaluation-root collisions, canonicalizes symmetry/role-swapped paths, retains duplicate source IDs, and deterministically caps unique windows. The build records episode-policy counts, exclusions, selected counts, action/actor/ply support, reference yield, and root failures. Shared openings are allowed and whole-tree disjointness is not claimed.
- The current `.gitignore` ignores `chess_data/` (`git check-ignore` confirmed it), and the producer writes raw payloads and the ledger there. The producer rejects dirty source, non-frozen seed, wrong destination prefix, and non-single-thread BLAS/OMP settings. It binds code and input hashes, preserves data/receipt files exclusively, and writes success/failure events to the durable ledger. Its source guard checks the `chess_data` path prefix rather than asking Git whether that exact destination is ignored; add a `git check-ignore` assertion before a future generation if the storage rule changes.
- **Contract audit gap before corpus acceptance/training:** `research/data_contract.json` requires target-count support in the split audit, but `build` records action/actor/ply counts only. Four-step nonterminal eligibility logically guarantees H1/H2/H4 availability, and the batch adapter verifies masks in synthetic coverage, but the production receipt does not publish those counts. Add per-game/role H1/H2/H4 valid-target counts (and terminal/missing counts, even if zero) before calling a generated corpus accepted or using it for training.
- The frozen producer tests exercise success, injected build failure, low-yield status, output hash binding, timing exclusion, dirty-source/thread guards, and path rejection. They mock `build`, so they do not establish real-recipe yield, full-run RSS/time, or end-to-end corpus acceptance. Current ignore behavior is verified independently. Exact corpus yield, reference-cost distribution, and window support remain unknown until the bounded batch runs.
- The bitboard reference and `two_player` adapters are independently written implementations in this same repository. Tiny tic-tac-toe values are also checked against a separate exhaustive traversal, and the production-game synthetic tests exercise rule parity and forced pass. This is differential engineering evidence, not third-party engine validation.

## Verification and closure

Ran `.venv/bin/python -m unittest discover -s tests -p 'test_counterplay_data*.py' -v`: all 9 tests passed. The system `python` lacks NumPy; the repository `.venv` was used. No full corpus, locked data, or model fitting was run.

Before the feasibility batch: commit/publish the reviewed source as a clean pinned checkpoint, then run the producer with the frozen contract and unique destination/receipt/run ID; retain the raw payload locally and the compact receipt/ledger snapshot for review. Stop on either failed construction gate and preserve the attempt. Before any training: add the target-mask counts above, review the measured yield/resources and payload identity, and obtain the separate integrated Review 2 decision. Do not generate locked data; that remains gated on Review 3.

## Addendum — target-count correction re-review

Reviewed the targeted working-tree change after checkpoint `0385d69f8d1983015a8c4f36f0a8170eb6fd9257`. `selected_windows` now classifies every raw candidate for H1/H2/H4 as valid nonterminal, terminal-masked, or missing/truncated; emits selected-bank counts for the same three categories; and `build` records retained episode counts after cross-role duplicate exclusion. Selected-bank valid counts are derived from the existing invariant that a selected item has exactly four transitions and a nonterminal fifth state. The tests reconcile the three raw categories to `raw_windows` for each horizon and assert all selected items are valid with zero terminal/missing masks. This closes the target-count audit gap for the bounded data receipt.

Current working-tree hashes: `counterplay/data.py` `18245686841335715f2bb31eaee886f74b8eea749302d306a488a161221439a5`; `tests/test_counterplay_data.py` `04f7419db21a156a453f286aa0ba57b3601a13b81701b5a1ade4262d5981eeae`. Other reviewed identities above are unchanged. Re-ran `.venv/bin/python -m unittest discover -s tests -p 'test_counterplay_data*.py' -v`: 9/9 passed in 0.616 seconds.

**Updated decision:** conditional pass remains for one model-blind feasibility generation only. These correction files are currently uncommitted on top of checkpoint `0385d69`; because the producer requires a clean source tree and pins the code commit, publish these exact reviewed hashes in a new clean checkpoint before running it. This addendum does not grant pilot-training or locked-data approval.
