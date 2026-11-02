"""Release-boundary regressions: common API admission and installed assets."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest
import zipfile

from taskcarry.api import invoke
from taskcarry.core import Core
from taskcarry.gitops import git, out
from taskcarry.store import GovernanceError


class PublicApiContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="taskcarry-release-")
        self.root = Path(self.temp.name)
        self.project = self.root / "control"
        invoke(self.project, "init", {"name": "Synthetic contract review"})
        invoke(self.project, "task", {"task_id": "forms"})

    def tearDown(self):
        self.temp.cleanup()

    def repository(self, name):
        path = self.root / name
        path.mkdir()
        git(path, "init", "-b", "main")
        git(path, "config", "user.name", "Synthetic Reviewer")
        git(path, "config", "user.email", "reviewer@example.invalid")
        (path / "form.txt").write_text("draft\n", encoding="utf-8")
        git(path, "add", "--", "form.txt")
        git(path, "commit", "-m", "Synthetic starting point")
        return path

    def test_non_object_arguments_are_rejected_even_when_falsy(self):
        for arguments in ([], "", 0, False):
            with self.subTest(arguments=arguments):
                with self.assertRaises(GovernanceError) as raised:
                    invoke(self.project, "status", arguments)
                self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")

    def test_bad_initialization_name_does_not_create_state(self):
        target = self.root / "invalid-control"
        with self.assertRaises(GovernanceError) as raised:
            invoke(target, "init", {"name": {"unexpected": "object"}})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")
        self.assertFalse((target / ".taskcarry").exists())

    def test_registered_workspace_checkpoint_uses_exact_registered_path(self):
        work = self.repository("worker")
        invoke(self.project, "workspace", {"name": "worker", "path": str(work)})
        content = "saved but undelivered\n"
        (work / "form.txt").write_bytes(content.encode("utf-8"))
        result = invoke(self.project, "checkpoint", {"task_id": "forms", "workspace": "worker", "paths": ["form.txt"], "next_step": "Review field labels", "paused": True})
        self.assertEqual(Path(result["workspace"]), work.resolve())
        self.assertEqual(result["files"][0]["worktree"]["sha256"], hashlib.sha256(content.encode()).hexdigest())
        status = invoke(self.project, "status")
        self.assertEqual(status["stages"], [])
        self.assertEqual(status["tasks"][0]["state"], "paused")

    def test_string_pause_is_rejected_before_checkpoint_or_task_change(self):
        work = self.repository("worker")
        invoke(self.project, "workspace", {"name": "worker", "path": str(work)})
        with self.assertRaises(GovernanceError) as raised:
            invoke(self.project, "checkpoint", {"task_id": "forms", "workspace": "worker", "paths": ["form.txt"], "next_step": "Continue", "paused": "false"})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")
        status = invoke(self.project, "status")
        self.assertEqual(status["checkpoints"], [])
        self.assertEqual(status["tasks"][0]["state"], "active")

    def test_string_enabled_does_not_store_an_enabled_rule(self):
        with self.assertRaises(GovernanceError) as raised:
            invoke(self.project, "experience", {"rule_id": "bad-rule", "code": "STALE_PLAN", "operation": "reconcile", "action": "refresh_plan", "enabled": "false"})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")
        self.assertIsNone(Core(self.project).store.get("experience", "bad-rule"))

    def test_string_execute_cannot_advance_a_real_baseline(self):
        baseline = self.repository("baseline")
        start = out(baseline, "rev-parse", "HEAD")
        worker = self.root / "worker"
        git(self.root, "clone", "--no-hardlinks", str(baseline), str(worker))
        git(worker, "config", "user.name", "Synthetic Worker")
        git(worker, "config", "user.email", "worker@example.invalid")
        (worker / "form.txt").write_text("stable revision\n", encoding="utf-8")
        git(worker, "add", "--", "form.txt")
        git(worker, "commit", "-m", "Synthetic stable stage")
        for name, path in (("baseline", baseline), ("worker", worker)):
            invoke(self.project, "workspace", {"name": name, "path": str(path)})
        invoke(self.project, "submit", {"task_id": "forms", "workspace": "worker", "commit": out(worker, "rev-parse", "HEAD"), "base": start, "paths": ["form.txt"], "stage_id": "forms-v1"})
        plan = invoke(self.project, "reconcile", {"baseline": "baseline"})["plan"]
        with self.assertRaises(GovernanceError) as raised:
            invoke(self.project, "reconcile", {"baseline": "baseline", "plan_id": plan["plan_id"], "execute": "false"})
        self.assertEqual(raised.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(out(baseline, "rev-parse", "HEAD"), start)
        self.assertEqual((baseline / "form.txt").read_text(encoding="utf-8"), "draft\n")
        result = invoke(self.project, "reconcile", {"baseline": "baseline", "plan_id": plan["plan_id"], "execute": True})
        self.assertNotEqual(out(baseline, "rev-parse", "HEAD"), start)
        self.assertEqual((baseline / "form.txt").read_text(encoding="utf-8"), "stable revision\n")


@unittest.skipUnless(os.environ.get("TASKCARRY_TEST_WHEEL"), "Set TASKCARRY_TEST_WHEEL to verify the actual built wheel")
class InstalledWheelContractTests(unittest.TestCase):
    def test_wheel_installs_four_skills_and_launches_project_bound_mcp(self):
        wheel = Path(os.environ["TASKCARRY_TEST_WHEEL"]).resolve()
        self.assertTrue(wheel.is_file(), str(wheel))
        with tempfile.TemporaryDirectory(prefix="taskcarry-wheel-") as temporary:
            root = Path(temporary)
            installed = root / "installed"
            project = root / "synthetic-project 合成"
            project.mkdir()
            process = subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--target", str(installed), str(wheel)], capture_output=True, text=True, encoding="utf-8", timeout=90)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            environment = os.environ.copy()
            environment.update(PYTHONPATH=str(installed), PYTHONUTF8="1")
            base = [sys.executable, "-m", "taskcarry", "--project", str(project)]
            for arguments in (["init"], ["setup", "--json", '{"mode":"install"}']):
                process = subprocess.run(base + arguments, capture_output=True, text=True, encoding="utf-8", cwd=root, env=environment, timeout=20)
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                self.assertTrue(json.loads(process.stdout)["ok"])
            skill_files = list((project / ".agents/skills").glob("*/SKILL.md"))
            self.assertEqual(len(skill_files), 4)
            for skill in skill_files:
                self.assertTrue(skill.read_text(encoding="utf-8").startswith("---\nname: taskcarry-"))
            config = tomllib.loads((project / ".taskcarry/codex.mcp.toml").read_text(encoding="utf-8"))["mcp_servers"]["taskcarry"]
            self.assertEqual(config["args"][:3], ["-I", "-X", "utf8"])
            self.assertNotIn("PYTHONPATH", config.get("env", {}))
            repository = Path(__file__).resolve().parents[1]
            # Same interpreter and installed path, but the old ordinary launch
            # selects cwd source. This demonstrates why wheel version alone
            # cannot establish which implementation a self-host uses.
            process = subprocess.run(
                [sys.executable, "-c", "import taskcarry; print(taskcarry.__file__)"],
                capture_output=True, text=True, encoding="utf-8", cwd=repository,
                env=environment, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(Path(process.stdout.strip()).parent, repository / "taskcarry")
            environment.update(PYTHONPATH=str(repository), PYTHONUTF8="0", PYTHONIOENCODING="ascii")
            frames = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "wheel-contract", "version": "1"}}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "taskcarry_status"}},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "taskcarry_agenda", "arguments": {"limit": 1}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "taskcarry_doctor"}},
                {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "taskcarry_task", "arguments": {"task_id": "wheel-unicode", "title": "合成检查 ✓"}}},
            ]
            for cwd in (root, repository):
                with self.subTest(cwd=cwd.name):
                    process = subprocess.run([config["command"], *config["args"]], input="\n".join(json.dumps(frame, ensure_ascii=False) for frame in frames) + "\n", text=True, encoding="utf-8", capture_output=True, cwd=cwd, env=environment, timeout=20)
                    self.assertEqual(process.returncode, 0, process.stderr)
                    replies = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertFalse(replies[1]["result"]["isError"])
                    self.assertIn("tasks", replies[1]["result"]["structuredContent"]["result"])
                    agenda = replies[2]["result"]["structuredContent"]["result"]
                    self.assertTrue(agenda["selection_only"])
                    self.assertFalse(agenda["effects_executed"])
                    self.assertEqual(agenda["total"], 0)
                    runtime = replies[3]["result"]["structuredContent"]["result"]["runtime"]
                    self.assertEqual(runtime["setup_status"], "installed")
                    self.assertEqual(Path(runtime["loaded_runtime"]["module_root"]), installed / "taskcarry")
                    self.assertTrue(runtime["managed_runtime_matches_disk"])
                    self.assertFalse(runtime["loaded_code_verified"])
                    self.assertEqual(replies[4]["result"]["structuredContent"]["result"]["title"], "合成检查 ✓")


@unittest.skipUnless(os.environ.get("TASKCARRY_TEST_SOURCE_BUILD") == "1", "Opt in to the independent source build with TASKCARRY_TEST_SOURCE_BUILD=1")
class StandardSourceBuildTests(unittest.TestCase):
    def test_plain_checkout_wheel_and_sdist_include_canonical_skills(self):
        """Exercise setuptools directly: the release ZIP builder is not involved."""
        repository = Path(__file__).resolve().parents[1]
        names = {"taskcarry-project-setup", "taskcarry-task-delivery", "taskcarry-governance-reconcile", "taskcarry-experience-recovery"}
        with tempfile.TemporaryDirectory(prefix="taskcarry-source-build-") as temporary:
            root = Path(temporary)
            source, output = root / "checkout", root / "artifacts"
            source.mkdir()
            output.mkdir()
            for name in ("pyproject.toml", "setup.py", "README.md", "LICENSE", "LICENSE_SCOPE.md"):
                (source / name).write_bytes((repository / name).read_bytes())
            for package_file in (repository / "taskcarry").glob("*.py"):
                target = source / "taskcarry" / package_file.name
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(package_file.read_bytes())
            for name in names:
                relative = Path("skills") / name / "SKILL.md"
                target = source / relative
                target.parent.mkdir(parents=True)
                target.write_bytes((repository / relative).read_bytes())
            self.assertFalse((source / "taskcarry/skill_data").exists())
            process = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "--wheel-dir", str(output), str(source)], capture_output=True, text=True, encoding="utf-8", timeout=180)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            wheels = list(output.glob("*.whl"))
            self.assertEqual(len(wheels), 1)
            with zipfile.ZipFile(wheels[0]) as wheel:
                packaged = {name for name in wheel.namelist() if name.startswith("taskcarry/skill_data/") and name.endswith("/SKILL.md")}
                self.assertEqual(packaged, {f"taskcarry/skill_data/{name}/SKILL.md" for name in names})
                for name in names:
                    self.assertEqual(wheel.read(f"taskcarry/skill_data/{name}/SKILL.md"), (source / "skills" / name / "SKILL.md").read_bytes())
            self.assertFalse((source / "taskcarry/skill_data").exists(), "Build must not generate duplicate source resources")
            # Verify the sdist retains those same canonical assets for downstream builds.
            process = subprocess.run([sys.executable, "-c", "import sys; from setuptools.build_meta import build_sdist; build_sdist(sys.argv[1])", str(output)], capture_output=True, text=True, encoding="utf-8", cwd=source, timeout=90)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            archives = list(output.glob("*.tar.gz"))
            self.assertEqual(len(archives), 1)
            with tarfile.open(archives[0], "r:gz") as archive:
                members = archive.getnames()
                for name in names:
                    matches = [member for member in members if member.endswith(f"/skills/{name}/SKILL.md")]
                    self.assertEqual(len(matches), 1, name)
                    self.assertEqual(archive.extractfile(matches[0]).read(), (source / "skills" / name / "SKILL.md").read_bytes())
            self.assertFalse((source / "taskcarry/skill_data").exists())


if __name__ == "__main__":
    unittest.main()
