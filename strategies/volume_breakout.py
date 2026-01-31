import pandas as pd
import numpy as np

def analyze(df):
    """
    策略版本：V1 (放量突破版)
    核心逻辑：吸筹期 → 启动期（无整理期）
    
    特殊标记：启动期（重点）
    条件：某日股价最低点低于前一天最低价且前一天股价上涨
    """
    if df is None or len(df) < 60: 
        return None 
    
    df = df.copy()
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 指标计算
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA30'] = df['close'].rolling(30).mean()
    df['pct_chg'] = df['close'].pct_change() * 100
    
    # 时间切片
    acc_period = df.iloc[-60:-20]   # 吸筹期：60-20日前
    shake_period = df.iloc[-20:-5]  # 观察期：20-5日前
    recent_period = df.iloc[-10:]   # 近期：10日内
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # 1. 吸筹判定（60-20日前）
    red_vol = acc_period[acc_period['close'] > acc_period['open']]['volume'].sum()
    green_vol = acc_period[acc_period['close'] <= acc_period['open']]['volume'].sum()
    is_accumulating = (red_vol > green_vol * 1.5)
    
    if not is_accumulating:
        return None
    
    # 2. 检测特殊形态：启动期（重点）
    # 条件：某日最低点 < 前一天最低点 且 前一天股价上涨
    is_key_breakout = False
    breakout_date = None
    
    for i in range(-30, -1):  # 检查最近30天（不包括今天）
        if i < -len(df) + 1:
            continue
            
        today_low = df.iloc[i]['low']
        prev_day = df.iloc[i-1]
        prev_low = prev_day['low']
        prev_change = (prev_day['close'] - prev_day['open']) / prev_day['open'] * 100
        
        # 条件：今天最低 < 昨天最低 且 昨天上涨
        if today_low < prev_low and prev_change > 0:
            is_key_breakout = True
            breakout_date = df.iloc[i]['date']
            break
    
    # 3. 启动特征（10日内）
    has_breakout = len(recent_period[recent_period['pct_chg'] >= 4.0]) >= 1
    is_shrinking = curr['volume'] < prev['volume']
    ma5_trending_up = curr['MA5'] > prev['MA5']
    on_ma5 = (curr['close'] >= curr['MA5']) and (curr['low'] <= curr['MA5'] * 1.015)
    
    is_pullback = is_shrinking and on_ma5 and ma5_trending_up
    
    # 4. 结果输出
    if has_breakout and is_pullback:
        if is_key_breakout:
            return "🚀 启动期（重点）"  # 特殊标记
        else:
            return "🚀 启动期"
    elif has_breakout:
        return "🧪 蓄势中"
    
    return None
