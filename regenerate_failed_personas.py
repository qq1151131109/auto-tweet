#!/usr/bin/env python3
"""
重新生成失败的3个personas的推文
专门针对Calendar JSON解析失败的情况，增加重试机制
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from generate_all_tweets_7days import DayByDayTweetGenerator

# 失败的3个persona文件
FAILED_PERSONAS = [
    "personas/byrecarvalho_fitness.json",
    "personas/taaarannn_exhibitionist.json",
    "personas/veronika_strict_mistress.json"
]


async def main():
    """重新生成失败的personas"""
    print("=" * 80)
    print("🔄 重新生成3个失败的personas")
    print("=" * 80)

    # API配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置OPENAI_API_KEY环境变量")
        sys.exit(1)

    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    max_concurrent = int(os.getenv("MAX_CONCURRENT", "50"))

    print(f"API: {api_base}")
    print(f"Model: {model}")
    print(f"并发数: {max_concurrent}")
    print("=" * 80)

    # 检查文件是否存在
    existing_personas = []
    for pf in FAILED_PERSONAS:
        if Path(pf).exists():
            existing_personas.append(pf)
            print(f"✓ 找到: {pf}")
        else:
            print(f"✗ 缺失: {pf}")

    if not existing_personas:
        print("❌ 没有找到任何失败的persona文件")
        sys.exit(1)

    print(f"\n将重新生成 {len(existing_personas)} 个personas")
    print()

    # 创建生成器
    generator = DayByDayTweetGenerator(
        api_key=api_key,
        api_base=api_base,
        model=model,
        max_concurrent=max_concurrent
    )

    start_time = datetime.now()

    # 串行生成（避免并发导致的问题）
    results = []
    for persona_file in existing_personas:
        try:
            result = await generator.generate_single_persona_7days(
                persona_file=persona_file,
                tweets_per_day=5,
                temperature=1.0
            )
            results.append(result)
        except Exception as e:
            print(f"\n❌ {Path(persona_file).stem} 生成失败: {e}")
            results.append({
                "persona": Path(persona_file).stem,
                "success_days": 0,
                "total_tweets": 0,
                "error": str(e)
            })

    # 统计结果
    duration = (datetime.now() - start_time).total_seconds()

    successful_personas = [r for r in results if r.get("total_tweets", 0) > 0]
    total_tweets = sum(r.get("total_tweets", 0) for r in successful_personas)

    print("\n" + "=" * 80)
    print("📊 重新生成结果统计")
    print("=" * 80)
    print(f"✅ 成功personas: {len(successful_personas)}/{len(existing_personas)}")
    print(f"📝 总推文数: {total_tweets}")
    print(f"⏱️  总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟)")
    if len(successful_personas) > 0:
        print(f"⚡ 平均每个persona: {duration/len(successful_personas):.1f}秒")
    print("=" * 80)

    # 显示仍然失败的
    still_failed = [r for r in results if r.get("total_tweets", 0) == 0]
    if still_failed:
        print("\n仍然失败的personas:")
        for r in still_failed:
            print(f"  ❌ {r['persona']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
