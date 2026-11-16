# Complete governance API reference

This reference supports the assistant-led [three-step setup](en/windows-example.md). API, CLI and MCP use the same typed contracts. Reading does not migrate state. Mutation tools require exact scope and applicable authorization; tool availability grants no access to unrelated files or chats.

## Project discovery before initialization

`discovery` / `taskcarry_discovery` supports `status/plan/execute` in an existing governance working directory, including before it has a control database. The AI obtains authorized index metadata from the current host, proposes project groups and asks the user which project to connect. Core stores that bounded review; it does not scan Codex, read conversation bodies, group projects itself or execute text found in titles. A title, directory or AI grouping remains a clue until the selected history has been read.

Use `status` with `discovery_id` to resume. `plan` takes the complete next `draft` and the observed `expected_revision` (zero initially), and performs no filesystem write. Review its result, then pass the entire returned `plan` unchanged to `execute`. Before MCP is connected, use the same CLI with the explicitly selected installed interpreter in isolated mode; no additional control is needed. Input files use the normal `--input` option.

For example, a first plan input can contain one inspected active index and explicitly unknown archived coverage:

```json
{
  "discovery_id": "first-use",
  "action": "plan",
  "expected_revision": 0,
  "draft": {
    "sources": [
      {
        "source_id": "selected-host-active",
        "label": "Current host active conversation index",
        "archive_scope": "active",
        "coverage": "exhausted",
        "pages": [{
          "cursor": null,
          "next_cursor": null,
          "receipt_ref": "synthetic-index:active-page-1",
          "threads": [{"thread_id": "drone-software", "title": "Obstacle recognition drone software"}]
        }]
      },
      {
        "source_id": "selected-host-archive",
        "label": "Archived conversations not yet inspected",
        "archive_scope": "archived",
        "coverage": "unknown",
        "pages": []
      }
    ],
    "candidates": [{
      "candidate_id": "drone",
      "label": "Image recognition and obstacle avoidance drone",
      "reason": "AI proposal from the visible title; confirm scope before reading history.",
      "members": [{"source_id": "selected-host-active", "thread_id": "drone-software"}]
    }]
  }
}
```

Execute with `{"discovery_id":"first-use","action":"execute","plan":...}` where `...` is the exact returned plan object. After the user chooses, include `selection: {"candidate_id":"drone","confirmation_ref":"user-turn:project-selection"}` in a new complete draft, then plan and execute the next revision. The reference records the actual user choice; supplying text does not create user authorization. The result supplies a content-bound `selection_fingerprint`. Continue by reading only the chosen sources and preparing their actual onboarding; newly suggested professional windows are created through the host's authorized workflow.

Sources use distinct IDs for a selected host/index scope and scan. Each source declares `archive_scope` (`active`, `archived` or `unknown`), `coverage` (`partial`, `exhausted`, `unavailable` or `unknown`) and its saved pages. Pages begin at a null `cursor` and follow the previous `next_cursor`. Repeat pages with identical cursor/content reuse their metadata; conflicting repeats are rejected. Resume a partial source at its last non-null `next_cursor`. Preserve earlier pages and sources in the complete next draft. When refreshing a changed index, retain its old scan under the old source ID and add a new source ID. Equal titles never merge identities: candidate members name both `source_id` and `thread_id`.

`exhausted` means only that the explicitly selected active or archived index reached a null next cursor. It does not mean every local account, another device, cloud history or conversation body was inspected. Mark unavailable or unknown coverage explicitly. The limits are 20 sources, 50 pages per source, 100 metadata entries per page, 500 distinct source-qualified threads, 100 candidates, 100 members per candidate, 2048 characters per string and 512 KiB per complete draft. Thread metadata accepts only `thread_id`, `title` and optional `cwd`; content/messages fields are rejected. Reaching a limit requires a scoped continuation rather than claiming complete inventory.

Revisions live privately under `.taskcarry-onboarding/discovery/<discovery_id>/`, separate from `.taskcarry/state.sqlite3`. They are local discovery drafts, not another control or a published project memory. Execution checks the precise root, local root identity, existing project/replica binding, expected revision and previous content fingerprint, then uses a real OS lock and atomic no-replace publication. Symlinks, reparse points and conflicting files are preserved and rejected. Existing standby replicas cannot save revisions. Inspect status after an uncertain failure: retrying the exact plan reuses its actual saved revision; a newer revision requires a new plan. Keep these machine-specific drafts out of public repositories and release archives.

After the real `onboarding` exists, an optional `onboarding` object in the draft can link the selected scope to its current receipt:

```json
{
  "onboarding_id": "drone-setup",
  "scope_fingerprint": "the-actual-onboarding-scope-fingerprint",
  "selection_fingerprint": "the-discovery-selection-fingerprint",
  "windows": [{
    "source_id": "selected-host-active",
    "thread_id": "drone-software",
    "window_thread_id": "the-retained-original-thread-id",
    "source_ref": "the-actual-onboarding-window-source-reference"
  }]
}
```

Each selected source/thread must map exactly once to a distinct actual onboarding window and its actual `source_ref`. Additional newly proposed windows may appear in onboarding. The link checks the actual local scope and reports `binding_current`; it does not transfer acceptance or modify onboarding records. Changed selected candidates require a new user confirmation reference. Changed selection fingerprints or onboarding scope invalidate an old link. Copied drafts require a fresh local selection and binding review. All discovery reports keep `chat_bodies_read`, `all_chats_verified`, `acceptance_inherited` and `native_acceptance_verified` false. Configuration, native connection, completed governance and natural scheduled execution retain their separate evidence.

## Portable identity and sourced facts

New projects receive a persistent `project_id` and a local `replica_id`. `identify`, `status` and `context` expose source-qualified identity. A legacy project retains its path identity until an explicit `identity` plan and execute; its previous identity becomes an alias. Initialization is not an update workflow. A copied database is not an independently authorized writer.

`facts` supports `record/get/list/history`. Bind each fact to its source ID/revision and existing task. Keep the source statement/evidence separate from AI judgment. Kinds include decision, artifact, relationship, alias and status; standing can be current, historical, superseded or disputed. Changed content requires `expected_revision`; unchanged content reuses its record. Relations preserve predecessor and dependency identities. A source reference or AI judgment does not establish user approval.

## Bounded reading and complete cycles

`source_scan` supports `register/registry/start/page/status` for explicitly authorized local metadata roots. Bounded pages retain continuation; repeated cursors return their original page. Changed directory watermarks invalidate the scan, and exhausted budgets remain incomplete. It reads no file bodies and discovers no chats. Authorized host tools or the `codex` adapter supply selected chat content separately. Inventory is neither understanding nor deletion proof.

`cycle` supports `start/resume/status/list`, effect plans/results, source phases, health, actual question/report receipts and `finish`. Owner/task/resource scope is frozen. Request IDs bind evidence mutations to original inputs. Inspect uncertain effects before retrying. The existing `run` action remains the selected delivery/operation receipt aggregate.

| Evidence | Required distinction |
|---|---|
| Sources | Same ID/revision advances through observed, understood, published to a named target, and consumed there. |
| Effects | Plan the expected outcome, then retain confirmed/rejected/deferred/failed with actual evidence. Unfinished effects prevent completed closeout. |
| Health | Each dimension has status, evidence, observation time and freshness interval. Stale/future observations read as unknown. |
| Questions | Count actual delivered receipts on distinct local dates, default unanswered-date limit two. Retries cannot count one receipt twice. |
| Reports | Actual delivery is separate from scheduled or generated report text. |

Ordinary MCP/CLI calls retain durable ownership between calls and take OS locks while executing. Python `cycle_session` holds real resource OS locks for its live process session. Process exit releases OS locks; the same owner resumes the reservation. This does not lock arbitrary editors or fence another computer.

## Current workbench entries

`workbench` supports `freeze/plan/execute/status/consume`. Freeze text with exact local file/record revisions or labeled external references. Plan registered workspace/task targets, original chat IDs and code-dependency assessments. Execute the exact plan. The Codex adapter preserves other settings, comments and professional instructions while updating its managed section. Private entry paths must be ignored and untracked; tracked configuration remains a review conflict.

Several original chats may share one registered directory. First preview and install its connection materials with `binding_mode: "directory"`, `target` and `workspace`, omitting `task_id`; then create a workbench plan with `routing: "shared"`. Each target still carries its own original `task_id` and `thread_id`. One `.codex/taskcarry-routing.json` index selects separate current entries by exact chat identity. An unknown chat must request its binding rather than choose the first task. `status` accepts `thread_id`; querying the directory returns its individual chat entries. Publish and consume each chat independently, including when two chats share a task.

The default `binding_mode: "task"` and saved v1 plans retain their existing contract. Converting the same control/workspace to directory mode is explicit: setup preserves its old byte preimages, and the first shared publication includes the original chat and task. A new publication cannot silently reassign that identity. Old objects remain historical evidence, and old single-task plans cannot replace a shared directory's router. Restore retains history and disables the old host routing file until bindings are verified for the recovered machine.

Publication and consumption have separate receipts. A consumer supplies the matching view/plan/task/source/chat/turn and a hashed evidence file. This records reviewed evidence, not independent host access. Native tools still need actual calls in each chat. Complete setup requires matching tasks/chats, fresh source revisions, verified publication, no pending finalization and consumption. Code adoption follows a separate dependency. One workbench's conflict does not force others to restart.

In `complete_v1`, workbench evidence has one entry for every selected active `(workspace, task_id, thread_id)`. A workspace-level receipt cannot cover another chat. Legacy entries lacking task/chat fields are accepted only when that workspace has exactly one selected active chat and the live publication matches it; stored historical evidence is not rewritten. Reference-only source chats do not require a native workbench connection.

## Selected recovery sets and one writer

`recovery` supports `backup_plan/backup_execute/verify/status`, `restore_plan/restore_execute`, `history`, `activation_plan/activate`. Read-only history retains the original collection/key and restore identity across multiple recovery generations.

Select registered workspaces and exact material payloads. Backup seals one consistent SQLite snapshot and referenced objects, plus separately stable selected Git history/refs, index, working layers and chosen untracked/material files. The manifest lists coverage and missing dependencies. It does not claim a transaction across all live directories. Interrupted work reuses sealed components and the original state snapshot; changed unsealed inputs need a new plan.

Untracked names are observations, not implicit file selections. Lists longer than 1,000 names retain at most 1,000 examples plus their full count and SHA-256 digest (`untracked_count`, `untracked_sha256`, `untracked_listing_truncated`; corresponding `excluded_untracked_*` fields apply to excluded names). The digest covers the complete canonical JSON list, so a change beyond the examples still invalidates an unsealed source. Small lists keep their existing shape. Frozen legacy plans retain their original full lists and plan IDs; the reader accepts metadata up to a finite 64 MiB, allowing plans above the former 16 MiB limit to continue without rewriting. Larger metadata still fails explicitly. Selected payload file/byte budgets are unchanged.

Verify every referenced object using the manifest hash from a trusted receipt. A manifest cannot replace missing bytes. Install a compatible trusted Core package separately. Retain exact capability resources and necessary project rules as selected payloads. Native credentials, OS permissions, unsaved buffers and excluded files need separate arrangements. Encryption and cloud login remain explicit external operations, with keys stored separately.

Restore into an independent absent/empty destination. Real Git history/index and selected work are restored; current workspace paths are rebound. Old executable plans/cycles become inert history. Host connection entries retain their original bytes in a disabled location, with the exact working-file exception listed in the receipt. Regenerate current-machine bindings before use. Schedules are not activated.

Include the registered receiving baseline when one is bound. Recovery rebinds it only to a unique captured Git identity and retains the original binding and accepted-stage provenance in history. A missing baseline makes coverage incomplete and blocks new reception until a complete set is restored. New receiving and adoption plans belong to the restored replica; old inert plan IDs are never reused. Cumulative successors continue from their verified received predecessors after relocation.

The restored replica retains project lineage, receives a new replica ID and starts in standby. Explicit activation requires an exact reviewed restore, bound native host evidence and a declaration that the named old writer has stopped. The engine cannot independently fence that machine. Do not run an older writer that lacks standby enforcement. Package rollback uses a compatible retained runtime and current project records; restoring an old database over newer decisions is a different operation.

## Optional private transport

`transfer` supports `publish_plan/publish_execute`, `copy_plan/copy_execute`, `verify/status`. Git plans freeze an existing remote's single push URL, exact commit/ref, expected old remote value and local state. Only verified fast-forward branches or new tags qualify; an exact single-ref lease protects concurrent changes. No bulk refs, old-tag replacement, repository creation or credential setup is implied. Inspect the actual remote effect after transport failure before retrying; an already matching effect can finish its missing receipt.

Static copying publishes only the manifest and its listed objects into an independent local directory. A sync-folder copy proves local bytes. Provider upload, independent retrieval and restore have separate evidence. Independent workspaces on other computers contribute reviewed commits or artifacts to one governance writer; they do not synchronize two live governance databases.

## Versioned complete setup

New setup explicitly uses `profile: "complete_v1"`. Unversioned records remain `legacy_v1`; old acceptance is not relabeled as new coverage. A synthetic complete scope is available in [scenario.json](../examples/complete-governance/scenario.json). Replace sample IDs with actual host/task identities.

The schedule has `timezone` and two or three `slots`, each with `slot_id`, `purpose` and `time`. Exactly one purpose is `report`; the other one or two are `absorb`. `schedule_plan` prepares original-chat instructions without creating host schedules.

`onboarding status` returns required evidence and revision. Update one item with that revision, key, status, structured evidence and next step. Required items cover scope, runtime, local Git, release assessment, identity, understood selected sources, consumed workbenches, independent recovery rehearsal, the first bounded cycle, native schedules and each active window. The installed project-setup Skill provides the exact evidence-field table.

Read back every actual native schedule under `schedule_config`. Later record `schedule_trigger:<slot_id>` for natural trigger and original AI execution; report slots also need delivery evidence, and unchanged absorption may be quiet. `complete_governance_ready` describes verified configuration; `closed_loop_verified` additionally requires all natural slot receipts. Waiting for first real delivery is pending observation, not failure or another manual setup step.

Source coverage includes each selected revision observed within the referenced cycle. Understanding an older revision cannot hide a newly observed revision that still needs reading.

Synthetic tests establish mechanisms. CLI/standalone stdio success is not native-host acceptance. Receipt strings and booleans do not independently establish their truth. Actual chat tools, natural triggers, cloud retrieval and physical multi-computer behavior each need their own evidence level.

## Persistent state compatibility

Program, project-state and derived-index versions are independent. Supported project schema 1 accepts the original SQLite application_id=0 as well as the current product marker, after checking the records/events layouts, project configuration and supported index versions. A different nonzero marker is foreign. Identification uses the same format reader as project snapshots; snapshots additionally require SQLite integrity checking. Recognition does not write markers, migrate evidence or create journals. Unknown/incomplete/corrupt snapshots return RECOVERY_STATE_CORRUPT; a recognized unsupported state/index format returns SCHEMA_VERSION_UNSUPPORTED. Failed backup publication never implies historical records were lost.

Explicit upgrade rebuilds derived indexes without rewriting records or events. Project recovery retains source lineage, tasks, decisions, object identities and archived original bindings, while recording a new replica and relocated paths. Old executable plans are not automatically replayed on a different replica. Repeated backup/restore calls verify existing effects before completing missing receipts.

Local governance-method adoption, a selected Core runtime change and public product publication have separate evidence. A local improvement may use the current verified engine or a verified isolated maintenance candidate; a public fix may be developed directly or extracted from local practice. Neither side requires the other's publication/acceptance, while real compatibility and recovery dependencies still apply to affected operations. Retain current facts when evaluating rollback; connection-file restoration alone does not establish full data-format downgrade support.
