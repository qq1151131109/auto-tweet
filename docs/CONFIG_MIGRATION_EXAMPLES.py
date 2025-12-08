"""
配置迁移示例 - 展示如何将硬编码参数迁移到配置文件

这个文件展示了如何修改现有代码以使用新的配置系统
"""

# ============================================
# 示例1: 人设生成器迁移
# ============================================

# BEFORE（硬编码）❌
"""
class PersonaGenerator:
    async def _generate_core_persona(self, ...):
        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.85,  # 硬编码
            max_tokens=4000    # 硬编码
        )

    async def _generate_tweet_strategy(self, ...):
        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.85,  # 硬编码
            max_tokens=8000    # 硬编码
        )
"""

# AFTER（使用配置）✅
"""
from config import generation_config

class PersonaGenerator:
    async def _generate_core_persona(self, ...):
        config = generation_config.persona.stage1_core_persona
        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

    async def _generate_tweet_strategy(self, ...):
        config = generation_config.persona.stage2_tweet_strategy
        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
"""


# ============================================
# 示例2: 推文生成器迁移
# ============================================

# BEFORE（硬编码）❌
"""
class StandaloneTweetGenerator:
    async def generate_single_tweet(self, ...):
        # 硬编码的配置
        max_examples = 3
        max_tokens = 2000

        selected_examples = self._select_diverse_examples(
            persona["data"]["extensions"]["twitter_persona"]["tweet_examples"],
            max_examples=max_examples
        )

        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
"""

# AFTER（使用配置）✅
"""
from config import generation_config

class StandaloneTweetGenerator:
    async def generate_single_tweet(self, ...):
        config = generation_config.tweet

        selected_examples = self._select_diverse_examples(
            persona["data"]["extensions"]["twitter_persona"]["tweet_examples"],
            max_examples=config.max_examples
        )

        response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=temperature,  # 可以保留参数传递以支持覆盖
            max_tokens=config.max_tokens
        )
"""


# ============================================
# 示例3: 图片生成器迁移
# ============================================

# BEFORE（硬编码）❌
"""
class ZImageGenerator:
    def generate_image(self, ...):
        # 硬编码的默认值
        width = image_params.get("width", 1024)
        height = image_params.get("height", 1024)
        steps = image_params.get("steps", 9)
        cfg = image_params.get("cfg", 0.0)
        lora_strength = lora_params.get("strength", 1.0)
        negative_prompt = "ugly, deformed, noisy, blurry, low quality"
"""

# AFTER（使用配置）✅
"""
from config import generation_config

class ZImageGenerator:
    def __init__(self):
        self.config = generation_config.image  # 缓存配置

    def generate_image(self, ...):
        # 使用配置作为默认值，仍允许参数覆盖
        width = image_params.get("width", self.config.default_width)
        height = image_params.get("height", self.config.default_height)
        steps = image_params.get("steps", self.config.default_steps)
        cfg = image_params.get("cfg", self.config.default_cfg)
        lora_strength = lora_params.get("strength", self.config.default_lora_strength)
        negative_prompt = self.config.negative_prompt
"""


# ============================================
# 示例4: 在主协调器中使用配置
# ============================================

# BEFORE（硬编码）❌
"""
class HighConcurrencyCoordinator:
    async def generate_calendar_if_needed(self, ...):
        days_to_generate = 15  # 硬编码

    async def generate_persona_from_image(self, ...):
        nsfw_level = "enabled"  # 硬编码
        language = "English"    # 硬编码
"""

# AFTER（使用配置）✅
"""
from config import generation_config

class HighConcurrencyCoordinator:
    async def generate_calendar_if_needed(
        self,
        days_to_generate: int = None,  # 支持参数覆盖
        ...
    ):
        # 使用配置作为默认值
        days = days_to_generate or generation_config.tweet.default_calendar_days

    async def generate_persona_from_image(
        self,
        nsfw_level: str = None,
        language: str = None,
        ...
    ):
        # 使用配置作为默认值
        nsfw = nsfw_level or generation_config.persona.default_nsfw_level
        lang = language or generation_config.persona.default_language
"""


# ============================================
# 示例5: 动态配置加载（高级用法）
# ============================================

"""
from config import settings
from config_generation import load_generation_config

# 场景1: 不同质量级别使用不同配置
def run_generation(quality_level: str):
    if quality_level == "high":
        config = load_generation_config("generation_config_high.yaml")
    elif quality_level == "fast":
        config = load_generation_config("generation_config_fast.yaml")
    else:
        config = settings.load_generation_config()  # 默认配置

    # 使用加载的配置
    generator = PersonaGenerator(config=config)


# 场景2: 根据用户偏好动态调整配置
def customize_config(user_preferences: dict):
    from config import generation_config

    # 运行时修改配置
    if user_preferences.get("high_creativity"):
        generation_config.tweet.temperature = 1.5

    if user_preferences.get("high_resolution"):
        generation_config.image.default_width = 1536
        generation_config.image.default_height = 2048

    return generation_config


# 场景3: 环境特定配置
import os

def load_environment_config():
    env = os.getenv("ENV", "development")
    config_file = f"generation_config.{env}.yaml"

    if os.path.exists(config_file):
        return load_generation_config(config_file)
    else:
        return settings.load_generation_config()
"""


# ============================================
# 示例6: 配置验证和调试
# ============================================

"""
from config import generation_config
import json

def validate_config():
    \"\"\"验证配置是否有效\"\"\"

    # 检查温度范围
    assert 0 <= generation_config.tweet.temperature <= 2.0, "温度超出范围"

    # 检查分辨率
    assert generation_config.image.default_width >= 512, "宽度太小"
    assert generation_config.image.default_height >= 512, "高度太小"

    # 打印配置摘要
    print("=== 当前配置 ===")
    print(f"推文温度: {generation_config.tweet.temperature}")
    print(f"图片分辨率: {generation_config.image.default_width}x{generation_config.image.default_height}")
    print(f"人设示例数: {generation_config.persona.num_example_tweets}")

    # 导出配置到JSON（用于调试）
    config_dict = generation_config.dict()
    print(json.dumps(config_dict, indent=2))


def debug_config_loading():
    \"\"\"调试配置加载过程\"\"\"
    from config import settings
    import os

    print("=== 配置加载调试 ===")

    # 检查环境变量
    config_file = os.getenv("GENERATION_CONFIG_FILE")
    print(f"环境变量 GENERATION_CONFIG_FILE: {config_file}")

    # 检查默认文件
    for filename in ["generation_config.yaml", "generation_config.json"]:
        exists = os.path.exists(filename)
        print(f"{filename}: {'存在' if exists else '不存在'}")

    # 加载配置
    config = settings.load_generation_config()
    print(f"成功加载配置: {type(config)}")
"""


# ============================================
# 最佳实践总结
# ============================================

"""
✅ DO（推荐做法）:
1. 在类初始化时缓存配置
   class Generator:
       def __init__(self):
           self.config = generation_config.tweet

2. 支持参数覆盖（保持灵活性）
   def generate(self, temperature=None):
       temp = temperature or self.config.temperature

3. 使用类型提示
   from config_generation import TweetGenerationConfig
   def process(config: TweetGenerationConfig):
       ...

4. 添加配置验证
   assert config.temperature > 0, "温度必须为正数"


❌ DON'T（避免做法）:
1. 不要在每次调用时重新加载配置
   def generate():
       config = load_generation_config()  # ❌ 低效

2. 不要直接修改全局配置（除非必要）
   generation_config.tweet.temperature = 2.0  # ⚠️ 影响全局

3. 不要绕过配置验证
   config.temperature = 99.0  # ❌ Pydantic会拒绝

4. 不要混合使用多个配置来源（导致混乱）
   temperature = 0.85  # 从哪来的？
"""
