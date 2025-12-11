"""
测试推文长度检测和自动改写功能
"""
import asyncio
import json
from pathlib import Path
from core.tweet_generator import StandaloneTweetGenerator
from utils.llm_client import AsyncLLMClient

async def test_tweet_length_check():
    """测试推文长度检测和改写"""

    # 初始化LLM客户端
    llm_client = AsyncLLMClient(
        api_key="test-key",  # 需要替换为真实API key
        api_base="https://api.openai.com/v1"
    )

    generator = StandaloneTweetGenerator(llm_client)

    # 加载测试persona
    persona_files = list(Path("personas").glob("*.json"))
    if not persona_files:
        print("❌ 未找到persona文件,请先生成persona")
        return

    persona_path = persona_files[0]
    print(f"📄 使用persona: {persona_path.name}")

    with open(persona_path, 'r', encoding='utf-8') as f:
        persona = json.load(f)

    # 创建测试日历计划
    test_calendar_plan = {
        "slot": 1,
        "theme": "late night vulnerability",
        "content_direction": "intimate confession",
        "topic_type": "personal_moment",
        "recommended_time": "late_night"
    }

    print("\n🔄 生成测试推文...")
    try:
        result = await generator.generate_single_tweet(
            persona=persona,
            calendar_plan=test_calendar_plan,
            temperature=1.0
        )

        tweet_text = result.get("tweet_text", "")
        tweet_length = len(tweet_text)

        print(f"\n✅ 推文生成成功!")
        print(f"📏 推文长度: {tweet_length} 字符")
        print(f"📝 推文内容:\n{tweet_text}")

        if tweet_length <= 270:
            print(f"\n✅ 推文长度符合要求 (≤270字符)")
        else:
            print(f"\n⚠️ 推文超长 ({tweet_length}字符)")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("推文长度检测和改写功能测试")
    print("=" * 60)
    asyncio.run(test_tweet_length_check())
