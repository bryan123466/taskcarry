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


def skill_files():
    """Copy the four public skills and their explicitly scoped Markdown references."""
    files = {}
    for source in skill_sources():
        base = source.parent
        if is_link(base):
            raise SetupError("SETUP_LINK", "Skill directories cannot be links")
        paths = [source]
        references = base / "references"
        if is_link(references):
            raise SetupError("SETUP_LINK", "Skill references cannot be links")
        if references.exists():
            if not references.is_dir():
                raise SetupError("SKILLS_NOT_PACKAGED", "Skill references must be a directory")
            for path in sorted(references.rglob("*")):
                if is_link(path):
                    raise SetupError("SETUP_LINK", "Skill references cannot contain links")
                if path.is_file() and path.suffix == ".md":
                    paths.append(path)
        for path in paths:
            relative = path.relative_to(base).as_posix()
            safe_target(base, relative)
            files[f".agents/skills/{base.name}/{relative}"] = path.read_bytes()
    return files


def planned_files(root, server_name="taskcarry", binding=None):
    server_name = validate_server_name(server_name)
    files = skill_files()
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
    if binding:
        files[".taskcarry/workbench.json"] = encoded(dict(binding, format=1, server_name=server_name,
            skills_directory=".agents/skills", mcp_fragment=".taskcarry/codex.mcp.toml",
            host_loading_verified=False, native_acceptance_verified=False))
        instructions = (
            "# TaskCarry workbench binding\n\n"
            "These are generated connection materials, not a second governance database.\n"
            "Keep these machine-specific paths and identities private.\n\n"
            f"- Control: {quote(binding['control'])}\n"
            f"- Workbench directory: {quote(binding['target'])}\n"
            f"- Workspace: {quote(binding['workspace'])}\n"
            f"- Task: {quote(binding['task_id'])}\n"
            f"- MCP server: {quote(server_name)}\n\n"
            "The four Skills and their public Markdown references are in `.agents/skills`.\n"
            "Read `taskcarry-project-setup/SKILL.md` there to continue onboarding.\n\n"
            "1. Review `.taskcarry/codex.mcp.toml` and explicitly merge its server section into the host configuration, preserving existing settings.\n"
            "2. Reload the host as needed. Generated files do not prove that the host loaded this server or these Skills.\n"
            "3. In this workbench, call the native `taskcarry_doctor` and `taskcarry_status` tools on the named server. Check the control, registered workspace/task, checkpoint, interpreter and module path.\n"
            "4. Record the actual native result and any remaining step in the existing governance records. A CLI or standalone stdio check is separate evidence.\n\n"
            "Do not initialize another control, change task state, receive a delivery, upgrade the runtime, or activate a schedule merely to finish setup.\n"
        )
        files[".taskcarry/workbench.md"] = instructions.encode("utf-8")
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
        parts = Path(name).parts
        skill_path = (len(parts) >= 4 and parts[:2] == (".agents", "skills")
                      and parts[2].startswith("taskcarry-")
                      and (parts[3:] == ("SKILL.md",)
                           or (len(parts) >= 5 and parts[3] == "references" and parts[-1].endswith(".md"))))
        if not (name in {".taskcarry/codex.mcp.toml", ".taskcarry/workbench.json", ".taskcarry/workbench.md"} or skill_path):
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
    if "binding" in result:
        binding = result["binding"]
        if (not isinstance(binding, dict) or set(binding) != {"control", "target", "workspace", "task_id"}
                or binding.get("target") != str(root)
                or not isinstance(binding.get("control"), str) or not Path(binding["control"]).is_absolute()
                or not valid_identity(binding.get("workspace")) or not valid_identity(binding.get("task_id"))):
            raise SetupError("SETUP_MANIFEST_INVALID", "Invalid workbench binding")
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


def valid_identity(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value) is not None


def workbench_binding(control, target, workspace, task_id, verify=True):
    if not valid_identity(workspace) or not valid_identity(task_id):
        raise SetupError("SETUP_BINDING_REQUIRED", "Workbench setup requires target, workspace and task_id together, with valid registered identities")
    if target != control and safe_target(target, ".taskcarry/state.sqlite3").exists():
        raise SetupError("SETUP_CONTROL_CONFLICT", "The target already contains a governance database; preserve its separate control")
    binding = {"control": str(control), "target": str(target), "workspace": workspace, "task_id": task_id}
    if verify:
        from .integration import Integration
        from .store import GovernanceError
        try:
            integration = Integration(control)
            if integration.store.get("tasks", task_id) is None:
                raise SetupError("SETUP_TASK_UNKNOWN", "Register the existing task in this control before workbench setup", {"task_id": task_id})
            registered = integration._ws(workspace)
            if registered != target:
                raise SetupError("SETUP_WORKSPACE_MISMATCH", "The registered workspace does not match the target directory",
                                 {"workspace": workspace, "registered": str(registered), "target": str(target)})
        except GovernanceError as exc:
            raise SetupError(exc.code, exc.message, exc.details) from exc
    return binding


def check_binding(manifest, intent, binding):
    recorded = (intent["manifest_after"] if intent else manifest).get("binding")
    if recorded is not None and recorded != binding:
        raise SetupError("SETUP_BINDING_CONFLICT", "This setup belongs to another workbench identity; use its recorded control, target, workspace and task_id",
                         {"recorded": recorded, "requested": binding})


def connection_result(result, control, root, binding):
    installed = result["mode"] == "install"
    removed = result["mode"] == "uninstall"
    return dict(result, control=str(control), target=str(root), workspace=binding["workspace"] if binding else None,
                task_id=binding["task_id"] if binding else None,
                registration_verified=bool(binding) and not removed,
                connection_state={"materials": "removed_or_preserved_modified" if removed else ("generated" if installed else "preview"),
                                  "host_loading": "not_verified", "native_acceptance": "not_verified"},
                host_loading_verified=False, native_acceptance_verified=False,
                next_steps=(["Manually activated host configuration remains user managed."] if removed else [
                    "Review the planned file list, resolve conflicts, then run setup with mode=install and the same binding." if not installed else
                    "Review the generated MCP fragment and explicitly merge it into the host configuration, preserving existing settings.",
                    "Load the project-scoped Skills in the target workbench; reload the host if required.",
                    "Call native taskcarry_doctor and taskcarry_status on this server in the target workbench; verify control, workspace, task, checkpoint and runtime.",
                    "Record actual native results and the next unfinished step in the existing control; generated materials do not attest host acceptance."]))


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


def configure(project, mode="preview", server_name=None, target=None, workspace=None, task_id=None):
    if mode not in {"preview", "install", "uninstall"}:
        raise SetupError("SETUP_MODE", "mode must be preview, install or uninstall")
    control = project_root(project)
    if target is None and (workspace is not None or task_id is not None):
        raise SetupError("SETUP_BINDING_REQUIRED", "Workbench setup requires target, workspace and task_id together")
    root = project_root(target) if target is not None else control
    binding = workbench_binding(control, root, workspace, task_id, verify=mode != "uninstall") if target is not None else None
    # Metadata is local to the workbench, while every generated MCP command
    # points to the existing control. No setup mode initializes governance.
    make_files = lambda selected: planned_files(control, selected, binding) if binding else planned_files(control, selected)
    finish = lambda result: connection_result(result, control, root, binding)
    if server_name is not None:
        validate_server_name(server_name)
    if mode == "preview":
        manifest, intent = read_manifest(root), read_intent(root)
        check_binding(manifest, intent, binding)
        selected = server_name or (intent or manifest).get("server_name", "taskcarry")
        files, runtime = make_files(selected), loaded_runtime()
        if intent:
            pending_matches(root, intent, files, runtime, selected)
        return finish(dict(preview(root, files, manifest, intent), server_name=selected, runtime=runtime))
    with setup_lock(root):
        manifest = read_manifest(root)
        manifest_path = safe_target(root, ".taskcarry/setup-manifest.json")
        intent_path = safe_target(root, ".taskcarry/setup-intent.json")
        intent = read_intent(root)
        check_binding(manifest, intent, binding)
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
            return finish({"mode": mode, "removed": removed, "preserved_modified": preserved,
                    "global_config_changed": False, "agents_md_changed": False,
                    "note": "Any configuration section manually activated in Codex remains user managed. Governance state and user files are retained."})
        selected = server_name or (intent or manifest).get("server_name", "taskcarry")
        files, runtime = make_files(selected), loaded_runtime()
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
            if binding:
                manifest_after["binding"] = binding
            if all(row["action"] == "unchanged" for row in result["files"]) and manifest == manifest_after:
                return finish(dict(result, mode="install", server_name=selected, runtime=runtime,
                            resumed=False, files_written=0, manifest_written=False))
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
        if binding:
            workbench_binding(control, root, workspace, task_id)
        pending_matches(root, intent, make_files(selected), loaded_runtime(), selected)
        if any(file_hash(safe_target(root, name)) != proof["after"] for name, proof in intent["files"].items()):
            raise SetupError("SETUP_CONFLICT", "Managed file changed before installation could be recorded")
        target_manifest = encoded(intent["manifest_after"])
        manifest_written = file_hash(manifest_path) != digest(target_manifest)
        if manifest_written:
            atomic_write(manifest_path, target_manifest)
        if file_hash(intent_path) != digest(encoded(intent)):
            raise SetupError("SETUP_INTENT_CHANGED", "Setup intent changed before completion")
        intent_path.unlink()
        return finish(dict(result, mode="install", server_name=selected, runtime=runtime, resumed=resumed,
                    pending_installation=False, files_written=writes, manifest_written=manifest_written))


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
        binding = (intent["manifest_after"] if intent else manifest).get("binding")
        control = Path(binding["control"]) if binding else root
        result.update(control=str(control), target=str(root), binding=binding)
        files = planned_files(control, result["server_name"], binding) if binding else planned_files(root, result["server_name"])
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
