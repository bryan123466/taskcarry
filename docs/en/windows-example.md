# Windows guide: connect a real project

[简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md) · [Operating overview](operation-manual.md) · [Quick start](getting-started.md) · [Command reference](../COMMANDS.md)

[Prepare the project](#choose) · [Install](#install) · [Governance chat](#governance) · [Professional chats](#agents) · [MCP and CLI](#mcp) · [First governance result](#delivery) · [Automation](#automation) · [Private Git](#private-git) · [Multiple computers](#multi-computer) · [Completion check](#check)

Applies to version 0.2.0rc5. This guide uses the fixed example directory `C:/TaskCarry`, with paths already filled in. Paste prompts into the indicated chat and commands into Windows PowerShell. **Bold square brackets mark fields for you to fill in**, such as **[Enter the project name]**. Replace them, then copy the complete prompt. Reuse existing records instead of entering the same information again.

This walkthrough uses Codex on Windows. TaskCarry targets local AI tools through one CLI/MCP engine; another host needs its own connection, instruction-loading and scheduling checks. Download [TaskCarry 0.2.0rc5](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5).

<a id="choose"></a>

## 0. Prepare a project name, a short description, and three directories

**One TaskCarry installation manages one complete real project.** For example, a product's development, experiments, research, and operations can belong to one project. Unrelated products or activities should use different root directories. The recommended workflow here covers one project. For another project, replace every occurrence of `C:/TaskCarry` with another root directory before the first installation, then follow the same steps.

Prepare two pieces of information: project name **[Enter the project name]** and a one-sentence description **[Describe this project in one sentence]**. You do not need a complete project brief or to choose a “New project / Existing project” route.

New and existing projects use the same everyday governance. During initial onboarding, the governance chat checks existing registrations, deliverables, and the replies you provide from original chats. It continues existing history when work already exists and creates a new integration baseline only when there is no existing work. An empty TaskCarry folder does not prove that the project has no earlier deliverables. If this is unclear, governance only needs to confirm whether there is work to continue.

Use File Explorer to create these three directories: create `TaskCarry` on the C drive, then create `control` and `toolkit` inside it. **Create only these three directories at this step.** The governance chat will create the runtime, repository, and workspaces later as needed.

```text
C:/TaskCarry
C:/TaskCarry/control
C:/TaskCarry/toolkit
```

Extract the product ZIP into `C:/TaskCarry/toolkit`. When you open that directory, you should directly see `START_HERE.md`, `packages`, `docs`, and `examples`, without an extra nested directory of the same name. If the root already serves this project, continue its existing installation. If it belongs to another project, choose a different root instead of overwriting it.

```text
Prepare the directories and product package
        ↓
Create a governance chat, choose control → Install tools and record the project name and description
        ↓
Connect existing professional chats, or create new chats for parallel work
        ↓
Configure governance MCP → Review current state and receive explicit deliveries
        ↓
Professional work continues ⇄ Scheduled governance receives, reports, and updates workspaces
        ↓
Add when needed: private Git memory repository / work across computers
```

<a id="install"></a>

## 1. Install: create a governance chat and choose control

Create a new chat in Codex and choose the `C:/TaskCarry/control` folder. A useful chat name is “Project governance.” Continue installation, project onboarding, and automation setup in this governance chat.

### Recommended: ask the governance chat to install it

Fill in the two bold fields, then copy the entire quoted prompt into the governance chat:

> Please install and configure TaskCarry as the governance tool for this real project.
>
> Project name: **[Enter the project name]**
>
> One-sentence description: **[Describe this project in one sentence]**
>
> Project root: `C:/TaskCarry`; the product is extracted at `C:/TaskCarry/toolkit`; governance directory: `C:/TaskCarry/control`.
>
> First read the product's START_HERE.md, docs/en/windows-example.md, docs/COMMANDS.md, and the skills needed for this work. Check Python 3.11+ and Git, create the dedicated environment at `C:/TaskCarry/runtime`, and install from the local wheel in packages. If a valid installation already exists, check its version and reuse it.
>
> Check existing governance registrations, directories, and the project material I provide to decide whether to initialize or continue; do not require me to choose a technical route. When work already exists, preserve its repositories and files, obtain the original chats' onboarding replies using Section 3.1, and establish the integration baseline from the actual project history. Reuse existing governance state directly. If you cannot determine whether work already exists, finish installing the tools and briefly confirm whether there is original work to continue; do not create a business repository just because TaskCarry is empty.
>
> When it is confirmed that there is no original work to continue and a new project is needed, run the product's examples/windows_quickstart/bootstrap.py during first initialization with an empty control directory, using this project root, the default of 0 professional workspaces, and the actual project name. Fill in PROJECT_CONTEXT.md from the name and one-sentence description without inventing requirements I have not stated. Commit the actual initialization content using exact paths, then fast-forward baseline to that commit while no other writes are active there. For existing work, use init/setup to install governance state and skills instead of running the new-repository scaffold. Register professional tasks after their responsibilities are clear.
>
> Do not create scheduled tasks at this step. When finished, tell me the installed version, control directory, and registered baseline, or the information still needed from original chats. After completing the appropriate initialization, record the project name, description, actual paths, and onboarding decisions in control/PROJECT_MAP.md. If system dependencies, a Git commit identity, or a login are missing, give me the specific action required.

**Success looks like:** the dedicated Python environment can run TaskCarry doctor. A new project has one integration baseline and no professional tasks yet; an existing project proceeds to connecting its current work. The initial scaffold is not a business deliverable.

### Manual installation: commands for the same route

Skip this if installation through the governance chat succeeded. For manual installation, first confirm Python 3.11+ and Git are installed, then run in PowerShell:

```powershell
py -3 -m venv 'C:/TaskCarry/runtime'
$taskcarryWheel = Get-ChildItem -LiteralPath 'C:/TaskCarry/toolkit/packages' -Filter '*.whl' -File
if (@($taskcarryWheel).Count -ne 1) { throw 'The product packages directory must contain exactly one wheel. Check where you extracted the ZIP.' }
& 'C:/TaskCarry/runtime/Scripts/python.exe' -m pip install --no-index --no-deps $taskcarryWheel.FullName
```

This step installs the product tools. Next, paste the installation prompt above into the governance chat. It will reuse the installed environment and complete initialization or continuation according to the actual project; you do not need to choose another initialization command. Then continue to Chapter 2. The scaffold refuses to overwrite a nonempty control directory or an existing repository. If interrupted, ask the governance chat to inspect completed work and resume the missing steps; do not delete the existing state and start over.

<a id="governance"></a>

## 2. Set the governance chat's responsibilities

`control` is an ordinary directory that stores this project's governance state. `baseline` is a dedicated Git workspace for receiving deliverables. Professional work takes place in its registered workspaces. You do not need a second governance chat.

Paste into the governance chat:

```text
You are this project's governance workbench. Reuse the project name and one-sentence description recorded during installation, together with the tasks and decisions I have already explained; do not ask me to enter them again.
Product: `C:/TaskCarry/toolkit`; the only control directory: `C:/TaskCarry/control`; Python: `C:/TaskCarry/runtime/Scripts/python.exe`.
Check the current installation and PROJECT_MAP.md, read the project skills needed for this action, and use status to confirm what is actually registered. All professional chats share this control directory; do not initialize separate governance stores for them.
Your responsibilities are to understand task and deliverable relationships from project goals and actual evidence, receive explicit deliveries, maintain current state, preserve continuation points, arrange applicable workspace updates, and report specific matters that need my decision or action.
Register workspaces by their actual paths and reuse an existing record for the same directory. Keep stable task_id values rather than creating duplicate tasks on continuation. Registration alone does not prove receipt or adoption; verify formal results and actual files.
Preserve the current position and next step for unfinished, paused, or unchanged work without automatically turning it into backlog. A stable stage can be delivered before its entire task is finished. New business goals, final tradeoffs, and additional external sharing remain my decisions.
Prefer this project's MCP when calling tools. Before it is configured, or if it is unavailable, use the CLI with the same control directory. Establish the actual onboarding scope before carrying out the corresponding bounded actions.
```

<a id="agents"></a>

## 3. Configure professional task chats: continue existing chats or create new ones

**Professional task chats support work that needs to progress in parallel.** Divide them by real responsibilities such as software, hardware, algorithms, experiments, research, operations, simulation, writing, or management, or by independent tasks. There is no need to mirror departments mechanically. Subtasks that do not need parallel work can continue sequentially in one chat.

One primary professional chat advances a task within its writable scope. Other chats can review it read-only or handle clearly separated, nonoverlapping subtasks. Even with separate workspaces, two chats should coordinate before changing the same interface for the same task.

<a id="existing"></a>

### 3.1 Existing ongoing chats: preserve history and connect current state

If an existing chat already works in a separate workspace suitable for this project, you can keep that chat and connect it where it is. Installing the toolkit does not require migrating the chat.

**If several existing chats share one directory, keep one as that directory's primary professional role. Continue the other responsibilities that need parallel work in new professional chats with separate workspaces.** First ask the relevant existing chats to save their task summaries, deliverable locations, unfinished work, and next steps. The governance chat uses these to arrange continuation. Keep the original conversations and history. Stop writes for a transferred task in the original directory before the new chat takes it over. You do not have to move all historical content or restart every existing chat.

**Step 1: In each original chat you want to connect, fill in its responsibility, paste the prompt below, and wait for its reply.**

> I want to connect the current project to TaskCarry while keeping this conversation's existing tasks and context.
> This chat will continue to own: **[Enter the project work this chat should actually own]**.
> The governance directory is `C:/TaskCarry/control`, and the product is at `C:/TaskCarry/toolkit`.
> Read `C:/TaskCarry/control/.agents/skills/taskcarry-task-delivery/SKILL.md` and organize the information using the toolkit's current onboarding and delivery workflow.
> First summarize the actual working directory, Git root and branch, current commit, my task requirements, completed deliverables, committed and uncommitted files, paused/waiting items, important decisions, and next step. Read only task-relevant material, preserve all existing WIP and history, do not equate an unfinished task with failed delivery, and do not commit every file at once.
> If other chats also work in this directory, describe known sharing and potentially overlapping write scopes; say unknown where it is unknown. Prepare an onboarding note I can paste directly into the governance chat, including actual paths and task boundaries.
> Reuse and report any existing task_id, workspace registration, or checkpoint. After receiving an explicit binding from the governance chat, continue this role in the original chat. For tasks that need to transfer to a new chat, first save a continuation summary and exact file scope, then stop writing that scope and retain the original history for reference.

**Step 2: Send the complete onboarding reply from the original chat and the governance onboarding prompt below together in one message to the governance chat.**

The “onboarding reply” is the response the original chat prepares after receiving the Step 1 prompt, covering directories, deliverables, WIP, and the next step. For multiple original chats, include all their replies, keeping each chat's name and directory attached. You do not need to copy the entire chat history. Paste these replies first, followed by the prompt below, and send them together in the governance chat:

```text
Please connect this project's existing work using the onboarding notes I provided, continuing with `C:/TaskCarry/control`.
First verify actual working directories, Git history, registered tasks, and existing WIP. Reuse one workspace for the same path; do not register multiple chat names as independent writers for that same path. Different unregistered workspaces can be named existing-1, existing-2, and so on; preserve existing identities and task_id values.
Continue an original chat in place when it already has a suitable separate workspace. If multiple existing chats share one directory, keep one primary professional role according to my responsibility assignments. For the other responsibilities that need parallel work, create separate workspaces using Section 3.2 before continuing them. Preserve original summaries, deliverables, and uncommitted files without overwriting or mixing commits.
The integration baseline must come from this project's confirmed Git history. If there is no Git repository yet, or unrelated histories are present, first identify the actual files to include, exclusions, and existing history. Establish a baseline within the explicit project scope; do not force unrelated repositories together or commit files from the entire computer.
Determine which existing deliverables are already in the baseline, which are explicit deliverable stages, and which need only checkpoints. For previously unregistered tasks, create stable task_id values, actually call workspace and task to complete the required registration, and confirm with status; reuse existing records. Generate a fully filled-in continuation prompt for each original chat using its actual path and registered task_id, requiring it to read the delivery skill and continue its task record. Record the bindings in PROJECT_MAP.md and tell me which prompt to paste into which chat. If I genuinely need to choose responsibility ownership, describe the specific overlapping work.
```

**Step 3: Wait for the governance chat to generate a continuation prompt for each original chat, then paste each one back into its corresponding original chat.** The original chat checks its onboarding information and continues the task. These decisions concern actual ownership of files and tasks. The product does not currently scan all chats automatically, and renaming a chat does not change its actual working directory.

### 3.2 Create new professional task chats: add 1–n as needed

**[n]** is the number of new professional workspaces to add this time. Enter a positive integer, such as 5. Existing workspaces remain in place, and you can add more later when you need further parallel responsibilities. Governance continues the existing numbering; you do not need to calculate directory, branch, or task numbers yourself.

**Step 1: Prepare the workspaces in the governance chat.** Fill in the number, then copy the entire prompt below:

> Please prepare **[n]** new professional workspaces for this project using `C:/TaskCarry/control`.
>
> First read the actual status and PROJECT_MAP.md to establish how many workspaces are being added and the target list for this operation. Preserve existing workspaces and their numbers. Start at the next unused number, create agent-number directories under `C:/TaskCarry/workspaces` with matching codex/agent-number branches, and register matching workspace names. Record this operation's target list. If the same preparation operation is interrupted, reuse completed objects on that list and finish only the missing ones instead of adding another batch.
>
> Create the required Git worktrees from this project's currently confirmed integration baseline. Use the number n I provided, without limiting workspaces to the first three or prescribing business responsibilities. If there is no confirmed baseline, complete onboarding from the actual project history first rather than creating unrelated history.
>
> When continuing parallel tasks from existing chats, preserve their task_id values and task descriptions. After confirming that the original chat has stopped the relevant writes, preserve and carry forward the original deliverables/WIP within the task's exact scope, recording their source. Do not copy an entire shared directory over a new workspace.
>
> First inspect any existing stages or unfinished operations within their specific scope and retain their original receipts. Do not copy a delivered stage and queue it again. Preserve original commits and ancestry evidence; determine base/commit for subsequent deliveries in the new workspace from the actual Git relationship. Cumulative supersedes applies only to stages in the same task and workspace that meet ancestry and coverage conditions; it cannot directly replace an original stage across workspaces.
>
> When finished, list the name, full folder path, branch, and any existing-task continuation relationship for each of this operation's n workspaces. Generate a ready-to-paste professional chat prompt for each one, with all paths and numbers filled in. Leave only one bold responsibility field for me to describe the project work that chat will actually own. Preserve the identities of transferred tasks; register new tasks after I assign their responsibilities.

**Step 2: Create each new chat and choose its corresponding folder from the governance reply.** These folders are already separate Git workspaces; select them directly. The table below only illustrates sequential numbering. Use the complete list returned by governance:

| Example workspace name | Folder to choose for the new chat |
|---|---|
| agent-1 | `C:/TaskCarry/workspaces/agent-1` |
| agent-2 | `C:/TaskCarry/workspaces/agent-2` |
| Subsequent workspaces | The full folder path supplied for that number in the governance reply, continuing to the required number of new workspaces. |

**Step 3: Paste the professional prompt for that workspace and fill in its actual responsibility.** Governance generates a prompt with the correct paths and number for every workspace. Alternatively, use this generic prompt in any newly registered workspace:

> You are one of this project's professional task chats, responsible for: **[Enter the project work this chat should actually own]**.
>
> Governance directory: `C:/TaskCarry/control`; product: `C:/TaskCarry/toolkit`; Python: `C:/TaskCarry/runtime/Scripts/python.exe`.
>
> Read `C:/TaskCarry/control/PROJECT_MAP.md` and `C:/TaskCarry/control/.agents/skills/taskcarry-task-delivery/SKILL.md`. Check this chat's actual working directory, Git branch, and workspace registration in status, and determine your workspace name from the actual directory. If they do not match, explain the specific difference before proceeding rather than creating another registration from the chat's name.
>
> Reuse an existing or handed-over task_id. For a genuinely new task, generate a unique stable task_id from the actual workspace, use that workspace name as workstream, and use the real responsibility I assigned as title. Actually call task to register it and confirm with status. Do not overwrite other tasks or mix new business work into an old task's identity.
>
> First tell me whether onboarding is working and how you understand your responsibilities and boundaries, then continue the work I have already assigned. Preserve earlier task decisions, deliverables, and WIP. For unfinished work, save an exact checkpoint and next step; submit stable stages with real base/commit values and the complete changed-path list. Use MCP or the CLI with the same control directory, without creating another governance store. The CLI remains usable without MCP. The governance chat handles shared integration, and technical receipt does not replace business acceptance.

A new chat can own independent work or continue a task transferred from an existing chat. Registering a stage does not mean the entire professional task has ended. Use a new stable task_id for a later new task.

<a id="mcp"></a>

## 4. Configure MCP: recommended for governance, with CLI as a fallback

| Interface | What it is | Recommended use |
|---|---|---|
| MCP | Exposes TaskCarry as tools Codex can call directly, with names such as taskcarry_status and taskcarry_checkpoint. | Recommended for the governance chat; calls are more direct, while the model still decides the next action. |
| CLI | Codex runs TaskCarry commands through Python in the terminal. | Installation, diagnosis, and fallback when MCP is unavailable; professional chats can start with this interface. |

**Both interfaces call the same core and share the same control state. They are not separate governance systems or additional AI models.** MCP is not a prerequisite for continuing work. Newly created neighboring professional folders do not automatically inherit the governance directory's MCP configuration.

Paste into the governance chat:

```text
Please configure project-scoped TaskCarry MCP for `C:/TaskCarry/control` using `C:/TaskCarry/runtime/Scripts/python.exe`.
First check the installation and this project's setup-generated .taskcarry/codex.mcp.toml. Merge its TaskCarry server configuration into `C:/TaskCarry/control/.codex/config.toml`, preserving other existing settings and leaving user-global configuration unchanged. Retain the generated isolated UTF-8 launcher and its explicit package path; it binds --project to this one control directory and starts the mcp subcommand.
If Codex does not yet trust this project, or the chat must be reopened or configuration reloaded, tell me the specific step. Then actually call taskcarry_doctor and taskcarry_status to confirm that the tools are available and point to this project. Generating a configuration file alone does not prove connection.
If this chat cannot configure the connection or has not loaded the tools, preserve the CLI workflow and state exactly what remains. Other professional chats need their own configuration pointing to the same control if they want MCP; using the CLI is the default starting route for them.
```

The CLI fallback can be run directly:

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' status
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' doctor
```

Project configuration, trust, and loading behavior depend on the Codex version in use. See the [official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp).

<a id="delivery"></a>

## 5. First governance pass: review current work and see the result

After installation and the relevant chats are connected, paste the following into the current governance chat. This uses the same Skill and tools as scheduled governance; it does not start an Automation. You can also do this before creating professional chats: an empty project can be ready for your first task.

```text
Please run one bounded governance pass for the registered project at `C:/TaskCarry/control` using taskcarry-governance-reconcile and the installed tools. Use the same workflow for later scheduled runs; do not create or trigger a schedule for this pass.
Check doctor, the actual available connection, agenda and relevant status detail. Derive the registered workspaces and tasks from the project records and PROJECT_MAP.md; do not assume three chats or read unrelated history.
Distinguish results already accepted, explicit stages ready for intake, unfinished checkpoints, paused/waiting tasks, and concrete conflicts. Retain unchanged work without requeuing it or asking me to finish it.
For authorized stable stages, check real base/commit and complete changed paths. Plan reconcile with limit 20 (maximum 100), inspect the frozen selection, then execute and verify actual effects. Keep remaining work visible for a later pass. Reuse already-applied effects and continue only missing steps. Cumulative replacement requires task, ancestry and coverage evidence.
Use adopt only where an actual task dependency needs accepted business/code results and the workspace can safely update without an active writer. Preserve local commits, staged, unstaged and new files; leave a concrete next condition for a busy or conflicting workspace.
Show the result directly in this chat: installed version and project directory; CLI/MCP connection actually checked; registered workspaces/tasks; accepted stages, retained work and this pass's effects; current remaining work; my next step or a clear statement that no action is needed.
If there are no tasks or deliverables, report that the installation and connection are ready to receive work, naming any actual setup gap. Do not create sample tasks, commits or deliveries to populate a report. Plan completion does not mean project completion or a verified scheduled trigger.
```

**What you should see:** a concise chat result grounded in actual checks. It separates installation, connection and this pass's work. If project inputs are still missing, it names them. Later schedule setup reuses this result instead of requiring another trial pass.

In everyday work, professional chats deliver at natural stages or save unfinished work as checkpoints. The same governance AI and host report meaningful changes and requested summaries in the chat; no separate report service or state page is needed.

<a id="automation"></a>

## 6. Create scheduled governance: read the actual registered scope

One scheduled governance task is enough to start. A daily 06:00 run is a useful initial schedule for intake, a morning report, and applicable workspace updates. Increase frequency later if more frequent intake is needed. Local automation depends on the availability of the computer and Codex; the toolkit does not provide an independent cloud scheduler.

Paste into the governance chat:

```text
Please create a daily 06:00 scheduled governance task for this project in this governance chat, using the actual current local time zone and targeting `C:/TaskCarry/control`. Keep my model and native permission settings.
Reuse the first governance pass from Chapter 5; do not trigger an extra Automation for verification. Save the same taskcarry-governance-reconcile Skill and bounded tool workflow in the scheduled instructions, normally with reconcile limit 20.
Read status and PROJECT_MAP.md for the actual registered professional workspaces, business tasks and explicitly bound chats. List the baseline and technical preservation tasks separately. Access to project records does not mean access to every chat; without binding evidence report workspace/task counts. Use one registration per path and investigate duplicates before acting.
Each run must reread the registered scope instead of hard-coding agent-1 through agent-3 or requiring a new scheduled task whenever a chat is added. Include only objects explicitly connected to this project, without scanning unrelated or private chats.
Reuse valid receipts and handle new deliveries and specific unfinished operations. Judge relationships from existing tasks, checkpoints, stages, and file evidence, rather than repeatedly reporting paused or unchanged work as backlog. Check intake plans before execution and confirm actual effects afterward; do not replay completed work.
Use adopt only where an actual task dependency needs accepted business/code results and the workspace can safely update without an active writer, preserving local work. Reading shared progress or updating Skills does not require merging business branches. Skip only the busy or conflicting workspace. Use currently implemented recovery behavior and applicable experience rules to handle known problems within scope. For unknown problems, explain the actual impact and next step instead of repeatedly rerunning all governance.
Produce one concise morning report each day: new receipts, workspace updates, changes to current task state, and matters that really require my action. State clearly when no user action is needed. Report specific unfinished actions honestly rather than using one PASS to imply that everything is complete.
Use the host's official automation tool to create the task or update an existing task with the same purpose. Tell me its actual name, time zone, time, and target. Do not write a configuration file and call that a created automation. If this environment cannot create it, give me the exact UI steps required and the final task prompt.
```

This covers professional workspaces and tasks **already connected and registered**. Existing chats not yet connected must first complete Chapter 3. A task's `paused` state alone does not prove that no other program is writing files. Receiving plans default to 20 work items, at most 100; governance checks the frozen selection and reports remaining work separately. This does not set a hard AI-session duration limit.

<a id="private-git"></a>

## 7. Optional: a private Git memory repository

Private Git can preserve received deliverables and selected task memory. It stores what is actually committed and pushed; it does not automatically back up the entire computer, chat history, uncommitted files, or governance database.

Paste into the governance chat:

```text
Please prepare a private Git memory repository for the project managed by `C:/TaskCarry/control`.
First read the product's docs/en/remote-and-multicomputer.md, check existing remotes and the actual baseline, and preserve existing configuration. Identify the exact deliverables and selected task notes to include, as well as sensitive content, large files, and runtime state to exclude. If I need to choose an account, private repository, access permissions, or authorize publication, list the specific objects.
After I confirm the actual remote and upload scope, use the currently received baseline for exact commits and pushes, then verify the remote commit. Do not treat the active .taskcarry database, secrets, caches, or an entire workspace as the Git memory repository. Also provide a consistent backup method and recovery steps covering governance state and WIP, distinguishing Git recovery from recovery of the complete working state.
```

For detailed operations and recovery limits, see [Private Git and backup](remote-and-multicomputer.md#private-git).

<a id="multi-computer"></a>

## 8. Optional: parallel work on different computers

Start with **one integration computer and separate task branches on other computers**. Different computers can use different Codex accounts with appropriate access. Account login is not a task lock.

Paste into the governance chat:

```text
Please prepare instructions for sharing this project at `C:/TaskCarry/control` with a second computer, keeping this computer as the sole integrator for now.
Read the product's docs/en/remote-and-multicomputer.md. Using actual tasks, the selected remote, and file scopes, generate a ready-to-use continuation prompt for the second computer and an intake checklist for this one. Divide work by different professional responsibilities or independent subtasks, with one primary writer for each task and write scope. Do not let both computers write the same workspace or share live .taskcarry or .git state.
The second computer submits deliverables through its own separate branch, preserving the original base/commit, complete changed paths, and stage relationships. This computer obtains that evidence through a stable intake workspace, then advances the baseline through normal submit/reconcile using this computer's control. The two computers' local state does not merge automatically.
If this computer becomes unavailable, another computer may continue independent work within its authorization. Before changing the integrator, stop or isolate the old writer, reconcile effects already performed, then arrange takeover. When the original computer returns, check the latest state before restarting its previous scheduled tasks.
Tell me which actions, logins, or confirmations genuinely require the second computer, and what remains unverified. Preparing this plan does not change existing schedules.
```

This version has not completed a real two-computer end-to-end validation. Start with parallel work across separate professional responsibilities. See [Multi-computer operations](remote-and-multicomputer.md#multi-computer) for the full steps. The toolkit does not provide automatic leader election, cross-computer locks, or automatic migration of the complete transaction store.

<a id="check"></a>

## 9. What you should see when finished

| Item | Evidence of actual completion |
|---|---|
| Product installation | The dedicated runtime runs the installed version, and doctor succeeds. |
| Project onboarding | The goal, one control directory, actual integration baseline, and registered scope are clear. |
| New-project scaffold | A neutral baseline exists; the user assigns professional responsibilities and business tasks afterward. |
| Continuation in existing chats | Original tasks, deliverables, history, and WIP are retained, with a clear location for continued writes. |
| Parallel professional chats | Actual directories/branches match registration, and task ownership and write scopes are clear. |
| MCP | Real tool calls succeed; if not connected, the CLI works and the missing step is identified. |
| First governance result | The chat shows installation, connection, registered scope and actual bounded results; no deliveries means readiness, not invented work. |
| Scheduled governance | The official task is created; actual scheduled-run evidence confirms its execution results. |
| Private Git / multiple computers | Actual remotes and the second computer are checked for the chosen scope; a plan is not treated as completion. |

Users only need to continue their normal project work; they do not need to run development maintenance tests. See [Release boundaries](../RELEASE_BOUNDARIES.md) for the implemented scope. If a problem occurs, preserve the current state, check existing results, and continue only the missing steps.
