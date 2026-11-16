# TaskCarry 0.2.0rc8 source validation

[Machine-readable results](VALIDATION_RESULTS.json) · [Release changes](RELEASE_0.2.0rc8.md) · [Drone example evidence](../examples/vision-drone-governance/EVIDENCE.md)

## English

The final local source outcomes on 2026-11-16 cover **536 unique tests: 530 passed, 6 skipped, zero remaining failures or errors**. The baseline suite used Windows / Python 3.12.10 and three disjoint module assignments. A private shard-launcher import-path omission initially prevented one module from loading; its 12 tests were then run successfully without repeating unrelated tests. Source files did not change during that baseline run.

Independent review then found that the new example's destination guard depended on a pathlib method absent from Python 3.11. The two-file correction uses the same link/reparse check as Core. Its entire seven-test module passed on Windows / Python 3.14.3, including two actual junction tests with the newer method temporarily removed. Those seven final outcomes supersede the earlier five example outcomes. This models the older API boundary; it is not a local Python 3.11 interpreter run. Each test's Python version is retained in the JSON.

New coverage exercises metadata-only discovery before project initialization, pagination and repeated cursors, source-qualified candidate identities, exact plans, concurrent saves, interrupted publication, changed selections, copied/standby roots and confirmation continuity across an unselected draft. The drone example checks retained task/checkpoint history, a shared scope change, four workbench entries, partial-publication continuation, Git WIP preservation and an independently restored standby with missing-receipt recovery. A release-membership regression excludes private discovery inventories.

The standard source wheel/sdist build is enabled. The six skips retain their exact reasons in the JSON: host symlink privileges and the separately selected installed-wheel check. CLI and **36 MCP tools** share the engine. Four packaged Skills and two references are checked for byte parity. Source and product archives use positive allowlists and exact membership/hash checks.

Keep evidence layers distinct: source regressions; an identified ZIP/wheel; fresh and previous-release update scenarios; standalone stdio; tools called in each native conversation; natural schedule delivery, AI execution and report delivery. The case report supplies its actual scope. Final-source public CI and release hashes belong to the matching GitHub release. No source test establishes production adoption, physical aircraft performance, unrestricted chat access, arbitrary cloud backup or a real multi-computer handoff.

## 简体中文

2026-11-16，本地最终源码结果覆盖 **536 条唯一测试：530 通过、6 跳过、无遗留失败或错误**。主体在 Windows / Python 3.12.10 上以三个不重叠的模块分片运行。私有启动脚本最初漏加测试导入目录，使一个模块未加载；随后单独运行其 12 项并全部通过，没有重跑无关测试。主体运行期间源码保持不变。

独立复核随后发现，新实例的目标目录检查依赖 Python 3.11 不具备的 pathlib 方法。两文件修正改用 Core 共用的链接与重解析点检查；受影响模块全部 7 项在 Windows / Python 3.14.3 通过，其中两项实际创建 junction 并临时移除较新的方法。最终七项替代了此前五项实例结果。此验证模拟旧 API 边界，不冒称本地使用 Python 3.11 运行。JSON 逐项保留实际 Python 版本。

新增覆盖包括：初始化前只保存索引元数据，分页与重复游标，按来源区分同名候选，精确计划，并发与写后中断续办，选择变更、复制/待机根目录，以及清空选择后旧确认仍不能跨范围复用。无人机实例验证原任务和检查点历史、共同范围变更、四工作台入口、部分发布续办、Git 未完成工作保全，以及恢复已落盘而回执缺失时的独立待机恢复。另有发行成员检查，防止私有发现草稿进入公开包。

标准源码 wheel/sdist 构建已启用。六个跳过项在 JSON 中分别说明宿主符号链接权限和须另选实际 wheel 的检查。CLI 与 **36 项 MCP 工具**共用实现；四项 Skills、两份引用以及源码/产品包的允许清单、成员和字节分别核对。

源码回归、精确 ZIP/wheel、新安装与上一公开版更新、独立 stdio、每个实际对话的原生工具、自然调度送达、AI 执行和报告送达分层记录。实例报告说明真实覆盖；最终源码 CI 和附件哈希归属对应 GitHub 发行对象。源码成功不表示生产采用、真实无人机性能、任意对话访问、任意网盘备份或真实跨电脑接管已验证。

## 繁體中文

2026-11-16，本機最終原始碼結果覆蓋 **536 條唯一測試：530 通過、6 跳過，無遺留失敗或錯誤**。主體以 Windows / Python 3.12.10、三個不重疊模組分片執行。私有啟動腳本最初漏加測試匯入目錄，導致一個模組未載入；其 12 項隨後單獨執行並全部通過，未重跑無關測試。主體執行期間原始碼保持不變。

獨立複核後，實例目標目錄檢查改用 Core 共用的連結與重解析點判斷，避免依賴 Python 3.11 沒有的 pathlib 方法。受影響模組全部 7 項在 Windows / Python 3.14.3 通過，包含兩項真實 junction 與移除新版方法的回歸；最終七項替代此前五項。這是模擬舊 API 邊界，不是本機 Python 3.11 執行證據。JSON 逐項保留實際版本。

新增驗證涵蓋初始化前有界索引發現、分頁與重複游標、來源身分、精確計畫、並行儲存、中斷接續、選擇變更、複製及待機根目錄，以及跨修訂的確認連續性。無人機實例實際驗證原任務與檢查點、共同範圍變更、四工作台、部分發布接續、Git 未完成工作保全與缺少回執時的獨立待機恢復。私有發現草稿另有公開套件排除回歸。

標準原始碼 wheel/sdist 建置已啟用。六個跳過原因在 JSON 內保留，涉及宿主符號連結權限及須另選實際 wheel 的檢查。CLI 與 **36 項 MCP 工具**共用實作；四項 Skills、兩份引用和發行成員位元組分別核對。

原始碼、精確套件、新安裝與上版更新、獨立 stdio、各對話原生工具、自然觸發、AI 執行和報告送達各自留證。最終原始碼 CI 與附件雜湊見對應 GitHub 發行，實例範圍見其證據說明；不由原始碼測試推論生產採用、真實無人機、任意對話/雲端存取或實體多電腦交接。
