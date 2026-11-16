# Continue the original task when a chat can no longer work

The drone algorithm had already been implemented and integrated into the software. This exercise asks whether a new chat can continue that same work from saved project memory when the original chat can no longer write. Governance stopped the original algorithm writer, retained its task, directory, checkpoint and artifacts, and created a continuation chat only when needed.

This was a controlled unavailability exercise. It did not deliberately crash Codex or reproduce a context-compaction failure. It tested task continuation outside the old chat. No unused spare chat was created during initial setup.

## Preserve the work before switching chats

The original chat finished its own verification and recorded that it had stopped writing. Governance checked the completed host turn and the absence of that chat's outstanding writers, then recorded Git HEAD, index, saved files and uncommitted work. The old chat, existing detector and original checkpoint remained available.

Governance published one handoff for the original algorithm task: retain the old chat as a read-only history source; let the new chat perform the bounded new check after validating its entry. The new chat uses its actual host identity to find the route, reads the same control and task, calls native MCP itself, and records its own view consumption. A configuration file or a receipt written on its behalf cannot substitute for these calls.

The continuation uses the single [delivered detector](../app/detector.js) as read-only input. It does not initialize a new project or replace the tested algorithm.

## Continue with a concrete engineering check

The next task tests the detector's minimum size of 16 pixels and four-connected component rule. Using the existing [interface contract](../INTERFACE_CONTRACT.json), the continuation chat independently writes a verifier for three 160×120 RGBA frames. Frame metadata, background and detector are identical; only selected obstacle pixels differ.

| Input | Boundary being tested | Expected result |
| --- | --- | --- |
| A: one 3×5 rectangle, 15 obstacle pixels | Below the size threshold | Valid frame, no detection |
| B: A plus one edge-adjacent pixel | One connected component reaches 16 | Exactly one box with pixel count 16 |
| C: A plus one diagonally adjacent pixel | Total 16 pixels split into components of 15 and 1 | Valid frame, no detection |

The new work records input digests, actual outputs, reproduction command and before/after detector hashes. The actual public outputs are [boundary evidence](boundary-evidence.json) and the [verification script](verify-boundary.cjs).

## Evidence currently available

| Step | Observed status |
| --- | --- |
| Original writer stopped; original task and directory retained | Recorded and reviewed by governance |
| New chat created on demand in the existing project | Completed |
| Two routes published for the same original task | Completed; prior entries and receipts retained |
| New chat's native connection, reading and consumption | Completed; see the [native summary](native-acceptance.json) |
| Three-frame check and preservation of original files | All three frames passed; original files and Git state retained |
| Old chat reads the new handoff and remains read-only | Read-only acknowledgment completed, without rerunning or recording new consumption |
| Governance reviews and preserves the new result | Completed; original task and checkpoint retained, reviewed summary saved |

The [continuation evidence](continuity-evidence.json) records the completed bounded exercise. Governance cross-checked the new chat's actual consumption, three passing frames, old chat's read-only acknowledgment, original Git state and four archived configuration preimages. The original business task remains at its original waiting checkpoint; this review does not mark the whole project accepted. The old chat deliberately did not submit a new Core consumption record: its `NOT_VERIFIED` consumer status is distinct from its completed host read-only acknowledgment.

## What a user should be told

The following illustrates the method; it is not a verbatim transcript:

> Your algorithm work is saved in the project. We will retain its original task and checkpoint. I will first confirm that the old chat and its background writers have stopped, then prepare the handoff. Create a new chat inside the existing algorithm project; keep the old chat for reference. You do not need to reinstall TaskCarry or move the original files. After the new chat verifies its MCP connection, task and current entry, it can finish the 16-pixel boundary check. I will incorporate its result into project memory. If the old chat becomes available, it must read the handoff and remain read-only so both chats do not write the same work.

When the host requires project trust, opening a folder or a restart, governance should give the exact location and limited steps. Completed checks are reused. The continuation depends on actual saved artifacts and checkpoints, not invented recollection of missing chat context.

**A different chat can continue using saved project memory, task identity and artifacts.** This does not repair the host or recover context that was never saved or read. TaskCarry routing identifies the right entry; the single-writer boundary relies on verified stopping and responsibility handoff, not a hard revocation of the old chat's filesystem permission.

```sh
node continuity/verify-boundary.cjs
```

Run from a copied simulation directory with Node.js 24. The portable verifier reads the fixed app and contract and writes a new result only under `continuity/local/`. It reproduces the pixel boundary check; it does not rerun a host chat handoff.
