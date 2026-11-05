# TaskCarry 0.2.0rc7 — complete candidate / 完整候选 / 完整候選

[Product entry / 使用入口 / 使用入口](../START_HERE.md) · [Capabilities and limits / 能力范围 / 能力範圍](RELEASE_BOUNDARIES.md) · [Validation / 验证 / 驗證](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc7/docs/VALIDATION.md)

## 简体中文

本页描述相对已发布 RC6 的完整 RC7 候选，包含此前整理的安装／更新双入口及本次治理内核增强。**本候选尚未公开发布，也未标为正式稳定版。** 具体源码、包和验证对象以最终复核报告为准；预定发行链接不表示已经能够下载。

### 新用户与已有用户分别怎么用

新用户取得完整包后按三步操作：建立独立治理窗口并发送一条主提示词；由总控继承已有项目并带领配置；查看真实验收报告和下一步建议。无需先安装旧版，也无需阅读历史升级过程。

已有用户回到原治理窗口，发送[更新提示词](zh-CN/updating.md)。助手核对当前包、治理材料、用户规则和已配置项目，只更新需要更新的部分。保留原任务、决定、成果、Git 未完成修改和宿主配置；遇到定制冲突时展示差异，不能直接覆盖。缺少的标准配置在原接入流程内续办，已经完成的部分无需重建。

### 本次完整修改

1. **从安装步骤转为完整的治理接入。** RC6 已能生成接入材料；本次把项目范围、来源、工作窗口和验收项目保存为可接续清单。总控先理解已有成果与分工，再提出线程建议。一个现实项目可包含多个目录、仓库和状态来源，记录保留来源身份；仅作历史参考的聊天不必变成活跃工作台。用户仍可直接在专业窗口工作，长期项目协调按需选择。
2. **专业窗口配置与实际目录核对更明确。** 持续工作的窗口需要真实任务、职责、工作目录与 Git 关系。已有仓库优先复用，需要并行修改时安排真实隔离；没有项目目录的旧对话按宿主能力关联或由新工作窗口承接。生成配置、实际加载和窗口内工具调用分别核验；给窗口写一个名字或路径不算接入完成。项目配置合并检查原文件和预览结果，保留已有配置与用户文件。
3. **增加项目识别和有界任务上下文。** 初始化前先识别已有状态，未知、损坏或不支持的格式拒绝写入。指定任务的上下文集中返回相关检查点、下一步、观察、阶段与问题证据，带来源、分页及变化指纹；无关任务变化不应使当前任务的分页失效。读取不会创建交付、改变任务状态或表示业务验收。
4. **补齐普通资料的继承。** 原有普通目录中的资料可明确关联到任务，保留指定文件检查点和恢复能力。它们不必先整体搬入新仓库；持续工作窗口的标准 Git 配置仍要完成。Git 接收与采用继续只适用于经过真实校验的 Git 工作流。
5. **随包提供 Codex 历史读取适配器。** 除可用的宿主工具外，CLI 与 MCP 可通过同一适配器检测能力、列出所选来源的对话、分页读取指定历史。调用使用只读方法白名单、输出上限和输入／输出超时，不开始 AI turn，不恢复执行旧对话。已核对的协议版本是 `0.166.0-alpha.6`；其他版本保留兼容性缺口和最小交接路径。索引未列出不证明对话不存在，宿主启动可能维护缓存与日志。
6. **本地 Git 保存成为标准配置。** 原先需要助手自行编排的选定治理文件保存，本次增加可预览、可执行并核对回执的精确保存流程。仅提交明确选定内容，保全原 Git 暂存区和未完成工作；无变化不产生空提交，中断后先核效果再续办。Git 作者信息、工作区身份和任务责任分别核对。大文件可保存在外部，引用、实体备份、上传和恢复结果分别记录。
7. **官方更新发现与采用判断进入治理。** 登记官方来源、正式／RC 通道和当前精确制品；有界查询发行信息，校验结构化清单、tag 提交及附件元数据，显式保存适用性判断。离线、旧发行缺少清单、同版本内容冲突均保留真实状态。发现新版本不会自动安装；检查结果、维护决定、实际安装和宿主重载分别记录。新增结构化发行清单由最终制品生成，避免把清单自身哈希写进自身。
8. **定时治理成为标准接入项目。** 总控准备返回原治理聊天的调度计划，包含读取相关进度、核对实际效果、维护项目记忆、本地保存、官方更新检查及结果报告。调度由宿主的真实能力建立或复用，Core 不另建常驻模型服务。频率、时区、原聊天和运行条件要回读；配置完成、手动试跑和第一次自然触发分别留证。没有变化不造任务、版本或重复提醒。
9. **区分公共内核、通用方法与用户规则。** 新增治理运行身份与明确规则文件的核对记录，区分当前工具包、Skills、项目自定规则及来源。公共方法更新不覆盖用户决定；记录了修正版不等于用户已经安装。四项 Skills 统一采用“先核实际效果、定位原问题、验证修正、记录采用、续办原操作”的方法。
10. **重新整理三语文档与包内资源。** 主手册保持三步、一条主提示词、完整交互示例和完成标准；手动命令与异常后备独立，已有用户更新独立。主入口、README、操作手册、四 Skills、示例及构建允许清单保持一致。私有远端和网盘按需配置，原有多电脑参考保留，未将其扩展为自动跨机治理。

### 必要操作与兼容说明

- 新用户按主提示词完成标准本地 Git、所选专业窗口接入、原治理窗口调度和官方更新检查。需要信任、重载或宿主确认时，助手只给当前操作。
- 已有用户由原治理窗口核对具体更新对象，在独立候选运行环境验证后再按授权安装，更新受管材料并核对宿主实际加载。旧状态继续保留；需要派生索引更新时使用明确工具操作，不重新初始化项目。
- `taskcarry upgrade` 是状态派生索引的更新动作，不是安装新版包的命令。软件包安装、业务 Git 接收／采用和用户业务验收是不同操作。
- RC6 的隔离启动、普通文件保存和恢复回执续办继续保留；不要求重做已经完成的历史迁移或修正。

### 验证与仍需如实报告的限制

源码回归、合成资料、实际构建包、独立 App Server／stdio、原生 MCP 和自然定时触发分别列证据。本页不提供未形成的最终测试数字或包哈希。**本候选的原生 MCP 接入与自然 heartbeat 仍等待相应实际验收**，不能用命令行成功代替；最终状态由复核报告更新。

Codex 读取适配器只声明已核对协议范围；系统配置、索引完整性和实际宿主能力可能影响接入。正式更新查询的附件元数据校验不等于下载全部包的字节校验。完整治理库跨机迁移、分布式写入、任意云盘接口和通用自动回退引擎不在本次范围。公开发行、用户安装和实际采用分别确认。

## English

This complete RC7 candidate is compared with published RC6. It includes the separate installation/update routes and the governance-core changes below. **It has not been publicly released or designated stable.** The final review identifies the exact source, artifacts and evidence; a planned release link is not an available download.

### New and existing users

New users use the complete package and three steps: establish an independent governance chat with one main prompt; let governance inherit the existing project and guide setup; review actual acceptance and next-step suggestions. There is no need to install an older version first.

Existing users return to their original governance chat with the [update prompt](en/updating.md). The assistant checks package, maintained methods, custom rules and connected work, updates only what is needed, preserves tasks, decisions, outputs, Git work in progress and host settings, and exposes customization conflicts. Missing standard items continue from the original checklist rather than rebuilding completed setup.

### Complete changes

1. **Guided governance onboarding.** Beyond generating integration files, onboarding now retains scope, sources, selected working windows and acceptance progress. Governance understands existing work before suggesting responsibilities. One real project may span several directories, repositories and state sources with distinct identities. Reference-only chats can remain sources. Users continue working directly in their professional chats; ongoing project coordination stays optional.
2. **Real workbench and connection checks.** Active windows need task/responsibility, actual directory and Git relationships. Reuse existing repositories; prepare genuine isolation for concurrent writing. A chat without a suitable directory is associated through supported host actions or handed over to a correctly located working chat. Generated configuration, host loading and actual native calls are separate. Project-config merging checks the preview and original bytes while retaining other settings and user files.
3. **Safe identification and bounded task context.** Unknown, damaged and unsupported state is identified before initialization writes. A task-specific reader gathers related checkpoints, next steps, observations, stages and issue evidence with source identity, pagination and fingerprints. Unrelated task changes should not invalidate its page. Reading does not deliver work, change task status or accept business results.
4. **Continuity for ordinary materials.** Material sources in ordinary directories can bind explicitly to a task while retaining selected-file checkpoint/restore support. Existing materials need not move into a new repository. Standard Git setup still applies to active workbenches; receiving and adopting Git changes retain their real Git constraints.
5. **Packaged Codex history adapter.** Shared CLI/MCP access can inspect capability, list a selected local source and page a named conversation. The adapter uses read-method allowlists, byte limits and input/output deadlines; it starts no AI turn and does not resume execution. The verified protocol version is `0.166.0-alpha.6`; other versions return a compatibility gap and handoff fallback. Missing index entries do not prove absent conversations, and host startup may maintain caches or logs.
6. **Standard local Git preservation.** Selected governance-file saving now has explicit preview, execution and verified receipts. It commits only named content, preserves the original index and unfinished work, makes no empty commit, and checks existing effects before recovering an interrupted receipt. Git authorship, workspace identity and task responsibility remain distinct. External large files retain separate reference, backup, upload and restore evidence.
7. **Official update discovery and assessment.** Register the official source, stable/RC channel and current artifact identities. Bounded release checks verify the structured manifest, resolved tag commit and asset metadata; an explicit action saves applicability decisions. Offline checks, legacy releases without manifests and same-version conflicts remain visible. Discovery does not install software. Checks, maintenance decisions, installation and host reload remain distinct. A structured release manifest is generated from final artifacts without a self-referential hash.
8. **Original-chat scheduled governance.** Standard setup prepares a host schedule returning to the original governance chat for focused progress review, effect verification, memory, local saving, official update checks and reporting. The host creates or reuses the actual schedule; Core starts no resident model. Verify time zone, frequency, target chat and prerequisites. Configuration, manual execution and the first natural trigger have different evidence. No change creates no artificial task, version or repeated reminder.
9. **Core, maintained methods and custom rules.** Governance identity records distinguish package, Skills, explicit project-rule files and their sources. Shared-method updates preserve user decisions. Recording a fixed version does not prove installation. The four Skills use a common recovery sequence: verify effects, identify the original problem, test the fix, record adoption and continue the original operation.
10. **Aligned three-language documentation and artifacts.** The main manual presents three steps, one prompt, a complete conversation example and acceptance criteria. Manual commands/fallbacks and existing-user updates are separate. Entrypoints, README files, manuals, four Skills, examples and package allowlists align. Private remotes and cloud storage remain optional; existing multi-computer guidance is retained without claiming automatic cross-host governance.

### Required actions and compatibility

New users finish local Git, selected workbench connections, the original governance chat's schedule and official update checks through the guided setup. Host trust, reload or confirmation is requested at the relevant step.

Existing users review the exact update in their original governance chat, validate a separate candidate runtime, install within their authorization, update managed materials and verify actual host loading. Keep the original project state; update derived indexes explicitly when required. `taskcarry upgrade` updates state indexes, not the installed package. Package maintenance, business Git reception/adoption and business acceptance remain separate. RC6 isolation, ordinary-file checkpoints and restore-receipt recovery remain included; completed migrations are not repeated.

### Verification and limits

Source regressions, synthetic data, built artifacts, independent App Server/stdio, native MCP and natural scheduled triggers have separate evidence. Final test counts and hashes belong to the exact candidate review. **Native MCP acceptance and a natural heartbeat for this candidate still await their actual verification**; CLI success cannot substitute for either.

Codex support is limited to the verified protocol and actual host configuration/index availability. Release asset-metadata checks are not full package-byte downloads. Full cross-host state migration, distributed writing, arbitrary cloud-storage integrations and a general automatic rollback engine are outside this candidate. Publication, installation and actual adoption remain distinct.

## 繁體中文

本頁描述相較已發行 RC6 的完整 RC7 候選，包含此前整理的安裝／更新雙入口及本次治理核心增強。**本候選尚未公開發行，也未定為正式穩定版。** 具體原始碼、套件與驗證對象以最終複核報告為準；預定發行連結不表示已經能夠下載。

### 新使用者與既有使用者分別如何使用

新使用者取得完整套件後按三步操作：建立獨立治理視窗並傳送一段主提示詞；由總控繼承既有專案並帶領設定；查看真實驗收報告與下一步建議。無需先安裝舊版，也無需閱讀歷史升級過程。

既有使用者回到原治理視窗，傳送[更新提示詞](zh-TW/updating.md)。助手核對目前套件、治理材料、使用者規則及已設定專案，只更新需要更新的部分。保留原任務、決定、成果、Git 未完成修改與宿主設定；遇到自訂衝突時展示差異，不能直接覆寫。缺少的標準設定在原接入流程內續辦，已完成部分無需重建。

### 本次完整修改

1. **從安裝步驟轉為完整治理接入。** 除產生接入材料外，本次把專案範圍、來源、工作視窗與驗收項目儲存為可接續清單。總控先理解既有成果與分工，再提出執行緒建議。一個現實專案可包含多個目錄、儲存庫及狀態來源，記錄保留來源身分；僅作歷史參考的對話不必變成活躍工作台。使用者仍可直接在專業視窗工作，長期專案協調按需選擇。
2. **專業視窗設定與實際目錄核對更明確。** 持續工作視窗需要真實任務、職責、工作目錄與 Git 關係。優先重用既有儲存庫，並行修改時安排真實隔離；沒有專案目錄的舊對話按宿主能力關聯或由新工作視窗承接。產生設定、實際載入與視窗內工具呼叫分別核驗；寫一個名稱或路徑不算接入完成。專案設定合併檢查原檔案與預覽結果，保留既有設定和使用者檔案。
3. **新增專案識別與有界任務上下文。** 初始化前識別既有狀態，未知、損壞或不支援的格式拒絕寫入。指定任務的上下文集中傳回相關檢查點、下一步、觀察、階段及問題證據，附來源、分頁與變更指紋；無關任務變更不應使目前任務分頁失效。讀取不建立交付、不變更任務狀態，也不表示業務驗收。
4. **補齊一般資料的繼承。** 原有一般目錄中的資料可明確關聯到任務，保留選定檔案檢查點及恢復能力。資料不必先整體搬入新儲存庫；持續工作視窗的標準 Git 設定仍須完成。Git 接收與採用繼續只適用於經真實校驗的 Git 工作流程。
5. **隨套件提供 Codex 歷史讀取適配器。** 除可用宿主工具外，CLI 與 MCP 可透過同一適配器偵測能力、列出選定來源的對話、分頁讀取指定歷史。呼叫使用唯讀方法白名單、輸出上限與輸入／輸出逾時，不開始 AI turn、不恢復執行舊對話。已核對的協定版本為 `0.166.0-alpha.6`；其他版本保留相容性缺口與最小交接路徑。索引未列出不證明對話不存在，宿主啟動可能維護快取與日誌。
6. **本機 Git 儲存成為標準設定。** 本次新增可預覽、可執行並核對回執的精確治理檔案儲存流程。僅提交明確選定內容，保全原 Git 暫存區與未完成工作；無變更不產生空提交，中斷後先核效果再續辦。Git 作者資訊、工作區身分與任務責任分別核對。大型檔案可儲存在外部，參照、實體備份、上傳與恢復結果分別記錄。
7. **官方更新探索與採用判斷進入治理。** 登記官方來源、正式／RC 通道與目前精確製品；有界查詢發行資訊，校驗結構化清單、tag 提交及附件中繼資料，明確儲存適用性判斷。離線、舊發行缺少清單、同版本內容衝突均保留真實狀態。發現新版不會自動安裝；檢查結果、維護決定、實際安裝及宿主重新載入分別記錄。結構化發行清單由最終製品產生，避免將清單自身雜湊寫入自身。
8. **排程治理成為標準接入項目。** 總控準備返回原治理對話的排程計畫，包含讀取相關進度、核對實際效果、維護專案記憶、本機儲存、官方更新檢查與結果報告。排程由宿主真實能力建立或重用，Core 不另建常駐模型服務。頻率、時區、原對話與執行條件須回讀；設定完成、手動試跑及第一次自然觸發分別留證。沒有變更不造任務、版本或重複提醒。
9. **區分公共核心、通用方法與使用者規則。** 新增治理執行身分及明確規則檔案的核對記錄，區分目前工具套件、Skills、專案自訂規則與來源。公共方法更新不覆寫使用者決定；記錄修正版不等於使用者已經安裝。四項 Skills 統一採用「先核實際效果、定位原問題、驗證修正、記錄採用、續辦原操作」的方法。
10. **重新整理三語文件與套件資源。** 主手冊保持三步、一段主提示詞、完整互動範例與完成標準；手動指令及異常後備獨立，既有使用者更新獨立。主入口、README、操作手冊、四 Skills、範例與建置允許清單一致。私有遠端及網路磁碟按需設定，原有多電腦參考保留，未擴充為自動跨機治理。

### 必要操作與相容說明

新使用者透過主提示詞完成標準本機 Git、選定專業視窗接入、原治理視窗排程及官方更新檢查。需要信任、重新載入或宿主確認時，助手只提供目前操作。

既有使用者由原治理視窗核對具體更新對象，在獨立候選執行環境驗證後再按授權安裝，更新受管材料並核對宿主實際載入。舊狀態繼續保留；需要衍生索引更新時使用明確工具操作，不重新初始化專案。`taskcarry upgrade` 是狀態衍生索引更新，不是新版套件安裝指令。套件安裝、業務 Git 接收／採用與使用者業務驗收分開處理。RC6 隔離啟動、一般檔案儲存及恢復回執續辦繼續保留，不重做已完成的歷史遷移或修正。

### 驗證與仍須如實回報的限制

原始碼回歸、合成資料、實際建置套件、獨立 App Server／stdio、原生 MCP 及自然排程觸發分別列證據。本頁不提供未形成的最終測試數字或套件雜湊。**本候選原生 MCP 接入與自然 heartbeat 仍等待相應實際驗收**，不能以命令列成功代替；最終狀態由複核報告更新。

Codex 讀取適配器僅聲明已核對協定範圍；系統設定、索引完整性與實際宿主能力可能影響接入。官方附件中繼資料校驗不等於下載全部套件的位元組校驗。完整治理庫跨機遷移、分散式寫入、任意網路磁碟介面及通用自動回退引擎不在本次範圍。公開發行、使用者安裝與實際採用分別確認。
