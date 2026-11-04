"""Workbench connection materials preserve one control and existing host files."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from taskcarry import setup
from taskcarry.core import Core
from taskcarry.integration import Integration


class WorkbenchSetupTests(unittest.TestCase):
    def setUp(self):
        sandbox = Path(__file__).resolve().parents[1] / "validation/local/setup-workbench-tests"
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-", dir=sandbox)
        self.base = Path(self.temporary.name).resolve()
        self.control = self.base / "control"
        self.control.mkdir()
        Core.initialize(self.control, name="Synthetic project")
        self.core = Core(self.control)
        self.worker = self.make_worker("worker-one", "task-one")
        self.arguments = {"target": str(self.worker), "workspace": "worker-one", "task_id": "task-one"}

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, target, *args):
        return subprocess.run(["git", "-C", str(target), *args], check=True, capture_output=True,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout

    def make_worker(self, name, task):
        target = self.base / name
        target.mkdir()
        self.git(target, "init", "-b", "main")
        self.git(target, "config", "user.name", "Synthetic User")
        self.git(target, "config", "user.email", "synthetic@example.invalid")
        (target / "README.md").write_text("Synthetic initial content\n", encoding="utf-8")
        (target / ".gitignore").write_text(".taskcarry/\n.agents/\n", encoding="utf-8")
        self.git(target, "add", ".")
        self.git(target, "commit", "-m", "Synthetic baseline")
        Integration(self.control).workspace(name, str(target))
        self.core.task(task, title="Synthetic task")
        return target

    def configure(self, mode="preview", **changes):
        return setup.configure(self.control, mode=mode, **dict(self.arguments, **changes))

    @staticmethod
    def snapshot(root):
        # SQLite may create coordination caches even for mode=ro readers. The
        # database file plus observable records/events are checked separately.
        return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in root.rglob("*") if p.is_file() and p.name not in {"state.sqlite3-shm", "state.sqlite3-wal"}}

    def governance_state(self):
        return self.core.status(), self.core.store.events()

    def test_preview_is_read_only_and_identifies_separate_control(self):
        records = self.governance_state()
        before = self.snapshot(self.base)
        result = self.configure()
        self.assertEqual(result["control"], str(self.control))
        self.assertEqual(result["target"], str(self.worker))
        self.assertEqual(result["workspace"], "worker-one")
        self.assertEqual(result["task_id"], "task-one")
        self.assertTrue(result["registration_verified"])
        self.assertEqual(result["connection_state"], {"materials": "preview", "host_loading": "not_verified", "native_acceptance": "not_verified"})
        self.assertEqual(before, self.snapshot(self.base))
        self.assertEqual(records, self.governance_state())

    def test_two_workbenches_share_control_without_new_databases(self):
        second = self.make_worker("worker-two", "task-two")
        records = self.governance_state()
        before = self.snapshot(self.control)
        for target, workspace, task in ((self.worker, "worker-one", "task-one"), (second, "worker-two", "task-two")):
            result = self.configure("install", target=str(target), workspace=workspace, task_id=task)
            fragment = tomllib.loads((target / ".taskcarry/codex.mcp.toml").read_text(encoding="utf-8"))["mcp_servers"]["taskcarry"]
            self.assertEqual(fragment["command"], setup.sys.executable)
            self.assertEqual(fragment["args"][:3], ["-I", "-X", "utf8"])
            self.assertEqual(fragment["args"][-3:], ["--project", str(self.control), "mcp"])
            binding = json.loads((target / ".taskcarry/workbench.json").read_text(encoding="utf-8"))
            self.assertEqual(binding["control"], str(self.control))
            self.assertEqual(binding["workspace"], workspace)
            self.assertEqual(binding["task_id"], task)
            self.assertEqual(len(list((target / ".agents/skills").glob("*/SKILL.md"))), 4)
            self.assertFalse((target / ".taskcarry/state.sqlite3").exists())
            self.assertFalse(result["host_loading_verified"])
            self.assertFalse(result["native_acceptance_verified"])
            diagnostic = setup.runtime_info(target)
            self.assertEqual(diagnostic["control"], str(self.control))
            self.assertTrue(diagnostic["generated_files_match"])
        self.assertEqual(before, self.snapshot(self.control))
        self.assertEqual(records, self.governance_state())

    def test_install_and_repeat_preserve_live_configuration_agents_and_git_wip(self):
        config = self.worker / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[mcp_servers.user_service]\ncommand = "user-owned"\n', encoding="utf-8")
        agents = self.worker / "AGENTS.md"
        agents.write_text("User project instructions\n", encoding="utf-8")
        (self.worker / "README.md").write_text("Staged user revision\n", encoding="utf-8")
        self.git(self.worker, "add", "README.md")
        (self.worker / "README.md").write_text("Unstaged user revision\n", encoding="utf-8")
        user_files = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (config, agents, self.worker / "README.md", self.worker / ".git/index")}
        status = self.git(self.worker, "status", "--porcelain=v1", "-z")
        self.configure("install")
        self.assertEqual(status, self.git(self.worker, "status", "--porcelain=v1", "-z"))
        installed = self.snapshot(self.worker)
        repeated = self.configure("install")
        self.assertEqual(repeated["files_written"], 0)
        self.assertFalse(repeated["manifest_written"])
        self.assertEqual(installed, self.snapshot(self.worker))
        self.assertEqual(user_files, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in user_files})

    def test_public_reference_is_installed_and_user_changes_are_preserved(self):
        self.configure("install")
        relative = ".agents/skills/taskcarry-project-setup/references/onboarding.md"
        path = self.worker / relative
        self.assertEqual(path.read_bytes(), setup.skill_files()[relative])
        path.write_text("User reference addition\n", encoding="utf-8")
        before = self.snapshot(self.worker)
        preview = self.configure()
        self.assertIn({"path": relative, "reason": "unmanaged_or_modified"}, preview["conflicts"])
        with self.assertRaises(setup.SetupError) as failure:
            self.configure("install")
        self.assertEqual(failure.exception.code, "SETUP_CONFLICT")
        self.assertEqual(before, self.snapshot(self.worker))
        result = self.configure("uninstall")
        self.assertIn(relative, result["preserved_modified"])
        self.assertEqual(path.read_text(encoding="utf-8"), "User reference addition\n")
        self.assertFalse((self.worker / ".taskcarry/workbench.json").exists())

    def test_legacy_manifest_upgrades_without_new_installation_identity(self):
        setup.configure(self.worker, mode="install")
        path = self.worker / ".taskcarry/setup-manifest.json"
        before = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("binding", before)
        self.configure("install")
        after = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(after["format"], 1)
        self.assertEqual(after["installation_id"], before["installation_id"])
        self.assertEqual(after["binding"]["control"], str(self.control))
        self.assertEqual(after["binding"]["target"], str(self.worker))

    def test_existing_binding_cannot_silently_change_task_or_become_default_setup(self):
        self.configure("install")
        self.core.task("another-task")
        before = self.snapshot(self.worker)
        for invocation in (lambda: self.configure("install", task_id="another-task"),
                           lambda: setup.configure(self.worker, mode="install")):
            with self.assertRaises(setup.SetupError) as failure:
                invocation()
            self.assertEqual(failure.exception.code, "SETUP_BINDING_CONFLICT")
        self.assertEqual(before, self.snapshot(self.worker))

    def test_another_control_cannot_rebind_workbench_identity(self):
        self.configure("install")
        other = self.base / "other-control"
        Core.initialize(other, name="Other synthetic project")
        Core(other).task("task-one")
        Integration(other).workspace("worker-one", str(self.worker))
        before = self.snapshot(self.worker)
        with self.assertRaises(setup.SetupError) as failure:
            setup.configure(other, mode="install", **self.arguments)
        self.assertEqual(failure.exception.code, "SETUP_BINDING_CONFLICT")
        self.assertEqual(before, self.snapshot(self.worker))

    def test_missing_identity_registration_or_path_mismatch_never_initializes_target(self):
        fresh = self.base / "fresh-target"
        fresh.mkdir()
        cases = [({"workspace": None}, "SETUP_BINDING_REQUIRED"),
                 ({"task_id": "missing-task"}, "SETUP_TASK_UNKNOWN"),
                 ({"workspace": "missing-worker"}, "WORKSPACE_UNKNOWN"),
                 ({"target": str(fresh)}, "SETUP_WORKSPACE_MISMATCH")]
        records = self.governance_state()
        before = self.snapshot(self.base)
        for changes, expected in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(setup.SetupError) as failure:
                    self.configure("install", **changes)
                self.assertEqual(failure.exception.code, expected)
        with self.assertRaises(setup.SetupError) as failure:
            setup.configure(fresh, mode="install", **self.arguments)
        self.assertEqual(failure.exception.code, "NOT_INITIALIZED")
        self.assertEqual(before, self.snapshot(self.base))
        self.assertEqual(records, self.governance_state())

    def test_changed_registered_branch_is_rejected_before_setup_writes(self):
        self.git(self.worker, "checkout", "-b", "unregistered-branch")
        before = self.snapshot(self.worker)
        with self.assertRaises(setup.SetupError) as failure:
            self.configure("install")
        self.assertEqual(failure.exception.code, "WORKSPACE_CHANGED")
        self.assertEqual(before, self.snapshot(self.worker))

    def test_an_existing_separate_control_cannot_be_used_as_target(self):
        Core.initialize(self.worker, name="Separate governance")
        before = self.snapshot(self.worker)
        with self.assertRaises(setup.SetupError) as failure:
            self.configure("install")
        self.assertEqual(failure.exception.code, "SETUP_CONTROL_CONFLICT")
        self.assertEqual(before, self.snapshot(self.worker))

    def interrupt_install(self):
        original = setup.atomic_write
        target = self.worker / ".taskcarry/workbench.json"

        def interrupted(path, content):
            original(path, content)
            if path == target:
                raise RuntimeError("Synthetic interruption after binding file")

        with patch.object(setup, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, "Synthetic interruption"):
                self.configure("install")
        return target

    def test_interrupted_workbench_install_resumes_without_rewriting_completed_files(self):
        target = self.interrupt_install()
        before = (target.read_bytes(), target.stat().st_mtime_ns)
        self.assertTrue(self.configure()["pending_installation"])
        diagnostic = setup.runtime_info(self.worker)
        self.assertEqual(diagnostic["setup_status"], "pending")
        self.assertEqual(diagnostic["control"], str(self.control))
        self.assertTrue(diagnostic["pending_source_matches_disk"])
        resumed = self.configure("install")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["files_written"], 1)
        self.assertEqual(before, (target.read_bytes(), target.stat().st_mtime_ns))
        self.assertFalse((self.worker / ".taskcarry/setup-intent.json").exists())

    def test_user_revision_after_interruption_is_not_overwritten_or_adopted(self):
        target = self.interrupt_install()
        target.write_text("User correction to generated binding\n", encoding="utf-8")
        before = self.snapshot(self.worker)
        with self.assertRaises(setup.SetupError) as failure:
            self.configure("install")
        self.assertEqual(failure.exception.code, "SETUP_CONFLICT")
        self.assertEqual(before, self.snapshot(self.worker))

    def test_branch_change_during_install_leaves_intent_and_resumes_after_identity_is_restored(self):
        original = setup.atomic_write

        def change_branch(path, content):
            original(path, content)
            if path == self.worker / ".taskcarry/workbench.json":
                self.git(self.worker, "checkout", "-b", "changed-during-setup")

        with patch.object(setup, "atomic_write", side_effect=change_branch):
            with self.assertRaises(setup.SetupError) as failure:
                self.configure("install")
        self.assertEqual(failure.exception.code, "WORKSPACE_CHANGED")
        self.assertTrue((self.worker / ".taskcarry/setup-intent.json").exists())
        self.assertFalse((self.worker / ".taskcarry/setup-manifest.json").exists())
        self.git(self.worker, "checkout", "main")
        before = self.snapshot(self.worker)
        resumed = self.configure("install")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["files_written"], 0)
        for name, state in before.items():
            if name != ".taskcarry/setup-intent.json":
                self.assertEqual(self.snapshot(self.worker)[name], state)

    def test_reference_link_is_rejected_without_copying_external_content(self):
        public = self.base / "public-skills"
        sources = []
        for index in range(4):
            skill = public / f"taskcarry-synthetic-{index}"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("Public synthetic Skill\n", encoding="utf-8")
            sources.append(skill / "SKILL.md")
        reference = sources[0].parent / "references"
        outside = self.base / "outside-reference"
        outside.mkdir()
        (outside / "escape.md").write_text("Must not be copied\n", encoding="utf-8")
        try:
            reference.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            if os.name != "nt":
                raise
            subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(reference), str(outside)],
                           check=True, capture_output=True)
        before = self.snapshot(self.worker)
        with patch.object(setup, "skill_sources", return_value=sources):
            with self.assertRaises(setup.SetupError) as failure:
                self.configure("install")
        self.assertEqual(failure.exception.code, "SETUP_LINK")
        # The lock file is the only setup metadata allowed before validation.
        after = self.snapshot(self.worker)
        after.pop(".taskcarry/setup.lock", None)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
