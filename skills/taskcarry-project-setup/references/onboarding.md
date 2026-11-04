# Conversational onboarding for an existing project

Use the four public Skills and the user's existing AI host, in the user's language. This is an assistant procedure, not a second database, model service or promise of background chat monitoring. Keep project-specific notes private to their project.

For an explicit update to an existing TaskCarry installation, use [the maintenance route](#6-update-an-existing-installation) below. First installation and ongoing business work are different questions: preserve the user's project in either route.

## 1. Establish the governance home

Identify the project and a separate governance chat. Reuse a verified TaskCarry governance chat/control if it already exists. The original main and professional chats keep their work. If the user explicitly chooses another existing project-control chat, record its role and check its actual TaskCarry capability.

Inspect existing installation and control records before creating anything. Identify runtime, target host directory, relevant Git roots/branches/HEAD/WIP and the trusted receiving baseline when Git delivery is needed. An empty control directory says nothing about prior business work. Keep independent projects separate; one control may bind several workbenches.

Save a small resumable checklist with actual result/source, pending condition and next action. Suggested rows: runtime, governance identity, project understanding, task/workspace mapping, integration files, host loading, native calls and first review. These are descriptive project notes; they do not replace task/stage/operation records. Check actual effects before retrying.

## 2. Understand and inherit the project

Start with the user's locator and current conversation. Read current instructions, named task/checkpoint/artifact records and relevant files. Use permitted host tools for specifically related old chats or missing changes. List the source/revision or time reviewed; partial history remains partial. When history cannot be read, ask for the smallest missing summary with a prepared prompt for that original chat. Do not request a complete project introduction already present in sources.

Produce a short handover record with:

- Goal, current stage, constraints and supporting sources.
- Existing deliverables and whether inclusion in the trusted baseline is known, pending or unverified.
- Confirmed decisions, their source, scope and effective version.
- Active/paused tasks, owners, outputs, dependencies and exact unfinished positions.
- Unknowns and model suggestions, separate from confirmed facts.

Use versioned project notes and artifact/checkpoint references to identify an understanding draft. Keep its source/version and user confirmation reference. A candidate correction does not overwrite effective understanding. When the user corrects a fact or decision, preserve the earlier version and identify affected tasks. Do not invent task revision/CAS fields or a general decision-promotion API; use actual installed command contracts.

Already included historical work needs provenance, not another queued delivery. Preserve task IDs and accepted-stage evidence. A paused task may stay paused; quiet history is not a new failure or overdue item.

## 3. Recommend the working arrangement

Default governance responsibility is governance and project memory: keep connected progress, evidence, effective decisions and continuation points coherent. Offer one project assessment during onboarding. Ask only about unresolved material choices; existing decisions already authorize their stated scope.

The user may choose temporary or ongoing project coordination. Record that preference without rebuilding state. Direct professional work remains available in either mode. Project suggestions, schedules and messages to other chats need applicable authorization; a recommendation alone is not a dispatch.

Inspect existing responsibilities first. Suggest a split only when independent outputs, parallel value, file ownership, dependencies and review cost justify it. A single existing work chat plus governance can be enough: zero added specialists is valid. If old chats share a directory, check active writers and preserve scoped WIP before arranging separate workspaces. Renaming chats does not isolate writes. Tasks and chats need not map one to one.

## 4. Complete installation and binding in conversation

If no dedicated runtime exists, read `docs/<language>/manual-setup.md#install` from the product directory supplied by the user. Follow its dedicated-environment and bundled-wheel steps using the exact selected package and checksum, within the authorized installation scope. A verified existing runtime is reused; do not silently upgrade it or replace it with a source checkout. The fallback guide supplies the assistant's installation procedure without requiring the user to perform every step manually.

Use the chosen fixed package and interpreter; preview managed updates before install. Reuse valid installations and identities. For a registered workbench use setup JSON `target`, `workspace` and `task_id` together, with `--project` still pointing to the original control. Target must match the registered workspace and actual Git identity; the task must exist in the same control. The assistant checks their intended relationship; setup does not impose a one-to-one task/workspace assignment. Keep the four Skills and their reference files together. Do not create stores inside each worktree or infer that Skills are inherited across directories.

Use only host capabilities available in this session and within authorization. Workspace registration does not create chats. Generating a fragment does not activate it. Trust/reload may require user action. If a capability is missing, provide:

1. The one current action and its exact target chat, directory or settings location.
2. Filled-in content based on verified paths and identities, without secrets.
3. What success looks like and a short message to return with so onboarding resumes.

Do not repeat installation when only host reload is missing. Record native doctor/status results in each window separately from CLI or standalone stdio tests. Confirm imported package and binding, not just a command string. Never claim native verification if those tools are unavailable.

## 5. Continue work and close the first review

Use task-delivery instructions in working chats: read the named task and relevant effective decisions before work; preserve meaningful changes at pause/delivery boundaries. Link sources and exact outputs, not full private transcripts. Governance reviews those records and requests only changed or missing relevant context. This is a method using existing records, not an automatic cross-chat change subscription.

Use governance-reconcile for one bounded initial review. Receive frozen Git stages only through their plan and authorization. Sharing progress does not merge every branch; adopt only for a real dependency and safe target. Plain file checkpoints preserve selected files; they do not implement the complete non-Git deliverable exchange/intake contract.

Return inherited understanding, effective decisions versus proposals, task ownership/next steps, actual connection results, the remaining onboarding action and how each workbench saves/continues. Tool readiness does not require business completion. Teach examples such as "continue my last unfinished task", "save this stopping point" and "show progress from connected workbenches".

Use experience-recovery after a concrete failure. Preserve operation identity and actual effects, completing only supported missing steps. Keep source fix, received fix, installed package and reloaded host separate. Automation, remote sharing and additional hosts are optional choices with their own evidence.

## 6. Update an existing installation

Stay in the original governance chat and use the same control, task identities and workbench registrations. Read the selected release's update information and `docs/<language>/updating.md`. Inspect the installed runtime, managed setup, activated project configuration and any operations affected by the update. A paused task or queued delivery alone does not block a tool update; do not receive or adopt business stages just to update TaskCarry.

Choose the smallest applicable change: documentation alone, managed Skills/integration materials, or a runtime package plus those materials. If the selected update is already in use and connections are current, report that no action is needed. The `upgrade` action only rebuilds the derived current-record index; it does not install a package.

For a package change, use authorized host tools to obtain the selected official wheel and verify its checksum. Prefer preparing a separate dedicated runtime and retaining the original environment until the switch has been verified. Do not use an editable source checkout. Run the candidate's fixed interpreter with isolated UTF-8 startup for read-only diagnosis and setup preview against the original control; compare actual proposed changes and user modifications. Keep the original package, managed-file manifest and active configuration together for recovery review. Package preparation is not a transaction covering later setup or host changes.

Before changing managed files or switching connections, coordinate a quiet interval for affected writers. Preserve schedules and unrelated host settings. If an existing setup intent is pending, inspect its actual effects and resume with its original candidate and runtime, or retain the conflict for review; changing runtime identity is not a way to continue that intent. Do not delete state or redo an entire governance pass. Save the update position before any host action that may interrupt the chat.

When the reviewed update is authorized and compatible, run candidate `setup` preview/install for the same control and affected registered workbenches. Preserve modified user files and report concrete conflicts. Setup manages its own files; use the host's authorized configuration tools to merge only the required project MCP settings, then restart/reload the affected connections. Do not replace global configuration or infer that all windows inherited a change.

Verify the candidate's isolated CLI and each relevant host's actual native doctor/status separately. Check that original tasks, checkpoints and workbench bindings remain available. If native tools or a host action are unavailable, give the user only the current necessary action, its exact destination and a resume instruction. If only reload is missing, do not reinstall. Preserve unfamiliar failures and inspect actual effects before retrying; rollback requires review of the matching runtime/configuration/managed-file set, not merely installing an old wheel.

Report a short outcome in the user's language: updated items or no update needed, whether original work is preserved, whether work can continue, and any single remaining user action. Save detailed versions, checksums, receipts and compatibility evidence in project records rather than repeating them throughout the user flow. This is assistant-led maintenance using existing tools, not a new automatic updater or delta-patch command.
