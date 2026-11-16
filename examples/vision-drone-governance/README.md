# From scattered chats to a drone simulation project

[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[Open the complete simulator case](simulation/README.md): an offline image-driven application, algorithms, hardware engineering documents, independent testing and product presentation. [Six-chat native acceptance](simulation/evidence/native-acceptance.json) is recorded separately from browser tests and natural scheduling. The [earlier fixed-event milestone](native-case/README.md) remains available with its original evidence boundaries.

Three existing conversations have useful work: a software display, an algorithm event proposal, and a hardware interface sketch. They initially disagree about the first milestone and event fields. Governance retains that work, connects the original chats to one project memory, then recommends product and independent testing roles. Six chats now have distinct responsibilities, including governance; testing shares the governance directory while keeping its own task and route.

The delivered prototype is a **visual obstacle-avoidance simulation**. Generated image pixels feed a rule-based detector, whose detections guide movement through a 9 × 9 discrete 2D world. Three scenes cover clear space, fixed obstacles and dropped frames followed by recovery. The application provides pause/reset and JSON export. Hardware deliverables are engineering documents; trained vision models, flight dynamics, physical wiring and real flight are outside the validated scope.

## What happens in the example

| Point | Project state | What governance contributes |
| --- | --- | --- |
| Before installation | Software proposes `frame_id/label/region`; algorithm adds confidence and timestamps; hardware needs capture-time provenance. | Read the selected existing conversations and keep their artifacts, effective decisions and unfinished work. |
| Project selection | The user selects this drone project. | Explain the shared goal and uncertainties, retain the three original conversations, and recommend product/presentation and independent testing roles as the milestone expands. |
| Initial setup | Six chats share the project with distinct responsibilities; two share a directory. | Connect the same control, preserve task identities and local versioned memory, then verify each connection and current-entry consumption. In this Windows exercise, the four professional chats passed after project trust and a Codex restart. |
| Scope change | The user chooses an indoor/offline first milestone. | Retain the earlier exploration as history; publish the new scope and shared interface to all four roles. |
| Continued work | Software updates the demo; algorithm aligns cases; hardware narrows integration; product copy matches evidence. | Distinguish publishing a workbench entry from the professional conversation actually reading and acting on it. |
| Runnable prototype | The detector processes image pixels, software executes and exports the three scenarios, and an independent tester checks a separate copy. | Align the interface contract, exact deliverables, engineering limits and claim evidence. The relocated public copy passed 5 algorithm, 9 browser and 10 software checks. |
| Interruption or recovery | Some work is incomplete, or a separate recovery copy is needed. | Continue the original checkpoint and exact plan; restore a standby copy while preserving task and Git history. |

The outdoor investigation remains a paused task. It is neither deleted nor treated as an urgent failure. The original software, algorithm and hardware tasks keep their identity.

An existing discussion may never have used TaskCarry. In that case, onboarding gives its work a stable task record linked to the original conversation and artifacts. If a TaskCarry task already exists, retain that identity. The deterministic replay starts with registered synthetic tasks so it can also verify that existing task/checkpoint relationships survive.

## Read the inputs and verify the result

- [Complete simulation](simulation/README.md), [independent report](simulation/testing/TEST_REPORT.md), [native acceptance](simulation/evidence/native-acceptance.json) and [product guide](simulation/product/USER_GUIDE.md).
- [Earlier actual-chat milestone](native-case/README.md): original work and fixed-event replay, retained as historical evidence rather than overwritten by later results.
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

A local replay proves supported local task, file, Git and recovery behavior. The separate simulator and six actual native chat receipts provide additional, dated evidence for their own layers. Natural scheduling, physical flight, production adoption and multi-computer handoff remain unverified by this case.

The governance method also supports preparing a replacement chat on demand, keeping the original task and saved work after the old writer has stopped. The [controlled continuation exercise](simulation/continuity/README.md) is complete: the replacement algorithm chat verified its own native access and current entry, completed a new three-frame pixel-threshold/connectivity check, and returned evidence to governance. The old chat confirmed the handoff read-only; the original task, saved work and Git state were retained. [Independent review](simulation/testing/public-product-review.md) passed the recorded 50-file public product snapshot, while subsequent LF-normalized bytes require their own manifest verification. The method does not repair a host compaction fault or reconstruct unsaved context. See the [evidence record](EVIDENCE.md).
