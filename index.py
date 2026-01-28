import os
import pandas as pd
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从 utils/data_tools 导入
from utils.data_tools import load_concept_map, generate_report
from strategies import ma5_support 

DATA_DIR = "./stock_data"

def process_file(file_name, concept_map, analyze_func):
    """
    单个文件处理函数，包含概念映射
    """
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, file_name))
        if df.empty or len(df) < 5: return None
        
        stage = analyze_func(df) 
        
        if stage:
            full_code = file_name.replace(".csv", "")
            # 处理代码格式，支持 sh.600000 或 600000
            pure_code = full_code.split(".")[1] if "." in full_code else full_code
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            pct = round((curr['close'] - prev['close']) / prev['close'] * 100, 2)
            
            return {
                '代码': pure_code, 
                '完整代码': full_code, 
                '现价': curr['close'],
                '涨跌幅': f"{pct}%", 
                '阶段': stage,
                '概念': concept_map.get(pure_code, "未分类")
            }
    except Exception:
        return None

def run_scanner(strategy_name):
    strat_map = {
        'ma5': ma5_support.analyze,
    }
    
    analyze_func = strat_map.get(strategy_name)
    if not analyze_func:
        print(f"❌ 找不到策略: {strategy_name}")
        return

    print(f"⚡ 启动量价+题材扫描 | 策略: {strategy_name}")
    
    # 1. 获取概念地图，直接秒读本地磁盘
    concept_map = load_concept_map()
    
    # 2. 获取待扫描文件
    if not os.path.exists(DATA_DIR):
        print(f"❌ 数据目录 {DATA_DIR} 不存在")
        return
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    results = []
    # 3. 多线程扫描
    with ThreadPoolExecutor(max_workers=40) as executor:
        # 注意：这里把 concept_map 传进去了
        futures = [executor.submit(process_file, f, concept_map, analyze_func) for f in files]
        for f in tqdm(as_completed(futures), total=len(futures), desc="执行扫描"):
            res = f.result()
            if res: 
                results.append(res)

    # 4. 生成报告
    if results:
        generate_report(results, len(files))
    else:
        print("💡 扫描完成，未发现符合策略的标的。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--strat', type=str, default='ma5', help='选择策略')
    args = parser.parse_args()
    
    run_scanner(args.strat)