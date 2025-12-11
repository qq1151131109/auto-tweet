"""
测试美国市场审美优化
验证LLM生成的scene_hint是否符合美国审美标准
"""


def test_us_market_scene_hints():
    """测试场景描述是否符合美国市场审美"""

    print("=" * 80)
    print("  美国市场审美优化测试")
    print("=" * 80)
    print()

    # 模拟LLM应该生成的美国市场优化scene_hint
    test_cases = [
        {
            "name": "健身房场景 (Gym Girl)",
            "scene_hint": """Medium shot from low angle: Woman standing in gym wearing tight black leggings and purple sports bra, one hand on hip, other hand running through messy ponytail, direct confident gaze into camera, visible ab definition, golden tan skin with slight sheen of sweat, arched back emphasizing curves, legs shoulder-width apart, gym equipment blurred in background, warm fluorescent lighting, smirking expression, Raw photo, candid photography, messy background""",
            "expected_features": {
                "body_language": ["direct gaze", "hand on hip", "arched back", "legs apart"],
                "skin": ["golden tan", "sheen"],
                "expression": ["confident", "smirking", "direct"],
                "styling": ["leggings", "sports bra", "gym"],
                "avoid_features": []  # Should NOT contain these
            }
        },
        {
            "name": "ABG风格卧室场景",
            "scene_hint": """Close-up shot from eye level: Woman sitting on edge of bed wearing cropped tank top and high-waisted distressed jeans, long hair with blonde balayage highlights falling over one shoulder, heavy contour makeup with arched brows and nude overlined lips, direct stare into camera with bedroom eyes, one hand playing with hair and other hand resting on thigh, visible temporary tattoo on upper arm, hoop earrings catching light, sun-kissed warm skin tone with dewy finish, confident relaxed posture with shoulders back, messy bedroom background with LED strip lights, authentic snapshot, smartphone camera aesthetic""",
            "expected_features": {
                "styling": ["blonde balayage", "crop", "high-waisted", "hoop earrings", "tattoo"],
                "makeup": ["heavy contour", "arched brows", "overlined lips"],
                "expression": ["direct stare", "bedroom eyes", "confident"],
                "skin": ["sun-kissed", "warm", "dewy"],
                "body_language": ["shoulders back", "relaxed"]
            }
        },
        {
            "name": "E-girl游戏场景",
            "scene_hint": """Medium shot from slightly above: Woman sitting at gaming desk wearing oversized black hoodie and pleated skirt, cat ear headphones on head, RGB keyboard and monitor visible in background, winged black eyeliner and pink blush on nose, playful expression sticking tongue out slightly, direct eye contact with camera, one hand doing peace sign near face, thigh-high striped socks visible, messy room with anime posters on wall, colorful LED lighting casting purple and blue glow, pale skin acceptable for indoor gamer aesthetic, candid photography, amateur photography, low lighting""",
            "expected_features": {
                "props": ["cat ear headphones", "RGB", "gaming desk", "anime posters"],
                "styling": ["oversized hoodie", "pleated skirt", "thigh-high socks"],
                "makeup": ["winged eyeliner", "pink blush"],
                "expression": ["playful", "tongue out", "direct eye contact"],
                "special_note": "pale skin OK for E-girl archetype"
            }
        },
        {
            "name": "❌ 反例：东亚纯欲风 (应该避免)",
            "scene_hint": """Woman in bedroom wearing oversized pastel sweater and white knee socks, sitting on bed with knees pulled to chest, looking down shyly avoiding camera, pale white skin, small delicate frame, twin braids, hands covering lower face, soft pink lighting, innocent doe eyes""",
            "expected_features": {
                "avoid_features": [
                    "looking down shyly",
                    "avoiding camera",
                    "pale white skin",
                    "small delicate frame",
                    "twin braids",
                    "hands covering",
                    "innocent doe eyes"
                ]
            },
            "is_bad_example": True
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        is_bad = test_case.get("is_bad_example", False)

        if is_bad:
            print(f"【反例 {i}】{test_case['name']}")
            print("─" * 80)
            print("这是一个应该避免的东亚审美示例:")
            print(f"{test_case['scene_hint'][:150]}...")
            print()
            print("❌ 存在的问题特征:")
            for feature in test_case['expected_features']['avoid_features']:
                if feature in test_case['scene_hint']:
                    print(f"  ❌ 发现: {feature}")
            print()
            print("💡 改进建议: 应使用直视镜头、自信姿态、暖色肤色、展示曲线")
            print()
        else:
            print(f"【测试 {i}】{test_case['name']}")
            print("─" * 80)
            print(f"Scene Hint: {test_case['scene_hint'][:120]}...")
            print()

            # 检查身体语言
            if 'body_language' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['body_language']:
                    if any(keyword in test_case['scene_hint'].lower() for keyword in feature.split()):
                        found.append(feature)

                if found:
                    print(f"✅ 身体语言 (自信/占据空间): {', '.join(found)}")
                else:
                    print(f"⚠️ 未检测到推荐的身体语言特征")
                    all_passed = False

            # 检查肤色描述
            if 'skin' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['skin']:
                    if feature.lower() in test_case['scene_hint'].lower():
                        found.append(feature)

                if found:
                    print(f"✅ 肤色/质感 (暖色/光泽): {', '.join(found)}")
                else:
                    print(f"⚠️ 未检测到推荐的肤色描述")
                    all_passed = False

            # 检查表情
            if 'expression' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['expression']:
                    if feature.lower() in test_case['scene_hint'].lower():
                        found.append(feature)

                if found:
                    print(f"✅ 表情/眼神 (自信/直接): {', '.join(found)}")
                else:
                    print(f"⚠️ 未检测到推荐的表情特征")
                    all_passed = False

            # 检查风格元素
            if 'styling' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['styling']:
                    if feature.lower() in test_case['scene_hint'].lower():
                        found.append(feature)

                if found:
                    print(f"✅ 风格元素: {', '.join(found)}")

            # 检查妆容
            if 'makeup' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['makeup']:
                    if feature.lower() in test_case['scene_hint'].lower():
                        found.append(feature)

                if found:
                    print(f"✅ 妆容特征: {', '.join(found)}")

            # 检查道具
            if 'props' in test_case['expected_features']:
                found = []
                for feature in test_case['expected_features']['props']:
                    if feature.lower() in test_case['scene_hint'].lower():
                        found.append(feature)

                if found:
                    print(f"✅ 道具/场景: {', '.join(found)}")

            # 特殊说明
            if 'special_note' in test_case['expected_features']:
                print(f"💡 {test_case['expected_features']['special_note']}")

            print()

    print("=" * 80)
    if all_passed:
        print("✅ 美国市场审美测试通过!")
    else:
        print("⚠️ 部分特征缺失,建议加强LLM指导")
    print("=" * 80)
    print()

    return all_passed


def analyze_us_market_requirements():
    """分析美国市场的核心要求"""

    print("=" * 80)
    print("  美国市场审美核心要求分析")
    print("=" * 80)
    print()

    requirements = {
        "必须包含 (MUST HAVE)": {
            "身体语言": [
                "Direct eye contact / direct gaze",
                "Confident posture / shoulders back",
                "Arched back / anterior pelvic tilt (强调腰臀比)",
                "Legs apart / weight shifted (占据空间)"
            ],
            "肤色描述": [
                "Warm/golden skin tone",
                "Sun-kissed / tan aesthetic",
                "Glossy/dewy skin (光泽感)",
                "避免: cold pale white skin"
            ],
            "表情特征": [
                "Bedroom eyes (眼睑微垂但聚焦)",
                "Smirk / knowing smile",
                "Parted lips",
                "Confident/assertive expression"
            ],
            "身材强调": [
                "Waist-hip ratio emphasis",
                "Curvy/athletic build",
                "Visible muscle definition (if gym setting)",
                "避免: stick-thin / childish proportions"
            ]
        },
        "推荐风格 (RECOMMENDED ARCHETYPES)": {
            "ABG (Asian Baby Girl)": [
                "Blonde highlights / balayage",
                "Heavy contour + arched brows",
                "Bodycon / crop tops / athleisure",
                "Hoop earrings + temporary tattoos",
                "Bad bitch energy attitude"
            ],
            "Gym Girl": [
                "Leggings + sports bra",
                "Visible ab/muscle definition",
                "Gym setting with equipment",
                "Post-workout glow / sweat sheen",
                "Confident athletic pose"
            ],
            "E-girl/Gamer": [
                "Cat ear headphones + RGB lighting",
                "Pleated skirt + thigh-high socks",
                "Winged eyeliner + playful expressions",
                "Gaming setup visible",
                "Pale skin acceptable (indoor aesthetic)"
            ]
        },
        "严格避免 (STRICTLY AVOID)": [
            "❌ Eye contact avoidance / looking down shyly",
            "❌ Covering face with hands",
            "❌ Pigeon-toed stance / knees together",
            "❌ Overly innocent / doe eyes",
            "❌ Cold pale skin (unless E-girl archetype)",
            "❌ Childish proportions / trying to look younger",
            "❌ Twin braids / schoolgirl uniform",
            "❌ Submissive shrinking body language"
        ]
    }

    for category, items in requirements.items():
        print(f"【{category}】")
        print()
        if isinstance(items, dict):
            for subcategory, features in items.items():
                print(f"  {subcategory}:")
                for feature in features:
                    print(f"    • {feature}")
                print()
        else:
            for feature in items:
                print(f"  {feature}")
            print()

    print("=" * 80)
    print()


def show_comparison_examples():
    """展示对比示例"""

    print("=" * 80)
    print("  中美审美对比示例")
    print("=" * 80)
    print()

    comparisons = [
        {
            "场景": "卧室拍摄",
            "东亚审美 (❌避免)": "Woman sitting on bed wearing oversized sweater, knees to chest, looking down shyly, pale skin, innocent expression, hands near face",
            "美国审美 (✅使用)": "Woman sitting on edge of bed wearing crop top and shorts, direct gaze into camera, one hand on hip, arched back showing curves, sun-kissed skin with dewy finish, confident smirk"
        },
        {
            "场景": "室外拍摄",
            "东亚审美 (❌避免)": "Woman standing with feet together, hands clasped in front, looking away from camera, pale white skin, delicate frame, shy smile",
            "美国审美 (✅使用)": "Woman standing with legs shoulder-width apart, one hand on hip, direct eye contact, athletic build with visible muscle tone, golden tan skin, confident assertive expression"
        },
        {
            "场景": "健身房",
            "东亚审美 (❌避免)": "Woman in loose gym clothes trying to hide body shape, looking at floor, avoiding camera, focusing on appearing small and delicate",
            "美国审美 (✅使用)": "Woman in tight leggings and sports bra, mid-squat showing glute definition, direct gaze into mirror, visible sweat sheen, confident powerful stance"
        }
    ]

    for i, comparison in enumerate(comparisons, 1):
        print(f"【示例 {i}】{comparison['场景']}")
        print("─" * 80)
        print(f"❌ 东亚审美 (不适合美国市场):")
        print(f"   {comparison['东亚审美 (❌避免)']}")
        print()
        print(f"✅ 美国审美 (推荐使用):")
        print(f"   {comparison['美国审美 (✅使用)']}")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n🎯 美国市场审美优化验证\n")

    # 测试1: 验证scene_hint格式
    test_us_market_scene_hints()

    # 测试2: 分析核心要求
    analyze_us_market_requirements()

    # 测试3: 对比示例
    show_comparison_examples()

    print("=" * 80)
    print("  测试完成")
    print("=" * 80)
    print()
    print("📖 下一步:")
    print("  1. 运行实际tweet生成,检查LLM是否遵循美国市场指导")
    print("  2. 验证生成的scene_hint是否包含:")
    print("     - Direct eye contact / confident gaze")
    print("     - Warm/golden skin tone")
    print("     - Arched back / curves emphasis")
    print("     - Space-occupying poses")
    print("  3. 确保避免了东亚审美特征:")
    print("     - Shy/avoiding gaze")
    print("     - Pale cold skin")
    print("     - Submissive posture")
    print()
    print("命令:")
    print("  python main.py --persona personas/test.json --tweets 5")
    print()
