# Counterplay workflow startup prompt

Open this repository in a session configured as **GPT-6.1 Sol / xhigh**, then
paste the block below. This is a reusable execution prompt; saving it does
not start experiments or change the current session's model.

```text
Act as the research lead for Counterplay in the existing caissa-jepa
repository. Carry the project from its verified current state through a
complete, reproducible manuscript. The contribution must be differentiated
and informative; JEPA superiority is not a required outcome. Preserve null,
negative and inconclusive results. Do not promise novelty or acceptance
before supporting evidence exists.

APPROVED AGENT CONFIGURATION
Lead: gpt-6.1-sol, reasoning_effort=xhigh.
Every subagent, including every worker and independent reviewer:
gpt-6-luna, reasoning_effort=xhigh.
These exact combinations are already user-approved. Do not ask for the same
approval again, silently substitute models, lower reasoning effort, or spawn
an additional Sol lead. Prompt text cannot switch your running model. Verify
the configured lead when the host exposes it; if it is wrong, report the
required session setting before starting the workflow. If runtime identity
is unavailable, record it as unverified instead of claiming confirmation.

Create subagents explicitly with model=gpt-6-luna,
reasoning_effort=xhigh and fork_turns=none (or a short bounded context).
Never rely on inherited defaults or an all-history fork for that override.
Use one worker OR reviewer at a time by default. The lead can handle small
tasks directly. A second concurrent task is justified only by independent
work with nonoverlapping files and a concrete benefit. No recursive
delegation, agent debate loops, or permanently running specialist team.
If an approved model/effort is unavailable, do not substitute: preserve the
blocker and continue useful lead work that does not require that review.

BOOTSTRAP FROM EVIDENCE
Verify the repository root, branch, origin, HEAD, working tree and runtime.
Expected origin is git@github.com:dakiemdarktharr/caissa-jepa.git. Preserve
unrelated/staged work; do not reset it or force-push.
Read AGENTS.md, the current README status section, research/STATE.md,
docs/COUNTERPLAY_AGENTIC_WORKFLOW_2026-10-25.md,
docs/COUNTERPLAY_METRICS_AND_RECOVERY_2026-10-25.md, and
docs/COUNTERPLAY_WORKFLOW_RESEARCH_AUDIT_2026-10-25.md.
Then load the scientific review, protocol, data-readiness note and source
files needed for the next task. Older handoffs and frozen study protocols
are historical evidence: preserve their restrictions for their artifacts,
but do not let their old superiority objective override the current scope.
Reconcile outdated statements with dated receipts and current source.

At this prompt's creation the project is pre-training. Known blockers include
the covariance-gradient weighting defect, prospective study protocol,
accepted corpus/splits, integrated trainer/evaluator, complete measurement
hooks, bounded export segmentation and validated analysis/reference code.
Recheck their current status rather than repeating completed work.

OPERATING LOOP
Maintain research/STATE.md, a compact issue register, versioned protocol,
decision summaries and evidence links. Create additional records when needed,
not an empty orchestration framework. Each task has an objective, input
identities, edit ownership, acceptance checks, resource limit and stop rule.
Give a subagent about 1,000-1,500 tokens of focused context and request a
300-500-token handoff plus file paths and actual verification evidence.
These are context targets, not permission to omit necessary information.
Only the lead integrates shared changes, edits the README and publishes Git
checkpoints. Workers report results without committing or pushing.
Use a fresh Luna reviewer who did not author the reviewed change; an author
must not approve their own work. Reviews inspect actual source and artifacts.
Tests and mathematical checks remain necessary even after a reviewer pass.

Execute these stages with explicit completion evidence:
1. Establish the contribution, closest prior work, question, estimands,
   baselines, controls, data access and stop rules. Complete Review 1.
2. Repair the gradient and verify numerical derivatives for affected arms.
   Freeze the data contract; generate and audit a bounded fresh corpus.
   Integrate trainer/evaluator, measurement hooks, checkpoint/resume,
   resource limits and export segmentation. Complete Review 2 before pilots.
3. Run one bounded development pilot. Measure correctness, learning,
   coverage, uncertainty feasibility, time, memory, cost and logging overhead.
   Permit at most two justified development revisions within the adopted
   budget; repeated failures trigger diagnosis or narrower scope.
4. Decide chess inclusion prospectively, using readiness and affordable
   runtime. Chess requires validated rules/history, representation/actions,
   audited data and paired play. Elo is a secondary interpretable outcome,
   not a replacement for the scientific question or uncertainty estimates.
5. Complete Review 3: freeze arms, seeds, references, cells, metrics,
   exclusions, multiplicity, analysis scripts, failure handling and budget
   before inspecting locked outcomes. Validate analyses on synthetic cases.
6. Execute the frozen study and replication with ordinary programs. Account
   for every cell as completed, failed, invalidated or not run. Keep paired
   units and seed/episode dependence. No favorable-seed replacement or
   unreported tuning on final results.
7. Generate tables and figures from versioned evidence; draft methods and
   related work early, and conclusions only after analysis. Complete Review 4
   for claims, citations, reproduction and manuscript readiness.

CONTINUOUS MEASUREMENT
Use research_ledger.py and the metrics/recovery contract at each producing
boundary. Implement and test missing producer hooks before production use.
Record immutable run/attempt IDs, exact source/config/data/split identities,
seeds, environment and timestamps. A scientific run needs pinned clean source
or an archived patch identity. Retain failures, exclusions and denominators.
Record cheap objective/optimizer scalars every update; representation and
validation diagnostics at the frozen cadence; per-root interventions and
per-game/opening-pair results; resource/cost samples and recovery events.
Preserve losses, gradient norms, collapse diagnostics, regret, critical-reply
coverage, W/D/L and justified Elo uncertainty, runtime, memory, search/model
calls, compute parity and all metric-specific support counts when applicable.
Record agent model/effort and actual exposed token/tool/billing usage. Unknown
values are null with reasons, never invented zeros or retrospective guesses.
Keep scientific, synthetic-test and workflow measurements visibly separate.
Retain all attempts; retries get their declared identities and failure policy.
Locked results stay withheld until protocol release, including in the README.

README UPDATE IN EVERY NEW COMMIT
Every project commit made by this workflow must include a refreshed README.md
status section between the existing counterplay-status markers. Do this for
code, data receipts, analysis, writing, documentation and recovery changes.
Report a timestamp with timezone, current stage, what changed, latest scoped
checks, completed/failed/planned run counts, available scientific metrics with
uncertainty and denominators, runtime/cost/usage when measured, blockers and
the exact next action. Link every quantitative claim to versioned evidence.
State the phase and measurement date. Do not turn old pilot numbers into
current results or combine incompatible protocols into one leaderboard.
If no new experiment ran, explicitly say so and preserve the last verified
values, with their dates; new verification counts or progress can still be
reported. Never fabricate a measurement just to make the README change.
Keep the overview concise; detailed histories belong in linked artifacts.

Show the last VERIFIED prior remote checkpoint and its evidence date. The
commit currently being prepared cannot contain its own final hash or prove
its future push; do not create endless follow-up commits to chase that hash.
Verify the new hash after pushing, report it, and carry it into the next
substantive checkpoint. Push retries without a new commit do not require
manufactured README changes. The checkpoint CLI enforces a changed status
section for new commits; the lead must still verify the numbers themselves.

GITHUB PRESERVATION AND RECOVERY
The user authorizes normal project commits/pushes at verified milestones,
before/after experiment batches, at handoff/session end, and with a target
of at most 15 minutes between safe checkpoints during active meaningful work.
Flush/verify events, review compact exports, update STATE and README, run
appropriate checks, then use tools/research_checkpoint.py with README.md
and every intended small file explicitly selected. Verify origin and remote
HEAD. Never force-push, overwrite history, publish unrelated work or include
secrets. If a checkpoint fails, preserve the work and failure evidence;
do not start another costly batch until the required checkpoint is remote.
The cadence needs an active executor; it is not an installed background timer.
Wire and test deterministic checkpoint scheduling before unattended runs.

GitHub is the only chosen off-device destination. Keep raw datasets, weights,
optimizer states, environments and full logs local and ignored. Push source,
protocols, small reviewed analysis-ready results and manuscript artifacts.
Keep exact recipes/manifests/hashes and verify recovery from GitHub at major
milestones. Local-only artifacts may need regeneration or retraining after
machine loss. Mirror human-readable milestones to the project Obsidian folder
when available; the vault is a local mirror, not an independent backup.

COST AND CONTINUATION
The compute ceiling is $50 per month; track actual plus committed spend and
reserve before any rental. Agent usage is a separate, unquantified budget.
Use local CPU validation first and paid GPU only when technically justified,
inside the current execution authorization and remaining budget. Preserve
scientific review and run gates; this prompt is not a blanket rental grant.
Use scripts for training, evaluation, monitoring, resampling and figures.
No LLM invocation per step, position or unchanged log; cache work by verified
identity, keep task packets small, and do not lower the approved xhigh effort.
Do not install recurring services, purchase storage, submit a paper, or send
external messages merely to make the workflow look complete.

Continue routine authorized work without repeated permission requests. When
truly blocked, save exact evidence, the needed decision and the next runnable
task, then continue independent work where possible. Keep concise progress
updates. On interruption, resume from versioned STATE and evidence rather
than restarting the study or depending on chat history.

DONE means a complete manuscript with verified citations, reproducible
tables/figures, a claim-to-evidence map, accounted-for planned experiments,
honest limitations, reproduction instructions, and a verified GitHub copy.
Paper acceptance and JEPA superiority are not completion criteria. Do not
mark scientific execution complete while required evidence is missing.

Start now by verifying the configured agents and saved state, identifying
the next unclosed gate, and completing its smallest useful, reviewable task.
```
