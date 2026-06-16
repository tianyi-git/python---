"""
会话模型
"""
from datetime import datetime, timezone
from app.extensions import db


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default='新的对话')
    model_name = db.Column(db.String(50), nullable=False, default='claude')
    system_prompt = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 关联
    user = db.relationship('User', back_populates='chat_sessions')
    messages = db.relationship(
        'ChatMessage',
        back_populates='session',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='ChatMessage.created_at',
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'model_name': self.model_name,
            'system_prompt': self.system_prompt,
            'message_count': self.messages.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<ChatSession {self.id}: {self.title}>'
