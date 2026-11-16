> 公开导出：来自本次实际合成对话产物；已移除本机绑定或改写链接。它不是原始宿主回执。

# RC8 室内回放演示路线

开场向观众说明，本次用合成帧元数据和预置事件逐拍演示室内固定障碍的候选显示，以及模拟链路的等待、断流和恢复。

## 载入并从头开始

把 [monitor.html](../software/monitor.html) 和 [rc8-indoor-replay-v1.json](../software/rc8-indoor-replay-v1.json) 放在同一目录。用桌面 Chrome 本地打开监控页，在「本地回放 JSON」选择该文件，点击「载入」。看到「已载入 rc8-indoor-replay-v1.json · 6 拍」后点「重置」，确认画面显示「等待单步」，页首显示「等待首帧」。（[software-evidence.json](../software/software-evidence.json) · `software.fixture-bytes`、`software.offline-load`、`software.reset`）

## 六次单步

每点击一次「单步」推进一拍。表内时间以合成回放起点计。（[hardware-evidence.json](../hardware/hardware-evidence.json) · `replay_clock`）

| 单步次数 | 节拍 | 相对时间 | 帧标识 | 给观众看的变化 | [software-evidence.json](../software/software-evidence.json) 检查 |
| ---: | ---: | ---: | --- | --- | --- |
| 1 | 0 | 0 ms | `indoor-000` | 出现左侧墙面，页首为「模拟已连接」。 | `software.tick-0` |
| 2 | 1 | 67 ms | `indoor-001` | 同一帧有中部立柱和右侧箱体，两条候选分别显示。 | `software.tick-1` |
| 3 | 2 | 133 ms | `indoor-002` | 有帧标识，显示「本帧无候选」，模拟连接维持。 | `software.tick-2` |
| 4 | 3 | 200 ms | — | 第一次缺帧，显示「等待新帧」，页首仍为「模拟已连接」。 | `software.tick-3` |
| 5 | 4 | 267 ms | — | 第二次连续缺帧，显示「模拟断流」，「链路记录」增加 `disconnected`。 | `software.tick-4` |
| 6 | 5 | 333 ms | `indoor-005` | 显示「链路已恢复」和左侧箱体，页首回到「模拟已连接」。链路记录增加 `reconnected`，「单步」变为不可用。 | `software.tick-5` |

## 核对记录并重演

请观众回看「候选日志」中的四条记录和「链路记录」中的 `connected`、`disconnected`、`reconnected`。复演时点「重置」，确认两张表回到 0 条，再点「单步」回到第 0 拍。（[software-evidence.json](../software/software-evidence.json) · `software.candidate-log`、`software.link-log`、`software.reset`）
