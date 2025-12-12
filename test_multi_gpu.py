#!/usr/bin/env python3
"""
测试多GPU并行图片生成
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

zimage_path = project_root / "Z-Image" / "src"
if zimage_path.exists():
    sys.path.insert(0, str(zimage_path))

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    """测试多GPU并行生成"""
    import torch

    # 检查GPU数量
    num_gpus = torch.cuda.device_count()
    logger.info(f"检测到 {num_gpus} 个GPU")

    if num_gpus < 2:
        logger.warning("需要至少2个GPU才能测试多GPU并行")
        sys.exit(1)

    # 查找一个tweet batch文件
    output_dir = Path("output_full_pipeline")
    tweet_files = list(output_dir.glob("*_tweets.json"))

    if not tweet_files:
        logger.error("未找到推文批次文件,请先运行推文生成")
        sys.exit(1)

    tweet_file = tweet_files[0]
    logger.info(f"使用推文文件: {tweet_file}")

    # 导入生成函数
    from generate_images_from_tweets import generate_images_for_batch

    # 测试多GPU生成 (使用所有可用GPU)
    logger.info(f"="*60)
    logger.info(f"开始多GPU并行测试 ({num_gpus} GPUs)")
    logger.info(f"="*60)

    generate_images_for_batch(str(tweet_file), num_gpus=num_gpus)

    logger.success("✓ 多GPU测试完成!")


if __name__ == "__main__":
    main()
