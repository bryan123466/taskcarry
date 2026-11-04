# Manual setup and handoff fallback

[Return to conversational onboarding](windows-example.md) · [简体中文](../zh-CN/manual-setup.md) · [繁體中文](../zh-TW/manual-setup.md) · [Command reference](../COMMANDS.md)

Use only the step governance identifies as missing. This page supports the **0.2.0rc6 candidate**; the published download remains [rc5](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5), whose package includes its matching manual. Do not use candidate-only setup fields with an older installed runtime. All paths below are synthetic examples; replace the root consistently before first setup.

- [Install or inspect the fixed runtime](#install)
  - [Initialize only missing governance state](#governance)
- [Generate and load connection materials](#mcp)
  - [Connect a registered workbench](#workbench)
  - [Verify the actual window](#verify)
- [Transfer only missing old-chat context](#existing)
  - [Open a new work chat when needed](#agents)
- [Continue after interruption](#recovery)

<a id="install"></a>

## Install or inspect the fixed runtime

First check for an existing installation/control and keep it when valid. For a genuinely first tool installation, create `C:/TaskCarry/control` and extract the selected product ZIP into `C:/TaskCarry/toolkit`. The RC6 ZIP includes a top-level `taskcarry-0.2.0rc6/` directory: the extracted product root is `C:/TaskCarry/toolkit/taskcarry-0.2.0rc6`, containing `START_HERE.md`, `packages/`, `docs/` and `skills/`. Use the actual extracted version directory if selecting another package. Keep the existing business project in place. Python 3.11+ is required; Git is required for Git workflows only.

Run these commands in PowerShell **only when the dedicated runtime does not already exist**. Installing the package does not create a new business project or authorize upgrading an existing runtime.

```powershell
py -3 -m venv 'C:/TaskCarry/runtime'
$taskcarryWheel = Get-ChildItem -LiteralPath 'C:/TaskCarry/toolkit/taskcarry-0.2.0rc6/packages' -Filter '*.whl' -File
if (@($taskcarryWheel).Count -ne 1) { throw 'Expected exactly one wheel in the selected product package.' }
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m pip install --no-index --no-deps $taskcarryWheel.FullName
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' doctor
```

Before control initialization, doctor returns `NOT_INITIALIZED` without runtime details; this alone does not mean installation failed. After governance verifies that this control genuinely has no state and initializes it as described below, repeat the same doctor command to inspect the actual runtime and prerequisites. Interpret unavailable Git capabilities for the operation being attempted; do not recreate an existing store to clear a warning. Return the output to the governance chat and continue the same onboarding prompt.

<a id="governance"></a>

### Initialize only missing governance state

Governance first checks existing tasks, folders and prior outputs. When this control genuinely has no state, `init` creates governance state for it. That does not create a receiving baseline or prove that the business project is new. Ask governance to use the actual `init`, `workspace` and `task` contracts in the [command reference](../COMMANDS.md), preserving identities already present.

The optional [new-project scaffold](../../examples/windows_quickstart) is only for a confirmed new project. Its default is zero professional workspaces. It refuses existing destinations; after interruption, inspect actual results rather than deleting directories and rerunning. Existing projects use their real history and baseline.

<a id="mcp"></a>

## Generate and load connection materials

Save the reviewed JSON request as UTF-8 `C:/TaskCarry/setup-request.json` (the example input file, not the database). For the governance directory, its initial content is `{"mode":"preview"}`. Run:

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' setup --input 'C:/TaskCarry/setup-request.json'
```

Review the proposed changes and conflicts. Within the authorized setup scope, change only `mode` to `install` and repeat the command. Keep the same candidate and parameters when resuming an interrupted install. Setup preserves modified user files and reports conflicts.

The generated `.taskcarry/codex.mcp.toml` is a **fragment**. In Codex, merge its selected `[mcp_servers.<name>]` table into the target chat's project-level `.codex/config.toml`: `C:/TaskCarry/control/.codex/config.toml` for governance, or `<registered-workbench>/.codex/config.toml` for that workbench. Preserve other settings and servers; do not replace the whole file or change global configuration. Keep the generated command/arguments: they use a fixed interpreter, isolated UTF-8 startup and the selected package location.

Open/select that same directory as the target chat's project and working directory, and complete its project-trust prompt if appropriate. Codex loads project configuration only for trusted projects. Then use the host's supported MCP restart/reload action; the official desktop instructions use **Settings → MCP servers → Restart**. If the current chat cannot switch directories, resume the saved checklist in a chat opened in the configured directory, using the same control. Writing a config in another folder does not connect the current chat. Setup does not choose a host folder, grant trust or reload the host. See the official [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=app) and [configuration layers](https://learn.chatgpt.com/docs/config-file/config-basic).

Skills appear under `.agents/skills/`, including referenced method files. If not automatically discovered, explicitly read the needed `SKILL.md` and its references from that directory. Do not assume a new worktree inherits another directory's configuration. Verify each target window below; configuration files or a successful standalone stdio process do not prove native host loading.

<a id="workbench"></a>

### Connect a registered workbench

Governance must already have registered this Git workspace and its task against the original control. The following is a **synthetic payload**, not a request to create sample work:

```json
{"mode":"preview","target":"C:/TaskCarry/workspaces/agent-1","workspace":"agent-1","task_id":"example-writing"}
```

Replace all three values with verified registration data, save the request and run the same preview command. Supply `target`, `workspace` and `task_id` together; target must match the registered workspace and its current Git identity, and the task must exist in the same control. Governance reviews the actual relationship; setup does not impose a one-to-one task/workspace assignment. Keep `--project` on the original control. Review, then install the same request with `mode: install`.

This writes the workbench's four Skills and references, MCP fragment, and `.taskcarry/workbench.json` / `workbench.md`. It does not create a chat, register a task, initialize another database or activate host configuration. A plain document folder can use control-bound CLI for checkpoints; do not invent Git registration just to save documents.

<a id="verify"></a>

### Verify the actual window

After host loading, ask that window to call native `taskcarry_doctor` and `taskcarry_status`. Check the actual version, interpreter, imported module, control and relevant task/workspace/checkpoint against the saved binding. Multiple servers require choosing the correct one. Do not accept a command-line result as proof that those native tools are exposed.

If MCP is unavailable, keep the raw error or missing-tool fact and use the fixed isolated CLI for authorized work:

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' doctor
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' status
```

Record this as CLI evidence and leave native connection pending. For a tool update, preview/install managed files, review the active host config and reload separately; an installed version alone does not prove that an already running server changed. Uninstall removes unchanged managed files only, retaining modified files, governance data and active config that was merged manually.

<a id="existing"></a>

## Transfer only missing old-chat context

Use this route only when governance cannot read the relevant permitted history itself. Do not restart the original task. Paste into the **original work chat**:

```text
Prepare a minimal handoff for connecting this existing work to TaskCarry. Read current instructions and actual files. Report the project/task and its stable identity if known, actual working directory, Git root/branch/HEAD and WIP when applicable, confirmed decisions with sources, completed outputs and known acceptance, the exact unfinished position and next step. Separate facts, last-known information, suggestions and gaps. Retain the original work and history. Do not change files, register tasks or make a delivery for this summary.
```

Send the reply to **governance** with:

```text
Connect this handoff to our existing project. Verify the cited sources and real ownership, reuse known task/control identities and preserve WIP. Do not requeue already included results. Fill in only missing registration and connection steps under the onboarding authorization. Give me a ready-to-use continuation message for the original chat, with the verified control, runtime, task/workspace, Skill locations and next step. Identify what remains unverified.
```

Paste governance's completed message back into the original chat. Its connection check should load the relevant Skills, read the named task and effective decisions, and continue from the retained next step. This manual transfer is a fallback; it is not required after every piece of work.

<a id="agents"></a>

### Open a new work chat when needed

After agreeing a genuinely useful division, governance supplies the exact directory, responsibility, task identity and continuation content. If native chat creation is unavailable, open the new chat yourself in that directory and paste the prepared content. The number of new specialists may be zero. Preserve one main writer per task/write scope; inspect shared-directory conflicts before moving work.

<a id="recovery"></a>

## Continue after interruption

Say “Continue from the saved onboarding checklist; first check what actually happened.” Keep the original setup candidate and operation identity. A generated file, successful CLI check or saved schedule prompt proves only its own step. Changed user files or changed restore targets must be preserved, not overwritten to obtain a clean retry.

For ordinary checkpoints, start restore into an empty independent destination. If restore already produced effects and then lost its final receipt, let the supported recovery verify those effects and finish only missing bookkeeping. Do not manually empty the target. See the recovery Skill for the exact installed contract.

Scheduling, private remotes and multiple computers remain [optional operations](operation-manual.md). A missing optional feature does not prevent continuing the existing project.
