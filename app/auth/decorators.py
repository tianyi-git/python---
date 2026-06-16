"""
认证装饰器
"""
from functools import wraps
from flask import jsonify, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def login_required_api(f):
    """API 路由的登录验证：返回 JSON 错误"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception:
            return jsonify({
                'code': 401,
                'message': '未登录或令牌已过期',
                'data': None
            }), 401
    return decorated


def login_required_page(f):
    """页面路由的登录验证：重定向到登录页"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception:
            return redirect(url_for('auth.login_page'))
    return decorated


def admin_required(f):
    """管理员权限验证（需在 login_required 之后使用）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            from app.models.user import User
            from app.extensions import db
            user = db.session.get(User, int(user_id))
            if not user or user.role != 'admin':
                return jsonify({
                    'code': 403,
                    'message': '需要管理员权限',
                    'data': None
                }), 403
            return f(*args, **kwargs)
        except Exception:
            return jsonify({
                'code': 401,
                'message': '未登录或令牌已过期',
                'data': None
            }), 401
    return decorated


def get_current_user():
    """获取当前登录的用户对象（用于 API 路由内部）"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        from app.models.user import User
        from app.extensions import db
        return db.session.get(User, int(user_id))
    except Exception:
        return None
