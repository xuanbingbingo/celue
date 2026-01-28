import os
import json
import datetime
import webbrowser
import platform
import pandas as pd
import akshare as ak
import logging
from tqdm import tqdm

# 配置日志：同时输出到文件，使用 UTF-8 编码防止中文乱码
logging.basicConfig(
    filename='sync_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    filemode='w' # 每次运行覆盖旧日志，若想追加请改为 'a'
)

CONCEPT_CACHE = "concept_cache.json"

def update_concept_cache():
    today = datetime.datetime.now().strftime('%Y%m%d')
    logging.info(f"🚀 开始同步概念板块数据 | 日期: {today}")
    print(f"🔄 正在同步数据，详情请查看 sync_debug.log...")
    
    concept_map = {}
    try:
        df_concepts = ak.stock_board_concept_name_em()
        if df_concepts.empty:
            logging.error("无法获取概念板块列表")
            return

        concept_list = df_concepts['板块名称'].tolist()[:200] 

        for name in tqdm(concept_list, desc="同步中"):
            try:
                df_members = ak.stock_board_concept_cons_em(symbol=name)
                
                # --- 将 Debug 信息写入日志而非控制台 ---
                logging.info(f"--- 正在解析板块: {name} ---")
                if df_members.empty:
                    logging.warning(f"板块 {name} 返回数据为空")
                    continue
                
                logging.info(f"列名: {df_members.columns.tolist()}")
                logging.info(f"数据样板:\n{df_members.head(3).to_string()}") 
                # ------------------------------------

                # 动态寻找代码列
                code_col = next((col for col in df_members.columns if '代码' in col), None)
                
                if not code_col:
                    logging.error(f"板块 {name} 未找到包含'代码'的列")
                    continue

                count_added = 0
                for code in df_members[code_col].tolist():
                    pure_code = str(code).zfill(6)
                    # 适配逻辑...
                    if pure_code not in concept_map:
                        concept_map[pure_code] = []
                    if name not in concept_map[pure_code] and len(concept_map[pure_code]) < 3:
                        concept_map[pure_code].append(name)
                        count_added += 1
                
                logging.info(f"成功关联 {count_added} 只个股")

            except Exception as e:
                logging.error(f"处理板块 {name} 时发生异常: {str(e)}")
                continue

        # 结果保存
        final_data = {k: " / ".join(v) for k, v in concept_map.items()}
        if final_data:
            with open(CONCEPT_CACHE, 'w', encoding='utf-8') as f:
                json.dump({'date': today, 'data': final_data}, f, ensure_ascii=False)
            logging.info(f"✅ 同步圆满完成，共记录 {len(final_data)} 只个股")
            print(f"✨ 同步成功！共记录 {len(final_data)} 只个股。")
        else:
            logging.critical("❌ 同步结束但结果为空字典！")

    except Exception as e:
        logging.critical(f"全局同步崩溃: {str(e)}")
def load_concept_map():
    """
    从本地加载缓存，不联网。主程序 main.py 调用此方法。
    """
    if not os.path.exists(CONCEPT_CACHE):
        print(f"⚠️ 警告：找不到缓存文件 {CONCEPT_CACHE}，请先运行同步脚本。")
        return {}

    with open(CONCEPT_CACHE, 'r', encoding='utf-8') as f:
        try:
            cache_data = json.load(f)
            return cache_data.get('data', {})
        except:
            return {}

# ================= 2. 交互式报告生成逻辑 =================

def generate_report(results, total_scanned):
    """
    生成支持单概念点击过滤的交互式 HTML 报告
    """
    if not results:
        print("💡 无结果，跳过报告生成。")
        return

    # 按阶段降序排序
    df_res = pd.DataFrame(results).sort_values(by=['阶段', '代码'], ascending=[False, True])
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    html_file = "scanner_report.html"
    
    # 提取所有代码方便一键复制
    all_codes = ",".join(df_res['代码'].tolist())

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>策略扫描报告</title>
        <style>
            body {{ font-family: 'Inter', -apple-system, sans-serif; background: #f8fafc; color: #1e293b; padding: 30px; line-height: 1.5; }}
            .card {{ background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); max-width: 1100px; margin: auto; }}
            
            .header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px; }}
            .info-bar {{ font-size: 14px; color: #64748b; margin-bottom: 20px; }}
            .code-box {{ background: #0f172a; color: #38bdf8; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 14px; word-break: break-all; margin-bottom: 25px; border-left: 4px solid #3b82f6; }}
            
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 12px; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
            td {{ padding: 16px 12px; border-bottom: 1px solid #f1f5f9; }}
            
            /* 交互组件样式 */
            .stage-tag {{ background: #1e293b; color: #f8fafc; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.3s; }}
            .stage-tag:hover {{ background: #3b82f6; }}
            
            .concept-tag {{ 
                display: inline-block; background: #f1f5f9; color: #475569; padding: 3px 10px; border-radius: 20px; 
                font-size: 11px; margin: 2px; cursor: pointer; transition: 0.2s; border: 1px solid #e2e8f0;
            }}
            .concept-tag:hover {{ background: #3b82f6; color: white; border-color: #3b82f6; }}
            
            .active-filter {{ background: #3b82f6 !important; color: white !important; border-color: #3b82f6 !important; }}
            .up-price {{ color: #ef4444; font-weight: 600; }}
            .down-price {{ color: #22c55e; font-weight: 600; }}
            
            .filter-status {{ display: inline-block; margin-left: 15px; color: #3b82f6; font-weight: bold; font-size: 13px; }}
            button.reset-btn {{ padding: 4px 12px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; font-size: 12px; }}
            button.reset-btn:hover {{ background: #f1f5f9; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <h1 style="margin:0; font-size: 24px;">📊 策略扫描结果</h1>
                <div id="filterControl">
                    <button class="reset-btn" onclick="resetFilter()">显示全部</button>
                    <span id="activeFilterDisplay" class="filter-status"></span>
                </div>
            </div>
            
            <div class="info-bar">
                <span>命中数量: <b>{len(df_res)}</b></span> | 
                <span>扫描总量: {total_scanned}</span> | 
                <span>生成时间: {report_time}</span>
            </div>

            <div class="code-box">
                <small style="color: #94a3b8; display: block; margin-bottom: 5px;">一键复制选股 (代码串):</small>
                {all_codes}
            </div>

            <table>
                <thead>
                    <tr>
                        <th>阶段</th><th>证券代码</th><th>现价</th><th>涨跌幅</th><th>概念板块 (点击标签过滤)</th><th>操作</th>
                    </tr>
                </thead>
                <tbody id="stockTableBody">
    """

    for _, r in df_res.iterrows():
        # 拆分概念为可点击的 span
        concept_list = str(r.get('概念', '未分类')).split(' / ')
        concept_html = "".join([f'<span class="concept-tag" onclick="filterByConcept(\'{c}\', this)">{c}</span>' for c in concept_list])
        
        # 涨跌幅样式
        is_up = "-" not in str(r['涨跌幅'])
        price_class = "up-price" if is_up else "down-price"
        
        # 构造跳转 URL
        m = "sh" if "sh" in str(r.get('完整_代码', r.get('完整代码', ''))).lower() else "sz"
        url = f"https://quote.eastmoney.com/concept/{m}{r['代码']}.html"

        html_template += f"""
                    <tr class="stock-row" data-stage="{r['阶段']}" data-concepts="{r.get('概念','')}">
                        <td><span class="stage-tag" onclick="filterByStage('{r['阶段']}', this)">{r['阶段']}</span></td>
                        <td><b>{r['代码']}</b></td>
                        <td>{r['现价']}</td>
                        <td class="{price_class}">{r['涨跌幅']}</td>
                        <td>{concept_html}</td>
                        <td><a href="{url}" target="_blank" style="text-decoration: none;">🔍</a></td>
                    </tr>
        """

    # 注入 JavaScript 交互引擎
    html_template += """
                </tbody>
            </table>
        </div>

        <script>
        function filterByConcept(concept, element) {
            updateUI(element);
            const rows = document.querySelectorAll('.stock-row');
            rows.forEach(row => {
                const concepts = row.getAttribute('data-concepts');
                row.style.display = concepts.includes(concept) ? '' : 'none';
            });
            document.getElementById('activeFilterDisplay').innerText = "🔎 当前过滤：" + concept;
        }

        function filterByStage(stage, element) {
            updateUI(element);
            const rows = document.querySelectorAll('.stock-row');
            rows.forEach(row => {
                row.style.display = (row.getAttribute('data-stage') === stage) ? '' : 'none';
            });
            document.getElementById('activeFilterDisplay').innerText = "🔎 当前过滤：" + stage;
        }

        function resetFilter() {
            document.querySelectorAll('.stock-row').forEach(row => row.style.display = '');
            document.querySelectorAll('.active-filter').forEach(el => el.classList.remove('active-filter'));
            document.getElementById('activeFilterDisplay').innerText = "";
        }

        function updateUI(activeEl) {
            document.querySelectorAll('.concept-tag, .stage-tag').forEach(el => el.classList.remove('active-filter'));
            activeEl.classList.add('active-filter');
        }
        </script>
    </body>
    </html>
    """

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    # 自动打开
    abs_path = os.path.abspath(html_file)
    if platform.system() == "Darwin":
        os.system(f'open "{abs_path}"')
    else:
        webbrowser.open(f"file://{abs_path}")