<a id="user-feedback-examples-a-usb-acquisition-and-curve-display-tool"></a>
<a id="make-the-project-understandable-first"></a>
<a id="1-governance-explains-its-understanding-and-proposed-scope"></a>
<a id="2-connection-produces-a-practical-continuation-plan"></a>
<a id="3-the-complete-setup-report-in-step-three"></a>
<a id="4-report-understandable-engineering-progress"></a>
<a id="5-explain-gaps-interrupted-work-and-quiet-checks"></a>
<a id="6-recovery-and-parallel-work-elsewhere"></a>
<a id="example-feedback-after-updating-an-existing-project"></a>

# Feedback examples: from scattered chats to shared project memory

[Three-step guide](windows-example.md) · [Drone governance example](../../examples/vision-drone-governance/README.md) · [Three layers](architecture.md) · [简体中文](../zh-CN/user-feedback-examples.md) · [繁體中文](../zh-TW/user-feedback-examples.md)

These examples use a vision-based obstacle-avoidance drone project. Software, algorithm and hardware work already exists in separate chats. Governance connects it to shared decisions, adding product and communications responsibilities only where useful.

**The replies below illustrate a synthetic scenario; they are not successful installation receipts.** Actual answers must cite that run's reading, configuration and verification. The [separate example](../../examples/vision-drone-governance/README.md) contains project materials, the full process and its evidence scope. Establishing governance does not verify a physical drone, flight control, flight safety or market outcomes.

## 1. See candidate projects before choosing history to read

> I have read the conversation indexes accessible through the current host. Active and archived coverage is reported separately, with remaining pages and access failures retained. This inventory covers only the listed sources, not other accounts, devices or inaccessible chats.
>
> Based on titles and directory clues, please choose:
>
> 1. **Vision-based obstacle-avoidance drone:** existing software, algorithm and hardware chats that may belong together; please confirm.
> 2. **Custom scope:** choose only some of these chats or add a missing project.
>
> These are proposed groups. I have not read their conversation bodies yet. Which project should I connect?

An explicitly supplied project scope can be confirmed directly without inventorying unrelated conversations. Similar titles are clues, not proof of a shared project.

## 2. Receive a sourced project understanding after selection

> You selected the drone project. I read the relevant history within that scope and linked findings to the original chats and materials.
>
> The current goal is a vision-based avoidance proposal and reproducible demonstration materials. Existing software, algorithm and hardware work continues. Unconfirmed parameters remain open questions.
>
> I recommend retaining the three working chats. When the boundaries are clear, a product and communications role can prepare target-user assumptions, a demonstration script and public wording. An existing chat may take that role; a fourth chat is not required.

Real goals and decisions must come from the read sources or user confirmation. This is only an illustration of wording. Partial history reading must include its actual coverage and remaining pages.

## 3. Connection instructions arrive filled in for each chat

Governance supplies a **connection card** identifying the original chat, actual directory, responsibility, task, shared governance source, complete prompt and expected reply. It fills in verified details instead of asking you to transcribe task IDs, interpreter paths or configuration blocks.

An existing algorithm chat might receive the following wording, accompanied by its actual connection location:

> Continue this window's original drone vision algorithm task. Read its published current governance entry and verify the original task, latest checkpoint, working directory and native TaskCarry connection. Preserve the existing algorithm proposal, unfinished comparisons and local changes.
>
> This milestone shares the confirmed input and acceptance boundaries with software and hardware. Report the decisions you actually read, missing inputs and next step. If the entry or connection is not loaded, name the exact gap and continue unaffected work.

For an active chat not attached to a project, check its actual directory and tools first, retaining its original chat and history and preferring supported association with the same directory. The label alone does not establish MCP availability. If trust or loading is still missing, governance gives only the necessary next action, then returns to the original chat for verification. A prompt cannot change cwd or replace a real MCP call.

<a id="open-existing-project"></a>

### When you need to open the original directory and restart Codex

Suppose governance has verified that the original algorithm chat uses the synthetic directory `C:/TaskCarry/workspaces/drone`, and its connection configuration is ready. **This is a filled-in example, not a request to create that directory.** Your actual connection card must contain your original directory:

> I prepared the connection for the original “Drone vision algorithms” chat. Codex now needs to open and trust its existing directory so it can load the MCP configuration there:
>
> 1. Press **Ctrl+O** in the current Windows Codex app; in other interfaces, use **Open / Add project folder**.
> 2. In the folder picker, select `C:/TaskCarry/workspaces/drone` and open this existing directory. **Do not create a new chat, copy files or create another governance store.**
> 3. If a trust prompt appears, check that it names the directory above and allow it.
> 4. Return here and reply, “I opened the specified directory and confirmed the trust prompt.” Tell me if no trust prompt appeared.
>
> I will then use the host's supported method to associate the original chat with this project, preserve its history and task, and check that its actual working directory is unchanged. Once configuration and associations are ready for every directory in this batch, I will tell you when to restart once; you do not need a restart for each directory.

If the new connections are not loaded, governance confirms readiness and continues:

> I have checked the original chat's project association, and configuration is ready. Codex now needs to reload the connection:
>
> 1. Save ongoing work, then **quit Codex and reopen the application**.
> 2. Return to this **original governance chat** in the sidebar and reply, “I restarted Codex.” Do not reinstall or create a new chat.
> 3. Return to the original “Drone vision algorithms” chat and send: **“Use this chat's native TaskCarry MCP to call doctor and status. Check the actual version, runtime paths, control, original algorithm task and latest checkpoint. Read and verify the current workbench entry and return the actual receipts to governance. Continue with the original identity, history and outputs.”**
>
> I will check the actual receipts from each original chat, confirming that each reads its own task from the same governance memory. Connections already verified will not require another restart.

These actions associate the original chat with its project and load the connection, retaining the same governance store and original task. Governance checks the association and actual working directory, then obtains native `taskcarry_doctor` and `taskcarry_status` receipts from the original chat. It reports the chat as connected only when version, source, control, original task and checkpoint match; a chat appearing under a project or a completed restart is not an acceptance receipt. Other chats sharing the directory still verify their own tasks and entries, without recreating the project.

### When several original chats share one directory

This is still an **expected feedback example, not a report of observed acceptance**. Suppose verification shows that three original chats use the same existing business directory, shown here as `drone/`:

| Original chat | Retained task | Actual working directory | Connection plan |
|---|---|---|---|
| Drone software | `drone-software` | Existing `drone/` directory | Use the directory connection and read its own software task entry. |
| Vision algorithms | `drone-vision` | Same directory | Reuse MCP and Skills, and read its own algorithm task entry. |
| Hardware concept | `drone-hardware` | Same directory | Reuse MCP and Skills, and read its own hardware task entry. |

> I will keep all three original chats and prepare one set of connection materials for this existing directory. You do not need three separate folders or replacement chats to connect. Each window continues its original task; native connection and actual reading of shared memory are still verified separately in each chat.
>
> An older component-selection discussion can remain a historical source with references, without MCP or Git setup in its original window. If the active chats later need to change conflicting files or Git state concurrently, we can assess separate worktrees then.

Shared configuration does not merge task identities. Governance maps each verified chat to its original task. An unknown chat needs its binding checked; it never defaults to the directory's first task.

## 4. Each responsibility receives the relevant effect of a shared decision

Suppose the user confirms: “For the first milestone, use offline image replay and simulated avoidance decisions. Do not proceed to physical flight yet.”

| Responsibility | Effect recorded by governance | Next work |
|---|---|---|
| Software | First-stage input is replay data; flight-controller integration is not claimed. | Specify image input, recognition output and decision-display interfaces. |
| Algorithms | Compare results on the same replay samples. | Preserve comparisons and failure samples; describe simulation limits. |
| Hardware | Supply constraints and verification requirements; flight integration stays outside this milestone. | Identify camera, computing and connection needs and unresolved choices. |
| Product and communications | Demonstrations describe proposals and simulation capabilities. | Prepare product wording and a script without claiming flight verification. |

> I recorded your confirmed milestone and the earlier scope it replaces, retaining the discussion as provenance. Updated workbench entries show the change relevant to each role. Publication and actual reading by the original windows are separate receipts.
>
> Continue directly in your working chats. Governance does not need to approve every action. New decisions affecting shared boundaries will be retained in project memory.

## 5. Receive a completion report you can check

A report uses actual results from the current run. Its shape should be:

> **Project understanding:** goals, effective decisions, outputs and stopping points are organized; unresolved conditions remain visible.
>
> **Working chats:** list each original chat, responsibility, task, real directory and connection result. Mark connected only after that window's native receipt.
>
> **Saving and recovery:** explain which files local Git saved and which state, outputs and history the recovery rehearsal covered. List reference-only materials separately.
>
> **Daily governance:** show the confirmed report/progress-review slots, time zone and configuration readback. Report the official update check and applicability decision; offline access leaves the remote state unverified.
>
> **Pending work:** if one window needs a reload, give only its reload and readback steps. Do not declare full setup while standard items remain incomplete.
>
> **Natural trigger:** before the scheduled time, say “configuration read back; first natural execution pending.” Add original-AI execution, saving and delivery evidence after a genuine trigger.
>
> **Next work:** software continues the replay interface, algorithms prepare comparisons, hardware clarifies constraints, and product communications uses claims supported by evidence. Return directly to the relevant chats.

Creating several files is not proof of complete governance. Waiting for the first genuine scheduled trigger is not a reason to reinstall.

## 6. Continue or update by stating the current goal

- **After interruption:** “Continue the remaining setup.” Governance checks existing plans and actual effects before filling gaps.
- **At a stopping point:** “Save here so we can resume.” The original task retains a checkpoint, artifact locations and next step.
- **When an update appears:** “Assess whether this update helps my project.” Governance compares Core, methods and project rules, then recommends applicable changes.
- **From another governance tool:** “Continue these rules and decisions.” Governance identifies the source and scope while preserving the existing system; inheriting content does not upgrade that tool.

<a id="chat-continuation"></a>

## 7. A new window continues the original algorithm task

This is an **expected feedback example**. Suppose the original algorithm chat repeatedly errors, project files remain available, empty-frame handling is verified, and comparing multiple targets in one frame is still unfinished. Governance first checks actual effects and whether the old window is still writing, then provides a continuation such as:

> The saved algorithm proposal, empty-frame test results and original task checkpoint are available. I checked the files affected before the interruption and confirmed that the old window is no longer writing. The multiple-target comparison remains unfinished, so completed empty-frame work will not be repeated.
>
> No spare window needed to be prepared in advance. We can now create a continuation chat in the original algorithm project and same working directory. I will supply a prompt filled with the original task, entry and next step, and record the new chat's actual identity. The original chat and history remain available as references.
>
> The new window first calls native MCP itself to check the same governance source, original algorithm task and latest checkpoint. It then reads project decisions and related outputs and reports what it inherited, what is missing and what comes next. After these checks match, it continues only the multiple-target comparison.
>
> If the old window becomes usable again, have it read this handoff decision first and retain it as a historical reference, avoiding concurrent changes to the original task. Unreadable old content and unsaved ideas remain explicit gaps; they are not claimed as recovered.

An actual report needs evidence that the old writer stopped, the new window's native reading receipts, and its continued outputs. Creating a new chat alone is not successful continuation. This preserves project work; it does not claim to repair Codex compaction or chat failures.

[Return to the three-step guide](windows-example.md) · [Update and continuation](updating.md) · [Separate example and actual evidence scope](../../examples/vision-drone-governance/README.md)
