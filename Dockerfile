# 使用官方Python 3.12镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/db /app/logs

# 设置文件权限
RUN chmod +x run.sh

# 创建非root用户
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# 切换到非root用户
USER botuser

# 暴露端口（如果需要健康检查）
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; import aiohttp; asyncio.run(aiohttp.ClientSession().get('https://api.telegram.org').close())" || exit 1

# 启动命令
CMD ["python", "-m", "app.bot"]