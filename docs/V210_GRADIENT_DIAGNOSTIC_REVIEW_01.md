# V2.10 gradient diagnostic independent review

**Disposition:** accepted as a train-only mechanism diagnostic; stop the gradient-conflict candidate. No P1 or P2 finding remains.

The reviewer checked `chess_data/v210_gradient_dev06/gradient_alignment.json` against the frozen screen in `METHOD_V210_GRADIENT_DIAGNOSTIC.md` and the 300-root support amendment. The artifact has the complete 20-seed × two-game × ten-batch grid (400 batches, 30 roots per batch, 12,000 root observations), zero invalid or skipped roots, finite gradients/cosines, reconciled terminal/nonterminal branch counts, and a maximum relative error of **5.15×10⁻¹⁸** between summed component gradients and the existing aggregate gradient.

The current source, fit-spec and panel hashes match their files. The checkpoint and receipt hash maps each contain 20 valid SHA-256 entries keyed to the frozen seed list. To preserve the diagnostic's weights-only boundary, the reviewer did not reopen checkpoint bytes or metadata and did not inspect training histories, V08, or locked-final data.

The reviewer independently recomputed each game-level median, seed-cluster t interval, persistent-conflict count and gate Boolean:

| Game | Median cosine | 95% seed-cluster CI | Seeds with conflict in ≥6/10 batches | Screen |
| --- | ---: | ---: | ---: | --- |
| Connect4 gravity 6×7 | −0.0293 | [−0.0483, 0.1560] | 13/20 | Fail all three criteria |
| Reversi6 | −0.0402 | [−0.0651, 0.1064] | 12/20 | Fail all three criteria |

Both games miss the predeclared median threshold (below −0.05), confidence-interval threshold (upper bound below zero), and persistence threshold (at least 15/20 seeds). `stop_gradient_conflict_candidate` is therefore the correct frozen decision. Do not fit a gradient-projected variant or select a subgroup post hoc.

The result tests gradient alignment on these checkpoints and audited train roots. It does not identify a cause for V2.9's development match result and says nothing about strength, JEPA superiority, equilibrium quality, transfer, or Q1 readiness. The complete machine-readable record is [the diagnostic artifact](validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json).

The first full-compute attempt (`dev05`) completed its gradients but failed while assembling the result because its aggregate-gate code treated Boolean criteria as mappings. It wrote no artifact. A unit test now covers both passing and failing gate aggregation, and the diagnostic was rerun to a fresh output root (`dev06`). This reviewer checked the successful rerun only.
