"""Frozen delivery, exact local Git integration, WIP-safe adoption and recovery."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from .core import Core, validate_relative_path, read_file_bytes
from .store import GovernanceError
from . import __version__
from .gitops import (git, out, repo, commit, ancestor, pathsafe, changed, assert_tree_types,
                     identity, digest, fingerprint, clean, import_commit, Scratch)


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value):
        raise GovernanceError("INVALID_ID", "Use 1-100 letters, digits, underscores, dots or hyphens")
    return value


class Integration:
    OPERATION_PROTOCOL = 1

    def __init__(self, project):
        self.core = Core(project)
        self.store = self.core.store
        self.root = Path(project).resolve()
        self.scratch = self.root / ".taskcarry" / "scratch"

    def _save(self, collection, key, record):
        if collection in {"operations", "plans"}:
            self._check_protocol(record)
            record.setdefault("operation_protocol", self.OPERATION_PROTOCOL)
            record.setdefault("created_with_version", __version__)
        self.store.put(collection, key, record)
        return record

    def _check_protocol(self, record):
        # Records created before protocol tagging use the same version-one
        # contract. A future contract must not be replayed by an older engine.
        version = record.get("operation_protocol", 1)
        if type(version) is not int or version != self.OPERATION_PROTOCOL:
            raise GovernanceError("OPERATION_PROTOCOL_UNSUPPORTED", "Use a compatible toolkit to continue this recorded operation", {"operation_protocol": version})

    def _ws(self, name):
        record = self.store.get("workspaces", identifier(name))
        if not record:
            raise GovernanceError("WORKSPACE_UNKNOWN", "Register the workspace first", {"name": name})
        path = repo(record["path"])
        if identity(path) != record["identity"]:
            raise GovernanceError("WORKSPACE_CHANGED", "Workspace branch or Git directory changed; explicitly re-register it")
        return path

    def workspace(self, name, path):
        name = identifier(name)
        p = repo(path)
        if p.is_relative_to(self.root / ".taskcarry"):
            raise GovernanceError("RESERVED_PATH", "Internal metadata cannot be a workspace")
        ident = identity(p)
        with self.store.transaction():
            prior = self.store.get("workspaces", name)
            if prior and prior["identity"] != ident:
                pending = [s for s in self.store.list("stages") if s["workspace"] == name and s["status"] in {"QUEUED", "CONFLICT"}]
                ops = [o for o in self.store.list("operations") if o.get("workspace") == name and o["status"] not in {"COMPLETED", "SUPERSEDED"}]
                if pending or ops:
                    raise GovernanceError("WORKSPACE_IN_USE", "Finish or resolve existing operations before rebinding this name")
            record = {"name": name, "path": str(p), "identity": ident}
            self._save("workspaces", name, record)
            self.store.event("workspace_registered", record)
            return record

    def submit(self, task_id, workspace, commit, base, paths, stage_id=None, relation="independent", supersedes=None):
        task_id = identifier(task_id)
        if not self.store.get("tasks", task_id):
            raise GovernanceError("TASK_UNKNOWN", "Create a task before declaring a stable delivery")
        source = self._ws(workspace)
        # Avoid shadowing the public argument name.
        from .gitops import commit as resolve_commit
        tip, origin = resolve_commit(source, commit), resolve_commit(source, base)
        if not ancestor(source, origin, tip) or origin == tip:
            raise GovernanceError("INVALID_RANGE", "Base must be a strict ancestor of the submitted commit")
        if not isinstance(paths, list) or not paths:
            raise GovernanceError("EXACT_PATHS_REQUIRED", "Specify all changed paths in this stable stage")
        exact = sorted({pathsafe(p) for p in paths})
        if len(exact) != len(paths) or len({p.casefold() for p in exact}) != len(exact):
            raise GovernanceError("DUPLICATE_PATH", "Duplicate or case-colliding paths")
        actual = changed(source, origin, tip)
        if actual != exact:
            raise GovernanceError("MANIFEST_MISMATCH", "Declared paths must exactly match the frozen commit range", {"declared": exact, "actual": actual})
        total_bytes = assert_tree_types(source, tip, exact) + assert_tree_types(source, origin, exact)
        if total_bytes > 128 * 1024 * 1024:
            raise GovernanceError("DELIVERY_TOO_LARGE", "Old and new delivery blobs exceed 128 MiB; use artifact references or smaller stages")
        if relation not in {"independent", "cumulative"}:
            raise GovernanceError("INVALID_RELATION", "Use independent or cumulative")
        predecessors = sorted(set(supersedes or []))
        if predecessors and relation != "cumulative":
            raise GovernanceError("INVALID_RELATION", "Superseding requires an explicit cumulative relation")
        if relation == "cumulative" and not predecessors:
            raise GovernanceError("PREDECESSOR_REQUIRED", "Cumulative deliveries must name their predecessor stages")
        body = {"task_id": task_id, "workspace": workspace, "commit": tip, "base": origin,
                "paths": exact, "relation": relation, "supersedes": predecessors}
        sid = identifier(stage_id or "stage-" + digest(body)[:20])
        with self.store.transaction():
            existing = self.store.get("stages", sid)
            if existing:
                if existing["declaration_hash"] != digest(body):
                    raise GovernanceError("ID_CONFLICT", "This stage id already describes a different delivery")
                return {"stage": existing, "reused": True}
            for old_id in predecessors:
                old = self.store.get("stages", old_id)
                if not old or old["task_id"] != task_id or old["workspace"] != workspace:
                    raise GovernanceError("INVALID_PREDECESSOR", "Predecessors must belong to the same task and workspace")
                if old["status"] == "SUPERSEDED":
                    raise GovernanceError("INVALID_PREDECESSOR", "Name the current successor rather than an already superseded stage")
                if not ancestor(source, old["commit"], tip) or not set(old["paths"]).issubset(exact):
                    raise GovernanceError("COVERAGE_UNPROVEN", "Cumulative stage must contain prior commit ancestry and declared paths")
            record = {**body, "stage_id": sid, "status": "QUEUED", "declaration_hash": digest(body), "created_at": now()}
            self._save("stages", sid, record)
            self.store.event("stage_submitted", {"stage_id": sid, "task_id": task_id, "commit": tip})
            return {"stage": record, "reused": False}

    def _pending(self):
        stages = self.store.list("stages")
        values = [s for s in stages if s["status"] == "QUEUED"]
        # A conflicting latest delivery must not silently reactivate an older
        # candidate. Explicit lineage remains valid until explicitly resolved.
        covered = {sid for s in stages for sid in s.get("supersedes", [])}
        return sorted((s for s in values if s["stage_id"] not in covered), key=lambda x: (x["created_at"], x["stage_id"]))

    def _predecessors(self, stage):
        result, seen, remaining = [], set(), list(stage.get("supersedes", []))
        while remaining:
            sid = remaining.pop()
            if sid in seen:
                continue
            seen.add(sid)
            old = self.store.get("stages", sid)
            if not old or old["task_id"] != stage["task_id"] or old["workspace"] != stage["workspace"]:
                raise GovernanceError("INVALID_PREDECESSOR", "Stored predecessor chain is inconsistent")
            result.append(old)
            remaining.extend(old.get("supersedes", []))
        return result

    def _fault(self, requested, at):
        if requested != at:
            return
        marker = self.root / ".taskcarry" / "SYNTHETIC_TEST_ONLY"
        if os.environ.get("TASKCARRY_TEST_FAULTS") != "1" or not marker.is_file():
            raise GovernanceError("FAULT_INJECTION_DISABLED", "Fault injection is restricted to explicitly marked synthetic tests")
        raise GovernanceError("INJECTED_INTERRUPTION", "Synthetic interruption at " + at, {"point": at})

    def _check_fault(self, fault):
        if fault is not None and (os.environ.get("TASKCARRY_TEST_FAULTS") != "1" or not (self.root / ".taskcarry" / "SYNTHETIC_TEST_ONLY").is_file()):
            raise GovernanceError("FAULT_INJECTION_DISABLED", "Fault injection is restricted to explicitly marked synthetic tests")

    def _finish(self, operation, baseline):
        self._check_protocol(operation)
        stage = self.store.get("stages", operation["stage_id"])
        candidate = operation["candidate"]
        if not ancestor(baseline, candidate, commit(baseline, "HEAD")):
            raise GovernanceError("EFFECT_NOT_CONFIRMED", "The frozen integration result is not present in the baseline")
        if out(baseline, "rev-parse", candidate + "^{tree}") != operation["result_tree"]:
            raise GovernanceError("EFFECT_MISMATCH", "Result tree differs from the journal")
        with self.store.transaction():
            stage.update({"status": "COMMITTED", "accepted_commit": candidate, "accepted_baseline": str(baseline), "accepted_at": now(), "operation_id": operation["operation_id"]})
            self._save("stages", stage["stage_id"], stage)
            for old in self._predecessors(stage):
                old_id = old["stage_id"]
                if old["status"] == "SUPERSEDED":
                    continue
                old.update({"status": "SUPERSEDED", "successor": stage["stage_id"], "historical_status": old["status"]})
                self._save("stages", old_id, old)
                old_op = self.store.get("operations", old.get("operation_id", ""))
                if old_op and old_op["status"] != "COMPLETED":
                    old_op.update({"historical_status": old_op["status"], "status": "COMPLETED", "resolved_by_successor": stage["stage_id"]})
                    self._save("operations", old_op["operation_id"], old_op)
            operation.update({"status": "COMPLETED", "completed_at": now()})
            self._save("operations", operation["operation_id"], operation)
            self.store.event("stage_received", {"stage_id": stage["stage_id"], "result_commit": candidate, "integration_verified": True})
        return {"stage_id": stage["stage_id"], "status": "COMMITTED", "commit": candidate, "integration_verified": True}

    def _resume_receive(self, baseline, operation):
        self._check_protocol(operation)
        if identity(baseline) != operation["baseline_identity"]:
            raise GovernanceError("WORKSPACE_CHANGED", "Original integration branch changed; no effects replayed")
        candidate = operation.get("candidate")
        if candidate and ancestor(baseline, candidate, commit(baseline, "HEAD")):
            rules = self.core.match_experience("EFFECT_PRESENT_RECEIPT_MISSING", "reconcile", operation["task_id"])
            if isinstance(rules, dict):
                rules = rules.get("matches", rules.get("rules", []))
            applicable = [r for r in rules if r.get("action") == "verify_and_finalize"]
            if not applicable:
                raise GovernanceError("EXPERIENCE_REVIEW_REQUIRED", "Effect is present; no currently applicable recovery rule permits automatic finalization", {"operation_id": operation["operation_id"]})
            with self.store.transaction():
                result = self._finish(operation, baseline)
                self.store.event("experience_applied", {"rule_id": applicable[0]["rule_id"], "operation_id": operation["operation_id"], "effect_verified": True})
            return {**result, "recovered": True, "experience_rule": applicable[0]["rule_id"]}
        if candidate and commit(baseline, "HEAD") == operation["expected_head"] and clean(baseline):
            git(baseline, "merge", "--ff-only", "--no-overwrite-ignore", "--no-edit", candidate)
            return self._finish(operation, baseline)
        if not candidate and commit(baseline, "HEAD") == operation["expected_head"]:
            stage = self.store.get("stages", operation["stage_id"])
            return self._receive(baseline, stage, operation["plan_id"], None, operation)
        raise GovernanceError("RECOVERY_REVIEW_REQUIRED", "Baseline changed outside the recorded operation; completed effects will not be replayed", {"operation_id": operation["operation_id"]})

    def _receive(self, baseline, stage, plan_id, fault, existing=None):
        source = self._ws(stage["workspace"])
        head = commit(baseline, "HEAD")
        oid = "receive-" + digest({"stage": stage["stage_id"], "baseline": str(baseline)})[:24]
        operation = existing or {"operation_id": oid, "kind": "reconcile", "stage_id": stage["stage_id"], "task_id": stage["task_id"],
                                 "baseline": str(baseline), "baseline_identity": identity(baseline), "expected_head": head, "plan_id": plan_id, "status": "PREPARED", "created_at": now()}
        self._save("operations", oid, operation)
        import_commit(baseline, source, stage["commit"])
        effective_base = stage["base"]
        accepted = [s for s in self._predecessors(stage) if s.get("accepted_commit")]
        # Among explicitly covered accepted predecessors choose the newest ancestor.
        for old in accepted:
            if old.get("accepted_baseline") == str(baseline) and ancestor(baseline, old["accepted_commit"], head) and ancestor(source, effective_base, old["commit"]):
                effective_base = old["commit"]
        delta = git(source, "diff", "--binary", "--full-index", "--no-renames", "--no-ext-diff", "--no-textconv", effective_base, stage["commit"], "--").stdout
        with Scratch(baseline, self.scratch, head) as scratch:
            if delta:
                result = git(scratch, "apply", "--index", "--3way", "--whitespace=nowarn", "-", data=delta, check=False)
                if result.returncode:
                    operation.update({"status": "REVIEW_REQUIRED", "code": "CONTENT_CONFLICT", "detail": result.stderr.decode("utf-8", "replace")})
                    self._save("operations", oid, operation)
                    stage.update({"status": "CONFLICT", "operation_id": oid})
                    self._save("stages", stage["stage_id"], stage)
                    raise GovernanceError("CONTENT_CONFLICT", "Frozen delivery conflicts with the current baseline; user work was not changed", {"stage_id": stage["stage_id"]})
            tree = out(scratch, "write-tree")
            message = f"Receive stage {stage['stage_id']}\n\nTaskCarry-Operation: {oid}\nTaskCarry-Source: {stage['commit']}\n"
            candidate = git(scratch, "commit-tree", tree, "-p", head, data=message.encode()).stdout.decode().strip()
        operation.update({"candidate": candidate, "result_tree": tree, "status": "CANDIDATE_READY", "effective_base": effective_base})
        self._save("operations", oid, operation)
        self._fault(fault, "after_candidate")
        if identity(baseline) != operation["baseline_identity"] or commit(baseline, "HEAD") != head or not clean(baseline):
            raise GovernanceError("BASELINE_CHANGED", "Baseline changed while preparing the result; the candidate is retained")
        git(baseline, "merge", "--ff-only", "--no-overwrite-ignore", "--no-edit", candidate)
        operation["status"] = "EFFECT_APPLIED"
        self._save("operations", oid, operation)
        self._fault(fault, "after_effect")
        return self._finish(operation, baseline)

    def _receive_selection(self, outstanding, stages, limit):
        # Recovery comes first. An operation and its queued stage are one work
        # item, even though both identities belong in the frozen plan.
        groups = {}
        for op in sorted(outstanding, key=lambda o: (o.get("created_at", ""), o["operation_id"])):
            key = ("stage", op["stage_id"]) if op.get("stage_id") else ("operation", op["operation_id"])
            groups.setdefault(key, {"operations": [], "stage": None})["operations"].append(op)
        for stage in stages:
            groups.setdefault(("stage", stage["stage_id"]), {"operations": [], "stage": None})["stage"] = stage
        selected = list(groups.values())[:limit]
        return ([op for group in selected for op in group["operations"]],
                [group["stage"] for group in selected if group["stage"] is not None],
                {"limit": limit, "selected_count": len(selected), "available_count": len(groups),
                 "unselected_count": len(groups) - len(selected)})

    def _receive_receipt(self, plan, results, reused=False):
        current = self.core.status()
        scoped_operations = set(plan.get("pending_operations", []))
        scoped_stages = set(plan["stage_ids"])
        operations = [o for o in current["actionable"]["operations"]
                      if o["operation_id"] in scoped_operations or o.get("plan_id") == plan["plan_id"]]
        unfinished = [s["stage_id"] for s in current["stages"]
                      if s["stage_id"] in scoped_stages and s["status"] not in {"COMMITTED", "SUPERSEDED"}]
        conflicts = [{"stage_id": s["stage_id"], "code": "CONTENT_CONFLICT"}
                     for s in current["stages"] if s["status"] == "CONFLICT"]
        queued = [s["stage_id"] for s in current["actionable"]["stages"] if s["status"] == "QUEUED"]
        unselected = [sid for sid in queued if sid not in scoped_stages]
        selected_operation_ids = {o["operation_id"] for o in operations}
        return {"status": "ACTION_REQUIRED" if conflicts or unfinished or operations else "COMPLETE",
                "scope": "plan", "plan_id": plan["plan_id"], "plan_complete": not unfinished and not operations,
                "project_complete": None, "results": results, "reused": reused, "remaining": conflicts,
                "remaining_stage_ids": unfinished, "remaining_operation_ids": [o["operation_id"] for o in operations],
                "queued_stage_ids": queued, "unselected_queued_stage_ids": unselected,
                "unselected_operation_ids": [o["operation_id"] for o in current["actionable"]["operations"]
                                             if o["operation_id"] not in selected_operation_ids],
                "current_actionable_counts": {name: len(records) for name, records in current["actionable"].items()},
                "meaning": "Completion covers only this frozen plan. Other recorded work and business acceptance require separate assessment."}

    def reconcile(self, baseline, execute=False, plan_id=None, fault=None, limit=20):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise GovernanceError("INVALID_ARGUMENT", "Reconciliation limit must be an integer from 1 to 100")
        self._check_fault(fault)
        with self.store.guard():
            recovery_binding = self.store.get("settings", "integration_baseline_recovery") or {}
            if recovery_binding.get("status") == "REBIND_REQUIRED":
                raise GovernanceError("RECOVERY_BASELINE_REBIND_REQUIRED", "The restored set omitted the bound baseline or its unique source identity; restore a complete reviewed set before receiving stages", recovery_binding)
            target = self._ws(baseline)
            binding = self.store.get("settings", "integration_baseline")
            if binding and binding != identity(target):
                raise GovernanceError("BASELINE_BOUND", "This state source already has an integration baseline; route another baseline to its own state source without redefining the user's project")
            outstanding = [o for o in self.store.list("operations") if o.get("kind") == "reconcile" and o.get("baseline") == str(target) and o["status"] not in {"COMPLETED", "REVIEW_REQUIRED", "SUPERSEDED"} and not o.get("recovery_inert")]
            if not execute:
                selected_ops, stages, selection = self._receive_selection(outstanding, self._pending(), limit)
                conflicts = [{"stage_id": s["stage_id"], "code": "CONTENT_CONFLICT"} for s in self.store.list("stages") if s["status"] == "CONFLICT"]
                data = {"kind": "reconcile", "baseline": baseline, "head": commit(target, "HEAD"), "stage_ids": [s["stage_id"] for s in stages], "declarations": {s["stage_id"]: s["declaration_hash"] for s in stages}, "unresolved": conflicts,
                        "pending_operations": [o["operation_id"] for o in selected_ops], "selection": selection}
                config = self.store.get("config", "project") or {}
                if config.get("recovery_restore_id"):
                    data["recovery_context"] = {"restore_id": config["recovery_restore_id"], "replica_id": config["replica_id"]}
                pid = "plan-" + digest(data)[:24]
                plan = self.store.get("plans", pid)
                if plan is None:
                    plan = {**data, "plan_id": pid, "created_at": now()}
                    self._save("plans", pid, plan)
                return {"plan": plan, "effects_executed": False, "clean_baseline": clean(target)}
            if not plan_id:
                raise GovernanceError("PLAN_REQUIRED", "Review a persisted reconciliation plan before execution")
            plan = self.store.get("plans", plan_id)
            if not plan or plan["kind"] != "reconcile" or plan["baseline"] != baseline:
                raise GovernanceError("PLAN_MISMATCH", "Plan does not describe this baseline")
            self._check_protocol(plan)
            for op in self.store.list("operations"):
                if op.get("plan_id") == plan_id or op.get("operation_id") in plan.get("pending_operations", []):
                    self._check_protocol(op)
            for sid in plan["stage_ids"]:
                stage = self.store.get("stages", sid)
                if stage:
                    for related in [stage, *self._predecessors(stage)]:
                        op = self.store.get("operations", related.get("operation_id", ""))
                        if op:
                            self._check_protocol(op)
            results = []
            for op in outstanding:
                if op["plan_id"] == plan_id or op["operation_id"] in plan.get("pending_operations", []):
                    results.append(self._resume_receive(target, op))
            completed_ops = [o for o in self.store.list("operations") if o.get("kind") == "reconcile" and o.get("candidate") and (o.get("plan_id") == plan_id or o["operation_id"] in plan.get("pending_operations", [])) and o["status"] == "COMPLETED"]
            expected = completed_ops[-1]["candidate"] if completed_ops else plan["head"]
            # Store list ordering is unspecified; chain last completed result by ancestry.
            for op in completed_ops:
                if ancestor(target, expected, op["candidate"]):
                    expected = op["candidate"]
            unfinished = [sid for sid in plan["stage_ids"] if self.store.get("stages", sid)["status"] not in {"COMMITTED", "SUPERSEDED"}]
            if not unfinished:
                return self._receive_receipt(plan, results, reused=not results)
            if commit(target, "HEAD") != expected:
                raise GovernanceError("STALE_BASELINE", "Baseline advanced since this plan; create a new plan", {"expected": expected, "actual": commit(target, "HEAD")})
            if not clean(target):
                raise GovernanceError("BASELINE_WIP", "Use a dedicated clean integration workspace; ordinary worker WIP remains untouched")
            if not binding:
                self._save("settings", "integration_baseline", identity(target))
            errors = []
            for sid in unfinished:
                stage = self.store.get("stages", sid)
                if stage["declaration_hash"] != plan["declarations"][sid]:
                    raise GovernanceError("DECLARATION_CHANGED", "Stage no longer matches the reviewed plan")
                if stage["status"] == "CONFLICT":
                    errors.append({"stage_id": sid, "code": "CONTENT_CONFLICT"})
                    continue
                try:
                    results.append(self._receive(target, stage, plan_id, fault))
                except GovernanceError as exc:
                    if exc.code != "CONTENT_CONFLICT":
                        raise
                    errors.append({"stage_id": sid, "code": exc.code})
            return self._receive_receipt(plan, results)

    def _restore_planned_bytes(self, workspace, operation):
        """Correct only proven checkout newline conversion, never new content.

        Git's clean/smudge conversion can change WIP bytes even when its diff is
        identical. Use the frozen result, check every affected file first, and
        preserve the exact index. This is not a general overwrite/recovery path.
        """
        references = operation.get("expected_worktree_bytes")
        if references is None:
            # Upgrade an old journal only where its checkpoint proves the exact
            # untracked content; do not infer merged tracked bytes from history.
            checkpoint = self.store.get("checkpoints", operation.get("checkpoint_id", ""))
            references = {f["path"]: f["worktree"] for f in (checkpoint or {}).get("files", [])
                          if f["path"] in operation["before"]["untracked"]}
        actual, expected = fingerprint(workspace), operation["expected_result"]
        if any(actual[k] != expected[k] for k in ("head", "status", "index", "work_diff")):
            return False
        if set(actual["untracked"]) != set(expected["untracked"]):
            return False
        pending = []
        for rel, reference in references.items():
            path = validate_relative_path(workspace, rel)
            if reference is None:
                if path.exists():
                    return False
                continue
            if not path.is_file():
                return False
            wanted, present = self.core._snapshot_bytes(reference), read_file_bytes(path)
            if wanted == present:
                continue
            if b"\0" in wanted or b"\0" in present or wanted.replace(b"\r\n", b"\n") != present.replace(b"\r\n", b"\n"):
                return False
            pending.append((path, present, wanted))
        if any(value != expected["untracked"][rel] for rel, value in actual["untracked"].items() if rel not in references):
            return False
        for path, present, wanted in pending:
            # Recheck through the same handle before replacing these known bytes.
            with path.open("r+b") as stream:
                if stream.read() != present:
                    raise GovernanceError("SOURCE_CHANGED", "Work changed during byte restoration; retained backups remain available")
                stream.seek(0)
                stream.write(wanted)
                stream.truncate()
                stream.flush()
                os.fsync(stream.fileno())
        if pending:
            self.store.event("worktree_bytes_restored", {"operation_id": operation["operation_id"], "files": len(pending), "reason": "verified_newline_conversion"})
        return True

    def _adopt_finish(self, workspace, operation):
        self._check_protocol(operation)
        bytes_verified = self._restore_planned_bytes(workspace, operation)
        if not bytes_verified or fingerprint(workspace) != operation["expected_result"]:
            raise GovernanceError("WIP_RESTORE_REQUIRED", "Workspace does not match the prevalidated restored state; retained checkpoint and stash need review", {"operation_id": operation["operation_id"], "stash": operation.get("stash"), "checkpoint_id": operation.get("checkpoint_id")})
        with self.store.transaction():
            operation.update({"status": "COMPLETED", "effect_state": "VERIFIED", "completed_at": now()})
            self._save("operations", operation["operation_id"], operation)
            self._resolve_adoption_preparations(operation)
            self.store.event("workspace_adopted", {"operation_id": operation["operation_id"], "workspace": operation["workspace"], "wip_verified": True})
        return {"status": "ADOPTED", "workspace": operation["workspace"], "commit": operation["candidate"], "wip_verified": True,
                "retained_backup_stash": operation.get("stash"), "checkpoint_id": operation.get("checkpoint_id")}

    def _resolve_adoption_preparations(self, operation):
        # Only a reviewed successor plan and verified adoption retire prior
        # no-effect preparations. The original failure evidence stays intact.
        for oid in operation.get("resolves_preparation_failures", []):
            old = self.store.get("operations", oid)
            if (not old or old.get("kind") != "adopt" or old.get("workspace") != operation["workspace"]
                    or old.get("baseline") != operation.get("baseline")
                    or old.get("status") not in {"PREPARING", "PREPARATION_FAILED"}
                    or old.get("effect_state") != "NOT_APPLIED" or old.get("candidate") or old.get("stash")):
                continue
            old.update({"historical_status": old["status"], "status": "SUPERSEDED",
                        "resolved_by_operation": operation["operation_id"], "resolved_by_plan": operation["plan_id"]})
            self._save("operations", oid, old)
            self.store.event("adoption_preparation_superseded", {"operation_id": oid, "successor": operation["operation_id"]})

    def _adoption_failure(self, operation, exc):
        failure = {"code": getattr(exc, "code", "PREPARATION_FAILED"), "message": str(exc),
                   "details": getattr(exc, "details", None)}
        first_failure = "first_failure" not in operation
        operation.setdefault("first_failure", failure)
        operation.update({"status": "PREPARATION_FAILED", "phase": "preparation", "effect_state": "NOT_APPLIED",
                          "code": failure["code"], "last_failure": failure})
        self._save("operations", operation["operation_id"], operation)
        # One durable attempt per plan, with bounded first/last diagnostics.
        # Repeated errors may contain fresh scratch paths; they are not new work.
        if first_failure:
            self.store.event("adoption_preparation_failed", {"operation_id": operation["operation_id"], **failure})

    def _adopt_resume(self, target, operation):
        self._check_protocol(operation)
        if fingerprint(target) == operation.get("expected_result"):
            return self._adopt_finish(target, operation)
        candidate = operation.get("candidate")
        if not candidate:
            raise GovernanceError("RECOVERY_REVIEW_REQUIRED", "Incomplete adoption preparation has no frozen candidate")
        if commit(target, "HEAD") == candidate and not clean(target):
            # A prior apply may have finished except for exact byte verification.
            # Check it once; never repeat stash application over present WIP.
            return self._adopt_finish(target, operation)
        stash = operation.get("stash")
        if operation.get("has_wip") and not stash:
            for row in out(target, "stash", "list", "--format=%H%x09%gs").splitlines():
                sha, _, subject = row.partition("\t")
                if subject.endswith("taskcarry:" + operation["operation_id"]):
                    stash = sha
                    operation["stash"] = sha
                    self._save("operations", operation["operation_id"], operation)
                    break
        if operation.get("has_wip") and not stash and fingerprint(target) == operation.get("before"):
            git(target, "stash", "push", "--include-untracked", "-m", "taskcarry:" + operation["operation_id"])
            stash = out(target, "rev-parse", "refs/stash")
            operation["stash"] = stash
            self._save("operations", operation["operation_id"], operation)
        if not clean(target):
            raise GovernanceError("RECOVERY_REVIEW_REQUIRED", "Unexpected work appeared during adoption; it is preserved")
        head = commit(target, "HEAD")
        if head == operation["expected_head"]:
            git(target, "merge", "--ff-only", "--no-overwrite-ignore", "--no-edit", candidate)
        elif head != candidate:
            raise GovernanceError("RECOVERY_REVIEW_REQUIRED", "Branch changed during adoption; retained WIP will not be replayed")
        if operation.get("has_wip"):
            if not stash:
                raise GovernanceError("WIP_RESTORE_REQUIRED", "Expected backup stash is not found; use retained checkpoint")
            git(target, "stash", "apply", "--index", stash)
        return self._adopt_finish(target, operation)

    def _prepare_adoption(self, target, source, plan, op):
        workspace = op["workspace"]
        before = plan["before"]
        staged = git(target, "diff", "--cached", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--").stdout
        unstaged = git(target, "diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--").stdout
        untracked = {rel: (target / rel).read_bytes() for rel in before["untracked"]}
        dirty_paths = set(git(target, "diff", "--cached", "--name-only", "-z", "--").stdout.decode().strip("\0").split("\0")) - {""}
        dirty_paths.update(set(git(target, "diff", "--name-only", "-z", "--").stdout.decode().strip("\0").split("\0")) - {""})
        dirty_paths.update(untracked)
        checkpoint_id = op.get("checkpoint_id")
        checkpoint = self.store.get("checkpoints", checkpoint_id) if checkpoint_id else None
        if checkpoint_id and checkpoint is None:
            raise GovernanceError("RECOVERY_REVIEW_REQUIRED", "The retained preparation checkpoint is missing")
        if dirty_paths and checkpoint is None:
            for rel in dirty_paths:
                pathsafe(rel)
            backup_task = "adoption-backup-" + workspace
            self.core.task(backup_task, title="Retained workspace update checkpoint", state="paused")
            checkpoint = self.core.checkpoint(backup_task, str(target), sorted(dirty_paths), "Continue original work after public baseline update", decision="Technical preservation only; not a new delivery", paused=True)
            checkpoint_id = checkpoint.get("checkpoint_id") or checkpoint.get("checkpoint", {}).get("checkpoint_id")
            op["checkpoint_id"] = checkpoint_id
            self._save("operations", op["operation_id"], op)
        import_commit(target, source, plan["baseline_head"])
        with Scratch(target, self.scratch, before["head"]) as scratch:
            merge = git(scratch, "merge", "--no-edit", plan["baseline_head"], check=False)
            if merge.returncode:
                raise GovernanceError("ADOPTION_CONFLICT", "Local commits conflict with the public baseline; original workspace remains unchanged")
            candidate = commit(scratch, "HEAD")
            changed_paths = changed(scratch, before["head"], candidate)
            assert_tree_types(scratch, candidate, changed_paths)
            for rel in changed_paths:
                pathsafe(rel)
                was_tracked = bool(git(target, "ls-tree", "-z", before["head"], "--", rel).stdout)
                if not was_tracked and (target / rel).exists() and rel not in untracked:
                    raise GovernanceError("IGNORED_FILE_COLLISION", "A local ignored file or directory overlaps the new baseline; it was not changed", {"path": rel})
            if staged:
                cp = git(scratch, "apply", "--index", "--3way", "--whitespace=nowarn", "-", data=staged, check=False)
                if cp.returncode:
                    raise GovernanceError("WIP_CONFLICT", "Staged changes need review against the new baseline; original WIP retained")
            if unstaged:
                cp = git(scratch, "apply", "--whitespace=nowarn", "-", data=unstaged, check=False)
                if cp.returncode:
                    raise GovernanceError("WIP_CONFLICT", "Unstaged changes need review against the new baseline; original WIP retained")
            for rel, payload in untracked.items():
                dest = scratch / pathsafe(rel)
                if dest.exists():
                    raise GovernanceError("WIP_CONFLICT", "Untracked file would collide with a baseline file", {"path": rel})
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(payload)
            # Preserve raw WIP bytes where adoption did not change that file.
            # For a merged file the isolated candidate defines its new bytes.
            for record in (checkpoint or {}).get("files", []):
                if record["path"] not in changed_paths and record["worktree"] is not None:
                    dest = validate_relative_path(scratch, record["path"])
                    dest.write_bytes(self.core._snapshot_bytes(record["worktree"]))
            expected_bytes = {}
            for rel in sorted(dirty_paths):
                dest = validate_relative_path(scratch, rel)
                expected_bytes[rel] = self.core._snapshot(read_file_bytes(dest)) if dest.is_file() else None
            expected = fingerprint(scratch)
        if identity(target) != self.store.get("workspaces", workspace)["identity"] or fingerprint(target) != before:
            raise GovernanceError("WORKSPACE_CHANGED", "Workspace changed during adoption preparation")
        has_wip = bool(before["status"])
        op.update({"status": "CANDIDATE_READY", "phase": "prepared", "candidate": candidate,
                   "expected_result": expected, "has_wip": has_wip, "checkpoint_id": checkpoint_id})
        op["expected_worktree_bytes"] = expected_bytes
        self._save("operations", op["operation_id"], op)
        return op

    def adopt(self, workspace, baseline, execute=False, plan_id=None, fault=None):
        self._check_fault(fault)
        target, source = self._ws(workspace), self._ws(baseline)
        if target == source:
            raise GovernanceError("SAME_WORKSPACE", "Baseline cannot adopt itself")
        with self.store.guard():
            if not execute:
                data = {"kind": "adopt", "workspace": workspace, "baseline": baseline, "baseline_head": commit(source, "HEAD"), "before": fingerprint(target)}
                config = self.store.get("config", "project") or {}
                if config.get("recovery_restore_id"):
                    data["recovery_context"] = {"restore_id": config["recovery_restore_id"], "replica_id": config["replica_id"]}
                failures = [o["operation_id"] for o in self.store.list("operations")
                            if o.get("kind") == "adopt" and o.get("workspace") == workspace and o.get("baseline") == baseline
                            and o.get("status") in {"PREPARING", "PREPARATION_FAILED"}
                            and o.get("effect_state") == "NOT_APPLIED" and not o.get("candidate") and not o.get("stash")
                            and (o.get("before") != data["before"] or o.get("baseline_head") != data["baseline_head"])]
                if failures:
                    data["resolves_preparation_failures"] = failures
                pid = "adopt-plan-" + digest(data)[:24]
                plan = self.store.get("plans", pid)
                if plan is None:
                    plan = {**data, "plan_id": pid, "created_at": now()}
                    self._save("plans", pid, plan)
                return {"plan": plan, "effects_executed": False}
            plan = self.store.get("plans", plan_id) if plan_id else None
            if not plan or plan["kind"] != "adopt" or plan["workspace"] != workspace or plan["baseline"] != baseline:
                raise GovernanceError("PLAN_REQUIRED", "Use the exact adoption plan for this workspace")
            self._check_protocol(plan)
            for old_id in plan.get("resolves_preparation_failures", []):
                previous = self.store.get("operations", old_id)
                if previous:
                    self._check_protocol(previous)
            oid = "adopt-" + digest(plan_id)[:24]
            op = self.store.get("operations", oid)
            if op:
                self._check_protocol(op)
                if op["status"] == "COMPLETED":
                    self._resolve_adoption_preparations(op)
                    return {"status": "ADOPTED", "reused": True, "workspace": workspace, "commit": op["candidate"]}
                if op["status"] == "SUPERSEDED":
                    raise GovernanceError("OPERATION_SUPERSEDED", "A verified successor resolved this failed preparation; use its receipt", {"operation_id": oid, "resolved_by_operation": op.get("resolved_by_operation")})
                if (op.get("effect_state") != "NOT_APPLIED" or op.get("candidate") or op.get("stash")
                        or op.get("status") not in {"PREPARING", "PREPARATION_FAILED"}):
                    return self._adopt_resume(target, op)
            if fingerprint(target) != plan["before"] or commit(source, "HEAD") != plan["baseline_head"]:
                raise GovernanceError("STALE_PLAN", "Work or baseline changed; create a new adoption plan")
            if op is None:
                op = {"operation_id": oid, "kind": "adopt", "workspace": workspace, "baseline": baseline,
                      "baseline_head": plan["baseline_head"], "plan_id": plan_id, "status": "PREPARING",
                      "phase": "preparation", "effect_state": "NOT_APPLIED", "before": plan["before"],
                      "expected_head": plan["before"]["head"], "created_at": now(),
                      "resolves_preparation_failures": plan.get("resolves_preparation_failures", [])}
                # An unchanged WIP snapshot may be reused even when the source
                # baseline moved and the new plan supersedes a failed attempt.
                for old_id in op["resolves_preparation_failures"]:
                    old = self.store.get("operations", old_id)
                    if old and old.get("before") == plan["before"] and old.get("checkpoint_id"):
                        op["checkpoint_id"] = old["checkpoint_id"]
                        break
                self._save("operations", oid, op)
            try:
                op = self._prepare_adoption(target, source, plan, op)
            except Exception as exc:
                self._adoption_failure(op, exc)
                raise
            has_wip = op["has_wip"]
            candidate = op["candidate"]
            if has_wip:
                git(target, "stash", "push", "--include-untracked", "-m", "taskcarry:" + oid)
                op["stash"] = out(target, "rev-parse", "refs/stash")
                op["status"] = "WIP_SAVED"
                op["effect_state"] = "WIP_SAVED"
                self._save("operations", oid, op)
            self._fault(fault, "after_stash")
            git(target, "merge", "--ff-only", "--no-overwrite-ignore", "--no-edit", candidate)
            op["status"] = "EFFECT_APPLIED"
            op["effect_state"] = "APPLIED"
            self._save("operations", oid, op)
            self._fault(fault, "after_adopt")
            if has_wip:
                git(target, "stash", "apply", "--index", op["stash"])
            self._fault(fault, "after_restore")
            return self._adopt_finish(target, op)

    def doctor(self):
        import platform
        from .setup import runtime_info
        try:
            version = out(self.root, "--version")
            git_status = "AVAILABLE"
        except GovernanceError:
            version, git_status = None, "UNAVAILABLE"
        checks = []
        for ws in self.store.list("workspaces"):
            try:
                self._ws(ws["name"])
                checks.append({"workspace": ws["name"], "status": "AVAILABLE"})
            except GovernanceError as exc:
                checks.append({"workspace": ws["name"], "status": "ACTION_REQUIRED", "code": exc.code})
        return {"toolkit_version": __version__, "python": platform.python_version(), "platform": platform.system(), "git": {"status": git_status, "version": version}, "workspaces": checks,
                "runtime": runtime_info(self.root),
                "native_codex_connection": "VERIFY_IN_TARGET_HOST", "remote_push_supported": False, "multi_host_writer_supported": False}
