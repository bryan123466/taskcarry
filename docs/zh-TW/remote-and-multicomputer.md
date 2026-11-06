# 私有遠端、備份恢復與多電腦協作

先完成[本機對話式接入](windows-example.md)。選擇私有遠端、檔案儲存或另一臺電腦時，再使用本參考；具體安裝指令保留在[手動後備](manual-setup.md)。

[返回操作手冊](operation-manual.md) · [English](../en/remote-and-multicomputer.md) · [简体中文](../zh-CN/remote-and-multicomputer.md) · [指令參考](../COMMANDS.md)

本機治理 Git 儲存、原治理視窗的排程任務與官方更新檢查屬於標準接入。下述私有遠端與多電腦流程是按需擴充，尚未經過兩臺實體電腦的端到端驗證；它組合 Git 操作與現有本機 TaskCarry 介面，已提供所選本機恢復集與 standby 移交能力；遠端傳輸和真實第二宿主驗收仍分別核對。

標準本機儲存使用明確檔案清單，保全原 Git 暫存區與未完成工作，只有選定內容變更才形成提交；排除執行中的 `.taskcarry` 資料庫、runtime、下載套件與憑據。持續工作的視窗保留真實任務與工作區關聯，提交署名或對話 ID 本身不能證明這些關聯。原資料可留在原處，大型外部產物以版本化參照和分別核對的儲存涵蓋範圍銜接。

選擇網路磁碟時，同步已封存的靜態備份套件；擷取、本機位元組核驗、上傳、下載與隔離恢復分別留證。寫入本機同步目錄不證明雲端已經上傳或另一臺電腦能夠恢復。不把活躍 `.taskcarry` 或 Git 中繼資料交給互相競爭的背景同步；加密金鑰與加密備份分開保管。

所有 `<...>` 都是需要替換的預留位置符號。`python` 應指向已經安裝 TaskCarry 的 Python 環境。JSON 檔案儲存為 UTF-8；不要把示例中的預留位置符號直接執行。Git 推送會向所選遠端傳送資料，應先確認儲存庫、存取者和本次授權範圍。

<a id="private-git"></a>

## 4. 私有 Git 線上記錄庫與恢復備份

### 4.1 先分清哪些內容儲存在哪裡

[本步驟可直接複製的 Windows 示例](manual-setup.md)

| 內容 | 推薦儲存位置 | 恢復時能提供什麼 |
|---|---|---|
| 選定的程式碼、文件、穩定成果 | 私有 Git 儲存庫，完成 commit 和 push | 已推送的檔案版本與提交歷史 |
| 精選專案記憶：目標、決策、當前節點、下一步、來源 | 私有 Git 中的普通 Markdown/JSON 檔案 | 可跨電腦閱讀的專案接續說明 |
| TaskCarry 任務、階段、操作與經驗記錄 | 本機治理目錄的 `.taskcarry/state.sqlite3` | 本機工具的狀態與原始記錄 |
| 檢查點檔案對象 | 同一治理目錄的 `.taskcarry/objects/` | 明確選中並儲存過的檔案及檢查點層次 |
| 未儲存的編輯器內容、未納入檢查點的檔案 | 原程式或工作區；需要單獨儲存/備份 | Git 和 TaskCarry 不會自動捕獲它們 |
| 影片、安裝套件、大型資料等 | 經授權的獨立檔案儲存；Git 儲存位置、大小和雜湊說明 | 找到並核對檔案，不代表檔案已上傳或可存取 |

**私有 Git 不是整個電腦或治理資料庫的自動鏡像。** 只有已經提交並推送的選定檔案才會到達遠端；忽略檔案、未提交成果和本機對話歷史不會因此自動儲存。GitHub 普通 Git 檔案超過 100 MiB 會被拒絕；大檔案應另選儲存或明確設定 Git LFS，TaskCarry 不自動設定它們。[GitHub 檔案限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

### 4.2 建立私有遠端，明確誰能推進主線

[本步驟可直接複製的 Windows 示例](manual-setup.md)

1. 在自己的 Git 託管服務建立**私有**儲存庫，檢查成員權限。接入已有專案時，不要讓新儲存庫自動生成與本機歷史無關的 README 或初始提交。
2. 選定一臺電腦作為整合主機。其專用乾淨接收工作區是唯一推進遠端 `main` 的位置；其他電腦使用任務分支。
3. 在接收工作區核對遠端、分支、工作區和待推送提交：

```text
git -C "<A_BASELINE>" status --short
git -C "<A_BASELINE>" branch --show-current
git -C "<A_BASELINE>" remote -v
git -C "<A_BASELINE>" log -5 --oneline
```

僅當該工作區尚無 `origin` 時添加：

```text
git -C "<A_BASELINE>" remote add origin "<PRIVATE_REPOSITORY_URL>"
```

若已有 `origin`，先核對地址，不要自動覆蓋。接收工作區的本機分支不必也叫 `main`。確認本次已接收成果適合上傳後，精確推送當前基線：

```text
git -C "<A_BASELINE>" push -u origin HEAD:refs/heads/main
git -C "<A_BASELINE>" rev-parse HEAD
git -C "<A_BASELINE>" ls-remote origin refs/heads/main
```

後兩條的提交雜湊應一致。被拒絕時先查原因，不強推。若遠端已有不同歷史或其他寫入，先核對差異與寫入責任。**這是原生 Git 推送，不是 TaskCarry 的 `reconcile` 或內建遠端回執。** 建議使用託管平台的分支保護/權限限制來落實唯一主線寫入者；僅在提示詞裡約定無法形成跨機鎖。

### 4.3 把有用記憶儲存為普通專案檔案

[本步驟可直接複製的 Windows 示例](manual-setup.md)

在一個已登記、負責文件的專業工作區維護例如 `project-memory/current.md`，內容包括：

- 任務標識、目標、當前階段，以及活躍/暫停/等待狀態。
- 已接受的階段和可查的提交、檔案路徑；業務驗收與技術接收分別說明。
- 當前有效決定、適用範圍、來源；過時決定指向其後繼。
- 尚未完成的工作、檢查點標識、下一步，以及只在真正需要時提出的使用者決定。
- 大檔案的位置、雜湊及備份是否已實際驗證；不把憑據寫進記錄。

這份說明是經整理的專案接續記憶，不是模型權重、全部私人對話或可直接恢復的資料庫。可以額外匯出 `status`，但其中可能包含本機路徑與內部任務資訊；先檢查存取範圍和內容。原始匯出適合儲存在備份目錄，進 Git 的版本可只保留必要欄位。

PowerShell 7 匯出示例（目標父目錄已存在）：

```powershell
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status | Set-Content -LiteralPath "<SNAPSHOT>/status.json" -Encoding utf8
```

檢查 JSON 中 `ok` 為 `true`，並記下采集時間。不要把失敗輸出當成正常狀態。整理後的記憶檔案也應走普通專業交付與接收；不要為寫摘要直接弄臟專用接收工作區。精確提交示例：

```text
git -C "<MEMORY_WORKSPACE>" diff -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" add -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" commit -m "Update current project handoff"
```

提交前兩次檢查暫存區；若存在不屬於本次交付的暫存內容，停止這一步並保留它，不混合提交。隨後按主手冊宣告階段，由整合主機接收並推送。記憶檔案進入 Git 不會自動匯入另一臺電腦的 TaskCarry 狀態庫或模型記憶。

可直接交給 Codex：

> 請為本專案維護一份精簡、可接續的 project-memory/current.md。基於已授權的任務記錄、提交和明確來源，寫清當前事實、有效決定、暫停節點與下一步；舊決定只保留必要沿革，不把沒有變化的任務列成新增積壓。先檢查現有檔案及暫存區，只交付這次真實變化。不要匯出私人對話、憑據或整個 .taskcarry。按本機 TaskCarry 流程提交接收；只有我已授權上傳的資料才推送到指定私有遠端。

### 4.4 產生有明確覆蓋範圍的恢復集

Core 可以從可信發行包重裝；專案記憶不能靠重新下載恢復。治理先列清單，再呼叫 `recovery backup_plan` / `backup_execute`，儲存資料庫一致快照及參照物件，並選擇實際需要的工作區與素材。來源檔案改變時保留具體差異，不能把跨時點內容說成同一快照。

| 覆蓋對象 | 應記錄和驗證的內容 |
|---|---|
| 專案狀態 | `.taskcarry` 資料庫的一致快照、實際參照物件、專案 source 身分和副本身分。讀取副本不得被當作另一位活躍治理寫入者。 |
| Git 工作區 | 選定 refs 和可達提交歷史、目前 HEAD、index、工作區修改及顯式選擇的未追蹤檔案。只推送 commit 不會儲存這些全部層次。 |
| 普通檔案與大型素材 | 精確路徑、內容雜湊、大小和恢復目標；未納入的素材或無法取得的來源必須列為排除/缺口。 |
| 能力層 | 正在使用的規則、四 Skills 的精確版本及自訂內容、相容 Core 版本與包雜湊、宿主能力清單。安裝目錄不是使用者記憶本身。 |
| 本機接入素材 | 保留可重建的綁定說明；恢復後重新產生解譯器路徑、MCP 與工作台入口。憑證、登入和信任另行處理。 |

治理應主動選擇可版本化的專案記憶和必要能力素材作為 payload；工具不會把整台電腦、對話平台或所有忽略檔案自動打包。儲存編輯器緩衝後再納入檔案。恢復集含私有專案資料，不能提交公共儲存庫。

本機 `verify` 核對清單和實際物件。需要網路硬碟或私有儲存時，上傳封存的靜態恢復集，下載到獨立位置再核對同一清單雜湊。寫入本機同步目錄、看到檔名或收到上傳指令成功，都不是下載與恢復證明。不要同步寫入活躍 SQLite 或共用 `.git`；加密金鑰與加密備份分開保管。

可以直接向治理說：

> 請為目前專案準備明確恢復計畫。包含必要治理狀態與物件、選定 Git refs/歷史/index/WIP、專案記憶、規則與 Skills 版本及必要素材，列明排除項。核對範圍後產生本機恢復集並驗證，在獨立目錄做恢復演練，保留原目錄和原任務。副本保持 standby。若我已啟用異地儲存，再分別提供上傳、重新下載雜湊和恢復證據；未授權的傳輸不要執行。

### 4.5 獨立恢復，驗證後再移交唯一寫入權

`recovery restore_plan` / `restore_execute` 在空的獨立目標恢復所選真實 Git 歷史及分層工作、狀態和素材。副本保留邏輯專案身分，取得明確副本身分，並預設處於 **standby**。路徑對應與舊操作作為接續證據處理，不能在新位置重放舊接收/採用計畫。

1. 核對恢復集來源、清單雜湊、精確覆蓋和相容版本；保留原備份不變。
2. 在獨立目錄恢復並核對任務、物件、選定 Git refs/HEAD/index/WIP 和素材。缺失內容寫入報告，不能稱整台電腦已恢復。
3. 依新機器實際目錄與解譯器重新產生連線，保留專業設定。治理和工作視窗分別原生呼叫 doctor/status；核對專案/副本身分、任務與 checkpoint。本機檔案恢復不證明宿主已連線。
4. 需要接管時明確停止並隔離舊寫入者。準備 `activation_plan`，核對原副本、新副本、交接授權和新宿主證據，再執行 `activate`。舊主機未確認停寫時，副本繼續 standby。
5. 新寫入點啟用後再檢查原生調度與送達；舊主機回來時作為協作端處理其獨立成果，不自行恢復舊治理寫入或舊調度。

工具核對明確交接聲明及原生證據參照，不能遠端證明舊機器已經停機，也不提供跨主機分散式鎖。需要的帳號權限、主線保護和實際停寫由環境執行。若僅需找回一個檢查點的選定檔案，舊 `restore` 仍可使用；它的合成還原基線不同於 `recovery` 儲存的原 Git 歷史，二者不可冒充。

<a id="multi-computer"></a>

## 5. 多電腦按任務分支協作

### 5.1 推薦拓撲與責任

[本步驟可直接複製的 Windows 示例](manual-setup.md)

```text
電腦 B：獨立 clone → 任務分支 → 穩定提交 + 交付 manifest
                         │ push 任務分支
                         ▼
                    私有 Git 遠端
                         │ fetch 精確源提交
                         ▼
電腦 A：穩定命名的本機 intake 倉/工作區
        → A 的 TaskCarry submit → 接收計畫 → 唯一接收基線
        → 授權 push main → B fetch 後接續下一任務節點
```

TaskCarry 的一個治理目錄由**一臺電腦上的本機 SQLite**管理。電腦 B 可以有獨立的本機 TaskCarry 做檢查點，但其資料庫不會自動合併到 A。不要把 `.taskcarry`、`.git` 或活動 worktree 放進雙向同步目錄共用。

同一業務主題可拆成任務支線；要明確成果、允許修改的路徑、基線和介面依賴。只有任務名不同而實際修改同一檔案，仍可能衝突。每個並行寫入者使用自己的檔案工作區和分支；同一 worktree 的檔案不會因為開了兩個對話窗而隔離。[Codex worktree 說明](https://learn.chatgpt.com/docs/environments/git-worktrees)

不同電腦可分別使用各自有權使用的 Codex 帳號和 Git 憑據。**帳號登入不構成任務鎖，也不會自動登出另一電腦。** 不共享會話檔案、登入權杖或密碼；Git 權限與主線寫入限制單獨設定。初始方案不需要自己搭登入服務器，也不承諾網路分區期間的自動主機切換。

### 5.2 電腦 B：從已公布基線開始一個任務

[本步驟可直接複製的 Windows 示例](manual-setup.md)

確認 A 已推送允許 B 使用的基線，並約定任務 `form-export` 僅修改 `forms/export.py` 與 `docs/export.md`。以下目錄、任務名和檔案都是示例，應換成實際約定。

```text
git clone "<PRIVATE_REPOSITORY_URL>" "<B_REPOSITORY>"
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" switch -c codex/form-export origin/main
git -C "<B_REPOSITORY>" rev-parse HEAD
```

把最後輸出記為 `<SOURCE_BASE>`，在工作開始前儲存。若已經有合適的儲存庫副本或工作區，重用它，不重複複製儲存庫、切換有 WIP 的工作區或佔用已有分支。

> 在本電腦的 [任務工作區] 推進任務 form-export，起點是 [SOURCE_BASE]。只修改約定的 forms/export.py 和 docs/export.md；業務判斷不明確時提出具體問題。儲存有意義的檢查點和下一步，達到穩定節點再精確提交。不要改 main、別人的工作區或治理資料庫，也不要把仍未完成的任務宣告為驗收完成。交付時給出原 base、源 commit、精確變更路徑、已做檢查、剩餘工作和材料位置。

完成穩定節點後：

```text
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" add -- forms/export.py docs/export.md
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Add task form-export stage one"
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" diff --no-renames --name-only "<SOURCE_BASE>" HEAD
```

仍須在提交前確認暫存區只有本次路徑。把產物提交記為 `<SOURCE_COMMIT>`；最後一條結果必須與交付清單完整相符。刪除和重命名涉及的路徑也需按實際 diff 核對。

### 5.3 電腦 B：另存交付說明並推送任務分支

[本步驟可直接複製的 Windows 示例](manual-setup.md)

在產物提交**之後**建立 `handoffs/form-export-v1.json`，避免“檔案裡寫它自身提交雜湊”的循環：

```json
{
  "task_id": "form-export",
  "stage_label": "form-export-v1",
  "source_branch": "codex/form-export",
  "source_base": "<SOURCE_BASE>",
  "source_commit": "<SOURCE_COMMIT>",
  "paths": ["forms/export.py", "docs/export.md"],
  "checks": ["<actual checks and outcomes>"],
  "task_state": "paused",
  "next_step": "<remaining work or the next decision>",
  "artifacts": [],
  "relation_note": "<independent change, or evidence about earlier stages>"
}
```

這是**人和治理 Agent 閱讀的交接說明，不是 TaskCarry import API**；不要直接把它傳給 `submit`。

```text
git -C "<B_REPOSITORY>" add -- handoffs/form-export-v1.json
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Record form-export stage one handoff"
git -C "<B_REPOSITORY>" push -u origin HEAD:refs/heads/codex/form-export
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" ls-remote origin refs/heads/codex/form-export
```

檢查暫存內容與遠端雜湊。遠端分支 HEAD 現在包含交接說明，其雜湊通常**不同於**被交付的 `<SOURCE_COMMIT>`，兩者都應保留，不能混用。B 的 checkpoint 對象和未提交檔案沒有隨此推送上傳。

### 5.4 電腦 A：複核原始證據，再用本機介面接收

[本步驟可直接複製的 Windows 示例](manual-setup.md)

為這個任務建立名稱穩定的 intake 儲存庫副本或工作區（例如本機登記名 `intake-form-export`），從遠端取得原提交。已有對應 intake 時先查其綁定和未完狀態，不重複建立或改寫其歷史。

首次建立示例：

```text
git clone --branch codex/form-export "<PRIVATE_REPOSITORY_URL>" "<A_INTAKE>"
git -C "<A_INTAKE>" show HEAD:handoffs/form-export-v1.json
git -C "<A_INTAKE>" cat-file -e "<SOURCE_BASE>^{commit}"
git -C "<A_INTAKE>" cat-file -e "<SOURCE_COMMIT>^{commit}"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_COMMIT>" HEAD
git -C "<A_INTAKE>" diff --no-renames --name-status "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" diff "<SOURCE_BASE>" "<SOURCE_COMMIT>" -- forms/export.py docs/export.md
git -C "<A_INTAKE>" switch -c codex/intake-form-export "<SOURCE_COMMIT>"
```

祖先檢查以退出碼 0 表示成立；檔案內容、清單、授權範圍或檢查結果不符時，先查清具體差異，不繼續安裝。不要先 cherry-pick、rebase 或重造提交，再把新雜湊稱為原階段。之後登記本機工作區、任務和階段，分別儲存以下三個檔案：

`intake-workspace.json`：

```json
{"name":"intake-form-export","path":"<A_INTAKE_ABSOLUTE_PATH>"}
```

`intake-task.json`：

```json
{"task_id":"form-export","title":"Form export","workstream":"forms"}
```

`intake-submit.json`：

```json
{"task_id":"form-export","workspace":"intake-form-export","stage_id":"form-export-v1","base":"<SOURCE_BASE>","commit":"<SOURCE_COMMIT>","paths":["forms/export.py","docs/export.md"],"relation":"independent"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" workspace --input intake-workspace.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" task --input intake-task.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" submit --input intake-submit.json
```

已有同名任務時先核對實際身分，不用說明檔案覆蓋另一任務。上面 `independent` 僅適用於這個示例的新階段；若要累積取代舊階段，必須滿足**同一任務、同一登記工作區、原提交祖先關係及路徑覆蓋**，並明確給出 `supersedes`。跨電腦同名階段不會自動產生關聯。歷史不滿足條件時保留原證據，請治理判斷關係，不能偽造覆蓋。

建立 `receive-plan.json`：

```json
{"baseline":"baseline"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-plan.json
```

核對返回計畫的全部 `stage_ids`、基線 HEAD、未完操作和衝突。接收計畫可能包含其他已有排隊階段，並不自動只選這個任務；全部都在本次授權內才執行。將返回的 `plan_id` 原樣填入 `receive-execute.json`：

```json
{"baseline":"baseline","execute":true,"plan_id":"<RETURNED_PLAN_ID>"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-execute.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status
```

檢查階段實際為 `COMMITTED`、相關操作完成及當前基線內容；整體呼叫成功不代表所有排隊項都已完成。具體衝突只處理相關任務，不覆蓋其他人的 WIP。需要更新 A 的某工作區時按主手冊先 `adopt` 計畫再執行。授權上傳的基線按 4.2 精確 push 到 `main`；接收形成的新整合提交和原 B 源提交都要能追溯。

> 接收電腦 B 的 form-export-v1。先讀取遠端交接說明與原提交，核對原 base/commit、精確路徑、已做檢查、當前基線及任務關係。使用本機穩定登記的 intake 工作區，通過 TaskCarry submit 與先計畫後執行的 reconcile 接收，不冒充跨機資料庫匯入，不重寫來源雜湊，不重複執行已完成效果。檢查計畫中的其他階段是否也在授權範圍。保留 B 的未完任務說明，業務驗收單獨判斷；僅按已有授權推送主線。

### 5.5 B 接續、主機換手和已知邊界

[本步驟可直接複製的 Windows 示例](manual-setup.md)

B 確認 A 接收並推送後，讀取最新接續說明。若舊任務工作區仍有 WIP，先保留，不直接把它重置到 `main`。可從已公布主線建立下一條乾淨任務支線：

```text
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" worktree add -b codex/form-export-next "<B_NEXT_WORKSPACE>" origin/main
```

根據任務關係接續，記錄新 base；不用重做已完成階段。其他機器上的 TaskCarry `adopt` 不會通過網路被 A 自動呼叫。

| 情況 | 應采取的動作 |
|---|---|
| 兩臺電腦推進互不重疊的任務 | 各自分支和工作區，A 循序核對並推進接收基線 |
| 同一任務拆成兩個支線 | 明確介面、路徑和整合順序；同名任務並不能消除內容衝突 |
| A 暫時離線，B 想繼續工作 | B 可繼續授權的任務分支，保留檢查點；主線接收等待 A 或明確換手 |
| A 無法恢復，需要 B 接管主線 | 明確停止/隔離舊主線寫入權，按 4.5 恢復資料與建立治理；對帳後讓 B 成為唯一整合主機 |
| A 恢復上線 | 先作為普通協作主機讀取當前遠端和接管記錄，不恢復舊定時寫入；核對其未推送成果後按任務分支交接 |
| 推送被拒、源提交缺失、清單不符或內容衝突 | 保留成果與原始證據，解決具體差異；不強推、不改 hash 造成功、不把舊操作盲目重放 |

無法確認舊主機停止時，不能聲稱已解決“雙主寫入”；需要在實際 Git 權限/主線保護或明確斷開舊寫入者層面落實。RC 不提供分散式租約、自動選主、跨機事務遷移、遠端副作用恢復、作業系統修復或 Codex 帳號遷移。上述流程讓任務資料可交接，但不承諾完整對話、未儲存內容或全部原生環境自動恢復。
