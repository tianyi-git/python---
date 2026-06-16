"""Pytest fixtures 和配置"""
import os
import pytest

# 设置测试环境
os.environ['FLASK_ENV'] = 'testing'

from app import create_app


@pytest.fixture
def app():
    """创建测试用 Flask 应用"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing-only-32bytes',
        'SECRET_KEY': 'test-secret-key-for-testing-only-also-32b',
    })
    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_token(client):
    """注册并返回有效 token"""
    resp = client.post('/auth/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123456',
    })
    data = resp.get_json()
    return data['data']['token']


@pytest.fixture
def auth_headers(auth_token):
    """带认证的请求头"""
    return {'Authorization': f'Bearer {auth_token}'}
