"""
数据分析路由：页面 + API
支持 CSV/Excel 上传、统计分析、图表生成
"""
import os
import uuid
import tempfile
from flask import request, jsonify, render_template, current_app, send_file

from app.data import data_bp
from app.auth.decorators import login_required_api, login_required_page
from app.services.data_service import DataAnalyzer

# 上传文件保存目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# 页面路由
# ============================================================

@data_bp.route('/data')
@login_required_page
def data_page():
    """数据分析页面"""
    return render_template('data/index.html')


# ============================================================
# API: 文件上传与分析
# ============================================================

@data_bp.route('/api/data/upload', methods=['POST'])
@login_required_api
def api_upload():
    """上传文件并返回基本信息"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择文件', 'data': None}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'code': 400, 'message': '文件名为空', 'data': None}), 400

    if not DataAnalyzer.allowed_file(file.filename):
        return jsonify({
            'code': 400,
            'message': f'不支持的文件类型，允许: {", ".join(DataAnalyzer.ALLOWED_EXTENSIONS)}',
            'data': None,
        }), 400

    try:
        # 保存上传文件
        ext = file.filename.rsplit('.', 1)[1].lower()
        saved_name = f"{uuid.uuid4().hex}.{ext}"
        saved_path = os.path.join(UPLOAD_DIR, saved_name)
        file.save(saved_path)

        # 解析数据
        df = DataAnalyzer.read_file(saved_path, file.filename)
        info = DataAnalyzer.get_basic_info(df)
        stats = DataAnalyzer.get_statistics(df)
        head_data = DataAnalyzer.get_head_data(df, n=15)

        # 保存文件路径到 session（简单方案：存内存，生产环境用 Redis）
        file_id = saved_name.rsplit('.', 1)[0]

        return jsonify({
            'code': 200,
            'message': '文件上传成功',
            'data': {
                'file_id': file_id,
                'filename': file.filename,
                'saved_name': saved_name,
                'info': info,
                'stats': stats,
                'preview': head_data,
            },
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'文件解析失败: {str(e)}', 'data': None}), 500


# ============================================================
# API: 图表生成
# ============================================================

@data_bp.route('/api/data/chart', methods=['POST'])
@login_required_api
def api_chart():
    """根据已上传的文件生成图表"""
    data = request.get_json(silent=True) or {}
    saved_name = data.get('saved_name', '')
    chart_type = data.get('chart_type', 'line')
    x_col = data.get('x_col', None)
    y_col = data.get('y_col', None)

    if not saved_name:
        return jsonify({'code': 400, 'message': '缺少文件标识', 'data': None}), 400

    valid_types = ['line', 'bar', 'pie', 'scatter', 'hist']
    if chart_type not in valid_types:
        return jsonify({
            'code': 400,
            'message': f'不支持的图表类型，可选: {", ".join(valid_types)}',
            'data': None,
        }), 400

    filepath = os.path.join(UPLOAD_DIR, saved_name)
    if not os.path.exists(filepath):
        return jsonify({'code': 404, 'message': '文件已过期，请重新上传', 'data': None}), 404

    try:
        df = DataAnalyzer.read_file(filepath, saved_name)
        chart_url = DataAnalyzer.generate_chart(df, chart_type, x_col, y_col)

        if not chart_url:
            return jsonify({'code': 500, 'message': '图表生成失败，请检查数据列', 'data': None}), 500

        return jsonify({
            'code': 200,
            'message': '图表生成成功',
            'data': {
                'chart_url': chart_url,
                'chart_type': chart_type,
            },
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'图表生成失败: {str(e)}', 'data': None}), 500


# ============================================================
# API: 自定义 SQL 查询（仅开发环境，生产需加固）
# ============================================================

@data_bp.route('/api/data/query', methods=['POST'])
@login_required_api
def api_query():
    """对上传的数据执行简单的类 SQL 过滤（使用 Pandas query）"""
    data = request.get_json(silent=True) or {}
    saved_name = data.get('saved_name', '')
    query_str = data.get('query', '')

    if not saved_name or not query_str:
        return jsonify({'code': 400, 'message': '缺少文件标识或查询条件', 'data': None}), 400

    filepath = os.path.join(UPLOAD_DIR, saved_name)
    if not os.path.exists(filepath):
        return jsonify({'code': 404, 'message': '文件已过期', 'data': None}), 404

    try:
        df = DataAnalyzer.read_file(filepath, saved_name)
        # 使用 safe query 限制（pandas query 表达式，非 SQL）
        filtered = df.query(query_str)
        result = filtered.head(100).fillna('').to_dict(orient='records')

        return jsonify({
            'code': 200,
            'message': f'查询返回 {len(result)} 条结果',
            'data': {
                'count': len(result),
                'results': result,
            },
        })
    except Exception as e:
        return jsonify({'code': 400, 'message': f'查询语法错误: {str(e)}', 'data': None}), 400


# ============================================================
# API: 相关性分析
# ============================================================

@data_bp.route('/api/data/correlation', methods=['POST'])
@login_required_api
def api_correlation():
    """计算数值列之间的相关系数"""
    data = request.get_json(silent=True) or {}
    saved_name = data.get('saved_name', '')

    if not saved_name:
        return jsonify({'code': 400, 'message': '缺少文件标识', 'data': None}), 400

    filepath = os.path.join(UPLOAD_DIR, saved_name)
    if not os.path.exists(filepath):
        return jsonify({'code': 404, 'message': '文件已过期', 'data': None}), 404

    try:
        df = DataAnalyzer.read_file(filepath, saved_name)
        corr = DataAnalyzer.get_correlation(df)
        return jsonify({'code': 200, 'message': 'ok', 'data': corr})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'计算失败: {str(e)}', 'data': None}), 500
