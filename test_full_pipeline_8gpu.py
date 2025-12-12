#!/usr/bin/env python3
"""
完整流程测试: 人设 → 推文 → 图片生成 (8卡并行)

测试配置:
- 5个角色,每个角色4张图,共20张图
- 使用8卡并行生成图片
- 包含LoRA加载和应用
"""
import sys
import os
import time
import json
from pathlib import Path
from loguru import logger

# Add project root and Z-Image to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add Z-Image to path (needed for model loading)
zimage_path = project_root / "Z-Image" / "src"
if zimage_path.exists() and str(zimage_path) not in sys.path:
    sys.path.insert(0, str(zimage_path))

# Get API key from environment
from dotenv import load_dotenv
load_dotenv()

# Try both OPENAI_API_KEY and LLM_API_KEY
API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY') or os.getenv('API_KEY')
API_BASE = os.getenv('LLM_API_BASE', 'https://api.openai.com/v1')
MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')


# 选择5个有LoRA的角色
PERSONAS = [
    "personas/hollyjai_corporate.json",
    "personas/byrecarvalho_fitness.json",
    "personas/jazmynmakenna_taboo.json",
    "personas/jfz_131_princess.json",
    "personas/jfz_45_soft_domme.json",
]

TWEETS_PER_PERSONA = 4
NUM_GPUS = 8
OUTPUT_DIR = Path("output_full_pipeline")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_persona(persona_path: str) -> dict:
    """Load persona JSON file."""
    with open(persona_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_tweets_for_persona(persona_path: str, num_tweets: int) -> str:
    """
    为单个人设生成推文批次

    Returns:
        tweet_batch_path: 生成的推文批次文件路径
    """
    import asyncio
    from core.tweet_generator import BatchTweetGenerator
    from utils.llm_client import LLMClientPool

    logger.info(f"Generating {num_tweets} tweets for {persona_path}")

    persona = load_persona(persona_path)
    persona_name = persona['data']['name']

    # 初始化LLM客户端池和推文生成器
    llm_pool = LLMClientPool(
        api_key=API_KEY,
        api_base=API_BASE,
        model=MODEL,
        max_concurrent=20
    )
    tweet_gen = BatchTweetGenerator(llm_pool)

    # 生成推文
    start_time = time.time()

    # Generate a simple calendar entry for testing
    calendar = {
        "persona_name": persona_name,
        "calendar": {
            f"2025-12-{12+i:02d}": {
                "content_type": "daily_life",
                "topic": "Casual selfie",
                "mood": "relaxed",
                "location": "bedroom"
            }
            for i in range(num_tweets)
        }
    }

    batch_result = asyncio.run(tweet_gen.generate_batch(
        persona=persona,
        calendar=calendar,
        tweets_count=num_tweets,
        temperature=1.0
    ))
    elapsed = time.time() - start_time

    tweets = batch_result.get('tweets', [])
    logger.info(f"Generated {len(tweets)} tweets in {elapsed:.1f}s")

    # Save tweet batch (batch_result already has correct structure)
    output_path = OUTPUT_DIR / f"{persona_name}_tweets.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(batch_result, f, indent=2, ensure_ascii=False)

    logger.success(f"Saved tweet batch to {output_path}")
    return str(output_path)


def generate_images_for_batch(tweet_batch_path: str, num_gpus: int):
    """
    为推文批次生成图片 (多GPU并行)
    """
    from core.native_image_generator import NativeImageGenerator

    logger.info(f"Generating images for {tweet_batch_path} using {num_gpus} GPUs")

    # 加载推文批次
    with open(tweet_batch_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)

    persona_name = batch_data['persona']['name']
    tweets = batch_data['tweets']
    lora_config = batch_data['persona'].get('lora', {})

    logger.info(f"Found {len(tweets)} tweets for {persona_name}")
    if lora_config:
        logger.info(f"LoRA config: {lora_config}")

    # 初始化图片生成器
    generator = NativeImageGenerator(num_gpus=num_gpus)

    try:
        # 生成所有图片
        start_time = time.time()

        for idx, tweet in enumerate(tweets, 1):
            logger.info(f"Generating image {idx}/{len(tweets)} for {persona_name}")

            # 准备生成参数
            scene_hint = tweet.get('image_generation', {}).get('scene_hint', '')
            if not scene_hint:
                logger.warning(f"Tweet {idx} has no scene_hint, skipping")
                continue

            # 生成图片
            output_path = OUTPUT_DIR / f"{persona_name}_{idx:02d}.png"

            image = generator.generate(
                prompt=scene_hint,
                lora_path=lora_config.get('model_path'),
                lora_strength=lora_config.get('strength', 0.8),
                width=672,
                height=864,
                progressive=True,
                seed=42 + idx
            )

            # 保存图片
            image.save(output_path)
            logger.success(f"✓ Saved image to {output_path}")

        elapsed = time.time() - start_time
        logger.success(f"Generated {len(tweets)} images in {elapsed:.1f}s ({elapsed/len(tweets):.1f}s/img)")

    finally:
        generator.unload()


def main():
    logger.info("=" * 60)
    logger.info("完整流程测试: 人设 → 推文 → 图片 (8卡并行)")
    logger.info("=" * 60)
    logger.info(f"角色数量: {len(PERSONAS)}")
    logger.info(f"每个角色推文数: {TWEETS_PER_PERSONA}")
    logger.info(f"总图片数: {len(PERSONAS) * TWEETS_PER_PERSONA}")
    logger.info(f"GPU数量: {NUM_GPUS}")
    logger.info("")

    overall_start = time.time()
    tweet_batches = []

    # Step 1: 为所有角色生成推文
    logger.info("=" * 60)
    logger.info("STEP 1: 生成推文批次")
    logger.info("=" * 60)

    for persona_path in PERSONAS:
        try:
            batch_path = generate_tweets_for_persona(persona_path, TWEETS_PER_PERSONA)
            tweet_batches.append(batch_path)
        except Exception as e:
            logger.error(f"Failed to generate tweets for {persona_path}: {e}")
            continue

    logger.info(f"\n✓ Generated {len(tweet_batches)} tweet batches\n")

    # Step 2: 为所有推文批次生成图片 (8卡并行)
    logger.info("=" * 60)
    logger.info("STEP 2: 生成图片 (8卡并行)")
    logger.info("=" * 60)

    for batch_path in tweet_batches:
        try:
            generate_images_for_batch(batch_path, num_gpus=NUM_GPUS)
        except Exception as e:
            logger.error(f"Failed to generate images for {batch_path}: {e}")
            continue

    # 统计结果
    overall_elapsed = time.time() - overall_start
    generated_images = list(OUTPUT_DIR.glob("*.png"))

    logger.info("")
    logger.info("=" * 60)
    logger.info("测试完成!")
    logger.info("=" * 60)
    logger.info(f"总耗时: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f}min)")
    logger.info(f"生成的图片: {len(generated_images)}/{len(PERSONAS) * TWEETS_PER_PERSONA}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"平均每张图: {overall_elapsed/len(generated_images):.1f}s" if generated_images else "N/A")

    # 显示生成的图片
    logger.info("\n生成的图片列表:")
    for img in sorted(generated_images):
        size_mb = img.stat().st_size / 1024 / 1024
        logger.info(f"  {img.name} ({size_mb:.2f}MB)")


if __name__ == "__main__":
    main()
