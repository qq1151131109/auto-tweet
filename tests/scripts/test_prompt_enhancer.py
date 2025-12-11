"""
PromptEnhancer测试脚本

演示如何使用PromptEnhancer增强场景描述
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.prompt_enhancer import create_prompt_enhancer, enhance_prompt


def test_z_image_enhancer():
    """测试Z-Image增强器"""
    print("=" * 80)
    print("Z-Image PromptEnhancer 测试")
    print("=" * 80)

    # 示例场景描述（来自LLM）
    scene_hint = """Morning in the driver's seat of a white SUV parked in suburban driveway, soft overcast light coming through windshield, woman sitting upright wearing pale yellow sundress with thin straps and loose cream cardigan slipping off both shoulders, delicate gold cross necklace resting in the center of her chest, seatbelt crossing diagonally tight between breasts pushing fabric together, hands gripping steering wheel at 10 and 2, thighs pressed together on warm leather seat, gentle flush on cheeks, lips slightly parted, medium shot from passenger side showing upper body and lap, innocent eyes looking forward with small knowing smile"""

    print("\n【原始 scene_hint】:")
    print(scene_hint)
    print()

    # 测试不同真实感级别
    for level in ["low", "medium", "high"]:
        print(f"\n--- 真实感级别: {level.upper()} ---")

        enhancer = create_prompt_enhancer("z-image", level)
        result = enhancer.enhance(scene_hint)

        print(f"\n✅ Positive Prompt:")
        print(result["positive_prompt"])

        print(f"\n❌ Negative Prompt:")
        print(result["negative_prompt"])
        print()


def test_sdxl_enhancer():
    """测试SDXL增强器"""
    print("\n" + "=" * 80)
    print("SDXL PromptEnhancer 测试")
    print("=" * 80)

    # 示例场景描述
    scene_hint = """Late evening bedroom, soft purple LED strips behind bed creating intimate glow, woman kneeling on carpet wearing black leather collar and oversized band t-shirt slipping off shoulder, black cotton panties visible, hands resting on thighs in submissive pose, expression vulnerable and longing with soft puppy eyes, close-up shot focusing on collar and face, cozy intimate atmosphere with unmade bed in blurred background"""

    print("\n【原始 scene_hint】:")
    print(scene_hint)
    print()

    # 测试不同真实感级别
    for level in ["low", "medium", "high"]:
        print(f"\n--- 真实感级别: {level.upper()} ---")

        enhancer = create_prompt_enhancer("sdxl", level)
        result = enhancer.enhance(scene_hint)

        print(f"\n✅ Positive Prompt:")
        print(result["positive_prompt"])

        print(f"\n❌ Negative Prompt:")
        print(result["negative_prompt"])
        print()


def test_contextual_selection():
    """测试智能选择功能"""
    print("\n" + "=" * 80)
    print("智能选择功能测试（根据场景内容动态添加词汇）")
    print("=" * 80)

    test_cases = [
        {
            "name": "夜间场景",
            "scene": "Late night in dark bedroom, dim purple light from LED strips, woman lying on bed..."
        },
        {
            "name": "户外场景",
            "scene": "Outdoor cafe on busy street, bright sunlight, woman sitting at table with messy background..."
        },
        {
            "name": "运动场景",
            "scene": "Woman walking quickly through hallway, motion in frame, moving towards camera..."
        },
        {
            "name": "明亮室内",
            "scene": "Bright morning room with sunlight streaming through large window, woman standing..."
        }
    ]

    for case in test_cases:
        print(f"\n{'─' * 60}")
        print(f"📝 场景: {case['name']}")
        print(f"{'─' * 60}")
        print(f"描述: {case['scene'][:80]}...")

        enhancer = create_prompt_enhancer("z-image", "high")
        result = enhancer.enhance(case['scene'])

        # 提取添加的真实感词（场景描述后的部分）
        prompt = result["positive_prompt"]
        if "..." in prompt:
            added_tokens = prompt.split("...")[-1].strip()
            print(f"\n✨ 智能添加的词汇:")
            print(f"   {added_tokens}")
        print()


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 80)
    print("便捷函数测试 (enhance_prompt)")
    print("=" * 80)

    scene = "Woman in casual clothes sitting in cafe..."

    # 一键调用
    result = enhance_prompt(
        scene,
        model_type="z-image",
        realism_level="medium"
    )

    print(f"\n原始: {scene}")
    print(f"\n增强后: {result['positive_prompt']}")


if __name__ == "__main__":
    print("\n🚀 PromptEnhancer 功能演示\n")

    # 运行所有测试
    test_z_image_enhancer()
    test_sdxl_enhancer()
    test_contextual_selection()
    test_convenience_function()

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
