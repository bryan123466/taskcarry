"""Replay the synthetic drone governance story through TaskCarry's shared API.

This creates local synthetic repositories, not native chats or schedules. Use an
installed TaskCarry runtime and an explicitly selected empty destination.
"""
import argparse
import json
from pathlib import Path

from taskcarry.api import invoke
from taskcarry.core import digest_bytes
from taskcarry.project_recovery import ProjectRecovery
from taskcarry.recovery_git import git
from taskcarry.store import _linked


EXAMPLE = Path(__file__).resolve().parent


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def scenario():
    return json.loads((EXAMPLE / "scenario.json").read_text(encoding="utf-8"))


def plan(destination):
    """Describe the example without touching its destination or any host state."""
    destination = Path(destination).expanduser().absolute()
    for path in (destination, *destination.parents):
        if _linked(path):
            raise ValueError("Choose a synthetic destination without links or junctions.")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("The example needs an absent or empty synthetic destination.")
    return {
        "destination": str(destination),
        "actions": [
            "Create a synthetic control and three independent existing-work repositories.",
            "Retain original tasks, selected files, interface decisions and paused outdoor work.",
            "Add the proposed product thread after a synthetic project-selection decision.",
            "Record the indoor/offline scope change and publish four explicit workbench entries.",
            "Read back local effects, save exact project memory with Git, and retain checkpoints.",
            "Create and verify a separate standby recovery with all five Git components."
        ],
        "effects_executed": False,
        "native_chats_created": False,
        "schedules_created": False,
        "real_aircraft_connected": False,
    }


class DroneExample:
    """Small tutorial orchestrator; all governance mutations use the shared API."""

    def __init__(self, destination):
        self.root = Path(destination).absolute()
        self.control = self.root / "TaskCarry"
        self.spec = scenario()
        self.windows = self.spec["existing_windows"] + [self.spec["suggested_window"]]

    def call(self, operation, **arguments):
        return invoke(self.control, operation, arguments)

    def workspace(self, name):
        return self.root / "workspaces" / name

    @staticmethod
    def repository(path, initial):
        path.mkdir(parents=True)
        git(path, "init", "--quiet", "-b", "main")
        git(path, "config", "user.name", "Synthetic Drone Example")
        git(path, "config", "user.email", "drone@example.invalid")
        write(path / ".gitignore", ".taskcarry/\n.local/\n.codex/\nevidence/\n")
        for relative, content in initial.items():
            write(path / relative, content)
        git(path, "add", "--", ".gitignore", *initial)
        git(path, "commit", "--quiet", "-m", "Retain synthetic initial work")

    def prepare(self):
        plan(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.repository(self.control, {"PROJECT.md": self.spec["scope_initial"] + "\n"})
        self.call("init", name="Synthetic vision drone")
        self.call("task", task_id=self.spec["governance_task"], title="Coordinate drone project memory")
        self.call("task", task_id="drone-outdoor-evaluation", title="Evaluate outdoor conditions", state="paused")
        for window in self.spec["existing_windows"]:
            self.register_window(window)
        self.record_scope(1)
        self.call("facts", action="record", source_id=self.spec["source_id"],
                  fact_id="frame-identity", source_revision="original-discussions",
                  task_id=self.spec["governance_task"], kind="decision",
                  statement=self.spec["decision_retained"],
                  evidence={"reference": "initial/software.md + initial/hardware.md",
                            "summary": "Authored synthetic source notes; original interface boundary retained."})
        return self.call("status")

    def register_window(self, window):
        root = self.workspace(window["workspace"])
        self.repository(root, {"SOURCE_NOTES.md": (EXAMPLE / window["source"]).read_text(encoding="utf-8"),
                               "DRAFT.md": "Unfinished professional draft; retain this original file.\n"})
        self.call("workspace", name=window["workspace"], path=str(root))
        self.call("task", task_id=window["task_id"], title=window["title"])
        return self.call("checkpoint", task_id=window["task_id"], workspace=window["workspace"],
                         paths=["SOURCE_NOTES.md", "DRAFT.md"], next_step=window["next_step"],
                         decision="Keep this original task and unfinished draft when introducing governance.")

    def record_scope(self, revision):
        current = revision == 2
        scope = self.spec["scope_current" if current else "scope_initial"]
        result = self.call("facts", action="record", source_id=self.spec["source_id"],
                           fact_id="first-milestone", source_revision="scope-" + str(revision),
                           task_id=self.spec["governance_task"], kind="decision", statement=scope,
                           **({"expected_revision": 1} if current else {}),
                           evidence={"reference": "scenario.json#scope_" + ("current" if current else "initial"),
                                     "summary": "Synthetic user decision, not an actual customer instruction."},
                           judgment={"statement": "Align the four workstreams; keep deferred work traceable.",
                                     "basis": "The selected first-milestone scope."})
        body = "# Shared drone project memory\n\n" + scope + "\n\n"
        body += "Retained decision: " + self.spec["decision_retained"] + "\n\n"
        if current:
            body += "Agreed interface: " + self.spec["interface_agreed"] + "\n\n"
        body += "Deferred work:\n" + "".join("- " + item + "\n" for item in self.spec["deferred"])
        write(self.control / "PROJECT.md", body)
        return result

    def scope_change_plan(self):
        self.register_window(self.spec["suggested_window"])
        self.record_scope(2)
        self.call("cycle", action="start", cycle_id="indoor-scope", owner="synthetic-governor",
                  task_id=self.spec["governance_task"], scope=["drone-project-memory"])
        self.call("cycle", action="effect_plan", cycle_id="indoor-scope", owner="synthetic-governor",
                  request_id="publish-plan", data={"effect_id": "four-workbench-entries", "kind": "local_navigation",
                  "resource": "drone-project-memory", "expected": "Four entries retain the original task and show the indoor/offline scope."})
        source = self.call("identity")["source"]["source_id"]
        body = (self.control / "PROJECT.md").read_text(encoding="utf-8")
        view = self.call("workbench", action="freeze", body=body, sources=[{
            "source_id": source, "path": "PROJECT.md", "revision": digest_bytes((self.control / "PROJECT.md").read_bytes())}])
        targets = []
        for window in self.windows:
            text = ("Original task: " + window["task_id"] + "\n\n" + body +
                    "\nNext step: " + window["next_step"] + "\n\n" +
                    "This is an authored synthetic replay. A local publication is not a native-chat read receipt.\n")
            targets.append({"workspace": window["workspace"], "task_id": window["task_id"],
                            "thread_id": window["thread_id"], "host": "none",
                            "code_assessment": {"status": "NO_CODE_DEPENDENCY", "reason": "Project memory and navigation only; no source or aircraft-control change."},
                            "writes": [{"path": ".local/CURRENT.md", "text": text}]})
        return self.call("workbench", action="plan", view_id=view["view_id"], targets=targets)

    def execute_scope_change(self, plan_id):
        return self.call("workbench", action="execute", plan_id=plan_id)

    def finish_scope_change(self, plan_id):
        status = self.call("workbench", action="status")
        entries = {item["workspace"]: item for item in status["items"]}
        for window in self.windows:
            entry = entries[window["workspace"]]
            text = (self.workspace(window["workspace"]) / ".local/CURRENT.md").read_text(encoding="utf-8")
            if (entry["state"] != "PUBLISHED" or entry["plan_id"] != plan_id or
                    self.spec["scope_current"] not in text or window["task_id"] not in text):
                raise RuntimeError("Inspect the actual entry and resume the original publication plan.")
            # Checkpoint ordinary professional files, not the ignored local host entry.
            self.call("checkpoint", task_id=window["task_id"], workspace=window["workspace"],
                      paths=["SOURCE_NOTES.md", "DRAFT.md"], next_step=window["next_step"],
                      decision="Indoor/offline milestone adopted in project memory; professional outputs still need review.")
        self.call("cycle", action="effect_result", cycle_id="indoor-scope", owner="synthetic-governor",
                  request_id="publish-result", data={"effect_id": "four-workbench-entries", "outcome": "confirmed",
                  "evidence_ref": "workbench-plan:" + plan_id,
                  "statement": "Read back all four local entries and bindings; no native host consumption asserted."})
        saved_plan = self.call("preserve", action="plan", repository=str(self.control), paths=["PROJECT.md"],
                               message="Retain the reviewed synthetic indoor milestone")
        saved = self.call("preserve", action="execute", plan_id=saved_plan["plan_id"])
        self.call("cycle", action="finish", cycle_id="indoor-scope", owner="synthetic-governor", request_id="finish",
                  data={"state": "completed", "next_step": "Review actual professional outputs and native host acceptance separately."})
        return saved

    def backup(self):
        selected = [{"name": window["workspace"]} for window in self.windows]
        selected.append({"name": "governance", "path": str(self.control)})
        planned = self.call("recovery", action="backup_plan", destination=str(self.root / "recovery-media"), workspaces=selected)
        return self.call("recovery", action="backup_execute", plan_id=planned["plan_id"])

    def restore_plan(self, backup):
        # Use an independent controller: no reliance on the original live database.
        controller = ProjectRecovery(self.root / "restore-controller")
        planned = controller.recovery("restore_plan", manifest=backup["manifest"],
                                      expected_sha256=backup["manifest_sha256"], destination=str(self.root / "standby"))
        return controller, planned

    def run(self):
        self.prepare()
        planned = self.scope_change_plan()
        published = self.execute_scope_change(planned["plan_id"])
        if published["status"] != "COMPLETED":
            raise RuntimeError("Publication is incomplete; inspect its exact plan and retained effects.")
        self.finish_scope_change(planned["plan_id"])
        backup = self.backup()
        controller, restoration = self.restore_plan(backup)
        restored = controller.recovery("restore_execute", plan_id=restoration["plan_id"])
        current = self.call("status")
        report = {"schema": "taskcarry.example.drone-report.v1", "synthetic": True,
                  "evidence_kind": "executed_shared_api_replay", "workbench_plan_id": planned["plan_id"],
                  "view_id": planned["view_id"], "published_workbenches": len(published["results"]),
                  "task_ids": sorted(task["task_id"] for task in current["tasks"]),
                  "scope_revision": self.call("facts", action="get", source_id=self.spec["source_id"], fact_id="first-milestone")["fact"]["revision"],
                  "recovery_state": restored["state"], "recovery_manifest_sha256": backup["manifest_sha256"],
                  "native_host_verified": False, "natural_schedule_verified": False,
                  "actual_aircraft_or_model_verified": False,
                  "next_step": "Review native synthetic conversations and their actual outputs separately; the standby writer remains inactive."}
        write(self.root / "REPLAY_REPORT.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="An absent or empty directory for this synthetic example only.")
    parser.add_argument("--execute", action="store_true", help="Perform the displayed local synthetic actions.")
    args = parser.parse_args()
    reviewed = plan(args.destination)
    result = DroneExample(args.destination).run() if args.execute else reviewed
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
