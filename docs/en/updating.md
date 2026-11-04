# Update an existing TaskCarry installation

[First installation](windows-example.md) · [简体中文](../zh-CN/updating.md) · [繁體中文](../zh-TW/updating.md)

Return to this project's existing governance chat and send the prompt below. Governance checks the current installation, identifies what needs updating and guides the remaining steps. Keep using your project and working chats.

## Send this to your governance chat

> Please help update TaskCarry for this project. Check the latest public release, including prereleases, at https://github.com/bryan123466/taskcarry/releases. If I have already provided a product package, verify and use that package first. Read the selected package's update guide and the update procedure in its taskcarry-project-setup Skill before determining what to do.
>
> First check the existing installation, project records and unfinished operations. Read the update notes and determine whether this update applies. Keep the original governance directory, tasks, checkpoints and working chats, preserving my files, configuration changes and unfinished work.
>
> Within this update's scope, prepare the appropriate changes, briefly explain their impact, then perform the update and checks you can handle. Change only what needs updating. If no update is needed, tell me the result without reinstalling or repeating project onboarding.
>
> If I need to confirm a host action or reload a connection, give me only the current necessary step, with its destination and content filled in. After I confirm completion, continue checking the actual connection and whether the original project can resume.
>
> Finish with a short checklist: what changed, whether my existing work was preserved, whether I can continue now, and any remaining action I need to take.

## What happens during an update

Governance continues from the existing project, handling the toolkit, project integration files and host connections as needed. You do not need to compare version numbers, choose wheel files or copy configuration entries yourself.

For a documentation update, use the updated instructions. When the toolkit package needs replacing, the assistant uses the installation capabilities provided by your host. TaskCarry itself has no separate one-click patch command. If configuration conflicts arise, governance preserves the current state and explains the specific decision needed.

## If you stop partway through

Return to the same chat and say: **“Continue the TaskCarry update, checking what has already completed first.”** Governance resumes from the saved progress. A pending reload does not require another installation.

## Further details

- [What changed in this version](../RELEASE_0.2.0rc7.md)
- [Maintenance, compatibility and recovery reference](governance-maintenance.md)
- [Manual fallback when the assistant cannot perform a step](manual-setup.md)
