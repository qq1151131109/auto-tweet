#!/bin/bash
#
# API服务快速启动脚本
# 本地开发环境（不使用Docker）
#

set -e

echo "🚀 Starting AI Tweet Generator API (Local Development Mode)"
echo ""

# 检查Redis是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "   Please start Redis first:"
    echo "   - macOS: brew services start redis"
    echo "   - Linux: sudo systemctl start redis"
    echo "   - Docker: docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi

echo "✓ Redis is running"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please copy .env.example to .env and configure it"
    exit 1
fi

echo "✓ .env file found"

# 创建必要的目录
mkdir -p personas calendars output_standalone output_images task_storage uploads/images

echo "✓ Directories created"
echo ""

# 启动Celery Worker（后台）
echo "📦 Starting Celery Worker..."
celery -A tasks.celery_app worker --loglevel=info --concurrency=4 --pool=solo &
CELERY_PID=$!

echo "   Celery Worker started (PID: $CELERY_PID)"
echo ""

# 可选：启动Flower监控
# echo "🌸 Starting Celery Flower..."
# celery -A tasks.celery_app flower --port=5555 &
# FLOWER_PID=$!

# 启动FastAPI服务
echo "🌐 Starting FastAPI Server..."
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 清理：Ctrl+C时停止所有服务
trap "echo ''; echo '👋 Stopping services...'; kill $CELERY_PID 2>/dev/null; exit 0" INT TERM
