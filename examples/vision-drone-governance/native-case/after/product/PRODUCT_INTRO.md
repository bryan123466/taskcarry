> 公开导出：来自本次实际合成对话产物；已移除本机绑定或改写链接。它不是原始宿主回执。

# RC8 室内固定障碍离线回放

RC8 用合成帧元数据和预置候选事件演示室内固定障碍的监控界面。在桌面 Chrome 本地打开 [monitor.html](../software/monitor.html)，载入 [rc8-indoor-replay-v1.json](../software/rc8-indoor-replay-v1.json)，即可逐拍查看画面区域、候选和模拟链路状态。（[software-evidence.json](../software/software-evidence.json) · `software.offline-load`）

画面区域把候选画成框，并标明左侧、中部或右侧。第 0 拍有一条左侧墙面候选，第 1 拍在同一帧列出中部立柱和右侧箱体，两个候选可分别查看。（[software-evidence.json](../software/software-evidence.json) · `software.tick-0`、`software.tick-1`）（[algorithm-evidence.json](../algorithm/algorithm-evidence.json) · `frame_event_contract`）

空帧显示「本帧无候选」。第一次缺帧显示「等待新帧」，第二次连续缺帧进入「模拟断流」。下一拍收到样例帧时，页面显示「链路已恢复」，并重新画出候选框。（[software-evidence.json](../software/software-evidence.json) · `software.tick-2`、`software.tick-3`、`software.tick-4`、`software.tick-5`）（[hardware-evidence.json](../hardware/hardware-evidence.json) · `link_replay`）

这份样例共六拍，收到四帧，其中一帧没有候选。结束时，「候选日志」保留四条候选，「链路记录」保留三次状态变化，便于回看候选出现在哪一帧，以及模拟链路何时变化。（[algorithm-evidence.json](../algorithm/algorithm-evidence.json) · `empty_and_missing`）（[software-evidence.json](../software/software-evidence.json) · `software.candidate-log`、`software.link-log`）
