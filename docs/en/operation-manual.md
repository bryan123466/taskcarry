# Workflow overview and configuration choices

[Complete Windows workflow](windows-example.md) · [简体中文](../zh-CN/operation-manual.md) · [繁體中文](../zh-TW/operation-manual.md) · [Product home](../../README.md) · [Command reference](../COMMANDS.md)

Applies to 0.2.0rc5. **Use the [Windows walkthrough](windows-example.md) as the single detailed source for steps, directories and copyable prompts.** This page explains the workflow and choices rather than supplying a second installation procedure.

## One recommended onboarding path

Create `TaskCarry`, `TaskCarry/control` and `TaskCarry/toolkit` yourself, and extract the package into `toolkit`. Open a new governance chat directly in `control`; it performs installation and onboarding. `control` is an ordinary governance directory containing this project's only `.taskcarry`, not a specialist Git worktree.

One TaskCarry directory represents one real project. Provide **[Project name]** and **[One-sentence introduction]**. Governance examines actual directories, Git ownership and prior outputs to decide initialization or continuation; you do not select a new/existing-project route. An empty TaskCarry directory is not evidence that no earlier work exists. If context is unclear, governance briefly checks for prior outputs or obtains the existing chat's summary through section 3.1 of the main walkthrough before deciding the baseline.

For new specialists, provide **[n: number of new specialist chats]**. Governance adds n workspaces, continuing the existing numbering. You then create a chat for each and choose its directory. Each chat receives **[The actual project work this chat should handle]**, without preset business responsibilities or worker count.

| Operation | Main walkthrough |
|---|---|
| Prepare the project introduction and directories | [Project and directory preparation](windows-example.md#choose) |
| Prepare directories, extract and install through governance | [Installation](windows-example.md#install) |
| Establish governance responsibility and project binding | [Governance chat](windows-example.md#governance) |
| Add specialists as needed or continue original chats | [Specialists](windows-example.md#agents) · [Existing-chat onboarding](windows-example.md#existing) |
| Connect governance MCP with CLI fallback | [MCP and CLI](windows-example.md#mcp) |
| Establish the first complete current-state inventory | [Inventory and reception](windows-example.md#delivery) |
| Schedule against the actual registered scope | [Automation](windows-example.md#automation) |
| Check whether work can continue normally | [Completion check](windows-example.md#check) |

Choose another root consistently before first initialization. Moving an already bound project does not make its old plans safe to execute in a new location.

## Responsibilities

| Participant or component | Responsibility |
|---|---|
| User | Actual project goals, business decisions and actions requiring authorization. |
| Governance chat | Interpret task/evidence relationships, call tools to receive work, verify results, coordinate adoption and explain actionable issues. |
| Specialist chat | Advance real work in its assigned workspace, retain checkpoints and deliver stable stages precisely. Keep one main writer per task/workspace. |
| Receiving baseline | A dedicated clean Git workspace for received work, without specialist WIP. |
| TaskCarry engine | Persist local state, check plans against actual Git conditions and perform supported reception, adoption and recovery. |
| Host automation | Wake the governance model on schedule; it is not another control database. |

Specialist chats follow parallel work needs, such as software, hardware, algorithms, experiments, research, operations, simulation, writing or management. There is no fixed department count; sequential subtasks do not require new chats. Keep one main writer per task. Others may review read-only or take explicitly separated, nonoverlapping subtasks.

Reuse suitable existing workspaces in place. If several old chats share a directory, retain one as its main specialist writer and continue other parallel responsibilities in separate new workspaces and chats. First confirm the old writers have stopped, then preserve scoped summaries, checkpoints and WIP while retaining their history. A prompt alone does not change file ownership.

Existing-chat onboarding belongs to this same workflow: paste the manual's summary prompt into the original chat → that chat returns its actual working context and task summary → send the reply together with the manual's handoff prompt to governance → governance verifies registration and produces a return prompt → paste it into the original chat to continue. The original task is retained rather than restarted or ignored because a directory is empty.

## Initial inventory and everyday continuation

The initial inventory covers the registered set in `status.workspaces`, `status.tasks` and `PROJECT_MAP.md`, checked against actual files and Git evidence. The map is a human/model-readable description. Investigate discrepancies rather than editing the table to pretend the actual state is correct.

| Current situation | Record or action |
|---|---|
| Older work already in the trusted current baseline | Record its known inclusion instead of queuing it again. |
| A stable, explicit stage not yet received | Verify the frozen commit, original base, exact paths and task relationship; plan before receiving. |
| Unfinished or uncommitted work | Preserve an exact checkpoint, findings and next step; do not claim delivery. |
| Paused, waiting or unchanged work | Retain its current position without creating new backlog or reminders. |
| A task needs accepted code or deliverables | Confirm the dependency and no active writer, plan adoption and preserve local work. Reading shared progress alone needs no merge. |
| Interruption or a concrete failure | Reconcile actual effects and original operations, then apply supported recovery to missing steps. |

**Complete state coverage does not mean receiving all unfinished work.** Governance does not automatically discover every app chat. Register additional chats/workspaces through the walkthrough. Task completion, stage reception and business acceptance remain different states.

## MCP, CLI and scheduled governance

MCP is the recommended direct tool connection for the governance chat. The CLI remains a fallback to the same control directory. A generated MCP fragment is not proof of connection; configure it in the host and confirm an actual tool call.

Generated MCP startup uses `-I -X utf8` and pins the package location selected during setup. Neither the host working directory nor `PYTHONPATH` can select another TaskCarry copy; a missing selected package stops startup. Run setup and CLI with the fixed installed interpreter and `-I -X utf8 -m taskcarry`. Explicit source setup remains a development connection and pins that source. For an older installation, review setup preview before install updates its unchanged managed fragment; modified files are preserved. Separately review the active host configuration and reload it, then call doctor to confirm `runtime.loaded_runtime.module_root`. Finish any interrupted setup with its original package first. These steps neither install an upgrade nor prove another host has reloaded it.

The first bounded governance pass shows its result directly in the current chat. Reuse that result when creating a schedule; do not run an extra Automation to demonstrate reporting. Create scheduled governance through the host's official tools, using its actual timezone and target. Daily results use the same AI and project records. Runs read registered tasks and workspaces without a fixed worker count or a claim to scan every chat.

Specialists keep working normally. Reception handles explicit stages; adoption runs only for an actual task dependency and when its target is ready. Reading shared progress or updating Skills does not require merging business branches. A `paused` task alone does not prove outside programs stopped writing. Toolkit locks serialize toolkit actions, not entire model turns or arbitrary external programs.

## Optional extensions and limits

| Need | Guidance and boundary |
|---|---|
| Private Git for selected outputs and curated memory | [Detailed procedure](remote-and-multicomputer.md#private-git): only committed and pushed files reach the remote; `.taskcarry` and uncommitted material require separate consistent backup. |
| Task branches across computers | [Detailed procedure](remote-and-multicomputer.md#multi-computer): one integration host and independent task branches; no built-in cross-host shared state or transaction migration. |
| Exact CLI/MCP parameters | [Command reference](../COMMANDS.md). |
| Actual system boundaries | [Architecture](architecture.md) and [operating scope](../RELEASE_BOUNDARIES.md). |

A receiving plan selects up to 20 work items by default, with a maximum limit of 100, prioritizing unfinished receiving operations. Review its frozen scope before execution and report remaining work separately. This count does not limit the whole AI session's duration. Experience records use implemented recovery actions; operating-system repair and native-account migration remain outside the product.

There is no requirement to enable every option or run maintainer tests. Establish clear preservation, delivery, reception and continuation for your own project, then extend the workflow when needed.
