"""数据分析蓝图 (Phase 2 骨架)"""
from flask import Blueprint

data_bp = Blueprint('data', __name__)

from app.data import routes
