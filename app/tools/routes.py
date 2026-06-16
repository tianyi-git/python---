"""
工具扩展路由：页面 + API
天气查询、计算器、文本处理、JSON 格式化等
"""
from flask import request, jsonify, render_template

from app.tools import tools_bp
from app.tools.weather import WeatherTool
from app.tools.calculator import safe_eval, text_tools, json_formatter
from app.tools.email_tool import EmailTool
from app.auth.decorators import login_required_api, login_required_page


# ============================================================
# 页面路由
# ============================================================

@tools_bp.route('/')
@login_required_page
def tools_page():
    """工具集页面"""
    return render_template('tools/index.html')


# ============================================================
# API: 天气查询
# ============================================================

@tools_bp.route('/api/tools/weather', methods=['POST'])
@login_required_api
def api_weather():
    """查询指定城市的天气"""
    data = request.get_json(silent=True) or {}
    city = data.get('city', '').strip()

    if not city:
        return jsonify({'code': 400, 'message': '请输入城市名称', 'data': None}), 400

    result = WeatherTool.query(city)
    if result['success']:
        return jsonify({'code': 200, 'message': '查询成功', 'data': result['data']})
    else:
        return jsonify({'code': 500, 'message': result['error'], 'data': None}), 500


# ============================================================
# API: 计算器
# ============================================================

@tools_bp.route('/api/tools/calculator', methods=['POST'])
@login_required_api
def api_calculator():
    """安全表达式求值"""
    data = request.get_json(silent=True) or {}
    expression = data.get('expression', '').strip()

    if not expression:
        return jsonify({'code': 400, 'message': '请输入计算表达式', 'data': None}), 400

    result = safe_eval(expression)
    if result['success']:
        return jsonify({'code': 200, 'message': '计算成功', 'data': result['data']})
    else:
        return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400


# ============================================================
# API: 文本处理
# ============================================================

@tools_bp.route('/api/tools/text', methods=['POST'])
@login_required_api
def api_text_tools():
    """文本处理（统计/编码/哈希等）"""
    data = request.get_json(silent=True) or {}
    action = data.get('action', '')
    text = data.get('text', '')

    if not action:
        return jsonify({'code': 400, 'message': '请选择处理类型', 'data': None}), 400
    if not text:
        return jsonify({'code': 400, 'message': '请输入文本内容', 'data': None}), 400

    result = text_tools(action, text)
    if result['success']:
        return jsonify({'code': 200, 'message': '处理成功', 'data': result['data']})
    else:
        return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400


# ============================================================
# API: JSON 格式化
# ============================================================

@tools_bp.route('/api/tools/json', methods=['POST'])
@login_required_api
def api_json_tool():
    """JSON 格式化/验证"""
    data = request.get_json(silent=True) or {}
    json_str = data.get('json_str', '').strip()

    if not json_str:
        return jsonify({'code': 400, 'message': '请输入 JSON 字符串', 'data': None}), 400

    result = json_formatter(json_str)
    if result['success']:
        return jsonify({'code': 200, 'message': '格式化成功', 'data': result['data']})
    else:
        return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400


# ============================================================
# API: 邮件发送
# ============================================================

@tools_bp.route('/api/tools/email', methods=['POST'])
@login_required_api
def api_email():
    """发送邮件"""
    data = request.get_json(silent=True) or {}
    to_email = data.get('to_email', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '')

    if not to_email:
        return jsonify({'code': 400, 'message': '请输入收件人邮箱', 'data': None}), 400
    if not subject:
        return jsonify({'code': 400, 'message': '请输入邮件主题', 'data': None}), 400
    if not body:
        return jsonify({'code': 400, 'message': '请输入邮件正文', 'data': None}), 400

    result = EmailTool.send(
        to_email=to_email,
        subject=subject,
        body=body,
        is_html=data.get('is_html', False),
    )

    if result['success']:
        return jsonify({'code': 200, 'message': result['message'], 'data': None})
    else:
        return jsonify({'code': 500, 'message': result['error'], 'data': None}), 500
