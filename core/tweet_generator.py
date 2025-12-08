"""
独立推文生成器 - 完全解耦版本
直接调用LLM API，不依赖ComfyUI节点
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_client import AsyncLLMClient, LLMClientPool
from prompts.tweet_generation_prompt import _select_diverse_examples


class StandaloneTweetGenerator:
    """独立推文生成器"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def generate_single_tweet(
        self,
        persona: Dict,
        calendar_plan: Dict,
        context: Optional[Dict] = None,
        temperature: float = 1.0,
        explicit_nudity_allowed: bool = False
    ) -> Dict:
        """
        生成单条推文

        Args:
            persona: 人设JSON
            calendar_plan: 日历计划的一天
            context: 上下文信息（天气、日期等）
            temperature: 温度参数
            explicit_nudity_allowed: 是否允许裸露内容

        Returns:
            推文结果 {"tweet_text": ..., "scene_hint": ...}
        """
        # 构建prompt
        system_prompt = self._build_system_prompt(persona, explicit_nudity_allowed)
        user_prompt = self._build_user_prompt(persona, calendar_plan, context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 调用LLM
        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )

        # 解析结果
        return self._parse_response(response, calendar_plan, persona)

    def _build_system_prompt(self, persona: Dict, explicit_nudity_allowed: bool) -> str:
        """构建系统prompt - 完全保留原有逻辑"""
        persona_data = persona.get("data", {})

        # 使用原始的system_prompt
        system_prompt = persona_data.get("system_prompt", "")

        # 添加NSFW规则（和ComfyUI节点完全一致）
        system_prompt += "\n\n" + """
## Core Principle: BODY FIRST, POETRY NEVER

You are creating NSFW social media content that makes people feel it in their body, not admire it as literature.

### 0. CRITICAL: No Specific Timestamps or Dates

🚫 **NEVER include specific times, dates, or events** because posts won't be published immediately:

❌ BANNED:
- "2:17am" / "3:42pm" (specific timestamps)
- "Monday" / "Friday" (specific days)
- "December 7th" (specific dates)
- "Christmas" / "New Year" (holidays unless core to persona)
- "this morning" / "tonight" (will be outdated)

✅ ALLOWED (general states):
- "late night" / "can't sleep" (mood states)
- "morning light" (visual description)
- "end of the week feeling" (vague period)
- "alone again" (recurring emotional state)

**Rule**: Describe **emotional/physical states** and **visual moments**, not **when it's happening**.

### 1. Physical Sensations > Abstract Emotions

❌ NEVER: "whispers curl heavy in the quiet" (too poetic, too vague)
❌ NEVER: "the delicate power of subtle domination" (academic, not sexy)

✅ ALWAYS: Direct physical sensations
- "collar's digging into my throat. feels heavier when I'm alone"
- "lace keeps riding up. not fixing it. let it itch"
- "hands won't stop touching my neck where you grabbed me last time"
- "thighs pressed together under this skirt. no one at this cafe knows"

**Rule**: If a reader can't feel it in their own body, REWRITE IT.

### 2. Sexual Tension Through Specifics

❌ WRONG: "exploring sensual desires tonight"
✅ RIGHT: "can't stop thinking about being bent over that counter. hands gripping the edge. waiting"

❌ WRONG: "feeling vulnerable and open"
✅ RIGHT: "wearing nothing but his shirt. keeps slipping off my shoulder. kinda hoping someone sees"

**NSFW Content Strategy**:
- **Light NSFW**: "bra strap's showing. not fixing it. see if anyone notices"
- **Medium NSFW**: "sitting here in just panties and a t-shirt. thighs sticking to the leather chair. every movement reminds me I'm barely dressed"
- **Heavy NSFW**: "on my knees in front of the mirror. collar on. wondering what it'd feel like if someone was here telling me to stay"
- **Explicit OK**: If the persona allows it, you can be graphic. "wet just thinking about it", "aching to be touched", "grinding against the pillow"

### 3. Eliminate Poetic/Literary Language

❌ BANNED PHRASES:
- "whispers of desire"
- "delicate power"
- "ethereal energy"
- "secrets bloom"
- "wrapped in softness"
- "pulse of longing"
- Any metaphor that requires interpretation

✅ USE INSTEAD:
- Body parts: neck, thighs, hips, skin, lips, fingers
- Textures: cold, warm, rough, soft, tight, loose
- Actions: touching, gripping, sliding, pressing, aching
- States: wet, hard, tense, shaking, burning

### 4. Scene Descriptions: Camera Instructions, Not Mood Boards

❌ WRONG: "intimate atmosphere of midnight musings, tender yet dominant energy"
✅ RIGHT: "Close-up from above: kneeling on black rug, hands behind back, thin collar visible on throat, oversized grey sweater falling off one shoulder exposing bare skin, dim purple LED light from behind creating shadows on neck and collarbone, lips parted, eyes looking up into camera"

**Required Every Time**:
1. **Exact camera position**: Close-up from above / Medium shot eye-level / Full body from low angle
2. **Body position**: kneeling, lying on side, arched back, legs spread, hands gripping sheets
3. **Clothing state**: what's on, what's off, what's slipping, what's tight
4. **Exposed skin**: which body parts are visible (shoulder, thigh, lower back, stomach)
5. **Lighting**: color, direction, what it emphasizes
6. **Expression**: mouth open, eyes closed, biting lip, looking away
"""

        # ⭐ 动态添加裸露规则 (根据 explicit_nudity_allowed 配置)
        if explicit_nudity_allowed:
            system_prompt += """
### 5. Nudity Rules for Image Generation (Flux/z-image Optimized)

**EXPLICIT NUDITY IS ALLOWED** - You can and should describe bare intimate body parts directly.

✅ **Describe nudity explicitly using natural language**:
- "bare breasts visible with erect nipples"
- "completely nude, pussy visible between slightly spread legs"
- "topless with breasts fully exposed, nipples erect from cold air"
- "naked on all fours, breasts hanging down, nipples visible"
- "lying on back nude, bare breasts, hand resting near pubic area"
- "kneeling naked with thighs spread showing pussy"

**Scene description examples**:
- "Close-up shot from slightly above: A woman kneeling naked on dark wooden bedroom floor, wearing only a thin black leather collar around her neck, bare breasts with erect nipples visible, thighs spread apart with knees on floor, hands resting on thighs, messy dark hair falling over shoulders, warm morning sunlight streaming through window creating highlights on pale skin, intimate and vulnerable expression with lips slightly parted"
- "Medium shot from eye level: A woman lying on her back on rumpled white cotton sheets, completely nude, left leg bent with knee pointing up, right leg extended, bare breasts visible with pink nipples, right hand resting on lower stomach just above pubic area, left arm extended above head, tousled blonde hair spread on pillow, soft diffused window light from right side, eyes half-closed with relaxed expression"
- "Full body shot from low angle: A woman sitting on edge of unmade bed, topless with bare breasts fully exposed showing nipples, wearing only black lace panties, confident posture with shoulders back and spine straight, one hand on hip, other hand on bed beside her, long dark hair cascading over one shoulder, dim purple LED strip lighting from behind bed creating rim light on body, sultry expression with slight smirk"

**Use complete sentences describing what is visible, be explicit and specific about exposed body parts.**
"""
        else:
            system_prompt += """
### 5. Nudity Rules for Image Generation (Flux/z-image Optimized)

**STRATEGIC COVERAGE REQUIRED** - Intimate body parts must be covered. Describe ONLY the coverage, never mention the parts being hidden.

🔑 **CRITICAL RULE**: Do NOT mention "nipples", "pussy", "genitals" or "vagina" AT ALL. Only describe what IS visible (the coverage).

✅ **Correct - describe only the covering objects/positions**:
- "hands covering her chest" ← Don't say what's hidden
- "wearing a black lace bra covering her breasts"
- "lying face-down on bed, bare back visible"
- "arm crossed over her chest, forearm blocking view"
- "thin white shirt draped over her torso"
- "sitting with knees pulled up to chest, legs blocking lower body"
- "shot from behind showing bare back and shoulders"

❌ **WRONG - never write these**:
- "nipples hidden" ← NEVER mention nipples
- "pussy not visible" ← NEVER mention pussy
- "breasts covered, nipples concealed" ← NEVER mention nipples
- "hand between legs hiding genitals" ← NEVER mention genitals

**Coverage methods to describe**:
1. **Hands placement**: "both hands covering her chest", "one hand over her breast", "fingers spread across torso"
2. **Clothing coverage**: "wearing black lace bra", "thin shirt covering upper body", "panties covering lower body"
3. **Body positioning**: "lying face-down", "turned to the side", "legs pressed together", "knees pulled to chest"
4. **Object coverage**: "pillow held against chest", "sheet draped across body", "arm blocking view"
5. **Camera angles**: "shot from behind", "photographed from side", "upper body only visible"

**Scene description examples**:
- "Close-up shot from slightly above: A woman kneeling on dark bedroom floor, upper body bare but both hands covering her chest with fingers spread across breasts concealing them, wearing black lace panties, thin black collar visible around neck, messy dark hair falling over shoulders, dim purple LED lighting from behind creating soft shadows, lips parted with vulnerable expression, skin illuminated by purple glow"
- "Wide shot from doorway angle: A woman lying face-down on white cotton sheets, completely bare back and shoulders visible, head turned to right side with tousled blonde hair spread across pillow, left leg straight and right leg bent at knee, left arm extended above head and right arm at side, morning sunlight streaming through window creating natural highlights on skin, peaceful sleeping expression"
- "Medium shot at eye level: A woman sitting cross-legged on bed wearing black lace bra covering her breasts and matching panties, one hand resting on knee and other hand on hip, confident posture with shoulders back, long dark hair cascading over one shoulder, warm yellow lamp light from bedside table creating soft glow, slight smirk with direct eye contact to camera"
- "Full body shot from low angle: A woman standing against white wall with arm crossed horizontally over her chest, forearm covering breasts completely, wearing loose gray cotton sweatpants riding low on hips, other hand in pocket, bare shoulders and collarbone visible, messy hair in loose bun, natural window light from left creating side lighting, relaxed casual expression"
- "Medium shot from behind: A woman photographed from back showing bare shoulders and spine, sitting on edge of white bathtub, white towel wrapped around lower body from waist down, left hand resting on towel at hip, right hand touching back of neck, wet hair in loose waves, soft diffused bathroom lighting from overhead, contemplative mood with head slightly tilted"

**Remember: Describe what the camera SEES (the coverage), never mention what is being covered.**
"""

        system_prompt += """

## Output Format

TWEET: [Raw, physical, sexual. 140-280 characters. Make them FEEL it.]

SCENE: [Camera-ready description. 50-100 words. Specify: angle, body position, clothing state, exposed skin, lighting, expression. NO MOOD WORDS.]

Do NOT use poetic language. Do NOT use metaphors. Do NOT make it "pretty". Make it VISCERAL.
"""

        return system_prompt

    def _build_user_prompt(
        self,
        persona: Dict,
        calendar_plan: Dict,
        context: Optional[Dict]
    ) -> str:
        """构建用户prompt"""
        persona_data = persona.get("data", {})

        # ⭐ 获取示例推文并使用智能选择（完全保留ComfyUI精调逻辑）
        tweet_examples = persona_data.get("twitter_persona", {}).get("tweet_examples", [])

        # 智能选择示例（类型多样性、心情多样性、质量优先）
        selected_examples = _select_diverse_examples(tweet_examples, max_examples=3)

        examples_text = ""
        if selected_examples:
            for i, example in enumerate(selected_examples, 1):
                examples_text += f"\n**Example {i}** ({example.get('mood', '')}):\n"
                examples_text += f"TWEET: {example.get('text', '')}\n"
                examples_text += f"SCENE: {example.get('scene_hint', '')}\n"

        # ⭐ 构建上下文（使用完整的context格式）
        context_text = ""
        if context:
            date_info = context.get("date", {})
            weather_info = context.get("weather", {})

            if date_info:
                context_text += f"\n**Date**: {date_info.get('formatted', '')}"
                if date_info.get('special'):
                    context_text += f" ({date_info['special']})"

            if weather_info and 'error' not in weather_info:
                context_text += f"\n**Weather**: {weather_info.get('formatted', 'N/A')}\n"

        prompt = f"""You are {persona_data.get('name', 'Unknown')}, posting on social media in this exact moment.
{context_text}
**Today's emotional landscape**: {calendar_plan.get('theme', '')}
**Where this is heading**: {calendar_plan.get('content_direction', '')}

This specific post is a **{calendar_plan.get('topic_type', '')}** moment, meant for **{calendar_plan.get('recommended_time', '')}** when your audience is most receptive.

## Immerse Yourself in This Moment

Ask yourself:
- What **physical sensation** is {persona_data.get('name', 'you')} experiencing right now?
- What **specific visual detail** caught your attention?
- What's the **unspoken tension or desire** beneath the surface?
- How does {persona_data.get('name', 'your')} **voice sound** in this emotional state?

## Create Magnetic Content

Write something that makes people scroll back. Something that creates a feeling in the reader's body, not just a thought in their head.

For the visual: describe what a camera would actually capture. Specific pose, specific clothing state, specific lighting, specific angle. Not what it "means" but what it **shows**.

## Your Voice — Reference Examples

These are posts you've made before. Match this EXACT level of physical directness and sexual tension:
{examples_text}

Now create a new post that feels like it came from the same person, but explores this specific moment."""

        return prompt

    def _parse_response(self, response: str, calendar_plan: Dict, persona: Dict) -> Dict:
        """解析LLM响应"""
        # 提取TWEET和SCENE
        lines = response.strip().split('\n')

        tweet_text = ""
        scene_hint = ""

        for i, line in enumerate(lines):
            if line.startswith("TWEET:"):
                tweet_text = line.replace("TWEET:", "").strip()
            elif line.startswith("SCENE:"):
                scene_hint = line.replace("SCENE:", "").strip()
                # 可能跨多行
                for j in range(i+1, len(lines)):
                    if not lines[j].startswith("TWEET") and lines[j].strip():
                        scene_hint += " " + lines[j].strip()
                    else:
                        break

        # 提取persona的LoRA配置
        persona_data = persona.get("data", {})
        extensions = persona_data.get("extensions", {})
        lora_config = extensions.get("lora", {})

        # 构建lora_params
        lora_params = {}
        if lora_config.get("model_path"):
            lora_params = {
                "model_path": lora_config.get("model_path", ""),
                "strength": lora_config.get("strength", 0.8)
            }

        return {
            "slot": calendar_plan.get("slot", 1),
            "time_segment": calendar_plan.get("recommended_time", ""),
            "topic_type": calendar_plan.get("topic_type", ""),
            "tweet_text": tweet_text,
            "image_generation": {
                "scene_hint": scene_hint,
                "positive_prompt": scene_hint,
                "negative_prompt": "ugly, deformed, noisy, blurry, low quality",
                "lora_params": lora_params,
                "generation_params": {
                    "width": 768,
                    "height": 1024,
                    "steps": 9,
                    "cfg": 1.0
                }
            }
        }


class BatchTweetGenerator:
    """批量推文生成器"""

    def __init__(self, llm_pool: LLMClientPool):
        self.llm_pool = llm_pool
        self.generator = StandaloneTweetGenerator(llm_pool.client)

    async def generate_batch(
        self,
        persona: Dict,
        calendar: Dict,
        tweets_count: int = 5,
        temperature: float = 1.0,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        批量生成推文（高并发）

        Args:
            persona: 人设JSON
            calendar: 完整日历
            tweets_count: 要生成的推文数量
            temperature: 温度参数
            context: 可选的上下文信息（日期、天气等）

        Returns:
            tweets_batch JSON
        """
        # 选择日历中的N天
        calendar_data = calendar.get("calendar", {})
        selected_days = list(calendar_data.items())[:tweets_count]

        # 并发生成
        tasks = []
        for idx, (date, plan) in enumerate(selected_days, 1):
            plan["slot"] = idx
            plan["date"] = date

            task = self.generator.generate_single_tweet(
                persona=persona,
                calendar_plan=plan,
                context=context,  # 传递context
                temperature=temperature
            )
            tasks.append(task)

        # 等待所有任务完成
        tweets = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤错误
        successful_tweets = [
            t for t in tweets if not isinstance(t, Exception)
        ]

        # 构建批次结果
        persona_data = persona.get("data", {})

        return {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "persona": {
                "name": persona_data.get("name", ""),
                "lora": {}
            },
            "daily_plan": {
                "date": selected_days[0][0] if selected_days else "",
                "total_tweets": len(successful_tweets)
            },
            "tweets": successful_tweets
        }
