"""Observable adapter contracts; all project effects stay in temporary directories."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

from taskcarry.mcp import MAX_LINE_BYTES, Server, serve, tools_list
from taskcarry.setup import SetupError, configure

REPOSITORY = Path(__file__).resolve().parents[1]


def request(method, params=None, request_id=1):
    result = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        result["params"] = params
    return result


def initialize(version="2025-11-25"):
    return request("initialize", {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1"}})


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.calls = []

        def fake_invoke(project, action, arguments):
            self.calls.append((project, action, arguments))
            return {"action": action, "arguments": arguments}

        self.server = Server(self.root, fake_invoke)

    def tearDown(self):
        self.tmp.cleanup()

    def test_session_negotiation_and_typed_tools(self):
        reply = self.server.handle(initialize())
        self.assertEqual(reply["result"]["protocolVersion"], "2025-11-25")
        reply = self.server.handle(request("tools/list"))
        tools = reply["result"]["tools"]
        self.assertEqual(len(tools), 28)
        for tool in tools:
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertNotIn("project", tool["inputSchema"]["properties"])
        agenda = next(tool for tool in tools if tool["name"] == "taskcarry_agenda")
        self.assertTrue(agenda["annotations"]["readOnlyHint"])
        self.assertFalse(self.calls)

    def test_requires_initialize_and_rejects_unknown_method(self):
        self.assertEqual(self.server.handle(request("tools/list"))["error"]["code"], -32002)
        self.server.handle(initialize())
        self.assertEqual(self.server.handle(request("exec"))["error"]["code"], -32601)
        self.assertFalse(self.calls)

    def test_fixed_root_and_unicode_tool_result(self):
        self.server.handle(initialize())
        result = self.server.handle(request("tools/call", {"name": "taskcarry_task", "arguments": {"task_id": "任务-1", "title": "Quality form"}}))["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(self.calls[0][0], self.root.resolve())
        self.assertEqual(result["structuredContent"]["result"]["arguments"]["task_id"], "任务-1")

    def test_project_override_and_fault_injection_are_not_tools(self):
        self.server.handle(initialize())
        for arguments in ({"project": str(self.root.parent)}, {"baseline": "baseline", "fault": "after_effect"}):
            tool = "taskcarry_status" if "project" in arguments else "taskcarry_reconcile"
            reply = self.server.handle(request("tools/call", {"name": tool, "arguments": arguments}))
            self.assertEqual(reply["error"]["code"], -32602)
        self.assertFalse(self.calls)

    def test_malformed_schema_values_do_not_reach_engine(self):
        self.server.handle(initialize())
        cases = [
            ("taskcarry_task", {"task_id": "x", "state": "maybe"}),
            ("taskcarry_reconcile", {"baseline": "baseline", "execute": 1}),
            ("taskcarry_checkpoint", {"task_id": "x", "workspace": "w", "paths": ["a", "a"], "next_step": "continue"}),
            ("taskcarry_checkpoint", {"task_id": "x"}),
            ("taskcarry_status", []),
            ("taskcarry_agenda", {"limit": True}),
            ("taskcarry_agenda", {"limit": 101}),
            ("taskcarry_agenda", {"limit": 1.5}),
        ]
        for name, arguments in cases:
            self.assertEqual(self.server.handle(request("tools/call", {"name": name, "arguments": arguments}))["error"]["code"], -32602)
        self.assertFalse(self.calls)

    def test_notification_cannot_mutate_and_unknown_tool_is_rpc_error(self):
        self.server.handle(initialize())
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "taskcarry_task", "arguments": {"task_id": "x"}}}))
        self.assertEqual(self.server.handle(request("tools/call", {"name": "taskcarry_shell"}))["error"]["code"], -32602)
        self.assertFalse(self.calls)

    def test_tool_failure_is_not_protocol_failure(self):
        class FakeFailure(Exception):
            code, message, details = "BASELINE_CHANGED", "Replan exact scope", {"plan": "p1"}

        def fail(*args):
            raise FakeFailure()

        self.server.invoke = fail
        self.server.handle(initialize())
        reply = self.server.handle(request("tools/call", {"name": "taskcarry_status"}))["result"]
        self.assertTrue(reply["isError"])
        self.assertEqual(reply["structuredContent"]["error"]["code"], "BASELINE_CHANGED")

    def test_old_version_omits_structured_results(self):
        self.server.handle(initialize("2024-11-05"))
        reply = self.server.handle(request("tools/call", {"name": "taskcarry_status"}))["result"]
        self.assertNotIn("structuredContent", reply)
        self.assertFalse(reply["isError"])

    def test_bad_json_does_not_corrupt_next_frame(self):
        output = io.StringIO()
        frames = "not json\n" + json.dumps(initialize()) + "\n" + json.dumps(request("ping", request_id=2)) + "\n"
        self.assertEqual(serve(self.root, io.StringIO(frames), output), 0)
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(replies[0]["error"]["code"], -32700)
        self.assertIn("serverInfo", replies[1]["result"])
        self.assertEqual(replies[2]["id"], 2)

    def test_oversized_frame_is_bounded(self):
        output = io.StringIO()
        self.assertEqual(serve(self.root, io.StringIO("x" * (MAX_LINE_BYTES + 100)), output), 1)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], -32600)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_is_read_only(self):
        result = configure(self.root)
        self.assertEqual(result["mode"], "preview")
        self.assertEqual(len(result["files"]), 7)
        self.assertIn(".agents/skills/taskcarry-project-setup/references/onboarding.md",
                      [row["path"] for row in result["files"]])
        self.assertFalse(result["conflicts"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_install_preserves_user_configuration_and_is_idempotent(self):
        (self.root / "AGENTS.md").write_text("User instructions", encoding="utf-8")
        (self.root / ".codex").mkdir()
        (self.root / ".codex/config.toml").write_text('model = "user-choice"\n', encoding="utf-8")
        configure(self.root, mode="install")
        repeated = configure(self.root, mode="install")
        self.assertTrue(all(item["action"] == "unchanged" for item in repeated["files"]))
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), "User instructions")
        self.assertEqual((self.root / ".codex/config.toml").read_text(encoding="utf-8"), 'model = "user-choice"\n')

    def test_uninstall_preserves_changed_skills_and_project_files(self):
        configure(self.root, mode="install")
        changed = self.root / ".agents/skills/taskcarry-task-delivery/SKILL.md"
        changed.write_text("User modified instructions", encoding="utf-8")
        (self.root / "deliverable.md").write_text("Keep", encoding="utf-8")
        result = configure(self.root, mode="uninstall")
        self.assertEqual(result["preserved_modified"], [".agents/skills/taskcarry-task-delivery/SKILL.md"])
        self.assertEqual(changed.read_text(encoding="utf-8"), "User modified instructions")
        self.assertTrue((self.root / "deliverable.md").exists())
        self.assertFalse((self.root / ".taskcarry/codex.mcp.toml").exists())

    def test_unmanaged_destination_conflict_causes_no_install(self):
        target = self.root / ".agents/skills/taskcarry-project-setup/SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("Existing user skill", encoding="utf-8")
        with self.assertRaises(SetupError) as raised:
            configure(self.root, mode="install")
        self.assertEqual(raised.exception.code, "SETUP_CONFLICT")
        self.assertEqual(target.read_text(encoding="utf-8"), "Existing user skill")
        self.assertFalse((self.root / ".taskcarry/codex.mcp.toml").exists())

    def test_manifest_cannot_authorize_deleting_arbitrary_project_file(self):
        (self.root / ".taskcarry").mkdir()
        (self.root / ".taskcarry/setup-manifest.json").write_text(json.dumps({"format": 1, "files": {"important.txt": "0" * 64}}), encoding="utf-8")
        with self.assertRaises(SetupError) as raised:
            configure(self.root, mode="uninstall")
        self.assertEqual(raised.exception.code, "SETUP_MANIFEST_INVALID")

    def test_generated_fragment_launches_real_subprocess_from_other_directory(self):
        configure(self.root, mode="install")
        config = tomllib.loads((self.root / ".taskcarry/codex.mcp.toml").read_text(encoding="utf-8"))["mcp_servers"]["taskcarry"]
        environment = os.environ.copy()
        environment.update(config.get("env", {}))
        frames = "\n".join(json.dumps(item) for item in [initialize(), request("tools/list", request_id=2)]) + "\n"
        process = subprocess.run([config["command"], *config["args"]], input=frames, text=True, encoding="utf-8", capture_output=True, cwd=self.root, env=environment, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        replies = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(replies), 2)
        self.assertEqual(len(replies[1]["result"]["tools"]), 28)
        self.assertFalse((self.root / ".codex").exists())

    def test_symlinked_install_directory_is_refused(self):
        destination = self.root / "elsewhere"
        destination.mkdir()
        try:
            (self.root / ".agents").symlink_to(destination, target_is_directory=True)
        except OSError:
            self.skipTest("Host cannot create a directory symlink")
        with self.assertRaises(SetupError) as raised:
            configure(self.root, mode="install")
        self.assertEqual(raised.exception.code, "SETUP_LINK")
        self.assertEqual(list(destination.iterdir()), [])


class CliSubprocessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.environment = os.environ.copy()
        self.environment.update({"PYTHONPATH": str(REPOSITORY), "PYTHONUTF8": "1"})

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "taskcarry", "--project", str(self.root), *args], capture_output=True, text=True, encoding="utf-8", env=self.environment, cwd=self.root, timeout=20)

    def test_invalid_json_and_action_have_machine_readable_errors(self):
        for args in (("status", "--json", "[1]"), ("status", "--json", "{"), ("shell",)):
            process = self.run_cli(*args)
            self.assertEqual(process.returncode, 1)
            self.assertFalse(json.loads(process.stdout)["ok"])

    def test_setup_input_file_and_mutually_exclusive_inputs(self):
        arguments = self.root / "request.json"
        arguments.write_text('{"mode":"preview"}', encoding="utf-8-sig")
        result = self.run_cli("setup", "--input", str(arguments))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["mode"], "preview")
        result = self.run_cli("setup", "--input", str(arguments), "--json", "{}")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / ".taskcarry").exists())

    def test_real_engine_roundtrip_in_independent_processes(self):
        initialized = self.run_cli("init", "--json", '{"name":"Synthetic interface test"}')
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        task = self.run_cli("task", "--json", json.dumps({"task_id": "form-review", "title": "品质表单", "state": "paused"}, ensure_ascii=False))
        self.assertEqual(task.returncode, 0, task.stdout + task.stderr)
        status = self.run_cli("status")
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("form-review", status.stdout)
        self.assertIn("paused", status.stdout)
        frames = "\n".join(json.dumps(item) for item in [initialize(), request("tools/call", {"name": "taskcarry_status"}, request_id=2)]) + "\n"
        process = subprocess.run([sys.executable, "-m", "taskcarry", "--project", str(self.root), "mcp"], input=frames, text=True, encoding="utf-8", capture_output=True, env=self.environment, cwd=self.root, timeout=20)
        replies = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(replies[1]["result"]["isError"])
        self.assertIn("form-review", replies[1]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
