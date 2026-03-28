# Emby Next Console

Emby 媒体服务器管理控制台 — FastAPI + Vue 3 + PostgreSQL + Redis

## 功能概览

### 📊 统计分析
- 播放趋势、热力图（观影生物钟）
- 软件/硬件分布（翻转卡片切换）
- 热门内容 Top 5 / 活跃用户 Top 5（金银铜排名）
- 内容分析详情 / 用户分析详情

### 👥 用户管理
- 用户列表 + 搜索 + 筛选（全部/VIP/禁用/已过期）
- 批量操作：启用/禁用/续期/设VIP/取消VIP/删除
- 单用户编辑：并发限制、过期时间、VIP、备注、权限

### 🛡️ 管控中心
- 实时播放监控 + 一键踢出
- 并发越界检测 + 自动处理
- 客户端黑名单/白名单（模糊匹配）
- 策略配置：弹窗→停止→强踢→封禁（复发加重）
- 违规记录 + 解封 + 执法日志

### 📅 追剧日历
- TMDB 排期 + Emby 物理校验
- 周历切换 + 多集聚合
- 入库状态自动更新（Webhook 联动）

### 🎨 质量盘点
- 分辨率/动态范围分布（翻转卡片）
- 按质量筛选 + 忽略项管理

### 🔔 推送通知
- Webhook 推送到外部 URL（JSON 格式）
- 支持事件：风控告警/创建用户/删除用户/VIP变更
- HMAC-SHA256 签名验证（可选）
- 发送失败自动重试 3 次

### ⚙️ 设置
- TMDB API Key + 图片代理
- Webhook 配置
- 系统状态（数据库/Redis）

## 技术栈

| 层     | 技术                                        |
| ------ | ------------------------------------------- |
| 后端   | FastAPI · SQLAlchemy (asyncpg) · Alembic    |
| 前端   | Vue 3 · Pinia · TypeScript · Vite · Naive UI |
| 数据库 | PostgreSQL · Redis                          |
| 部署   | Docker Compose · GitHub Actions → GHCR      |

## 快速部署

### 1. Fork & 构建

Fork 本仓库到你的 GitHub，推送到 main 分支后 GitHub Actions 自动构建镜像。

### 2. docker-compose.yml

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
      EMBY_WEBHOOK_TOKEN: "embyconsole"
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
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

## 环境变量

| 变量                  | 说明                    | 默认值                       |
| --------------------- | ----------------------- | ---------------------------- |
| `EMBY_HOST`           | Emby 服务器地址         | `http://127.0.0.1:8096`     |
| `EMBY_API_KEY`        | Emby API 密钥           | 必填                         |
| `EMBY_WEBHOOK_TOKEN`  | Webhook 鉴权 Token      | `embyconsole`               |
| `TMDB_API_KEY`        | TMDB API Key（日历功能）| 可选                         |

## Webhook 配置

### 接收 Emby 事件

在 Emby 后台 → 设置 → Webhook 添加：

```
http://你的地址/api/v1/webhook/emby?token=embyconsole
```

### 推送通知到外部

在控制台「更多 → 通知」中添加推送目标，支持任意 Webhook URL。

## 本地开发

```bash
# 启动数据库
docker compose up -d postgres redis

# 后端
cd backend
pip install poetry && poetry install
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install && npm run dev
```

访问 http://localhost:5173

## License

MIT
