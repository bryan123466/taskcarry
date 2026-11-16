"""Observable shared-engine replay of the public synthetic drone case."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from taskcarry.api import invoke
from taskcarry.core import Core
from taskcarry.project_recovery import ProjectRecovery
from taskcarry.recovery_git import git
from taskcarry.store import GovernanceError
import taskcarry.workbench as workbench


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vision_drone_example", ROOT / "examples/vision-drone-governance/replay.py")
EXAMPLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXAMPLE)


@unittest.skipUnless(shutil.which("git"), "Synthetic Git/recovery example requires Git")
class VisionDroneGovernanceTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get("TASKCARRY_EXAMPLE_SANDBOX", str(ROOT / "validation/local/drone-example-tests")))
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-", dir=base)
        self.root = Path(self.temp.name) / "case"
        self.example = EXAMPLE.DroneExample(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def ready(self):
        self.example.prepare()
        plan = self.example.scope_change_plan()
        self.assertEqual("COMPLETED", self.example.execute_scope_change(plan["plan_id"])["status"])
        self.example.finish_scope_change(plan["plan_id"])
        return plan

    def test_plan_is_read_only_and_existing_user_data_is_refused(self):
        result = EXAMPLE.plan(self.root)
        self.assertFalse(result["effects_executed"])
        self.assertFalse(self.root.exists())
        self.root.mkdir()
        (self.root / "user-work.md").write_text("Keep this work.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "absent or empty"):
            self.example.prepare()
        self.assertEqual("Keep this work.", (self.root / "user-work.md").read_text(encoding="utf-8"))
        self.assertFalse(self.example.control.exists())

    def assert_junction_rejected_without_new_pathlib_api(self, missing_leaf=False):
        external = Path(self.temp.name) / "external-empty"
        external.mkdir()
        quote = lambda path: "'" + str(path).replace("'", "''") + "'"
        command = ("New-Item -ItemType Junction -Path " + quote(self.root) +
                   " -Target " + quote(external) + " | Out-Null")
        created = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(0, created.returncode, created.stderr)
        self.assertTrue(self.root.lstat().st_file_attributes & 0x400)
        self.assertEqual(external.resolve(), self.root.resolve())
        self.assertEqual([], list(external.iterdir()))
        destination = self.root / "not-created" if missing_leaf else self.root
        # Python 3.11 lacks Path.is_junction. Remove it on newer interpreters so
        # the actual Windows reparse-point case exercises that supported floor.
        absent = object()
        method = Path.__dict__.get("is_junction", absent)
        try:
            if method is not absent:
                delattr(Path, "is_junction")
            self.assertFalse(hasattr(destination, "is_junction"))
            with self.assertRaisesRegex(ValueError, "without links or junctions"):
                EXAMPLE.plan(destination)
            with self.assertRaisesRegex(ValueError, "without links or junctions"):
                EXAMPLE.DroneExample(destination).prepare()
        finally:
            if method is not absent:
                setattr(Path, "is_junction", method)
        self.assertEqual([], list(external.iterdir()))
        self.assertFalse((external / "TaskCarry").exists())
        self.assertFalse((external / "not-created").exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_actual_junction_destination_rejected_before_writes_without_python312_api(self):
        self.assert_junction_rejected_without_new_pathlib_api()

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_actual_junction_ancestor_rejected_before_missing_leaf_is_created(self):
        self.assert_junction_rejected_without_new_pathlib_api(missing_leaf=True)

    def test_scope_change_retains_original_tasks_history_checkpoints_and_four_bindings(self):
        self.example.prepare()
        before = {row["task_id"]: row for row in self.example.call("status")["tasks"]}
        plan = self.example.scope_change_plan()
        # Planning freezes the intended entries but does not publish any of them.
        self.assertFalse(plan["effects_executed"])
        self.assertFalse((self.example.workspace("software") / ".local/CURRENT.md").exists())
        result = self.example.execute_scope_change(plan["plan_id"])
        self.assertEqual("COMPLETED", result["status"])
        self.example.finish_scope_change(plan["plan_id"])
        after = {row["task_id"]: row for row in self.example.call("status")["tasks"]}
        for window in self.example.spec["existing_windows"]:
            task_id = window["task_id"]
            self.assertEqual(before[task_id]["created_at"], after[task_id]["created_at"])
            self.assertNotEqual(before[task_id]["latest_checkpoint"], after[task_id]["latest_checkpoint"])
            old = Core(self.example.control).store.get("checkpoints", before[task_id]["latest_checkpoint"])
            self.assertEqual(task_id, old["task_id"])
            self.assertEqual(window["next_step"], old["next_step"])
            self.assertIn("Unfinished professional draft", (self.example.workspace(window["workspace"]) / "DRAFT.md").read_text(encoding="utf-8"))
        self.assertEqual("paused", after["drone-outdoor-evaluation"]["state"])
        history = self.example.call("facts", action="history", source_id=self.example.spec["source_id"], fact_id="first-milestone")["items"]
        self.assertEqual([1, 2], [fact["revision"] for fact in history])
        self.assertEqual(self.example.spec["scope_initial"], history[0]["statement"])
        self.assertEqual(self.example.spec["scope_current"], history[1]["statement"])
        original_decision = self.example.call("facts", action="get", source_id=self.example.spec["source_id"], fact_id="frame-identity")["fact"]
        self.assertEqual(1, original_decision["revision"])
        entries = self.example.call("workbench", action="status")["items"]
        self.assertEqual(4, len(entries))
        for entry in entries:
            self.assertEqual(plan["view_id"], entry["view_id"])
            self.assertEqual("PUBLISHED", entry["state"])
            self.assertEqual("NOT_VERIFIED", entry["consumer_state"])
            self.assertFalse(entry["native_acceptance_verified"])
        self.assertIn(self.example.spec["scope_current"].encode(), git(self.example.control, "show", "HEAD:PROJECT.md"))

    def test_partial_publication_resumes_exact_plan_without_touching_professional_wip(self):
        self.example.prepare()
        root = self.example.workspace("software")
        (root / "DRAFT.md").write_text("Staged professional work.\n", encoding="utf-8")
        git(root, "add", "--", "DRAFT.md")
        (root / "DRAFT.md").write_text("Later unstaged professional work.\n", encoding="utf-8")
        before_index = git(root, "ls-files", "--stage", "-z")
        before_head = git(root, "rev-parse", "HEAD")
        plan = self.example.scope_change_plan()
        real_write = workbench.atomic_write
        failed = False

        def interrupted(path, content):
            nonlocal failed
            if Path(path) == self.example.workspace("algorithm") / ".local/CURRENT.md" and not failed:
                failed = True
                raise OSError("Synthetic interruption before this target write")
            return real_write(path, content)

        with mock.patch.object(workbench, "atomic_write", side_effect=interrupted):
            partial = self.example.execute_scope_change(plan["plan_id"])
        self.assertEqual("PARTIAL", partial["status"])
        self.assertEqual(3, sum(item["status"] == "PUBLISHED" for item in partial["results"]))
        # A reopened orchestrator uses the same plan; it never reinitializes the project.
        reopened = EXAMPLE.DroneExample(self.root)
        repaired = reopened.execute_scope_change(plan["plan_id"])
        self.assertEqual("COMPLETED", repaired["status"])
        repeated = reopened.execute_scope_change(plan["plan_id"])
        self.assertEqual(repaired["results"], repeated["results"])
        self.assertEqual(before_index, git(root, "ls-files", "--stage", "-z"))
        self.assertEqual(before_head, git(root, "rev-parse", "HEAD"))
        self.assertEqual("Later unstaged professional work.\n", (root / "DRAFT.md").read_text(encoding="utf-8"))
        self.assertEqual(4, len(Core(self.example.control).store.list("workbench_receipts")))

    def test_restore_recovers_actual_effect_before_missing_receipt_and_remains_standby(self):
        self.ready()
        before = {row["task_id"]: row for row in self.example.call("status")["tasks"]}
        backup = self.example.backup()
        controller, plan = self.example.restore_plan(backup)
        with mock.patch.object(ProjectRecovery, "_receipt", side_effect=OSError("Synthetic missing final receipt")):
            with self.assertRaisesRegex(OSError, "missing final receipt"):
                controller.recovery("restore_execute", plan_id=plan["plan_id"])
        self.assertTrue((self.root / "standby/control/PROJECT.md").is_file())
        reopened = ProjectRecovery(self.root / "restore-controller")
        restored = reopened.recovery("restore_execute", plan_id=plan["plan_id"])
        self.assertEqual("RESTORED_STANDBY", restored["state"])
        self.assertTrue(restored["recovered_existing_effect"])
        self.assertFalse(restored["old_plans_replayed"])
        self.assertFalse(restored["native_host_verified"])
        self.assertFalse(restored["writer_activated"])
        target = self.root / "standby/control"
        after = {row["task_id"]: row for row in invoke(target, "status")["tasks"]}
        self.assertEqual(set(before), set(after))
        for task_id in before:
            self.assertEqual(before[task_id].get("latest_checkpoint"), after[task_id].get("latest_checkpoint"))
        for window in self.example.windows:
            source = self.example.workspace(window["workspace"])
            copy = self.root / "standby/workspaces" / window["workspace"]
            self.assertEqual(git(source, "rev-parse", "HEAD"), git(copy, "rev-parse", "HEAD"))
            self.assertEqual((source / "SOURCE_NOTES.md").read_bytes(), (copy / "SOURCE_NOTES.md").read_bytes())
        with self.assertRaises(GovernanceError):
            invoke(target, "task", {"task_id": "drone-software", "state": "complete"})

    def test_replay_report_separates_local_governance_effects_from_native_or_flight_claims(self):
        report = self.example.run()
        disk = json.loads((self.root / "REPLAY_REPORT.json").read_text(encoding="utf-8"))
        self.assertEqual(report, disk)
        self.assertEqual(4, report["published_workbenches"])
        self.assertEqual(2, report["scope_revision"])
        self.assertEqual("RESTORED_STANDBY", report["recovery_state"])
        self.assertFalse(report["native_host_verified"])
        self.assertFalse(report["natural_schedule_verified"])
        self.assertFalse(report["actual_aircraft_or_model_verified"])
        self.assertNotIn(str(self.root), json.dumps(report))


if __name__ == "__main__":
    unittest.main()
