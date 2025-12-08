#!/usr/bin/env python3
"""
批量生成所有推文的图片
使用多GPU并发处理84个JSON文件（420条推文）
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent))

from core.image_generator import ImageGenerationCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_images_for_file(
    coordinator: ImageGenerationCoordinator,
    json_file: Path,
    output_dir: str,
    index: int,
    total: int
):
    """为单个JSON文件生成图片"""
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"📍 [{index}/{total}] 处理: {json_file.name}")
        logger.info(f"{'='*70}")

        results = await coordinator.generate_from_tweets_batch(
            tweets_batch_file=str(json_file),
            output_dir=output_dir,
            use_multi_gpu=True  # 启用多GPU
        )

        success_count = sum(1 for r in results if r["status"] == "success")

        logger.info(f"✅ [{index}/{total}] 完成: {json_file.name}")
        logger.info(f"   成功: {success_count}/{len(results)}")

        return {
            "success": True,
            "file": json_file.name,
            "generated": success_count,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"❌ [{index}/{total}] 失败: {json_file.name} - {e}")
        return {
            "success": False,
            "file": json_file.name,
            "error": str(e)
        }


async def main():
    """主函数 - 批量生成所有图片"""
    print("=" * 80)
    print("🎨 批量图片生成: 84个文件 × 5条推文 = 420张图片")
    print("=" * 80)

    # 参数配置
    output_standalone_dir = Path("output_standalone")
    output_images_dir = Path("output_images")
    zimage_model_path = os.getenv("ZIMAGE_MODEL_PATH", "Z-Image/ckpts/Z-Image-Turbo")
    num_gpus = int(os.getenv("NUM_GPUS", "4"))  # 默认使用4个GPU

    # 获取所有JSON文件
    json_files = sorted(output_standalone_dir.glob("*.json"))

    if not json_files:
        print(f"❌ 错误: {output_standalone_dir} 目录下没有找到JSON文件")
        sys.exit(1)

    print(f"\nZ-Image模型: {zimage_model_path}")
    print(f"GPU数量: {num_gpus}")
    print(f"输出目录: {output_images_dir}")
    print(f"找到 {len(json_files)} 个推文批次文件")
    print("=" * 80)

    # 创建图片生成协调器
    coordinator = ImageGenerationCoordinator(
        model_path=zimage_model_path,
        num_gpus=num_gpus,
        use_diffusers=True  # 使用Diffusers模式以支持LoRA
    )

    start_time = datetime.now()

    # 🚀 串行处理所有文件（每个文件内部会多GPU并行）
    # 串行是因为每个文件可能有不同的LoRA，需要加载/卸载避免污染
    results = []
    for i, json_file in enumerate(json_files, 1):
        result = await generate_images_for_file(
            coordinator,
            json_file,
            str(output_images_dir),
            i,
            len(json_files)
        )
        results.append(result)

    # 统计结果
    duration = (datetime.now() - start_time).total_seconds()

    successful_files = [r for r in results if r.get("success")]
    failed_files = [r for r in results if not r.get("success")]
    total_images = sum(r.get("generated", 0) for r in successful_files)

    print("\n" + "=" * 80)
    print("📊 图片生成结果统计")
    print("=" * 80)
    print(f"✅ 成功文件: {len(successful_files)}/{len(json_files)}")
    print(f"❌ 失败文件: {len(failed_files)}")
    print(f"🖼️  总图片数: {total_images}")
    print(f"⏱️  总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟 / {duration/3600:.2f}小时)")
    if total_images > 0:
        print(f"⚡ 平均每张图片: {duration/total_images:.2f}秒")
    print("=" * 80)

    if failed_files:
        print("\n失败的文件:")
        for r in failed_files:
            print(f"  ❌ {r['file']}: {r.get('error', 'Unknown error')}")

    print("\n下一步操作:")
    print(f"1. 查看生成的图片: ls -lh {output_images_dir}/")
    print(f"2. 统计每个persona的图片数: ls {output_images_dir}/ | cut -d_ -f1 | sort | uniq -c")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
