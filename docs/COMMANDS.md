# CLI and MCP contract / 命令与 MCP 合同

All ordinary actions route through one dispatch API. Use JSON files to avoid shell-dependent quoting. 所有普通动作调用同一个分发 API；使用 JSON 文件避免不同终端的引号差异。

```text
python -I -X utf8 -m taskcarry --project <control-directory> <action> --input <request.json>
```

`--input` and `--json` are mutually exclusive. Input files contain the **argument object only**, not an action wrapper. `status` and `doctor` need no input file. Replace angle-bracket placeholders; do not type them literally. 请求文件只包含参数对象，`status` 与 `doctor` 无需请求文件；尖括号是占位符。

Use the fixed installed interpreter for `python` above. Isolated startup excludes cwd and environment import overrides. Source development must explicitly select its checkout instead; it is not a governance installation. 上述 python 指固定安装解释器；源码开发需明确选定源码，不作为正式治理安装。

Success: `{"ok":true,"result":{...}}`. Failure: `{"ok":false,"error":{"code":"...","message":"...","details":{...}}}` and a nonzero exit status. A successful planning result is not proof that execution occurred. 计划成功不代表实际执行成功。

| Action / 动作 | Main fields / 主要字段 | Meaning / 含义 |
|---|---|---|
| `init` | `name` | Initialize the control directory / 初始化控制目录 |
| `task` | `task_id`, optional `title`, `workstream`, `state` | Record task; states active, paused, waiting, complete / 记录任务状态 |
| `workspace` | `name`, `path` | Register existing Git workspace / 登记已有 Git 工作区 |
| `checkpoint` | `task_id`, `workspace`, `paths`, `next_step`, optional `decision`, `paused` | Snapshot exact saved work / 保存精确检查点 |
| `restore` | `checkpoint_id`, `destination` | Restore to absent/empty independent destination / 恢复到不存在或空的独立目录 |
| `artifact` | `task_id`, `path`, optional `role`, `backup`, `decision` | Register content identity and available backup evidence / 记录材料身份及备份证据 |
| `submit` | `task_id`, `workspace`, `commit`, `base`, `paths`, optional `stage_id`, `relation`, `supersedes` | Freeze explicit stage; paths must equal commit diff / 冻结明确交付，路径与提交差异须一致 |
| `reconcile` | `baseline`, optional `execute`, `plan_id`, planning `limit` (1–100, default 20) | Plan a bounded receiving batch or execute its frozen scope / 计划有限接收批次或执行冻结范围 |
| `adopt` | `workspace`, `baseline`, optional `execute`, `plan_id` | Plan or execute workspace adoption / 计划或执行工作区采用 |
| `experience` | `rule_id`, `code`, `operation`, `action`, optional `task_id`, `version`, `enabled` | Store bounded experience / 保存有限经验 |
| `status` | none / 无 | Read current state / 读取当前状态 |
| `agenda` | optional `limit` (1–100), `previous_fingerprint`, `cursor` | Read a bounded, paginated selection; no execution / 读取有限分页议程，不执行操作 |
| `doctor` | none / 无 | Inspect prerequisites / 检查运行条件 |
| `upgrade` | none / 无 | Explicitly build/repair the derived current-work index; preserve records and events / 显式建立或修复当前事项派生索引，不升级软件包 |
| `observe` | `observation_id`, `workspace`, `task_id`, `source_ref`, `source_revision`, `summary`; optional `relations`, `expected_revision` | Persist host-reviewed references with revision checks / 持久保存宿主已复核依据与关联 |
| `run` | `run_id`; `mode` start/inspect/finish; optional `stage_ids`, `operation_ids`, `observation_ids`, `note` | Freeze and inspect a round's selected records / 固定并核对本轮选中记录 |
| `issue` | `issue_id`, `condition`, `summary`; optional `state` open/resolved, `resolution_ref`, `expected_revision` | Keep a concrete issue and reviewed resolution / 保存具体问题条件与解决依据 |
| `fix` | `fix_id`, `issue_id`, `version`, `evidence_refs`; optional `summary`, `expected_revision` | Link validation and fix version; inspect project setup evidence / 关联验证与修正版本，核对项目安装依据 |

Paths in a checkpoint or submission are workspace-relative exact files, not wildcard expressions. In a cumulative submission, `relation` is `cumulative` and `supersedes` lists the exact earlier stage identifiers. The default relation is `independent`. 检查点和交付的路径是工作区相对精确文件，不使用通配符；累计交付明确列出被替代阶段。

Plain-directory checkpoints and their restoration do not require Git. A workspace with Git metadata, or inside a repository, still requires working Git and the exact working-tree root; an unreadable or damaged repository is never silently saved as plain files. A repository appearing during a plain capture prevents checkpoint publication.

普通目录的检查点及恢复不要求安装 Git。工作区或父级存在 Git 元数据时，仍须使用可用的 Git 和准确的工作树根；不会把不可读取或损坏的仓库悄悄降为普通文件保存。普通目录在捕获期间变为仓库时，不发布该检查点。

一般目錄的檢查點及還原不要求安裝 Git。工作區或父層存在 Git 中繼資料時，仍須使用可用的 Git 與正確的工作樹根；不會將無法讀取或損壞的儲存庫悄悄降為一般檔案儲存。一般目錄在擷取期間變為儲存庫時，不發布該檢查點。

`reconcile` and `adopt` default to planning. To execute, copy the returned plan identifier into a request with `execute: true`. First reconcile recorded unfinished operations against their actual effects and resume the original operation when applicable. If external changes invalidate the relevant facts and there is no applicable operation to resume, inspect the error and generate a fresh plan. Do not edit the persisted plan. 接收和采用默认只计划；先核对未完操作的实际效果，适用时接续原操作。外部变化使前提失效且无适用原操作可续办时，再检查错误并重新计划，不直接修改保存的计划。

Installed MCP can start with `python -I -X utf8 -m taskcarry --project <control-directory> mcp`. The setup-generated fragment additionally pins its selected package path through an isolated launcher, supporting explicit source development and failing if that path is unavailable. Retain the generated arguments when activating it. Tools have `taskcarry_` prefixes and expose the corresponding ordinary actions, except project initialization and setup. The server is project-bound. CLI and MCP output formatting differ where required by their protocols, but both call the same action dispatcher.

Receiving plans include selected recovery operations in their identity. `scope: plan` and `plan_complete` describe the frozen selection; `project_complete` remains null, with current remaining work reported separately. An old empty plan can complete while later deliveries remain queued. An adoption preparation failure stays visible for review, with its checkpoint and original error. Matching `refresh_plan` experience can supply a `plan_request` for a proven no-effect operation; it proposes a fresh plan, never automatic execution. A candidate or uncertain effect requires effect reconciliation first.

接收计划的身份覆盖选中的恢复操作。`scope: plan` 与 `plan_complete` 只说明冻结范围，`project_complete` 保持 null，当前剩余工作另列。旧空计划完成不代表后来交付也已接收。采用准备失败保留检查点和原错误，供下一轮复核。匹配的 `refresh_plan` 经验仅对已证明没有应用效果的操作给出 `plan_request` 建议，不自动执行；已有候选或效果未知时先对账实际效果。

MCP 工具名以 `taskcarry_` 开头，提供普通动作，不通过工具初始化或改装项目。服务固定到启动时的项目。协议封装可以不同，实际行为共用同一分发器。

Observation `relations` contain objects with `kind: stage` or `kind: artifact` and an existing `id`. The engine checks task/workspace links and freezes each related record's content fingerprint. Supplied source references remain host-reviewed evidence, not independently read conversations. Identical observations/issues/fixes reuse their existing record; changed content requires the current positive integer `expected_revision`. Original revisions remain available in the local history.

`status.continuity` exposes current observations, runs, issues and fixes. The agenda includes open issues and unfinished runs without replacing actual operation failures. A run freezes identities at `start`; `finish` checks their durable receipt linkage and records `COMPLETED` or `WAITING`, with `project_complete: null`. Changed observations are reported separately. Neither a closed issue nor a completed run is new authorization or business acceptance. `fix.adoption` compares the current project's managed setup files, runtime disk fingerprint and version; it never installs software or proves another host process reloaded.

观察关系使用 `{"kind":"stage","id":"阶段ID"}` 或 `{"kind":"artifact","id":"材料ID"}`。内容变化须提供当前整数修订号；不变则复用。`status.continuity` 查询持久依据，`agenda` 显示未关闭问题与未完成轮次。单轮完成只核对冻结记录的回执，不重新执行 Git，也不代表项目结束；版本采用说明来自实际安装清单与磁盘指纹，不能冒充原生宿主重新加载验证。

New plans and operations carry `operation_protocol: 1`. Untagged earlier records follow the compatible version-one contract; unsupported future protocols are rejected before continuing the selected operations. Tool version tags alone are not authorization to replay an effect.

See `python -m taskcarry --help` and MCP `tools/list` for the installed version's exact interface. Fault-injection controls are for explicitly marked synthetic test projects only; they are not a supported production recovery method. 参数以已安装版本帮助和工具列表为准；故障注入只用于明确标记的合成项目。

`setup` is CLI-only: `mode` is `preview`, `install`, or `uninstall`; optional `server_name` selects a distinct MCP service name and is retained for later setup calls. Setup changes project-managed Skills and the generated configuration fragment, not live Codex configuration or business Git branches. A frozen pending install resumes only when its candidate and exact file evidence remain valid. `doctor.runtime` reports the package imported by the current process and managed setup state. See [maintenance and upgrades](en/governance-maintenance.md).

`setup` 仅通过 CLI 配置，支持 `mode` 和可选 `server_name`。安装中断后，在相同候选和精确文件证据仍有效时接续；实际文件有独立修改时保留现场。它不修改已启用的 Codex 配置或业务分支。`doctor.runtime` 区分当前进程导入的版本和项目接入状态，不能替代其他进程的实际加载验证。详见[维护与升级](zh-CN/governance-maintenance.md)。
