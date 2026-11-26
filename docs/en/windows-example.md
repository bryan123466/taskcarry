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
<a id="5-first-governance-pass-review-current-work-and-see-the-result"></a>
<a id="9-what-you-should-see-when-finished"></a>
<a id="6-create-scheduled-governance-read-the-actual-registered-scope"></a>
<a id="7-optional-a-private-git-memory-repository"></a>
<a id="8-optional-parallel-work-on-different-computers"></a>
<a id="automation"></a>
<a id="windows-guide-connect-your-existing-codex-project"></a>
<a id="1-establish-a-governance-chat"></a>
<a id="send-one-onboarding-prompt"></a>
<a id="2-let-governance-connect-your-existing-work"></a>
<a id="keep-the-original-chats-and-decisions"></a>
<a id="complete-the-actual-tool-connection"></a>
<a id="3-continue-in-your-usual-way"></a>
<a id="what-successful-onboarding-looks-like"></a>
<a id="optional-additions"></a>
<a id="install"></a>

# Get started with TaskCarry in three steps

[Update or continue existing governance](updating.md) · [Manual fallback](manual-setup.md) · [Feedback examples](user-feedback-examples.md) · [Drone project example](../../examples/vision-drone-governance/README.md) · [简体中文](../zh-CN/windows-example.md) · [繁體中文](../zh-TW/windows-example.md)

Keep writing code, designing and organizing materials in your existing AI chats. Start a separate **project manager** chat to track progress, connect the work across chats and find earlier decisions and lessons. If you already have a manager or are upgrading, start with [update and continuation](updating.md).

## 1. Extract TaskCarry and start a project manager chat

**① Extract the ZIP** into an empty folder of your choice. For example, create a folder on your D: drive and extract the package there.

**② Start a project manager chat.** Follow the row for your tool to select the folder you extracted into and start a new chat using that folder. This chat will be your project manager.

| Your tool | How to open the folder |
|---|---|
| **Codex desktop** | Press **Ctrl+O** on Windows or **⌘O (Command+O)** on Mac. Select the extracted folder, then start a new chat using it. |
| **WorkBuddy** | Start a new task. Set the working directory below the input box to the extracted folder, then send the opening message below. |
| **Claude Code (CC, desktop)** | Open the **Code** tab in the Claude desktop app, start a local session and select the extracted folder. |
| **Claude Code (CC) / Gemini CLI / Kimi Code CLI (terminal)** | In Windows PowerShell or a Mac terminal, run `cd "full path to the extracted folder"`. Then run the command for your tool: `claude` for CC, `gemini` for Gemini CLI, or `kimi` for Kimi Code CLI. |
| **DeepSeek / GLM (used through CC or WorkBuddy)** | If you already configured the model in CC, follow the CC instructions above. If you use it in WorkBuddy, follow the WorkBuddy instructions. |

**③ Paste this message** into the new chat:

> Find the TaskCarry instructions in this folder and set up my project manager. If I already have one here, continue with it. You may suggest projects and chats from titles I allow you to see, or I can choose the chats myself. Give me a single invitation I can paste into the chats I want to include. Only read the work I choose to share.

The manager follows the package instructions to install and configure TaskCarry, then gives you an invitation. Choose from the projects and chats it suggests, or say, “Give me the invitation. I’ll choose the chats myself.” It will tell you when a step needs a click or confirmation.

If the manager reports that Git or Python is missing, install the missing tool and continue. [Git](https://git-scm.com/downloads) · [Python 3.11+](https://www.python.org/downloads/)

<details>
<summary>Official instructions for each tool</summary>

[Codex shortcuts](https://developers.openai.com/codex/app/commands) · [WorkBuddy working directory](https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Task-Bar) · [Open a project in Claude Code](https://support.claude.com/en/articles/14552382-your-first-day-in-claude-code) · [Gemini CLI](https://github.com/google-gemini/gemini-cli#quick-examples) · [Kimi Code CLI](https://moonshotai.github.io/kimi-code/en/reference/kimi-command.html) · [DeepSeek in CC](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/) · [GLM in CC](https://docs.z.ai/devpack/tool/claude)

</details>

<a id="agents"></a>
<a id="existing"></a>
<a id="mcp"></a>

## 2. Paste the invitation into the chats you want to include

**① Paste the invitation into your working chats.** The manager gives you a message to copy. Paste it once into each chat you want to include. Use the original chat for work already underway. For a new task, you can start a new chat.

**② Complete the connection with the manager’s help.** It guides you through setup and tells you when to select a working folder, save work or restart your AI tool. Once connected, each working chat reports its responsibility, where it left off and what comes next. For a new chat, tell it which task to take on.

**③ Check which chats have joined and continue working.** Ask the manager “Which chats have joined?” It lists their responsibilities, progress and next actions. If one is missing, give the manager its name so it can check the remaining step.

To add another chat later, say “I want to add another chat.” The manager gives you the invitation and instructions. With scheduled check-ins enabled, it picks up the new chat and reports back at the next check-in.

**Drone project example.** Paste the same invitation into the software development and product testing chats. The software chat says, “The demo is updated.” The product chat says, “Testing is done.” Ask the manager, “Did the product team test the version the software chat just changed?” It checks both versions and the test records, then tells you which version was tested and whether the change reached the shared version. When more changes arrive, it also points out what needs another test.

<a id="check"></a>
<a id="delivery"></a>
<a id="private-git"></a>
<a id="multi-computer"></a>

## 3. Get to work and let the manager follow up

**① Review the project overview**

Once your chats are connected, the manager puts together a project overview. You can also ask:

> Show me where the project stands and what I should work on next.

| What you want to know | What the manager tells you |
|---|---|
| **How is the project going?** | The current goal, completed work, and anything unfinished or blocked. |
| **What is each chat working on?** | Each chat's responsibility, where it left off and what it plans to do next. |
| **What is already set up?** | Whether the working chats are connected, where project records are saved and which setup steps remain. |
| **What should I do next?** | Which chat to return to, what to work on and which decisions need your input. |

Return to a working chat and say “Continue where we left off.” You can also ask the manager “Which chat has already done this?” or “How did we solve a similar problem last time?”

**② Turn on scheduled check-ins — recommended**

Let the manager check progress in the connected chats, organize new results, decisions and lessons, and flag things that need your attention. You can say:

> Help me enable scheduled check-ins. Suggest times to review progress and report back that suit this project.

The manager gives you setup instructions for your AI tool and confirms the check-in and reporting times with you. Once enabled, keep working in your usual chats while the manager follows up as agreed. New chats are picked up at the next check-in after you paste their invitation.

To change the arrangement, say “Report every evening instead” or “Pause scheduled check-ins for now.”

**③ Add online backups or collaboration with other AIs and computers as needed**

The manager suggests whether your project would benefit from online backups or collaboration across computers and AI tools. If you need to keep the project long term, move computers or work with others, back up important files and organized project records to **your own private GitHub repository**.

Tell the manager what you want to do:

| What you want to do | What to say to the manager |
|---|---|
| **Back up important materials online** | “Help me back up this project's important files and project records to my own private GitHub repository. Walk me through setup.” |
| **Bring in another AI or computer** | “I want another AI or computer to work on this project with me. Help me plan its role and how to connect it.” |
| **Join someone else's managed project** | “I want to join a project that already uses TaskCarry as a collaborator. Tell me what I need from its manager.” |
| **Move project management to another AI or computer** | “I want to move overall project coordination from the other AI or computer to you. Please take over that role and help me rebuild the full existing workflow locally.” If only part of the work is moving, name the chats to move. |

Combine these arrangements as needed, or add them later. The manager gives you the steps and tells you where to act when you need to sign in, choose what to share or open a working chat.

[Scheduled check-in setup](automation.md) · [Online backup and collaboration](remote-and-multicomputer.md) · [Project migration steps](operation-manual.md#move-project) · [Daily operations](operation-manual.md) · [Official update and maintenance](core-update-maintenance.md)

<details>
<summary>Complete setup acceptance and technical references</summary>

The assistant uses the `complete_v1` checklist for scope, native runtime, local Git, project identity, understood sources, workbench publication and consumption, the first cycle, recovery, official updates and original-chat scheduling. Natural triggers retain separate evidence. Older receipts retain their original meaning.

[Daily operations](operation-manual.md) · [Three layers and project memory](architecture.md) · [Backup, recovery and parallel work](remote-and-multicomputer.md) · [CLI / MCP contracts](../COMMANDS.md)

</details>
