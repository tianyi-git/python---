"""
工具集：计算器、编码转换、文本处理等
"""
import json
import base64
import hashlib
import re
from typing import Any


def safe_eval(expression: str) -> dict:
    """
    安全的表达式求值（仅支持数学运算）
    """
    # 白名单：只允许数字、运算符、括号、空格、小数点
    allowed = re.compile(r'^[\d\s\+\-\*\/\(\)\.\,\%eE]+$')
    if not allowed.match(expression):
        return {'success': False, 'error': '表达式包含不允许的字符'}

    # 替换一些友好写法
    expr = expression.replace('×', '*').replace('÷', '/').replace('^', '**')

    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return {'success': True, 'data': {'expression': expression, 'result': result}}
    except ZeroDivisionError:
        return {'success': False, 'error': '除数不能为零'}
    except Exception as e:
        return {'success': False, 'error': f'计算错误: {str(e)}'}


def text_tools(action: str, text: str) -> dict:
    """
    文本处理工具

    action:
        - 'count': 字数统计
        - 'base64_encode': Base64 编码
        - 'base64_decode': Base64 解码
        - 'md5': MD5 哈希
        - 'sha256': SHA256 哈希
        - 'reverse': 反转文本
        - 'upper': 转大写
        - 'lower': 转小写
    """
    if action == 'count':
        return {
            'success': True,
            'data': {
                'chars': len(text),
                'chars_no_space': len(text.replace(' ', '').replace('\n', '')),
                'words': len(text.split()),
                'lines': len(text.splitlines()) if text else 0,
            },
        }

    elif action == 'base64_encode':
        encoded = base64.b64encode(text.encode()).decode()
        return {'success': True, 'data': {'result': encoded}}

    elif action == 'base64_decode':
        try:
            decoded = base64.b64decode(text.encode()).decode()
            return {'success': True, 'data': {'result': decoded}}
        except Exception:
            return {'success': False, 'error': 'Base64 解码失败，请检查输入'}

    elif action == 'md5':
        return {'success': True, 'data': {'result': hashlib.md5(text.encode()).hexdigest()}}

    elif action == 'sha256':
        return {'success': True, 'data': {'result': hashlib.sha256(text.encode()).hexdigest()}}

    elif action == 'reverse':
        return {'success': True, 'data': {'result': text[::-1]}}

    elif action == 'upper':
        return {'success': True, 'data': {'result': text.upper()}}

    elif action == 'lower':
        return {'success': True, 'data': {'result': text.lower()}}

    else:
        return {'success': False, 'error': f'不支持的操作: {action}'}


def json_formatter(json_str: str) -> dict:
    """
    JSON 格式化/验证工具
    """
    try:
        parsed = json.loads(json_str)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        return {'success': True, 'data': {'parsed': parsed, 'formatted': formatted}}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': f'JSON 格式错误: {str(e)}'}
