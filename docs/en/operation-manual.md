# Workflow overview and configuration choices

[Start with conversational onboarding](windows-example.md) · [Manual fallback](manual-setup.md) · [简体中文](../zh-CN/operation-manual.md) · [繁體中文](../zh-TW/operation-manual.md)

Use this page for everyday work after setup. For initial setup, see [First installation](windows-example.md); to update an existing installation, return to your original governance chat with the [update prompt](updating.md).

- [Onboarding and working modes](#onboarding)
- [Responsibilities](#responsibilities)
- [Save, read and continue work](#continuation)
  - [Understand what a result proves](#evidence)
- [MCP, CLI and scheduling](#connection)
- [Optional extensions](#options)

<a id="onboarding"></a>

## One recommended onboarding path

Create an independent governance chat for the existing project, or reuse a verified existing TaskCarry governance chat/control. Send the [single onboarding prompt](windows-example.md#install). Governance inherits project context, installs or reuses the tool and guides remaining connections; users need not decide technical IDs or a specialist count first.

Governance and memory are the default responsibilities. A one-time project assessment helps onboarding; temporary or ongoing project coordination is optional. Keep working directly in the original main or specialist chats. Changing the coordination preference uses the same memory and task identities. Added specialists may be zero.

The assistant reads permitted, related evidence and identifies missing history. Candidate interpretations and suggestions stay separate from effective confirmed decisions. An empty governance folder does not establish a new business project. Keep historical completed work and WIP in their actual places.

## Responsibilities

| Participant or component | Responsibility |
|---|---|
| User | Project direction, business decisions, acceptance and actions requiring authorization. |
| Governance chat | Maintain project memory and evidence, review connected progress and receive explicit stages through plans; coordinate priorities if chosen. |
| Working chat | Read related effective decisions, advance the task, save meaningful progress and deliver stable stages precisely. |
| Receiving baseline | A dedicated clean Git workspace for receiving stages; no specialist WIP. |
| TaskCarry engine | Persist records, check conditions and perform supported checkpoint/reception/adoption/recovery operations. |
| Host | AI interpretation, actual chat access/creation, configuration loading, permissions and optional scheduling. |

Keep one main writer for each task/write scope. Others may review or own distinct nonoverlapping subtasks. Separate chats are not automatically separate workspaces. Inspect real ownership and active writers before changing their arrangement.

<a id="continuation"></a>

## Initial inventory and everyday continuation

Work chats read the named task, latest relevant checkpoint and effective decisions before continuing. At a meaningful result, decision change or pause, save selected task-owned files, findings, source references and next steps. Governance uses those records to maintain shared understanding, requesting only changed or missing related context. Host access to old chats is checked separately; there is no automatic full-history monitor.

Keep a sourced, versioned understanding candidate until a correction is confirmed. Preserve the earlier effective version and identify affected tasks when updating it. This method uses existing project files and task/checkpoint/artifact records; it is not a separate decision database or a new task revision API.

<a id="evidence"></a>

### Understand what a result proves

| Situation | Appropriate record or action |
|---|---|
| Older output already included in the trusted baseline | Preserve provenance and inclusion; do not queue it again. |
| Unfinished or uncommitted work | Save a checkpoint and exact continuation point; do not call it delivery. |
| Stable explicit Git stage | Verify base, commit, task and complete path set; preview reception before execution. |
| Ordinary document project | Save selected files without Git; general non-Git deliverable exchange/intake is not implemented by that checkpoint. |
| Paused, waiting or unchanged task | Keep its position without creating reminders or new backlog. |
| Task needs accepted code | Preview adoption for that dependency and preserve local commits/index/worktree/new files. Reading progress alone needs no merge. |
| Interrupted operation | Verify actual effects and original identity; complete supported missing steps. |

The map and notes describe the project; engine records and actual files establish effects. A checkpoint, delivery, reception, adoption and business acceptance are different. A recorded artifact path is not a verified backup.

<a id="connection"></a>

## MCP, CLI and scheduled governance

MCP exposes engine actions directly to the host AI. The isolated fixed-runtime CLI uses the same control when native tools are unavailable. Neither requires a separate model service. Generated connection files, host loading and native doctor/status calls are separate evidence. Each workbench must verify its own actual imported package and binding.

Registered workbench setup can put its four Skills and connection materials in the host directory while binding the original control. `target`, `workspace` and `task_id` are provided together and checked against existing registration. No second control is initialized. The generated fragment pins the selected package with isolated UTF-8 startup; preserve it when merging active configuration. See [manual binding and verification](manual-setup.md#mcp).

The initial bounded governance pass reports actual results in the chat. If scheduling is requested later, reuse that result and use official host tools for the schedule; actual natural triggering requires its own evidence. Do not invent work or run an extra demonstration Automation. Keep unchanged tasks quiet unless the user requests a report. One receiving plan defaults to 20 selected items, at most 100; remaining work is reported separately, and this is not a timer for an entire AI turn.

<a id="options"></a>

## Optional extensions and limits

| Need | Guidance |
|---|---|
| Manual installation, transfer or reload | [Fallback steps](manual-setup.md). Complete only the missing step. |
| Scheduled governance | [Automation](automation.md). Installation does not create it. |
| Selected private Git outputs and memory | [Remote and backup scope](remote-and-multicomputer.md#private-git). Actual commit/push/readback evidence is required. |
| More computers or hosts | [Multi-computer boundaries](remote-and-multicomputer.md#multi-computer). A real two-computer end-to-end workflow remains separately unverified. |
| Tool maintenance and failure recovery | [Maintenance](governance-maintenance.md), the four [Skills](../../skills), and [commands](../COMMANDS.md). |

Only operations actually implemented and verified in the chosen version are available. Task condition revisions, complete incremental context contracts and general non-Git intake are subsequent work. Native permissions, whole-machine backup and automatic multi-writer coordination are not provided by the local engine. See [release boundaries](../RELEASE_BOUNDARIES.md).
