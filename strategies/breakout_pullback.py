import pandas as pd
import numpy as np

def analyze(df):
    """
    策略版本：V3.1 (突破回调版 - 增强)
    核心逻辑：大红小绿吸筹期 + 五日小幅放量 + 三连阳后缩量大跌
    
    阶段定义：
    - 🚀 启动期（重中之重）：满足启动期(重点)条件，且近5日内有效跌破三连阳最后一天的最低价，收盘下跌
    - 🚀 启动期（重点）：满足所有条件，且大跌后快速收复
    - 🚀 启动期：满足所有条件
    - 🧪 蓄势中：满足吸筹+放量条件，等待大跌信号
    - 🏖️ 整理区：仅满足吸筹条件
    """
    if df is None or len(df) < 60:
        return None
    
    df = df.copy()
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 指标计算
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    df['MA30'] = df['close'].rolling(30).mean()
    df['MA60'] = df['close'].rolling(60).mean()
    df['MA20_vol'] = df['volume'].rolling(20).mean()
    df['pct_chg'] = df['close'].pct_change() * 100
    
    curr = df.iloc[-1]
    
    # 时间切片
    acc_period = df.iloc[-60:-20]
    recent_5d = df.iloc[-5:]
    
    # ========== 1. 吸筹判定（大红小绿） ==========
    red_days = acc_period[acc_period['close'] > acc_period['open']]
    green_days = acc_period[acc_period['close'] <= acc_period['open']]
    
    red_vol = red_days['volume'].sum()
    green_vol = green_days['volume'].sum()
    red_count = len(red_days)
    green_count = len(green_days)
    
    is_accumulating = (red_vol > green_vol * 1.3) and (red_count >= green_count)
    
    if not is_accumulating:
        return None
    
    # ========== 2. 五日小幅放量判定 ==========
    vol_above_ma20 = (recent_5d['volume'] > recent_5d['MA20_vol']).sum()
    has_volume_expansion = vol_above_ma20 >= 3
    max_vol_ratio = (recent_5d['volume'] / recent_5d['MA20_vol']).max()
    is_moderate_volume = max_vol_ratio < 3.0
    volume_ok = has_volume_expansion and is_moderate_volume
    
    # ========== 3. 三连阳后缩量大跌判定（含重中之重逻辑） ==========
    has_three_rising = False
    has_crash = False
    crash_recovered = False
    
    # 用于重中之重判断的数据
    three_rising_last_low = None  # 三连阳最后一天的最低价
    
    # 检查最近20天内的三连阳+大跌组合
    for i in range(-20, -3):
        if i < -len(df) + 3:
            continue
        
        day1 = df.iloc[i]
        day2 = df.iloc[i+1]
        day3 = df.iloc[i+2]
        
        # 三连阳判定
        rising_count = 0
        if day1['close'] > day1['open']: rising_count += 1
        if day2['close'] > day2['open']: rising_count += 1
        if day3['close'] > day3['open']: rising_count += 1
        
        total_gain = (day3['close'] - day1['open']) / day1['open'] * 100
        
        if rising_count >= 2 and total_gain > 3:
            has_three_rising = True
            three_rising_last_low = day3['low']  # 记录三连阳最后一天的最低价
            
            # 检查第四天是否大跌
            crash_day = df.iloc[i+3]
            prev_day = day3
            
            is_falling = crash_day['close'] < crash_day['open']
            break_low = crash_day['low'] < prev_day['low']
            
            avg_vol_3d = (day1['volume'] + day2['volume'] + day3['volume']) / 3
            is_shrinking = crash_day['volume'] < avg_vol_3d * 0.8
            
            drop_pct = (crash_day['close'] - crash_day['open']) / crash_day['open'] * 100
            is_big_drop = -7 < drop_pct < -3
            
            if is_falling and break_low and is_shrinking and is_big_drop:
                has_crash = True
                
                # 检查大跌后是否快速收复（3日内）
                if i + 6 < 0:
                    crash_close = crash_day['close']
                    for j in range(i+4, min(i+7, 0)):
                        if df.iloc[j]['close'] > crash_close * 1.02:
                            crash_recovered = True
                            break
                break
    
    # ========== 4. 重中之重判定 ==========
    # 条件：近5日内，有效跌破三连阳最后一天的最低价，且收盘下跌
    is_key_signal = False
    if has_three_rising and three_rising_last_low is not None:
        for i in range(-5, 0):  # 近5日
            if i < -len(df):
                continue
            check_day = df.iloc[i]
            # 有效跌破：最低价低于三连阳最后一天的最低价
            # 收盘下跌：收盘价低于开盘价
            if check_day['low'] < three_rising_last_low and check_day['close'] < check_day['open']:
                is_key_signal = True
                break
    
    # ========== 5. 结果输出 ==========
    if has_three_rising and has_crash:
        if is_key_signal:
            return "🚀 启动期（重中之重）"  # 最高优先级
        elif crash_recovered:
            return "🚀 启动期（重点）"
        else:
            return "🚀 启动期"
    elif volume_ok and has_three_rising:
        return "🧪 蓄势中"
    elif is_accumulating:
        return "🏖️ 整理区"
    
    return None
