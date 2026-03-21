#!/bin/bash

echo "🛠️  开发模式启动 Emby Next Console..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 1. 启动 postgres + redis（只起数据库，不起应用容器）
echo "🐘 启动数据库和缓存..."
docker compose up -d postgres redis

# 等待就绪
echo "⏳ 等待数据库就绪..."
sleep 3

# 2. 准备后端 .env
if [ ! -f backend/.env ]; then
    echo "📝 创建 backend/.env..."
    cp backend/.env.example backend/.env
    SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/change-me-in-production/$SECRET/" backend/.env
fi

# 3. 启动后端（后台）
echo "🐍 启动后端 (uvicorn --reload)..."
cd backend
pip install poetry -q 2>/dev/null
poetry install --quiet 2>/dev/null
alembic upgrade head 2>/dev/null
# 后台启动，保存代码自动重载
nohup poetry run uvicorn app.main:app --reload --port 8000 > /tmp/emby-backend.log 2>&1 &
echo "  后端日志: tail -f /tmp/emby-backend.log"

# 4. 启动前端（后台）
echo "📦 启动前端 (npm run dev)..."
cd ../frontend
npm install --silent 2>/dev/null
nohup npm run dev > /tmp/emby-frontend.log 2>&1 &
echo "  前端日志: tail -f /tmp/emby-frontend.log"

# 等待
sleep 3

echo ""
echo "✅ 开发环境已启动！"
echo "🌐 前端: http://localhost:5173"
echo "🔧 后端: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo ""
echo "改代码 → 保存 → 浏览器自动刷新，不用重启"
echo ""
echo "停止所有服务："
echo "  docker compose stop postgres redis"
echo "  pkill -f uvicorn"
echo "  pkill -f vite"
