<!-- headroom-setup: begin -->
## Headroom 上下文压缩

本项目已配置 [Headroom](https://github.com/headroomlabs-ai/headroom)
作为 CodeWhale MCP 工具。以下工具自动可用：

- `mcp_headroom_compress` — 压缩大型工具输出、日志、搜索结果等，
  可在处理大量数据前调用以减少 token 消耗。
- `mcp_headroom_retrieve` — 通过 hash 检索之前压缩的原始内容。
- `mcp_headroom_stats` — 查看当前会话的压缩统计。

> **建议**：当工具返回超过 ~2000 tokens 的输出时，优先调用
> `mcp_headroom_compress` 压缩后再进行分析。压缩后的内容可保留关键
> 信息，同时大幅降低上下文占用。
<!-- headroom-setup: end -->

