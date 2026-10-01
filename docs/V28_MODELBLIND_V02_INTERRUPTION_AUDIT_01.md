# V2.8 model-blind proxy pilot V02 interruption audit

**Date:** 2026-10-01

**Disposition:** incomplete exploratory run; no power-gate result and no JEPA comparison.

## Run identity and outcome

The hidden watchdog launched the current committed model-blind proxy runner for
the locked 9,600-row schedule. At launch, the runner source SHA-256 was
`8aabca47ae6835666acd7d2b6ac5373c8b0f7c8c1808102811f09b90d88669be`, and the
schedule SHA-256 was
`80a5f741c6bf94e4fb93664e503158a91e959c28015b45e2a9ba9d28e4fe084f`. The
configured CPU cap was 14,400 seconds. The run stopped after 616 outcome rows
(schedule indices 0–615) and the runner preserved its temporary JSONL as
`chess_data/v28_modelblind_proxy_v02_current.jsonl.partial.jsonl`.

The preserved artifact is 12,637,953 bytes, SHA-256
`B0EDD59C509EFD4DA4C970F76A06740E843FDA50F82CE8086A2EF897C17DA9C0`. It
contains one manifest and 616 outcomes. All rows form the exact schedule prefix
with no duplicate or unknown index. The manifest binds the current runner and
schedule hashes. All 616 outcomes pass the current `verify_block` replay,
transcript, score, finite-runtime, and required-field checks. This validates
only this prefix; it does not make the run complete or estimate JEPA's effect.

There is no final artifact, receipt, or active runner/watchdog. No V02 file was
resumed, overwritten, or deleted. The earlier V01 partial remains separately
preserved and is not combined with V02.

## Interruption evidence and limits

Runner stderr is 552 bytes (SHA-256
`99BE5DA7E06E9B22851949A06568FACC54B1D9263985CD9F1A989EDAA6A5A338`). It
contains a Python traceback through `run_pilot(...)`, followed by the
interpreter's `object address` and `object refcount` diagnostic, but omits the
exception type and message. Runner stdout is empty. The watchdog status file
still says `running`; its `.json.tmp` is empty. Watchdog process stdout and
stderr are empty. No matching Windows Application Error/WER event was found in
the inspected recent event window. The original watchdog log from its first
launch records `ModuleNotFoundError: No module named 'tools'`; that watchdog
was replaced with a corrected launch that successfully started the runner.

These facts show an abnormal early stop and incomplete terminal reporting.
They do **not** establish the exception or which process stopped first. Do not
attribute the stop to the CPU cap, a software defect, user input, or the
execution host without further evidence. The watchdog's stale status and empty
temporary status file show that terminal-state capture itself did not finish.

## Decision

Treat V02 as an interrupted prefix and preserve it for audit only. Do not append
to it, count it as a completed runtime/power gate, or use its descriptive rows
for a treatment or superiority claim. A future run requires a fresh output
identity, preflight that verifies no collision, current code/schedule hashes,
independent process liveness/terminal monitoring, durable periodic progress,
and a terminal receipt. The exploratory proxy run remains distinct from the
locked learned-model evaluator. Production training remains blocked.

## Provenance

Run-control evidence was retained under `%TEMP%` on the originating Windows
host: `caissa_modelblind_v02_launch_record_02.json`,
`caissa_modelblind_v02_watchdog_status.json`,
`caissa_modelblind_v02_watchdog_status.json.tmp`,
`caissa_modelblind_v02_runner_stdout.log`,
`caissa_modelblind_v02_runner_stderr.log`,
`caissa_modelblind_v02_watchdog_process_02.out`, and
`caissa_modelblind_v02_watchdog_process_02.err`. These transient host logs are
not tracked in Git. The ignored partial data artifact stays local and is not
copied to Obsidian or GitHub.
