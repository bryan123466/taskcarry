"""Versioned, private workbench navigation through the shared governance engine.

Views are derived guidance, never a second task database. Publication, evidence
of consumption, code adoption and business acceptance remain separate facts.
The Codex adapter changes only one protected instruction section; the generic
publication engine also supports ignored navigation files without a host.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path, PurePosixPath
import re
import tomllib
import uuid

from .core import Core, _id, _linked, digest_bytes, git, read_file_bytes, validate_relative_path
from .gitops import git as repository_git
from .store import GovernanceError, now

MAX_BYTES = 256 * 1024
MAX_PLAN_BYTES = 8 * 1024 * 1024
SOURCE_COLLECTIONS = {"tasks", "workspaces", "checkpoints", "stages", "operations", "issues", "fixes", "experience", "runs", "observations",
                      "governance_facts", "governance_cycles", "scan_sources"}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def fail(message, code="WORKBENCH_CONFLICT"):
    raise GovernanceError(code, message)


def _hash(data):
    return digest_bytes(data) if data is not None else None


def _links(path):
    path = Path(path).absolute()
    if any(_linked(p) for p in (path, *path.parents)):
        fail("Workbench paths cannot traverse links or junctions.", "UNSAFE_PATH")
    return path


def _read(path, maximum=MAX_BYTES):
    path = _links(path)
    try:
        return read_file_bytes(path, maximum)
    except FileNotFoundError:
        return None


def atomic_write(path, content):
    """The final name is never visible with a partially written body."""
    path = _links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _links(path)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _links(path)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def immutable(path, content):
    """Called under Store.guard; durable intent precedes every publication."""
    existing = _read(path, MAX_PLAN_BYTES)
    if existing is not None:
        if existing != content:
            fail("An immutable workbench object differs; preserve it for review.")
        return
    atomic_write(path, content)


def managed_section(original, section_id, text):
    _id(section_id, "Section ID")
    original = original or b""
    original.decode("utf-8-sig")
    if not isinstance(text, str) or len(text.encode()) > MAX_BYTES:
        fail("Managed text exceeds the bounded text limit.", "INVALID_ARGUMENT")
    start = ("<!-- taskcarry:" + section_id + ":begin -->").encode()
    end = ("<!-- taskcarry:" + section_id + ":end -->").encode()
    if b"<!-- taskcarry:" in text.encode():
        fail("Managed text cannot contain nested TaskCarry markers.")
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    body = text.replace("\r\n", "\n").strip("\n").encode().replace(b"\n", newline)
    block = start + newline + body + newline + end
    if original.count(start) == original.count(end) == 0:
        separator = b"" if not original or original.endswith((b"\n", b"\r")) else newline
        return original + separator + block + newline
    if original.count(start) != 1 or original.count(end) != 1:
        fail("Managed markers are incomplete or duplicated.")
    first, last = original.index(start), original.index(end)
    if last < first or (first and original[first - 1:first] != b"\n"):
        fail("Managed markers must be ordered and start on their own line.")
    tail = last + len(end)
    if original[tail:tail + 1] not in (b"", b"\r", b"\n"):
        fail("Managed markers must end on their own line.")
    if b"<!-- taskcarry:" in original[first + len(start):last]:
        fail("Managed sections cannot nest.")
    return original[:first] + block + original[tail:]


def _string_end(text, start):
    """Locate one TOML string value; tomllib validates its actual semantics."""
    if start >= len(text) or text[start] not in "\"'":
        return None
    quote = text[start]
    delimiter = quote * 3 if text.startswith(quote * 3, start) else quote
    index = start + len(delimiter)
    while index < len(text):
        if quote == '"' and text[index] == "\\":
            index += 2
        elif text.startswith(delimiter, index):
            end = index + len(delimiter)
            if len(delimiter) == 3:
                while end < len(text) and text[end] == quote:
                    end += 1
            return end
        else:
            index += 1
    return None


def codex_instructions(original, instructions):
    """Preserve bytes outside the instruction value, and custom text inside it.

    Candidate locations are accepted only if parsing proves that replacing the
    token changes the top-level developer_instructions field and nothing else.
    This also excludes key-looking text inside other multiline strings/tables.
    """
    original = original or b""
    text = original.decode("utf-8-sig")
    try:
        before = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        fail("Existing Codex configuration is invalid TOML: " + str(exc))
    previous = before.get("developer_instructions", "")
    if not isinstance(previous, str):
        fail("developer_instructions must be a string.")
    updated = managed_section(previous.encode(), "workbench-entry", instructions).decode()
    encoded = json.dumps(updated, ensure_ascii=False)
    expected = dict(before, developer_instructions=updated)
    if "developer_instructions" not in before:
        newline = "\r\n" if "\r\n" in text else "\n"
        result = "developer_instructions = " + encoded + newline + text
    else:
        result = None
        pattern = r"(?m)^[ \t]*(?:developer_instructions|\"developer_instructions\"|'developer_instructions')[ \t]*=[ \t]*"
        for match in re.finditer(pattern, text):
            end = _string_end(text, match.end())
            if end is None:
                continue
            candidate = text[:match.end()] + encoded + text[end:]
            try:
                if tomllib.loads(candidate) == expected:
                    if result is not None:
                        fail("Ambiguous developer instruction field; preserve it for manual review.")
                    result = candidate
            except tomllib.TOMLDecodeError:
                continue
        if result is None:
            fail("Cannot safely locate the top-level instruction value.")
    if tomllib.loads(result) != expected:
        fail("Codex adapter would change unrelated configuration.")
    return (b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b"") + result.encode()


def git_snapshot(root):
    """No refresh or write: preserve HEAD, index bytes and existing WIP."""
    root = _links(root)
    output = lambda *args: git(root, *args).stdout.decode("utf-8").strip()
    if Path(output("rev-parse", "--show-toplevel")).resolve() != root.resolve():
        fail("Use the registered Git worktree root.")
    index = Path(output("rev-parse", "--path-format=absolute", "--git-path", "index"))
    return {"root": str(root), "common_dir": output("rev-parse", "--path-format=absolute", "--git-common-dir"),
            "branch": output("symbolic-ref", "--quiet", "HEAD"), "head": output("rev-parse", "HEAD"),
            "index_sha256": _hash(_read(index, 32 * 1024 * 1024))}


def private_target(root, relative):
    if not isinstance(relative, str) or PurePosixPath(relative).as_posix() != relative:
        fail("Use a canonical relative target path.", "UNSAFE_PATH")
    path = validate_relative_path(root, relative)
    if git(root, "ls-files", "-z", "--", relative).stdout or git(root, "ls-tree", "-z", "HEAD", "--", relative).stdout:
        fail("Private workbench entries must not be tracked or staged: " + relative, "WORKBENCH_PUBLIC_PATH")
    # check-ignore accepts literal filenames but rejects Git's global literal
    # pathspec mode, so use the bounded helper without that global switch.
    if repository_git(root, "--no-optional-locks", "check-ignore", "--no-index", "--quiet", "--", relative, check=False).returncode != 0:
        fail("Private workbench targets must already be Git-ignored: " + relative, "WORKBENCH_PRIVATE_PATH_REQUIRED")
    return path


class Workbench(Core):
    def _path(self, *parts):
        return _links(self.store.directory.joinpath("workbench", *parts))

    def _source_ids(self):
        current = self.source()
        return {current["source_id"], *current.get("aliases", [])}

    def _same_local_source(self, recorded):
        """Only a same-location legacy identity adoption can cross an alias.

        Replica changes and path moves need new plans. Older immutable objects
        stay unchanged; a registered alias is not cross-host write authority.
        """
        current = self.source()
        if not isinstance(recorded, dict) or recorded.get("control") != current["control"]:
            return False
        if recorded.get("source_id") == current["source_id"]:
            return recorded.get("replica_id") == current.get("replica_id")
        return (recorded.get("identity_scope") == "resolved_local_path"
                and recorded.get("replica_id") is None
                and recorded.get("source_id") in current.get("aliases", []))

    @staticmethod
    def _sha(value, label):
        if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
            fail(label + " must be a SHA-256 identifier.", "INVALID_ARGUMENT")
        return value

    def _object(self, collection, key, value):
        prior = self.store.get(collection, key)
        if prior is not None:
            if prior != value:
                fail("Immutable workbench record differs: " + key)
            return False
        self.store.put(collection, key, value)
        self.store.event(collection, {"id": key})
        return True

    def _source_revision(self, source):
        if source.get("collection"):
            if source["source_id"] not in self._source_ids() or source["collection"] not in SOURCE_COLLECTIONS:
                fail("Record sources must refer to this control and a supported collection.", "WORKBENCH_SOURCE_MISMATCH")
            local_id = source.get("local_id")
            # These are bounded record keys, not task IDs or filesystem paths.
            # Source-qualified fact keys include a namespace hash and colon.
            if not isinstance(local_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}", local_id) is None:
                fail("Source local ID must be a bounded exact record key.", "INVALID_ARGUMENT")
            record = self.store.get(source["collection"], local_id)
            return _hash(canonical(record)) if record is not None else None
        if source.get("path"):
            return _hash(_read(validate_relative_path(self.root, source["path"])))
        return None

    def _freshness(self, view):
        result = []
        for source in view["manifest"]["sources"]:
            try:
                revision = self._source_revision(source)
                state = "UNVERIFIED_REFERENCE" if not (source.get("path") or source.get("collection")) else (
                    "MATCHES" if revision == source["revision"] else "CHANGED_OR_MISSING")
                result.append({"source_id": source["source_id"], "state": state, "revision": source["revision"], "observed_revision": revision})
            except (GovernanceError, OSError, ValueError) as exc:
                result.append({"source_id": source["source_id"], "state": "UNREADABLE", "error": str(exc)[:300]})
        return result

    def _freeze(self, body, sources):
        if not isinstance(body, str) or not body.strip() or len(body.encode()) > MAX_BYTES:
            fail("Freeze requires 1-256 KiB of nonempty view text.", "INVALID_ARGUMENT")
        if not isinstance(sources, list) or not 1 <= len(sources) <= 50:
            fail("Freeze requires 1-50 explicit source revisions.", "INVALID_ARGUMENT")
        normalized = []
        for source in sources:
            if not isinstance(source, dict) or set(source) - {"source_id", "revision", "collection", "local_id", "path"}:
                fail("Unsupported source fields.", "INVALID_ARGUMENT")
            if any(not isinstance(source.get(key), str) or not source[key].strip() or len(source[key]) > 500 for key in ("source_id", "revision")):
                fail("Each source needs bounded identity and revision.", "INVALID_ARGUMENT")
            if bool(source.get("collection")) != bool(source.get("local_id")) or (source.get("path") and source.get("collection")):
                fail("Use a record reference, file reference or explicit external revision.", "INVALID_ARGUMENT")
            observed = self._source_revision(source)
            if (source.get("path") or source.get("collection")) and observed != source["revision"]:
                fail("A source no longer matches its declared revision.", "WORKBENCH_SOURCE_CHANGED")
            normalized.append(dict(source))
        manifest = {"schema": "taskcarry.workbench.view.v1", "source": self.source(), "sources": normalized,
                    "body_sha256": digest_bytes(body.encode()), "body_bytes": len(body.encode()),
                    "meaning": "Derived navigation; query Core for current task state."}
        view_id = digest_bytes(canonical(manifest))
        record = {"manifest": manifest, "body": body}
        with self.store.guard():
            with self.store.transaction():
                created = self._object("workbench_views", view_id, record)
            immutable(self._path("views", view_id, "view.md"), body.encode())
            immutable(self._path("views", view_id, "manifest.json"), canonical(manifest))
        return {"view_id": view_id, "created": created, "view_path": str(self._path("views", view_id, "view.md")),
                "manifest_path": str(self._path("views", view_id, "manifest.json")), "sources": self._freshness(record)}

    def _view(self, view_id):
        self._sha(view_id, "View ID")
        record = self.store.get("workbench_views", view_id)
        if not record or record.get("manifest", {}).get("schema") != "taskcarry.workbench.view.v1":
            fail("View is missing or has an unsupported schema.")
        manifest = record["manifest"]
        if not self._same_local_source(manifest.get("source")):
            fail("This view belongs to another control or replica; freeze a local view.")
        if (digest_bytes(canonical(manifest)) != view_id or _hash(record["body"].encode()) != manifest["body_sha256"]
                or len(record["body"].encode()) != manifest["body_bytes"]
                or _read(self._path("views", view_id, "manifest.json")) != canonical(manifest)
                or _read(self._path("views", view_id, "view.md")) != record["body"].encode()):
            fail("View integrity check failed; repeat the original freeze only for missing publication steps.")
        return record

    def _binding(self, workspace, task_id):
        from .integration import Integration
        self._task(task_id)
        workspace = _id(workspace, "Workspace")
        root = Integration(self.root)._ws(workspace)
        if root != self.root and _links(root / ".taskcarry" / "state.sqlite3").exists():
            fail("This workbench already has a separate control.")
        for relative in (".taskcarry/workbench.json", ".taskcarry/setup-manifest.json"):
            raw = _read(root / relative)
            if raw is not None:
                try:
                    record = json.loads(raw)
                    binding = record.get("binding") if relative.endswith("setup-manifest.json") else record
                except (ValueError, AttributeError):
                    fail("Existing connection binding cannot be read.")
                if binding and any(binding.get(key) != value for key, value in (
                        ("control", str(self.root)), ("target", str(root)), ("workspace", workspace), ("task_id", task_id))):
                    fail("Keep the workbench's original task/control binding.", "WORKBENCH_BINDING_MISMATCH")
        return root

    def _pointer(self, workspace):
        raw = _read(self._path("current", workspace + ".json"))
        if raw is None:
            return None
        try:
            pointer = json.loads(raw)
            receipt = self.store.get("workbench_receipts", pointer["receipt_id"])
            if (pointer.get("schema") != "taskcarry.workbench.current.v1" or pointer.get("workspace") != workspace
                    or pointer.get("source_id") not in self._source_ids() or not receipt
                    or any(pointer.get(key) != receipt.get(key) for key in ("workspace", "task_id", "plan_id", "view_id", "source_id"))
                    or raw != canonical(pointer)):
                fail("Current pointer does not match its immutable publication receipt.")
            return pointer
        except (ValueError, KeyError, TypeError) as exc:
            fail("Current pointer is invalid: " + str(exc))

    def _instructions(self, row, view_id):
        return ("Read the TaskCarry current entry at " + str(self._path("current", row["workspace"] + ".json")) + ".\n"
                "Published view: " + str(self._path("views", view_id, "view.md")) + ".\n"
                "Keep workspace " + row["workspace"] + ", original task " + row["task_id"] + ", and the same control " + str(self.root) + ".\n"
                "Use Core to check the latest task and checkpoint. This versioned view is guidance, not live task state.\n"
                "Continue your existing responsibility and WIP. A navigation update does not initialize, receive, adopt or release work.\n"
                "Report actual host loading and source differences; publication alone does not prove consumption.")

    def _plan(self, view_id, targets):
        self._view(view_id)
        if not isinstance(targets, list) or not 1 <= len(targets) <= 24:
            fail("Plan requires 1-24 explicit workbenches.", "INVALID_ARGUMENT")
        rows, seen, roots = [], set(), set()
        with self.store.guard():
            for target in targets:
                if not isinstance(target, dict) or set(target) - {"workspace", "task_id", "thread_id", "source_id", "host", "code_assessment", "writes"}:
                    fail("Unsupported target fields.", "INVALID_ARGUMENT")
                workspace, task_id = target.get("workspace"), target.get("task_id")
                root = self._binding(workspace, task_id)
                if workspace in seen or os.path.normcase(str(root)) in roots:
                    fail("Duplicate workspace or root in a plan.", "INVALID_ARGUMENT")
                seen.add(workspace)
                roots.add(os.path.normcase(str(root)))
                _id(target.get("thread_id"), "Thread ID")
                if target.get("source_id", self.source()["source_id"]) not in self._source_ids():
                    fail("Workbench task belongs to another source.", "WORKBENCH_SOURCE_MISMATCH")
                previous = self._pointer(workspace)
                if previous and previous["task_id"] != task_id:
                    fail("A workbench entry must retain its original task.", "WORKBENCH_BINDING_MISMATCH")
                assessment = target.get("code_assessment")
                if (not isinstance(assessment, dict) or set(assessment) != {"status", "reason"}
                        or assessment.get("status") not in {"NO_CODE_DEPENDENCY", "ALREADY_CONTAINS", "SEPARATE_CODE_PLAN_REQUIRED"}
                        or not isinstance(assessment.get("reason"), str) or not 1 <= len(assessment["reason"].strip()) <= 2000):
                    fail("Each workbench needs an explicit bounded code-dependency assessment.", "INVALID_ARGUMENT")
                host = target.get("host", "codex")
                if host not in ("codex", "none"):
                    fail("Unsupported workbench host.", "INVALID_ARGUMENT")
                row = {"workspace": workspace, "task_id": task_id, "thread_id": target["thread_id"],
                       "source_id": self.source()["source_id"], "root": str(root), "host": host,
                       "code_assessment": assessment, "git": git_snapshot(root), "previous": previous, "writes": []}
                specs = target.get("writes", [])
                if not isinstance(specs, list) or len(specs) > 16:
                    fail("At most 16 explicit navigation writes per workbench.", "INVALID_ARGUMENT")
                paths = set()
                if host == "codex":
                    path = private_target(root, ".codex/config.toml")
                    old = _read(path)
                    row["writes"].append(self._write_record(".codex/config.toml", old, codex_instructions(old, self._instructions(row, view_id))))
                    paths.add(".codex/config.toml")
                for spec in specs:
                    if not isinstance(spec, dict) or set(spec) - {"path", "mode", "section_id", "text", "expected_sha256"}:
                        fail("Unsupported write fields.", "INVALID_ARGUMENT")
                    relative = spec.get("path")
                    path = private_target(root, relative)
                    if relative.casefold() in paths:
                        fail("Duplicate or case-colliding target path.", "INVALID_ARGUMENT")
                    paths.add(relative.casefold())
                    old = _read(path)
                    text = spec.get("text")
                    if not isinstance(text, str) or len(text.encode()) > MAX_BYTES:
                        fail("Navigation text must be bounded UTF-8.", "INVALID_ARGUMENT")
                    mode = spec.get("mode", "managed_section")
                    if relative == ".codex/config.toml":
                        fail("Use the Codex adapter for its configuration field.")
                    if mode == "managed_section":
                        new = managed_section(old, spec.get("section_id", "navigation"), text)
                    elif mode == "exact" and "expected_sha256" in spec and spec["expected_sha256"] == _hash(old):
                        new = text.encode()
                    else:
                        fail("Exact writes need the current expected hash, including null for an absent file.")
                    row["writes"].append(self._write_record(relative, old, new))
                if not row["writes"]:
                    fail("A publication must name at least one private entry.", "INVALID_ARGUMENT")
                rows.append(row)
            plan = {"schema": "taskcarry.workbench.plan.v1", "view_id": view_id, "source": self.source(), "targets": rows}
            if len(canonical(plan)) > MAX_PLAN_BYTES:
                fail("Split this workbench plan into smaller batches.", "INVALID_ARGUMENT")
            plan_id = digest_bytes(canonical(plan))
            with self.store.transaction():
                self._object("workbench_plans", plan_id, plan)
            immutable(self._path("plans", plan_id + ".json"), canonical(plan))
        return {"plan_id": plan_id, "view_id": view_id, "plan_path": str(self._path("plans", plan_id + ".json")),
                "targets": [{**{k: row[k] for k in ("workspace", "task_id", "thread_id", "host", "code_assessment", "git")},
                             "writes": [{k: value for k, value in write.items() if k != "content"} for write in row["writes"]]} for row in rows],
                "effects_executed": False, "next_step": "Review the exact private plan, then execute its plan_id."}

    @staticmethod
    def _write_record(path, old, new):
        if len(new) > MAX_BYTES:
            fail("Resulting entry exceeds the bounded text limit.", "INVALID_ARGUMENT")
        return {"path": path, "before": _hash(old), "after": _hash(new), "content": base64.b64encode(new).decode()}

    def _load_plan(self, plan_id):
        self._sha(plan_id, "Plan ID")
        plan = self.store.get("workbench_plans", plan_id)
        if not plan or plan.get("schema") != "taskcarry.workbench.plan.v1" or digest_bytes(canonical(plan)) != plan_id:
            fail("Plan is missing, changed or has an unsupported schema.")
        if not self._same_local_source(plan.get("source")):
            fail("This plan belongs to another control or replica; make a new local plan.")
        return plan

    def _execute_target(self, plan_id, plan, row):
        workspace = row["workspace"]
        root = self._binding(workspace, row["task_id"])
        receipt_id = plan_id + "." + workspace
        existing = self.store.get("workbench_receipts", receipt_id)
        pointer = {"schema": "taskcarry.workbench.current.v1", "workspace": workspace, "task_id": row["task_id"],
                   "source_id": row["source_id"], "view_id": plan["view_id"], "plan_id": plan_id, "receipt_id": receipt_id}
        current = self._pointer(workspace)
        if current not in (row["previous"], pointer):
            return {"workspace": workspace, "status": "SUPERSEDED", "current_plan_id": current["plan_id"] if current else None}
        if git_snapshot(root) != row["git"]:
            fail("Git identity, HEAD or index changed after planning; preserve work and make a fresh plan.")
        for write in row["writes"]:
            actual = _hash(_read(private_target(root, write["path"])))
            if actual != write["after"] and (existing is not None or actual != write["before"]):
                fail("A planned file was modified; preserve it and make a fresh plan: " + write["path"])
        for write in row["writes"]:
            path = private_target(root, write["path"])
            actual = _hash(_read(path))
            if actual == write["after"]:
                continue
            if actual != write["before"]:
                fail("Target changed during publication: " + write["path"])
            atomic_write(path, base64.b64decode(write["content"], validate=True))
        if git_snapshot(root) != row["git"]:
            fail("Git state changed concurrently; effects are retained for inspection, not declared complete.")
        if any(_hash(_read(private_target(root, w["path"]))) != w["after"] for w in row["writes"]):
            fail("Published entry verification failed; inspect actual effects before retrying.")
        if existing is None:
            existing = {"schema": "taskcarry.workbench.receipt.v1", "receipt_id": receipt_id,
                        **{key: pointer[key] for key in ("workspace", "task_id", "source_id", "view_id", "plan_id")},
                        "thread_id": row["thread_id"], "published_at": now(), "status": "PUBLISHED",
                        "git_before": row["git"], "git_after": row["git"], "code_assessment": row["code_assessment"],
                        "writes": [{"path": w["path"], "sha256": w["after"]} for w in row["writes"]],
                        "consumer_state": "NOT_VERIFIED", "meaning": "Publication is not host consumption, code adoption or business acceptance."}
            with self.store.transaction():
                self._object("workbench_receipts", receipt_id, existing)
        immutable(self._path("receipts", receipt_id + ".json"), canonical(existing))
        if current != pointer:
            atomic_write(self._path("current", workspace + ".json"), canonical(pointer))
        with self.store.transaction():
            if self.store.get("workbench_current", workspace) != pointer:
                self.store.put("workbench_current", workspace, pointer)
                self.store.event("workbench_published", pointer)
        return {"workspace": workspace, "status": "PUBLISHED", "receipt_id": receipt_id,
                "view_id": plan["view_id"], "consumer_state": "NOT_VERIFIED"}

    def _execute(self, plan_id):
        results = []
        with self.store.guard():
            plan = self._load_plan(plan_id)
            self._view(plan["view_id"])
            immutable(self._path("plans", plan_id + ".json"), canonical(plan))
            for row in plan["targets"]:
                try:
                    results.append(self._execute_target(plan_id, plan, row))
                except (GovernanceError, OSError, ValueError) as exc:
                    results.append({"workspace": row["workspace"], "status": "CONFLICT" if isinstance(exc, GovernanceError) else "IO_ERROR",
                                    "code": getattr(exc, "code", type(exc).__name__), "error": str(exc)[:1000],
                                    "next_step": "Inspect actual effects; resume this exact plan for missing steps, or re-plan changed files."})
        return {"plan_id": plan_id, "status": "COMPLETED" if all(r["status"] == "PUBLISHED" for r in results) else "PARTIAL",
                "results": results, "source_freshness": self._freshness(self._view(plan["view_id"])), "business_accepted": False}

    def _consume(self, proof):
        keys = {"workspace", "plan_id", "view_id", "task_id", "source_id", "thread_id", "turn_id", "evidence_path", "evidence_sha256", "reviewer", "observed_at"}
        if not isinstance(proof, dict) or set(proof) != keys or any(not isinstance(v, str) or not v.strip() or len(v) > 1000 for v in proof.values()):
            fail("Consumption requires exact bounded identity and reviewed evidence fields.", "INVALID_ARGUMENT")
        plan_id, workspace = self._sha(proof["plan_id"], "Plan ID"), _id(proof["workspace"], "Workspace")
        with self.store.guard():
            plan = self._load_plan(plan_id)
            row = next((r for r in plan["targets"] if r["workspace"] == workspace), None)
            receipt_id = plan_id + "." + workspace
            receipt = self.store.get("workbench_receipts", receipt_id)
            if not row or not receipt or any(proof[key] != receipt[key] for key in ("view_id", "task_id", "source_id", "thread_id")):
                fail("Consumption evidence must match an actual publication and its original task/thread.")
            evidence = validate_relative_path(self.root, proof["evidence_path"], allow_missing=False)
            if _hash(_read(evidence)) != self._sha(proof["evidence_sha256"], "Evidence hash"):
                fail("Reviewed consumption evidence is missing or changed.")
            record = {"schema": "taskcarry.workbench.consumption.v1", **proof, "receipt_id": receipt_id,
                      "meaning": "Caller-reviewed evidence reference; not an independent assertion of understanding, native loading or business acceptance."}
            consumption_id = digest_bytes(canonical(record))
            with self.store.transaction():
                self._object("workbench_consumption", consumption_id, record)
                self.store.put("workbench_consumed", receipt_id, {"consumption_id": consumption_id})
            immutable(self._path("consumption", consumption_id + ".json"), canonical(record))
        return {"consumption_id": consumption_id, "receipt_id": receipt_id, "consumer_state": "REVIEWED_EVIDENCE_RECORDED",
                "current_view": bool((self._pointer(workspace) or {}).get("plan_id") == plan_id), "native_acceptance_verified": False}

    def _status(self, workspace, limit, cursor):
        if type(limit) is not int or not 1 <= limit <= 100:
            fail("Status limit must be 1-100.", "INVALID_ARGUMENT")
        if workspace is not None:
            _id(workspace, "Workspace")
        if cursor is not None:
            _id(cursor, "Cursor")
        with self.store._connect(readonly=True) as db:
            if workspace:
                rows = db.execute("SELECT key FROM records WHERE collection='workspaces' AND key=?", (workspace,)).fetchall()
            else:
                rows = db.execute("SELECT key FROM records WHERE collection='workspaces' AND key>? ORDER BY key LIMIT ?", (cursor or "", limit + 1)).fetchall()
        result = []
        for (name,) in rows[:limit]:
            try:
                pointer = self._pointer(name)
                if pointer is None:
                    result.append({"workspace": name, "state": "NOT_PUBLISHED"})
                    continue
                view = self._view(pointer["view_id"])
                selected = self.store.get("workbench_consumed", pointer["receipt_id"], {})
                consumption = self.store.get("workbench_consumption", selected.get("consumption_id", ""))
                consumer_state = "NOT_VERIFIED"
                if consumption:
                    evidence = validate_relative_path(self.root, consumption["evidence_path"])
                    consumer_state = "REVIEWED_EVIDENCE_RECORDED" if _hash(_read(evidence)) == consumption["evidence_sha256"] else "EVIDENCE_CHANGED_OR_MISSING"
                plan = self._load_plan(pointer["plan_id"])
                target = next(r for r in plan["targets"] if r["workspace"] == name)
                root = self._binding(name, pointer["task_id"])
                if str(root) != target["root"]:
                    fail("The registered workspace moved; regenerate its local entry in the new location.")
                entry_matches = all(_hash(_read(private_target(root, w["path"]))) == w["after"] for w in target["writes"])
                result.append({**pointer, "state": "PUBLISHED" if entry_matches else "ENTRY_CHANGED",
                               "thread_id": target["thread_id"],
                               "finalization_pending": self.store.get("workbench_current", name) != pointer,
                               "source_freshness": self._freshness(view), "consumer_state": consumer_state,
                               "consumption_id": selected.get("consumption_id"),
                               "view_path": str(self._path("views", pointer["view_id"], "view.md")),
                               "current_path": str(self._path("current", name + ".json")), "native_acceptance_verified": False})
            except (GovernanceError, OSError, ValueError, StopIteration) as exc:
                result.append({"workspace": name, "state": "UNVERIFIED", "error": str(exc)[:1000]})
        return {"source": self.source(), "items": result, "next_cursor": rows[limit - 1][0] if len(rows) > limit else None,
                "read_only": True, "meaning": "Current publication and reviewed evidence are separate; query Core for the latest task/checkpoint."}

    def workbench(self, action="status", body=None, sources=None, view_id=None, targets=None, plan_id=None,
                  workspace=None, proof=None, limit=20, cursor=None):
        if action == "freeze":
            return self._freeze(body, sources)
        if action == "plan":
            return self._plan(view_id, targets)
        if action == "execute":
            return self._execute(plan_id)
        if action == "consume":
            return self._consume(proof)
        if action == "status":
            return self._status(workspace, limit, cursor)
        fail("Unknown workbench action.", "INVALID_ARGUMENT")
