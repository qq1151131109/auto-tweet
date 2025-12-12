#!/usr/bin/env python3
"""
批量生成测试图片 - 为每个人设的前10条推文生成图片
"""
import subprocess
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    """批量生成测试图片"""

    num_gpus = 4  # 使用0-3号GPU

    final_dir = Path('output_standalone/final')
    test_files = sorted(final_dir.glob('*_test10.json'))

    logger.info("="*60)
    logger.info("批量图片生成测试")
    logger.info("="*60)
    logger.info(f"人设数量: {len(test_files)}")
    logger.info(f"每个人设: 10张图")
    logger.info(f"GPU数量: {num_gpus}")
    logger.info(f"总图片数: {len(test_files) * 10}")
    logger.info("="*60)
    logger.info("")

    success_count = 0
    failed_personas = []

    for idx, test_file in enumerate(test_files, 1):
        logger.info(f"\n[{idx}/{len(test_files)}] 处理: {test_file.name}")

        cmd = [
            sys.executable,
            "generate_images_from_tweets.py",
            str(test_file),
            str(num_gpus)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                logger.success(f"✓ {test_file.stem} 完成")
                success_count += 1
            else:
                logger.error(f"✗ {test_file.stem} 失败")
                logger.error(f"  错误: {result.stderr[-200:]}")
                failed_personas.append(test_file.name)

        except subprocess.TimeoutExpired:
            logger.error(f"✗ {test_file.stem} 超时")
            failed_personas.append(test_file.name)
        except Exception as e:
            logger.error(f"✗ {test_file.stem} 异常: {e}")
            failed_personas.append(test_file.name)

    logger.info("\n" + "="*60)
    logger.info("生成完成!")
    logger.info("="*60)
    logger.info(f"成功: {success_count}/{len(test_files)}")
    logger.info(f"失败: {len(failed_personas)}/{len(test_files)}")

    if failed_personas:
        logger.info("\n失败的人设:")
        for name in failed_personas:
            logger.info(f"  - {name}")

    logger.info("="*60)


if __name__ == "__main__":
    main()
