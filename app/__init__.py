"""
Flask 应用工厂
"""
from flask import Flask
from config import config


def create_app(config_name=None):
    """创建 Flask 应用实例"""
    if config_name is None:
        import os
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # 初始化扩展
    from app.extensions import db, migrate, jwt
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # 注册蓝图
    from app.main.routes import main_bp
    from app.auth import auth_bp
    from app.chat import chat_bp
    from app.data import data_bp
    from app.tools import tools_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(tools_bp)

    # 注册错误处理器
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # SQLite 自动建表（开发/测试便利），PostgreSQL 生产环境请用 Flask-Migrate 迁移
    with app.app_context():
        from app.models import User, ChatSession, ChatMessage
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            db.create_all()

    return app
