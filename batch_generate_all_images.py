#!/usr/bin/env python3
"""
批量图片生成 - 支持模型复用,避免重复加载

用法:
    python3 batch_generate_all_images.py output_full_pipeline/*_tweets.json
"""
import sys
import os
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

zimage_path = project_root / "Z-Image" / "src"
if zimage_path.exists():
    sys.path.insert(0, str(zimage_path))

import json
import time
from loguru import logger
from core.native_image_generator import NativeImageGenerator

logger.remove()
logger.add(sys.stderr, level="INFO")


def batch_generate_images(tweet_batch_files: list, output_dir: str = "output_full_pipeline"):
    """
    批量生成图片,所有batch共享同一个generator

    Args:
        tweet_batch_files: 推文批次文件列表
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 初始化generator一次,所有batch共享
    logger.info("=" * 60)
    logger.info("初始化图片生成器...")
    logger.info("=" * 60)
    generator = NativeImageGenerator()

    total_images = 0
    total_time = 0
    current_lora = None

    for batch_idx, batch_file in enumerate(tweet_batch_files, 1):
        logger.info(f"\n[{batch_idx}/{len(tweet_batch_files)}] 处理: {batch_file}")

        # 加载batch数据
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)

        persona_name = batch_data.get('persona', {}).get('name', 'unknown')
        lora_config = batch_data.get('persona', {}).get('lora', {})
        tweets = batch_data.get('tweets', [])

        logger.info(f"  角色: {persona_name}")
        logger.info(f"  推文数: {len(tweets)}")

        # 切换LoRA(如果需要)
        lora_path = lora_config.get('model_path') if lora_config else None
        if lora_path:
            # 处理相对路径
            if not os.path.isabs(lora_path):
                lora_path = os.path.join(project_root, lora_path)

            # 只在LoRA变化时重新加载
            if lora_path != current_lora:
                # 卸载旧LoRA
                if current_lora:
                    logger.info(f"  卸载LoRA: {current_lora}")
                    generator.lora_manager.unload_lora()

                # 加载新LoRA
                if os.path.exists(lora_path):
                    lora_strength = lora_config.get('strength', 0.8)
                    logger.info(f"  加载LoRA: {lora_path} (strength={lora_strength})")
                    generator.lora_manager.load_lora(lora_path, lora_strength)
                    current_lora = lora_path
                else:
                    logger.warning(f"  LoRA文件不存在: {lora_path}")
                    current_lora = None
        else:
            # 如果当前batch不需要LoRA,但之前加载了,需要卸载
            if current_lora:
                logger.info("  卸载LoRA(当前batch不需要)")
                generator.lora_manager.unload_lora()
                current_lora = None

        # 生成图片
        batch_start = time.time()
        for idx, tweet in enumerate(tweets, 1):
            scene_hint = tweet.get('image_generation', {}).get('scene_hint', '')
            if not scene_hint:
                logger.warning(f"    推文 {idx} 缺少scene_hint,跳过")
                continue

            logger.info(f"    [{idx}/{len(tweets)}] 生成图片...")

            try:
                start_time = time.time()
                image = generator.generate(
                    prompt=scene_hint,
                    progressive=True,
                    seed=42 + idx
                )
                elapsed = time.time() - start_time

                # 保存
                output_filename = f"{persona_name.replace(' ', '_')}_{idx:02d}.png"
                output_file = output_path / output_filename
                image.save(output_file)

                total_images += 1
                total_time += elapsed
                logger.success(f"    ✓ {output_filename} ({elapsed:.1f}s)")

            except Exception as e:
                logger.error(f"    ✗ 失败: {e}")

        batch_elapsed = time.time() - batch_start
        logger.info(f"  Batch完成: {len(tweets)}张, 耗时 {batch_elapsed:.1f}s")

    # 清理
    if current_lora:
        logger.info("\n清理: 卸载LoRA")
        generator.lora_manager.unload_lora()

    # 统计
    avg_time = total_time / total_images if total_images > 0 else 0
    logger.info("\n" + "=" * 60)
    logger.info("批量生成完成!")
    logger.info("=" * 60)
    logger.info(f"总图片数: {total_images}")
    logger.info(f"总耗时: {total_time:.1f}s ({total_time/60:.1f}min)")
    logger.info(f"平均: {avg_time:.1f}s/张")
    logger.info(f"输出目录: {output_path}")
    logger.info("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 batch_generate_all_images.py <tweet_batch_files...>")
        print("示例: python3 batch_generate_all_images.py output_full_pipeline/*_tweets.json")
        sys.exit(1)

    tweet_files = sys.argv[1:]
    logger.info(f"找到 {len(tweet_files)} 个推文批次文件")

    batch_generate_images(tweet_files)


if __name__ == "__main__":
    main()
