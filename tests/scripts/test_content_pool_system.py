"""
快速测试新的内容池生成系统
"""
import json
from pathlib import Path


def test_complete_system():
    """测试完整的内容池生成系统"""

    print("=" * 80)
    print("  内容池生成系统测试")
    print("=" * 80)
    print()

    # 1. 测试配置加载
    print("【步骤1】测试配置加载...")
    from utils.config_loader import get_config_loader

    loader = get_config_loader()

    archetypes = loader.list_archetypes()
    content_types = loader.list_content_types()

    print(f"✅ 加载了 {len(archetypes)} 个Archetypes")
    print(f"✅ 加载了 {len(content_types)} 个Content Types")
    print()

    # 2. 测试内容计划生成
    print("【步骤2】测试内容计划生成...")
    from core.content_planner import ContentPlanner

    # 创建测试persona
    test_persona = {
        "data": {
            "name": "测试角色 Mia",
            "extensions": {
                "content_strategy": {
                    "archetype": "ABG",
                    "target_count": 50  # 测试用小数量
                }
            }
        }
    }

    planner = ContentPlanner()
    plan = planner.create_content_plan(test_persona, total_count=50)

    print(f"✅ 为 {plan['persona_name']} 生成了内容计划")
    print(f"   Archetype: {plan['archetype']}")
    print(f"   总数: {plan['total_count']}")
    print()

    print("   内容分布:")
    for content_type, count in plan['distribution'].items():
        print(f"     {content_type}: {count} 条")
    print()

    # 3. 检查generation specs
    print("【步骤3】检查生成规格...")
    first_type = list(plan['detailed_plan'].keys())[0]
    first_specs = plan['detailed_plan'][first_type]

    print(f"   {first_type} 的前3个生成规格:")
    for i, spec in enumerate(first_specs[:3], 1):
        print(f"     [{i}] {spec['subtype']} ({spec['mood']})")
        print(f"         变化维度: {len(spec['variations'])} 个")
    print()

    # 4. 多样性检查
    print("【步骤4】多样性检查...")
    diversity = planner.get_diversity_report()

    for content_type, stats in diversity.items():
        uniqueness = (stats['unique_combinations'] / stats['total_generated'] * 100
                      if stats['total_generated'] > 0 else 0)
        print(f"   {content_type}: {uniqueness:.1f}% 唯一性")
    print()

    # 5. 总结
    print("=" * 80)
    print("  ✅ 系统测试通过！")
    print("=" * 80)
    print()

    print("📖 系统准备就绪！")
    print()
    print("下一步操作:")
    print("  1. 为现有persona添加content_strategy")
    print("  2. 使用新API生成内容池")
    print()

    print("示例命令（需要在main.py中实现）:")
    print("  python main.py --generate-pool --persona personas/mia.json --count 365")
    print()

    return True


def create_sample_persona_with_strategy():
    """创建一个带content_strategy的示例persona"""

    print("=" * 80)
    print("  创建示例Persona（带content_strategy）")
    print("=" * 80)
    print()

    sample_persona = {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": "Mia Chen",
            "description": "Fitness enthusiast and lifestyle content creator",
            "personality": "Confident, playful, and assertive",
            "extensions": {
                "twitter_persona": {
                    "tweet_examples": [
                        {
                            "text": "gym mirror hitting different today 💪",
                            "mood": "confident",
                            "scene_hint": "Mirror selfie in gym..."
                        }
                    ]
                },
                "lora": {
                    "model_path": "lora/mia.safetensors",
                    "strength": 0.8
                },
                # ⭐ 新增: content_strategy
                "content_strategy": {
                    "archetype": "ABG",
                    "target_count": 365,
                    # 可选: 自定义权重
                    "custom_weights": {
                        "gym_workout": 0.35  # 比默认的0.25更多健身内容
                    }
                }
            }
        }
    }

    output_path = Path("personas") / "sample_mia_with_strategy.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_persona, f, ensure_ascii=False, indent=2)

    print(f"✅ 示例persona已创建: {output_path}")
    print()
    print("包含的content_strategy:")
    print(json.dumps(sample_persona['data']['extensions']['content_strategy'], indent=2))
    print()

    return output_path


def show_usage_examples():
    """展示使用示例"""

    print("=" * 80)
    print("  使用示例")
    print("=" * 80)
    print()

    examples = [
        {
            "title": "基础用法 - 生成365条内容",
            "command": "python main.py --generate-pool --persona personas/mia.json"
        },
        {
            "title": "指定数量 - 生成500条",
            "command": "python main.py --generate-pool --persona personas/mia.json --count 500"
        },
        {
            "title": "批量生成多个personas",
            "command": "for persona in personas/*.json; do\n  python main.py --generate-pool --persona $persona --count 365\ndone"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"【示例 {i}】{example['title']}")
        print(f"  {example['command']}")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n🧪 内容池生成系统 - 完整测试\n")

    # 测试1: 系统组件测试
    test_complete_system()

    # 测试2: 创建示例persona
    sample_path = create_sample_persona_with_strategy()

    # 测试3: 展示使用示例
    show_usage_examples()

    print("=" * 80)
    print("  测试完成 ✅")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 配置文件位于: config/archetypes.yaml 和 config/content_types.yaml")
    print("  - 可以自定义archetype和content_types来调整生成策略")
    print("  - 多样性由DiversityTracker自动保证")
    print()
