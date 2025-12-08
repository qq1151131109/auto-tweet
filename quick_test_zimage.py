#!/usr/bin/env python3
"""
Z-Image 快速测试脚本 - 生成一张测试图片
"""
import torch
from diffusers import ZImagePipeline
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_image():
    """生成一张测试图片"""
    logger.info("=" * 60)
    logger.info("🎨 Z-Image 快速测试 - 生成测试图片")
    logger.info("=" * 60)

    # 配置
    model_path = "Z-Image/ckpts/Z-Image-Turbo"
    output_path = Path("test_output")
    output_path.mkdir(exist_ok=True)

    # 测试提示词
    prompt = "A beautiful young woman with long black hair, wearing a red dress, smiling, professional photography, high quality, detailed"

    logger.info(f"\n📝 提示词: {prompt}")
    logger.info(f"💾 输出目录: {output_path.absolute()}")

    # 加载模型
    logger.info(f"\n🔧 加载模型: {model_path}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    logger.info(f"   设备: {device}")
    logger.info(f"   数据类型: {dtype}")

    pipeline = ZImagePipeline.from_pretrained(
        model_path,
        torch_dtype=dtype,
        low_cpu_mem_usage=False
    )
    pipeline.to(device)

    logger.info("   ✅ 模型加载完成")

    # 可选：启用 Flash Attention
    if hasattr(pipeline.transformer, 'set_attention_backend'):
        try:
            pipeline.transformer.set_attention_backend("flash")
            logger.info("   ✅ 使用 Flash Attention")
        except:
            pass

    # 生成图片
    logger.info(f"\n🎨 生成图片...")
    logger.info(f"   分辨率: 1024x1024")
    logger.info(f"   步数: 9 (实际8步)")
    logger.info(f"   CFG: 0.0 (Turbo模式)")

    image = pipeline(
        prompt=prompt,
        height=1024,
        width=1024,
        num_inference_steps=9,  # 8 DiT forwards
        guidance_scale=0.0,     # Turbo 模式
        generator=torch.Generator(device).manual_seed(42)
    ).images[0]

    # 保存图片
    output_file = output_path / "test_zimage.png"
    image.save(output_file)

    logger.info(f"\n✅ 图片生成完成！")
    logger.info(f"   保存路径: {output_file.absolute()}")

    # 显存使用
    if device == "cuda":
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        logger.info(f"   显存使用: {allocated:.2f} GB")

    logger.info("\n" + "=" * 60)
    logger.info("🎉 测试完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    generate_test_image()
