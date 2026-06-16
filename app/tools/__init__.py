"""工具扩展蓝图 (Phase 2 骨架)"""
from flask import Blueprint

tools_bp = Blueprint('tools', __name__)

from app.tools import routes
