# TaskCarry 0.2.0rc6 candidate

This candidate follows the published **0.2.0rc5**. It is prepared for review; a local build or source-stage receipt does not mean it has been publicly released, installed in an existing project or loaded by a host. Historical rc6.dev1 notes describe the earlier isolated-launch development stage only. Existing published downloads remain unchanged until the reviewed release is approved.

## English

### Connect an existing project in one guided conversation

The recommended Windows/Codex guide now starts with a distinct governance chat, reusing a verified existing one when available. One prompt combines installation, project handover and governance responsibility. It asks the assistant to recover relevant existing outcomes, decisions, tasks and unfinished work, then guide the remaining connection. Users continue working directly in their original chats. Project coordination is optional; advice on responsibilities or next steps does not automatically enable dispatch, schedules or extra chats. A small project can keep its existing work chat with zero additional specialists.

The main guide has three nested sections and one starting prompt. Manual installation, fallback handoff prompts, MCP configuration and troubleshooting move to a separate guide in all three languages. Existing links/anchors remain available. README, START_HERE, daily-operation indexes and the four public Skills follow the same flow. A packaged onboarding reference explains inherited facts versus proposals, effective decisions, sources, a resumable checklist and short user teaching.

### Bind professional workbenches to one control

CLI setup can now place connection materials in a registered workbench while MCP remains bound to the original control. Supply `target`, `workspace` and `task_id` together. It validates the existing task and the current registered Git identity, previews changes, then installs four Skills with their public references, a configuration fragment and private workbench binding notes. It does not initialize another control, create chats or edit active/global host configuration. Existing user files and modified managed files remain protected; interrupted installation resumes with the same binding and package.

Returned connection state distinguishes materials generated from host loading and actual native tool calls. The latter two remain unverified until checked in the target chat. Registered workbench setup and Git delivery require Git; the ordinary document checkpoint feature below does not require a Git repository.

### Save and restore work more reliably

- Generated MCP launch commands now select the fixed interpreter and package with isolated UTF-8 startup. A source checkout used as the working directory, or an inherited import environment, cannot silently replace the selected installed package. Missing selected packages fail explicitly. Existing activated host configuration must be reviewed/reloaded separately after managed setup is updated.
- Plain-directory checkpoints now work without the Git executable. Repository metadata and repository ancestors still require real Git verification and the exact workspace root. Unreadable, damaged, bare or redirected metadata is not silently treated as ordinary files.
- Restore now records an intent before writing, verifies its destination and Git/file effects, then publishes completion, receipt and event together. If the final receipt fails, retrying the same checkpoint/destination verifies the saved effect and only completes that receipt. It does not rewrite files or duplicate events. Later user changes, extra paths, changed Git metadata and replaced destinations are preserved and require review.
- A selected governance run can recognize a completed restore through its matching durable receipt. This describes a historical completed operation, not current business acceptance or a fresh filesystem audit.

An interrupted restore without durable complete-effect evidence remains an explicit review case, even if some files appear correct. Old checkpoints remain usable; old failed restores without an intent cannot be retroactively certified. This release does not implement general non-Git result reception, task revision/CAS, incremental context subscription or verified multi-computer collaboration.

### Package and verification changes

Upgrade and rollback are different operations. RC6 can read older checkpoints and upgrade an rc5 managed setup. Its added managed resource paths are not understood by rc5 setup, so downgrading only the wheel is insufficient. Keep a reviewed matching package, managed-file/manifest and host-configuration set before an upgrade; preserve later user changes and control records when reviewing rollback. See the maintenance guide for this boundary. Installed-runtime command examples also use isolated startup consistently.

The positive build allowlist includes the three fallback manuals and the public onboarding reference. Standard wheels and source distributions include that reference, and setup carries it to the workbench. Tests exercise actual CLI/MCP subprocesses, user-file preservation, repeated/interrupted setup, restore failures, and single-chat/multiple-chat synthetic projects. Exact source results, installed-wheel checks, skipped cases and remaining host/CI limits are recorded separately in the source repository's validation records and the candidate review report. No production project or scheduled task is used as a test fixture.

## 简体中文

### 一次对话接入已有项目

新版推荐手册先引导建立独立治理窗口；已有经核实的治理总控时直接复用。一个提示词合并安装、项目接手和治理职责，让 AI 从获准来源继承成果、决定、任务与未完成位置，并带领完成后续接入。用户仍可直接在原工作聊天推进；是否长期兼任项目总控由用户选择。分工建议不会自动启用派工、调度或额外聊天，简单项目可以新增零个专业窗口。

主手册收敛为三个有层级的部分和一条起步提示词。手动安装、人工转交、MCP 配置与排错移至三语独立后备手册，保留旧链接/锚点。README、START_HERE、日常操作索引及四项 Skills 同步；随包提供接入方法引用，说明事实与建议、有效决定、来源、中断清单及简短使用教学。

### 专业工作台共用原治理库

CLI setup 新增成组的 `target`、`workspace`、`task_id`，将材料安装到专业工作目录，MCP 仍指向原 control。它核对已有任务与工作区当前 Git 身份，先预览再安装四 Skills、公开引用、配置片段和私有绑定说明。不会另建 control、创建聊天或修改已启用/全局宿主配置。用户文件和受管文件中的用户修改继续保全；同一绑定和包可续办中断安装。

返回值区分材料生成、宿主加载和原生实调，后两者必须在目标窗口真实验收。专业工作台登记与 Git 交付仍要求 Git；普通文档检查点不因此要求仓库。

### 保存与恢复的修正

- 生成的 MCP 启动默认采用固定解释器、明确包路径和隔离 UTF-8 参数，避免源码工作目录或环境变量遮蔽正式安装包。选定包缺失时明确失败；已有启用配置仍需另行审阅和重载。
- 普通目录没有 Git 可执行文件也能保存检查点。存在仓库元数据或仓库祖先时仍严格核验 Git 与准确根目录，不把损坏、不可读取、裸仓库或重定向的元数据降为普通文件。
- 恢复操作先记录意图，核验文件/Git 效果后一次事务写入完成状态、回执和事件。最后回执失败时，同一目标重试只核验和补回执，不重复写文件。后来用户修改、额外路径、Git 元数据变化或目录替换均保留并要求复核。
- 治理轮次可用匹配的持久回执识别已完成恢复，不将其当成业务验收或当前文件系统重新核验。

效果证据持久化前的中断仍需复核，即使部分文件看起来正确也不重放或认领完成。旧检查点可继续使用；旧版无意图的失败恢复不能追认。本次未包含通用非 Git 成果接收、任务条件修订、增量上下文订阅或真实多机协作。

### 发行包和验证

升级与回退分别处理：RC6 可以读取旧检查点并更新 rc5 的受管安装，但 rc5 setup 不认识新增的受管资源路径，因此不能只降 wheel 就当作完成回退。升级前保留已核对的包、受管文件/manifest 和宿主配置；复核回退时保全后来的用户修改与 control 记录。维护手册明确这一边界，安装运行环境的命令示例也统一使用隔离启动。

构建允许清单补入三语后备手册与公开接入引用。标准 wheel、源码分发及工作台安装均包含该引用。回归覆盖实际 CLI/MCP 子进程、用户文件保全、重复/中断接入、恢复失败，以及单主聊天/多旧聊天合成项目。精确测试结果、真实 wheel 检查、跳过项目和宿主/CI 尚缺证据分别列于源码验证记录及候选复核报告；不用生产项目或生产定时任务做实验。

## 繁體中文

### 一次對話接入既有專案

新版推薦手冊先引導建立獨立治理視窗；已有經核實的治理總控時直接重用。一個提示詞合併安裝、專案接手與治理職責，讓 AI 從獲准來源繼承成果、決定、任務及未完成位置，再帶領完成後續接入。使用者仍可直接在原工作對話推進，是否長期兼任專案總控由使用者選擇。分工建議不會自動啟用派工、排程或額外對話，簡單專案可以新增零個專業視窗。

主手冊整理為三個有層次的部分及一條起步提示詞。手動安裝、人工交接、MCP 設定與排錯移至三語獨立後備手冊，保留舊連結/錨點。README、START_HERE、日常操作索引與四項 Skills 同步；隨套件提供接入方法引用，說明事實與建議、有效決定、來源、中斷清單與簡短教學。

### 專業工作台共用原治理庫

CLI setup 新增成組的 `target`、`workspace`、`task_id`，將材料安裝到專業工作目錄，MCP 仍指向原 control。它核對既有任務及工作區目前的 Git 身分，先預覽再安裝四 Skills、公開引用、設定片段與私有綁定說明。不另建 control、不建立對話、不修改已啟用或全域宿主設定。使用者檔案及受管檔案中的使用者修改持續保全，同一綁定與套件可續辦中斷安裝。

回傳值區分材料產生、宿主載入與原生實測，後兩者必須在目標視窗驗收。專業工作台登記與 Git 交付仍要求 Git，一般文件檢查點不因此要求儲存庫。

### 儲存與還原修正

- 產生的 MCP 啟動預設採用固定直譯器、明確套件路徑及隔離 UTF-8 參數，避免原始碼工作目錄或環境變數遮蔽已安裝套件。選定套件缺失時明確失敗；既有啟用設定仍須另行審閱與重載。
- 一般目錄沒有 Git 執行檔也能儲存檢查點。有儲存庫中繼資料或祖先時，仍嚴格核驗 Git 與正確根目錄，不將損壞、無法讀取、裸儲存庫或重新導向的中繼資料降為一般檔案。
- 還原先記錄意圖，核驗檔案/Git 效果後以同一交易寫入完成狀態、回執與事件。最後回執失敗時，同一目標重試只核驗並補回執，不重複寫入檔案。後來的使用者修改、額外路徑、Git 中繼資料變化或目錄替換均保留並要求複核。
- 治理輪次可藉匹配的持久回執識別已完成還原，不將其視為業務驗收或目前檔案系統重新核驗。

完整效果證據持久化前的中斷仍須複核，即使部分檔案看來正確也不重做或認領完成。舊檢查點仍可使用；舊版無意圖的失敗還原不能追認。本次未包含通用非 Git 成果接收、任務條件修訂、增量上下文訂閱或真實多機協作。

### 發行套件與驗證

升級與回退分別處理：RC6 可以讀取舊檢查點並更新 rc5 的受管安裝，但 rc5 setup 不認識新增受管資源路徑，不能只降 wheel 就視為完成回退。升級前保留已核對的套件、受管檔案/manifest 與宿主設定；複核回退時保全後來的使用者修改及 control 記錄。維護手冊明確說明此邊界，已安裝環境的指令範例也統一使用隔離啟動。

建置允許清單加入三語後備手冊及公開接入引用。標準 wheel、原始碼分發與工作台安裝均包含該引用。回歸涵蓋實際 CLI/MCP 子程序、使用者檔案保全、重複/中斷接入、還原失敗，以及單主對話/多舊對話合成專案。精確測試結果、實際 wheel 檢查、略過項目及宿主/CI 尚缺證據，分別列於原始碼驗證記錄與候選複核報告；不用生產專案或生產排程做實驗。
