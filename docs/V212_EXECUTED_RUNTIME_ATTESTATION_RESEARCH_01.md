# V2.12 executed-runtime attestation research 01

Status: design research only. This note does not authorize host filesystem
configuration changes, adapter integration, a live service, inference,
training, pilot work, or OOM testing. It refines the open runtime-identity
decision in `docs/V212_REQUEST_RUNTIME_BINDING_AMENDMENT_DRAFT_01.md`.

## Finding

A pathname hash collected after Python starts is an inventory observation, not
proof of the bytes executed. `fexecve()` closes the pathname-replacement gap by
executing an open file descriptor, but the Linux manual explicitly says that it
does not stop the referenced file contents changing between checksum and
execution. A descriptor-pinned launch therefore needs a separately enforced
content-immutability property.

One strong candidate for individually provisioned runtime files is fs-verity
plus an independently trusted expected digest. Linux fs-verity
makes a file read-only after enabling verity, verifies data as it is read (also
through mmap), and exposes a constant-time digest measurement. The measured
fs-verity digest is a distinct format from an ordinary whole-file SHA-256; the
receipt should record the algorithm and measured digest and bind it to a
trusted expected value. fs-verity supplies integrity, not authenticity by
itself, so the expected digest still needs a trusted signed manifest, pinned
launcher, or equivalent source.

## Candidate execution contract

1. A small trusted launcher reads a signed/pinned allowlist of runtime
   artifacts. The expected manifest must come from outside the mutable project
   tree. It establishes a trusted read-only runtime mount (or equivalent
   trusted directory boundary), because fs-verity protects file contents but
   files can still be renamed or deleted. The launcher opens each expected
   file without following substitutions, checks file identity and fs-verity
   status/digest, and compares the measured digest with the trusted manifest.
   A missing verity measurement or mismatch blocks launch for any component
   marked mandatory.
2. The launcher opens the Python ELF interpreter by descriptor and executes
   that descriptor (`fexecve`/`execveat`). At minimum, the interpreter, its ELF
   interpreter/dynamic loader, `libpython`, libc/libm, and every mandatory
   native extension and dependent shared library need the same immutable-byte
   proof. The read-only trusted runtime namespace must also stabilize the
   `PT_INTERP` and library search paths: `fexecve` on the Python binary does
   not pass an already-open dynamic-loader descriptor to the kernel. Before
   any compute import/callback, pin the actual mapped device/inode identities
   to the prevalidated artifacts; a post-import pathname hash is not a
   substitute. If that binding cannot be established before a trusted
   bootstrap runs, use one digest-verified immutable root/runtime image as the
   stronger candidate.
3. Treat interpreter startup as executed code too. The loader and CPython run
   before a Python bootstrap can inspect its environment. Build the launcher
   with an allowlisted environment that removes `LD_LIBRARY_PATH`,
   `LD_PRELOAD`, `LD_AUDIT`, and other loader controls before `exec`; do not
   assume secure-execution mode. Pin the ELF `PT_INTERP`, inspect `DT_RPATH` /
   `DT_RUNPATH`, and bind `/etc/ld.so.preload`, `/etc/ld.so.cache`, and every
   resolved shared object to the immutable runtime manifest. Later `dlopen()`
   loads (including native extensions) must resolve only to the same verified
   namespace and manifest. If that cannot be proven, the runtime is partial.
4. Launch CPython with isolated startup (`-I -S`) and a deliberately bounded
   import path. `-I` ignores `PYTHON*` environment settings and removes the
   current directory and user site-packages from `sys.path`; `-S` suppresses
   automatic `site` initialization. This prevents startup processing of
   executable `.pth` lines and imports of `sitecustomize` / `usercustomize`.
   These switches do not authenticate CPython's earlier path initialization or
   the frozen/import-bootstrap/stdlib code needed to run the bootstrap; those
   inputs remain part of the trusted runtime manifest. Any startup mode other
   than one whose import provenance is established blocks the runtime gate.
5. A minimal Python bootstrap validates an allowlisted project-source
   manifest before application imports, reads each bounded source once,
   compiles those exact bytes, and installs the resulting code into explicit
   module namespaces. Restrict import paths so unlisted source or bytecode
   cannot enter the compute path. The current armed bootstrap already compiles
   its small verified helper bundle from bytes; broadening that to the eventual
   adapter dependency graph remains unimplemented.
6. The receipt distinguishes `verified`, `partially_verified`, and
   `unavailable` per mandatory component. A partial diagnostic can be retained
   for investigation, but it cannot satisfy the accepted-compute runtime gate
   when a required interpreter, loader, library, or module lacks executed-byte
   evidence.

An immutable, digest-verified read-only runtime image is an alternative to
per-file verity, provided the launcher verifies the image before use and the
worker's mount namespace and mappings are shown to come from that image. This
also gives the dynamic loader one stable filesystem namespace for `PT_INTERP`
and library paths. Merely observing a read-only mount from the caller namespace
is not enough to infer the worker sees the same mount or that the image digest
is trusted.

## Lattice shell observations on 2026-10-05

Read-only checks in the current interactive shell observed:

- project worktree path under `/home/koi/src/caissa-jepa` is on an ext4 bind
  mount displayed read-write; `/usr/bin/python3.14` and its sampled runtime
  libraries resolve under `/`, displayed as ext4 read-only;
- `python3` resolved to `/usr/bin/python3.14`, CPython 3.14.7, cache tag
  `cpython-314`, platform `linux-x86_64`;
- the `fsverity` command was not found and `/sys/fs/verity` was absent;
- read-only `FS_IOC_MEASURE_VERITY` attempts returned errno 95 (`ENOTSUP`,
  aliased to `EOPNOTSUPP` on Linux here) for all seven sampled paths:
  `/usr/bin/python3.14`, `/usr/lib/ld-linux-x86-64.so.2`, `/usr/lib/libc.so.6`,
  `/usr/lib/libm.so.6`, `/usr/lib/libpython3.14.so.1.0`,
  `/usr/lib/python3.14/lib-dynload/_struct.cpython-314-x86_64-linux-gnu.so`,
  and `/usr/lib/python3.14/lib-dynload/fcntl.cpython-314-x86_64-linux-gnu.so`.

Reproduction commands (read-only; no service namespace is entered):

```sh
findmnt -T /home/koi/src/caissa-jepa -o TARGET,SOURCE,FSTYPE,OPTIONS
findmnt -T /usr/bin/python3.14 -o TARGET,SOURCE,FSTYPE,OPTIONS
command -v fsverity || true
ls -ld /sys/fs/verity
```

For each path above, open it `O_RDONLY` and call
`fcntl.ioctl(fd, 0xC0046686, bytearray(68), True)` after initializing the
first two little-endian `uint16` fields to `algorithm=0, digest_size=64`. The
observed result was `OSError: [Errno 95] Operation not supported`; the same
probe is represented by the following Python fragment:

```python
import fcntl, os, struct
fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
buf = bytearray(68)
struct.pack_into("=HH", buf, 0, 0, 64)
fcntl.ioctl(fd, 0xC0046686, buf, True)
```

These are observations of the interactive shell's mount/runtime view only.
`EOPNOTSUPP` does not distinguish kernel configuration, filesystem-superblock
feature state, or the execution sandbox's ioctl policy. Seccomp can reject a
system call without executing it and return an errno selected by its filter,
so errno 95 is not host-capability evidence by itself. No service namespace
was started or inspected. Therefore this does **not** prove the host lacks
fs-verity globally, but fs-verity is not currently demonstrated as usable for
this worker runtime. The root's read-only appearance is likewise not yet a
verified runtime artifact boundary: worker namespace equality, source image
identity, and mapped-library identity were not tested.

## Request/response framing consequence

The current IPC transport hard ceiling is `MAX_IPC_BYTES = 65_536`; release
messages are capped at 4,096 bytes. `read_response()` already checks path/file
identity before and after a bounded read, rejects growth beyond its configured
limit, duplicate keys, non-finite numbers, invalid UTF-8 and non-object JSON.
It returns the parsed object, however, and does not return the exact wire-byte
digest/length or enforce canonical re-encoding. Request workspace construction
serializes JSON but has no eventual request-v02 schema-derived byte cap; the
worker's raw-stdin hashing/token binding is still only proposed.

Therefore 65,536 is a transport hard limit, not a justified protocol limit.
Before implementation review, define versioned request and response schemas,
derive their explicit smaller caps from the maximum legal fields/values plus
encoding overhead, then prove both caller and worker enforce those limits even
if a backing file grows. Each side must hash the exact bounded byte string it
consumes before parsing, bind byte length and schema to the receipt, reject
non-canonical JSON, and preserve existing file-identity/reconciliation
behavior. The current same-UID workspace caveat remains: private mode and
identity checks protect cooperating processes and detect ordinary mutation,
not a hostile process with the same UID.

## Decision and next gate

Do not mark Python or native dependencies verified from `/proc/self/exe`,
`/proc/<pid>/maps`, a post-import pathname hash, CPython version fields, or
read-only bind/mount observations alone. First obtain independent review of
this execution contract and a feasibility disposition for the actual
systemd-user-worker namespace. If fs-verity or an authenticated immutable
runtime image cannot be demonstrated for every mandatory runtime dependency,
keep the worker dependency status unverified and adapter integration closed.

Primary documentation:

- [Linux kernel fs-verity documentation](https://docs.kernel.org/filesystems/fsverity.html)
- [Linux `fexecve(3)` manual](https://man7.org/linux/man-pages/man3/fexecve.3.html)
- [Python `importlib` documentation](https://docs.python.org/3/library/importlib.html)
- [Python 3.14 command-line options](https://docs.python.org/3.14/using/cmdline.html)
- [Python 3.14 `site` startup hooks](https://docs.python.org/3.14/library/site.html)
- [Linux `ld.so(8)` manual](https://man7.org/linux/man-pages/man8/ld.so.8.html)
- [Linux `seccomp(2)` manual](https://man7.org/linux/man-pages/man2/seccomp.2.html)

The kernel documentation describes fs-verity's read-time checks and the need
to authenticate its measured digest; the Linux manual documents the remaining
file-content race for `fexecve`; Python documents compiling source bytes into a
code object that can then be executed in a module namespace. These support the
component properties above, not a claim that CAISSA-JEPA has implemented or
validated the proposed chain.

The Python documentation confirms the distinct effects of `-I` and `-S`, and
that `.pth` executable lines plus `sitecustomize` / `usercustomize` execute
during automatic `site` startup. The loader manual documents library search
ordering, environment-based preload/audit behavior, cache/preload files, and
ELF RPATH/RUNPATH. The seccomp manual documents `SECCOMP_RET_ERRNO`; together
these sources justify treating startup and loader configuration as inputs to
the executed-runtime evidence, not as claims that these controls were tested
in the service namespace.
