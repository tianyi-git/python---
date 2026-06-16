"""
Flask 扩展初始化
使用延迟初始化模式，由 create_app() 工厂函数调用 init_app()
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
