"""
会话上下文管理器
管理对话历史的持久化、检索和上下文裁剪
"""
from app.extensions import db
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


class SessionManager:
    """对话会话管理"""

    @staticmethod
    def create_session(
        user_id: int,
        title: str = '新的对话',
        model_name: str = 'claude',
        system_prompt: str = None,
    ) -> ChatSession:
        """创建新会话"""
        session = ChatSession(
            user_id=user_id,
            title=title,
            model_name=model_name,
            system_prompt=system_prompt,
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def get_user_sessions(user_id: int) -> list:
        """获取用户的所有会话（按更新时间倒序）"""
        return (
            ChatSession.query
            .filter_by(user_id=user_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_session(session_id: int, user_id: int) -> ChatSession | None:
        """获取指定会话（确保属于当前用户）"""
        return ChatSession.query.filter_by(id=session_id, user_id=user_id).first()

    @staticmethod
    def delete_session(session_id: int, user_id: int) -> bool:
        """删除会话"""
        session = SessionManager.get_session(session_id, user_id)
        if not session:
            return False
        db.session.delete(session)
        db.session.commit()
        return True

    @staticmethod
    def update_session(session_id: int, user_id: int, **kwargs) -> ChatSession | None:
        """更新会话信息（标题、模型、system_prompt）"""
        session = SessionManager.get_session(session_id, user_id)
        if not session:
            return None
        if 'title' in kwargs:
            session.title = kwargs['title']
        if 'model_name' in kwargs:
            session.model_name = kwargs['model_name']
        if 'system_prompt' in kwargs:
            session.system_prompt = kwargs['system_prompt']
        db.session.commit()
        return session

    @staticmethod
    def add_message(
        session_id: int,
        role: str,
        content: str,
        model_name: str = None,
        token_count: int = None,
    ) -> ChatMessage:
        """添加消息到会话"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            model_name=model_name,
            token_count=token_count,
        )
        db.session.add(message)
        # 同时更新会话的 updated_at
        session = ChatSession.query.get(session_id)
        if session:
            from datetime import datetime, timezone
            session.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return message

    @staticmethod
    def get_messages(session_id: int, limit: int = None) -> list:
        """获取会话的消息列表"""
        query = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at)
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_context_messages(session_id: int, max_messages: int = 20) -> list:
        """
        获取用于 LLM 上下文的消息列表
        返回 role + content 格式，用于直接发送给 LLM
        """
        messages = SessionManager.get_messages(session_id, limit=max_messages * 2)
        # 只取 user 和 assistant 消息（过滤 system）
        context = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
            if msg.role in ('user', 'assistant')
        ]
        # 限制上下文长度（简单估算：每字符约0.5 token，目标不超过4000 tokens）
        total_chars = sum(len(m['content']) for m in context)
        while total_chars > 8000 and len(context) > 2:  # 8000 字符 ≈ 4000 tokens
            removed = context.pop(0)
            total_chars -= len(removed['content'])

        return context

    @staticmethod
    def auto_title(session_id: int, first_message: str) -> str:
        """根据首条消息自动生成会话标题"""
        # 取前30个字符作为标题
        title = first_message.strip().replace('\n', ' ')[:30]
        if len(title) < len(first_message.strip()):
            title += '...'
        return title if title else '新的对话'
