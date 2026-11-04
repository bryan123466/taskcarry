# Trial, installation, upgrade, and removal

[中文](../zh-CN/trial-guide.md) · [Home](../../README.md)

Use only a new disposable project for this RC trial. You do not need an API key, a second computer, a hosted service, or a scheduled task. The tool itself does not call a model. A Codex-assisted trial uses the Codex access you already have.

## 1. Install in a virtual environment

Extract the release source, open a terminal in it, and run `python -m venv .venv`. Thereafter use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS/Linux in place of `python` in this guide. Run:

```text
python -m pip install .
python -I -X utf8 -m taskcarry --help
```

Installation may require locally cached or downloaded Python build tooling. The installed toolkit runtime uses the standard library. Git must be installed separately for integration workflows. Do not use an administrator terminal merely to work around a project permission error.

## 2. Create and initialize the fictional project

```text
python examples/quality_forms/bootstrap.py --destination ../taskcarry-quality-demo
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control init --input ../taskcarry-quality-demo/requests/init.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control workspace --input ../taskcarry-quality-demo/requests/workspace-baseline.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control workspace --input ../taskcarry-quality-demo/requests/workspace-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control task --input ../taskcarry-quality-demo/requests/task-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control doctor
```

Review and quality workers have matching `workspace-review.json`, `task-review.json`, `workspace-quality.json`, and `task-quality.json` files. Register only the workers you intend to exercise. The baseline and workers are distinct Git worktrees; the control directory stores governance state.

## 3. Save work without delivering it

Edit the forms worker's `forms/inspection.csv` using fictional values. Save the file. Then run:

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control checkpoint --input ../taskcarry-quality-demo/requests/checkpoint-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control status
```

Inspect the returned checkpoint identifier. The request pauses the task and records the next step. It does not create a delivered stage. Unsaved editor buffers are outside the snapshot.

To test restoration, create a JSON request containing `checkpoint_id` and an absolute `destination` that does not exist, and invoke `restore --input` with it. The original workspace must remain untouched. Inspect the restored files and Git status. A restored Git checkpoint labels its synthetic restore commit and keeps original HEAD provenance; it does not pretend to reproduce the complete original repository history.

## 4. Explicitly deliver a stable stage

Once a small synthetic edit is ready:

```text
git -C ../taskcarry-quality-demo/workers/forms add -- forms/inspection.csv
git -C ../taskcarry-quality-demo/workers/forms commit -m "Improve fictional inspection form"
git -C ../taskcarry-quality-demo/workers/forms rev-parse HEAD
```

Open `requests/submit-forms-template.json`, replace `REPLACE_WITH_YOUR_NEW_COMMIT` with that exact commit, and save it as `requests/submit-forms.json`. Its `base` came from the fictional baseline; its `paths` must exactly match the changed files between base and commit. Add a new field-dictionary path only if you actually committed it.

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control submit --input ../taskcarry-quality-demo/requests/submit-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control reconcile --input ../taskcarry-quality-demo/requests/reconcile-plan.json
```

Read the plan. Make a new JSON file with `baseline: "baseline"`, `execute: true`, and the returned `plan_id`. Invoke `reconcile --input` with that execution file. Inspect both the result envelope and the baseline Git log. Do not edit a stored plan to force an outdated plan to pass.

Call planning again after a completed acceptance. Verify it does not offer the same completed effect as new work. Technical acceptance of this fixture does not approve any real quality process.

## 5. Exercise parallel work and adoption

Have a second worker edit only its assigned files, checkpoint, and deliver. Distinct branch names do not prove task independence: use task identifiers and explicit stage relationships.

Use `templates/adopt-plan.json` as a starting point. After inspecting the plan, put its identifier into an execution request. Confirm exact local commits, staged changes, unstaged changes, and new files are preserved where the operation reports success. If the tool reports a conflict, retain the local work and report that specific conflict. A failed adoption must not be interpreted as permission to reset or clean the workspace.

For cumulative stages use `relation: "cumulative"` and a `supersedes` list. The new stage must prove the prior stage's ancestry and changed-path coverage; a newer label alone is insufficient.

## 6. Add project-local Codex guidance

Create `setup-preview.json` containing `{"mode":"preview"}`. Then run:

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control setup --input setup-preview.json
```

Preview must not change files. If the listed managed paths are appropriate, create `setup-install.json` containing `{"mode":"install"}` and run the same command with that file. Setup writes:

- `.agents/skills/taskcarry-project-setup/SKILL.md`
- `.agents/skills/taskcarry-task-delivery/SKILL.md`
- `.agents/skills/taskcarry-governance-reconcile/SKILL.md`
- `.agents/skills/taskcarry-experience-recovery/SKILL.md`
- `.taskcarry/codex.mcp.toml`
- `.taskcarry/setup-manifest.json`

All are relative to the supplied project. Open **that project directory** as the Codex task's working directory so its project-local Skills can be discovered. Worker paths are supplied through the registered workspace records; keep each worker's assigned edit scope explicit.

The TOML file is a **configuration fragment**, not an already activated connection. It contains a project-bound stdio server command. Review it and add the entry through the supported MCP configuration mechanism in your installed Codex version. The helper does not overwrite `.codex/config.toml`, `AGENTS.md`, or user-global configuration. Follow the [official MCP documentation](https://developers.openai.com/codex/mcp) for the host interface.

Restart or refresh the tool connection if your host requires it, then ask Codex to call `taskcarry_doctor` and `taskcarry_status`. An ordinary CLI or protocol test does not prove this desktop connection works; preserve that distinction in your feedback.

Suggested worker prompt:

> Use the installed project guidance and the registered forms workspace. Improve only the fictional inspection form for TASK-FORMS. Do not change review or quality worker files. Save a checkpoint before pausing. Show the precise stable stage before delivery, then use the toolkit to deliver it if it is within my request. Do not run scheduled tasks or operate outside this disposable example.

Suggested governance prompt:

> Inspect this example's current status and available stages. Explain cumulative relationships using recorded evidence. Plan and execute eligible local acceptance, verifying actual Git effects. Preserve paused tasks as state. If a known recovery is applicable, validate its scope before using it; otherwise report the concrete missing condition. Do not push, deploy, or repair my computer.

## 7. Verify before reporting success

Run `python -m unittest discover -s tests -v` from the toolkit source. Record actual results. Fault tests must use their own disposable repositories and explicit synthetic markers, never a real project.

Report separately: local CLI, local Git integration, MCP protocol, actual Codex connection, model-assisted task decisions, and native scheduling. The RC does not require or execute native scheduling. Use [the validation report](../VALIDATION.md) to see which checks the maintainers actually performed.

## Upgrade

Stop the example's MCP process and wait for active tool calls to finish. Keep the original release and make a local backup of the disposable example while no mutation is running. Create a **new** virtual environment, install the new candidate, read its migration notes, and run `doctor` and the disposable scenario before using prior state. No automatic cross-version data migration is promised by this RC; an unsupported format should be reported rather than edited by hand.

Project setup can update previously managed files only when its ownership and content checks allow it. Modified files are reported as conflicts and retained. The MCP fragment contains the Python path that generated it; review the fragment when moving an environment or installing a new version.

## Uninstall

Create `setup-uninstall.json` containing `{"mode":"uninstall"}` and invoke `setup --input` with it in the same project. The helper removes eligible unmodified managed files and reports modified files to preserve. It keeps core task state and snapshots. Remove a manually activated MCP configuration entry separately, after reviewing its identity; it remains user-managed.

You can then uninstall the package from the dedicated environment with `python -m pip uninstall taskcarry`, or retire that dedicated environment. Keep any checkpoints or evidence you still need. Do not use a cleanup command that deletes a parent directory containing unrelated work.

## Feedback

Use [templates/defect-report.md](../../templates/defect-report.md). Include a small fictional reproduction, version, platform, interface, expected result, actual error, and whether a Git effect had already happened. Do not upload actual project files or the whole state directory.
