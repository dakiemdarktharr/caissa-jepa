---
title: Counterplay — Research audit of the agentic workflow
date: 2026-10-25
tags: [counterplay, workflow-audit, related-work, reproducibility]
---

**Verdict:** retain a small lead/worker/reviewer workflow, but make durable
evidence and recovery part of every stage. The earlier diagram was a useful
allocation of responsibilities, not yet an operationally complete research
system. It lacked enforced measurement boundaries, a publication cadence,
result-preserving recovery, and a tested way to distinguish an acknowledged
event from a missing one.

User decisions: no fixed deadline/venue; $50/month compute ceiling; novel and
informative research is the aim, not mandatory JEPA superiority; exact agent
models/efforts require approval; **GitHub only for backup for now, with large
artifacts kept local**. The last decision limits disaster recovery and is
preserved rather than silently replaced with paid storage.

**1. Research method and limits**

Exa was used for 12 successful searches across three workstreams: coordination
and cost, scientific research automation, and provenance/recovery. There were
79 returned discovery records and 77 distinct exact URLs. These are not 77
independent studies: versions, mirrors, DOI pages and publisher pages overlap.
Three initial requests failed tool-schema validation and returned no sources.
The discovery inventory is `docs/validation/AGENTIC_WORKFLOW_SEARCH_2026-10-25.json`.

Screening prioritized original papers, author/project pages, proceedings,
standards and official documentation. Sixteen selected primary/documentation
URLs were fetched for abstracts and relevant sections; additional search
highlights supplied targeted methods/limitations passages. This is a targeted
multi-pass review, not an exhaustive systematic review or a claim of reading
every full paper. Newer preprints and vendor evaluations are distinguished
from published research. Evidence is current to 25 October 2026; search-result
timestamps were not used as proof of a paper's publication date.

**2. What the evidence supports**

| Evidence | Finding relevant to this project | Scope and resulting decision |
| --- | --- | --- |
| [AI Agents That Matter](https://arxiv.org/abs/2407.01502), Kapoor et al. | Accuracy-only evaluation can favor unnecessarily costly systems; inadequate holdouts and inconsistent evaluation undermine agent comparisons | Adopt success, cost, reliability and reproducibility together. Its benchmark findings do not identify the best model for this repository |
| [Agentless](https://arxiv.org/abs/2407.01489), Xia et al. | A constrained localization/repair/validation workflow competes effectively with more autonomous software-agent approaches | Keep routine coding and validation structured. Historical SWE-bench Lite results are not a guarantee for novel research |
| [Towards a Science of Scaling Agent Systems, v2](https://arxiv.org/html/2512.08296v2), Kim et al. | Across 180 configurations, coordination benefits depend on task structure; their sequential-planning tasks suffer while some parallelizable tasks improve | Preserve one owner for dependent design/code decisions. Parallelize separable searches or checks only when useful. Do not transplant reported thresholds or multipliers as universal laws |
| [Why Do Multi-Agent LLM Systems Fail?, v2](https://arxiv.org/html/2503.13657v2), Cemri et al. | MAST identifies specification, inter-agent alignment and verification failure families | Require explicit task contracts, artifact identities and executable acceptance checks. A reviewer role alone does not eliminate these failures |
| [How Do AI Agents Spend Your Money?, v2](https://arxiv.org/html/2604.22750v2), Bai et al. | Agentic coding cost is strongly affected by input context, with large variability and weak self-prediction of usage | Measure actual exposed usage; compact context and bound retries. Mark unexposed tokens/cost as unavailable rather than estimating them from confidence |
| [Agent Laboratory](https://arxiv.org/abs/2501.04227), Schmidgall et al. | A literature/experiment/report pipeline supports human feedback; authors report improved research quality with feedback | Retain intervention at substantive scientific decisions. Its reported cost reductions are relative to its own comparison setup, not our budget forecast |
| [Towards end-to-end automation of AI research](https://www.nature.com/articles/s41586-026-10265-5), Lu et al., Nature 2026 | Demonstrates automated ideation, experiments and manuscript generation, including a workshop acceptance; also reports incorrect implementations, weak rigor and citation errors | Borrow artifact-linked stages, not acceptance-optimizing search. A workshop success does not guarantee novelty, reliability or journal acceptance here |
| [Hidden pitfalls of autonomous AI scientists](https://www.pnas.org/doi/10.1073/pnas.2610214123), Luo et al., PNAS 2026 | Controlled tests of two systems identify benchmark/metric selection problems, undisclosed data changes and structural post hoc selection bias; workflow artifacts improve auditing | Preserve all attempts, data exclusions, metric choices and failures. The study does not establish intentional deception or explicit test-set peeking in those systems |
| [PaperBench](https://proceedings.mlr.press/v267/starace25a.html), Starace et al., ICML 2025 | Uses author-developed hierarchical rubrics to assess actual research replication; evaluated agents remain far from completing all requirements | Decompose completion into checkable outputs, including execution and reproduction, rather than trusting a polished report |
| [ScienceAgentBench](https://arxiv.org/html/2410.05080v3), Chen et al. | Evaluates individual scientific tasks through executable programs, results and costs, showing substantial remaining limitations | Test each workflow component before claiming end-to-end readiness. Its historical model scores are not estimates of today's configuration |
| [AstaBench](https://arxiv.org/abs/2510.21652), Bragg et al. | Standardizes scientific research tools and evaluates a broad suite while accounting for cost/tool confounds | Pin tool and environment identities and keep comparable evaluation conditions. Do not treat all agent benchmarks as interchangeable |
| [Improving Reproducibility in ML Research](https://jmlr.org/papers/v22/20-303.html), Pineau et al., JMLR 2021 | Connects code, reproducibility challenges and reporting checklists to more reliable ML research | Make the final paper reconstructible from code, configurations, data recipes and results, not prose alone |
| [Recording provenance of workflow runs with RO-Crate](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0309210), Leo et al., PLOS ONE 2024 | Represents workflow executions together with inputs, outputs and provenance | Use explicit run/input/output identities now; preserve an export path to a standard package later. Installing a workflow engine is unnecessary for the first study |

Engineering references add practical, narrower support. Anthropic recommends
simple composable patterns in [Building effective agents](https://www.anthropic.com/research/building-effective-agents).
Its [multi-agent research case study](https://www.anthropic.com/engineering/multi-agent-research-system)
reports gains for broad parallel research together with substantial token
cost; this is a vendor's internal evaluation, not a universal advantage.
[MLflow's run/metric/artifact separation](https://mlflow.org/docs/latest/ml/tracking/)
is a useful data model. This project adopts a small compatible conceptual
boundary without adding a tracking server dependency.

These sources do **not** prove that three roles, four reviews, 1,500-token task
packets, two development revisions, or 15-minute checkpoints are optimal.
Those are adjustable engineering choices. Measure cost per accepted task,
rework, missed defects, evidence completeness and recovery success before
claiming a workflow efficiency improvement.

**3. Audit of the previous workflow**

| Issue | Consequence | Disposition / remaining closure condition |
| --- | --- | --- |
| W01 — “Record metrics” had no schema or cadence | Important denominators, seeds, failures or intermediate losses could disappear | Metrics/recovery contract added; durable ledger and objective adapter implemented. Trainer/evaluator integration remains required |
| W02 — No dependable off-device checkpoint policy | Chat or laptop loss could erase progress despite local commits | Standing authorization and 15-minute active-work target added; explicit-file checkpoint tool implemented; earlier documentation already pushed and verified |
| W03 — Git was implicitly treated as a full experiment backup | Ignored datasets, checkpoints and logs would still be lost | GitHub-only boundary made explicit. Regeneration recipes and compact result exports mitigate loss; large-artifact survival is not solved under the user's current choice |
| W04 — State depended too much on chat history | A new agent could repeat work or use stale assumptions | `research/STATE.md` is now the compact entry point; source of truth is versioned artifacts and evidence |
| W05 — Four review calls could be mistaken for sufficient validation | Same-model reviews can miss shared errors; final prose can conceal process faults | Require executable checks, artifact access and incident-triggered re-review; four gates are a minimum design, not a hard quota |
| W06 — Means/Elo alone would not support paper analysis | Dependence, uncertainty and failure handling could not be reconstructed | Preserve per-seed/root/episode/opening-pair derived observations and denominators in reviewed small exports |
| W07 — Unbounded or selectively reported retries | Cost growth and biased evidence | Immutable attempt IDs, failure events, predeclared retry policy, and no favorable-run replacement |
| W08 — Locked outputs had no publication boundary | Automatic backups could expose evaluation results prematurely | Exporter withholds locked runs by default; a run-bound release record is required. Release is an operator/protocol decision, not cryptographic access control |
| W09 — Recovery was hypothetical | A backup might exist but be unusable | Local round-trip test and actual GitHub fresh-clone check pass. The same host/environment was used; full training resume and replacement-machine environment recreation remain future tests |
| W10 — “Least usage” lacked measured evidence | An efficiency claim could be invented | Record exposed token counts, tool calls, retries, elapsed time and accepted deliverables; missing host usage remains null |
| W11 — No distinction between proposals and installed automation | User could assume autonomous monitoring was already active | Explicit status: journal/checkpoint primitives exist; no unattended scheduler, autonomous agents or production trainer is running |
| W12 — Paper completeness could become a proxy for scientific validity | A polished paper might overstate novelty or unreproduced results | Claims-to-evidence map, process audit, outcome-independent reporting and human scientific judgment remain mandatory |
| W13 — Full-journal exports eventually exceed the size cap | Long runs could stop publishing new evidence | Current exporter deliberately fails at its cap and has no automatic partitioning. Before long runs, implement and verify bounded segments with parent snapshot hashes and complete analysis-unit coverage; never silently discard old or failed events |

**4. Revised operating loop**

Every task begins from a saved state and a bounded contract. The worker uses
the appropriate source/data identities, runs the task, and records results
and failures. Deterministic checks verify the output. At the appropriate
scientific gate, the reviewer inspects artifacts and the claim. Small reviewed
exports, code and handoffs are committed, normally pushed, and checked against
the expected remote commit. A subsequent agent resumes from that checkpoint.

The evidence loop runs through the whole research process: source selection,
dataset generation/exclusions, gradient repair, fitting, evaluation,
interventions, statistics, figures, citations and writing. Decision summaries
and action/tool receipts are sufficient; private internal chain-of-thought is
not requested or logged. No secrets, raw credentials or unrelated user data
belong in the published history.

The largest unresolved scientific blockers are unchanged: covariance-gradient
correctness, an accepted fresh corpus, the integrated trainer, reference and
analysis validation, and the prospective Counterplay protocol. Logging makes
these visible; it does not fix them or authorize expensive runs.

**5. What has actually been implemented**

- `research_ledger.py`: transactional local SQLite journal, immutable run
  identity through the API, idempotent event keys, integrity-checked chains,
  explicit missingness, consistent snapshots, and bounded checksummed exports.
- `measured_objective`: records the existing objective's returned loss,
  gradient/representation/support metrics and objective elapsed time while
  preserving its outputs and gradients. It performs no optimizer update.
- `tools/research_ledger.py`: create, record, verify and export commands.
- `tools/research_checkpoint.py`: commits only explicit small reviewed files,
  preserves staged work by refusing to proceed, rejects ignored/large
  artifacts, uses a normal push, and verifies the remote hash. It is not a
  timer or a substitute for substantive tests/content review.
- Focused tests cover interruption, replay conflicts, concurrency, integrity,
  protected exports, actual-objective equivalence, and local Git recovery and
  divergence. Only synthetic fixtures and documentation/workflow events were
  used; no research result was manufactured.

The journal detects the tested corruption cases, but is not tamper-proof:
external anchored snapshots are needed to detect deletion of the entire tail,
and SQLite durability depends on the filesystem/storage honoring its writes.
The CPU/epoch/optimizer/evaluator/agent-usage collectors are not magically
installed by creating a database. Their integration and cadence are explicit
gates in the metrics contract before production runs.

Full recovery from laptop destruction remains limited to what is successfully
pushed and independently verified. GitHub's [backup documentation](https://docs.github.com/en/repositories/archiving-a-github-repository/backing-up-a-repository)
explains repository backup scope; [Git's ignore rules](https://git-scm.com/docs/gitignore)
explain why intentionally untracked artifacts are not included. A same-laptop
Obsidian mirror is useful memory, but not another failure-independent copy.

**6. Verification and first preserved measurements**

The [infrastructure receipt](validation/WORKFLOW_INFRASTRUCTURE_2026-10-25.json)
records **14 passing tests**, exact source hashes, environment and elapsed
time. The [GitHub recovery receipt](validation/GITHUB_RECOVERY_2026-10-25.json)
records a fresh clone of `49f9f05f597c250bdab2815b5e3bc29950f53a9c`, verification
of five source/test hashes, and all 14 tests passing from the recovered tree.
This checks GitHub-to-checkout recovery on the same host using the existing
environment; it does not claim an independent-machine or power-loss test.

The first `research/results/` snapshot contains five real workflow events:
search counts, focused verification, GitHub recovery, verified publication,
and usage availability. It contains no trained-model result. Unexposed token
and billing fields are explicitly missing. The local database remains ignored.

The first attempt to publish that CSV snapshot stopped before committing:
Git's default whitespace check treated standard CRLF CSV terminators as
trailing whitespace. The checkpoint tool now permits CRLF without disabling
actual trailing-space checks. The [regression receipt](validation/WORKFLOW_CHECKPOINT_CRLF_2026-10-25.json)
records **15 passing tests**, including byte-exact CSV recovery and rejection
of a source line with trailing spaces. A subsequent snapshot keeps all five
original events and adds the failed attempt and its regression verification.
The verification event binds changed source hashes explicitly; this workflow
run spans implementation revisions and is not a scientific experiment.
