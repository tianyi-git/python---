"""工具模块测试"""
import pytest


class TestCalculator:
    """计算器测试"""

    def test_simple_add(self, client, auth_headers):
        resp = client.post('/tools/api/tools/calculator', json={
            'expression': '2 + 3',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['result'] == 5

    def test_complex_expr(self, client, auth_headers):
        resp = client.post('/tools/api/tools/calculator', json={
            'expression': '(100 + 50) * 2 - 30',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['result'] == 270

    def test_division(self, client, auth_headers):
        resp = client.post('/tools/api/tools/calculator', json={
            'expression': '100 / 3',
        }, headers=auth_headers)
        assert resp.status_code == 200
        result = resp.get_json()['data']['result']
        assert abs(result - 33.3333) < 0.01

    def test_empty_expression(self, client, auth_headers):
        resp = client.post('/tools/api/tools/calculator', json={
            'expression': '',
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_invalid_chars(self, client, auth_headers):
        resp = client.post('/tools/api/tools/calculator', json={
            'expression': '__import__("os")',
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestTextTools:
    """文本工具测试"""

    def test_count(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'count',
            'text': 'Hello World 你好',
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['words'] == 3

    def test_base64_encode(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'base64_encode',
            'text': 'Hello',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['result'] == 'SGVsbG8='

    def test_base64_decode(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'base64_decode',
            'text': 'SGVsbG8=',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['result'] == 'Hello'

    def test_md5(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'md5',
            'text': 'hello',
        }, headers=auth_headers)
        assert resp.get_json()['data']['result'] == '5d41402abc4b2a76b9719d911017c592'

    def test_reverse(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'reverse',
            'text': 'Hello',
        }, headers=auth_headers)
        assert resp.get_json()['data']['result'] == 'olleH'

    def test_empty_text(self, client, auth_headers):
        resp = client.post('/tools/api/tools/text', json={
            'action': 'count',
            'text': '',
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestJsonTool:
    """JSON 工具测试"""

    def test_format_valid_json(self, client, auth_headers):
        resp = client.post('/tools/api/tools/json', json={
            'json_str': '{"name":"test","value":123}',
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['data']['parsed'] == {'name': 'test', 'value': 123}

    def test_invalid_json(self, client, auth_headers):
        resp = client.post('/tools/api/tools/json', json={
            'json_str': '{invalid}',
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestAgentTools:
    """Agent 工具测试"""

    def test_execute_calculator(self, client, auth_headers):
        resp = client.post('/api/chat/tool-call', json={
            'tool_name': 'calculator',
            'input': {'expression': '2+2'},
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert '4' in resp.get_json()['data']['result']

    def test_execute_time(self, client, auth_headers):
        resp = client.post('/api/chat/tool-call', json={
            'tool_name': 'time',
            'input': {},
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert '当前时间' in resp.get_json()['data']['result']

    def test_execute_unknown_tool(self, client, auth_headers):
        resp = client.post('/api/chat/tool-call', json={
            'tool_name': 'unknown_tool',
            'input': {},
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert '未知工具' in resp.get_json()['data']['result']
