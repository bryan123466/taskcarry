# 手動安裝與轉交後備步驟

[返回對話式接入](windows-example.md) · [English](../en/manual-setup.md) · [简体中文](../zh-CN/manual-setup.md) · [命令參考](../COMMANDS.md)

僅在治理助手無法代辦某一步時使用本頁。首次安裝從[主手冊](windows-example.md)開始；既有安裝使用[更新提示詞](updating.md)。下列路徑為合成範例，依實際位置統一調整。

- [安裝或核對固定執行環境](#install)
  - [只初始化缺失的治理狀態](#governance)
- [產生並載入接入資料](#mcp)
  - [接入已登記工作台](#workbench)
  - [驗收實際視窗](#verify)
- [只轉交缺失的舊視窗上下文](#existing)
  - [確有需要時建立工作視窗](#agents)
- [中斷後繼續](#recovery)

<a id="install"></a>

## 安裝或核對固定執行環境

先核實既有安裝與治理位置，可用時從原處接續。首次安裝時先校驗整份 ZIP。官方發行套件使用同一 Release 另外提供的 `SHA256SUMS.txt`。內部審閱套件使用交付時另外提供的整包 SHA-256。用 PowerShell 的 `Get-FileHash` 讀取 ZIP 的 SHA-256，與相應的值逐位比對。校驗值缺少或不同，先核實來源再安裝。

將 ZIP 解壓縮到空位置，依實際看到的資料夾繼續。

- 如果已經有 `TaskCarry/START_HERE.md` 與 `TaskCarry/toolkit/`，直接使用這層 `TaskCarry`。工具位於 `toolkit/` 下的版本資料夾。
- 舊版 RC8 的 ZIP 解壓縮後只有 `taskcarry-0.2.0rc8/`。使用這份舊套件時，建立空的 `TaskCarry/toolkit/`，將版本資料夾放進去。

下方指令假設外層為 `C:/TaskCarry`。若你使用其他位置，請將所有範例路徑一起換成實際路徑。版本資料夾裡應有 `RELEASE_MANIFEST.json`、`packages/`、`docs/` 與 `skills/`。執行需要 Python 3.11+。Git 保存還需要 Git，一般檔案讀取可以獨立進行。

以下指令在 PowerShell 執行，**僅用於專用 runtime 尚不存在的情況**。安裝工具不建立新的業務專案，也不表示獲准升級既有執行環境。

下方指令再將內建 wheel 與版本資料夾中的 `RELEASE_MANIFEST.json` 比對。紀錄缺失、不唯一、大小或 SHA-256 不符時，指令在建立 runtime 前停止。這項檢查驗證套件內部一致性。發行者身分仍取決於套件與整包校驗值的來源。

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $taskcarryProductRoot = 'C:/TaskCarry/toolkit/taskcarry-0.2.0'
    $taskcarryManifest = Get-Content -LiteralPath (Join-Path $taskcarryProductRoot 'RELEASE_MANIFEST.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskcarryWheels = @(Get-ChildItem -LiteralPath (Join-Path $taskcarryProductRoot 'packages') -Filter '*.whl' -File)
    if ($taskcarryWheels.Count -ne 1) { throw 'Expected exactly one wheel in the selected product package.' }
    $taskcarryWheel = $taskcarryWheels[0]
    $taskcarryExpected = @($taskcarryManifest.files | Where-Object { $_.path -ceq ('packages/' + $taskcarryWheel.Name) })
    if ($taskcarryExpected.Count -ne 1 -or $taskcarryExpected[0].sha256 -notmatch '\A[0-9a-fA-F]{64}\z') { throw 'Missing or invalid wheel checksum in RELEASE_MANIFEST.json.' }
    $taskcarryActual = (Get-FileHash -LiteralPath $taskcarryWheel.FullName -Algorithm SHA256).Hash
    if ($taskcarryExpected[0].bytes -ne $taskcarryWheel.Length -or $taskcarryActual -ne $taskcarryExpected[0].sha256) { throw 'Wheel verification failed. Stop and obtain the correct product package.' }
    if (Test-Path -LiteralPath 'C:/TaskCarry/runtime') { throw 'Runtime already exists. Return to governance for inspection; do not reinstall.' }
    py -3 -m venv 'C:/TaskCarry/runtime'
    if ($LASTEXITCODE -ne 0) { throw 'Runtime creation failed. Inspect its actual state before continuing.' }
    & 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m pip install --no-index --no-deps $taskcarryWheel.FullName
    if ($LASTEXITCODE -ne 0) { throw 'Package installation failed. Inspect its actual state before continuing.' }
    & 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' doctor
}
```

control 尚未初始化時，doctor 回傳 `NOT_INITIALIZED`，不含執行環境細節；僅此結果不表示安裝失敗。治理依下節核實這個 control 確實沒有狀態並初始化後，再執行同一條 doctor 指令查看實際執行環境與前提條件。Git 能力不可用時結合目前操作判斷；不要為了清除提示重建已有狀態。將輸出交回治理視窗，繼續同一次接入。

<a id="governance"></a>

### 只初始化缺失的治理狀態

治理先檢查既有任務、目錄與歷史成果。這個 control 確實沒有狀態時，`init` 才為它建立治理狀態；這不會建立接收基準，也不證明業務專案是新的。讓治理依[命令參考](../COMMANDS.md)的實際 `init`、`workspace`、`task` 合同操作，保留既有身分。

可選的[新專案腳手架](../../examples/windows_quickstart)只用於已確認的新專案，預設專業工作區數量為零。它拒絕已有目標；中斷後核對實際效果，不刪除目錄重跑。既有專案採用真實歷史與基準。

<a id="mcp"></a>

## 產生並載入接入資料

將審閱後的 JSON 請求儲存為 UTF-8 檔案 `C:/TaskCarry/setup-request.json`，這是範例輸入檔案，不是資料庫。治理目錄的初始內容為 `{"mode":"preview"}`。執行：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' setup --input 'C:/TaskCarry/setup-request.json'
```

檢查擬變更檔案與衝突。在已授權接入範圍內，只將 `mode` 改為 `install`，再執行相同指令。中斷續辦保留原候選與參數；setup 保全使用者改過的檔案並報告衝突。

產生的 `.taskcarry/codex.mcp.toml` 是**片段**。在 Codex 中，將選定的 `[mcp_servers.<name>]` 表合併到目標聊天的專案級 `.codex/config.toml`：治理目錄為 `C:/TaskCarry/.codex/config.toml`，專業工作台為 `<已登記工作台>/.codex/config.toml`。保留其他設定與服務，不覆蓋整份檔案或修改全域設定。保留產生的 command/args：它們綁定固定解譯器，使用隔離 UTF-8 啟動並指定套件來源。

先核對原對話的實際工作目錄與設定所在目錄一致，並由治理提供該目錄的完整路徑。已在正確目錄的原對話直接沿用，保留歷史和原任務身分。若宿主尚未開啟並信任該目錄，依以下步驟補齊：

1. 在目前 Windows Codex 按 **Ctrl+O**；其他介面選擇「開啟／新增專案資料夾」。
2. 選擇治理提供的完整**原目錄**，不建立替代目錄，不複製檔案，**不新增對話**。
3. 出現信任提示時核對目錄後確認；沒有出現提示則記錄這一情況。
4. 回到治理對話，回覆「已開啟指定目錄」，並說明信任提示是否出現、是否已確認。治理依宿主支援的方式將原對話關聯到該專案，核對原對話身分、實際 cwd 和設定。
5. 治理確認本次所有目標目錄的設定與關聯已準備好後，先儲存正在進行的工作，**結束並重新開啟 Codex 一次**，讓尚未載入的新連線生效。不必每個目錄重新啟動一次；已經原生驗收通過的連線略過此步。
6. 回到原治理對話回覆「已重新啟動」，再回到各個原工作對話，依下節分別呼叫原生 `taskcarry_doctor`、`taskcarry_status`。不要新增替代對話或重新安裝。

這讓宿主登記並信任設定所在的原專案目錄，保留原對話與同一 control。本次 Windows Codex 驗證中，信任及關聯完成後仍回傳工具未載入，重新啟動後原生呼叫成功，所以此路線把重新啟動列為明確步驟。其他宿主依其支援的方式載入；已經成功的連線無需重複處理。隨後依[原生驗收](#verify)核對實際版本、解譯器、模組、control、原任務和最新檢查點。側欄關聯或重新啟動完成不能代替這些回執；仍失敗時保留原始錯誤，由治理只排查目前缺口。

未掛在專案下的原對話，先核對實際 cwd，優先依宿主能力關聯同一目錄並保留原歷史。這個標籤不表示一定沒有 MCP；使用者級或專案級設定、外掛都可能提供連線，應查看實際工具，不自動改寫使用者級設定。目錄不相符時，先由治理核對宿主支援的關聯或保留歷史的接續方式，仍使用同一 control。把設定寫在另一目錄不會讓目前對話自動連線。setup 不選擇宿主目錄、不授予信任，也不重載宿主。操作入口以目前宿主為準，參考官方 [MCP 設定](https://learn.chatgpt.com/docs/extend/mcp?surface=app)與[設定層級](https://learn.chatgpt.com/docs/config-file/config-basic)。

Skills 位於 `.agents/skills/`，包括引用的方法檔案；未被自動發現時，明確讀取該目錄下需要的 `SKILL.md` 及引用。新 worktree 不會自動繼承另一目錄的設定。每個目標視窗依下節分別驗收，設定檔案或獨立 stdio 程序成功均不證明原生宿主已載入。

<a id="workbench"></a>

### 接入已登記工作台

先依真實目錄分組，復用原 control 中的工作區登記。多個活躍對話共用一個業務目錄時，目錄共享連線與 Skills，各對話仍使用自己的原任務。以下是**合成請求範例**，不是要求建立範例目錄或任務：

```json
{"mode":"preview","binding_mode":"directory","target":"<existing-project-directory>","workspace":"drone"}
```

`directory` 模式提供 `target`、`workspace` 並省略 `task_id`，避免把目錄裡的所有對話固定到一個任務。target 須符合登記工作區及其目前 Git 身分。儲存核對過的請求後執行上面的預覽指令；審閱後將同一請求的 `mode` 改為 `install`。`connect` 計畫沿用 `binding_mode: "directory"` 和同一目標，`--project` 始終指向原 control。

既有單任務綁定仍可使用預設 `task` 模式，同時提供 `target`、`workspace`、`task_id`；任務須存在於同一 control。例如：

```json
{"mode":"preview","target":"<existing-project-directory>","workspace":"drone","task_id":"drone-software"}
```

setup 寫入目錄的四項 Skills 及引用、MCP 片段和工作台資料，不建立對話、任務或另一資料庫。共享目錄的工作台計畫使用 `routing: "shared"`，每個目標保留真實 `thread_id` 與原 `task_id`。目前視窗依自己的真實對話身分讀取入口，不能用目錄中的第一個任務代替；每個原對話分別驗收與記錄實際讀取。只有並行寫入確實存在衝突時，才考慮獨立 Git 工作樹。

僅作歷史來源的對話不需要原視窗的 MCP 或 Git 設定。普通文件目錄也可用綁定 control 的 CLI 儲存 checkpoint，不為儲存文件偽造 Git 登記。

<a id="verify"></a>

### 驗收實際視窗

宿主載入後，在該視窗呼叫原生 `taskcarry_doctor` 與 `taskcarry_status`，將實際版本、解譯器、模組、control 及相關任務/工作區/檢查點與綁定資料核對。存在多個服務時選對服務。命令列成功不能證明原生工具已經暴露。

MCP 不可用時保留原始錯誤或工具缺失事實，可用固定隔離 CLI 繼續已授權工作：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' doctor
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' status
```

這項證據標為 CLI，原生連線繼續保留為待驗收。更新工具時先預覽並安裝受管理檔案，再檢查實際宿主設定與重新載入；安裝版本變化不代表執行中的服務已變化。解除安裝只移除未被使用者改動的受管理檔案，保留已修改檔案、治理資料與手動合併的生效設定。

<a id="existing"></a>

## 只轉交缺失的舊視窗上下文

僅在治理無法直接讀取獲准的相關歷史時使用，不重新開始原任務。向**原工作視窗**傳送：

```text
請為目前工作接入 TaskCarry 準備最小交接。讀取現行指令與實際檔案，說明專案/任務及已知穩定身分、真實工作目錄、適用時的 Git 根/分支/HEAD/WIP、有來源的有效決定、已完成成果及已知接收情況、準確未完成位置與下一步。區分事實、最後已知資訊、建議與缺口。保留原工作與歷史；本次摘要不要修改檔案、登記任務或製造交付。
```

把回覆交給**治理視窗**，同時傳送：

```text
請將這份交接接入現有專案，核對引用來源與真實歸屬，重用已知任務/control 身分並保全 WIP。已納入基準的成果不重複排隊。依接入授權補齊缺失登記與連線步驟，給我一份可直接貼回原視窗的接續內容，填好核實過的 control、執行環境、任務/工作區、Skill 位置與下一步，說明尚未驗收的部分。
```

將治理填好的內容貼回原視窗。連線檢查應讀取相關 Skills、任務與有效決定，然後從原下一步繼續。人工轉交是後備，不是每次工作的必經步驟。

<a id="agents"></a>

### 確有需要時建立工作視窗

確認有價值的分工後，治理給出準確目錄、職責、任務身分與接續內容。無法原生建立對話時，由你在該目錄開啟視窗並貼上已填內容。新增專業視窗可以為零。每個任務與寫入範圍保留一個主要寫入者，移動工作前先核對共目錄衝突。

<a id="recovery"></a>

## 中斷後繼續

可以說「請從接入清單繼續，先核對實際已經發生的結果」。保留原 setup 候選與操作身分。檔案產生、CLI 檢查成功或儲存排程提示詞只證明各自步驟；使用者改過的檔案與恢復目標要保全，不覆蓋現場換取順利重試。

普通 checkpoint 首次恢復到獨立空目錄。若恢復已產生效果、最終回執失敗，應由支援的恢復邏輯核驗原效果並補缺失記錄，不手動清空目標。具體以所安裝版本的恢復 Skill 為準。

## 手動一步之後，回到完整建制清單

每次後備操作後都回原治理視窗、沿同一接入身分繼續。`init` 前先 `identify`，未知或不支援的狀態保留。舊本機路徑身分先顯示明確 `identity` 計畫再採用持久身分；唯讀狀態不會代做。

完成登記工作台 `setup` 後，用審閱過的 `connect` 計畫合併專案 MCP 設定，再用 `workbench` 凍結和發布選定治理 view。目標應是被 Git 忽略的私有入口，保留自訂指令及其他服務。由實際工作視窗讀取 current/view、原任務和 checkpoint，原生呼叫 doctor/status 並給出相符證據；寫了設定不等於信任/重載已完成。精確合同見[治理 API](../GOVERNANCE_API.md)，不要臨時改資料庫。

補齊本機 Git 與核實作者設定、精確 `preserve` 儲存、官方來源登記/檢查/評估、首次有界整輪和獨立恢復演練。透過宿主設定一個早晨報告加一到兩個吸收時段，並準確回讀，用 `complete_v1` 明確剩餘標準項。設定、自然觸發、AI 執行和報告送達分別說明；私有遠端/網路硬碟可選。[回饋範例](user-feedback-examples.md)展示完成報告。

獨立恢復副本預設 standby。恢復回執中的 `disabled_host_files` 指明被隔離的舊機器連線設定：內容作為證據保留，不直接啟用；按目標路徑重新產生後核驗原生綁定，明確舊寫入者停寫後才移交。選定檢查點檔案恢復小於完整所選恢復集，詳見[恢復參考](remote-and-multicomputer.md)。
