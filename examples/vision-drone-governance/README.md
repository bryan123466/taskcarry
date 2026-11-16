# A drone project across four conversations

[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

Three existing conversations have useful work: a software display, an algorithm event proposal, and a hardware interface sketch. They do not yet agree on the first milestone or the event fields. TaskCarry helps the governance conversation retain that work, reconcile the project memory, and give each original conversation a precise place to continue. A new product/presentation conversation fills a missing role.

The example is a **vision obstacle-avoidance drone concept**. Its first milestone becomes an **indoor, fixed-obstacle offline demonstration**. It illustrates project governance and a product shape; it does not establish a working recognition model or aircraft.

## What happens in the example

| Point | Project state | What governance contributes |
| --- | --- | --- |
| Before installation | Software proposes `frame_id/label/region`; algorithm adds confidence and timestamps; hardware needs capture-time provenance. | Read the selected existing conversations and keep their artifacts, effective decisions and unfinished work. |
| Project selection | The user selects this drone project. | Explain the shared goal and uncertainties, retain the three original conversations, and recommend a product/presentation role. |
| Initial setup | Four conversations have separate responsibilities and working locations. | Connect the same control, preserve task identities, establish local versioned memory, and verify each connection separately. |
| Scope change | The user chooses an indoor/offline first milestone. | Retain the earlier exploration as history; publish the new scope and shared interface to all four roles. |
| Continued work | Software updates the demo; algorithm aligns cases; hardware narrows integration; product copy matches evidence. | Distinguish publishing a workbench entry from the professional conversation actually reading and acting on it. |
| Interruption or recovery | Some work is incomplete, or a separate recovery copy is needed. | Continue the original checkpoint and exact plan; restore a standby copy while preserving task and Git history. |

The outdoor investigation remains a paused task. It is neither deleted nor treated as an urgent failure. The original software, algorithm and hardware tasks keep their identity.

An existing discussion may never have used TaskCarry. In that case, onboarding gives its work a stable task record linked to the original conversation and artifacts. If a TaskCarry task already exists, retain that identity. The deterministic replay starts with registered synthetic tasks so it can also verify that existing task/checkpoint relationships survive.

## Read the inputs and verify the result

- [Synthetic initial notes](initial/software.md), [algorithm notes](initial/algorithm.md), [hardware notes](initial/hardware.md) and [the proposed new role](initial/product-brief.md).
- [Scenario and expected scope](scenario.json): portable task names, original and current scope, retained decision and explicit deferred work.
- [Real-chat verification runbook](NATIVE_CHAT_RUNBOOK.zh-CN.md): start with scattered discussions, apply the main guide, then verify a real scope change. This is a runbook, not proof that a host action occurred.
- [Evidence and expected outputs](EVIDENCE.md): what a useful project result looks like and how to distinguish source inputs, executable replay and native evidence.
- [Executable local replay](replay.py): uses TaskCarry's shared API to exercise the governance records and actual filesystem/Git/recovery effects.

The main installation guide contains the three onboarding steps. This case provides a concrete outcome to compare against; users do not need to reproduce a drone project to install TaskCarry.

## Run the deterministic local replay

Use Python 3.11+ with the candidate TaskCarry wheel installed in a separate environment, and Git. Run with that environment's interpreter; `-I` prevents the current source directory from shadowing the installed package. Select an **absent or empty synthetic destination**. In this example directory:

```text
python -I replay.py /path/to/empty-drone-demo
python -I replay.py /path/to/empty-drone-demo --execute
```

The first command only displays a plan. The second executes local synthetic work. Replace the example destination with the one you selected; no user-level settings, chats, schedules, network calls or flight hardware are used. Do not use a real project directory.

The resulting tree is:

```text
empty-drone-demo/
  TaskCarry/               Synthetic project memory and local Git history
  workspaces/
    software/              Retained software notes and unfinished draft
    algorithm/             Retained algorithm notes and unfinished draft
    hardware/              Retained hardware notes and unfinished draft
    product/               Newly proposed product/presentation role
  recovery-media/          Selected state, files and Git recovery objects
  restore-controller/     Independent controller used for the restore
  standby/                 Independent restored copy; writer inactive
  REPLAY_REPORT.json       Actual local replay result and explicit evidence limits
```

The tests also inject an interrupted workbench publication and a lost final recovery receipt. They inspect actual effects and continue the same plan. They preserve staged and unstaged work, keep the original checkpoints, and verify that the recovery copy cannot silently become an active writer.

## What the example establishes

A local replay can prove local task continuity, source-qualified decision history, bounded publication, exact file preservation and standby recovery. It cannot prove that an AI understood a chat, that MCP is loaded in a particular native window, that a scheduled heartbeat arrived naturally, or that a drone works. Native chat outputs and host receipts must be reviewed separately; they must never be manufactured by the replay.
