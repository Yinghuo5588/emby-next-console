#!/bin/bash

echo "🚀 启动 Emby Next Console..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 创建 backend/.env（如果不存在）
if [ ! -f backend/.env ]; then
    echo "📝 创建 backend/.env..."
    cp backend/.env.example backend/.env
    # 生成随机 SECRET_KEY
    SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/change-me-in-production/$SECRET/" backend/.env
    echo "⚠️  已自动生成随机 SECRET_KEY"
else
    echo "✅ backend/.env 已存在，跳过"
fi

# 停止旧容器（如果存在）
echo "🛑 停止现有容器..."
docker compose down 2>/dev/null || true

# 构建并启动
echo "🔨 构建并启动服务..."
docker compose up --build -d

# 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 8

# 检查容器状态
echo ""
echo "📋 容器状态："
docker compose ps

echo ""
echo "✅ 服务已启动！"
echo "🌐 前端: http://localhost:5173"
echo "🔧 后端 API: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo ""
echo "常用命令："
echo "  查看日志: docker compose logs -f"
echo "  停止服务: docker compose down"
echo "  重启后端: docker compose restart backend"
