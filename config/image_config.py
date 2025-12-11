"""
图片生成配置加载器

使用方法:
    from config.image_config import load_image_config, get_prompt_enhancer_config

    # 加载配置
    config = load_image_config()

    # 获取prompt enhancer配置
    enhancer_config = get_prompt_enhancer_config(config)
    model_type = enhancer_config["model_type"]
    realism_level = enhancer_config["realism_level"]
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG_PATH = Path(__file__).parent / "image_generation.yaml"


def load_image_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载图片生成配置

    Args:
        config_path: 配置文件路径（默认使用config/image_generation.yaml）

    Returns:
        配置字典
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def get_prompt_enhancer_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    从配置中提取PromptEnhancer相关参数

    Args:
        config: 完整配置字典

    Returns:
        {
            "model_type": "z-image" | "sdxl",
            "realism_level": "low" | "medium" | "high",
            "enable_realism": bool,
            "enable_variation": bool,
            "enabled": bool  # 是否启用增强（false则回退到原始行为）
        }
    """
    prompt_config = config.get("prompt_enhancement", {})
    realism_config = prompt_config.get("realism", {})
    model_type = config.get("model", {}).get("type", "z-image")

    return {
        "model_type": model_type,
        "realism_level": realism_config.get("level", "medium"),
        "enable_realism": realism_config.get("enabled", True),
        "enable_variation": realism_config.get("variation", True),
        "enabled": prompt_config.get("enabled", True)
    }


def get_generation_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    从配置中提取生成参数

    Args:
        config: 完整配置字典

    Returns:
        {
            "width": int,
            "height": int,
            "steps": int,
            "cfg": float
        }
    """
    gen_config = config.get("generation", {})

    return {
        "width": gen_config.get("width", 768),
        "height": gen_config.get("height", 1024),
        "steps": gen_config.get("steps", 9),
        "cfg": gen_config.get("cfg", 1.0)
    }


def load_preset(preset_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    加载预设配置

    Args:
        preset_name: 预设名称 ("high_quality" | "balanced" | "authentic" | "sdxl")
        config: 基础配置（可选，不提供则从文件加载）

    Returns:
        应用预设后的配置字典
    """
    if config is None:
        config = load_image_config()

    presets = config.get("presets", {})
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")

    # 深拷贝基础配置
    import copy
    result = copy.deepcopy(config)

    # 应用预设（递归合并）
    preset_config = presets[preset_name]
    _deep_merge(result, preset_config)

    return result


def _deep_merge(base: Dict, update: Dict) -> None:
    """递归合并字典"""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ============ 新增：高级生成模式配置函数 ============

def load_negative_prompt_template(config: Optional[Dict] = None) -> str:
    """
    加载负向提示词模板

    Args:
        config: 配置字典（如果为 None，则自动加载）

    Returns:
        负向提示词字符串
    """
    if config is None:
        config = load_image_config()

    # 检查是否启用负向提示词
    advanced_gen = config.get("advanced_generation", {})
    neg_prompt_config = advanced_gen.get("negative_prompt", {})

    if not neg_prompt_config.get("enabled", False):
        return ""

    # 读取模板文件
    template_file = neg_prompt_config.get("template_file", "config/negative_prompts_en.txt")
    template_path = Path(template_file)

    if not template_path.exists():
        print(f"⚠️  负向提示词模板文件不存在: {template_file}")
        return ""

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # 移除注释行（以 # 开头）
    lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
    negative_prompt = ' '.join(lines)

    return negative_prompt


def get_generation_mode(config: Optional[Dict] = None) -> str:
    """
    获取生成模式

    Args:
        config: 配置字典（如果为 None，则自动加载）

    Returns:
        "advanced" 或 "simple"
    """
    if config is None:
        config = load_image_config()

    return config.get("generation_mode", "advanced")


def get_progressive_config(config: Optional[Dict] = None) -> Dict:
    """
    获取渐进式生成配置

    Args:
        config: 配置字典（如果为 None，则自动加载）

    Returns:
        渐进式生成配置字典
    """
    if config is None:
        config = load_image_config()

    advanced_gen = config.get("advanced_generation", {})
    progressive = advanced_gen.get("progressive", {})

    # 获取最终尺寸
    gen_config = config.get("generation", {})
    final_width = gen_config.get("width", 768)
    final_height = gen_config.get("height", 1024)

    # 构建配置
    stage1 = progressive.get("stage1", {})
    stage2 = progressive.get("stage2", {})
    stage3 = progressive.get("stage3", {})

    return {
        "stage1_size": tuple(stage1.get("size", [512, 672])),
        "stage2_size": tuple(stage2.get("size", [640, 832])),
        "stage3_size": (final_width, final_height),
        "stage1_steps": stage1.get("steps", 9),
        "stage2_steps": stage2.get("steps", 16),
        "stage3_steps": stage3.get("steps", 16),
        "stage1_cfg": stage1.get("cfg", 2.0),
        "stage2_cfg": stage2.get("cfg", 1.0),
        "stage3_cfg": stage3.get("cfg", 1.0),
        "stage2_denoise": stage2.get("denoise", 0.7),
        "stage3_denoise": stage3.get("denoise", 0.6),
    }


# ============ 便捷函数 ============

def get_enhancer_from_config(config_path: Optional[str] = None, preset: Optional[str] = None):
    """
    从配置文件创建PromptEnhancer

    Args:
        config_path: 配置文件路径
        preset: 预设名称（可选）

    Returns:
        PromptEnhancer实例
    """
    from core.prompt_enhancer import create_prompt_enhancer

    config = load_image_config(config_path)

    # 如果指定预设，应用预设
    if preset:
        config = load_preset(preset, config)

    enhancer_config = get_prompt_enhancer_config(config)

    # 如果增强被禁用，返回None
    if not enhancer_config["enabled"]:
        return None

    return create_prompt_enhancer(
        model_type=enhancer_config["model_type"],
        realism_level=enhancer_config["realism_level"]
    )
