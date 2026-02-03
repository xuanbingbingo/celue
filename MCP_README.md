# MCP Server - 股票策略扫描器

## 概述

将股票策略扫描项目封装为 MCP Server，支持通过 MCP 协议调用所有功能。

## 提供的 Tools

### 1. 扫描分析类

| Tool | 功能 | 对应原代码 |
|------|------|-----------|
| `run_scanner` | 执行完整扫描流程，生成HTML报告 | `index.run_scanner()` |
| `analyze_single_stock` | 分析单只股票 | `index.analyze_single_stock()` |

### 2. 数据管理类

| Tool | 功能 | 对应原代码 |
|------|------|-----------|
| `init_stock_data` | 初始化股票历史数据 | `initData.init_database()` |
| `update_stock_data` | 增量更新最新数据 | `appendData.update_stock_data()` |
| `sync_concepts` | 同步概念板块数据 | `data_tools.sync_concepts()` |

### 3. 查询类

| Tool | 功能 | 对应原代码 |
|------|------|-----------|
| `get_data_status` | 检查数据状态 | - |
| `get_concept_list` | 获取所有概念 | `data_tools.load_concept_map()` |
| `get_stock_concept` | 获取股票概念 | `data_tools.load_concept_map()` |

## 使用方法

### 方式一：在 Trae 中使用（stdio 模式）

1. 确保已安装依赖：
```bash
pip install mcp
```

2. 在 Trae 的 MCP 配置中添加：
```json
{
  "mcpServers": {
    "stock-scanner": {
      "command": "python3",
      "args": ["/Users/libin/Documents/trae_projects/celue/mcp_server.py"]
    }
  }
}
```

3. 重启 Trae 后，AI 助手会自动识别并使用这些 tools

### 方式二：直接运行测试

```bash
python3 mcp_server.py
```

### 方式三：HTTP/SSE 模式（供其他客户端使用）

修改 `mcp_server.py` 的 main 函数：
```python
# 改为 SSE 模式
from mcp.server.sse import SseServerTransport

app = Server("stock-scanner-mcp")
transport = SseServerTransport("/messages")

@app.connect_sse()
async def connect_sse(scope, receive, send):
    async with transport.connect_sse(scope, receive, send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
```

## Tool 调用示例

### 检查数据状态
```json
{
  "name": "get_data_status",
  "arguments": {}
}
```

### 分析单只股票
```json
{
  "name": "analyze_single_stock",
  "arguments": {
    "code": "600519",
    "strategy": "ma5"
  }
}
```

### 执行完整扫描

支持三种策略：
- `ma5` - MA5均线支撑策略
- `volume_breakout` - 放量突破策略（吸筹→启动）
- `breakout_pullback` - 突破回调策略（大红小绿吸筹+放量+三连阳后缩量大跌）

```json
{
  "name": "run_scanner",
  "arguments": {
    "strategy": "breakout_pullback",
    "auto_open": false
  }
}
```

### 更新数据
```json
{
  "name": "update_stock_data",
  "arguments": {}
}
```

## 文件说明

- `mcp_server.py` - MCP Server 主程序
- `mcp_config.json` - MCP 配置文件示例
- `MCP_README.md` - 本文档

## 注意事项

1. 确保 `stock_data/` 目录存在且有数据
2. 首次使用需要运行 `init_stock_data` 或 `sync_concepts`
3. 长时间运行的操作（如扫描、初始化）使用后台线程
