# 🤖 Python 多功能智能助手系统

基于 **Flask + LangChain + Claude AI** 的轻量级智能对话平台，支持多模型切换、对话管理、数据分析等企业级功能。

## ✨ 功能特性

- 🔐 **用户认证** — 注册/登录，JWT 令牌，角色权限管理
- 💬 **智能对话** — 多轮上下文记忆，Claude / DeepSeek 双模型
- 📊 **数据分析** — CSV/Excel 上传，统计分析与图表生成（开发中）
- 🔧 **工具扩展** — 天气查询、邮件发送等可插拔工具（开发中）
- 🐳 **容器化部署** — Docker + Gunicorn + Nginx 生产级部署
- 🎨 **现代 UI** — 三栏 SPA 布局，响应式设计，Markdown 渲染

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- pip

### 2. 安装

```bash
# 克隆项目
cd python多功能智能助手1

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖（国内用户可使用清华镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 API Key（至少配置一个）
# ANTHROPIC_API_KEY=sk-ant-xxx    (Claude API 密钥)
# DEEPSEEK_API_KEY=sk-xxx         (DeepSeek API 密钥)
```

获取 API Key：
- **Claude API**: 访问 [console.anthropic.com](https://console.anthropic.com/) 注册获取
- **DeepSeek API**: 访问 [platform.deepseek.com](https://platform.deepseek.com/) 注册获取

### 4. 运行

```bash
python run.py
```

访问 [http://localhost:5000](http://localhost:5000)

## 📁 项目结构

```
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── extensions.py        # 扩展初始化 (db/jwt/migrate)
│   ├── errors.py            # 全局错误处理
│   ├── models/              # 数据模型
│   │   ├── user.py
│   │   ├── chat_session.py
│   │   └── chat_message.py
│   ├── auth/                # 用户认证模块
│   │   ├── routes.py        # 登录/注册/资料 API
│   │   └── decorators.py    # JWT 装饰器
│   ├── chat/                # 智能对话模块
│   │   ├── routes.py        # 会话/消息 API
│   │   ├── llm_service.py   # 多模型抽象层
│   │   └── session_manager.py  # 会话管理
│   ├── data/                # 数据分析模块 (Phase 2)
│   ├── tools/               # 工具扩展模块 (Phase 2)
│   ├── main/                # 主页/健康检查
│   ├── templates/           # Jinja2 模板
│   └── static/              # CSS/JS 静态资源
├── config.py                # 配置类
├── run.py                   # 入口
└── requirements.txt         # 依赖清单
```

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask 3.x |
| AI 框架 | LangChain + LangChain-Anthropic |
| 数据库 | SQLAlchemy ORM (SQLite/PostgreSQL) |
| 认证 | Flask-JWT-Extended |
| 数据校验 | Marshmallow |
| 前端 | 原生 HTML/CSS/JS (SPA) |

## 📝 License

MIT
