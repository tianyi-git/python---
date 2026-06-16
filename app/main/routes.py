"""主路由：首页、健康检查"""
from flask import render_template, redirect, url_for, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.main import main_bp


@main_bp.route('/')
def index():
    """首页 - 已登录跳转对话页，否则跳转登录页"""
    try:
        verify_jwt_in_request(optional=True)
        if get_jwt_identity():
            return redirect(url_for('chat.chat_page'))
    except Exception:
        pass
    return redirect(url_for('auth.login_page'))


@main_bp.route('/health')
def health():
    """健康检查接口"""
    return jsonify({
        'code': 200,
        'message': '服务运行正常',
        'data': {'status': 'healthy'},
    })
