#!/usr/bin/env python3
"""
批量生成推文 - 7天 × 5条/天
为13个personas生成7天的推文，每天5条
"""
import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_client import LLMClientPool
from utils.calendar_manager import CalendarManager
from core.tweet_generator import BatchTweetGenerator
from tools.datetime_tool import DateTimeTool
from tools.weather_tool import WeatherTool
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DayByDayTweetGenerator:
    """按天生成推文的生成器"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        max_concurrent: int = 50,
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

        # Calendar manager
        self.calendar_manager = CalendarManager()

        # API配置
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.weather_api_key = weather_api_key

        # 输出目录
        self.output_dir = Path("output_standalone")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"✓ DayByDayTweetGenerator初始化完成")
        logger.info(f"  API: {api_base}")
        logger.info(f"  Model: {model}")
        logger.info(f"  最大并发: {max_concurrent}")

    def load_persona(self, persona_file: str) -> dict:
        """加载人设文件"""
        with open(persona_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "spec" in data and data["spec"] == "chara_card_v2":
            return data
        else:
            return {
                "spec": "chara_card_v2",
                "spec_version": "2.0",
                "data": data
            }

    def gather_context(self, persona: dict, day_offset: int = 0) -> dict:
        """收集上下文信息（支持day_offset）"""
        persona_data = persona.get("data", {})
        context = {}

        # 获取location信息
        core_info = persona_data.get("core_info", {})
        location = core_info.get("location", {})
        city = location.get("city", "New York")
        country_code = location.get("country_code", "US")
        timezone = location.get("timezone")

        # 1. 日期时间（支持day_offset）
        try:
            date_tool = DateTimeTool(country=country_code, compact=True, timezone=timezone)
            context["date"] = date_tool.execute(day_offset=day_offset)
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

    async def generate_calendar_if_needed(
        self,
        persona: dict,
        days_to_generate: int = 14
    ) -> dict:
        """生成calendar（14天）"""
        persona_data = persona.get("data", {})
        persona_name = persona_data.get("name", "Unknown")

        year_month = datetime.now().strftime("%Y-%m")

        # 检查是否已存在
        if self.calendar_manager.calendar_exists(persona_name, year_month):
            logger.info(f"  ✓ 使用已有calendar: {persona_name}_{year_month}")
            return self.calendar_manager.load_calendar(persona_name, year_month)

        # 生成新calendar
        logger.info(f"  🤖 生成calendar: {persona_name} (14天)")

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

    async def generate_tweets_for_one_day(
        self,
        persona: dict,
        calendar: dict,
        day_offset: int,
        tweets_per_day: int = 5,
        temperature: float = 1.0
    ) -> dict:
        """为某一天生成多条推文"""
        persona_data = persona.get("data", {})
        persona_name = persona_data.get("name", "Unknown")

        # 获取calendar中的日期列表
        calendar_data = calendar.get("calendar", {})
        dates_list = list(calendar_data.keys())

        if day_offset >= len(dates_list):
            raise ValueError(f"day_offset {day_offset} 超出calendar范围 ({len(dates_list)}天)")

        # 选择对应天的plan
        target_date = dates_list[day_offset]
        day_plan = calendar_data[target_date]

        # 收集context（带day_offset）
        context = self.gather_context(persona, day_offset=day_offset)

        logger.info(f"  📅 日期: {context.get('date', {}).get('formatted', 'N/A')}")
        if 'weather' in context:
            weather_formatted = context['weather'].get('formatted', 'N/A')
            logger.info(f"  🌤️  天气: {weather_formatted}")

        # 为这一天生成多条推文（并发）
        tasks = []
        for slot_idx in range(1, tweets_per_day + 1):
            # 复制plan避免互相干扰
            plan_copy = day_plan.copy()
            plan_copy["slot"] = slot_idx
            plan_copy["date"] = target_date

            task = self.tweet_generator.generator.generate_single_tweet(
                persona=persona,
                calendar_plan=plan_copy,
                context=context,
                temperature=temperature
            )
            tasks.append(task)

        # 并发生成
        tweets = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤错误
        successful_tweets = [
            t for t in tweets if not isinstance(t, Exception)
        ]

        # 构建结果
        return {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "persona": {
                "name": persona_name,
                "lora": persona_data.get("lora", {})
            },
            "daily_plan": {
                "date": target_date,
                "day_offset": day_offset,
                "total_tweets": len(successful_tweets)
            },
            "tweets": successful_tweets
        }

    async def generate_single_persona_7days(
        self,
        persona_file: str,
        tweets_per_day: int = 5,
        temperature: float = 1.0
    ):
        """为单个persona生成7天的推文"""
        persona_name = Path(persona_file).stem
        logger.info(f"\n{'='*70}")
        logger.info(f"📝 生成推文: {persona_name} (7天 × {tweets_per_day}条/天)")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()

        # 1. 加载persona
        persona = self.load_persona(persona_file)

        # 2. 生成/加载14天calendar
        calendar = await self.generate_calendar_if_needed(persona, days_to_generate=14)

        # 3. 循环7天，每天生成5条推文
        results = []
        for day_offset in range(7):
            logger.info(f"\n  📆 第{day_offset + 1}天 (offset={day_offset})")

            try:
                tweets_batch = await self.generate_tweets_for_one_day(
                    persona, calendar, day_offset, tweets_per_day, temperature
                )

                # 保存到文件
                persona_name_clean = persona["data"]["name"]
                output_file = self.output_dir / f"{persona_name_clean}_day{day_offset}_tweets{tweets_per_day}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(tweets_batch, f, ensure_ascii=False, indent=2)

                results.append({
                    "day_offset": day_offset,
                    "success": True,
                    "tweets_count": len(tweets_batch["tweets"]),
                    "file": str(output_file)
                })

                logger.info(f"  ✅ 第{day_offset + 1}天完成: {len(tweets_batch['tweets'])}条推文 → {output_file.name}")

            except Exception as e:
                logger.error(f"  ❌ 第{day_offset + 1}天失败: {e}")
                results.append({
                    "day_offset": day_offset,
                    "success": False,
                    "error": str(e)
                })

        duration = (datetime.now() - start_time).total_seconds()

        success_days = sum(1 for r in results if r["success"])
        total_tweets = sum(r.get("tweets_count", 0) for r in results if r["success"])

        logger.info(f"\n✅ {persona_name} 完成")
        logger.info(f"   成功天数: {success_days}/7")
        logger.info(f"   总推文数: {total_tweets}")
        logger.info(f"   耗时: {duration:.1f}秒\n")

        return {
            "persona": persona_name,
            "success_days": success_days,
            "total_tweets": total_tweets,
            "duration": duration,
            "results": results
        }


async def main():
    """主函数 - 批量生成所有personas的7天推文"""
    print("=" * 80)
    print("🚀 批量生成推文: 13个personas × 7天 × 5条/天 = 455条推文")
    print("=" * 80)

    # API配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置OPENAI_API_KEY环境变量")
        sys.exit(1)

    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    max_concurrent = int(os.getenv("MAX_CONCURRENT", "50"))
    weather_api_key = os.getenv("WEATHER_API_KEY")

    print(f"API: {api_base}")
    print(f"Model: {model}")
    print(f"并发数: {max_concurrent}")
    print("=" * 80)

    # 获取所有persona文件
    personas_dir = Path("personas")
    persona_files = sorted(personas_dir.glob("*.json"))

    if not persona_files:
        print("❌ 错误: personas/目录下没有找到persona文件")
        sys.exit(1)

    print(f"\n找到 {len(persona_files)} 个personas:")
    for pf in persona_files:
        print(f"  - {pf.stem}")
    print()

    # 创建生成器
    generator = DayByDayTweetGenerator(
        api_key=api_key,
        api_base=api_base,
        model=model,
        max_concurrent=max_concurrent,
        weather_api_key=weather_api_key
    )

    start_time = datetime.now()

    # 并发生成所有personas（每个persona内部会串行生成7天）
    semaphore = asyncio.Semaphore(3)  # 限制同时处理的persona数量为3（因为每个会生成7天）

    async def generate_with_semaphore(persona_file):
        async with semaphore:
            return await generator.generate_single_persona_7days(
                persona_file=str(persona_file),
                tweets_per_day=5,
                temperature=1.0
            )

    # 创建所有任务
    tasks = [
        generate_with_semaphore(pf)
        for pf in persona_files
    ]

    # 并发执行
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    duration = (datetime.now() - start_time).total_seconds()

    successful_personas = [r for r in all_results if isinstance(r, dict)]
    total_tweets = sum(r.get("total_tweets", 0) for r in successful_personas)

    print("\n" + "=" * 80)
    print("📊 生成结果统计")
    print("=" * 80)
    print(f"✅ 成功personas: {len(successful_personas)}/{len(persona_files)}")
    print(f"📝 总推文数: {total_tweets}")
    print(f"⏱️  总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟)")
    print(f"⚡ 平均每个persona: {duration/len(persona_files):.1f}秒")
    print(f"⚡ 平均每条推文: {duration/total_tweets:.2f}秒" if total_tweets > 0 else "")
    print("=" * 80)

    # 显示失败的
    failed_personas = [r for r in all_results if isinstance(r, Exception)]
    if failed_personas:
        print("\n失败的personas:")
        for err in failed_personas:
            print(f"  ❌ {err}")

    print("\n下一步操作:")
    print("1. 查看生成的推文: ls -lh output_standalone/")
    print("2. 生成图片: python main.py --generate-images --tweets-batch output_standalone/xxx.json --num-gpus 4")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
