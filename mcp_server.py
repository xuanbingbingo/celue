#!/usr/bin/env python3
"""
MCP Server for Stock Strategy Scanner
提供股票策略扫描的 MCP 工具服务
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
import mcp.server.stdio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from index import run_scanner, analyze_single_stock
from initData import init_database
from appendData import update_stock_data
from utils.data_tools import load_concept_map, update_concept_cache

# 创建 MCP Server
app = Server("stock-scanner-mcp")

# ==================== Tools 定义 ====================

TOOLS = [
    Tool(
        name="run_scanner",
        description="执行完整的股票策略扫描流程：加载概念数据→扫描所有股票→生成HTML报告",
        inputSchema={
            "type": "object",
            "properties": {
                "strategy": {
                    "type": "string",
                    "enum": ["ma5"],
                    "default": "ma5",
                    "description": "扫描策略名称，目前支持 ma5 (MA5均线支撑策略)"
                },
                "auto_open": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否自动打开报告"
                }
            }
        }
    ),
    Tool(
        name="analyze_single_stock",
        description="分析单只股票的策略信号",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "股票代码，如 600519, sh.600519, sz.000001"
                },
                "strategy": {
                    "type": "string",
                    "enum": ["ma5"],
                    "default": "ma5",
                    "description": "分析策略"
                }
            },
            "required": ["code"]
        }
    ),
    Tool(
        name="init_stock_data",
        description="初始化股票历史数据，从 BaoStock 下载 2025-01-01 至今的数据",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="update_stock_data",
        description="增量更新股票数据，下载最新交易日的数据",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="sync_concepts",
        description="同步东方财富概念板块数据到本地缓存",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_concept_list",
        description="获取所有概念板块列表",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_data_status",
        description="检查本地数据状态：股票数据数量、最后更新日期、概念缓存日期",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="get_stock_concept",
        description="获取指定股票的概念板块",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "股票代码，如 600519"
                }
            },
            "required": ["code"]
        }
    )
]

# ==================== Tool 处理函数 ====================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """列出所有可用的 Tools"""
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
    """处理 Tool 调用"""
    arguments = arguments or {}
    
    try:
        if name == "run_scanner":
            return await handle_run_scanner(arguments)
        elif name == "analyze_single_stock":
            return await handle_analyze_single_stock(arguments)
        elif name == "init_stock_data":
            return await handle_init_stock_data(arguments)
        elif name == "update_stock_data":
            return await handle_update_stock_data(arguments)
        elif name == "sync_concepts":
            return await handle_sync_concepts(arguments)
        elif name == "get_concept_list":
            return await handle_get_concept_list(arguments)
        elif name == "get_data_status":
            return await handle_get_data_status(arguments)
        elif name == "get_stock_concept":
            return await handle_get_stock_concept(arguments)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

# ==================== 具体 Tool 实现 ====================

async def handle_run_scanner(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 run_scanner 工具调用"""
    strategy = arguments.get("strategy", "ma5")
    auto_open = arguments.get("auto_open", False)
    
    # 注意：run_scanner 是同步函数，使用线程池运行
    import threading
    result_container = {}
    
    def run_in_thread():
        try:
            # 捕获输出
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                run_scanner(strategy)
            
            output = f.getvalue()
            result_container["output"] = output
            result_container["success"] = True
        except Exception as e:
            result_container["error"] = str(e)
            result_container["success"] = False
    
    # 在后台线程运行
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=300)  # 最多等待5分钟
    
    if thread.is_alive():
        return [TextContent(type="text", text=json.dumps({
            "warning": "扫描超时，可能在后台继续运行"
        }, ensure_ascii=False))]
    
    if result_container.get("success"):
        # 检查报告文件
        report_path = "./scanner_report.html"
        if os.path.exists(report_path):
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "message": "扫描完成",
                "output": result_container.get("output", ""),
                "report_path": os.path.abspath(report_path),
                "report_exists": True
            }, ensure_ascii=False))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "message": "扫描完成，未发现符合条件的标的",
                "output": result_container.get("output", "")
            }, ensure_ascii=False))]
    else:
        return [TextContent(type="text", text=json.dumps({
            "error": result_container.get("error", "未知错误")
        }, ensure_ascii=False))]

async def handle_analyze_single_stock(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 analyze_single_stock 工具调用"""
    code = arguments.get("code")
    strategy = arguments.get("strategy", "ma5")
    
    if not code:
        return [TextContent(type="text", text=json.dumps({
            "error": "缺少参数: code"
        }, ensure_ascii=False))]
    
    result = analyze_single_stock(code, strategy)
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_init_stock_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 init_stock_data 工具调用"""
    import threading
    result_container = {}
    
    def run_in_thread():
        try:
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                init_database()
            
            result_container["output"] = f.getvalue()
            result_container["success"] = True
        except Exception as e:
            result_container["error"] = str(e)
            result_container["success"] = False
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=600)  # 最多等待10分钟
    
    if thread.is_alive():
        return [TextContent(type="text", text=json.dumps({
            "warning": "初始化超时，可能在后台继续运行"
        }, ensure_ascii=False))]
    
    return [TextContent(type="text", text=json.dumps({
        "success": result_container.get("success", False),
        "output": result_container.get("output", ""),
        "error": result_container.get("error")
    }, ensure_ascii=False))]

async def handle_update_stock_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 update_stock_data 工具调用"""
    import threading
    result_container = {}
    
    def run_in_thread():
        try:
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                update_stock_data()
            
            result_container["output"] = f.getvalue()
            result_container["success"] = True
        except Exception as e:
            result_container["error"] = str(e)
            result_container["success"] = False
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=300)  # 最多等待5分钟
    
    if thread.is_alive():
        return [TextContent(type="text", text=json.dumps({
            "warning": "更新超时，可能在后台继续运行"
        }, ensure_ascii=False))]
    
    return [TextContent(type="text", text=json.dumps({
        "success": result_container.get("success", False),
        "output": result_container.get("output", ""),
        "error": result_container.get("error")
    }, ensure_ascii=False))]

async def handle_sync_concepts(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 sync_concepts 工具调用"""
    import threading
    result_container = {}
    
    def run_in_thread():
        try:
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                update_concept_cache()
            
            result_container["output"] = f.getvalue()
            result_container["success"] = True
        except Exception as e:
            result_container["error"] = str(e)
            result_container["success"] = False
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=600)  # 最多等待10分钟
    
    if thread.is_alive():
        return [TextContent(type="text", text=json.dumps({
            "warning": "同步超时，可能在后台继续运行"
        }, ensure_ascii=False))]
    
    return [TextContent(type="text", text=json.dumps({
        "success": result_container.get("success", False),
        "output": result_container.get("output", ""),
        "error": result_container.get("error")
    }, ensure_ascii=False))]

async def handle_get_concept_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 get_concept_list 工具调用"""
    concept_map = load_concept_map()
    
    # 提取所有概念
    all_concepts = set()
    for concepts in concept_map.values():
        if isinstance(concepts, str):
            for c in concepts.split(" / "):
                all_concepts.add(c.strip())
    
    return [TextContent(type="text", text=json.dumps({
        "total_stocks": len(concept_map),
        "total_concepts": len(all_concepts),
        "concepts": sorted(list(all_concepts))
    }, ensure_ascii=False, indent=2))]

async def handle_get_data_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 get_data_status 工具调用"""
    DATA_DIR = "./stock_data"
    CONCEPT_CACHE = "concept_cache.json"
    
    # 检查股票数据
    stock_count = 0
    last_update = None
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
        stock_count = len(files)
        
        # 获取最新修改时间
        if files:
            mtimes = [os.path.getmtime(os.path.join(DATA_DIR, f)) for f in files]
            last_update = datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d %H:%M")
    
    # 检查概念缓存
    concept_cache_date = None
    if os.path.exists(CONCEPT_CACHE):
        try:
            with open(CONCEPT_CACHE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                concept_cache_date = cache_data.get('date')
        except:
            pass
    
    # 判断是否需要更新
    needs_update = False
    if not last_update:
        needs_update = True
    else:
        last_date = datetime.strptime(last_update.split()[0], "%Y-%m-%d")
        if (datetime.now() - last_date).days >= 1:
            needs_update = True
    
    return [TextContent(type="text", text=json.dumps({
        "stock_data_count": stock_count,
        "last_update": last_update or "未更新",
        "concept_cache_date": concept_cache_date or "未同步",
        "needs_update": needs_update,
        "data_dir": os.path.abspath(DATA_DIR)
    }, ensure_ascii=False, indent=2))]

async def handle_get_stock_concept(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理 get_stock_concept 工具调用"""
    code = arguments.get("code")
    
    if not code:
        return [TextContent(type="text", text=json.dumps({
            "error": "缺少参数: code"
        }, ensure_ascii=False))]
    
    # 提取纯数字代码
    if '.' in code:
        pure_code = code.split('.')[1]
    else:
        pure_code = code
    
    concept_map = load_concept_map()
    concepts = concept_map.get(pure_code, "未分类")
    
    return [TextContent(type="text", text=json.dumps({
        "code": pure_code,
        "concepts": concepts
    }, ensure_ascii=False, indent=2))]

# ==================== 主入口 ====================

async def main():
    """启动 MCP Server"""
    # 使用 stdio 传输
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
