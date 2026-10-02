# V2.10 method note: shared-encoder gradient-interference diagnostic

Status: frozen no-update diagnostic protocol, amended by `docs/V210_GRADIENT_DIAGNOSTIC_AMENDMENT_01.md` after the 640-root support requirement failed before any gradient was computed (2026-10-02). The amendment supersedes only the batch/root count. It authorizes only the pinned train-only diagnostic after independent review. It does not authorize training a new model, model selection, or confirmatory evaluation.

## Question and scope

For the current deterministic two-player adapters, do legal two-ply reply-set JEPA gradients consistently conflict with policy/value supervision on the shared online encoder? The tested family remains alternating-turn, fully observed, deterministic, finite legal actions, zero-sum games. The opponent is a worst-case legal reply in a depth-two max-min planner; this is not behavior prediction for a named opponent, an expectation over an uncalibrated policy, or equilibrium/exploitability computation.

V2.9's frozen development comparison found JEPA-minus-task-value paired score -0.1375 on Connect4-6x7, +0.0125 on Reversi6, and -0.0625 macro. More training duration failed the frozen nomination gate. Gradient conflict is a new, falsifiable diagnosis, not a post-hoc causal finding.

## Mathematical decomposition

For a training batch B of roots x, let z=f_theta(x) be online latent, zbar=f_bar_theta(x') a stop-gradient EMA target for exact legal two-ply successor x', and zhat=g_phi(z,a,b,r) the prediction conditioned on ordered own action a and opponent reply b. Let L_pi be legal-masked policy cross-entropy; L_v be root value regression; L_o be observed nonterminal successor-value regression; L_J be root-balanced squared error between zhat and zbar across every nonterminal legal (a,b); and L_R be the existing variance plus off-diagonal covariance regularizer. The current objective is L_task + L_J + L_R, where L_task=L_pi+L_v+L_o. Terminal returns remain exact and are masked from latent-target regression.

For shared online-encoder parameters theta_e, measure g_task=grad_theta_e L_task, g_J=grad_theta_e L_J, and g_R=grad_theta_e L_R separately. Record cosine(g_J,g_task), norms, and dot product alongside per-game, per-initialization-seed, and batch counts. Do not mix predictor-only coordinates into the shared-encoder cosine. The online encoder is the only shared component whose gradient direction is routed by the later candidate.

The diagnostic computes each component from the exact same frozen checkpoint and batch. It performs no optimizer step, target-EMA update, hyperparameter selection, or checkpoint write. A weights-only loader verifies the whole-file SHA-256, inspects the NPZ tensor-name inventory, and reads only online/EMA parameter arrays; it never decodes the checkpoint metadata or embedded training history. The gradient report excludes all training-loss values. The sum of decomposed gradients must match the existing aggregate gradient numerically. Data access is limited to the audited `train` split. It must not inspect the old `train_metrics` files/loss histories, V08, validation, selection, or locked-final data.

## Frozen diagnostic gate

Use the 20 hash-verified V2.9 `reply-jepa` checkpoints and their matched rule adapters, a deterministic fixed hash-sampled set of 300 train roots per game, ten non-overlapping minibatches per seed/game, batch size 30, and the exact model config pinned in the V2.9 fit ledger. This is a post-outcome mechanism diagnostic: the match result motivated this hypothesis, but the diagnostic itself will not select among model recipes. Verify each checkpoint against the completed V2.9 fit ledger, receipt, model-code/data identity, and tensor hashes. Do not use checkpoint loss history as a diagnostic input. Hash selected record IDs (without exporting the IDs) and code/config before execution. Report all samples, invalid/masked cases, gradient cosines, norms, task/JEPA dot products, and seed-cluster 95% intervals. Resampling for intervals is at the initialization-seed cluster, not the batch. The 300-root fixed hash sample is a support-driven amendment: the audited train split contains only 307 Connect4 roots and 1,490 Reversi6 roots; the first 640-root preflight stopped before model/checkpoint gradient evaluation.

Proceed to a separate intervention preregistration only if (i) the median across the 20 per-seed median encoder cosines is below -0.05 in each game, (ii) the two-sided 95% t interval for the mean per-seed median is below zero in each game, and (iii) at least 15/20 seeds have negative cosine in at least 6/10 batches in each game. The numeric thresholds are an explicit screening choice and must not be described as a universal criterion. If any gate fails, stop this mechanism without post-hoc subgroup search.

## Candidate intervention (not yet authorized by this note)

If the gate passes and an independent pre-fit review approves the next protocol, decompose only the JEPA encoder gradient against g_task. For eta>0, use the conflict-projected encoder component

\[
g_{J\perp}=g_J-\frac{\min(0,\langle g_J,g_{task}\rangle)}{\|g_{task}\|_2^2+\epsilon}g_{task},
\qquad g_e=g_{task}+g_{J\perp}+g_R.
\]

Apply the original JEPA gradient unchanged to predictor-specific parameters. Do not project policy/value task gradients or regularizer gradients. This is a narrow PCGrad-style intervention, not a novel gradient algorithm. Its purpose is to test whether protecting decision-task encoder descent lets two-player reply-set JEPA targets help planning.

The future experiment must compare raw JEPA, projected JEPA, task-value-dynamics, and direct-leaf under identical data, initialization, update count, model/search, opponents, opening/situation schedule and measured compute. It must freeze a primary paired decision metric, practical margin, sample size/power, uncertainty/multiplicity, seat swap, timeout/censor rules, and kill screen before fitting. Development, model-selection and locked confirmation must remain separate. Do not infer superiority from the gradient diagnostic itself.

## Required implementation checks

- Component gradients sum to the original gradient within relative error 1e-9 on deterministic float64 fixtures and 1e-7 on audited data batches.
- A prediction-only component changes neither task heads nor target-encoder parameters; all terminal/missing-target masks and legal reply closure match the existing model.
- Repeated execution with frozen batch/model fingerprints produces identical diagnostics; all outputs include code, data, seed, and config hashes.
- No optimizer, EMA, checkpoint, model-selection or locked-data APIs are called.
- Independent review must explicitly inspect gradient decomposition, masking, fairness, stop conditions and access boundaries before the diagnostic runs.

## Novelty and limitation

PCGrad and CAGrad establish gradient-conflict mitigation; the recent JEPA Policy preprint reports dual-branch and gradient-routing controls for paired action/future representation prediction. Therefore encoder gradient routing is not new by itself. Any claim would be limited to an empirical, matched-control result for EMA latent prediction conditioned on complete legal action/reply sets and fixed-budget minimax planning in the declared games. Prior art review and a backward/forward citation search remain required.
