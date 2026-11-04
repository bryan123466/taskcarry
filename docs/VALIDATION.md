# TaskCarry 0.2.0rc6 — local candidate validation

Recorded 2026-11-04. **Local candidate for review; not published.** The fixed governance runtime remains rc5. All new executable checks used disposable synthetic projects or candidate installations; no production control, scheduled task or user-level host configuration was changed. Portable counts, source fingerprints and dated historical records are in [VALIDATION_RESULTS.json](VALIDATION_RESULTS.json).

| Evidence | Observed result | Scope and limit |
|---|---|---|
| Windows / Python 3.12.10 complete source suite | **265 tests: 262 passed, 3 skipped, 0 failures/errors** | Measured files did not change during the run; standard wheel/sdist build was explicitly enabled and passed |
| Independent installed-wheel contract | **1 passed** | Resolves the installed-wheel opt-in skip in the source suite; disposable candidate runtime |
| Existing-project onboarding from the installed wheel | **2 scenarios passed** | One existing work chat, then multiple existing work chats; real CLI and generated stdio MCP, shared control, original identities and WIP preserved |
| Product ZIP cold start | Passed; 97 manifest payloads verified | Final exact-Git-blob archive extraction, bundled wheel and fresh runtime, three fallback manuals, installed onboarding reference, repeated setup with zero managed-file or manifest rewrites |
| Original rc5 wheel to rc6 candidate update | Passed; 6 managed files updated, repeat wrote 0 | Installation identity, user configuration and task state retained; old checkpoint restored and repeated restore reused its receipt |
| Bounded AI onboarding review | **2 synthetic text cases reviewed** | Seven input files unchanged; observed AI handoff responses using the public Skill and reference, separate from executable tests |

The independent wheel, onboarding, cold-start and rc5 update checks above were repeated successfully against the final product built from exact Git blob bytes. Its 95 source payloads match Git, all 98 ZIP members are accounted for, and 461 local links plus 75 retained heading anchors passed. Final artifact SHA256 values are recorded in the JSON artifact_record. Counts from independent scenarios are not added to the 265-test source count.

Only two source-suite skips remain unresolved by separate execution: native file and directory symlink cases require privileges unavailable on this Windows host. The source-suite installed-wheel skip was executed successfully in its separate wheel run. Junction rejection has separate coverage. A skip is not a successful native symlink test.

The complete source suite covers isolated package selection and legacy setup preservation; optional-Git plain checkpoints and fail-closed repository detection; restore effect verification and atomic receipt recovery; existing-workbench binding to one control; CLI/MCP contracts; Git receive/adopt, WIP protection, atomic records and current indexes; observe/run/issue/fix and protocol compatibility. The earlier plain-checkpoint and restore-receipt findings are fixed in this candidate and are not remaining backlog. A restore stopped in `APPLYING` with an unknown effect remains a review case: it is not automatically replayed or declared complete.

The executable onboarding scenarios preserve existing tasks, checkpoints, staged/unstaged work, `AGENTS.md` and live host settings. Generated bindings keep the same control and do not create task work, a second database or an acceptance claim. The rc5 update also verifies that the older setup tool refuses the newer managed resource set without writing. These checks use an actual installed candidate and generated stdio commands; they do not prove that a user's host loaded those commands or exposed native tools.

The AI review read the current public setup Skill and onboarding reference, then handled one existing non-Git writing project and one project with two existing work chats/worktrees. Its outputs retained accepted results, original task/checkpoint positions and paused work, separated confirmed decisions from AI suggestions, applied a later responsibility correction, suggested no unnecessary new chats, and identified only the current connection gap. It made no governance or installation calls. This is evidence for those two bounded inputs, not a statistical model-quality assessment, a claim about arbitrary chat histories or independent-user acceptance.

**Not verified for rc6:** native host activation/acceptance, natural scheduled automation, production installation, public CI for the final candidate commit, physical multi-computer use or independent-user usability. The fixed rc5 runtime was not upgraded. No generated setup file, CLI response, standalone stdio exchange or textual AI review is counted as native-host acceptance.

## 简体中文：当前候选验证

2026-11-04 的 RC6 是**本地待审候选，尚未发布**；正式固定运行包仍为 rc5。Windows / Python 3.12.10 完整源码测试 **265 项：262 通过、3 跳过、0 失败/错误**，测试期间记录的文件哈希未变；标准 wheel/sdist 构建已明确启用并通过。独立安装包合同另有 **1 项通过**，补足源码轮对应的 opt-in 跳过；剩余两项仍是本机原生符号链接权限限制，不算通过。

实际安装候选的两项既有项目接入场景通过，覆盖单工作聊天及多个工作聊天共用 control、原 task/checkpoint、两层 Git WIP、AGENTS 与用户宿主配置保全。最终产品包冷启动核对了 97 个 manifest payload、内置 wheel、三语手动备用手册与接入引用，重复 setup 不重写受管理文件或 manifest。原始 rc5 wheel 更新至候选只改 6 份管理文件，身份/配置/任务保留，旧 checkpoint 可恢复并复用回执。这些验证已对精确 Git blob 字节构建的最终包重新执行通过；95 份源码 payload 与 Git 完全一致，98 个 ZIP 成员齐全，461 个本地链接及 75 个旧标题锚点通过。最终 SHA256 见 JSON 的 artifact_record。

无 Git 普通 checkpoint 与 restore 效果后的回执恢复已实现并纳入全套回归，不再列为未修复问题。未知 `APPLYING` 效果仍须核验，不自动重放。另有 AI 实际阅读公开 Skill/引用后处理两例有界合成文本，保留旧成果与停点，区分有效决定和建议，保留暂停及责任更正，只给当前接入缺步；7 份输入的哈希不变，未执行治理或安装。该文本审验与真实 CLI/生成 stdio MCP 测试分别列证据，不能互相替代。

本候选没有正式生产安装、原生宿主验收、自然自动化、最终提交的公开 CI、实体多电脑或陌生用户验收证据；没有自动升级 rc5。下方历史报告中的“待修复”描述只代表当时时点，请以本节及 JSON 的当前结论为准。

## 繁體中文：目前候選驗證

2026-11-04 的 RC6 是**本機待審候選，尚未發布**；正式固定執行套件仍為 rc5。Windows / Python 3.12.10 完整原始碼測試 **265 項：262 通過、3 跳過、0 失敗/錯誤**，測試期間記錄的檔案雜湊未變；標準 wheel/sdist 建置已明確啟用並通過。獨立安裝套件合同另有 **1 項通過**，補足原始碼輪對應的 opt-in 跳過；剩餘兩項仍是本機原生符號連結權限限制，不算通過。

實際安裝候選的兩項既有專案接入情境通過，涵蓋單一工作聊天及多個工作聊天共用 control、原 task/checkpoint、兩層 Git WIP、AGENTS 與使用者宿主設定保全。最終產品套件冷啟動核對了 97 個 manifest payload、內置 wheel、三語手動備用手冊與接入引用，重複 setup 不重寫受管檔案或 manifest。原始 rc5 wheel 更新至候選只改 6 份管理檔案，身分/設定/任務保留，舊 checkpoint 可還原並重用回執。這些驗證已對精確 Git blob 位元組建置的最終套件重新執行通過；95 份原始碼 payload 與 Git 完全一致，98 個 ZIP 成員齊全，461 個本機連結及 75 個舊標題錨點通過。最終 SHA256 見 JSON 的 artifact_record。

無 Git 一般 checkpoint 與 restore 效果後的回執恢復已實作並納入全套回歸，不再列為未修復問題。未知 `APPLYING` 效果仍須核驗，不自動重放。另有 AI 實際閱讀公開 Skill/引用後處理兩例有界合成文字，保留舊成果與停點，區分有效決定和建議，保留暫停及責任更正，只給目前接入缺步；7 份輸入的雜湊不變，未執行治理或安裝。此文字審驗與實際 CLI/產生 stdio MCP 測試分列證據，不能互相替代。

本候選沒有正式生產安裝、原生宿主驗收、自然自動化、最終提交的公開 CI、實體多電腦或陌生使用者驗收證據；沒有自動升級 rc5。下方歷史報告中的「待修復」描述僅代表當時時點，請以本節及 JSON 的目前結論為準。

---

The following dated records are retained as historical evidence. Their artifact hashes, test counts and then-open findings belong to those earlier stages. They do not override the current rc6 results or reopen defects already fixed above.

# Historical source stage — optional Git checkpoints (2026-11-04)

The plain-directory checkpoint fix is implemented in a separate source stage. Plain files can be saved and restored without Git; repository metadata in the workspace or its ancestors requires successful Git verification. Corrupt, unreadable, bare or split metadata cannot silently become a plain checkpoint. The existing Git layer capture and atomic publication remain in use.

Windows / Python 3.12.10: the complete source suite passed **224 of 228 tests, 4 skipped, no failures/errors**. The four skips are two native symlink limitations plus the opt-in installed-wheel and standard source-build contracts. After adding the final split-metadata boundary and two tests, the affected suites passed **56 of 58 tests, 2 native symlink skips, no failures/errors**. All **14 optional-Git tests passed**, including real CLI/MCP subprocesses with an empty PATH. Exact core source hashes and the full-versus-final-targeted mapping are in the `rc6_nongit_checkpoint_source_stage` entry of [VALIDATION_RESULTS.json](VALIDATION_RESULTS.json).

This is source-stage evidence, not a newly built wheel, an installation, final RC6 acceptance or a public release. The restore post-effect receipt issue and the remaining RC6 onboarding, workspace-binding and manual work are still pending. Historical dev1 evidence below remains tied to its original source and artifacts.

**简体中文：** 无 Git 普通目录保存/恢复已形成独立源码修正；存在仓库元数据时必须核验 Git，失败不降级。完整源码测试 228 项中 224 通过、4 跳过；最后补充分离元数据边界后，相关 58 项中 56 通过、2 项原生符号链接限制跳过；14 项新增专项均通过。四项全套跳过还包含未启用的 wheel/源码构建合同，不能算本次新包验证。此阶段不表示完整 RC6、安装或公开发行已完成，restore 回执恢复及其余接入/手册工作仍待完成。

**繁體中文：** 無 Git 一般目錄儲存/還原已形成獨立原始碼修正；存在儲存庫中繼資料時必須驗證 Git，失敗不降級。完整原始碼測試 228 項中 224 通過、4 跳過；最後補充分離中繼資料邊界後，相關 58 項中 56 通過、2 項原生符號連結限制跳過；14 項新增專項均通過。四項全套跳過還包含未啟用的 wheel/原始碼建置合同，不能算本次新套件驗證。此階段不表示完整 RC6、安裝或公開發布已完成，restore 回執恢復與其餘接入/手冊工作仍待完成。

---


# Historical TaskCarry 0.2.0rc6.dev1 candidate (2026-11-02)

This is an unpublished development candidate. Windows / Python 3.12.10: **216 tests, 214 passed, 2 skipped, 0 failures or errors**. Both skips require unavailable symlink permissions. The full run explicitly enabled standard wheel/sdist build and the actual candidate wheel contract. The final rebuilt wheel also passed its independent installed-wheel contract (1 test). No governance installation was upgraded.

Real MCP subprocess regressions cover source and other working directories, conflicting Python import/encoding environment variables, Unicode, selected package disappearance, legacy fragment updates, user-file preservation, idempotence and interrupted-update recovery. A synthetic project upgraded from the original rc5 wheel to the final candidate: exactly two managed files changed (setup Skill and MCP fragment); installation identity, task state and user config were preserved; repeat install wrote nothing; MCP launched from source cwd loaded the new wheel.

The final product archive has 91 manifest payloads plus the manifest, with matching hashes and current product-source bytes. The wheel's 17 package files and four Skills match the allowlist; 50 Markdown/HTML documents have no missing local link targets. Release screening found no findings. Exact candidate hashes and portable results are in [VALIDATION_RESULTS.json](VALIDATION_RESULTS.json).

The initial full run placed temporary plain-directory fixtures inside the source Git worktree: 210 passed, 4 encountered the intended Git-root guard, and 2 skipped. Those failure records were retained privately. The complete suite was rerun in a dedicated external synthetic sandbox; the product guard was not relaxed.

Separate audit follow-ups remain: a plain-directory checkpoint still requires an executable Git, and a restore whose final event write fails leaves target effects but cannot resume its receipt in the same nonempty target. This candidate addresses launch selection, not those recovery contracts. Native host activation, natural scheduled runs, new cross-platform CI, physical multi-computer use and independent-user acceptance were not tested for this candidate. The historical rc5 evidence below is retained with its original version and scope.

## 简体中文：本地候选

本候选未发布、未安装到正式治理环境。Windows / Python 3.12.10 完整测试216项：214通过、2项因符号链接权限跳过、0失败/错误；已启用标准wheel/sdist和真实候选wheel测试，最终重建包的独立安装合同另有1项通过。真实MCP覆盖源码cwd、环境污染、中文、缺包失败和旧安装保全；原始rc5 wheel到最终候选的合成更新只写2份管理文件，身份/任务/用户配置保留，重复0写。最终产品包91个payload逐项hash匹配，50份文档链接无缺失。

首轮仓库内临时目录使4个普通目录场景触发Git根保护；失败证据保留，完整重跑改用专属外部合成沙箱，未放宽产品保护。无Git普通checkpoint及restore效果后事件失败的接续缺口另列后续，未混称已修复。本候选原生宿主、自然自动化及新跨平台CI未验收。下方保留rc5历史验证时点。

## 繁體中文：本機候選

本候選未發布、未安裝至正式治理環境。Windows / Python 3.12.10 完整測試216項：214通過、2項因符號連結權限跳過、0失敗/錯誤；已啟用標準wheel/sdist及實際候選wheel測試，最終重建套件的獨立安裝合同另有1項通過。實際MCP涵蓋原始碼cwd、環境污染、中文、缺包失敗與舊安裝保全；原始rc5 wheel至最終候選的合成更新僅寫2份管理檔案，身分/任務/使用者設定保留，重複0寫。最終產品套件91個payload逐項hash相符，50份文件連結無缺失。

首輪倉庫內暫存目錄使4個普通目錄情境觸發Git根保護；失敗證據保留，完整重跑改用專屬外部合成沙箱，未放寬產品保護。無Git普通checkpoint與restore效果後事件失敗的接續缺口另列後續，未混稱已修復。本候選原生宿主、自然自動化及新跨平台CI尚未驗收。下方保留rc5歷史驗證時點。

---

# Historical TaskCarry 0.2.0rc5 validation (2026-10-28)

[English](#english) · [简体中文](#简体中文) · [繁體中文](#繁體中文)

## English

All scenarios used disposable synthetic projects. No user's production project, native scheduled task or global host configuration was changed.

| Validation | Observed result | Scope |
|---|---|---|
| Windows / Python 3.12.14 source suite | 211 cases: 208 passed, 3 skipped, 0 failures, 0 errors | Real local Git, records, recovery, state projection, public interfaces and standard source build |
| Installed-wheel contract | 1 passed | Independent installation, generated stdio MCP command and packaged Skills |
| Downloadable product walkthrough | 62 checks passed | Final ZIP manifest, member hashes, actual installed CLI/MCP and three synthetic workspaces |
| AI-guided Skill rehearsal | 17 checks passed | One independently developed synthetic scenario, public API and CLI; development candidate, not native-host acceptance |
| Four Skill definitions | Format checks passed | Structure and metadata, not a guarantee of every model decision |

Two source skips require symbolic-link privileges unavailable on the local host. The installed-wheel contract is skipped within the source run and executed separately against the packaged wheel. Standard wheel and source-distribution construction was explicitly enabled. Do not add walkthrough check counts to the unit-test count.

The product walkthrough verifies cumulative and independent stages, paused checkpoints, unfinished files, receipt recovery after a real Git effect, repeat execution without a new integration commit, checkpoint restoration and selected workspace adoption. It also exercises the new installed `observe`, `run`, `issue`, `fix` and `upgrade` entrypoints. A fix is checked against genuine setup evidence while host reload remains unverified.

The new regression cases cover atomic state/event rollback, explicit legacy-index rebuild, an older writer invalidating the derived index, compare-and-swap evidence updates, selected-run receipts, retained failure conditions, safe successor closeout and operation protocol checks. With fixed current work, growing terminal history from 100 to 1,000 groups still loads 5 required records in the measured agenda fixture. This is structural evidence, not a production speedup percentage or a constant-cost claim for growing current work.

The AI-guided rehearsal read the public Skills and made successive tool choices in a generated project. After an injected post-effect interruption, it verified the existing effect, used the supported experience rule and completed one receipt. Paused work and unsubmitted files remained unchanged. The scenario was prepared while the development version label changed from rc4 to rc5; it is recorded as candidate evidence, not the final wheel test. The final package was separately verified as above.

Public files were screened through the release allowlist, private-term, host-path and common-secret checks. Local documentation links were checked. The product ZIP excludes maintainer tests and these validation receipts. The existing artwork was retained; this release does not claim a new visual or native browser acceptance run.

**Not verified here:** native Codex/other host activation, real scheduled triggers, physical multi-computer operation or independent-user usability. Cross-platform CI belongs to the [Actions run for the exact release commit](https://github.com/bryan123466/taskcarry/actions). Earlier release evidence remains in Git history. Portable details: [VALIDATION_RESULTS.json](VALIDATION_RESULTS.json).

## 简体中文

本轮全部使用可丢弃的合成项目，没有运行生产项目、原生自动化或更改全局宿主配置。Windows / Python 3.12.14 源码测试 **211 项：208 通过、3 跳过、0 失败、0 错误**。其中两项需要本机未具备的符号链接权限，安装包合同在源码轮跳过后另行实际通过；标准 wheel/sdist 构建已启用。

最终产品包在源码目录外解压、校验逐项哈希并安装。实际 CLI、生成的 stdio MCP、四份 Skills 及三个合成工作区演练通过 **62 个检查点**，覆盖累计与独立交付、暂停检查点、WIP 保全、已发生 Git 效果后的经验恢复、重复执行、观察依据、具名轮次、问题修正采用核对及索引升级。另有 **1 项独立安装包合同通过**，四份 Skill 格式检查通过。

独立 AI 引导演练通过 **17 项检查**：模型读取公开 Skill 后分步决定 API/CLI 调用，在预设回执中断后复用真实 Git 效果，仅补一次回执；暂停任务和未交付文件保持原位。该场景跨候选版本标签更新，明确作为开发候选演练，不冒充最终安装包、陌生用户或原生宿主验收。

本轮回归验证了状态与事件共同回滚、旧库显式重建、旧写入者使索引失效、依据修订号校验、合法后继收口、操作协议预检等。固定当前工作时，历史从 100 组增至 1,000 组，议程仍只加载 5 条必要记录；这是结构性结果，不是生产耗时比例或任意规模固定成本。

公开文件经过允许清单、私有词语、主机路径和常见密钥筛查，本地文档链接已核对。产品包不附维护测试及本页。原生宿主激活、定时自然触发、实体多电脑及陌生用户验收仍未覆盖；跨平台结果以发布提交对应 Actions 为准。

## 繁體中文

本輪全部使用可丟棄的合成專案，未執行生產專案、原生排程或更改全域宿主設定。Windows / Python 3.12.14 原始碼測試 **211 項：208 通過、3 跳過、0 失敗、0 錯誤**。其中兩項需要本機未具備的符號連結權限，套件合同在原始碼輪跳過後另行實際通過；標準 wheel/sdist 建置已啟用。

最終產品套件在原始碼目錄之外解壓縮、逐項核對雜湊並安裝。實際 CLI、產生的 stdio MCP、四份 Skills 及三個合成工作區演練通過 **62 個檢查點**，涵蓋累計及獨立交付、暫停檢查點、WIP 保全、Git 效果已發生後的經驗恢復、重複執行、觀察依據、具名輪次、問題修正採用核對及索引升級。另有 **1 項獨立安裝套件合同通過**，四份 Skill 格式檢查通過。

獨立 AI 引導演練通過 **17 項檢查**：模型讀取公開 Skill 後分步決定 API/CLI 呼叫，於預設回執中斷後重用實際 Git 效果，只補一次回執；暫停任務及未交付檔案保留原位。此情境跨候選版本標籤更新，明確列為開發候選演練，不冒充最終安裝套件、陌生使用者或原生宿主驗收。

回歸驗證涵蓋狀態與事件共同回滾、舊庫明確重建、舊寫入者使索引失效、依據修訂號檢查、合法後繼收口及操作協定預檢。固定目前工作時，歷史從 100 組增加至 1,000 組，議程仍只載入 5 筆必要記錄；此為結構性結果，並非生產耗時比例或任意規模固定成本。

公開檔案經過允許清單、私有詞語、主機路徑及常見金鑰篩查，本機文件連結已核對。產品套件不附維護測試及本頁。原生宿主啟用、排程自然觸發、實體多電腦及陌生使用者驗收仍未涵蓋；跨平台結果以發布提交對應 Actions 為準。
