"""
全局错误处理器
API 路由（/api/ 前缀）返回 JSON，页面路由返回 HTML
"""
from flask import request, jsonify, render_template


def is_api_request():
    """判断当前请求是否为 API 请求"""
    return request.path.startswith('/api/')


def register_error_handlers(app):
    """注册所有错误处理器到 Flask 应用"""

    @app.errorhandler(400)
    def bad_request(error):
        if is_api_request():
            return jsonify({
                'code': 400,
                'message': '请求参数有误',
                'data': None
            }), 400
        return render_template('base.html', error='请求参数有误'), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if is_api_request():
            return jsonify({
                'code': 401,
                'message': '未登录或令牌已过期',
                'data': None
            }), 401
        from flask import redirect, url_for
        return redirect(url_for('auth.login_page'))

    @app.errorhandler(403)
    def forbidden(error):
        if is_api_request():
            return jsonify({
                'code': 403,
                'message': '无此操作权限',
                'data': None
            }), 403
        return render_template('base.html', error='无此操作权限'), 403

    @app.errorhandler(404)
    def not_found(error):
        if is_api_request():
            return jsonify({
                'code': 404,
                'message': '请求的资源不存在',
                'data': None
            }), 404
        return render_template('base.html', error='页面不存在'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if is_api_request():
            return jsonify({
                'code': 500,
                'message': '服务器内部错误',
                'data': None
            }), 500
        return render_template('base.html', error='服务器内部错误，请稍后重试'), 500
