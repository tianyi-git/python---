"""
应用入口
开发环境: python run.py
生产环境: gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print('=' * 50)
    print('  Python 多功能智能助手系统')
    print('  访问地址: http://localhost:5000')
    print('  对话页面: http://localhost:5000/chat')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
