"""
多模型 LLM 服务层
统一抽象 Claude（langchain-anthropic）和 DeepSeek（OpenAI 兼容 API）
支持自动重试、错误处理
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMService:
    """大模型调度服务，支持多模型切换与自动回退"""

    # 可用模型配置
    AVAILABLE_MODELS = {
        'claude': {
            'name': 'Claude (Anthropic)',
            'provider': 'anthropic',
            'requires_key': 'ANTHROPIC_API_KEY',
        },
        'deepseek': {
            'name': 'DeepSeek',
            'provider': 'deepseek',
            'requires_key': 'DEEPSEEK_API_KEY',
        },
    }

    MAX_RETRIES = 3
    RETRY_DELAY = 1.5  # 重试间隔（秒）

    def __init__(self, app_config: dict):
        self.config = app_config
        self._claude_model = None
        self._claude_available = bool(app_config.get('ANTHROPIC_API_KEY'))

    # ================================================================
    # Claude (langchain-anthropic)
    # ================================================================

    def _get_claude_model(self):
        """延迟初始化 Claude 模型实例"""
        if self._claude_model is not None:
            return self._claude_model

        api_key = self.config.get('ANTHROPIC_API_KEY', '')
        if not api_key or api_key == 'sk-ant-your-key-here':
            self._claude_available = False
            return None

        try:
            from langchain_anthropic import ChatAnthropic
            self._claude_model = ChatAnthropic(
                model='claude-sonnet-4-6',
                api_key=api_key,
                temperature=0.7,
                max_tokens=4096,
            )
            self._claude_available = True
            logger.info('Claude 模型初始化成功')
        except Exception as e:
            logger.warning(f'Claude 模型初始化失败: {e}')
            self._claude_available = False
            self._claude_model = None

        return self._claude_model

    # ================================================================
    # DeepSeek (OpenAI 兼容 API)
    # ================================================================

    def _call_deepseek(self, messages: list) -> Optional[str]:
        """通过 OpenAI 兼容 API 调用 DeepSeek"""
        api_key = self.config.get('DEEPSEEK_API_KEY', '')
        if not api_key or api_key == 'your-deepseek-key-here':
            return None

        import requests
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 4096,
        }

        try:
            resp = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content']
            else:
                logger.warning(f'DeepSeek API 返回错误: {resp.status_code} {resp.text[:200]}')
                return None
        except Exception as e:
            logger.warning(f'DeepSeek API 调用异常: {e}')
            return None

    # ================================================================
    # 统一对话接口
    # ================================================================

    def chat(
        self,
        messages: list,
        model_name: str = 'claude',
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        发送消息到指定模型

        参数:
            messages: [{'role': 'user'|'assistant', 'content': '...'}, ...]
            model_name: 'claude' | 'deepseek'
            system_prompt: 可选的系统提示词

        返回:
            {'success': True, 'reply': '...', 'model': 'claude'}
            或
            {'success': False, 'error': '...', 'model': '...'}
        """
        # 构建完整消息列表（含 system prompt）
        full_messages = []
        if system_prompt and system_prompt.strip():
            full_messages.append({'role': 'system', 'content': system_prompt.strip()})
        full_messages.extend(messages)

        # 尝试首选模型
        if model_name == 'claude':
            result = self._retry_call(
                lambda: self._call_claude(full_messages),
                'claude',
            )
            if result['success']:
                return result
            # Claude 失败，尝试 DeepSeek
            logger.info('Claude 调用失败，尝试回退到 DeepSeek')
            fallback = self._retry_call(
                lambda: self._call_deepseek(full_messages),
                'deepseek',
            )
            if fallback['success']:
                fallback['model'] = 'deepseek (fallback)'
                return fallback
            return result  # 返回原始错误

        elif model_name == 'deepseek':
            result = self._retry_call(
                lambda: self._call_deepseek(full_messages),
                'deepseek',
            )
            if result['success']:
                return result
            # DeepSeek 失败，尝试 Claude
            logger.info('DeepSeek 调用失败，尝试回退到 Claude')
            fallback = self._retry_call(
                lambda: self._call_claude(full_messages),
                'claude',
            )
            if fallback['success']:
                fallback['model'] = 'claude (fallback)'
                return fallback
            return result

        else:
            return {'success': False, 'error': f'不支持的模型: {model_name}', 'model': model_name}

    def _call_claude(self, messages: list) -> Optional[str]:
        """调用 Claude 模型"""
        model = self._get_claude_model()
        if not model:
            return None
        # langchain-anthropic 直接接受消息列表
        response = model.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)

    def _retry_call(self, call_fn, model_name: str) -> dict:
        """带重试的调用包装"""
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                reply = call_fn()
                if reply:
                    return {
                        'success': True,
                        'reply': reply,
                        'model': model_name,
                    }
            except Exception as e:
                last_error = str(e)
                logger.warning(f'{model_name} 第 {attempt} 次调用失败: {last_error}')

            if attempt < self.MAX_RETRIES:
                time.sleep(self.RETRY_DELAY * attempt)

        return {
            'success': False,
            'error': last_error or '所有重试均失败',
            'model': model_name,
        }

    def get_available_models(self) -> list:
        """返回当前可用的模型列表"""
        models = []
        if self._claude_available or self._get_claude_model():
            models.append({
                'id': 'claude',
                'name': 'Claude (Anthropic)',
                'available': True,
            })
        else:
            models.append({
                'id': 'claude',
                'name': 'Claude (Anthropic)',
                'available': False,
                'hint': '请设置 ANTHROPIC_API_KEY 环境变量',
            })

        deepseek_key = self.config.get('DEEPSEEK_API_KEY', '')
        deepseek_ok = bool(deepseek_key and deepseek_key != 'your-deepseek-key-here')
        models.append({
            'id': 'deepseek',
            'name': 'DeepSeek',
            'available': deepseek_ok,
            'hint': '' if deepseek_ok else '请设置 DEEPSEEK_API_KEY 环境变量',
        })

        return models
