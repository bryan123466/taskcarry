"""Plain-directory checkpoints work without Git; repository ambiguity fails closed."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from taskcarry import core as core_module
from taskcarry.core import Core, git
from taskcarry.store import GovernanceError


REPOSITORY = Path(__file__).resolve().parents[1]
PAYLOAD = "合成表单\r\n".encode("utf-8") + b"\x00\xff\n"


class OptionalGitCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="taskcarry-optional-git-")
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / "control"
        Core.initialize(self.project, "Synthetic optional Git")
        self.core = Core(self.project)
        self.core.task("forms", "Synthetic form review")
        self.workspace = self.root / "author"
        self.workspace.mkdir()
        (self.workspace / "form.bin").write_bytes(PAYLOAD)

    def tearDown(self):
        self.temporary.cleanup()

    def checkpoint(self, workspace=None):
        return self.core.checkpoint("forms", workspace or self.workspace,
                                    ["form.bin"], "Continue synthetic review", paused=True)

    def assert_rejected(self, workspace=None, code=None):
        workspace = workspace or self.workspace
        source_before = (workspace / "form.bin").read_bytes()
        task_before = self.core.store.get("tasks", "forms")
        events_before = self.core.store.events()
        checkpoints_before = self.core.store.list("checkpoints")
        index = workspace / ".git/index"
        index_before = index.read_bytes() if index.is_file() else None
        with self.assertRaises((GovernanceError, PermissionError)) as failure:
            self.checkpoint(workspace)
        if code:
            self.assertEqual(getattr(failure.exception, "code", None), code)
        self.assertEqual((workspace / "form.bin").read_bytes(), source_before)
        self.assertEqual(self.core.store.get("tasks", "forms"), task_before)
        self.assertEqual(self.core.store.events(), events_before)
        self.assertEqual(self.core.store.list("checkpoints"), checkpoints_before)
        if index_before is not None:
            self.assertEqual(index.read_bytes(), index_before)

    def initialize_git(self, workspace=None):
        workspace = workspace or self.workspace
        git(workspace, "init", "--quiet")
        git(workspace, "config", "user.name", "Synthetic Author")
        git(workspace, "config", "user.email", "author@example.invalid")
        git(workspace, "add", "--", "form.bin")
        git(workspace, "commit", "--quiet", "-m", "Synthetic baseline")

    def launch(self, action, arguments=None, mcp=False):
        # The interpreter is absolute; only Git discovery loses PATH. Explicit
        # source selection is confined to this disposable development test.
        bootstrap = "import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); runpy.run_module('taskcarry', run_name='__main__', alter_sys=True)"
        command = [sys.executable, "-I", "-X", "utf8", "-c", bootstrap,
                   str(REPOSITORY), "--project", str(self.project)]
        environment = dict(os.environ, PATH="")
        if mcp:
            command.append("mcp")
            frames = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-11-25", "capabilities": {},
                    "clientInfo": {"name": "synthetic-no-git", "version": "1"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                    "name": "taskcarry_" + action, "arguments": arguments or {}}},
            ]
            input_text = "".join(json.dumps(frame, ensure_ascii=False) + "\n" for frame in frames)
        else:
            command.extend([action, "--json", json.dumps(arguments or {}, ensure_ascii=False)])
            input_text = None
        process = subprocess.run(command, cwd=self.root, env=environment,
                                 input=input_text, capture_output=True, text=True,
                                 encoding="utf-8", timeout=30)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        if mcp:
            responses = [json.loads(line) for line in process.stdout.splitlines()]
            result = next(row for row in responses if row.get("id") == 2)["result"]
            self.assertFalse(result["isError"], result)
            envelope = result["structuredContent"]
        else:
            envelope = json.loads(process.stdout)
        self.assertTrue(envelope["ok"], envelope)
        return envelope["result"]

    def subprocess_roundtrip(self, mcp):
        checkpoint = self.launch("checkpoint", {
            "task_id": "forms", "workspace": str(self.workspace), "paths": ["form.bin"],
            "next_step": "继续检查", "paused": True}, mcp=mcp)
        self.assertFalse(checkpoint["git"])
        self.assertFalse(checkpoint["delivery"])
        self.assertIsNone(checkpoint["original_head"])
        record = checkpoint["files"][0]
        self.assertIsNone(record["head"])
        self.assertIsNone(record["index"])
        self.assertEqual(record["worktree"]["sha256"], hashlib.sha256(PAYLOAD).hexdigest())
        (self.workspace / "form.bin").write_bytes(b"newer user work\n")
        destination = self.root / "restored"
        restored = self.launch("restore", {
            "checkpoint_id": checkpoint["checkpoint_id"], "destination": str(destination)}, mcp=mcp)
        self.assertTrue(restored["restored"])
        self.assertFalse(restored["synthetic_git_baseline"])
        self.assertFalse(restored["original_workspace_modified"])
        self.assertEqual((destination / "form.bin").read_bytes(), PAYLOAD)
        self.assertEqual((self.workspace / "form.bin").read_bytes(), b"newer user work\n")
        self.assertFalse((destination / ".git").exists())
        status = self.launch("status", mcp=mcp)
        self.assertEqual(status["tasks"][0]["latest_checkpoint"], checkpoint["checkpoint_id"])
        self.assertEqual(status["tasks"][0]["state"], "paused")
        self.assertEqual(status["tasks"][0]["next_step"], "继续检查")
        self.assertEqual(status["stages"], [])
        events = self.core.store.events()
        saved = [row for row in events if row["kind"] == "checkpoint_saved"]
        restored_events = [row for row in events if row["kind"] == "checkpoint_restored"]
        self.assertEqual(len(saved), 1)
        self.assertEqual(len(restored_events), 1)
        self.assertEqual(saved[0]["payload"]["checkpoint_id"], checkpoint["checkpoint_id"])
        self.assertEqual(restored_events[0]["payload"]["checkpoint_id"], checkpoint["checkpoint_id"])

    def test_cli_plain_checkpoint_and_restore_with_empty_path(self):
        self.subprocess_roundtrip(mcp=False)

    def test_mcp_plain_checkpoint_and_restore_with_empty_path(self):
        self.subprocess_roundtrip(mcp=True)

    def test_plain_directory_does_not_invoke_git_even_when_it_is_present(self):
        with mock.patch.object(core_module, "git", side_effect=AssertionError("Plain snapshot must not execute Git")):
            checkpoint = self.checkpoint()
            destination = self.root / "plain-restored"
            self.core.restore(checkpoint["checkpoint_id"], destination)
        self.assertFalse(checkpoint["git"])
        self.assertEqual((destination / "form.bin").read_bytes(), PAYLOAD)

    def test_real_git_root_requires_git_without_changing_index_or_worktree(self):
        self.initialize_git()
        (self.workspace / "form.bin").write_bytes(b"unstaged user work\n")
        with mock.patch.dict(os.environ, {"PATH": ""}):
            self.assert_rejected(code="GIT_UNAVAILABLE")

    def test_linked_worktree_git_file_requires_git(self):
        self.initialize_git()
        linked = self.root / "linked"
        git(self.workspace, "worktree", "add", "--quiet", "-b", "synthetic-linked", str(linked))
        self.assertTrue((linked / ".git").is_file())
        with mock.patch.dict(os.environ, {"PATH": ""}):
            self.assert_rejected(linked, code="GIT_UNAVAILABLE")

    def test_ancestor_git_root_is_not_mistaken_for_plain_directory(self):
        self.initialize_git()
        nested = self.workspace / "nested" / "deeper"
        nested.mkdir(parents=True)
        (nested / "form.bin").write_bytes(PAYLOAD)
        with mock.patch.dict(os.environ, {"PATH": ""}):
            self.assert_rejected(nested, code="GIT_UNAVAILABLE")
        self.assert_rejected(nested, code="GIT_WORKSPACE_ROOT")

    def test_bare_repository_root_and_descendants_never_use_plain_mode(self):
        git(self.workspace, "init", "--bare", "--quiet")
        nested = self.workspace / "nested"
        nested.mkdir()
        (nested / "form.bin").write_bytes(PAYLOAD)
        for damaged in (False, True):
            if damaged:
                (self.workspace / "HEAD").unlink()
            for workspace in (self.workspace, nested):
                with self.subTest(workspace=workspace.name, missing_head=damaged):
                    self.assert_rejected(workspace)
                    with mock.patch.dict(os.environ, {"PATH": ""}):
                        self.assert_rejected(workspace, code="GIT_UNAVAILABLE")

    def test_corrupt_git_file_or_directory_is_not_a_plain_directory(self):
        for kind in ("file", "directory"):
            with self.subTest(kind=kind):
                workspace = self.root / ("corrupt-" + kind)
                workspace.mkdir()
                (workspace / "form.bin").write_bytes(PAYLOAD)
                marker = workspace / ".git"
                if kind == "file":
                    marker.write_text("gitdir: missing-metadata\n", encoding="utf-8")
                else:
                    marker.mkdir()
                self.assert_rejected(workspace)

    def test_split_metadata_with_commondir_cannot_be_saved_as_plain_files(self):
        (self.workspace / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        (self.workspace / "commondir").write_text("../missing-common\n", encoding="utf-8")
        self.assert_rejected(code="GIT_ERROR")
        with mock.patch.dict(os.environ, {"PATH": ""}):
            self.assert_rejected(code="GIT_UNAVAILABLE")

    def test_commondir_filename_alone_does_not_require_git(self):
        (self.workspace / "commondir").write_text("ordinary project note\n", encoding="utf-8")
        with mock.patch.object(core_module, "git", side_effect=AssertionError("Plain file name is not Git metadata")):
            checkpoint = self.checkpoint()
        self.assertFalse(checkpoint["git"])

    def test_dangling_git_marker_is_not_treated_as_absent(self):
        marker = self.workspace / ".git"
        try:
            marker.symlink_to(self.root / "missing-metadata", target_is_directory=True)
        except OSError:
            # Keep the semantic regression on hosts without symlink privilege:
            # lstat sees a link while exists/stat report a missing target.
            original = Path.lstat
            link_stat = os.stat_result((stat.S_IFLNK, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            def dangling(path):
                return link_stat if path == marker else original(path)

            with mock.patch.object(Path, "lstat", new=dangling):
                self.assert_rejected()
        else:
            self.assertFalse(marker.exists())
            self.assertTrue(marker.is_symlink())
            self.assert_rejected()

    def test_failed_or_inaccessible_git_probe_never_publishes_plain_checkpoint(self):
        (self.workspace / ".git").mkdir()
        failures = [
            (subprocess.CompletedProcess(["git"], 128, b"", b"synthetic corrupt metadata"), "GIT_ERROR"),
            (subprocess.CompletedProcess(["git"], 0, b"false\n", b""), "GIT_WORKSPACE_ROOT"),
            (subprocess.TimeoutExpired(["git"], 60), "GIT_TIMEOUT"),
            (PermissionError("synthetic executable permission denied"), "GIT_UNAVAILABLE"),
        ]
        for failure, code in failures:
            with self.subTest(failure=type(failure).__name__ + str(getattr(failure, "returncode", ""))):
                options = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                with mock.patch.object(core_module.subprocess, "run", **options):
                    self.assert_rejected(code=code)

    def test_metadata_inspection_permission_failure_preserves_task_and_source(self):
        original = Path.lstat
        marker = self.workspace / ".git"

        def denied(path):
            if path == marker:
                raise PermissionError("synthetic metadata access denied")
            return original(path)

        with mock.patch.object(Path, "lstat", new=denied):
            self.assert_rejected(code="GIT_WORKSPACE_UNVERIFIED")

    def test_plain_directory_becoming_repository_during_capture_is_not_published(self):
        original = self.core._snapshot
        changed = False

        def initialize_after_capture(data):
            nonlocal changed
            result = original(data)
            if not changed:
                changed = True
                git(self.workspace, "init", "--quiet")
            return result

        with mock.patch.object(self.core, "_snapshot", side_effect=initialize_after_capture):
            self.assert_rejected()
        self.assertTrue((self.workspace / ".git").is_dir())
        self.assertEqual((self.workspace / "form.bin").read_bytes(), PAYLOAD)


if __name__ == "__main__":
    unittest.main()
