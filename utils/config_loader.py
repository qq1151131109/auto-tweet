"""
配置加载工具
加载archetypes和content_types配置
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or PROJECT_ROOT / "config"
        self._archetypes = None
        self._content_types = None

    def load_archetypes(self) -> Dict[str, Any]:
        """加载archetype配置"""
        if self._archetypes is None:
            archetype_file = self.config_dir / "archetypes.yaml"
            with open(archetype_file, 'r', encoding='utf-8') as f:
                self._archetypes = yaml.safe_load(f)
        return self._archetypes

    def load_content_types(self) -> Dict[str, Any]:
        """加载content_types配置"""
        if self._content_types is None:
            content_types_file = self.config_dir / "content_types.yaml"
            with open(content_types_file, 'r', encoding='utf-8') as f:
                self._content_types = yaml.safe_load(f)
        return self._content_types

    def get_archetype(self, archetype_name: str) -> Dict[str, Any]:
        """获取指定archetype的配置"""
        archetypes = self.load_archetypes()

        if archetype_name not in archetypes['archetypes']:
            # 使用默认archetype
            default_name = archetypes.get('default_archetype', 'ABG')
            print(f"⚠️ Archetype '{archetype_name}' not found, using default: {default_name}")
            archetype_name = default_name

        return archetypes['archetypes'][archetype_name]

    def get_content_type(self, content_type_name: str) -> Dict[str, Any]:
        """获取指定content_type的配置"""
        content_types = self.load_content_types()

        if content_type_name not in content_types['content_types']:
            raise ValueError(f"Content type '{content_type_name}' not found in config")

        return content_types['content_types'][content_type_name]

    def get_global_variations(self) -> Dict[str, Any]:
        """获取全局变化因素"""
        content_types = self.load_content_types()
        return content_types.get('global_variations', {})

    def list_archetypes(self) -> list:
        """列出所有可用的archetypes"""
        archetypes = self.load_archetypes()
        return list(archetypes['archetypes'].keys())

    def list_content_types(self) -> list:
        """列出所有可用的content_types"""
        content_types = self.load_content_types()
        return list(content_types['content_types'].keys())


# 全局单例
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """获取全局ConfigLoader实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_archetype(archetype_name: str) -> Dict[str, Any]:
    """快捷函数：加载archetype"""
    return get_config_loader().get_archetype(archetype_name)


def load_content_type(content_type_name: str) -> Dict[str, Any]:
    """快捷函数：加载content_type"""
    return get_config_loader().get_content_type(content_type_name)


def load_global_variations() -> Dict[str, Any]:
    """快捷函数：加载全局变化因素"""
    return get_config_loader().get_global_variations()


if __name__ == "__main__":
    # 测试配置加载
    print("🧪 测试配置加载\n")

    loader = ConfigLoader()

    # 测试1: 列出所有archetypes
    print("📋 可用的Archetypes:")
    for name in loader.list_archetypes():
        archetype = loader.get_archetype(name)
        print(f"  • {name}: {archetype['description']}")
    print()

    # 测试2: 列出所有content types
    print("📋 可用的Content Types:")
    for name in loader.list_content_types():
        content_type = loader.get_content_type(name)
        print(f"  • {name}: {content_type['description']}")
    print()

    # 测试3: 加载具体archetype
    print("📖 加载 ABG archetype:")
    abg = loader.get_archetype("ABG")
    print(f"  Name: {abg['name']}")
    print(f"  Description: {abg['description']}")
    print(f"  Distribution:")
    for content_type, ratio in abg['default_distribution'].items():
        print(f"    - {content_type}: {ratio:.0%}")
    print()

    # 测试4: 加载具体content type
    print("📖 加载 gym_workout content type:")
    gym = loader.get_content_type("gym_workout")
    print(f"  Description: {gym['description']}")
    print(f"  Subtypes:")
    for subtype_name, subtype_data in gym['subtypes'].items():
        print(f"    - {subtype_name}: {subtype_data['weight']:.0%}")
    print()

    # 测试5: 全局变化因素
    print("🌍 全局变化因素:")
    global_vars = loader.get_global_variations()
    for category, options in global_vars.items():
        print(f"  {category}: {len(options)} options")
    print()

    print("✅ 配置加载测试完成")
