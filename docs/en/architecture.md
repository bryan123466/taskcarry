# How the toolkit keeps a project moving

[简体中文](../zh-CN/architecture.md) · [繁體中文](../zh-TW/architecture.md) · [Home](../../README.md)

When several local AI workspaces advance a project, each needs to know what to do next without losing its earlier work. TaskCarry gives them shared task records and a governance chat that brings ready results together. Files and progress remain on your computer; the project does not depend on one chat remembering everything. Codex is the first documented host setup; other local AI tools can use the same CLI/MCP interfaces after their connection and capabilities are verified.

## Project workflow governance

TaskCarry combines project memory, workspace collaboration, and governance of the work people and AI produce together. Its focus is how a task keeps its current position, how a stage joins the shared project, and how an interrupted operation continues. This provides a practical workflow for a long-running project across multiple chats or Agents.

The governance chat interprets supplied task information and reviews the proposed integration plan. The tools bind that plan to registered workspaces, specific versions, changed paths, and expected state. They record actual results, preserve supported unfinished work, and check applicable recovery methods before continuing missing steps. People retain project direction, priorities, business acceptance, and external-delivery decisions.

Workspace identity here means the registered directory and repository, not authentication of an Agent or a person. Toolkit locks coordinate its own writes; other editors and Git commands still need to respect the workspace's writing responsibility. AI-platform permissions, identity security, and operating-system isolation remain with the host environment. See [security and project data](../../SECURITY.md) for that scope.

## Who does what

You set the direction, divide responsibilities, and decide whether a result meets your needs. Professional chats work in their own registered directories. The governance chat uses AI to interpret their task records and deliverables, then calls the tools to save state, collect stages, and update workspaces.

| Part | What it does for you |
|---|---|
| Task records | Keep the goal, current position, decisions, saved progress, and next step together. |
| Git workspaces | Give parallel tasks separate working files and retain their change history. |
| Receiving baseline | Hold the stages already collected into the shared project. |
| CLI and MCP | Offer two ways to call the same local tools and records. |
| Project Skills | Explain when and how the chats should save progress, deliver work, and handle a known problem. |
| Standard host scheduling | Wake the governance chat at configured times to perform the same workflow. |

The toolkit keeps four things distinct: the installed package supplies tools and Skills; the control project's `.taskcarry` directory retains durable task state; shared progress is read from those records; and business deliverables remain in their Git workspaces. Updating the package or Skills, or reading `status`, does not merge business Git history or advance a workspace's `HEAD`. Bringing received business results into a working workspace is an explicit `adopt` operation. See [governance maintenance](governance-maintenance.md) for package updates and recovery.

## From unfinished work to the next stage

1. **Work on the task.** A professional chat uses its registered workspace and stable task record.
2. **Save a useful pause point.** A checkpoint records selected files already saved to disk and where to continue. Within its selected scope, a Git checkpoint keeps the committed version, staged changes, working files, and new files distinguishable.
3. **Offer a ready stage.** The chat identifies the Git commit, its starting commit, and the complete changed-path list. Later edits in that workspace do not silently change the offered stage.
4. **Bring it into the shared project.** Governance prepares a plan against the current receiving baseline, checks its scope, and executes it. Before replacing a plan, it checks the actual effects of unfinished operations and continues supported missing steps. A new plan is needed when an external change invalidates the old plan and there is no existing operation that can safely continue.
5. **Adopt business results where needed.** An explicit `adopt` plan brings received business changes into a selected workspace while preserving supported local work. Installing tools or Skills does not require every worktree to adopt business changes. A busy workspace or a concrete conflict keeps its own next step while other independent tasks continue.
6. **Continue.** The records show what was collected, what is still in progress, and what should happen next. You still decide whether the result satisfies the business or professional requirements.

## Keep history without repeating old work

A pause remains a pause; an unchanged task does not become new backlog on every run. Old stages remain traceable after a newer cumulative stage replaces them. Before replacing one, the tools require evidence that the newer stage belongs to the same task and registered workspace, descends from the earlier commit, and covers its changed paths. A newer filename or date alone is not enough; independent results remain separate.

After an interrupted operation, governance checks what actually happened before continuing. It reuses valid records and completes only the missing steps supported by the tools, rather than assuming that a missing reply means the whole operation failed.

## Reuse experience where it applies

An experience record describes a known problem and an available recovery action. The tools check its failure code, operation, version, task scope, and enabled state before applying it. This can help with a repeated problem under matching conditions. It does not turn a written note into a new repair capability or execute arbitrary scripts from that note.

For an unfamiliar problem, governance explains the concrete obstacle and next step. A general prevention fix still requires a change to the shared software and verification before it is installed; recording experience alone does not install that fix or guarantee that the model will select it.

## Where the records live

The project's `.taskcarry` directory stores its task database, events, experience records, and selected-file snapshots. Keep these as project data, with suitable backups. Do not publish the database or edit it to make an incomplete operation look successful.

The tools run locally on one computer. Separate worktrees support parallel tasks; multi-computer work needs the explicit branch-based handoff described in the manual. The toolkit does not provide distributed locks, automatic remote push or deployment, or guaranteed recovery of effects in external services.

AI comes from your chosen local AI tool. TaskCarry does not train a model or require a separate model API. Its current setup generates Codex project integration files. Other hosts need their own configuration and instruction-loading checks; MCP availability alone does not verify a host, grant file access or supply scheduling. Reports are produced in the governance chat from the same project records, without a separate reporting service or state page. See [practical capabilities and limits](../RELEASE_BOUNDARIES.md).


## Standard local governance and task continuation

Complete onboarding includes local governance Git, real task/workspace/Git bindings for ongoing windows, native per-window connection checks, original-chat schedule configuration/readback and an official update check. Private remotes and cloud storage remain optional. Historical-source chats do not need active workspaces. Large external files need explicit references and backup coverage; a file reference is not a saved copy.

Use `context` for a selected task. It returns source-qualified identity, task state, latest checkpoint and next step, paginated related records, selected issue/fix references and missing evidence. Same local IDs from different sources stay distinct. Output and record payload reads are bounded; SQL still counts matching index entries, so this is not a fixed latency guarantee. Oversized records are explicitly omitted. Old state needs explicit `upgrade` for the derived task index; reading context never performs that migration. Regular SQLite reads may create coordination sidecars but do not publish records or events.

A real project can span several directories, repositories and existing state sources. Keep their routes and local identities; one source still has one receiving baseline. Sharing context or maintaining the package does not merge business Git branches or create a multi-store transaction.
