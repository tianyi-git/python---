"""
对话路由：页面 + API（含流式输出和工具调用）
"""
import json
from flask import request, jsonify, render_template, current_app, Response, stream_with_context
from marshmallow import Schema, fields, ValidationError, validate

from app.chat import chat_bp
from app.chat.llm_service import LLMService
from app.chat.session_manager import SessionManager
from app.chat.stream_service import StreamChatService
from app.chat.agent_tools import get_anthropic_tools, execute_tool
from app.auth.decorators import login_required_api, login_required_page, get_current_user


# ============================================================
# 参数校验
# ============================================================

class SendMessageSchema(Schema):
    session_id = fields.Integer(required=False)
    message = fields.String(required=True, validate=validate.Length(min=1, max=10000))
    model = fields.String(required=False)


class CreateSessionSchema(Schema):
    title = fields.String(required=False)
    model_name = fields.String(required=False)
    system_prompt = fields.String(required=False)


class UpdateSessionSchema(Schema):
    title = fields.String()
    model_name = fields.String()
    system_prompt = fields.String()


# ============================================================
# 页面路由
# ============================================================

@chat_bp.route('/chat')
@login_required_page
def chat_page():
    """对话主页面 (SPA)"""
    return render_template('chat/index.html')


# ============================================================
# API: 模型列表
# ============================================================

@chat_bp.route('/api/chat/models', methods=['GET'])
@login_required_api
def api_models():
    """获取可用模型列表"""
    service = LLMService(current_app.config)
    models = service.get_available_models()
    return jsonify({'code': 200, 'message': 'ok', 'data': {'models': models}})


# ============================================================
# API: 会话管理
# ============================================================

@chat_bp.route('/api/chat/sessions', methods=['GET'])
@login_required_api
def api_list_sessions():
    """获取用户的所有会话"""
    user = get_current_user()
    sessions = SessionManager.get_user_sessions(user.id)
    return jsonify({
        'code': 200,
        'message': 'ok',
        'data': {'sessions': [s.to_dict() for s in sessions]},
    })


@chat_bp.route('/api/chat/sessions', methods=['POST'])
@login_required_api
def api_create_session():
    """创建新会话"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    try:
        validated = CreateSessionSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    session = SessionManager.create_session(
        user_id=user.id,
        title=validated.get('title', '新的对话'),
        model_name=validated.get('model_name', 'claude'),
        system_prompt=validated.get('system_prompt'),
    )
    return jsonify({
        'code': 201,
        'message': '会话创建成功',
        'data': {'session': session.to_dict()},
    }), 201


@chat_bp.route('/api/chat/sessions/<int:session_id>', methods=['GET'])
@login_required_api
def api_get_session(session_id):
    """获取会话详情（含消息列表）"""
    user = get_current_user()
    session = SessionManager.get_session(session_id, user.id)
    if not session:
        return jsonify({'code': 404, 'message': '会话不存在', 'data': None}), 404

    messages = SessionManager.get_messages(session_id)
    return jsonify({
        'code': 200,
        'message': 'ok',
        'data': {
            'session': session.to_dict(),
            'messages': [m.to_dict() for m in messages],
        },
    })


@chat_bp.route('/api/chat/sessions/<int:session_id>', methods=['PUT'])
@login_required_api
def api_update_session(session_id):
    """更新会话"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    try:
        validated = UpdateSessionSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    if not validated:
        return jsonify({'code': 400, 'message': '没有要更新的字段', 'data': None}), 400

    session = SessionManager.update_session(session_id, user.id, **validated)
    if not session:
        return jsonify({'code': 404, 'message': '会话不存在', 'data': None}), 404

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': {'session': session.to_dict()},
    })


@chat_bp.route('/api/chat/sessions/<int:session_id>', methods=['DELETE'])
@login_required_api
def api_delete_session(session_id):
    """删除会话"""
    user = get_current_user()
    ok = SessionManager.delete_session(session_id, user.id)
    if not ok:
        return jsonify({'code': 404, 'message': '会话不存在', 'data': None}), 404
    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


# ============================================================
# API: 发送消息
# ============================================================

@chat_bp.route('/api/chat/send', methods=['POST'])
@login_required_api
def api_send_message():
    """发送消息并获取 AI 回复"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    try:
        validated = SendMessageSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    # 获取或创建会话
    session_id = validated.get('session_id')
    if session_id:
        session = SessionManager.get_session(session_id, user.id)
        if not session:
            return jsonify({'code': 404, 'message': '会话不存在', 'data': None}), 404
    else:
        # 自动创建新会话，用首条消息前30字做标题
        title = SessionManager.auto_title(None, validated['message'])
        session = SessionManager.create_session(
            user_id=user.id,
            title=title,
            model_name=validated.get('model', 'claude'),
        )
        session_id = session.id

    model_name = validated.get('model', session.model_name)

    # 保存用户消息
    SessionManager.add_message(session_id, 'user', validated['message'])

    # 构建上下文
    context_messages = SessionManager.get_context_messages(
        session_id,
        max_messages=current_app.config.get('MAX_CONTEXT_MESSAGES', 20),
    )

    # 调用 LLM
    service = LLMService(current_app.config)
    result = service.chat(
        messages=context_messages,
        model_name=model_name,
        system_prompt=session.system_prompt,
    )

    if result['success']:
        # 保存 AI 回复
        reply_msg = SessionManager.add_message(
            session_id,
            'assistant',
            result['reply'],
            model_name=result.get('model', model_name),
        )
        # 如果会话标题仍是默认的，用第一条消息更新
        if session.title == '新的对话' and session.messages.count() <= 2:
            new_title = SessionManager.auto_title(session_id, validated['message'])
            SessionManager.update_session(session_id, user.id, title=new_title)

        return jsonify({
            'code': 200,
            'message': 'ok',
            'data': {
                'session_id': session_id,
                'reply': result['reply'],
                'model': result.get('model', model_name),
                'message_id': reply_msg.id,
            },
        })
    else:
        # LLM 调用失败
        return jsonify({
            'code': 503,
            'message': f'AI 服务暂时不可用: {result.get("error", "未知错误")}',
            'data': {
                'session_id': session_id,
                'detail': result.get('error', ''),
            },
        }), 503


# ============================================================
# API: 流式对话 (SSE)
# ============================================================

@chat_bp.route('/api/chat/stream', methods=['POST'])
@login_required_api
def api_stream_chat():
    """流式对话 - Server-Sent Events"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    try:
        validated = SendMessageSchema().load(data)
    except ValidationError as e:
        return jsonify({'code': 400, 'message': f'参数校验失败: {e.messages}', 'data': None}), 400

    # 获取或创建会话
    session_id = validated.get('session_id')
    if session_id:
        session = SessionManager.get_session(session_id, user.id)
        if not session:
            return jsonify({'code': 404, 'message': '会话不存在', 'data': None}), 404
    else:
        title = SessionManager.auto_title(None, validated['message'])
        session = SessionManager.create_session(
            user_id=user.id,
            title=title,
            model_name=validated.get('model', 'claude'),
        )
        session_id = session.id

    model_name = validated.get('model', session.model_name)
    enable_tools = data.get('enable_tools', False)

    # 保存用户消息
    SessionManager.add_message(session_id, 'user', validated['message'])

    # 构建上下文
    context_messages = SessionManager.get_context_messages(
        session_id,
        max_messages=current_app.config.get('MAX_CONTEXT_MESSAGES', 20),
    )

    # 用于收集完整回复的容器
    full_reply_parts = []

    def generate():
        api_key = current_app.config.get('ANTHROPIC_API_KEY', '')

        if enable_tools:
            tools = get_anthropic_tools()
            stream = StreamChatService.stream_chat_with_tools(
                messages=context_messages,
                api_key=api_key,
                tools=tools,
                system_prompt=session.system_prompt,
            )
        else:
            stream = StreamChatService.stream_chat(
                messages=context_messages,
                api_key=api_key,
                system_prompt=session.system_prompt,
            )

        for chunk in stream:
            full_reply_parts.append(chunk)
            yield chunk

        # SSE 流结束后，将完整消息保存到数据库
        try:
            full_text = ''
            tool_calls = []
            for chunk in full_reply_parts:
                if chunk.startswith('data: '):
                    try:
                        payload = json.loads(chunk[6:])
                        if 'text' in payload:
                            full_text += payload['text']
                        elif 'tool_call' in payload:
                            tool_calls.append(payload['tool_call'])
                    except json.JSONDecodeError:
                        pass

            # 如果有工具调用，执行工具并追加结果
            tool_results = []
            for tc in tool_calls:
                result = execute_tool(tc['name'], tc.get('input', {}))
                tool_results.append({'tool': tc['name'], 'result': result})
                full_text += f'\n\n🔧 调用工具 [{tc["name"]}]: {result}'

            if full_text:
                SessionManager.add_message(
                    session_id, 'assistant', full_text.strip(),
                    model_name=model_name,
                )
                # 更新标题
                if session.title == '新的对话':
                    new_title = SessionManager.auto_title(session_id, validated['message'])
                    SessionManager.update_session(session_id, user.id, title=new_title)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'保存流式回复失败: {e}')

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


# ============================================================
# API: 可用工具列表
# ============================================================

@chat_bp.route('/api/chat/tools', methods=['GET'])
@login_required_api
def api_list_tools():
    """列出 AI 可用的工具"""
    from app.chat.agent_tools import TOOLS_REGISTRY
    tools = [
        {'name': t['name'], 'description': t['description']}
        for t in TOOLS_REGISTRY.values()
    ]
    return jsonify({'code': 200, 'message': 'ok', 'data': {'tools': tools}})


# ============================================================
# API: 工具调用结果（手动触发）
# ============================================================

@chat_bp.route('/api/chat/tool-call', methods=['POST'])
@login_required_api
def api_tool_call():
    """手动执行工具调用（供前端）"""
    data = request.get_json(silent=True) or {}
    tool_name = data.get('tool_name', '')
    tool_input = data.get('input', {})

    if not tool_name:
        return jsonify({'code': 400, 'message': '请指定工具名称', 'data': None}), 400

    result = execute_tool(tool_name, tool_input)
    return jsonify({'code': 200, 'message': 'ok', 'data': {'result': result}})
