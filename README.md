# TaskCarry

**Project memory and collaboration for AI tools.**

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[Get TaskCarry](START_HERE.md#download) · [First-time setup](docs/en/windows-example.md) · [Update an existing installation](docs/en/updating.md)

TaskCarry gives projects already advancing in AI chats **durable memory and a continuing governance workflow**. An independent governance chat inherits confirmed decisions, understands selected new progress, keeps task relationships current, delivers guidance to the relevant workbenches, and checks saving and recovery. Your existing chats keep doing their work; their outputs and unfinished positions stay connected beyond one conversation.

Use it with a project already advancing in your AI chats, whether one long-running conversation or several parallel workstreams. Keep prior outputs, decisions and unfinished work. Your AI tool helps do the work; TaskCarry gives it a durable local record and a way to bring results together. An extra specialist chat is useful only when the work benefits from it.

**The current step-by-step examples use Codex.** The toolkit exposes the same local engine through a command line and MCP, providing a foundation for other AI-tool integrations. Each host still needs its own connection and workflow verification.

## Why add TaskCarry to Git and project instructions?

Git already keeps file history. Project instructions such as AGENTS.md already explain how an AI assistant should work. A handoff message already helps the next conversation get started. TaskCarry connects these useful pieces to the changing state of a project.

| What you already use | What it helps with | What TaskCarry adds |
|---|---|---|
| Git | Versions, branches, and file changes | Which task a result belongs to, which stage was received, and what still needs to continue. |
| AGENTS.md and Skills | Working practices and role instructions | Persistent records of the work actually saved, offered, integrated, or paused. |
| Conversation summaries | Context for a person or another chat | Task records and file references you can update and revisit beyond one conversation. |
| Manual handoffs | Coordination between a few workstreams | Reviewed plans, recorded operation results, and supported recovery when work is interrupted. |

For a short task in one chat, your existing tools may be enough. TaskCarry becomes useful when you repeatedly need to answer: **Where did we stop? Which result is current? What has already joined the project?**

## Remember the project. Coordinate results. Govern progress.

### Remember the project

Keep task goals, recorded decisions, current position, and next steps outside chat context. Save selected files and continuation notes when a task pauses, and read a focused agenda without losing paused work or completed history. Material references record where larger files live and whether a specified backup matches, so every file need not go into Git.

### Coordinate results

Give parallel tasks independent workspaces, then bring ready results into a shared project version. A useful stage can be delivered while its task continues. Explicit version relationships and matching change history show when a later stage replaces an earlier one, while keeping independent results available.

### Govern how the project moves forward

Project workflow governance connects the work people and AI produce with clear plans, checked updates, and recorded outcomes.

| Capability | What it helps you do |
|---|---|
| **Understand connected work** | Review selected source revisions, distinguish facts from judgments, and retain decisions and dependencies without reopening finished history. |
| **Keep working chats aligned** | Publish versioned private workbench guidance, preserving professional instructions and Git WIP; distinguish publication from actual consumption. |
| **Govern a complete cycle** | Retain ownership, intended effects, actual results and continuation points; use a morning report and quieter absorption slots. |
| **Receive exact stages** | Review commits, changed paths and task relationships before receiving business results; adopt them into selected workspaces while preserving supported local work. |
| **Recover selected project work** | Verify consistent state/objects, original Git history and layered WIP, explicit materials and standby recovery before a sole-writer handoff. |
| **Maintain with evidence** | Link problems to verified fixes, distinguish update discovery from installation, and report source, native-host and natural-trigger evidence separately. |

This governance focuses on project deliverables and their workflow. Host permissions and Agent authentication remain with your AI platform and operating environment; [the architecture](docs/en/architecture.md) explains how these responsibilities fit together.

Memory comes from the tasks, notes, files, and deliveries you or your AI assistant explicitly connect. TaskCarry does not automatically collect all private conversations or capture unsaved editor content.

## How people, AI, and tools work together

![People set direction, a governance chat coordinates, specialist workspaces advance in parallel, and TaskCarry retains project records](docs/assets/collaboration.en.svg)

Your independent **governance chat** maintains project memory and reviews connected progress. It uses the host AI to understand permitted sources, distinguish confirmed decisions from suggestions, and call TaskCarry tools. It can also coordinate project priorities if you choose. Keep giving work directly to your existing main or specialist chats; governance does not become a required dispatch gate.

The product has three responsibility layers: **Core** supplies verifiable shared operations; the **capability layer** combines packaged Skills, project methods and available host tools; the **user project layer** retains your facts, decisions, relationships, files and progress. Public updates preserve your project rules and memory. Core can be reinstalled, but restoring your project requires its actual state, objects, Git history/WIP, materials and capability versions. See [how the three layers work together](docs/en/architecture.md).

TaskCarry stores records and performs the supported local operations. You retain decisions about project direction, priorities, business acceptance, and external delivery. The toolkit does not require a separate model API or train a model.

For example, software may have a usable module while experiments are paused and documentation is still a draft. Governance can receive the software stage and retain the other two tasks at their current positions. Nobody needs to mark the entire project complete just to preserve useful progress.

## The everyday workflow

Governance keeps decisions, dependencies and current guidance aligned while you work in your existing chats. The following flow applies when a stable set of Git changes is ready to join the shared project; an ordinary progress update does not require a delivery or code merge.

![Work on tasks, save progress, offer a stable stage, receive it into the shared project, update selected workspaces, and continue](docs/assets/governance-flow.en.svg)

1. **Work in your task chat.** Continue the real task in its assigned workspace.
2. **Save a useful stopping point.** Record the current position and selected files when you pause.
3. **Offer a ready result.** Identify the stable version and the files it changes.
4. **Bring it into the project.** The governance chat reviews a plan and receives the stage through the tools.
5. **Continue from shared progress.** Update the workspaces that need those business changes, preserving supported local work and addressing concrete conflicts.

A received stage can be part of an unfinished task. A paused task can stay paused. Replacing an older stage requires a documented relationship and matching change history, so independent results are not discarded merely because a newer file exists.

<a id="start-with-one-project"></a>

## Install or update TaskCarry

### First time using TaskCarry

[Get the complete product package](START_HERE.md#download), then follow the [three-step guide](docs/en/windows-example.md):

1. **Establish governance.** Put the package under a local TaskCarry folder, open an independent Codex chat there and send the guide's single prompt.
2. **Complete setup through conversation.** Governance inherits selected work, prepares task/workspace/Git bindings, verifies native MCP and current workbench views, performs the first governance cycle and an isolated recovery rehearsal, and configures the daily rhythm and official update checks. It gives you only the necessary trust, login or reload action.
3. **Review the evidence and continue.** Receive the inherited decisions, chat/role/task map, connection, saving, recovery and update results, remaining conditions and next actions. Complete setup and verified natural scheduling are distinct; configuration, trigger, AI execution and report delivery each need evidence. See [the feedback you should receive](docs/en/user-feedback-examples.md).

Keep working in your original chats. Governance maintains project memory; ongoing project coordination is optional, and you may need no additional specialist chats.

### Already using TaskCarry

Return to your existing governance chat and send the prompt in the [update guide](docs/en/updating.md). It checks your installation, preserves project records and settings, carries out the applicable update, and verifies the result. Keep the same project and governance home.

If the host needs you to complete an action, the assistant supplies that one step. Detailed commands are in the [manual fallback](docs/en/manual-setup.md); changes between releases are in the [release notes](docs/RELEASE_0.2.0rc7.md).

<img src="docs/assets/workspace-sidebar-example.png" alt="Example arrangement of governance and working chats; specialist count is optional" width="360">

This is an organization example. Existing working chats remain useful. If they share a directory, inspect active writers and preserve scoped WIP before arranging independent write areas.

## Build on the local workflow

- **Standard local governance:** local Git, workbench publication/consumption, a first complete cycle and recovery rehearsal, official release checking, and two or three daily original-chat slots: one report plus one or two absorption periods. Missing host steps stay explicit. A new release is evaluated before installation.
- **Private Git:** configure your own remote repository for selected committed results. File references help locate materials, but copying, backup, and remote synchronization remain explicit operations.
- **Additional AI tools:** CLI and MCP provide integration points around one engine. The Codex guide is the current concrete onboarding path; it does not establish that every MCP client, model, or AI platform has been verified.
- **Multiple computers:** selected recovery sets can rebuild an independent standby copy; separate task branches can return exact outputs to one governance writer. Transfer the writer role explicitly. [The guide](docs/en/remote-and-multicomputer.md) separates local recovery, remote transport and actual second-host evidence; real two-computer end-to-end validation remains a separate condition.

TaskCarry uses Python 3.11+ and includes four project Skills for setup, task delivery, governance, and recovery. Standard onboarding prepares local Git; the lower-level ability to checkpoint ordinary files remains available for compatibility and recovery. Each control scope has one local store and one receiving baseline; a user-defined project can connect multiple existing sources without silently merging them. Installation updates tools and Skills; adopting received business changes into a workspace is a separate, reviewed action. See [maintenance](docs/en/governance-maintenance.md) and [capabilities and limits](docs/RELEASE_BOUNDARIES.md).

## Documentation

| Guide | English | 简体中文 | 繁體中文 |
|---|---|---|---|
| Manual fallback | [Commands and handoffs](docs/en/manual-setup.md) | [手动后备](docs/zh-CN/manual-setup.md) | [手動後備](docs/zh-TW/manual-setup.md) |
| User manual | [Start here](docs/en/windows-example.md) | [从这里开始](docs/zh-CN/windows-example.md) | [從這裡開始](docs/zh-TW/windows-example.md) |
| Existing users | [Update TaskCarry](docs/en/updating.md) | [更新指南](docs/zh-CN/updating.md) | [更新指南](docs/zh-TW/updating.md) |
| Feedback examples | [What users should hear](docs/en/user-feedback-examples.md) | [反馈示例](docs/zh-CN/user-feedback-examples.md) | [回饋範例](docs/zh-TW/user-feedback-examples.md) |
| Architecture | [How it works](docs/en/architecture.md) | [架构说明](docs/zh-CN/architecture.md) | [架構說明](docs/zh-TW/architecture.md) |
| Maintenance | [Maintain a project](docs/en/governance-maintenance.md) | [维护项目](docs/zh-CN/governance-maintenance.md) | [維護專案](docs/zh-TW/governance-maintenance.md) |
| Private Git and multiple computers | [Guide](docs/en/remote-and-multicomputer.md) | [说明](docs/zh-CN/remote-and-multicomputer.md) | [說明](docs/zh-TW/remote-and-multicomputer.md) |

[How the workflow became simpler](docs/en/governance-evolution.md)

[CLI / MCP reference](docs/COMMANDS.md) · [Public Skills](skills) · [Validation records](docs/RELEASE_0.2.0rc7.md)

## Join in

Questions, real use cases, clearer examples, translations, and code improvements are welcome. Start with [Issues](https://github.com/bryan123466/taskcarry/issues) or the [contribution guide](https://github.com/bryan123466/taskcarry/blob/main/CONTRIBUTING.md). Remove private project information before sharing; the [security guide](SECURITY.md) explains what to keep out of a report.

## License

The public code, documentation, templates, and examples use the [MIT license](LICENSE), including commercial reuse under its terms. Your own project and materials remain yours to manage; using TaskCarry does not make them public. Dependencies and services retain their own terms. See [license scope](LICENSE_SCOPE.md).
