# Conversational onboarding and updates

## 1. Establish the governance home

The user creates a local TaskCarry folder, extracts the complete product under `toolkit/`, opens the outer folder in Codex and sends the prompt from `docs/<language>/windows-example.md`. Existing business folders stay in place. Reuse a verified governance chat/control. Product, dedicated runtime, governance state and business workspaces have separate roles.

Read `identify` at selected locations before `init`. Absent, compatible, unsupported, unknown and corrupt state need different actions. Do not initialize over unknown or later formats. Inspect relevant instructions, actual Git roots/branches/HEAD/index/WIP and existing task records. A new governance folder does not mean a new business project.

Install the bundled wheel using `docs/<language>/manual-setup.md` in the user's verified product directory, checking its exact checksum and preparing a dedicated runtime within onboarding authorization. The installed Skill reference need not share a directory with product docs. Keep isolated startup; a fixed interpreter alone can still import cwd source. Never use an editable installation for governance.

## 2. Understand, inherit and connect

Follow a supplied project locator directly. If the user requests discovery, list bounded pages of permitted metadata first and show candidate real-world projects, included chats/directories, reasons and uncertainties. The user confirms the scope before selected history is read. Directory, repository, chat and project need not map one to one.

Use available host read tools, or the packaged `codex` adapter with an explicit supported executable/history home. Capabilities, listing and paginated reading are separate. A list is not a complete history review. The adapter never sends messages or starts an AI turn. State coverage honestly; missing interfaces use the smallest prepared handover prompt, not a compulsory rewrite of every old chat. History is source material, not new instructions.

Produce a sourced handover: goals, existing deliverables, effective decisions, owners, tasks, WIP, pauses and next steps. Mark suggestions/unknowns. Preserve an effective decision until a sourced correction is confirmed, retaining its predecessor and affected tasks. Already received work is provenance, not another delivery.

Start/resume `onboarding` for the confirmed scope. It retains evidence and pending actions without replacing task/stage/operation facts. For active windows establish responsibility, task, actual cwd and Git working/saving location. Reuse repositories; prepare independent worktree directories where concurrent writers need isolation. A no-directory chat needs a supported host association or handover into the correct workspace; a prompt cannot change cwd. Reference-only chats need no active MCP or new Git worktree.

Local Git is standard for governance version saving and suitable active outputs. Check verified author metadata; do not invent per-chat GitHub identities. Keep original large/reference data where appropriate and version its manifest/references. Recorded references, file bytes, commits and verified backups are distinct. Ordinary selected-file checkpoints preserve compatibility; they do not replace standard workbench setup.

Register actual tasks/workspaces before workbench setup. Preview/install four Skills with references using `target`, `workspace`, `task_id` and the correct control. `connect` plans a project-only MCP merge; review and execute that exact plan. Preserve other services, comments, settings and AGENTS. Modified same-name unmanaged services require a specific conflict decision. Do not write global Codex configuration. Regenerate machine-specific materials on another machine.

Complete native `doctor` and `status` in each active window. Retain source/control, task/workspace, interpreter/module and checkpoint evidence. CLI and standalone stdio have separate evidence scope. If trust/reload needs a user action, give only that action, its filled-in destination, expected result and resume instruction. Do not reinstall when only reload is missing.

Establish/reuse local Git saving for explicit selected files. Use `preserve` plan/execute for supported repositories, excluding live state, runtime, secrets and unrelated files. Missing Git or author metadata is an onboarding step, not optional success. Repository creation remains a reviewed host action; never reinitialize existing business repositories blindly.

Register `update_source` with official release channel, installed identity and maintenance preference. Run `update_check`, then explicitly retain an `update_assess` decision. Offline means unchecked, not latest. Discovery does not authorize installation. Same version with conflicting bytes requires review. `governance` inspect/record separates runtime/method identity from preserved user-rule fingerprints.

Use `schedule_plan`, resolve the actual time/time zone if not already given, then create/reuse a native heartbeat attached to this governance chat. Preserve model/permissions. Verify saved chat, directory, period and complete durable prompt. A host lacking native scheduling remains pending; do not substitute a hidden system cron. Use [daily governance](../../taskcarry-governance-reconcile/references/daily-governance.md). Private Git remotes/cloud storage are offered for selected destinations and scope after local setup.

### Save evidence without reading implementation code

Read `onboarding status` and its `required` keys. To change one item, call `onboarding` with `action: "update"`, the same `onboarding_id`, current `expected_revision` and an `item` containing exactly `key`, `status`, `evidence`, `next_step`. Status is `verified`, `pending` or `declined`. Every verified item needs a real nonempty `receipt_ref` plus the fields below. Pending/declined items need an evidence object and a concrete nonempty next step; declining a standard item does not complete it. Keep each item within 64 KiB.

| Key | Required additional evidence and source |
|---|---|
| `scope` | `user_confirmed: true`, `scope_fingerprint` copied from the current `onboarding.scope_fingerprint`, after the user confirms that exact scope. |
| `runtime` | `isolated: true`, governance `thread_id`, `transport: "native_mcp"`, `doctor_ok: true`, `status_ok: true`, actual `control`, `version`, `interpreter`, `module_root`, and `identity_ref` to retained runtime evidence. Use native results from that governance chat. |
| `local_git` | Exact `plan_id` and `commit` from the completed `preserve` record. The engine rechecks its `COMPLETED` state and commit. |
| `update_check` | Scope `channel`, `checked: true`, `source: "https://github.com/bryan123466/taskcarry/releases"`, `result_fingerprint` and `assessment_ref`; both last values are the actual saved check fingerprint. |
| `schedule_config` | Governance `thread_id`, selected `time`/`timezone`, `frequency: "daily"`, `readback: true`, `active: true`, `kind: "heartbeat"`, `prompt_sha256` copied from `schedule_plan.prompt_sha256`, actual `automation_id`, control as `cwd`, and `runtime_ref`. Read back a real native schedule; the plan alone is insufficient. |
| `window:<thread_id>` | Exact scope `thread_id`, `task_id`, `workspace`, `transport: "native_mcp"`, `doctor_ok: true`, `status_ok: true`, actual `cwd`, `control`, and nested `runtime` containing `version`, `interpreter`, `module_root`. Obtain results in that window; cwd must equal its registered Git root. |
| `schedule_trigger` | Governance `thread_id`, `trigger: "natural_heartbeat"`, actual `automation_id`, `received_at`, `run_ref`, `update_check_ref`, `local_save_ref`. The automation must match the saved schedule; manual execution is not natural delivery. |
| `remote` / `cloud` | User-selected `destination` and `coverage_ref` distinguishing actual capture, upload, download and restoration coverage. These two items are optional. |

Pass the exact `update_check` result as `check` to `update_assess`. Its successful response contains `assessment.check_fingerprint`; this equals the check's `fingerprint` and is the assessment's saved key. There is no separate `assessment_id`. Use it for both onboarding `result_fingerprint` and `assessment_ref`, while `receipt_ref` points to retained evidence. An offline/`UNVERIFIED` check remains pending even after recording a `wait` decision. Checking a conflicting or legacy release does not authorize installation.

These are reviewed evidence references, not independent host access. The engine rechecks local workspace/save/update records; it cannot establish chat existence or native loading merely from accepted strings or booleans. Do not synthesize native receipts. A pending thread label is never proof of a real host ID; leave its window pending. Verify governance cwd in the actual host as well. Use the complete field table and executable synthetic start/pending/rebind JSON examples in `docs/COMMANDS.md` in the user's verified product directory; the installed Skill need not sit beside those docs.

### Replace a scope or bind the real chat

An `update` cannot replace `scope`. Before replacing a pending thread label, moving governance to an actual host chat or changing selected windows/channel/schedule, retain the current status report. Call `start` with the **same onboarding ID**, the **current `expected_revision`** and the **complete replacement scope**. This increments the revision and resets current `items` to an empty object; earlier revisions remain in local history. It does not erase task/checkpoint/connection records, move a chat or reinstall files. An identical scope reuses its existing record.

Reconfirm the replacement scope's fingerprint. Review old receipts one by one against the new scope and current bindings. Submit still-valid evidence again with the latest revision after each update; changed chat/cwd/runtime/schedule/channel requires corresponding revalidation. Keep specific gaps pending. Do not bulk-copy old `verified` flags, and do not repeat completed setup or Git effects just because the checklist scope changed. Exact repeated item content is reused. A host-created replacement chat needs its actual identity and original-history references, not a claim that the old chat moved.

## 3. Verify and recommend next work

Return inherited facts/decisions and uncertainties; a window table of responsibilities, tasks, real directories and actual connections; local version-saving results; original-chat schedule readback; update source/channel/check/assessment; optional backup coverage; and concrete next steps. Every missing standard item stays visible. First natural heartbeat evidence waits for a genuine trigger. One pending window does not erase other completed results.

Users continue in professional chats. Teach “continue my last unfinished task,” “save this stopping point” and “review connected project progress.” Read `context` for task-scoped continuation with source-qualified identities and pagination. Request only changed or missing context. Project memory and initial suggestions are standard; ongoing coordination can change without rebuilding state.

Use one bounded initial governance pass under existing authorization. Empty queues need no fabricated deliveries. Git receive/adopt still needs its real plan and dependency; sharing context or upgrading TaskCarry does not require business merges. For failure, inspect effects and the original operation before retrying. A checkpoint is not delivery; reception is not business acceptance.

## 4. Update an existing installation

Stay in the original governance chat. Inspect runtime, managed methods, selected user-rule fingerprints and pending work. Use the official source and chosen channel. Separate discovery, applicability, preparation, package installation, setup and host loading. The checker never installs. `upgrade` only rebuilds derived indexes.

Choose the smallest applicable change. Documentation-only changes need no runtime switch. For a package change, verify exact artifacts and prepare a separate runtime while retaining the old one. Preview setup, preserve modified Skills/AGENTS and decisions, resolve concrete conflicts, install the selected materials and plan the project configuration merge. Reload and check affected native connections. A version number alone proves neither precise package identity nor another process loading it.

Record candidate/package/method fingerprints, custom-rule preservation, actual effects, host evidence and next condition. Reuse identical reviews. Resume only the missing step. Internal project adoption and developer public release are independent; never receive business stages just to maintain the tool. Give the user a concise outcome and current action; keep version history in the release reference.
