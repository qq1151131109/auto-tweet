#!/usr/bin/env python3
"""
Test Native Image Generation

Validates the NativeImageGenerator implementation by generating test images
using the three-stage progressive pipeline.
"""

import sys
import time
from pathlib import Path
import json

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_basic_generation():
    """Test basic single-stage generation."""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Single-Stage Generation")
    logger.info("=" * 60)

    from core.native_image_generator import NativeImageGenerator

    # Initialize generator
    generator = NativeImageGenerator()

    # Test prompt
    prompt = (
        "A young woman with long brown hair, wearing a white sundress, "
        "standing in a sunlit garden with flowers. Natural lighting, "
        "soft focus background, candid photography"
    )

    # Generate image
    start_time = time.time()
    image = generator.generate(
        prompt=prompt,
        progressive=False,  # Single-stage
        seed=42
    )
    elapsed = time.time() - start_time

    # Save output
    output_dir = Path("output_native_test")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_single_stage.png"
    image.save(output_path)

    logger.success(
        f"✓ Single-stage generation complete: {image.size}, "
        f"time={elapsed:.1f}s, saved to {output_path}"
    )

    generator.unload()
    return True


def test_progressive_generation():
    """Test three-stage progressive generation."""
    logger.info("=" * 60)
    logger.info("TEST 2: Three-Stage Progressive Generation")
    logger.info("=" * 60)

    from core.native_image_generator import NativeImageGenerator

    # Initialize generator
    generator = NativeImageGenerator()

    # Test prompt
    prompt = (
        "A young woman with long brown hair, wearing a white sundress, "
        "standing in a sunlit garden with flowers. Natural lighting, "
        "soft focus background, candid photography"
    )

    # Generate image
    start_time = time.time()
    image = generator.generate(
        prompt=prompt,
        progressive=True,  # Three-stage progressive
        seed=42
    )
    elapsed = time.time() - start_time

    # Save output
    output_dir = Path("output_native_test")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_progressive.png"
    image.save(output_path)

    logger.success(
        f"✓ Progressive generation complete: {image.size}, "
        f"time={elapsed:.1f}s, saved to {output_path}"
    )

    generator.unload()
    return True


def test_with_lora():
    """Test generation with LoRA (if available)."""
    logger.info("=" * 60)
    logger.info("TEST 3: Generation with LoRA")
    logger.info("=" * 60)

    from core.native_image_generator import NativeImageGenerator

    # Check if LoRA exists
    lora_path = "lora/hollyjai.safetensors"
    if not Path(lora_path).exists():
        logger.warning(f"LoRA not found: {lora_path}, skipping test")
        return True

    # Initialize generator
    generator = NativeImageGenerator()

    # Test prompt with trigger word
    trigger_word = "sunway"
    prompt = (
        "A woman in a casual summer outfit, smiling at the camera, "
        "outdoor natural lighting, soft background blur"
    )

    # Generate image
    start_time = time.time()
    image = generator.generate(
        prompt=prompt,
        lora_path=lora_path,
        lora_strength=0.8,
        trigger_word=trigger_word,
        progressive=True,
        seed=42
    )
    elapsed = time.time() - start_time

    # Save output
    output_dir = Path("output_native_test")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_with_lora.png"
    image.save(output_path)

    logger.success(
        f"✓ LoRA generation complete: {image.size}, "
        f"time={elapsed:.1f}s, saved to {output_path}"
    )

    generator.unload()
    return True


def test_from_tweet_batch():
    """Test generation from actual tweet batch data."""
    logger.info("=" * 60)
    logger.info("TEST 4: Generation from Tweet Batch")
    logger.info("=" * 60)

    from core.native_image_generator import NativeImageGenerator

    # Load tweet batch
    tweet_file = "output_standalone/Valeria \"Val\" Ortiz_20251211_071653.json"
    if not Path(tweet_file).exists():
        logger.warning(f"Tweet file not found: {tweet_file}, skipping test")
        return True

    with open(tweet_file, 'r') as f:
        tweet_data = json.load(f)

    # Load persona for LoRA info
    persona_file = "personas/test_optimized.json"
    if not Path(persona_file).exists():
        logger.warning(f"Persona file not found: {persona_file}, skipping test")
        return True

    with open(persona_file, 'r') as f:
        persona_data = json.load(f)

    # Get LoRA config
    lora_config = persona_data.get('data', {}).get('lora', {})
    lora_path = lora_config.get('model_path')
    lora_strength = lora_config.get('strength', 0.8)
    trigger_word = persona_data.get('data', {}).get('name', '').split()[0].lower()

    # Initialize generator
    generator = NativeImageGenerator()

    # Generate first 3 images
    output_dir = Path("output_native_test")
    output_dir.mkdir(exist_ok=True)

    for i, tweet in enumerate(tweet_data['tweets'][:3], 1):
        scene_hint = tweet.get('image_generation', {}).get('scene_hint', '')

        if not scene_hint:
            logger.warning(f"Tweet {i} has no scene_hint, skipping")
            continue

        logger.info(f"Generating image {i}/3...")

        start_time = time.time()
        image = generator.generate(
            prompt=scene_hint,
            lora_path=lora_path,
            lora_strength=lora_strength,
            trigger_word=trigger_word,
            progressive=True,
            seed=42 + i
        )
        elapsed = time.time() - start_time

        # Save output
        output_path = output_dir / f"test_tweet_{i:02d}.png"
        image.save(output_path)

        logger.success(
            f"✓ Image {i}/3 complete: {image.size}, "
            f"time={elapsed:.1f}s, saved to {output_path}"
        )

    generator.unload()
    logger.success("✓ All tweet batch images generated successfully")
    return True


def main():
    """Run all tests."""
    logger.info("Starting Native Image Generation Tests")
    logger.info("")

    tests = [
        ("Basic Single-Stage Generation", test_basic_generation),
        ("Three-Stage Progressive Generation", test_progressive_generation),
        ("Generation with LoRA", test_with_lora),
        ("Generation from Tweet Batch", test_from_tweet_batch),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "PASS" if success else "FAIL"))
            logger.info("")
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "ERROR"))
            logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, status in results:
        icon = "✓" if status == "PASS" else "✗"
        logger.info(f"{icon} {test_name}: {status}")

    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.success("\n🎉 All tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
