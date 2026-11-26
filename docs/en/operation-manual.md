# Workflow overview and configuration choices

[Start with conversational onboarding](windows-example.md) · [Manual fallback](manual-setup.md) · [简体中文](../zh-CN/operation-manual.md) · [繁體中文](../zh-TW/operation-manual.md)

Use this page for everyday work after setup. For initial setup, see [First installation](windows-example.md); to update an existing installation, return to your original governance chat with the [update prompt](updating.md).

- [Onboarding and working modes](#onboarding)
- [Continue your project on another computer or with another AI](#move-project)
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
| Host | AI interpretation, actual chat access/creation, configuration loading, permissions and native scheduling. |

Keep one main writer for each task/write scope. Others may review or own distinct nonoverlapping subtasks. Separate chats are not automatically separate workspaces. Inspect real ownership and active writers before changing their arrangement.

<a id="continuation"></a>

## Initial inventory and everyday continuation

Work chats read the named task, latest relevant checkpoint and effective decisions before continuing. At a meaningful result, decision change or pause, save selected task-owned files, findings, source references and next steps. Governance uses those records to maintain shared understanding, requesting only changed or missing related context. Host access to old chats is checked separately; there is no automatic full-history monitor.

Keep source-qualified decisions and relationships through `facts`, retaining the original statement, evidence and separate AI judgment. Explicit revisions preserve earlier effective facts and identify affected work. This uses the same Core store; it does not create a competing database or silently change the original task identity.

<a id="chat-continuation"></a>

### When the original chat cannot continue

You do not need an empty spare chat in advance. If a window repeatedly errors or cannot resume, governance first checks the original task, saved decisions, checkpoint, outputs and uncommitted changes. It inspects the effects of the interrupted operation and confirms that the old window and its background writers have stopped. If that cannot be confirmed, the new chat remains read-only.

When a replacement is needed, governance supplies a continuation prompt for a new chat in the same project and actual working directory. It retains the original control and `task_id` and records the new chat's real identity. The new window calls native MCP itself, reads the current task and workbench entry, and explains completed work, gaps and next steps before continuing only what remains. Retain the old chat as history; if it becomes usable again, read the handoff decision before working to avoid two writers on the same task. Replacing governance itself also requires checking the schedule's original-chat binding; do not duplicate schedules automatically.

This continues saved, verifiable project work. It does not repair host compaction errors or promise to recover unsaved or inaccessible content. See the [chat-failure feedback example](user-feedback-examples.md#chat-continuation).

<a id="evidence"></a>

### Understand what a result proves

| Situation | Appropriate record or action |
|---|---|
| Older output already included in the trusted baseline | Preserve provenance and inclusion; do not queue it again. |
| Unfinished or uncommitted work | Save a checkpoint and exact continuation point; do not call it delivery. |
| Stable explicit Git stage | Verify base, commit, task and complete path set; preview reception before execution. |
| Original ordinary documents | Preserve selected files and references; complete standard working-window Git setup for ongoing outputs. General non-Git delivery/intake is outside checkpoint scope. |
| Paused, waiting or unchanged task | Keep its position without creating reminders or new backlog. |
| Task needs accepted code | Preview adoption for that dependency and preserve local commits/index/worktree/new files. Reading progress alone needs no merge. |
| Interrupted operation | Verify actual effects and original identity; complete supported missing steps. |

The map and notes describe the project; engine records and actual files establish effects. A checkpoint, delivery, reception, adoption and business acceptance are different. A recorded artifact path is not a verified backup.

<a id="move-project"></a>

## Continue your project on another computer or with another AI

Open a TaskCarry manager chat on the destination computer or in the AI tool you want to use. To move responsibility for integrating the project's work, tell it what to take over.

> The integration manager for [project name] is currently in [other AI tool or computer]. I want to move that role here and have you take it over. Rebuild the local setup for the project's existing work. Tell me where each workstream stands and which chat to use to continue it.

You can move the integration role while keeping some working chats where they are. For example, add “Set up only development and acceptance testing on this computer. The other chats will continue where they are.” To keep the original integration manager and move specific work, use this request instead.

> Keep the current integration manager for [project name]. Move only [workstream] here. Help me reconnect its files, progress and working chat.

The new manager checks the owners, adopted versions and next actions against the project files and records you authorize it to use. It helps you connect those tasks to local chats. If it needs handoff material or you need to sign in or open a chat, it gives you the next step. When moving the integration role, first review what the new manager found. After you confirm the switch, it verifies that the original manager has stopped writing as the primary and takes over. [Cross-computer recovery and handoff guide](remote-and-multicomputer.md)

<a id="connection"></a>

## MCP, CLI and scheduled governance

MCP exposes engine actions directly to the host AI. The isolated fixed-runtime CLI uses the same control when native tools are unavailable. Neither requires a separate model service. Generated connection files, host loading and native doctor/status calls are separate evidence. Each workbench must verify its own actual imported package and binding.

For new connections in Windows Codex, use **Ctrl+O / Open project folder** to open and trust the exact original directory governance supplies. After governance checks configuration and the original chat's project association, save work, **quit and reopen Codex once**, then return to each original chat to verify version, control, original task and latest checkpoint. Skip the restart for connections already verified through native calls; other hosts use their supported loading method. See [connection and restart steps](manual-setup.md#mcp).

Registered workbench setup can put its four Skills and connection materials in the host directory while binding the original control. Shared directories use `binding_mode: "directory"` with `target` and `workspace`, omitting `task_id`; existing single-task bindings retain the default `task` mode with all three fields. Both modes check existing registration and initialize no second control. The generated fragment pins the selected package with isolated UTF-8 startup; preserve it when merging active configuration. See [manual binding and verification](manual-setup.md#mcp).

<a id="options"></a>

## Further guidance and limits

| Need | Guidance |
|---|---|
| Manual installation, transfer or reload | [Fallback steps](manual-setup.md). Complete only the missing step. |
| Standard scheduled governance | [Automation](automation.md). Complete native setup and readback during onboarding. |
| Selected private Git outputs and memory | [Remote and backup scope](remote-and-multicomputer.md#private-git). Actual commit/push/readback evidence is required. |
| More computers or hosts | [Multi-computer boundaries](remote-and-multicomputer.md#multi-computer). A real two-computer end-to-end workflow remains separately unverified. |
| Tool maintenance and failure recovery | [Maintenance](governance-maintenance.md), the four [Skills](../../skills), and [commands](../COMMANDS.md). |

## Complete governance and task continuation

The `complete_v1` checklist covers persistent project/replica identity, understood selected sources, real task/workspace/Git bindings, per-chat native connection and exact workbench consumption, local governance Git, the first bounded cycle, an independently verified recovery rehearsal, official update checking, and two or three daily original-chat slots. These are standard setup items. Private remotes, cloud storage and ongoing project coordination remain choices. Historical reference chats need source evidence, not artificial active workspaces.

Read `context` for the original task and current checkpoint; use `facts` for source-qualified decisions and relationships, keeping evidence distinct from AI judgments. Use `cycle` to retain the exact owner/resources, intended effects, actual receipts, source phases, health and next step. `source_scan` only enumerates authorized local metadata through bounded pages; the host separately reads selected bodies. Details and payloads are centralized in [Governance API](../GOVERNANCE_API.md).

`workbench` freezes a source-versioned view, plans exact private entry changes and publishes them without modifying Git HEAD/index or unrelated WIP. Verify the current pointer, original task/thread and source freshness; publication, reviewed consumption and native doctor/status are separate evidence. An old view with changed sources is not current truth.

`recovery` captures a selected consistent project set, verifies bytes and restores independently in standby. Its receipt lists `disabled_host_files`: preserved host-configuration evidence is kept out of active restored configuration until regenerated for the new machine. Original project identity and a new replica identity do not authorize two writers. Explicit handoff and actual native verification precede writer activation. [Recovery coverage](remote-and-multicomputer.md) distinguishes local capture, transport and real second-host evidence.

Legacy records remain readable. `identity plan/execute` explicitly adopts a portable project identity while retaining the old source alias; it does not silently merge another project. `upgrade` separately maintains derived indexes. Older acceptance records retain their original profile; a new complete-governance review reuses applicable evidence and fills actual gaps instead of rewriting history.
