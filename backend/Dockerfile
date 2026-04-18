# 构建阶段
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 用 pip 直接安装（更可靠的多阶段构建）
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy[asyncio] asyncpg alembic \
    redis[hiredis] bcrypt pyjwt gunicorn httpx python-multipart

COPY . .

# 运行阶段
FROM python:3.12-slim

WORKDIR /app

# 设置时区为上海（解决 UTC 差 8 小时问题）
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 复制 builder 的 site-packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# 创建非 root 用户
RUN useradd -m -u 1000 emby && chown -R emby:emby /app
USER emby

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2"]
