"""Synthetic observable publication, preservation and interrupted-effect tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from taskcarry.core import Core
from taskcarry.integration import Integration
from taskcarry.store import GovernanceError
from taskcarry import workbench as wb


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        sandbox = Path(__file__).resolve().parents[1] / "validation/local/workbench-tests"
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-", dir=sandbox)
        self.base = Path(self.temporary.name).resolve()
        self.control = self.base / "control"
        self.control.mkdir()
        Core.initialize(self.control, name="Synthetic publication")
        self.engine = wb.Workbench(self.control)
        self.worker = self.make_worker("one")
        self.view = self.freeze()

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout

    def make_worker(self, name):
        root = self.base / name
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Synthetic User")
        self.git(root, "config", "user.email", "synthetic@example.invalid")
        (root / ".gitignore").write_text(".local/\n.codex/\n.taskcarry/\n.agents/\n", encoding="utf-8")
        (root / "business.txt").write_text("committed\n", encoding="utf-8")
        self.git(root, "add", ".gitignore", "business.txt")
        self.git(root, "commit", "-m", "Synthetic baseline")
        Integration(self.control).workspace(name, str(root))
        self.engine.task("task-" + name, title="Synthetic work")
        return root

    def freeze(self, body="# Current\nSynthetic governance view\n", sources=None):
        return self.engine.workbench("freeze", body=body, sources=sources or [{"source_id": "synthetic-rules", "revision": "r1"}])

    def target(self, name="one", host="none", **changes):
        result = {"workspace": name, "task_id": "task-" + name, "thread_id": "thread-" + name,
                  "host": host, "code_assessment": {"status": "NO_CODE_DEPENDENCY", "reason": "Navigation only; no code required."},
                  "writes": [{"path": ".local/CURRENT.md", "text": "Read the published synthetic view."}]}
        result.update(changes)
        return result

    def plan(self, targets=None, view=None):
        return self.engine.workbench("plan", view_id=(view or self.view)["view_id"], targets=targets or [self.target()])

    def execute(self, plan):
        return self.engine.workbench("execute", plan_id=plan["plan_id"])

    def current(self, name="one"):
        return self.engine.workbench("status", workspace=name)["items"][0]

    def proof(self, plan, view=None):
        evidence = self.control / "synthetic-evidence.json"
        evidence.write_text('{"fixture":"synthetic read, not actual host loading"}\n', encoding="utf-8")
        return {"workspace": "one", "task_id": "task-one", "source_id": self.engine.source()["source_id"],
                "plan_id": plan["plan_id"], "view_id": (view or self.view)["view_id"], "thread_id": "thread-one", "turn_id": "turn-one",
                "evidence_path": "synthetic-evidence.json", "evidence_sha256": wb.digest_bytes(evidence.read_bytes()),
                "reviewer": "synthetic reviewer", "observed_at": "2026-01-01T00:00:00Z"}

    def test_freeze_deduplicates_and_requires_provenance(self):
        repeated = self.freeze()
        self.assertEqual(repeated["view_id"], self.view["view_id"])
        self.assertFalse(repeated["created"])
        with self.assertRaises(GovernanceError):
            self.engine.workbench("freeze", body="x", sources=[])

    def test_view_tamper_and_future_schema_are_refused(self):
        Path(self.view["view_path"]).write_text("changed", encoding="utf-8")
        with self.assertRaises(GovernanceError):
            self.plan()

    def test_preserves_head_index_business_wip_and_professional_section(self):
        business = self.worker / "business.txt"
        business.write_text("staged\n", encoding="utf-8")
        self.git(self.worker, "add", "business.txt")
        business.write_text("unstaged\n", encoding="utf-8")
        entry = self.worker / ".local/CURRENT.md"
        entry.parent.mkdir()
        entry.write_bytes(b"Professional text\r\n<!-- taskcarry:navigation:begin -->\r\nold\r\n<!-- taskcarry:navigation:end -->\r\nTail\r\n")
        before = wb.git_snapshot(self.worker)
        plan = self.plan()
        self.assertIn(b"old", entry.read_bytes())
        self.assertEqual(self.execute(plan)["status"], "COMPLETED")
        self.assertEqual(before, wb.git_snapshot(self.worker))
        self.assertEqual(business.read_text(), "unstaged\n")
        self.assertTrue(entry.read_bytes().startswith(b"Professional text\r\n"))
        self.assertTrue(entry.read_bytes().endswith(b"Tail\r\n"))

    def test_effect_before_receipt_retry_only_finishes_missing_steps(self):
        plan = self.plan()
        real_write = wb.atomic_write
        def crash_after_effect(path, content):
            real_write(path, content)
            if path.name == "CURRENT.md":
                raise RuntimeError("synthetic process interruption")
        with patch.object(wb, "atomic_write", side_effect=crash_after_effect):
            with self.assertRaisesRegex(RuntimeError, "interruption"):
                self.execute(plan)
        entry = self.worker / ".local/CURRENT.md"
        before = (entry.read_bytes(), entry.stat().st_mtime_ns)
        self.assertEqual(self.execute(plan)["status"], "COMPLETED")
        self.assertEqual(before, (entry.read_bytes(), entry.stat().st_mtime_ns))
        receipts = self.engine.store.list("workbench_receipts")
        self.assertEqual(self.execute(plan)["status"], "COMPLETED")
        self.assertEqual(receipts, self.engine.store.list("workbench_receipts"))

    def test_partial_write_retries_remaining_file_and_preserves_modified_one(self):
        target = self.target(writes=[{"path": ".local/a.md", "text": "A"}, {"path": ".local/b.md", "text": "B"}])
        plan = self.plan([target])
        real_write = wb.atomic_write
        def error_second(path, content):
            if path.name == "b.md":
                raise PermissionError("synthetic disk denial")
            return real_write(path, content)
        with patch.object(wb, "atomic_write", side_effect=error_second):
            self.assertEqual(self.execute(plan)["results"][0]["status"], "IO_ERROR")
        self.assertTrue((self.worker / ".local/a.md").exists())
        (self.worker / ".local/a.md").write_text("later professional work", encoding="utf-8")
        self.assertEqual(self.execute(plan)["results"][0]["status"], "CONFLICT")
        self.assertFalse((self.worker / ".local/b.md").exists())
        self.assertEqual((self.worker / ".local/a.md").read_text(), "later professional work")

    def test_content_and_io_failures_are_isolated_per_workspace(self):
        second = self.make_worker("two")
        third = self.make_worker("three")
        plan = self.plan([self.target(), self.target("two"), self.target("three")])
        entry = self.worker / ".local/CURRENT.md"
        entry.parent.mkdir()
        entry.write_text("user work", encoding="utf-8")
        real_write = wb.atomic_write
        def deny_second(path, content):
            if path.is_relative_to(second):
                raise PermissionError("synthetic IO error")
            return real_write(path, content)
        with patch.object(wb, "atomic_write", side_effect=deny_second):
            result = self.execute(plan)
        self.assertEqual([r["status"] for r in result["results"]], ["CONFLICT", "IO_ERROR", "PUBLISHED"])
        self.assertTrue((third / ".local/CURRENT.md").is_file())
        self.assertEqual(entry.read_text(), "user work")

    def test_receipt_does_not_hide_later_target_drift(self):
        plan = self.plan()
        self.execute(plan)
        (self.worker / ".local/CURRENT.md").write_text("new user writing", encoding="utf-8")
        self.assertEqual(self.execute(plan)["status"], "PARTIAL")
        self.assertEqual(self.current()["state"], "ENTRY_CHANGED")

    def test_old_plan_never_regresses_a_new_view_with_same_entry_bytes(self):
        first = self.plan()
        self.execute(first)
        view = self.freeze(body="New revision")
        second = self.plan(view=view)
        self.execute(second)
        self.assertEqual(self.execute(first)["results"][0]["status"], "SUPERSEDED")
        self.assertEqual(self.current()["view_id"], view["view_id"])

    def test_index_or_head_changes_block_without_writing(self):
        plan = self.plan()
        (self.worker / "business.txt").write_text("new staged", encoding="utf-8")
        self.git(self.worker, "add", "business.txt")
        self.assertEqual(self.execute(plan)["status"], "PARTIAL")
        self.assertFalse((self.worker / ".local/CURRENT.md").exists())

    def test_tracked_and_unignored_targets_are_rejected(self):
        for path in ("business.txt", "unignored.md"):
            with self.subTest(path=path), self.assertRaises(GovernanceError):
                self.plan([self.target(writes=[{"path": path, "text": "private"}])])
        config = self.worker / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('model = "unchanged"\n', encoding="utf-8")
        self.git(self.worker, "add", "-f", ".codex/config.toml")
        with self.assertRaises(GovernanceError):
            self.plan([self.target(host="codex")])

    def test_unsafe_paths_and_duplicate_workspace_are_refused(self):
        for path in ("../escape", "/absolute", ".git/config", "x/../y", "C:" + "/escape", ".local/CON", ".local/x.", ".local\\x", ".local//x"):
            with self.subTest(path=path), self.assertRaises(GovernanceError):
                self.plan([self.target(writes=[{"path": path, "text": "x"}])])
        with self.assertRaises(GovernanceError):
            self.plan([self.target(), self.target()])

    def test_managed_markers_are_not_guessed_or_nested(self):
        for original in (b"<!-- taskcarry:x:begin -->", b"<!-- taskcarry:x:end -->\n<!-- taskcarry:x:begin -->",
                         b"prefix<!-- taskcarry:x:begin -->\nx\n<!-- taskcarry:x:end -->",
                         b"<!-- taskcarry:x:begin -->\n<!-- taskcarry:y:begin -->\n<!-- taskcarry:x:end -->"):
            with self.subTest(original=original), self.assertRaises(GovernanceError):
                wb.managed_section(original, "x", "new")

    def test_config_adapter_preserves_comments_tables_and_custom_instructions(self):
        config = self.worker / ".codex/config.toml"
        config.parent.mkdir()
        original = b'# user comment\r\ndeveloper_instructions = "Keep professional responsibility." # inline\r\nmodel = "existing"\r\n[mcp_servers.existing]\r\ncommand = "python"\r\n'
        config.write_bytes(original)
        first = self.plan([self.target(host="codex")])
        self.execute(first)
        updated = config.read_bytes()
        self.assertTrue(updated.startswith(b"# user comment\r\n"))
        self.assertTrue(updated.endswith(original[original.index(b" # inline"):]))
        self.assertIn("Keep professional responsibility.", tomllib.loads(updated.decode())["developer_instructions"])
        second = self.plan([self.target(host="codex")], view=self.freeze(body="Next view"))
        self.execute(second)
        final = tomllib.loads(config.read_text())
        self.assertEqual(final["model"], "existing")
        self.assertEqual(final["mcp_servers"], {"existing": {"command": "python"}})
        self.assertEqual(final["developer_instructions"].count("taskcarry:workbench-entry:begin"), 1)

    def test_config_first_add_preserves_original_bytes_and_multiline_values(self):
        for original in (b'# original\n[mcp_servers.example]\ncommand = "python"\n',
                         b'developer_instructions = """Professional\nmultiline text""" # retain\nmodel="m"\n',
                         b"'developer_instructions' = '''Professional\nliteral text'''\n# keep\n"):
            with self.subTest(original=original):
                updated = wb.codex_instructions(original, "Read current view")
                old, new = tomllib.loads(original.decode()), tomllib.loads(updated.decode())
                previous = old.pop("developer_instructions", "")
                self.assertIn(previous, new.pop("developer_instructions"))
                self.assertEqual(old, new)
                if "developer_instructions" not in tomllib.loads(original.decode()):
                    self.assertTrue(updated.endswith(original))

    def test_existing_connect_config_survives_and_intervening_change_conflicts(self):
        config = self.worker / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('# shared\n[mcp_servers.sample]\ncommand = "python"\nargs = ["-I"]\n', encoding="utf-8")
        plan = self.plan([self.target(host="codex")])
        original = config.read_bytes()
        config.write_bytes(original + b"# later connection change\n")
        self.assertEqual(self.execute(plan)["status"], "PARTIAL")
        self.assertEqual(config.read_bytes(), original + b"# later connection change\n")
        revised = self.plan([self.target(host="codex")])
        self.assertEqual(self.execute(revised)["status"], "COMPLETED")
        self.assertIn(b"# later connection change\n", config.read_bytes())

    def test_exact_writes_require_reviewed_original_hash(self):
        target = self.target(writes=[{"path": ".local/exact.md", "mode": "exact", "text": "x", "expected_sha256": "wrong"}])
        with self.assertRaises(GovernanceError):
            self.plan([target])
        target["writes"][0]["expected_sha256"] = None
        self.assertEqual(self.execute(self.plan([target]))["status"], "COMPLETED")

    def test_consumption_requires_exact_publication_and_real_evidence_hash(self):
        plan = self.plan()
        proof = self.proof(plan)
        with self.assertRaises(GovernanceError):
            self.engine.workbench("consume", proof=proof)
        self.execute(plan)
        for field, value in (("thread_id", "other"), ("task_id", "other"), ("source_id", "other"), ("evidence_sha256", "0" * 64)):
            with self.subTest(field=field), self.assertRaises(GovernanceError):
                self.engine.workbench("consume", proof=dict(proof, **{field: value}))
        result = self.engine.workbench("consume", proof=proof)
        self.assertFalse(result["native_acceptance_verified"])
        self.assertEqual(self.current()["consumer_state"], "REVIEWED_EVIDENCE_RECORDED")
        self.assertEqual(self.engine.store.list("workbench_receipts")[0]["consumer_state"], "NOT_VERIFIED")
        (self.control / proof["evidence_path"]).write_text("later changed evidence", encoding="utf-8")
        self.assertEqual(self.current()["consumer_state"], "EVIDENCE_CHANGED_OR_MISSING")

    def test_consumption_for_old_view_does_not_mark_new_view_consumed(self):
        first = self.plan()
        self.execute(first)
        self.engine.workbench("consume", proof=self.proof(first))
        second = self.plan(view=self.freeze(body="New view"))
        self.execute(second)
        self.assertEqual(self.current()["consumer_state"], "NOT_VERIFIED")
        self.assertEqual(len(self.engine.store.list("workbench_consumption")), 1)

    def test_source_revision_drift_is_visible_and_does_not_rewrite_view(self):
        source = self.control / "rules.md"
        source.write_text("one", encoding="utf-8")
        view = self.freeze(sources=[{"source_id": "rules", "revision": wb.digest_bytes(source.read_bytes()), "path": "rules.md"}])
        self.execute(self.plan(view=view))
        before = Path(view["view_path"]).read_bytes()
        source.write_text("two", encoding="utf-8")
        self.assertEqual(self.current()["source_freshness"][0]["state"], "CHANGED_OR_MISSING")
        self.assertEqual(before, Path(view["view_path"]).read_bytes())
        with self.assertRaises(GovernanceError):
            self.freeze(sources=[{"source_id": "rules", "revision": "old", "path": "rules.md"}])

    def test_record_sources_use_same_control_and_actual_revision(self):
        task = self.engine.store.get("tasks", "task-one")
        source = {"source_id": self.engine.source()["source_id"], "revision": wb.digest_bytes(wb.canonical(task)),
                  "collection": "tasks", "local_id": "task-one"}
        view = self.freeze(sources=[source])
        self.execute(self.plan(view=view))
        self.engine.task("task-one", title="Updated task")
        self.assertEqual(self.current()["source_freshness"][0]["state"], "CHANGED_OR_MISSING")
        with self.assertRaises(GovernanceError):
            self.freeze(sources=[dict(source, source_id="other-control")])

    def test_current_decision_cycle_and_registry_can_back_a_view(self):
        from taskcarry.governance_cycle import GovernanceCycle, _hash as source_hash
        cycle = GovernanceCycle(self.control)
        source_id = self.engine.source()["source_id"]
        arguments = {"fact_id": "booking-rule", "task_id": "task-one", "kind": "decision", "source_revision": "r1",
                     "statement": "Bookings require confirmation.", "evidence": {"reference": "synthetic-note", "summary": "Confirmed rule"},
                     "judgment": {"statement": "Retain the rule.", "basis": "Reviewed synthetic note"}}
        cycle.facts("record", **arguments)
        cycle.cycle("start", cycle_id="cycle-one", owner="synthetic-owner", task_id="task-one", scope=["rules"])
        material = self.base / "materials"
        material.mkdir()
        cycle.source_scan("register", source_id="synthetic-materials", root=str(material), authorization_ref="synthetic authorization")
        references = [("governance_facts", source_hash(source_id) + ":booking-rule"),
                      ("governance_cycles", "cycle-one"), ("scan_sources", source_hash("synthetic-materials"))]
        sources = [{"source_id": source_id, "collection": collection, "local_id": key,
                    "revision": wb.digest_bytes(wb.canonical(self.engine.store.get(collection, key)))} for collection, key in references]
        view = self.freeze(sources=sources)
        self.execute(self.plan(view=view))
        self.assertEqual([item["state"] for item in self.current()["source_freshness"]], ["MATCHES"] * 3)
        cycle.facts("record", **dict(arguments, source_revision="r2", statement="Bookings require two confirmations.", expected_revision=1))
        self.assertEqual(self.current()["source_freshness"][0]["state"], "CHANGED_OR_MISSING")

    def test_legacy_identity_adoption_retains_publication_consumption_and_source_revision(self):
        from taskcarry.project_identity import ProjectIdentity
        config = self.engine.store.get("config", "project")
        for field in ("project_id", "replica_id", "source_aliases"):
            config.pop(field, None)
        self.engine.store.put("config", "project", config)
        legacy = self.engine.source()
        task = self.engine.store.get("tasks", "task-one")
        view = self.freeze(body="Legacy view", sources=[{"source_id": legacy["source_id"], "collection": "tasks", "local_id": "task-one",
                                                         "revision": wb.digest_bytes(wb.canonical(task))}])
        plan = self.plan(view=view)
        self.execute(plan)
        proof = self.proof(plan, view=view)
        self.engine.workbench("consume", proof=proof)
        before = {name: self.engine.store.list(name) for name in ("workbench_views", "workbench_plans", "workbench_receipts", "workbench_consumption")}
        identity = ProjectIdentity(self.control)
        adoption = identity.identity("plan")
        identity.identity("execute", plan_id=adoption["plan_id"])
        self.assertEqual(self.current()["state"], "PUBLISHED")
        self.assertEqual(self.current()["consumer_state"], "REVIEWED_EVIDENCE_RECORDED")
        self.assertEqual(self.current()["source_freshness"][0]["state"], "MATCHES")
        self.assertEqual(self.current()["source_id"], legacy["source_id"])
        self.assertEqual(self.execute(plan)["status"], "COMPLETED")
        self.assertEqual(before, {name: self.engine.store.list(name) for name in before})
        self.assertFalse(self.engine._same_local_source(dict(legacy, control=str(self.base / "another-control"))))
        current = self.engine.source()
        self.assertFalse(self.engine._same_local_source(dict(current, replica_id="different-replica")))

    def test_unknown_or_rebound_workspace_task_is_rejected(self):
        for changed in ({"task_id": "unknown"}, {"workspace": "unknown"}, {"source_id": "other-source"}):
            with self.subTest(changed=changed), self.assertRaises(GovernanceError):
                self.plan([self.target(**changed)])
        first = self.plan()
        self.execute(first)
        self.engine.task("different-task", title="Different")
        with self.assertRaises(GovernanceError):
            self.plan([self.target(task_id="different-task")])

    def test_original_setup_binding_must_match(self):
        materials = self.worker / ".taskcarry/workbench.json"
        materials.parent.mkdir()
        materials.write_text(json.dumps({"control": str(self.control), "target": str(self.worker),
                                         "workspace": "one", "task_id": "another-task"}), encoding="utf-8")
        with self.assertRaises(GovernanceError):
            self.plan()

    def test_plan_file_tamper_is_refused(self):
        plan = self.plan()
        Path(plan["plan_path"]).write_text("{}", encoding="utf-8")
        with self.assertRaises(GovernanceError):
            self.execute(plan)
        self.assertFalse((self.worker / ".local/CURRENT.md").exists())

    def test_missing_view_mirror_resumes_from_durable_intent(self):
        original = wb.atomic_write
        def interrupt_manifest(path, content):
            if path.name == "manifest.json":
                raise OSError("synthetic manifest interruption")
            return original(path, content)
        with patch.object(wb, "atomic_write", side_effect=interrupt_manifest), self.assertRaises(OSError):
            self.freeze(body="Interrupted view")
        view = self.freeze(body="Interrupted view")
        self.assertFalse(view["created"])
        self.assertEqual(self.execute(self.plan(view=view))["status"], "COMPLETED")

    def test_receipt_and_pointer_failures_resume_without_rewriting_effect(self):
        for basename in ("receipt", "pointer"):
            with self.subTest(basename=basename):
                plan = self.plan(view=self.freeze(body="Fault at " + basename))
                original = wb.atomic_write
                def interrupt(path, content):
                    if path.parent.name == ("receipts" if basename == "receipt" else "current"):
                        raise PermissionError("synthetic durable receipt failure")
                    return original(path, content)
                with patch.object(wb, "atomic_write", side_effect=interrupt):
                    self.assertEqual(self.execute(plan)["status"], "PARTIAL")
                target = self.worker / ".local/CURRENT.md"
                before = target.stat().st_mtime_ns
                self.assertEqual(self.execute(plan)["status"], "COMPLETED")
                self.assertEqual(before, target.stat().st_mtime_ns)

    def test_pointer_effect_before_index_finalize_has_truthful_status(self):
        plan = self.plan()
        original = self.engine.store.put
        def interrupt(collection, key, value):
            if collection == "workbench_current":
                raise RuntimeError("synthetic finalize interruption")
            return original(collection, key, value)
        with patch.object(self.engine.store, "put", side_effect=interrupt), self.assertRaises(RuntimeError):
            self.execute(plan)
        self.assertTrue(self.current()["finalization_pending"])
        self.assertEqual(self.current()["view_id"], self.view["view_id"])
        self.execute(plan)
        self.assertFalse(self.current()["finalization_pending"])

    def test_atomic_write_failure_leaves_no_partial_final_object(self):
        target = self.control / "synthetic-final.txt"
        target.write_bytes(b"original")
        with patch.object(wb.os, "replace", side_effect=PermissionError("synthetic replace denial")), self.assertRaises(PermissionError):
            wb.atomic_write(target, b"replacement")
        self.assertEqual(target.read_bytes(), b"original")
        self.assertFalse(list(self.control.glob("*.tmp-*")))

    def test_os_lock_releases_after_process_exit_without_deleting_lock_file(self):
        source = Path(__file__).resolve().parents[1]
        program = ("import sys,os;sys.path.insert(0,sys.argv[1]);from taskcarry.store import Store;"
                   "s=Store(sys.argv[2]);g=s.guard();g.__enter__();os._exit(0)")
        child = subprocess.run([sys.executable, "-I", "-B", "-c", program, str(source), str(self.control)], capture_output=True)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        lock = self.control / ".taskcarry/mutation.lock"
        self.assertTrue(lock.exists())
        self.assertEqual(self.execute(self.plan())["status"], "COMPLETED")

    def test_status_is_read_only_and_paginates_workspaces(self):
        self.make_worker("two")
        self.execute(self.plan())
        before = self.engine.store.events()
        first = self.engine.workbench("status", limit=1)
        self.assertEqual(first["items"][0]["workspace"], "one")
        self.assertEqual(first["items"][0]["thread_id"], "thread-one")
        self.assertEqual(first["next_cursor"], "one")
        second = self.engine.workbench("status", limit=1, cursor=first["next_cursor"])
        self.assertEqual(second["items"][0], {"workspace": "two", "state": "NOT_PUBLISHED"})
        self.assertIsNone(second["next_cursor"])
        self.assertEqual(before, self.engine.store.events())
        with self.assertRaises(GovernanceError):
            self.engine.workbench("status", limit=101)

    def test_symlink_target_refused_when_os_supports_it(self):
        outside = self.base / "outside"
        outside.mkdir()
        try:
            (self.worker / ".local").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("OS denies synthetic symlink creation")
        with self.assertRaises(GovernanceError):
            self.plan()


if __name__ == "__main__":
    unittest.main()
