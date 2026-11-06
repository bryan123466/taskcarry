"""Shared typed public contracts for CLI, API and MCP. No runtime dependencies."""
from copy import deepcopy

def string(description="", **kwargs):
    return {"type": "string", "description": description, **kwargs}


def schema(properties=None, required=()):
    return {"type": "object", "properties": properties or {}, "required": list(required), "additionalProperties": False}


PATHS = {"type": "array", "items": string("Exact workspace-relative file path"), "minItems": 1, "uniqueItems": True}
BOOL = {"type": "boolean"}
OPEN_OBJECT = {"type": "object", "additionalProperties": True}
SCHEMAS = {
    "identity": schema({"action": string(enum=["status", "plan", "execute"]), "plan_id": string()}),
    "onboarding": schema({"onboarding_id": string(), "action": string(enum=["start", "update", "status"]),
                          "scope": schema({"governance_thread": string(), "channel": string(enum=["rc", "stable"]),
                                           "schedule": schema({"time": string(), "timezone": string()}, ["time", "timezone"]),
                                           "windows": {"type": "array", "minItems": 1, "maxItems": 100,
                                                       "items": schema({"thread_id": string(), "mode": string(enum=["active", "reference"]),
                                                                        "task_id": string(), "workspace": string(), "source_ref": string(), "responsibility": string()},
                                                                       ["thread_id", "mode", "source_ref", "responsibility"])}},
                                          ["governance_thread", "channel", "schedule", "windows"]),
                          "item": schema({"key": string(), "status": string(enum=["verified", "pending", "declined"]),
                                          "evidence": OPEN_OBJECT, "next_step": string()}, ["key", "status", "evidence", "next_step"]),
                          "expected_revision": {"type": "integer", "minimum": 1}}, ["onboarding_id"]),
    "schedule_plan": schema({"onboarding_id": string()}, ["onboarding_id"]),
    "preserve": schema({"action": string(enum=["plan", "execute", "status"]), "repository": string(),
                        "paths": {**PATHS, "maxItems": 500}, "message": string(), "plan_id": string()}),
    "connect": schema({"action": string(enum=["plan", "execute", "status"]),
                       "target": string(), "workspace": string(), "task_id": string(), "plan_id": string()}),
    "identify": schema(),
    "context": schema({"task_id": string(), "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                       "cursor": string(), "previous_fingerprint": string(),
                       "issue_ids": {"type": "array", "items": string(), "maxItems": 50, "uniqueItems": True},
                       "fix_ids": {"type": "array", "items": string(), "maxItems": 50, "uniqueItems": True}}, ["task_id"]),
    "governance": schema({"mode": string(enum=["inspect", "record"]),
                          "rule_paths": {"type": "array", "items": string(), "maxItems": 100, "uniqueItems": True},
                          "record_id": string(), "expected_fingerprint": string(),
                          "evidence_refs": {"type": "array", "items": string(), "minItems": 1, "maxItems": 50, "uniqueItems": True},
                          "expected_revision": {"type": "integer", "minimum": 0}}),
    "upgrade": schema(),
    "observe": schema({"observation_id": string(), "workspace": {"type": ["string", "null"]}, "task_id": string(),
                       "source_ref": string(), "source_revision": string(), "summary": string(),
                       "relations": {"type": "array", "items": schema({"kind": string(enum=["stage", "artifact"]), "id": string()}, ["kind", "id"])},
                       "expected_revision": {"type": "integer", "minimum": 1}},
                      ["observation_id", "workspace", "task_id", "source_ref", "source_revision", "summary"]),
    "run": schema({"run_id": string(), "mode": string(enum=["start", "finish", "inspect"]),
                   "stage_ids": {"type": "array", "items": string(), "uniqueItems": True},
                   "operation_ids": {"type": "array", "items": string(), "uniqueItems": True},
                   "observation_ids": {"type": "array", "items": string(), "uniqueItems": True}, "note": string()}, ["run_id"]),
    "issue": schema({"issue_id": string(), "condition": string(), "summary": string(),
                     "state": string(enum=["open", "resolved"]), "resolution_ref": string(),
                     "expected_revision": {"type": "integer", "minimum": 1}}, ["issue_id", "condition", "summary"]),
    "fix": schema({"fix_id": string(), "issue_id": string(), "version": string(),
                   "evidence_refs": {"type": "array", "items": string(), "minItems": 1, "uniqueItems": True},
                   "summary": string(), "expected_revision": {"type": "integer", "minimum": 1}},
                  ["fix_id", "issue_id", "version", "evidence_refs"]),
    "status": schema(),
    "agenda": schema({"limit": {"type": "integer", "minimum": 1, "maximum": 100}, "previous_fingerprint": string(), "cursor": string()}),
    "doctor": schema(),
    "task": schema({"task_id": string(), "title": string(), "workstream": string(), "state": string(enum=["active", "paused", "waiting", "complete"])}, ["task_id"]),
    "checkpoint": schema({"task_id": string(), "workspace": string(), "paths": PATHS, "next_step": string(), "decision": string(), "paused": BOOL}, ["task_id", "workspace", "paths", "next_step"]),
    "restore": schema({"checkpoint_id": string(), "destination": string("Absent or empty independent destination; repeat the same checkpoint and destination to verify and finish a recorded restore")}, ["checkpoint_id", "destination"]),
    "artifact": schema({"task_id": string(), "path": string(), "role": string(), "backup": string(),
                        "decision": string("Content-bound review choice, not free-text checkpoint reasoning. retain keeps unverified backup work actionable; ignore/dismiss/no_backup_needed suppress that item only after an authorized decision. Omit to preserve a choice for unchanged content; registration does not create a backup.",
                                           enum=["ignore", "dismiss", "no_backup_needed", "retain"])}, ["task_id", "path"]),
    "experience": schema({"rule_id": string(), "code": string(), "operation": string(), "action": string(enum=["verify_and_finalize", "refresh_plan"]), "task_id": string(), "version": string(), "enabled": BOOL}, ["rule_id", "code", "operation", "action"]),
    "workspace": schema({"name": string(), "path": string("Existing local Git worktree")}, ["name", "path"]),
    "submit": schema({"task_id": string(), "workspace": string(), "commit": string(), "base": string(), "paths": PATHS, "stage_id": string(), "relation": string(enum=["independent", "cumulative"]), "supersedes": {"type": "array", "items": string(), "uniqueItems": True}}, ["task_id", "workspace", "commit", "base", "paths"]),
    "reconcile": schema({"baseline": string(), "execute": BOOL, "plan_id": string(), "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Maximum distinct work items frozen into a new plan; execution uses its existing plan scope."}}, ["baseline"]),
    "adopt": schema({"workspace": string(), "baseline": string(), "execute": BOOL, "plan_id": string()}, ["workspace", "baseline"]),
}

from .adapter_contracts import SCHEMAS as ADAPTER_SCHEMAS
SCHEMAS.update(ADAPTER_SCHEMAS)
from .cycle_contracts import SCHEMAS as CYCLE_SCHEMAS
from .workbench_contracts import SCHEMAS as WORKBENCH_SCHEMAS
from .recovery_contracts import SCHEMAS as RECOVERY_SCHEMAS
SCHEMAS.update(CYCLE_SCHEMAS)
SCHEMAS.update(WORKBENCH_SCHEMAS)
SCHEMAS.update(RECOVERY_SCHEMAS)
from .transfer_contracts import SCHEMAS as TRANSFER_SCHEMAS
SCHEMAS.update(TRANSFER_SCHEMAS)

# Missing profile retains the legacy receipt contract. New complete setup must
# explicitly choose its versioned coverage rather than relabel old acceptance.
_scope_properties = SCHEMAS['onboarding']['properties']['scope']['properties']
_scope_properties['profile'] = string(enum=['complete_v1'])
_schedule = _scope_properties['schedule']
_schedule['required'] = ['timezone']
_schedule['properties']['slots'] = {
    'type': 'array', 'minItems': 2, 'maxItems': 3,
    'items': schema({'slot_id': string(), 'purpose': string(enum=['report', 'absorb']), 'time': string()},
                    ['slot_id', 'purpose', 'time'])}
def validate(value, definition, location="arguments"):
    """Validate the deliberately small schema subset used by these public tools."""
    kind = definition.get("type")
    if isinstance(kind, list):
        for member in kind:
            try:
                validate(value, {**definition, 'type': member}, location)
                return
            except ValueError:
                pass
        raise ValueError(f"{location} has an unsupported type")
    if kind == "null":
        if value is not None:
            raise ValueError(f"{location} must be null")
        return
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{location} must be an object")
        props = definition.get("properties", {})
        extra = set(value) - set(props)
        missing = set(definition.get("required", [])) - set(value)
        if extra and definition.get("additionalProperties") is not True:
            raise ValueError(f"{location} has unknown fields: {', '.join(sorted(extra))}")
        if missing:
            raise ValueError(f"{location} lacks required fields: {', '.join(sorted(missing))}")
        for name, item in value.items():
            if name in props:
                validate(item, props[name], f"{location}.{name}")
    elif kind == "string" and not isinstance(value, str):
        raise ValueError(f"{location} must be a string")
    elif kind == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{location} must be a boolean")
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{location} must be an integer")
        if value < definition.get("minimum", value) or value > definition.get("maximum", value):
            raise ValueError(f"{location} is outside the supported range")
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError(f"{location} must be an array")
        if not definition.get("minItems", 0) <= len(value) <= definition.get("maxItems", len(value)):
            raise ValueError(f"{location} has an unsupported item count")
        for index, item in enumerate(value):
            validate(item, definition["items"], f"{location}[{index}]")
        if definition.get("uniqueItems") and len(value) != len(set(value)):
            raise ValueError(f"{location} must contain unique items")
    if "enum" in definition and value not in definition["enum"]:
        raise ValueError(f"{location} is outside the supported values")


def action_schema(action, allow_fault=False):
    if action == "init":
        return schema({"name": string()})
    if action not in SCHEMAS:
        raise ValueError("Unknown action: " + str(action))
    definition = deepcopy(SCHEMAS[action])
    if allow_fault and action in {"reconcile", "adopt"}:
        choices = ["after_candidate", "after_effect"] if action == "reconcile" else ["after_stash", "after_adopt", "after_restore"]
        definition["properties"]["fault"] = string(enum=choices)
    return definition


