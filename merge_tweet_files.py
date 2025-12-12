#!/usr/bin/env python3
"""
合并同一人设的多个推文文件
"""
import json
from pathlib import Path
from collections import defaultdict
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=''), level="INFO")


def merge_tweets():
    """合并同一人设的推文文件"""

    output_dir = Path('output_standalone')
    files = sorted(output_dir.glob('*_20251212_*.json'))

    # 按人设名分组
    persona_files = defaultdict(list)
    for f in files:
        with open(f, 'r') as file:
            data = json.load(file)
        persona_name = data.get('persona', {}).get('name', 'Unknown')
        persona_files[persona_name].append((f, data))

    logger.info(f"找到 {len(persona_files)} 个人设，共 {len(files)} 个文件\n")

    merged_count = 0

    for persona_name, file_list in sorted(persona_files.items()):
        if len(file_list) == 1:
            # 只有一个文件，无需合并
            tweets_count = len(file_list[0][1]['tweets'])
            logger.info(f"✓ {persona_name:25s} {tweets_count:4d}条 (单文件)")
            continue

        # 合并多个文件
        logger.info(f"🔄 {persona_name:25s} 合并 {len(file_list)} 个文件...")

        # 使用第一个文件作为base
        base_file, base_data = file_list[0]
        all_tweets = base_data['tweets'].copy()

        # 合并其他文件的tweets
        for f, data in file_list[1:]:
            all_tweets.extend(data['tweets'])
            logger.info(f"   + {f.name}: {len(data['tweets'])}条")

        # 重新编号slots
        for idx, tweet in enumerate(all_tweets, 1):
            tweet['slot'] = idx

        # 保存合并后的文件
        merged_filename = f"{persona_name}_{base_file.stem.split('_')[-1]}_merged.json"
        merged_path = output_dir / merged_filename

        base_data['tweets'] = all_tweets

        with open(merged_path, 'w', encoding='utf-8') as f:
            json.dump(base_data, f, indent=2, ensure_ascii=False)

        logger.info(f"   ✅ 合并完成: {len(all_tweets)}条 -> {merged_path.name}\n")
        merged_count += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"合并完成: {merged_count} 个人设")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    merge_tweets()
