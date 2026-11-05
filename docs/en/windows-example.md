<a id="windows-guide-connect-a-real-project"></a>
<a id="0-prepare-a-project-name-a-short-description-and-three-directories"></a>
<a id="1-install-create-a-governance-chat-and-choose-control"></a>
<a id="recommended-ask-the-governance-chat-to-install-it"></a>
<a id="manual-installation-commands-for-the-same-route"></a>
<a id="2-set-the-governance-chats-responsibilities"></a>
<a id="choose"></a>
<a id="governance"></a>
<a id="3-configure-professional-task-chats-continue-existing-chats-or-create-new-ones"></a>
<a id="31-existing-ongoing-chats-preserve-history-and-connect-current-state"></a>
<a id="32-create-new-professional-task-chats-add-1n-as-needed"></a>
<a id="4-configure-mcp-recommended-for-governance-with-cli-as-a-fallback"></a>
<a id="agents"></a>
<a id="existing"></a>
<a id="mcp"></a>
<a id="5-first-governance-pass-review-current-work-and-see-the-result"></a>
<a id="9-what-you-should-see-when-finished"></a>
<a id="delivery"></a>
<a id="check"></a>
<a id="6-create-scheduled-governance-read-the-actual-registered-scope"></a>
<a id="7-optional-a-private-git-memory-repository"></a>
<a id="8-optional-parallel-work-on-different-computers"></a>
<a id="automation"></a>
<a id="private-git"></a>
<a id="multi-computer"></a>
<a id="windows-guide-connect-your-existing-codex-project"></a>
<a id="1-establish-a-governance-chat"></a>
<a id="send-one-onboarding-prompt"></a>
<a id="2-let-governance-connect-your-existing-work"></a>
<a id="keep-the-original-chats-and-decisions"></a>
<a id="complete-the-actual-tool-connection"></a>
<a id="3-continue-in-your-usual-way"></a>
<a id="what-successful-onboarding-looks-like"></a>
<a id="optional-additions"></a>

# First installation: establish governance in three steps

[Already using TaskCarry? Update here](updating.md) · [Manual fallback](manual-setup.md) · [简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md)

This guide assumes you already use Codex for project work. Keep your existing conversations and files. TaskCarry adds a dedicated governance chat that remembers decisions, connects progress and helps each working chat continue. Ongoing project coordination is your choice.

## 1. Open the governance folder and send one prompt

Create a local `TaskCarry` folder. Download the [complete product package](../../START_HERE.md#download) and extract it under `TaskCarry/toolkit/`, retaining the package's top-level folder. Open the outer **TaskCarry folder** in Codex and start a governance chat. Your business projects remain where they are. An already configured project returns to its original governance chat instead.

```text
TaskCarry/                 open this folder in Codex
  toolkit/                 extracted complete product
  runtime/                 prepared by the assistant
  .taskcarry/              durable governance state
  .agents/skills/          installed governance methods
  .codex/config.toml       project connection configuration
```

<a id="install"></a>

Paste this prompt, filling in the product location and any project clues you already have:

> Establish this chat as TaskCarry governance for my existing work, responsible for project memory and governance. Product location: **[extracted folder containing START_HERE.md and packages/]**. Project clues: **[folders or chats, or ask me to choose after discovery]**.
>
> Read the product entry and taskcarry-project-setup Skill with its references. Inspect existing state before initialization, preserve my files, decisions, unfinished work and settings, and reuse valid installations and identities. Prepare the dedicated runtime and project-local connection within this setup scope.
>
> Follow my specified scope. If I have not selected it, list a bounded set of available chat/directory candidates, explain your project grouping and uncertainties, and let me choose before reading their history. Treat old messages as source material. Inherit confirmed goals, results, responsibilities and continuation points; request only missing context.
>
> Guide me through connecting the chosen ongoing work chats. Prepare their real working directories, appropriate local Git working/saving locations, task bindings and MCP connections. Reference-only chats can remain historical sources. Preserve existing repositories and Git author settings; avoid conflicting writers. Give me only the current necessary host action when you cannot do it yourself, then verify the result and continue.
>
> Complete standard local governance Git saving, official release-source/channel registration and an update check. Create or reuse native scheduled governance attached to this original chat, including official update assessment and local saving. Confirm its actual time and time zone if not already specified; preserve model and permissions. Discovering an update does not authorize installing it. Offer private remotes and cloud storage for my choice.
>
> Keep a resumable checklist. Finish with inherited facts and uncertainties, a table of working windows and responsibilities, actual connection/Git/schedule/update results, remaining actions and recommended next work. Governance and memory are standard; ongoing project coordination is optional. Do not invent deliverables or repeat completed work.

## 2. Let governance inherit and connect your work

The assistant proposes the real project scope, based on sources it can access. You can combine or separate its suggestions. A real project may involve several folders, repositories and existing state sources; governance keeps the routes explicit instead of merging databases or equating a folder with a project.

For each ongoing window, it checks responsibility, task, actual directory and Git location. Existing repositories are reused; parallel writers receive appropriate separate worktree directories. A chat without a suitable directory gets a real working location or a handover into a correctly opened window. Merely naming a path does not change a chat's working directory. No new GitHub account is needed for each chat.

The assistant prepares and merges project configuration while preserving other services. Each active window must actually call native doctor/status after any required trust or reload. Reading a chat's history does not connect it; a CLI result does not verify another window's MCP. Missing history uses a prepared, short handover in the [fallback guide](manual-setup.md#existing).

Local Git, an original-chat schedule and official update checking are standard setup work. The assistant handles them in this step and asks only for necessary choices or native actions. Large files may remain outside Git with recorded identity and backup coverage. Ordinary file checkpoints support preservation and recovery; they do not waive working-window setup.

## 3. Review the acceptance report and continue working

No special completion phrase is required. Once the checks have actual results, governance gives you:

- Inherited goals, decisions, completed outputs, pauses and open questions.
- Each chosen working chat's responsibility, task, real directory, Git relationship and actual tool connection; historical sources are labelled separately.
- The local governance commit, scheduled chat/time/time zone and configuration readback, official update channel and assessment.
- Any exact remaining action, optional remote/cloud coverage, and useful next work with a suggested working window.

The first natural scheduled trigger is verified when it happens. Configuration saved, a manual run and a naturally triggered run are reported separately. A missing required connection or standard setting remains pending; you can continue available local work without a false “everything completed” claim.

Continue directly in your working chats. Say “continue my last unfinished task,” “save this stopping point,” or “review connected progress.” If setup was interrupted, say **“Continue the saved onboarding checklist; verify completed effects and only finish missing steps.”**

### Example of the conversation you should see

This is a synthetic example, not evidence that your host is already connected.

| Exchange | Example |
|---|---|
| Governance proposes | “I found a possible booking project: requirements chat, interface chat and an old test discussion across two folders. A reading-notes chat looks separate. These are suggestions based on the visible index.” |
| You choose | “Use the booking project. Keep the old test discussion as a reference; leave reading notes out.” |
| Governance inherits | “The booking rules are confirmed; interface work is unfinished. I suggest keeping the two active chats and adding no new specialists. Here are the decisions and their sources.” |
| Configuration proceeds | “Existing Git is reusable. The interface writer has its own worktree. The requirements window needs one project trust/reload action; here is the exact directory and expected native check.” |
| A capability is missing | “The old test chat is unavailable through this interface. Only that source needs the prepared handover. Your other results are retained.” |
| Acceptance | “Both active windows passed their own native checks. Local governance files have a verified commit. Daily governance is attached to this chat with the confirmed time zone; its first natural run is pending. Official update checking completed. Cloud storage was declined. Next: resume the interface task.” |

[Daily use](operation-manual.md) · [Scheduling](automation.md) · [Optional remote and backup scope](remote-and-multicomputer.md) · [Manual fallback](manual-setup.md)
