# RC9 · From exercises to product capabilities

[简体中文](#zh-cn) · [English](#en) · [繁體中文](#zh-tw)

<a id="zh-cn"></a>

## 简体中文

RC9 把已完成的项目演练整理成可重复使用的管家工作方法，并补上新对话收录的内核支持。下表区分本版新增代码、已有内核能力和随包工作方法；演练使用合成项目。

| 用户要做的事 | 已完成的演练 | 本版在哪里提供 |
|---|---|---|
| 把正在工作的对话交给管家跟进 | 原对话收到加入提示后关联原任务；管家吸收回执、跨轮保留待回报事项，重复加入不重复计数 | 新增 `taskcarry/chat_joins.py`；`cycle join_inbox/join_absorb/report_delivered`；项目设置与日常治理 Skill |
| 不同 AI 交回的成果能对上同一版 | R01/C01：不同电脑通过各自任务分支交付，A 选定集成，B/C 对照候选与共同版本回读 | 现有阶段接收、工作区更新与 Git 文件交接；三步手册和多电脑参考 |
| 用上别的窗口已经积累的经验 | C02：先检查是否收到感知画面。未改变的样本复用已有结论；改过缺帧提示的样本重新验证并判为不通过，独立复核一致 | 日常治理方法要求核对经验的来源、版本、适用条件和反例；经验通过选定的 Git 文件交接 |
| 新 AI 加入后先完成一项工作 | D01：本机隔离 CLI 中运行 Gemini，读取加入资料、完成一份无人机演示指南，原管家复演后接收其授权范围内交付 | 三步上手、已有 TaskCarry 项目加入、任务交付 Skill。该成果在任务分支，接收不等于已经进入共同主线 |
| 换 AI 时找回整个工作链 | WorkBuddy 与 Gemini 的只读接手演练；D01 从旧恢复副本及较新选定记录还原 5 项任务、4 个专业工作区，原管家复核并指出局部修正 | 标准“接手项目”方法：确认项目与角色、还原目标与进度、交叉检查当前文件及历史、主动建议下一步；需要迁移时再办理主写交接 |
| 安装包更容易开始 | 外层 `TaskCarry/` + `toolkit/` + 首次提示；Windows x64 包提供固定版本的 Python 与 MinGit | `templates/first-use/START_HERE.md`、发行构建脚本、三语安装与更新手册 |

**这些验证支撑的是人和 AI 一起推进项目。** 三机临时轮询仅用于演练；没有作为无人值守协作产品推给用户。项目管家可以主动整理和建议，专业对话继续承担自己的工作。

连接方面，支持自定义本地 stdio MCP 的 AI 工具具备接入条件，仍要在实际窗口核对工具调用。Codex、WorkBuddy 与运行 Gemini 的本地 CLI 有项目演练记录；模型名称本身不证明某个应用支持 MCP。网页端 HTTPS 的临时试验只验证了限定来源的角色与记录读取，本版不提供托管服务或稳定公网连接器。

迁移演练依据已保存且可访问的项目资料，未复制 AI 账号或所有聊天历史，也未把备用副本激活成新的主写方。经验跨机复用走明确文件交接，未声称运行中的治理数据库自动同步。

公开内容保留合成案例和通用方法，原账号、私人仓库、本机路径与原始会话回执不随包发布。[代码测试与验证记录](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc9/docs/VALIDATION.md) · [更新说明](RELEASE_0.2.0rc9.md#zh-cn)

<a id="en"></a>

## English

RC9 adds verified chat-join intake in the shared Core and packages the working methods learned from synthetic project exercises.

- **Existing chats:** a join receipt is checked against the exact project, chat, task and consumed workbench entry. Intake survives a later reporting cycle and deduplicates repeat joins. The new module is `taskcarry/chat_joins.py`, called by the existing CLI/MCP cycle API.
- **Collaborative versions (R01/C01):** separate computers contributed on task branches; the integration manager selected results; collaborators checked the candidate and shared version. Git carries selected files between otherwise separate controls.
- **Experience reuse (C02):** collaborators reused an unchanged sample's acceptance and retested changed missing-frame wording. The changed sample failed, with an independent matching review. The daily governance method carries source, revision, applicability and counterexamples through selected project files.
- **A new AI collaborator (D01):** Gemini running in an isolated local CLI delivered a drone guide. The original manager replayed it and accepted the scoped contribution. Its task-branch delivery was not silently counted as integration into the common main branch.
- **Project takeover:** WorkBuddy and Gemini read-only exercises reconstructed project context. D01 traced five tasks and four specialist workspaces using an older standby plus newer selected records. The original manager found the account useful with localized corrections and retained write authority. The packaged method guides reconstruction, priorities, missing evidence and an explicit writer handoff when migration is requested.
- **First use:** an outer TaskCarry folder, toolkit and opening prompt; the Windows x64 artifact also includes pinned Python and MinGit distributions.

Temporary multi-machine polling was an exercise aid, not a shipped unattended collaboration service. Local stdio MCP is an integration route, not proof that every AI app works. The HTTPS web exercise covered scoped role and source reads only; RC9 does not ship a hosted service or stable public connector. Saved project records do not include every private chat or unsaved editor buffer, and experience files do not automatically synchronize live governance databases.

See [source test evidence](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc9/docs/VALIDATION.md) and [release notes](RELEASE_0.2.0rc9.md#en). Only synthetic examples and reusable methods are public; private receipts, accounts and machine paths are excluded.

<a id="zh-tw"></a>

## 繁體中文

RC9 新增原對話加入回執的核對、收錄、跨輪回報與去重，並把合成專案演練整理成隨附工作方法。

- **R01/C01 協作版本：** 不同電腦各自交付任務分支，整合管家選定接收，協作者讀回候選與共同版本。
- **C02 經驗複用：** 未變更樣本沿用既有驗收；改過缺幀文字的樣本重新驗證並判為不通過，獨立複核一致。經驗記錄保留來源、版本、適用條件與反例，透過選定 Git 檔案交接。
- **D01 新 AI 協作者：** 本機隔離 CLI 中的 Gemini 完成演示指南，原管家復演後接收範圍內交付；任務分支交付不等於已併入共同主線。
- **接手專案：** WorkBuddy 與 Gemini 完成唯讀演練；D01 從舊備用副本和較新選定記錄還原 5 項任務、4 個專業工作區。原管家複核後指出局部修正，保留主寫權。隨附方法引導管家重建工作鏈、提出下一步，在使用者要求遷移時再交接主寫。
- **上手：** 外層 TaskCarry 資料夾、toolkit 與開場提示；Windows x64 發行套件另附固定版本 Python 和 MinGit。

這些演練支援人與 AI 共同推進專案。三機臨時輪詢沒有變成無人值守產品。自訂本機 stdio MCP 是接入條件，實際應用仍需核對工具；網頁 HTTPS 試驗只涵蓋限定角色與記錄讀取，本版沒有託管服務或穩定公網連接器。遷移依據可取得的已儲存記錄，不複製 AI 帳號或全部私人對話，也不自動同步執行中的治理資料庫。

[程式碼測試與驗證記錄](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc9/docs/VALIDATION.md) · [更新說明](RELEASE_0.2.0rc9.md#zh-tw)
