"""
生成流程配置 - 统一管理人设/推文/图片生成参数
这是一个建议的配置文件示例，展示如何统一管理所有生成流程的参数
"""
from pydantic import BaseModel, Field
from typing import Optional


# ============================================
# 人设生成配置
# ============================================
class PersonaStageConfig(BaseModel):
    """单个人设生成阶段的配置"""
    temperature: float = Field(default=0.85, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=4000, ge=100, le=32000, description="最大token数")


class PersonaGenerationConfig(BaseModel):
    """人设生成器配置"""

    # 各阶段配置
    stage1_core_persona: PersonaStageConfig = PersonaStageConfig(
        temperature=0.85,
        max_tokens=4000
    )

    stage2_tweet_strategy: PersonaStageConfig = PersonaStageConfig(
        temperature=0.85,
        max_tokens=8000
    )

    stage3_example_tweets: PersonaStageConfig = PersonaStageConfig(
        temperature=0.9,  # 示例推文需要更高的创造性
        max_tokens=8000
    )
    num_example_tweets: int = Field(default=8, ge=1, le=20, description="生成的示例推文数量")

    stage4_social_network: PersonaStageConfig = PersonaStageConfig(
        temperature=0.85,
        max_tokens=4000
    )

    stage5_authenticity: PersonaStageConfig = PersonaStageConfig(
        temperature=0.8,
        max_tokens=3000
    )

    stage6_visual_profile: PersonaStageConfig = PersonaStageConfig(
        temperature=0.8,
        max_tokens=2000
    )

    stage7_character_book: PersonaStageConfig = PersonaStageConfig(
        temperature=0.8,
        max_tokens=5000
    )
    num_character_entries: int = Field(default=6, ge=1, le=20, description="角色知识库条目数量")

    # 通用配置
    default_nsfw_level: str = Field(default="enabled", description="NSFW等级")
    default_language: str = Field(default="English", description="默认语言")


# ============================================
# 推文生成配置
# ============================================
class TweetGenerationConfig(BaseModel):
    """推文生成器配置"""

    # LLM 参数
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="单条推文最大token")

    # 示例选择
    max_examples: int = Field(default=3, ge=1, le=8, description="从人设中选择的示例数量")

    # 内容约束
    tweet_min_length: int = Field(default=140, description="推文最小字符数")
    tweet_max_length: int = Field(default=280, description="推文最大字符数")
    scene_min_words: int = Field(default=50, description="场景描述最小词数")
    scene_max_words: int = Field(default=100, description="场景描述最大词数")

    # 日历配置
    default_calendar_days: int = Field(default=15, ge=1, le=90, description="默认生成日历天数")


# ============================================
# 图片生成配置
# ============================================
class ImageGenerationConfig(BaseModel):
    """图片生成器配置"""

    # Z-Image 模型参数
    default_width: int = Field(default=768, ge=512, le=2048, description="默认图片宽度")
    default_height: int = Field(default=1024, ge=512, le=2048, description="默认图片高度")
    default_steps: int = Field(default=9, ge=1, le=50, description="Z-Image-Turbo推荐步数")
    default_cfg: float = Field(default=1.0, ge=0.0, le=20.0, description="CFG scale")

    # LoRA 参数
    default_lora_strength: float = Field(default=1.0, ge=0.0, le=2.0, description="LoRA强度")

    # 负向提示词
    negative_prompt: str = Field(
        default="ugly, deformed, noisy, blurry, low quality",
        description="默认负向提示词"
    )

    # 多GPU配置
    task_queue_timeout: int = Field(default=1, description="任务队列获取超时(秒)")
    result_queue_timeout: int = Field(default=300, description="结果队列获取超时(秒)")
    process_join_timeout: int = Field(default=10, description="进程等待超时(秒)")


# ============================================
# 完整的生成配置集合
# ============================================
class GenerationConfig(BaseModel):
    """统一的生成配置"""

    persona: PersonaGenerationConfig = PersonaGenerationConfig()
    tweet: TweetGenerationConfig = TweetGenerationConfig()
    image: ImageGenerationConfig = ImageGenerationConfig()

    class Config:
        # 可以从JSON/YAML文件加载配置
        json_schema_extra = {
            "example": {
                "persona": {
                    "stage1_core_persona": {"temperature": 0.85, "max_tokens": 4000},
                    "num_example_tweets": 8
                },
                "tweet": {
                    "temperature": 1.0,
                    "max_tokens": 2000
                },
                "image": {
                    "default_width": 768,
                    "default_height": 1024
                }
            }
        }


# ============================================
# 工厂函数 - 支持从文件加载配置
# ============================================
def load_generation_config(config_file: Optional[str] = None) -> GenerationConfig:
    """
    加载生成配置

    Args:
        config_file: 配置文件路径（支持 .json 或 .yaml），None则使用默认值

    Returns:
        GenerationConfig 实例
    """
    if config_file is None:
        return GenerationConfig()

    import json
    from pathlib import Path

    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    if config_path.suffix == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return GenerationConfig(**data)

    elif config_path.suffix in ['.yaml', '.yml']:
        try:
            import yaml
        except ImportError:
            raise ImportError("需要安装 PyYAML: pip install pyyaml")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return GenerationConfig(**data)

    else:
        raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")


# ============================================
# 全局默认配置实例
# ============================================
default_generation_config = GenerationConfig()


# ============================================
# 导出
# ============================================
__all__ = [
    'PersonaGenerationConfig',
    'TweetGenerationConfig',
    'ImageGenerationConfig',
    'GenerationConfig',
    'load_generation_config',
    'default_generation_config'
]
