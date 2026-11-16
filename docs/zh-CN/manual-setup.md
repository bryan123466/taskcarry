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

先检查已有安装与 control，有效时直接复用。确实首次安装工具时，创建 `C:/TaskCarry`，将选定产品 ZIP 解压到 `C:/TaskCarry/toolkit`。产品 ZIP 自带顶层目录 `taskcarry-0.2.0rc8/`，因此实际产品根是 `C:/TaskCarry/toolkit/taskcarry-0.2.0rc8`，其中包含 `START_HERE.md`、`packages/`、`docs/` 和 `skills/`。选用其他版本时按实际解压出的版本目录调整。原业务项目保留在原位置。需要 Python 3.11+；本地 Git 是标准接入项；普通文件 API 仍保留无 Git 兼容。

以下命令在 PowerShell 执行，**仅用于专用 runtime 尚不存在的情况**。安装工具不创建新的业务项目，也不意味着获准升级已有运行时。

命令块先将内置 wheel 与 `RELEASE_MANIFEST.json` 中的精确记录核对；记录缺失或不唯一、大小不符或 SHA-256 不符时，在创建 runtime 和安装之前立即停止。这只证明包内一致性。请另从所选官方 Release 单独取得 `SHA256SUMS.txt`，在解压前核对下载产品 ZIP 的 SHA-256。该外部校验文件提供 ZIP 之外的比对来源；两种校验值都不是数字签名，单凭它们不能证明发行者身份。

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $taskcarryProductRoot = 'C:/TaskCarry/toolkit/taskcarry-0.2.0rc8'
    $taskcarryManifest = Get-Content -LiteralPath (Join-Path $taskcarryProductRoot 'RELEASE_MANIFEST.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskcarryWheels = @(Get-ChildItem -LiteralPath (Join-Path $taskcarryProductRoot 'packages') -Filter '*.whl' -File)
    if ($taskcarryWheels.Count -ne 1) { throw 'Expected exactly one wheel in the selected product package.' }
    $taskcarryWheel = $taskcarryWheels[0]
    $taskcarryExpected = @($taskcarryManifest.files | Where-Object { $_.path -ceq ('packages/' + $taskcarryWheel.Name) })
    if ($taskcarryExpected.Count -ne 1 -or $taskcarryExpected[0].sha256 -notmatch '\A[0-9a-fA-F]{64}\z') { throw 'Missing or invalid wheel checksum in RELEASE_MANIFEST.json.' }
    $taskcarryActual = (Get-FileHash -LiteralPath $taskcarryWheel.FullName -Algorithm SHA256).Hash
    if ($taskcarryExpected[0].bytes -ne $taskcarryWheel.Length -or $taskcarryActual -ne $taskcarryExpected[0].sha256) { throw 'Wheel verification failed. Stop and obtain the correct product package.' }
    if (Test-Path -LiteralPath 'C:/TaskCarry/runtime') { throw 'Runtime already exists. Return to governance for inspection; do not reinstall.' }
    py -3 -m venv 'C:/TaskCarry/runtime'
    if ($LASTEXITCODE -ne 0) { throw 'Runtime creation failed. Inspect its actual state before continuing.' }
    & 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m pip install --no-index --no-deps $taskcarryWheel.FullName
    if ($LASTEXITCODE -ne 0) { throw 'Package installation failed. Inspect its actual state before continuing.' }
    & 'C:/TaskCarry/runtime/Scripts/python.exe' -I -X utf8 -m taskcarry --project 'C:/TaskCarry' doctor
}
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

先核对原聊天的实际工作目录与配置所在目录一致，并由治理给出该目录的完整路径。已在正确目录的原聊天直接沿用，保留历史和原任务身份。若宿主尚未打开并信任该目录，按以下步骤补齐：

1. 在当前 Windows Codex 按 **Ctrl+O**；其他界面选择“打开／添加项目文件夹”。
2. 选择治理给出的完整**原目录**，不创建替代目录，不复制文件，**不新建聊天**。
3. 出现信任提示时核对目录后确认；没有出现提示则记录这一情况。
4. 回到治理对话，回复“已打开指定目录”，并说明信任提示是否出现、是否已确认。治理按宿主支持的方式将原聊天关联到该项目，核对原聊天身份、实际 cwd 和配置。
5. 治理确认本次所有目标目录的配置与关联已准备好后，先保存正在进行的工作，**退出并重新打开 Codex 一次**，让尚未加载的新连接生效。不必每个目录重启一次；已经原生验收通过的连接跳过此步。
6. 回到原治理聊天回复“已重启”，再回到各个原工作聊天，按下节分别调用原生 `taskcarry_doctor`、`taskcarry_status`。不要新建替代聊天或重新安装。

这让宿主登记并信任配置所在的原项目目录，保留原对话与同一 control。本次 Windows Codex 验证中，信任及关联完成后仍返回工具未加载，重启后原生调用成功，所以此路线把重启列为明确步骤。其他宿主按其支持的方式加载；已经成功的连接无需重复处理。随后按[原生验收](#verify)核对实际版本、解释器、模块、control、原任务和最新检查点。侧栏关联或重启完成不能代替这些回执；仍失败时保留原始错误，由治理只排查当前缺口。

未挂在项目下的原对话，先核对实际 cwd，优先按宿主能力关联同一目录并保留原历史。这个标签不表示一定没有 MCP；用户级或项目级配置、插件都可能提供连接，应查看实际工具，不自动改写用户级配置。目录不匹配时，先由治理核对宿主支持的关联或保留历史的接续方式，仍使用同一 control。把配置写在另一目录不会让当前聊天自动连接。setup 不选择宿主目录、不授予信任，也不重载宿主。操作入口以当前宿主为准，参考官方 [MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=app)和[配置层级](https://learn.chatgpt.com/docs/config-file/config-basic)。

Skills 位于 `.agents/skills/`，包括引用的方法文件；未被自动发现时，明确读取该目录下需要的 `SKILL.md` 及引用。新 worktree 不会自动继承另一目录的配置。每个目标窗口按下节单独验收，配置文件或独立 stdio 进程成功均不证明原生宿主已经加载。

<a id="workbench"></a>

### 接入已登记工作台

先按真实目录分组，复用原 control 中的工作区登记。多个活跃对话共用一个业务目录时，目录共享连接与 Skills，各对话仍使用自己的原任务。以下是**合成请求示例**，不是要求建立样例目录或任务：

```json
{"mode":"preview","binding_mode":"directory","target":"<existing-project-directory>","workspace":"drone"}
```

`directory` 模式提供 `target`、`workspace` 并省略 `task_id`，避免把目录里的所有对话固定到一个任务。target 须匹配登记工作区及其当前 Git 身份。保存核对过的请求后执行上面的预览命令；审阅后将同一请求的 `mode` 改为 `install`。`connect` 计划沿用 `binding_mode: "directory"` 和同一目标，`--project` 始终指向原 control。

已有单任务绑定仍可使用默认 `task` 模式，同时提供 `target`、`workspace`、`task_id`；任务须存在于同一 control。例如：

```json
{"mode":"preview","target":"<existing-project-directory>","workspace":"drone","task_id":"drone-software"}
```

setup 写入目录的四项 Skills 及引用、MCP 片段和工作台材料，不创建聊天、任务或另一数据库。共享目录的工作台计划使用 `routing: "shared"`，每个目标保留真实 `thread_id` 与原 `task_id`。当前窗口按自己的真实聊天身份读取入口，不能使用目录中的第一个任务代替；每个原对话分别验收与记录实际读取。只有并行写入确实存在冲突时，才考虑独立 Git 工作树。

仅作历史来源的对话不需要原窗口的 MCP 或 Git 配置。普通文档目录也可用绑定 control 的 CLI 保存 checkpoint，不为保存文档伪造 Git 登记。

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

## 手动一步之后，回到完整建制清单

每次后备操作后都回原治理窗口、沿同一接入身份继续。`init` 前先 `identify`，未知或不支持的状态保留。旧本地路径身份先显示明确 `identity` 计划再采用持久身份；只读状态不会代做。

完成登记工作台 `setup` 后，用审阅过的 `connect` 计划合并项目 MCP 设置，再用 `workbench` 冻结和发布选定治理 view。目标应是被 Git 忽略的私有入口，保留定制指令及其他服务。由实际工作窗口读取 current/view、原任务和 checkpoint，原生调用 doctor/status 并给出相符证据；写了配置不等于信任/重载已完成。精确合同见[治理 API](../GOVERNANCE_API.md)，不要临时改数据库。

补齐本地 Git 与核实作者配置、精确 `preserve` 保存、官方来源登记/检查/评估、首次有界整轮和独立恢复演练。通过宿主配置一个早晨报告加一到两个吸收时段，并准确回读，用 `complete_v1` 明确剩余标准项。配置、自然触发、AI 执行和报告送达分别说明；私有远端/网盘可选。[反馈示例](user-feedback-examples.md)展示完成报告。

独立恢复副本默认 standby。恢复回执中的 `disabled_host_files` 指明被隔离的旧机器连接配置：内容作为证据保留，不直接激活；按目标路径重新生成后核验原生绑定，明确旧写入者停写后才移交。选定检查点文件恢复小于完整所选恢复集，详见[恢复参考](remote-and-multicomputer.md)。
