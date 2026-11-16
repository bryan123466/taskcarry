> 公开导出：来自本次实际合成对话产物；已移除本机绑定或改写链接。它不是原始宿主回执。

# RC8 室内固定障碍离线回放技术复核

**`rc8-indoor-replay-v1` 的三份专业回执与共用输入及协议一致。** 这批证据支持分享可重复的室内固定障碍合成离线演示。产品介绍、演示路线和使用说明由产品原窗口根据技术结果起草。 [回放协议](SHARED_INTERFACE.md)

## 输入和六拍结果

共用 JSON 与三个专业目录的副本各为 2,113 字节，重新计算的 SHA-256 均为 `2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17`。三份回执记录同一版本和摘要，软件回执还记录了 Chrome 实际选中文件的字节摘要。 [共用输入](rc8-indoor-replay-v1.json) · [software-evidence.json](../after/software/software-evidence.json) · [algorithm-evidence.json](../after/algorithm/algorithm-evidence.json) · [hardware-evidence.json](../after/hardware/hardware-evidence.json)

下表把软件实测回执的候选、归一化框、显示区和链路日志，与算法逐拍校验及硬件时序验算比对。六拍均匹配。

| 拍号 | 相对时间 | 帧 | 与证据一致的观察 |
| --- | ---: | --- | --- |
| 0 | 0 ms | `indoor-000` | 左侧墙面，记录 `connected`。 |
| 1 | 67 ms | `indoor-001` | 同一帧显示中部立柱和右侧箱体，两个框和候选次序匹配。 |
| 2 | 133 ms | `indoor-002` | 收到并处理空帧，显示「本帧无候选」，链路已连接。 |
| 3 | 200 ms | 无 | 连续缺帧计数为 1，显示「等待新帧」，链路已连接。 |
| 4 | 267 ms | 无 | 连续缺帧计数为 2，显示「模拟断流」，记录 `disconnected`。 |
| 5 | 333 ms | `indoor-005` | 显示左侧箱体和「链路已恢复」，缺帧计数清零，记录 `reconnected`。 |

总计 6 拍、4 个收到的帧、4 条候选、1 个成功处理的空帧和 2 拍连续缺帧。软件候选日志最终为 4 行，链路日志为 3 行。空帧与缺帧拍均清空当前框和候选显示。 [软件逐拍与日志](../after/software/software-evidence.json) · [算法帧关联](../after/algorithm/algorithm-evidence.json) · [硬件帧交付与链路](../after/hardware/hardware-evidence.json)

## 可供分享稿使用的成果

- **离线监控演示。** 将 `monitor.html` 与原字节的 `rc8-indoor-replay-v1.json` 放在一起。在 Chrome 本地打开页面，选择 JSON，点「载入」「重置」，再点六次「单步」。原软件窗口用无头 Chrome 实际操作并读回页面和日志，本次记录中外部请求和页面错误均为空。重置后回到等待首帧并清空日志。适合引用 `software.offline-load`、`software.tick-0` 至 `software.tick-5`、`software.candidate-log`、`software.link-log` 和 `software.reset`。 [软件实测回执](../after/software/software-evidence.json)
- **合成事件校验。** `validate_replay.py` 以共用源文件和保留副本各执行一次，两次退出码均为 0，结果一致。实证覆盖帧号与时间关联、三种类别、有限分数、归一化正面积框和空帧。算法与软件均验证中心点恰为 `1/3` 时归中部、恰为 `2/3` 时归右侧。算法还记录五种非法输入被拒绝。原 `40 ms` 样例用于原计划的匹配走查，本版的时间来自 `15 fps` 的逐拍取整。适合引用 `fixture_identity`、`frame_event_contract`、`region_boundary_equality`、`invalid_events_rejected` 和软件的 `software.zone-boundaries`。 [算法校验回执](../after/algorithm/algorithm-evidence.json) · [软件区域回执](../after/software/software-evidence.json)
- **合成输入与时序验算。** 硬件回执按名义 `15 fps` 独立复算出 `0、67、133、200、267、333 ms`。`640×480 RGB24` 紧密排列的估算为 `1,920 B/行`、`921,600 B/帧`、`13,824,000 B/s` 名义原始负载。原 3 帧假设下为 `2,764,800 B`，仅计算原始帧字节。可随技术材料附上 `HARDWARE_REPLAY.md` 和 `verify_hardware_replay.py`。适合引用 `input_profile`、`replay_clock`、`link_replay` 和 `resource_arithmetic`。 [硬件验算回执](../after/hardware/hardware-evidence.json)

## 证据适用范围

- 本轮帧内容是合成元数据和预置候选。人工样例分数用于演示字段。真实识别、精确率与召回率、避障成功率、室外和实飞均待相应数据及测试。算法回执的 `reference_region_evaluation` 和 `measured_recognition_and_flight_performance` 为 `PENDING`。 [算法待验证项](../after/algorithm/algorithm-evidence.json)
- `timestamp_ms` 是回放起点后的相对时间，缺帧与连接变化按预置序列单步产生。采集时钟 `capture_time`、真实链路延迟、实际吞吐、CPU 与内存、缓冲峰值和过载处置仍待实测。硬件回执的 `capture_time_and_latency`、`hardware_measurement` 和 `buffer_behavior` 为 `PENDING`。 [硬件待验证项](../after/hardware/hardware-evidence.json)
- 原生 TaskCarry MCP 接入仍为既有待验收事项。本次核对依据专业回执中的 `observed` 数据、共用协议和输入摘要。
