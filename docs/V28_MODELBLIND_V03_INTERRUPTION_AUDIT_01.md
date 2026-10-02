# V2.8 model-blind proxy V03 interruption audit

Date: 2026-10-02

## Disposition

V03 did not complete. Preserve its output unchanged as an incomplete, exploratory
runtime artifact. Do not use its outcomes to estimate a JEPA treatment effect,
power the learned-model contrast, or authorize confirmatory evaluation.

## Evidence

- Intended schedule: 9,600 proxy blocks; schedule SHA-256
  `80a5f741c6bf94e4fb93664e503158a91e959c28015b45e2a9ba9d28e4fe084f`.
- The temporary JSONL contains one manifest and 3,581 outcome rows. Its size is
  73,806,339 bytes and SHA-256 is
  `32a40d88517faf58a5aac87686c06850bad74658a4cf5a977a8d3fe6c4447b39`.
- A separate prefix audit parsed every row, confirmed ordered schedule identity,
  and replayed every recorded game and score: 3,581/3,581 verified, zero
  failures, no duplicate or out-of-order block. The manifest's runner SHA-256
  is `8aabca47ae6835666acd7d2b6ac5373c8b0f7c8c1808102811f09b90d88669be` and
  agrees with the current pilot entry point.
- The last supervisor sidecar says `running`, heartbeat
  `2026-10-01T13:05:35Z`, elapsed wall time 4,202.921 seconds, CPU cap 14,400
  seconds, and runner PID 52,724. On 2026-10-02, the supervisor, runner, and
  completion watcher PIDs (21,940, 52,724, and 18,696) no longer existed.
- There is no final artifact, receipt, terminal sidecar, or independent
  completion report. Both runner logs are empty. The termination cause is
  unknown; the stale `running` status is not terminal evidence.

The prefix audit output is local under `%TEMP%` as
`caissa_v03_prefix_audit.json`; the ignored source artifact remains under
`chess_data/v28_modelblind_proxy_v03_current.jsonl.tmp`. No partial outcome
statistics were inspected for model selection.

## Scientific and workflow consequence

Both seats in V03 use the same bounded-search proxy. The two RNG-tape designs
can describe this proxy's paired-score variation and execution cost, but cannot
estimate the treatment contrast or sampling variance for reply-set JEPA versus
learned non-JEPA controls. A full 9,600-block completion would therefore not
answer the gating question previously assigned to it. Development fitting is
now governed by `V28_DEVELOPMENT_FIT_AMENDMENT_01.md`: only the audited train
split is available to fitting, development evaluation remains separate from
the locked V08 schedule, and this interruption provides no confirmatory gate
pass. The original partial remains immutable.
