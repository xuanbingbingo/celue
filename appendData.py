#追加最新的stock_data
import baostock as bs
import pandas as pd
import os
from datetime import datetime
DATA_DIR = './stock_data'
def update_stock_data():
    bs.login()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔄 正在更新 {today} 的增量数据...")
    
    # 获取最新列表（包含可能的新股）
    rs = bs.query_all_stock()
    while rs.next():
        code, status, name = rs.get_row_data()
        # 剔除399开头的行业指数
        pure_code = code.split('.')[1] if '.' in code else code
        if pure_code.startswith('399'):
            continue
        if not (code.startswith(('sh.6', 'sz.0', 'sz.3', 'bj.'))): continue
        
        file_path = f"{DATA_DIR}/{code}.csv"
        
        # 1. 获取该股票本地最后一条日期
        last_date = "2025-01-01"
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty and 'date' in existing_df.columns:
                    last_date = existing_df.iloc[-1]['date']
            except Exception:
                pass  # 如果读取失败，使用默认日期
        
        # 如果最后日期就是今天，说明已经更新过了
        if last_date >= today: continue

        # 2. 抓取从最后一天到今天的增量
        rs_inc = bs.query_history_k_data_plus(code,
            "date,open,high,low,close,volume",
            start_date=last_date, end_date=today,
            frequency="d", adjustflag="2")
        
        inc_list = []
        while rs_inc.next(): inc_list.append(rs_inc.get_row_data())
        
        if len(inc_list) > 1: # 第一条通常是重复的 last_date
            new_df = pd.DataFrame(inc_list, columns=rs_inc.fields)
            # 过滤掉已经存在的日期
            new_df = new_df[new_df['date'] > last_date]
            # 追加写入
            new_df.to_csv(file_path, mode='a', header=False, index=False)
            
    bs.logout()
    print(f"✅ {today} 增量数据同步完成！")
if __name__ == "__main__":
    update_stock_data()