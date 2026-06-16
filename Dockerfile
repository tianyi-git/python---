# Python 多功能智能助手 - Docker 镜像
FROM python:3.12-slim

LABEL maintainer="assistant"
LABEL description="Python 多功能智能助手系统 - Flask + LangChain + Claude AI"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p instance static/charts static/uploads

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 使用 Gunicorn 启动（生产模式）
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "run:app"]
