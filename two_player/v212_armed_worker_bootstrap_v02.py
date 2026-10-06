"""Candidate raw-stdin worker bootstrap for the v02 armed protocol.

This module only builds a bootstrap source and its synthetic request manifest.
It does not launch systemd, the request adapter, inference, or an OOM test.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUEST_SCHEMA = "caissa.synthetic.armed-bootstrap-request.v02"
MAX_REQUEST_BYTES = 65_536
MAX_SOURCE_BYTES = 262_144
WORKER_MODULES = (
    "two_player/v212_worker_ipc.py",
    "two_player/v212_release_token_v01.py",
    "two_player/v212_armed_protocol_v01.py",
    "two_player/v212_release_token_v02.py",
    "two_player/v212_armed_protocol_v02.py",
)


def worker_source() -> str:
    """Return a small no-inference worker entrypoint using exact raw stdin."""
    return r'''import hashlib,json,os,stat,sys,syslog,time,types
from pathlib import Path

MAX_REQUEST_BYTES=65536
MAX_SOURCE_BYTES=262144
def read_raw_request():
    chunks=bytearray()
    while True:
        count=MAX_REQUEST_BYTES+1-len(chunks)
        block=os.read(0,min(4096,count))
        if not block: return bytes(chunks)
        chunks.extend(block)
        if len(chunks)>MAX_REQUEST_BYTES: sys.exit(30)

def reject_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError("duplicate request key")
        out[key]=value
    return out

def reject_constant(value): raise ValueError("non-finite request value")
request_raw=read_raw_request()
try:
    request=json.loads(request_raw.decode("utf-8",errors="strict"),
                       object_pairs_hook=reject_pairs,parse_constant=reject_constant)
except (UnicodeError,ValueError,RecursionError):
    sys.exit(31)
if (not isinstance(request,dict) or set(request)!={"schema","nonce","source_manifest","source_manifest_sha256"}
        or request.get("schema")!="caissa.synthetic.armed-bootstrap-request.v02"):
    sys.exit(32)
nonce=request.get("nonce")
if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in "0123456789abcdef" for c in nonce):
    sys.exit(33)
try:
    canonical_request=json.dumps(request,sort_keys=True,separators=(",",":"),
                                 ensure_ascii=False,allow_nan=False).encode("utf-8")
except (TypeError,ValueError,UnicodeError,RecursionError):
    sys.exit(43)
if canonical_request!=request_raw: sys.exit(43)

# The raw request is bounded and parsed before project helper files are opened.
root=Path(sys.argv[3]).resolve(strict=True)
argv=Path("/proc/self/cmdline").read_bytes().split(b"\0")
if len(argv)<7 or argv[1:5]!=[b"-I",b"-S",b"-B",b"-c"]: sys.exit(34)
manifest=request["source_manifest"]
if not isinstance(manifest,dict) or set(manifest)!={"bootstrap_sha256","files"}: sys.exit(35)
if hashlib.sha256(argv[5]).hexdigest()!=manifest["bootstrap_sha256"]: sys.exit(36)
expected={"two_player/v212_worker_ipc.py","two_player/v212_release_token_v01.py",
          "two_player/v212_armed_protocol_v01.py","two_player/v212_release_token_v02.py",
          "two_player/v212_armed_protocol_v02.py"}
files=manifest.get("files")
if not isinstance(files,dict) or set(files)!=expected: sys.exit(37)
if (not hasattr(os,"O_NOFOLLOW") or not hasattr(os,"O_DIRECTORY")
        or not hasattr(os,"O_NONBLOCK") or not hasattr(os,"O_NOCTTY")): sys.exit(41)
def read_verified_source(relative,digest):
    parts=relative.split("/")
    if len(parts)!=2 or parts[0]!="two_player": sys.exit(38)
    opened=[]
    try:
        root_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        opened.append(root_fd)
        package_fd=os.open(parts[0],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=root_fd)
        opened.append(package_fd)
        source_fd=os.open(parts[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_NOCTTY,
                           dir_fd=package_fd)
        opened.append(source_fd)
        info=os.fstat(source_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_SOURCE_BYTES: sys.exit(42)
        content=bytearray()
        while True:
            block=os.read(source_fd,min(65536,MAX_SOURCE_BYTES+1-len(content)))
            if not block: break
            content.extend(block)
            if len(content)>MAX_SOURCE_BYTES: sys.exit(42)
        data=bytes(content)
        if hashlib.sha256(data).hexdigest()!=digest: sys.exit(39)
        return data
    except OSError:
        sys.exit(38)
    finally:
        for fd in reversed(opened): os.close(fd)

verified={}
for relative,digest in files.items():
    verified[relative]=read_verified_source(relative,digest)
canonical=json.dumps(manifest,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
if hashlib.sha256(canonical).hexdigest()!=request.get("source_manifest_sha256"): sys.exit(40)

package=types.ModuleType("two_player")
package.__path__=[]
package.__package__="two_player"
sys.modules["two_player"]=package
module_files=(
    ("v212_worker_ipc","two_player/v212_worker_ipc.py"),
    ("v212_release_token_v01","two_player/v212_release_token_v01.py"),
    ("v212_armed_protocol_v01","two_player/v212_armed_protocol_v01.py"),
    ("v212_release_token_v02","two_player/v212_release_token_v02.py"),
    ("v212_armed_protocol_v02","two_player/v212_armed_protocol_v02.py"),
)
for short,relative in module_files:
    name="two_player."+short
    module=types.ModuleType(name)
    module.__file__=str(root/relative)
    module.__package__="two_player"
    sys.modules[name]=module
    exec(compile(verified[relative],module.__file__,"exec"),module.__dict__)
    setattr(package,short,module)

ipc=sys.modules["two_player.v212_worker_ipc"]
release=sys.modules["two_player.v212_release_token_v02"]
armed=sys.modules["two_player.v212_armed_protocol_v02"]
directory=Path(sys.argv[1])
unit=sys.argv[2]
boot=Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip().replace("-","").lower()
matches=[line[3:] for line in Path("/proc/self/cgroup").read_text(encoding="ascii").splitlines() if line.startswith("0::")]
if len(matches)!=1: sys.exit(41)
group=matches[0]
def identity(name): return ipc.FileIdentity.from_stat(os.stat(directory/name,follow_symlinks=False))
directory_info=os.stat(directory,follow_symlinks=False)
workspace=ipc.WorkerIPCWorkspace(
    directory=directory,request_path=directory/ipc.REQUEST_NAME,
    response_path=directory/ipc.RESPONSE_NAME,
    response_identity=identity(ipc.RESPONSE_NAME),
    request_identity=identity(ipc.REQUEST_NAME),
    directory_device=directory_info.st_dev,directory_inode=directory_info.st_ino,
    request_bytes=(directory/ipc.REQUEST_NAME).stat().st_size,
    release_path=directory/ipc.RELEASE_NAME,
    release_identity=identity(ipc.RELEASE_NAME))
def callback(token):
    invocation=os.environ.get("INVOCATION_ID","")
    if len(invocation)!=32: raise RuntimeError("missing systemd invocation ID")
    syslog.syslog(syslog.LOG_INFO,"CAISSA_V212_NO_INFERENCE_MARKER "+invocation)
    time.sleep(0.1)
    return {"schema":"caissa.v212.armed-no-inference-response.v02",
            "nonce":nonce,"request_sha256":token["request_sha256"],
            "status":"released_no_inference"}
response=armed.run_synthetic_armed_worker(
    workspace,request_bytes=request_raw,expected_nonce=nonce,
    expected_service_unit=unit,invocation_id=os.environ.get("INVOCATION_ID"),
    boot_id=boot,self_control_group=group,
    expected_source_manifest_sha256=request["source_manifest_sha256"],
    on_release=callback)
json.dump(response,sys.stdout,separators=(",",":"),allow_nan=False)
sys.stdout.write("\n")
sys.stdout.flush()
'''


def source_manifest(repo_root: Path, source: str | None = None
                    ) -> tuple[dict[str, Any], str]:
    bootstrap = worker_source() if source is None else source
    files = {
        relative: hashlib.sha256((repo_root / relative).read_bytes()).hexdigest()
        for relative in WORKER_MODULES
    }
    manifest = {
        "bootstrap_sha256": hashlib.sha256(bootstrap.encode("utf-8")).hexdigest(),
        "files": files,
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return manifest, hashlib.sha256(encoded).hexdigest()


def request_bytes(nonce: str, manifest: dict[str, Any],
                  manifest_sha256: str) -> bytes:
    if (not isinstance(nonce, str) or len(nonce) != 32
            or any(character not in "0123456789abcdef" for character in nonce)):
        raise ValueError("nonce must be 32 lowercase hexadecimal characters")
    value = {
        "schema": REQUEST_SCHEMA,
        "nonce": nonce,
        "source_manifest": manifest,
        "source_manifest_sha256": manifest_sha256,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


__all__ = ["MAX_REQUEST_BYTES", "MAX_SOURCE_BYTES", "REQUEST_SCHEMA", "WORKER_MODULES",
           "request_bytes", "source_manifest", "worker_source"]
