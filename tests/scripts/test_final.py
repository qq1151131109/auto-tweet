#!/usr/bin/env python3
"""
最终测试：使用合理尺寸的 Latent 空间三阶段生成
目标：768×1024 最终输出
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator_advanced_v2 import ZImageGeneratorAdvancedV2
import yaml


def main():
    print("🎨 最终测试：Latent 空间三阶段生成（合理尺寸）\n")

    # 加载负向提示词
    neg_file = Path('config/negative_prompts_en.txt')
    with open(neg_file, 'r', encoding='utf-8') as f:
        neg_content = f.read()
    lines = [line for line in neg_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    print(f"✅ 配置加载完成\n")

    # 初始化生成器
    print("🔧 初始化生成器（使用 GPU 2，避免 0 和 1 被占用）...\n")
    generator = ZImageGeneratorAdvancedV2(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda:2"  # 使用 GPU 2
    )

    # 测试提示词
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    print(f"📝 正向提示词: {positive_prompt[:80]}...")
    print(f"🎯 开始三阶段生成（合理尺寸）...\n")

    # 合理的 latent 尺寸（适配 768×1024 输出）
    # Latent 尺寸 = 像素尺寸 / 8
    image = generator.generate_progressive_latent(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word="",
        # Latent 空间尺寸（H, W）
        stage1_latent_size=(85, 64),   # → 680×512 像素
        stage2_latent_size=(106, 79),  # → 848×632 像素
        stage3_latent_size=(128, 96),  # → 1024×768 像素
        # 参数
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
    output_path = Path("output_images/test_final_latent_progressive.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


if __name__ == "__main__":
    main()
