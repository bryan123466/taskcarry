# 手動安裝與轉交後備步驟

[返回對話式接入](windows-example.md) · [English](../en/manual-setup.md) · [简体中文](../zh-CN/manual-setup.md) · [命令參考](../COMMANDS.md)

只執行治理指出的目前缺步。本頁對應 **0.2.0rc6 候選**；已發布下載仍為 [rc5](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc5)，其產品套件有對應手冊。舊執行套件不能直接使用候選新增 setup 參數。下列路徑均為合成範例，首次設定前統一替換根目錄。

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

先檢查既有安裝與 control，有效時直接重用。確實首次安裝工具時，建立 `C:/TaskCarry/control` 與 `C:/TaskCarry/toolkit`，將選定產品 ZIP 的內容直接解壓縮到 `toolkit`。原業務專案保留在原位置。需要 Python 3.11+；只有 Git 工作流程需要 Git。

以下指令在 PowerShell 執行，**僅用於專用 runtime 尚不存在的情況**。安裝工具不建立新的業務專案，也不表示獲准升級既有執行環境。

```powershell
py -3 -m venv 'C:/TaskCarry/runtime'
$taskcarryWheel = Get-ChildItem -LiteralPath 'C:/TaskCarry/toolkit/packages' -Filter '*.whl' -File
if (@($taskcarryWheel).Count -ne 1) { throw 'Expected exactly one wheel in the selected product package.' }
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m pip install --no-index --no-deps $taskcarryWheel.FullName
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' doctor
```

doctor 回傳實際執行環境與前提條件。control 尚未初始化或 Git 能力不可用，需要結合目前操作判斷；不要為了清除提示重建已有狀態。將輸出交回治理視窗，繼續同一次接入。

<a id="governance"></a>

### 只初始化缺失的治理狀態

治理先檢查既有任務、目錄與歷史成果。這個 control 確實沒有狀態時，`init` 才為它建立治理狀態；這不會建立接收基準，也不證明業務專案是新的。讓治理依[命令參考](../COMMANDS.md)的實際 `init`、`workspace`、`task` 合同操作，保留既有身分。

可選的[新專案腳手架](../../examples/windows_quickstart)只用於已確認的新專案，預設專業工作區數量為零。它拒絕已有目標；中斷後核對實際效果，不刪除目錄重跑。既有專案採用真實歷史與基準。

<a id="mcp"></a>

## 產生並載入接入資料

將審閱後的 JSON 請求儲存為 UTF-8 檔案 `C:/TaskCarry/setup-request.json`，這是範例輸入檔案，不是資料庫。治理目錄的初始內容為 `{"mode":"preview"}`。執行：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' setup --input 'C:/TaskCarry/setup-request.json'
```

檢查擬變更檔案與衝突。在已授權接入範圍內，只將 `mode` 改為 `install`，再執行相同指令。中斷續辦保留原候選與參數；setup 保全使用者改過的檔案並報告衝突。

產生的 `.taskcarry/codex.mcp.toml` 是**片段**。讓助手把指定服務合併到宿主支援的專案級設定，保留其他服務與指令。目前宿主無法代辦時，應給出準確的受支援位置與合併動作，不用一份完整設定覆蓋原設定。保留產生的 command/args：它們綁定固定解譯器，使用隔離 UTF-8 啟動並指定套件來源，不換成未限定的 Python 指令。

專案信任或宿主重新載入可能需要你操作，setup 本身不執行。Skills 位於 `.agents/skills/`，包括引用的方法檔案；未被自動發現時，明確讀取該目錄下需要的 `SKILL.md` 及引用。新 worktree 不會自動繼承另一目錄的設定。

<a id="workbench"></a>

### 接入已登記工作台

治理應已在原 control 登記該 Git 工作區及其任務。下列是**合成請求範例**，不是要求建立範例任務：

```json
{"mode":"preview","target":"C:/TaskCarry/workspaces/agent-1","workspace":"agent-1","task_id":"example-writing"}
```

用核對過的登記值替換三項，儲存請求後執行相同的預覽指令。`target`、`workspace`、`task_id` 必須一起提供；target 須符合登記工作區及其目前 Git 身分，任務須存在於同一個 control。具體任務與工作台關係由治理核對，setup 不強制一對一歸屬。`--project` 始終指向原 control。審閱後把相同請求的 `mode` 改為 `install`。

它寫入工作台的四項 Skills 及引用、MCP 片段、`.taskcarry/workbench.json` 與 `workbench.md`，不建立對話、不登記任務、不初始化另一資料庫，也不啟用宿主設定。普通文件目錄可以透過綁定 control 的 CLI 儲存 checkpoint，不為儲存文件偽造 Git 登記。

<a id="verify"></a>

### 驗收實際視窗

宿主載入後，在該視窗呼叫原生 `taskcarry_doctor` 與 `taskcarry_status`，將實際版本、解譯器、模組、control 及相關任務/工作區/檢查點與綁定資料核對。存在多個服務時選對服務。命令列成功不能證明原生工具已經暴露。

MCP 不可用時保留原始錯誤或工具缺失事實，可用固定隔離 CLI 繼續已授權工作：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' doctor
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry/control' status
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

排程任務、私有遠端與多電腦仍是[可選操作](operation-manual.md)，缺少可選能力不妨礙繼續原專案。
