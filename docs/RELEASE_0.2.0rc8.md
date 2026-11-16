# TaskCarry 0.2.0rc8

[Get started](../START_HERE.md) · [首次安装](zh-CN/windows-example.md) · [更新与接续](zh-CN/updating.md) · [Drone simulator / 无人机仿真](../examples/vision-drone-governance/simulation/README.md)

## 简体中文

这次更新把已有 Codex 对话接入项目治理的过程收拢到三步。先准备 `TaskCarry/toolkit`，在外层目录打开治理对话，直接发送主提示词；随后由治理帮助选项目、接续原窗口、补充需要的职责并完成配置；最后给出实际结果、缺项和下一步。用户继续在原专业窗口工作。

相对上一公开版的变化：

- **首次安装更少手工填写。** 手册只展示用户需要建立的两个目录，助手从 `toolkit/` 核对产品入口。完整生成目录移到独立实例，手动配置放在后备页。
- **先选项目，再读相关历史。** 助手整理当前宿主实际可见的对话索引，说明覆盖范围和分页，再给出候选项目。用户确认后才读取所选历史。索引不等于完整对话，也不承诺访问所有账户或设备。
- **选择过程可以接续。** 新增共享 `discovery` 操作，保存有界索引覆盖、候选理由、用户选择与后续接入记录的关联。查看与计划不创建项目状态；执行须核对计划和原修订。中断后继续已有草稿，不会为每个候选项目创建一份治理。
- **已有治理有明确的接续入口。** TaskCarry 更新、其他工具的治理、仅有治理对话分开处理；保留现有规则和状态，先评估共存或迁移范围。
- **反馈围绕用户下一步。** 三语手册和 Skill 要求给出已填好的原窗口接入内容、新窗口建立位置和激活方法。实际连接、读到共同记忆、配置时段与自然定时执行分别报告。
- **原窗口加载 MCP 有明确操作。** 在本次 Windows Codex 实测中，专业目录配置、打开并信任后，四个原窗口仍未加载服务；用户重启后原生调用成功。治理现在给出已有目录、Ctrl+O／打开项目、信任、集中重启一次、返回原聊天验收的完整操作。新聊天先核对实际连接，不默认每建一窗就重启；已验收窗口无需重复，不要求重建聊天或重装产品。
- **原聊天可以共用原目录。** 连接与 Skills 按真实目录复用，当前任务入口按原聊天分别选择；同目录两个聊天不会再覆盖一个入口，也不会用其中一个的已读回执代替另一个。旧单任务配置可明确转换，保留原任务、检查点和历史前像。独立恢复会停用旧机器的路由，等待重新核对接入。
- **聊天中断时按原任务接续。** 四项 Skills 补充按需替代窗口的方法：先核旧窗口和后台动作已停、确认实际效果，再让新真实聊天沿原 control、任务、检查点与成果继续。[合成接续实例](../examples/vision-drone-governance/simulation/continuity/README.zh-CN.md)已完成新窗口原生连接、自己的消费与新增验证，旧窗口只读回看，治理吸收结果并给出下一步。无需预建空备用，也不承诺修复宿主压缩或找回未保存内容。
- **读取回执的调用说明完整。** 文档明确 `workbench consume` 的十一项 proof 字段、control 内证据文件与实际哈希，并说明执行和消费不重复传入 `routing`。已记录回执与实际原生加载仍是两类证据；参数错误只补正确调用。
- **可运行的图像驱动无人机仿真。** 零散软件、算法、硬件聊天在治理下形成共同合同，再加入产品与独立测试职责。离线页面以真实生成像素驱动规则检测和 9 × 9 二维移动，提供三场景、暂停／重置／日志导出、硬件工程资料、独立浏览器验证与产品演示。早期固定事件回放原样保留为历史阶段；新实例不宣称训练模型、实体硬件或实飞完成。
- **入口与包保持一致。** 三语 README、手册、四项 Skills 与构建正向清单同步。完整实例逐文件列入产品包；冻结源码后再对实际打包字节核对清单成员、大小和 SHA-256，实例文本统一 LF，防止工作树与 Git 字节差异使清单失效。可复现脚本、方法引用与哈希清单接受相同隐私检查，临时草稿、原始回执和本机资料仍留在私有目录。

已有用户把[更新与接续提示词](zh-CN/updating.md)交给原治理窗口即可开始评估。更新工具不重建项目，不自动升级正在运行的治理，也不把已完成的历史变成新任务。RC 表示预发布候选：可下载体验，后续正式版仍会有单独的发行对象。

## English

This update brings existing Codex conversations into a three-step, assistant-led setup: prepare `TaskCarry/toolkit` and send the main prompt, follow governance through project selection and connection, then review actual results and next actions. Keep working in the original specialist chats.

- The guide shows only the two directories users create. The assistant locates the product entry; generated directories and manual commands move to the case and fallback guide.
- Host-visible conversation indexes are reviewed before project selection. Coverage and pagination stay explicit; selected history is read after confirmation.
- The shared `discovery` action retains bounded index coverage, candidate reasons, confirmed selection and the link to onboarding. Status and planning do not initialize a control store. Execution validates the exact plan and revision so interrupted selection can resume.
- Existing TaskCarry installations, other governance tools and governance-only chats have distinct continuation routes that preserve existing rules and state.
- Filled-in activation instructions and observable per-chat receipts guide the user. Native connection, shared-memory consumption, schedule configuration and natural execution remain separate results.
- Windows Codex instructions now name the existing folder, Ctrl+O/Open project, trust, one consolidated restart and return to the original chat. In this exercise, all four professional chats began passing native calls after that restart. Check a new chat's actual connection first; creating a chat does not automatically require another restart. Already verified windows need no repeat; no new chat or reinstall is required merely to load MCP.
- Original chats can share their existing directory, MCP connection and Skills while selecting separate task entries. Publishing or consuming one chat's entry no longer replaces or certifies another's. Explicit conversion retains legacy tasks, checkpoints and setup preimages; isolated recovery disables old-machine routing until reconnection is verified.
- The four Skills explain on-demand chat continuation: stop the old writer and background operations, inspect effects, then retain the original control, task, checkpoint and saved work under the new actual chat identity. The [synthetic continuation case](../examples/vision-drone-governance/simulation/continuity/README.md) completed the replacement's own native access, consumption and new verification, the old chat's read-only return and governance absorption. No empty spare is required. Host compaction repair and unsaved context remain outside this method.
- The `workbench consume` example specifies its eleven proof fields, a hashed evidence file under the control and omission of the planning-only `routing` selector. Recorded consumption and actual native loading remain distinct; rejected arguments require a corrected call, not repeated setup.
- A runnable image-driven drone case joins software, algorithms, hardware engineering documents, independent testing and product presentation. Generated pixels drive a rule-based detector and movement through a 9 × 9 discrete 2D world, with three scenes, pause/reset and JSON export. The earlier fixed-event replay stays as a historical milestone; there is no trained-model, physical-hardware or real-flight claim.
- Three-language entrypoints, four Skills and positive package membership are synchronized. The complete case, portable verification scripts and hash manifest are explicitly included and screened. After source freezing, packaging checks exact membership, byte sizes and SHA-256; LF-normalized example text prevents checkout conversion from invalidating the manifest. Local discovery drafts, raw host receipts and personal machine data remain private.

Existing users start in their original governance chat with the [update guide](en/updating.md). RC means a prerelease candidate available for review; installation and a later stable release are separate actions.

## 繁體中文

這次更新把既有 Codex 對話接入專案治理的過程收斂為三步：準備 `TaskCarry/toolkit` 並發送主提示詞；由治理帶著選專案、接續原視窗與完成配置；最後複核實際結果和下一步。使用者繼續在原專業視窗工作。

- 主手冊只列出需要手動建立的兩個目錄，由助手核對產品入口；生成目錄與手動命令移至獨立實例及後備頁。
- 先整理宿主可見的對話索引，說明範圍及分頁；使用者選定專案後才讀取相關歷史。
- 共用 `discovery` 操作保留有界索引覆蓋、候選理由、確認選擇及後續接入關聯。查看和規劃不初始化治理狀態；執行核對精確計畫和修訂，中斷後可接續。
- 既有 TaskCarry、其他治理工具及僅有治理對話分流處理，保留原規則與狀態。
- 提供填好的原視窗接入內容、新視窗位置與激活方法；原生連接、共同記憶讀取、時段配置和自然執行分別回報。
- Windows Codex 操作明確列出既有目錄、Ctrl+O／開啟專案、信任、集中重新啟動一次，以及回原對話驗收。本次四個專業視窗均在使用者重啟後通過原生呼叫；新對話先核對實際連線，不預設每建一窗便重啟。已驗收視窗不重做，不為載入 MCP 重建對話或重裝產品。
- 原聊天可共用既有目錄、MCP 連線與 Skills，並依原聊天選擇各自的任務入口；其中一個的發布或已讀回執不會覆蓋或證明另一個。明確轉換保留舊任務、檢查點與設定前像，獨立恢復後停用舊機器路由，等待重新核對連線。
- 四項 Skills 補充按需替代視窗的方法：先核對舊視窗與背景動作停止、確認實際效果，再讓新真實對話沿原 control、任務、檢查點及成果接續。[合成接續實例](../examples/vision-drone-governance/simulation/continuity/README.zh-TW.md)已完成新視窗原生連線、自身消費及新增驗證，舊視窗唯讀回看，治理吸收結果並給出下一步。無需預建空備用，也不承諾修復宿主壓縮或找回未儲存內容。
- `workbench consume` 範例明確列出十一項 proof 欄位、control 內證據檔案與實際雜湊，執行與消費不重複傳入 `routing`。已記錄回執與實際原生載入分別驗證；參數錯誤只補正確呼叫。
- 可執行的影像驅動無人機模擬連結軟體、演算法、硬體工程資料、獨立測試與產品展示。生成像素驅動規則偵測及 9 × 9 離散二維移動，提供三場景、暫停／重設與 JSON 匯出。早期固定事件重播保留為歷史階段，不宣稱訓練模型、實體硬體或實飛完成。
- 三語入口、四項 Skills 與建置正向清單同步，完整實例、可重現腳本及雜湊清單逐檔納入並接受隱私檢查。凍結原始碼後，建置再次核對實際套件的成員、位元組大小及 SHA-256；實例文字統一 LF，避免 Git 轉換使清單失效。本機草稿、原始回執與個人機器資料保留於私有目錄。

既有使用者把[更新與接續提示詞](zh-TW/updating.md)交給原治理視窗開始評估。RC 是供複核的預發行候選，公開發行不代表已安裝，後續正式版仍是獨立發行對象。

## Verification / 验证 / 驗證

Validation reuses the unchanged Core's complete local suite of 565 tests (559 passed, 6 skipped), with 20 later source-pinning/release-screen checks, one standard wheel/sdist build check and exported-simulator replay recorded separately. Six chats have their own successful native calls and current-entry consumption for the recorded batches; the four professional chats passed after restart, while governance and testing retain their earlier matching-runtime evidence. The bundled [case evidence](../examples/vision-drone-governance/EVIDENCE.md) and [native summary](../examples/vision-drone-governance/simulation/evidence/native-acceptance.json) distinguish those observations from natural scheduled execution.

This document describes the local RC8 candidate. [Independent review](../examples/vision-drone-governance/simulation/testing/public-product-review.md) passed the recorded 50-file public product snapshot, including ten checks and twelve claims; subsequent line-ending normalization changes file bytes and needs separate manifest verification. The [controlled continuation exercise](../examples/vision-drone-governance/simulation/continuity/README.md) is complete: the new algorithm chat passed its own native access, current-entry consumption and three-frame pixel-threshold/connectivity check; the old chat returned read-only, and governance absorbed the new evidence. Its receipts are separate from the earlier six-chat batch and product review. Exact final source, matching CI and downloadable artifact hashes belong to the actual GitHub prerelease after publication; this file is not a publication receipt. Real aircraft, production adoption, arbitrary host access and multi-computer operation remain outside this example.
