# RC8 室内固定障碍仿真原型

> 本页依据固定技术快照：九项独立浏览器检查、工程文件检查及公开副本三场景复演均通过。表述登记记录技术支持与公开文件引用；精确公开对象的验收由另行出具的独立公开内容复核回执决定，该回执单向引用本页与登记，不在这里重复可变审核状态。

RC8 v2 在桌面 Chrome 中演示室内固定障碍的二维合成仿真。本地打开包内的 [`app/index.html`](../app/index.html)，可以在空房间到达、固定障碍绕行、缺帧等待与恢复三个场景间切换。页面同时呈现局部模拟相机、检测框、地图路线和逐拍记录。（`PRODUCT-REPLAY-OFFLINE`）

「局部相机」显示 160 × 120 的合成像素。空房间的首帧显示「有效空帧」。固定障碍场景首帧可见墙面、立柱和前方箱体的检测框，仿真位置先向东移动一格，沿地图路线到达目标。（`PRODUCT-REPLAY-CLEAR`、`PRODUCT-REPLAY-DETOUR`）

在缺帧场景，连续两拍没有新画面，位置保持。第二次缺帧显示「模拟断流」，收到下一帧后恢复连接并显示新检测。运行中可以暂停、继续或重置，完成后可以导出逐拍 JSON 日志。（`PRODUCT-REPLAY-DROP`、`PRODUCT-REPLAY-CONTROLS`、`PRODUCT-REPLAY-EXPORT`）

工程资料提供模块、接口时序、接线规划和预算，详见 [硬件工程说明](../hardware/HARDWARE_ENGINEERING.md)、[接口接线方案](../hardware/INTERFACE_WIRING_PLAN.md) 和 [资源预算](../hardware/RESOURCE_BUDGET.csv)。单帧 76,800 B、名义原始帧负载 768,000 B/s、双帧像素占用 153,600 B 是按合成帧规格和缓冲假设推算的。台架选型及物理测量待办。（`hardware-evidence.json` 的文档自查 `ENG-DOCS`）

[本地复演记录](product-replay-evidence.json) · [表述与独立检查登记](product-claims.json)
