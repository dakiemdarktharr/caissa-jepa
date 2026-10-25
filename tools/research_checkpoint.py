"""Commit explicit, reviewed small files and optionally verify a normal push.

No scheduler is installed. Invoke at a milestone or the active-work checkpoint
deadline. Scientific/test acceptance remains the caller's responsibility.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


DEFAULT_REMOTE = "git@github.com:dakiemdarktharr/caissa-jepa.git"
ALLOWED = {".py", ".md", ".json", ".csv", ".yaml", ".yml", ".toml", ".txt", ".tex", ".bib"}
EXCLUDED = {"chess_data", "fen_dataset", "downloads", "build", "dist", ".venv", ".git", ".aws", ".codex", ".agents"}


def git(root, *args, check=True):
    return subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *args],
                          check=check, text=True, capture_output=True)


def checkpoint(root, paths, message, *, push=False, expected_remote=DEFAULT_REMOTE, branch="main"):
    root = Path(root).resolve()
    if not paths or not message.strip():
        raise ValueError("explicit files and a commit message are required")
    if git(root, "rev-parse", "--show-toplevel").stdout.strip() != str(root):
        raise ValueError("use the repository root")
    if git(root, "branch", "--show-current").stdout.strip() != branch:
        raise ValueError("current branch does not match the expected branch")
    remotes = git(root, "remote", "get-url", "--push", "--all", "origin").stdout.splitlines()
    if remotes != [expected_remote]:
        raise ValueError("push destination differs from the explicitly expected remote")
    if git(root, "diff", "--cached", "--name-only").stdout:
        raise ValueError("index already contains staged work; preserve it and inspect manually")
    selected, total = [], 0
    for name in paths:
        p = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts or any(part in EXCLUDED for part in Path(name).parts):
            raise ValueError("excluded or outside-repository path")
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root):
            raise ValueError("explicit existing regular files are required")
        if p.suffix not in ALLOWED or p.stat().st_size > 2_000_000:
            raise ValueError("only small source/documentation/curated-result files are allowed")
        if git(root, "check-ignore", "--no-index", "-q", "--", name, check=False).returncode == 0:
            raise ValueError("ignored artifact cannot be checkpointed by this tool")
        total += p.stat().st_size
        selected.append(name)
    if total > 10_000_000:
        raise ValueError("checkpoint exceeds the 10 MB curated-file budget")
    git(root, "add", "--", *selected)
    # CSV's standard CRLF terminator is valid data. Accept it without disabling
    # checks for spaces before the terminator or other source whitespace errors.
    git(root, "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol",
        "diff", "--cached", "--check")
    changed = bool(git(root, "diff", "--cached", "--name-only").stdout)
    if changed:
        git(root, "commit", "-m", message)
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    remote_head = None
    if push:
        # This is deliberately a normal push: divergence is never overwritten.
        git(root, "push", "origin", f"HEAD:refs/heads/{branch}")
        rows = git(root, "ls-remote", expected_remote, f"refs/heads/{branch}").stdout.splitlines()
        remote_head = rows[0].split()[0] if len(rows) == 1 else None
        if remote_head != head:
            raise RuntimeError("push is not verified at the expected remote head")
    return {"commit": head, "created_commit": changed, "destination": expected_remote,
            "branch": branch, "remote_head": remote_head, "remote_verified": remote_head == head,
            "selected_files": selected, "validation": "staged whitespace check; caller supplies substantive checks"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--message", required=True)
    p.add_argument("--push", action="store_true")
    p.add_argument("--expected-remote", default=DEFAULT_REMOTE)
    p.add_argument("--branch", default="main")
    p.add_argument("paths", nargs="+")
    args = p.parse_args()
    print(json.dumps(checkpoint(args.repo, args.paths, args.message, push=args.push,
                               expected_remote=args.expected_remote, branch=args.branch), indent=2))


if __name__ == "__main__":
    main()
