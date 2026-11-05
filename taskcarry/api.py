"""The single dispatch surface shared by CLI and MCP."""
from .core import Core
from .integration import Integration
from .store import GovernanceError
from .contracts import action_schema, validate


def invoke(project, action, arguments=None):
    args = {} if arguments is None else arguments
    if not isinstance(args, dict):
        raise GovernanceError("INVALID_ARGUMENT", "Arguments must be a JSON object")
    try:
        validate(args, action_schema(action, allow_fault=True))
    except (ValueError, KeyError) as exc:
        raise GovernanceError("INVALID_ARGUMENT", str(exc)) from exc
    if action == "init":
        return Core.initialize(project, **args)
    if action == "identify":
        return Core.identify(project)
    if action == "codex":
        from .codex_host import codex_read
        return codex_read(**args)
    if action in {"update_source", "update_check", "update_assess"}:
        from .updates import Updates
        return getattr(Updates(project), action)(**args)
    if action in {"onboarding", "schedule_plan"}:
        from .onboarding import Onboarding
        return getattr(Onboarding(project), action)(**args)
    if action == "preserve":
        from .preservation import Preservation
        return Preservation(project).preserve(**args)
    core_actions = {"status", "agenda", "context", "task", "checkpoint", "restore", "artifact", "experience", "upgrade"}
    git_actions = {"workspace", "submit", "reconcile", "adopt", "doctor"}
    continuity_actions = {"observe", "run"}
    maintenance_actions = {"issue", "fix"}
    if action == "governance":
        from .governance import Governance
        return Governance(project).governance(**args)
    if action == "connect":
        from .connection import Connection
        return Connection(project).connect(**args)
    if action not in core_actions | git_actions | continuity_actions | maintenance_actions:
        raise GovernanceError("UNKNOWN_ACTION", f"Unknown action: {action}")
    if action in continuity_actions:
        from .continuity import Continuity
        obj = Continuity(project)
    elif action in maintenance_actions:
        from .maintenance import Maintenance
        obj = Maintenance(project)
    else:
        obj = Core(project) if action in core_actions else Integration(project)
    if action == "checkpoint" and isinstance(args.get("workspace"), str):
        registered = obj.store.get("workspaces", args["workspace"])
        if registered:
            args = {**args, "workspace": str(Integration(project)._ws(args["workspace"]))}
    try:
        return getattr(obj, action)(**args)
    except TypeError as exc:
        raise GovernanceError("INVALID_ARGUMENT", str(exc)) from exc
