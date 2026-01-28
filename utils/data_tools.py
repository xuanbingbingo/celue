import os
import json
import datetime
import webbrowser
import platform
import urllib.parse
import pandas as pd
import akshare as ak
from tqdm import tqdm

def get_concept_map_cached():
    """
    获取全 A 股的概念板块映射
    """
    cache_file = "concept_cache.json"
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # 1. 检查缓存
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            try:
                cache_data = json.load(f)
                if cache_data.get('date') == today and len(cache_data.get('data', {})) > 100:
                    return cache_data.get('data')
            except: pass

    print("🔄 正在同步东方财富核心概念板块 (预计 1 分钟)...")
    concept_map = {}
    
    try:
        # 获取所有概念板块名称
        df_concepts = ak.stock_board_concept_name_em()
        # 选取前 200 个热门概念，兼顾速度与覆盖率
        concept_list = df_concepts['板块名称'].tolist()[:200] 

        for name in tqdm(concept_list, desc="解析板块成分"):
            try:
                # 获取该板块成分股
                df_members = ak.stock_board_concept_cons_em(symbol=name)
                for code in df_members['代码'].tolist():
                    if code not in concept_map:
                        concept_map[code] = []
                    # 每个股票最多保留 3 个关联概念
                    if name not in concept_map[code] and len(concept_map[code]) < 3:
                        concept_map[code].append(name)
            except:
                continue

        # 转换为字符串格式: "概念A / 概念B"
        final_map = {k: " / ".join(v) for k, v in concept_map.items()}

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({'date': today, 'data': final_map}, f, ensure_ascii=False)
            
        return final_map
    except Exception as e:
        print(f"⚠️ 概念同步失败: {e}")
        return {}

def generate_report(results, total_scanned):
    """
    生成包含概念板块的 HTML 报告
    """
    if not results:
        print("💡 无结果，跳过报告生成。")
        return

    # 排序：先按阶段，再按代码
    df_res = pd.DataFrame(results).sort_values(by=['阶段', '代码'], ascending=[False, True])
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    html_file = "scanner_report.html"
    
    all_codes = ",".join(df_res['代码'].tolist())

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #333; padding: 20px; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 1100px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .code-box {{ background: #2d3436; color: #fab1a0; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 14px; margin: 15px 0; word-break: break-all; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #f8f9fa; color: #636e72; font-weight: 600; }}
            .tag {{ background: #dfe6e9; color: #2d3436; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .concept-tag {{ color: #0984e3; font-size: 12px; font-style: italic; }}
            .price {{ font-family: 'Arial', sans-serif; font-weight: bold; }}
            .btn {{ text-decoration: none; color: #0984e3; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h2>🚀 策略扫描报告 (概念增强版)</h2>
                <span>命中: <b>{len(df_res)}</b> / 扫描: {total_scanned}</span>
            </div>
            <p style="font-size: 13px; color: #636e72;">生成时间: {report_time}</p>
            
            <div class="code-box">📋 快捷复制: {all_codes}</div>

            <table>
                <thead>
                    <tr>
                        <th>阶段</th>
                        <th>代码</th>
                        <th>价格</th>
                        <th>涨跌幅</th>
                        <th>所属概念</th>
                        <th>详情</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, r in df_res.iterrows():
        m = "sh" if "sh" in r['完整代码'].lower() else "sz"
        url = f"https://quote.eastmoney.com/concept/{m}{r['代码']}.html"
        
        # 涨跌幅颜色
        color = "#d63031" if "-" not in r['涨跌幅'] else "#00b894"
        
        html_template += f"""
                    <tr>
                        <td><span class="tag">{r['阶段']}</span></td>
                        <td><b>{r['代码']}</b></td>
                        <td class="price">{r['现价']}</td>
                        <td style="color: {color}">{r['涨跌幅']}</td>
                        <td class="concept-tag">{r.get('概念', '-')}</td>
                        <td><a href="{url}" target="_blank" class="btn">📈</a></td>
                    </tr>
        """

    html_template += "</tbody></table></div></body></html>"
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    abs_path = os.path.abspath(html_file)
    if platform.system() == "Darwin":
        os.system(f'open "{abs_path}"')
    else:
        webbrowser.open(f"file://{abs_path}")