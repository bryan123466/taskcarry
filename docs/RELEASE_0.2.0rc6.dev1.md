# 0.2.0rc6.dev1 — local development candidate

This candidate follows the released 0.2.0rc5 baseline. It is not a published release or evidence of installation in an existing project.

Generated MCP configuration now starts the fixed interpreter with `-I -X utf8` and explicitly selects the package location that generated setup. A source working directory or inherited `PYTHONPATH` can no longer select a different TaskCarry copy. If the selected package is missing, startup fails without falling back. Explicit source setup remains available for development and binds that source.

Use the installed interpreter with `-I -X utf8 -m taskcarry` when running setup or governance CLI commands. Review setup preview before updating an older managed fragment. User edits remain protected, installation identity is retained, and interrupted updates resume with their original candidate. Review and reload manually activated host configuration separately, then verify the module location through the actual host's doctor call. No control-store migration, receiving operation, package installation or host reload is performed by this change.

Regression coverage includes real MCP subprocesses from source and other directories, an actual installed candidate wheel, conflicting environment import settings, Unicode, missing-package failure, legacy setup updates, user-file preservation and post-write interruption recovery. Maintainer validation results and limitations are recorded in docs/VALIDATION.md in the source repository (excluded from the product archive). Historical rc5 validation remains separately identified.

## 简体中文

这是接续已发布 rc5 的本地开发候选，尚未发布，也不表示既有项目已经安装。生成的 MCP 配置默认使用固定解释器、`-I -X utf8`，并明确选择生成 setup 时使用的包位置。源码 cwd 或继承的 `PYTHONPATH` 不会让它改用另一份 TaskCarry；选定包缺失时直接失败。显式源码 setup 仍可用于开发，并绑定该源码。

setup 与治理 CLI 使用固定安装解释器和 `-I -X utf8 -m taskcarry`。旧受管理片段先预览再更新，保留用户修改及安装身份；中断更新使用原候选接续。已手动启用的宿主配置另行审阅、重载，并在实际宿主调用 doctor 核对模块位置。本改动不迁移 control、不执行接收、不安装升级、不代宿主重载。回归覆盖实际 MCP/候选 wheel、源码及其他 cwd、环境污染、中文、缺包、旧安装更新和中断保全；实测结果见验证记录。

## 繁體中文

這是接續已發布 rc5 的本機開發候選，尚未發布，也不表示既有專案已經安裝。產生的 MCP 設定預設使用固定直譯器、`-I -X utf8`，並明確選擇產生 setup 時使用的套件位置。原始碼 cwd 或繼承的 `PYTHONPATH` 不會讓它改用另一份 TaskCarry；選定套件缺失時直接失敗。明確的原始碼 setup 仍可用於開發，並綁定該原始碼。

setup 與治理 CLI 使用固定安裝直譯器和 `-I -X utf8 -m taskcarry`。舊受管理片段先預覽再更新，保留使用者修改及安裝身分；中斷更新使用原候選接續。已手動啟用的宿主設定另行審閱、重載，並在實際宿主呼叫 doctor 核對模組位置。本改動不遷移 control、不執行接收、不安裝升級、不代宿主重載。回歸涵蓋實際 MCP/候選 wheel、原始碼及其他 cwd、環境污染、中文、缺包、舊安裝更新和中斷保全；實測結果見驗證記錄。
