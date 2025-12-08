#!/usr/bin/env python3
"""
测试 Z-Image 环境配置
"""
import sys
import torch
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """测试环境配置"""
    logger.info("=" * 60)
    logger.info("🧪 测试 Z-Image 环境配置")
    logger.info("=" * 60)

    # 1. 检查 Python 版本
    logger.info(f"\n1️⃣ Python 版本: {sys.version}")

    # 2. 检查 PyTorch
    logger.info(f"\n2️⃣ PyTorch 版本: {torch.__version__}")
    logger.info(f"   CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"   CUDA 版本: {torch.version.cuda}")
        logger.info(f"   GPU 数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            logger.info(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
            memory_gb = torch.cuda.get_device_properties(i).total_memory / 1024**3
            logger.info(f"          显存: {memory_gb:.2f} GB")

    # 3. 检查 diffusers
    try:
        import diffusers
        logger.info(f"\n3️⃣ Diffusers 版本: {diffusers.__version__}")

        # 检查是否支持 Z-Image
        try:
            from diffusers import ZImagePipeline
            logger.info("   ✅ ZImagePipeline 可用")
        except ImportError:
            logger.error("   ❌ ZImagePipeline 不可用")
            return False
    except ImportError:
        logger.error("\n3️⃣ Diffusers 未安装")
        return False

    # 4. 检查其他依赖
    logger.info("\n4️⃣ 其他依赖:")
    try:
        import transformers
        logger.info(f"   Transformers: {transformers.__version__}")
    except:
        logger.error("   Transformers: ❌ 未安装")

    try:
        import safetensors
        logger.info(f"   Safetensors: ✅")
    except:
        logger.error("   Safetensors: ❌ 未安装")

    try:
        from PIL import Image
        logger.info(f"   Pillow: ✅")
    except:
        logger.error("   Pillow: ❌ 未安装")

    # 5. 检查模型文件
    model_path = Path("Z-Image/ckpts/Z-Image-Turbo")
    logger.info(f"\n5️⃣ 模型文件检查:")
    logger.info(f"   模型路径: {model_path.absolute()}")
    logger.info(f"   路径存在: {model_path.exists()}")

    if model_path.exists():
        # 检查关键文件
        key_files = [
            "model_index.json",
            "scheduler_config.json",
            "text_encoder/config.json",
            "transformer/config.json",
            "vae/config.json"
        ]

        for file in key_files:
            file_path = model_path / file
            status = "✅" if file_path.exists() else "❌"
            logger.info(f"   {status} {file}")

        # 检查模型权重
        safetensors_files = list(model_path.glob("**/*.safetensors"))
        logger.info(f"\n   模型权重文件数量: {len(safetensors_files)}")
        total_size = sum(f.stat().st_size for f in safetensors_files)
        logger.info(f"   总大小: {total_size / 1024**3:.2f} GB")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 环境检查完成")
    logger.info("=" * 60)
    return True


def test_model_loading():
    """测试模型加载"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 测试模型加载")
    logger.info("=" * 60)

    try:
        from diffusers import ZImagePipeline

        model_path = "Z-Image/ckpts/Z-Image-Turbo"
        logger.info(f"\n正在加载模型: {model_path}")
        logger.info("⚠️ 这可能需要几分钟...")

        # 加载模型（使用 float32 以减少显存使用）
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float32  # 测试时使用 float32

        logger.info(f"设备: {device}")
        logger.info(f"数据类型: {dtype}")

        pipeline = ZImagePipeline.from_pretrained(
            model_path,
            torch_dtype=dtype,
            low_cpu_mem_usage=False
        )
        pipeline.to(device)

        logger.info("✅ 模型加载成功！")

        # 检查模型组件
        logger.info("\n模型组件:")
        logger.info(f"   Text Encoder: {type(pipeline.text_encoder).__name__}")
        logger.info(f"   Transformer: {type(pipeline.transformer).__name__}")
        logger.info(f"   VAE: {type(pipeline.vae).__name__}")
        logger.info(f"   Scheduler: {type(pipeline.scheduler).__name__}")

        # 检查显存使用（如果使用 CUDA）
        if device == "cuda":
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            logger.info(f"\n显存使用:")
            logger.info(f"   已分配: {allocated:.2f} GB")
            logger.info(f"   已保留: {reserved:.2f} GB")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 模型加载测试完成")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试 Z-Image 环境配置")
    parser.add_argument(
        "--skip-model-loading",
        action="store_true",
        help="跳过模型加载测试（节省时间）"
    )

    args = parser.parse_args()

    # 测试环境
    env_ok = test_environment()

    if not env_ok:
        logger.error("\n❌ 环境检查失败，请检查依赖安装")
        sys.exit(1)

    # 测试模型加载（可选）
    if not args.skip_model_loading:
        model_ok = test_model_loading()
        if not model_ok:
            logger.error("\n❌ 模型加载失败")
            sys.exit(1)
    else:
        logger.info("\n⏭️ 跳过模型加载测试")

    logger.info("\n🎉 所有测试通过！Z-Image 环境配置正确。")
