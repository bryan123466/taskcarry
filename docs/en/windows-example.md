# Windows guide: connect your existing Codex project

[简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md) · [Everyday operations](operation-manual.md) · [Manual fallback](manual-setup.md)

This guide is for people already working in Codex. Keep your existing project and working chats; add an independent governance chat that helps maintain project memory and progress. You can continue to give work directly to your original chats.

**Version:** this checkout describes the **0.2.0rc6 candidate**. The current published download remains [0.2.0rc5](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5); use the manual shipped with the package you actually install. Candidate documentation does not mean that rc6 is published or installed. These examples use Codex on Windows; other hosts need their own connection verification.

- [1. Establish a governance chat](#choose)
  - [Send one onboarding prompt](#install)
- [2. Let governance connect your existing work](#agents)
  - [Keep the original chats and decisions](#existing)
  - [Complete the actual tool connection](#mcp)
- [3. Continue in your usual way](#delivery)
  - [What successful onboarding looks like](#check)
  - [Optional additions](#automation)

<a id="windows-guide-connect-a-real-project"></a>
<a id="0-prepare-a-project-name-a-short-description-and-three-directories"></a>
<a id="1-install-create-a-governance-chat-and-choose-control"></a>
<a id="recommended-ask-the-governance-chat-to-install-it"></a>
<a id="manual-installation-commands-for-the-same-route"></a>
<a id="2-set-the-governance-chats-responsibilities"></a>
<a id="choose"></a>
<a id="governance"></a>

## 1. Establish a governance chat

If this project already has a working TaskCarry governance chat, return there and ask it to check and continue the existing connection. Otherwise create a **new independent chat** named, for example, “Project governance.” Your existing main and specialist chats keep their work and history.

Choose a separate governance folder. For a first installation, the synthetic example is `C:/TaskCarry/control`; extract the selected product ZIP into `C:/TaskCarry/toolkit`. The RC6 archive includes its version directory, so the product root containing `START_HERE.md`, `packages/`, `docs/` and `skills/` is `C:/TaskCarry/toolkit/taskcarry-0.2.0rc6`. Use that actual product root in the prompt below. Open the new chat in `control`. Existing projects keep their business files where they are. The assistant can prepare directories when its host permissions allow; [manual preparation](manual-setup.md#install) is available if needed. Use a different root for an unrelated project; do not move an already bound control as a shortcut.

You only need a project locator: a directory, a relevant chat name/link, or both. A short name/description helps if it is not already in the project. You do not need to decide a task ID, branch name or number of specialist chats first.

<a id="install"></a>

### Send one onboarding prompt

Replace the two fields and paste this into the governance chat. Installation and taking on governance responsibility are one conversation.

> Please establish this chat as TaskCarry governance for my existing project, responsible for governance and project memory.
>
> Project locator: **[Project directory and/or relevant existing chats]**. Extracted product directory: **[Directory containing START_HERE.md and packages]**.
>
> Read that package's START_HERE.md, taskcarry-project-setup Skill and its references/onboarding.md. Check the actual host capabilities, installation and governance records. Reuse an existing valid TaskCarry governance chat/control; preserve my original working chats, task identities, files and unfinished work.
>
> Read relevant permitted sources to recover project goals, completed outputs, effective decisions, responsibilities and the exact continuation points. Separate confirmed facts from your suggestions and missing evidence. Complete the authorized installation and workbench connection through conversation, keeping a resumable checklist. If you cannot perform a host action, give me only the current necessary action with the destination and content filled in.
>
> Give me one project assessment, useful work-division suggestions and next steps. Additional specialist chats may be zero. Explain how you can optionally coordinate the project over time; keep my ability to work directly in each chat. Do not treat this initial advice as permission for ongoing dispatch or scheduling.
>
> Finish with a bounded review: what was inherited, what is actually installed/connected, what remains, how working chats save and read relevant progress, and what I should do next. Do not create sample deliverables or replay work already completed.

**If you are already partway through:** say “Continue onboarding from the saved checklist.” Governance checks actual results and completes missing steps. You do not need a second role prompt or a reinstall for a pending reload.

<a id="3-configure-professional-task-chats-continue-existing-chats-or-create-new-ones"></a>
<a id="31-existing-ongoing-chats-preserve-history-and-connect-current-state"></a>
<a id="32-create-new-professional-task-chats-add-1n-as-needed"></a>
<a id="4-configure-mcp-recommended-for-governance-with-cli-as-a-fallback"></a>
<a id="agents"></a>

## 2. Let governance connect your existing work

Governance first checks what already exists, then guides the remaining configuration. An empty governance folder does not mean the business project is new. For a genuinely new project, the same conversation can establish initial goals and a baseline after checking that no earlier work needs to be retained.

<a id="existing"></a>

### Keep the original chats and decisions

The first handover should identify existing outcomes, decisions with sources, current tasks and their owners, paused work, and the next step. Already accepted work stays historical evidence. A proposed interpretation remains a draft until the relevant correction is confirmed; it does not silently replace the effective decision.

Governance uses the related context it can actually access. If a previous chat is unavailable, it supplies a short prepared handoff for that chat; [the manual fallback](manual-setup.md#existing) contains the separate prompts. It does not scan every private conversation or promise to watch all chats continuously.

Work division follows actual needs. One existing work chat plus governance may be sufficient. Add specialists when outputs, parallel value, write ownership and dependencies justify it. If several chats share a directory, check active writers and preserve their work before changing ownership or creating separate workspaces. A new chat name alone does not isolate writes.

<a id="mcp"></a>

### Complete the actual tool connection

All workbenches for this project use the same control. Governance generates each workbench's connection materials and four Skills, with the correct runtime and registered task/workspace. Files can live in the workbench directory while MCP binds the original control. It does not initialize another store there.

The assistant merges the generated server into the target directory's `.codex/config.toml` (for example, `C:/TaskCarry/control/.codex/config.toml` for governance), preserving existing settings. Open/select that same directory in the target Codex chat, complete any required project trust, then restart/reload MCP using the host's supported controls. Another directory's config does not connect this chat. If a host action needs you, the assistant gives the exact current step and continues after your reply. [Manual setup and verification](manual-setup.md#mcp) gives the supported configuration location, official sources and fallback; setup itself does not activate the host.

Connection results have three separate meanings: **materials generated**, **host loaded**, and **native doctor/status calls succeeded in that window**. A successful isolated CLI call is useful fallback evidence; it does not prove native MCP is connected. Governance records the actual version, interpreter, module and control/task binding. It never infers that another window loaded the same package.

<a id="5-first-governance-pass-review-current-work-and-see-the-result"></a>
<a id="9-what-you-should-see-when-finished"></a>
<a id="delivery"></a>

## 3. Continue in your usual way

Work directly in the original or newly agreed professional chats. At a meaningful pause, result or decision change, the assistant saves the relevant progress and next step; before continuing, it reads the named task and related effective decisions. Governance summarizes connected evidence and checks gaps. Sharing progress does not automatically merge every workspace's code.

You can say “Continue my last unfinished work,” “Save this stopping point,” or “Show the current progress of the connected tasks.” A stable Git stage can be offered separately from unfinished work. Ordinary document checkpoints save selected files without Git; a complete non-Git delivery/intake workflow is a later capability, not implied by file saving.

| Working mode | Governance helps with | Your day-to-day work |
|---|---|---|
| Governance and memory, the default | Evidence, effective decisions, task progress, continuation and reviewed reception | Continue directly in working chats; consult governance as needed. |
| Also coordinate the project, optional | The same memory plus priorities, dependencies and division-of-work suggestions | Discuss overall plans there while still working directly elsewhere. |

You can change this preference without rebuilding the project. An initial project assessment does not automatically enable ongoing coordination or a schedule.

<a id="check"></a>

### What successful onboarding looks like

- The inherited goal, decisions, tasks, existing results and unfinished positions are clear; suggestions and unknowns remain labelled.
- One control and any required receiving baseline are identified; existing work and configuration are preserved.
- Actual installation, each host connection and any remaining action have separate evidence.
- Each working chat knows how to read relevant context, save progress and continue; added specialists may be zero.
- The first bounded review reports actual results or readiness. A checkpoint is not a delivery, reception is not business acceptance, and a plan is not proof of execution.

<a id="6-create-scheduled-governance-read-the-actual-registered-scope"></a>
<a id="7-optional-a-private-git-memory-repository"></a>
<a id="8-optional-parallel-work-on-different-computers"></a>
<a id="automation"></a>

### Optional additions

Scheduling is optional. If requested, governance reuses the first review and configures the host's actual scheduling capability; a saved prompt is not a verified scheduled run. See [scheduled governance](automation.md).

<a id="private-git"></a>

[Private Git and backups](remote-and-multicomputer.md#private-git) preserve the content actually included and verified. A recorded file path is not a backup, and ordinary Git pushes do not preserve a live control database or all WIP.

<a id="multi-computer"></a>

[Multiple computers](remote-and-multicomputer.md#multi-computer) require separate validation. This release does not provide automatic leader election or a shared multi-writer database. Adding MCP does not by itself establish every platform or multi-computer workflow.

For everyday choices, see [the operation index](operation-manual.md). For exact commands or a blocked step, use [manual setup](manual-setup.md) and [CLI/MCP reference](../COMMANDS.md).
