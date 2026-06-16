"""
LangChain Agent 工具集
让 AI 在对话中可以调用计算器、天气查询等工具
"""
import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入 LangChain，如果版本不兼容则回退到自定义实现
try:
    from langchain_core.tools import tool
    USE_LANGCHAIN = True
except ImportError:
    USE_LANGCHAIN = False


# ================================================================
# 工具定义
# ================================================================

def calculator_tool(expression: str) -> str:
    """安全计算数学表达式。输入如 '(100+50)*2-30'，返回计算结果。"""
    import re
    allowed = re.compile(r'^[\d\s\+\-\*\/\(\)\.\,\%eE]+$')
    expr = expression.replace('×', '*').replace('÷', '/').replace('^', '**')
    if not allowed.match(expr):
        return f'错误: 表达式包含不允许的字符，仅支持数字和 + - * / ( ) 等运算符'
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return f'计算结果: {expression} = {result}'
    except ZeroDivisionError:
        return '错误: 除数不能为零'
    except Exception as e:
        return f'计算错误: {str(e)}'


def weather_tool(city: str) -> str:
    """查询指定城市的实时天气。输入如 'Beijing' 或 '北京'。"""
    api_key = os.getenv('WEATHER_API_KEY', '')
    if not api_key:
        return '未配置天气 API Key（WEATHER_API_KEY 环境变量）。'

    try:
        resp = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'q': city, 'appid': api_key, 'units': 'metric', 'lang': 'zh_cn'},
            timeout=10,
        )
        if resp.status_code == 200:
            d = resp.json()
            return (
                f'{d["name"]} 当前天气：{d["weather"][0]["description"]}，'
                f'温度 {d["main"]["temp"]:.1f}°C（体感 {d["main"]["feels_like"]:.1f}°C），'
                f'湿度 {d["main"]["humidity"]}%，风速 {d["wind"]["speed"]} m/s。'
                f'最高温 {d["main"]["temp_max"]:.1f}°C，最低温 {d["main"]["temp_min"]:.1f}°C。'
            )
        elif resp.status_code == 404:
            return f'未找到城市 "{city}" 的天气信息。'
        else:
            return f'天气查询失败（状态码: {resp.status_code}）。'
    except Exception as e:
        return f'天气查询异常: {str(e)}'


def time_tool(_: str = '') -> str:
    """获取当前日期和时间。"""
    from datetime import datetime
    now = datetime.now()
    return f'当前时间: {now.strftime("%Y年%m月%d日 %H:%M:%S")}，星期{["一","二","三","四","五","六","日"][now.weekday()]}'


def text_tool_for_ai(text: str) -> str:
    """对文本进行统计，返回字数、单词数和行数。"""
    return (
        f'文本统计结果：总字符数 {len(text)}，'
        f'不含空格 {len(text.replace(" ", "").replace(chr(10), ""))}，'
        f'单词数 {len(text.split())}，'
        f'行数 {len(text.splitlines())}。'
    )


# ================================================================
# 工具注册表
# ================================================================

TOOLS_REGISTRY = {
    'calculator': {
        'name': 'calculator',
        'description': '计算数学表达式。输入示例: "(100+50)*2-30"。支持 + - * / ( ) 等运算符。',
        'function': calculator_tool,
    },
    'weather': {
        'name': 'weather',
        'description': '查询指定城市的实时天气。输入城市名（英文或中文），如 "Beijing" 或 "北京"。',
        'function': weather_tool,
    },
    'time': {
        'name': 'time',
        'description': '获取当前日期和时间。不需要参数。',
        'function': time_tool,
    },
    'text_stats': {
        'name': 'text_stats',
        'description': '对给定的文本进行统计分析，返回字符数、单词数、行数等。',
        'function': text_tool_for_ai,
    },
}


# ================================================================
# Anthropic Tool 格式转换（用于 Claude API）
# ================================================================

def get_anthropic_tools() -> list:
    """将工具注册表转换为 Anthropic/Claude API 的 tool 格式"""
    tools = []
    for t in TOOLS_REGISTRY.values():
        # 根据函数构造 input_schema
        if t['name'] == 'calculator':
            input_schema = {
                'type': 'object',
                'properties': {
                    'expression': {
                        'type': 'string',
                        'description': '要计算的数学表达式，如 "(100+50)*2-30"',
                    },
                },
                'required': ['expression'],
            }
        elif t['name'] == 'weather':
            input_schema = {
                'type': 'object',
                'properties': {
                    'city': {
                        'type': 'string',
                        'description': '城市名称，如 "Beijing" 或 "北京"',
                    },
                },
                'required': ['city'],
            }
        elif t['name'] == 'time':
            input_schema = {
                'type': 'object',
                'properties': {
                    '_': {
                        'type': 'string',
                        'description': '不需要参数，传空字符串即可',
                    },
                },
            }
        elif t['name'] == 'text_stats':
            input_schema = {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                        'description': '要统计分析的文本内容',
                    },
                },
                'required': ['text'],
            }
        else:
            continue

        tools.append({
            'name': t['name'],
            'description': t['description'],
            'input_schema': input_schema,
        })

    return tools


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """执行指定工具并返回结果"""
    if tool_name not in TOOLS_REGISTRY:
        return f'错误: 未知工具 "{tool_name}"'

    func = TOOLS_REGISTRY[tool_name]['function']
    try:
        if tool_name == 'calculator':
            return func(tool_input.get('expression', ''))
        elif tool_name == 'weather':
            return func(tool_input.get('city', ''))
        elif tool_name == 'time':
            return func('')
        elif tool_name == 'text_stats':
            return func(tool_input.get('text', ''))
        else:
            return func(tool_input)
    except Exception as e:
        return f'工具执行错误: {str(e)}'
