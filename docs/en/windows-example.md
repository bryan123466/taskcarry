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
<a id="install"></a>

# First installation: complete project governance in three steps

[Update or continue existing governance](updating.md) · [Manual fallback](manual-setup.md) · [Feedback examples](user-feedback-examples.md) · [Drone project example](../../examples/vision-drone-governance/README.md) · [简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md)

This guide is for people already advancing projects in Codex. A separate governance chat maintains project memory, connects existing work and guides setup. Keep working directly in your original chats; ongoing project coordination by governance is your choice.

## 1. Open the governance folder and send one prompt

Create a local `TaskCarry` folder and extract the [complete product package](../../START_HERE.md#download) under `toolkit/`, retaining the version directory inside the package. Open the **outer TaskCarry folder** in Codex and create a separate chat. Keep existing business files where they are.

(If you already installed TaskCarry, use another governance tool or have a governance chat, see [update and continuation](updating.md).)

```text
TaskCarry/                 Governance working folder opened in Codex
  toolkit/                 Extracted product package
```

**Copy this complete prompt. No product path needs filling in:**

> Read the TaskCarry product entry and onboarding Skill under toolkit in the current working directory, then guide me through project governance setup. Inspect existing governance, installations and work first; preserve my rules, decisions, tasks and unfinished work.
>
> Start with a read-only inventory of conversation indexes available through the current tools. Show likely projects and their included chats for me to choose; read relevant history only after I select a scope. Prepare complete connection prompts for my existing chats and recommend new chats only where useful.
>
> Then reuse local Git, MCP and Skills by actual working directory, keeping each original chat's task identity when chats share a directory. Do not require a new folder for every chat. Help complete project memory, the first governance cycle and recovery verification. Confirm times and time zone with me before configuring daily governance and official update checks. When I need to act, give me only the necessary next step, with the key or menu entry, exact directory, purpose and what to report afterward. If new connections are not loaded, finish configuration and original-chat project associations first, then guide me through one Codex restart and verification in each original chat. Do not repeat a restart for connections already verified. Resume missing steps after an interruption.
>
> Finish by telling me which chats are connected, their responsibilities, what remains incomplete and what to do next. I can still work directly in my original chats.

The product directory means the TaskCarry package under `toolkit/`; the assistant locates it from this working folder. Reading it teaches the governance method. **Your project information comes from the chats and files you subsequently select.** The assistant asks about the package only when it is missing, incomplete or genuinely ambiguous.

## 2. Let governance complete connection and its first cycle

Follow the current step governance supplies. First it reports which conversation indexes it can access, whether archived chats are included, whether more pages remain and what it cannot see. It then groups candidate projects for your choice. Indexes provide clues such as titles and directories; relevant history is read after you confirm the scope. You can also name the project directly.

After selection, expect these results:

| What you receive | What governance does |
|---|---|
| Project understanding and a connection proposal | Preserve existing outputs, effective decisions, tasks and stopping points; distinguish facts from suggestions. Historical reference chats may remain references. |
| Specific instructions for each chat | Supply a fully filled-in connection prompt for each original chat. Recommend a new role only when useful, with its working location, activation prompt and expected receipt. There is no required number of chats. |
| The current action requiring you | Prepare real working locations, local Git, project settings and MCP. For host trust, login or reload, explain where to act and the expected result, then verify it. |
| Connection and first-cycle results | Verify each window's actual connection, original task and current entry; establish shared memory, save selected files precisely, check official updates and rehearse local recovery. |
| A proposed daily rhythm | Confirm times and time zone, create or reuse report and progress-review slots returning to this original governance chat, then read back the actual configuration. |

**Keep existing chats; a separate folder for every chat is not required.** Several original chats can share a business directory and its connection settings while retaining their own tasks, checkpoints and memory entries. Governance recommends separate Git worktrees only when concurrent writes need isolation.

If the original chat's directory has not been opened and trusted in Codex, governance first verifies and supplies that exact existing directory, then guides these actions:

1. Press **Ctrl+O** in the current Windows Codex app; in other interfaces, use the **Open / Add project folder** entry.
2. Select the **original working directory** supplied by governance and open it. **Do not create a new chat or copy files at this point.**
3. If a trust prompt appears, check that it names this directory and confirm it.
4. Return to governance and reply, “I opened the specified directory and confirmed the trust prompt.” If no prompt appeared, report that instead. Governance checks the configuration and the original chat's project association.
5. Once governance confirms that this batch of directories is ready and new connections need loading, save ongoing work, then **quit and reopen Codex once**. Prepare all directories in this batch before restarting; a restart for every directory is unnecessary.
6. Return to the **original governance chat** and reply, “I restarted Codex.” Return to each **original working chat** for the verification prompt governance supplies. Keep the original history, tasks and files; do not reinstall or create replacement chats.

These actions register and trust the existing directory, **associate the original chat with that project and load its connection settings**, using the same governance memory. Governance uses the host's supported association method, verifies that the actual working directory is unchanged, then calls native `taskcarry_doctor` and `taskcarry_status` in each chat to check version, source, control, original task and latest checkpoint. For newly added connections in this Windows Codex workflow, restart once after the directories and chat associations are ready, then verify the original chats. Skip it for connections already verified; other hosts use their supported loading mechanism. A sidebar entry or a completed restart alone is not native acceptance. [See an example with the directory filled in](user-feedback-examples.md#open-existing-project).

For an active chat not attached to a project, first check its actual directory and tools, then use a supported association with that directory while retaining the original chat. That label alone does not mean MCP is unavailable, and a prompt cannot change the chat's directory. Historical reference chats can remain sources without MCP or Git setup in those windows. When the host cannot read needed history, connect or schedule, governance supplies the current missing step and resume instruction, with [manual fallback](manual-setup.md) only where needed.

Local version saving, working-window connections, recovery verification, daily governance configuration and official update checking are standard setup. Private Git remotes and cloud storage can follow if you choose them; they are not required for local governance. Finding an update leads to an applicability review, not an automatic runtime replacement.

## 3. Review the completion report and keep working

Governance should return a readable report covering:

- **What it understood:** project goals, inherited decisions and outputs, and unresolved questions.
- **Which chats are connected:** each responsibility, original task, real work location and connection result.
- **What setup completed:** actual local saving, project memory, recovery, official update checking and daily schedule results.
- **What remains:** concrete missing steps, their impact and the next necessary action. Pending work is not labeled complete.
- **What to do next:** which original chats can continue which work, and which recommendations await your decision.

“Configuration complete” and “natural scheduled cycle verified” are reported separately. Reading back a schedule is followed by waiting for a real trigger, then checking the original AI's execution, saving and report delivery. A pending host action does not erase the other completed results.

Continue with “resume my last unfinished task” in the working chat, or “review current project progress” in governance. After an interruption, say “retain completed results and continue the remaining setup”; no restart from step one is needed.

[See feedback at each stage](user-feedback-examples.md) · [See the separate drone governance example and final layout](../../examples/vision-drone-governance/README.md)

<details>
<summary>Complete setup acceptance and technical references</summary>

The assistant uses the `complete_v1` checklist for scope, native runtime, local Git, project identity, understood sources, workbench publication and consumption, the first cycle, recovery, official updates and original-chat scheduling. Natural triggers retain separate evidence. Older receipts retain their original meaning.

[Daily operations](operation-manual.md) · [Three layers and project memory](architecture.md) · [Backup, recovery and parallel work](remote-and-multicomputer.md) · [CLI / MCP contracts](../COMMANDS.md)

</details>
