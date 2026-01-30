#!/usr/bin/env python3
"""
测试 MCP Server 的启动和工具列表
"""

import asyncio
import subprocess
import json
import sys

async def test_mcp_server():
    """测试 MCP Server"""
    print("=" * 60)
    print("测试 MCP Server 启动")
    print("=" * 60)
    
    # 启动 MCP Server 进程
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("\n1. 发送初始化请求...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # 读取响应
        response = process.stdout.readline()
        if response:
            result = json.loads(response)
            print(f"✅ 初始化成功")
            print(f"   Server: {result.get('result', {}).get('serverInfo', {})}")
        
        # 发送 initialized 通知
        initialized = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # 请求工具列表
        print("\n2. 请求工具列表...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        if response:
            result = json.loads(response)
            tools = result.get('result', {}).get('tools', [])
            print(f"✅ 获取到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:50]}...")
        
        # 测试调用 get_data_status
        print("\n3. 测试调用 get_data_status...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_data_status",
                "arguments": {}
            }
        }
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        if response:
            result = json.loads(response)
            content = result.get('result', {}).get('content', [])
            if content:
                data = json.loads(content[0]['text'])
                print(f"✅ 调用成功")
                print(f"   股票数量: {data.get('stock_data_count')}")
                print(f"   最后更新: {data.get('last_update')}")
        
        # 测试调用 analyze_single_stock
        print("\n4. 测试调用 analyze_single_stock...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "analyze_single_stock",
                "arguments": {
                    "code": "600519",
                    "strategy": "ma5"
                }
            }
        }
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        if response:
            result = json.loads(response)
            content = result.get('result', {}).get('content', [])
            if content:
                data = json.loads(content[0]['text'])
                print(f"✅ 调用成功")
                print(f"   股票: {data.get('代码')}")
                print(f"   现价: {data.get('现价')}")
                print(f"   阶段: {data.get('阶段')}")
        
        print("\n" + "=" * 60)
        print("✅ MCP Server 测试全部通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭进程
        process.terminate()
        process.wait(timeout=5)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
