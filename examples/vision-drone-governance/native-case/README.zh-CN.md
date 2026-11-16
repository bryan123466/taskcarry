# 原对话怎样共同形成一段能演示的产品

[English](README.md) · [繁體中文](README.zh-TW.md) · [返回实例](../README.zh-CN.md)

这里收录的是一次真实执行的**合成项目对话练习**：三个原窗口先分别形成软件、算法、硬件资料，治理窗口读取选定的历史，保留原成果，整理共同决定，再让专业窗口接着推进。目录里的工程材料来自那些对话的实际产物，经审阅后导出；它们与上一级 `initial/` 中预先编写的教程种子不同。

成果是一段可以离线查看的室内固定障碍回放：同一帧中的立柱与箱体怎样显示、空帧怎样与没有收到帧区分、连续两拍缺帧时怎样提示模拟断流，以及下一帧到来怎样恢复。数据是人工构造的帧元数据与候选事件，没有运行识别模型、连接真实飞控或完成试飞。

## 先看成果

下载完整产品包后，在本目录打开 [after/software/monitor.html](after/software/monitor.html)。选择同目录的 [rc8-indoor-replay-v1.json](after/software/rc8-indoor-replay-v1.json)，点“载入”“重置”，再点六次“单步”。GitHub 文件页显示的是源码；离线页面需要从下载后的目录打开。

| 拍号 | 页面应显示什么 | 项目需要共同明确什么 |
| --- | --- | --- |
| 0 | 左侧墙面，建立模拟连接 | 类别字典与框到显示区域的映射。 |
| 1 | 同一帧里的中部立柱、右侧箱体 | 同帧多个候选的关联、顺序与展示。 |
| 2 | 本帧无候选，保持连接 | 成功处理的空帧有自己的含义。 |
| 3 | 等待新帧，保持连接 | 未收到帧不能被解释成没有障碍。 |
| 4 | 模拟断流 | 连续两拍缺帧的明确定义。 |
| 5 | 左侧箱体，链路恢复 | 恢复后的当前结果与历史日志如何呈现。 |

页面、校验器和硬件说明使用同一份输入原字节，SHA-256 为 `2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17`。界面中的候选分数是人工样例分数，不是模型性能。

## 治理连接起来的具体内容

开始时，三个窗口的接口并不一致。

| 原成果 | 原先的差异 | 这次共同推进的结果 |
| --- | --- | --- |
| [软件简报与原页面](before/software/SOFTWARE_BRIEF.md) | `region` 直接是左、中、右；示例含“围挡”，时间和分数还没有统一。 | [新页面](after/software/monitor.html)按归一化框中心映射区域，使用墙面、立柱、箱体字典，并显示逐拍时间、空帧和模拟链路。 |
| [算法原计划](before/algorithm/ALGORITHM_PLAN.md) | 六帧旧样例以 40 ms 间隔演示评估规则，尚未与其他窗口对齐。 | [校验器](after/algorithm/validate_replay.py)使用共同的 15 fps 名义节拍，核对帧关联、字段、边界和非法输入；旧 40 ms 样例继续保留。 |
| [硬件原概念](before/hardware/HARDWARE_CONCEPT.md) | 输入和缓冲只是设计假设，采集时间提案与算法时间字段不同。 | [硬件复算](after/hardware/HARDWARE_REPLAY.md)核对同一段时间和链路序列；采集时间、实际资源和延迟保持待测。 |

治理先保存[接入时记忆](governance/INTAKE_MEMORY.md)，其中“室内外尚未确认”保持为当时的判断。操作者随后确认第一阶段只做室内固定障碍离线演示；治理据此形成[共同协议](governance/SHARED_INTERFACE.md)。专业窗口沿原工作继续，留下各自实际观察，治理再作[跨专业技术复核](governance/TECHNICAL_REVIEW.md)。原三个窗口的 12 份初版文件均保留，并在导出前与首次保存的内容摘要核对。

产品与演示职责是在发现需要面向读者讲清成果后才增加的。[角色刚建立时的说明](before/product/PRODUCT_DEMO_BRIEF.md)与停点保留。该窗口随后使用同一页面和输入，在浏览器实际核对 11 项检查，完成[产品介绍](after/product/PRODUCT_INTRO.md)、[演示路线](after/product/DEMO_ROUTE.md)及[使用说明](after/product/USER_GUIDE.md)。它的表述引用技术检查，没有把模拟结果写成实飞承诺。[产品复核导出](after/product/product-evidence.json)记录了相同界面与数据的摘要、实际观察和引用关系；治理的[最终项目复核](governance/PROJECT_REVIEW.md)再核对三稿，并保留发现的证据摘要缺口。此目录的文件与完成范围以 [case-manifest.json](case-manifest.json) 为准。

这次练习使用了分别已有工作目录的专用合成窗口。它不要求每位用户为每个对话新建目录，也不是多个聊天共享同一目录功能的现场验收；该功能另凭对应内核和宿主验证。

## 可以怎样复核

在本目录使用 Python 3.11+，无需安装第三方库或连接 TaskCarry 服务：

```text
python -I -B -X utf8 after/algorithm/validate_replay.py after/algorithm/rc8-indoor-replay-v1.json
python -I -B -X utf8 after/hardware/verify_hardware_replay.py
```

前一条检查输入摘要、六拍关联、坐标边界及非法输入，后一条复算时间、断流/恢复和资源算术。两条只读输入并向标准输出报告结果，不创建治理、调度或真实业务任务。硬件结果保留三项待测条件，这些不是本轮脚本失败。

原专业结果经过脱敏整理为：[软件 13 项检查](after/software/software-evidence.json)、[算法检查与待验证项](after/algorithm/algorithm-evidence.json)、[硬件 6 项通过与 3 项待测](after/hardware/hardware-evidence.json)、[产品 11 项浏览器复核](after/product/product-evidence.json)。JSON 中的 `export_metadata` 说明处理方式；公开导出不是原始宿主回执，不能用导出文件摘要冒称原回执摘要。产品报告指向的其他公开报告和协议摘要已重新计算；原始映射、机器路径、真实聊天身份和运行配置留在私有验证记录中。

产品报告的算法摘要只汇总了 `checks`，漏列算法原报告在 `pending_checks` 中保留的两项：共同回放的参考框评价，以及真实识别与飞行性能。[治理最终复核](governance/PROJECT_REVIEW.md)指出了这处遗漏。导出保留原记录并注明摘要缺口；这些能力继续待验证，不能用产品摘要中的空列表判断它们已完成。

**原生 MCP 与自然定时闭环尚未在这批材料中验收通过。** 文件读取、实际技术回放、工作台发布、原窗口原生加载和自然调度分别判断。这里展示已发生的共同技术推进，不把安装文件存在或回放成功写成所有治理步骤都已完成。真实识别、实体硬件、多机并行与长期运行也不在本次证据范围内。
