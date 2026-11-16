# RC8 v2 演示路线

> 本页依据固定技术快照：九项独立浏览器检查、工程文件检查及公开副本三场景复演均通过。表述登记记录技术支持与公开文件引用；精确公开对象的验收由另行出具的独立公开内容复核回执决定，该回执单向引用本页与登记，不在这里重复可变审核状态。

开场说明，本次演示使用生成的相机像素、规则检测和软件中的网格运动。逐拍记录中的相邻时标相差 100 ms，这是仿真逻辑时间。（`PRODUCT-REPLAY-EXPORT`）

## 打开并切换任务

保留 `app/` 目录结构，在桌面 Chrome 本地打开 [`app/index.html`](../app/index.html)。从「场景／任务」选择一项，点「重置」，确认页首显示「就绪」「等待帧」、路线停在 `(4,6)`、逐拍记录为空，再点「开始」。每次切换后按同一顺序启动。（`PRODUCT-REPLAY-OFFLINE`、`PRODUCT-REPLAY-CONTROLS`）

| 场景 | 现场观察 | 本地复演检查 |
| --- | --- | --- |
| 空房间到达 `clear-room` | 首帧显示「有效空帧」，逐拍记录为 `ok · 0`。路线连续四步向北，拍 3 到达 `(4,2)`。 | `PRODUCT-REPLAY-CLEAR` |
| 固定障碍绕行 `fixed-obstacle` | 首帧出现墙面、立柱和箱体框，箱体标为相对格 `(0,-1)`。逐拍记录首条命令是 `MOVE_E`，路线向东绕行并在拍 5 到达。 | `PRODUCT-REPLAY-DETOUR` |
| 缺帧等待与恢复 `drop-and-recover` | 在逐拍记录回看拍 1、2，均为 `HOLD`，位置保持。拍 2 显示「模拟断流」，拍 3 以有效帧 `drop-and-recover:3` 恢复。拍 7 到达。 | `PRODUCT-REPLAY-DROP` |

## 暂停、复查与导出

在空房间场景启动后点「暂停」，让观众读当前画面、拍号和日志。点「继续」时查看下一逻辑拍。每种场景完成后点「导出 JSON」，再点「重置」。打开下载文件核对场景、路线、帧摘要、检测、链路、命令和终态。（`PRODUCT-REPLAY-CONTROLS`、`PRODUCT-REPLAY-EXPORT`）

像素 A/B、碰撞探针和超时探针分别由独立 `SIM-PIXELS`、`SIM-COLLISION`、`SIM-TIMEOUT` 的通过记录支持，具体输入、观察和范围见表述登记。

[本地复演记录](product-replay-evidence.json) · [表述与独立检查登记](product-claims.json)
