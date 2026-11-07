<a id="windows-guide-connect-a-real-project"></a>
<a id="0-prepare-a-project-name-a-short-description-and-three-directories"></a>
<a id="1-install-create-a-governance-chat-and-choose-control"></a>
<a id="recommended-ask-the-governance-chat-to-install-it"></a>
<a id="manual-installation-commands-for-the-same-route"></a>
<a id="2-set-the-governance-chats-responsibilities"></a>
<a id="choose"></a>
<a id="governance"></a>
<a id="3-configure-professional-task-chats-continue-existing-chats-or-create-new-ones"></a>
<a id="31-existing-ongoing-chats-preserve-history-and-connect-current-state"></a>
<a id="32-create-new-professional-task-chats-add-1n-as-needed"></a>
<a id="4-configure-mcp-recommended-for-governance-with-cli-as-a-fallback"></a>
<a id="agents"></a>
<a id="existing"></a>
<a id="mcp"></a>
<a id="5-first-governance-pass-review-current-work-and-see-the-result"></a>
<a id="9-what-you-should-see-when-finished"></a>
<a id="delivery"></a>
<a id="check"></a>
<a id="6-create-scheduled-governance-read-the-actual-registered-scope"></a>
<a id="7-optional-a-private-git-memory-repository"></a>
<a id="8-optional-parallel-work-on-different-computers"></a>
<a id="automation"></a>
<a id="private-git"></a>
<a id="multi-computer"></a>
<a id="windows-guide-connect-your-existing-codex-project"></a>
<a id="1-establish-a-governance-chat"></a>
<a id="send-one-onboarding-prompt"></a>
<a id="2-let-governance-connect-your-existing-work"></a>
<a id="keep-the-original-chats-and-decisions"></a>
<a id="complete-the-actual-tool-connection"></a>
<a id="3-continue-in-your-usual-way"></a>
<a id="what-successful-onboarding-looks-like"></a>
<a id="optional-additions"></a>

# First installation: complete project governance in three steps

[Existing-user update](updating.md) · [Manual fallback](manual-setup.md) · [Complete feedback examples](user-feedback-examples.md) · [简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md)

You already use Codex to advance a project. TaskCarry adds an independent governance chat: it retains valid decisions, understands progress, returns shared agreements to relevant chats, and saves recoverable project memory. Keep working in your existing chats. Ongoing project coordination is an optional governance responsibility.

This guide uses a USB acquisition and curve-display tool: firmware supplies simulated readings, PC software parses, displays and exports CSV, and simulation checks normal input, disconnection and reconnection. Substitute your own project. Installation does not require a fixed number of professional chats.

## 1. Open the governance folder and send one prompt

Create a local `TaskCarry` folder and extract the [complete product package](../../START_HERE.md#download) under `toolkit/`, retaining its versioned directory. Open the outer **TaskCarry folder** in Codex and start an independent governance chat. Business files stay where they are. Already governed projects use the [update entry](updating.md).

```text
TaskCarry/                 Governance working directory opened in Codex
  toolkit/                 Extracted product package
  runtime/                 Separate runtime prepared by the assistant
  .taskcarry/              Durable project state, objects and workbench entries
  .agents/skills/          Governance methods used by this project
  .codex/config.toml       Project connection; other settings preserved
```

<a id="install"></a>

Replace the brackets and send this complete prompt. Governance guides the remaining setup:

> Establish this chat as the TaskCarry governance home for my existing project, responsible for project memory and governance. Product location: [extracted directory containing START_HERE.md and packages/]. Project clues: [existing directories, chats or a short goal; help propose candidates if scope is unclear].
>
> Read the product entry, taskcarry-project-setup Skill and its references. Inspect existing installation, governance, tasks, directories and Git first. Inherit valid decisions, outputs, task relationships, pause points and uncommitted work. Reuse existing configuration rather than initializing an existing project again.
>
> Explain your understanding of my goal, progress and proposed scope first. If scope is unclear, use only permitted indexes and directories visible through current tools to identify candidates; read relevant contents after scope selection, without scanning unrelated history. Separate confirmed facts from recommendations. If an original chat cannot be read, guide it to provide a minimal handoff instead of claiming understanding. Historical materials can remain references without becoming working chats.
>
> Recommend responsibilities based on existing chats and retain original task identities. Establish each active chat's actual working directory, local Git working/saving location and writing boundary; reuse repositories and verified author settings. Connect MCP, Skills and current workbench guidance to the same governance, preserving specialist instructions and other settings. Each chat must verify its own real connection, original task, progress and shared agreements. I can continue directly in professional chats without routing every action through governance.
>
> Save governance versions locally, register the official update source and check once. Evaluate new versions before proposing installation; do not install automatically. Suggest one morning report plus one or two daily progress-absorption slots. Confirm times and timezone with me, then create or reuse native schedules bound to this original governance chat without changing model or permissions.
>
> Complete a first governance cycle: reconcile decisions, dependencies and unfinished work; review issues, fixes and actual effects; send changed shared agreements to relevant chats and verify what they read. Define recovery coverage for necessary state, objects, Git history and uncommitted changes, project materials and capability versions. Capture a local recovery set and verify an independent restore, leaving the copy in standby. Let me choose private remotes or cloud storage; verify upload, download and restore separately.
>
> Complete the product's full governance acceptance checklist. When I must trust a directory, reload, sign in or choose scope, give only the current action and exact target, then verify and continue. Finish in plain language with project understanding, chat responsibilities, actual completed work and gaps, and next suggestions; retain technical evidence as a reviewable appendix. Distinguish configuration, natural scheduled triggering, actual AI execution and report delivery. After interruption, retain original identities, inspect actual effects and finish only missing steps. Ongoing project coordination remains my choice.

## 2. Let governance complete connection and its first cycle

Governance explains scope and understanding so you can correct omissions or grouping. One real project may span directories, repositories and historical chats; similar names do not establish the same task. This example produces concrete responsibilities:

| Existing work | Responsibility and next action |
|---|---|
| Firmware/protocol chat | Agree the fields and newline in `READ,42,1000,1.234`, then save three stable simulated input frames. |
| PC software chat | Use that input to connect parsing, curve display and CSV; check each output. |
| Simulation chat | Start with normal input, then replay disconnect/reconnect without inventing readings or duplicating points. |
| Older hardware/interface notes | Retain valid agreements as sources without claiming an active chat or reopening finished work. |

Combine responsibilities to fit existing chats; three new chats are not required. Actual device tests remain separate because this example starts with simulation. Governance completes the following work, rather than merely handing you a checklist:

- Preserve each chat's original task, progress, professional instructions and uncommitted work. Establish actual directories, Git saving locations and concurrent-writing boundaries. Where no suitable directory exists, guide real host association or continuation in the correct location. Each chat does not need a new GitHub account.
- Prepare connections and entries for the same governance. Each active chat calls native tools and confirms its current agreement. Generated configuration, published entries and actual reading are checked separately.
- Complete local Git saving, an official update check, the first cycle, explicit recovery coverage and an independent restore rehearsal. Ordinary files may stay in place, but necessary materials need recovery coverage; credentials are managed separately.
- Configure and read back one morning report and one or two absorption slots. You confirm time and timezone; only necessary host trust, sign-in or similar actions are handed back to you.

Local Git, schedule configuration, update checks and the first cycle are standard setup. Private remotes and cloud storage are optional locations, so declining them creates no artificial gap. When the host requires participation, governance identifies the current action. Detailed commands stay in the [manual fallback](manual-setup.md).

## 3. Review the completion report and keep working

No special completion phrase is required. Governance reports actual acceptance. The following illustration assumes required setup has passed; it is not a receipt from a real installation:

> Governance setup for the USB acquisition project is complete. Existing firmware/protocol, PC software and simulation work is connected; older hardware notes remain references. The shared milestone uses simulated readings to connect the USB serial frame format, curve and CSV. Wireless and physical-device tests are outside this simulation.
>
> Each working chat verified its real connection and current entry. Local version saving, the first governance cycle and independent recovery rehearsal passed; the restored copy remains in standby. The official update source was checked. Morning report and afternoon absorption slots are configured and read back; first natural triggers still await acceptance.
>
> Next, return to PC software and check the curve and export with the three-frame input, then have simulation check normal, disconnect and reconnect behavior. Continue development directly; I will keep absorbing relevant progress. Governance is established, while engineering work continues.

If required items are missing, report setup in progress with completed work, exact gaps and next actions. **Setup complete** and **natural scheduled loop verified** are separate: the latter needs actual scheduled occurrence, AI execution in the original chat and delivery for the report slot. Manual execution cannot substitute.

You can say “continue the original task,” “save this pause point,” or “which chats does this change affect?” After interruption: **“Continue from the original checklist and task, inspect actual effects, and finish only the missing steps.”**

Existing users continue updating in the original governance chat, verify original tasks, decisions, sources and checkpoints, and exercise full backup and independent recovery on old-state copies. See the [existing-user update flow](updating.md).

<details>
<summary>Acceptance criteria and technical evidence</summary>

Complete setup uses `complete_v1`: selected sources and valid decisions, active identities and native connections, current entries and reading evidence, local Git, official update checks, first cycle, recovery and schedules must all satisfy the checklist. `complete_governance_ready` does not substitute for `natural_trigger_verified` or `closed_loop_verified`. Source drift, incomplete receipts and changed configuration are reported accurately.

Original task/chat, actual cwd/Git, checkpoint, view and consumption evidence for each chat remain reviewable alongside recovery manifests, package identity and schedule readback. Users do not need to copy these fields through the main flow. Calls are documented in [Governance API](../GOVERNANCE_API.md).

</details>

[Complete feedback examples](user-feedback-examples.md) · [Core, capabilities and project layers](architecture.md) · [Recovery and parallel work](remote-and-multicomputer.md) · [Everyday operations](operation-manual.md)
