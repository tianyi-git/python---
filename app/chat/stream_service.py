"""
流式对话服务
支持 Server-Sent Events (SSE) 流式输出 AI 回复
"""
import json
import logging
import time
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class StreamChatService:
    """流式对话服务 - 使用 Anthropic SDK 的原生 streaming"""

    @staticmethod
    def stream_chat(
        messages: list,
        api_key: str,
        system_prompt: Optional[str] = None,
        model: str = 'claude-sonnet-4-6',
    ) -> Generator[str, None, None]:
        """
        生成器函数：逐块产出 AI 回复文本（SSE 格式）

        Yields:
            SSE 格式的事件字符串
        """
        if not api_key:
            yield f'data: {json.dumps({"error": "未配置 ANTHROPIC_API_KEY"})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
            return

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            # 构建消息
            api_messages = []
            for m in messages:
                role = m.get('role', 'user')
                if role == 'system':
                    continue  # system 消息通过 system 参数传递
                api_messages.append({
                    'role': role,
                    'content': m.get('content', ''),
                })

            kwargs = {
                'model': model,
                'max_tokens': 4096,
                'messages': api_messages,
                'stream': True,
            }
            if system_prompt:
                kwargs['system'] = system_prompt

            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield f'data: {json.dumps({"text": text})}\n\n'

            # 完成信号
            yield f'data: {json.dumps({"done": True})}\n\n'

        except Exception as e:
            logger.error(f'流式对话异常: {e}')
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'


    @staticmethod
    def stream_chat_with_tools(
        messages: list,
        api_key: str,
        tools: list,
        system_prompt: Optional[str] = None,
        model: str = 'claude-sonnet-4-6',
    ) -> Generator[str, None, None]:
        """
        带工具调用的流式对话
        Claude 可以自主决定是否调用工具

        Yields:
            SSE 格式事件: {"text": "..."} | {"tool_call": {"name": "...", "input": {...}}} | {"done": True}
        """
        if not api_key:
            yield f'data: {json.dumps({"error": "未配置 ANTHROPIC_API_KEY"})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
            return

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            api_messages = []
            for m in messages:
                role = m.get('role', 'user')
                if role == 'system':
                    continue
                api_messages.append({
                    'role': role,
                    'content': m.get('content', ''),
                })

            kwargs = {
                'model': model,
                'max_tokens': 4096,
                'messages': api_messages,
                'tools': tools,
                'stream': True,
            }
            if system_prompt:
                kwargs['system'] = system_prompt

            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    # 检查是否是文本增量
                    if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                        if event.delta.text:
                            yield f'data: {json.dumps({"text": event.delta.text})}\n\n'

                    # 检查是否是工具调用
                    elif hasattr(event, 'content_block_start'):
                        block = event.content_block_start
                        if hasattr(block, 'content_block') and block.content_block.type == 'tool_use':
                            tool_info = {
                                'id': block.content_block.id,
                                'name': block.content_block.name,
                                'input': getattr(block.content_block, 'input', {}),
                            }
                            yield f'data: {json.dumps({"tool_call": tool_info})}\n\n'

            yield f'data: {json.dumps({"done": True})}\n\n'

        except Exception as e:
            logger.error(f'流式工具调用异常: {e}')
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
