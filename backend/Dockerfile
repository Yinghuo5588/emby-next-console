# 构建阶段
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.in-project true

COPY pyproject.toml ./
RUN poetry install --no-dev --no-interaction --no-root || pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy[asyncio] asyncpg alembic redis[hiredis] passlib[bcrypt] pyjwt gunicorn

COPY . .

# 运行阶段
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app

# 如果 venv 存在就用，否则直接用系统 python
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -m -u 1000 emby && chown -R emby:emby /app
USER emby

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2"]
