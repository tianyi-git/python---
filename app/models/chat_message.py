"""
消息模型
"""
from datetime import datetime, timezone
from app.extensions import db


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False, index=True
    )
    role = db.Column(db.String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(50), nullable=True)
    token_count = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联
    session = db.relationship('ChatSession', back_populates='messages')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'model_name': self.model_name,
            'token_count': self.token_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role}>'
