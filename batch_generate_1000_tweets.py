#!/usr/bin/env python3
"""
批量为所有人设生成1000条推文 - 100并发
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")


async def generate_tweets_for_persona(persona_file: Path, num_tweets: int = 1000) -> dict:
    """为单个人设生成推文"""
    from main import main as generate_main

    persona_name = persona_file.stem
    output_dir = Path("output_standalone")
    output_dir.mkdir(exist_ok=True)

    logger.info(f"开始生成: {persona_name} ({num_tweets}条推文)")

    start_time = asyncio.get_event_loop().time()

    try:
        # 调用main.py的生成函数
        # 使用subprocess运行以避免状态污染
        import subprocess

        cmd = [
            sys.executable,
            "main.py",
            "--persona", str(persona_file),
            "--tweets", str(num_tweets),
            "--api-key", os.getenv('API_KEY'),
            "--api-base", os.getenv('API_BASE', 'https://api.openai.com/v1'),
            "--model", os.getenv('MODEL', 'gpt-4'),
            "--max-concurrent", "100",  # 100并发
            "--output-dir", "output_standalone"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )

        elapsed = asyncio.get_event_loop().time() - start_time

        if result.returncode == 0:
            logger.success(f"✓ {persona_name} 完成 ({elapsed:.1f}s)")
            return {
                'persona': persona_name,
                'status': 'success',
                'elapsed': elapsed,
                'stdout': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            }
        else:
            logger.error(f"✗ {persona_name} 失败 (返回码: {result.returncode})")
            return {
                'persona': persona_name,
                'status': 'failed',
                'elapsed': elapsed,
                'error': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
            }

    except subprocess.TimeoutExpired:
        logger.error(f"✗ {persona_name} 超时")
        return {
            'persona': persona_name,
            'status': 'timeout',
            'elapsed': 3600
        }
    except Exception as e:
        logger.error(f"✗ {persona_name} 异常: {e}")
        return {
            'persona': persona_name,
            'status': 'error',
            'error': str(e)
        }


async def main():
    """主函数 - 并发生成所有人设的推文"""

    # 获取所有人设
    personas_dir = Path('personas')
    persona_files = sorted([f for f in personas_dir.glob('*.json')])

    logger.info(f"{'='*60}")
    logger.info(f"批量生成推文任务")
    logger.info(f"{'='*60}")
    logger.info(f"人设数量: {len(persona_files)}")
    logger.info(f"每个人设: 1000条推文")
    logger.info(f"并发数: 100")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}\n")

    # 串行执行每个人设（避免过度负载）
    # 每个人设内部使用100并发
    results = []

    for idx, persona_file in enumerate(persona_files, 1):
        logger.info(f"\n[{idx}/{len(persona_files)}] 处理人设: {persona_file.name}")
        result = await generate_tweets_for_persona(persona_file, num_tweets=1000)
        results.append(result)

    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    total_time = sum(r.get('elapsed', 0) for r in results)

    logger.info(f"\n{'='*60}")
    logger.info(f"生成完成!")
    logger.info(f"{'='*60}")
    logger.info(f"成功: {success_count}/{len(results)}")
    logger.info(f"失败: {failed_count}/{len(results)}")
    logger.info(f"总耗时: {total_time:.1f}s ({total_time/60:.1f}分钟)")
    logger.info(f"平均耗时: {total_time/len(results):.1f}s/人设")
    logger.info(f"{'='*60}")

    if failed_count > 0:
        logger.warning("\n失败的人设:")
        for r in results:
            if r['status'] != 'success':
                logger.warning(f"  - {r['persona']}: {r.get('error', r['status'])}")


if __name__ == "__main__":
    asyncio.run(main())
