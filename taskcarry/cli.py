"""One JSON command interface shared with the MCP adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ACTIONS = (
    "init", "status", "agenda", "task", "checkpoint", "restore", "artifact", "experience",
    "workspace", "submit", "reconcile", "adopt", "doctor", "setup", "mcp",
    "upgrade", "observe", "run", "issue", "fix", "identify", "context", "governance", "connect",
    "codex", "update_source", "update_check", "update_assess", "onboarding", "schedule_plan", "preserve",
)


class ArgumentError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)


def envelope_error(exc):
    return {"ok": False, "error": {
        "code": getattr(exc, "code", "INVALID_ARGUMENT" if isinstance(exc, (ValueError, TypeError)) else "INTERNAL_ERROR"),
        "message": getattr(exc, "message", str(exc)),
        "details": getattr(exc, "details", None),
    }}


def main(argv=None):
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = Parser(description="TaskCarry: project-local governance")
    parser.add_argument("--project", required=True, help="Explicit governance project directory")
    parser.add_argument("action", choices=ACTIONS)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--json", dest="arguments_json", help="Action arguments as a JSON object")
    source.add_argument("--input", type=Path, help="UTF-8 JSON file containing action arguments")
    try:
        args = parser.parse_args(argv)
        if args.action == "mcp":
            if args.input is not None or args.arguments_json is not None:
                raise ArgumentError("MCP takes its requests on stdin, not --json or --input")
            from .mcp import serve
            return serve(Path(args.project))
        text = args.arguments_json or "{}"
        if args.input is not None:
            if args.input.stat().st_size > 1024 * 1024:
                raise ArgumentError("Input JSON exceeds the 1 MiB limit")
            text = args.input.read_text(encoding="utf-8-sig")
        if len(text.encode("utf-8")) > 1024 * 1024:
            raise ArgumentError("Input JSON exceeds the 1 MiB limit")
        arguments = json.loads(text)
        if not isinstance(arguments, dict):
            raise ArgumentError("Action arguments must be a JSON object")
        if args.action == "setup":
            from .setup import configure
            result = configure(Path(args.project), **arguments)
        else:
            from .api import invoke
            result = invoke(Path(args.project), args.action, arguments)
        output, exit_code = {"ok": True, "result": result}, 0
    except Exception as exc:
        output, exit_code = envelope_error(exc), 1
    sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
    return exit_code
