# TaskCarry 0.2.0rc7

[Start here / 使用入口 / 使用入口](../START_HERE.md)

## 简体中文

本版为待复核的预发布候选。预发布是供提前使用和反馈的发行状态，尚未标为正式稳定版；本次候选在复核后才公开下载。

### 首次安装

下载完整产品包，按主手册建立独立治理窗口，用一条提示词接入已有项目。用户不需要先安装旧版，也不需要阅读升级过程或历史勘误。下载入口集中显示本版标识，手册专注于当前操作。

### 已有用户更新

新增独立更新指南：回到原治理窗口，发送更新提示词。助手核对实际安装和变化，按需处理说明、接入材料、工具包与宿主连接，保留原项目记录和配置。没有需要更新的内容时直接说明；仅剩重载时给出当前一步。

这是一条使用既有工具的对话式维护流程。软件包由宿主助手安装，setup 更新受管理文件，宿主负责加载连接；没有新增一键补丁命令或通用自动回退能力。`taskcarry upgrade` 仍只处理派生索引，不能用作包安装命令。

### 相对 RC6 的变化

- 把首次安装和已有用户更新分成两个入口，三语 README、入口页与主手册保持一致。
- 将版本沿革、兼容性和历史说明移出安装主流程，保留在本页及维护参考中；完整新包包含整理后的手册。
- 补充公开 setup Skill 的已有安装维护方法：按需更新、保留原 control 与工作、使用隔离候选环境核对、保全用户配置、核实实际连接、中断后继续。
- 构建时检查中央下载链接与包版本一致，并检查三语的安装及更新入口完整；发现旧下载目标或缺少更新入口时，在生成发行文件前停止。

RC6 的安全启动、无 Git 普通保存和恢复回执修正继续保留。旧包的历史记录保持对应原版本，不能替代本候选的验证。

### 验证范围

验证结果以本候选的复核报告和发行回执为准。包、源码、CLI、独立 stdio、原生宿主与实际采用分别记录；本页不把它们视为同一种验证。新包尚未发布时，下载链接只是该版本预定入口。

## English

This is a prerelease candidate for review, not a stable release. Download availability is determined by its release page.

New users get the complete package and use one installation prompt in an independent governance chat for their existing project. Existing users stay in their original governance chat and use a separate update prompt. The assistant checks what is needed, preserves project records and configuration, completes supported maintenance and gives only the remaining host action when one is necessary.

Compared with RC6, the three-language entry pages now separate these routes. Version history and compatibility details live in reference pages rather than repeated installation notices. The setup Skill describes existing-installation maintenance, candidate-runtime preparation, configuration preservation and continuation after interruption. Packaging rejects a current download link for the wrong version or a missing translated user route before creating artifacts.

The host assistant installs packages; setup manages integration files; the host reloads connections. This adds no one-click patch command or automatic rollback engine. `taskcarry upgrade` remains an index-rebuild action. RC6 reliability fixes remain included. Consult the candidate review and release receipts for verification results; package, source, CLI, standalone stdio, native-host activation and production adoption are recorded separately.

## 繁體中文

本版為供複核的預發布候選，尚未定為正式穩定版；下載是否開放以發布頁為準。

新使用者取得完整套件，在獨立治理視窗用一條安裝提示詞接入既有專案。既有使用者回到原治理視窗，使用獨立更新提示詞。助手判斷需要哪些更新、保留原專案記錄與設定、完成支援的維護；需要宿主操作時只提供目前一步。

相較 RC6，三語入口已分開這兩條路線，版本沿革與相容性細節集中於參考頁。setup Skill 補充既有安裝維護、候選執行環境準備、設定保全與中斷續辦方法。打包時若中央下載連結指向其他版本，或缺少任一語言的安裝／更新入口，會在產生發行檔案前停止。

套件由宿主助手安裝，setup 管理接入檔案，宿主重新載入連線；沒有新增一鍵補丁或自動回退引擎。`taskcarry upgrade` 仍是索引重建動作。RC6 可靠性修正繼續保留。驗證結果以本候選的複核報告與發行回執為準；套件、原始碼、CLI、獨立 stdio、原生宿主接入及生產採用分別記錄。
