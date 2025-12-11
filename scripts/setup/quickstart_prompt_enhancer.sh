#!/bin/bash
# PromptEnhancer 快速开始脚本

echo "=================================================="
echo "  PromptEnhancer 快速开始"
echo "=================================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

echo "✅ Python3已安装"
echo ""

# 1. 运行功能演示
echo "【步骤1】运行功能演示..."
echo "────────────────────────────────────────────────"
python3 test_prompt_enhancer.py | head -150
echo ""
echo "✅ 功能演示完成（完整输出请查看上方）"
echo ""

# 2. 检查配置文件
echo "【步骤2】检查配置文件..."
echo "────────────────────────────────────────────────"
if [ -f "config/image_generation.yaml" ]; then
    echo "✅ 配置文件存在: config/image_generation.yaml"
    echo ""
    echo "当前配置:"
    echo "  - 模型类型: $(grep 'type:' config/image_generation.yaml | head -1 | awk '{print $2}' | tr -d '"')"
    echo "  - 真实感级别: $(grep 'level:' config/image_generation.yaml | head -1 | awk '{print $2}' | tr -d '"')"
    echo "  - 增强开关: $(grep 'enabled:' config/image_generation.yaml | head -1 | awk '{print $2}')"
else
    echo "❌ 配置文件不存在"
    exit 1
fi
echo ""

# 3. 文档位置
echo "【步骤3】文档位置"
echo "────────────────────────────────────────────────"
echo "📖 使用指南: docs/PROMPT_ENHANCER_GUIDE.md"
echo "📊 研究报告: docs/IMAGE_GENERATION_RESEARCH_REPORT.md"
echo "📝 实施总结: docs/PROMPT_ENHANCER_SUMMARY.md"
echo ""

# 4. 使用建议
echo "【步骤4】下一步建议"
echo "────────────────────────────────────────────────"
echo ""
echo "🎯 推荐配置（生产环境）:"
echo "   编辑 config/image_generation.yaml:"
echo "   prompt_enhancement:"
echo "     enabled: true"
echo "     realism:"
echo "       level: \"medium\"  # balanced模式"
echo "       variation: true"
echo ""
echo "🧪 测试不同级别:"
echo "   1. 修改 level: \"low\" → \"medium\" → \"high\""
echo "   2. 运行: python main.py --persona test.json --tweets 5"
echo "   3. 对比生成的图片效果"
echo ""
echo "🔧 切换到SDXL:"
echo "   使用预设: presets.sdxl"
echo "   或修改 model.type: \"sdxl\""
echo ""
echo "❌ 关闭增强（回退）:"
echo "   设置 prompt_enhancement.enabled: false"
echo ""

# 5. 快捷命令
echo "【步骤5】快捷命令"
echo "────────────────────────────────────────────────"
echo "# 查看详细文档"
echo "cat docs/PROMPT_ENHANCER_GUIDE.md"
echo ""
echo "# 运行完整测试"
echo "python3 test_prompt_enhancer.py"
echo ""
echo "# 生成测试推文（会自动使用PromptEnhancer）"
echo "python main.py --persona personas/test.json --tweets 5"
echo ""

echo "=================================================="
echo "  ✅ 快速开始完成！"
echo "=================================================="
