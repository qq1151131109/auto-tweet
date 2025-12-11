"""
Standalone Persona Generator
独立人设生成器 - 完全复制ComfyUI精调逻辑
"""
import asyncio
import json
import base64
import io
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_client import AsyncLLMClient
from utils.json_parser import parse_llm_json_response
from prompts.core_generation_prompt import (
    get_core_generation_system_prompt,
    get_core_generation_user_prompt
)


class PersonaGenerator:
    """
    完整的人设生成器
    完全保留ComfyUI的多阶段生成流程和精调prompts
    """

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def generate_from_image(
        self,
        image_path: str,
        nsfw_level: str = "enabled",
        language: str = "English",
        location: str = "",
        business_goal: str = "",
        custom_instructions: str = "",
        temperature: float = 0.85
    ) -> Dict:
        """
        从图片生成完整人设（多阶段流程）
        完全保留ComfyUI的PersonaCoreGenerator逻辑

        Args:
            image_path: 图片文件路径
            nsfw_level: "disabled" 或 "enabled"
            language: "English" 或 "中文"
            location: 地理位置（留空自动生成）
            business_goal: 业务目标
            custom_instructions: 自定义控制词
            temperature: 温度参数

        Returns:
            完整的人设JSON（SillyTavern Character Card V2格式）
        """
        print(f"\n{'='*70}")
        print(f"🏗️  PersonaGenerator: Generating complete persona from image")
        print(f"    ✨ Multi-stage generation with精调 prompts")
        print(f"{'='*70}\n")

        # Stage 1: Core Persona Generation（核心人设生成）
        print("📍 Stage 1: Generating core persona...")
        core_persona = await self._generate_core_persona(
            image_path, nsfw_level, language, location,
            business_goal, custom_instructions, temperature
        )

        # Stage 2: Tweet Strategy Generation（推文策略生成）
        print("\n📍 Stage 2: Generating tweet strategy...")
        strategy = await self._generate_tweet_strategy(core_persona, temperature)

        # Stage 3: Example Tweets Generation（示例推文生成）
        print("\n📍 Stage 3: Generating example tweets...")
        tweets = await self._generate_example_tweets(
            core_persona, strategy, num_tweets=8, temperature=0.9
        )

        # ⚡ Stage 4-7: 并发生成（这些阶段只依赖core_persona，互相独立）
        print("\n⚡ Stage 4-7: Parallel generation (social, authenticity, visual, knowledge)...")

        # 创建并发任务
        stage_4_task = self._generate_social_network(core_persona, temperature=0.85)
        stage_5_task = self._generate_authenticity(core_persona, temperature=0.8)
        stage_6_task = self._extract_visual_profile(core_persona, temperature=0.8)
        stage_7_task = self._generate_character_book(core_persona, num_entries=6, temperature=0.8)

        # 🚀 并发执行 Stage 4-7
        results = await asyncio.gather(
            stage_4_task,
            stage_5_task,
            stage_6_task,
            stage_7_task,
            return_exceptions=True
        )

        # 解包结果
        social_data = results[0] if not isinstance(results[0], Exception) else {}
        authenticity = results[1] if not isinstance(results[1], Exception) else {}
        visual_profile = results[2] if not isinstance(results[2], Exception) else {}
        character_book = results[3] if not isinstance(results[3], Exception) else {}

        # 检查错误
        for i, result in enumerate(results, start=4):
            if isinstance(result, Exception):
                print(f"  ⚠️  Stage {i} failed: {result}")

        print("  ✓ Parallel stages completed")

        # Final Stage: Merge All Components（合并所有组件）
        print("\n📍 Final Stage: Merging all components...")
        complete_persona = self._merge_persona_components(
            core_persona, tweets, social_data, authenticity,
            visual_profile, character_book
        )

        print(f"\n✅ Persona generation complete!")
        print(f"   Name: {complete_persona['data']['name']}")
        print(f"   Total tweet examples: {len(complete_persona['data'].get('twitter_persona', {}).get('tweet_examples', []))}")
        print(f"{'='*70}\n")

        return complete_persona

    def _image_to_base64(self, image_path: str) -> str:
        """将图片转换为base64"""
        with Image.open(image_path) as img:
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            return base64.b64encode(img_bytes).decode('utf-8')

    async def _generate_core_persona(
        self,
        image_path: str,
        nsfw_level: str,
        language: str,
        location: str,
        business_goal: str,
        custom_instructions: str,
        temperature: float
    ) -> Dict:
        """
        Stage 1: 核心人设生成
        完全保留ComfyUI PersonaCoreGenerator的prompt逻辑
        """
        # 转换图像为base64
        base64_image = self._image_to_base64(image_path)
        image_url = f"data:image/png;base64,{base64_image}"

        # 构建base_params（完全保留ComfyUI逻辑）
        base_params = {
            "nsfw_level": nsfw_level,
            "language": language,
            "location": location if location.strip() else "请自动生成合适的地理位置",
            "business_goal": business_goal,
            "custom_instructions": custom_instructions
        }

        # 使用精调的prompts（从prompts/core_generation_prompt.py）
        system_prompt = get_core_generation_system_prompt(language)
        appearance_analysis = "Analyze the appearance in the provided image carefully."
        user_prompt = get_core_generation_user_prompt(appearance_analysis, base_params)

        # 调用LLM（支持vision）
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=4000
        )

        # 解析JSON（完全保留ComfyUI的解析逻辑）
        core_persona = self._parse_json_response(response)

        return core_persona

    async def _generate_tweet_strategy(
        self,
        core_persona: Dict,
        temperature: float
    ) -> Dict:
        """
        Stage 2: 推文策略生成
        完全保留ComfyUI PersonaTweetStrategyGenerator的逻辑
        """
        data = core_persona.get('data', {})

        system_prompt = """You are a social media strategy expert specializing in authentic content planning.

Create a CUSTOM content strategy that matches this persona's unique characteristics, NOT generic categories.

CRITICAL: Analyze the persona's personality, tags, and background to derive SPECIFIC content types that fit THEM.

Output ONLY valid JSON, no markdown blocks."""

        user_prompt = f"""Create a custom content strategy for this persona:

CHARACTER:
Name: {data.get('name', '')}
Tags: {', '.join(data.get('tags', []))}
Personality: {data.get('personality', '')[:500]}
Description: {data.get('description', '')[:300]}

OUTPUT FORMAT:
{{
  "content_type_distribution": {{
    "custom_type_1": {{
      "weight": 0.25,
      "desc": "Description of what this type means for THIS persona"
    }},
    "custom_type_2": {{
      "weight": 0.20,
      "desc": "..."
    }}
    // 5-8 types total, weights sum to 1.0
  }}
}}

CRITICAL GUIDELINES:
1. Content types must be SPECIFIC to this persona, not generic
2. **IMPORTANT**: Mirror selfies (especially iPhone selfies in bathroom/bedroom) perform extremely well and should be heavily weighted (20-30%)
3. Include variations like:
   - "bathroom_mirror_selfie" or "bedroom_mirror_selfie" - showing off outfit/body
   - "gym_mirror_selfie" - post-workout physique shots
   - "fitting_room_selfie" - trying on clothes
4. Mirror selfies are versatile and work for almost any persona - they're casual, authentic, and high-engagement"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=8000
        )

        return self._parse_json_response(response)

    async def _generate_example_tweets(
        self,
        core_persona: Dict,
        strategy: Dict,
        num_tweets: int,
        temperature: float
    ) -> Dict:
        """
        Stage 3: 生成示例推文
        完全保留ComfyUI PersonaTweetGenerator的逻辑
        """
        data = core_persona.get('data', {})

        # 这里使用tweet_generation_prompt.py中的prompts
        from prompts.tweet_generation_prompt import (
            get_tweet_generation_system_prompt,
            get_tweet_generation_user_prompt
        )

        system_prompt = get_tweet_generation_system_prompt()
        user_prompt = get_tweet_generation_user_prompt(
            core_persona, num_tweets=num_tweets, strategy=strategy
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=8000
        )

        # 解析tweets array
        tweets_data = self._parse_json_response(response)

        # 包装成twitter_persona格式
        return {
            "twitter_persona": {
                "tweet_examples": tweets_data if isinstance(tweets_data, list) else tweets_data.get("tweets", [])
            }
        }

    async def _generate_social_network(
        self,
        core_persona: Dict,
        temperature: float
    ) -> Dict:
        """
        Stage 4: 社交关系生成
        完全保留ComfyUI PersonaSocialGenerator的逻辑
        """
        data = core_persona.get('data', {})

        system_prompt = """You are an expert at creating believable social networks for characters.

Create detailed, realistic relationships with:
1. Specific personalities and backgrounds for each person
2. Detailed stories of how they met and their history
3. Specific memories and shared experiences
4. Realistic interaction patterns and contact frequency
5. Natural conflicts, support, and dynamics

Output ONLY valid JSON, no markdown blocks.

CRITICAL: Each relationship should feel like a real person with depth, not a cardboard cutout."""

        user_prompt = f"""Create a detailed social network for this character:

CHARACTER:
Name: {data.get('name', '')}
Age: {data.get('core_info', {}).get('age', 23)}
Personality: {data.get('personality', '')[:500]}
Description: {data.get('description', '')[:300]}

REQUIRED OUTPUT:
{{
  "social_circle": {{
    "close_friends": [
      // 2-3 detailed friends with full backgrounds
    ],
    "past_relationships": [
      // 1-2 past romantic relationships with stories
    ],
    "online_friends": [
      // 2-3 online connections
    ]
  }}
}}

Each person needs: name, age, relation, personality, backstory, current_status, memorable_moments, interaction_pattern."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=4000
        )

        return self._parse_json_response(response)

    async def _generate_authenticity(
        self,
        core_persona: Dict,
        temperature: float
    ) -> Dict:
        """
        Stage 5: 真实感系统生成
        完全保留ComfyUI PersonaAuthenticityGenerator的逻辑
        """
        data = core_persona.get('data', {})

        system_prompt = """You are an expert at making AI personas feel genuinely human and authentic.

Create strategic imperfections and authentic patterns that make this character feel REAL.

Output ONLY valid JSON, no markdown blocks."""

        user_prompt = f"""Create authenticity systems for this character:

CHARACTER:
Name: {data.get('name', '')}
Personality: {data.get('personality', '')[:500]}

OUTPUT:
{{
  "language_authenticity": {{
    "capitalization": {{"casual_lowercase_rate": 0.3}},
    "punctuation_style": {{"omit_final_period": 0.6}},
    "typo_patterns": {{"enabled": true, "base_rate": 0.1}},
    "filler_words": {{"usage_rate": 0.4}},
    "slang_and_abbreviations": {{"usage_rate": 0.5}}
  }},
  "strategic_flaws": {{
    "active_flaws": [
      {{
        "type": "sleep_deprived",
        "frequency": 0.2,
        "manifestations": ["..."]
      }}
    ]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=3000
        )

        return self._parse_json_response(response)

    async def _extract_visual_profile(
        self,
        core_persona: Dict,
        temperature: float
    ) -> Dict:
        """
        Stage 6: 视觉档案提取
        完全保留ComfyUI PersonaVisualProfileExtractor的逻辑
        """
        data = core_persona.get('data', {})

        system_prompt = """Extract and organize visual elements for consistent image generation.

Create detailed outfit catalogs, pose guidelines, and atmosphere keywords.

Output ONLY valid JSON."""

        user_prompt = f"""Extract visual profile for:

CHARACTER:
Appearance: {data.get('appearance', {})}
Style: {data.get('appearance', {}).get('style', '')}

OUTPUT:
{{
  "visual_profile": {{
    "common_outfits": ["outfit descriptions..."],
    "common_props": ["props..."],
    "color_preferences": ["colors..."],
    "lighting_preferences": ["lighting setups..."],
    "typical_poses": ["pose descriptions..."],
    "atmosphere_keywords": ["moods..."],
    "camera_angles": ["angle descriptions..."]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )

        return self._parse_json_response(response)

    async def _generate_character_book(
        self,
        core_persona: Dict,
        num_entries: int,
        temperature: float
    ) -> Dict:
        """
        Stage 7: 知识库生成
        完全保留ComfyUI PersonaCharacterBookGenerator的逻辑
        """
        data = core_persona.get('data', {})

        system_prompt = """Create a character knowledge base with deep contextual entries.

Each entry should provide rich context that deepens understanding of the character.

Output ONLY valid JSON."""

        user_prompt = f"""Create character book for:

CHARACTER:
Name: {data.get('name', '')}
Description: {data.get('description', '')[:500]}

Create {num_entries} knowledge entries about key aspects of their life.

OUTPUT:
{{
  "character_book": {{
    "entries": [
      {{
        "id": 1,
        "keys": ["keyword1", "keyword2"],
        "content": "Detailed contextual information...",
        "enabled": true
      }}
    ]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=5000
        )

        return self._parse_json_response(response)

    def _merge_persona_components(
        self,
        core_persona: Dict,
        tweets: Dict,
        social_data: Dict,
        authenticity: Dict,
        visual_profile: Dict,
        character_book: Dict
    ) -> Dict:
        """
        Final Stage: 合并所有组件
        完全保留ComfyUI PersonaMerger的逻辑
        """
        # 深拷贝core_persona
        import copy
        merged = copy.deepcopy(core_persona)

        # 合并twitter_persona
        if "twitter_persona" in tweets:
            merged["data"]["twitter_persona"] = tweets["twitter_persona"]

        # 合并social_circle
        if "social_circle" in social_data:
            merged["data"]["social_circle"] = social_data["social_circle"]

        # 合并language_authenticity和strategic_flaws
        if "language_authenticity" in authenticity:
            merged["data"]["language_authenticity"] = authenticity["language_authenticity"]
        if "strategic_flaws" in authenticity:
            merged["data"]["strategic_flaws"] = authenticity["strategic_flaws"]

        # 合并visual_profile
        if "visual_profile" in visual_profile:
            merged["data"]["visual_profile"] = visual_profile["visual_profile"]

        # 合并character_book
        if "character_book" in character_book:
            merged["data"]["character_book"] = character_book["character_book"]

        return merged

    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM返回的JSON（使用统一的解析工具）"""
        return parse_llm_json_response(
            response,
            source_name="PersonaGenerator",
            enable_fallback=True
        )
