"""
配置包 - 统一的配置管理

这个包提供了项目的所有配置管理功能：
- settings: 基础设施配置（API、Redis、Celery等）
- generation_config: 生成流程配置（人设、推文、图片参数）

使用方法:
    from config import settings, generation_config

    # 使用基础设施配置
    api_key = settings.llm_api_key

    # 使用生成配置
    temperature = generation_config.tweet.temperature
"""

from config.settings import Settings, settings
from config.generation import (
    GenerationConfig,
    PersonaGenerationConfig,
    TweetGenerationConfig,
    ImageGenerationConfig,
    load_generation_config
)

# 全局生成配置实例
generation_config = settings.load_generation_config()

# 导出所有配置
__all__ = [
    # 基础设施配置
    'Settings',
    'settings',

    # 生成配置
    'GenerationConfig',
    'PersonaGenerationConfig',
    'TweetGenerationConfig',
    'ImageGenerationConfig',
    'load_generation_config',
    'generation_config',
]
