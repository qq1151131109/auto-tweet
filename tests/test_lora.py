#!/usr/bin/env python3
"""
LoRA功能测试脚本
演示如何使用diffusers模式加载LoRA生成图片
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator import ZImageGenerator
import logging

logging.basicConfig(level=logging.INFO)


async def test_lora_generation():
    """测试LoRA图片生成"""

    print("\n" + "="*70)
    print("🧪 LoRA功能测试")
    print("="*70 + "\n")

    # 初始化生成器（diffusers模式，支持LoRA）
    generator = ZImageGenerator(
        model_path="Z-Image/ckpts/Z-Image-Turbo",
        device="cuda",
        use_diffusers=True  # 启用diffusers模式
    )

    # 测试提示词
    prompt = "A beautiful woman with long hair, wearing a red dress, smiling, high quality, detailed"

    # 场景1：不使用LoRA
    print("\n📸 场景1：基础模型生成（无LoRA）")
    image1 = generator.generate_image(
        positive_prompt=prompt,
        negative_prompt="ugly, deformed, low quality",
        width=1024,
        height=1024,
        steps=9,
        cfg=0.0,
        seed=42
    )

    output1 = Path("test_output/no_lora.png")
    output1.parent.mkdir(exist_ok=True)
    image1.save(output1)
    print(f"✓ 保存至: {output1}")

    # 场景2：使用LoRA（如果有）
    lora_path = "path/to/your/lora.safetensors"  # 替换为实际路径

    if Path(lora_path).exists():
        print(f"\n📸 场景2：使用LoRA生成")
        print(f"   LoRA: {lora_path}")

        image2 = generator.generate_image(
            positive_prompt=prompt,
            negative_prompt="ugly, deformed, low quality",
            width=1024,
            height=1024,
            steps=9,
            cfg=0.0,
            seed=42,
            lora_path=lora_path,
            lora_strength=0.8
        )

        output2 = Path("test_output/with_lora.png")
        image2.save(output2)
        print(f"✓ 保存至: {output2}")
    else:
        print(f"\n⚠️  LoRA文件不存在: {lora_path}")
        print("   跳过LoRA测试")

    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_lora_generation())
