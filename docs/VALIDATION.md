# RC9 verification / RC9 验证 / RC9 驗證

RC9 changes and exercised capabilities are mapped in [RC9_VERIFICATION.md](RC9_VERIFICATION.md). Exact-source regression, final package, installation, upgrade and CI results are recorded in the [release evidence](https://github.com/bryan123466/taskcarry/releases/download/v0.2.0rc9/RC9-VALIDATION.json) and [release page](https://github.com/bryan123466/taskcarry/releases/tag/v0.2.0rc9).

RC9 的功能与已完成演练见[验证对照](RC9_VERIFICATION.md)。本次源码回归、最终包、新安装、旧版升级和 CI 的实际结果随发行附件提供。以下保留 RC8 历史证据，不把旧结果冒充本版重跑。

可重复执行 / Reproduce: `python scripts/verify_release.py --output <evidence.json>`; `python scripts/verify_installed_wheel.py --directory <wheel-directory>`. Use an isolated temporary directory outside the checkout for fixtures that verify plain directories without Git ancestors.

---

# TaskCarry 0.2.0rc8 source validation

[Machine-readable results](VALIDATION_RESULTS.json) · [Release changes](RELEASE_0.2.0rc8.md) · [Complete simulator case](../examples/vision-drone-governance/simulation/README.md)

## English

The complete local source run on 2026-11-16 covers **565 unique tests: 559 passed, 6 skipped, zero failures or errors**, using Windows and Python 3.12.10. This evidence belongs to Core candidate `c3aac797da4b1f9ca9fc57581bd004d600ef2d31`. Three disjoint module assignments covered that suite, with engine, test, Skill and build-script hashes unchanged during the run. It is reused for the unchanged Core; later documentation, Skills and example/package changes are checked separately, not reported as another complete suite run.

Twenty shared-directory core regressions, eight per-chat onboarding regressions and an actual shared-history recovery regression cover separate original tasks in one directory, independent consumption, explicit legacy conversion, retained byte preimages, interruption recovery, concurrent identity claims and refusal to replay an old plan over a shared entry. Backup and independent restore retain tasks, checkpoints and history while quarantining old host routing and keeping the recovered writer in standby.

The suite also covers bounded metadata discovery before initialization, selection continuity, source-qualified identities, existing Git/WIP preservation, receipt recovery and the deterministic drone governance replay. Its actual Windows junction tests model the older pathlib API boundary; this local run is not a Python 3.11 interpreter run. The six skips retain their reasons in the JSON: host symbolic-link privileges and a separately selected installed-wheel check. CLI and **36 MCP tools** use one engine; four Skills and two references are checked for package parity.

The [complete exported simulator](../examples/vision-drone-governance/simulation/README.md) has passed **5 algorithm checks, 9 independent browser checks and 10 software verifier checks** in a relocated public copy. Its six app files and interface contract retain their original delivered bytes. The original independent report also verifies the hardware engineering documents. [Independent public-product review](../examples/vision-drone-governance/simulation/testing/public-product-review.md) passed the recorded 50-file manifest, ten checks and twelve claims. That result does not certify later LF-normalized bytes; the updated manifest and exact frozen package require separate verification. The [earlier fixed-event case](../examples/vision-drone-governance/native-case/README.md) is retained as history.

The [native acceptance summary](../examples/vision-drone-governance/simulation/evidence/native-acceptance.json) verifies **six actual chats**, each with successful native `doctor`/`status`, matching runtime/control/task and its own current-entry consumption. Four original professional chats passed after the user restarted Codex; governance and testing reuse earlier receipts for the same c3 runtime. The runtime disk fingerprint is `e1c8571120eea9eaaea60891a7cabef51cef1ab0e5c276d32318ae18262e6b90`. Raw `loaded_code_verified: false` and `native_acceptance_verified: false` are preserved: native acceptance comes from observed host calls and reviewed responses, not changing those engine flags.

Subsequent focused validation passed **20 source-pinning/release-screen checks** and **one standard wheel/sdist build check**. Build checks used a development build environment and a short synthetic temporary root to stay within Windows Git path limits. The build now checks simulation manifest membership, sizes and SHA-256 after source freezing; two added regressions exercise this guard and the exact resource allowlist. Final-source public CI and attachment hashes remain tied to the eventual release object. The [controlled continuation exercise](../examples/vision-drone-governance/simulation/continuity/README.md) is complete: the new algorithm chat passed its own native calls, current-entry consumption and three-frame pixel-threshold/connectivity check; the old chat returned read-only, and governance absorbed the result. Original task/checkpoint, Git state, 25 retained files and four history preimages were preserved. The old chat did not record a new consume; its historical NOT_VERIFIED state does not negate the separate observed read-only acknowledgment. Natural long-term scheduling remains unverified. Accordingly, no simulator or native result establishes real aircraft performance, production adoption or two-computer handoff.

## 简体中文

2026-11-16 的本地完整源码验证覆盖 **565 条唯一测试：559 通过、6 跳过，零失败、零错误**，实际环境为 Windows / Python 3.12.10。这份证据属于内核候选 `c3aac797da4b1f9ca9fc57581bd004d600ef2d31`。三个不重叠的模块分片覆盖该套测试；运行期间内核、测试、Skill 和构建脚本摘要未改变。后续内核未变，复用这份证据；文档、方法与实例包的新增修改分别验证，不冒称完整源码套件又跑过一遍。

新增 20 项共享目录内核回归、8 项逐聊天接入验收回归，以及一项真实共享历史恢复回归。它们核对同目录原任务分别保留、逐聊天读取回执、明确转换旧单绑定、保存原字节前像、中断续办、并发争用身份，以及旧计划不能覆盖新共享入口。完整备份与独立恢复保留原任务、检查点和历史，隔离旧宿主路由，并让恢复副本保持待命。

完整测试还覆盖初始化前有界索引发现、选择连续性、来源身份、已有 Git 与未完成工作保全、回执恢复以及无人机治理的确定性回放。实际 Windows junction 回归模拟旧 pathlib API 边界；本地没有冒称使用 Python 3.11 运行。六项跳过原因保留在 JSON，涉及宿主符号链接权限及另选安装 wheel 的检查。CLI 与 **36 项 MCP 工具**共用引擎，四项 Skills 和两份引用核对随包一致性。

[完整导出的仿真实例](../examples/vision-drone-governance/simulation/README.zh-CN.md)已在重新定位的公开副本中通过 **5 项算法、9 项独立浏览器和 10 项软件验证**。六个应用文件与合同保留原交付字节，原独立报告还核验了硬件工程资料。[独立公开产品审阅](../examples/vision-drone-governance/simulation/testing/public-product-review.md)已通过当时的 50 文件清单、10 项检查和 12 项宣称。随后统一 LF 会改变部分字节，这份通过不替代新清单及最终冻结包的核验；[早期固定事件实例](../examples/vision-drone-governance/native-case/README.zh-CN.md)保留为历史阶段。

[原生汇总](../examples/vision-drone-governance/simulation/evidence/native-acceptance.json)核实了 **6 个真实聊天**各自的原生 `doctor/status`、对应运行包／control／任务，以及自己的当前入口消费。四个原专业窗口在用户重启 Codex 后通过；治理和独立测试复用相同 c3 运行包的较早回执。磁盘运行代码摘要为 `e1c8571120eea9eaaea60891a7cabef51cef1ab0e5c276d32318ae18262e6b90`。原响应中的 `loaded_code_verified: false` 和 `native_acceptance_verified: false` 原样保留，验收依据是实际宿主调用与回读证据。

后续另通过 **20 项源码固定／发行筛查和 1 项标准 wheel/sdist 构建检查**。构建使用开发构建环境和较短的合成临时根目录，以适应 Windows Git 路径限制。构建在冻结源码后再次核对实例清单成员、大小及 SHA-256，新增两项回归覆盖摘要防护与精确资源白名单。最终源码 CI、包及附件哈希随实际发行对象核对。[受控接续演练](../examples/vision-drone-governance/simulation/continuity/README.zh-CN.md)已完整完成：新算法聊天通过自己的原生调用、当前入口消费与三帧像素阈值／连通性检查；旧窗口只读回看，治理吸收结果。原任务、检查点、Git 状态、25 个保留文件及四份历史前像均保留。旧窗口按要求未新增 consume，历史 NOT_VERIFIED 不等于没有实际只读回看。自然长期调度仍待验。仿真与原生通过不代表真实飞行、生产采用或双电脑接管。

## 繁體中文

2026-11-16 的本機完整原始碼驗證覆蓋 **565 條唯一測試：559 通過、6 跳過，零失敗、零錯誤**，實際環境為 Windows / Python 3.12.10。這份證據屬於內核候選 `c3aac797da4b1f9ca9fc57581bd004d600ef2d31`。三個不重疊模組分片覆蓋該測試集；執行期間內核、測試、Skill 與建置腳本摘要未改變。後續內核未變，沿用這份證據；文件、方法及實例套件的新修改分別驗證，不冒稱完整原始碼套件又執行一遍。

新增 20 項共用目錄內核回歸、8 項逐聊天接入驗收回歸，以及一項真實共用歷史恢復回歸。驗證同目錄原任務分別保留、逐聊天讀取回執、明確轉換舊單綁定、原始位元組前像、中斷接續、並行身分衝突與拒絕舊計畫覆蓋新入口。完整備份及獨立恢復保留原任務、檢查點與歷史，隔離舊宿主路由，恢復副本保持待命。

完整測試也涵蓋初始化前有界索引發現、選擇連續性、來源身分、既有 Git 與未完成工作保全、回執恢復及無人機治理的確定性回放。真實 Windows junction 回歸模擬舊 pathlib API 邊界，不冒稱本機使用 Python 3.11 執行。六項跳過原因留於 JSON，包含宿主符號連結權限及另選安裝 wheel 的檢查。CLI 與 **36 項 MCP 工具**共用引擎，四項 Skills 及兩份引用核對套件一致性。

[完整匯出的模擬實例](../examples/vision-drone-governance/simulation/README.zh-TW.md)已在重新定位的公開副本通過 **5 項演算法、9 項獨立瀏覽器及 10 項軟體驗證**。六個應用檔案與合約保留原交付位元組，原獨立報告亦核驗硬體工程資料。[獨立公開產品審閱](../examples/vision-drone-governance/simulation/testing/public-product-review.md)已通過當時的 50 檔清單、10 項檢查與 12 項宣稱。後續統一 LF 會改變部分位元組，這份通過不能替代新清單與最終凍結套件核驗；[早期固定事件實例](../examples/vision-drone-governance/native-case/README.zh-TW.md)保留為歷史階段。

[原生彙總](../examples/vision-drone-governance/simulation/evidence/native-acceptance.json)核實 **6 個真實對話**各自的原生 `doctor/status`、對應執行套件／control／任務，以及自己的目前入口消費。四個原專業視窗在使用者重新啟動 Codex 後通過；治理與獨立測試沿用相同 c3 執行套件的較早回執。磁碟程式摘要為 `e1c8571120eea9eaaea60891a7cabef51cef1ab0e5c276d32318ae18262e6b90`。原回應的 `loaded_code_verified: false` 與 `native_acceptance_verified: false` 原樣保留，驗收依據是實際宿主呼叫與讀回證據。

後續另通過 **20 項原始碼固定／發行篩查和 1 項標準 wheel/sdist 建置檢查**。建置使用開發建置環境及較短的合成暫存根目錄，以符合 Windows Git 路徑限制。建置在凍結原始碼後再次核對實例清單成員、大小及 SHA-256，新增兩項回歸涵蓋摘要防護與精確資源白名單。最終原始碼 CI、套件與附件雜湊依實際發行物件核對。[受控接續演練](../examples/vision-drone-governance/simulation/continuity/README.zh-TW.md)已完整完成：新演算法對話通過自身原生呼叫、目前入口消費及三幀像素閾值／連通性檢查；舊視窗唯讀回看，治理吸收結果。原任務、檢查點、Git 狀態、25 個保留檔案及四份歷史前像均保留。舊視窗依要求未新增 consume，歷史 NOT_VERIFIED 不等於沒有實際唯讀回看。自然長期排程仍待驗。模擬和原生通過不代表真實飛行、生產採用或雙電腦接管。
