# TaskCarry

**Project memory and collaboration for AI tools.**

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[Download TaskCarry](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5) · [Start with the user manual](docs/en/windows-example.md) · [See the architecture](docs/en/architecture.md)

TaskCarry provides **project memory, workspace collaboration, and project workflow governance** for people working with AI tools. Bring ready stages into a shared project, preserve unfinished work, and resume supported interrupted operations from recorded and verified results. Task context, selected files, deliverable history, and next steps stay with the project across conversations and pauses.

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
| **Reviewable integration plans** | See which stages and files will join the project before carrying out the update. |
| **Workspace binding and conflict checks** | Check the registered workspace and expected state, coordinate the toolkit's own writes, and identify concrete conflicts. |
| **Work-in-progress preservation** | Retain supported local commits, staged changes, working files, and new files when adopting shared results. |
| **Interrupted-operation recovery** | Check what actually happened, reuse a recovery method when its conditions match, and complete supported missing steps without blindly repeating finished work. |
| **Durable review and maintenance evidence** | Reuse reviewed source relationships, track a selected round's receipts, and link a concrete defect to its tested fix and actual local setup. |

This governance focuses on project deliverables and their workflow. Host permissions and Agent authentication remain with your AI platform and operating environment; [the architecture](docs/en/architecture.md) explains how these responsibilities fit together.

Memory comes from the tasks, notes, files, and deliveries you or your AI assistant explicitly connect. TaskCarry does not automatically collect all private conversations or capture unsaved editor content.

## How people, AI, and tools work together

![People set direction, a governance chat coordinates, specialist workspaces advance in parallel, and TaskCarry retains project records](docs/assets/collaboration.en.svg)

Your independent **governance chat** maintains project memory and reviews connected progress. It uses the host AI to understand permitted sources, distinguish confirmed decisions from suggestions, and call TaskCarry tools. It can also coordinate project priorities if you choose. Keep giving work directly to your existing main or specialist chats; governance does not become a required dispatch gate.

TaskCarry stores records and performs the supported local operations. You retain decisions about project direction, priorities, business acceptance, and external delivery. The toolkit does not require a separate model API or train a model.

For example, software may have a usable module while experiments are paused and documentation is still a draft. Governance can receive the software stage and retain the other two tasks at their current positions. Nobody needs to mark the entire project complete just to preserve useful progress.

## The everyday workflow

![Work on tasks, save progress, offer a stable stage, receive it into the shared project, update selected workspaces, and continue](docs/assets/governance-flow.en.svg)

1. **Work in your task chat.** Continue the real task in its assigned workspace.
2. **Save a useful stopping point.** Record the current position and selected files when you pause.
3. **Offer a ready result.** Identify the stable version and the files it changes.
4. **Bring it into the project.** The governance chat reviews a plan and receives the stage through the tools.
5. **Continue from shared progress.** Update the workspaces that need those business changes, preserving supported local work and addressing concrete conflicts.

A received stage can be part of an unfinished task. A paused task can stay paused. Replacing an older stage requires a documented relationship and matching change history, so independent results are not discarded merely because a newer file exists.

## Start with one project

The confirmed download remains **taskcarry-0.2.0rc5-product.zip** on the [release page](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5). Use the instructions shipped with that package. This source tree prepares the **0.2.0rc6 candidate** and its [revised conversational onboarding guide](docs/en/windows-example.md); candidate preparation does not mean it has been published or installed.

The candidate's main path is for people already using Codex:

1. **Establish an independent governance chat.** Reuse a verified existing TaskCarry governance chat/control if present. Give a project locator and the product-package location, then send the guide's one prompt.
2. **Let governance connect existing work.** It inherits known outputs, decisions, tasks and continuation points, guides installation and remaining host actions, and suggests a useful division of work. Added specialists may be zero.
3. **Continue working in your usual chats.** Governance maintains memory and progress; temporary or ongoing project coordination is optional. At work boundaries, assistants save the relevant evidence and read the effective context before continuing.

The same conversation handles installation, governance responsibility and the first bounded review. If the host cannot complete an action, governance supplies the exact current manual step. Commands and separate transfer prompts live in the [fallback manual](docs/en/manual-setup.md), not in a parallel main route.

You do not need to learn the engine, inspect its database or run developer tests. Reports appear in the governance chat. Native connection, saved progress, delivery and acceptance have separate evidence; optional scheduling does not start during installation.

<img src="docs/assets/workspace-sidebar-example.png" alt="Example arrangement of governance and working chats; specialist count is optional" width="360">

This is an organization example. Existing working chats remain useful. If they share a directory, inspect active writers and preserve scoped WIP before arranging independent write areas.

## Build on the local workflow

- **Scheduled coordination:** use your host's scheduling feature to ask governance to review connected work and produce a useful summary. Installing TaskCarry does not create a schedule.
- **Private Git:** configure your own remote repository for selected committed results. File references help locate materials, but copying, backup, and remote synchronization remain explicit operations.
- **Additional AI tools:** CLI and MCP provide integration points around one engine. The Codex guide is the current concrete onboarding path; it does not establish that every MCP client, model, or AI platform has been verified.
- **Multiple computers:** the [guide](docs/en/remote-and-multicomputer.md) describes separate task branches and one integration computer. Real two-computer operation has not completed end-to-end validation; start after the local workflow is established.

TaskCarry uses Python 3.11+; Git is needed for Git workflows. It stores project state locally and includes four project Skills for setup, task delivery, governance, and recovery. Each control scope has one local store and one receiving baseline. Installation updates tools and Skills; adopting received business changes into a workspace is a separate, reviewed action. See [maintenance](docs/en/governance-maintenance.md) and [capabilities and limits](docs/RELEASE_BOUNDARIES.md).

## Documentation

| Guide | English | 简体中文 | 繁體中文 |
|---|---|---|---|
| Manual fallback | [Commands and handoffs](docs/en/manual-setup.md) | [手动后备](docs/zh-CN/manual-setup.md) | [手動後備](docs/zh-TW/manual-setup.md) |
| User manual | [Start here](docs/en/windows-example.md) | [从这里开始](docs/zh-CN/windows-example.md) | [從這裡開始](docs/zh-TW/windows-example.md) |
| Architecture | [How it works](docs/en/architecture.md) | [架构说明](docs/zh-CN/architecture.md) | [架構說明](docs/zh-TW/architecture.md) |
| Maintenance | [Maintain a project](docs/en/governance-maintenance.md) | [维护项目](docs/zh-CN/governance-maintenance.md) | [維護專案](docs/zh-TW/governance-maintenance.md) |
| Private Git and multiple computers | [Guide](docs/en/remote-and-multicomputer.md) | [说明](docs/zh-CN/remote-and-multicomputer.md) | [說明](docs/zh-TW/remote-and-multicomputer.md) |

[How the workflow became simpler](docs/en/governance-evolution.md)

[CLI / MCP reference](docs/COMMANDS.md) · [Public Skills](skills) · [Validation records](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc5/docs/VALIDATION.md)

## Join in

Questions, real use cases, clearer examples, translations, and code improvements are welcome. Start with [Issues](https://github.com/bryan123466/taskcarry/issues) or the [contribution guide](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc5/CONTRIBUTING.md). Remove private project information before sharing; the [security guide](SECURITY.md) explains what to keep out of a report.

## License

The public code, documentation, templates, and examples use the [MIT license](LICENSE), including commercial reuse under its terms. Your own project and materials remain yours to manage; using TaskCarry does not make them public. Dependencies and services retain their own terms. See [license scope](LICENSE_SCOPE.md).
