import os
import pandas as pd
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从 utils/data_tools 导入
from utils.data_tools import load_concept_map, load_stock_name_map, generate_report
from strategies import ma5_support, volume_breakout, breakout_pullback

DATA_DIR = "./stock_data"

# 策略映射表
STRATEGY_MAP = {
    'ma5': {
        'name': 'ma5',
        'func': ma5_support.analyze,
        'description': 'MA5均线支撑策略'
    },
    'volume_breakout': {
        'name': 'volume_breakout',
        'func': volume_breakout.analyze,
        'description': '放量突破策略（吸筹→启动，无整理期）'
    },
    'breakout_pullback': {
        'name': 'breakout_pullback',
        'func': breakout_pullback.analyze,
        'description': '突破回调策略（大红小绿吸筹+放量+三连阳后缩量大跌）'
    }
}

def analyze_single_stock(code: str, strategy: str = "ma5"):
    """
    分析单只股票
    code: "600519" 或 "sh.600519" 或 "sz.000001"
    strategy: 策略名称，默认 "ma5"
    返回: dict 包含分析结果，如果股票不存在或数据不足返回 None
    """
    # 1. 加载策略
    strategy_config = STRATEGY_MAP.get(strategy)
    if not strategy_config:
        return {"error": f"找不到策略: {strategy}"}
    analyze_func = strategy_config['func']
    
    # 2. 处理代码格式
    if '.' in code:
        # 已经是 sh.600519 格式
        full_code = code
        pure_code = code.split('.')[1]
    else:
        # 纯数字代码，需要判断 sh 还是 sz
        pure_code = code
        if code.startswith('6'):
            full_code = f"sh.{code}"
        elif code.startswith('0') or code.startswith('3'):
            full_code = f"sz.{code}"
        elif code.startswith('8') or code.startswith('4') or code.startswith('92'):
            full_code = f"bj.{code}"
        else:
            return {"error": f"无法识别股票代码: {code}"}
    
    # 3. 加载股票数据
    file_path = os.path.join(DATA_DIR, f"{full_code}.csv")
    if not os.path.exists(file_path):
        return {"error": f"股票数据不存在: {code}"}
    
    try:
        df = pd.read_csv(file_path)
        if df.empty or len(df) < 60:
            return {"error": f"股票数据不足: {code}"}
        
        # 4. 分析
        stage = analyze_func(df)
        
        # 5. 计算额外指标
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA30'] = df['close'].rolling(30).mean()
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        pct = round((curr['close'] - prev['close']) / prev['close'] * 100, 2)
        
        # 6. 加载概念
        concept_map = load_concept_map()
        concepts = concept_map.get(pure_code, "未分类")
        
        return {
            "代码": pure_code,
            "完整代码": full_code,
            "现价": float(curr['close']),
            "涨跌幅": f"{pct}%",
            "阶段": stage,
            "概念": concepts,
            "MA5": round(float(curr['MA5']), 2) if not pd.isna(curr['MA5']) else None,
            "MA30": round(float(curr['MA30']), 2) if not pd.isna(curr['MA30']) else None,
            "成交量": int(curr['volume']),
            "数据日期": str(curr['date'])
        }
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

def process_file(file_name, concept_map, stock_name_map, analyze_func):
    """
    单个文件处理函数，包含概念映射和股票名称
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
                '名称': stock_name_map.get(pure_code, ''),
                '完整代码': full_code, 
                '现价': curr['close'],
                '涨跌幅': f"{pct}%", 
                '阶段': stage,
                '概念': concept_map.get(pure_code, "未分类")
            }
    except Exception:
        return None

def run_scanner(strategy_name):
    strategy_config = STRATEGY_MAP.get(strategy_name)
    if not strategy_config:
        print(f"❌ 找不到策略: {strategy_name}")
        return
    
    analyze_func = strategy_config['func']
    strategy_desc = strategy_config['description']

    print(f"⚡ 启动量价+题材扫描 | 策略: {strategy_name} ({strategy_desc})")
    
    # 1. 获取概念地图和股票名称映射，直接秒读本地磁盘
    concept_map = load_concept_map()
    stock_name_map = load_stock_name_map()
    
    # 2. 获取待扫描文件
    if not os.path.exists(DATA_DIR):
        print(f"❌ 数据目录 {DATA_DIR} 不存在")
        return
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    results = []
    # 3. 多线程扫描
    with ThreadPoolExecutor(max_workers=40) as executor:
        # 注意：这里把 concept_map 和 stock_name_map 传进去了
        futures = [executor.submit(process_file, f, concept_map, stock_name_map, analyze_func) for f in files]
        for f in tqdm(as_completed(futures), total=len(futures), desc="执行扫描"):
            res = f.result()
            if res: 
                results.append(res)

    # 4. 生成报告（传入策略名用于文件名区分）
    if results:
        generate_report(results, len(files), strategy_name)
    else:
        print("💡 扫描完成，未发现符合策略的标的。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--strat', type=str, default='ma5', help='选择策略')
    args = parser.parse_args()
    
    run_scanner(args.strat)