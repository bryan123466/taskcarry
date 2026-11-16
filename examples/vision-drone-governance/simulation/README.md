# From scattered chats to a working obstacle-avoidance simulator

[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

This case shows TaskCarry preserving existing software, algorithm and hardware work, joining those chats to shared governance memory, and adding product and independent testing roles to deliver a local visual obstacle-avoidance prototype. [Open the application](app/index.html) or read the [demo route](product/DEMO_ROUTE.md). GitHub displays HTML source: download the complete package and open the HTML file in desktop Chrome to run it without a server or network.

## Try the result

1. Open `app/index.html` and select the clear-room, fixed-obstacle, or dropped-frame-and-recovery scene.
2. Start the scene and inspect generated camera pixels, detection boxes, route and tick records. Pause, continue and reset are available.
3. Export the JSON log. Two runs of the same scene from reset produce identical logical records.

The application UI and original engineering reports are in Chinese. This is a discrete 2D simulation with generated image pixels and an inspectable color/component vision baseline. Hardware delivery consists of engineering documents and budgets. Physical wiring, real cameras, flight dynamics, real flight and trained vision models have not been validated. The detector consumes actual pixel buffers; the controller chooses actions from detections. A pixel-only counterfactual changes both detection and movement.

## How governance helped

The original technical chats had separate interface drafts, algorithm plans and hardware constraints. Governance asked the user to choose the project scope, retained the original tasks and decisions, then agreed a concrete offline milestone. Original chats continued their professional work. An independent testing chat shared the governance directory with its own task and actual chat route. TaskCarry kept the decision history, dependencies and stopping points, published current work entries, and checked each chat's own receipt.

| Role | Delivered work | Shared dependency |
| --- | --- | --- |
| Software | Six-file offline app, frame rendering, UI, tick execution and export | Exact algorithm files and one interface contract |
| Algorithm | Pixel detection and detection-driven movement | Empty, missing, invalid and counterfactual pixel inputs |
| Hardware engineering | Modules, wiring concept, timing, budgets and measurement backlog | Shared frame specification; estimates separated from measurements |
| Independent testing | Chrome operations, real downloads and failure probes in a separate copy | Matching tested-file hashes and reproducible observations |
| Product | Introduction, user guide, demo and claim-to-evidence mapping | Claims supported by passing checks |
| Governance | Goal, decisions, responsibilities, interface and acceptance plan | Actual professional receipts; separate publication verification |

The user-facing onboarding still has three steps: establish governance, follow its connection guidance, and receive the acceptance report and next steps. The case expands the work behind that flow. Associating an existing chat with a Codex project loads that project's configuration without replacing the chat. In this Windows exercise, the four original professional chats began succeeding with native MCP after the user restarted Codex following project configuration and trust. Each chat still required its own connection check.

A later [on-demand chat-continuation exercise](continuity/README.md) preserved the original algorithm task when its writer was deliberately stopped, created a replacement chat in the existing trusted project, and completed a new three-frame pixel-boundary check. Governance verified the returned evidence and the old chat's read-only acknowledgment. This tested a controlled handoff, not a host crash or recovery of unsaved context; no empty spare chat was created in advance.

## Deliverables and evidence

- [Software guide](SOFTWARE_RUN.md), [algorithm baseline](algorithm/ALGORITHM_BASELINE.md), [unchanged interface contract](INTERFACE_CONTRACT.json).
- [Hardware engineering](hardware/HARDWARE_ENGINEERING.md), [wiring plan](hardware/INTERFACE_WIRING_PLAN.md), [resource budget](hardware/RESOURCE_BUDGET.csv).
- [Independent report](testing/TEST_REPORT.md) and [machine-readable checks](testing/test-evidence.json): nine browser checks and the engineering-document check passed for the delivered source app. Replay of the exact public export is recorded separately.
- [Product introduction](product/PRODUCT_INTRO.md), [user guide](product/USER_GUIDE.md), [claim register](product/product-claims.json).
- [Historical plan](governance/PROJECT_PLAN.md), [acceptance plan](governance/ACCEPTANCE_PLAN.md), [file hashes](case-manifest.json).
- [Native MCP and view-consumption acceptance](evidence/native-acceptance.json): six actual chats passed; the four original professional chats passed after the user's restart, while governance and testing reuse their earlier matching-runtime receipts.

Development self-tests, independent browser tests, native MCP checks and governance consumption are distinct evidence layers. Browser success does not certify MCP loading. Published files do not prove a chat read them. Public evidence removes actual host paths and chat identifiers; files with `export_metadata` are sanitized exports. The six app files and contract retain their original bytes. The [earlier v1 case](../native-case/README.md) remains available.

## Reproduce the checks

Copy this directory to a scratch location. The app needs only a browser; automated verification additionally requires Node.js 24 and a local Chrome installation. Set `RC8_CHROME_PATH` when automatic OS-based discovery is insufficient. The verifier uses a separate temporary browser profile.

From the copied directory:

```sh
node algorithm/verify-algorithm.cjs INTERFACE_CONTRACT.json
node testing/prepare-public-handoff.mjs
```

The second command checks the public manifest, resolves paths for this run, and invokes the independent verifier on a separate app copy. Results, actual downloads, screenshots and pixel probes go into `testing/local/`; shipped historical evidence is preserved. The separate software self-test, `node verify-software.mjs`, writes to `local/`. These browser-test dependencies belong to the example; TaskCarry Core continues to use the Python standard library and Git when needed.

The [independent public-product review](testing/public-product-review.md) passed for the exact 50-file object it identifies. This distribution then normalizes text to LF, updates dependent public-file hashes and adds the review summary, navigation links and separately evidenced continuation case. Those export differences are disclosed separately; the earlier pass is not presented as a review of later additions. The app, contract, verification scripts and frozen technical snapshot retain their accepted bytes.
