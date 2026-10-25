# Copy-ready continuation prompt

**Historical prompt:** its superiority objective and unassigned agent models
have been superseded by the [Counterplay startup prompt](../COUNTERPLAY_AGENTIC_START_PROMPT.md)
and current `research/STATE.md`. Preserve this text as historical context.

Paste the following into the new project/chat after opening or cloning
https://github.com/dakiemdarktharr/caissa-jepa (branch `main`):

```text
Continue CAISSA-JEPA from its master handoff. Read AGENTS.md,
MASTER_HANDOFF.md, docs/handoff/VERIFICATION_2026-10-25.md, and the source
inventory first. Verify the current branch, remote, HEAD, working tree and
available environment before changes; the repo may have advanced since the
handoff. Then read METHOD_SPEC_V212.md (adopted v06), the V06 Adam/EMA
amendment, V212_PREFIT_ACTION_REGRET_DECISION_REGISTER_DRAFT_01.md,
V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md, and the relevant portions of
GROUND_TRUTH.md, ROADMAP.md and V212_FLOP_COUNTER_COVERAGE_AUDIT_DRAFT_01.md.

Objective: investigate a reproducible JEPA planning advantage over matched
non-JEPA baselines under frozen data and compute budgets. No advantage or
publication readiness has been established. V2.9 duration-only tuning,
V2.10 gradient-conflict intervention, and V2.11 lambda-only tuning failed
their declared gates. Preserve those negative results.

Current V2.12 has a no-update six-arm loss/manual-gradient graph, a scratch
optimizer, synthetic replay/schedule/receipt boundaries, and partial source
compute inventories. It does not have an exclusive production trainer,
authenticated production corpus, replay-derived 20x87 schedule, complete
runtime-bound FLOP counter, graph freeze, or passed <=5% parity. The root
Design02/V05 sampling amendment and calibration D03 are unadopted proposals;
the adopted raw-state/optimizer spec is v06. V03 compute pilot and v02
worker/bootstrap helpers are candidates, not operational approval.

First make a short implementation-level gap assessment against the current
pre-fit register. Propose the next bounded, reviewable source/synthetic-test
change and continue authorized work. Preserve protocol and artifact hashes;
do not launch training, matches, production corpus/root generation,
calibration simulations, live adapter/OOM tests, paid compute, or locked-final
evaluation merely because those entry points exist. Obtain the applicable
versioned review and separate authorization before those gated activities.

Use the research runtime (Python 3.11.9 / NumPy 2.4.6), not the legacy V7
lock. Raw historical experiment artifacts are excluded and mostly absent;
do not manufacture replacements to make provenance tests pass. Keep UI text
in English, commit verified changes, preserve generated-artifact exclusions,
and never force-push without explicit approval. Do not create agents unless
I first approve the exact model and reasoning effort. Historical approved
reviewer names do not carry new agent authorization.

The handoff preserved the stale local snapshot in e3d73bd and merged the
415 newer GitHub commits in 4d67caf. Both histories are retained. Use current
main for continuation, not the checkpoint snapshot. Report what you changed,
what passed, and any remaining evidence or environment limitations.
```
