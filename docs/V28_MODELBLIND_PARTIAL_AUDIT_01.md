# V2.8 model-blind proxy partial audit 01

**Date:** 2026-10-01


**Review:** independent, read-only, gpt-6-luna / high

## Artifact identity and integrity

The preserved ignored artifact is `chess_data/v28_modelblind_proxy_v01_full.jsonl.tmp`, 98,901,756 bytes, SHA-256 `701e3f15ef2fe21bf4c43fc60d4cdf5e2457223aee667f246718a54f19b91637`. It contains 4,839 newline-terminated JSON records: one manifest and 4,838 outcome blocks. All lines parse; block IDs are unique and map to exact schedule positions 0 through 4,837; the manifest schedule hash agrees with the current 9,600-block schedule. There is no final output, `.partial.jsonl`, or runner receipt. The process and watchdog no longer exist and no watchdog terminal report was found.

The artifact's runner-source SHA (`96b7d24d3583d07bd84d6c000ee45fa7455cfb3ae4548d4fdb2cb4e24c593fbd`) differs from current tracked runner source (`8aabca47ae6835666acd7d2b6ac5373c8b0f7c8c1808102811f09b90d88669be`). All rows use an older game-record schema that current `verify_block` rejects unless missing role/family fields are inferred. With those fields supplied only for audit, 4,837/4,838 blocks replay against current rules and stored state hashes. One reversed-tape Connect4 block, schedule index 4,665 / match seed 33,002,265, records an opponent timeout but lacks `forfeit_details`; its outcome cannot be validated. The original bytes remain untouched.

## Descriptive diagnostics only

The first two schedule cells are Connect4. For independent-tape self-play, all 2,400 blocks replay: mean paired score difference `d = -0.00917`, sample SD `0.30114`, with 545 positive, 1,250 zero and 605 negative blocks. For reversed-tape self-play, 2,399 blocks are verifiable after excluding the malformed timeout: mean `d = +0.00917`, sample SD `0.30120`, with 605 positive, 1,249 zero and 545 negative blocks. The near-opposite results are consistent with relabeling roles/tapes in same-policy self-play. They are not an effect of JEPA or of a distinct treatment.

The 38 Reversi rows are only the beginning of its independent-tape cell and are insufficient for an outcome or runtime population estimate. The Connect4 cell timings are descriptive for this exact schedule and machine: independent-tape blocks average 1.372 seconds wall / 1.286 CPU; reversed-tape blocks average 1.752 seconds wall / 1.585 CPU. Do not treat these consecutive scheduled prefixes as confirmatory or use them to claim power across games.

## Disposition

Preserve this file and hash as exploratory evidence. Do not append to or resume it, because its process termination is unexplained and its source/schema differs from the current runner. It establishes that the current full 9,600-block plan needs careful runtime monitoring, while its partial Reversi cell leaves the cross-game variance/runtimes unresolved. Any rerun must use a fresh artifact name, the committed current runner/schema, an explicit CPU cap, and a recorded terminal status. This proxy experiment still compares project-owned bounded-search policy with itself under different RNG-tape assignments; it is not a JEPA-versus-baseline experiment.
