# TaskCarry in practice / 实际能力范围 / 實際能力範圍

[English](#en) · [简体中文](#zh-CN) · [繁體中文](#zh-TW)

<a id="en"></a>

## English

TaskCarry gives AI-assisted projects a local record of progress and results. It connects task records, selected saved files, Git history, and a governance chat so work can pause, contribute useful stages, and continue later. The current user manual demonstrates this workflow with Codex.

### Everyday use

Use the three-step onboarding conversation with an existing Codex project. Establish or reuse its governance chat, inherit selected responsibilities and decisions, and choose whether it also coordinates the project. Standard setup includes real working-window directories and Git bindings, native MCP checks, local governance Git saving, a schedule returning to the original governance chat, and official release checks. A history-only conversation can remain a source without becoming an active workspace. Ordinary file checkpoints support continuity and recovery; they do not replace the standard Git setup.

The shared Core and maintained Skills work alongside your own project rules. A real project can include several directories, conversations and existing state sources. Source-qualified records keep those identities distinct. The bounded task-context reader returns related decisions, checkpoints, next steps and evidence without treating a read as acceptance.

- Keep one receiving baseline per control scope and separate registered workspaces for parallel tasks. CLI and MCP call the same tools for saved progress, stage collection, workspace updates, and supported recovery.
- Preserve unfinished work without marking it complete. A checkpoint captures selected files already saved to disk; it does not capture unsaved editor buffers or all conversation history.
- Review plans before collecting stages or updating workspaces. Supported local commits, staged changes, working-file changes, and new files are preserved during updates; specific conflicts need attention.
- Reuse a known recovery action when its conditions match. An unfamiliar problem needs diagnosis; an experience note alone does not create a new repair function.

### Connections verified during setup

MCP must be connected in the AI host you use and confirmed with a real tool call. CLI and MCP provide integration points; each host needs its own verification. Codex is the current documented onboarding example, not proof that all AI platforms have been checked. AI comes from your host, with no separate model API or model training performed by TaskCarry.

The governance chat provides its first acceptance report and next-step suggestions in the same conversation. Host scheduling is a standard guided setup item; the wheel does not contain a scheduler or create host schedules by itself. Configuration readback, a manual run and the first natural trigger are separate evidence. Host access or reload steps remain visible until complete. Private remotes and cloud storage remain optional.

The packaged Codex reader uses a bounded App Server read-method allowlist and state-index-only listing. Its tested protocol version is `0.166.0-alpha.6`; other versions return a compatibility gap rather than silently dropping safeguards. It reads the selected local source, not every account, cloud conversation or computer. Host startup can maintain caches and logs. A missing index entry is not proof that a conversation does not exist; use an explicit permitted handoff when needed.

Official updates use the selected stable/RC channel. Checks verify available manifest, tag and asset metadata; they do not download every package byte or install a candidate. Older releases without structured metadata require review. Offline checks stay unverified. Saved applicability decisions, installed packages and actual host loading remain distinct.

Private Git can hold selected committed and pushed results. Remote push and deployment are separate operations. The [multi-computer guide](en/remote-and-multicomputer.md) describes independent task branches and one integration host; it **has not completed a real two-computer end-to-end validation**. Computers do not share a live control database, merge their local state automatically, or take over pending operations automatically.

### Practical limits to account for

- Each control scope uses one local store and one receiving baseline. Toolkit locks serialize its own operations; other editors and Git commands must not write the same receiver or updating workspace at that time. Independent workspaces can continue their tasks.
- Checkpoints allow 500 paths, 32 MiB per stored object, and 128 MiB total capture. Larger files can be recorded as artifact references, which are pointers rather than backups of their contents.
- Restoring a checkpoint rebuilds the selected file layers on an identified synthetic Git baseline. Preserve a Git backup as well when you need the full repository history.
- Connections cover explicitly registered workspaces and tasks, not every private chat. Project Skills guide behavior but do not add permissions or create an OS security sandbox.
- Installing or updating tools and Skills does not merge business Git history. Receiving results and adopting them into a selected workspace use their own reviewed plans. Saved setup diagnostics describe files on disk and do not prove that an existing host process loaded a newly installed version.
- The toolkit does not repair the operating system, move AI-host accounts, send external messages, or guarantee recovery of arbitrary external effects. You decide professional or business acceptance and external sharing.

[Start with the manual](en/windows-example.md) · [Working together over time](OPERATING_PRINCIPLES.md) · [Recorded validation](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc7/docs/VALIDATION.md)

<a id="zh-CN"></a>

## 简体中文

TaskCarry 为 AI 辅助项目提供本地进度与成果记录。它把任务记录、选定的已保存文件、Git 历史和治理聊天接起来，让工作可以暂停、按阶段贡献成果，再从原位置继续。当前操作手册使用 Codex 演示这套流程。

### 日常可以怎样用

通过三步对话接入已有 Codex 项目：建立或复用治理窗口，继承选定分工和决定，由用户选择是否兼任项目协调。标准配置包括持续工作窗口的真实目录和 Git 关联、原生 MCP 验收、本地治理 Git 保存、返回原治理窗口的定时任务，以及官方发行检查。仅作历史来源的对话不必变成活跃工作区。普通文件检查点用于接续与恢复，不替代标准 Git 配置。

共享 Core 和随产品维护的 Skills 与用户自己的项目规则共同工作。一个现实项目可以包含多个目录、对话和既有状态来源；记录保留来源身份。有界任务上下文返回相关决定、检查点、下一步和证据，读取本身不会变成接收或验收。

- 每个治理范围保留一条接收基线，并为并行任务登记独立工作区。CLI 与 MCP 调用同一套保存进度、汇总阶段、更新工作区和已知恢复工具。
- 保留未完成工作，不必把它标成完成。检查点保存选定且已经写入磁盘的文件，不包含编辑器未保存内容或全部聊天历史。
- 汇总阶段或更新工作区前先检查计划。更新会保全支持范围内的本地提交、暂存修改、工作文件修改和新文件；具体冲突需单独处理。
- 条件符合时复用已有恢复动作。陌生问题需要诊断，写下一段经验不会自动产生新的修复功能。

### 接入时完成验收的连接

MCP 要在你使用的 AI 宿主中接通，并实际调用工具确认。CLI 与 MCP 提供接入方式，各宿主仍需单独验证。Codex 是当前文档的上手示例，不代表所有 AI 平台都已经检查。AI 能力来自宿主，TaskCarry 不自行调用另一套模型 API 或训练模型。

治理窗口在原对话中给出首次验收报告和下一步建议。宿主定时任务属于标准对话式接入项目；wheel 本身不包含调度器，也不会自行创建宿主任务。配置回读、手动运行和第一次自然触发分别留证。需要宿主授权或重载的步骤保留到实际完成。私有远端与网盘按需启用。

随包提供的 Codex 读取适配器使用有界 App Server 只读方法白名单，并只查询状态索引。已核对的协议版本为 `0.166.0-alpha.6`；其他版本报告兼容性缺口，不静默省略约束。读取范围是选定的本地来源，不代表所有账号、云端聊天或电脑；宿主启动可能维护缓存与日志。索引未列出不等于对话不存在，需要时使用明确授权的交接。

官方更新按所选正式/RC 通道检查现有清单、tag 和附件元数据，不代表每个包的字节已下载，也不会安装候选。缺少结构化清单的旧发行保留人工复核；离线检查保留未核实。已保存适用性判断、实际安装和宿主实际加载分别记录。

私有 Git 可以保存选定且已经提交、推送的成果；远端推送和部署属于单独操作。[多电脑手册](zh-CN/remote-and-multicomputer.md)介绍独立任务分支与单一集成主机的配合，但**尚未完成真实双电脑端到端验证**。电脑之间不共享运行中的治理库，也不自动合并本地状态或接管未完成操作。

### 使用时需要知道的范围

- 每个治理范围使用一个本地控制库和一条接收基线。工具锁只协调工具自身操作；更新期间，其他编辑器和 Git 命令不要写同一接收或更新工作区，独立工作区可以继续各自任务。
- 检查点最多选择 500 条路径，单个存储对象上限 32 MiB，总量上限 128 MiB。较大文件可以记录材料引用；引用保存位置，不等于备份了文件内容。
- 从检查点恢复时，会在明确标识的合成 Git 基线上重建选定的文件层。需要完整仓库历史时，也要保留 Git 备份。
- 连接覆盖明确登记的工作区和任务，不读取全部私人聊天。项目技能指导工作方式，不增加权限，也不构成操作系统级安全沙盒。
- 安装或更新工具与技能不会合并业务 Git 历史。接收成果、将其更新到选定工作区，都使用各自需要检查的计划。安装诊断说明磁盘上的文件状态，不证明已有宿主进程已经加载新版本。
- 工具不修复操作系统、不迁移 AI 宿主账号、不发送外部消息，也不保证恢复任意外部操作。专业或业务验收以及对外分享由你决定。

[从手册开始](zh-CN/windows-example.md) · [持续协作](OPERATING_PRINCIPLES.md) · [验证记录](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc7/docs/VALIDATION.md)

<a id="zh-TW"></a>

## 繁體中文

TaskCarry 為 AI 輔助專案提供本機進度與成果記錄。它把任務記錄、選定且已儲存的檔案、Git 歷史與治理對話接起來，讓工作可以暫停、按階段貢獻成果，再從原位置繼續。目前操作手冊使用 Codex 示範這套流程。

### 日常可以如何使用

透過三步對話接入既有 Codex 專案：建立或重用治理視窗，繼承選定分工與決定，由使用者選擇是否兼任專案協調。標準設定包含持續工作視窗的真實目錄與 Git 關聯、原生 MCP 驗收、本機治理 Git 儲存、返回原治理視窗的排程任務，以及官方發行檢查。僅作歷史來源的對話不必變成活躍工作區。一般檔案檢查點用於接續與恢復，不替代標準 Git 設定。

共用 Core 與隨產品維護的 Skills 和使用者自己的專案規則共同工作。一個現實專案可以包含多個目錄、對話及既有狀態來源；記錄保留來源身分。有界任務上下文傳回相關決定、檢查點、下一步與證據，讀取本身不會變成接收或驗收。

- 每個治理範圍保留一條接收基線，並為並行任務登記獨立工作區。CLI 與 MCP 呼叫同一套儲存進度、彙整階段、更新工作區及已知恢復工具。
- 保留未完成工作，不必將它標為完成。檢查點儲存選定且已寫入磁碟的檔案，不包含編輯器未儲存的內容或全部對話歷史。
- 彙整階段或更新工作區前先檢查計畫。更新會保全支援範圍內的本機提交、暫存修改、工作檔案修改與新檔案；具體衝突需個別處理。
- 條件符合時重用已有恢復動作。陌生問題需要診斷，寫下一段經驗不會自動產生新的修復功能。

### 接入時完成驗收的連線

MCP 要在你使用的 AI 宿主中接通，並實際呼叫工具確認。CLI 與 MCP 提供接入方式，各宿主仍需個別驗證。Codex 是目前文件的上手範例，不代表所有 AI 平台都已經檢查。AI 能力來自宿主，TaskCarry 不自行呼叫另一套模型 API 或訓練模型。

治理視窗在原對話中提供首次驗收報告與下一步建議。宿主排程任務屬於標準對話式接入項目；wheel 本身不包含排程器，也不會自行建立宿主任務。設定回讀、手動執行與第一次自然觸發分別留證。需要宿主授權或重新載入的步驟保留到實際完成。私有遠端與網路磁碟按需啟用。

隨套件提供的 Codex 讀取適配器使用有界 App Server 唯讀方法白名單，並僅查詢狀態索引。已核對的協定版本為 `0.166.0-alpha.6`；其他版本回報相容性缺口，不靜默省略約束。讀取範圍是選定的本機來源，不代表所有帳號、雲端對話或電腦；宿主啟動可能維護快取與日誌。索引未列出不等於對話不存在，需要時使用明確授權的交接。

官方更新按所選正式/RC 通道檢查現有清單、tag 與附件中繼資料，不代表每個套件的位元組已下載，也不會安裝候選。缺少結構化清單的舊發行保留人工複核；離線檢查保留未核實。已儲存適用性判斷、實際安裝與宿主實際載入分別記錄。

私有 Git 可以儲存選定且已提交、推送的成果；遠端推送與部署屬於個別操作。[多電腦手冊](zh-TW/remote-and-multicomputer.md)介紹獨立任務分支與單一整合主機的配合，但**尚未完成真實雙電腦端到端驗證**。電腦之間不共用執行中的治理資料庫，也不自動合併本機狀態或接管未完成操作。

### 使用時需要知道的範圍

- 每個治理範圍使用一個本機控制庫和一條接收基線。工具鎖只協調工具自身操作；更新期間，其他編輯器和 Git 指令不要寫入同一接收或更新工作區，獨立工作區可以繼續各自任務。
- 檢查點最多選擇 500 條路徑，單個儲存物件上限 32 MiB，總量上限 128 MiB。較大檔案可以記錄材料參照；參照儲存位置，不等於備份了檔案內容。
- 從檢查點恢復時，會在明確標示的合成 Git 基線上重建選定的檔案層。需要完整儲存庫歷史時，也要保留 Git 備份。
- 連線涵蓋明確登記的工作區與任務，不讀取全部私人對話。專案技能指引工作方式，不增加權限，也不構成作業系統層級的安全沙盒。
- 安裝或更新工具與技能不會合併業務 Git 歷史。接收成果、將其更新到選定工作區，都使用各自需要檢查的計畫。安裝診斷說明磁碟上的檔案狀態，不證明既有宿主程序已經載入新版本。
- 工具不修復作業系統、不遷移 AI 宿主帳號、不傳送外部訊息，也不保證恢復任意外部操作。專業或業務驗收以及對外分享由你決定。

[從手冊開始](zh-TW/windows-example.md) · [持續協作](OPERATING_PRINCIPLES.md) · [驗證記錄](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc7/docs/VALIDATION.md)
