# Private remotes, recovery backups and multiple computers

Start with the [guided local setup](windows-example.md). Use this reference when you choose a private remote, storage service or an additional computer; detailed installation commands remain in the [manual fallback](manual-setup.md).

[Operation manual](operation-manual.md) · [简体中文](../zh-CN/remote-and-multicomputer.md) · [繁體中文](../zh-TW/remote-and-multicomputer.md) · [Command reference](../COMMANDS.md)

Local governance Git saving, the original-chat schedule and official release checks belong to standard onboarding. The private remote and multi-computer procedures below are optional extensions. The cross-computer procedure has not been validated end to end on two physical computers. It combines Git operations with the existing local TaskCarry interface; it does not add automatic cross-host synchronization or recovery.

Standard local saving uses an explicit file list, preserves the existing Git index and unfinished work, and records a commit only when selected content changes. It excludes the active `.taskcarry` database, runtime, downloaded packages and credentials. Working windows keep their real task/workspace bindings; a Git author name or a chat identifier alone does not establish these relationships. Original materials can stay in place, while large external outputs have versioned references and separately verified storage coverage.

When you choose cloud storage, synchronize sealed static backup packages. Verify capture, local bytes, upload, download and isolated restore as separate steps. Writing into a local sync folder does not prove cloud upload or recovery on another machine. Do not place live `.taskcarry` or Git metadata under competing background synchronization. Keep any encryption key separate from its encrypted backup.

Replace every `<...>` placeholder. Use the Python environment in which TaskCarry is installed. Save request files as UTF-8 JSON. Git pushes transmit data to the selected remote, so establish the destination, its readers and the authorized scope before uploading.

<a id="private-git"></a>

## 4. A private Git record repository and recovery backups

### 4.1 Know what each store contains

[Ready-to-paste Windows example for this step](manual-setup.md)

| Content | Recommended location | What it can recover |
|---|---|---|
| Selected code, documents and stable outputs | A private Git repository, committed and pushed | Uploaded file versions and commit history |
| Curated project memory: goals, decisions, current position, next steps and sources | Ordinary Markdown/JSON files in private Git | A readable project handoff across computers |
| TaskCarry tasks, stages, operations and experience records | `.taskcarry/state.sqlite3` in the local control directory | Local tool state and historical records |
| Checkpoint file objects | `.taskcarry/objects/` in that same control directory | Explicitly captured files and their checkpoint layers |
| Unsaved editor buffers and files outside checkpoints | Their original application/workspace; save or back them up separately | Git and TaskCarry do not capture these automatically |
| Videos, installers, large data and similar artifacts | Authorized file storage; record location, size and hash in Git | A way to locate and verify bytes, not proof of upload or access |

**Private Git is not an automatic mirror of a computer or the governance database.** Selected files reach it only after commit and push. Ignored files, unfinished uncommitted work and local chat history are not included automatically. GitHub blocks ordinary Git files larger than 100 MiB; use separately chosen storage or explicitly configure Git LFS for suitable large files. TaskCarry configures neither automatically. [GitHub file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

### 4.2 Establish the private remote and one main writer

[Ready-to-paste Windows example for this step](manual-setup.md)

1. Create a **private** repository with your Git hosting provider and review its members. For an existing project, avoid creating an unrelated remote README or initial commit.
2. Designate one computer as the integration host. Its dedicated clean receiving workspace is the only place advancing remote `main`; other computers publish task branches.
3. Inspect the receiving workspace, remote, branch and commits:

```text
git -C "<A_BASELINE>" status --short
git -C "<A_BASELINE>" branch --show-current
git -C "<A_BASELINE>" remote -v
git -C "<A_BASELINE>" log -5 --oneline
```

Only if this workspace has no `origin`, add it:

```text
git -C "<A_BASELINE>" remote add origin "<PRIVATE_REPOSITORY_URL>"
```

If `origin` exists, inspect it rather than replacing it automatically. The receiving workspace's local branch need not be named `main`. Once the accepted content is authorized for upload, push that exact baseline:

```text
git -C "<A_BASELINE>" push -u origin HEAD:refs/heads/main
git -C "<A_BASELINE>" rev-parse HEAD
git -C "<A_BASELINE>" ls-remote origin refs/heads/main
```

The last two hashes should match. Investigate rejection instead of forcing a push. If remote history differs or another writer advanced it, reconcile the evidence and responsibility first. **This is a native Git push, not TaskCarry `reconcile` or a built-in remote receipt.** Use the provider's branch protection/access controls where appropriate to enforce the main writer; a prompt alone cannot provide a cross-host lock.

### 4.3 Keep useful memory in ordinary project files

[Ready-to-paste Windows example for this step](manual-setup.md)

Use a registered documentation workspace to maintain, for example, `project-memory/current.md` with:

- Task identity, goal, current stage and active/paused/waiting state.
- Accepted stages and verifiable commits/files; technical reception and business acceptance stated separately.
- Current decisions, scope and sources; references from outdated decisions to their successors.
- Unfinished work, checkpoint IDs, next steps and user decisions only when actually needed.
- Locations and hashes of large artifacts, with the actual backup verification status; no credentials.

This is a curated project handoff, not model weights, all private chats or a restorable database. A `status` export is also useful, but can contain absolute host paths and internal task information. Review its audience and content. Keep the raw export with the backup; a Git copy may retain only necessary fields.

PowerShell 7 export example, with the destination parent already present:

```powershell
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status | Set-Content -LiteralPath "<SNAPSHOT>/status.json" -Encoding utf8
```

Check that the JSON has `ok: true` and record the capture time. Do not treat an error envelope as a valid state report. Curated memory files use normal delivery and reception; do not dirty the dedicated receiving workspace just to add a summary. An exact commit example:

```text
git -C "<MEMORY_WORKSPACE>" diff -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" add -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" commit -m "Update current project handoff"
```

Inspect the index both before staging and before committing. If unrelated changes are staged, stop this commit step and preserve them rather than making a mixed commit. Then declare the stage as described in the main manual, receive it on the integration host and push it. A memory file in Git does not import itself into another computer's TaskCarry database or model memory.

Prompt for Codex:

> Maintain a concise project-memory/current.md for this project. Use authorized task records, commits and explicit sources to describe current facts, effective decisions, paused positions and next steps. Preserve necessary lineage without turning unchanged tasks into new backlog. Inspect existing files and the index, and deliver only actual changes. Do not export private chats, credentials or the whole .taskcarry directory. Use local TaskCarry reception; push only content already authorized for the specified private remote.

### 4.4 Create a verifiable, consistent backup

[Ready-to-paste Windows example for this step](manual-setup.md)

**Pause writes for this project before capturing one consistent point.** TaskCarry does not currently provide a single coordinated backup command for Git, SQLite and file objects. Follow this order:

1. Save task files. Capture precise checkpoints for meaningful unfinished work, including `next_step`. A checkpoint is not a delivery and does not require declaring unfinished work as a completed output. Current checkpoints allow at most 500 selected paths, 32 MiB per file object and 128 MiB across captured layers; back up omitted or larger material separately.
2. Let current TaskCarry operations finish. Pause this project's scheduled mutations and governance calls; no CLI, MCP or other program may modify its `.taskcarry` during the copy. Pause edits to Git workspaces being captured as well. Retain the actual state of unfinished operations; do not manufacture completion or delete lock files for backup.
3. Create a fresh backup directory **outside the source repositories, workspaces and control directory**. Record toolkit version, workspace paths/branches/HEADs, checkpoint IDs, `status`, capture time and the scope paused.
4. Save reachable commits and references for every independent Git repository with a bundle. Worktrees sharing one Git common directory can have their references covered by the same bundle.

```text
git -C "<REPOSITORY>" bundle create "<SNAPSHOT>/project.bundle" --all
git -C "<REPOSITORY>" bundle verify "<SNAPSHOT>/project.bundle"
git -C "<REPOSITORY>" bundle list-heads "<SNAPSHOT>/project.bundle"
```

A bundle can transport commits offline. It is not a complete backup of working files, index, untracked files, configuration or all local recovery information. Capture those separately or in checkpoints. [Official Git bundle documentation](https://git-scm.com/docs/git-bundle)

5. While all relevant writes remain stopped, copy the complete `.taskcarry` directory: `state.sqlite3`, accompanying WAL/SHM files if present, `objects` and other state files. Do not copy only the database's main file or move the originals. Save specifically needed files outside checkpoint coverage, plus reviewed project configuration; exclude login tokens.

PowerShell 7 cold-copy example, where `<SNAPSHOT>` is a newly created empty directory:

```powershell
Copy-Item -LiteralPath "<A_CONTROL>/.taskcarry" -Destination "<SNAPSHOT>/.taskcarry" -Recurse -ErrorAction Stop
Get-ChildItem -LiteralPath "<SNAPSHOT>/.taskcarry" -Force
```

On other systems, use a local file-copy tool under the same stopped-writer condition, preserving hidden files and directory structure. Do not synchronize a **running** `.taskcarry` or `.git` directory through a background file-sync service. SQLite's online backup API can snapshot a database; that alone does not coordinate the TaskCarry file objects and Git state with it. [SQLite backup documentation](https://www.sqlite.org/backup.html)

6. Compare file inventories, sizes and SHA-256 hashes; check the database copy and representative checkpoint readability. At minimum verify the bundle, object directory and absence of copy errors before resuming the project. Archive the completed snapshot to your chosen storage and verify hashes on a downloaded copy before calling it a verified offsite backup. A directory name or sync icon is insufficient evidence.

> Back up this project to [new backup directory] during a coordinated pause. First save selected WIP checkpoints and wait for current governance actions to finish. Pause relevant writers. Capture a Git bundle per independent repository, complete .taskcarry, specifically needed files outside checkpoint coverage, and version/path inventories. Validate copies only; do not delete originals or recovery stashes. Record exclusions. When the backup is verified, restore the project settings paused for this operation without changing other projects.

### 4.5 Separate recovery of material from re-enabling governance

[Ready-to-paste Windows example for this step](manual-setup.md)

**Do not copy an old `.taskcarry` to a new computer and execute its old reception/adoption plans.** Workspace identity includes absolute path, Git common directory and branch. The integration baseline also binds that identity. There is no full cross-host state-migration API. Matching directory names do not prove the same execution state.

Recovery procedure:

1. Keep the backup original unchanged and work from a copy in a new location. Confirm the old host cannot concurrently advance main. If that is uncertain, recover material and independent task branches first, without activating another main writer.
2. Clone into a **new, nonexistent directory** from the private remote:

```text
git clone "<PRIVATE_REPOSITORY_URL>" "<NEW_REPOSITORY>"
```

Or recover a named branch offline:

```text
git clone --branch "<SAVED_BRANCH>" "<SNAPSHOT>/project.bundle" "<NEW_REPOSITORY>"
```

A bundle clone has the bundle as `origin`. Before uploading later, explicitly configure the intended private remote; do not assume it is already connected online.

3. To retrieve checkpoint files, **copy** the backed-up `.taskcarry` into `<RECOVERY_CONTROL>/.taskcarry` as a separate recovery working copy. Use a compatible TaskCarry version to inspect `status` and identify the checkpoint. Create `restore.json`:

```json
{"checkpoint_id":"<SAVED_CHECKPOINT_ID>","destination":"<NEW_INDEPENDENT_RESTORED_FILES_DIRECTORY>"}
```

```text
python -I -X utf8 -m taskcarry --project "<RECOVERY_CONTROL>" status
python -I -X utf8 -m taskcarry --project "<RECOVERY_CONTROL>" restore --input restore.json
```

The destination must be absent or empty, separate from the source workspace and recovery control directory. `restore` recovers only selected checkpoint files. A Git checkpoint creates a **synthetic restoration baseline** to represent HEAD/index/worktree layers and preserves the original HEAD as provenance; it does not restore the complete original repository history. It records a restoration event in the recovery working copy, leaving the backup original unchanged. Compare recovered files with the real cloned project before resuming on a named task branch. Never label the synthetic commit as the original commit.

4. Create a fresh `<NEW_CONTROL>` for ongoing work. Initialize it and register the new receiving/workspace paths. Re-establish current task positions from the old `status`, artifact hashes and actual local/remote commits. Retain old receipts as provenance and reconcile incomplete operations individually; do not repeat effects that already occurred.
5. Regenerate local Skills/MCP configuration and call `doctor`/`status`. Old MCP fragments contain the original Python executable and project paths. Do not reuse them unchanged. Workspace re-registration also cannot bypass pending stages, operations or the bound integration-baseline identity.

```text
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" init
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" workspace --input new-baseline.json
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" doctor
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" status
```

Example `new-baseline.json`: `{"name":"baseline","path":"<NEW_BASELINE_ABSOLUTE_PATH>"}`. Follow the [operation manual](operation-manual.md) for other registrations and connection. Record the mapping from old IDs to new registrations. This is an explicit human/agent-assisted reconstruction, not automatic continuation of all transactions in the old database.

<a id="multi-computer"></a>

## 5. Collaborate across computers using task branches

### 5.1 Recommended topology and responsibilities

[Ready-to-paste Windows example for this step](manual-setup.md)

```text
Computer B: independent clone → task branch → stable commit + handoff manifest
                                     │ push task branch
                                     ▼
                                private Git remote
                                     │ fetch original commits
                                     ▼
Computer A: consistently named local intake clone/workspace
            → A's TaskCarry submit → reception plan → sole receiving baseline
            → authorized push to main → B fetches for its next task position
```

One TaskCarry control directory uses **local SQLite on one host**. B may use a separate local TaskCarry control directory for checkpoints; its database does not automatically merge with A's. Never share `.taskcarry`, `.git` or an active worktree through bidirectional file sync.

A business area may contain multiple task branches. Define deliverables, writable paths, starting baseline and interface dependencies. Different task names still conflict if they change the same files. Every parallel writer needs its own file workspace and branch; opening two chats does not isolate a shared worktree. [Codex worktree documentation](https://learn.chatgpt.com/docs/environments/git-worktrees)

Each computer may use its own legitimately authorized Codex account and Git credentials. **An account login is not a task lock and does not log another computer out.** Do not share session files, tokens or passwords. Configure Git access and main-writer restrictions separately. This starting arrangement does not require a custom login server and provides no automatic failover during network partitions.

### 5.2 Computer B: start a task from the published baseline

[Ready-to-paste Windows example for this step](manual-setup.md)

Confirm A has pushed the baseline B should use. For this example, task `form-export` is scoped to `forms/export.py` and `docs/export.md`; replace the names and paths with the actual agreement.

```text
git clone "<PRIVATE_REPOSITORY_URL>" "<B_REPOSITORY>"
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" switch -c codex/form-export origin/main
git -C "<B_REPOSITORY>" rev-parse HEAD
```

Save the last output as `<SOURCE_BASE>` before work starts. Reuse an existing suitable clone/workspace when available; do not duplicate it, switch a workspace containing WIP or take over an existing branch.

> In [task workspace] on this computer, advance task form-export from [SOURCE_BASE]. Modify only forms/export.py and docs/export.md. Raise specific unresolved business decisions. Save meaningful checkpoints and next steps, then commit precisely at a stable stage. Do not change main, another worker's workspace or governance database. Unfinished work is not business acceptance. Deliver the original base, source commit, exact changed paths, checks actually performed, remaining work and artifact locations.

At a stable point:

```text
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" add -- forms/export.py docs/export.md
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Add task form-export stage one"
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" diff --no-renames --name-only "<SOURCE_BASE>" HEAD
```

Confirm the index contains only the intended paths before committing. Record this output commit as `<SOURCE_COMMIT>`. The final command's result must exactly match the declared delivery paths, including the actual paths involved in deletions or renames.

### 5.3 Computer B: record a handoff and push its task branch

[Ready-to-paste Windows example for this step](manual-setup.md)

Create `handoffs/form-export-v1.json` **after** the output commit, avoiding a file trying to contain its own commit hash:

```json
{
  "task_id": "form-export",
  "stage_label": "form-export-v1",
  "source_branch": "codex/form-export",
  "source_base": "<SOURCE_BASE>",
  "source_commit": "<SOURCE_COMMIT>",
  "paths": ["forms/export.py", "docs/export.md"],
  "checks": ["<actual checks and outcomes>"],
  "task_state": "paused",
  "next_step": "<remaining work or the next decision>",
  "artifacts": [],
  "relation_note": "<independent change, or evidence about earlier stages>"
}
```

This is a **human/agent-readable handoff, not an TaskCarry import API**. Do not pass it directly to `submit`.

```text
git -C "<B_REPOSITORY>" add -- handoffs/form-export-v1.json
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Record form-export stage one handoff"
git -C "<B_REPOSITORY>" push -u origin HEAD:refs/heads/codex/form-export
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" ls-remote origin refs/heads/codex/form-export
```

Check the index and the remote hash. The branch HEAD now contains the handoff and usually **differs from** the delivered `<SOURCE_COMMIT>`; retain both identities. B's checkpoint objects and uncommitted files did not travel with this push.

### 5.4 Computer A: verify original evidence, then receive locally

[Ready-to-paste Windows example for this step](manual-setup.md)

Use a consistently named intake clone/workspace for this task, for example registration `intake-form-export`. If it already exists, inspect its identity binding and unfinished operations rather than recreating it or rewriting its history.

First-time setup example:

```text
git clone --branch codex/form-export "<PRIVATE_REPOSITORY_URL>" "<A_INTAKE>"
git -C "<A_INTAKE>" show HEAD:handoffs/form-export-v1.json
git -C "<A_INTAKE>" cat-file -e "<SOURCE_BASE>^{commit}"
git -C "<A_INTAKE>" cat-file -e "<SOURCE_COMMIT>^{commit}"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_COMMIT>" HEAD
git -C "<A_INTAKE>" diff --no-renames --name-status "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" diff "<SOURCE_BASE>" "<SOURCE_COMMIT>" -- forms/export.py docs/export.md
git -C "<A_INTAKE>" switch -c codex/intake-form-export "<SOURCE_COMMIT>"
```

An ancestry check succeeds with exit code 0. Resolve content, manifest, authorization or check discrepancies before installation. Do not cherry-pick, rebase or recreate a source commit and then label the resulting hash as the original stage. Register the local workspace, task and stage using three files:

`intake-workspace.json`:

```json
{"name":"intake-form-export","path":"<A_INTAKE_ABSOLUTE_PATH>"}
```

`intake-task.json`:

```json
{"task_id":"form-export","title":"Form export","workstream":"forms"}
```

`intake-submit.json`:

```json
{"task_id":"form-export","workspace":"intake-form-export","stage_id":"form-export-v1","base":"<SOURCE_BASE>","commit":"<SOURCE_COMMIT>","paths":["forms/export.py","docs/export.md"],"relation":"independent"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" workspace --input intake-workspace.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" task --input intake-task.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" submit --input intake-submit.json
```

If a task ID already exists, confirm it is the same task instead of overwriting another task's meaning. `independent` here applies only to the example's new stage. A cumulative replacement must satisfy **the same task, the same registered workspace, original commit ancestry and path coverage**, with explicit `supersedes`. Matching names on two computers do not establish lineage. Retain evidence and resolve the relationship when those conditions are absent; do not invent coverage.

Create `receive-plan.json`:

```json
{"baseline":"baseline"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-plan.json
```

Review all returned `stage_ids`, baseline HEAD, unfinished operations and conflicts. A reception plan can include other already queued stages; it does not automatically select only this task. Execute only if the whole plan is within the authorized scope. Copy its returned `plan_id` into `receive-execute.json`:

```json
{"baseline":"baseline","execute":true,"plan_id":"<RETURNED_PLAN_ID>"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-execute.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status
```

Confirm the stage is actually `COMMITTED`, its operations are complete and baseline content is correct. A successful call does not mean every queued item completed. Resolve specific conflicts without overwriting other WIP. Use planned `adopt` from the main manual when an A workspace needs the update. Publish the authorized baseline to `main` as in 4.2; preserve traceability between A's integration commit and B's source commit.

> Receive computer B's form-export-v1. Read its remote handoff and original commits. Verify original base/commit, exact paths, actual checks, current baseline and task relationship. Use the consistently registered local intake workspace and TaskCarry submit, then planned reconcile. Do not claim a cross-host database import, rewrite source hashes or repeat completed effects. Check whether other stages in the plan are authorized too. Preserve B's unfinished-task notes and separate business acceptance. Push main only within existing authorization.

### 5.5 Continuing on B, transferring the main role and known limits

[Ready-to-paste Windows example for this step](manual-setup.md)

After A confirms reception and push, B reads the current handoff. Preserve WIP in its old task workspace rather than resetting it to `main`. Start a clean next task branch from the published baseline when appropriate:

```text
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" worktree add -b codex/form-export-next "<B_NEXT_WORKSPACE>" origin/main
```

Continue with the appropriate task relationship and record the new base. Do not redo completed stages. A does not automatically call TaskCarry `adopt` over the network on another computer.

| Situation | Action |
|---|---|
| Two computers work on nonoverlapping tasks | Separate branches/workspaces; A receives and advances the baseline serially |
| One task is split into two lines of work | Define interfaces, paths and integration order; a shared task name does not resolve conflicts |
| A is temporarily offline | B can continue authorized task branches and checkpoints; main reception waits for A or an explicit handover |
| A cannot recover and B must take over main | Stop or exclude the old main writer, recover material and create new governance as in 4.5, reconcile evidence, then designate B as sole integration host |
| A comes back online | First read current remote state and handover records as an ordinary collaborator; do not resume its old scheduled writes; transfer any unpushed work through task branches |
| Push rejection, missing source commit, manifest mismatch or content conflict | Preserve work and original evidence; resolve the specific discrepancy without force-pushing, inventing hashes or blindly replaying old operations |

If the old writer cannot be confirmed stopped, dual-main writing is not solved. Enforce the transition through actual Git permissions, branch protection or disconnection of the old writer. The RC provides no distributed lease, leader election, cross-host transaction migration, remote-side-effect recovery, operating-system repair or Codex-account migration. This procedure supports task-material handoffs; it does not promise automatic recovery of complete chats, unsaved work or the whole native environment.
