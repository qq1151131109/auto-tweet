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
        result = self._parse_response(response, calendar_plan, persona)

        # 检查推文长度并自动改写
        tweet_text = result.get("tweet_text", "")
        max_retries = 3
        retry_count = 0

        while len(tweet_text) > 270 and retry_count < max_retries:
            print(f"⚠️ 推文超长 ({len(tweet_text)}字符), 触发改写 (第{retry_count+1}次)")
            tweet_text = await self._rewrite_tweet(tweet_text, persona)
            result["tweet_text"] = tweet_text
            retry_count += 1

        if len(tweet_text) > 270:
            print(f"⚠️ 警告: 推文在{max_retries}次改写后仍超过270字符 ({len(tweet_text)}字符)")

        return result

    async def generate_from_spec(
        self,
        persona: Dict,
        generation_spec: Dict,
        temperature: float = 1.0,
        explicit_nudity_allowed: bool = False
    ) -> Dict:
        """
        从generation_spec生成推文（新版，用于pool generation）

        Args:
            persona: 人设JSON
            generation_spec: 生成规格（来自ContentPlanner）
            temperature: 温度参数
            explicit_nudity_allowed: 是否允许裸露内容

        Returns:
            推文结果 {"tweet_text": ..., "scene_hint": ..., "content_type": ..., "subtype": ...}
        """
        # 构建prompt
        system_prompt = self._build_system_prompt(persona, explicit_nudity_allowed)
        user_prompt = self._build_user_prompt_from_spec(persona, generation_spec)

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
        result = self._parse_response(response, generation_spec, persona)

        # 添加generation_spec信息到结果
        result["content_type"] = generation_spec.get("content_type", "")
        result["subtype"] = generation_spec.get("subtype", "")
        result["mood"] = generation_spec.get("mood", "")

        # 检查推文长度并自动改写
        tweet_text = result.get("tweet_text", "")
        max_retries = 3
        retry_count = 0

        while len(tweet_text) > 270 and retry_count < max_retries:
            print(f"⚠️ 推文超长 ({len(tweet_text)}字符), 触发改写 (第{retry_count+1}次)")
            tweet_text = await self._rewrite_tweet(tweet_text, persona)
            result["tweet_text"] = tweet_text
            retry_count += 1

        if len(tweet_text) > 270:
            print(f"⚠️ 警告: 推文在{max_retries}次改写后仍超过270字符 ({len(tweet_text)}字符)")

        return result

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
7. **Realism modifiers**: Add 2-4 realistic photography qualities (see below)

### 4.3. CRITICAL: US Market Aesthetic Optimization

🎯 **Goal**: Appeal to American male gaze by emphasizing sexual maturity, confidence, and vitality.

**Body Language & Posing** (CRITICAL - avoid East Asian aesthetics):

✅ **DO - Confident & Space-Occupying**:
- **Direct eye contact with camera** - creates parasocial connection, signals confidence
- **Arched back pose** (anterior pelvic tilt) - emphasizes waist-hip ratio and curves
- **Legs apart stance** - weight shifted to one hip (contrapposto), shows confidence
- **Arms away from body** - stretched out, hands on hips, occupying space
- **Open chest** - shoulders back, spine straight, displaying second sexual characteristics

❌ **DON'T - Submissive & Shrinking**:
- Eye contact avoidance, looking down, covering face with hands
- Pigeon-toed stance (内八字), feet together, knees touching
- Hunched shoulders, arms pressed against body
- Head tilted down excessively, hiding neck
- Pouting lips or overly innocent expressions

**Facial Expression & Gaze**:

✅ **Confident Western Expressions**:
- **"Bedroom eyes"** - eyelids slightly lowered but gaze focused and intense
- **Parted lips** showing teeth slightly, tongue barely visible
- **Smirk or knowing smile** - "I know I'm attractive" attitude
- **Direct stare into camera** - making viewer feel "seen" and "wanted"

❌ **Avoid Neotenic/Innocent Expressions**:
- Overly wide doe eyes trying to look innocent
- Covering mouth when smiling
- Biting finger or excessive cutesy gestures
- Blank or confused expressions

**Body Emphasis** (American preference):

✅ **Highlight These Features**:
- **Waist-hip ratio** - emphasize curves through pose (side angles, back arches)
- **Curvy/athletic build** - "slim-thick" aesthetic (thin waist, full hips/thighs)
- **Toned legs and glutes** - fitness culture influence, visible muscle definition
- **Strong defined features** - high cheekbones, defined jawline, arched brows

❌ **Avoid These Signals**:
- Stick-thin limbs without curves or muscle tone
- Trying to appear smaller/younger than actual age
- Hiding body curves with loose/oversized clothing (unless styled as "boyfriend shirt")
- Childish proportions or doll-like features

**Skin Tone & Texture**:

✅ **Healthy Western Aesthetic**:
- **Warm/golden skin tone** - sun-kissed, tan aesthetic (NOT pale)
- **Glossy/dewy skin** - visible sheen, looks touchable and alive
- **Natural texture visible** - pores, fine lines show authenticity
- Use descriptors: "sun-kissed skin", "golden glow", "healthy tan"

❌ **Avoid Cold/Artificial Look**:
- Cold pale white skin (冷白皮)
- Overly smoothed porcelain doll skin
- Flat matte complexion without dimension

**Styling & Archetypes** (High-conversion niches):

✅ **ABG (Asian Baby Girl) Style** - Recommended for Asian creators:
- **Hair**: Highlights (balayage), platinum/ash blonde streaks, never pure black
- **Makeup**: Heavy contour, arched brows, thick lashes, overlined nude lips
- **Attitude**: "Bad bitch energy" - confident, assertive, slightly aggressive
- **Clothing**: Bodycon dresses, crop tops, athleisure (yoga pants), streetwear
- **Accessories**: Hoop earrings, temporary tattoos (thigh/arm), acrylic nails

✅ **Gym Girl/Fitness Aesthetic**:
- Athletic wear: tight leggings, sports bra, showing muscle definition
- Setting: gym mirrors, workout equipment visible in background
- Pose: mid-workout or post-workout glow, showing strength
- Signals discipline, health, and upper-class leisure time

✅ **E-girl/Gamer Girl** (for petite builds):
- Props: cat ear headphones, RGB lighting, gaming setup
- Clothing: pleated skirts, thigh-high socks, oversized hoodies
- Makeup: winged eyeliner, blush on nose, playful expressions
- Can be pale-skinned (indoor gamer aesthetic acceptable)

**Cultural Translation Guide**:

| Avoid (East Asian) | Use Instead (US Market) |
|-------------------|------------------------|
| "Innocent schoolgirl" vibe | "Confident college student" vibe |
| Shy hiding behind hands | Direct seductive gaze |
| Twintails + sailor uniform | Messy bun + crop top + high-waisted jeans |
| Pale porcelain skin | Sun-kissed golden skin |
| Tiny delicate frame | Curvy athletic build |
| Submissive body language | Dominant/equal power stance |

**Example Scenarios**:

✅ GOOD (US-optimized):
"Medium shot from low angle: Woman standing in gym wearing tight black leggings and purple sports bra, one hand on hip, other hand running through messy ponytail, direct confident gaze into camera, visible ab definition, golden tan skin with slight sheen of sweat, arched back emphasizing curves, legs shoulder-width apart, gym equipment blurred in background, warm fluorescent lighting, smirking expression"

❌ BAD (East Asian aesthetic - will underperform in US):
"Woman in bedroom wearing oversized pastel sweater and white knee socks, sitting on bed with knees pulled to chest, looking down shyly avoiding camera, pale white skin, small delicate frame, twin braids, hands covering lower face, soft pink lighting, innocent doe eyes"

### 4.5. CRITICAL: Realistic Photography Style

🎯 **Goal**: Make images look like authentic phone photos, NOT AI-generated perfect renders.

**ALWAYS include 2-4 realistic modifiers at the END of your scene description**:

**Core Authenticity** (choose 2-3, PRIORITIZE these):
- "Raw photo" - unedited, straight from camera [USE FREQUENTLY]
- "candid photography" - natural, unposed moment [USE FREQUENTLY]
- "authentic snapshot" - real moment captured [USE FREQUENTLY]
- "smartphone camera aesthetic" - phone camera quality
- "shot on iPhone" - casual phone photography

**Natural Imperfections** (choose 2, use liberally for realism):
- "messy background" - cluttered, real environment [USE IN 70% OF SCENES - both indoor AND outdoor]
- "uneven skin tone" - natural skin texture, not airbrushed [USE FREQUENTLY]
- "motion blur" - subject moving [USE IN 40% OF SCENES - even slight movements count]
- "Chromatic aberration" - lens color fringing [USE OFTEN]
- "slightly out of focus" - not perfectly sharp (use moderately, not too much)

**Lighting Variations** (choose 1 if applicable):
- "low lighting" - dim/night scenes
- "overexposed" - very bright/sunny scenes (use liberally in daylight)
- "underexposed" - shadowy/dim areas (use liberally in indoor scenes)

**Camera Effects** (optional, choose 0-1):
- "in motion" - capturing movement
- "GoPro lens" - wide angle distortion
- "amateur photography" - not professionally shot

**Atmospheric** (optional, rare):
- "eerie atmosphere" - mysterious/creepy scenes only

**Format**: Add these modifiers as a natural continuation at the end:
"[main scene description], Raw photo, candid photography, messy background, uneven skin tone"

**Examples**:

❌ BAD (too perfect, no realism):
"Woman in bedroom wearing lingerie, perfect lighting, professional quality"

✅ GOOD (realistic):
"Late evening bedroom, woman kneeling on carpet wearing oversized t-shirt and panties, dim purple LED light from behind bed, messy hair, vulnerable expression, Raw photo, candid photography, authentic snapshot, messy background, uneven skin tone, low lighting"

✅ GOOD (outdoor):
"Afternoon at outdoor cafe, woman sitting at table with coffee, bright sunlight through windows, casual sundress, people visible in blurred background, candid photography, messy background, motion blur, Chromatic aberration, slightly overexposed"

✅ GOOD (movement):
"Woman walking quickly through hallway, motion in frame, casual clothes, hair moving, natural indoor lighting, authentic snapshot, motion blur, messy background, in motion, amateur photography"

✅ GOOD (indoor):
"Morning bathroom mirror selfie, woman holding iPhone showing reflection, messy hair, casual t-shirt, bathroom counter cluttered with makeup, Raw photo, authentic snapshot, messy background, uneven skin tone, Chromatic aberration"

**Scene Type Guidance** (UPDATED - use these liberally):
- Night/dark scenes → ALWAYS include "low lighting"
- Outdoor/public → ALWAYS include "messy background"
- Indoor scenes → ALWAYS include "messy background" (70% of time)
- Moving subject → ALWAYS include "motion blur" and optionally "in motion"
- Bright/sunny → ALWAYS include "overexposed" (60% of time, not 20%)
- Indoor shadows → include "underexposed" (40% of time, not 20%)
- Mirror selfies → ALWAYS include "authentic snapshot" + "messy background"

**CRITICAL**: Default to MORE realism modifiers, not less. Aim for 3-4 modifiers per scene, not 2.
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
        """构建用户prompt（旧版，calendar-based）"""
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

    def _build_user_prompt_from_spec(
        self,
        persona: Dict,
        generation_spec: Dict
    ) -> str:
        """
        从generation_spec构建用户prompt（新版，pool generation）

        Args:
            persona: Persona数据
            generation_spec: 生成规格，包含:
                - content_type: 内容类型
                - subtype: 子类型
                - subtype_description: 子类型描述
                - variations: 变化维度字典
                - mood: 心情
        """
        persona_data = persona.get("data", {})

        # 获取示例推文
        tweet_examples = persona_data.get("twitter_persona", {}).get("tweet_examples", [])
        selected_examples = _select_diverse_examples(tweet_examples, max_examples=3)

        examples_text = ""
        if selected_examples:
            for i, example in enumerate(selected_examples, 1):
                examples_text += f"\n**Example {i}** ({example.get('mood', '')}):\n"
                examples_text += f"TWEET: {example.get('text', '')}\n"
                examples_text += f"SCENE: {example.get('scene_hint', '')}\n"

        # 提取generation_spec信息
        content_type = generation_spec.get('content_type', 'casual_selfie')
        subtype = generation_spec.get('subtype', '')
        subtype_desc = generation_spec.get('subtype_description', '')
        variations = generation_spec.get('variations', {})
        mood = generation_spec.get('mood', 'confident')

        # 构建详细的场景指导
        scene_guidance = f"""
**Content Type**: {content_type.replace('_', ' ').title()}
**Specific Scene**: {subtype.replace('_', ' ').title()} - {subtype_desc}
**Mood**: {mood}

**Scene Requirements**:"""

        for dim, value in variations.items():
            dim_name = dim.replace('_', ' ').title()
            scene_guidance += f"\n- {dim_name}: {value}"

        prompt = f"""You are {persona_data.get('name', 'Unknown')}, creating alluring social media content.

{scene_guidance}

## CRITICAL: Content Creation Rules

1. **NO Timestamps or Dates**: This content will be published later
   - ❌ NEVER: "2:17am", "Monday", "tonight", "this morning"
   - ✅ ALWAYS: General states like "late night", "can't sleep", "feeling restless"

2. **Create Standalone Content**: This post should work ANY day, ANY time
   - Write about a **mood** or **physical state**, not a specific moment in time
   - Focus on sensations, desires, visual details - not temporal references

3. **Follow Scene Requirements EXACTLY**:
   - You MUST incorporate ALL the scene requirements listed above
   - Don't deviate from the specified camera angle, clothing, lighting, etc.
   - These create visual variety across multiple posts

4. **Match Your Authentic Voice**:
{examples_text}

5. **Visual Description Must Include**:
   - Exact camera position and angle (as specified)
   - Precise clothing description (as specified)
   - Specific body position and pose
   - Lighting details (as specified)
   - Your facial expression matching the mood: {mood}
   - 2-4 realistic photography modifiers (Raw photo, candid, etc.)

## Create Content NOW

Write a tweet and scene description that:
- Feels authentic and personal (like your examples)
- Works standalone without time references
- Incorporates all specified scene requirements
- Captures the {mood} mood
- Makes people feel it in their body, not just admire it

Output format:
TWEET: [140-280 characters, raw physical sensations, {mood} mood]
SCENE: [Detailed camera-ready description following ALL requirements above]"""

        return prompt

    async def _rewrite_tweet(self, original_tweet: str, persona: Dict) -> str:
        """
        改写超长推文，保持原意但缩短长度

        Args:
            original_tweet: 原始推文文本
            persona: 人设JSON

        Returns:
            改写后的推文文本
        """
        persona_data = persona.get("data", {})

        rewrite_prompt = f"""You are {persona_data.get('name', 'Unknown')}.

Your previous tweet is TOO LONG ({len(original_tweet)} characters) and exceeds Twitter's 280 character limit.

**Original tweet**:
{original_tweet}

**Task**: Rewrite this tweet to be UNDER 270 characters while:
1. **Preserving the core meaning and emotion** - keep the same vibe and message
2. **Maintaining your authentic voice** - same tone, same style
3. **Keeping the physical/sensory details** - don't lose the visceral quality
4. **Cutting unnecessary words** - remove filler, redundancy, over-description

**Strategies to shorten**:
- Remove redundant adjectives ("wet and dripping" → "dripping")
- Cut filler words ("just", "really", "kinda", "like")
- Use contractions ("I am" → "I'm", "cannot" → "can't")
- Merge similar phrases
- Keep the most impactful sensory detail, drop the rest

**Output ONLY the rewritten tweet text** (no "TWEET:" prefix, no explanations, just the raw tweet).
"""

        messages = [
            {"role": "user", "content": rewrite_prompt}
        ]

        response = await self.llm.generate(
            messages=messages,
            temperature=0.7,  # 稍低温度保持一致性
            max_tokens=500
        )

        # 清理响应（移除可能的前缀）
        rewritten = response.strip()
        if rewritten.startswith("TWEET:"):
            rewritten = rewritten.replace("TWEET:", "").strip()

        return rewritten

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

        # ⭐ LLM已经在scene_hint中包含了真实感词汇，直接使用
        # 不再需要PromptEnhancer的死规则处理
        positive_prompt = scene_hint

        # 使用增强的negative prompt (避免AI感)
        negative_prompt = (
            "ugly, deformed, noisy, blurry, low quality, "
            "distorted, watermark, text, logo, "
            "artificial lighting, oversaturated, "
            "perfect studio lighting, airbrushed skin, "
            "flawless complexion, professional makeup, "
            "CGI, 3d render, anime, "
            "perfect, flawless, professional photoshoot"
        )

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

        # 从配置读取生成参数（保留配置系统）
        try:
            from config.image_config import load_image_config, get_generation_params
            config = load_image_config()
            gen_params = get_generation_params(config)
        except Exception:
            # 配置加载失败，使用默认值
            gen_params = {
                "width": 768,
                "height": 1024,
                "steps": 9,
                "cfg": 1.0
            }

        return {
            "slot": calendar_plan.get("slot", 1),
            "time_segment": calendar_plan.get("recommended_time", ""),
            "topic_type": calendar_plan.get("topic_type", ""),
            "tweet_text": tweet_text,
            "image_generation": {
                "scene_hint": scene_hint,               # 包含LLM生成的真实感词汇
                "positive_prompt": positive_prompt,     # 直接使用scene_hint
                "negative_prompt": negative_prompt,     # 增强的负向词
                "lora_params": lora_params,
                "generation_params": gen_params
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

    async def generate_pool(
        self,
        persona: Dict,
        count: int = 365,
        temperature: float = 1.0,
        explicit_nudity_allowed: bool = False
    ) -> Dict:
        """
        生成内容池（新版，基于archetype和content_types配置）

        Args:
            persona: 人设JSON
            count: 生成数量
            temperature: 温度参数
            explicit_nudity_allowed: 是否允许裸露内容

        Returns:
            tweets_pool JSON
        """
        from core.content_planner import ContentPlanner

        # 1. 创建内容计划
        planner = ContentPlanner()
        plan = planner.create_content_plan(persona, total_count=count)

        print(f"\n📋 内容生成计划:")
        print(f"   Persona: {plan['persona_name']}")
        print(f"   Archetype: {plan['archetype']}")
        print(f"   Total: {plan['total_count']} 条")
        print()
        print("📊 内容分布:")
        for content_type, type_count in plan['distribution'].items():
            print(f"   {content_type}: {type_count} 条")
        print()

        # 2. 收集所有generation specs
        all_specs = []
        for content_type, specs in plan['detailed_plan'].items():
            all_specs.extend(specs)

        print(f"🚀 开始生成 {len(all_specs)} 条推文...\n")

        # 3. 并发生成
        tasks = []
        for spec in all_specs:
            task = self.generator.generate_from_spec(
                persona=persona,
                generation_spec=spec,
                temperature=temperature,
                explicit_nudity_allowed=explicit_nudity_allowed
            )
            tasks.append(task)

        # 等待所有任务完成
        tweets = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 过滤错误
        successful_tweets = []
        failed_count = 0

        for i, tweet in enumerate(tweets):
            if isinstance(tweet, Exception):
                print(f"❌ 第 {i+1} 条生成失败: {str(tweet)}")
                failed_count += 1
            else:
                successful_tweets.append(tweet)

        print(f"\n✅ 生成完成:")
        print(f"   成功: {len(successful_tweets)} 条")
        print(f"   失败: {failed_count} 条")
        print()

        # 5. 多样性报告
        diversity_report = planner.get_diversity_report()
        print("📈 多样性报告:")
        for content_type, stats in diversity_report.items():
            print(f"   {content_type}:")
            print(f"     生成: {stats['total_generated']} 条")
            print(f"     唯一组合: {stats['unique_combinations']}")
        print()

        # 6. 构建结果
        persona_data = persona.get("data", {})

        return {
            "version": "2.0",  # 新版本标记
            "generated_at": datetime.now().isoformat(),
            "generation_mode": "content_pool",
            "persona": {
                "name": persona_data.get("name", ""),
                "archetype": plan['archetype'],
                "lora": {}
            },
            "content_plan": {
                "total_count": plan['total_count'],
                "distribution": plan['distribution'],
                "diversity_stats": diversity_report
            },
            "tweets": successful_tweets
        }

