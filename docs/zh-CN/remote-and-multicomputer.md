# 第 4、5 章：私有 Git、备份恢复与多电脑协作

Windows 用户可以直接跟随[固定目录完整示例](windows-example.md)，复制配套命令与提示词；以下通用说明仍适用于自定义目录。

[返回操作手册](operation-manual.md) · [English](../en/remote-and-multicomputer.md) · [繁體中文](../zh-TW/remote-and-multicomputer.md) · [命令参考](../COMMANDS.md)

适用版本：0.2.0rc5。这两章是按需要启用的参考流程，不是安装后每天必须执行的任务。下述跨电脑流程尚未经过两台实体电脑的端到端验证；它组合了 Git 操作与现有本地 TaskCarry 接口，没有新增跨机同步或自动恢复能力。

所有 `<...>` 都是需要替换的占位符。`python` 应指向已经安装 TaskCarry 的 Python 环境。JSON 文件保存为 UTF-8；不要把示例中的占位符直接执行。Git 推送会向所选远端传送资料，应先确认仓库、访问者和本次授权范围。

<a id="private-git"></a>

## 4. 私有 Git 在线记录库与恢复备份

### 4.1 先分清哪些内容保存在哪里

[本步骤可直接复制的 Windows 示例](windows-example.md#private-git)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#private-git)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#private-git)

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

### 4.4 做一份可核对的一致备份

[本步骤可直接复制的 Windows 示例](windows-example.md#private-git)

**先停止这一个项目的写入，再备份同一时点。** 当前 TaskCarry 没有跨仓库、SQLite 与文件对象的一键一致备份命令。操作顺序：

1. 让相关任务保存文件。对有意义的未完成内容创建精确检查点，记录 `next_step`；检查点不是交付，也不要求把未完成工作提交为成果。当前检查点最多选择 500 个路径，单个文件对象上限 32 MiB、各层合计上限 128 MiB；超出或未选中的资料另行备份。
2. 等当前 TaskCarry 操作结束，暂停此项目的定时写入与治理调用，保证备份期间没有 CLI/MCP/其他程序改动其 `.taskcarry`。需要捕获的 Git 工作区也暂停修改。保留未完成操作的真实状态，不为备份伪造终态或删除锁文件。
3. 新建一个**不在源仓库、工作区或治理目录内部**的备份目录。保存工具版本、各工作区路径/分支/HEAD、检查点 ID、`status`、备份时间和暂停范围。
4. 用 Git bundle 保存每个独立 Git 仓库的可达提交与引用；共享同一 Git 公共目录的 worktree 可由同一 bundle 覆盖相应引用。

```text
git -C "<REPOSITORY>" bundle create "<SNAPSHOT>/project.bundle" --all
git -C "<REPOSITORY>" bundle verify "<SNAPSHOT>/project.bundle"
git -C "<REPOSITORY>" bundle list-heads "<SNAPSHOT>/project.bundle"
```

Bundle 可用于离线传递提交。它不是工作目录、暂存区、未跟踪文件、配置和所有本地恢复信息的完整备份；这些需要检查点或另外保存。[Git bundle 官方说明](https://git-scm.com/docs/git-bundle)

5. 在所有相关写入仍停止时，完整复制治理目录中的 `.taskcarry`，包括 `state.sqlite3`、存在的 WAL/SHM 配套文件、`objects` 和其他状态文件。不要只挑数据库主文件，不要移动原件。另存尚未被检查点覆盖、确实需要保留的文件，以及经检查的项目配置；不包含登录令牌。

PowerShell 7 的冷备份示例（`<SNAPSHOT>` 是已经新建的空目录）：

```powershell
Copy-Item -LiteralPath "<A_CONTROL>/.taskcarry" -Destination "<SNAPSHOT>/.taskcarry" -Recurse -ErrorAction Stop
Get-ChildItem -LiteralPath "<SNAPSHOT>/.taskcarry" -Force
```

其他系统可在同样停写条件下用本地文件复制工具，保留隐藏文件和完整目录结构。不要让同步盘在后台复制**运行中的** `.taskcarry` 或 `.git`。SQLite 在线备份 API 能处理数据库快照，但单独快照数据库仍不等于同时一致地保存 TaskCarry 的文件对象和 Git 状态。[SQLite 备份说明](https://www.sqlite.org/backup.html)

6. 核对文件清单、大小与 SHA-256；检查数据库副本及代表性检查点能否读取。至少确认 bundle 校验通过、对象目录已保存、没有复制错误，再恢复原项目正常运行。把完成的备份归档上传到所选存储，并在另一份下载副本上核对哈希，才称“异地备份已验证”。目录名或同步图标不构成这项证据。

> 请给本项目做一次停写期间的一致备份到 [新备份目录]。先保存选定 WIP 检查点，等待当前治理动作结束，再协调暂停相关写入。保存每个独立仓库的 Git bundle、完整 .taskcarry、未被检查点覆盖的具名必要文件、版本与路径清单。只对副本做验证，不删除原文件或恢复用 stash。记录哪些内容不在备份中。完成并核验后恢复刚才暂停的本项目运行设置，不改变其他项目。

### 4.5 恢复时分成“找回资料”与“重新启用治理”

[本步骤可直接复制的 Windows 示例](windows-example.md#private-git)

**不要把旧 `.taskcarry` 复制到新电脑后直接执行旧接收/采用计划。** 工作区身份包含绝对路径、Git 公共目录和分支；集成基线还绑定原身份。0.2.0rc5 没有完整的跨机状态迁移 API。相同目录名字不代表同一现场。

恢复步骤：

1. 保持备份原件不动，在新位置创建恢复工作副本。确认旧主机不会同时继续写主线；若无法确认，先只恢复资料和独立任务分支，不启用第二个主线写入者。
2. 从私有远端或 bundle 恢复到**不存在的新目录**：

```text
git clone "<PRIVATE_REPOSITORY_URL>" "<NEW_REPOSITORY>"
```

或离线恢复明确的分支：

```text
git clone --branch "<SAVED_BRANCH>" "<SNAPSHOT>/project.bundle" "<NEW_REPOSITORY>"
```

从 bundle 克隆时 `origin` 指向 bundle；之后若要上传，先明确配置正确私有远端，不能把它当成已连接在线仓库。

3. 需要找回检查点时，把备份 `.taskcarry` **复制**到独立的 `<RECOVERY_CONTROL>/.taskcarry`，只把它当恢复工具的工作副本。使用与备份兼容的 TaskCarry 版本读取 `status`，核对检查点。创建 `restore.json`：

```json
{"checkpoint_id":"<SAVED_CHECKPOINT_ID>","destination":"<NEW_INDEPENDENT_RESTORED_FILES_DIRECTORY>"}
```

```text
python -I -X utf8 -m taskcarry --project "<RECOVERY_CONTROL>" status
python -I -X utf8 -m taskcarry --project "<RECOVERY_CONTROL>" restore --input restore.json
```

目标必须为空或不存在，且独立于原工作区与恢复治理目录。`restore` 只恢复检查点选中的文件；Git 检查点会建立**合成恢复基线**以呈现原 HEAD/暂存/工作区层次，保留原 HEAD 的来源记录，但不是还原完整原仓库历史。它会在恢复工作副本登记恢复事件，不修改备份原件。先比对这些文件与克隆出的真实项目，再在具名任务分支中恢复工作，不能把合成提交冒充原始提交。

4. 为继续工作创建新的 `<NEW_CONTROL>`，重新初始化、登记新路径的接收基线和工作区。根据原 `status`、成果哈希、远端/本地提交证据重新确认任务当前节点。旧收据作为来源保留，旧未完成操作逐项对账；已经实际发生的效果不要再执行。
5. 重新生成本机 Skills/MCP 配置并做 `doctor`/`status` 检查。旧 MCP 片段含原 Python 和项目绝对路径，不直接复用。当前路径重绑定入口也不能绕过待处理阶段、未完操作或基线身份限制。

```text
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" init
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" workspace --input new-baseline.json
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" doctor
python -I -X utf8 -m taskcarry --project "<NEW_CONTROL>" status
```

`new-baseline.json` 示例：`{"name":"baseline","path":"<NEW_BASELINE_ABSOLUTE_PATH>"}`。其余登记与接入见[操作手册](operation-manual.md)。保留恢复记录里的旧 ID 与新登记 ID 的对应关系；这是一项明确的人工/Agent 辅助重建，不能称为自动延续了旧数据库的完整事务历史。

<a id="multi-computer"></a>

## 5. 多电脑按任务分支协作

### 5.1 推荐拓扑与责任

[本步骤可直接复制的 Windows 示例](windows-example.md#multi-computer)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#multi-computer)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#multi-computer)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#multi-computer)

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

[本步骤可直接复制的 Windows 示例](windows-example.md#multi-computer)

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
| A 无法恢复，需要 B 接管主线 | 明确停止/隔离旧主线写入权，按 4.5 恢复资料与新建治理；对账后让 B 成为唯一集成主机 |
| A 恢复上线 | 先作为普通协作主机读取当前远端和接管记录，不恢复旧定时写入；核对其未推送成果后按任务分支交接 |
| 推送被拒、源提交缺失、清单不符或内容冲突 | 保留成果与原始证据，解决具体差异；不强推、不改 hash 造成功、不把旧操作盲目重放 |

无法确认旧主机停止时，不能声称已解决“双主写入”；需要在实际 Git 权限/主线保护或明确断开旧写入者层面落实。RC 不提供分布式租约、自动选主、跨机事务迁移、远端副作用恢复、操作系统修复或 Codex 账户迁移。上述流程让任务资料可交接，但不承诺完整聊天、未保存内容或全部原生环境自动恢复。
