"""用户认证模块测试"""
import pytest


class TestAuth:
    """认证功能测试"""

    def test_register_success(self, client):
        """正常注册"""
        resp = client.post('/auth/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'pass1234',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['code'] == 201
        assert 'token' in data['data']
        assert data['data']['user']['username'] == 'newuser'

    def test_register_duplicate_username(self, client, auth_token):
        """重复用户名注册"""
        resp = client.post('/auth/api/auth/register', json={
            'username': 'testuser',  # 已在 fixture 中注册
            'email': 'another@test.com',
            'password': 'pass1234',
        })
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        """密码过短"""
        resp = client.post('/auth/api/auth/register', json={
            'username': 'user1',
            'email': 'u1@test.com',
            'password': '123',
        })
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        """无效邮箱"""
        resp = client.post('/auth/api/auth/register', json={
            'username': 'user2',
            'email': 'invalid-email',
            'password': 'pass1234',
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        """正常登录"""
        # 先注册
        client.post('/auth/api/auth/register', json={
            'username': 'loginuser',
            'email': 'login@test.com',
            'password': 'mypassword',
        })
        # 再登录
        resp = client.post('/auth/api/auth/login', json={
            'username': 'loginuser',
            'password': 'mypassword',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data['data']

    def test_login_wrong_password(self, client):
        """密码错误"""
        resp = client.post('/auth/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        assert resp.status_code == 401

    def test_get_me(self, client, auth_headers):
        """获取当前用户信息"""
        resp = client.get('/auth/api/auth/me', headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['user']['username'] == 'testuser'

    def test_get_me_unauthorized(self, client):
        """未登录获取信息"""
        resp = client.get('/auth/api/auth/me')
        assert resp.status_code == 401

    def test_change_password(self, client, auth_headers):
        """修改密码"""
        resp = client.put('/auth/api/auth/password', json={
            'old_password': 'test123456',
            'new_password': 'newpass666',
        }, headers=auth_headers)
        assert resp.status_code == 200

    def test_change_password_wrong_old(self, client, auth_headers):
        """用错误旧密码修改"""
        resp = client.put('/auth/api/auth/password', json={
            'old_password': 'wrongold',
            'new_password': 'newpass666',
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_update_profile(self, client, auth_headers):
        """更新资料"""
        resp = client.put('/auth/api/auth/profile', json={
            'email': 'updated@test.com',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['user']['email'] == 'updated@test.com'

    def test_health_check(self, client):
        """健康检查"""
        resp = client.get('/health')
        assert resp.status_code == 200
        assert resp.get_json()['data']['status'] == 'healthy'
