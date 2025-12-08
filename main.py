#!/usr/bin/env python3
"""
独立高并发推文生成器
完全独立于ComfyUI，直接调用LLM API
"""
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_client import LLMClientPool
from utils.calendar_manager import CalendarManager
from core.tweet_generator import BatchTweetGenerator
from core.persona_generator import PersonaGenerator  # ⭐ 新增
from tools.datetime_tool import DateTimeTool
from tools.weather_tool import WeatherTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HighConcurrencyCoordinator:
    """高并发协调器"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        max_concurrent: int = 20,
        output_dir: str = "output_standalone",
        weather_api_key: str = None
    ):
        # 创建LLM客户端池
        self.llm_pool = LLMClientPool(
            api_key=api_key,
            api_base=api_base,
            model=model,
            max_concurrent=max_concurrent
        )

        # 创建生成器
        self.tweet_generator = BatchTweetGenerator(self.llm_pool)

        # ⭐ 创建PersonaGenerator（完全保留ComfyUI精调逻辑）
        self.persona_generator = PersonaGenerator(self.llm_pool.client)

        # ⭐ 创建Calendar Manager（完全保留ComfyUI精调逻辑）
        self.calendar_manager = CalendarManager()

        # ⭐ 保存API配置用于calendar生成
        self.api_key = api_key
        self.api_base = api_base
        self.model = model

        # ⭐ 保存weather API key
        self.weather_api_key = weather_api_key

        # 输出目录
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"协调器初始化完成")
        logger.info(f"  API: {api_base}")
        logger.info(f"  Model: {model}")
        logger.info(f"  最大并发: {max_concurrent}")
        if weather_api_key:
            logger.info(f"  天气API: 已启用")

    async def load_persona(self, persona_file: str) -> Dict:
        """加载人设文件"""
        with open(persona_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持两种格式：
        # 1. SillyTavern Character Card V2 格式
        # 2. 直接的persona JSON
        if "spec" in data and data["spec"] == "chara_card_v2":
            return data
        else:
            # 假设是直接格式，包装成Character Card
            return {
                "spec": "chara_card_v2",
                "spec_version": "2.0",
                "data": data
            }

    def _add_lora_config(self, persona: Dict, image_path: str) -> None:
        """
        自动添加LoRA配置到persona

        规则：
        - 文件名包含'jfz' → trigger_word: "sundub"
        - 文件名不包含'jfz' → trigger_word: "sunway"
        - 所有人物 → strength: 0.8 (默认)

        Args:
            persona: persona字典（会被直接修改）
            image_path: 图片路径（用于推断lora文件名）
        """
        # 从image_path提取文件名（不含扩展名）
        image_file = Path(image_path).stem  # 例如: "jfz_45" or "byrecarvalho"

        # 判断trigger_word
        if "jfz" in image_file.lower():
            trigger_word = "sundub"
        else:
            trigger_word = "sunway"

        # 构建lora文件路径（假设lora文件名与image文件名一致）
        lora_filename = f"{image_file}.safetensors"
        lora_path = f"lora/{lora_filename}"

        # 构建lora配置
        lora_config = {
            "model_path": lora_path,
            "strength": 0.8,
            "trigger_words": [trigger_word],
            "note": "LoRA for consistent character appearance"
        }

        # 添加到persona.data
        if "data" not in persona:
            persona["data"] = {}

        persona["data"]["lora"] = lora_config

        logger.info(f"  ✓ 自动添加LoRA配置: {lora_filename} (trigger: {trigger_word}, strength: 0.8)")

    async def load_calendar(self, calendar_file: str) -> Dict:
        """加载日历文件"""
        with open(calendar_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def generate_calendar_if_needed(
        self,
        persona: Dict,
        calendar_file: str,
        days_to_generate: int = 15,
        force_regenerate: bool = False
    ) -> Dict:
        """
        自动生成calendar（如果不存在）
        完全保留ComfyUI精调的calendar生成逻辑
        """
        persona_data = persona.get("data", {})
        persona_name = persona_data.get("name", "Unknown")

        # 尝试加载现有calendar
        calendar_path = Path(calendar_file)
        if calendar_path.exists() and not force_regenerate:
            logger.info(f"  ✓ 使用现有calendar: {calendar_file}")
            return await self.load_calendar(calendar_file)

        # 需要生成新calendar
        logger.info(f"  🔄 生成calendar: {persona_name}")

        from datetime import datetime
        year_month = datetime.now().strftime("%Y-%m")

        # 检查CalendarManager中是否已有
        if not force_regenerate and self.calendar_manager.calendar_exists(persona_name, year_month):
            logger.info(f"  ✓ 从CalendarManager加载: {persona_name}_{year_month}")
            return self.calendar_manager.load_calendar(persona_name, year_month)

        # 生成新calendar - 使用ComfyUI精调的prompt
        logger.info(f"  🤖 调用LLM生成calendar...")

        # 构建prompt（完全使用calendar_manager的精调逻辑）
        system_prompt = """You are planning a content calendar for an authentic social media presence. This is NOT corporate marketing—it's a real person's digital diary with all its beautiful messiness.

## Core Philosophy: Emotional Arcs Over Mechanical Scheduling

Real people don't post on perfect schedules or follow content type quotas. They post when they feel something.

### 1. Plan Around Emotional Journeys
Create natural emotional arcs across days:
- **Day 1-2**: Vulnerability/loneliness → subtle desire for connection
- **Day 3-4**: Playful confidence → teasing/flirtatious energy
- **Day 5-6**: Introspective/melancholic → raw confession
- **Day 7**: Empowerment → bold self-expression

Don't just rotate "daily_life, emotional, visual"—let emotions flow and build.

### 2. Strategic Imperfection (CRITICAL)
Include realistic human patterns:
- **Insomnia posts**: 2-3am timestamps when thoughts get too loud
- **Mood swings**: Monday's confidence can crash into Tuesday's anxiety
- **Posting gaps**: Some days have 3 posts, some have 0 (real life isn't consistent)
- **Typo-prone states**: Late night or emotional posts may be less polished
- **Deleted-then-reposted thoughts**: (indicate with theme variations)

CRITICAL NSFW RULES - BODY FIRST, POETRY NEVER (from calendar generation):
When content_direction requires sexual/NSFW content, be CONCRETE and PHYSICAL, never abstract/poetic.

❌ WRONG content_direction examples:
- "exploring the edges of desire"
- "whispers of passion curling through the quiet"
- "the delicate power of subtle domination"

✅ RIGHT content_direction examples:
- "2am. Wearing just the collar and an oversized shirt. Fingers keep tracing it. Want someone to tell you what to do but the apartment's empty. Post about the ache of wanting to submit with no one to submit to. Mention how the collar feels heavier when you're alone."
- "Just woke up in yesterday's underwear. Sheets tangled around legs. Hand keeps sliding to touch yourself but you're making yourself wait. Post about being horny and disciplined at the same time. Can mention being wet, aching, grinding against the pillow."
- "Getting dressed for no one. Black lace set. Sitting in front of mirror on your knees practicing poses. Post about training yourself even when alone. Can mention wanting to be good, wanting to be used."

**NO TIMESTAMPS/DATES**: Never include "Monday", "tonight", "2am", "December 7" in content_direction - use mood states instead.

## Technical Requirements

Must output valid JSON format:
1. All strings use English double quotes `"`, not Chinese quotes
2. All required fields must be present
3. Output must be complete, not truncated
4. No explanatory text before/after JSON—pure JSON only"""

        user_prompt = self.calendar_manager.generate_calendar_prompt(
            persona, year_month, days_to_generate
        )

        # 调用LLM
        from utils.llm_client import AsyncLLMClient
        llm = AsyncLLMClient(self.api_key, self.api_base, self.model)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await llm.generate(messages, temperature=0.7, max_tokens=10000)

        # 解析并保存
        calendar_data = self.calendar_manager.parse_calendar_response(
            response, persona_name, year_month
        )

        if self.calendar_manager.save_calendar(persona_name, year_month, calendar_data):
            logger.info(f"  ✓ Calendar生成成功: {len(calendar_data['calendar'])}天")
            return calendar_data
        else:
            raise RuntimeError("Failed to save calendar")

    def gather_context(self, persona: Dict) -> Dict:
        """
        收集上下文信息（天气、日期等）
        完全保留ComfyUI的ContextGatherer逻辑
        """
        persona_data = persona.get("data", {})
        context = {}

        # 获取location信息
        core_info = persona_data.get("core_info", {})
        location = core_info.get("location", {})
        city = location.get("city", "New York")
        country_code = location.get("country_code", "US")
        timezone = location.get("timezone")

        # 1. 日期时间（必需）
        try:
            date_tool = DateTimeTool(country=country_code, compact=True, timezone=timezone)
            context["date"] = date_tool.execute()
        except Exception as e:
            logger.warning(f"获取日期失败: {e}")
            context["date"] = {"error": str(e)}

        # 2. 天气（可选）
        if self.weather_api_key:
            try:
                weather_tool = WeatherTool(self.weather_api_key)
                context["weather"] = weather_tool.execute(city, country_code)
            except Exception as e:
                logger.warning(f"获取天气失败: {e}")
                context["weather"] = {"error": str(e)}

        return context

    async def generate_persona_from_image(
        self,
        image_path: str,
        output_file: str,
        nsfw_level: str = "enabled",
        language: str = "English",
        location: str = "",
        business_goal: str = "",
        custom_instructions: str = "",
        temperature: float = 0.85
    ) -> Dict:
        """
        从图片生成完整人设（完全保留ComfyUI精调逻辑）

        Args:
            image_path: 图片路径
            output_file: 输出的persona JSON文件路径
            nsfw_level: "enabled" 或 "disabled"
            language: "English" 或 "中文"
            location: 地理位置（留空自动生成）
            business_goal: 业务目标
            custom_instructions: 自定义控制词
            temperature: 温度参数
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🎨 从图片生成人设: {Path(image_path).name}")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()

        # 调用PersonaGenerator（完全保留ComfyUI的多阶段流程）
        persona = await self.persona_generator.generate_from_image(
            image_path=image_path,
            nsfw_level=nsfw_level,
            language=language,
            location=location,
            business_goal=business_goal,
            custom_instructions=custom_instructions,
            temperature=temperature
        )

        # ⭐ 自动添加LoRA配置（基于文件名规则）
        self._add_lora_config(persona, image_path)

        # 保存persona
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(persona, f, ensure_ascii=False, indent=2)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"\n✅ 人设生成完成!")
        logger.info(f"   名称: {persona['data']['name']}")
        logger.info(f"   示例推文数: {len(persona['data'].get('twitter_persona', {}).get('tweet_examples', []))}")
        logger.info(f"   耗时: {duration:.1f}秒")
        logger.info(f"   保存至: {output_path}\n")

        return persona

    async def generate_tweets_for_persona(
        self,
        persona_file: str,
        calendar_file: str,
        tweets_count: int = 5,
        temperature: float = 1.0,
        auto_generate_calendar: bool = False,
        enable_context: bool = False
    ) -> Dict:
        """为单个人设生成推文"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📝 生成推文: {Path(persona_file).stem}")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()

        # 加载数据
        persona = await self.load_persona(persona_file)

        # ⭐ 自动生成calendar（如果需要）
        if auto_generate_calendar:
            calendar = await self.generate_calendar_if_needed(
                persona, calendar_file, days_to_generate=15
            )
        else:
            calendar = await self.load_calendar(calendar_file)

        # ⭐ 收集上下文（如果启用）
        context = None
        if enable_context:
            context = self.gather_context(persona)
            logger.info(f"  📅 日期: {context.get('date', {}).get('formatted', 'N/A')}")
            if 'weather' in context:
                weather_formatted = context['weather'].get('formatted', 'N/A')
                logger.info(f"  🌤️  天气: {weather_formatted}")

        # ⭐ 生成推文（直接使用BatchTweetGenerator，传递context）
        tweets_batch = await self.tweet_generator.generate_batch(
            persona=persona,
            calendar=calendar,
            tweets_count=tweets_count,
            temperature=temperature,
            context=context  # 直接传递context
        )

        # 保存结果
        persona_name = persona["data"]["name"]
        output_file = self.output_dir / f"{persona_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tweets_batch, f, ensure_ascii=False, indent=2)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"\n✅ 推文生成完成")
        logger.info(f"   人设: {persona_name}")
        logger.info(f"   推文数: {len(tweets_batch['tweets'])}")
        logger.info(f"   耗时: {duration:.1f}秒")
        logger.info(f"   保存至: {output_file}\n")

        return tweets_batch

    async def generate_batch_tweets(
        self,
        persona_files: List[str],
        calendar_files: List[str],
        tweets_per_persona: int = 5,
        temperature: float = 1.0
    ):
        """批量生成推文（高并发）"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 批量生成推文: {len(persona_files)} 个人设")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()

        # 创建任务
        tasks = []
        for persona_file, calendar_file in zip(persona_files, calendar_files):
            task = self.generate_tweets_for_persona(
                persona_file=persona_file,
                calendar_file=calendar_file,
                tweets_count=tweets_per_persona,
                temperature=temperature
            )
            tasks.append(task)

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]

        duration = (datetime.now() - start_time).total_seconds()
        total_tweets = sum(len(r["tweets"]) for r in successful)

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 批量生成完成")
        logger.info(f"{'='*70}")
        logger.info(f"   人设数: {len(persona_files)}")
        logger.info(f"   成功: {len(successful)}")
        logger.info(f"   失败: {len(failed)}")
        logger.info(f"   总推文数: {total_tweets}")
        logger.info(f"   总耗时: {duration:.1f}秒")
        logger.info(f"   平均: {duration/len(persona_files):.1f}秒/人设")
        logger.info(f"{'='*70}\n")

    async def generate_batch_personas(
        self,
        image_files: List[str],
        output_dir: str = "personas",
        nsfw_level: str = "enabled",
        language: str = "English",
        location: str = "",
        business_goal: str = "",
        custom_instructions: str = "",
        temperature: float = 0.85
    ):
        """
        ⚡ 批量人设生成（并发模式）

        Args:
            image_files: 图片文件列表
            output_dir: 输出目录
            其他参数同 generate_persona_from_image
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"⚡ 批量人设生成模式（并发）")
        logger.info(f"   图片数量: {len(image_files)}")
        logger.info(f"   输出目录: {output_dir}")
        logger.info(f"{'='*70}\n")

        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        start_time = datetime.now()

        # 为每个图片创建任务
        tasks = []
        for image_path in image_files:
            # 自动生成输出文件名
            image_name = Path(image_path).stem
            output_file = f"{output_dir}/{image_name}_persona.json"

            # 创建任务
            task = self.generate_persona_from_image(
                image_path=image_path,
                output_file=output_file,
                nsfw_level=nsfw_level,
                language=language,
                location=location,
                business_goal=business_goal,
                custom_instructions=custom_instructions,
                temperature=temperature
            )
            tasks.append((image_path, task))

        # 🚀 并发执行所有人设生成
        logger.info(f"🚀 开始并发生成 {len(tasks)} 个人设...\n")

        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        # 统计结果
        success = 0
        failed = 0
        for (image_path, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {Path(image_path).name}: {result}")
                failed += 1
            else:
                logger.info(f"✅ {Path(image_path).name}: {result.get('data', {}).get('name', 'Unknown')}")
                success += 1

        elapsed = (datetime.now() - start_time).total_seconds()
        total = len(image_files)

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 批量人设生成完成")
        logger.info(f"   总耗时: {elapsed:.1f}秒")
        logger.info(f"   成功: {success} / {total}")
        logger.info(f"   失败: {failed} / {total}")
        if total > 0:
            logger.info(f"   平均速度: {elapsed/total:.1f}秒/人设")
        logger.info(f"{'='*70}\n")


async def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="独立高并发推文生成器 - 完全解耦于ComfyUI，支持人设生成、推文生成、calendar生成"
    )

    # ⭐ 人设生成模式（完全保留ComfyUI精调逻辑）
    parser.add_argument(
        "--generate-persona",
        action="store_true",
        help="人设生成模式：从图片生成完整人设"
    )
    parser.add_argument(
        "--image",
        help="图片路径（用于单个人设生成）"
    )
    parser.add_argument(
        "--images",
        nargs="+",
        help="批量人设生成：多个图片路径"
    )
    parser.add_argument(
        "--nsfw-level",
        choices=["enabled", "disabled"],
        default="enabled",
        help="NSFW内容级别（默认enabled）"
    )
    parser.add_argument(
        "--language",
        choices=["English", "中文", "日本語"],
        default="English",
        help="生成语言（默认English）"
    )
    parser.add_argument(
        "--location",
        default="",
        help="地理位置（留空自动生成）"
    )
    parser.add_argument(
        "--business-goal",
        default="",
        help="业务目标"
    )
    parser.add_argument(
        "--custom-instructions",
        default="",
        help="自定义控制词"
    )
    parser.add_argument(
        "--persona-output",
        default="personas/generated_persona.json",
        help="生成的人设保存路径（默认personas/generated_persona.json）"
    )

    # 推文生成模式参数
    parser.add_argument(
        "--persona",
        help="人设JSON文件路径"
    )
    parser.add_argument(
        "--calendar",
        help="日历JSON文件路径"
    )
    parser.add_argument(
        "--tweets",
        type=int,
        default=5,
        help="要生成的推文数量（默认5）"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("API_KEY"),
        help="LLM API密钥（可从.env文件读取API_KEY）"
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("API_BASE", "https://api.openai.com/v1"),
        help="LLM API地址（可从.env文件读取API_BASE，默认：https://api.openai.com/v1）"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("MODEL", "gpt-4"),
        help="LLM模型名称（可从.env文件读取MODEL，默认：gpt-4）"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=int(os.getenv("MAX_CONCURRENT", "20")),
        help="最大并发数（可从.env文件读取MAX_CONCURRENT，默认：20）"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.getenv("TEMPERATURE", "1.0")),
        help="温度参数（可从.env文件读取TEMPERATURE，默认：1.0）"
    )
    parser.add_argument(
        "--output-dir",
        default="output_standalone",
        help="输出目录（默认output_standalone）"
    )

    # 批量模式
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="批量模式：同时处理多个人设"
    )
    parser.add_argument(
        "--personas",
        nargs="+",
        help="批量模式：多个人设文件路径"
    )
    parser.add_argument(
        "--calendars",
        nargs="+",
        help="批量模式：多个日历文件路径"
    )

    # ⭐ Calendar自动生成选项（完全保留ComfyUI精调逻辑）
    parser.add_argument(
        "--generate-calendar",
        action="store_true",
        help="自动生成calendar（如果不存在）"
    )

    # ⭐ 上下文收集选项
    parser.add_argument(
        "--enable-context",
        action="store_true",
        help="启用上下文收集（日期、天气等）"
    )
    parser.add_argument(
        "--weather-api-key",
        default=os.getenv("WEATHER_API_KEY"),
        help="OpenWeatherMap API密钥（可从.env文件读取WEATHER_API_KEY，用于天气上下文）"
    )

    # ⭐ 图片生成选项（Z-Image）
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="图片生成模式：从推文批次JSON生成图片"
    )
    parser.add_argument(
        "--tweets-batch",
        help="推文批次JSON文件路径（用于图片生成）"
    )
    parser.add_argument(
        "--zimage-model-path",
        default="Z-Image/ckpts/Z-Image-Turbo",
        help="Z-Image模型路径（默认Z-Image/ckpts/Z-Image-Turbo）"
    )
    parser.add_argument(
        "--num-gpus",
        type=int,
        default=None,
        help="使用的GPU数量（默认None=自动检测全部）"
    )
    parser.add_argument(
        "--image-output-dir",
        default="output_images",
        help="图片输出目录（默认output_images）"
    )
    parser.add_argument(
        "--start-slot",
        type=int,
        default=0,
        help="起始slot索引（默认0）"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="最大生成图片数量（默认None=全部生成）"
    )
    parser.add_argument(
        "--single-gpu",
        action="store_true",
        help="强制使用单GPU模式（即使有多个GPU）"
    )
    parser.add_argument(
        "--use-native-pytorch",
        action="store_true",
        help="使用原生PyTorch模式（默认使用diffusers，支持LoRA）"
    )

    args = parser.parse_args()

    # 检查必需的 API_KEY
    if not args.api_key:
        parser.error("需要提供 API_KEY，请在 .env 文件中设置或使用 --api-key 参数")

    # 创建协调器
    coordinator = HighConcurrencyCoordinator(
        api_key=args.api_key,
        api_base=args.api_base,
        model=args.model,
        max_concurrent=args.max_concurrent,
        output_dir=args.output_dir,
        weather_api_key=args.weather_api_key
    )

    # ⭐ 人设生成模式
    if args.generate_persona:
        # 批量人设生成
        if args.images:
            await coordinator.generate_batch_personas(
                image_files=args.images,
                output_dir="personas",
                nsfw_level=args.nsfw_level,
                language=args.language,
                location=args.location,
                business_goal=args.business_goal,
                custom_instructions=args.custom_instructions,
                temperature=args.temperature
            )
            return

        # 单个人设生成
        if not args.image:
            parser.error("人设生成模式需要 --image 或 --images 参数")

        await coordinator.generate_persona_from_image(
            image_path=args.image,
            output_file=args.persona_output,
            nsfw_level=args.nsfw_level,
            language=args.language,
            location=args.location,
            business_goal=args.business_goal,
            custom_instructions=args.custom_instructions,
            temperature=args.temperature
        )
        return

    # ⭐ 图片生成模式（Z-Image）
    if args.generate_images:
        if not args.tweets_batch:
            parser.error("图片生成模式需要 --tweets-batch 参数")

        from core.image_generator import ImageGenerationCoordinator

        logger.info(f"\n{'='*70}")
        logger.info(f"🎨 图片生成模式")
        logger.info(f"{'='*70}\n")

        # 创建图片生成协调器
        image_coord = ImageGenerationCoordinator(
            model_path=args.zimage_model_path,
            num_gpus=args.num_gpus,
            use_diffusers=not args.use_native_pytorch  # 默认使用diffusers
        )

        # 生成图片
        results = await image_coord.generate_from_tweets_batch(
            tweets_batch_file=args.tweets_batch,
            output_dir=args.image_output_dir,
            start_slot=args.start_slot,
            max_images=args.max_images,
            use_multi_gpu=not args.single_gpu
        )

        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"\n✅ 图片生成完成")
        logger.info(f"   成功: {success_count}/{len(results)}")
        logger.info(f"   输出目录: {args.image_output_dir}\n")

        return

    # 推文生成模式
    if not args.persona or not args.calendar:
        parser.error("推文生成模式需要 --persona 和 --calendar 参数")

    # 运行
    if args.batch_mode:
        if not args.personas or not args.calendars:
            parser.error("批量模式需要 --personas 和 --calendars")

        if len(args.personas) != len(args.calendars):
            parser.error("人设和日历文件数量必须相同")

        await coordinator.generate_batch_tweets(
            persona_files=args.personas,
            calendar_files=args.calendars,
            tweets_per_persona=args.tweets,
            temperature=args.temperature
        )
    else:
        await coordinator.generate_tweets_for_persona(
            persona_file=args.persona,
            calendar_file=args.calendar,
            tweets_count=args.tweets,
            temperature=args.temperature,
            auto_generate_calendar=args.generate_calendar,  # ⭐ 传递auto-generate选项
            enable_context=args.enable_context  # ⭐ 传递context选项
        )


if __name__ == "__main__":
    asyncio.run(main())
