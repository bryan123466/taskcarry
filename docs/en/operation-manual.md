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
| Host | AI interpretation, actual chat access/creation, configuration loading, permissions and native scheduling. |

Keep one main writer for each task/write scope. Others may review or own distinct nonoverlapping subtasks. Separate chats are not automatically separate workspaces. Inspect real ownership and active writers before changing their arrangement.

<a id="continuation"></a>

## Initial inventory and everyday continuation

Work chats read the named task, latest relevant checkpoint and effective decisions before continuing. At a meaningful result, decision change or pause, save selected task-owned files, findings, source references and next steps. Governance uses those records to maintain shared understanding, requesting only changed or missing related context. Host access to old chats is checked separately; there is no automatic full-history monitor.

Keep source-qualified decisions and relationships through `facts`, retaining the original statement, evidence and separate AI judgment. Explicit revisions preserve earlier effective facts and identify affected work. This uses the same Core store; it does not create a competing database or silently change the original task identity.

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

<a id="connection"></a>

## MCP, CLI and scheduled governance

MCP exposes engine actions directly to the host AI. The isolated fixed-runtime CLI uses the same control when native tools are unavailable. Neither requires a separate model service. Generated connection files, host loading and native doctor/status calls are separate evidence. Each workbench must verify its own actual imported package and binding.

Registered workbench setup can put its four Skills and connection materials in the host directory while binding the original control. `target`, `workspace` and `task_id` are provided together and checked against existing registration. No second control is initialized. The generated fragment pins the selected package with isolated UTF-8 startup; preserve it when merging active configuration. See [manual binding and verification](manual-setup.md#mcp).

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
