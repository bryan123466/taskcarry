# 手动安装与转交后备步骤

[返回对话式接入](windows-example.md) · [English](../en/manual-setup.md) · [繁體中文](../zh-TW/manual-setup.md) · [命令参考](../COMMANDS.md)

仅在治理助手无法代办某一步时使用本页。首次安装从[主手册](windows-example.md)开始；已有安装使用[更新提示词](updating.md)。下列路径为合成示例，按实际位置统一调整。

- [安装或核对固定运行时](#install)
  - [只初始化缺失的治理状态](#governance)
- [生成并加载接入材料](#mcp)
  - [接入已登记工作台](#workbench)
  - [验收实际窗口](#verify)
- [只转交缺失的旧窗口上下文](#existing)
  - [确有需要时新建工作窗口](#agents)
- [中断后继续](#recovery)

<a id="install"></a>

## 安装或核对固定运行时

先检查已有安装与 control，有效时直接复用。确实首次安装工具时，创建 `C:/TaskCarry`，将选定产品 ZIP 解压到 `C:/TaskCarry/toolkit`。产品 ZIP 自带顶层目录 `taskcarry-0.2.0rc7/`，因此实际产品根是 `C:/TaskCarry/toolkit/taskcarry-0.2.0rc7`，其中包含 `START_HERE.md`、`packages/`、`docs/` 和 `skills/`。选用其他版本时按实际解压出的版本目录调整。原业务项目保留在原位置。需要 Python 3.11+；本地 Git 是标准接入项；普通文件 API 仍保留无 Git 兼容。

以下命令在 PowerShell 执行，**仅用于专用 runtime 尚不存在的情况**。安装工具不创建新的业务项目，也不意味着获准升级已有运行时。

```powershell
py -3 -m venv 'C:/TaskCarry/runtime'
$taskcarryWheel = Get-ChildItem -LiteralPath 'C:/TaskCarry/toolkit/taskcarry-0.2.0rc7/packages' -Filter '*.whl' -File
if (@($taskcarryWheel).Count -ne 1) { throw 'Expected exactly one wheel in the selected product package.' }
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m pip install --no-index --no-deps $taskcarryWheel.FullName
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' doctor
```

control 尚未初始化时，doctor 返回 `NOT_INITIALIZED`，不含运行时细节；仅此结果不表示安装失败。治理按下节核实这个 control 确实没有状态并初始化后，再运行同一条 doctor 命令查看实际运行时与前提条件。Git 能力不可用时结合当前操作判断；不要为了清除提示重建已有状态。将输出交回治理窗口，继续同一次接入。

<a id="governance"></a>

### 只初始化缺失的治理状态

治理先检查已有任务、目录与历史成果。这个 control 确实没有状态时，`init` 才为它建立治理状态；这不会建立接收基线，也不证明业务项目是新的。让治理按[命令参考](../COMMANDS.md)的实际 `init`、`workspace`、`task` 合同操作，保留既有身份。

可选的[新项目脚手架](../../examples/windows_quickstart)只用于已确认的新项目，默认专业工作区数量为零。它拒绝已有目标；中断后核对实际效果，不删除目录重跑。已有项目采用真实历史与基线。

<a id="mcp"></a>

## 生成并加载接入材料

将审阅后的 JSON 请求保存为 UTF-8 文件 `C:/TaskCarry/setup-request.json`，这是示例输入文件，不是数据库。治理目录的初始内容为 `{"mode":"preview"}`。执行：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' setup --input 'C:/TaskCarry/setup-request.json'
```

检查拟变更文件和冲突。在已授权接入范围内，只将 `mode` 改为 `install`，再执行相同命令。中断续办保持原候选与参数；setup 保全用户改过的文件并报告冲突。

生成的 `.taskcarry/codex.mcp.toml` 是**片段**。在 Codex 中，将选定的 `[mcp_servers.<name>]` 表合并到目标聊天的项目级 `.codex/config.toml`：治理目录为 `C:/TaskCarry/.codex/config.toml`，专业工作台为 `<已登记工作台>/.codex/config.toml`。保留其他设置与服务，不覆盖整份文件或修改全局配置。保留生成的 command/args：它们绑定固定解释器，使用隔离 UTF-8 启动并指定包来源。

让目标聊天打开或选用同一目录作为项目和工作目录，并在适当时完成该项目的信任提示；Codex 只加载受信任项目的配置。随后使用宿主支持的 MCP 重启/重载操作；官方桌面说明使用 **Settings → MCP servers → Restart**。当前聊天不能更换目录时，在配置所在目录打开的聊天中按保存清单接续，仍复用同一 control。把配置写在另一目录不会让当前聊天自动连接。setup 不选择宿主目录、不授予信任，也不重载宿主。依据见官方 [MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=app)和[配置层级](https://learn.chatgpt.com/docs/config-file/config-basic)。

Skills 位于 `.agents/skills/`，包括引用的方法文件；未被自动发现时，明确读取该目录下需要的 `SKILL.md` 及引用。新 worktree 不会自动继承另一目录的配置。每个目标窗口按下节单独验收，配置文件或独立 stdio 进程成功均不证明原生宿主已经加载。

<a id="workbench"></a>

### 接入已登记工作台

治理应已在原 control 登记该 Git 工作区及其任务。下列是**合成请求示例**，不是要求建立样例任务：

```json
{"mode":"preview","target":"C:/TaskCarry/workspaces/agent-1","workspace":"agent-1","task_id":"example-writing"}
```

用核对过的登记值替换三项，保存请求后执行相同的预览命令。`target`、`workspace`、`task_id` 必须一起提供；target 须匹配登记工作区及其当前 Git 身份，任务须存在于同一个 control。具体任务与工作台关系由治理核对，setup 不强制一对一归属。`--project` 始终指向原 control。审阅后把相同请求的 `mode` 改为 `install`。

它写入工作台的四项 Skills 及引用、MCP 片段、`.taskcarry/workbench.json` 和 `workbench.md`，不创建聊天、不登记任务、不初始化另一数据库，也不激活宿主配置。普通文档目录可以通过绑定 control 的 CLI 保存 checkpoint，不为保存文档伪造 Git 登记。

<a id="verify"></a>

### 验收实际窗口

宿主加载后，在该窗口调用原生 `taskcarry_doctor` 与 `taskcarry_status`，将实际版本、解释器、模块、control 及相关任务/工作区/检查点与绑定材料核对。存在多个服务时选对服务。命令行成功不能证明原生工具已经暴露。

MCP 不可用时保留原始错误或工具缺失事实，可用固定隔离 CLI 继续已授权工作：

```powershell
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' doctor
& 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' status
```

这项证据标为 CLI，原生连接继续保留为待验收。更新工具时先预览并安装受管理文件，再检查实际宿主配置和重载；安装版本变化不代表运行中的服务已变化。卸载只移除未被用户改动的受管理文件，保留已修改文件、治理数据和手工合并的生效配置。

<a id="existing"></a>

## 只转交缺失的旧窗口上下文

仅在治理无法直接读取获准的相关历史时使用，不重新开始原任务。向**原工作窗口**发送：

```text
请为当前工作接入 TaskCarry 准备最小交接。读取现行指令与实际文件，说明项目/任务及已知稳定身份、真实工作目录、适用时的 Git 根/分支/HEAD/WIP、有来源的有效决定、已完成成果及已知接收情况、准确未完成位置与下一步。区分事实、最后已知信息、建议和缺口。保留原工作与历史；本次摘要不要修改文件、登记任务或制造交付。
```

把回复交给**治理窗口**，同时发送：

```text
请将这份交接接入现有项目，核对引用来源与真实归属，复用已知任务/control 身份并保全 WIP。已纳入基线的成果不重复排队。按接入授权补齐缺失登记与连接步骤，给我一份可直接贴回原窗口的接续内容，填好核实过的 control、运行时、任务/工作区、Skill 位置和下一步，说明尚未验收的部分。
```

将治理填好的内容贴回原窗口。连接检查应读取相关 Skills、任务与有效决定，然后从原下一步继续。人工转交是后备，不是每次工作的必经步骤。

<a id="agents"></a>

### 确有需要时新建工作窗口

确认有价值的分工后，治理给出准确目录、职责、任务身份和接续内容。无法原生创建聊天时，由你在该目录打开窗口并粘贴已填内容。新增专业窗口可以为零。每个任务和写入范围保留一个主要写入者，移动工作前先核对共目录冲突。

<a id="recovery"></a>

## 中断后继续

可以说“请从接入清单继续，先核对实际已经发生的结果”。保留原 setup 候选与操作身份。文件生成、CLI 检查成功或保存调度提示词只证明各自步骤；用户改过的文件和恢复目标要保全，不覆盖现场换取顺利重试。

普通 checkpoint 首次恢复到独立空目录。若恢复已产生效果、最终回执失败，应由支持的恢复逻辑核验原效果并补缺失记录，不手动清空目标。具体以所安装版本的恢复 Skill 为准。

## 手动一步完成后，补齐标准接入

`init` 前先 `identify`，未知或不兼容状态保持原状。每完成一步都接续原 onboarding 清单；同一项目有多份状态来源时保持真实路由。

助手可用 `connect` 预览并执行项目级 MCP 配置合并，保留其他服务和用户修改；宿主信任、重载及各窗口原生验收另做。持续工作的原对话缺少合适目录时，准备真实 Git 工作位置或交接到正确目录的窗口；历史参考对话无需激活。

核对 Git 和真实作者配置，准备或复用本地治理仓库及专业工作仓库。用精确 `preserve` 计划保存选定文件，保全无关暂存和工作区。完成官方来源登记/检查/评估及原治理窗口的原生调度创建/回读；具体参数见[调用合同](../COMMANDS.md)和已安装 Skills。这些属于标准配置，私有远端与网盘才是可选项；首次自然触发在实际发生后补回执。
