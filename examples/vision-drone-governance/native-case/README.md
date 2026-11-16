# From separate chats to one offline demonstration

[简体中文：完整案例](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Example overview](../README.md)

These are reviewed exports from an actual exercise in dedicated **synthetic** conversations. Three original chats produced software, algorithm and hardware work. A governance chat read the selected history, preserved the outputs and unresolved decisions, and proposed a shared indoor offline milestone. The original specialist chats then used the same fixture to continue their work. These artifacts are distinct from the authored tutorial seeds in the parent `initial/` directory.

After downloading the complete product, open [after/software/monitor.html](after/software/monitor.html), select its adjacent [replay JSON](after/software/rc8-indoor-replay-v1.json), click **载入** (Load), **重置** (Reset), then **单步** (Step) six times. GitHub displays the HTML source; use the downloaded local page to run the demonstration.

The six ticks show a wall on the left, a column and box in one frame, a processed empty frame, a missing frame, a simulated disconnection after two missing ticks, and recovery with a box on the left. This is preset event playback, not image recognition or aircraft control.

| Stage | What to inspect |
| --- | --- |
| Separate original outputs | [Software proposal](before/software/SOFTWARE_BRIEF.md), [algorithm plan](before/algorithm/ALGORITHM_PLAN.md), [hardware concept](before/hardware/HARDWARE_CONCEPT.md). All 12 initial files remain intact. |
| Inherited project memory | [Intake snapshot](governance/INTAKE_MEMORY.md) retains the earlier indoor/outdoor uncertainty and interface differences. |
| Shared decision | [Replay protocol](governance/SHARED_INTERFACE.md) selects the indoor offline milestone, coordinate mapping, class names, time convention and missing-frame behavior. |
| Continued work | [Software page](after/software/monitor.html), [algorithm validator](after/algorithm/validate_replay.py) and [hardware calculations](after/hardware/HARDWARE_REPLAY.md) use the same fixture. |
| Cross-role review | [Governance review](governance/TECHNICAL_REVIEW.md) compares the actual reports and identifies claims that the technical evidence supports. |
| Product communication | The new role retained its [initial brief](before/product/PRODUCT_DEMO_BRIEF.md), checked the same page and input in a browser, and produced a [product introduction](after/product/PRODUCT_INTRO.md), [demo route](after/product/DEMO_ROUTE.md) and [user guide](after/product/USER_GUIDE.md), citing the technical checks. |
| Final project review | [Governance's final review](governance/PROJECT_REVIEW.md) checks the three documents against the observed replay and preserves the summary omission described below. |

The original algorithm's 40 ms sample remains a historical evaluation fixture. The shared replay uses nominal 15 fps, with times rounded independently to `0, 67, 133, 200, 267, 333 ms`. Its four candidate scores are manually assigned. Real capture timestamps, latency, hardware resource use, recognition performance and flight remain outside the verified scope.

From this directory, Python 3.11+ with its standard library can reproduce the technical checks:

```text
python -I -B -X utf8 after/algorithm/validate_replay.py after/algorithm/rc8-indoor-replay-v1.json
python -I -B -X utf8 after/hardware/verify_hardware_replay.py
```

Both commands read the fixture and print results without creating governance state, tasks or schedules. The fixture copies retain the original bytes and SHA-256 `2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17`.

The [software](after/software/software-evidence.json), [algorithm](after/algorithm/algorithm-evidence.json), [hardware](after/hardware/hardware-evidence.json) and [product](after/product/product-evidence.json) reports carry `export_metadata`: they are sanitized exports, not raw host receipts. The product role recorded 11 passing browser checks of the same page and fixture. Its references to the public technical reports and protocol use recomputed export hashes. [case-manifest.json](case-manifest.json) identifies exported files, hashes and transformations. Original mappings, real chat IDs, machine paths and host configuration remain private.

The product report's algorithm summary covers `checks` but omits two items retained in the algorithm report's `pending_checks`: reference-region evaluation for the shared replay, and measured recognition/flight performance. [Governance's final review](governance/PROJECT_REVIEW.md) identified this omission. The export preserves that original record and labels the summary gap. An empty list in the product summary does not establish that those evaluations passed.

**Native MCP acceptance and naturally scheduled governance are not established by this export.** Actual artifact work and technical replay succeeded while those integration checks remained separate. This exercise used dedicated chats with separate existing directories; it does not prove native acceptance for multiple chats sharing a directory or require users to create a folder for every chat. No real model, aircraft, hardware integration, flight or long-term multi-host operation was validated.
