# V2.12 request and runtime binding amendment draft 01

Status: design proposal only. It does not change the frozen V2.12 method,
authorize adapter execution, inference, training, pilot use, or an OOM test.
Baseline: supervision architecture audit 01 at `157bc60f`.

## Problem statement

The current synthetic smoke hashes the controller's request file before and
after service execution, but its worker parses standard input without hashing
the exact bytes it consumed. The release token binds a nonce and worker source
manifest, not the request digest. The receipt therefore cannot prove the exact
serialized request that crossed the worker boundary. Also, the controller's
source manifest is read after its Python modules have already been imported;
those file hashes establish file stability, not the bytes from which loaded
code objects were created.

The change proposed here adds a versioned binding contract before any request
adapter is connected. It preserves the existing rule that compute cannot start
until the caller has checked effective service properties, worker placement,
and live cgroup limits.

## Request-byte and release-token contract

Use a new request/release schema version; do not extend v01 in place.

1. The controller builds the strict request object once, serializes it to
   the project's canonical UTF-8 JSON, and writes those exact bytes to the private
   mode-0600 request file. The byte limit is explicit and no larger than
   `MAX_IPC_BYTES`. The controller hashes the serialized byte string, not a
   later re-serialization, and retains the digest with the file identity.
2. The worker reads standard input as raw bytes with a `MAX_IPC_BYTES + 1`
   bounded read. Empty, oversized, truncated, invalid UTF-8, non-canonical,
   duplicate-key, non-finite, or wrong-schema payloads fail before the release
   barrier. It computes SHA-256 over the exact bytes before decoding or
   parsing, and retains that digest in local state.
3. Add `request_sha256` to the release-token v02 required field set and token
   digest. The caller derives the token from the digest in step 1. After
   consuming and validating the one-shot release token, the worker compares
   its step-2 digest with the token value before any model/search import or
   callback. A mismatch exits without computation or a successful response.
4. The response echoes the request nonce and the accepted `request_sha256`.
   The worker serializes the strict response exactly once using the versioned
   canonical encoding, and the caller performs one bounded read of those exact
   response bytes, hashes them before parsing, then validates schema, nonce,
   and request digest against the original request identity. Bind both the
   exact response-byte digest and byte length to the response schema in the
   receipt. Do not describe a digest of re-serialized parsed JSON as the bytes
   received. Reject non-canonical response bytes. The receipt records request
   schema, exact request digest, release schema/token digest, response schema,
   exact response-byte digest, and response byte length. The request digest is
   metadata only; the request body, move/action, and outcome are not copied
   into the supervision receipt.
5. Preserve the controller's pre-dispatch and pre-receipt file identity/hash
   checks. These checks detect ordinary mutation and improve diagnosis; the
   worker's raw-byte comparison is the decisive proof of what it parsed.

The private workspace remains a same-UID trust boundary. A process running as
the same user may be able to inspect or alter private files; mode 0700/0600,
no-follow opens, inode checks, and request hashing are integrity/reproducibility
controls for the cooperating controller/worker, not protection against a
hostile same-UID process. Do not describe them as such.

For v02, define canonical request bytes exactly: UTF-8 without a BOM; one JSON
object; string keys only at every object depth; keys sorted by Python Unicode
code-point order; no insignificant whitespace; non-ASCII characters emitted
directly; arrays retain order; and
only objects, arrays, strings, booleans, null, and signed 64-bit integers are
permitted (`-2^63 <= n <= 2^63 - 1`). Serialize with the pinned Python
expression `json.dumps(value, ensure_ascii=False, allow_nan=False,
separators=(",", ":"), sort_keys=True).encode("utf-8")`. Validate the object
tree and reject non-string mapping keys before serialization; Python's JSON
encoder can coerce some keys, which could make the in-memory request differ
from the signed wire schema. This specifies
string escaping, including control characters. Reject floats, NaN/Infinity,
lone surrogates, out-of-range integers, duplicate keys, and any encoding that
does not byte-match the canonical re-encoding. The runtime fingerprint pins the
Python implementation/version. If a cross-language worker is introduced,
adopt a separately versioned canonicalization standard rather than assuming
equivalent JSON serializers produce identical bytes.

The same canonical encoding, permitted JSON value types, signed 64-bit integer
bounds, recursive string-key rule, decoder duplicate-key checks, and
canonical-re-encoding comparison apply to response bytes. The response has its
own versioned schema and explicit byte limit no larger than `MAX_IPC_BYTES`;
the caller hashes the exact bounded bytes read before parsing and rejects any
response that exceeds the limit, has an invalid/truncated frame, or fails the
same canonical-byte checks.

## Runtime and loaded-source contract

The receipt needs distinct identities for the worker and controller. The
worker bootstrap must validate its source manifest before importing
compute-capable project modules. The controller must stop treating a source
file hash read after import as proof of loaded code identity.

Proposed minimum fingerprint fields:

- Python executable real path and SHA-256 of `/proc/self/exe` (or the worker's
  corresponding process link), implementation, full version, cache tag,
  platform/ABI, and relevant `sysconfig` build identifiers;
- systemd manager version and exact effective unit property snapshot;
- for each project module used in the run: import origin, expected source
  digest, and confirmation that the module was compiled/executed from the
  verified in-memory bytes or loaded from an immutable content-addressed
  artifact;
- for loaded native/runtime dependencies (including NumPy if the adapter
  imports it): distribution/version plus hashes tied to the mapped binary's
  device/inode and the pinned dependency manifest; do not hash a path after
  import and call that proof of the already-loaded machine code;
- kernel release, architecture, cgroup-v2 mode, and relevant runtime limits
  needed to interpret the receipt.

The Python executable is itself an executed-code dependency. A hash read after
startup identifies the executable backing object at read time; it does not by
itself prove which bytes the interpreter executed or rule out mutation of a
writable backing object after mapping. Treat it under the same rule as native
libraries: verified only when an immutable/content-addressed execution
boundary or an independent mechanism proves the executed bytes; otherwise
record the observation as partial/unverified and keep any component that
requires this identity gated. Hashing `/proc/self/exe` or a mapped-file link
alone does not close the writable-mapping race.

For project Python code, prefer an explicit loader that reads a bounded,
allowlisted manifest, validates every digest, then compiles those exact bytes
into module objects before exposing compute callbacks. Keep the initial
bootstrap small and free of application imports. For the controller, either
use the same verified-byte loader from a minimal launcher or package the
controller as an immutable, content-addressed artifact whose digest is checked
before execution. Recheck artifact identity after the run and invalidate the
receipt if any expected file or manifest changed. Python executable and
native-dependency hashes still need to be recorded separately. For a native
library, the proposed check is to identify its mapping in `/proc/<pid>/maps`,
open the corresponding `/proc/<pid>/map_files/<start>-<end>` object when
permitted, verify its device/inode matches the mapping, and hash through that
opened object. If the host denies access or the identity does not match, mark
that dependency unverified and fail closed wherever that binary is mandatory.
This map-files digest identifies and hashes the mapped backing file at read
time; by itself, it does not prove the current mapped pages if the file could
change after mapping. It is supporting evidence only and must be paired with
an immutable/verified artifact boundary established before mapping or another
loader that proves the executed bytes. Until that property is demonstrated,
keep the dependency unverified. A post-import pathname hash is not an
acceptable substitute.

Do not claim that `-B`, `sys.modules` paths, a read-only bind mount, or hashes
of source files collected after imports alone attest executed code. If exact
loaded-code identity cannot be demonstrated for a component, label it as an
unverified runtime dependency and keep adapter integration closed until the
scope is reviewed.

## Receipt and failure semantics

The new receipt schema must bind both request and runtime fingerprints to the
same nonce, unit, invocation ID, boot ID, worker cgroup, source manifest, and
monotonic interval. It must state whether a fingerprint is verified,
partially verified, or unavailable; missing required fields invalidate the
request result. Do not create an accepted response or receipt on request digest
mismatch, source mismatch, runtime mismatch, deadline, manager failure, or
incomplete journal/counter evidence. Keep enough identifiers for operator
reconciliation and retain ambiguous IPC/unit state as the current harness
does.

No request body, board position, chosen action, score, or outcome belongs in
the supervision receipt. This change adds reproducibility metadata only and
does not provide scientific-performance evidence.

## Required tests before implementation review

- raw input at 0, 1, exact-limit, and limit-plus-one bytes; partial EOF;
  invalid UTF-8; duplicate keys; non-finite numbers; non-canonical encoding;
  altered bytes between caller write and worker read;
- release token missing, mismatching, or tampering with `request_sha256`, with
  assertions that no compute callback/import is reached;
- response nonce/digest mismatch and receipt omission/mismatch;
- response framing tests proving the digest is over the exact bounded bytes
  read (not re-serialized JSON), with byte-length/schema binding and rejection
  of non-canonical response bytes;
- module file changed after preflight but before import, proving the exact
  verified bytes execute or the run fails before release;
- executable, runtime, systemd, and native dependency fingerprint mismatch;
- manifest path substitution, duplicate/extra modules, symlink traversal,
  oversized files, and source mutation during execution;
- serialized receipt round-trip and independent recomputation of all linked
  hashes, while confirming it contains no request body or action.
- integrated amended-schema regression tests for manager-state loss,
  missing/duplicate/mismatched journal markers, disappearing or mismatched
  counters, deadline/kill/reap, and reconciliation failure. Use
  `docs/V212_SUPERVISION_FAILURE_MATRIX_DRAFT_01.md` as the case inventory and
  the adapter design's “Required implementation tests and gates” as the
  interface-level coverage list; each case must retain necessary
  reconciliation handles and never return an accepted action or receipt when
  required evidence is missing.

The current 116-test suite and one normal-exit synthetic receipt do not cover
these cases. Implementing the schema amendment requires versioned code,
focused tests, updated failure mapping, and independent design review first.
Even after those pass, existing external-supervision stage ordering remains in
force: no adapter integration, inference, pilot, training, or OOM operation is
authorized by this proposal.

## Open decisions for review

1. Choose the immutable worker/controller artifact form and define how its
   digest is supplied before execution without trusting mutable in-repo code.
2. Decide which Python/systemd/native-dependency identities are mandatory for
   the synthetic no-inference harness versus the later model worker; keep the
   receipt schema explicit about that boundary.
3. Define the request byte cap from the eventual versioned request schema and
   prove the worker's standard-input read is bounded even if the backing file
   grows concurrently.
4. Reconcile request-file post-run hashing with the worker's single-read
   digest so that cleanup/reconciliation behavior remains safe on every
   failure branch.

For runtime execution options and current interactive-shell feasibility
observations, see `docs/V212_EXECUTED_RUNTIME_ATTESTATION_RESEARCH_01.md`.
The 2026-10-05 no-inference transient-service probe now records the actual
worker mount/cgroup view and sampled mapped libraries, but still does not
resolve executed-byte identity or these open decisions.

## Independent design review

The configured reviewer found no P1/P2 blocker. Review confirmed the
raw-request digest can be compared after the existing no-compute barrier and
before any compute import/callback. It requested exact JSON encoder flags,
integer bounds, and a caveat that mapped-file hashing alone does not attest
pages if the backing file can change after mapping; these clarifications are
now included. A focused follow-up review required and confirmed four further
design clarifications: Python interpreter executed-byte identity, recursive
string-key validation, exact response-byte digest and length semantics, and
integration of the manager/journal/counter failure map. The reviewer also
confirmed that response bytes use the same canonical JSON rules as request
bytes. `/proc/map_files` access, the immutable-artifact guarantee, request
limits, and runtime/source binding remain unvalidated implementation
requirements.

The 2026-10-05 runtime-attestation research note compares descriptor execution,
fs-verity and source-byte compilation and records interactive-shell and
transient-worker `FS_IOC_MEASURE_VERITY` probes returning errno 95 for sampled
runtime files. This is scoped to the observed ext4 mounts, not a host-wide
feature claim. Independent review and a worker-namespace feasibility check
remain required.

The follow-up no-inference systemd worker probe confirmed `Seccomp: 0` while
the same ioctl returned errno 95 for the sampled files on the worker's ext4
root; Linux documents this measure-ioctl result as missing kernel fs-verity
support or a missing ext4-superblock `verity` feature. The running kernel and
ext4 driver advertise fs-verity support, making a missing superblock feature
likely, but a read-only superblock query was denied. The probe does not
establish another filesystem's capability. The root and project path were
read-write and no private/read-only root or binds were configured. This does
not establish a trusted runtime image.
The independent design review found no issue; a signed dm-verity image
candidate and request/response schema limits remain open.
