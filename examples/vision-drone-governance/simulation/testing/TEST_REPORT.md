> 本报告是公开产品内容修正前的独立技术快照，保留当时 PRODUCT-EVIDENCE 的待验状态。九项应用与工程文档检查不变；后续公开内容复核单独出具回执，不回写本技术快照的对象摘要。

# RC8 v2 独立验收报告

2026-11-16 21:45:58 至 21:46:12（UTC+8），本独立测试窗口以最终软件交付的精确副本复跑。九项应用用例通过，工程资料审阅通过。产品稿复演与独立技术证据已对齐，`PRODUCT-EVIDENCE` 待确切的脱敏发布包复演。

## 被测交付与环境

软件来源为交付轮次 `redacted-host-chat-or-turn`。按 `software-evidence.json` 的 `file_sha256` 逐项核对六个 `app/` 文件及一份原字节合同。算法源文件、交付脚本和软件集成记录三处摘要一致。复制应用、合同、运行说明、软件自测脚本与证据到独立目录，复跑后再次核对源文件和副本 SHA-256。[核对清单](../case-manifest.json) · [独立副本](../app/index.html)

| 文件 | SHA-256 |
| --- | --- |
| `INTERFACE_CONTRACT.json` | `77fa7df9dc17bbc95e3a728dd45e68c420dfbabdf770c3ac5ff9c714be025130` |
| `app/detector.js` | `3581c1f94f780315bc29f3af19462e994aa8571c32ec6550ab16ddec9e3770a7` |
| `app/controller.js` | `414b781b680a9ec2025f794eaa5eae9f2944f0b149a2bb130f8a40bae9a6d967` |

Windows x64，Node.js `24.14.1`。使用桌面 Chrome `155.0.8059.39` 的无头模式和独立浏览器配置，以 `file:` 打开副本。正常入口用实际页面控件完成操作和下载。逐拍探针通过同一应用的 `#test` 入口。完整页面记录包含 12 次本地资源读取，外部请求、资源失败和页面异常均为 0。[完整浏览器记录](recorded/browser-activity-complete.json)

## 技术结果

| 检查 | 结果 | 观察与证据 |
| --- | --- | --- |
| `SIM-OFFLINE` | PASS | 从页面菜单选择三个场景。启动后在拍 0 暂停，758 ms 后拍号、位置、日志与界面未变。继续进入拍 1，重置后回到 `(4,6)`、`ready/waiting` 和空日志。暂停截图（原运行二进制私有保留；可用脚本重现） |
| `SIM-CLEAR` | PASS | 首帧有效，结果为 `ok` 且检测为空，四拍均为 `MOVE_N`，拍 3 到达 `(4,2)`，零碰撞。[下载日志](recorded/round-1-clear-room/rc8-drone-sim-v2-clear-room.json) |
| `SIM-DETOUR` | PASS | 首帧的真实 RGBA 字节、画布与 FNV-1a 匹配，检出墙面、立柱和箱体。前方箱体占 `(dx=0,dy=-1)`，首拍 `MOVE_E`，拍 5 到达，轨迹与合同一致，零碰撞。首帧截图（原运行二进制私有保留；可用脚本重现） · [下载日志](recorded/round-1-fixed-obstacle/rc8-drone-sim-v2-fixed-obstacle.json) |
| `SIM-DROP` | PASS | 拍 1、2 的帧为 `null`，两拍均 `HOLD`，位置与访问计数保持。拍 2 断流，拍 3 使用新帧恢复，对同拍帧复算检测一致。拍 7 到达，零碰撞。[前四拍](recorded/drop-first-steps.json) · [下载日志](recorded/round-1-drop-and-recover/rc8-drone-sim-v2-drop-and-recover.json) |
| `SIM-PIXELS` | PASS | A、B 的帧号、时标、场景、链路、姿态、目标和访问计数完全相同。仅将前方格内缩矩形改为箱体色，改变 560 个像素、1,680 个真实 RGBA 字节。FNV-1a 从 `2c6c1dc5` 变为 `a925d965`，检测从空变为 `box`，命令从 `MOVE_N` 变为 `MOVE_E`。[实际输入和输出](recorded/pixel-ab.json) · A 原始字节（原运行二进制私有保留；可用脚本重现） · B 原始字节（原运行二进制私有保留；可用脚本重现） · B 截图（原运行二进制私有保留；可用脚本重现） |
| `SIM-COLLISION` | PASS | 按合同从固定障碍起点注入 `MOVE_N`。前后均为 `(4,6)`，进入 `collision`，界面显示「模拟碰撞」。等待 750 ms 后仍为一条记录，再推进返回 `null`。碰撞截图（原运行二进制私有保留；可用脚本重现） · [下载日志](recorded/collision-export/rc8-drone-sim-v2-fixed-obstacle.json) |
| `SIM-INVALID` | PASS | 分别给原检测入口传入坏宽度、坏长度及坏帧号，均返回 `invalid`、空检测和 `HOLD/invalid_frame`。逐拍注入坏长度后，位置保持，界面显示「输入帧无效」。坏帧截图（原运行二进制私有保留；可用脚本重现） · [脱敏结果](recorded/run-evidence.json) |
| `SIM-TIMEOUT` | PASS | 通过 `#test` 推进，在检测调用边界连续给原检测函数送入 12 个 `frame:null`。每拍判断为 `missing` 并由原控制逻辑给出 `HOLD`。末拍 11 进入 `timeout`，等待 750 ms 和再次推进后日志仍为 12 条。恢复检测入口，直接在同一仿真实例点击重置和开始，原场景于拍 3 到达。[实际注入](recorded/timeout-inputs.json) · 界面（原运行二进制私有保留；可用脚本重现） · [超时下载](recorded/timeout-export/rc8-drone-sim-v2-clear-room.json) · [重置后下载](recorded/timeout-reset-replay/rc8-drone-sim-v2-clear-room.json) |
| `SIM-EXPORT` | PASS | 三场景各从重置后运行两轮，点击「导出 JSON」得到六个实际下载。对应记录数为 4、6、8。每场景两轮文件字节一致，版本、时标、帧摘要、命令和轨迹均匹配。[下载清单与比对](recorded/browser-exports.json) |
| `ENG-DOCS` | PASS | 三份工程资料覆盖模块及数据方向、接口时序、概念接线、预算和后续测量。依合同复算 `160 × 120 × 4 = 76,800 B`，名义十拍每秒为 `768,000 B/s`，双帧为 `153,600 B`。电平、供电和性能的物理参数保留为台架待测项。[文档摘要和算术](test-evidence.json) |
| `PRODUCT-EVIDENCE` | PENDING | 三份内部产品稿已审阅。产品复演采用相同的合同及应用摘要，三场景终止拍和下载 SHA-256 均与独立测试一致。十二条拟用表述所需检查已有证据。待确切的脱敏发布包复演所附材料与链接。[逐条对应](test-evidence.json) |

## 原生连接单独留证

本公开报告保留应用与工程验证。原生 MCP 回执包含本机和聊天身份，私有保留；公开汇总由治理核对后另行提供。浏览器测试通过不等于已接入 MCP。

## 复现

运行以下命令会按交付清单复核输入，在测试目录下生成新副本及结果。机器可读总表提供每项的预期、实际输入、观察与复现步骤。[机器可读总表](test-evidence.json) · [本次实测脱敏结果](recorded/run-evidence.json)

```sh
node testing/prepare-public-handoff.mjs
```
