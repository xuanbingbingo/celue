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
from PIL import Image, ImageDraw, ImageFont

# ================= 配置与初始化 =================

# 缓存与日志文件名
CONCEPT_CACHE = "concept_cache.json"
STOCK_NAME_CACHE = "stock_name_cache.json"
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

def sync_concepts():
    """
    管理员专用：同步东方财富概念板块数据到本地缓存
    只需要在概念数据需要更新时运行
    """
    print("🔄 开始同步概念板块数据...")
    
    try:
        # 获取概念板块列表
        df_concepts = ak.stock_board_concept_name_em()
        logging.info(f"获取到 {len(df_concepts)} 个概念板块")
        
        concept_map = {}
        concept_list = df_concepts['板块名称'].tolist()[:100]  # 只取前100个热门概念
        
        for name in tqdm(concept_list, desc="同步题材中"):
            retry = 0
            max_retries = 3
            
            while retry < max_retries:
                try:
                    # 获取该概念板块的成分股
                    df_members = ak.stock_board_concept_cons_em(symbol=name)
                    
                    if not df_members.empty:
                        logging.info(f"板块 [{name}] 同步成功 | 样本: {df_members.iloc[0, :2].to_dict()}")
                        
                        # 提取股票代码并更新映射
                        for _, row in df_members.iterrows():
                            # 处理代码格式，支持 sh.600000 或 600000
                            code = str(row['代码'])
                            pure_code = code.split('.')[1] if '.' in code else code
                            
                            if pure_code not in concept_map:
                                concept_map[pure_code] = []
                            
                            # 最多保存3个概念，避免数据过大
                            if name not in concept_map[pure_code] and len(concept_map[pure_code]) < 3:
                                concept_map[pure_code].append(name)
                    break
                    
                except Exception as e:
                    retry += 1
                    logging.warning(f"板块 {name} 第 {retry} 次失败: {e}")
                    time.sleep(random.uniform(1, 3))
            else:
                logging.error(f"❌ 板块 {name} 彻底同步失败")
                
        # 保存到本地缓存
        cache_data = {
            'last_update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_concepts': len(concept_list),
            'data': concept_map
        }
        
        with open(CONCEPT_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 概念数据同步完成！共 {len(concept_map)} 只股票关联了概念")
        print(f"💾 数据已保存到: {CONCEPT_CACHE}")
        
    except Exception as e:
        logging.error(f"同步过程出错: {e}")
        print(f"❌ 同步失败: {e}")

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

def load_stock_name_map():
    """
    加载股票名称映射缓存
    """
    if not os.path.exists(STOCK_NAME_CACHE):
        return {}
    try:
        with open(STOCK_NAME_CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载股票名称缓存失败: {e}")
        return {}

# ================= 3. 股票代码图片生成模块 =================

def generate_strategy_snapshot_image(stock_codes, strategy_name='ma5'):
    """
    生成策略股票代码汇总快照图片（单张图片包含所有股票代码）
    参数:
        stock_codes: 股票代码列表
        strategy_name: 策略名称
    返回:
        生成的图片路径
    """
    if not stock_codes:
        return None
    
    # 设置图片尺寸和布局
    width = 1200
    padding = 60
    code_height = 50
    header_height = 100
    footer_height = 60
    
    # 计算每行显示的代码数量
    codes_per_row = 6
    rows = (len(stock_codes) + codes_per_row - 1) // codes_per_row
    
    # 计算总高度
    content_height = rows * code_height
    height = header_height + content_height + footer_height + padding * 2
    
    # 创建图片
    img = Image.new('RGB', (width, height), '#fafafa')
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_code = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_info = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font_title = ImageFont.load_default()
        font_code = ImageFont.load_default()
        font_info = ImageFont.load_default()
    
    # 绘制标题背景
    draw.rectangle([0, 0, width, header_height], fill='#1e40af')
    
    # 绘制标题
    title = f"策略: {strategy_name}"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 30), title, font=font_title, fill='white')
    
    # 绘制股票代码
    start_y = header_height + padding
    code_width = (width - padding * 2) // codes_per_row
    
    for i, code in enumerate(stock_codes):
        row = i // codes_per_row
        col = i % codes_per_row
        
        x = padding + col * code_width + 10
        y = start_y + row * code_height + 10
        
        # 绘制代码背景框
        box_coords = [x, y, x + code_width - 20, y + code_height - 10]
        draw.rectangle(box_coords, fill='white', outline='#d1d5db', width=1)
        
        # 绘制代码文字
        text_x = x + (code_width - 20) // 2
        text_y = y + (code_height - 10) // 2 - 8
        bbox = draw.textbbox((0, 0), code, font=font_code)
        text_width = bbox[2] - bbox[0]
        draw.text((text_x - text_width // 2, text_y), code, font=font_code, fill='#1f2937')
    
    # 绘制底部信息
    footer_y = height - footer_height + 20
    info_text = f"共 {len(stock_codes)} 只股票 | 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    bbox = draw.textbbox((0, 0), info_text, font=font_info)
    info_width = bbox[2] - bbox[0]
    draw.text(((width - info_width) // 2, footer_y), info_text, font=font_info, fill='#6b7280')
    
    # 保存图片
    image_path = f"./strategy_snapshot_{strategy_name}.png"
    img.save(image_path, 'PNG')
    
    return image_path

# ================= 4. 交互式报告生成模块 =================

def generate_report(results, total_scanned, strategy_name='ma5'):
    """
    生成使用React的HTML报告
    参数:
        results: 扫描结果列表
        total_scanned: 扫描总数
        strategy_name: 策略名称，用于文件名区分
    """
    if not results:
        print("💡 无结果，跳过报告。")
        return

    # 格式化数据为JSON
    formatted_results = []
    for r in sorted(results, key=lambda x: (x.get('阶段', ''), x.get('代码', ''))):
        formatted_results.append({
            'code': r.get('代码', ''),
            'name': r.get('名称', ''),
            'fullCode': r.get('完整代码', ''),
            'price': r.get('现价', 0),
            'change': r.get('涨跌幅', '0%'),
            'stage': r.get('阶段', ''),
            'concepts': r.get('概念', '未分类')
        })

    # 策略名称映射
    strategy_names = {
        'ma5': 'MA5均线支撑策略',
        'volume_breakout': '放量突破策略'
    }
    strategy_display_name = strategy_names.get(strategy_name, strategy_name)

    # 生成JSON数据
    data_json = json.dumps({
        'results': formatted_results,
        'strategyName': strategy_name,
        'strategyDisplayName': strategy_display_name,
        'totalScanned': total_scanned,
        'totalHit': len(formatted_results)
    }, ensure_ascii=False)

    # 生成文件名
    html_file = f"scanner_report_{strategy_name}.html"

    # 读取模板文件
    template_path = os.path.join(os.path.dirname(__file__), '..', 'report_template.html')
    if not os.path.exists(template_path):
        # 如果模板不存在，使用当前目录
        template_path = 'report_template.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 替换数据占位符
    html_content = template.replace('{{DATA_PLACEHOLDER}}', data_json)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 跨平台自动打开报告
    abs_path = os.path.abspath(html_file)
    if platform.system() == "Darwin":
        os.system(f'open "{abs_path}"')
    else:
        webbrowser.open(f"file://{abs_path}")
    
    print(f"✅ 报告已生成: {html_file}")
