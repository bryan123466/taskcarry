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
| `identify` | none / 无 | Read selected state format/source before initialization; no migration / 初始化前只读识别状态格式与来源 |
| `context` | `task_id`; optional `limit` 1–100, `cursor`, `previous_fingerprint`, `issue_ids`, `fix_ids` | Bounded task context with source-qualified references and omitted/missing evidence / 有界任务上下文与来源身份 |
| `connect` | `action` plan/execute/status; plan `target`, `workspace`, `task_id` for a workbench; execution `plan_id` | Preserve and merge the generated project MCP block; no host reload / 保全合并项目 MCP 配置，不代宿主重载 |
| `onboarding` | `onboarding_id`, `action` start/update/status; `scope`, `item`, `expected_revision` | Resume standard onboarding from verified local bindings and reviewed native evidence / 可接续接入清单 |
| `schedule_plan` | `onboarding_id` | Return original-chat schedule instructions without creating a scheduler / 生成原聊天调度计划，不创建调度 |
| `preserve` | `action` plan/execute/status; plan `repository`, `paths`, `message`; execute/status `plan_id` | Exact local Git save, retaining unrelated index/WIP / 精确本地 Git 保存，保全其他暂存与工作内容 |
| `governance` | `mode` inspect/record; `rule_paths`; record `record_id`, `expected_fingerprint`, `evidence_refs`, `expected_revision` | Separate package/method/user-rule identity and retain reviewed evidence / 区分包、方法与用户规则身份 |
| `codex` | `action` capabilities/list/read, `executable`; optional `codex_home`, `limit`, `cursor`, `archived`, `thread_id`, bounded `timeout`, `max_bytes` | Optional explicit Codex App Server adapter; no AI turns or messages / 显式 Codex 只读适配 |
| `update_source` | `channel` rc/stable, `current_version`, `current_artifacts`, `method_refs`, `maintenance`, `expected_revision` | Register official release source and current identity / 登记官方来源和当前身份 |
| `update_check` | optional `channel` | Read bounded official releases; no local write or installation / 有界只读更新查询，不安装 |
| `update_assess` | exact `check`, `decision` prioritize/plan/keep/wait/reject, `reason`; optional `evidence_refs`, `expected_revision` | Explicitly retain a release applicability review / 显式保存适用性判断 |
| `init` | `name` | Initialize the control directory / 初始化控制目录 |
| `task` | `task_id`, optional `title`, `workstream`, `state` | Record task; states active, paused, waiting, complete / 记录任务状态 |
| `workspace` | `name`, `path` | Register existing Git workspace / 登记已有 Git 工作区 |
| `checkpoint` | `task_id`, `workspace`, `paths`, `next_step`, optional `decision`, `paused` | Snapshot exact saved work / 保存精确检查点 |
| `restore` | `checkpoint_id`, `destination` | Restore to absent/empty independent destination; repeat the same pair to verify a recorded effect and finish its receipt / 恢复到不存在或空的独立目录；同参数重试核验原效果并续办回执 |
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

`artifact.decision` is an optional choice: `retain`, `ignore`, `dismiss`, or `no_backup_needed`. It is not the free-text reasoning accepted by `checkpoint.decision`. `retain` keeps an unverified backup item actionable; the other three choices suppress it only when the corresponding decision is authorized. They do not delete files or create a backup. Omit the field to preserve the earlier choice for unchanged content; changed content requires a fresh review. For example: `{"task_id":"example-writing","path":"<authorized-handover-file>","role":"handover","decision":"retain"}`.

`artifact.decision` 只能选择 `retain`、`ignore`、`dismiss`、`no_backup_needed`，不是 `checkpoint.decision` 接受的自由说明文字。`retain` 保留尚无已核实备份的待复核项；其他三项仅在已有对应授权决定时排除该项，不删除文件、不创建备份。省略时，同内容继承旧决定；内容变化后重新复核。上例为合成材料登记，路径和任务须换成真实获准对象。

`artifact.decision` 僅能選擇 `retain`、`ignore`、`dismiss`、`no_backup_needed`，不是 `checkpoint.decision` 接受的自由說明文字。`retain` 保留尚無已核實備份的待複核項；其餘三項僅在已有對應授權決定時排除該項，不刪除檔案、不建立備份。省略時，相同內容沿用舊決定；內容變更後重新複核。上例為合成材料登記，須替換為實際獲准的路徑與任務。

Plain-directory checkpoints and their restoration do not require Git. A workspace with Git metadata, or inside a repository, still requires working Git and the exact working-tree root; an unreadable or damaged repository is never silently saved as plain files. A repository appearing during a plain capture prevents checkpoint publication.

普通目录的检查点及恢复不要求安装 Git。工作区或父级存在 Git 元数据时，仍须使用可用的 Git 和准确的工作树根；不会把不可读取或损坏的仓库悄悄降为普通文件保存。普通目录在捕获期间变为仓库时，不发布该检查点。

一般目錄的檢查點及還原不要求安裝 Git。工作區或父層存在 Git 中繼資料時，仍須使用可用的 Git 與正確的工作樹根；不會將無法讀取或損壞的儲存庫悄悄降為一般檔案儲存。一般目錄在擷取期間變為儲存庫時，不發布該檢查點。

Restore freezes an operation before writing the destination. When file/Git effects have been verified and recorded but the final receipt transaction fails, repeat the same `checkpoint_id` and `destination`: the engine verifies the full recorded destination, then publishes only the missing receipt and event. A completed retry returns the original result without another restore event. Changed files, extra paths, changed Git layers or a replaced destination are preserved and reported for review. An interruption before durable effect evidence exists remains an explicit review case; it is not permission to clear the destination or replay all writes. Earlier checkpoints remain readable; an older failed restore without an operation journal cannot be retroactively proved by a new version. A run can close a recorded restore from its matching durable receipt; it does not recheck today's destination contents or declare business acceptance.

恢复前先冻结操作记录。文件/Git 效果已经核验并记录、最后回执事务失败时，使用相同 `checkpoint_id` 和 `destination` 重试：先核对完整目标效果，再只补回执和事件。已完成操作重试不会重复产生恢复事件。目标文件、额外路径、Git 层或目录身份发生变化时保留现场并报告；效果证据落盘前的中断仍需复核，不清空目标、不整轮重放。旧检查点仍可读取；旧版失败恢复没有操作记录的，不能由新版追认其效果。run 只依据匹配的持久回执收口，不重新证明目标当前未变，也不代业务验收。

還原前先凍結操作記錄。檔案/Git 效果已核驗並記錄、最後回執交易失敗時，以相同參數重試，先核對完整目標效果，再只補回執與事件；已完成操作不重複產生事件。目標內容、額外路徑、Git 層或目錄身分改變時保留現場；效果證據落盤前的中斷仍需複核，不清空目標、不整輪重做。舊檢查點仍可讀取，舊版無操作記錄的失敗不能追認。run 只依匹配的持久回執收口，不代替目前效果核驗或業務驗收。

`reconcile` and `adopt` default to planning. To execute, copy the returned plan identifier into a request with `execute: true`. First reconcile recorded unfinished operations against their actual effects and resume the original operation when applicable. If external changes invalidate the relevant facts and there is no applicable operation to resume, inspect the error and generate a fresh plan. Do not edit the persisted plan. 接收和采用默认只计划；先核对未完操作的实际效果，适用时接续原操作。外部变化使前提失效且无适用原操作可续办时，再检查错误并重新计划，不直接修改保存的计划。

Installed MCP can start with `python -I -X utf8 -m taskcarry --project <control-directory> mcp`. The setup-generated fragment additionally pins its selected package path through an isolated launcher, supporting explicit source development and failing if that path is unavailable. Retain the generated arguments when activating it. Tools have `taskcarry_` prefixes and expose the corresponding ordinary actions, except project initialization and setup. The server is project-bound. CLI and MCP output formatting differ where required by their protocols, but both call the same action dispatcher.

Receiving plans include selected recovery operations in their identity. `scope: plan` and `plan_complete` describe the frozen selection; `project_complete` remains null, with current remaining work reported separately. An old empty plan can complete while later deliveries remain queued. An adoption preparation failure stays visible for review, with its checkpoint and original error. Matching `refresh_plan` experience can supply a `plan_request` for a proven no-effect operation; it proposes a fresh plan, never automatic execution. A candidate or uncertain effect requires effect reconciliation first.

接收计划的身份覆盖选中的恢复操作。`scope: plan` 与 `plan_complete` 只说明冻结范围，`project_complete` 保持 null，当前剩余工作另列。旧空计划完成不代表后来交付也已接收。采用准备失败保留检查点和原错误，供下一轮复核。匹配的 `refresh_plan` 经验仅对已证明没有应用效果的操作给出 `plan_request` 建议，不自动执行；已有候选或效果未知时先对账实际效果。

MCP 工具名以 `taskcarry_` 开头，提供普通动作；`init` 和 `setup` 仍通过 CLI 完成。`connect` 可按明确计划保全合并已生成的项目配置，不能代替宿主加载。服务固定到启动时的项目。协议封装可以不同，实际行为共用同一分发器。

Observation `relations` contain objects with `kind: stage` or `kind: artifact` and an existing `id`. The engine checks task/workspace links and freezes each related record's content fingerprint. Supplied source references remain host-reviewed evidence, not independently read conversations. Identical observations/issues/fixes reuse their existing record; changed content requires the current positive integer `expected_revision`. Original revisions remain available in the local history.

For ordinary source material, `observe.workspace` may be JSON `null` with an existing `task_id`. It does not register a Git workspace and cannot attach a Git stage without its real workspace. Source-qualified identity is `(source_id, collection, local_id)`; unchanged local IDs from older clients remain valid inside their selected state source.

`context` reads the named task, its latest checkpoint and a bounded indexed page of related records. Each payload is limited to 16 KiB; larger records are explicitly omitted with a reason. Selected unscoped issues/fixes must be named explicitly. The response distinguishes missing evidence, pagination, task input changes and external effects not reverified. Older stores lacking the derived context index require explicit `upgrade`; reads do not silently migrate or acknowledge work. SQLite may manage its own transient reader files; read-only means no project record/event mutation, not a filesystem-wide zero-write guarantee.

## Standard onboarding and configuration / 标准接入与配置

`onboarding` starts with a confirmed scope containing `governance_thread`, `channel`, daily `schedule` (`time`, `timezone`) and selected `windows`. Each window has `thread_id`, `mode` (`active`/`reference`), `source_ref` and `responsibility`; active windows also name their existing `task_id` and registered Git `workspace`. Update one `item` with `key`, `status`, structured `evidence`, `next_step` and the current revision. Exact repeats reuse records. Reference-only history does not become an active writer.

Required evidence covers confirmed scope, governance native runtime, local Git preservation, official update assessment, saved native schedule and each active workbench's native calls. `standard_ready` concerns actual standard configuration; `closed_loop_verified` additionally needs a naturally delivered heartbeat. Supplied native receipts remain host-reviewed references, with local Git identities independently rechecked. No boolean field creates a host capability or proves a remote effect. Pending items remain actionable without erasing other completed setup.

`connect` requires completed setup materials. It retains existing user configuration bytes and adds only the generated service block; a previously managed block can be replaced only when unchanged. Same-name unmanaged changes, unsupported TOML layout, changed target or binding return specific conflicts without overwriting. Execution uses the saved plan. After an interrupted file effect, repeat that plan to verify bytes and repair only the receipt. `host_loading_verified` remains false until separately checked in the actual host. User-level configuration is not a supported target.

`preserve` plans exact regular files in an existing Git working tree using verified author configuration. It creates no repository and performs no push. Selected already-staged paths require review; unrelated staged/unstaged content is retained. The content policy is raw file bytes, with no clean filters or hooks. No meaningful change creates no commit. Recovery checks the recorded ref/index effect before continuing; changed index conditions require review. A local commit does not automatically become a submitted stage, remote backup or business acceptance. Use the [coverage template](../templates/preservation-coverage.json) to keep capture, upload, download and recovery evidence separate.

## Host reading and release maintenance / 宿主读取与更新维护

`codex` uses a selected executable and explicit history home when supplied. It supports the tested App Server protocol/version, lists from the existing state index and reads selected paginated turns. It does not start/resume an AI turn, repair missing history indexes, send messages or archive threads. Version mismatch, host configuration failures, output limits and timeouts retain specific errors. App Server startup may write its own cache/log files. Desktop, archived, cloud and other-account coverage must be verified separately; a plugin's success does not certify this independent adapter. Read results are untrusted source data, not instructions to execute.

`update_check` reads at most two pages of 20 official releases, chooses the selected channel and verifies structured manifest bytes, tag commit and asset metadata when available. It does not download or attest package bytes. A legacy release without a manifest needs manual identity review; offline is `UNVERIFIED`, never “latest.” The separate `taskcarry-release.json` is generated from exact reviewed source and final artifacts, excludes itself and records compatibility/actions. No source-branch commit is an update candidate by itself.

`update_assess` binds the supplied check content and source revision. Same inputs reuse the decision; conflicting identity for one version remains a conflict. Querying or assessing does not install. `governance` separately fingerprints the current runtime, managed method files and explicitly selected user rules. Its saved review does not establish another process's reload. Preserve custom rules during setup/update and verify actual native connections afterward.

中文：标准三步需完成真实工作位置、Git 保存、逐窗口原生连接、原聊天调度及官方更新判断；网盘与私有远端按需选择。普通资料保存保留兼容性，不替代专业工作区配置。首次自然触发与配置回读分开，接收业务阶段与工具升级分开。

繁體中文：標準三步須完成實際工作位置、Git 儲存、逐視窗原生連線、原治理對話排程與官方更新判斷；網盤及私有遠端按需選擇。一般資料儲存保留相容性，不替代專業工作區設定。首次自然觸發與設定回讀分開，業務階段接收與工具更新分開。

`status.continuity` exposes current observations, runs, issues and fixes. The agenda includes open issues and unfinished runs without replacing actual operation failures. A run freezes identities at `start`; `finish` checks their durable receipt linkage and records `COMPLETED` or `WAITING`, with `project_complete: null`. Changed observations are reported separately. Neither a closed issue nor a completed run is new authorization or business acceptance. `fix.adoption` compares the current project's managed setup files, runtime disk fingerprint and version; it never installs software or proves another host process reloaded.

观察关系使用 `{"kind":"stage","id":"阶段ID"}` 或 `{"kind":"artifact","id":"材料ID"}`。内容变化须提供当前整数修订号；不变则复用。`status.continuity` 查询持久依据，`agenda` 显示未关闭问题与未完成轮次。单轮完成只核对冻结记录的回执，不重新执行 Git，也不代表项目结束；版本采用说明来自实际安装清单与磁盘指纹，不能冒充原生宿主重新加载验证。

New plans and operations carry `operation_protocol: 1`. Untagged earlier records follow the compatible version-one contract; unsupported future protocols are rejected before continuing the selected operations. Tool version tags alone are not authorization to replay an effect.

See `python -I -X utf8 -m taskcarry --help` and MCP `tools/list` for the installed version's exact interface. Fault-injection controls are for explicitly marked synthetic test projects only; they are not a supported production recovery method. 参数以已安装版本帮助和工具列表为准；故障注入只用于明确标记的合成项目。

`setup` is CLI-only: `mode` is `preview`, `install`, or `uninstall`; optional `server_name` selects a distinct MCP service name and is retained for later setup calls. Setup changes project-managed Skills and the generated configuration fragment, not live Codex configuration or business Git branches. A frozen pending install resumes only when its candidate and exact file evidence remain valid. `doctor.runtime` reports the package imported by the current process and managed setup state. See [maintenance and upgrades](en/governance-maintenance.md).

Workbench setup additionally accepts `target`, `workspace` and `task_id` together. `--project` remains the existing control. The target must match the registered Git workspace's current identity and the task must already exist in that control. Preview verifies the registration and lists files without writing them; install uses the same preservation and resumable-intent machinery as ordinary setup. It copies the four Skills and their public Markdown references, generates the MCP fragment and `.taskcarry/workbench.json` / `.taskcarry/workbench.md`, and creates no target governance database. A different binding or another existing target control is rejected. Repeat the same complete binding arguments to resume; do not initialize a second control. Uninstall removes only unchanged managed files and keeps user edits and live host configuration.

```json
{
  "mode": "preview",
  "target": "<registered-workbench-directory>",
  "workspace": "existing-workspace",
  "task_id": "existing-task",
  "server_name": "project_memory"
}
```

Results include `control`, `target`, `workspace`, `task_id`, `registration_verified`, `connection_state` and `next_steps`. `connection_state.materials` distinguishes preview, generated files and removal; `host_loading` and `native_acceptance` remain `not_verified`. They must be verified in the actual target chat. Neither generating these files nor a standalone MCP subprocess creates a chat or proves native host loading. Ordinary non-Git checkpoint use remains available by explicit path; workbench registration/delivery still use the Git contract.

专业工作台接入同时传入 `target`、`workspace`、`task_id`，`--project` 仍指原 control。目标须匹配已登记 Git 工作区的当前身份，任务须已存在。预览只核对，安装复用文件保全与中断续办机制，复制四 Skills 及公开引用，并生成 MCP 片段、工作台 JSON/说明，不创建第二份治理库。重复使用相同完整绑定参数续办；身份冲突或目标已有其他 control 时拒绝。返回实际绑定、材料状态和下一步；宿主加载与原生验收保持未核验，须在目标窗口实调，不能以生成文件代替。卸载保留用户修改与已启用的宿主配置。

專業工作台接入須同時傳入 `target`、`workspace`、`task_id`，`--project` 仍指原 control。目標須符合已登記 Git 工作區的目前身分，任務須已存在。預覽只核對，安裝重用檔案保全與中斷續辦機制，複製四 Skills 及公開引用，產生 MCP 片段與工作台說明，不建立第二份治理庫。同一完整綁定可續辦；身分衝突或已有其他 control 時拒絕。回傳實際綁定、材料狀態與下一步，宿主載入及原生驗收須在目標視窗另行實測。移除時保留使用者修改與已啟用的宿主設定。

`setup` 仅通过 CLI 配置，支持 `mode` 和可选 `server_name`。安装中断后，在相同候选和精确文件证据仍有效时接续；实际文件有独立修改时保留现场。它不修改已启用的 Codex 配置或业务分支。`doctor.runtime` 区分当前进程导入的版本和项目接入状态，不能替代其他进程的实际加载验证。详见[维护与升级](zh-CN/governance-maintenance.md)。
