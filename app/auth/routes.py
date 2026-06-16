"""
认证路由：登录、注册、登出、个人资料
"""
from flask import request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    get_jwt_identity,
)
from marshmallow import Schema, fields, ValidationError, validate

from app.auth import auth_bp
from app.auth.decorators import login_required_api, login_required_page, get_current_user
from app.extensions import db
from app.models.user import User


# ============================================================
# 参数校验 Schema
# ============================================================

class RegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=30))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6, max=100))


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class UpdateProfileSchema(Schema):
    email = fields.Email()
    avatar = fields.String(validate=validate.Length(max=500))


class ChangePasswordSchema(Schema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate.Length(min=6, max=100))


# ============================================================
# 页面路由
# ============================================================

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """登录页面"""
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET'])
def register_page():
    """注册页面"""
    return render_template('auth/register.html')


@auth_bp.route('/profile', methods=['GET'])
@login_required_page
def profile_page():
    """个人资料页面"""
    return render_template('profile.html')


# ============================================================
# API 路由
# ============================================================

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """用户注册 API"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None}), 400

    try:
        validated = RegisterSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=validated['username']).first():
        return jsonify({'code': 400, 'message': '用户名已被占用', 'data': None}), 400

    # 检查邮箱是否已存在
    if User.query.filter_by(email=validated['email']).first():
        return jsonify({'code': 400, 'message': '邮箱已被注册', 'data': None}), 400

    # 创建用户
    user = User(
        username=validated['username'],
        email=validated['email'],
    )
    user.set_password(validated['password'])

    db.session.add(user)
    db.session.commit()

    # 生成 JWT
    token = create_access_token(identity=str(user.id))
    response = jsonify({
        'code': 201,
        'message': '注册成功',
        'data': {'token': token, 'user': user.to_dict()},
    })
    response.status_code = 201
    set_access_cookies(response, token)
    return response


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """用户登录 API"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None}), 400

    try:
        validated = LoginSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    user = User.query.filter_by(username=validated['username']).first()
    if not user or not user.check_password(validated['password']):
        return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None}), 401

    token = create_access_token(identity=str(user.id))
    response = jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {'token': token, 'user': user.to_dict()},
    })
    set_access_cookies(response, token)
    return response


@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """登出"""
    response = jsonify({'code': 200, 'message': '已登出', 'data': None})
    unset_jwt_cookies(response)
    return response


@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required_api
def api_me():
    """获取当前用户信息"""
    user = get_current_user()
    if not user:
        return jsonify({'code': 401, 'message': '未登录', 'data': None}), 401
    return jsonify({
        'code': 200,
        'message': 'ok',
        'data': {'user': user.to_dict()},
    })


@auth_bp.route('/api/auth/profile', methods=['PUT'])
@login_required_api
def api_update_profile():
    """更新个人资料"""
    user = get_current_user()
    if not user:
        return jsonify({'code': 401, 'message': '未登录', 'data': None}), 401

    data = request.get_json(silent=True) or {}
    try:
        validated = UpdateProfileSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    if 'email' in validated and validated['email']:
        # 检查邮箱是否被其他人使用
        existing = User.query.filter_by(email=validated['email']).first()
        if existing and existing.id != user.id:
            return jsonify({'code': 400, 'message': '邮箱已被其他用户使用', 'data': None}), 400
        user.email = validated['email']

    if 'avatar' in validated:
        user.avatar = validated['avatar']

    db.session.commit()
    return jsonify({
        'code': 200,
        'message': '资料更新成功',
        'data': {'user': user.to_dict()},
    })


@auth_bp.route('/api/auth/password', methods=['PUT'])
@login_required_api
def api_change_password():
    """修改密码"""
    user = get_current_user()
    if not user:
        return jsonify({'code': 401, 'message': '未登录', 'data': None}), 401

    data = request.get_json(silent=True) or {}
    try:
        validated = ChangePasswordSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    if not user.check_password(validated['old_password']):
        return jsonify({'code': 400, 'message': '原密码不正确', 'data': None}), 400

    user.set_password(validated['new_password'])
    db.session.commit()

    return jsonify({'code': 200, 'message': '密码修改成功', 'data': None})
