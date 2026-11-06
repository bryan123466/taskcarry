# 私有远端、备份恢复与多电脑协作

先完成[本地对话式接入](windows-example.md)。选择私有远端、文件存储或另一台电脑时，再使用本参考；具体安装命令保留在[手动后备](manual-setup.md)。

[返回操作手册](operation-manual.md) · [English](../en/remote-and-multicomputer.md) · [繁體中文](../zh-TW/remote-and-multicomputer.md) · [命令参考](../COMMANDS.md)

本地治理 Git 保存、原治理窗口的定时任务和官方更新检查属于标准接入。下述私有远端与多电脑流程是按需扩展，尚未经过两台实体电脑的端到端验证；它组合 Git 操作与现有本地 TaskCarry 接口，已提供所选本地恢复集与 standby 移交能力；远端传输和真实第二宿主验收仍分别核对。

标准本地保存使用明确文件清单，保全原 Git 暂存区与未完成工作，只有选定内容变化才形成提交；排除运行中的 `.taskcarry` 数据库、runtime、下载包和凭据。持续工作的窗口保留真实任务与工作区关联，提交署名或对话 ID 本身不能证明这些关联。原资料可留在原处，大型外部产物以版本化引用和分别核对的存储覆盖衔接。

选择网盘时，同步已封存的静态备份包；捕获、本地字节核验、上传、下载和隔离恢复分别留证。写入本地同步目录不证明云端已经上传或另一台电脑能够恢复。不把活跃 `.taskcarry` 或 Git 元数据交给互相竞争的后台同步；加密密钥与加密备份分开保管。

所有 `<...>` 都是需要替换的占位符。`python` 应指向已经安装 TaskCarry 的 Python 环境。JSON 文件保存为 UTF-8；不要把示例中的占位符直接执行。Git 推送会向所选远端传送资料，应先确认仓库、访问者和本次授权范围。

<a id="private-git"></a>

## 4. 私有 Git 在线记录库与恢复备份

### 4.1 先分清哪些内容保存在哪里

[本步骤可直接复制的 Windows 示例](manual-setup.md)

| 内容 | 推荐保存位置 | 恢复时能提供什么 |
|---|---|---|
| 选定的代码、文档、稳定成果 | 私有 Git 仓库，完成 commit 和 push | 已推送的文件版本与提交历史 |
| 精选项目记忆：目标、决策、当前节点、下一步、来源 | 私有 Git 中的普通 Markdown/JSON 文件 | 可跨电脑阅读的项目接续说明 |
| TaskCarry 任务、阶段、操作与经验记录 | 本机治理目录的 `.taskcarry/state.sqlite3` | 本机工具的状态与原始记录 |
| 检查点文件对象 | 同一治理目录的 `.taskcarry/objects/` | 明确选中并保存过的文件及检查点层次 |
| 未保存的编辑器内容、未纳入检查点的文件 | 原程序或工作区；需要单独保存/备份 | Git 和 TaskCarry 不会自动捕获它们 |
| 视频、安装包、大型数据等 | 经授权的独立文件存储；Git 保存位置、大小和哈希说明 | 找到并核对文件，不代表文件已上传或可访问 |

**私有 Git 不是整个电脑或治理数据库的自动镜像。** 只有已经提交并推送的选定文件才会到达远端；忽略文件、未提交成果和本机聊天历史不会因此自动保存。GitHub 普通 Git 文件超过 100 MiB 会被拒绝；大文件应另选存储或明确配置 Git LFS，TaskCarry 不自动配置它们。[GitHub 文件限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

### 4.2 建立私有远端，明确谁能推进主线

[本步骤可直接复制的 Windows 示例](manual-setup.md)

1. 在自己的 Git 托管服务创建**私有**仓库，检查成员权限。接入已有项目时，不要让新仓库自动生成与本地历史无关的 README 或初始提交。
2. 选定一台电脑作为集成主机。其专用干净接收工作区是唯一推进远端 `main` 的位置；其他电脑使用任务分支。
3. 在接收工作区核对远端、分支、工作区和待推送提交：

```text
git -C "<A_BASELINE>" status --short
git -C "<A_BASELINE>" branch --show-current
git -C "<A_BASELINE>" remote -v
git -C "<A_BASELINE>" log -5 --oneline
```

仅当该工作区尚无 `origin` 时添加：

```text
git -C "<A_BASELINE>" remote add origin "<PRIVATE_REPOSITORY_URL>"
```

若已有 `origin`，先核对地址，不要自动覆盖。接收工作区的本地分支不必也叫 `main`。确认本次已接收成果适合上传后，精确推送当前基线：

```text
git -C "<A_BASELINE>" push -u origin HEAD:refs/heads/main
git -C "<A_BASELINE>" rev-parse HEAD
git -C "<A_BASELINE>" ls-remote origin refs/heads/main
```

后两条的提交哈希应一致。被拒绝时先查原因，不强推。若远端已有不同历史或其他写入，先核对差异与写入责任。**这是原生 Git 推送，不是 TaskCarry 的 `reconcile` 或内建远端回执。** 建议使用托管平台的分支保护/权限限制来落实唯一主线写入者；仅在提示词里约定无法形成跨机锁。

### 4.3 把有用记忆保存为普通项目文件

[本步骤可直接复制的 Windows 示例](manual-setup.md)

在一个已登记、负责文档的专业工作区维护例如 `project-memory/current.md`，内容包括：

- 任务标识、目标、当前阶段，以及活跃/暂停/等待状态。
- 已接受的阶段和可查的提交、文件路径；业务验收与技术接收分别说明。
- 当前有效决定、适用范围、来源；过时决定指向其后继。
- 尚未完成的工作、检查点标识、下一步，以及只在真正需要时提出的用户决定。
- 大文件的位置、哈希及备份是否已实际验证；不把凭据写进记录。

这份说明是经整理的项目接续记忆，不是模型权重、全部私人聊天或可直接恢复的数据库。可以额外导出 `status`，但其中可能包含本机路径与内部任务信息；先检查访问范围和内容。原始导出适合保存在备份目录，进 Git 的版本可只保留必要字段。

PowerShell 7 导出示例（目标父目录已存在）：

```powershell
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status | Set-Content -LiteralPath "<SNAPSHOT>/status.json" -Encoding utf8
```

检查 JSON 中 `ok` 为 `true`，并记下采集时间。不要把失败输出当成正常状态。整理后的记忆文件也应走普通专业交付与接收；不要为写摘要直接弄脏专用接收工作区。精确提交示例：

```text
git -C "<MEMORY_WORKSPACE>" diff -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" add -- project-memory/current.md
git -C "<MEMORY_WORKSPACE>" diff --cached --name-only
git -C "<MEMORY_WORKSPACE>" commit -m "Update current project handoff"
```

提交前两次检查暂存区；若存在不属于本次交付的暂存内容，停止这一步并保留它，不混合提交。随后按主手册声明阶段，由集成主机接收并推送。记忆文件进入 Git 不会自动导入另一台电脑的 TaskCarry 状态库或模型记忆。

可直接交给 Codex：

> 请为本项目维护一份精简、可接续的 project-memory/current.md。基于已授权的任务记录、提交和明确来源，写清当前事实、有效决定、暂停节点与下一步；旧决定只保留必要沿革，不把没有变化的任务列成新增积压。先检查现有文件及暂存区，只交付这次真实变化。不要导出私人聊天、凭据或整个 .taskcarry。按本地 TaskCarry 流程提交接收；只有我已授权上传的资料才推送到指定私有远端。

### 4.4 生成有明确覆盖范围的恢复集

Core 可以从可信发行包重装；项目记忆不能靠重新下载恢复。治理先列清单，再调用 `recovery backup_plan` / `backup_execute`，保存数据库一致快照及引用对象，并选择实际需要的工作区与材料。源文件改变时保留具体差异，不能把跨时点的内容说成同一快照。

| 覆盖对象 | 应记录和验证的内容 |
|---|---|
| 项目状态 | `.taskcarry` 数据库的一致快照、实际引用对象、项目 source 身份和副本身份。读取副本不得被当作另一位活跃治理写入者。 |
| Git 工作区 | 选定 refs 和可达提交历史、当前 HEAD、index、工作区修改及显式选择的未跟踪文件。只推送 commit 不会保存这些全部层次。 |
| 普通文件与大材料 | 精确路径、内容哈希、大小和恢复目标；未纳入的材料或无法取得的来源必须列为排除/缺口。 |
| 能力层 | 正在使用的规则、四 Skills 的精确版本及自定义内容、兼容 Core 版本与包哈希、宿主能力清单。安装目录不是用户记忆本身。 |
| 本机接入材料 | 保留可重建的绑定说明；恢复后重新生成解释器路径、MCP 与工作台入口。凭证、登录和信任另行处理。 |

治理应主动选择可版本化的项目记忆和必要能力材料作为 payload；工具不会把整个电脑、聊天平台或所有忽略文件自动打包。保存编辑器缓冲后再纳入文件。恢复集含私有项目数据，不能提交公共仓库。

本地 `verify` 核对清单和实际对象。需要网盘或私有存储时，上传封存的静态恢复集，下载到独立位置再核对同一清单哈希。写入本地同步目录、看到文件名或收到上传指令成功，都不是下载与恢复证明。不要同步写入活跃 SQLite 或共享 `.git`；加密密钥与加密备份分开保管。

可以直接向治理说：

> 请为当前项目准备明确恢复计划。包含必要治理状态与对象、选定 Git refs/历史/index/WIP、项目记忆、规则与 Skills 版本及必要材料，列明排除项。核对范围后生成本地恢复集并验证，在独立目录做恢复演练，保留原目录和原任务。副本保持 standby。若我已启用异地存储，再分别提供上传、重新下载哈希和恢复证据；未授权的传输不要执行。

### 4.5 独立恢复，验证后再移交唯一写入权

`recovery restore_plan` / `restore_execute` 在空的独立目标恢复所选真实 Git 历史及分层工作、状态和材料。副本保留逻辑项目身份，获得明确副本身份，并默认处于 **standby**。路径映射与旧操作作为接续证据处理，不能在新位置重放旧接收/采用计划。

1. 核对恢复集来源、清单哈希、精确覆盖和兼容版本；保留原备份不变。
2. 在独立目录恢复并核对任务、对象、选定 Git refs/HEAD/index/WIP 和材料。缺失内容写入报告，不能称整台电脑已恢复。
3. 根据新机器实际目录与解释器重新生成连接，保留专业配置。治理和工作窗口分别原生调用 doctor/status；核对项目/副本身份、任务与 checkpoint。本机文件恢复不证明宿主已连接。
4. 需要接管时明确停止并隔离旧写入者。准备 `activation_plan`，核对原副本、新副本、交接授权和新宿主证据，再执行 `activate`。旧主机未确认停写时，副本继续 standby。
5. 新写入点启用后再检查原生调度与送达；旧主机回来时作为协作端处理其独立成果，不自行恢复旧治理写入或旧调度。

工具核对明确交接声明及原生证据引用，不能远程证明旧机器已经停机，也不提供跨主机分布式锁。需要的账号权限、主线保护和实际停写由环境执行。若仅需找回一个检查点的选定文件，旧 `restore` 仍可使用；它的合成还原基线不同于 `recovery` 保存的原 Git 历史，二者不可冒充。

<a id="multi-computer"></a>

## 5. 多电脑按任务分支协作

### 5.1 推荐拓扑与责任

[本步骤可直接复制的 Windows 示例](manual-setup.md)

```text
电脑 B：独立 clone → 任务分支 → 稳定提交 + 交付 manifest
                         │ push 任务分支
                         ▼
                    私有 Git 远端
                         │ fetch 精确源提交
                         ▼
电脑 A：稳定命名的本地 intake 仓/工作区
        → A 的 TaskCarry submit → 接收计划 → 唯一接收基线
        → 授权 push main → B fetch 后接续下一任务节点
```

TaskCarry 的一个治理目录由**一台电脑上的本地 SQLite**管理。电脑 B 可以有独立的本地 TaskCarry 做检查点，但其数据库不会自动合并到 A。不要把 `.taskcarry`、`.git` 或活动 worktree 放进双向同步目录共用。

同一业务主题可拆成任务支线；要明确成果、允许修改的路径、基线和接口依赖。只有任务名不同而实际修改同一文件，仍可能冲突。每个并行写入者使用自己的文件工作区和分支；同一 worktree 的文件不会因为开了两个对话窗而隔离。[Codex worktree 说明](https://learn.chatgpt.com/docs/environments/git-worktrees)

不同电脑可分别使用各自有权使用的 Codex 账户和 Git 凭据。**账户登录不构成任务锁，也不会自动登出另一电脑。** 不共享会话文件、登录令牌或密码；Git 权限与主线写入限制单独配置。初始方案不需要自己搭登录服务器，也不承诺网络分区期间的自动主机切换。

### 5.2 电脑 B：从已公布基线开始一个任务

[本步骤可直接复制的 Windows 示例](manual-setup.md)

确认 A 已推送允许 B 使用的基线，并约定任务 `form-export` 仅修改 `forms/export.py` 与 `docs/export.md`。以下目录、任务名和文件都是示例，应换成实际约定。

```text
git clone "<PRIVATE_REPOSITORY_URL>" "<B_REPOSITORY>"
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" switch -c codex/form-export origin/main
git -C "<B_REPOSITORY>" rev-parse HEAD
```

把最后输出记为 `<SOURCE_BASE>`，在工作开始前保存。若已经有合适克隆或工作区，复用它，不重复克隆、切换有 WIP 的工作区或占用已有分支。

> 在本电脑的 [任务工作区] 推进任务 form-export，起点是 [SOURCE_BASE]。只修改约定的 forms/export.py 和 docs/export.md；业务判断不明确时提出具体问题。保存有意义的检查点和下一步，达到稳定节点再精确提交。不要改 main、别人的工作区或治理数据库，也不要把仍未完成的任务声明为验收完成。交付时给出原 base、源 commit、精确变更路径、已做检查、剩余工作和材料位置。

完成稳定节点后：

```text
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" add -- forms/export.py docs/export.md
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Add task form-export stage one"
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" diff --no-renames --name-only "<SOURCE_BASE>" HEAD
```

仍须在提交前确认暂存区只有本次路径。把产物提交记为 `<SOURCE_COMMIT>`；最后一条结果必须与交付清单完整相符。删除和重命名涉及的路径也需按实际 diff 核对。

### 5.3 电脑 B：另存交付说明并推送任务分支

[本步骤可直接复制的 Windows 示例](manual-setup.md)

在产物提交**之后**创建 `handoffs/form-export-v1.json`，避免“文件里写它自身提交哈希”的循环：

```json
{
  "task_id": "form-export",
  "stage_label": "form-export-v1",
  "source_branch": "codex/form-export",
  "source_base": "<SOURCE_BASE>",
  "source_commit": "<SOURCE_COMMIT>",
  "paths": ["forms/export.py", "docs/export.md"],
  "checks": ["<actual checks and outcomes>"],
  "task_state": "paused",
  "next_step": "<remaining work or the next decision>",
  "artifacts": [],
  "relation_note": "<independent change, or evidence about earlier stages>"
}
```

这是**人和治理 Agent 阅读的交接说明，不是 TaskCarry import API**；不要直接把它传给 `submit`。

```text
git -C "<B_REPOSITORY>" add -- handoffs/form-export-v1.json
git -C "<B_REPOSITORY>" diff --cached --name-only
git -C "<B_REPOSITORY>" commit -m "Record form-export stage one handoff"
git -C "<B_REPOSITORY>" push -u origin HEAD:refs/heads/codex/form-export
git -C "<B_REPOSITORY>" rev-parse HEAD
git -C "<B_REPOSITORY>" ls-remote origin refs/heads/codex/form-export
```

检查暂存内容与远端哈希。远端分支 HEAD 现在包含交接说明，其哈希通常**不同于**被交付的 `<SOURCE_COMMIT>`，两者都应保留，不能混用。B 的 checkpoint 对象和未提交文件没有随此推送上传。

### 5.4 电脑 A：复核原始证据，再用本地接口接收

[本步骤可直接复制的 Windows 示例](manual-setup.md)

为这个任务建立名称稳定的 intake 克隆/工作区（例如本地登记名 `intake-form-export`），从远端取得原提交。已有对应 intake 时先查其绑定和未完状态，不重复创建或改写其历史。

首次建立示例：

```text
git clone --branch codex/form-export "<PRIVATE_REPOSITORY_URL>" "<A_INTAKE>"
git -C "<A_INTAKE>" show HEAD:handoffs/form-export-v1.json
git -C "<A_INTAKE>" cat-file -e "<SOURCE_BASE>^{commit}"
git -C "<A_INTAKE>" cat-file -e "<SOURCE_COMMIT>^{commit}"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" merge-base --is-ancestor "<SOURCE_COMMIT>" HEAD
git -C "<A_INTAKE>" diff --no-renames --name-status "<SOURCE_BASE>" "<SOURCE_COMMIT>"
git -C "<A_INTAKE>" diff "<SOURCE_BASE>" "<SOURCE_COMMIT>" -- forms/export.py docs/export.md
git -C "<A_INTAKE>" switch -c codex/intake-form-export "<SOURCE_COMMIT>"
```

祖先检查以退出码 0 表示成立；文件内容、清单、授权范围或检查结果不符时，先查清具体差异，不继续安装。不要先 cherry-pick、rebase 或重造提交，再把新哈希称为原阶段。之后登记本机工作区、任务和阶段，分别保存以下三个文件：

`intake-workspace.json`：

```json
{"name":"intake-form-export","path":"<A_INTAKE_ABSOLUTE_PATH>"}
```

`intake-task.json`：

```json
{"task_id":"form-export","title":"Form export","workstream":"forms"}
```

`intake-submit.json`：

```json
{"task_id":"form-export","workspace":"intake-form-export","stage_id":"form-export-v1","base":"<SOURCE_BASE>","commit":"<SOURCE_COMMIT>","paths":["forms/export.py","docs/export.md"],"relation":"independent"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" workspace --input intake-workspace.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" task --input intake-task.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" submit --input intake-submit.json
```

已有同名任务时先核对实际身份，不用说明文件覆盖另一任务。上面 `independent` 仅适用于这个示例的新阶段；若要累计取代旧阶段，必须满足**同一任务、同一登记工作区、原提交祖先关系及路径覆盖**，并明确给出 `supersedes`。跨电脑同名阶段不会自动产生关联。历史不满足条件时保留原证据，请治理判断关系，不能伪造覆盖。

创建 `receive-plan.json`：

```json
{"baseline":"baseline"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-plan.json
```

核对返回计划的全部 `stage_ids`、基线 HEAD、未完操作和冲突。接收计划可能包含其他已有排队阶段，并不自动只选这个任务；全部都在本次授权内才执行。将返回的 `plan_id` 原样填入 `receive-execute.json`：

```json
{"baseline":"baseline","execute":true,"plan_id":"<RETURNED_PLAN_ID>"}
```

```text
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" reconcile --input receive-execute.json
python -I -X utf8 -m taskcarry --project "<A_CONTROL>" status
```

检查阶段实际为 `COMMITTED`、相关操作完成及当前基线内容；整体调用成功不代表所有排队项都已完成。具体冲突只处理相关任务，不覆盖其他人的 WIP。需要更新 A 的某工作区时按主手册先 `adopt` 计划再执行。授权上传的基线按 4.2 精确 push 到 `main`；接收形成的新集成提交和原 B 源提交都要能追溯。

> 接收电脑 B 的 form-export-v1。先读取远端交接说明与原提交，核对原 base/commit、精确路径、已做检查、当前基线及任务关系。使用本机稳定登记的 intake 工作区，通过 TaskCarry submit 与先计划后执行的 reconcile 接收，不冒充跨机数据库导入，不重写来源哈希，不重复执行已完成效果。检查计划中的其他阶段是否也在授权范围。保留 B 的未完任务说明，业务验收单独判断；仅按已有授权推送主线。

### 5.5 B 接续、主机换手和已知边界

[本步骤可直接复制的 Windows 示例](manual-setup.md)

B 确认 A 接收并推送后，读取最新接续说明。若旧任务工作区仍有 WIP，先保留，不直接把它重置到 `main`。可从已公布主线建立下一条干净任务支线：

```text
git -C "<B_REPOSITORY>" fetch origin
git -C "<B_REPOSITORY>" worktree add -b codex/form-export-next "<B_NEXT_WORKSPACE>" origin/main
```

根据任务关系接续，记录新 base；不用重做已完成阶段。其他机器上的 TaskCarry `adopt` 不会通过网络被 A 自动调用。

| 情况 | 应采取的动作 |
|---|---|
| 两台电脑推进互不重叠的任务 | 各自分支和工作区，A 串行核对并推进接收基线 |
| 同一任务拆成两个支线 | 明确接口、路径和集成顺序；同名任务并不能消除内容冲突 |
| A 暂时离线，B 想继续工作 | B 可继续授权的任务分支，保留检查点；主线接收等待 A 或明确换手 |
| A 无法恢复，需要 B 接管主线 | 明确停止/隔离旧主线写入权，按 4.5 独立恢复 standby 副本并完成明确移交；对账后让 B 成为唯一集成主机 |
| A 恢复上线 | 先作为普通协作主机读取当前远端和接管记录，不恢复旧定时写入；核对其未推送成果后按任务分支交接 |
| 推送被拒、源提交缺失、清单不符或内容冲突 | 保留成果与原始证据，解决具体差异；不强推、不改 hash 造成功、不把旧操作盲目重放 |

无法确认旧主机停止时，不能声称已解决“双主写入”；需要在实际 Git 权限/主线保护或明确断开旧写入者层面落实。RC 不提供分布式租约、自动选主、跨机事务迁移、远端副作用恢复、操作系统修复或 Codex 账户迁移。上述流程让任务资料可交接，但不承诺完整聊天、未保存内容或全部原生环境自动恢复。
