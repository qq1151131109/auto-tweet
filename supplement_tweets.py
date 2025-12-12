#!/usr/bin/env python3
"""
补充未完成的推文生成
"""
import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")


def count_tweets_in_file(filepath: str) -> int:
    """统计文件中的推文数量"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return len(data.get('tweets', []))
    except Exception as e:
        logger.error(f"读取文件失败 {filepath}: {e}")
        return 0


def supplement_tweets(persona_file: str, current_count: int, target_count: int = 1000):
    """补充推文到目标数量"""

    needed = target_count - current_count

    if needed <= 0:
        logger.info(f"✓ {persona_file} 已有 {current_count} 条，无需补充")
        return True

    logger.info(f"补充 {persona_file}: {current_count} -> {target_count} (需要 {needed} 条)")

    # 构建命令
    cmd = [
        sys.executable,
        "main.py",
        "--persona", f"personas/{persona_file}",
        "--tweets", str(needed),
        "--api-key", os.getenv('API_KEY'),
        "--api-base", os.getenv('API_BASE', 'https://api.openai.com/v1'),
        "--model", os.getenv('MODEL', 'gpt-4'),
        "--max-concurrent", "100",
        "--output-dir", "output_standalone"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result.returncode == 0:
            logger.success(f"✓ {persona_file} 补充完成")
            return True
        else:
            logger.error(f"✗ {persona_file} 补充失败: {result.stderr[-200:]}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"✗ {persona_file} 超时")
        return False
    except Exception as e:
        logger.error(f"✗ {persona_file} 异常: {e}")
        return False


def main():
    """主函数"""

    # 需要补充的人设及其当前数量
    supplements = [
        ("jfz_45_soft_domme.json", 90),      # Lina Moreau
        ("jfz_131_princess.json", 396),      # Lilia Volkov
        ("jfz_46_church_wild.json", 834),    # Abigail Grace
        ("jfz_96_mommy_dom.json", 825),      # Evelina Holm
        ("keti_pet_handler.json", 938),      # Lara Valente
        ("jfz_89_bratty_sub.json", 983),     # Lina Voss
        ("jazmynmakenna_taboo.json", 883),   # Sydney Harlow
        ("taaarannn_exhibitionist.json", 994), # Alina Volkova
    ]

    logger.info("="*60)
    logger.info("推文补充任务")
    logger.info("="*60)
    logger.info(f"需要补充的人设: {len(supplements)}")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    results = []

    for persona_file, current_count in supplements:
        success = supplement_tweets(persona_file, current_count)
        results.append({
            'persona': persona_file,
            'success': success
        })

    # 统计
    success_count = sum(1 for r in results if r['success'])

    logger.info("\n" + "="*60)
    logger.info("补充完成!")
    logger.info("="*60)
    logger.info(f"成功: {success_count}/{len(results)}")
    logger.info(f"失败: {len(results) - success_count}/{len(results)}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
