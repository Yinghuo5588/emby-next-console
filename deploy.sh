#!/bin/bash

set -e

echo "🚀 部署 Emby Next Console..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "📦 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
fi

# 检查 docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在项目根目录执行此脚本"
    exit 1
fi

# 如果还没改过用户名，提示
if grep -q "YOUR_GITHUB_USERNAME" docker-compose.yml; then
    echo "❌ 请先编辑 docker-compose.yml，替换 YOUR_GITHUB_USERNAME 为你的 GitHub 用户名"
    exit 1
fi

# 拉取最新镜像
echo "📦 拉取最新镜像..."
docker compose pull

# 启动
echo "🚀 启动服务..."
docker compose up -d

sleep 5

echo ""
echo "📋 容器状态："
docker compose ps

echo ""
echo "✅ 部署完成！"
echo "🌐 前端: http://localhost:3000"
echo ""
echo "更新版本："
echo "  docker compose pull && docker compose up -d"
echo ""
echo "查看日志: docker compose logs -f"
echo "停止服务: docker compose down"
