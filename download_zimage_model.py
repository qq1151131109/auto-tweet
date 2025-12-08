#!/usr/bin/env python3
"""
下载 Z-Image-Turbo 模型到本地
"""
import os
from pathlib import Path
from huggingface_hub import snapshot_download
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_zimage_model(
    model_id: str = "Tongyi-MAI/Z-Image-Turbo",
    local_dir: str = "Z-Image/ckpts/Z-Image-Turbo",
    resume_download: bool = True
):
    """
    从 HuggingFace 下载 Z-Image-Turbo 模型

    Args:
        model_id: HuggingFace 模型 ID
        local_dir: 本地保存目录
        resume_download: 是否支持断点续传
    """
    logger.info(f"📥 开始下载 Z-Image-Turbo 模型...")
    logger.info(f"   模型 ID: {model_id}")
    logger.info(f"   保存路径: {local_dir}")

    # 创建目录
    local_path = Path(local_dir)
    local_path.mkdir(parents=True, exist_ok=True)

    try:
        # 下载模型
        snapshot_download(
            repo_id=model_id,
            local_dir=str(local_path),
            resume_download=resume_download,
            local_dir_use_symlinks=False  # 不使用符号链接，直接复制文件
        )

        logger.info(f"✅ 模型下载完成！")
        logger.info(f"   保存在: {local_path.absolute()}")

        # 检查文件
        files = list(local_path.glob("**/*"))
        logger.info(f"\n📂 已下载文件数量: {len(files)}")

        # 显示主要文件
        main_files = [f for f in files if f.suffix in ['.safetensors', '.json', '.txt', '.md']]
        if main_files:
            logger.info("\n主要文件:")
            for f in sorted(main_files)[:10]:  # 显示前10个
                size_mb = f.stat().st_size / 1024 / 1024
                logger.info(f"   - {f.name} ({size_mb:.2f} MB)")

        return str(local_path.absolute())

    except Exception as e:
        logger.error(f"❌ 下载失败: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="下载 Z-Image-Turbo 模型")
    parser.add_argument(
        "--model-id",
        default="Tongyi-MAI/Z-Image-Turbo",
        help="HuggingFace 模型 ID"
    )
    parser.add_argument(
        "--local-dir",
        default="Z-Image/ckpts/Z-Image-Turbo",
        help="本地保存目录"
    )
    parser.add_argument(
        "--use-mirror",
        action="store_true",
        help="使用国内镜像加速（设置 HF_ENDPOINT）"
    )

    args = parser.parse_args()

    # 如果使用镜像
    if args.use_mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        logger.info("🌐 使用 HuggingFace 镜像: https://hf-mirror.com")

    download_zimage_model(
        model_id=args.model_id,
        local_dir=args.local_dir
    )
