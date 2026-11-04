# Inspection and issue-tracking forms / 检查记录与问题处理表单

An optional business example for understanding project governance. A fictional workshop records inspections, reviews findings and follows corrective actions. “Quality” refers to the business subject, not a rating of Agent collaboration. The toolkit can instead govern your own software, documents or other Git-based work.

这是一个可选业务示例：虚构车间记录检查结果、复核问题并跟进纠正措施。“质量检查”是业务主题，**不是对多 Agent 协作能力评分**。使用工具时可以直接接入自己的软件、文档或其他 Git 项目，不必先完成这个示例。

All example identifiers and values are fictional. 示例不含真实公司、客户或人员资料。

## Create the example / 创建示例

From the extracted product directory:

```text
python examples/quality_forms/bootstrap.py --destination ../taskcarry-forms-example
```

The destination must not exist. This creates a Git baseline, three worker worktrees and ready-to-edit JSON requests in the new destination. It does not activate Codex configuration or receive deliveries automatically.

目标目录必须不存在。生成器只在新目录中创建 Git 基线、三个工作者工作区和 JSON 请求文件；不自动启用 Codex 配置或接收成果。

```text
taskcarry-forms-example/
  control/           project governance / 项目治理
  baseline/          receiving baseline / 接收基线
  workers/forms/     inspection records / 检查记录
  workers/review/    review criteria / 复核要求
  workers/quality/   corrective actions / 纠正措施
  requests/          workspace and task requests / 登记与任务请求
```

## Connect and work / 接入并工作

Use the fixed installed interpreter in place of `python` below; isolated commands select that installed package. 下列 `python` 指固定安装解释器，隔离参数保证选择该安装包。

```text
python -I -X utf8 -m taskcarry --project ../taskcarry-forms-example/control init --input ../taskcarry-forms-example/requests/init.json
python -I -X utf8 -m taskcarry --project ../taskcarry-forms-example/control workspace --input ../taskcarry-forms-example/requests/workspace-baseline.json
python -I -X utf8 -m taskcarry --project ../taskcarry-forms-example/control workspace --input ../taskcarry-forms-example/requests/workspace-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-forms-example/control task --input ../taskcarry-forms-example/requests/task-forms.json
python -I -X utf8 -m taskcarry --project ../taskcarry-forms-example/control status
```

Register the review and quality workspaces using their matching request files when you want those roles. Each role can be a Codex chat, another Agent, or a person. Multiple Agents are optional; one user can perform the roles sequentially.

需要其他角色时，使用对应请求登记 review 和 quality 工作区。角色可以由 Codex 对话、其他 Agent 或人承担；并不要求启动多个 Agent，一个用户也可以依次完成这些工作。

| Role / 角色 | Business work / 业务内容 |
|---|---|
| Forms / 表单 | Maintain inspection identifiers, item counts, defect categories and status. / 维护检查编号、对象、数量、缺陷类别与状态。 |
| Review / 复核 | Describe evidence needed to review or close a finding. / 明确问题被复核或关闭所需的证据。 |
| Corrective actions / 纠正措施 | Link actions to inspections and record progress and next steps. / 关联检查记录，说明处置进度和下一步。 |

Work in the assigned workspace, save meaningful checkpoints, deliver stable stages and use governance to receive them and update other workspaces. These are the same operations used on your own project; no fault injection or maintenance-test report is required.

各角色在自己的工作区编辑，保存有意义的工作节点，交付稳定阶段，由治理接收并更新其他工作区。具体命令见[项目接入指南](../../docs/zh-CN/getting-started.md)和[命令参考](../../docs/COMMANDS.md)。
