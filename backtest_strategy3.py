#!/usr/bin/env python3
"""
策略3回测脚本
回测2025年全年数据，统计"重中之重"信号出现后10日和20日的成功率
成功率定义：信号出现后N日内最高涨幅 > 5%
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.breakout_pullback import analyze
from tqdm import tqdm

DATA_DIR = "./stock_data"

def analyze_on_date(df, check_date_str):
    """
    在指定日期运行策略分析
    返回该日期的策略结果
    """
    # 找到指定日期的索引
    date_mask = df['date'] == check_date_str
    if not date_mask.any():
        return None
    
    date_idx = df[date_mask].index[0]
    
    # 截取到该日期的数据（包含历史数据）
    df_up_to_date = df.loc[:date_idx].copy()
    
    if len(df_up_to_date) < 60:
        return None
    
    # 运行策略分析
    result = analyze(df_up_to_date)
    return result

def check_future_return(df, signal_date_str, days=10, target_return=0.05):
    """
    检查信号出现后N日内的最高涨幅
    返回：(是否成功, 最高涨幅, 达到最高涨幅的日期)
    """
    # 找到信号日期的索引
    date_mask = df['date'] == signal_date_str
    if not date_mask.any():
        return False, 0, None
    
    signal_idx = df[date_mask].index[0]
    signal_close = df.loc[signal_idx, 'close']
    
    # 获取信号后N天的数据
    future_df = df.loc[signal_idx+1:signal_idx+days]
    
    if len(future_df) == 0:
        return False, 0, None
    
    # 计算最高涨幅
    max_price = future_df['high'].max()
    max_return = (max_price - signal_close) / signal_close
    max_return_pct = max_return * 100
    
    # 找到达到最高涨幅的日期
    max_idx = future_df['high'].idxmax()
    max_date = df.loc[max_idx, 'date']
    
    success = max_return >= target_return
    
    return success, max_return_pct, max_date

def run_backtest():
    """运行回测"""
    print("=" * 80)
    print("策略3回测 - 2025年全年数据")
    print("信号：🚀 启动期（重中之重）")
    print("成功率定义：信号出现后N日内最高涨幅 > 5%")
    print("=" * 80)
    print()
    
    # 获取所有股票文件
    stock_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    print(f"共加载 {len(stock_files)} 只股票")
    print()
    
    # 2025年交易日（简化处理，使用每月1日作为检查点）
    check_dates = []
    for month in range(1, 13):
        for day in [1, 5, 10, 15, 20, 25]:
            date_str = f"2025-{month:02d}-{day:02d}"
            check_dates.append(date_str)
    
    # 存储所有信号
    signals_10d = []  # 10日回测结果
    signals_20d = []  # 20日回测结果
    
    print("开始回测...")
    print()
    
    for stock_file in tqdm(stock_files, desc="回测进度"):
        code = stock_file.replace('.csv', '')
        file_path = os.path.join(DATA_DIR, stock_file)
        
        try:
            df = pd.read_csv(file_path)
            
            # 过滤2025年数据
            df_2025 = df[df['date'].str.startswith('2025')].copy()
            
            if len(df_2025) < 60:
                continue
            
            # 在每个检查日期运行策略
            for check_date in check_dates:
                # 检查该日期是否有数据
                if check_date not in df_2025['date'].values:
                    continue
                
                # 获取该日期之前的数据
                df_up_to_date = df[df['date'] <= check_date].copy()
                
                if len(df_up_to_date) < 60:
                    continue
                
                # 运行策略
                result = analyze(df_up_to_date)
                
                # 只记录"重中之重"信号
                if result == "🚀 启动期（重中之重）":
                    # 检查10日收益
                    success_10d, return_10d, max_date_10d = check_future_return(df, check_date, days=10, target_return=0.05)
                    
                    # 检查20日收益
                    success_20d, return_20d, max_date_20d = check_future_return(df, check_date, days=20, target_return=0.05)
                    
                    signal_info = {
                        'code': code,
                        'date': check_date,
                        'close': df_up_to_date.iloc[-1]['close'],
                    }
                    
                    signals_10d.append({
                        **signal_info,
                        'success': success_10d,
                        'max_return': return_10d,
                        'max_date': max_date_10d
                    })
                    
                    signals_20d.append({
                        **signal_info,
                        'success': success_20d,
                        'max_return': return_20d,
                        'max_date': max_date_20d
                    })
                    
        except Exception as e:
            continue
    
    print()
    print("=" * 80)
    print("回测结果")
    print("=" * 80)
    print()
    
    # 统计10日结果
    if signals_10d:
        total_10d = len(signals_10d)
        success_10d = sum(1 for s in signals_10d if s['success'])
        success_rate_10d = success_10d / total_10d * 100
        avg_return_10d = sum(s['max_return'] for s in signals_10d) / total_10d
        
        print("【10日回测结果】")
        print(f"  总信号数: {total_10d}")
        print(f"  成功次数: {success_10d}")
        print(f"  成功率: {success_rate_10d:.2f}%")
        print(f"  平均最高涨幅: {avg_return_10d:.2f}%")
        print()
        
        # 显示前10个成功信号
        print("  成功信号示例（前10个）:")
        success_signals = [s for s in signals_10d if s['success']][:10]
        for s in success_signals:
            print(f"    {s['code']} - 信号日期: {s['date']}, 最高涨幅: {s['max_return']:.2f}%")
        print()
    else:
        print("【10日回测结果】无信号")
        print()
    
    # 统计20日结果
    if signals_20d:
        total_20d = len(signals_20d)
        success_20d = sum(1 for s in signals_20d if s['success'])
        success_rate_20d = success_20d / total_20d * 100
        avg_return_20d = sum(s['max_return'] for s in signals_20d) / total_20d
        
        print("【20日回测结果】")
        print(f"  总信号数: {total_20d}")
        print(f"  成功次数: {success_20d}")
        print(f"  成功率: {success_rate_20d:.2f}%")
        print(f"  平均最高涨幅: {avg_return_20d:.2f}%")
        print()
        
        # 显示前10个成功信号
        print("  成功信号示例（前10个）:")
        success_signals = [s for s in signals_20d if s['success']][:10]
        for s in success_signals:
            print(f"    {s['code']} - 信号日期: {s['date']}, 最高涨幅: {s['max_return']:.2f}%")
        print()
    else:
        print("【20日回测结果】无信号")
        print()
    
    # 保存详细结果到CSV
    if signals_10d:
        df_10d = pd.DataFrame(signals_10d)
        df_10d.to_csv('backtest_result_10d.csv', index=False, encoding='utf-8-sig')
        print("详细结果已保存: backtest_result_10d.csv")
    
    if signals_20d:
        df_20d = pd.DataFrame(signals_20d)
        df_20d.to_csv('backtest_result_20d.csv', index=False, encoding='utf-8-sig')
        print("详细结果已保存: backtest_result_20d.csv")

if __name__ == "__main__":
    run_backtest()
