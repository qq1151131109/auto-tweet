#!/usr/bin/env python3
"""
实用版本：适配我们实际需要的 768×1024 输出
不追求完全复刻 ComfyUI 的超大尺寸
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator_advanced_v2 import ZImageGeneratorAdvancedV2


def main():
    print("🎨 实用版本：三阶段生成 768×1024\n")

    # 加载负向提示词
    neg_file = Path('config/negative_prompts_en.txt')
    with open(neg_file, 'r', encoding='utf-8') as f:
        neg_content = f.read()
    lines = [line for line in neg_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    print(f"✅ 负向提示词加载完成 ({len(negative_prompt)} 字符)\n")

    # 初始化生成器
    print("🔧 初始化生成器（GPU 3）...\n")
    generator = ZImageGeneratorAdvancedV2(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda:3"  # 使用 GPU 3
    )

    # 测试提示词
    positive_prompt = (
        "photo of a young woman with long brown hair, "
        "wearing casual clothes, sitting in a coffee shop, "
        "natural lighting from window, candid moment, "
        "looking at camera with gentle smile"
    )

    print(f"📝 提示词: {positive_prompt[:60]}...")
    print(f"🎯 开始三阶段生成...\n")

    # 按照 ComfyUI 的比例，但缩小到实际需要的尺寸
    # 目标：768×1024
    # 比例保持：约 0.25 → 0.4 → 0.75 倍
    image = generator.generate_progressive_latent(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        trigger_word="",
        # 渐进式尺寸 (H, W)
        stage1_latent_size=(256, 192),   # 小尺寸基础 (16的倍数)
        stage2_latent_size=(512, 384),   # 中间精修
        stage3_latent_size=(1024, 768),  # 最终输出 768×1024
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
    output_path = Path("output_images/test_practical_768x1024.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)

    print(f"\n✅ 生成完成！")
    print(f"   保存至: {output_path}")
    print(f"   尺寸: {image.size}\n")


if __name__ == "__main__":
    main()
