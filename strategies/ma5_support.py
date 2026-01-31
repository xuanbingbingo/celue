import pandas as pd
import numpy as np

def analyze(df):
    """
    策略版本：V1 (中线版)
    核心逻辑：吸筹判定 -> 20日内出现缩量挖坑(诱空) -> 缩量回踩MA5(确认启动)
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
    
    # 核心判定：缩量大跌信号
    df['is_shrink_drop'] = (df['low'] < df['low'].shift(1)) & (df['volume'] < df['volume'].shift(1))
    
    # 时间切片
    acc_period = df.iloc[-60:-30]   
    shake_period = df.iloc[-30:-10] 
    active_period = df.iloc[-10:]  
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # 1. 吸筹判定
    red_vol = acc_period[acc_period['close'] > acc_period['open']]['volume'].sum()
    green_vol = acc_period[acc_period['close'] <= acc_period['open']]['volume'].sum()
    is_accumulating = (red_vol > green_vol * 1.5) 
    
    # 2. 20日洗盘特征
    had_panic_shrink_20d = df.iloc[-20:]['is_shrink_drop'].any()
    avg_vol_long = df.iloc[-60:-10]['volume'].mean()
    big_down_vol = df.iloc[-30:-1]['volume'] > avg_vol_long * 2.5
    is_clean_shake = big_down_vol.any() == False and had_panic_shrink_20d

    # 3. 启动特征
    has_breakout = len(active_period[active_period['pct_chg'] >= 4.0]) >= 2 
    is_shrinking = curr['volume'] < prev['volume']  
    ma5_trending_up = curr['MA5'] > prev['MA5']     
    on_ma5 = (curr['close'] >= curr['MA5']) and (curr['low'] <= curr['MA5'] * 1.015) 
    
    is_pullback = is_shrinking and on_ma5 and ma5_trending_up

    # 4. 结果输出
    if is_accumulating and is_clean_shake:
        if has_breakout and is_pullback:
            return "🚀 启动期"
        elif not has_breakout and had_panic_shrink_20d:
            return "🧪 蓄势中"
        else:
            return "🏖️ 整理区"
            
    return None