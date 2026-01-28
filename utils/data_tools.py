import os
import json
import datetime
import logging
import time
import random
import webbrowser
import platform
import urllib.parse
import pandas as pd
import akshare as ak
from tqdm import tqdm

# ================= 配置与初始化 =================

# 缓存与日志文件名
CONCEPT_CACHE = "concept_cache.json"
LOG_FILE = "sync_debug.log"

# 配置日志系统
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    filemode='w'
)

# ================= 1. 概念数据同步模块 =================

def update_concept_cache():
    """
    同步东方财富热门概念数据。
    采用随机延迟与重试机制，防止 RemoteDisconnected 封禁。
    """
    today = datetime.datetime.now().strftime('%Y%m%d')
    logging.info(f"🚀 启动增强版同步 (抗封锁模式) | 日期: {today}")
    print(f"🔄 正在同步（随机延迟模式，详情见 {LOG_FILE}）...")
    
    concept_map = {}
    try:
        # 获取概念板块列表
        df_concepts = ak.stock_board_concept_name_em()
        if df_concepts.empty:
            logging.error("无法获取概念板块列表")
            return

        # 选取前 100 个热门概念（建议先测试 100 个，稳定后再增加）
        concept_list = df_concepts['板块名称'].tolist()[:100] 

        for name in tqdm(concept_list, desc="同步题材中"):
            # 随机休眠 0.6 - 1.4 秒，模拟人工翻阅
            time.sleep(random.uniform(0.6, 1.4))
            
            # 建立 3 次重试机制以应对网络波动
            success = False
            for retry in range(3):
                try:
                    df_members = ak.stock_board_concept_cons_em(symbol=name)
                    if not df_members.empty:
                        # 记录样本到日志
                        logging.info(f"板块 [{name}] 同步成功 | 样本: {df_members.iloc[0, :2].to_dict()}")
                        
                        # 动态寻找代码列
                        code_col = next((col for col in df_members.columns if '代码' in col), None)
                        if code_col:
                            for code in df_members[code_col].tolist():
                                pure_code = str(code).zfill(6)
                                if pure_code not in concept_map:
                                    concept_map[pure_code] = []
                                # 每只股票保留前 3 个核心题材
                                if name not in concept_map[pure_code] and len(concept_map[pure_code]) < 3:
                                    concept_map[pure_code].append(name)
                        success = True
                        break # 请求成功，退出重试循环
                except Exception as e:
                    logging.warning(f"板块 {name} 第 {retry+1} 次失败: {e}")
                    time.sleep(3) # 失败后多等待一会儿
            
            if not success:
                logging.error(f"❌ 板块 {name} 彻底同步失败")

        # 格式化并保存结果
        final_data = {k: " / ".join(v) for k, v in concept_map.items()}
        
        if final_data:
            with open(CONCEPT_CACHE, 'w', encoding='utf-8') as f:
                json.dump({'date': today, 'data': final_data}, f, ensure_ascii=False)
            logging.info(f"✅ 同步圆满完成，共记录 {len(final_data)} 只个股")
            print(f"✨ 同步成功！共记录 {len(final_data)} 只个股的概念映射。")
        else:
            logging.critical("❌ 同步结束但结果为空，请检查网络权限。")

    except Exception as e:
        logging.error(f"全局同步崩溃: {e}")
        print(f"❌ 运行错误: {e}")

# ================= 2. 缓存加载模块 =================

def load_concept_map():
    """
    主程序调用：秒级从本地 JSON 加载数据
    """
    if not os.path.exists(CONCEPT_CACHE):
        return {}
    try:
        with open(CONCEPT_CACHE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            return cache_data.get('data', {})
    except Exception as e:
        logging.error(f"加载缓存失败: {e}")
        return {}

# ================= 3. 交互式报告生成模块 =================

def generate_report(results, total_scanned):
    """
    生成带 JS 过滤逻辑的 HTML 报告
    """
    if not results:
        print("💡 无结果，跳过报告。")
        return

    df_res = pd.DataFrame(results).sort_values(by=['阶段', '代码'], ascending=[False, True])
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    html_file = "scanner_report.html"
    all_codes = ",".join(df_res['代码'].tolist())

    # HTML 结构定义
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f8fafc; color: #1e293b; padding: 25px; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); max-width: 1100px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 20px; }}
            .code-box {{ background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 12px; color: #64748b; font-size: 12px; text-transform: uppercase; }}
            td {{ padding: 14px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
            .stage-tag {{ background: #1e293b; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; }}
            .concept-tag {{ background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px; cursor: pointer; }}
            .active-filter {{ background: #3b82f6 !important; color: white !important; }}
            .up {{ color: #ef4444; font-weight: bold; }}
            .down {{ color: #22c55e; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h2 style="margin:0;">🎯 题材联动扫描结果</h2>
                <div id="filterInfo" style="font-size: 12px; color: #3b82f6;">
                    点击下方<b>标签</b>即可过滤标的 | <button onclick="resetFilter()" style="cursor:pointer;">清除过滤</button>
                </div>
            </div>
            <div class="code-box">📋 复制选股: {all_codes}</div>
            <p style="font-size: 12px; color: #64748b;">扫描: {total_scanned} | 命中: {len(df_res)} | 时间: {report_time}</p>
            <table>
                <thead>
                    <tr><th>状态</th><th>代码</th><th>价格</th><th>涨跌幅</th><th>概念板块</th><th>详情</th></tr>
                </thead>
                <tbody>
    """

    for _, r in df_res.iterrows():
        concepts = str(r.get('概念', '其他')).split(' / ')
        concept_html = "".join([f'<span class="concept-tag" onclick="filterByConcept(\'{c}\', this)">{c}</span>' for c in concepts])
        
        m = "sh" if "sh" in str(r.get('完整_代码', r.get('完整代码', ''))).lower() else "sz"
        url = f"https://quote.eastmoney.com/concept/{m}{r['代码']}.html"
        change_style = "up" if "-" not in str(r['涨跌幅']) else "down"

        html_template += f"""
                    <tr class="stock-row" data-stage="{r['stage'] if 'stage' in r else r.get('阶段', '')}" data-concepts="{r.get('概念','')}">
                        <td><span class="stage-tag" onclick="filterByStage('{r.get('阶段', '')}', this)">{r.get('阶段', '')}</span></td>
                        <td><b>{r['代码']}</b></td>
                        <td>{r['现价']}</td>
                        <td class="{change_style}">{r['涨跌幅']}</td>
                        <td>{concept_html}</td>
                        <td><a href="{url}" target="_blank" style="text-decoration:none;">🔍</a></td>
                    </tr>
        """

    html_template += """
                </tbody>
            </table>
        </div>
        <script>
        function filterByConcept(val, el) {
            updateUI(el);
            document.querySelectorAll('.stock-row').forEach(row => {
                row.style.display = row.getAttribute('data-concepts').includes(val) ? '' : 'none';
            });
        }
        function filterByStage(val, el) {
            updateUI(el);
            document.querySelectorAll('.stock-row').forEach(row => {
                row.style.display = row.getAttribute('data-stage') === val ? '' : 'none';
            });
        }
        function resetFilter() {
            document.querySelectorAll('.stock-row').forEach(row => row.style.display = '');
            document.querySelectorAll('.active-filter').forEach(el => el.classList.remove('active-filter'));
        }
        function updateUI(el) {
            document.querySelectorAll('.concept-tag, .stage-tag').forEach(tag => tag.classList.remove('active-filter'));
            el.classList.add('active-filter');
        }
        </script>
    </body>
    </html>
    """

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    # 跨平台自动打开报告
    abs_path = os.path.abspath(html_file)
    if platform.system() == "Darwin":
        os.system(f'open "{abs_path}"')
    else:
        webbrowser.open(f"file://{abs_path}")