#!/usr/bin/env python3
"""
测试简化版：像素空间三阶段渐进式生成
不使用复杂的 latent 操作，直接用 img2img
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator_advanced import ZImageGeneratorAdvanced  # 使用原来的 V1
import yaml


def main():
    print("🎨 测试简化版三阶段生成（像素空间 img2img）\n")

    # 加载配置
    with open('config/image_generation.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 加载负向提示词
    neg_file = Path('config/negative_prompts_en.txt')
    with open(neg_file, 'r', encoding='utf-8') as f:
        neg_content = f.read()
    lines = [line for line in neg_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    print(f"✅ 配置加载完成\n")

    # 初始化生成器
    print("🔧 初始化生成器...\n")
    generator = ZImageGeneratorAdvanced(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda:1"
    )

    # 测试提示词
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    print(f"📝 正向提示词: {positive_prompt[:80]}...")
    print(f"🎯 开始三阶段生成（像素空间）...\n")

    # 使用合理的像素尺寸（不是 latent）
    image = generator.generate_progressive(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word="",
        # 像素空间尺寸
        stage1_size=(512, 672),   # 基础生成
        stage2_size=(640, 832),   # 中间精修
        stage3_size=(768, 1024),  # 最终输出
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
    output_path = Path("output_images/test_v1_pixel_progressive.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


if __name__ == "__main__":
    main()
