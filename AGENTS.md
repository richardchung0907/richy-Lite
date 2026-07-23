<!-- headroom-setup: begin -->
## Headroom 上下文压缩

本项目已配置 [Headroom](https://github.com/headroomlabs-ai/headroom)
作为 MCP 工具。以下工具自动可用：

- `mcp_headroom_compress` — 压缩大型工具输出、日志、搜索结果等，
  可在处理大量数据前调用以减少 token 消耗。
- `mcp_headroom_retrieve` — 通过 hash 检索之前压缩的原始内容。
- `mcp_headroom_stats` — 查看当前会话的压缩统计。

> **建议**：当工具返回超过 ~2000 tokens 的输出时，优先调用
> `mcp_headroom_compress` 压缩后再进行分析。压缩后的内容可保留关键
> 信息，同时大幅降低上下文占用。
> 查看mcp.json
<!-- headroom-setup: end -->

## 🛠️ 開發與自動化指令腳本規範 (Development & Automation Scripts)

本項目在 [scripts/](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts) 子目錄下為 AI Agents 及開發者準備了完整的自動化工具鏈。**任何接手的 AI Agent 在編寫新腳本或執行建置、運行、除錯任務前，必須先閱讀 [scripts/README.md](file:///c:/Users/User/Desktop/MYproject/Filter_APP2/scripts/README.md) 並檢查是否有現成的合用工具，嚴禁重複發明輪子！**

### 📦 現有自動化腳本清單：
- **`run_app.py`** — 用於本地模擬器引導、埠衝突解決、啟動 `flutter run` 熱重載。
- **`deploy_apk.py`** — 專用於本地 Release APK 的 WMI 獨立進程掛載與 Android 8.0/9.0 模擬器安裝。
- **`github_build_handler.py`** — 遠端 Actions 觸發、自動進度輪詢及 APK 下載整合腳本。
- **`setup_github_secrets.py`** — 自動進行 GitHub 密鑰、密碼及 keystore 加密並上傳到 Actions。
- **`appstore_connect_audit.py`** — 經由 JWT ES256 驗證深入檢測 App Store Connect 元數據、多語言、分類及 TestFlight 狀態。
- **`appstore_connect_enhance.py`** — 自動進行 App Store Connect REST API 設定優化（如 6.5" 螢幕尺寸配置及建置版本關聯）。
- **`process_screenshots.py`** — 使用 Pillow LANCZOS 演算法處理原始圖片至 6.5" 標準尺寸 (1242x2688) 避免失真。
- **`upload_screenshots_appstore.py`** — 將 6.5" 截圖經由 REST API 上傳至 10 大語言分區。
- **`verify_appstore_state.py`** — 即時查詢 App Store Connect 後台關聯版本與截圖狀態。
- **`build_android.py`** — Android 建置與靜態分析主工具。
- **`build_ios.py`** — iOS 建置引導與 EAS 雲端建置配置工具。
- **`setup_and_build.py`** — 全自動環境初始化、Flutter 安裝與建置主指令。

**規範：**
1. 欲執行某項任務時，必須優先調用上述現成指令（如建置呼叫 `build_android.py`，部署呼叫 `deploy_apk.py`，觸發遠端 Actions 呼叫 `github_build_handler.py`）。
2. 如確實需要新增腳本，必須將其歸類至 `scripts/` 目錄中，並同步更新 `scripts/README.md` 與本文件的腳本清單。


