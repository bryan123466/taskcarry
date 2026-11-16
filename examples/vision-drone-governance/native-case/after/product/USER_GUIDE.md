> 公开导出：来自本次实际合成对话产物；已移除本机绑定或改写链接。它不是原始宿主回执。

# RC8 室内回放使用说明

## 启动

1. 将 [monitor.html](../software/monitor.html) 和 [rc8-indoor-replay-v1.json](../software/rc8-indoor-replay-v1.json) 放在同一目录，用桌面 Chrome 本地打开 [monitor.html](../software/monitor.html)。（[software-evidence.json](../software/software-evidence.json) · `software.offline-load`）
2. 在「本地回放 JSON」选择 [rc8-indoor-replay-v1.json](../software/rc8-indoor-replay-v1.json)，再点「载入」。确认提示为「已载入 rc8-indoor-replay-v1.json · 6 拍」。（[software-evidence.json](../software/software-evidence.json) · `software.fixture-bytes`、`software.offline-load`）
3. 点「重置」，看到「等待首帧」和「等待单步」后点一次「单步」。页面从第 0 拍开始。（[software-evidence.json](../software/software-evidence.json) · `software.reset`、`software.tick-0`）

## 查看候选和区域

在「画面区域」读节拍、相对时间与帧标识，再看候选框旁的列表。候选按框的横向中心归入左侧、中部或右侧。同一帧有多条候选时逐条列出，例如第 1 拍的立柱在中部、箱体在右侧。界面的「置信度」读作随合成事件预置的样例分数。（[software-evidence.json](../software/software-evidence.json) · `software.tick-1`）（[algorithm-evidence.json](../algorithm/algorithm-evidence.json) · `tick_candidates_and_regions`）（[RC8-INDOOR-REPLAY-PROTOCOL.md](../../governance/SHARED_INTERFACE.md)）

## 读懂状态提示

| 页面提示 | 当前状态与操作 | [software-evidence.json](../software/software-evidence.json) 检查 |
| --- | --- | --- |
| 本帧无候选 | 有帧标识，当前帧已交付且候选列表为空。点「单步」继续。 | `software.tick-2` |
| 等待新帧 | 帧标识显示「—」，页首仍为「模拟已连接」。点「单步」查看下一拍。 | `software.tick-3` |
| 模拟断流 | 连续两拍缺帧，当前候选和框已清空。点一次「单步」查看本样例的恢复拍。 | `software.tick-4` |
| 链路已恢复 | 第 5 拍出现左侧箱体，页首回到「模拟已连接」。末拍完成后「单步」不可用。 | `software.tick-5` |

「候选日志」保留已经显示过的候选，「链路记录」单独记录模拟状态变化。要从头播放同一份文件，点「重置」清空这两张表，然后再点「单步」。（[software-evidence.json](../software/software-evidence.json) · `software.candidate-log`、`software.link-log`、`software.reset`）
