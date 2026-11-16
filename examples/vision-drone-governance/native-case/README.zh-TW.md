# 原對話如何共同形成一段能展示的產品

[English](README.md) · [简体中文：完整案例](README.zh-CN.md) · [返回實例](../README.zh-TW.md)

這裡是一次實際執行的**合成專案對話練習**之審閱導出。三個原視窗先形成軟體、演算法和硬體資料；治理讀取選定的歷史，保留原成果與未決項，再依操作者確認的室內離線里程碑整理共同協議。專業視窗沿原工作繼續推進。這些產物與上層 `initial/` 中預先編寫的教學種子不同。

下載完整產品後，開啟 [after/software/monitor.html](after/software/monitor.html)，選取同目錄的 [回放 JSON](after/software/rc8-indoor-replay-v1.json)，點「载入」「重置」，再點六次「单步」。GitHub 檔案頁顯示 HTML 原始碼；展示需從下載後的本機目錄開啟。

六拍依序呈現左側牆面、同一幀中的立柱與箱體、成功處理的空幀、等待新幀、連續兩拍缺幀造成的模擬斷流，以及下一幀抵達後的恢復。這是人工預置事件的回放，不是影像辨識或飛控執行。

| 階段 | 可複核資料 |
| --- | --- |
| 原本分散的成果 | [軟體簡報](before/software/SOFTWARE_BRIEF.md)、[演算法計畫](before/algorithm/ALGORITHM_PLAN.md)、[硬體概念](before/hardware/HARDWARE_CONCEPT.md)，12 份初版檔案完整保留。 |
| 接入時的理解 | [記憶快照](governance/INTAKE_MEMORY.md)保留當時的室內外未定及接口差異。 |
| 共同決定 | [回放協議](governance/SHARED_INTERFACE.md)明確室內離線目標、座標映射、類別、時間和缺幀行為。 |
| 原視窗接續成果 | [軟體頁面](after/software/monitor.html)、[演算法校驗器](after/algorithm/validate_replay.py)、[硬體復算](after/hardware/HARDWARE_REPLAY.md)使用同一輸入。 |
| 跨專業複核 | [治理技術複核](governance/TECHNICAL_REVIEW.md)對照實際回執及可支持的表述。 |
| 產品表達 | 新職責保留[建立時的工作說明](before/product/PRODUCT_DEMO_BRIEF.md)，在瀏覽器核對相同頁面與輸入，完成引用技術檢查的[產品介紹](after/product/PRODUCT_INTRO.md)、[展示路線](after/product/DEMO_ROUTE.md)及[使用說明](after/product/USER_GUIDE.md)。 |
| 最終專案複核 | [治理最終複核](governance/PROJECT_REVIEW.md)核對三份文稿與實際回放，保留下面說明的證據摘要缺口。 |

原演算法的 40 ms 樣例保留為歷史評估資料。共用回放採名義 15 fps，逐拍取整為 `0、67、133、200、267、333 ms`；候選分數由人工設定。真實採集時鐘、延遲、硬體資源、辨識表現和飛行仍待相應驗證。

在本目錄以 Python 3.11+ 執行，不需第三方套件或 TaskCarry 連線：

```text
python -I -B -X utf8 after/algorithm/validate_replay.py after/algorithm/rc8-indoor-replay-v1.json
python -I -B -X utf8 after/hardware/verify_hardware_replay.py
```

兩條指令只讀輸入並輸出技術結果，不建立治理、任務或排程。各回放副本保留原始位元組，SHA-256 為 `2c5e0a9157c0bc0ce7a2f4681f3faeb1e8693e19f144b72b0b066e1386198b17`。

[軟體](after/software/software-evidence.json)、[演算法](after/algorithm/algorithm-evidence.json)、[硬體](after/hardware/hardware-evidence.json)及[產品](after/product/product-evidence.json)報告均帶有 `export_metadata`，說明它們是脫敏導出，並非原始宿主回執。產品職責記錄了同一頁面與輸入的 11 項瀏覽器檢查通過，對公開技術報告和協議的引用摘要已重新計算。[case-manifest.json](case-manifest.json)列出檔案、摘要和轉換；原始映射、真實對話身分、本機路徑及宿主設定留在私有紀錄。

產品報告的演算法摘要只彙總 `checks`，漏列原演算法報告在 `pending_checks` 中保留的兩項：共用回放的參考框評估，以及真實辨識與飛行表現。[治理最終複核](governance/PROJECT_REVIEW.md)指出了這處遺漏。導出保留原紀錄並標示摘要缺口，不能用產品摘要中的空列表判斷這些評估已通過。

**這批材料尚未證明原生 MCP 接入與自然定時治理通過。** 實際技術產物與回放結果和宿主驗收分開列證。本次專用合成視窗各有已有目錄，不能當成同目錄多對話的原生驗收，也不要求使用者為每個對話建一個資料夾。實體無人機、模型、硬體整合、飛行和長期異地執行均不在本次證據範圍內。
