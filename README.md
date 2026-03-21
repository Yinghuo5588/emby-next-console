# Emby Next Console

Emby 管理控制台 — FastAPI + Vue 3 + PostgreSQL + Redis

## 快速部署

### 1. 创建 GitHub 仓库

把代码推到 GitHub，Actions 会自动构建 Docker 镜像到 GHCR。

### 2. 服务器上部署

```bash
# 拉取项目
git clone https://github.com/你的用户名/emby-next-console.git
cd emby-next-console

# 替换 docker-compose.yml 中的 YOUR_GITHUB_USERNAME 为你的 GitHub 用户名
sed -i 's/YOUR_GITHUB_USERNAME/你的用户名/g' docker-compose.yml

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 3. 访问

- 前端：http://你的服务器IP:3000
- API 文档：http://你的服务器IP:8000/docs

### 4. 更新

每次推送到 main 分支，GitHub Actions 自动构建新镜像。

服务器上执行：
```bash
docker compose pull && docker compose up -d
```

## 本地开发

```bash
# 只启动数据库（Docker）
docker compose up -d postgres redis

# 启动后端（本地跑，改代码自动重载）
cd backend
pip install poetry
poetry install
cp .env.example .env
sed -i 's/@postgres:/@localhost:/' .env
sed -i 's/@redis:6379/@localhost:6379/' .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 启动前端（本地跑，改代码自动热更新）
cd frontend
npm install
npm run dev
```

## 项目结构

```
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── core/      # 配置、安全、异常
│   │   ├── db/        # SQLAlchemy 模型
│   │   ├── modules/   # 业务模块 (auth, dashboard, stats, users, risk, notifications, system)
│   │   ├── cache/     # Redis 缓存
│   │   └── shared/    # 通用工具
│   ├── alembic/       # 数据库迁移
│   └── pyproject.toml
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── api/       # API 调用层
│       ├── pages/     # 页面组件
│       ├── stores/    # Pinia 状态管理
│       └── components/# 通用组件
├── .github/workflows/ # CI/CD
├── docker-compose.yml # 容器编排
├── deploy.sh          # 服务器部署脚本
└── dev.sh             # 本地开发脚本
```
