"""
内容计划生成器
根据persona的archetype和配置生成详细的内容生成计划
"""
import random
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from pathlib import Path
import sys

# 添加路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_loader import get_config_loader


class DiversityTracker:
    """多样性跟踪器 - 避免重复的变化组合"""

    def __init__(self):
        self.used_combinations = set()
        self.feature_counts = defaultdict(int)

    def get_unique_variation(
        self,
        content_type: str,
        subtype: str,
        variations: Dict[str, List[str]],
        max_attempts: int = 100
    ) -> Dict[str, str]:
        """
        获取一个尚未使用的变化组合

        Args:
            content_type: 内容类型 (e.g., "gym_workout")
            subtype: 子类型 (e.g., "squat_rack")
            variations: 变化维度字典 {"camera_angle": [...], "clothing": [...]}
            max_attempts: 最大尝试次数

        Returns:
            变化组合字典
        """
        for attempt in range(max_attempts):
            # 从每个维度随机选择
            combo = {
                dim: random.choice(options)
                for dim, options in variations.items()
            }

            # 创建可哈希的key
            combo_key = (
                content_type,
                subtype,
                tuple(sorted(combo.items()))
            )

            # 检查是否用过
            if combo_key not in self.used_combinations:
                self.used_combinations.add(combo_key)

                # 记录特征使用次数
                for dim, value in combo.items():
                    self.feature_counts[f"{content_type}:{dim}:{value}"] += 1

                return combo

        # 所有组合都用过了，允许重复但给警告
        print(f"⚠️  {content_type}/{subtype} 的变化组合已用尽，开始重复")
        return combo

    def get_diversity_stats(self, content_type: str) -> Dict[str, float]:
        """获取指定content_type的多样性统计"""
        total = len([k for k in self.used_combinations if k[0] == content_type])

        stats = {
            "total_generated": total,
            "unique_combinations": len([k for k in self.used_combinations if k[0] == content_type])
        }

        return stats


class ContentPlanner:
    """内容计划生成器"""

    def __init__(self):
        self.config_loader = get_config_loader()
        self.diversity_tracker = DiversityTracker()

    def create_content_plan(
        self,
        persona: Dict[str, Any],
        total_count: int = 365
    ) -> Dict[str, Any]:
        """
        为persona创建内容生成计划

        Args:
            persona: Persona JSON数据
            total_count: 总生成数量

        Returns:
            内容计划字典
        """
        # 1. 获取persona的content_strategy
        extensions = persona.get('data', {}).get('extensions', {})
        strategy = extensions.get('content_strategy', {})

        archetype_name = strategy.get('archetype', 'ABG')
        custom_weights = strategy.get('custom_weights', {})
        exclude_types = strategy.get('exclude_types', [])
        force_include = strategy.get('force_include', {})

        # 2. 加载archetype配置
        archetype = self.config_loader.get_archetype(archetype_name)
        distribution = archetype['default_distribution'].copy()

        # 3. 应用自定义权重
        distribution.update(custom_weights)

        # 4. 应用force_include
        distribution.update(force_include)

        # 5. 移除排除的类型
        for excluded in exclude_types:
            distribution.pop(excluded, None)

        # 6. 归一化权重（确保总和为1）
        total_weight = sum(distribution.values())
        distribution = {k: v / total_weight for k, v in distribution.items()}

        # 7. 计算每种类型的数量
        content_plan = {}
        remaining = total_count

        for content_type, ratio in distribution.items():
            count = int(total_count * ratio)
            content_plan[content_type] = count
            remaining -= count

        # 8. 分配剩余的（四舍五入误差）
        if remaining > 0:
            # 分配给占比最大的类型
            max_type = max(distribution.items(), key=lambda x: x[1])[0]
            content_plan[max_type] += remaining

        # 9. 为每种类型生成详细计划
        detailed_plan = {}
        for content_type, count in content_plan.items():
            detailed_plan[content_type] = self._plan_content_type(
                content_type,
                count,
                archetype.get('mood_weights', {})
            )

        return {
            "persona_name": persona.get('data', {}).get('name', 'Unknown'),
            "archetype": archetype_name,
            "total_count": total_count,
            "distribution": content_plan,
            "detailed_plan": detailed_plan,
            "mood_weights": archetype.get('mood_weights', {})
        }

    def _plan_content_type(
        self,
        content_type: str,
        count: int,
        mood_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        为单个content_type生成详细计划

        Returns:
            List of generation specs
        """
        # 加载content_type配置
        type_config = self.config_loader.get_content_type(content_type)

        subtypes = type_config['subtypes']
        variations = type_config['variations']

        # 计算每个subtype的数量
        subtype_counts = {}
        for subtype_name, subtype_data in subtypes.items():
            weight = subtype_data['weight']
            subtype_counts[subtype_name] = int(count * weight)

        # 分配剩余
        remaining = count - sum(subtype_counts.values())
        if remaining > 0:
            max_subtype = max(subtypes.items(), key=lambda x: x[1]['weight'])[0]
            subtype_counts[max_subtype] += remaining

        # 为每个要生成的内容创建spec
        generation_specs = []

        for subtype_name, subtype_count in subtype_counts.items():
            for i in range(subtype_count):
                # 获取唯一的变化组合
                variation_combo = self.diversity_tracker.get_unique_variation(
                    content_type=content_type,
                    subtype=subtype_name,
                    variations=variations
                )

                # 随机选择mood
                mood = self._weighted_random_choice(mood_weights)

                # 创建生成spec
                spec = {
                    "content_type": content_type,
                    "subtype": subtype_name,
                    "subtype_description": subtypes[subtype_name]['description'],
                    "variations": variation_combo,
                    "mood": mood
                }

                generation_specs.append(spec)

        # 打乱顺序（避免同类型连续）
        random.shuffle(generation_specs)

        return generation_specs

    def _weighted_random_choice(self, weights: Dict[str, float]) -> str:
        """根据权重随机选择"""
        if not weights:
            return "confident"  # 默认mood

        items = list(weights.keys())
        weights_list = list(weights.values())

        return random.choices(items, weights=weights_list, k=1)[0]

    def get_diversity_report(self) -> Dict[str, Any]:
        """获取多样性报告"""
        all_content_types = set(k[0] for k in self.diversity_tracker.used_combinations)

        report = {}
        for content_type in all_content_types:
            report[content_type] = self.diversity_tracker.get_diversity_stats(content_type)

        return report


def create_content_plan(persona: Dict[str, Any], count: int = 365) -> Dict[str, Any]:
    """快捷函数：创建内容计划"""
    planner = ContentPlanner()
    return planner.create_content_plan(persona, count)


if __name__ == "__main__":
    # 测试内容计划生成
    print("🧪 测试内容计划生成\n")

    # 模拟persona
    test_persona = {
        "data": {
            "name": "Test Mia",
            "extensions": {
                "content_strategy": {
                    "archetype": "ABG",
                    "target_count": 100
                }
            }
        }
    }

    planner = ContentPlanner()
    plan = planner.create_content_plan(test_persona, total_count=100)

    print(f"📋 为 {plan['persona_name']} 生成内容计划")
    print(f"   Archetype: {plan['archetype']}")
    print(f"   总数: {plan['total_count']}")
    print()

    print("📊 内容分布:")
    for content_type, count in plan['distribution'].items():
        print(f"  {content_type}: {count} 条")
    print()

    # 检查第一个content_type的详细计划
    first_type = list(plan['detailed_plan'].keys())[0]
    first_plan = plan['detailed_plan'][first_type]

    print(f"🔍 {first_type} 详细计划（前5条）:")
    for i, spec in enumerate(first_plan[:5], 1):
        print(f"  [{i}] {spec['subtype']}")
        print(f"      Mood: {spec['mood']}")
        print(f"      Variations: {', '.join(f'{k}={v[:30]}...' for k, v in list(spec['variations'].items())[:2])}")
    print()

    # 多样性报告
    print("📈 多样性报告:")
    diversity_report = planner.get_diversity_report()
    for content_type, stats in diversity_report.items():
        print(f"  {content_type}:")
        print(f"    生成总数: {stats['total_generated']}")
        print(f"    唯一组合: {stats['unique_combinations']}")
    print()

    print("✅ 内容计划生成测试完成")
