#!/usr/bin/env python3
"""
测试 V2 高级生成器（Latent 空间操作）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator_advanced_v2 import ZImageGeneratorAdvancedV2
import yaml


def main():
    print("🎨 测试 V2 高级生成器（Latent 空间三阶段）\n")

    # 加载配置
    with open('config/image_generation.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 加载负向提示词
    neg_file = Path('config/negative_prompts_en.txt')
    with open(neg_file, 'r', encoding='utf-8') as f:
        neg_content = f.read()
    lines = [line for line in neg_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    print(f"✅ 配置加载完成")
    print(f"   负向提示词长度: {len(negative_prompt)} 字符\n")

    # 初始化生成器
    print("🔧 初始化生成器...\n")
    generator = ZImageGeneratorAdvancedV2(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda:1"  # 使用 GPU 1（GPU 0 被占用）
    )

    # 测试提示词
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    print(f"\n📝 正向提示词: {positive_prompt[:80]}...")
    print(f"🎯 开始三阶段生成...\n")

    # 生成图片（使用 ComfyUI 工作流的实际尺寸）
    image = generator.generate_progressive_latent(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word="",
        # ComfyUI 工作流的 latent 尺寸
        stage1_latent_size=(224, 176),  # (H, W)
        stage2_latent_size=(432, 336),
        stage3_latent_size=(864, 672),
        # ComfyUI 工作流的参数
        stage1_steps=9,
        stage2_steps=16,
        stage3_steps=16,
        stage1_cfg=2.0,
        stage2_cfg=1.0,
        stage3_cfg=1.0,
        stage2_denoise=0.7,
        stage3_denoise=0.6
    )

    # 保存
    output_path = Path("output_images/test_v2_latent_progressive.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


if __name__ == "__main__":
    main()
