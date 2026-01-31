#初始化stock_data
import baostock as bs
import pandas as pd
import os
import json
from tqdm import tqdm
from datetime import datetime, timedelta

DATA_DIR = "./stock_data"
STOCK_NAME_CACHE = "stock_name_cache.json"
if not os.path.exists(DATA_DIR): 
    os.makedirs(DATA_DIR)
    print(f"📁 已创建文件夹: {DATA_DIR}")

def init_database():
    # 1. 登录
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ BaoStock 登录失败: {lg.error_msg}")
        return

    # 2. 获取证券清单
    # 注意：如果当天不是交易日，某些版本可能返回空，这里我们尝试获取最近一个交易日的清单
    target_date = datetime.now().strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=target_date)
    
    stock_list = []
    while rs.next():
        stock_list.append(rs.get_row_data())

    # 如果列表为空，尝试往前推一天（防止周末运行报错）
    if not stock_list:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"⚠️ {target_date} 清单为空，尝试获取 {yesterday} 的清单...")
        rs = bs.query_all_stock(day=yesterday)
        while rs.next():
            stock_list.append(rs.get_row_data())

    if not stock_list:
        print("❌ 无法获取证券清单，请检查网络或 BaoStock 服务状态。")
        bs.logout()
        return

    print(f"🔍 成功获取清单，共 {len(stock_list)} 条记录，开始筛选并下载...")

    # 3. 设定时间范围
    start_date = "2025-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # 4. 创建股票名称映射缓存
    stock_name_map = {}
    for code, status, name in stock_list:
        pure_code = code.split('.')[1] if '.' in code else code
        stock_name_map[pure_code] = name
    
    # 保存股票名称缓存
    with open(STOCK_NAME_CACHE, 'w', encoding='utf-8') as f:
        json.dump(stock_name_map, f, ensure_ascii=False)
    print(f"💾 已保存 {len(stock_name_map)} 只股票名称映射")

    success_count = 0
    # 5. 循环下载
    for code, status, name in tqdm(stock_list, desc="初始化进度"):
        # 严格匹配号段：沪深主板、创业板、科创板、北交所 (920/8/4)
        pure_code = code.split('.')[1]
        if not (code.startswith(('sh.60', 'sh.68', 'sz.00', 'sz.30', 'bj.92', 'bj.8', 'bj.4'))):
            continue
        
        # 排除 ST
        if "ST" in name or "*" in name:
            continue

        file_path = f"{DATA_DIR}/{code}.csv"
        
        # 抓取日线数据
        rs_data = bs.query_history_k_data_plus(
            code, 
            "date,open,high,low,close,volume",
            start_date=start_date, 
            end_date=end_date, 
            frequency="d", 
            adjustflag="2"  # 前复权
        )
        
        res_list = []
        while rs_data.next():
            res_list.append(rs_data.get_row_data())
        
        if res_list:
            df = pd.DataFrame(res_list, columns=rs_data.fields)
            df.to_csv(file_path, index=False)
            success_count += 1
            
    bs.logout()
    print(f"✅ 初始化完成！成功同步 {success_count} 只股票。")
    print(f"📂 数据存储位置: {os.path.abspath(DATA_DIR)}")

if __name__ == "__main__":
    init_database()