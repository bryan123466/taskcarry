# Complete governance example: USB acquisition and curve display

This synthetic project gives governance a concrete job: keep firmware/protocol, PC software and simulation work aligned while a user develops a USB data-acquisition tool. The first milestone uses simulated readings, displays their values as a curve, and exports CSV. Wireless support is outside this milestone; actual device work requires separate acceptance.

## Understand the work before the governance fields

| Existing responsibility | Next useful output | Observable acceptance |
|---|---|---|
| Firmware and protocol | A shared text-frame agreement and repeatable mock readings | Both sides use the same fields, units/meaning and line boundary; this fixture asserts no physical unit. |
| PC software | Parser, curve display and CSV export | Three input frames supply three matching points and CSV rows; actual UI and file operations need additional checks. |
| Simulation validation | Normal, disconnect and reconnect replay | No invented reading during disconnection, no duplicate old point after reconnection, and incomplete frames are not joined across a break. |
| Hardware/interface notes | Retained decisions and constraints | Read as references; not counted as active chats or new assignments. |

These responsibilities can share existing chats. The demonstration has three active workbenches because its synthetic scenario already has that division; a real user need not create three windows. Governance keeps effective decisions, task relationships, exact results and continuation points while the user works directly in those chats.

## A shared input everyone can inspect

UTF-8 text, one LF-terminated reading per line:

```text
READ,42,1000,1.234
READ,43,1100,1.250
READ,44,1200,1.220
```

The fields are type, sequence number, simulated elapsed time in milliseconds, and simulated measurement value. The three curve-input points occur at 1000, 1100 and 1200 ms. Corresponding CSV rows contain `1.234`, `1.25` and `1.22`; decimal formatting can differ while numeric values remain equal.

- [Protocol and assumptions](fixture/PROTOCOL.md)
- [Normal input](fixture/normal_frames.txt)
- [Expected CSV](fixture/expected.csv)
- [Executable replay checks](fixture/replay.py)

With Python 3.11 or newer, run from this example directory:

```sh
python fixture/replay.py
```

The standard-library checks exercise sample parsing and CSV values, invalid/non-finite records, partial frames, disconnection/reconnection and numeric round-trip preservation. Old or duplicate sequences are ignored. Reconnection assumes sequence numbers continue; a device that resets its counter needs an explicit session/epoch agreement beyond this fixture.

This executable is deliberately a small parsing/replay fixture, not a complete USB application. It does not read a physical serial port, implement or flash firmware, draw a live interface, or verify actual CSV file interactions. A passing result proves the specified synthetic data outcomes; the displayed application, hardware and timing require their own evidence.

## What TaskCarry governs in the example

[scenario.json](scenario.json) defines the selected project and original responsibilities. Integration tests exercise project identity, sourced decisions, bounded cycles, each current workbench entry, local Git, update identity, selected recovery data, an isolated restore and native schedule configuration readback.

Their host receipts are explicitly synthetic. They do not prove a real Codex connection, a natural scheduled trigger or report delivery. Real test-chat evidence belongs in its own report. Likewise, recording the intended curve-display task does not prove that a curve UI was implemented.

The user-facing order is the same as the three-step manual: establish governance, let it connect existing work and complete the first cycle, then review a clear report with responsibilities, actual results, gaps and next work. Required setup and the later naturally triggered loop remain separate acceptance levels. Source-only notes remain sources; unfinished engineering stays unfinished.

<details>
<summary>Synthetic identity and acceptance mapping</summary>

| Workspace | Original task | Synthetic chat |
|---|---|---|
| `firmware-protocol` | `usb-firmware` | `synthetic-firmware` |
| `pc-software` | `usb-pc` | `synthetic-pc` |
| `simulation-validation` | `usb-simulation` | `synthetic-simulation` |

`synthetic-interface-notes` is reference-only. The `complete_v1` setup profile requires actual checks for the configured scope; `complete_governance_ready=true` does not claim `natural_trigger_verified` or `closed_loop_verified` before natural execution. A restored replica stays in standby until an explicit single-writer handoff.

Adapt source selection and responsibilities to actual work. Do not insert these example identities, simulated receipts or demonstration engineering tasks into a user's governance store.

</details>

[API reference](../../docs/GOVERNANCE_API.md) · User feedback: [English](../../docs/en/user-feedback-examples.md) / [简体中文](../../docs/zh-CN/user-feedback-examples.md) / [繁體中文](../../docs/zh-TW/user-feedback-examples.md)
