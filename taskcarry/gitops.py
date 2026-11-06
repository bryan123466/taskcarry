"""Bounded local Git helpers. No remote transport, arbitrary shell, or force reset."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

from .store import GovernanceError
from .core import _linked, validate_relative_path
from .path_batches import path_batches

MAX_DELIVERY_PATHS = 500
MAX_BLOB_BYTES = 32 * 1024 * 1024
MAX_DELIVERY_BYTES = 128 * 1024 * 1024


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def git(path, *args, data=None, check=True, timeout=60):
    env = os.environ.copy()
    # Git environment variables inherited from hooks must not redirect our scope.
    for key in list(env):
        if key.startswith("GIT_"):
            env.pop(key, None)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "TaskCarry",
                "GIT_AUTHOR_EMAIL": "toolkit@localhost", "GIT_COMMITTER_NAME": "TaskCarry",
                "GIT_COMMITTER_EMAIL": "toolkit@localhost"})
    argv = ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "commit.gpgsign=false",
            "-c", "merge.autoStash=false", "-c", "core.quotePath=false", "-C", str(path), *map(str, args)]
    try:
        cp = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, timeout=timeout, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GovernanceError("GIT_UNAVAILABLE", str(exc)) from exc
    if check and cp.returncode:
        raise GovernanceError("GIT_FAILED", cp.stderr.decode("utf-8", "replace").strip(), {"args": list(args), "returncode": cp.returncode})
    return cp


def out(path, *args):
    return git(path, *args).stdout.decode("utf-8", "strict").strip()


def repo(path):
    raw = Path(path).expanduser().absolute()
    if any(_linked(x) for x in [raw, *raw.parents]):
        raise GovernanceError("UNSUPPORTED_FILE_TYPE", "Workspace roots cannot traverse symlinks or junctions")
    p = raw.resolve()
    if not p.is_dir():
        raise GovernanceError("WORKSPACE_MISSING", "Workspace does not exist")
    actual = Path(out(p, "rev-parse", "--show-toplevel")).resolve()
    if actual != p:
        raise GovernanceError("WORKSPACE_ROOT_REQUIRED", "Use the exact Git workspace root")
    if out(p, "rev-parse", "--is-bare-repository") != "false":
        raise GovernanceError("BARE_REPOSITORY", "A working tree is required")
    return p


def commit(path, value):
    if not isinstance(value, str) or value.startswith("-") or not value or len(value) > 256:
        raise GovernanceError("INVALID_COMMIT", "Invalid commit identifier")
    return out(path, "rev-parse", "--verify", "--end-of-options", value + "^{commit}")


def ancestor(path, older, newer):
    result = git(path, "merge-base", "--is-ancestor", older, newer, check=False)
    if result.returncode not in (0, 1):
        raise GovernanceError("GIT_FAILED", "Could not check commit ancestry")
    return result.returncode == 0


def pathsafe(value):
    if not isinstance(value, str) or "\\" in value or "\0" in value or ":" in value:
        raise GovernanceError("INVALID_PATH", "Use a repository-relative POSIX path")
    p = PurePosixPath(value)
    if not value or p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")):
        raise GovernanceError("INVALID_PATH", "Path must stay inside the workspace")
    lower = [x.lower() for x in p.parts]
    if any(x in {".git", ".taskcarry", ".ssh"} for x in lower):
        raise GovernanceError("RESERVED_PATH", "Governance and Git internals are not deliverables")
    name = lower[-1]
    if name == ".env" or name.startswith(".env.") and name not in {".env.example", ".env.sample"} or name in {"id_rsa", "id_ed25519", "credentials.json", "auth.json"} or name.endswith((".pfx", ".p12", ".key")):
        raise GovernanceError("SENSITIVE_PATH", "This credential-like path requires a separate workflow")
    return value


def changed(path, base, head):
    data = git(path, "diff", "--no-renames", "--name-only", "-z", base, head, "--").stdout
    return sorted(x.decode("utf-8") for x in data.split(b"\0") if x)


def assert_tree_types(path, ref, paths):
    if len(paths) > MAX_DELIVERY_PATHS:
        raise GovernanceError("DELIVERY_TOO_LARGE", "Split stable stages with more than 500 paths")
    if not paths:
        return 0
    data = b''.join(git(path, "--literal-pathspecs", "ls-tree", "-z", "-l", ref, "--", *batch).stdout
                    for batch in path_batches(paths))
    total = 0
    for entry in data.split(b"\0"):
        if not entry:
            continue
        header, _, rel = entry.partition(b"\t")
        fields = header.split()
        if fields[0] not in {b"100644", b"100755"}:
            raise GovernanceError("UNSUPPORTED_FILE_TYPE", "Symlinks, directories and submodules cannot be submitted", {"path": rel.decode("utf-8")})
        size = int(fields[3])
        total += size
        if size > MAX_BLOB_BYTES or total > MAX_DELIVERY_BYTES:
            raise GovernanceError("DELIVERY_TOO_LARGE", "Use artifact references for oversized binary or aggregate delivery content")
    return total


def identity(path):
    return {"path": str(path), "common_dir": str(Path(out(path, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()),
            "branch": out(path, "symbolic-ref", "--quiet", "HEAD")}


def fingerprint(path):
    raw = git(path, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    untracked = git(path, "ls-files", "--others", "--exclude-standard", "-z").stdout
    extras = {}
    for item in untracked.split(b"\0"):
        if not item:
            continue
        rel = item.decode("utf-8")
        p = validate_relative_path(path, rel, allow_missing=False)
        if p.stat().st_size > 64 * 1024 * 1024:
            raise GovernanceError("FILE_TOO_LARGE", "Use artifact references for files over 64 MiB")
        extras[rel] = digest(p.read_bytes())
    return {"head": commit(path, "HEAD"), "status": raw.hex(),
            "index": digest(git(path, "ls-files", "--stage", "-z").stdout),
            "work_diff": digest(git(path, "diff", "--binary", "--no-ext-diff", "--no-textconv", "--").stdout),
            "untracked": extras}


def clean(path):
    return not git(path, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip()


def import_commit(destination, source, sha):
    source = repo(source)
    git(destination, "-c", "protocol.file.allow=always", "fetch", "--no-tags", "--no-write-fetch-head", str(source), sha)
    if commit(destination, sha) != sha:
        raise GovernanceError("COMMIT_CHANGED", "Imported commit did not match the frozen commit")


class Scratch:
    def __init__(self, repository, scratch_root, ref):
        self.repository = repository
        raw_root = Path(scratch_root).absolute()
        if any(_linked(x) for x in [raw_root, *raw_root.parents]):
            raise GovernanceError("UNSUPPORTED_FILE_TYPE", "Scratch storage cannot traverse symlinks or junctions")
        self.scratch_root = raw_root.resolve()
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix="git-", dir=self.scratch_root))
        self.ref = ref

    def __enter__(self):
        git(self.repository, "worktree", "add", "--detach", str(self.path), self.ref)
        return self.path

    def __exit__(self, *exc):
        # Only an exact directory created by this object, inside its private scratch root.
        if self.path.resolve().is_relative_to(self.scratch_root) and self.path.parent == self.scratch_root:
            git(self.repository, "worktree", "remove", "--force", str(self.path), check=False)
