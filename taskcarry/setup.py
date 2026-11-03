"""Additive project-scoped Codex setup. Never edits global or live Codex config."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import uuid


class SetupError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_target(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise SetupError("SETUP_PATH_ESCAPE", "Managed path is outside the project")
    current = path
    while current != root:
        if is_link(current):
            raise SetupError("SETUP_LINK", "Setup refuses links in managed paths", {"path": relative})
        current = current.parent
    if not path.resolve().is_relative_to(root):
        raise SetupError("SETUP_PATH_ESCAPE", "Managed path escapes the project")
    return path


def is_link(path):
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False


def skill_sources():
    package = Path(__file__).resolve().parent
    for candidate in (package / "skill_data", package.parent / "skills"):
        if candidate.is_dir():
            sources = sorted(candidate.glob("*/SKILL.md"))
            if len(sources) == 4:
                return sources
    raise SetupError("SKILLS_NOT_PACKAGED", "Four public skills were not found in the installed package")


def validate_server_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value):
        raise SetupError("SETUP_SERVER_NAME", "server_name must start with a letter and contain at most 64 letters, digits, underscores or hyphens")
    return value


def mcp_launch_args(root):
    """Pin the selected installation (or explicit source checkout), not cwd.

    Isolated mode ignores PYTHONPATH and user site packages. The explicit path
    also supports unpacked/source development without an editable installation.
    If that package disappears, fail rather than fall back to another copy.
    """
    package_parent = Path(__file__).resolve().parent.parent
    bootstrap = (
        "import importlib.util, pathlib, runpy, sys\n"
        "root = pathlib.Path(sys.argv.pop(1)).resolve()\n"
        "sys.path.insert(0, str(root))\n"
        "spec = importlib.util.find_spec('taskcarry')\n"
        "if spec is None or spec.origin is None or pathlib.Path(spec.origin).resolve() != root / 'taskcarry' / '__init__.py':\n"
        "    raise SystemExit('Selected TaskCarry package is unavailable; regenerate setup with the intended runtime')\n"
        "runpy.run_module('taskcarry', run_name='__main__', alter_sys=True)\n"
    )
    return ["-I", "-X", "utf8", "-c", bootstrap, str(package_parent),
            "--project", str(root), "mcp"]


def planned_files(root, server_name="taskcarry"):
    server_name = validate_server_name(server_name)
    files = {}
    for source in skill_sources():
        files[f".agents/skills/{source.parent.name}/SKILL.md"] = source.read_bytes()
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    args = mcp_launch_args(root)
    fragment = (
        "# Generated project-specific MCP fragment. This is NOT loaded automatically.\n"
        "# Review and add this section to the appropriate Codex configuration.\n"
        "# Do not copy this fragment to another machine: regenerate it there.\n"
        "# Isolated UTF-8 startup pins the package selected during setup.\n"
        f"[mcp_servers.{server_name}]\n"
        f"command = {quote(sys.executable)}\n"
        f"args = {json.dumps(args, ensure_ascii=False)}\n"
    )
    files[".taskcarry/codex.mcp.toml"] = fragment.encode("utf-8")
    return files


def read_manifest(root):
    path = safe_target(root, ".taskcarry/setup-manifest.json")
    if not path.exists():
        return {"format": 1, "files": {}}
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise SetupError("SETUP_MANIFEST_INVALID", "Setup manifest cannot be read") from exc
    return validate_manifest(result, root)


def validate_manifest(result, root):
    if not isinstance(result, dict) or result.get("format") != 1 or not isinstance(result.get("files"), dict):
        raise SetupError("SETUP_MANIFEST_INVALID", "Setup manifest has an unsupported format")
    for name, value in result["files"].items():
        if not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise SetupError("SETUP_MANIFEST_INVALID", "Invalid managed file record")
        if not (name == ".taskcarry/codex.mcp.toml" or (name.startswith(".agents/skills/taskcarry-") and name.endswith("/SKILL.md") and len(Path(name).parts) == 4)):
            raise SetupError("SETUP_MANIFEST_INVALID", "Manifest includes a path outside the managed setup scope")
        safe_target(root, name)
    if "server_name" in result:
        validate_server_name(result["server_name"])
    if "project" in result and result["project"] != str(root):
        raise SetupError("SETUP_MANIFEST_INVALID", "Setup manifest belongs to a different project")
    if "installation_id" in result and not re.fullmatch(r"[0-9a-f]{32}", str(result["installation_id"])):
        raise SetupError("SETUP_MANIFEST_INVALID", "Invalid setup installation identity")
    if "runtime" in result and not valid_runtime(result["runtime"]):
        raise SetupError("SETUP_MANIFEST_INVALID", "Invalid managed runtime record")
    return result


@contextmanager
def setup_lock(root):
    directory = safe_target(root, ".taskcarry")
    directory.mkdir(parents=True, exist_ok=True)
    path = safe_target(root, ".taskcarry/setup.lock")
    stream = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise SetupError("SETUP_BUSY", "Another setup process holds the project setup lock") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise SetupError("SETUP_BUSY", "Another setup process holds the project setup lock") from exc
        yield
    finally:
        stream.close()


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".taskcarry-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8")


def file_hash(path):
    if not path.exists():
        return None
    if not path.is_file():
        raise SetupError("SETUP_CONFLICT", "A managed target is not a regular file", {"path": str(path)})
    return digest(path.read_bytes())


def loaded_runtime():
    # Import metadata identifies this process's package location and version
    # label. The hash reads source files on disk, not already loaded bytecode;
    # a long-lived process must restart after a package change.
    from . import __version__
    package = Path(__file__).resolve().parent
    source = {p.name: digest(p.read_bytes()) for p in sorted(package.glob("*.py"))}
    return {"version": __version__, "module_root": str(package),
            "interpreter": sys.executable, "source_sha256": digest(encoded(source)),
            "source_fingerprint_scope": "on_disk", "loaded_code_verified": False,
            "requires_restart_after_package_change": True}


def valid_runtime(value):
    return (isinstance(value, dict)
            and all(isinstance(value.get(key), str) and value[key] for key in ("version", "module_root", "interpreter"))
            and re.fullmatch(r"[0-9a-f]{64}", str(value.get("source_sha256"))) is not None)


def read_intent(root):
    path = safe_target(root, ".taskcarry/setup-intent.json")
    if not path.exists():
        return None
    try:
        intent = json.loads(path.read_text(encoding="utf-8"))
        body = {key: value for key, value in intent.items() if key != "intent_id"}
        if (intent.get("format") != 1 or intent.get("action") != "install"
                or intent.get("project") != str(root)
                or intent.get("intent_id") != digest(encoded(body))
                or not re.fullmatch(r"[0-9a-f]{32}", str(intent.get("installation_id")))
                or not valid_runtime(intent.get("runtime"))
                or not isinstance(intent.get("files"), dict)
                or "manifest_before_sha256" not in intent
                or (intent["manifest_before_sha256"] is not None
                    and not re.fullmatch(r"[0-9a-f]{64}", str(intent["manifest_before_sha256"])))
                or not isinstance(intent.get("manifest_after"), dict)):
            raise ValueError("Invalid setup intent")
        validate_manifest(intent["manifest_after"], root)
        validate_server_name(intent["server_name"])
        for name, row in intent["files"].items():
            safe_target(root, name)
            if (not isinstance(row, dict)
                    or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("after")))
                    or (row.get("before") is not None and not re.fullmatch(r"[0-9a-f]{64}", str(row["before"])))):
                raise ValueError("Invalid setup file proof")
        return intent
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        if isinstance(exc, SetupError):
            raise
        raise SetupError("SETUP_INTENT_INVALID", "Pending setup intent cannot be verified") from exc


def project_root(project):
    supplied = Path(project).expanduser().absolute()
    if any(is_link(p) for p in (supplied, *supplied.parents)):
        raise SetupError("SETUP_LINK", "Setup requires a concrete project directory")
    root = supplied.resolve()
    if not root.is_dir():
        raise SetupError("PROJECT_NOT_FOUND", "Setup requires an existing project directory")
    return root


def pending_matches(root, intent, files, runtime, server_name):
    # A changed source tree requires completing the pending operation with its
    # original package, rather than silently rebasing a partly applied install.
    if (intent["runtime"] != runtime or intent["server_name"] != server_name
            or set(intent["files"]) != set(files)
            or any(intent["files"][name]["after"] != digest(content) for name, content in files.items())):
        raise SetupError("SETUP_PENDING_SOURCE_CHANGED", "Resume pending setup with its original package and server name; project files were preserved")
    after = intent["manifest_after"]
    if (after.get("format") != 1 or after.get("project") != str(root)
            or after.get("installation_id") != intent["installation_id"]
            or after.get("server_name") != server_name or after.get("runtime") != runtime
            or not isinstance(after.get("files"), dict)
            or any(after["files"].get(name) != row["after"] for name, row in intent["files"].items())):
        raise SetupError("SETUP_INTENT_INVALID", "Pending setup has an inconsistent target manifest")
    actual = file_hash(safe_target(root, ".taskcarry/setup-manifest.json"))
    if actual not in {intent["manifest_before_sha256"], digest(encoded(after))}:
        raise SetupError("SETUP_MANIFEST_CHANGED", "Setup manifest changed since the pending installation")


def preview(root, files, manifest, intent=None):
    changes, conflicts = [], []
    for name, content in files.items():
        path = safe_target(root, name)
        current = digest(path.read_bytes()) if path.is_file() else None
        if path.exists() and not path.is_file():
            conflicts.append({"path": name, "reason": "not_a_regular_file"})
        elif intent and current not in {intent["files"][name]["before"], intent["files"][name]["after"]}:
            conflicts.append({"path": name, "reason": "changed_since_install_intent"})
        elif not intent and path.exists() and current != manifest["files"].get(name):
            conflicts.append({"path": name, "reason": "unmanaged_or_modified"})
        else:
            changes.append({"path": name, "action": "unchanged" if current == digest(content) else ("update" if path.exists() else "create"), "sha256": digest(content)})
    return {"mode": "preview", "project": str(root), "files": changes, "conflicts": conflicts,
            "activation": "The TOML fragment is not active configuration. Review it and explicitly configure Codex; generated skills are project scoped.",
            "pending_installation": intent is not None,
            "global_config_changed": False, "agents_md_changed": False}


def configure(project, mode="preview", server_name=None):
    if mode not in {"preview", "install", "uninstall"}:
        raise SetupError("SETUP_MODE", "mode must be preview, install or uninstall")
    root = project_root(project)
    if server_name is not None:
        validate_server_name(server_name)
    if mode == "preview":
        manifest, intent = read_manifest(root), read_intent(root)
        selected = server_name or (intent or manifest).get("server_name", "taskcarry")
        files, runtime = planned_files(root, selected), loaded_runtime()
        if intent:
            pending_matches(root, intent, files, runtime, selected)
        return dict(preview(root, files, manifest, intent), server_name=selected, runtime=runtime)
    with setup_lock(root):
        manifest = read_manifest(root)
        manifest_path = safe_target(root, ".taskcarry/setup-manifest.json")
        intent_path = safe_target(root, ".taskcarry/setup-intent.json")
        intent = read_intent(root)
        if mode == "uninstall":
            if intent:
                raise SetupError("SETUP_PENDING", "Complete the pending installation before uninstalling its managed files")
            removed, preserved, remaining = [], [], {}
            for name, original in manifest["files"].items():
                path = safe_target(root, name)
                if not path.exists():
                    continue
                if path.is_file() and digest(path.read_bytes()) == original:
                    path.unlink()
                    removed.append(name)
                else:
                    preserved.append(name)
                    remaining[name] = original
            if remaining:
                updated = dict(manifest, files=remaining)
                if file_hash(manifest_path) != digest(encoded(updated)):
                    atomic_write(manifest_path, encoded(updated))
            elif manifest_path.exists():
                manifest_path.unlink()
            return {"mode": mode, "removed": removed, "preserved_modified": preserved,
                    "global_config_changed": False, "agents_md_changed": False,
                    "note": "Any configuration section manually activated in Codex remains user managed. Governance state and user files are retained."}
        selected = server_name or (intent or manifest).get("server_name", "taskcarry")
        files, runtime = planned_files(root, selected), loaded_runtime()
        if intent:
            pending_matches(root, intent, files, runtime, selected)
        result = preview(root, files, manifest, intent)
        if result["conflicts"]:
            raise SetupError("SETUP_CONFLICT", "Existing unmanaged or changed files are preserved", result)
        resumed = intent is not None
        if intent is None:
            manifest_after = dict(manifest, format=1, project=str(root), server_name=selected,
                                  runtime=runtime, installation_id=manifest.get("installation_id") or uuid.uuid4().hex,
                                  files={**manifest["files"], **{name: digest(content) for name, content in files.items()}})
            if all(row["action"] == "unchanged" for row in result["files"]) and manifest == manifest_after:
                return dict(result, mode="install", server_name=selected, runtime=runtime,
                            resumed=False, files_written=0, manifest_written=False)
            body = {"format": 1, "action": "install", "project": str(root),
                    "installation_id": manifest_after["installation_id"], "server_name": selected,
                    "runtime": runtime, "manifest_before_sha256": file_hash(manifest_path),
                    "manifest_after": manifest_after,
                    "files": {name: {"before": file_hash(safe_target(root, name)), "after": digest(content)}
                              for name, content in files.items()}}
            if read_manifest(root) != manifest:
                raise SetupError("SETUP_MANIFEST_CHANGED", "Setup manifest changed during preparation")
            for name, proof in body["files"].items():
                if proof["before"] is not None and proof["before"] != manifest["files"].get(name):
                    raise SetupError("SETUP_CONFLICT", "A target changed during installation preparation", {"path": name})
            intent = dict(body, intent_id=digest(encoded(body)))
            atomic_write(intent_path, encoded(intent))
        writes = 0
        for name, content in files.items():
            path = safe_target(root, name)
            current, proof = file_hash(path), intent["files"][name]
            if current == proof["after"]:
                continue
            if current != proof["before"]:
                raise SetupError("SETUP_CONFLICT", "Managed file changed after installation was planned", {"path": name})
            atomic_write(path, content)
            writes += 1
        pending_matches(root, intent, planned_files(root, selected), loaded_runtime(), selected)
        if any(file_hash(safe_target(root, name)) != proof["after"] for name, proof in intent["files"].items()):
            raise SetupError("SETUP_CONFLICT", "Managed file changed before installation could be recorded")
        target_manifest = encoded(intent["manifest_after"])
        manifest_written = file_hash(manifest_path) != digest(target_manifest)
        if manifest_written:
            atomic_write(manifest_path, target_manifest)
        if file_hash(intent_path) != digest(encoded(intent)):
            raise SetupError("SETUP_INTENT_CHANGED", "Setup intent changed before completion")
        intent_path.unlink()
        return dict(result, mode="install", server_name=selected, runtime=runtime, resumed=resumed,
                    pending_installation=False, files_written=writes, manifest_written=manifest_written)


def runtime_info(project):
    """Inspect import metadata, on-disk source and setup; never attest loaded code."""
    result = {"loaded_runtime": None, "setup_status": "not_installed",
              "managed_setup_version": None, "server_name": None, "pending_installation": False,
              "managed_files_match": None, "generated_files_match": None,
              "managed_runtime_matches_disk": None, "source_fingerprint_scope": "on_disk",
              "loaded_code_verified": False, "requires_restart_after_package_change": True,
              "host_loading_verified": False, "package_upgrade_performed": False}
    try:
        runtime = loaded_runtime()
        result["loaded_runtime"] = runtime
        root = project_root(project)
        manifest, intent = read_manifest(root), read_intent(root)
        result["pending_installation"] = intent is not None
        result["managed_setup_version"] = manifest.get("runtime", {}).get("version")
        result["server_name"] = (intent or manifest).get("server_name", "taskcarry")
        if intent:
            result["pending_runtime_version"] = intent.get("runtime", {}).get("version")
        files = planned_files(root, result["server_name"])
        details = []
        for name in sorted(set(files) | set(manifest["files"])):
            current = file_hash(safe_target(root, name))
            expected = digest(files[name]) if name in files else None
            details.append({"path": name, "current_sha256": current,
                            "managed_sha256": manifest["files"].get(name), "generated_sha256": expected,
                            "matches_managed": name in manifest["files"] and current == manifest["files"][name],
                            "matches_generated": expected is not None and current == expected})
        result["files"] = details
        result["managed_files_match"] = bool(manifest["files"]) and all(
            row["matches_managed"] for row in details if row["path"] in manifest["files"])
        result["generated_files_match"] = all(row["matches_generated"] for row in details if row["path"] in files)
        result["managed_runtime_matches_disk"] = manifest.get("runtime") == runtime if manifest.get("runtime") else None
        if intent:
            result["setup_status"] = "pending"
            result["pending_source_matches_disk"] = intent.get("runtime") == runtime and all(
                intent.get("files", {}).get(name, {}).get("after") == digest(content) for name, content in files.items())
        elif manifest["files"]:
            result["setup_status"] = "installed" if result["managed_files_match"] else "modified"
        return result
    except (SetupError, OSError, ValueError, TypeError, KeyError) as exc:
        error = {"code": getattr(exc, "code", "SETUP_DIAGNOSTIC_ERROR"),
                 "type": type(exc).__name__, "message": str(exc)}
        if isinstance(exc, OSError):
            error.update(errno=exc.errno, filename=exc.filename)
        return dict(result, setup_status="unavailable", error=error)
