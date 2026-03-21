#!/bin/bash

set -e

PROJECT_DIR="/home/node/clawd/projects/emby-next-console"
BACKUP_DIR="/tmp/emby-console-$(date +%Y%m%d-%H%M%S)"
ARCHIVE="/tmp/emby-console-$(date +%Y%m%d-%H%M%S).tar.gz"

echo "📦 准备打包 Emby Next Console..."
echo "📂 源目录: $PROJECT_DIR"
echo "📂 临时复制到: $BACKUP_DIR"
echo "📦 归档文件: $ARCHIVE"

# 创建临时目录
mkdir -p "$BACKUP_DIR"

# 复制必要文件（排除大型文件和缓存）
echo "📋 复制文件..."
cp -r "$PROJECT_DIR"/{backend,frontend,docker-compose.yml,start.sh,deploy.sh,dev.sh,README.md,部署说明.md} "$BACKUP_DIR" 2>/dev/null || true

# 清理前端 node_modules（太大，不打包）
rm -rf "$BACKUP_DIR/frontend/node_modules" 2>/dev/null || true
rm -rf "$BACKUP_DIR/backend/.venv" 2>/dev/null || true
rm -rf "$BACKUP_DIR/backend/__pycache__" 2>/dev/null || true

# 打包
echo "🗜️  正在打包..."
tar -czf "$ARCHIVE" -C "$BACKUP_DIR" .

# 清理临时目录
rm -rf "$BACKUP_DIR"

echo ""
echo "✅ 打包完成！"
echo "📦 归档位置: $ARCHIVE"
echo ""
echo "你可以将此文件发送给任何人，对方解压后运行："
echo "  cd emby-next-console"
echo "  ./start.sh"