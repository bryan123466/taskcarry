---
name: taskcarry-task-delivery
description: Preserve task checkpoints or deliver stable project work through TaskCarry. Use when work pauses, reaches a meaningful stage, or needs continuation; ordinary editing remains independent.
---

# Task continuity and delivery / 接续与交付

Read `taskcarry_context` for the named task, then continue from its evidence and next step. Keep source-qualified identity when several state sources contain the same local task ID. Read related effective decisions and their source/version before changing affected work; follow pagination and missing-evidence markers. Older stores may need explicit `upgrade` of derived indexes; that does not install a package. Users can give work directly in this chat; ordinary work need not pass through governance first. Reuse the stable task identity; register a genuinely missing task with `taskcarry_task`. Keep workstreams separate; a paused or quiet task is not necessarily overdue.

At meaningful changes, save actual findings, selected outputs, decision sources and next conditions in existing task notes, checkpoints or artifact references. Distinguish current verified state from last known state. Keep suggestions and unconfirmed understanding drafts separate from effective decisions. A correction retains its source and identifies affected tasks. Use supported fields; do not invent task revision APIs. For another chat, provide the smallest relevant saved references or a filled-in handoff if the host cannot read them.

Use `taskcarry_checkpoint` at a meaningful pause or milestone. Select exact task-owned relative paths and record the next step and relevant decision. Checkpoints preserve saved work and selected Git layers; they do not capture unsaved editor buffers or declare delivery. Ordinary file checkpoints do not need Git. Avoid secret, unrelated and generated dependency files. Start `taskcarry_restore` into an empty independent destination. After interruption, inspect the original operation and target effects before the supported retry; never clear a nonempty target or overwrite later user changes just to retry.

For an authorized stable delivery, make a precise local Git commit, determine its base, and use `taskcarry_submit` with the exact changed path set. Supply cumulative lineage only when the newer commit covers the older delivered work from the same task; a later timestamp alone is insufficient. The delivery points to frozen commit content, so subsequent workspace edits remain independent.

Use the assigned real work directory and Git relationship verified during onboarding. A task ID or chat name does not isolate concurrent writes. `preserve` can plan and save exact selected files locally while retaining unrelated index/worktree state; its commit is not automatically a submitted stage or a remote backup. Selected paths with pre-existing staged intent require specific review instead of silently folding it into a save. Ordinary source directories and large external files remain valid references, with content coverage explicitly stated.

Large reference artifacts can use `taskcarry_artifact` with content identity and an optional backup path. A recorded location is not proof of an available, matching backup. Ordinary document saving does not create a Git stage or implement general non-Git delivery/intake. Record ignore/dismiss decisions only when the user made them. Sharing progress does not authorize merging every workspace or messaging other chats.

中文：保存、提交、交付、接收和业务验收分别报告。普通工作不等待治理事务。暂停保留接续点；后续迭代只有证据充分才声明覆盖旧交付，不把历史安静状态重复当积压。
