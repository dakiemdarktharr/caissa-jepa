# V2.12 request/response schema v02 proposal draft 01

Status: unreviewed protocol proposal derived from a source audit. It does not
authorize implementation, adapter integration, inference, training, pilot
execution, or any resource-limit change. The current v01 schemas and method
spec remain unchanged.

## Purpose and scope

This proposal closes the field and encoding domains needed to calculate
smaller byte caps for the existing synthetic random-weight request adapter.
It is a protocol candidate, not a claim that the adapter's current runtime or
resource profile is safe or ready. Independent design review must approve the
field set, bounds, resource-profile relationship, and failure semantics before
implementation.

## Canonical encoding

Keep the proposed amendment's Python canonical encoding: UTF-8, no BOM, one
top-level object, recursively string-keyed objects, sorted keys, compact
separators, `ensure_ascii=False`, no floats, and signed 64-bit integers only.
Reject duplicate keys, non-finite constants, invalid UTF-8, lone surrogates,
out-of-range integers, trailing bytes, and any payload not byte-identical to
its canonical re-encoding. The runtime fingerprint must pin the Python
implementation/version that serializes and validates these bytes.

All string fields below are fixed ASCII enums or fixed-length lowercase hex;
there are no free-form diagnostic strings. Worker errors are process failures
with no valid response body. This removes an otherwise open-ended exception
class-name field from the accepted-response schema.

## Request `caissa.synthetic.request.v02`

Require exactly these 16 keys, with no additional keys:

| Key | Bound |
| --- | --- |
| `schema` | Literal `caissa.synthetic.request.v02` |
| `nonce` | Exactly 32 lowercase hexadecimal characters (128 random bits) |
| `variant` | One of the four names in `v212_pilot.VARIANTS` |
| `target_ply` | One of `0, 8, 16, 24`, matching the current frozen root-ply schedule |
| `root_seed` | Integer `0..2^63-1` |
| `root_state_sha256` | Exactly 64 lowercase hexadecimal characters |
| `board` | Integer array of exactly the selected variant's cell count, at most 64; each value is `-1`, `0`, or `1` |
| `player` | Integer `-1` or `1` |
| `arm` | One of the six names in `v212_pilot.ARMS` |
| `model_seed` | Integer `0..2^63-1` |
| `request_started_ns` | Integer `0..2^63-1` from the caller's monotonic clock |
| `planner_deadline_ns` | Integer greater than `request_started_ns`, at most `2^63-1`, and at most 5,000,000,000 ns after start |
| `node_cap` | Integer `1..10,000`, matching the current adapter's declared candidate cap |
| `rss_cap_bytes` | Integer `1..2^63-1`; caller must also enforce the separately reviewed live resource profile before release |
| `expected_cgroup_path_sha256` | SHA-256 hex of the exact UTF-8 bytes of the controller's captured unified cgroup path; worker recomputes from its own path |
| `expected_memory_max` | Integer `1..2^63-1`; worker must compare to its live cgroup and the caller must match it to the separately reviewed service profile |

Implementations must enforce the complete listed key set.
`expected_cgroup_path_sha256` avoids placing a variable-length
host path in the message. The caller still retains the path locally for its
receipt and independently hashes its exact UTF-8 representation; the worker
compares the request digest with its own captured path before release. This
digest binding is not protection from a hostile same-UID process.

The request deadline representation changes the current float-valued
`request_started` and `planner_deadline`; conversion to integer monotonic
nanoseconds is proposed only for this version. Runtime/resource parameters
remain pre-release rejection conditions tied to an approved unit profile;
their broad int64 wire ranges are representation bounds, not permission to
request those resources. The candidate 1.5 GiB adapter default and the
separately observed 128/96 MiB synthetic service profile are not reconciled by
this proposal. That profile must be decided before implementation or any
service use.

## Success response `caissa.synthetic.response.v02`

Require exactly these 18 keys, with no additional keys:

| Key | Bound |
| --- | --- |
| `schema` | Literal `caissa.synthetic.response.v02` |
| `nonce` | Exact request nonce |
| `request_sha256` | SHA-256 hex of the exact canonical request bytes consumed |
| `action` | Integer `0..64` (caller still validates legality against original root) |
| `completed_depth` | Integer `0..4` |
| `stop_reason` | One of `depth_4_complete`, `node_cap`, `wall_cap`, `rss_cap`, `no_completed_root_action` |
| `node_visits` | Integer `0..2^63-1` |
| `transition_calls` | Integer `0..2^63-1` |
| `encoder_calls` | Integer `0..2^63-1` |
| `predictor_calls` | Integer `0..2^63-1` |
| `decoder_calls` | Integer `0..2^63-1` |
| `value_calls` | Integer `0..2^63-1` |
| `model_calls` | Integer `0..2^63-1` |
| `terminal_nodes` | Integer `0..2^63-1` |
| `peak_sampled_rss_bytes` | Integer `0..2^63-1` |
| `search_wall_ns` | Integer `0..2^63-1`; this is a representation bound, while a late result is rejected by the caller deadline |
| `worker_cgroup_path_sha256` | SHA-256 hex of the worker's exact UTF-8 unified cgroup path |
| `worker_memory_max` | Integer `1..2^63-1`, verified against live worker cgroup |

Implementations must enforce the complete listed key set. A nonzero worker
exit, missing/partial response, or response
with any other schema does not yield an action. The caller hashes the exact
bounded response bytes before parse and includes exact digest and byte length
in the versioned receipt; the body/action remains out of that receipt.

## Candidate exact byte caps

Under the field sets and representation bounds above, compact sorted canonical
encoding has a worst-case request size of **811 bytes** and success-response
size of **747 bytes**. These sizes include every required key, maximum fixed
enum/hex length, maximum signed-64-bit decimal width, a 64-cell board of
`-1` values, and all JSON structural bytes. The request witness uses
`request_started_ns = 9223372031854775807` and
`planner_deadline_ns = 9223372036854775807`, which are both 19 digits and
differ by exactly the proposed 5-second maximum. The response witness uses the
longest stop-reason string and maximum allowed integer widths. No free-form
string is present, so JSON escaping cannot increase a bound.

Proposed protocol caps are therefore `MAX_REQUEST_V02_BYTES = 811` and
`MAX_RESPONSE_V02_BYTES = 747`, subject to independent review and a reproducible
byte-count check against the exact serializer/schema. Any schema change,
additional field, larger enum, or relaxed string rule requires a new version
or a recalculated cap before implementation. Both readers must consume at
most `cap + 1` bytes from the actual stream/file, reject growth/extra bytes,
hash the exact accepted bytes before parsing, validate the closed schema, and
reject non-canonical encodings. A parsed-object length estimate is not a
substitute.

## Reproduction method and unresolved review points

The byte counts were calculated with this standard-library witness builder,
using the exact Python expression proposed by the amendment:

```python
import json

encode = lambda value: json.dumps(
    value, ensure_ascii=False, allow_nan=False,
    separators=(",", ":"), sort_keys=True,
).encode("utf-8")
i = 2**63 - 1
h, n = "f" * 64, "f" * 32
request = {
    "schema": "caissa.synthetic.request.v02", "nonce": n,
    "variant": "connect4-gravity-6x7", "target_ply": 24,
    "root_seed": i, "root_state_sha256": h, "board": [-1] * 64,
    "player": -1, "arm": "recursive-raw-state-dynamics",
    "model_seed": i, "request_started_ns": i - 5_000_000_000,
    "planner_deadline_ns": i, "node_cap": 10_000,
    "rss_cap_bytes": i, "expected_cgroup_path_sha256": h,
    "expected_memory_max": i,
}
response = {
    "schema": "caissa.synthetic.response.v02", "nonce": n,
    "request_sha256": h, "action": 64, "completed_depth": 4,
    "stop_reason": "no_completed_root_action",
    "node_visits": i, "transition_calls": i, "encoder_calls": i,
    "predictor_calls": i, "decoder_calls": i, "value_calls": i,
    "model_calls": i, "terminal_nodes": i,
    "peak_sampled_rss_bytes": i, "search_wall_ns": i,
    "worker_cgroup_path_sha256": h, "worker_memory_max": i,
}
assert len(request) == 16 and len(encode(request)) == 811
assert len(response) == 18 and len(encode(response)) == 747
```

The candidate objects use the maximum permitted string/integer lengths and a
64-cell board. The script verifies counts for this witness; it is not a schema
validator and does not prove that every other combination stays below the
caps. Before implementation review, add a checked reproducer that validates
every witness field against the schema and the worker/caller tests that
exercise 0, exact-cap, and cap-plus-one input cases. This draft does not
implement that verifier.

Review must specifically decide whether the digest-only cgroup identity is
sufficiently clear/reproducible, whether the current root-ply and node caps
are the right versioned interface, how the adapter's 1.5 GiB default relates
to the 128/96 MiB service profile, and whether `search_wall_ns` and stop reasons
have the stated bounds. No gate advances on the draft or the arithmetic alone.
