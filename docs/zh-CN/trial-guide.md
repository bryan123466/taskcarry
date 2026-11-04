# 试用、安装、升级与卸载

[English](../en/trial-guide.md) · [首页](../../README.zh-CN.md)

本候选版先在新建、可丢弃的项目中试用，不需要 API Key、第二台电脑、服务器或定时任务。工具自身不调用模型；需要模型参与时使用你已有的 Codex。

## 1．在虚拟环境内安装

解压发布源码并在该目录打开终端，运行 `python -m venv .venv`。之后本指南中的 `python`，Windows 使用 `.venv/Scripts/python.exe`，macOS/Linux 使用 `.venv/bin/python`：

```text
python -m pip install .
python -I -X utf8 -m taskcarry --help
```

安装可能需要本机缓存或下载的 Python 构建工具，安装后的工具运行时使用标准库。Git 集成需要单独安装 Git。不要仅为绕过项目权限错误而改用管理员终端。

## 2．生成并初始化虚构项目

```text
python examples/quality_forms/bootstrap.py --destination ../taskcarry-quality-demo
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control init --input ../taskcarry-quality-demo/requests/init.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control workspace --input ../taskcarry-quality-demo/requests/workspace-baseline.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control workspace --input ../taskcarry-quality-demo/requests/workspace-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control task --input ../taskcarry-quality-demo/requests/task-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control doctor
```

其他两个工作者分别有 `workspace-review.json`、`task-review.json`、`workspace-quality.json`、`task-quality.json`，只登记本次准备使用的工作者。基线和工作者各有独立 Git 工作树，控制目录保存治理状态。

## 3．保存工作，不立即交付

在表单工作者的 `forms/inspection.csv` 中修改虚构数值，先保存文件，再运行：

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control checkpoint --input ../taskcarry-quality-demo/requests/checkpoint-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control status
```

核对返回的检查点编号。请求将任务标记暂停并记录下一步，不创建交付阶段，也不覆盖编辑器尚未保存的内容。

恢复演练使用一个 JSON 文件，包含 `checkpoint_id` 和一个尚不存在的独立绝对目录 `destination`，再用 `restore --input` 调用。原工作区应保持不变。核对恢复目录的文件及 Git 状态；恢复生成的 Git 提交会标明合成恢复性质，并保留原 HEAD 来源，不冒充原仓库的完整历史。

## 4．明确交付一个稳定阶段

当小范围虚构修改可以交付时：

```text
git -C ../taskcarry-quality-demo/workers/forms add -- forms/inspection.csv
git -C ../taskcarry-quality-demo/workers/forms commit -m "Improve fictional inspection form"
git -C ../taskcarry-quality-demo/workers/forms rev-parse HEAD
```

打开 `requests/submit-forms-template.json`，把 `REPLACE_WITH_YOUR_NEW_COMMIT` 换成精确提交号，另存为 `requests/submit-forms.json`。其中 `base` 来自合成基线，`paths` 必须与基准到提交的实际变化路径完全一致；只有实际提交了字段说明时才加入该路径。

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control submit --input ../taskcarry-quality-demo/requests/submit-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control reconcile --input ../taskcarry-quality-demo/requests/reconcile-plan.json
```

阅读计划后新建 JSON 文件，填写 `baseline: "baseline"`、`execute: true` 和返回的 `plan_id`，用 `reconcile --input` 执行。同时核对返回结果和基线 Git 日志。不要直接改保存的计划来强迫过期计划通过。

完成接收后再次计划，确认已经完成的效果不会重新成为新工作。这个资料的技术接收不代表任何真实品质流程获得批准。

## 5．演练并行工作与采用

第二个工作者仅修改其分配路径，保存检查点后交付。分支名不同不足以证明任务独立，应有明确任务和阶段关系。

以 `templates/adopt-plan.json` 为起点，核对计划后把计划号填入执行请求。报告成功时应确认本地提交、暂存、未暂存和新文件的实际保全。工具报告冲突时，保留原工作并报告该具体冲突；不能把采用失败解释成可以 reset 或 clean 工作区。

累计阶段使用 `relation: "cumulative"` 与 `supersedes` 列表，证明旧阶段的祖先关系和变化路径覆盖。仅有更新的版本标签不够。

## 6．接入项目内 Codex 指引

创建内容为 `{"mode":"preview"}` 的 `setup-preview.json`，运行：

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-quality-demo/control setup --input setup-preview.json
```

预览不应修改文件。确认受管理路径适合本项目后，创建 `{"mode":"install"}` 的 `setup-install.json` 并使用同样命令调用该文件。安装生成：

- `.agents/skills/taskcarry-project-setup/SKILL.md`
- `.agents/skills/taskcarry-task-delivery/SKILL.md`
- `.agents/skills/taskcarry-governance-reconcile/SKILL.md`
- `.agents/skills/taskcarry-experience-recovery/SKILL.md`
- `.taskcarry/codex.mcp.toml`
- `.taskcarry/setup-manifest.json`

这些路径都相对于指定项目。将**该项目目录**作为 Codex 任务工作目录打开，以便发现项目内 Skills。工作者路径由工作区登记提供，各工作者的实际编辑范围仍需明确。

TOML 是**配置片段，不等于连接已经启用**。它包含固定到该项目的 stdio 服务命令。核对内容后，按本机 Codex 支持的 MCP 配置方式加入；安装助手不覆盖 `.codex/config.toml`、`AGENTS.md` 或用户全局设置。宿主设置方式以[官方 MCP 文档](https://developers.openai.com/codex/mcp)为准。

按宿主需要刷新工具连接后，请 Codex 调用 `taskcarry_doctor` 和 `taskcarry_status`。CLI 或协议测试不能证明桌面连接已经成功，反馈时要分别说明。

工作者提示词示例：

> 使用已安装项目指引和已登记的 forms 工作区，为 TASK-FORMS 只完善虚构检查表。不修改 review 或 quality 工作者的文件。暂停前保存检查点。先明确可交付阶段，如果属于我的任务要求就用工具交付。不要运行定时任务，不操作这个独立示例之外的项目。

治理提示词示例：

> 查看该示例的当前状态和可接收阶段，依据已有证据解释累计关系。计划并执行符合条件的本地接收，核对实际 Git 效果。暂停任务保留为状态。若已有恢复经验适用，核对范围后使用；否则报告具体缺失条件。不要推送、部署或修复电脑。

## 7．核对结果后再报告成功

在工具源码目录运行 `python -m unittest discover -s tests -v` 并记录实际结果。故障测试使用自己的独立仓库和明确合成标记，不对真实项目注入故障。

分别报告本地 CLI、真实 Git 集成、MCP 协议、实际 Codex 连接、模型参与的任务判断和原生调度。本候选版不要求或执行原生调度。[验证报告](../VALIDATION.md)说明维护者实际覆盖的范围。

## 升级

停止示例 MCP 进程，等待工具调用完成。在没有写入时保留原发行版并对可丢弃示例做本地备份。创建**新的**虚拟环境，安装新候选，阅读迁移说明，先运行 `doctor` 和独立演练再使用原状态。本候选版不承诺跨版本自动数据迁移，遇到不支持格式应报告，不手改数据库。

安装助手只在所有权和内容检查通过时更新受管理文件，被用户修改的文件保留并报告冲突。MCP 片段包含生成时的 Python 路径，移动环境或升级后需要核对。

## 卸载

创建内容为 `{"mode":"uninstall"}` 的 `setup-uninstall.json`，在相同项目调用 `setup --input`。助手移除符合条件且未修改的受管理文件，保留修改过的文件、核心任务状态与快照。手动启用的 MCP 配置仍由用户管理，需要核对身份后单独移除。

之后可在独立环境运行 `python -m pip uninstall taskcarry`，或停用该专用环境。保留仍需要的检查点与证据，不使用会删除无关项目父目录的清理命令。

## 反馈

使用[问题模板](../../templates/defect-report.md)，提供小型虚构复现、版本、平台、接口、预期、错误和出错前是否已经发生 Git 效果。不上传实际项目资料或完整状态目录。
