# Emby Next Console

Emby 管理控制台 — FastAPI + Vue 3 + PostgreSQL + Redis

## 技术栈

| 层     | 技术                              |
| ------ | --------------------------------- |
| 后端   | FastAPI · SQLAlchemy · Alembic    |
| 前端   | Vue 3 · Pinia · TypeScript · Vite |
| 数据库 | PostgreSQL · Redis                |
| 部署   | Docker · GitHub Actions → GHCR   |

## 快速部署

### 1. 构建镜像

Fork 本仓库到你自己的 GitHub，推送到 main 分支后 GitHub Actions 会自动构建镜像推送到 GHCR。

### 2. 创建 docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: emby-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: emby_next
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: emby-redis
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  backend:
    image: ghcr.io/你的用户名/emby-next-console-backend:latest
    container_name: emby-backend
    environment:
      APP_ENV: production
      DEBUG: "false"
      SECRET_KEY: "换成随机字符串"
      DATABASE_URL: "postgresql+asyncpg://postgres:postgres@postgres:5432/emby_next"
      REDIS_URL: "redis://redis:6379/0"
      CORS_ORIGINS: "http://localhost:3000"
      EMBY_HOST: "http://你的Emby地址:8096"
      EMBY_API_KEY: "你的Emby API Key"
      EMBY_DATA_MODE: "api"
      EMBY_WEBHOOK_TOKEN: "embyconsole"
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    command: >
      sh -c "alembic upgrade head && gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2"
    restart: unless-stopped

  frontend:
    image: ghcr.io/你的用户名/emby-next-console-frontend:latest
    container_name: emby-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3. 启动

```bash
docker compose up -d
```

访问 http://localhost:3000

## Emby 配置

| 环境变量          | 说明                               | 默认值                       |
| ----------------- | ---------------------------------- | ---------------------------- |
| `EMBY_HOST`       | Emby 服务器地址                    | `http://127.0.0.1:8096`     |
| `EMBY_API_KEY`    | Emby API 密钥                      | 必填                         |
| `EMBY_DATA_MODE`  | 数据源模式：`api` / `sqlite` / `auto` | `api`                     |
| `EMBY_WEBHOOK_TOKEN` | Webhook 鉴权 Token              | `embyconsole`               |

- **api 模式**：通过 Emby REST API 获取数据，适合远程部署
- **sqlite 模式**：直接读取 `playback_reporting.db`，适合同机部署（需挂载数据库目录）
- **auto 模式**：自动检测，有数据库文件走 SQLite，否则走 API

## Webhook

在 Emby 后台 → 设置 → Webhook 添加：

```
http://你的地址/api/v1/webhook/emby?token=embyconsole
```

## 本地开发

```bash
# 只启动数据库
docker compose up -d postgres redis

# 后端
cd backend
pip install poetry && poetry install
cp .env.example .env
# 改 .env 里的 postgres/redis 地址为 localhost
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install && npm run dev
```

访问 http://localhost:5173

## 项目结构

```
backend/
  app/
    core/          # 配置、安全、异常、Emby 适配器
    db/            # SQLAlchemy 模型
    modules/       # 业务模块 (auth, dashboard, stats, users, risk, notifications, system, webhook)
    cache/         # Redis 缓存
    shared/        # 通用工具
  alembic/         # 数据库迁移
frontend/
  src/
    api/           # API 调用层
    pages/         # 页面组件
    stores/        # Pinia 状态管理
    components/    # 通用组件
.github/workflows/ # CI/CD
docker-compose.yml # 容器编排
```
