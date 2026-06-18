"""
流式对话服务
支持 Server-Sent Events (SSE) 流式输出 AI 回复
"""
import json
import logging
import time
import requests
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

            # index -> tool_use_id 映射（SDK 用 index 标识内容块位置）
            index_to_tool_id = {}
            tool_input_acc = {}  # tool_use.id -> input_json_str
            tool_meta = {}       # tool_use.id -> {name, id}

            with client.messages.stream(**kwargs) as stream:
                for event in stream:
                    event_type = getattr(event, 'type', None)

                    # ---- 文本增量 ----
                    if event_type == 'content_block_delta':
                        delta = event.delta
                        if delta.type == 'text_delta' and delta.text:
                            yield f'data: {json.dumps({"text": delta.text})}\n\n'
                        elif delta.type == 'input_json_delta':
                            # 通过 index 找到对应的 tool_use_id
                            tid = index_to_tool_id.get(event.index)
                            if tid and tid in tool_input_acc:
                                tool_input_acc[tid] += delta.partial_json or ''

                    # ---- 内容块开始：记录工具元信息 ----
                    elif event_type == 'content_block_start':
                        cb = event.content_block
                        if cb.type == 'tool_use':
                            tool_meta[cb.id] = {'id': cb.id, 'name': cb.name}
                            tool_input_acc[cb.id] = ''
                            index_to_tool_id[event.index] = cb.id

                    # ---- 内容块结束：工具调用 JSON 完整，输出 ----
                    elif event_type == 'content_block_stop':
                        tid = index_to_tool_id.get(event.index)
                        if tid and tid in tool_input_acc:
                            try:
                                parsed = json.loads(tool_input_acc[tid])
                            except json.JSONDecodeError:
                                parsed = tool_input_acc[tid]
                            meta = tool_meta.get(tid, {})
                            yield f'data: {json.dumps({"tool_call": {
                                "id": meta.get('id', tid),
                                "name": meta.get('name', tid),
                                "input": parsed,
                            }})}\n\n'

                    # ---- 消息结束 ----
                    elif event_type == 'message_stop':
                        break

            yield f'data: {json.dumps({"done": True})}\n\n'

        except Exception as e:
            logger.error(f'流式工具调用异常: {e}')
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'

    # ================================================================
    # DeepSeek 流式对话（OpenAI 兼容 SSE 协议）
    # ================================================================

    @staticmethod
    def stream_chat_deepseek(
        messages: list,
        api_key: str,
        system_prompt: Optional[str] = None,
        model: str = 'deepseek-chat',
    ) -> Generator[str, None, None]:
        """
        DeepSeek 流式对话 — 使用 OpenAI 兼容的 SSE 协议

        Yields:
            SSE 格式的事件字符串: {"text": "..."} | {"done": True} | {"error": "..."}
        """
        if not api_key:
            yield f'data: {json.dumps({"error": "未配置 DEEPSEEK_API_KEY"})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
            return

        # 构建消息列表
        api_messages = []
        if system_prompt and system_prompt.strip():
            api_messages.append({'role': 'system', 'content': system_prompt.strip()})
        for m in messages:
            role = m.get('role', 'user')
            if role == 'system':
                continue
            api_messages.append({
                'role': role,
                'content': m.get('content', ''),
            })

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': api_messages,
            'temperature': 0.7,
            'max_tokens': 4096,
            'stream': True,
        }

        try:
            resp = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=120,
                stream=True,
            )

            if resp.status_code != 200:
                error_text = resp.text[:300]
                logger.error(f'DeepSeek 流式请求失败: {resp.status_code} {error_text}')
                yield f'data: {json.dumps({"error": f"API 错误 ({resp.status_code}): {error_text}"})}\n\n'
                yield f'data: {json.dumps({"done": True})}\n\n'
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # DeepSeek SSE 格式: "data: {...}" 或 "data: [DONE]"
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get('choices', [])
                        if choices:
                            delta = choices[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield f'data: {json.dumps({"text": content})}\n\n'
                    except json.JSONDecodeError:
                        continue

            yield f'data: {json.dumps({"done": True})}\n\n'

        except requests.exceptions.Timeout:
            logger.error('DeepSeek 流式请求超时')
            yield f'data: {json.dumps({"error": "请求超时，请稍后重试"})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
        except Exception as e:
            logger.error(f'DeepSeek 流式对话异常: {e}')
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
            yield f'data: {json.dumps({"done": True})}\n\n'
