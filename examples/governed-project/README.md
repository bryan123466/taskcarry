# Three-step onboarding of an existing project

[First-installation handbook](../../docs/en/windows-example.md) · [简体中文手册](../../docs/zh-CN/windows-example.md) · [繁體中文手冊](../../docs/zh-TW/windows-example.md) · [Manual fallback](../../docs/en/manual-setup.md)

This fictional appointment planner already has a coding chat, an unfinished Git change, guide notes from a chat without a project folder, and an older decision discussion. All names and inputs in [scenario.json](scenario.json) are synthetic. Use the handbook's onboarding prompt with your own confirmed scope; running this example is not a prerequisite for using TaskCarry.

## 1. Establish governance and retain the existing work

Open the TaskCarry folder in a new governance conversation and send the complete installation prompt from the handbook. The assistant identifies existing work, asks you to confirm the project scope and retains the decision that the application and guide belong to one real-world project.

The example's intended arrangement is:

| Window | Responsibility | Actual work location | TaskCarry task/workspace |
|---|---|---|---|
| `example-governance` | Governance, memory and next-step suggestions | Dedicated governance directory with local Git preservation | Own project control |
| `example-app` | Continue the application | Existing application Git worktree | `app` / `app-writer` |
| `example-guide` | Write the guide | A newly prepared guide Git worktree | `guide` / `guide-writer` |
| `example-history` | Historical decisions | Retained source reference | Reference only; no new active worktree |

A task ID states responsibility; a workspace registration identifies a real Git directory and branch; Git author settings identify commit attribution. They are checked separately. Different chat names or task IDs do not isolate concurrent file writes. The original application changes remain in their existing HEAD/index/worktree layers, and the guide's original notes stay in their ordinary source directory.

## 2. Let governance guide the remaining setup

The assistant registers tasks and the existing application worktree. For the guide it prepares a suitable Git work location, records the original notes as a task source, and retains a selected-file checkpoint. If the host cannot associate the old projectless chat with that location, it guides a new continuation window and carries over decisions and the next step. Registration alone never proves that a chat's actual directory changed.

Each active workbench receives materials pointing to the same control. The assistant previews and merges its project MCP block while preserving other settings. It asks for the specific trust/reload action only when the host needs it. Each window then calls native doctor/status in its own context. The governance window also needs its own native acceptance.

The assistant saves the chosen governance rules locally in Git, registers the official update channel, checks releases and records an applicability assessment. It creates or reuses a native daily heartbeat in the original governance chat and reads back its actual thread, directory, time, timezone and prompt. Remote Git and cloud storage remain unselected in this example. No business repository is uploaded merely because governance was installed.

## 3. Read the actual acceptance report and continue

A report should distinguish results such as:

- **Saved locally:** project rules have a specific Git commit; original application staged and unstaged work are retained; selected guide notes have a recoverable checkpoint.
- **Materials connected:** each generated project MCP block points to the intended control. This proves file configuration, not host loading.
- **Pending native acceptance:** until the actual window supplies doctor/status, that window remains pending. CLI or a separate stdio session cannot complete this item.
- **Schedule configuration / first natural trigger:** these are separate results. A generated plan is not an active schedule, and a manual run is not a natural trigger.
- **Next work:** continue application validation in its original worktree and draft the guide's cancellation section in the assigned guide worktree. The historical conversation stays reference-only.

The executable source test deliberately stops before real host activation. Its honest final report therefore has `standard_ready=false` and `natural_trigger_verified=false`, with specific host steps still pending. A real user's three-step setup continues through those steps; this synthetic test does not manufacture native evidence to make a complete-looking report.

## Source verification

From a source checkout, run `python -m unittest tests.test_governed_project_example -v`. The test reads the supplied scenario and uses the same dispatch API as CLI/MCP. It creates isolated synthetic Git repositories, preserves pre-existing staged/unstaged bytes, registers both workbenches, connects project configuration, captures and restores original notes, stores governance files, checks a synthetic release response, and resumes the existing checklist. It makes no network request, host configuration change outside the test directories, real chat, production schedule or public release.

## 中文说明

这是一个完整的三步接入示例：先建立独立治理窗口并继承已有工作，再由总控安排持续工作窗口的真实工作目录、Git 关系、任务与 MCP 接入，最后按实际证据出具验收报告和下一步建议。已有应用的暂存与未暂存内容保留；原本没有项目目录的资料线程获得新的 Git 工作位置，原始资料仍可留在普通目录；旧讨论仅作为历史来源。

本地治理 Git、官方更新检查和原治理窗口定时任务是标准配置。网盘和远端仓库按需选择。源码测试只验证合成环境中的文件、Git、配置与接续结果，因此如实保留原生窗口验收和自然定时触发待完成；实际用户接入时，由总控继续带领完成这些步骤。

## 繁體中文說明

本例依三個步驟建立治理、繼承既有工作、配置持續工作視窗並驗收。既有應用的 Git 暫存與未暫存內容保留；原本沒有專案目錄的資料視窗獲得合適的 Git 工作位置，原始資料保留原處；歷史討論不重新變成待辦。任務身分、實際工作目錄與 Git 提交署名分別核對。

本地治理 Git、官方更新檢查與原治理視窗的定時任務屬於標準配置；遠端與網盤依需求啟用。合成測試不冒稱原生視窗已載入，也不把排程計畫當成自然觸發。實際接入時，由治理繼續完成具體缺步並提供下一步建議。
