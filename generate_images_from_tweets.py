#!/usr/bin/env python3
"""
从推文批次生成图片 - 使用native PyTorch实现

直接调用NativeImageGenerator,支持LoRA
"""
import sys
import os
import json
from pathlib import Path
import time
from typing import Optional, List, Dict

# 必须在导入其他模块前设置路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

zimage_path = project_root / "Z-Image" / "src"
if zimage_path.exists():
    sys.path.insert(0, str(zimage_path))

from loguru import logger
from core.native_image_generator import NativeImageGenerator
from core.multi_gpu_image_generator import MultiGPUImageGenerator

logger.remove()
logger.add(sys.stderr, level="INFO")


def load_tweet_batch(filepath: str) -> dict:
    """加载推文批次"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_images_for_batch(tweet_batch_path: str, num_gpus: int = 8):
    """
    为一个推文批次生成所有图片

    Args:
        tweet_batch_path: 推文批次JSON文件路径
        num_gpus: 使用的GPU数量 (1=单GPU, >1=多GPU并行)
    """
    logger.info(f"加载推文批次: {tweet_batch_path}")
    batch_data = load_tweet_batch(tweet_batch_path)

    persona_name = batch_data.get('persona', {}).get('name', 'unknown')
    lora_config = batch_data.get('persona', {}).get('lora', {})
    tweets = batch_data.get('tweets', [])

    logger.info(f"角色: {persona_name}")
    logger.info(f"推文数量: {len(tweets)}")
    logger.info(f"LoRA配置: {lora_config}")

    # 处理LoRA路径
    lora_path = None
    lora_strength = 0.8
    if lora_config and lora_config.get('model_path'):
        lora_path = lora_config['model_path']
        lora_strength = lora_config.get('strength', 0.8)

        # 处理相对路径
        if not os.path.isabs(lora_path):
            lora_path = os.path.join(project_root, lora_path)

        if not os.path.exists(lora_path):
            logger.warning(f"LoRA文件不存在: {lora_path}")
            lora_path = None

    output_dir = Path("output_full_pipeline")
    output_dir.mkdir(exist_ok=True)

    # 选择单GPU或多GPU模式
    if num_gpus > 1:
        logger.info(f"🚀 使用多GPU并行模式 ({num_gpus} GPUs)")
        results = _generate_multi_gpu(
            tweets, persona_name, lora_path, lora_strength, output_dir, num_gpus
        )
    else:
        logger.info("使用单GPU模式")
        results = _generate_single_gpu(
            tweets, persona_name, lora_path, lora_strength, output_dir
        )

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    failed_tweets = [(r['task_id'] + 1, r.get('error', 'Unknown')) for r in results if not r['success']]
    total_time = sum(r.get('elapsed', 0) for r in results)
    avg_time = total_time / success_count if success_count > 0 else 0

    logger.info(f"\n完成! 成功: {success_count}/{len(tweets)}, 总耗时: {total_time:.1f}s, 平均: {avg_time:.1f}s/张")

    if failed_tweets:
        logger.warning(f"失败的推文: {failed_tweets}")


def _generate_single_gpu(
    tweets: list,
    persona_name: str,
    lora_path: Optional[str],
    lora_strength: float,
    output_dir: Path
) -> List[Dict]:
    """单GPU顺序生成"""
    generator = NativeImageGenerator()
    results = []

    # 加载LoRA
    lora_applied = False
    if lora_path:
        logger.info(f"加载LoRA: {lora_path} (strength={lora_strength})")
        generator.lora_manager.load_lora(lora_path=lora_path, strength=lora_strength)
        lora_applied = True
        logger.success(f"✓ LoRA加载成功")

    try:
        for idx, tweet in enumerate(tweets, 1):
            image_gen = tweet.get('image_generation', {})
            scene_hint = image_gen.get('scene_hint', '')

            if not scene_hint:
                logger.warning(f"推文 {idx} 没有scene_hint,跳过")
                results.append({'success': False, 'task_id': idx - 1, 'error': '缺少scene_hint'})
                continue

            logger.info(f"[{idx}/{len(tweets)}] 生成图片...")

            start_time = time.time()

            try:
                # 生成图片
                image = generator.generate(
                    prompt=scene_hint,
                    progressive=True,
                    seed=42 + idx
                )

                elapsed = time.time() - start_time

                # 保存图片
                output_filename = f"{persona_name.replace(' ', '_')}_{idx:02d}.png"
                output_path = output_dir / output_filename
                image.save(output_path)

                logger.success(f"✓ 已保存: {output_path} ({elapsed:.1f}s)")

                results.append({
                    'success': True,
                    'task_id': idx - 1,
                    'output_path': str(output_path),
                    'elapsed': elapsed
                })

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"✗ 图片 {idx} 生成失败: {e}")
                results.append({
                    'success': False,
                    'task_id': idx - 1,
                    'error': str(e),
                    'elapsed': elapsed
                })

    finally:
        if lora_applied:
            logger.info("卸载LoRA...")
            generator.lora_manager.unload_lora()

    return results


def _generate_multi_gpu(
    tweets: list,
    persona_name: str,
    lora_path: Optional[str],
    lora_strength: float,
    output_dir: Path,
    num_gpus: int
) -> List[Dict]:
    """多GPU并行生成"""

    # 准备任务列表
    tasks = []
    for idx, tweet in enumerate(tweets, 1):
        image_gen = tweet.get('image_generation', {})
        scene_hint = image_gen.get('scene_hint', '')

        if not scene_hint:
            logger.warning(f"推文 {idx} 没有scene_hint,跳过")
            continue

        output_filename = f"{persona_name.replace(' ', '_')}_{idx:02d}.png"
        output_path = str(output_dir / output_filename)

        tasks.append({
            'prompt': scene_hint,
            'lora_path': lora_path,
            'lora_strength': lora_strength,
            'seed': 42 + idx,
            'output_path': output_path
        })

    # 使用多GPU生成器
    with MultiGPUImageGenerator(num_gpus=num_gpus) as multi_gen:
        results = multi_gen.generate_batch(tasks)

    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_images_from_tweets.py <tweet_batch_file> [num_gpus]")
        print("示例: python3 generate_images_from_tweets.py output_full_pipeline/Arabella_Sinclair_tweets.json 8")
        sys.exit(1)

    tweet_batch_path = sys.argv[1]
    num_gpus = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    logger.info("="*60)
    logger.info("图片生成 - Native PyTorch + LoRA")
    logger.info("="*60)
    logger.info(f"推文批次: {tweet_batch_path}")
    logger.info(f"GPU数量: {num_gpus}")
    logger.info("")

    generate_images_for_batch(tweet_batch_path, num_gpus)


if __name__ == "__main__":
    main()
