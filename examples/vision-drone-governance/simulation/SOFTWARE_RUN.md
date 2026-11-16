# RC8 室内视觉避障仿真运行手册

交付版本为 `rc8-drone-sim-v2`。将本目录复制到独立位置后，用桌面 Chrome 从文件系统打开应用入口。正常操作所需的 HTML、样式和经典脚本均随 `app/` 携带。 [应用入口](app/index.html)

1. 在「场景／任务」选择空房间到达、固定障碍绕行或缺帧等待与恢复。
2. 点击「开始」。运行中可「暂停」，观察当前帧和逐拍记录，再点「继续」。选择其他场景或点击「重置」会回到所选场景的起点、等待帧状态和空日志。
3. 点击「导出 JSON」，得到以版本和场景 ID 命名的下载文件。文件包含起点、目标、成功移动组成的路线，以及每一拍的时标、帧标识、像素摘要、检测、链路、命令和动作前后位置。

## 执行与数据

仿真器按动作前位置在独立 Canvas 上绘制 160×120 的北向局部帧，再通过 `getImageData` 读取 76,800 字节的 RGBA8 像素。绘制使用合同中的格宽、内缩量和颜色。检测器接收帧包，控制器接收检测、更新后的链路状态、位置、目标和访问次数。仿真器收到命令后才用场景真值判定移动、到达和碰撞。界面的叠框使用单独画布。

逻辑拍从 0 起，`sim_time_ms = tick × 100`。画面播放的定时器在相邻拍之间等待 300 ms。暂停会取消下一次播放排程，恢复继续推进下一逻辑拍。有效帧的 `frame_digest` 记录检测输入的 FNV-1a 32-bit 摘要。缺帧和坏帧的摘要为 `null`。到达、碰撞或累计执行 12 拍即停止，拍数上限的末拍索引为 11。 [原字节接口合同](INTERFACE_CONTRACT.json)

## 本地 Chrome 自测

在隔离目录用 Chrome 155.0.8059.39 的无头模式打开 `file:` 入口。三个场景各从重置独立运行两次，同一场景两轮下载逐字节一致。拍 0 暂停实测 454 ms，拍号和日志数保持一致。监测期未捕获外部请求或页面异常。

| 场景 | 实际动作和终态 | 回执检查 |
| --- | --- | --- |
| `clear-room` | 首帧有效空帧，四次向北，拍 3 到达 `(4,2)` | `SIM-CLEAR` |
| `fixed-obstacle` | 首帧检出墙面、立柱、前方箱体，先向东绕行，拍 5 到达 `(4,2)` | `SIM-DETOUR` |
| `drop-and-recover` | 拍 1、2 保持原位和访问次数，拍 2 断流，拍 3 恢复，拍 7 到达 `(4,2)` | `SIM-DROP` |

三场景正常路径均为零碰撞。碰撞、无效帧、拍数上限和像素 A/B 另有隔离探针。回执包含两次下载的摘要、一份实际导出内容、逐项观察和复现方法。 [软件自测回执](software-evidence.json)

## 独立目录复验

在独立副本的包根目录运行 `node verify-software.mjs`。本次使用 Node 24 和本地 Chrome。可用 `RC8_CHROME_PATH` 指定本机 Chrome 可执行文件；未指定时按当前操作系统查找。脚本建立隔离副本，通过 Chrome 实际操作页面与下载，输出该副本的 `local/software-evidence.json`，保留原记录。 [浏览器自测脚本](verify-software.mjs)

需要单独检验时，在测试副本的新标签打开 `app/index.html#test`，在 DevTools 使用 `RC8DroneSimV2.testMonitor`。其 `step` 与界面播放调用同一个仿真器逻辑，`readFrame()` 提供最近一次检测输入的副本，`readState()` 提供当前状态和访问计数。

以下 A/B 两次均从 `clear-room` 的拍 0 开始。第二次只在前方格 `(col=2,row=1)` 的内缩矩形写入箱体色。

```js
{
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene("clear-room");
  const a = test.step();
  const frameA = test.readFrame();

  test.selectScene("clear-room");
  const b = test.step({
    replacePixels(bytes) {
      for (let y = 26; y < 46; y += 1) {
        for (let x = 66; x < 94; x += 1) {
          bytes.set([230, 180, 60, 255], (y * 160 + x) * 4);
        }
      }
      return bytes;
    }
  });
  const frameB = test.readFrame();
  console.log(a, b, frameA.frame.frame_id, frameB.frame.frame_id);
}
```

自测读回的两个摘要为 `2c6c1dc5` 和 `a925d965`。实测差异为矩形内的 560 个像素、1,680 个颜色字节。A 返回有效空检测和 `MOVE_N`，B 返回 `box`、相对格 `(0,-1)` 和 `MOVE_E`。回执还记录了两次调用的帧元数据、控制元数据及实际参数键。

碰撞可通过下列步骤检查。界面显示「模拟碰撞」，位置保持 `(4,6)`，下一次推进返回 `null`。

```js
{
  const test = RC8DroneSimV2.testMonitor;
  test.selectScene("fixed-obstacle");
  const hit = test.step({ commandOverride: { action: "MOVE_N", reason: "toward_goal" } });
  console.log(hit, test.step(), test.readState().records.length);
}
```

坏帧探针可先用 `RC8DroneSimV2.testMonitor.selectScene("clear-room")` 选择空房间，再调用同一入口的 `step({replacePixels: bytes => bytes.slice(0, 4)})`，观察 `invalid` 和 `HOLD / invalid_frame`。

## 包内版本与接续

| 文件 | SHA-256 |
| --- | --- |
| `INTERFACE_CONTRACT.json` | `77fa7df9dc17bbc95e3a728dd45e68c420dfbabdf770c3ac5ff9c714be025130` |
| `app/detector.js` | `3581c1f94f780315bc29f3af19462e994aa8571c32ec6550ab16ddec9e3770a7` |
| `app/controller.js` | `414b781b680a9ec2025f794eaa5eae9f2944f0b149a2bb130f8a40bae9a6d967` |

两份算法原文件、包内副本和浏览器实际装入的脚本文本摘要相符。其余应用文件摘要在回执的 `file_sha256`。软件侧停在交独立测试复验同一包及合同的阶段。

本软件自测完成后，独立测试继续复验同一应用。见[独立报告](testing/TEST_REPORT.md)。宿主 MCP 与工作台接入单独验收，不由浏览器自测替代。
