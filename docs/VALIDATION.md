# TaskCarry 0.2.0rc7 source validation

This dated record describes the frozen source run on 2026-11-07. [Machine-readable results](VALIDATION_RESULTS.json) list every test outcome. Exact artifact, installation, native-chat and scheduling receipts accompany the corresponding candidate; an earlier revision's results do not certify a later package.

## English

Windows / Python 3.12.10: **492 tests, 487 passed, 5 skipped, zero failures or errors**. Three isolated processes ran non-overlapping module assignments covering every test module once. Public source, tests, Skills, fixtures and documentation did not change during execution. Only these portable validation summaries were updated after the run.

The standard source wheel/sdist build was enabled and passed. The skips name Windows symlink privilege limits and the built-wheel opt-in check, which belongs to the independent exact-artifact verification. CLI and all **35 MCP actions** share the same engine. Four public Skills and two reference resources must match the wheel. Source and product archives use positive allowlists with explicit membership and byte checks.

Synthetic regressions cover existing Git/index/WIP, exact delivery and adoption, optional-file checkpoints, bounded context/history/update protocols, source revisions, portable identities, complete cycles, current workbench publication/consumption, configuration preservation, sealed recovery, standby, path rebinding and actual post-restore receiving/adoption. They also cover missing receiving baselines, cumulative successors, stale source revisions and uncertain-effect recovery. The engineering fixture supplies concrete USB text frames and replay/CSV checks; it does not connect a real device or certify firmware or a live UI.

Evidence layers remain separate: source tests; an exact ZIP/wheel and fresh/RC5/RC6 installation checks; standalone stdio; native tools in each actual chat; natural scheduled trigger, AI execution and report delivery. Synthetic host attestations in tests are labeled as such. The candidate report names the actual artifacts and any observed native coverage, with remaining conditions. The supported Codex reader protocol is 0.166.0-alpha.6; broader host access is not inferred.

Final-commit public CI awaits authorized publication. Real two-computer recovery, arbitrary cloud services, production adoption and independent-human acceptance are outside this source-run evidence. A restored replica starts in standby and requires explicit single-writer handoff; a local lock cannot stop another computer.

## 简体中文

2026-11-07，Windows / Python 3.12.10：**492 项，487 通过，5 跳过，最终各项均通过或明确跳过**。三个独立进程按不重叠模块覆盖完整套件，每个模块只分配一次。执行期间公共源码、测试、Skills、示例和文档均未改变；本页及 JSON 验证摘要在运行结束后更新。

标准源码 wheel/sdist 构建已启用并通过。跳过项逐项注明 Windows 符号链接权限限制及需要实际 wheel 的独立检查。CLI 与 **35 项 MCP 工具**共用实现；四项 Skills 和两份引用须与 wheel 一致。源码和产品包按允许清单核对成员及字节。

合成回归覆盖原 Git/index/未提交工作保全、精确交付与采用、普通文件保存、有界上下文/历史/更新查询、来源修订、稳定身份、完整治理整轮、工作台发布/消费、配置保全，以及封存恢复、待机与迁址后真实继续接收/采用。还验证了遗漏接收仓库、累计阶段续办、旧理解不能掩盖未读新修订，以及效果不明时先核验再续办。工程示例提供具体 USB 文本帧、回放与 CSV 检查，不连接真实设备，不证明固件或实时界面已通过。

源码、精确 ZIP/wheel、新安装/RC5/RC6 升级、独立 stdio、各实际窗口原生工具、自然触发、AI 执行和报告送达分别列证。测试中的宿主回执明确为合成资料；具体包、真实宿主覆盖及剩余条件见对应候选报告，不能沿用其他提交的成功。Codex 读取器核对协议为 0.166.0-alpha.6，不推断全部宿主或账户可读。

最终提交的远端 CI 等待获准公开。真实双电脑、任意网盘服务、生产采用与独立真人体验不属于这份源码证据。恢复副本默认待机，明确移交唯一写入权后再继续；本机锁无法关闭另一台电脑。

## 繁體中文

2026-11-07，Windows / Python 3.12.10：**492 項，487 通過，5 跳過，最終各項均通過或明確跳過**。三個獨立程序以不重疊模組覆蓋完整套件，每個模組只分配一次。執行期間公共原始碼、測試、Skills、範例及文件均未改變；本頁與 JSON 摘要在執行結束後更新。

標準原始碼 wheel/sdist 建置已啟用並通過。跳過項逐一註明 Windows 符號連結權限限制及須以實際 wheel 執行的獨立檢查。CLI 與 **35 項 MCP 工具**共用實作；四項 Skills 及兩份參考須與 wheel 一致。原始碼與產品套件依允許清單核對成員及位元組。

合成回歸涵蓋既有 Git/index/未提交工作保全、精確交付與採用、一般檔案儲存、有界上下文/歷史/更新查詢、來源修訂、穩定身分、完整治理整輪、工作台發布/消費、設定保全，以及封存恢復、待機與遷址後實際繼續接收/採用。另驗證遺漏接收儲存庫、累計階段接續、舊理解不能掩蓋未讀新修訂，以及效果不明時先核驗再續辦。工程範例提供 USB 文字幀、回放及 CSV 檢查，不連接真實裝置，也不證明韌體或即時介面已通過。

原始碼、精確 ZIP/wheel、新安裝/RC5/RC6 更新、獨立 stdio、各實際視窗原生工具、自然觸發、AI 執行與報告送達分別留證。測試中的宿主回執明確為合成資料；具體套件、真實宿主覆蓋及剩餘條件見對應候選報告，不沿用其他提交的成功。Codex 讀取器核對協定為 0.166.0-alpha.6，不推論所有宿主或帳戶皆可讀。

最終提交的遠端 CI 等待獲准公開。真實雙電腦、任意網路磁碟服務、生產採用與獨立真人體驗不屬於本次原始碼證據。恢復副本預設待機，明確移交唯一寫入權後再繼續；本機鎖無法關閉另一台電腦。

## Build-environment retry / 构建环境补验 / 建構環境補驗

The first complete run covered 492 tests: 486 passed, 5 skipped and one source-build check failed because that runtime lacked build-only setuptools. With public inputs unchanged, that one check passed in the retained dedicated build environment (Python 3.12.10, setuptools 84.2.1, wheel 0.48.0). Final unique-test coverage is 487 passes and 5 skips across 492 tests; 493 test attempts include the retry. No build dependencies were installed into the governance runtime. The original result and the targeted retry are retained separately in the JSON evidence.

首轮完整覆盖 492 项：486 通过、5 跳过，1 项源码构建因所选运行环境缺少构建用 setuptools 失败。公共输入保持不变，该项在独立构建环境中补验通过。最终 492 个唯一测试为 487 通过、5 跳过；含补验共执行 493 次。治理运行环境未安装构建依赖，原失败与补验分别保留。新增回归覆盖合法旧状态、历史关联保全、完整备份/待机恢复、索引升级、原计划续办及外来/损坏/未来格式拒绝。

首輪完整涵蓋 492 項：486 通過、5 跳過，1 項原始碼建構因所選執行環境缺少建構用 setuptools 失敗。公共輸入保持不變，該項在獨立建構環境中補驗通過。最終 492 個唯一測試為 487 通過、5 跳過；含補驗共執行 493 次。治理執行環境未安裝建構依賴，原失敗與補驗分別保留。新增回歸涵蓋合法舊狀態、歷史關係保全、完整備份/待機恢復、索引升級、原計畫續辦及外來/損壞/未來格式拒絕。
