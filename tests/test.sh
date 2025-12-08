#!/bin/bash
# 独立生成器测试脚本

set -e

echo "========================================"
echo "🧪 独立推文生成器测试"
echo "========================================"

# 配置
API_KEY=${API_KEY:-"your-api-key-here"}
API_BASE=${API_BASE:-"https://www.dmxapi.cn/v1"}
MODEL=${MODEL:-"grok-4.1-non-thinking"}

# 检查依赖
echo ""
echo "📦 检查依赖..."
python3 -c "import openai" 2>/dev/null || {
    echo "  ⚠️  缺少 openai 库，正在安装..."
    pip install openai aiohttp
}
echo "  ✓ 依赖检查完成"

# 测试1: 单个人设
echo ""
echo "🧪 测试1: 单个人设生成"
echo "----------------------------------------"

if [ -f "../personas/lila_monroe.json" ] && [ -f "../calendars/lila_monroe_2025-12.json" ]; then
    python3 main.py \
        --persona ../personas/lila_monroe.json \
        --calendar ../calendars/lila_monroe_2025-12.json \
        --tweets 3 \
        --api-key "$API_KEY" \
        --api-base "$API_BASE" \
        --model "$MODEL" \
        --max-concurrent 5 \
        --output-dir test_output

    echo "  ✓ 测试1通过"
else
    echo "  ⚠️  跳过测试1: 找不到测试文件"
fi

# 测试2: 批量生成
echo ""
echo "🧪 测试2: 批量生成（3个人设）"
echo "----------------------------------------"

PERSONAS=$(find ../personas -name "*.json" | head -3)
CALENDARS=$(find ../calendars -name "*.json" | head -3)

if [ ! -z "$PERSONAS" ]; then
    python3 main.py \
        --batch-mode \
        --personas $PERSONAS \
        --calendars $CALENDARS \
        --tweets 2 \
        --api-key "$API_KEY" \
        --api-base "$API_BASE" \
        --model "$MODEL" \
        --max-concurrent 10 \
        --output-dir test_output

    echo "  ✓ 测试2通过"
else
    echo "  ⚠️  跳过测试2: 找不到测试文件"
fi

# 检查输出
echo ""
echo "📊 检查输出文件..."
ls -lh test_output/*.json 2>/dev/null | head -5 || echo "  没有生成文件"

echo ""
echo "========================================"
echo "✅ 测试完成"
echo "========================================"
echo ""
echo "查看输出:"
echo "  ls -lh test_output/"
echo ""
echo "查看日志:"
echo "  cat test_output/*.log"
