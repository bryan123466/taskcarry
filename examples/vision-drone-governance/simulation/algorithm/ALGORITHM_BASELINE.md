# 室内视觉避障仿真算法基线

版本 `rc8-drone-sim-v2`，工作台 `algorithm`，原任务 `drone-vision-events`。本轮实现室内固定障碍的合成像素检测与一格控制。

## 软件调用

把两份脚本与软件应用一同打包，以经典脚本加载。

```html
<script src="../app/detector.js"></script>
<script src="../app/controller.js"></script>
```

```javascript
const detection = globalThis.RC8DroneSimV2.detectFrame(frameEnvelope);
const command = globalThis.RC8DroneSimV2.chooseCommand({
  detection,
  link_state,
  pose,
  goal,
  visit_counts,
});
```

调用方在检测后依据当前拍更新链路，再把本拍状态传给控制器。访问计数用 81 项非负整数，按 `y * 9 + x` 排列。场景障碍表由仿真器用于渲染和动作后的碰撞判定。

| 已测脚本 | SHA-256 |
| --- | --- |
| `detector.js` | `3581c1f94f780315bc29f3af19462e994aa8571c32ec6550ab16ddec9e3770a7` |
| `controller.js` | `414b781b680a9ec2025f794eaa5eae9f2944f0b149a2bb130f8a40bae9a6d967` |

接口合同的原字节 SHA-256 为 `77fa7df9dc17bbc95e3a728dd45e68c420dfbabdf770c3ac5ff9c714be025130`。

## 合成基线适用范围

帧输入为北向局部视野的 160×120 RGBA8，逐行 640 字节，像素缓冲为 76,800 字节的 `Uint8ClampedArray`。按墙面、立柱和箱体的精确 RGBA 合成色读取同色 4 连通块，保留至少 16 像素的分量。框坐标归一化并使用半开边界，输出按 `y_min`、`x_min`、标签排序。

每个框由中心映射到 5×5 局部栅格中的一个占用格。投影在像素单位计算中心，再映射到格索引。控制器在 9×9 世界网格内筛出未被检测占用的正交邻格。有缩短曼哈顿距离的邻格时依次比较距离、到访计数和北东南西顺序。需要绕行时先比较到访计数，再比较距离和方向。到达目标或无安全邻格时保持。

| 检测状态 | 本拍检测与控制结果 |
| --- | --- |
| 有效空帧 | `ok`，保留帧 ID，候选为 `[]`。依据姿态和目标正常选动作。 |
| 缺帧 | `missing`，帧 ID 为 `null`，候选为 `[]`。命令为 `HOLD/frame_missing` 或 `HOLD/link_disconnected`。 |
| 非法帧 | `invalid`，帧 ID 为 `null`，候选为 `[]`，带错误说明。命令为 `HOLD/invalid_frame`。 |

该基线适用于合同的合成色、固定俯视画面和局部占用规则。逐拍动作与检测证据用于软件仿真及工程资料。

## 算法自测

使用 `v24.14.1` 的 `node:vm` 在同一上下文按经典脚本加载两份交付。运行 `verify-algorithm.cjs` 并传入原字节接口合同路径，可复现 5 项检查。实际命令、输入、预期、观察和退出码在 `algorithm-evidence.json`。

像素 A/B 使用同一 `clear-room:0` 帧元数据、链路、姿态、目标与访问计数。实际只修改半开矩形 `[66,94) × [26,46)` 中的 560 个像素和 1680 个 RGBA 字节。

| 帧 | FNV-1a | 原始 RGBA 的 SHA-256 | 实测检测与动作 |
| --- | --- | --- | --- |
| A | `2c6c1dc5` | `c0415e4bc24dcc109a973acd6952f4ef3fd7cb2334e60ea67d54cc6e8a0a45c8` | `ok + []`，`MOVE_N/toward_goal` |
| B | `a925d965` | `567bc05fd7edd767314abe5e581da0dbb8016826b7299ecdf76bb35b65681967` | `box`，前方格 `(dx=0, dy=-1)`，`MOVE_E/detour` |

B 的实测框为 `x_min=0.4125`，`y_min=0.21666666666666667`，`x_max=0.5875`，`y_max=0.38333333333333336`，分量为 560 像素。两种链路下的缺帧分别得到 `HOLD/frame_missing` 与 `HOLD/link_disconnected`。5 种坏帧均返回空检测及 `HOLD/invalid_frame`。

上述为算法交付时的自测说明。随后同一脚本已集成到 [app](../app/index.html)，独立运行结果见[测试报告](../testing/TEST_REPORT.md)。
