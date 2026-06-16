"""对话模块测试"""
import pytest


class TestChatSessions:
    """会话管理测试"""

    def test_create_session(self, client, auth_headers):
        """创建新会话"""
        resp = client.post('/api/chat/sessions', json={
            'title': '测试会话',
            'model_name': 'claude',
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['data']['session']['title'] == '测试会话'

    def test_list_sessions(self, client, auth_headers):
        """获取会话列表"""
        # 先创建
        client.post('/api/chat/sessions', json={'title': 'S1'}, headers=auth_headers)
        client.post('/api/chat/sessions', json={'title': 'S2'}, headers=auth_headers)

        resp = client.get('/api/chat/sessions', headers=auth_headers)
        assert resp.status_code == 200
        sessions = resp.get_json()['data']['sessions']
        assert len(sessions) >= 2

    def test_get_session(self, client, auth_headers):
        """获取单个会话"""
        create_resp = client.post('/api/chat/sessions', json={
            'title': '详情测试',
        }, headers=auth_headers)
        session_id = create_resp.get_json()['data']['session']['id']

        resp = client.get(f'/api/chat/sessions/{session_id}', headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['session']['title'] == '详情测试'

    def test_get_nonexistent_session(self, client, auth_headers):
        """获取不存在的会话"""
        resp = client.get('/api/chat/sessions/99999', headers=auth_headers)
        assert resp.status_code == 404

    def test_update_session(self, client, auth_headers):
        """更新会话标题"""
        create_resp = client.post('/api/chat/sessions', json={
            'title': '旧标题',
        }, headers=auth_headers)
        session_id = create_resp.get_json()['data']['session']['id']

        resp = client.put(f'/api/chat/sessions/{session_id}', json={
            'title': '新标题',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['session']['title'] == '新标题'

    def test_delete_session(self, client, auth_headers):
        """删除会话"""
        create_resp = client.post('/api/chat/sessions', json={
            'title': '待删除',
        }, headers=auth_headers)
        session_id = create_resp.get_json()['data']['session']['id']

        resp = client.delete(f'/api/chat/sessions/{session_id}', headers=auth_headers)
        assert resp.status_code == 200

        # 再次获取应返回 404
        resp2 = client.get(f'/api/chat/sessions/{session_id}', headers=auth_headers)
        assert resp2.status_code == 404

    def test_unauthorized_access(self, client):
        """未认证访问"""
        resp = client.get('/api/chat/sessions')
        assert resp.status_code == 401

    def test_list_models(self, client, auth_headers):
        """获取可用模型列表"""
        resp = client.get('/api/chat/models', headers=auth_headers)
        assert resp.status_code == 200
        models = resp.get_json()['data']['models']
        assert len(models) >= 2  # Claude + DeepSeek

    def test_list_tools(self, client, auth_headers):
        """获取可用工具列表"""
        resp = client.get('/api/chat/tools', headers=auth_headers)
        assert resp.status_code == 200
        tools = resp.get_json()['data']['tools']
        assert len(tools) >= 3  # calculator, weather, time, text_stats
        tool_names = [t['name'] for t in tools]
        assert 'calculator' in tool_names
        assert 'weather' in tool_names
