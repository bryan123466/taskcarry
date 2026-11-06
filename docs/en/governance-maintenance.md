# Keep governance current while work continues

[简体中文](../zh-CN/governance-maintenance.md) · [繁體中文](../zh-TW/governance-maintenance.md)

TaskCarry keeps project records in the control directory while the installed toolkit provides the operations that use them. Updating the toolkit should help the next session continue the same work. It should not create a new project, resubmit past results, or merge business branches simply to refresh a Skill.

This is a technical reference for the governance assistant. Users can start with the [update prompt](updating.md); the assistant consults these details when needed. Standard scheduling is covered in [scheduled governance](automation.md).

## Three updates with different purposes

| What changes | How to use it |
|---|---|
| Toolkit and project Skills | Evaluate an exact candidate; within authorization prepare a separate runtime, preview managed/configuration changes, preserve the old environment and verify native host loading. |
| Shared project progress and rules | Read current Core context/facts, then publish a source-versioned workbench view only where guidance changed. Verify consumption without merging business Git branches. |
| Accepted code or deliverables needed by a worker | Use an explicit `adopt` plan. This is a business/code update and keeps its existing conflict and WIP checks. |

## Start a governance turn with current work

`agenda` gives the existing AI a limited selection of unfinished operations, submitted stages, and artifacts needing a decision. Paused or waiting tasks stay recorded without becoming extra deliveries. Completed history remains available through the full status and records.

```json
{"limit": 20}
```

Send this to `taskcarry_agenda`, or use the CLI `agenda` action with a JSON request file. Follow `next_cursor` to inspect remaining pages. A cursor belongs to the same current-input fingerprint; if work changes, start a fresh selection. Pass the previous `fingerprint` as `previous_fingerprint` when comparing observations. `changed: false` does not close pending work or authorize another attempt.

Selection does not perform a repair, run another AI, or start a schedule. Matching experience is a suggestion; the existing executor must still verify actual effects. An indexed store selects current records and required predecessors without loading unrelated completed history. The item limit bounds the response, not all current-input processing, query time or the duration of an AI session.

## Maintain the current-work index

New projects create the derived index automatically. An older or invalidated index leaves the original records intact: `agenda` falls back to a full selection and reports `storage.upgrade_required`. After installing the chosen toolkit version and safely stopping affected governance writers, use the explicit `upgrade` action on the existing control directory:

```sh
python -I -X utf8 -m taskcarry --project ./control upgrade
```

Use the actual existing control path; do not initialize a replacement. The action rebuilds only the derived index, in one transaction, and is safe to repeat. Original records and events remain unchanged. Confirm `storage.mode` is `indexed_current_v1` and `storage.upgrade_required` is false afterward. This is not a package updater or a migration of business files. An older client writing records can invalidate the index again; retire that writer before rebuilding it.

## Preserve reviewed evidence and a run's exact scope

When authorized host tools supply relevant evidence, `observe` records its source reference, reviewed revision, registered task/workspace and explicit stage or artifact relationships. Repeating the same observation reuses it; a changed observation requires the previous revision so stale information cannot overwrite newer evidence. The record does not fetch a chat, establish source truth or grant access. Preserve a source reference rather than copying sensitive conversation content.

For a round with selected work, `run` starts a record with named stages, operations and relevant observations. Finishing it checks the recorded terminal states of that selection. It reports unresolved objects and changed observations without replaying the operations or silently adding later work to the original scope. Verify actual effects through the corresponding operation tools first; a run result summarizes those records, not an independent Git audit. New work and the project's overall state remain separate from the selected result.

See [the evolution report](governance-evolution.md) for the reasoning and focused synthetic checks behind these changes.

## Resume an interrupted installation

Before upgrading, inspect current receiving work and pending adoptions. `reconcile` accepts a planning `limit` (default 20, maximum 100), selecting unfinished receiving operations before new stages. Their identities enter the frozen plan. Plan completion covers its selection; later deliveries remain pending and are reported separately. An agenda page does not define execution scope.

An adoption preparation failure retains its error and checkpoint for the next agenda. Once the conflict is addressed, a successful successor can explicitly supersede it while preserving the original failure. Do not erase journals or retry unchanged conflicts. `refresh_plan` offers planning advice for proven no-effect operations; it does not execute a replacement. `verify_and_finalize` lets the receiving executor verify an existing effect and finish its receipt.

Setup saves an exact installation intent before changing managed files. If it stops after writing a file but before recording the result, repeating the same install can recognize that effect and finish the record. Files that have already reached the expected state do not need to be rewritten.

If you have edited a managed file, or selected a different candidate while an installation is pending, setup preserves the evidence and reports the conflict. Keep the pending record and use the original candidate to diagnose or resume; deleting metadata is not a recovery method. Unmanaged files are not adopted merely because they happen to match a packaged file.

While setup is changing its managed files, avoid editing those same files in another application. Its lock coordinates setup operations; it does not lock every external editor.

## Confirm which version is actually running

Keep the precise wheel, managed-file manifest and activated configuration before a package change. Forward compatibility does not guarantee downgrade compatibility; review the complete set and later user edits before recovery. Keep existing checkpoints and pending operations, and resume them with a compatible package. There is no automatic rollback command.

A historical source snapshot describes what was used then; a current runtime observation or adoption receipt describes what is used now. Preserve both when software changes. The selected Codex adapter reports its actual history coverage; it does not import arbitrary legacy identities or promise access to every native chat.

`doctor.runtime` reports the package version, interpreter and module location imported by the process answering the request, together with managed setup information. A successful CLI check does not prove a previously opened MCP process has reloaded. After deliberately updating its configuration or restarting that connection, check through that connection too.

Source fingerprints describe the files currently on disk. They do not prove that a long-running process has replaced previously imported code. Restart the affected MCP connection after changing the runtime package; `loaded_code_verified` remains false rather than asserting in-memory code attestation.

For TaskCarry's own development, run governance from an installed wheel outside the editable source checkout. Develop and test the next version separately. Adopt it when the affected operations are safely stopped. Keep the control directory: tasks, checkpoints and previous receipts belong to the project, not a particular toolkit build. This release does not include a general automatic package upgrader or a cross-schema rollback engine.

## One governance chat, separate repository scopes

One control store still has one receiving baseline. A product with two independent repositories can use two control stores and one common project overview maintained by its governance chat. Give each MCP connection an explicit distinct `server_name` during setup, for example `product_core` and `product_app`; subsequent setup calls retain the chosen name.

```json
{"mode": "preview", "server_name": "product_core"}
```

After reviewing the result, use `mode: install` with the same name. The generated fragment still requires deliberate host configuration; it is not activated automatically. Do not assign two control stores to write the same receiver. This arrangement does not create a shared multi-repository transaction or a cross-computer lock.

The same issue found by a local governance turn and by a user report should remain one product change. Fix the shared implementation once, validate it, then record which installations adopted it. A note about a fix and the installed fix are different parts of that work.


## Complete governance and task continuation

The `complete_v1` checklist covers persistent project/replica identity, understood selected sources, real task/workspace/Git bindings, per-chat native connection and exact workbench consumption, local governance Git, the first bounded cycle, an independently verified recovery rehearsal, official update checking, and two or three daily original-chat slots. These are standard setup items. Private remotes, cloud storage and ongoing project coordination remain choices. Historical reference chats need source evidence, not artificial active workspaces.

Read `context` for the original task and current checkpoint; use `facts` for source-qualified decisions and relationships, keeping evidence distinct from AI judgments. Use `cycle` to retain the exact owner/resources, intended effects, actual receipts, source phases, health and next step. `source_scan` only enumerates authorized local metadata through bounded pages; the host separately reads selected bodies. Details and payloads are centralized in [Governance API](../GOVERNANCE_API.md).

`workbench` freezes a source-versioned view, plans exact private entry changes and publishes them without modifying Git HEAD/index or unrelated WIP. Verify the current pointer, original task/thread and source freshness; publication, reviewed consumption and native doctor/status are separate evidence. An old view with changed sources is not current truth.

`recovery` captures a selected consistent project set, verifies bytes and restores independently in standby. Its receipt lists `disabled_host_files`: preserved host-configuration evidence is kept out of active restored configuration until regenerated for the new machine. Original project identity and a new replica identity do not authorize two writers. Explicit handoff and actual native verification precede writer activation. [Recovery coverage](remote-and-multicomputer.md) distinguishes local capture, transport and real second-host evidence.

Legacy records remain readable. `identity plan/execute` explicitly adopts a portable project identity while retaining the old source alias; it does not silently merge another project. `upgrade` separately maintains derived indexes. Older acceptance records retain their original profile; a new complete-governance review reuses applicable evidence and fills actual gaps instead of rewriting history.

## Identify, evaluate and preserve before changing anything

Use `identify` on the selected location before initialization. Unknown, corrupt or unsupported state is preserved. A nonempty SQLite WAL makes this inspection report busy rather than ignoring pending data; let the existing writer close and retry without deleting its journal. Compatible state is reused.

Register the official channel and installed identity with `update_source`. `update_check` performs a bounded read; `update_assess` explicitly retains the applicability decision. Keep discovery, evaluation, preparation, installation, setup and native host loading separate. `governance` records the package/method identity and selected custom-rule fingerprints; recording a fix is not proof it was adopted.

Use `connect` plan/execute for supported project-only MCP merges, and `preserve` plan/execute for explicitly selected Git files. Preserve comments, unrelated services, custom AGENTS and Git index/worktree state. Repository preparation and Git author verification remain real setup work. Exclude live governance databases, runtime, downloads, secrets and unrelated files from version-saving selections.

Use selected `recovery` sets for consistent state, referenced objects, Git history/index/WIP and explicit materials; use checkpoint `restore` for its narrower selected-file scope. Report capture, local verification, upload, fresh download, independent restore and host activation separately. An artifact reference is not a database snapshot or proof of remote storage.

The legacy `storage.upgrade_required` flag describes only the current-work index. Also check `storage.context_ready` and `storage.context_upgrade_required`: an older installation may have a valid agenda index but still need the explicit context-index upgrade.
