#!/usr/bin/env python3
"""
测试 MCP Server 的工具调用
"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入测试
from index import analyze_single_stock
from utils.data_tools import load_concept_map

def test_analyze_single_stock():
    """测试单只股票分析"""
    print("=" * 50)
    print("测试: analyze_single_stock")
    print("=" * 50)
    
    # 测试茅台
    result = analyze_single_stock("600519")
    print(f"\n股票: 600519 (茅台)")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试平安银行
    result = analyze_single_stock("000001")
    print(f"\n股票: 000001 (平安银行)")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试不存在的股票
    result = analyze_single_stock("999999")
    print(f"\n股票: 999999 (不存在)")
    print(json.dumps(result, ensure_ascii=False, indent=2))

def test_get_data_status():
    """测试数据状态"""
    print("\n" + "=" * 50)
    print("测试: get_data_status")
    print("=" * 50)
    
    DATA_DIR = "./stock_data"
    CONCEPT_CACHE = "concept_cache.json"
    
    # 检查股票数据
    stock_count = 0
    last_update = None
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
        stock_count = len(files)
        if files:
            mtimes = [os.path.getmtime(os.path.join(DATA_DIR, f)) for f in files]
            from datetime import datetime
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
    
    result = {
        "stock_data_count": stock_count,
        "last_update": last_update or "未更新",
        "concept_cache_date": concept_cache_date or "未同步",
        "data_dir": os.path.abspath(DATA_DIR)
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

def test_get_concept_list():
    """测试概念列表"""
    print("\n" + "=" * 50)
    print("测试: get_concept_list")
    print("=" * 50)
    
    concept_map = load_concept_map()
    
    # 提取所有概念
    all_concepts = set()
    for concepts in concept_map.values():
        if isinstance(concepts, str):
            for c in concepts.split(" / "):
                all_concepts.add(c.strip())
    
    result = {
        "total_stocks": len(concept_map),
        "total_concepts": len(all_concepts),
        "sample_concepts": sorted(list(all_concepts))[:10]  # 只显示前10个
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

def test_get_stock_concept():
    """测试获取股票概念"""
    print("\n" + "=" * 50)
    print("测试: get_stock_concept")
    print("=" * 50)
    
    concept_map = load_concept_map()
    
    # 测试几只股票
    test_codes = ["600519", "000001", "300750"]
    for code in test_codes:
        concepts = concept_map.get(code, "未分类")
        print(f"\n股票 {code}: {concepts}")

if __name__ == "__main__":
    print("开始测试 MCP Server 功能...\n")
    
    try:
        test_get_data_status()
    except Exception as e:
        print(f"❌ get_data_status 测试失败: {e}")
    
    try:
        test_get_concept_list()
    except Exception as e:
        print(f"❌ get_concept_list 测试失败: {e}")
    
    try:
        test_get_stock_concept()
    except Exception as e:
        print(f"❌ get_stock_concept 测试失败: {e}")
    
    try:
        test_analyze_single_stock()
    except Exception as e:
        print(f"❌ analyze_single_stock 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
