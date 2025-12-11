#!/usr/bin/env python3
"""
测试高级图片生成方案

用法:
    # 测试高级模式 (三阶段渐进式)
    python test_advanced_generation.py --mode advanced

    # 测试备用模式 (单阶段生成)
    python test_advanced_generation.py --mode simple

    # 对比测试 (生成两张图对比)
    python test_advanced_generation.py --mode compare
"""
import asyncio
import sys
from pathlib import Path
import argparse

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator_advanced import ZImageGeneratorAdvanced
from config.image_config import (
    load_image_config,
    get_progressive_config,
    load_negative_prompt_template
)


async def test_advanced_mode():
    """测试高级模式（三阶段渐进式）"""
    print("🎨 测试高级模式（三阶段渐进式生成）\n")

    # 加载配置
    config = load_image_config()
    progressive_config = get_progressive_config(config)
    negative_prompt = load_negative_prompt_template(config)

    print(f"📋 配置信息:")
    print(f"   阶段1尺寸: {progressive_config['stage1_size']}")
    print(f"   阶段2尺寸: {progressive_config['stage2_size']}")
    print(f"   阶段3尺寸: {progressive_config['stage3_size']}")
    print(f"   负向提示词长度: {len(negative_prompt)} 字符\n")

    # 初始化生成器
    generator = ZImageGeneratorAdvanced(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda"
    )

    # 测试提示词
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    trigger_word = ""  # 如果有 LoRA 可以添加触发词

    print(f"📝 正向提示词: {positive_prompt[:100]}...\n")
    print(f"🎯 开始生成...\n")

    # 生成图片
    image = generator.generate_progressive(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word=trigger_word,
        **progressive_config
    )

    # 保存
    output_path = Path("output_images/test_advanced_mode.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


async def test_simple_mode():
    """测试备用模式（单阶段生成）"""
    print("🎨 测试备用模式（单阶段生成）\n")

    # 加载配置
    config = load_image_config()
    gen_params = config.get("generation", {})
    negative_prompt = load_negative_prompt_template(config)

    print(f"📋 配置信息:")
    print(f"   尺寸: {gen_params.get('width', 768)}×{gen_params.get('height', 1024)}")
    print(f"   步数: {gen_params.get('steps', 9)}")
    print(f"   CFG: {gen_params.get('cfg', 1.0)}\n")

    # 初始化生成器
    generator = ZImageGeneratorAdvanced(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda"
    )

    # 测试提示词（与高级模式相同）
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    trigger_word = ""

    print(f"📝 正向提示词: {positive_prompt[:100]}...\n")
    print(f"🎯 开始生成...\n")

    # 生成图片
    image = generator.generate_simple(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word=trigger_word,
        width=gen_params.get('width', 768),
        height=gen_params.get('height', 1024),
        steps=gen_params.get('steps', 9),
        cfg=gen_params.get('cfg', 1.0)
    )

    # 保存
    output_path = Path("output_images/test_simple_mode.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


async def test_compare_mode():
    """对比测试两种模式"""
    print("🎨 对比测试：高级模式 vs 备用模式\n")
    print("=" * 60)
    print()

    # 先测试备用模式
    print("【1/2】生成备用模式图片...")
    await test_simple_mode()

    print("\n" + "=" * 60 + "\n")

    # 再测试高级模式
    print("【2/2】生成高级模式图片...")
    await test_advanced_mode()

    print("=" * 60)
    print("\n✅ 对比测试完成！")
    print("\n请查看以下图片对比效果：")
    print("   备用模式: output_images/test_simple_mode.png")
    print("   高级模式: output_images/test_advanced_mode.png\n")


async def main():
    parser = argparse.ArgumentParser(description="测试高级图片生成方案")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["advanced", "simple", "compare"],
        default="compare",
        help="测试模式: advanced(高级), simple(备用), compare(对比)"
    )

    args = parser.parse_args()

    if args.mode == "advanced":
        await test_advanced_mode()
    elif args.mode == "simple":
        await test_simple_mode()
    elif args.mode == "compare":
        await test_compare_mode()


if __name__ == "__main__":
    asyncio.run(main())
