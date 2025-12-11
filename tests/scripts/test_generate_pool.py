#!/usr/bin/env python3
"""
测试内容池生成系统
为现有persona添加content_strategy并生成测试推文
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_client import LLMClientPool
from core.tweet_generator import BatchTweetGenerator


def add_content_strategy_to_persona(persona_path: Path) -> dict:
    """为现有persona添加content_strategy"""

    with open(persona_path, 'r', encoding='utf-8') as f:
        persona = json.load(f)

    # 检查是否已有content_strategy
    extensions = persona.get('data', {}).get('extensions', {})
    if 'content_strategy' in extensions:
        print(f"  ✓ 已有content_strategy")
        return persona

    # 根据persona名称/描述推断archetype
    persona_data = persona.get('data', {})
    name = persona_data.get('name', '').lower()
    description = persona_data.get('description', '').lower()
    personality = persona_data.get('personality', '').lower()

    # 简单推断规则
    if 'fitness' in description or 'gym' in description or 'workout' in personality:
        archetype = "Gym Girl"
    elif 'gamer' in description or 'gaming' in personality or 'e-girl' in description:
        archetype = "E-girl"
    elif 'baddie' in personality or 'assertive' in personality or 'dominant' in personality:
        archetype = "Baddie"
    else:
        archetype = "ABG"  # 默认最通用

    # 添加content_strategy
    if 'extensions' not in persona['data']:
        persona['data']['extensions'] = {}

    persona['data']['extensions']['content_strategy'] = {
        "archetype": archetype,
        "target_count": 10  # 测试用小数量
    }

    # 保存回文件
    with open(persona_path, 'w', encoding='utf-8') as f:
        json.dump(persona, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 添加了 content_strategy (archetype: {archetype})")

    return persona


async def test_generate_pool(persona_path: Path, count: int = 10):
    """测试为单个persona生成内容池"""

    print(f"\n{'='*80}")
    print(f"  测试: {persona_path.name}")
    print(f"{'='*80}\n")

    # 1. 添加content_strategy
    print("【步骤1】检查/添加 content_strategy...")
    persona = add_content_strategy_to_persona(persona_path)
    persona_name = persona['data']['name']
    print()

    # 2. 创建LLM客户端
    print("【步骤2】创建LLM客户端...")

    # 从环境变量或配置读取API key
    import os
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")

    if not api_key:
        print("❌ 未找到API KEY")
        print("   请设置环境变量: export OPENAI_API_KEY=your_key")
        return None

    llm_pool = LLMClientPool(
        api_key=api_key,
        api_base=os.getenv("API_BASE", "https://api.openai.com/v1"),
        model=os.getenv("MODEL", "gpt-4"),
        max_concurrent=10  # 测试用较小并发
    )

    print(f"  ✓ LLM客户端创建成功")
    print()

    # 3. 生成内容池
    print(f"【步骤3】生成 {count} 条推文...")
    print()

    generator = BatchTweetGenerator(llm_pool)

    try:
        result = await generator.generate_pool(
            persona=persona,
            count=count,
            temperature=1.0,
            explicit_nudity_allowed=False
        )

        # 4. 保存结果
        print("【步骤4】保存结果...")

        output_dir = Path("content_pool")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{persona_path.stem}_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 结果已保存: {output_file}")
        print()

        # 5. 显示统计
        print("【步骤5】生成统计:")
        print(f"  Persona: {result['persona']['name']}")
        print(f"  Archetype: {result['persona']['archetype']}")
        print(f"  成功生成: {len(result['tweets'])} 条")
        print()

        print("  内容分布:")
        for content_type, type_count in result['content_plan']['distribution'].items():
            print(f"    {content_type}: {type_count} 条")
        print()

        print("  多样性统计:")
        for content_type, stats in result['content_plan']['diversity_stats'].items():
            print(f"    {content_type}: {stats['unique_combinations']} 唯一组合")
        print()

        # 6. 显示前3条推文预览
        print("【步骤6】内容预览（前3条）:")
        for i, tweet in enumerate(result['tweets'][:3], 1):
            print(f"\n  [{i}] {tweet.get('content_type', '')} / {tweet.get('subtype', '')}")
            print(f"      Mood: {tweet.get('mood', '')}")
            print(f"      Tweet: {tweet['tweet_text'][:80]}...")
            print(f"      Scene: {tweet['image_generation']['scene_hint'][:100]}...")
        print()

        print(f"✅ {persona_name} 测试完成!\n")

        return result

    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_all_personas(count: int = 10, limit: int = None):
    """测试所有personas"""

    personas_dir = Path("personas")
    persona_files = sorted(personas_dir.glob("*.json"))

    if limit:
        persona_files = persona_files[:limit]

    print(f"\n🧪 内容池生成系统 - 批量测试")
    print(f"{'='*80}\n")
    print(f"找到 {len(persona_files)} 个personas")
    if limit:
        print(f"限制测试前 {limit} 个\n")
    else:
        print()

    results = []

    for persona_path in persona_files:
        result = await test_generate_pool(persona_path, count=count)
        if result:
            results.append({
                "persona": persona_path.name,
                "success": True,
                "count": len(result['tweets'])
            })
        else:
            results.append({
                "persona": persona_path.name,
                "success": False,
                "count": 0
            })

    # 总结
    print(f"\n{'='*80}")
    print("  批量测试总结")
    print(f"{'='*80}\n")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"成功: {len(successful)} / {len(results)}")
    print(f"失败: {len(failed)} / {len(results)}")
    print()

    if successful:
        print("成功的personas:")
        for r in successful:
            print(f"  ✓ {r['persona']}: {r['count']} 条推文")
        print()

    if failed:
        print("失败的personas:")
        for r in failed:
            print(f"  ✗ {r['persona']}")
        print()

    total_tweets = sum(r['count'] for r in results)
    print(f"总计生成: {total_tweets} 条推文")
    print()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="测试内容池生成系统")
    parser.add_argument('--persona', type=str, help='指定单个persona文件')
    parser.add_argument('--count', type=int, default=10, help='每个persona生成数量 (默认10)')
    parser.add_argument('--all', action='store_true', help='测试所有personas')
    parser.add_argument('--limit', type=int, help='限制测试persona数量')

    args = parser.parse_args()

    if args.persona:
        # 测试单个persona
        persona_path = Path(args.persona)
        if not persona_path.exists():
            print(f"❌ 文件不存在: {persona_path}")
            return

        await test_generate_pool(persona_path, count=args.count)

    elif args.all:
        # 测试所有personas
        await test_all_personas(count=args.count, limit=args.limit)

    else:
        # 默认：测试第一个persona
        personas_dir = Path("personas")
        persona_files = sorted(personas_dir.glob("*.json"))

        if not persona_files:
            print("❌ 未找到persona文件")
            return

        print(f"默认测试第一个persona: {persona_files[0].name}")
        print("使用 --all 测试所有personas\n")

        await test_generate_pool(persona_files[0], count=args.count)


if __name__ == "__main__":
    asyncio.run(main())
