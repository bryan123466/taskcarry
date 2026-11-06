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
    if action == "recovery":
        from .project_recovery import ProjectRecovery
        return ProjectRecovery(project).recovery(**args)
    # Restored replicas must not execute old plans or mutate until an explicit
    # writer handoff. This preflight precedes external Git/filesystem effects;
    # Store also guards direct record writes and transactions.
    state = Core(project)
    config = state.store.get('config', 'project') or {}
    read_modes = {
        'identity': {'status'}, 'onboarding': {'status'}, 'preserve': {'status'},
        'connect': {'status'}, 'governance': {'inspect'}, 'run': {'inspect'},
        'workbench': {'status'}, 'cycle': {'status', 'list', 'question_check'}, 'source_scan': {'status', 'registry'},
        'facts': {'get', 'history', 'list'},
        'transfer': {'verify', 'status'},
    }
    mode = args.get('action', args.get('mode', {
        'identity': 'status', 'onboarding': 'status', 'governance': 'inspect',
        'workbench': 'status', 'cycle': 'status', 'source_scan': 'status', 'facts': 'list',
    }.get(action)))
    readonly = (action in {'status', 'agenda', 'context', 'doctor', 'schedule_plan', 'update_check'}
                or mode in read_modes.get(action, set()))
    if not readonly:
        state.store.assert_writable()
        if args.get('plan_id') in config.get('recovery_inert_plan_ids', []):
            raise GovernanceError('RESTORED_PLAN_INERT',
                                  'Historical plans are evidence only after recovery; prepare a new local plan.')
        if (args.get('cycle_id') in config.get('recovery_inert_cycle_ids', [])
                or args.get('run_id') in config.get('recovery_inert_run_ids', [])):
            raise GovernanceError('RESTORED_RUN_INERT',
                                  'Retain the historical run and start a new bounded cycle on this replica.')
    if action == "identity":
        from .project_identity import ProjectIdentity
        return ProjectIdentity(project).identity(**args)
    if action in {"cycle", "facts", "source_scan"}:
        from .governance_cycle import GovernanceCycle
        return getattr(GovernanceCycle(project), action)(**args)
    if action == "workbench":
        from .workbench import Workbench
        return Workbench(project).workbench(**args)
    if action == "transfer":
        from .remote_transfer import RemoteTransfer
        return RemoteTransfer(project).transfer(**args)
    if action in {"update_source", "update_check", "update_assess"}:
        from .updates import Updates
        return getattr(Updates(project), action)(**args)
    if action in {"onboarding", "schedule_plan"}:
        from .onboarding_complete import CompleteOnboarding
        return getattr(CompleteOnboarding(project), action)(**args)
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
