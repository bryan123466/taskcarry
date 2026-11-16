# TaskCarry 0.2.0rc8

[Get started](../START_HERE.md) · [首次安装](zh-CN/windows-example.md) · [更新与接续](zh-CN/updating.md) · [Drone project case / 无人机实例](../examples/vision-drone-governance/README.md)

## 简体中文

这次更新把已有 Codex 对话接入项目治理的过程收拢到三步。先准备 `TaskCarry/toolkit`，在外层目录打开治理对话，直接发送主提示词；随后由治理帮助选项目、接续原窗口、补充需要的职责并完成配置；最后给出实际结果、缺项和下一步。用户继续在原专业窗口工作。

相对上一公开版的变化：

- **首次安装更少手工填写。** 手册只展示用户需要建立的两个目录，助手从 `toolkit/` 核对产品入口。完整生成目录移到独立实例，手动配置放在后备页。
- **先选项目，再读相关历史。** 助手整理当前宿主实际可见的对话索引，说明覆盖范围和分页，再给出候选项目。用户确认后才读取所选历史。索引不等于完整对话，也不承诺访问所有账户或设备。
- **选择过程可以接续。** 新增共享 `discovery` 操作，保存有界索引覆盖、候选理由、用户选择与后续接入记录的关联。查看与计划不创建项目状态；执行须核对计划和原修订。中断后继续已有草稿，不会为每个候选项目创建一份治理。
- **已有治理有明确的接续入口。** TaskCarry 更新、其他工具的治理、仅有治理对话分开处理；保留现有规则和状态，先评估共存或迁移范围。
- **反馈围绕用户下一步。** 三语手册和 Skill 要求给出已填好的原窗口接入内容、新窗口建立位置和激活方法。实际连接、读到共同记忆、配置时段与自然定时执行分别报告。
- **独立的视觉避障无人机实例。** 软件、视觉算法、硬件概念和产品推广通过共同决定协作。它展示如何处理原有接口分歧以及“先完成室内离线演示”的范围变更，不表示真实模型、硬件或飞行已完成。
- **入口与包保持一致。** 三语 README、产品入口、手册、安装后备页、随包方法与构建清单同步；临时对话发现草稿不会进入公开发行包。

已有用户把[更新与接续提示词](zh-CN/updating.md)交给原治理窗口即可开始评估。更新工具不重建项目，不自动升级正在运行的治理，也不把已完成的历史变成新任务。RC 表示预发布候选：可下载体验，后续正式版仍会有单独的发行对象。

## English

This update brings existing Codex conversations into a three-step, assistant-led setup: prepare `TaskCarry/toolkit` and send the main prompt, follow governance through project selection and connection, then review actual results and next actions. Keep working in the original specialist chats.

- The guide shows only the two directories users create. The assistant locates the product entry; generated directories and manual commands move to the case and fallback guide.
- Host-visible conversation indexes are reviewed before project selection. Coverage and pagination stay explicit; selected history is read after confirmation.
- The shared `discovery` action retains bounded index coverage, candidate reasons, confirmed selection and the link to onboarding. Status and planning do not initialize a control store. Execution validates the exact plan and revision so interrupted selection can resume.
- Existing TaskCarry installations, other governance tools and governance-only chats have distinct continuation routes that preserve existing rules and state.
- Filled-in activation instructions and observable per-chat receipts guide the user. Native connection, shared-memory consumption, schedule configuration and natural execution remain separate results.
- A standalone vision-drone case connects software, algorithms, hardware concepts and product communication around a shared indoor offline-demo scope. It does not claim a trained model, working aircraft or flight validation.
- Three-language entrypoints, packaged methods and build membership agree. Local discovery drafts are excluded from public packages.

Existing users start in their original governance chat with the [update guide](en/updating.md). RC means a prerelease candidate available for review; installation and a later stable release are separate actions.

## 繁體中文

這次更新把既有 Codex 對話接入專案治理的過程收斂為三步：準備 `TaskCarry/toolkit` 並發送主提示詞；由治理帶著選專案、接續原視窗與完成配置；最後複核實際結果和下一步。使用者繼續在原專業視窗工作。

- 主手冊只列出需要手動建立的兩個目錄，由助手核對產品入口；生成目錄與手動命令移至獨立實例及後備頁。
- 先整理宿主可見的對話索引，說明範圍及分頁；使用者選定專案後才讀取相關歷史。
- 共用 `discovery` 操作保留有界索引覆蓋、候選理由、確認選擇及後續接入關聯。查看和規劃不初始化治理狀態；執行核對精確計畫和修訂，中斷後可接續。
- 既有 TaskCarry、其他治理工具及僅有治理對話分流處理，保留原規則與狀態。
- 提供填好的原視窗接入內容、新視窗位置與激活方法；原生連接、共同記憶讀取、時段配置和自然執行分別回報。
- 獨立視覺避障無人機實例讓軟體、演算法、硬體概念及產品推廣依共同決定協作，處理接口分歧和室內離線演示的範圍變更，不宣稱真實模型、硬體或飛行已完成。
- 三語入口、隨包方法與建置清單一致，本機發現草稿排除在公開套件外。

既有使用者把[更新與接續提示詞](zh-TW/updating.md)交給原治理視窗開始評估。RC 是供複核的預發行候選，公開發行不代表已安裝，後續正式版仍是獨立發行對象。

## Verification / 验证 / 驗證

[Source results](https://github.com/bryan123466/taskcarry/blob/v0.2.0rc8/docs/VALIDATION.md) describe the applicable test run. The [case evidence](../examples/vision-drone-governance/README.md) distinguishes deterministic replay, actual native chats and any observed scheduled execution. Exact source, CI and downloadable artifact hashes belong to the matching GitHub release. Real aircraft, production adoption, arbitrary host access and multi-computer operation are outside this example.
