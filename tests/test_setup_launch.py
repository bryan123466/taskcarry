"""Isolated launch and upgrade outcomes in disposable synthetic projects."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from taskcarry import setup
from taskcarry.api import invoke


REPOSITORY = Path(__file__).resolve().parents[1]
FRAGMENT = ".taskcarry/codex.mcp.toml"


class SetupLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="taskcarry-launch-")
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / "合成项目 Unicode"
        self.project.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def config(self):
        return tomllib.loads((self.project / FRAGMENT).read_text(encoding="utf-8"))["mcp_servers"]["taskcarry"]

    def process(self, config, cwd, frames, environment=None):
        return subprocess.run(
            [config["command"], *config["args"]], cwd=cwd, env=environment,
            input="".join(json.dumps(frame, ensure_ascii=False) + "\n" for frame in frames),
            capture_output=True, text=True, encoding="utf-8", timeout=30)

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.project.rglob("*") if p.is_file()}

    def legacy_install(self):
        """A format-1 rc5 installation, including its nonisolated fragment."""
        files = setup.planned_files(self.project)
        args = ["-m", "taskcarry", "--project", str(self.project), "mcp"]
        files[FRAGMENT] = (
            "[mcp_servers.taskcarry]\n"
            f"command = {json.dumps(sys.executable)}\n"
            f"args = {json.dumps(args, ensure_ascii=False)}\n"
            "[mcp_servers.taskcarry.env]\n"
            f"PYTHONPATH = {json.dumps(str(REPOSITORY))}\n"
            'PYTHONUTF8 = "1"\n'
        ).encode("utf-8")
        runtime = dict(setup.loaded_runtime(), version="0.2.0rc5", source_sha256="0" * 64)
        with patch.object(setup, "planned_files", return_value=files), patch.object(setup, "loaded_runtime", return_value=runtime):
            setup.configure(self.project, mode="install")
        return setup.read_manifest(self.project)

    def test_source_launch_ignores_cwd_and_environment_and_preserves_unicode(self):
        invoke(self.project, "init", {"name": "合成启动"})
        setup.configure(self.project, mode="install")
        hostile = self.root / "unselected-source"
        (hostile / "taskcarry").mkdir(parents=True)
        (hostile / "taskcarry/__init__.py").write_text("raise RuntimeError('unselected source imported')\n", encoding="utf-8")
        environment = dict(os.environ, PYTHONPATH=str(hostile), PYTHONUTF8="0", PYTHONIOENCODING="ascii")
        frames = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "synthetic-launch", "version": "1"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "taskcarry_task", "arguments": {"task_id": "quality-task", "title": "检查表单 ✓"}}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "taskcarry_status"}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "taskcarry_doctor"}},
        ]
        for cwd in (REPOSITORY, self.project, hostile):
            with self.subTest(cwd=cwd.name):
                process = self.process(self.config(), cwd, frames, environment)
                self.assertEqual(process.returncode, 0, process.stderr)
                replies = [json.loads(line) for line in process.stdout.splitlines()]
                for reply in replies[1:]:
                    self.assertFalse(reply["result"]["isError"], reply)
                task = replies[2]["result"]["structuredContent"]["result"]["tasks"][0]
                self.assertEqual((task["task_id"], task["title"]), ("quality-task", "检查表单 ✓"))
                runtime = replies[3]["result"]["structuredContent"]["result"]["runtime"]
                self.assertEqual(Path(runtime["loaded_runtime"]["module_root"]), REPOSITORY / "taskcarry")
                self.assertTrue(runtime["managed_runtime_matches_disk"])

    def test_missing_selected_package_fails_without_falling_back_to_checkout(self):
        selected = self.root / "selected-package"
        (selected / "taskcarry").mkdir(parents=True)
        for source in (REPOSITORY / "taskcarry").glob("*.py"):
            shutil.copyfile(source, selected / "taskcarry" / source.name)
        shutil.copytree(REPOSITORY / "skills", selected / "skills")
        bootstrap = "import sys; sys.path.insert(0, sys.argv.pop(1)); from taskcarry.setup import configure; configure(sys.argv[1], mode='install')"
        process = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", bootstrap, str(selected), str(self.project)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        (selected / "taskcarry").rename(selected / "removed-taskcarry")
        process = self.process(self.config(), REPOSITORY, [], dict(os.environ, PYTHONPATH=str(REPOSITORY)))
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("Selected TaskCarry package is unavailable", process.stderr)
        self.assertEqual(process.stdout, "")
        self.assertFalse((self.project / ".taskcarry/state.sqlite3").exists())

    def test_legacy_fragment_upgrade_preserves_identity_user_config_and_replay(self):
        previous = self.legacy_install()
        (self.project / ".codex").mkdir()
        user_config = self.project / ".codex/config.toml"
        user_config.write_text('model = "synthetic-user-choice"\n', encoding="utf-8")
        before = self.snapshot()
        preview = setup.configure(self.project)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual([row["path"] for row in preview["files"] if row["action"] == "update"], [FRAGMENT])
        result = setup.configure(self.project, mode="install")
        self.assertEqual(result["files_written"], 1)
        manifest = setup.read_manifest(self.project)
        self.assertEqual(manifest["installation_id"], previous["installation_id"])
        self.assertEqual(self.config()["args"][:3], ["-I", "-X", "utf8"])
        for name, saved in before.items():
            if name not in (FRAGMENT, ".taskcarry/setup-manifest.json"):
                self.assertEqual(self.snapshot()[name], saved)
        updated = self.snapshot()
        repeated = setup.configure(self.project, mode="install")
        self.assertEqual(repeated["files_written"], 0)
        self.assertFalse(repeated["manifest_written"])
        self.assertEqual(self.snapshot(), updated)

    def test_modified_legacy_fragment_is_preserved_without_adoption(self):
        self.legacy_install()
        fragment = self.project / FRAGMENT
        fragment.write_bytes(fragment.read_bytes() + b"\n# User customization\n")
        before = self.snapshot()
        with self.assertRaises(setup.SetupError) as raised:
            setup.configure(self.project, mode="install")
        self.assertEqual(raised.exception.code, "SETUP_CONFLICT")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.project / ".taskcarry/setup-intent.json").exists())

    def test_upgrade_interruption_resumes_receipt_without_rewriting_fragment(self):
        previous = self.legacy_install()
        original = setup.atomic_write

        def interrupt(path, content):
            original(path, content)
            if path == self.project / FRAGMENT:
                raise RuntimeError("synthetic interruption after isolated fragment write")

        with patch.object(setup, "atomic_write", side_effect=interrupt):
            with self.assertRaisesRegex(RuntimeError, "synthetic interruption"):
                setup.configure(self.project, mode="install")
        self.assertEqual(setup.read_manifest(self.project), previous)
        fragment_before = self.snapshot()[FRAGMENT]
        resumed = setup.configure(self.project, mode="install")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["files_written"], 0)
        self.assertEqual(self.snapshot()[FRAGMENT], fragment_before)
        self.assertEqual(setup.read_manifest(self.project)["installation_id"], previous["installation_id"])
        self.assertFalse((self.project / ".taskcarry/setup-intent.json").exists())
        self.assertTrue(setup.runtime_info(self.project)["managed_runtime_matches_disk"])


if __name__ == "__main__":
    unittest.main()
