# 构建阶段
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装系统依赖（编译需要）
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install --no-cache-dir poetry

# 复制依赖文件
COPY pyproject.toml ./

# 安装依赖到虚拟环境
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction

# 运行阶段
FROM python:3.12-slim

WORKDIR /app

# 安装 PostgreSQL 客户端库（运行时需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 emby && chown -R emby:emby /app
USER emby

# 暴露端口
EXPOSE 8000

# 默认命令（docker compose 会覆盖）
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2"]
