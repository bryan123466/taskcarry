# TaskCarry 0.2.0rc8 source validation

[Machine-readable results](VALIDATION_RESULTS.json) · [Release changes](RELEASE_0.2.0rc8.md) · [Actual synthetic-chat case](../examples/vision-drone-governance/native-case/README.md)

## English

The complete local source run on 2026-11-16 covers **565 unique tests: 559 passed, 6 skipped, zero failures or errors**, using Windows and Python 3.12.10. Three disjoint module assignments covered the current suite. Engine, test, Skill and build-script hashes were unchanged during the run. A later Skill clarification and explicit example package membership are checked separately with the final package.

Twenty shared-directory core regressions, eight per-chat onboarding regressions and an actual shared-history recovery regression cover separate original tasks in one directory, independent consumption, explicit legacy conversion, retained byte preimages, interruption recovery, concurrent identity claims and refusal to replay an old plan over a shared entry. Backup and independent restore retain tasks, checkpoints and history while quarantining old host routing and keeping the recovered writer in standby.

The suite also covers bounded metadata discovery before initialization, selection continuity, source-qualified identities, existing Git/WIP preservation, receipt recovery and the deterministic drone governance replay. Its actual Windows junction tests model the older pathlib API boundary; this local run is not a Python 3.11 interpreter run. The six skips retain their reasons in the JSON: host symbolic-link privileges and a separately selected installed-wheel check. CLI and **36 MCP tools** use one engine; four Skills and two references are checked for package parity.

The [exported chat exercise](../examples/vision-drone-governance/native-case/README.md) contains actual synthetic engineering outputs and reviewed evidence summaries. Source tests, exact ZIP/wheel installation, standalone stdio, each chat's native MCP calls and natural scheduled execution are separate layers. Neither source success nor a working offline demonstration proves native host loading, production adoption, real aircraft performance or a two-computer handoff. Final-source public CI and attachment hashes belong to the matching release.

## 简体中文

2026-11-16 的本地完整源码验证覆盖 **565 条唯一测试：559 通过、6 跳过，零失败、零错误**，实际环境为 Windows / Python 3.12.10。三个不重叠的模块分片覆盖当前完整测试集；运行期间内核、测试、Skill 和构建脚本摘要未改变。随后补充的 Skill 迁移说明和实例包成员清单，随最终包另行核对。

新增 20 项共享目录内核回归、8 项逐聊天接入验收回归，以及一项真实共享历史恢复回归。它们核对同目录原任务分别保留、逐聊天读取回执、明确转换旧单绑定、保存原字节前像、中断续办、并发争用身份，以及旧计划不能覆盖新共享入口。完整备份与独立恢复保留原任务、检查点和历史，隔离旧宿主路由，并让恢复副本保持待命。

完整测试还覆盖初始化前有界索引发现、选择连续性、来源身份、已有 Git 与未完成工作保全、回执恢复以及无人机治理的确定性回放。实际 Windows junction 回归模拟旧 pathlib API 边界；本地没有冒称使用 Python 3.11 运行。六项跳过原因保留在 JSON，涉及宿主符号链接权限及另选安装 wheel 的检查。CLI 与 **36 项 MCP 工具**共用引擎，四项 Skills 和两份引用核对随包一致性。

[真实合成对话实例](../examples/vision-drone-governance/native-case/README.zh-CN.md)收录实际工程产物与审阅后的证据摘要。源码、精确 ZIP/wheel 安装、独立 stdio、各聊天原生 MCP，以及自然定时执行分别留证。源码通过和离线演示可用，都不能代替原生加载、生产采用、真实飞行或双电脑接管的证明。最终源码 CI 与附件摘要归属对应发行对象。

## 繁體中文

2026-11-16 的本機完整原始碼驗證覆蓋 **565 條唯一測試：559 通過、6 跳過，零失敗、零錯誤**，實際環境為 Windows / Python 3.12.10。三個不重疊模組分片覆蓋目前完整測試集；執行期間內核、測試、Skill 與建置腳本摘要未改變。之後補充的 Skill 轉換說明及實例套件成員清單，隨最終套件另行核對。

新增 20 項共用目錄內核回歸、8 項逐聊天接入驗收回歸，以及一項真實共用歷史恢復回歸。驗證同目錄原任務分別保留、逐聊天讀取回執、明確轉換舊單綁定、原始位元組前像、中斷接續、並行身分衝突與拒絕舊計畫覆蓋新入口。完整備份及獨立恢復保留原任務、檢查點與歷史，隔離舊宿主路由，恢復副本保持待命。

完整測試也涵蓋初始化前有界索引發現、選擇連續性、來源身分、既有 Git 與未完成工作保全、回執恢復及無人機治理的確定性回放。真實 Windows junction 回歸模擬舊 pathlib API 邊界，不冒稱本機使用 Python 3.11 執行。六項跳過原因留於 JSON，包含宿主符號連結權限及另選安裝 wheel 的檢查。CLI 與 **36 項 MCP 工具**共用引擎，四項 Skills 及兩份引用核對套件一致性。

[真實合成對話實例](../examples/vision-drone-governance/native-case/README.zh-TW.md)收錄實際工程產物與審閱後的證據摘要。原始碼、精確套件安裝、獨立 stdio、各聊天原生 MCP 與自然排程執行分別留證；原始碼通過和離線演示可用不代表原生載入、生產採用、真實飛行或雙電腦接管。最終原始碼 CI 與附件摘要歸屬對應發行物件。
