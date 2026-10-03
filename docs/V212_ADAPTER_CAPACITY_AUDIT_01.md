# V2.12 inference-adapter capacity audit 01

**Status: static source audit only; no request, model scoring, data access, or
training occurred.** This records what the current random-weight request
adapter bounds structurally and what remains unmeasured. It does not establish
operational feasibility or authorize a pilot.

## Scope and source identity

The audit inspected `two_player/v212_request_adapter_v02.py`
(`32e62834b7baf6a64695f2467e6539e531fd8144`),
`two_player/v212_request_adapter_v01.py`
(`3303a1441d3e6807a2b5e6eb81dffb0e22f18223`),
`two_player/v212_pilot.py` (`4b270f3c5fc6a2797277a0daa3cc80673e316ac9`),
`METHOD_SPEC_V212.md` (`139b56dd3f0fb6b39fe163b9b8123bfd42d3cd25`), and
`docs/V212_COMPUTE_BUDGET_AMENDMENT_06_DRAFT.md`
(`07a3d7c2d0cc35010fb7fdc94f5f5a819513a467`). The adapter is exercised only
with a random-initialized, inference-shaped model and a synthetic legal root.
It has no training data, optimizer, saved action values, or score output.

## Static model-size and call bounds

`RandomInferenceModel` uses a 198-feature input, 32 latent units, a 65-action
encoding, one actor scalar, and six game-descriptor values. Its predictor input
width is therefore 104. The NumPy weights and biases use `float64` arrays.

| Random pilot arm shape | Parameter-array arithmetic | Array bytes only |
| --- | ---: | ---: |
| Encoder + predictor + value | `(198×32+32) + (104×32+32) + (32+1) = 9,761` | 78,088 B (about 76 KiB) |
| Recursive raw-state control, including decoder | `9,761 + (104×198+198) = 30,551` | 244,408 B (about 239 KiB) |

These totals exclude Python/NumPy runtime, object and temporary-array overhead,
process startup, and filesystem/runtime libraries. The harness allocates a
predictor even for arms that do not call it. It does not contain the method's
policy head, EMA target encoder, optimizer state, or training batches, so these
figures are not a training-memory estimate and should not be generalized to a
fitted checkpoint without a separate inventory.

The 10,000-node counter is checked before each entered search node and cannot
exceed its configured cap. Each child transition and (for predictive arms)
latent advance occur before the recursive call checks the next node. At a
budget boundary, that ordering can perform one extra transition/advance before
the stop is observed. Conservative source-level model-call ceilings for one
request at the 10,000-node cap are therefore:

- ordinary predictive arms: at most one root encode, 10,001 predictor calls,
  and 10,000 value calls (20,002 total);
- recursive raw-state control: at most one root encode, 10,001 decoder and
  re-encode calls, and 10,000 value calls (30,003 total);
- direct-leaf value arm: at most 10,000 leaf encodes and 10,000 value calls
  (20,000 total).

These are conservative call-count bounds derived from control flow, not FLOP,
latency, or observed-call estimates. A single NumPy operation is not
preemptible by the cooperative planner check.

## Operational boundary

The request wrapper starts its monotonic clock before request validation and
cgroup inspection, passes an absolute five-second planner deadline into the
worker, and applies a six-second response timeout to subprocess communication.
The worker performs module/process startup, request parsing, root reconstruction,
cgroup checks, and random-model construction on that same request clock. The
planner checks time between search operations and retains the last completed
root iteration; this is cooperative stopping, not a hard real-time guarantee.
The outer wrapper rechecks elapsed time after supervisor-side validation and
turns a late response into a forfeit.

In the current v02 path the worker is another process in the caller's existing
cgroup, not a separately managed transient service. Source inspection also
shows that v02 launches `python -m two_player.v212_request_adapter_v01
--worker`; ordinary requests therefore execute the v01 worker entry point,
while the v02 module contains a duplicate worker implementation that its
normal request path does not call. The effective runtime identity spans both
adapter files and the shared pilot model module; a future correction must bind
and test the dispatched worker version explicitly. Thus `memory.max` limits
the shared cgroup, and a caller can be an OOM victim before it classifies or
records the request. The adapter's sampled RSS is per-process telemetry; it is
not cgroup peak memory. `docs/V212_COMPUTE_BUDGET_AMENDMENT_06_DRAFT.md` proposes
an external supervisor and corrected memory language, but that design is not
integrated or independently accepted. The synthetic receipt assembler also
does not yet consume live adapter/service evidence.

## What remains unverified

Static tensor sizes do not establish the request's wall-time or memory profile.
There is no accepted end-to-end request measurement covering fresh process
startup, module import, random model construction, root encoding, search,
supervisor-side event validation, receipt assembly, and caller-observed
response. The earlier random-weight search-call pilot excludes several of
those stages. No fitted model's capacity or throughput is measured. The
proposed resource values remain proposals, and the existing resource,
supervision, generation, split/leakage, novelty, and pre-fit gates remain
closed.

The next permitted step is independent review of a versioned supervision and
receipt integration design, followed by only the separately authorized
no-outcome checks named in that review. This audit itself does not authorize
an OOM fault test, inference request, data generation, scoring, match, or fit.
