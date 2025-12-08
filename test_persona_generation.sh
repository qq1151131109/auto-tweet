#!/bin/bash
# 测试人设生成脚本 - 生成2个样本验证配置

set -e

# API配置
API_KEY="${OPENAI_API_KEY:-}"
API_BASE="${OPENAI_API_BASE:-https://api.openai.com/v1}"
MODEL="${OPENAI_MODEL:-gpt-4o}"

if [ -z "$API_KEY" ]; then
    echo "错误: 请设置OPENAI_API_KEY环境变量"
    exit 1
fi

echo "======================================================================"
echo "🧪 测试人设生成 (2个样本)"
echo "======================================================================"
echo ""

mkdir -p personas

# 测试1: jfz开头的文件 (应该使用sundub)
echo "📍 测试1: jfz_45 - Soft Domme (trigger_word应为sundub)"
python main.py \
  --generate-persona \
  --image image/jfz_45.png \
  --persona-output personas/test_jfz_45.json \
  --business-goal "Attract male submissives interested in gentle femdom" \
  --custom-instructions "Soft domme personality" \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "验证LoRA配置 (jfz_45):"
cat personas/test_jfz_45.json | grep -A 5 '"lora"' || echo "未找到lora配置"

echo ""
echo "======================================================================"
echo ""

# 测试2: 非jfz文件 (应该使用sunway)
echo "📍 测试2: byrecarvalho - Fitness Babe (trigger_word应为sunway)"
python main.py \
  --generate-persona \
  --image image/byrecarvalho.jpg \
  --persona-output personas/test_byrecarvalho.json \
  --business-goal "Attract fitness enthusiasts" \
  --custom-instructions "Fitness influencer with high libido" \
  --api-key "$API_KEY" \
  --api-base "$API_BASE" \
  --model "$MODEL"

echo ""
echo "验证LoRA配置 (byrecarvalho):"
cat personas/test_byrecarvalho.json | grep -A 5 '"lora"' || echo "未找到lora配置"

echo ""
echo "======================================================================"
echo "✅ 测试完成！"
echo "======================================================================"
echo ""
echo "请检查以下配置是否正确："
echo "1. jfz_45 应该使用 trigger_words: [\"sundub\"]"
echo "2. byrecarvalho 应该使用 trigger_words: [\"sunway\"]"
echo "3. 两者的 strength 都应该是 0.8"
echo ""
echo "查看完整配置:"
echo "  cat personas/test_jfz_45.json | jq '.data.lora'"
echo "  cat personas/test_byrecarvalho.json | jq '.data.lora'"
echo ""
