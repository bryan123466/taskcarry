# What to review in this case

The files under `initial/`, `scenario.json`, the runbook and `replay.py` are authored synthetic tutorial inputs. They are not exports of real customer projects or claims of native chat execution.

The [earlier native-case export](native-case/README.md) contains actual outputs from the first dedicated-chat milestone: retained initial work, a fixed-event replay, technical documents and product guidance. Its original pending native and scheduling statements describe that historical batch. The files and receipts are preserved.

The later [complete simulator export](simulation/README.md) advances the same original work into an image-driven application, engineering documents, independent testing and product presentation. Six delivered application files and the interface contract retain their original bytes. Exported reports, portable scripts and sanitized receipts have their own [file hashes](simulation/case-manifest.json); they are not presented as byte-identical raw host responses. Actual host paths, chat/turn IDs and original private receipts are kept outside the public repository.

## Current verified results

| Evidence layer | Actual result | Evidence and limit |
| --- | --- | --- |
| Algorithm | 5 checks passed on a relocated public copy | Pixel counterfactual, valid/missing/invalid frames, connected components and movement order; [algorithm baseline](simulation/algorithm/ALGORITHM_BASELINE.md). Generated pixels and a rule-based baseline, no trained model. |
| Independent browser | 9 checks passed on the original delivered app and again on a relocated public copy | Offline controls, three scenarios, pixel causality, collision, invalid input, timeout and actual JSON downloads; [report](simulation/testing/TEST_REPORT.md), [recorded observations](simulation/testing/recorded/run-evidence.json). |
| Software verifier | 10 checks passed on the relocated public copy | Includes package byte identity and app behavior. Its checks overlap with independent checks and are not added together as unique Core tests; [software evidence](simulation/software-evidence.json). |
| Hardware engineering | Document review passed | Contract, wiring concept and resource arithmetic; [engineering documents](simulation/hardware/HARDWARE_ENGINEERING.md). No physical wiring, measurements, hardware execution or flight. |
| Native MCP and workbench consumption | Six actual chats passed individually for their recorded batches | [Native summary](simulation/evidence/native-acceptance.json) matches runtime/control/task and each window's own receipt. Four original professional chats passed after project trust and the user's Codex restart; governance and testing retain earlier matching-runtime evidence. A later view or replacement chat needs new evidence. |
| Product claims | Independent review passed the recorded 50-file public snapshot, ten checks and twelve claims | The [independent product review](simulation/testing/public-product-review.md) names the exact reviewed object and its 97 file references, 110 local links and four historical links. The [claim register](simulation/product/product-claims.json) matches technical evidence; later LF normalization and its new manifest require separate byte verification. |
| Replacement-chat continuation | Complete controlled exercise: native access, own consumption, new three-frame verification, old-chat read-only return and governance absorption | [Continuation case](simulation/continuity/README.md) and its separate receipts retain the original task/checkpoint, Git state, 25 files and four history preimages. The old chat intentionally recorded no new consume; its prior NOT_VERIFIED state does not negate the observed read-only acknowledgment. No actual compaction failure was induced or repaired. |
| Natural scheduling | Not verified for this RC8 case | Configuration, actual trigger, AI execution and report delivery remain separate observations. No temporary script or manual message substitutes for natural delivery. |

The six-chat evidence identifies Core source `c3aac797da4b1f9ca9fc57581bd004d600ef2d31` and disk runtime fingerprint `e1c8571120eea9eaaea60891a7cabef51cef1ab0e5c276d32318ae18262e6b90`. The raw engine fields `loaded_code_verified: false` and `native_acceptance_verified: false` remain unchanged; the summary's native conclusion uses actual host call markers and matching returned objects. Core source tests, installed-package/stdio checks and final release checks remain separate from this case. Twenty focused source-pinning/release-screen checks and one standard wheel/sdist build check passed separately. Packaging verifies manifest membership, sizes and SHA-256 against the actual frozen bytes; example text uses LF so checkout normalization cannot silently stale those hashes. The bundled [release notes](../../docs/RELEASE_0.2.0rc8.md) summarize their scope; final source, CI and attachment hashes belong to the actual published release.

## Useful project outputs

The project should have tangible outputs beyond a list of task names:

| Owner | Output | Review question |
| --- | --- | --- |
| Governance | Project definition, current scope, decision history and responsibility map | Does the indoor/offline milestone coexist with the retained earlier exploration and original task identities? |
| Software | A runnable offline app with scene selection, frame/detection/route display, pause/reset and JSON downloads | Are missing/invalid frames, terminal collisions and timeouts visible without suggesting real aircraft control? |
| Algorithm | Pixel detector and detection-driven controller under one interface contract | Does a pixel-only change affect detections and movement, without giving the controller the world obstacle map? |
| Hardware | Engineering plan, wiring concept, resource budget and measurement backlog | Are calculations separated from physical measurements, with real hardware and flight still deferred? |
| Independent testing | Separate app copy, actual browser controls/downloads and failure probes | Do input hashes match the delivered application, and are observations independently reproducible? |
| Product/presentation | A concise introduction and review checklist | Does the description match the actual offline demonstration instead of claiming tested recognition or autonomous flight? |

## Evidence levels

1. **Local replay:** `replay.py` calls the shared Core API, creates actual synthetic Git repositories, preserves checkpoints and decision revisions, publishes local workbench entries and verifies independent recovery. `REPLAY_REPORT.json` names its results. It explicitly keeps native and natural-schedule claims false.
2. **Native conversation exercise:** the dedicated chats followed the main installation guide and continued original work, including a new independent testing role in a shared directory. Each chat's actual native connection and current-view consumption are supported by its own reviewed receipts; these do not certify a later view or replacement chat.
3. **Natural schedule:** configuration, an explicit invocation and a heartbeat arriving naturally at a selected time are different observations. Record each only when it happens; a deterministic script is not natural delivery.
4. **Engineering validation:** actual image buffers, browser behavior and documents have scoped evidence. The case does not train a model, connect aircraft hardware, perform a flight or establish real-world detection accuracy. Those are future engineering tasks with separate protocols.
5. **Chat continuation:** on-demand handoff retains the original control, task, checkpoint, saved outputs and effects, binds a new real host ID, then verifies its own native access, view consumption and useful next action. The [completed exercise](simulation/continuity/README.md) includes the old chat's read-only return and final governance absorption. The old writer must first stop. Routing is not a hard filesystem lock; host compaction repair and unsaved context recovery are not claimed.

## Repeatable failure checks

`tests/test_vision_drone_governance.py` checks observable outcomes:

- A read-only plan leaves the destination absent; existing user work is refused and left intact.
- Original task creation identities and prior checkpoints survive setup; the changed scope keeps both fact revisions and the paused outdoor task.
- Each of four local entries binds the expected task and new view. Publishing does not manufacture a native consumption receipt.
- One injected write interruption leaves three entries published; reopening and executing the same plan completes the missing entry without changing professional Git HEAD, index or unfinished work.
- A restore interrupted after its files land but before the last receipt is recovered by inspecting the existing effect. It retains all original task/checkpoint identities and Git history, remains standby, and refuses unapproved writes.

Public native-case exports must contain only synthetic project materials, relative paths and reviewed evidence summaries. Keep real chat IDs, local account paths, host configuration, original receipts and unrelated project material in private validation storage.
