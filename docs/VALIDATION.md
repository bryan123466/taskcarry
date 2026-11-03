# TaskCarry 0.2.0rc6.dev1 — local candidate validation

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

# TaskCarry 0.2.0rc5 — validation

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
