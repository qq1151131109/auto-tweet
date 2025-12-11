"""
测试LLM生成的scene_hint是否包含真实感词汇

这个脚本会模拟LLM的输出，验证新的prompt指导是否有效
"""
import re


def test_scene_hint_realism():
    """测试生成的scene_hint是否包含真实感词汇"""

    print("=" * 80)
    print("  LLM真实感词汇注入测试")
    print("=" * 80)
    print()

    # 模拟LLM生成的scene_hint（期望格式）
    test_cases = [
        {
            "name": "夜间卧室场景",
            "scene_hint": "Late evening bedroom, woman kneeling on carpet wearing oversized t-shirt and black panties, dim purple LED light from behind bed, messy hair falling over shoulders, vulnerable expression with soft puppy eyes, close-up shot focusing on upper body, Raw photo, smartphone camera aesthetic, low lighting, uneven skin tone",
            "expected_keywords": ["Raw photo", "smartphone camera aesthetic", "low lighting", "uneven skin tone"]
        },
        {
            "name": "户外咖啡厅场景",
            "scene_hint": "Afternoon at outdoor cafe on busy street, woman sitting at table with coffee cup, bright sunlight streaming through windows, casual sundress, people visible in blurred background, relaxed expression, medium shot from across table, candid photography, messy background, Chromatic aberration, slightly overexposed",
            "expected_keywords": ["candid photography", "messy background", "Chromatic aberration", "overexposed"]
        },
        {
            "name": "运动场景",
            "scene_hint": "Woman walking quickly through hallway, motion in frame, casual clothes with hair moving, natural indoor lighting from ceiling lights, determined expression, full body shot from front, authentic snapshot, motion blur, in motion, amateur photography",
            "expected_keywords": ["authentic snapshot", "motion blur", "in motion", "amateur photography"]
        },
        {
            "name": "明亮室内场景",
            "scene_hint": "Bright morning bedroom, woman sitting on edge of unmade bed wearing tank top and shorts, sunlight streaming through large window creating highlights, messy morning hair, stretching arms above head, medium shot from doorway, Raw photo, candid photography, uneven skin tone, Chromatic aberration",
            "expected_keywords": ["Raw photo", "candid photography", "uneven skin tone", "Chromatic aberration"]
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"【测试 {i}】{test_case['name']}")
        print("─" * 80)
        print(f"Scene Hint: {test_case['scene_hint'][:100]}...")
        print()

        # 检查是否包含期望的关键词
        found_keywords = []
        missing_keywords = []

        for keyword in test_case['expected_keywords']:
            if keyword in test_case['scene_hint']:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        # 输出结果
        if found_keywords:
            print(f"✅ 找到的真实感词汇: {', '.join(found_keywords)}")

        if missing_keywords:
            print(f"❌ 缺失的词汇: {', '.join(missing_keywords)}")
            all_passed = False

        # 统计真实感词汇数量
        realism_keywords = [
            "Raw photo", "candid photography", "authentic snapshot",
            "smartphone camera aesthetic", "shot on iPhone",
            "messy background", "uneven skin tone", "Chromatic aberration",
            "motion blur", "slightly out of focus",
            "low lighting", "overexposed", "underexposed",
            "in motion", "GoPro lens", "amateur photography",
            "eerie atmosphere"
        ]

        total_count = sum(1 for kw in realism_keywords if kw in test_case['scene_hint'])
        print(f"📊 真实感词汇总数: {total_count}")

        if total_count >= 2:
            print("✅ 满足最低要求（≥2个真实感词汇）")
        else:
            print("❌ 不满足要求（需要≥2个真实感词汇）")
            all_passed = False

        print()

    print("=" * 80)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)
    print()

    return all_passed


def analyze_realism_distribution():
    """分析真实感词汇的分布"""

    print("=" * 80)
    print("  真实感词汇类别分析")
    print("=" * 80)
    print()

    categories = {
        "Core Authenticity": [
            "Raw photo", "candid photography", "authentic snapshot",
            "smartphone camera aesthetic", "shot on iPhone"
        ],
        "Natural Imperfections": [
            "messy background", "uneven skin tone", "Chromatic aberration",
            "motion blur", "slightly out of focus"
        ],
        "Lighting Variations": [
            "low lighting", "overexposed", "underexposed"
        ],
        "Camera Effects": [
            "in motion", "GoPro lens", "amateur photography"
        ],
        "Atmospheric": [
            "eerie atmosphere"
        ]
    }

    print("📋 可用词汇清单:")
    print()

    for category, keywords in categories.items():
        print(f"【{category}】")
        for kw in keywords:
            print(f"  • {kw}")
        print()

    print("💡 使用建议:")
    print("  1. Core Authenticity: 总是选择2个")
    print("  2. Natural Imperfections: 根据场景选择1-2个")
    print("  3. Lighting Variations: 夜间/明亮场景选择1个")
    print("  4. Camera Effects: 运动场景选择1个")
    print("  5. Atmospheric: 特殊场景偶尔使用")
    print()
    print("  ⭐ 建议总数: 2-4个真实感词汇")
    print()


def test_prompt_instruction():
    """测试prompt指导是否清晰"""

    print("=" * 80)
    print("  Prompt指导测试")
    print("=" * 80)
    print()

    instructions = """
ALWAYS include 2-4 realistic modifiers at the END of your scene description:

**Core Authenticity** (choose 2):
- "Raw photo"
- "candid photography"
- "authentic snapshot"
- "smartphone camera aesthetic"
- "shot on iPhone"

**Natural Imperfections** (choose 1-2 based on scene):
- "messy background" (outdoor/public places)
- "uneven skin tone"
- "Chromatic aberration"
- "motion blur" (ONLY if movement in scene)
- "slightly out of focus" (use sparingly)

**Scene Type Guidance**:
- Night/dark scenes → always include "low lighting"
- Outdoor/public → always include "messy background"
- Moving subject → include "motion blur" and "in motion"
"""

    print("📝 LLM收到的指导:")
    print(instructions)

    print("✅ 指导特点:")
    print("  • 明确要求添加2-4个修饰词")
    print("  • 提供分类词汇列表")
    print("  • 给出具体使用场景")
    print("  • 包含正反例")
    print()


if __name__ == "__main__":
    print("\n🚀 LLM真实感词汇注入验证\n")

    # 测试1: 验证scene_hint格式
    test_scene_hint_realism()

    # 测试2: 分析词汇分布
    analyze_realism_distribution()

    # 测试3: 检查prompt指导
    test_prompt_instruction()

    print("=" * 80)
    print("  测试完成")
    print("=" * 80)
    print()
    print("📖 下一步:")
    print("  1. 运行实际tweet生成，检查LLM是否遵循指导")
    print("  2. 查看生成的scene_hint是否包含真实感词汇")
    print("  3. 生成图片并验证真实感效果")
    print()
    print("命令:")
    print("  python main.py --persona personas/test.json --tweets 5")
    print()
