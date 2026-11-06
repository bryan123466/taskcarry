"""Bounded synchronous MCP stdio server; no network or arbitrary method dispatch."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from .cli import envelope_error

PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MAX_LINE_BYTES = 1024 * 1024


from .contracts import SCHEMAS, validate


DESCRIPTIONS = {
    "identity": "Read a portable project identity or explicitly plan and adopt one for legacy state. Retains previous source aliases; no package update.",
    "codex": "Use a selected supported Codex executable to inspect capabilities, list or read bounded chat history. No turns or messages; host startup may write its own caches.",
    "update_source": "Explicitly register the official release channel and current artifact/method identities. Does not install or schedule.",
    "update_check": "Read bounded official release metadata and compare the selected channel. No local record, installation or claim of host loading.",
    "update_assess": "Explicitly save an applicability assessment for a content-bound release check; reuse unchanged input. Does not install.",
    "onboarding": "Start, read or update a resumable onboarding checklist tied to actual local identities and qualified host evidence.",
    "schedule_plan": "Prepare durable original-chat governance instructions. The host must create/read back its schedule; no scheduler execution here.",
    "preserve": "Plan or execute exact local Git file saving, preserving unrelated staged and working changes. Not submission or remote backup.",
    "connect": "Plan or apply the exact generated MCP block to a project configuration, preserving other settings. Host trust/reload and native acceptance remain separate.",
    "identify": "Read the selected location's state format and source identity without initialization or migration.",
    "context": "Read bounded, source-qualified context for a named task, with pagination and missing evidence. No acknowledgment or execution.",
    "governance": "Inspect package, managed methods and user-rule identities, or explicitly record a content-bound review. No install or host reload.",
    "upgrade": "Explicitly build or repair the derived current-work index. Preserve original records and events; no package update.",
    "observe": "Save host-reviewed evidence references and relationships with revision checks. Does not read chats or grant permissions.",
    "run": "Freeze selected record identities, inspect them, or record their verified terminal state. No Git effects or claim that the whole project is complete.",
    "issue": "Record a concrete condition and its resolution reference. Changed conditions reopen review; never mask an unfinished operation.",
    "fix": "Link a defect to a version and validation references. Compare actual project setup evidence; no installation or claim of host reload.",
    "status": "Read current tasks, deliveries and actionable issues without creating state.",
    "agenda": "Read a bounded, paginated current-work selection for the existing agent. No execution, retry, scheduling or completion claim.",
    "doctor": "Read runtime prerequisites and project support; no installation or repair.",
    "task": "Create or update a task's retained current state. This does not declare a delivery.",
    "checkpoint": "Save exact files and Git work layers for later continuation; not a submission.",
    "restore": "Restore into an empty independent directory, or verify the same recorded destination and finish its missing receipt without replaying effects. Preserve the original and later user changes.",
    "artifact": "Register content identity, task relationship, optional verified backup and decision.",
    "experience": "Register a conditional recovery rule from the fixed allowed actions; no executable shell.",
    "workspace": "Register an existing local Git workspace for bounded governance operations.",
    "submit": "Explicitly deliver exact frozen commit changes. Cumulative replacement needs lineage evidence.",
    "reconcile": "Plan delivery acceptance, or execute an existing plan with exact baseline conditions. No push.",
    "adopt": "Plan or execute an exact baseline adoption while retaining workspace work. No push.",
}

from .cycle_contracts import DESCRIPTIONS as CYCLE_DESCRIPTIONS
from .workbench_contracts import DESCRIPTIONS as WORKBENCH_DESCRIPTIONS
from .recovery_contracts import DESCRIPTIONS as RECOVERY_DESCRIPTIONS
DESCRIPTIONS.update(CYCLE_DESCRIPTIONS)
DESCRIPTIONS.update(WORKBENCH_DESCRIPTIONS)
DESCRIPTIONS.update(RECOVERY_DESCRIPTIONS)
from .transfer_contracts import DESCRIPTIONS as TRANSFER_DESCRIPTIONS
DESCRIPTIONS.update(TRANSFER_DESCRIPTIONS)


def tools_list():
    return [{"name": "taskcarry_" + action, "description": DESCRIPTIONS[action], "inputSchema": definition,
             "annotations": {"readOnlyHint": action in {"status", "agenda", "doctor", "identify", "context", "schedule_plan", "update_check"},
                             "openWorldHint": action in {"codex", "update_check"}}}
            for action, definition in SCHEMAS.items()]


def rpc_error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


class Server:
    def __init__(self, project, invoke=None):
        self.project = Path(project).resolve()
        self.initialized = False
        self.invoke = invoke

    def handle(self, request):
        if not isinstance(request, dict):
            return rpc_error(None, -32600, "JSON-RPC batches and non-object messages are unsupported")
        request_id = request.get("id")
        if request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            return rpc_error(request_id, -32600, "Invalid JSON-RPC request")
        if "id" in request and (isinstance(request_id, bool) or not isinstance(request_id, (str, int))):
            return rpc_error(None, -32600, "Request id must be a string or integer")
        method = request["method"]
        # Notifications never invoke tools or change project state.
        if "id" not in request:
            return None
        params = request.get("params", {})
        if not isinstance(params, dict):
            return rpc_error(request_id, -32602, "params must be an object")
        if method == "initialize":
            version = params.get("protocolVersion")
            if not isinstance(version, str) or not isinstance(params.get("capabilities"), dict) or not isinstance(params.get("clientInfo"), dict):
                return rpc_error(request_id, -32602, "initialize requires protocolVersion, capabilities and clientInfo")
            self.initialized = True
            from . import __version__
            result = {"protocolVersion": version if version in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "taskcarry", "version": __version__},
                      "instructions": "Project root is fixed by server startup. Use exact task and file evidence. Plan before execute. Tool availability is not permission to expand user scope."}
        elif method == "ping":
            result = {}
        elif not self.initialized:
            return rpc_error(request_id, -32002, "Initialize the MCP session first")
        elif method == "tools/list":
            if params.get("cursor"):
                return rpc_error(request_id, -32602, "This server has no paginated tool cursor")
            result = {"tools": tools_list()}
        elif method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in {"taskcarry_" + a for a in SCHEMAS}:
                return rpc_error(request_id, -32602, "Unknown tool")
            action = name[len("taskcarry_"):]
            arguments = params.get("arguments", {})
            try:
                validate(arguments, SCHEMAS[action])
            except ValueError as exc:
                return rpc_error(request_id, -32602, str(exc))
            try:
                invoke = self.invoke
                if invoke is None:
                    from .api import invoke
                output = {"ok": True, "result": invoke(self.project, action, arguments)}
                failed = False
            except Exception as exc:
                output, failed = envelope_error(exc), True
            result = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}], "isError": failed}
            if version_supports_structured(self):
                result["structuredContent"] = output
        else:
            return rpc_error(request_id, -32601, "Method not found")
        if method == "initialize":
            self.protocol = result["protocolVersion"]
        return {"jsonrpc": "2.0", "id": request_id, "result": result}


def version_supports_structured(server):
    return getattr(server, "protocol", "") in {"2025-06-18", "2025-11-25"}


def serve(project, stdin=None, stdout=None):
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    server = Server(project)
    while True:
        line = input_stream.readline(MAX_LINE_BYTES + 1)
        if not line:
            return 0
        if len(line.encode("utf-8")) > MAX_LINE_BYTES or (len(line) > MAX_LINE_BYTES and not line.endswith("\n")):
            response = rpc_error(None, -32600, "Message exceeds 1 MiB limit")
            output_stream.write(json.dumps(response) + "\n")
            output_stream.flush()
            return 1
        try:
            response = server.handle(json.loads(line))
        except (json.JSONDecodeError, UnicodeError):
            response = rpc_error(None, -32700, "Invalid JSON")
        except Exception:
            response = rpc_error(None, -32603, "Internal protocol error")
        if response is not None:
            output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
            output_stream.flush()
