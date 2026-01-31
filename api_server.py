"""
股票扫描API服务
提供RESTful API供前端调用
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_tools import load_concept_map, load_stock_name_map
from strategies import ma5_support, volume_breakout
from index import process_file, DATA_DIR
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

app = Flask(__name__)
CORS(app)  # 允许跨域

# 策略映射
STRATEGY_MAP = {
    'ma5': {
        'name': 'ma5',
        'func': ma5_support.analyze,
        'description': 'MA5均线支撑策略'
    },
    'volume_breakout': {
        'name': 'volume_breakout',
        'func': volume_breakout.analyze,
        'description': '放量突破策略（吸筹→启动，无整理期）'
    }
}


@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """获取可用策略列表"""
    return jsonify({
        'success': True,
        'data': [
            {'id': k, 'name': v['name'], 'description': v['description']}
            for k, v in STRATEGY_MAP.items()
        ]
    })


@app.route('/api/scan/<strategy_name>', methods=['GET'])
def scan_strategy(strategy_name):
    """
    执行策略扫描
    参数:
        strategy_name: 策略名称 (ma5 或 volume_breakout)
    """
    strategy_config = STRATEGY_MAP.get(strategy_name)
    if not strategy_config:
        return jsonify({
            'success': False,
            'error': f'找不到策略: {strategy_name}'
        }), 404

    analyze_func = strategy_config['func']
    strategy_desc = strategy_config['description']

    # 加载概念和股票名称映射
    concept_map = load_concept_map()
    stock_name_map = load_stock_name_map()

    # 检查数据目录
    if not os.path.exists(DATA_DIR):
        return jsonify({
            'success': False,
            'error': f'数据目录 {DATA_DIR} 不存在'
        }), 500

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    # 执行扫描
    results = []
    with ThreadPoolExecutor(max_workers=40) as executor:
        futures = [executor.submit(process_file, f, concept_map, stock_name_map, analyze_func) for f in files]
        for f in tqdm(as_completed(futures), total=len(futures), desc=f"执行扫描-{strategy_name}"):
            res = f.result()
            if res:
                results.append(res)

    # 格式化结果
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

    return jsonify({
        'success': True,
        'data': {
            'strategyName': strategy_name,
            'strategyDisplayName': strategy_desc,
            'totalScanned': len(files),
            'totalHit': len(formatted_results),
            'results': formatted_results
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'ok',
        'dataDir': os.path.exists(DATA_DIR),
        'stockCount': len([f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]) if os.path.exists(DATA_DIR) else 0
    })


if __name__ == '__main__':
    print("🚀 启动股票扫描API服务...")
    print("📍 API地址: http://localhost:5000")
    print("📚 可用接口:")
    print("   GET /api/health          - 健康检查")
    print("   GET /api/strategies      - 获取策略列表")
    print("   GET /api/scan/<strategy> - 执行扫描 (ma5, volume_breakout)")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)
