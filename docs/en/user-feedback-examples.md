# User feedback examples: a USB acquisition and curve-display tool

[Three-step guide](windows-example.md) · [Three-layer architecture](architecture.md) · [简体中文](../zh-CN/user-feedback-examples.md) · [繁體中文](../zh-TW/user-feedback-examples.md)

Suppose you already use Codex to build a small tool: a device sends readings over USB serial, and a PC displays a curve and exports CSV. You have firmware, PC software and simulation chats, plus older hardware/interface notes. TaskCarry connects their work to shared project memory so each chat knows the agreed interface and its next task.

**The conversations below are synthetic product feedback examples, not acceptance reports for your project or a particular host.** The included [executable fixture](../../examples/complete-governance/README.md) checks text parsing and replay. It does not connect a device, flash firmware or draw an actual application interface. A real report cites its own evidence instead of copying these success claims.

## Make the project understandable first

The first milestone uses one UTF-8 measurement per line: `READ,42,1000,1.234`, followed by a newline. The fields mean measurement type, sequence 42, simulated device time 1000 ms, and simulated value 1.234. First connect data generation, parsing, curve display and CSV export; then test interruption and recovery. Wireless support is outside this milestone.

| Responsibility | Concrete work | Observable acceptance |
|---|---|---|
| Firmware and protocol | Agree the fields and supply repeatable simulated readings and frames | The same input produces results both sides can reproduce; this does not accept firmware on a board. |
| PC software | Parse frames, supply the live curve, and export CSV | Three frames correspond to three points and matching sequence/time/value CSV rows; actual UI and file operations need their own checks. |
| Simulation validation | Replay normal input, disconnection and reconnection | Normal values match; disconnection creates no measurements; reconnection duplicates neither old points nor an interrupted partial frame. |

These are three responsibilities, not a requirement for three professional chats. Existing chats may combine them. Older hardware notes are reference sources, not claimed active connections. Actual sampling, drivers, USB timing and measurement accuracy require physical-device tests.

## 1. Governance explains its understanding and proposed scope

> You are building a USB acquisition and curve-display tool. The first milestone uses simulated data: the firmware side supplies agreed frames, the PC parses, displays and exports them, and validation checks normal operation and interruption recovery.
>
> I found existing firmware/protocol, PC software and simulation chats and suggest keeping them. If you currently have two chats, protocol and simulation can remain together; installation does not require splitting them. Older hardware/interface discussion stays a reference source. You choose the included chats and materials.
>
> I will retain the decisions to simulate before connecting hardware and leave wireless support outside this milestone. Continue directly in your professional chats. I will record decisions, check dependencies and return shared protocol changes to the affected chats. Ongoing project coordination remains your choice.

If only titles and directories were visible, governance must say this is a candidate grouping whose contents have not yet been read. After scope selection, read relevant contents. When the host cannot read another chat, use a minimal handoff from that chat; a directory scan is not project understanding.

## 2. Connection produces a practical continuation plan

> The selected working chats now use the same governance. Original tasks, files, uncommitted work and specialist instructions remain intact. Each chat checked its own actual connection and current workbench entry.
>
> The shared frame format is agreed, but the PC curve and CSV have not yet passed acceptance. Next, firmware/protocol saves a stable three-frame input; PC software uses it to connect parsing, display and export; simulation checks normal data before disconnection and reconnection. Old interface notes remain references rather than new work assignments.

The user should understand who continues what, with which material, and how to check it. Establishing governance does not finish these engineering tasks.

## 3. The complete setup report in step three

This example assumes the required setup, first governance cycle and independent recovery rehearsal have actually passed:

> **Governance setup for the USB acquisition project is complete.** Continue development in your existing chats. The first cycle aligned the simulation protocol, confirmed where each chat stopped, and retained the unfinished curve and export work.

| Chat or source | Responsibility | Next useful work |
|---|---|---|
| Governance | Project memory, shared guidance, saving/recovery and scheduled governance | Check protocol/PC agreement and return meaningful changes to affected chats. |
| Firmware and protocol | Simulated readings, frame format and field meanings | Save shared input; actual firmware and device testing remain separate. |
| PC software | Parsing, live curve and CSV | Verify the interface and export using shared input. |
| Simulation validation | Normal, disconnect and reconnect replay | Compare data and display results and report reproducible differences. |
| Old hardware/interface notes | Reference source | Retain agreed constraints without claiming an active working chat. |

> Each active chat passed its own native tool acceptance and read its workbench entry. Selected governance files are saved in local Git; existing repositories and uncommitted work remain. You can save progress first and form an exact version of selected files when appropriate; saved progress is not delivery or acceptance.
>
> The recovery rehearsal covered selected project state, objects, protocol materials, validation scripts, Git history and staged/unstaged changes. The independently restored copy remains in standby. Unsaved editor buffers and private platform chat history are excluded; credentials are managed separately. This example declined cloud storage, so it claims no offsite upload.
>
> The official update source was checked. New versions are evaluated before any proposed installation. In your confirmed timezone, one morning report and one afternoon absorption slot are configured for this original governance chat. Configuration was read back; first natural triggers are still pending. This manual execution does not establish the natural scheduled loop.
>
> Next, return to PC software and connect the three-frame input to the curve and CSV. Governance is ready; engineering continues. No actual USB device has been tested.

If a required connection, local save, schedule or recovery check is missing, report setup in progress with the exact gap and next action. Package installation alone cannot establish complete governance, and completed work does not need to be restarted.

## 4. Report understandable engineering progress

The shared input is:

```text
READ,42,1000,1.234
READ,43,1100,1.250
READ,44,1200,1.220
```

The following feedback is appropriate only after its corresponding checks:

> The three simulated frames produced matching sequence, time and value fields. Parsing/replay passed, giving the curve three input points at 1000, 1100 and 1200 ms. Reference CSV rows match those values. This validates the data path; actual curve UI and file-export interactions retain separate evidence.
>
> Disconnection created no new measurements and discarded the incomplete frame. Reconnection accepted continuing sequence numbers without duplicating old ones. Next, PC software checks the actual interface's offline indication and display recovery. Hardware connection remains a later stage.

The packaged replay program checks these simulated parsing, disconnect/reconnect and CSV numeric round-trip outcomes; it is not a complete PC application. A real device that resets sequence numbering needs an explicit session/epoch agreement rather than this continuing-sequence assumption. Real reports cite exact inputs, outputs and checks. A static plot also does not establish live interface interaction.

## 5. Explain gaps, interrupted work and quiet checks

> The PC chat's configuration is written, but its current tools do not expose native TaskCarry yet. Trust and reload the exact directory in the report. I will verify that chat's actual connection afterward. The completed protocol configuration stays; no reinstall or task re-registration is needed.

> The protocol entry was written before interruption and only its receipt was missing. I inspected the effect and completed that receipt. You later changed another chat's file; I retained it and will plan against the new contents. Independent work can continue.

> The sources read in this absorption check contain no substantive changes. Original progress and next actions remain, with no new delivery, installation or reopened completed task. Unread sources are listed separately for follow-up.

An absorption slot can save a quiet result for the morning report. An unread source is not evidence of no change; neither success nor failure should be invented.

## 6. Recovery and parallel work elsewhere

> Selected protocol files, scripts, project memory and Git changes were restored independently and checked against the manifest. This is still the same logical project, but the copy is in standby. Connections at the new location still need acceptance.
>
> To continue PC development on another computer, use an independent task branch and return exact versions, changed files, results and next steps to the same governance. Moving governance itself requires stopping the old writer, checking the new host, and an explicit handoff. Two replicas must not concurrently write the same governance state.

Report local independent restore, upload, offsite download, actual second-computer acceptance and writer transfer separately. A same-machine rehearsal does not prove a two-computer workflow. None of these checks proves physical USB behavior.

<details>
<summary>Technical evidence mapping for reviewers</summary>

The example uses `firmware-protocol / usb-firmware`, `pc-software / usb-pc`, and `simulation-validation / usb-simulation`; `synthetic-interface-notes` is reference-only. Do not copy these demonstration identities into a real user's governance.

- Source evidence records selected scope, revisions, reading and understanding. Each working chat retains its original task/chat, actual directory/Git identity, checkpoint and current `view_id`.
- `PUBLISHED`, `REVIEWED_EVIDENCE_RECORDED`, `finalization_pending=false` and matching source freshness are separate checks. Actual native doctor/status and reading evidence from that chat are still required.
- `profile=complete_v1` can report `complete_governance_ready=true` only after every required item passes. Before actual scheduled occurrence, `natural_trigger_verified=false` and `closed_loop_verified=false`. Configuration, natural trigger, original-chat AI execution and report delivery have separate evidence.
- Engineering evidence preserves exact versions, frame inputs, parsing/CSV outputs and disconnect/reconnect results. UI, firmware and device acceptance remain separate.
- Recovery evidence includes the manifest, coverage/exclusions, independent restore and standby state. Transfer, host acceptance and single-writer handoff are distinct.

See [Governance API](../GOVERNANCE_API.md) for fields and calls, and the [complete governance fixture](../../examples/complete-governance/README.md) for synthetic inputs.

</details>

## Example feedback after updating an existing project

This illustrates feedback for the USB acquisition project, assuming the listed checks actually passed. It is not a receipt from a real installation.

> Candidate compatibility checks passed in an independent environment. The firmware/protocol, PC curve/CSV and simulation chats still map to their original tasks and latest checkpoints. The frame-format decision and its source remain. The task waiting for a device parameter remains paused; completed decoder checks have not become pending work again.
>
> Old-state project backup, manifest verification and independent restoration passed. The restored replica remains in standby; production state was not replaced. Next, switch the exact package within the authorized scope and check each native chat's loaded runtime. Without installation authorization, the verified current combination continues running.
>
> The improved project governance rules can be adopted separately. Public release, package installation and actual local resolution are recorded separately. Physical devices and another computer retain their own verification scopes.

On failure, report the exact step, actual effects, retained original plan and next condition. Do not restart every chat's initial setup or interpret a backup rejection as evidence that history was lost.
