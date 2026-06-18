"""
应用配置模块
支持 development / production / testing 三种环境
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')

    # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-change')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = False  # 生产环境改为 True（HTTPS）
    JWT_COOKIE_CSRF_PROTECT = False  # 开发环境关闭，生产应启用

    # LLM API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

    # LLM 默认设置
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek')
    MAX_CONTEXT_MESSAGES = 20  # 每次请求携带的最大历史消息数

    # 上传文件限制
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 限流（预留）
    RATELIMIT_ENABLED = False


class DevelopmentConfig(Config):
    """开发环境"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')


class ProductionConfig(Config):
    """生产环境"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost:5432/assistant'
    )
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True


class TestingConfig(Config):
    """测试环境"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
