#!/bin/bash
#
# Docker Compose快速启动脚本
#

set -e

echo "🐳 Starting AI Tweet Generator API (Docker Mode)"
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please configure .env file first"
    exit 1
fi

echo "✓ .env file found"
echo ""

# 启动服务
echo "🚀 Starting services with docker-compose..."
docker-compose up --build -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "   - API Server: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Flower (Task Monitor): http://localhost:5555"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart: docker-compose restart"
echo ""
