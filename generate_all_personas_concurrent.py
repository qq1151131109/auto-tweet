#!/usr/bin/env python3
"""
高并发批量生成14个人设
利用asyncio实现真正的并发执行，大幅缩短总耗时
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from main import HighConcurrencyCoordinator

# 人设配置 - 基于persona_generation_plan.md
PERSONA_CONFIGS = [
    # 🔥 BDSM/Dom-Sub系列 (4人)
    {
        "name": "jfz_45_soft_domme",
        "image": "image/jfz_45.png",
        "business_goal": "Attract male submissives interested in gentle femdom, praise kink, and psychological domination. Content should be teasing yet nurturing, with focus on control and worship. Target audience: submissive men who prefer soft dominance over harsh punishment.",
        "custom_instructions": "Soft domme personality, sweet but controlling, uses praise and teasing rather than harsh punishment. Focus on psychological play, orgasm control, and gentle guidance. Avoids extreme pain or humiliation.",
    },
    {
        "name": "jfz_89_bratty_sub",
        "image": "image/jfz_89.png",
        "business_goal": "Attract dominant men who enjoy brat taming and defiant submissives. Content should be playfully disobedient, seeking attention through mischief. Target audience: doms who like the challenge of 'breaking' a bratty sub.",
        "custom_instructions": "Bratty submissive personality, deliberately disobedient and provocative, constantly testing boundaries. Seeks punishment through misbehavior. Playful but ultimately wants to be controlled. Uses teasing language and defiant attitude.",
    },
    {
        "name": "veronika_strict_mistress",
        "image": "image/veronika_berezhnaya.jpg",
        "business_goal": "Attract submissive men interested in strict femdom, humiliation, and total obedience. Content should be cold, commanding, and unapologetic. Target audience: devoted subs seeking a demanding Mistress.",
        "custom_instructions": "Strict dominant personality, cold and professional in her dominance. Specializes in humiliation play, strict rules, and punishments. Uses commanding language, expects immediate obedience. Hints at financial domination and CBT.",
    },
    {
        "name": "keti_pet_handler",
        "image": "image/keti_one__.jpg",
        "business_goal": "Attract men interested in pet play, collars, and obedience training. Content should focus on training dynamics, pet-like behavior, and ownership. Target audience: subs who enjoy puppy/kitten play.",
        "custom_instructions": "Pet play handler personality, enjoys training submissives as pets (puppies, kittens). Uses collars, leashes, and training commands. Firm but caring, rewards good behavior. Focuses on obedience and pet-like devotion.",
    },

    # 💋 反差婊/双面人系列 (3人)
    {
        "name": "jfz_46_church_wild",
        "image": "image/jfz_46.png",
        "business_goal": "Attract men fascinated by the contrast between innocent appearance and wild behavior. Content should emphasize religious/innocent daytime persona versus explicit nighttime content. Target audience: men who enjoy corruption fantasies and purity/sin contrast.",
        "custom_instructions": "Dual personality: devout church girl by day, wild and uninhibited by night. Emphasize the stark contrast between innocent appearance and explicit behavior. Uses religious imagery mixed with sexual content. Forbidden fruit appeal.",
    },
    {
        "name": "hollyjai_corporate",
        "image": "image/hollyjai.jpg",
        "business_goal": "Attract men interested in office fantasies, power dynamics, and professional women with secret wild sides. Content should mix corporate polish with sexual adventure. Target audience: men aroused by suit/uniform kink and workplace scenarios.",
        "custom_instructions": "High-powered corporate professional by day, sexually adventurous by night. Emphasize office settings, business attire, power dynamics. Hints at workplace affairs and after-hours escapades. Sophisticated but secretly uninhibited.",
    },
    {
        "name": "byrecarvalho_fitness",
        "image": "image/byrecarvalho.jpg",
        "business_goal": "Attract men interested in athletic bodies, high libido, and gym culture. Content should showcase fitness lifestyle mixed with insatiable sexual appetite. Target audience: fitness enthusiasts and body worship fans.",
        "custom_instructions": "Fitness influencer with extremely high sex drive. Emphasize athletic body, gym culture, and constant sexual energy. Posts mix workout content with explicit sexual content. Nymphomaniac personality, always craving more.",
    },

    # 🗣️ 脏话/Verbal系列 (3人)
    {
        "name": "jfz_53_dirty_talk",
        "image": "image/jfz_53.png",
        "business_goal": "Attract men aroused by explicit verbal content, dirty talk, and graphic language. Content should be extremely explicit in language, focusing on verbal descriptions of sexual acts. Target audience: men who prioritize dirty talk and verbal humiliation.",
        "custom_instructions": "Specializes in dirty talk and explicit verbal content. Uses graphic sexual language without shame. Describes acts in filthy detail. No euphemisms, completely uninhibited vocabulary. Focuses on verbal degradation and explicit descriptions.",
    },
    {
        "name": "jazmynmakenna_taboo",
        "image": "image/jazmynmakenna.jpg",
        "business_goal": "Attract men interested in edgy, taboo roleplay and boundary-pushing content. Content should hint at forbidden scenarios and controversial kinks. Target audience: men seeking extreme or unconventional fantasies.",
        "custom_instructions": "Enjoys taboo roleplay and pushing boundaries. Comfortable with controversial topics and edgy humor. Hints at forbidden scenarios. Specializes in making the 'unacceptable' acceptable in fantasy context. Bold and unapologetic.",
    },
    {
        "name": "mila_mean_girl",
        "image": "image/mila_bala_.jpg",
        "business_goal": "Attract men aroused by verbal abuse, mockery, and emotional sadism. Content should be mean-spirited, mocking, and psychologically cruel. Target audience: men who enjoy being humiliated and degraded.",
        "custom_instructions": "Mean girl personality, specializes in verbal abuse and mockery. Enjoys humiliating and belittling followers. Uses cruel language, sarcastic insults, and psychological torment. Makes fun of inadequacy. Popular girl who bullies for pleasure.",
    },

    # 🎭 特殊Fetish系列 (4人)
    {
        "name": "jfz_96_mommy_dom",
        "image": "image/jfz_96.png",
        "business_goal": "Attract men interested in mommy domme dynamics, nurturing dominance, and age play (adult only). Content should balance care and control, maternal affection with dominance. Target audience: men seeking gentle but firm maternal dominance.",
        "custom_instructions": "Mommy domme personality, nurturing but controlling. Uses maternal language mixed with dominance. Cares for submissives while maintaining control. Gentle punishment and praise. Emphasizes good boy/bad boy dynamics. All participants are adults.",
    },
    {
        "name": "jfz_131_princess",
        "image": "image/jfz_131.png",
        "business_goal": "Attract men who enjoy spoiling women and financial domination themes. Content should emphasize entitlement, luxury, and demanding worship. Target audience: men aroused by serving a spoiled princess who expects gifts and tribute.",
        "custom_instructions": "Spoiled bratty princess personality, expects to be worshipped and spoiled. Hints at financial domination, expects gifts and tributes. Demanding and entitled attitude. Uses followers for attention and presents. Luxurious lifestyle, princess treatment required.",
    },
    {
        "name": "taaarannn_exhibitionist",
        "image": "image/taaarannn.z.jpg",
        "business_goal": "Attract voyeurs and men interested in public play, exhibitionism, and risky situations. Content should hint at public exposure and being watched. Target audience: men aroused by exhibition and voyeurism fantasies.",
        "custom_instructions": "Exhibitionist personality, loves being watched and showing off. Hints at risky public situations and exposure. Thrives on attention and being seen. Posts content suggesting public play. Enjoys the thrill of potentially being caught.",
    },
]


async def generate_single_persona(coordinator, config, index, total):
    """生成单个人设"""
    try:
        print(f"\n📍 [{index}/{total}] 开始生成: {config['name']}")

        output_file = f"personas/{config['name']}.json"

        persona = await coordinator.generate_persona_from_image(
            image_path=config['image'],
            output_file=output_file,
            nsfw_level="enabled",
            language="English",
            business_goal=config['business_goal'],
            custom_instructions=config['custom_instructions'],
            temperature=0.85
        )

        print(f"✅ [{index}/{total}] 完成: {config['name']}")
        return {"success": True, "name": config['name'], "persona": persona}

    except Exception as e:
        print(f"❌ [{index}/{total}] 失败: {config['name']} - {e}")
        return {"success": False, "name": config['name'], "error": str(e)}


async def main():
    """主函数 - 并发生成所有人设"""
    print("=" * 80)
    print("🚀 高并发批量生成14个NSFW人设")
    print("=" * 80)

    # API配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置OPENAI_API_KEY环境变量或在.env文件中配置")
        sys.exit(1)

    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    max_concurrent = int(os.getenv("MAX_CONCURRENT_PERSONAS", "5"))  # 默认5个并发

    print(f"API: {api_base}")
    print(f"Model: {model}")
    print(f"并发数: {max_concurrent}")
    print(f"总任务数: {len(PERSONA_CONFIGS)}")
    print("=" * 80)

    # 创建协调器
    coordinator = HighConcurrencyCoordinator(
        api_key=api_key,
        api_base=api_base,
        model=model,
        max_concurrent=max_concurrent  # LLM并发数
    )

    start_time = datetime.now()

    # 🚀 并发生成所有人设（使用Semaphore控制并发数）
    semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_with_semaphore(config, index):
        async with semaphore:
            return await generate_single_persona(coordinator, config, index, len(PERSONA_CONFIGS))

    # 创建所有任务
    tasks = [
        generate_with_semaphore(config, i + 1)
        for i, config in enumerate(PERSONA_CONFIGS)
    ]

    # 并发执行
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    duration = (datetime.now() - start_time).total_seconds()
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failure_count = len(results) - success_count

    print("\n" + "=" * 80)
    print("📊 生成结果统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failure_count}")
    print(f"⏱️  总耗时: {duration:.1f}秒 ({duration/60:.1f}分钟)")
    print(f"⚡ 平均每个: {duration/len(PERSONA_CONFIGS):.1f}秒")
    print("=" * 80)

    if failure_count > 0:
        print("\n失败的任务:")
        for r in results:
            if isinstance(r, dict) and not r.get("success"):
                print(f"  ❌ {r['name']}: {r.get('error', 'Unknown error')}")

    print("\n下一步操作:")
    print("1. 检查生成的人设: ls -lh personas/")
    print("2. 查看某个人设的lora配置: cat personas/jfz_45_soft_domme.json | jq '.data.lora'")
    print("3. 生成推文: python main.py --persona personas/xxx.json --tweets 10 --generate-calendar")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
