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
    生成数据仪表盘风格的 HTML 报告，带 Tab 切换功能
    """
    if not results:
        print("💡 无结果，跳过报告。")
        return

    df_res = pd.DataFrame(results).sort_values(by=['阶段', '代码'], ascending=[False, True])
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    html_file = "scanner_report.html"
    all_codes = ",".join(df_res['代码'].tolist())

    # 统计数据
    stage_counts = df_res['阶段'].value_counts().to_dict()
    total_hit = len(df_res)

    # 阶段排序和颜色映射
    stage_order = ['🚀 启动期', '🧪 蓄势中', '🏖️ 整理区']
    stage_colors = {
        '🚀 启动期': {'bg': '#fef3c7', 'border': '#f59e0b', 'text': '#92400e', 'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'},
        '🧪 蓄势中': {'bg': '#dbeafe', 'border': '#3b82f6', 'text': '#1e40af', 'gradient': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'},
        '🏖️ 整理区': {'bg': '#d1fae5', 'border': '#10b981', 'text': '#065f46', 'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)'}
    }

    # HTML 结构定义
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 量化扫描仪表盘</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .dashboard {{ 
            max-width: 1400px; 
            margin: 0 auto;
        }}
        
        /* 头部区域 */
        .header {{
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }}
        
        .title {{
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .report-time {{
            color: #6b7280;
            font-size: 14px;
        }}
        
        /* 统计卡片 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.5);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: 800;
            color: #1e293b;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 13px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* 阶段卡片 */
        .stage-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .stage-card {{
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 3px solid transparent;
            position: relative;
            overflow: hidden;
        }}
        
        .stage-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            opacity: 0.1;
            transition: opacity 0.3s;
        }}
        
        .stage-card:hover::before {{
            opacity: 0.2;
        }}
        
        .stage-card.active {{
            border-color: currentColor;
            transform: scale(1.02);
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .stage-card-启动期 {{ background: {stage_colors['🚀 启动期']['bg']}; color: {stage_colors['🚀 启动期']['text']}; }}
        .stage-card-蓄势中 {{ background: {stage_colors['🧪 蓄势中']['bg']}; color: {stage_colors['🧪 蓄势中']['text']}; }}
        .stage-card-整理区 {{ background: {stage_colors['🏖️ 整理区']['bg']}; color: {stage_colors['🏖️ 整理区']['text']}; }}
        
        .stage-name {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .stage-count {{
            font-size: 36px;
            font-weight: 800;
            margin-bottom: 5px;
        }}
        
        .stage-desc {{
            font-size: 12px;
            opacity: 0.8;
        }}
        
        /* 内容区域 */
        .content {{
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        .content-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .filter-info {{
            font-size: 14px;
            color: #6b7280;
        }}
        
        .filter-info span {{
            font-weight: 600;
            color: #1e293b;
        }}
        
        .actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border-radius: 10px;
            border: none;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #f1f5f9;
            color: #475569;
        }}
        
        .btn-secondary:hover {{
            background: #e2e8f0;
        }}
        
        /* 代码复制框 */
        .code-box {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #38bdf8;
            padding: 15px 20px;
            border-radius: 12px;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 13px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .code-box:hover {{
            box-shadow: 0 5px 20px rgba(30, 41, 59, 0.4);
        }}
        
        .code-text {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: calc(100% - 80px);
        }}
        
        .copy-hint {{
            font-size: 11px;
            color: #64748b;
            background: rgba(255,255,255,0.1);
            padding: 4px 10px;
            border-radius: 6px;
        }}
        
        /* 表格样式 */
        .table-container {{
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        thead {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }}
        
        th {{
            text-align: left;
            padding: 16px;
            color: #475569;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        td {{
            padding: 16px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }}
        
        tr:hover {{
            background: #f8fafc;
        }}
        
        tr.hidden {{
            display: none;
        }}
        
        /* 状态标签 */
        .stage-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-启动期 {{ background: {stage_colors['🚀 启动期']['bg']}; color: {stage_colors['🚀 启动期']['text']}; }}
        .badge-蓄势中 {{ background: {stage_colors['🧪 蓄势中']['bg']}; color: {stage_colors['🧪 蓄势中']['text']}; }}
        .badge-整理区 {{ background: {stage_colors['🏖️ 整理区']['bg']}; color: {stage_colors['🏖️ 整理区']['text']}; }}
        
        /* 概念标签 */
        .concept-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .concept-tag {{
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
            color: #0369a1;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}
        
        .concept-tag:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(3, 105, 161, 0.2);
        }}
        
        .concept-tag.active {{
            background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%);
            color: white;
        }}
        
        /* 涨跌幅 */
        .change-up {{ 
            color: #ef4444; 
            font-weight: 700;
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            padding: 6px 12px;
            border-radius: 8px;
            display: inline-block;
        }}
        .change-down {{ 
            color: #22c55e; 
            font-weight: 700;
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            padding: 6px 12px;
            border-radius: 8px;
            display: inline-block;
        }}
        
        /* 价格 */
        .price {{
            font-weight: 700;
            color: #1e293b;
            font-size: 15px;
        }}
        
        /* 代码 */
        .stock-code {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            color: #1e293b;
            font-size: 15px;
        }}
        
        /* 详情链接 */
        .detail-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            border-radius: 10px;
            text-decoration: none;
            transition: all 0.3s;
        }}
        
        .detail-link:hover {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transform: scale(1.1);
        }}
        
        .detail-link:hover svg {{
            stroke: white;
        }}
        
        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        }}
        
        .empty-state svg {{
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }}
        
        /* Toast 提示 */
        .toast {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: white;
            padding: 14px 28px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        
        .toast.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 20px; }}
            .title {{ font-size: 22px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .stage-cards {{ grid-template-columns: 1fr; }}
            th, td {{ padding: 12px 10px; font-size: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- 头部区域 -->
        <div class="header">
            <div class="header-top">
                <h1 class="title">🎯 量化扫描仪表盘</h1>
                <span class="report-time">📅 {report_time}</span>
            </div>
            
            <!-- 统计卡片 -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_scanned}</div>
                    <div class="stat-label">扫描总数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_hit}</div>
                    <div class="stat-label">命中标的</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{round(total_hit/total_scanned*100, 1)}%</div>
                    <div class="stat-label">命中率</div>
                </div>
            </div>
            
            <!-- 阶段 Tab 卡片 -->
            <div class="stage-cards">
                <div class="stage-card stage-card-启动期" data-stage="🚀 启动期" onclick="filterByStage('🚀 启动期')">
                    <div class="stage-name">🚀 启动期</div>
                    <div class="stage-count">{stage_counts.get('🚀 启动期', 0)}</div>
                    <div class="stage-desc">已突破 + 回踩确认，建议关注</div>
                </div>
                <div class="stage-card stage-card-蓄势中" data-stage="🧪 蓄势中" onclick="filterByStage('🧪 蓄势中')">
                    <div class="stage-name">🧪 蓄势中</div>
                    <div class="stage-count">{stage_counts.get('🧪 蓄势中', 0)}</div>
                    <div class="stage-desc">吸筹完成 + 洗盘结束，等待突破</div>
                </div>
                <div class="stage-card stage-card-整理区" data-stage="🏖️ 整理区" data-stage="🏖️ 整理区" onclick="filterByStage('🏖️ 整理区')">
                    <div class="stage-name">🏖️ 整理区</div>
                    <div class="stage-count">{stage_counts.get('🏖️ 整理区', 0)}</div>
                    <div class="stage-desc">吸筹中或横盘整理，观察为主</div>
                </div>
            </div>
        </div>
        
        <!-- 内容区域 -->
        <div class="content">
            <div class="content-header">
                <div class="filter-info">
                    当前显示: <span id="currentFilter">全部标的</span> | 
                    共 <span id="visibleCount">{total_hit}</span> 条
                </div>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="resetFilter()">
                        🔄 重置筛选
                    </button>
                    <button class="btn btn-primary" onclick="copyAllCodes()">
                        📋 复制全部代码
                    </button>
                </div>
            </div>
            
            <!-- 代码复制框 -->
            <div class="code-box" onclick="copyToClipboard(this.querySelector('.code-text').textContent)">
                <span class="code-text">{all_codes}</span>
                <span class="copy-hint">点击复制</span>
            </div>
            
            <!-- 数据表格 -->
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>状态</th>
                            <th>代码</th>
                            <th>现价</th>
                            <th>涨跌幅</th>
                            <th>概念板块</th>
                            <th>详情</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # 生成表格行
    for _, r in df_res.iterrows():
        stage = r.get('阶段', '')
        stage_class = stage.replace('🚀 ', '').replace('🧪 ', '').replace('🏖️ ', '')
        concepts = str(r.get('概念', '其他')).split(' / ')
        concept_html = "".join([f'<span class="concept-tag" onclick="filterByConcept(\'{c}\', event)">{c}</span>' for c in concepts])
        
        m = "sh" if "sh" in str(r.get('完整代码', '')).lower() else "sz"
        url = f"https://quote.eastmoney.com/concept/{m}{r['代码']}.html"
        
        # 涨跌幅样式
        change_val = str(r['涨跌幅']).replace('%', '')
        try:
            is_up = float(change_val) >= 0
        except:
            is_up = '-' not in str(r['涨跌幅'])
        change_class = "change-up" if is_up else "change-down"
        change_icon = "📈" if is_up else "📉"

        html_template += f"""
                        <tr class="stock-row" data-stage="{stage}" data-concepts="{r.get('概念','')}">
                            <td><span class="stage-badge badge-{stage_class}">{stage}</span></td>
                            <td><span class="stock-code">{r['代码']}</span></td>
                            <td><span class="price">¥{r['现价']}</span></td>
                            <td><span class="{change_class}">{change_icon} {r['涨跌幅']}</span></td>
                            <td><div class="concept-tags">{concept_html}</div></td>
                            <td>
                                <a href="{url}" target="_blank" class="detail-link" title="查看详情">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"></circle>
                                        <path d="m21 21-4.35-4.35"></path>
                                    </svg>
                                </a>
                            </td>
                        </tr>
"""

    html_template += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Toast 提示 -->
    <div class="toast" id="toast"></div>
    
    <script>
        let currentStageFilter = null;
        let currentConceptFilter = null;
        
        // 筛选阶段
        function filterByStage(stage) {
            currentStageFilter = stage;
            currentConceptFilter = null;
            
            // 更新卡片状态
            document.querySelectorAll('.stage-card').forEach(card => {
                card.classList.remove('active');
                if (card.dataset.stage === stage) {
                    card.classList.add('active');
                }
            });
            
            // 更新概念标签状态
            document.querySelectorAll('.concept-tag').forEach(tag => {
                tag.classList.remove('active');
            });
            
            // 筛选表格
            applyFilters();
            
            // 更新显示信息
            document.getElementById('currentFilter').textContent = stage;
        }
        
        // 筛选概念
        function filterByConcept(concept, event) {
            if (event) event.stopPropagation();
            
            currentConceptFilter = concept;
            
            // 更新概念标签状态
            document.querySelectorAll('.concept-tag').forEach(tag => {
                tag.classList.remove('active');
                if (tag.textContent === concept) {
                    tag.classList.add('active');
                }
            });
            
            // 更新阶段卡片状态
            document.querySelectorAll('.stage-card').forEach(card => {
                card.classList.remove('active');
            });
            
            // 筛选表格
            applyFilters();
            
            // 更新显示信息
            document.getElementById('currentFilter').textContent = `概念: ${concept}`;
        }
        
        // 应用筛选
        function applyFilters() {
            const rows = document.querySelectorAll('.stock-row');
            let visibleCount = 0;
            
            rows.forEach(row => {
                let show = true;
                
                if (currentStageFilter && row.dataset.stage !== currentStageFilter) {
                    show = false;
                }
                
                if (currentConceptFilter && !row.dataset.concepts.includes(currentConceptFilter)) {
                    show = false;
                }
                
                if (show) {
                    row.classList.remove('hidden');
                    visibleCount++;
                } else {
                    row.classList.add('hidden');
                }
            });
            
            document.getElementById('visibleCount').textContent = visibleCount;
        }
        
        // 重置筛选
        function resetFilter() {
            currentStageFilter = null;
            currentConceptFilter = null;
            
            document.querySelectorAll('.stage-card').forEach(card => {
                card.classList.remove('active');
            });
            
            document.querySelectorAll('.concept-tag').forEach(tag => {
                tag.classList.remove('active');
            });
            
            document.querySelectorAll('.stock-row').forEach(row => {
                row.classList.remove('hidden');
            });
            
            document.getElementById('currentFilter').textContent = '全部标的';
            document.getElementById('visibleCount').textContent = document.querySelectorAll('.stock-row').length;
        }
        
        // 复制到剪贴板
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('✅ 已复制到剪贴板');
            }).catch(() => {
                // 降级方案
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showToast('✅ 已复制到剪贴板');
            });
        }
        
        // 复制全部代码
        function copyAllCodes() {
            const visibleRows = document.querySelectorAll('.stock-row:not(.hidden)');
            const codes = Array.from(visibleRows).map(row => {
                return row.querySelector('.stock-code').textContent;
            }).join(',');
            
            if (codes) {
                copyToClipboard(codes);
            } else {
                showToast('⚠️ 没有可复制的代码');
            }
        }
        
        // 显示 Toast
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 可以在这里添加初始化逻辑
        });
    </script>
</body>
</html>"""

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    # 跨平台自动打开报告
    abs_path = os.path.abspath(html_file)
    if platform.system() == "Darwin":
        os.system(f'open "{abs_path}"')
    else:
        webbrowser.open(f"file://{abs_path}")