"""
Prompt templates for persona generation
"""

from .core_generation_prompt import (
    get_core_generation_system_prompt,
    get_core_generation_user_prompt,
    get_persona_type_examples
)

from .tweet_generation_prompt import (
    get_tweet_generation_system_prompt,
    get_tweet_generation_user_prompt,
    get_scene_hint_quality_guide
)

__all__ = [
    'get_core_generation_system_prompt',
    'get_core_generation_user_prompt',
    'get_persona_type_examples',
    'get_tweet_generation_system_prompt',
    'get_tweet_generation_user_prompt',
    'get_scene_hint_quality_guide'
]
